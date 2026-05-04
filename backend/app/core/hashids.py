"""Hashids helper for generating unique_hash values per model type."""

from hashids import Hashids

from app.config import settings


def encode_id(model_name: str, id: int) -> str:
    salt = f"{settings.secret_key}:{model_name}"
    h = Hashids(salt=salt, min_length=8)
    return h.encode(id)
