#!/usr/bin/env python3
"""
Monitor de Logs em Tempo Real para WhatsApp API

Este script monitora os arquivos de log em tempo real e apresenta estatísticas
e visualizações para ajudar no diagnóstico de problemas.

Uso:
    python log_monitor.py [opções]

Opções:
    --logs-dir LOG_DIR    Diretório de logs (padrão: ./logs)
    --filter PATTERN      Filtrar logs por padrão
    --level LEVEL         Filtrar por nível mínimo (DEBUG, INFO, etc.)
    --follow, -f          Seguir logs em tempo real (como tail -f)
    --stats, -s           Mostrar estatísticas em tempo real
    --interval SECONDS    Intervalo de atualização (padrão: 2.0)
    --dashboard, -d       Executar painel interativo (requer rich)
"""

import os
import sys
import time
import re
import argparse
import signal
from datetime import datetime, timedelta
from collections import defaultdict, Counter, deque
import threading
from pathlib import Path
import glob
from typing import Dict, List, Any, Optional, Tuple, Set, Callable

# Tentar importar bibliotecas opcionais
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich import print as rprint
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Constantes
LOG_PATTERN = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+\[(\w+)\]\s+([^:]+):\s+(.*)'
)
WHATSAPP_PATTERN = re.compile(r'(✓|❌|⚠️|ℹ️|→)\s+(.*)')
ERROR_KEYWORDS = ['error', 'exception', 'fail', 'failed', 'traceback', 'erro']
WARNING_KEYWORDS = ['warning', 'warn', 'aviso', 'atenção']

# Classe para estatísticas de logs
class LogStats:
    def __init__(self, window_size=1000):
        self.total_logs = 0
        self.logs_by_level = Counter()
        self.logs_by_module = Counter()
        self.errors = []
        self.warnings = []
        self.recent_logs = deque(maxlen=window_size)
        self.start_time = datetime.now()
        self.status_codes = Counter()
        self.response_times = []
        self.api_calls = Counter()
        self.whatsapp_messages = {
            "sent": 0,
            "received": 0,
            "error": 0
        }
        self.error_patterns = Counter()
        self.slow_requests = []  # Requisições com tempo > 1s
    
    def add_log(self, timestamp, level, module, message):
        """Adiciona uma entrada de log às estatísticas"""
        self.total_logs += 1
        self.logs_by_level[level] += 1
        self.logs_by_module[module] += 1
        self.recent_logs.append((timestamp, level, module, message))
        
        # Processar erros e avisos
        if level in ["ERROR", "CRITICAL"]:
            self.errors.append((timestamp, module, message))
            # Extrair padrão de erro para agrupamento
            error_pattern = self._extract_error_pattern(message)
            if error_pattern:
                self.error_patterns[error_pattern] += 1
        elif level == "WARNING":
            self.warnings.append((timestamp, module, message))
        
        # Processar mensagens do WhatsApp
        self._process_whatsapp_message(message)
        
        # Extrair códigos de status HTTP e tempos de resposta
        self._process_http_info(message)
    
    def _extract_error_pattern(self, message):
        """Extrai um padrão de erro para agrupamento"""
        # Remover IDs, timestamps e valores específicos
        pattern = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<id>', message)
        pattern = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '<timestamp>', pattern)
        pattern = re.sub(r'\b\d+\.\d+\.\d+\.\d+\b', '<ip>', pattern)
        
        # Capturar linha principal do erro
        error_line = pattern.split('\n')[0]
        
        # Limitar tamanho
        if len(error_line) > 100:
            error_line = error_line[:100] + '...'
            
        return error_line
    
    def _process_whatsapp_message(self, message):
        """Processa mensagens específicas do WhatsApp"""
        match = WHATSAPP_PATTERN.search(message)
        if match:
            symbol, content = match.groups()
            if symbol == "✓" and "Recebida nova mensagem" in content:
                self.whatsapp_messages["received"] += 1
            elif symbol == "✓" and "Mensagem enviada" in content:
                self.whatsapp_messages["sent"] += 1
            elif symbol == "❌":
                self.whatsapp_messages["error"] += 1
    
    def _process_http_info(self, message):
        """Extrai informações HTTP de mensagens de log"""
        # Extrair código de status HTTP
        status_match = re.search(r'→ (\d{3}) em', message)
        if status_match:
            status_code = int(status_match.group(1))
            self.status_codes[status_code] += 1
        
        # Extrair tempo de resposta
        time_match = re.search(r'em (\d+\.\d+)s', message)
        if time_match:
            response_time = float(time_match.group(1))
            self.response_times.append(response_time)
            
            # Registrar requisições lentas (> 1s)
            if response_time > 1.0:
                endpoint_match = re.search(r'(GET|POST|PUT|DELETE) ([^\s→]+)', message)
                if endpoint_match:
                    method, endpoint = endpoint_match.groups()
                    self.slow_requests.append((response_time, method, endpoint))
        
        # Extrair chamadas de API
        api_match = re.search(r'(GET|POST|PUT|DELETE) ([/\w_]+)', message)
        if api_match:
            method, endpoint = api_match.groups()
            self.api_calls[f"{method} {endpoint}"] += 1
    
    def get_summary(self):
        """Retorna resumo das estatísticas"""
        runtime = datetime.now() - self.start_time
        logs_per_second = self.total_logs / max(1, runtime.total_seconds())
        
        # Calcular estatísticas de tempo de resposta
        avg_response_time = sum(self.response_times) / max(1, len(self.response_times)) if self.response_times else 0
        
        return {
            "total_logs": self.total_logs,
            "runtime": str(runtime).split('.')[0],  # Sem milissegundos
            "logs_per_second": logs_per_second,
            "by_level": dict(self.logs_by_level),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "whatsapp_messages": dict(self.whatsapp_messages),
            "http_status": dict(self.status_codes),
            "avg_response_time": avg_response_time,
            "top_modules": dict(self.logs_by_module.most_common(5)),
            "top_endpoints": dict(self.api_calls.most_common(5)),
            "top_errors": dict(self.error_patterns.most_common(5))
        }

