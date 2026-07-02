from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.deps import require_internal_token
from src.schemas.resolver import ResolverResponse
from src.services.resolver import ResolverService

router = APIRouter(
    prefix="/api/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_token)],
)


@router.get("/prospectos/by-gtin/{gtin}", response_model=ResolverResponse)
async def resolver_por_gtin(
    gtin: Annotated[str, Path(pattern=r"^\d{14}$")],
    session: AsyncSession = Depends(get_db),
) -> ResolverResponse:
    service = ResolverService(session)
    return await service.resolver(gtin)
