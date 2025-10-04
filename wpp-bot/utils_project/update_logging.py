#!/usr/bin/env python3
"""
Script para atualizar e configurar o sistema de logs do WhatsApp API

Este script:
1. Cria os diretórios de logs necessários
2. Instala as dependências para logs aprimorados
3. Configura o formato de logs para o ambiente
4. Testa a configuração com alguns logs de exemplo
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import time
import argparse
import shutil

# Definir cores para output do terminal
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RED = "\033[31m"


def print_color(message, color=RESET, bold=False):
    """Imprime mensagem colorida"""
    prefix = BOLD if bold else ""
    print(f"{prefix}{color}{message}{RESET}")


def print_header(message):
    """Imprime cabeçalho destacado"""
    print("\n" + "=" * 80)
    print_color(f" {message} ".center(80, "="), BLUE, bold=True)
    print("=" * 80)


def print_step(step, message):
    """Imprime passo de execução"""
    print_color(f"[{step}] {message}", BLUE)


def print_success(message):
    """Imprime mensagem de sucesso"""
    print_color(f"✅ {message}", GREEN)


def print_warning(message):
    """Imprime aviso"""
    print_color(f"⚠️ {message}", YELLOW)


def print_error(message):
    """Imprime erro"""
    print_color(f"❌ {message}", RED, bold=True)


def create_log_directories(base_path, verbose=False):
    """Cria estrutura de diretórios para logs"""
    print_step(1, f"Criando diretórios de logs em {base_path}")
    
    # Diretórios a serem criados
    directories = [
        "app",          # Logs da aplicação
        "api",          # Logs da API
        "whatsapp",     # Logs específicos do WhatsApp
        "error",        # Logs de erros
        "debug",        # Logs de depuração
        "archived"      # Logs arquivados (rotacionados)
    ]
    
    for directory in directories:
        dir_path = os.path.join(base_path, directory)
        os.makedirs(dir_path, exist_ok=True)
        if verbose:
            print(f"  - Diretório {dir_path} criado")
    
    print_success(f"Diretórios de logs criados com sucesso")
    return True


def install_dependencies(verbose=False):
    """Instala dependências necessárias para logs aprimorados"""
    print_step(2, "Instalando dependências para logs aprimorados")
    
    dependencies = [
        "rich",           # Formatação rica para console
        "coloredlogs",    # Logs coloridos
        "pythonjsonlogger", # Logs em formato JSON
    ]
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--upgrade"] + dependencies + (["-q"] if not verbose else [])
        )
        print_success(f"Dependências instaladas com sucesso: {', '.join(dependencies)}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Falha ao instalar dependências: {str(e)}")
        return False


def copy_log_files(source_dir, target_dir, verbose=False):
    """Copia arquivos de configuração de logs para o destino"""
    print_step(3, "Copiando arquivos de configuração de logs")
    
    # Lista de arquivos a serem copiados (relativo à raiz do projeto)
    files = [
        ("app/services/logger.py", "app/services/logger.py"),
        ("app/utils/logging_middleware.py", "app/utils/logging_middleware.py"),
        ("app/utils/metrics.py", "app/utils/metrics.py"),
        ("config/uvicorn_log_config.py", "config/uvicorn_log_config.py"),
        ("app/utils/pretty_logs.py", "app/utils/pretty_logs.py")
    ]
    
    success = True
    for src_rel, dst_rel in files:
        src = os.path.join(source_dir, src_rel)
        dst = os.path.join(target_dir, dst_rel)
        
        # Criar diretório de destino se não existir
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        try:
            if os.path.exists(src):
                shutil.copy2(src, dst)
                if verbose:
                    print(f"  - Copiado: {src} → {dst}")
            else:
                print_warning(f"Arquivo não encontrado: {src}")
                success = False
        except Exception as e:
            print_error(f"Erro ao copiar {src} para {dst}: {str(e)}")
            success = False
    
    if success:
        print_success("Arquivos de configuração de logs copiados com sucesso")
    return success


def test_logging_configuration(verbose=False):
    """Testa a configuração de logs"""
    print_step(4, "Testando configuração de logs")
    
    try:
        # Importar módulo de logging
        from app.services.logger import setup_logging, format_whatsapp_message
        
        # Configurar logger
        logger = setup_logging(log_level="DEBUG")
        
        # Testar diferentes níveis de log
        logger.info(format_whatsapp_message("info", "Teste de configuração de logs"))
        logger.debug(format_whatsapp_message("debug", "Informação detalhada de depuração"))
        logger.warning(format_whatsapp_message("warning", "Aviso de teste"))
        logger.error(format_whatsapp_message("error", "Erro de teste"))
        
        # Testar log de exceção
        try:
            # Provocar exceção de exemplo
            1/0
        except Exception as e:
            logger.exception("Exceção de teste capturada")
        
        print_success("Testes de logging executados com sucesso")
        return True
    except Exception as e:
        print_error(f"Erro ao testar configuração de logs: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Configuração de logs do WhatsApp API")
    parser.add_argument("--project-dir", default=".", help="Diretório raiz do projeto")
    parser.add_argument("--logs-dir", default="logs", help="Diretório para armazenar logs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")
    parser.add_argument("--skip-deps", action="store_true", help="Pular instalação de dependências")
    
    args = parser.parse_args()
    
    print_header("Configuração de Logs do WhatsApp API")
    
    # Validar diretórios
    project_dir = os.path.abspath(args.project_dir)
    logs_dir = os.path.abspath(args.logs_dir)
    
    if not os.path.isdir(project_dir):
        print_error(f"Diretório do projeto não encontrado: {project_dir}")
        return 1
    
    # Criar diretórios de logs
    if not create_log_directories(logs_dir, args.verbose):
        return 1
    
    # Instalar dependências
    if not args.skip_deps:
        if not install_dependencies(args.verbose):
            return 1
    else:
        print_step(2, "Instalação de dependências ignorada (--skip-deps)")
    
    # Copiar arquivos de configuração
    if not copy_log_files(project_dir, project_dir, args.verbose):
        print_warning("Alguns arquivos não puderam ser copiados")
    
    # Testar configuração
    if not test_logging_configuration(args.verbose):
        print_warning("A configuração de logs pode não estar funcionando corretamente")
        return 1
    
    print_header("Configuração Concluída com Sucesso")
    print_success("O sistema de logs foi configurado e testado com sucesso!")
    print("\nPara usar no seu código:")
    print_color("  from app.services.logger import setup_logging, format_whatsapp_message", BLUE)
    print_color("  logger = setup_logging()", BLUE)
    print_color("  logger.info(format_whatsapp_message('success', 'Mensagem de exemplo'))", BLUE)
    
    print("\nRecomendações:")
    print("  1. Verifique os logs em:", logs_dir)
    print("  2. Ajuste o nível de log em config/settings.py (LOG_LEVEL)")
    print("  3. Use format_whatsapp_message() para logs consistentes")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())