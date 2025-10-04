from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import json
import logging
import os
import shutil
from pathlib import Path
import datetime
import httpx

from config.settings import settings
from config.database import get_db
from app.db.crud.user import user as user_crud, conversation_log
from app.db.crud.menu import CRUDMenu, CRUDMenuState
from app.models.user import User
from app.services.whatsapp import whatsapp_service
from app.services.projeto_asas_menu import ProjetoAsasMenuService
from app.services.ai_service import AIService
from app.services.fluxo_bemobi import FluxoBemobi
from app.services.fluxo_bemobi_automatico import FluxoBemobiAutomatico
from app.utils.helpers import is_greeting, is_business_hours, format_phone_number
from app.models.menu import Menu, MenuState

# Criar instância do serviço de menu
menu_crud = CRUDMenu(Menu)
menu_state_crud = CRUDMenuState(MenuState)

projeto_asas_service = ProjetoAsasMenuService(
    menu_crud=menu_crud,
    menu_state_crud=menu_state_crud,
    user_crud=user_crud,
    log_crud=conversation_log
)

# Serviço de IA será inicializado quando necessário
ai_service = None

# Cria o logger
logger = logging.getLogger(__name__)

# Cria a rota
router = APIRouter()

# Caminho para o template JSON
TEMPLATE_FILE = settings.BASE_DIR / "app" / "utils" / "projeto_asas_menu_templates.json"

# Configura a rota estática para servir arquivos da interface web
# Criando o diretório webinterface/static se não existir
STATIC_DIR = settings.BASE_DIR / "webinterface" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/verify")
async def verify_whatsapp_challenge(request: Request):
    """
    Endpoint dedicado para verificação do webhook do WhatsApp
    """
    # Extrair parâmetros da query
    params = dict(request.query_params)
    hub_mode = params.get("hub.mode")
    hub_verify_token = params.get("hub.verify_token")
    hub_challenge = params.get("hub.challenge")
    
    logger.info(f"Verificação de webhook recebida: mode={hub_mode}, token={hub_verify_token}")
    
    # Verificar se é uma solicitação de verificação válida
    if hub_mode == "subscribe" and hub_verify_token:
        if hub_verify_token == settings.VERIFY_TOKEN:
            logger.info(f"Verificação bem sucedida, retornando challenge: {hub_challenge}")
            return Response(content=hub_challenge, media_type="text/plain")
        else:
            logger.warning(f"Token de verificação inválido: {hub_verify_token}")
    
    logger.error("Verificação falhou: parâmetros inválidos ou token incorreto")
    return Response(content="Verification failed", status_code=403)


