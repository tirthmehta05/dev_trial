from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from ..services.model_service import ModelService
from ..services.config_service import ConfigService
from ..repositories.schema_repository import SchemaRepository
from ..exceptions.custom_exceptions import SchemaNotFoundError

router = APIRouter()

# --- Dependency Injection --- #
def get_schema_repository():
    return SchemaRepository()

def get_model_service(repo: SchemaRepository = Depends(get_schema_repository)):
    return ModelService(repo)

def get_config_service(repo: SchemaRepository = Depends(get_schema_repository)):
    return ConfigService(repo)

# --- --- #

@router.post("/generate-config/{model_name}")
async def generate_config_endpoint(
    request: Request,
    model_name: str,
    model_service: ModelService = Depends(get_model_service),
    config_service: ConfigService = Depends(get_config_service),
):
    """
    Receives form data, validates it, and returns the generated YAML config.
    """
    try:
        DynamicModel = model_service.create_dynamic_model(model_name)
        json_data = await request.json()
        validated_data = DynamicModel(**json_data)
        yaml_config = config_service.generate_config(model_name, validated_data)
        return PlainTextResponse(content=yaml_config)

    except SchemaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        # Pydantic validation errors
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        # Catch-all for other exceptions
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
