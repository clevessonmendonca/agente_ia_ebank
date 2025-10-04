"""
Configuração de logs para o Uvicorn
Coloque este arquivo em config/uvicorn_logging.py
"""
import logging
from pathlib import Path

from config.settings import settings

# Configuração para o Uvicorn
UVICORN_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s [%(asctime)s] %(message)s",
            "datefmt": "%H:%M:%S",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s [%(asctime)s] %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%H:%M:%S",
            "use_colors": True,
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
        "uvicorn": {
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False
        },
        "uvicorn.error": {
            "level": "WARNING",
            "propagate": True
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "WARNING",
            "propagate": False
        },
    }
}


class UvicornFilter(logging.Filter):
    """
    Filtra logs do Uvicorn para reduzir ruído
    """
    def __init__(self, exclude_paths=None):
        super().__init__()
        self.exclude_paths = exclude_paths or [
            "/health", "/metrics", "/favicon.ico", "/docs", "/openapi.json"
        ]
        self._startup_logged = False
        
    def filter(self, record):
        # Filtrar logs de acesso para paths excluídos
        if hasattr(record, "scope"):
            path = record.scope.get("path", "")
            if any(path.startswith(excluded) for excluded in self.exclude_paths):
                return False
        
        # Filtrar mensagens repetitivas
        if hasattr(record, "msg") and isinstance(record.msg, str):
            # Mostrar mensagens de inicialização apenas uma vez
            if "Uvicorn running on" in record.msg or "Reloading" in record.msg:
                if self._startup_logged:
                    return False
                self._startup_logged = True
        
        return True


def setup_uvicorn_logging():
    """
    Configura logging personalizado para o Uvicorn
    """
    # Configurar filtro personalizado
    uvicorn_filter = UvicornFilter()
    
    # Adicionar o filtro aos loggers do Uvicorn
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logging.getLogger(logger_name).addFilter(uvicorn_filter)
    
    return UVICORN_LOGGING