@router.post("/verify")
async def receive_webhook_verify(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Recebe as requisições do webhook enviadas pela api WhatsApp no endpoint verify
    """
    logger.info("POST /verify webhook recebido - redirecionando para processamento")
    return await receive_webhook(request, background_tasks, db)


@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Recebe as requisições do webhook enviadas pela API WhatsApp
    """
    logger.info("POST webhook recebido - iniciando processamento")
    
    try:
        # Obter o corpo da requisição
        body = await request.body()
        text_body = body.decode('utf-8')
        logger.debug(f"Corpo da requisição recebido: {text_body}")
        
        # Parsear o JSON
        data = json.loads(text_body)
        
        if "object" not in data:
            logger.warning("Objeto não encontrado na requisição")
            return Response(content="Invalid request", status_code=400)
            
        if data["object"] != "whatsapp_business_account":
            logger.warning(f"Objeto não é whatsapp_business_account: {data['object']}")
            return Response(content="Invalid request", status_code=400)
            
        # Processamento assincrono
        logger.info("Iniciando processamento assíncrono")
        background_tasks.add_task(process_webhook_entries, data, db, background_tasks)
            
        return {"status": "processing"}
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {str(e)}")
        return Response(content=f"JSON Error: {str(e)}", status_code=400)
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(content=f"Error: {str(e)}", status_code=500)


async def process_webhook_entries(data: Dict[str, Any], db: Session, background_tasks: BackgroundTasks = None):
    """
    Processa as entradas do webhook de forma assíncrona
    """
    logger.info("Iniciando processamento de entradas do webhook")
    
    try:
        if "entry" not in data:
            logger.error("No entries in webhook data")
            return
            
        for entry_index, entry in enumerate(data["entry"]):
            logger.info(f"Processando entrada {entry_index+1}/{len(data['entry'])}")
            
            if "changes" not in entry:
                logger.warning(f"Entrada {entry_index+1} não possui 'changes'")
                continue
                
            for change_index, change in enumerate(entry["changes"]):
                logger.info(f"Processando alteração {change_index+1}/{len(entry['changes'])}")
                
                if "value" not in change:
                    logger.warning(f"Alteração {change_index+1} não possui 'value'")
                    continue
                    
                value = change["value"]
                
                if "messages" not in value:
                    logger.warning(f"Value não possui 'messages'")
                    continue
                    
                # Extrai informações do user
                phone_number = None
                name = None
                
                if "contacts" in value:
                    for contact in value["contacts"]:
                        if "wa_id" in contact:
                            phone_number = contact["wa_id"]
                            
                        if "profile" in contact and "name" in contact["profile"]:
                            name = contact["profile"]["name"]
                
                logger.info(f"Encontradas {len(value['messages'])} mensagens para processamento")
                
                # Process each message
                for msg_index, message in enumerate(value["messages"]):
                    logger.info(f"Processando mensagem {msg_index+1}/{len(value['messages'])}")
                    await process_message(db, message, phone_number, name, background_tasks)
                    
        logger.info("Processamento de entradas do webhook concluído com sucesso")
    except Exception as e:
        logger.error(f"Error processing webhook entries: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


async def process_message(
    db: Session, 
    message: Dict[str, Any], 
    phone_number: Optional[str] = None, 
    name: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """
    Processa mensagens pegas do webhook usando o serviço do Projeto ASAS
    """
    try:
        # Garantir que vamos ter o número do usuário
        if not phone_number and "from" in message:
            phone_number = message["from"]
            
        if not phone_number:
            logger.error("No phone number in message")
            return
            
        # Extrai o texto da mensagem e dados interativos
        message_text = "No text"
        message_type = message.get("type", "unknown")
        interactive_data = None
        
        logger.info(f"Processando mensagem do tipo: {message_type}")
        
        if message_type == "text" and "text" in message:
            message_text = message["text"].get("body", "No text")
        elif message_type == "interactive" and "interactive" in message:
            interactive_data = message["interactive"]
            interactive_type = interactive_data.get("type")
            logger.info(f"Tipo de mensagem interativa: {interactive_type}")
            
            if interactive_type == "button_reply":
                message_text = f"Botão: {interactive_data.get('button_reply', {}).get('title', 'Desconhecido')}"
            elif interactive_type == "list_reply":
                message_text = f"Lista: {interactive_data.get('list_reply', {}).get('title', 'Desconhecido')}"
            else:
                message_text = f"Interativo: {interactive_type}"
        else:
            logger.info(f"Tipo de mensagem não processado: {message_type}")
            message_text = f"Mensagem do tipo: {message_type}"
        
        # Log receipt of message
        logger.info(f"Received message: '{message_text}' from {phone_number}")
        
        # Verificar se o usuário existe
        user = user_crud.get_by_phone_number(db, phone_number=phone_number)
        
        if not user:
            # Criar novo usuário
            logger.info(f"Creating new user with phone number {phone_number}")
            user = user_crud.create_with_phone(
                db,
                obj_in={
                    "phone_number": phone_number,
                    "name": name or "Usuário",
                    "terms_accepted": False  # Começamos com termos não aceitos
                }
            )
        
        # Sistema Bemobi com fluxo de botões - substitui completamente o Projeto ASAS
        if await is_verification_request(message_text, message_type, message):
            # Verificação de cobrança com agentes especializados
            await handle_verification_request(db, user, message_text, message_type, message, background_tasks)
        elif interactive_data and interactive_data.get("type") == "button_reply":
            # Processar clique em botão do fluxo Bemobi
            button_id = interactive_data.get("button_reply", {}).get("id")
            await fluxo_bemobi.processar_botao(db, user, button_id)
        else:
            # Iniciar fluxo Bemobi padrão
            await fluxo_bemobi.iniciar_fluxo(db, user, message_text)
        
        logger.info(f"Mensagem processada com sucesso para {phone_number}")
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Print detailed traceback for debugging
        import traceback
        logger.error(traceback.format_exc())


async def send_terms_message(db: Session, user: User):
    """
    Menssagem de termos e condições
    """
    message = (
        "*Termos e Condições*\n\n"
        "Antes de começarmos, precisamos que você aceite nossos termos e condições de uso.\n\n"
        "Por favor, leia nossos termos em: https://example.com/terms\n\n"
        "Para continuar, selecione uma opção abaixo:"
    )
    
    buttons = [
        {"id": "accept_terms", "title": "Aceitar"},
        {"id": "reject_terms", "title": "Recusar"}
    ]
    
    await whatsapp_service.send_button_message(
        phone_number=user.phone_number,
        body_text=message,
        buttons=buttons,
        log_to_db=True,
        user_id=user.id,
        db=db
    )


async def send_outside_business_hours_message(db: Session, user: User):
    """
    Envia msg quando não esta em horario comercial
    """
    start_hour = settings.BUSINESS_HOURS_START
    end_hour = settings.BUSINESS_HOURS_END
    
    message = (
        f"*Fora do Horário de Atendimento*\n\n"
        f"Olá! Nosso horário de atendimento é de {start_hour}h às {end_hour}h, de segunda a sexta-feira.\n\n"
        f"Sua mensagem foi registrada e responderemos assim que possível durante o próximo horário de atendimento.\n\n"
        f"Agradecemos sua compreensão."
    )
    
    await whatsapp_service.send_message(
        phone_number=user.phone_number,
        message=message,
        log_to_db=True,
        user_id=user.id,
        db=db
    )


async def send_response(db: Session, user: User, message: str, response_data: Dict[str, Any]):
    """
    Envia resposta baseado no tipo
    """
    response_type = response_data.get("type", "text")
    
    if response_type == "text":
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message=message,
            log_to_db=True,
            user_id=user.id,
            db=db
        )
    elif response_type == "button":
        await whatsapp_service.send_button_message(
            phone_number=user.phone_number,
            body_text=message,
            buttons=response_data.get("buttons", []),
            log_to_db=True,
            user_id=user.id,
            db=db
        )
    elif response_type == "list":
        await whatsapp_service.send_list_message(
            phone_number=user.phone_number,
            header_text=response_data.get("header", "Menu"),
            body_text=message,
            footer_text=response_data.get("footer", "Select an option"),
            button_text=response_data.get("button_text", "Click here"),
            sections=response_data.get("sections", []),
            log_to_db=True,
            user_id=user.id,
            db=db
        )
    elif response_type == "link":
        await whatsapp_service.send_link_message(
            phone_number=user.phone_number,
            title=response_data.get("title", "Link"),
            body_text=message,
            url=response_data.get("url", ""),
            button_text=response_data.get("button_text", "Click here"),
            log_to_db=True,
            user_id=user.id,
            db=db
        )
    else:
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message=message,
            log_to_db=True,
            user_id=user.id,
            db=db
        )


def is_admin_user(user: User) -> bool:
    """
    Verifica se o usuario é administrador
    """
    # Ainda falta implementar

    '''
    Ideia de logica:

        if user.number in admin_numbers:
            return admin_pannel()

    '''

    admin_numbers = os.getenv("ADMIN_PHONE_NUMBERS", "").split(",")
    return user.phone_number in admin_numbers


###########################################
# Endpoints da Interface Web de Gerenciamento
###########################################

@router.get("/painel", response_class=HTMLResponse)
async def admin_panel():
    """Página principal do painel administrativo"""
    logger.info(f"Acessando o painel administrativo")
    html_file = settings.BASE_DIR / "webinterface" / "index.html"
    
    if html_file.exists():
        logger.info(f"Arquivo HTML encontrado: {html_file}")
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    else:
        logger.error(f"Arquivo HTML não encontrado: {html_file}")
        raise HTTPException(status_code=404, detail="Interface web não encontrada")


@router.get("/painel/static/{file_path:path}", include_in_schema=False)
async def admin_static_files(file_path: str):
    """Servir arquivos estáticos para a interface web"""
    logger.info(f"Requisição de arquivo estático: {file_path}")
    
    # Verificar se o arquivo existe na pasta webinterface/static
    file_location = settings.BASE_DIR / "webinterface" / "static" / file_path
    
    if file_location.exists():
        logger.info(f"Arquivo encontrado: {file_location}")
        return FileResponse(file_location)
    else:
        # Verificar se é o arquivo JavaScript principal
        js_file_location = settings.BASE_DIR / "webinterface" / "static" / "js" / file_path
        if js_file_location.exists():
            logger.info(f"Arquivo JavaScript encontrado: {js_file_location}")
            return FileResponse(js_file_location)
        
        logger.error(f"Arquivo não encontrado: {file_path}")
        raise HTTPException(status_code=404, detail=f"Arquivo {file_path} não encontrado")


@router.get("/painel/api/flow", response_class=JSONResponse)
async def get_flow():
    """Obtém o fluxo de conversa atual"""
    try:
        logger.info(f"Acessando o fluxo de conversa. Caminho do arquivo: {TEMPLATE_FILE}")
        logger.info(f"O arquivo existe? {TEMPLATE_FILE.exists()}")
        
        if not TEMPLATE_FILE.exists():
            logger.error(f"Arquivo de template não encontrado: {TEMPLATE_FILE}")
            return JSONResponse(
                content={"error": f"Arquivo de template não encontrado: {TEMPLATE_FILE}"},
                status_code=404
            )
        
        logger.info(f"Lendo o arquivo: {TEMPLATE_FILE}")
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



@router.post("/painel/api/flow", response_class=JSONResponse)
async def save_flow(data: Dict[str, Any]):
    """Salva o fluxo de conversa"""
    try:
        # Sempre fazer backup antes de salvar
        if TEMPLATE_FILE.exists():
            backup_file = TEMPLATE_FILE.with_suffix(".bak")
            try:
                shutil.copy2(TEMPLATE_FILE, backup_file)
                logger.info(f"Backup do fluxo criado: {backup_file}")
            except Exception as e:
                logger.warning(f"Não foi possível criar backup: {str(e)}")
        
        # Garantir que o diretório existe
        TEMPLATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar o novo fluxo
        logger.info(f"Salvando fluxo em: {TEMPLATE_FILE}")
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Recarregar o serviço de menu para aplicar as alterações
        projeto_asas_service._load_menu_templates()
        logger.info("Serviço de menu recarregado com sucesso")
        
        # Atualizar o arquivo hot_reload.py para acionar o recarregamento
        hot_reload_path = os.path.join(os.path.dirname(__file__), "..", "..", "utils", "hot_reload.py")
        
        now = datetime.datetime.now().isoformat()
        with open(hot_reload_path, "r+", encoding="utf-8") as f:
            content = f.read()
            f.seek(0)
            f.write(content.replace(
                'LAST_UPDATE = "', 
                f'LAST_UPDATE = "{now}'))
            f.truncate()
        
        logger.info(f"Arquivo hot_reload.py atualizado para forçar recarregamento")
        
        return {"status": "success", "message": "Fluxo salvo com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao salvar o fluxo: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"error": f"Erro ao salvar o fluxo: {str(e)}"},
            status_code=500
        )


@router.post("/painel/api/flow/validate", response_class=JSONResponse)
async def validate_flow(data: Dict[str, Any]):
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
        
        # Verificar botões e links de todos os menus para garantir que apontam para menus existentes
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


@router.post("/painel/api/flow/import", response_class=JSONResponse)
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
        
        # Recarregar o serviço de menu para aplicar as alterações
        projeto_asas_service._load_menu_templates()
        logger.info("Serviço de menu recarregado com sucesso")
        
        return {"status": "success", "message": "Fluxo importado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao importar o fluxo: {str(e)}")
        return JSONResponse(
            content={"error": f"Erro ao importar o fluxo: {str(e)}"},
            status_code=500
        )


@router.get("/painel/api/flow/export", response_class=JSONResponse)
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


# ===== FUNÇÕES PARA INTEGRAÇÃO COM FLUXO DE VERIFICAÇÃO IA =====

def get_ai_service():
    """
    Obtém instância do serviço de IA, inicializando se necessário
    """
    global ai_service
    if ai_service is None:
        try:
            ai_service = AIService()
            logger.info("Serviço de IA inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar serviço de IA: {e}")
            raise HTTPException(
                status_code=500,
                detail="Serviço de IA não disponível"
            )
    return ai_service

# Inicializar fluxo Bemobi automático
fluxo_bemobi = FluxoBemobiAutomatico()

async def is_verification_request(message_text: str, message_type: str, message: Dict[str, Any]) -> bool:
    """
    Detecta se a mensagem é uma solicitação de verificação de cobrança
    """
    try:
        # Palavras-chave que indicam verificação de cobrança
        verification_keywords = [
            "verificar cobrança", "verificar boleto", "verificar pagamento",
            "verificar fatura", "verificar conta", "verificar documento",
            "verificar", "cobrança", "boleto", "pix", "pagamento",
            "fatura", "conta", "documento", "verificar se é golpe",
            "é golpe", "é verdade", "é legítimo", "é falso",
            "bemobi", "financeiro", "dinheiro", "valor", "preço",
            "cobrança bemobi", "pagamento bemobi", "fatura bemobi"
        ]
        
        # Verificar texto da mensagem
        if message_text:
            message_lower = message_text.lower()
            for keyword in verification_keywords:
                if keyword in message_lower:
                    logger.info(f"Detectada solicitação de verificação: '{keyword}' em '{message_text}'")
                    return True
        
        # Verificar se é uma imagem (possível boleto/documento)
        if message_type == "image":
            logger.info("Imagem detectada - possível documento para verificação")
            return True
        
        # Verificar se é um documento
        if message_type == "document":
            logger.info("Documento detectado - possível boleto para verificação")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Erro ao detectar solicitação de verificação: {e}")
        return False


async def is_bemobi_financial_request(message_text: str, message_type: str, message: Dict[str, Any]) -> bool:
    """
    Detecta se a mensagem é uma solicitação financeira da Bemobi
    """
    try:
        # Palavras-chave que indicam solicitações financeiras Bemobi
        bemobi_keywords = [
            "bemobi", "financeiro", "dinheiro", "valor", "preço",
            "cobrança", "pagamento", "fatura", "conta", "boleto",
            "pix", "transferência", "depósito", "saque", "saldo",
            "extrato", "cartão", "débito", "crédito", "limite",
            "juros", "taxa", "comissão", "desconto", "promoção",
            "plano", "assinatura", "mensalidade", "anuidade",
            "oi", "olá", "bom dia", "boa tarde", "boa noite",
            "ajuda", "suporte", "atendimento", "contato",
            "serviço", "produto", "cliente", "usuário"
        ]
        
        # Verificar texto da mensagem
        if message_text:
            message_lower = message_text.lower()
            for keyword in bemobi_keywords:
                if keyword in message_lower:
                    logger.info(f"Detectada solicitação financeira Bemobi: '{keyword}' em '{message_text}'")
                    return True
        
        # Verificar se é uma imagem (possível documento financeiro)
        if message_type == "image":
            logger.info("Imagem detectada - possível documento financeiro Bemobi")
            return True
        
        # Verificar se é um documento
        if message_type == "document":
            logger.info("Documento detectado - possível documento financeiro Bemobi")
            return True
        
        # Sistema Bemobi é sempre ativado para qualquer mensagem
        # Isso substitui completamente o Projeto ASAS
        logger.info("Sistema Bemobi ativado para qualquer mensagem")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao detectar solicitação financeira Bemobi: {e}")
        return False


async def handle_bemobi_default_request(db: Session, user: User, message_text: str, message_type: str, message: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Processa solicitação padrão da Bemobi (substitui Projeto ASAS)
    """
    try:
        logger.info(f"Processando solicitação padrão Bemobi para usuário {user.id}")
        
        # Enviar mensagem de boas-vindas da Bemobi
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="🏦 **Bemobi - Assistente Inteligente**\n\nOlá! Sou a Grace, sua assistente da Bemobi.\n\nComo posso ajudar você hoje?",
            log_to_db=True,
            user_id=user.id,
            db=db
        )
        
        # Enviar opções principais da Bemobi
        await send_bemobi_main_options(db, user)
        
    except Exception as e:
        logger.error(f"Erro ao processar solicitação padrão Bemobi: {e}")
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="❌ **Erro**\n\nOcorreu um erro ao processar sua solicitação. Tente novamente.",
            log_to_db=True,
            user_id=user.id,
            db=db
        )


async def send_bemobi_main_options(db: Session, user: User):
    """
    Envia opções principais da Bemobi
    """
    try:
        # Criar botões para opções principais
        buttons = [
            {"id": "verificar_cobranca", "title": "🔍 Verificar Cobrança"},
            {"id": "suporte_financeiro", "title": "💰 Suporte Financeiro"},
            {"id": "ajuda", "title": "❓ Ajuda"},
            {"id": "contato", "title": "📞 Contato"}
        ]
        
        await whatsapp_service.send_button_message(
            phone_number=user.phone_number,
            body_text="**Escolha uma opção:**",
            buttons=buttons,
            log_to_db=True,
            user_id=user.id,
            db=db
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar opções principais: {e}")


async def handle_bemobi_financial_request(db: Session, user: User, message_text: str, message_type: str, message: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Processa solicitação financeira da Bemobi
    """
    try:
        logger.info(f"Processando solicitação financeira Bemobi para usuário {user.id}")
        
        # Enviar mensagem de boas-vindas da Bemobi
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="🏦 **Bemobi - Sistema Financeiro**\n\nOlá! Sou a Grace, sua assistente financeira da Bemobi.\n\nComo posso ajudar você hoje?",
            log_to_db=True,
            user_id=user.id,
            db=db
        )
        
        # Enviar opções financeiras
        await send_bemobi_financial_options(db, user)
        
    except Exception as e:
        logger.error(f"Erro ao processar solicitação financeira Bemobi: {e}")
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="❌ **Erro**\n\nOcorreu um erro ao processar sua solicitação. Tente novamente.",
            log_to_db=True,
            user_id=user.id,
            db=db
        )


