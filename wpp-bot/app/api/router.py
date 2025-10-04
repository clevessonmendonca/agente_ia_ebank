from fastapi import APIRouter
from app.api.endpoints import webhook
from app.api.endpoints.flow_manager import router as flow_manager_router  # Importar o novo router
from app.api.endpoints.verificacao_ia import router as verificacao_ia_router  # Importar o router de verificação IA

api_router = APIRouter()
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
api_router.include_router(flow_manager_router, prefix="/flow-manager", tags=["flow-manager"])  # Adicionar o novo router
api_router.include_router(verificacao_ia_router, prefix="/api/v1", tags=["verificacao-ia"])  # Adicionar o router de verificação IA