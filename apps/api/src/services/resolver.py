from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.resolver import ResolverRepository
from src.schemas.resolver import ProductoPublico, ProspectoPublico, ResolverResponse


class ResolverService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ResolverRepository(session)

    async def resolver(self, gtin: str) -> ResolverResponse:
        resultado = await self.repo.resolver_gtin(gtin)

        if "error" in resultado:
            return ResolverResponse(error=resultado["error"])

        return ResolverResponse(
            producto=ProductoPublico.model_validate(resultado["producto"]),
            prospectos=[
                ProspectoPublico(tipo_audiencia=p.tipo_audiencia, url_archivo=p.url_archivo)
                for p in resultado["prospectos"]
            ],
        )
