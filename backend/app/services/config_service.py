import yaml
from pydantic import BaseModel
from ..repositories.schema_repository import SchemaRepository

class ConfigService:
    """Service for generating YAML configurations."""

    def __init__(self, repository: SchemaRepository):
        self.repository = repository

    def generate_config(self, model_name: str, data: BaseModel) -> str:
        """
        Generates a YAML configuration string from a Pydantic model instance.

        Args:
            model_name: The name of the data model schema.
            data: The validated Pydantic model instance.

        Returns:
            A string containing the generated YAML.
        """
        # Load the schema to check for a custom root_key
        schema = self.repository.get_schema_by_name(model_name)
        root_key = schema.get('root_key', model_name)

        # Convert the Pydantic model to a dictionary
        config_dict = data.model_dump(exclude_unset=True)

        # Wrap the data with the correct root key
        final_config = {root_key: config_dict}

        return yaml.dump(final_config, sort_keys=False)