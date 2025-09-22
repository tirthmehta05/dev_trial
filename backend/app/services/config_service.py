import yaml
from pydantic import BaseModel

class ConfigService:
    """Service for generating YAML configurations."""

    def generate_config(self, model_name: str, data: BaseModel) -> str:
        """
        Generates a YAML configuration string from a Pydantic model instance.

        Args:
            model_name: The root key for the YAML configuration.
            data: The validated Pydantic model instance.

        Returns:
            A string containing the generated YAML.
        """
        config_data = {model_name: data.model_dump(exclude_unset=True)}
        return yaml.dump(config_data, sort_keys=False)
