import logging
import coloredlogs
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console
from rich import pretty
from rich.theme import Theme
import os

from config.settings import settings

# Definir tema personalizado para mensagens coloridas
RICH_THEME = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "success": "bold green",
    "debug": "dim",
    "whatsapp.incoming": "bold green",
    "whatsapp.outgoing": "bold blue",
    "database.query": "dim magenta",
    "database.params": "dim",
})

# Configurações de formato para diferentes tipos de logs
LOG_FORMATS = {
    'default': "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    'simple': "%(message)s",
    'detailed': "[%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    'rich': "%(message)s"
}

# Filtros personalizados
class SQLAlchemyFilter(logging.Filter):
    def filter(self, record):
        # Filtra mensagens de SQL para não mostrar consultas em massa
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Ignora logs específicos para reduzir ruído
            if any(x in record.msg for x in ["SELECT pg_catalog.pg_class.relname", "show standard_conforming_strings"]):
                return False
            
            # Para consultas SQL, simplifica usando apenas a primeira linha
            if "SELECT" in record.msg and "\n" in record.msg:
                record.msg = record.msg.split("\n")[0] + " [...]"
                
        return True

class WhatsAppMessageFilter(logging.Filter):
    def filter(self, record):
        # Detecta e formata mensagens de WhatsApp
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            if "Recebida nova mensagem" in record.msg:
                record.levelname = "INCOMING"
                return True
            elif "Erro ao processar mensagem" in record.msg:
                record.levelname = "ERROR"
                return True
        return True

def setup_logging(
    log_level: str = settings.LOG_LEVEL, 
    log_file: Optional[Path] = None,
    console_output: bool = True
):
    """
    Configura o sistema de logging com formatação bonita para console e arquivo
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para o arquivo de log
        console_output: Se True, exibe logs no console
    """
    level = getattr(logging, log_level.upper())
    
    # Criar diretório de logs se não existir
    if log_file:
        log_dir = log_file.parent
        os.makedirs(log_dir, exist_ok=True)
    
    # Configuração básica de logging
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatador para logs de arquivo (detalhado)
    file_formatter = logging.Formatter(
        fmt=LOG_FORMATS['detailed'],
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Adicionar log para arquivo se especificado
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configurar saída do console com Rich ou ColoredLogs
    if console_output:
        # Usar RichHandler para formatação atraente no console
        console = Console(theme=RICH_THEME)
        pretty.install(console=console)
        
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_extra_lines=1,
            tracebacks_show_locals=False
        )
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)
    
    # Configuração específica para SQLAlchemy
    sql_logger = logging.getLogger('sqlalchemy.engine')
    sql_logger.setLevel(logging.WARNING)  # Defina como INFO para ver consultas SQL
    
    # Aplica filtros personalizados
    sql_filter = SQLAlchemyFilter()
    for handler in root_logger.handlers:
        handler.addFilter(sql_filter)
    
    # Configuração para o logger do WhatsApp
    whatsapp_logger = logging.getLogger('app.services.whatsapp')
    whatsapp_filter = WhatsAppMessageFilter()
    whatsapp_logger.addFilter(whatsapp_filter)
    
    return root_logger

# Formato bonito para mensagens de status do WhatsApp
def format_whatsapp_message(message_type, content):
    """
    Formata mensagens de status do WhatsApp para exibição mais bonita
    """
    symbols = {
        "success": "✅",
        "error": "❌", 
        "warning": "⚠️",
        "info": "ℹ️",
        "received": "📩",
        "sent": "📤",
        "processing": "⏳"
    }
    
    return f"{symbols.get(message_type, '•')} {content}"

# Função auxiliar para colorir logs manuais no console
def colorize(text, color='white'):
    """Colorize text for console output"""
    colors = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'reset': '\033[0m',
        'bold': '\033[1m'
    }
    
    if color not in colors:
        return text
    
    return f"{colors[color]}{text}{colors['reset']}"

# Inicializar o logger para a aplicação
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=Path(settings.LOG_PATH) / "whatsapp_api.log"
)