# Função para analisar uma linha de log
def parse_log_line(line):
    """Parse uma linha de log e retorna componentes"""
    match = LOG_PATTERN.match(line)
    if match:
        timestamp_str, level, module, message = match.groups()
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
        except ValueError:
            timestamp = datetime.now()  # Fallback
        return timestamp, level, module, message
    return None

# Função para monitorar arquivos de log
def monitor_logs(log_dir, pattern="*.log", level_filter=None, message_filter=None, callback=None):
    """
    Monitora arquivos de log e chama o callback para cada nova linha
    
    Args:
        log_dir: Diretório de logs
        pattern: Padrão de nome de arquivo (glob)
        level_filter: Filtrar por nível de log
        message_filter: Filtrar por texto na mensagem
        callback: Função a ser chamada com os componentes de log
    """
    log_files = {}
    stats = LogStats()
    
    # Função para ler novas linhas do arquivo
    def process_file(filepath):
        if filepath not in log_files:
            log_files[filepath] = {
                'position': 0,
                'last_check': time.time(),
                'file_obj': None
            }
        
        file_info = log_files[filepath]
        
        # Reabrir o arquivo se fechado
        if file_info['file_obj'] is None or file_info['file_obj'].closed:
            try:
                file_info['file_obj'] = open(filepath, 'r', encoding='utf-8')
                file_info['file_obj'].seek(file_info['position'])
            except Exception as e:
                print(f"Erro ao abrir {filepath}: {e}")
                return
        
        # Ler novas linhas
        new_position = file_info['position']
        for line in file_info['file_obj']:
            new_position = file_info['file_obj'].tell()
            
            # Analisar linha
            parsed = parse_log_line(line)
            if parsed:
                timestamp, level, module, message = parsed
                
                # Aplicar filtros
                if level_filter and level not in level_filter:
                    continue
                
                if message_filter and not re.search(message_filter, message, re.IGNORECASE):
                    continue
                
                # Adicionar às estatísticas
                stats.add_log(timestamp, level, module, message)
                
                # Chamar callback se fornecido
                if callback:
                    callback(timestamp, level, module, message, stats)
            
        # Atualizar posição
        file_info['position'] = new_position
        file_info['last_check'] = time.time()
    
    # Loop principal
    try:
        while True:
            # Encontrar arquivos de log
            all_files = glob.glob(os.path.join(log_dir, pattern))
            
            # Processar cada arquivo
            for filepath in sorted(all_files):
                process_file(filepath)
            
            # Pequena pausa para não sobrecarregar CPU
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        # Fechar todos os arquivos abertos
        for file_info in log_files.values():
            if file_info['file_obj'] and not file_info['file_obj'].closed:
                file_info['file_obj'].close()
    
    return stats

