from fastapi import APIRouter, Request, Response, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import json
import os
import shutil
import datetime
import re
import traceback

from config.settings import settings

# Configurar o logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Define o caminho para a aplicação React
REACT_APP_DIR = settings.BASE_DIR / "web_interface" / "dist"
# Caminho do arquivo JSON do fluxo
TEMPLATE_FILE = settings.BASE_DIR / "app" / "utils" / "projeto_asas_menu_templates.json"

# Verificar se o diretório da aplicação React existe
if not REACT_APP_DIR.exists():
    logger.warning(f"Diretório da aplicação React não encontrado: {REACT_APP_DIR}")
    logger.warning("Você precisa construir a aplicação React primeiro!")

# Endpoint para a página principal
@router.get("/", response_class=HTMLResponse)
async def serve_react_app():
    """Serve a página principal da aplicação React com reescrita dos caminhos dos assets"""
    logger.info(f"Servindo a aplicação React de {REACT_APP_DIR}")
    
    index_html = REACT_APP_DIR / "index.html"
    if index_html.exists():
        with open(index_html, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Reescrever os caminhos dos assets para incluir o prefixo correto
        # Vite gera links para assets como /assets/file.js, mas precisamos /api/v1/flow-manager/assets/file.js
        content = content.replace(
            'href="/assets/', 
            'href="/api/v1/flow-manager/assets/'
        )
        content = content.replace(
            'src="/assets/', 
            'src="/api/v1/flow-manager/assets/'
        )
        
        # Também ajustar outros recursos na raiz, como favicon
        content = re.sub(
            r'(href|src)="/(favicon\.ico|vite\.svg|logo\.png|manifest\.json|robots\.txt)', 
            r'\1="/api/v1/flow-manager/\2', 
            content
        )
        
        return HTMLResponse(content=content)
    else:
        logger.error(f"Arquivo index.html não encontrado em {REACT_APP_DIR}")
        raise HTTPException(status_code=404, detail="Aplicação React não encontrada")

# Servir arquivos estáticos
@router.get("/assets/{file_path:path}")
async def serve_static_assets(file_path: str):
    """Serve arquivos estáticos da pasta assets"""
    logger.info(f"Servindo arquivo estático: assets/{file_path}")
    file_location = REACT_APP_DIR / "assets" / file_path
    
    if file_location.exists():
        return FileResponse(file_location)
    else:
        logger.error(f"Arquivo não encontrado: assets/{file_path}")
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: assets/{file_path}")

# Servir arquivos na raiz (favicon.ico, etc)
@router.get("/{file_name:path}")
async def serve_root_files(file_name: str):
    """Serve arquivos da raiz do build (favicon.ico, etc)"""
    # Se o nome do arquivo contiver uma barra, é um caminho para um arquivo em um subdiretório
    # que não deveria ser servido por este endpoint
    if "/" in file_name or file_name == "api" or file_name == "assets":
        logger.warning(f"Tentativa de acessar caminho inválido: {file_name}")
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
        
    logger.info(f"Servindo arquivo da raiz: {file_name}")
    file_location = REACT_APP_DIR / file_name
    
    if file_location.exists() and file_location.is_file():
        return FileResponse(file_location)
    else:
        # Se não encontrar o arquivo, pode ser uma rota do React Router
        # Nesse caso, retornamos o index.html
        if file_name.split(".")[-1] not in ["ico", "png", "svg", "json", "js", "css", "txt"]:
            logger.info(f"Redirecionando rota {file_name} para a aplicação React")
            return await serve_react_app()
        else:
            logger.error(f"Arquivo não encontrado: {file_name}")
            raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {file_name}")

# API para obter o fluxo
@router.get("/api/flow", response_class=JSONResponse)
async def get_flow():
    """Obtém o fluxo de conversa atual"""
    try:
        logger.info(f"Acessando o fluxo de conversa. Caminho do arquivo: {TEMPLATE_FILE}")
        
        if not TEMPLATE_FILE.exists():
            logger.error(f"Arquivo de template não encontrado: {TEMPLATE_FILE}")
            return JSONResponse(
                content={"error": f"Arquivo de template não encontrado: {TEMPLATE_FILE}"},
                status_code=404
            )
        
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        logger.info(f"Dados lidos com sucesso. Número de menus: {len(data.get('menus', {}))}")
        return data
    except Exception as e:
        logger.error(f"Erro ao carregar o fluxo: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"error": f"Erro ao carregar o fluxo: {str(e)}"},
            status_code=500
        )

# API para salvar o fluxo
@router.post("/api/flow", response_class=JSONResponse)
async def save_flow(data: dict):
    """Salva o fluxo de conversa"""
    logger.info(f"Iniciando processo de salvamento do fluxo")
    logger.info(f"Tipo de dados recebidos: {type(data)}")
    logger.info(f"Conteúdo parcial recebido: {str(data)[:200]}...")  # Logs primeiros 200 caracteres para não logar todo o JSON
    
    try:
        # Verificar se os dados são válidos
        if not isinstance(data, dict):
            logger.error(f"Dados inválidos: esperado dict, recebido {type(data)}")
            return JSONResponse(
                content={"error": f"Dados inválidos: esperado dict, recebido {type(data)}"},
                status_code=400
            )
        
        if "menus" not in data:
            logger.error("Dados inválidos: a chave 'menus' não foi encontrada")
            return JSONResponse(
                content={"error": "Dados inválidos: a chave 'menus' não foi encontrada"},
                status_code=400
            )
        
        # Verificar se o arquivo de template existe
        logger.info(f"Verificando arquivo de template: {TEMPLATE_FILE}")
        logger.info(f"O arquivo existe? {TEMPLATE_FILE.exists()}")
        logger.info(f"Caminho absoluto: {TEMPLATE_FILE.absolute()}")
        
        # Sempre fazer backup antes de salvar
        if TEMPLATE_FILE.exists():
            backup_file = TEMPLATE_FILE.with_suffix(".bak")
            try:
                shutil.copy2(TEMPLATE_FILE, backup_file)
                logger.info(f"Backup do fluxo criado: {backup_file}")
            except Exception as e:
                logger.warning(f"Não foi possível criar backup: {str(e)}")
                logger.warning(f"Detalhes do erro de backup: {traceback.format_exc()}")
        
        # Garantir que o diretório existe
        logger.info(f"Garantindo que o diretório existe: {TEMPLATE_FILE.parent}")
        TEMPLATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar o novo fluxo
        logger.info(f"Salvando fluxo em: {TEMPLATE_FILE}")
        try:
            with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Arquivo salvo com sucesso")
        except Exception as write_error:
            logger.error(f"Erro ao escrever no arquivo: {str(write_error)}")
            logger.error(f"Detalhes do erro de escrita: {traceback.format_exc()}")
            return JSONResponse(
                content={"error": f"Erro ao escrever no arquivo: {str(write_error)}"},
                status_code=500
            )
        
        # Atualizar o arquivo hot_reload.py para acionar o recarregamento
        hot_reload_path = settings.BASE_DIR / "app" / "utils" / "hot_reload.py"
        logger.info(f"Atualizando arquivo hot_reload.py: {hot_reload_path}")
        logger.info(f"O arquivo hot_reload.py existe? {hot_reload_path.exists()}")
        
        now = datetime.datetime.now().isoformat()
        if hot_reload_path.exists():
            try:
                with open(hot_reload_path, "r+", encoding="utf-8") as f:
                    content = f.read()
                    f.seek(0)
                    f.write(content.replace(
                        'LAST_UPDATE = "', 
                        f'LAST_UPDATE = "{now}'))
                    f.truncate()
                logger.info(f"Arquivo hot_reload.py atualizado com sucesso")
            except Exception as reload_error:
                logger.warning(f"Erro ao atualizar hot_reload.py: {str(reload_error)}")
                logger.warning(f"Detalhes do erro de hot reload: {traceback.format_exc()}")
                # Continuamos mesmo se falhar aqui, pois o fluxo já foi salvo
        else:
            logger.warning(f"Arquivo hot_reload.py não encontrado. O recarregamento automático pode não funcionar.")
        
        logger.info(f"Processo de salvamento concluído com sucesso")
        
        return {"status": "success", "message": "Fluxo salvo com sucesso"}
    except Exception as e:
        logger.error(f"Erro não tratado ao salvar o fluxo: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"error": f"Erro ao salvar o fluxo: {str(e)}"},
            status_code=500
        )

# API para validar o fluxo
@router.post("/api/flow/validate", response_class=JSONResponse)
async def validate_flow(data: dict):
    """Valida o fluxo de conversa sem salvá-lo"""
    try:
        logger.info("Validando fluxo de conversa")
        # Verificar a estrutura básica do JSON
        if "menus" not in data:
            logger.warning("Fluxo inválido: não contém objeto 'menus'")
            return JSONResponse(
                content={"valid": False, "error": "O fluxo deve conter um objeto 'menus'"},
                status_code=400
            )
        
        # Verificar se 'privacidade' e 'inicial' existem
        if "privacidade" not in data["menus"]:
            logger.warning("Fluxo inválido: menu 'privacidade' não encontrado")
            return JSONResponse(
                content={"valid": False, "error": "O menu 'privacidade' é obrigatório"},
                status_code=400
            )
        
        if "inicial" not in data["menus"]:
            logger.warning("Fluxo inválido: menu 'inicial' não encontrado")
            return JSONResponse(
                content={"valid": False, "error": "O menu 'inicial' é obrigatório"},
                status_code=400
            )
        
        # Verificar botões e links de todos os menus
        for menu_name, menu_data in data["menus"].items():
            # Verificar se tem 'options'
            if "options" not in menu_data:
                continue
                
            options = menu_data["options"]
            
            # Verificar botões
            if "menu_type" in options and options["menu_type"] == "button" and "buttons" in options:
                for button in options["buttons"]:
                    if "next_menu" in button and button["next_menu"] not in data["menus"]:
                        logger.warning(f"Botão em '{menu_name}' aponta para menu inexistente: '{button['next_menu']}'")
                        return JSONResponse(
                            content={
                                "valid": False, 
                                "error": f"No menu '{menu_name}', o botão '{button.get('title', '')}' aponta para um menu inexistente: '{button['next_menu']}'"
                            },
                            status_code=400
                        )
        
        logger.info("Fluxo validado com sucesso")
        return {"valid": True, "message": "Fluxo válido"}
    except Exception as e:
        logger.error(f"Erro ao validar o fluxo: {str(e)}")
        return JSONResponse(
            content={"valid": False, "error": f"Erro ao validar o fluxo: {str(e)}"},
            status_code=500
        )

# API para importar o fluxo
@router.post("/api/flow/import", response_class=JSONResponse)
async def import_flow(file: UploadFile = File(...)):
    """Importa um fluxo de conversa a partir de um arquivo JSON"""
    try:
        logger.info(f"Importando fluxo do arquivo: {file.filename}")
        # Ler o conteúdo do arquivo
        content = await file.read()
        
        # Verificar se é um JSON válido
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("O arquivo não é um JSON válido")
            return JSONResponse(
                content={"error": "O arquivo não é um JSON válido"},
                status_code=400
            )
        
        # Validar a estrutura do fluxo
        if "menus" not in data:
            logger.warning("O arquivo não contém um fluxo de conversa válido")
            return JSONResponse(
                content={"error": "O arquivo não contém um fluxo de conversa válido"},
                status_code=400
            )
        
        # Sempre fazer backup antes de importar
        if TEMPLATE_FILE.exists():
            backup_file = TEMPLATE_FILE.with_suffix(".bak")
            shutil.copy2(TEMPLATE_FILE, backup_file)
            logger.info(f"Backup do fluxo criado: {backup_file}")
        
        # Salvar o novo fluxo
        logger.info(f"Salvando fluxo importado em: {TEMPLATE_FILE}")
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info("Fluxo importado com sucesso")
        
        return {"status": "success", "message": "Fluxo importado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao importar o fluxo: {str(e)}")
        return JSONResponse(
            content={"error": f"Erro ao importar o fluxo: {str(e)}"},
            status_code=500
        )

# API para exportar o fluxo
@router.get("/api/flow/export", response_class=JSONResponse)
async def export_flow():
    """Exporta o fluxo de conversa atual"""
    try:
        logger.info("Exportando fluxo de conversa")
        if not TEMPLATE_FILE.exists():
            logger.error(f"Arquivo de template não encontrado: {TEMPLATE_FILE}")
            return JSONResponse(
                content={"error": f"Arquivo de template não encontrado: {TEMPLATE_FILE}"},
                status_code=404
            )
        
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        logger.error(f"Erro ao exportar o fluxo: {str(e)}")
        return JSONResponse(
            content={"error": f"Erro ao exportar o fluxo: {str(e)}"},
            status_code=500
        )