async def send_bemobi_financial_options(db: Session, user: User):
    """
    Envia opções financeiras da Bemobi
    """
    try:
        # Criar botões para opções financeiras
        buttons = [
            {"id": "verificar_cobranca", "title": "🔍 Verificar Cobrança"},
            {"id": "consultar_saldo", "title": "💰 Consultar Saldo"},
            {"id": "extrato", "title": "📊 Extrato"},
            {"id": "suporte_financeiro", "title": "📞 Suporte Financeiro"}
        ]
        
        await whatsapp_service.send_button_message(
            phone_number=user.phone_number,
            body_text="**Escolha uma opção financeira:**",
            buttons=buttons,
            log_to_db=True,
            user_id=user.id,
            db=db
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar opções financeiras: {e}")


async def handle_verification_request(db: Session, user: User, message_text: str, message_type: str, message: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Processa solicitação de verificação de cobrança
    """
    try:
        logger.info(f"Processando solicitação de verificação para usuário {user.id}")
        
        # Enviar mensagem de confirmação
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="🏦 **Grace - Bemobi Financeiro**\n\nAnalisando sua solicitação de verificação...",
            log_to_db=True,
            user_id=user.id,
            db=db
        )
        
        # Processar baseado no tipo de mensagem
        if message_type == "image":
            await handle_image_verification(db, user, message, background_tasks)
        elif message_type == "document":
            await handle_document_verification(db, user, message, background_tasks)
        elif message_text and any(keyword in message_text.lower() for keyword in ["pix", "chave", "valor"]):
            await handle_text_verification(db, user, message_text, background_tasks)
        else:
            # Solicitar que envie uma imagem ou dados
            await send_verification_instructions(db, user)
            
    except Exception as e:
        logger.error(f"Erro ao processar solicitação de verificação: {e}")
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="❌ **Erro**\n\nOcorreu um erro ao processar sua solicitação. Tente novamente.",
            log_to_db=True,
            user_id=user.id,
            db=db
        )


async def handle_image_verification(db: Session, user: User, message: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Processa verificação de imagem (boleto/documento)
    """
    try:
        # Obter URL da imagem
        image_data = message.get("image", {})
        image_id = image_data.get("id")
        
        if not image_id:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="❌ **Erro**\n\nNão foi possível obter a imagem. Tente novamente.",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            return
        
        # Obter URL da imagem da API do WhatsApp
        image_url = await get_media_url(image_id)
        
        if not image_url:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="❌ **Erro**\n\nNão foi possível acessar a imagem. Tente novamente.",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            return
        
        # Processar com fluxo automático
        background_tasks.add_task(
            fluxo_bemobi.processar_imagem,
            db, user, image_url
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar imagem: {e}")
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="❌ **Erro**\n\nErro ao processar a imagem. Tente novamente.",
            log_to_db=True,
            user_id=user.id,
            db=db
        )


async def handle_document_verification(db: Session, user: User, message: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Processa verificação de documento
    """
    try:
        # Similar ao handle_image_verification mas para documentos
        document_data = message.get("document", {})
        document_id = document_data.get("id")
        
        if not document_id:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="❌ **Erro**\n\nNão foi possível obter o documento. Tente novamente.",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            return
        
        # Obter URL do documento
        document_url = await get_media_url(document_id)
        
        if not document_url:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="❌ **Erro**\n\nNão foi possível acessar o documento. Tente novamente.",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            return
        
        # Executar verificação em background
        background_tasks.add_task(
            process_verification_background,
            db, user, image_url=document_url, user_id=str(user.id)
        )
        
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="📄 **Documento recebido - Bemobi**\n\nIniciando análise com nossos agentes especializados da Bemobi...\n\n⏳ Aguarde alguns segundos...",
            log_to_db=True,
            user_id=user.id,
            db=db
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar documento: {e}")
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="❌ **Erro**\n\nErro ao processar o documento. Tente novamente.",
            log_to_db=True,
            user_id=user.id,
            db=db
        )


async def handle_text_verification(db: Session, user: User, message_text: str, background_tasks: BackgroundTasks):
    """
    Processa verificação de texto (dados PIX, etc.)
    """
    try:
        # Processar com fluxo automático
        background_tasks.add_task(
            fluxo_bemobi.processar_texto_pix,
            db, user, message_text
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar texto: {e}")
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="❌ **Erro**\n\nErro ao processar os dados. Tente novamente.",
            log_to_db=True,
            user_id=user.id,
            db=db
        )


async def send_verification_instructions(db: Session, user: User):
    """
    Envia instruções para verificação
    """
    try:
        ai_service = get_ai_service()
        message = ai_service.obter_mensagem_inicial()
        
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message=message,
            log_to_db=True,
            user_id=user.id,
            db=db
        )
    except Exception as e:
        logger.error(f"Erro ao obter mensagem inicial: {e}")
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="🏦 **Grace - Bemobi Financeiro**\n\nPara verificar uma cobrança Bemobi, envie:\n📸 Uma foto do boleto\n📋 Os dados do PIX\n📄 Um documento\n\nOu digite 'bemobi' para ver opções financeiras",
            log_to_db=True,
            user_id=user.id,
            db=db
        )


async def get_media_url(media_id: str) -> Optional[str]:
    """
    Obtém URL da mídia da API do WhatsApp
    """
    try:
        url = f"{settings.BASE_URL.rstrip('/')}/{media_id}"
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("url")
            
        return None
        
    except Exception as e:
        logger.error(f"Erro ao obter URL da mídia: {e}")
        return None


async def process_verification_background(db: Session, user: User, image_url: str = None, texto_pix: str = None, user_id: str = None):
    """
    Processa verificação em background
    """
    try:
        logger.info(f"Iniciando verificação em background para usuário {user_id}")
        
        # Obter serviço de IA
        ai_service = get_ai_service()
        
        # Executar verificação completa
        resultado = await ai_service.verificar_cobranca_completa(
            image_url=image_url,
            texto_pix=texto_pix,
            user_id=user_id
        )
        
        if not resultado.get("sucesso", True):
            await send_verification_error(db, user, resultado.get("erro", "Erro na verificação"))
            return
        
        # Enviar resultado para o usuário
        await send_verification_result(db, user, resultado)
        
    except Exception as e:
        logger.error(f"Erro na verificação em background: {e}")
        await send_verification_error(db, user, f"Erro interno: {str(e)}")


async def send_verification_result(db: Session, user: User, resultado: Dict[str, Any]):
    """
    Envia resultado da verificação para o usuário
    """
    try:
        # Mensagem principal
        mensagem_principal = resultado.get("mensagem_usuario", "Verificação concluída")
        
        # Enviar mensagem principal
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message=mensagem_principal,
            log_to_db=True,
            user_id=user.id,
            db=db
        )
        
        # Enviar botões de interação se disponíveis
        botoes = resultado.get("botoes_interacao", [])
        if botoes:
            await whatsapp_service.send_button_message(
                phone_number=user.phone_number,
                body_text="Escolha uma opção:",
                buttons=[{"id": botao["reply"]["id"], "title": botao["reply"]["title"]} for botao in botoes],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
        
        # Enviar métricas se disponíveis
        metricas = resultado.get("metricas", {})
        if metricas:
            tempo = metricas.get("tempo_total_formatado", "N/A")
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=f"⏱️ **Tempo de análise:** {tempo}",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
        
    except Exception as e:
        logger.error(f"Erro ao enviar resultado: {e}")


async def send_verification_error(db: Session, user: User, erro: str):
    """
    Envia mensagem de erro da verificação
    """
    try:
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message=f"❌ **Erro na Verificação**\n\n{erro}\n\nTente novamente ou entre em contato com o suporte.",
            log_to_db=True,
            user_id=user.id,
            db=db
        )
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de erro: {e}")