# Função para exibir estatísticas periodicamente
def print_stats(stats, interval=10):
    """Imprime estatísticas a cada intervalo definido"""
    last_print = time.time()
    
    while True:
        now = time.time()
        if now - last_print >= interval:
            summary = stats.get_summary()
            
            print("\n" + "=" * 80)
            print(f"ESTATÍSTICAS DE LOGS (Tempo: {summary['runtime']})")
            print("=" * 80)
            print(f"Total de logs: {summary['total_logs']} " 
                  f"({summary['logs_per_second']:.2f} logs/segundo)")
            print(f"Por nível: {summary['by_level']}")
            print(f"Erros: {summary['errors']}, Avisos: {summary['warnings']}")
            print(f"Mensagens WhatsApp: {summary['whatsapp_messages']}")
            print(f"Códigos HTTP: {summary['http_status']}")
            print(f"Tempo médio de resposta: {summary['avg_response_time']:.4f}s")
            print("=" * 80)
            
            last_print = now
            
        time.sleep(1)

# Dashboard rico se a biblioteca estiver disponível
def run_dashboard(stats, interval=2.0):
    """
    Executa um dashboard interativo usando a biblioteca rich
    """
    if not RICH_AVAILABLE:
        print("ERROR: Rich library not available. Install with 'pip install rich'")
        return
    
    console = Console()
    layout = Layout()
    
    # Dividir o layout
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1)
    )
    
    # Subdividir a seção principal
    layout["main"].split_row(
        Layout(name="stats", ratio=1),
        Layout(name="logs", ratio=2)
    )
    
    # Subdividir as estatísticas
    layout["stats"].split(
        Layout(name="general", ratio=2),
        Layout(name="http", ratio=2),
        Layout(name="errors", ratio=2)
    )
    
    # Função para criar o header
    def make_header():
        summary = stats.get_summary()
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        
        grid.add_row(
            f"[bold blue]WhatsApp API - Monitor de Logs[/bold blue]",
            f"[bold]Tempo de execução:[/bold] {summary['runtime']}"
        )
        
        return Panel(grid, style="bold white on blue")
    
    # Função para criar as estatísticas gerais
    def make_general_stats():
        summary = stats.get_summary()
        table = Table(title="Estatísticas Gerais", expand=True)
        
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right")
        
        table.add_row("Total de logs", str(summary['total_logs']))
        table.add_row("Logs/segundo", f"{summary['logs_per_second']:.2f}")
        table.add_row("Erros", str(summary['errors']))
        table.add_row("Avisos", str(summary['warnings']))
        
        # Adicionar estatísticas do WhatsApp
        table.add_row("WhatsApp Enviadas", str(summary['whatsapp_messages']['sent']))
        table.add_row("WhatsApp Recebidas", str(summary['whatsapp_messages']['received']))
        table.add_row("WhatsApp Erros", str(summary['whatsapp_messages']['error']))
        
        # Adicionar principais módulos
        table.add_section()
        table.add_row("[bold]Top Módulos[/bold]", "")
        for module, count in list(summary['top_modules'].items())[:3]:
            table.add_row(str(module), str(count))
        
        return table
    
    # Função para criar estatísticas HTTP
    def make_http_stats():
        summary = stats.get_summary()
        table = Table(title="Estatísticas HTTP", expand=True)
        
        table.add_column("Métrica", style="magenta")
        table.add_column("Valor", justify="right")
        
        # Tempo médio de resposta
        table.add_row("Tempo médio", f"{summary['avg_response_time']:.4f}s")
        
        # Códigos de status
        table.add_section()
        table.add_row("[bold]Códigos HTTP[/bold]", "")
        for status, count in sorted(summary['http_status'].items()):
            color = "green" if 200 <= int(status) < 300 else "yellow" if 300 <= int(status) < 400 else "red"
            table.add_row(f"[{color}]{status}[/{color}]", str(count))
        
        # Top endpoints
        table.add_section()
        table.add_row("[bold]Top Endpoints[/bold]", "")
        for endpoint, count in list(summary['top_endpoints'].items())[:3]:
            table.add_row(str(endpoint), str(count))
        
        return table
    
    # Função para criar estatísticas de erros
    def make_error_stats():
        summary = stats.get_summary()
        table = Table(title="Erros e Avisos", expand=True)
        
        table.add_column("Padrão de Erro", style="red")
        table.add_column("Ocorrências", justify="right")
        
        for error, count in list(summary['top_errors'].items())[:5]:
            table.add_row(str(error), str(count))
        
        return table
    
    # Função para criar a visualização de logs
    def make_logs_view():
        table = Table(title="Logs Recentes", expand=True)
        
        table.add_column("Hora", style="bright_black", width=10)
        table.add_column("Nível", width=8)
        table.add_column("Módulo", style="bright_blue", width=15)
        table.add_column("Mensagem", ratio=1)
        
        # Adicionar logs recentes (últimos 10)
        recent_logs = list(stats.recent_logs)[-10:]
        for timestamp, level, module, message in recent_logs:
            time_str = timestamp.strftime("%H:%M:%S")
            
            # Colorir com base no nível
            if level == "ERROR":
                level_text = Text(level, style="bold red")
            elif level == "WARNING":
                level_text = Text(level, style="bold yellow")
            elif level == "INFO":
                level_text = Text(level, style="green")
            elif level == "DEBUG":
                level_text = Text(level, style="bright_black")
            else:
                level_text = Text(level)
            
            # Processar a mensagem
            if "\n" in message:
                message = message.split("\n")[0] + "..."
            
            # Truncar mensagem se necessário
            if len(message) > 80:
                message = message[:77] + "..."
            
            # Colorir palavras-chave na mensagem
            msg_text = Text(message)
            for word in ERROR_KEYWORDS:
                msg_text.highlight_regex(f"\\b{word}\\b", style="bold red")
            for word in WARNING_KEYWORDS:
                msg_text.highlight_regex(f"\\b{word}\\b", style="bold yellow")
            
            table.add_row(time_str, level_text, module, msg_text)
        
        if not recent_logs:
            table.add_row("", "", "", "Nenhum log registrado ainda")
        
        return table
    
    # Função para atualizar todo o layout
    def update_layout():
        layout["header"].update(make_header())
        layout["stats"]["general"].update(make_general_stats())
        layout["stats"]["http"].update(make_http_stats())
        layout["stats"]["errors"].update(make_error_stats())
        layout["logs"].update(make_logs_view())
        
        return layout
    
    # Iniciar o dashboard ao vivo
    with Live(update_layout(), refresh_per_second=1/interval, screen=True) as live:
        try:
            while True:
                time.sleep(interval)
                live.update(update_layout())
        except KeyboardInterrupt:
            pass

