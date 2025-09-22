import yaml
from pathlib import Path
from ..exceptions.custom_exceptions import SchemaNotFoundError

class SchemaRepository:
    """Handles reading schema files from the data_models directory."""

    def __init__(self, base_path: str = "data_models"):
        self.base_path = Path(base_path)

    def get_schema_by_name(self, model_name: str) -> dict:
        """
        Finds and loads a YAML schema file by its name.

        Args:
            model_name: The name of the model (and the YAML file).

        Returns:
            A dictionary containing the loaded schema.

        Raises:
            SchemaNotFoundError: If the schema file cannot be found.
        """
        schema_path = self.base_path / f"{model_name}.yaml"
        if not schema_path.exists():
            raise SchemaNotFoundError(f"Schema file not found for model: {model_name}")

        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
