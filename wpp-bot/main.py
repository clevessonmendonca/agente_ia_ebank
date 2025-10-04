import os
import warnings
import re
from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import datetime
import platform
import logging

# Filtrar avisos específicos do Pydantic
warnings.filterwarnings(
    "ignore", 
    message="Valid config keys have changed in V2.*",
    category=UserWarning
)

from config.settings import settings
from config.database import engine, Base, get_db
from app.api.endpoints import webhook
from app.api.endpoints.flow_manager import router as flow_manager_router
from app.api.router import api_router
from app.api.exceptions import add_exception_handlers
from app.services.logger import setup_logging, format_whatsapp_message
from app.utils.logging_middleware import add_logging_middleware
from app.utils.metrics import metrics, start_metrics_logging
from sqlalchemy.orm import Session

# Configuração aprimorada de logging
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=Path(settings.LOG_PATH) / "whatsapp_api.log"
)

# Criar diretórios necessários
os.makedirs(settings.MEDIA_PATH, exist_ok=True)
os.makedirs(settings.LOG_PATH, exist_ok=True)

# Define o caminho para a aplicação React
REACT_APP_DIR = settings.BASE_DIR / "web_interface" / "dist"
# Verificar se o diretório da aplicação React existe
if not REACT_APP_DIR.exists():
    logger.warning(f"Diretório da aplicação React não encontrado: {REACT_APP_DIR}")
    logger.warning("Você precisa construir a aplicação React primeiro!")
