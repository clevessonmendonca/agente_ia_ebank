import logging
from pathlib import Path
from typing import List

from config.settings import settings

# Configurações básicas do Uvicorn
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s [%(asctime)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s [%(asctime)s] %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(Path(settings.LOG_PATH) / "uvicorn.log"),
            "maxBytes": 10_000_000,  # ~10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default", "file"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access", "file"], "level": "INFO", "propagate": False},
    },
}

# Classe para filtrar logs do Uvicorn
class UvicornFilter(logging.Filter):
    """
    Filtra mensagens de log do Uvicorn para reduzir ruído
    """
    def __init__(self, excluded_paths: List[str] = None):
        super().__init__()
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/favicon.ico"]
    
    def filter(self, record):
        # Filtrar logs de acesso para caminhos excluídos
        if hasattr(record, "scope"):
            path = record.scope.get("path", "")
            if any(path.startswith(excluded) for excluded in self.excluded_paths):
                return False
        
        # Filtrar mensagens específicas do Uvicorn para reduzir ruído
        if hasattr(record, "msg") and isinstance(record.msg, str):
            # Filtrar mensagens de recarregamento durante desenvolvimento
            if "Uvicorn running on" in record.msg or "Reloading" in record.msg:
                # Permitir estes apenas uma vez durante o startup
                if getattr(self, "_startup_logged", False):
                    return False
                self._startup_logged = True
        
        return True

# Função para adicionar o filtro aos loggers do Uvicorn
def configure_uvicorn_logging():
    """
    Configura logging personalizado para o Uvicorn
    """
    # Obter o logger do Uvicorn
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access = logging.getLogger("uvicorn.access")
    
    # Adicionar filtro personalizado
    uvicorn_filter = UvicornFilter()
    uvicorn_logger.addFilter(uvicorn_filter)
    uvicorn_access.addFilter(uvicorn_filter)
    
    # Reduzir o nível de log para módulos ruidosos
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    
    return log_config