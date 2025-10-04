import logging
import re
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import traceback
import inspect
import os

# Definições de estilo ANSI (cores e formatação)
class Style:
    # Cores de texto
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Cores de fundo
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Estilos de texto
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Resetar estilo
    RESET = "\033[0m"
    
    # Estilos compostos para níveis de log
    DEBUG_STYLE = f"{BRIGHT_BLACK}"
    INFO_STYLE = f"{BRIGHT_BLUE}"
    WARNING_STYLE = f"{YELLOW}"
    ERROR_STYLE = f"{RED}"
    CRITICAL_STYLE = f"{BOLD}{BG_RED}{WHITE}"
    
    @staticmethod
    def apply(text: str, style: str) -> str:
        """Aplica estilo a um texto e garante reset no final"""
        return f"{style}{text}{Style.RESET}"

# Classe para formatação de logs bonitos
class PrettyLogFormatter(logging.Formatter):
    """
    Formatador personalizado que cria logs mais legíveis e coloridos
    """
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, colorize=True):
        super().__init__(fmt, datefmt, style, validate)
        self.colorize = colorize
        
        # Emojis para níveis de log
        self.level_emojis = {
            logging.DEBUG: "🔍",
            logging.INFO: "ℹ️",
            logging.WARNING: "⚠️",
            logging.ERROR: "❌",
            logging.CRITICAL: "💥"
        }
        
        # Estilos para níveis de log
        self.level_styles = {
            logging.DEBUG: Style.DEBUG_STYLE,
            logging.INFO: Style.INFO_STYLE,
            logging.WARNING: Style.WARNING_STYLE,
            logging.ERROR: Style.ERROR_STYLE,
            logging.CRITICAL: Style.CRITICAL_STYLE
        }
    
    def format(self, record):
        """Formatar registro de log com estilo melhorado"""
        # Formatar tempo
        record.asctime = self.formatTime(record, self.datefmt)
        
        # Determinar emoji e estilo baseado no nível
        level_emoji = self.level_emojis.get(record.levelno, "🔹")
        level_style = self.level_styles.get(record.levelno, Style.RESET)
        
        # Nome da classe/módulo mais curto
        try:
            if "." in record.name:
                parts = record.name.split(".")
                record.shortname = parts[-1]
            else:
                record.shortname = record.name
        except:
            record.shortname = record.name
        
        # Obter informações da origem do log
        file_info = f"{record.filename}:{record.lineno}" if hasattr(record, "filename") else ""
        
        # Formatação base da mensagem
        log_prefix = f"{level_emoji} [{record.asctime}] "
        
        if hasattr(record, "shortname") and record.shortname:
            module_part = f"{record.shortname:<12} "
        else:
            module_part = ""
        
        # Formatar mensagem principal
        message = str(record.getMessage())
        
        # Detectar e formatar JSON na mensagem
        message = self._format_json_in_message(message)
        
        # Aplicar cores e estilos se habilitado
        if self.colorize:
            level_name = f"{Style.apply(record.levelname.ljust(8), level_style)}"
            module_part = Style.apply(module_part, Style.BRIGHT_MAGENTA)
            
            # Destacar partes importantes na mensagem
            message = self._highlight_message(message, level_style)
        else:
            level_name = record.levelname.ljust(8)
        
        # Montar mensagem final
        formatted_message = f"{log_prefix}{level_name} {module_part}{message}"
        
        # Adicionar informações de exceção se presentes
        if record.exc_info:
            # Formatar traceback
            tb_text = self._format_traceback(record.exc_info)
            formatted_message = f"{formatted_message}\n{tb_text}"
        
        return formatted_message
    
    def _highlight_message(self, message: str, level_style: str) -> str:
        """Realça partes importantes da mensagem"""
        # Realçar URLs
        message = re.sub(
            r'(https?://[^\s]+)', 
            Style.apply(r'\1', Style.UNDERLINE + Style.CYAN), 
            message
        )
        
        # Realçar valores entre aspas
        message = re.sub(
            r'"([^"]*)"', 
            Style.apply(r'"\1"', Style.BRIGHT_CYAN), 
            message
        )
        
        # Realçar números
        message = re.sub(
            r'\b(\d+(\.\d+)?)\b', 
            Style.apply(r'\1', Style.BRIGHT_GREEN), 
            message
        )
        
        # Realçar palavras-chave de sucesso/erro
        success_words = ["success", "successful", "succeeded", "completed", "ok", "done"]
        error_words = ["error", "failed", "failure", "exception", "invalid", "rejected"]
        
        for word in success_words:
            message = re.sub(
                rf'\b({word})\b', 
                Style.apply(r'\1', Style.BRIGHT_GREEN), 
                message, 
                flags=re.IGNORECASE
            )
            
        for word in error_words:
            message = re.sub(
                rf'\b({word})\b', 
                Style.apply(r'\1', Style.BRIGHT_RED), 
                message, 
                flags=re.IGNORECASE
            )
        
        return message
    
    def _format_json_in_message(self, message: str) -> str:
        """Detecta e formata JSON dentro da mensagem"""
        # Procurar por conteúdo que parece ser JSON entre chaves
        json_pattern = r'(\{.*\})'
        match = re.search(json_pattern, message)
        
        if match:
            try:
                # Tentar analisar como JSON
                json_str = match.group(1)
                json_obj = json.loads(json_str)
                
                # Se for JSON, substituir pelo formato formatado com indentação
                pretty_json = json.dumps(json_obj, indent=2, ensure_ascii=False)
                # Adicionar quebras de linha para melhor legibilidade nos logs
                formatted_json = f"\n{pretty_json}"
                message = message.replace(json_str, formatted_json)
            except json.JSONDecodeError:
                # Não é JSON válido, manter como está
                pass
        
        return message
    
    def _format_traceback(self, exc_info) -> str:
        """Formata traceback de uma maneira mais legível"""
        exc_type, exc_value, exc_tb = exc_info
        
        # Formatar traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        
        # Aplicar estilo se habilitado
        if self.colorize:
            # Destacar nome da exceção
            tb_lines[0] = Style.apply(tb_lines[0], Style.BOLD + Style.RED)
            
            # Destacar nomes de arquivos e linhas no traceback
            for i in range(1, len(tb_lines)):
                # Destacar linhas "File ..."
                tb_lines[i] = re.sub(
                    r'(File ".*", line \d+)',
                    Style.apply(r'\1', Style.BRIGHT_CYAN),
                    tb_lines[i]
                )
                
                # Destacar nomes de funções
                tb_lines[i] = re.sub(
                    r'(in [a-zA-Z0-9_]+)',
                    Style.apply(r'\1', Style.BRIGHT_YELLOW),
                    tb_lines[i]
                )
        
        return "".join(tb_lines)