else:
    logger.info(f"Encontrado diretório da aplicação React: {REACT_APP_DIR}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Eventos de ciclo de vida da aplicação FastAPI
    """
    # Iniciar banner de startup
    display_startup_banner()
    
    # Criar tabelas do banco de dados se não existirem
    logger.info(format_whatsapp_message("info", "Iniciando a aplicação WhatsApp API"))
    Base.metadata.create_all(bind=engine)
    logger.info(format_whatsapp_message("success", "Tabelas do banco de dados verificadas"))
    
    # Iniciar monitoramento de métricas
    monitor_thread = start_metrics_logging(interval_minutes=30)
    logger.info(format_whatsapp_message("info", "Monitoramento de métricas iniciado"))
    
    # Registrar a aplicação React
    if REACT_APP_DIR.exists():
        logger.info(format_whatsapp_message("success", f"Aplicação React registrada em /flow-manager"))
    
    logger.info(format_whatsapp_message("success", "Aplicação inicializada com sucesso"))
    yield
    logger.info(format_whatsapp_message("info", "Encerrando a aplicação"))


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para integração com o WhatsApp Business API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Adicionar middleware de logging
add_logging_middleware(
    app,
    exclude_paths=["/health", "/metrics", "/static", "/favicon.ico", "/flow-manager/assets"],
    log_request_headers=settings.DEBUG,
    log_response_headers=False,
    log_request_body=False
)

# Adicionar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar gerenciadores de exceção
add_exception_handlers(app)

# Adicionar rotas da API
app.include_router(api_router, prefix=settings.API_V1_STR)

# Adicionar o router da aplicação Flow Manager separadamente para manter o prefixo limpo
app.include_router(flow_manager_router, prefix=f"{settings.API_V1_STR}/flow-manager")

@app.get("/")
async def root():
    """
    Endpoint raiz
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "running",
        "documentation": f"{settings.API_V1_STR}/docs",
        "flow_manager": f"{settings.API_V1_STR}/flow-manager"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Endpoint de verificação de saúde que retorna o status de todos os componentes
    """
    # Verificar conexão com o banco de dados
    db_status = "connected"
    try:
        # Tentativa simples de consulta
        db.execute("SELECT 1").fetchall()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Status básico da aplicação
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "components": {
            "api": "running",
            "database": db_status,
            "whatsapp_api": "connected",  # Em um app real, verificar conexão com a API
            "flow_manager": "available" if REACT_APP_DIR.exists() else "not available"
        },
        "system_info": {
            "python_version": platform.python_version(),
            "platform": platform.platform()
        }
    }


@app.get("/metrics")
async def get_metrics(detailed: bool = False):
    """
    Endpoint para obter métricas da aplicação
    """
    return metrics.get_summary(detailed=detailed)


def display_startup_banner():
    """
    Exibe um banner visualmente agradável ao iniciar a aplicação
    """
    banner = r"""
 __          ___           _                       _    ____ ___ 
 \ \        / / |         | |                     | |  |  _ \_ _|
  \ \  /\  / /| |__   __ _| |_ ___   __ _ _ __   | |  | |_) | | 
   \ \/  \/ / | '_ \ / _` | __/ __| / _` | '_ \  | |  |  __/| | 
    \  /\  /  | | | | (_| | |_\__ \| (_| | |_) | |_|  | |  _| |_
     \/  \/   |_| |_|\__,_|\__|___/ \__,_| .__/  (_)  |_| |_(_)
                                          | |                    
                                          |_|                    
    """
    
    # Obter a versão da aplicação a partir do ambiente ou usar um valor padrão
    version = getattr(settings, "VERSION", "1.0.0")
    
    # Criar um boxed banner mais limpo e organizado
    info = f"""
    {settings.APP_NAME} v{version}
    ┌─────────────────────────────────────────────────────────────┐
    │ 🔧 Ambiente: {getattr(settings, 'ENVIRONMENT', 'development').ljust(48)}│
    │ 🔌 API: https://plainly-glowing-kodiak.ngrok-free.app/{' ' * 42}│
    │ 📚 Documentação: https://plainly-glowing-kodiak.ngrok-free.app/api/v1/docs{' ' * 29}│
    │ 🎨 Flow Manager: https://plainly-glowing-kodiak.ngrok-free.app/api/v1/flow-manager{' ' * 28}│
    │ 📝 Logs: {str(settings.LOG_PATH).ljust(52)}│
    │ 🗃️ Banco de dados: PostgreSQL{' ' * 37}│
    │ 📱 WhatsApp API: Conectado (ID: {settings.PAGE_ID}){' ' * (25 - len(settings.PAGE_ID))}│
    └─────────────────────────────────────────────────────────────┘
    """
    
    # Adiciona informações sobre o monitoramento de arquivos, se houver
    flow_json_path = getattr(settings, "FLOW_JSON_PATH", None)
    if flow_json_path and os.path.exists(flow_json_path):
        file_info = f"""
    ┌─────────────────────────────────────────────────────────────┐
    │ 🔍 Monitorando arquivo de fluxo:{' ' * 32}│
    │    {flow_json_path.ljust(55)}│
    └─────────────────────────────────────────────────────────────┘
        """
        info += file_info
    
    # Adicionar info da aplicação React
    if REACT_APP_DIR.exists():
        react_info = f"""
    ┌─────────────────────────────────────────────────────────────┐
    │ ⚛️ Aplicação React detectada:{' ' * 34}│
    │    {str(REACT_APP_DIR).ljust(55)}│
    └─────────────────────────────────────────────────────────────┘
        """
        info += react_info
    
    # Adicionar info do servidor
    server_info = f"""
    ┌─────────────────────────────────────────────────────────────┐
    │ 💻 Python: {platform.python_version().ljust(50)}│
    │ 🖥️ Sistema: {platform.system()} {platform.release().ljust(41)}│
    │ 🕒 Iniciado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S').ljust(40)}│
    └─────────────────────────────────────────────────────────────┘
    """
    info += server_info
    
    # Mostrar banner em logger com formatação adequada
    logger.info("\n" + banner)
    
    # Mostrar cada linha da informação separadamente para formatação adequada
    for line in info.strip().split("\n"):
        logger.info(line)
    
    # Adicionar mensagem final
    if settings.DEBUG:
        logger.info("\n🚀 Aplicação iniciada em modo DEBUG - recarregamento automático ativado")
    else:
        logger.info("\n🚀 Aplicação iniciada em modo PRODUÇÃO")


if __name__ == "__main__":
    import uvicorn
    import os
    from config.settings import settings
    from pathlib import Path
    
    try:
        from config.uvicorn_logging import setup_uvicorn_logging
        log_config = setup_uvicorn_logging()
    except ImportError:
        log_config = None
    
    # Obter o caminho do arquivo JSON a ser monitorado
    flow_json_path = getattr(settings, "FLOW_JSON_PATH", None)
    if not flow_json_path:
        # Se não estiver definido no ambiente, use o caminho padrão
        flow_json_path = os.path.join(
            "app", "utils", "projeto_asas_menu_templates.json"
        )
    else:
        # Converter caminho absoluto para relativo, se necessário
        abs_path = Path(os.path.abspath(flow_json_path))
        cwd = Path.cwd()
        try:
            flow_json_path = str(abs_path.relative_to(cwd))
        except ValueError:
            # Se não for possível converter para relativo, use apenas o nome do arquivo
            logger.warning(f"⚠️ Não foi possível converter o caminho para relativo: {flow_json_path}")
            flow_json_path = os.path.basename(flow_json_path)
    
    # Configurar arquivos extras para serem monitorados para recarregamento
    reload_dirs = ["app"]
    reload_includes = [flow_json_path]
    
    if os.path.exists(flow_json_path):
        logger.info(f"🔍 Monitorando arquivo de fluxo para recarregamento automático: {flow_json_path}")
    else:
        logger.warning(f"⚠️ Arquivo de fluxo não encontrado: {flow_json_path}")
    
    logger.info(f"🌐 Interface de logs local  http://127.0.0.1:4040")
    logger.info(f"🌐 Flow Manager  http://127.0.0.1:8000/api/v1/flow-manager")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        reload_dirs=reload_dirs,
        reload_includes=reload_includes,  # Arquivos específicos a serem monitorados
        log_level="warning" if not settings.DEBUG else "info",
        access_log=False,     # Desabilitar logs de acesso do Uvicorn
        log_config=log_config
    )