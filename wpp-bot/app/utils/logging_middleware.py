import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from typing import Callable, Dict, Optional, List, Union, Any

from app.services.logger import format_whatsapp_message
from app.utils.metrics import metrics

# Configurar logger
logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para log detalhado de requisições HTTP
    """
    def __init__(
        self, 
        app, 
        exclude_paths: Optional[List[str]] = None,
        log_request_headers: bool = False,
        log_response_headers: bool = False,
        log_request_body: bool = False
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
        self.log_request_headers = log_request_headers
        self.log_response_headers = log_response_headers
        self.log_request_body = log_request_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Gerar ID único para a requisição
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Verificar se devemos ignorar o logging para este caminho
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Iniciar tempo de processamento
        start_time = time.time()
        
        # Coletar informações da requisição
        method = request.method
        path = request.url.path
        client = f"{request.client.host}:{request.client.port}" if request.client else "unknown"
        
        # Log de início da requisição
        logger.info(format_whatsapp_message(
            "info", 
            f"→ {method} {path} (ID: {request_id[:8]})"
        ))
        
        # Coletar cabeçalhos da requisição se habilitado
        if self.log_request_headers:
            logger.debug(f"Headers da requisição: {dict(request.headers)}")
        
        # Coletar corpo da requisição se habilitado
        if self.log_request_body and method in ["POST", "PUT", "PATCH"]:
            try:
                # Fazer uma cópia do corpo para não consumir o stream
                body = await request.body()
                request._body = body  # Preservar corpo para processamento futuro
                
                # Tentar decodificar como JSON ou texto
                try:
                    import json
                    body_str = json.loads(body)
                    if isinstance(body_str, dict) and "password" in body_str:
                        body_str["password"] = "********"  # Ocultar senhas
                    logger.debug(f"Corpo da requisição: {body_str}")
                except:
                    if len(body) > 500:
                        logger.debug(f"Corpo da requisição (truncado): {body[:500]}...")
                    else:
                        logger.debug(f"Corpo da requisição: {body}")
            except Exception as e:
                logger.warning(f"Não foi possível logar o corpo da requisição: {str(e)}")
        
        # Processar a requisição
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Calcular tempo de resposta
            process_time = time.time() - start_time
            
            # Determinar o símbolo de status baseado no código de status
            if status_code < 200:
                status_symbol = "●"  # Informativo
            elif status_code < 300:
                status_symbol = "✓"  # Sucesso
            elif status_code < 400:
                status_symbol = "↪"  # Redirecionamento
            elif status_code < 500:
                status_symbol = "⚠"  # Erro do cliente
            else:
                status_symbol = "✗"  # Erro do servidor
            
            # Log de conclusão da requisição
            log_message = f"{status_symbol} {method} {path} → {status_code} em {process_time:.3f}s"
            
            if status_code >= 500:
                logger.error(format_whatsapp_message("error", log_message))
            elif status_code >= 400:
                logger.warning(format_whatsapp_message("warning", log_message))
            else:
                logger.info(format_whatsapp_message("success", log_message))
            
            # Coletar cabeçalhos da resposta se habilitado
            if self.log_response_headers:
                logger.debug(f"Headers da resposta: {dict(response.headers)}")
            
            # Atualizar métricas
            metrics.track_endpoint(path, process_time, status_code)
            
            return response
            
        except Exception as exc:
            # Calcular tempo até o erro
            process_time = time.time() - start_time
            
            # Log detalhado do erro
            logger.error(format_whatsapp_message(
                "error", 
                f"✗ {method} {path} → Erro em {process_time:.3f}s: {str(exc)}"
            ))
            
            # Registrar exceção com traceback
            logger.exception("Detalhes do erro:")
            
            # Atualizar métricas
            metrics.track_endpoint(path, process_time, 500, str(exc))
            
            # Re-lançar a exceção para o gerenciador de exceções do FastAPI
            raise

# Função para adicionar o middleware à aplicação FastAPI
def add_logging_middleware(app, **kwargs):
    """
    Adicionar middleware de logging à aplicação FastAPI
    """
    app.add_middleware(LoggingMiddleware, **kwargs)
    logger.info("Middleware de logging adicionado")