# Função para configurar o logger com formatação bonita
def setup_pretty_logging(logger_name=None, level=logging.INFO, colorize=True):
    """
    Configura um logger com formatação bonita e colorida
    
    Args:
        logger_name: Nome do logger (None para logger raiz)
        level: Nível de log
        colorize: Se True, aplica cores nos logs
    
    Returns:
        O logger configurado
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Limpar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Criar handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Criar formatador bonito
    formatter = PrettyLogFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        colorize=colorize
    )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Função para obter informações do chamador
def get_caller_info():
    """Obter informações sobre quem chamou esta função"""
    frame = inspect.currentframe().f_back.f_back  # Pular dois frames para obter o chamador real
    filename = os.path.basename(frame.f_code.co_filename)
    line_number = frame.f_lineno
    function_name = frame.f_code.co_name
    return filename, line_number, function_name


# Funções úteis para logs formatados
def log_divider(logger, message=None, char="=", length=80):
    """Imprime um divisor no log para separar seções"""
    if message:
        # Calcular quantidade de caracteres em cada lado
        message = f" {message} "
        side_length = (length - len(message)) // 2
        divider = char * side_length + message + char * side_length
        
        # Ajustar comprimento exato
        if len(divider) < length:
            divider += char * (length - len(divider))
    else:
        divider = char * length
    
    logger.info(divider)


def log_section(logger, title, level=logging.INFO):
    """Imprime título de seção destacado no log"""
    filename, line, function = get_caller_info()
    section_header = f"==== {title.upper()} "
    section_header = section_header.ljust(80, "=")
    
    logger.log(level, section_header)


def log_dict(logger, data, title=None, level=logging.INFO):
    """Imprime dicionário formatado como JSON no log"""
    if title:
        logger.log(level, f"{title}:")
    
    if isinstance(data, dict):
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        for line in formatted.split("\n"):
            logger.log(level, f"  {line}")
    else:
        logger.log(level, f"  {data}")


def log_step(logger, step, description=None, level=logging.INFO):
    """Imprime um passo em formato numerado no log"""
    if description:
        logger.log(level, f"[{step}] {description}")
    else:
        logger.log(level, f"[{step}]")


def log_success(logger, message):
    """Imprime mensagem de sucesso"""
    logger.info(f"✅ {message}")


def log_failure(logger, message):
    """Imprime mensagem de falha"""
    logger.error(f"❌ {message}")


def log_warning(logger, message):
    """Imprime mensagem de aviso"""
    logger.warning(f"⚠️ {message}")


def log_start(logger, operation):
    """Imprime início de operação"""
    logger.info(f"▶️ Iniciando: {operation}")


def log_end(logger, operation, success=True):
    """Imprime fim de operação"""
    if success:
        logger.info(f"✅ Concluído: {operation}")
    else:
        logger.warning(f"⚠️ Finalizado com problemas: {operation}")