# Função principal
def main():
    parser = argparse.ArgumentParser(description="Monitor de Logs em Tempo Real para WhatsApp API")
    parser.add_argument("--logs-dir", default="./logs", help="Diretório de logs")
    parser.add_argument("--filter", help="Filtrar logs por padrão")
    parser.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                        help="Filtrar por nível mínimo")
    parser.add_argument("--follow", "-f", action="store_true", help="Seguir logs em tempo real")
    parser.add_argument("--stats", "-s", action="store_true", help="Mostrar estatísticas")
    parser.add_argument("--interval", type=float, default=2.0, help="Intervalo de atualização")
    parser.add_argument("--dashboard", "-d", action="store_true", help="Executar dashboard interativo")
    
    args = parser.parse_args()
    
    # Verificar se o diretório de logs existe
    if not os.path.isdir(args.logs_dir):
        print(f"ERRO: Diretório de logs não encontrado: {args.logs_dir}")
        return 1
    
    # Configurar filtro de nível
    level_filter = None
    if args.level:
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level_index = levels.index(args.level)
        level_filter = levels[level_index:]
    
    # Configurar estatísticas
    stats = LogStats()
    
    # Configurar callback de exibição de logs
    if args.follow:
        def print_log(timestamp, level, module, message, _):
            time_str = timestamp.strftime("%H:%M:%S")
            
            # Colorir com base no nível
            if level == "ERROR":
                level_color = "\033[91m"  # Vermelho
            elif level == "WARNING":
                level_color = "\033[93m"  # Amarelo
            elif level == "INFO":
                level_color = "\033[92m"  # Verde
            else:
                level_color = "\033[0m"   # Normal
            
            reset = "\033[0m"
            print(f"{time_str} {level_color}{level:<8}{reset} {module}: {message}")
    else:
        print_log = None
    
    # Iniciar thread de estatísticas se solicitado
    if args.stats and not args.dashboard:
        stats_thread = threading.Thread(
            target=print_stats, 
            args=(stats, args.interval),
            daemon=True
        )
        stats_thread.start()
    
    # Executar dashboard se solicitado
    if args.dashboard:
        # Iniciar monitoramento em uma thread separada
        monitor_thread = threading.Thread(
            target=monitor_logs,
            args=(args.logs_dir, "*.log", level_filter, args.filter, None),
            kwargs={"callback": lambda *args: stats.add_log(*args[:4])},
            daemon=True
        )
        monitor_thread.start()
        
        # Executar o dashboard na thread principal
        run_dashboard(stats, args.interval)
        return 0
    
    # Iniciar monitoramento
    try:
        print(f"Monitorando logs em {args.logs_dir}...")
        if args.filter:
            print(f"Filtrando por: {args.filter}")
        if level_filter:
            print(f"Níveis: {', '.join(level_filter)}")
        print("Pressione Ctrl+C para sair")
        
        monitor_logs(args.logs_dir, "*.log", level_filter, args.filter, print_log)
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())