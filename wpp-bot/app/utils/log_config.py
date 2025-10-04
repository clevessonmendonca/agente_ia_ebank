import logging
import re
from typing import Dict, Any, List, Optional, Set

# Configuração para filtrar logs do SQLAlchemy
class SQLAlchemyFilter(logging.Filter):
    """
    Filtro personalizado para logs do SQLAlchemy que deixa as mensagens mais limpas
    """
    
    def __init__(self):
        super().__init__()
        # Padrões de mensagens para ignorar completamente
        self.ignore_patterns = [
            r"SELECT pg_catalog\.pg_class\.relname",
            r"show standard_conforming_strings",
            r"select current_schema()",
            r"SELECT pg_catalog\.version\(\)",
            r"BEGIN \(implicit\)",
        ]
        
        # Cache de mensagens já processadas para evitar duplicações
        self.seen_messages: Set[str] = set()
        
        # Contador para limitar quantidade de logs similares
        self.log_counts: Dict[str, int] = {}
        
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'msg') or not isinstance(record.msg, str):
            return True
            
        msg = record.msg
        
        # Ignorar mensagens que correspondem aos padrões
        for pattern in self.ignore_patterns:
            if re.search(pattern, msg):
                return False
                
        # Simplificar consultas SQL
        if "[SQL]" in msg or "SELECT" in msg or "INSERT" in msg or "UPDATE" in msg or "DELETE" in msg:
            # Simplificar consultas longas e multi-linha
            if "\n" in msg:
                first_line = msg.split("\n")[0]
                if len(first_line) > 80:
                    first_line = first_line[:77] + "..."
                
                # Evitar mensagens duplicadas para a mesma consulta
                msg_key = first_line
                if msg_key in self.seen_messages:
                    return False
                    
                self.seen_messages.add(msg_key)
                record.msg = first_line + " [...]"
                
            # Para consultas menores, apenas limite o tamanho
            elif len(msg) > 80:
                record.msg = msg[:77] + "..."
                
        # Simplificar mensagens de parâmetros SQL
        if "parameters" in msg.lower():
            # Limitar tamanho das mensagens de parâmetros
            if len(msg) > 100:
                record.msg = msg[:97] + "..."
                
        return True

# Função para ser chamada no arquivo main.py
def setup_clean_logs():
    """
    Configura logs limpos para a aplicação WhatsApp API
    """
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remover handlers existentes para evitar duplicação
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Criar console handler com formatação bonita
    console_format = "%(asctime)s [%(levelname)s] %(message)s"
    console_date_format = "%H:%M:%S"
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(fmt=console_format, datefmt=console_date_format)
    )
    
    # Adicionar filtro para logs SQL
    sql_filter = SQLAlchemyFilter()
    console_handler.addFilter(sql_filter)
    
    root_logger.addHandler(console_handler)
    
    # Reduzir verbosidade dos loggers SQLAlchemy
    logging.getLogger('sqlalchemy.engine.base').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING) 
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)
    
    # Configurar logger da aplicação
    app_logger = logging.getLogger('whatsapp_api')
    app_logger.setLevel(logging.INFO)
    
    return app_logger
