from fastapi import APIRouter

from app import database
from app.models.schemas import AppStatus, Profile
from app.services import llm_provider

router = APIRouter(prefix="/api", tags=["perfil"])


@router.get("/status", response_model=AppStatus)
def status() -> AppStatus:
    return llm_provider.get_status()


@router.get("/profile", response_model=Profile)
def read_profile() -> Profile:
    return database.get_profile()


@router.put("/profile", response_model=Profile)
def update_profile(profile: Profile) -> Profile:
    return database.save_profile(profile)


@router.post("/profile/reset", response_model=Profile)
def reset_profile() -> Profile:
    """Restaura o perfil inicial fornecido (descarta edições do perfil; candidaturas salvas não são afetadas)."""
    return database.reset_profile()
