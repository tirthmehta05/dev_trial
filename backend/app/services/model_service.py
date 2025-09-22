from pydantic import create_model, Field, BaseModel, conlist
from pydantic.types import constr, conint
from typing import List, Optional, Any, Literal, Union

from ..repositories.schema_repository import SchemaRepository

# Mapping from YAML types to Python types
TYPE_MAPPING = {
    'str': str,
    'int': int,
    'bool': bool,
    'float': float,
}

class ModelService:
    """Service for creating dynamic Pydantic models from schemas."""

    def __init__(self, repository: SchemaRepository):
        self.repository = repository

    def create_dynamic_model(self, model_name: str) -> BaseModel:
        """Loads a schema and creates a Pydantic model."""
        schema = self.repository.get_schema_by_name(model_name)
        return self._create_model_from_schema(model_name, schema['fields'])

    def _parse_type_definition(self, model_name: str, field_name: str, props: dict) -> Any:
        """Recursively parses a type definition from a schema properties dictionary."""
        if 'union' in props:
            union_types = []
            for type_props in props['union']:
                union_types.append(
                    self._parse_type_definition(model_name, field_name, type_props)
                )
            return Union[*union_types]

        field_type = props.get('type', 'str')
        validation = props.get('validation', {})

        if 'choices' in validation:
            return Literal[*validation['choices']]
        elif field_type == 'model':
            return self._create_model_from_schema(
                f"{model_name}_{field_name}", props['model']['fields']
            )
        elif field_type == 'list[model]':
            nested_model = self._create_model_from_schema(
                f"{model_name}_{field_name}_item", props['model']['fields']
            )
            return List[nested_model]
        elif field_type == 'list[str]':
            if 'pattern' in validation:
                return conlist(constr(pattern=validation['pattern']), min_length=1)
            else:
                return List[str]
        else:  # Basic type
            return TYPE_MAPPING.get(field_type, Any)

    def _create_model_from_schema(self, model_name: str, schema_fields: dict) -> BaseModel:
        """Recursively creates a Pydantic model from a schema dictionary."""
        fields = {}
        for field_name, field_props in schema_fields.items():
            field_type_hint = self._parse_type_definition(
                model_name, field_name, field_props
            )

            is_required = field_props.get('required', False)
            if not is_required:
                field_type_hint = Optional[field_type_hint]

            default = field_props.get('default', ... if is_required else None)
            validation = field_props.get('validation', {})
            field_args = {'default': default}

            # Apply validation only if it hasn't been handled by the type parser already
            if field_props.get('type') == 'str' and 'pattern' in validation:
                field_args['pattern'] = validation['pattern']
            if field_props.get('type') in ['int', 'float']:
                if 'ge' in validation:
                    field_args['ge'] = validation['ge']
                if 'le' in validation:
                    field_args['le'] = validation['le']

            if field_props.get('type') == 'str' and 'max_length' in validation:
                field_args['max_length'] = validation['max_length']

            fields[field_name] = (field_type_hint, Field(**field_args))

        return create_model(model_name, **fields)