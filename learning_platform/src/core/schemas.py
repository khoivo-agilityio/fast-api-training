"""Storage schemas (DTOs) — Pydantic v2."""

from pydantic import BaseModel, Field


class PresignedUrlRequest(BaseModel):
    """Request body for POST /users/me/avatar/presigned."""

    content_type: str = Field(
        description="MIME type of the file to upload (e.g. image/jpeg).",
        examples=["image/jpeg"],
    )

    model_config = {"json_schema_extra": {"example": {"content_type": "image/jpeg"}}}


class PresignedUrlResponse(BaseModel):
    """Presigned PUT URL returned to the client for direct S3 upload."""

    upload_url: str = Field(description="PUT this URL directly from the client.")
    object_key: str = Field(
        description="S3 object key — send this back in PATCH /users/me/avatar."
    )
    expires_in: int = Field(description="URL validity in seconds.")


class AvatarConfirmRequest(BaseModel):
    """Request body for PATCH /users/me/avatar."""

    object_key: str = Field(
        description="The object_key returned by POST /users/me/avatar/presigned."
    )

    model_config = {
        "json_schema_extra": {
            "example": {"object_key": "avatars/3fa85f64-5717-4562-b3fc-2c963f66afa6.jpg"}
        }
    }
