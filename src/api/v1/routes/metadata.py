from fastapi import APIRouter

from src.api.v1.schemas.metadata import MetadataResponse

router = APIRouter()


@router.get("/metadata", response_model=MetadataResponse)
async def get_metadata() -> MetadataResponse:
    return MetadataResponse(
        version="0.1.0",
    )
