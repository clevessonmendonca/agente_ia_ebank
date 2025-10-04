import time
import threading
import functools
import statistics
from collections import defaultdict, deque
import logging
from typing import Dict, List, Callable, Any, Optional, Deque
from datetime import datetime, timedelta

# Configurar logger
logger = logging.getLogger("metrics")

class APIMetrics:
    """
    Classe para rastrear métricas de desempenho da API
    """
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._lock = threading.RLock()
        self.reset()
    
    def reset(self):
        """Reiniciar todas as métricas"""
        with self._lock:
            # Métricas para endpoints
            self.endpoints: Dict[str, Dict[str, Deque]] = defaultdict(
                lambda: {
                    'response_times': deque(maxlen=self.window_size),
                    'status_codes': deque(maxlen=self.window_size),
                    'errors': deque(maxlen=self.window_size)
                }
            )
            
            # Métricas para WhatsApp
            self.whatsapp = {
                'messages_sent': 0,
                'messages_received': 0,
                'api_errors': 0,
                'api_latency': deque(maxlen=self.window_size)
            }
            
            # Métricas para banco de dados
            self.database = {
                'queries': 0,
                'query_times': deque(maxlen=self.window_size),
                'errors': 0
            }
            
            # Métricas gerais
            self.start_time = time.time()
            self.requests = 0
            self.errors = 0
            self.last_reset = time.time()
    
    def track_endpoint(self, endpoint: str, response_time: float, status_code: int, 
                      error: Optional[str] = None):
        """Rastrear métricas de um endpoint"""
        with self._lock:
            self.endpoints[endpoint]['response_times'].append(response_time)
            self.endpoints[endpoint]['status_codes'].append(status_code)
            
            self.requests += 1
            if error:
                self.endpoints[endpoint]['errors'].append(error)
                self.errors += 1
    
    def track_whatsapp_message(self, direction: str, latency: Optional[float] = None, 
                              error: bool = False):
        """Rastrear métricas de mensagens do WhatsApp"""
        with self._lock:
            if direction == 'sent':
                self.whatsapp['messages_sent'] += 1
            elif direction == 'received':
                self.whatsapp['messages_received'] += 1
                
            if latency is not None:
                self.whatsapp['api_latency'].append(latency)
                
            if error:
                self.whatsapp['api_errors'] += 1
    
    def track_database_query(self, execution_time: float, error: bool = False):
        """Rastrear métricas de consultas ao banco de dados"""
        with self._lock:
            self.database['queries'] += 1
            self.database['query_times'].append(execution_time)
            
            if error:
                self.database['errors'] += 1
    
    def get_summary(self, detailed: bool = False) -> Dict[str, Any]:
        """Obter resumo das métricas coletadas"""
        with self._lock:
            uptime = time.time() - self.start_time
            uptime_str = str(timedelta(seconds=int(uptime)))
            
            summary = {
                "uptime": uptime_str,
                "requests": self.requests,
                "errors": self.errors,
                "error_rate": (self.errors / max(1, self.requests)) * 100,
                "whatsapp": {
                    "messages_sent": self.whatsapp['messages_sent'],
                    "messages_received": self.whatsapp['messages_received'],
                    "api_errors": self.whatsapp['api_errors']
                },
                "database": {
                    "total_queries": self.database['queries'],
                    "errors": self.database['errors']
                }
            }
            
            # Adicionar latência média da API do WhatsApp se houver dados
            if self.whatsapp['api_latency']:
                summary['whatsapp']['avg_latency'] = statistics.mean(self.whatsapp['api_latency'])
            
            # Adicionar tempo médio de consulta ao banco de dados se houver dados
            if self.database['query_times']:
                summary['database']['avg_query_time'] = statistics.mean(self.database['query_times'])
            
            # Adicionar detalhes de endpoints se solicitado
            if detailed and self.endpoints:
                endpoints_summary = {}
                for endpoint, data in self.endpoints.items():
                    if data['response_times']:
                        endpoints_summary[endpoint] = {
                            "requests": len(data['response_times']),
                            "avg_response_time": statistics.mean(data['response_times']),
                            "success_rate": (sum(1 for c in data['status_codes'] if c < 400) / 
                                          max(1, len(data['status_codes']))) * 100
                        }
                        # Adicionar mais estatísticas se houver dados suficientes
                        if len(data['response_times']) >= 5:
                            endpoints_summary[endpoint]["p95_response_time"] = statistics.quantiles(
                                data['response_times'], n=20
                            )[-1]  # 95th percentile
                
                summary["endpoints"] = endpoints_summary
            
            return summary
    
    def log_summary(self, interval_minutes: int = 60):
        """Registrar resumo de métricas nos logs periodicamente"""
        current_time = time.time()
        if current_time - self.last_reset >= (interval_minutes * 60):
            summary = self.get_summary()
            logger.info(f"🔍 Métricas da aplicação (últimas {interval_minutes} minutos):")
            logger.info(f"⏱️ Tempo de atividade: {summary['uptime']}")
            logger.info(f"📊 Solicitações: {summary['requests']} (Taxa de erro: {summary['error_rate']:.2f}%)")
            logger.info(f"💬 WhatsApp: {summary['whatsapp']['messages_sent']} enviadas, "
                       f"{summary['whatsapp']['messages_received']} recebidas")
            logger.info(f"🗄️ Banco de dados: {summary['database']['total_queries']} consultas")
            
            # Reiniciar contadores após o log
            self.reset()
            return True
        return False

# Criar instância global
metrics = APIMetrics()

# Decorator para rastrear métricas de endpoints
def track_endpoint_metrics(endpoint_name: Optional[str] = None):
    """Decorator para rastrear métricas de endpoints"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__
            error = None
            status_code = 200
            
            try:
                response = await func(*args, **kwargs)
                if hasattr(response, 'status_code'):
                    status_code = response.status_code
                return response
            except Exception as e:
                error = str(e)
                status_code = getattr(e, 'status_code', 500)
                raise
            finally:
                execution_time = time.time() - start_time
                metrics.track_endpoint(endpoint, execution_time, status_code, error)
        return wrapper
    return decorator

# Função para monitoramento periódico
def start_metrics_logging(interval_minutes: int = 60):
    """Iniciar monitoramento periódico de métricas"""
    def monitor_task():
        while True:
            metrics.log_summary(interval_minutes)
            time.sleep(60)  # Verificar a cada minuto
    
    thread = threading.Thread(target=monitor_task, daemon=True)
    thread.start()
    logger.info(f"Monitoramento de métricas iniciado (intervalo: {interval_minutes} minutos)")
    return thread