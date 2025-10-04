from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import os
import json
import logging
import re
import asyncio

from app.db.crud.menu import CRUDMenu, CRUDMenuState
from app.db.crud.user import CRUDUser, CRUDConversationLog
from app.models.menu import Menu, MenuState
from app.models.user import User
from app.services.whatsapp import whatsapp_service
from app.utils.constants import MenuType, MessageDirection
from config.settings import settings

logger = logging.getLogger(__name__)

class ProjetoAsasMenuService:
    """
    Serviço especializado para gerenciar o fluxo de menus do Projeto ASAS
    """
    def __init__(
        self, 
        menu_crud: CRUDMenu, 
        menu_state_crud: CRUDMenuState, 
        user_crud: CRUDUser, 
        log_crud: CRUDConversationLog
    ):
        self.menu_crud = menu_crud
        self.menu_state_crud = menu_state_crud
        self.user_crud = user_crud
        self.log_crud = log_crud
        
        # Carregar templates de menu
        self.menu_templates = self._load_menu_templates()
        # Números de administradores para notificações
        self.admin_numbers = {
            "coordenacao": "556121951085",
            "secretaria": "556121951086",
            "comunicacao": "556121951087",
            "financeiro": "556121951088",
            "patrimonio": "556121951089",
            "abraao": "55999831166"
        }
        
    def _load_menu_templates(self) -> Dict[str, Any]:
        """
        Carrega os templates de menu do arquivo JSON
        """
        try:
            menu_file = os.path.join(
                settings.BASE_DIR, 
                "app", 
                "utils", 
                "projeto_asas_menu_templates.json"
            )
            
            with open(menu_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Menu templates file not found: {menu_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding menu templates: {e}")
            return {}
    
    async def get_or_create_menu_state(self, db: Session, user_id: int) -> MenuState:
        """
        Obtém ou cria o estado do menu para um usuário
        """
        menu_state = self.menu_state_crud.get_by_user_id(db, user_id=user_id)
        
        if not menu_state:
            # Criar novo estado de menu
            menu_state = self.menu_state_crud.create(
                db,
                obj_in={
                    "user_id": user_id,
                    "current_menu": "privacidade",  # Começar com o menu de privacidade
                    "awaiting_response": False,
                    "form_filled": False,
                    "context_data": {}
                }
            )
            
        return menu_state
    
    async def handle_incoming_message(
        self, 
        db: Session, 
        user: User, 
        message_text: str,
        interactive_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Processa uma mensagem recebida e envia a resposta apropriada
        """
        # Obter ou criar estado do menu para o usuário
        menu_state = await self.get_or_create_menu_state(db, user.id)
        
        # Registrar mensagem recebida
        self.log_crud.create_log(
            db=db,
            user_id=user.id,
            message=message_text,
            direction=MessageDirection.INCOMING,
            menu_option=menu_state.current_menu
        )
        
        # Verificar se aceitou os termos
        # Se o menu atual é "privacidade" e o usuário não aceitou os termos
        if menu_state.current_menu == "privacidade" and not user.terms_accepted:
            if interactive_data and "button_reply" in interactive_data:
                button_id = interactive_data["button_reply"]["id"]
                
                if button_id == "ACEITOU":
                    # Atualizar aceitação de termos
                    user.terms_accepted = True
                    db.commit()
                    
                    # Ir para o menu inicial
                    menu_state.current_menu = "inicial"
                    db.commit()
                    
                    await self.send_menu(db, user, "inicial")
                    return
                elif button_id == "NEGOU":
                    # Enviar mensagem de encerramento
                    await whatsapp_service.send_message(
                        phone_number=user.phone_number,
                        message="Não será possivel prosseguir. Agradecemos seu contato!",
                        log_to_db=True,
                        user_id=user.id,
                        db=db
                    )
                    return
            else:
                # Enviar menu de privacidade novamente
                await self.send_menu(db, user, "privacidade")
                return
        
        # Processar mensagem interativa (botões/listas)
        if interactive_data:
            await self._process_interactive_message(db, user, menu_state, interactive_data)
            return
            
        # Processar resposta de texto para formulários específicos
        if menu_state.awaiting_response:
            await self._process_form_response(db, user, menu_state, message_text)
            return
            
        # Caso especial: verificar se é uma mensagem "Pronto" para formulário de participação
        if menu_state.current_menu == "participar" and message_text.lower() in ["pronto", "pronto."]:
            # Atualizar estado e enviar próximo menu
            menu_state.current_menu = "participar_confirmacao"
            db.commit()
            
            await self.send_menu(db, user, "participar_confirmacao")
            
            # Enviar notificações para os coordenadores
            await self._send_admin_notifications(
                db, 
                user, 
                menu_state, 
                "participar_confirmacao"
            )
            return
        
        # Para qualquer outra mensagem de texto, mostrar o menu atual
        await self.send_menu(db, user, menu_state.current_menu)
    
    async def _process_interactive_message(
        self,
        db: Session,
        user: User,
        menu_state: MenuState,
        interactive_data: Dict[str, Any]
    ) -> None:
        """
        Processa uma mensagem interativa (botão/lista)
        """
        # Extrair ID da seleção
        selection_id = None
        
        if "button_reply" in interactive_data:
            selection_id = interactive_data["button_reply"]["id"]
        elif "list_reply" in interactive_data:
            selection_id = interactive_data["list_reply"]["id"]
            
        if not selection_id:
            # Dados interativos inválidos
            await self.send_menu(db, user, menu_state.current_menu)
            return
            
        logger.info(f"User {user.phone_number} selected option: {selection_id}")
        
        # Ações especiais baseadas no ID selecionado
        if selection_id == "encerrar":
            # Ir para menu de encerramento
            menu_state.current_menu = "encerrar_atendimento"
            db.commit()
            await self.send_menu(db, user, "encerrar_atendimento")
            return
            
        if selection_id == "VOLTAR":
            # Voltar para o menu inicial
            menu_state.current_menu = "inicial"
            db.commit()
            await self.send_menu(db, user, "inicial")
            return
            
        if selection_id.startswith("voltar"):
            # Para voltar2, precisamos determinar o menu pai com base no estado atual
            parent_menu = self._get_parent_menu(menu_state.current_menu)
            if parent_menu:
                menu_state.current_menu = parent_menu
                db.commit()
                await self.send_menu(db, user, parent_menu)
            else:
                # Fallback para o menu inicial
                menu_state.current_menu = "inicial"
                db.commit()
                await self.send_menu(db, user, "inicial")
            return
            
        # Avaliações
        if selection_id in ["muito_bom", "bom", "mediano", "ruim", "pessimo"]:
            # Mapear para o menu de avaliação correspondente
            evaluation_menu = f"avaliacao_{selection_id}"
            menu_state.current_menu = evaluation_menu
            db.commit()
            
            # Enviar mensagem de confirmação
            await self.send_menu(db, user, evaluation_menu)
            
            # Enviar notificação para o admin
            await self._send_admin_notifications(db, user, menu_state, evaluation_menu)
            return
        
        # Verificar se a opção tem uma ação especial ou próximo menu
        action_or_menu = self._get_action_or_next_menu(menu_state.current_menu, selection_id)
        
        if action_or_menu:
            # Verificar se é uma ação especial
            if action_or_menu == "menu_avaliacao":
                # Ação especial: ir para o menu de avaliação
                menu_state.current_menu = "menu_avaliacao"
                db.commit()
                await self.send_menu(db, user, "menu_avaliacao")
                return
            elif action_or_menu.startswith("avaliacao_"):
                # Ação especial: ir para um menu de avaliação específico
                menu_state.current_menu = action_or_menu
                db.commit()
                await self.send_menu(db, user, action_or_menu)
                return
            else:
                # Menu normal: atualizar estado e enviar próximo menu
                menu_state.current_menu = action_or_menu
                db.commit()
                await self.send_menu(db, user, action_or_menu)
                return
        
        # Se chegou aqui, a opção não foi reconhecida
        # Manter no menu atual
        await self.send_menu(db, user, menu_state.current_menu)
    
    async def _process_form_response(
        self,
        db: Session,
        user: User,
        menu_state: MenuState,
        message_text: str
    ) -> None:
        """
        Processa uma resposta de texto para um formulário
        """
        current_menu = menu_state.current_menu
        
        # Verificar se estamos no menu de ouvidoria
        if current_menu == "ouvidoria":
            # Armazenar a mensagem enviada para o coordenador
            await self._handle_ouvidoria_submission(db, user, menu_state, message_text)
            return
        
        # Para outros formulários que possam ser adicionados posteriormente
        # Manter no menu atual se não souber o que fazer
        await self.send_menu(db, user, current_menu)
    
    async def _handle_ouvidoria_submission(
        self,
        db: Session,
        user: User,
        menu_state: MenuState,
        message_text: str
    ) -> None:
        """
        Processa o envio do formulário de ouvidoria
        """
        # Enviar confirmação para o usuário
        await whatsapp_service.send_message(
            phone_number=user.phone_number,
            message="*Agradecemos o seu feedback!*\n\n- Sua participação é fundamental para alcançarmos nossos objetivos.\n\n- Iremos conduzir os próximos passos com a atenção que sua mensagem requer e, se necessário, entraremos em contato em breve.",
            log_to_db=True,
            user_id=user.id,
            db=db
        )
        
        # Enviar a mensagem para o coordenador
        admin_number = self.admin_numbers["coordenacao"]
        admin_message = f"O contato número: {user.phone_number}, está requisitando *OUVIDORIA* conforme detalhamento a seguir:\n\n- {message_text}"
        
        await whatsapp_service.send_message(
            phone_number=admin_number,
            message=admin_message,
            log_to_db=False
        )
        
        # Enviar o contato do usuário para o coordenador
        await whatsapp_service.send_contact_message(
            phone_number=admin_number,
            contact_name=user.name or "Usuário",
            contact_phone=user.phone_number,
            log_to_db=False
        )
        
        # Desativar modo de espera
        menu_state.awaiting_response = False
        db.commit()
        
        # Mostrar o menu de encerramento
        menu_state.current_menu = "encerrar_atendimento"
        db.commit()
        await self.send_menu(db, user, "encerrar_atendimento")
    
    async def send_menu(self, db: Session, user: User, menu_name: str) -> None:
        """
        Envia um menu para o usuário
        """
        menu_data = self._get_menu_data(menu_name)
        if not menu_data:
            logger.error(f"Menu not found: {menu_name}")
            # Fallback para o menu inicial
            menu_data = self._get_menu_data("inicial")
            if not menu_data:
                # Último recurso: enviar uma mensagem básica
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message="Desculpe, ocorreu um erro no sistema de menus. Por favor, tente novamente mais tarde.",
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
                return
        
        # Formatar conteúdo com dados do usuário
        content = menu_data.get("content", "")
        content = content.replace("{name}", user.name or "")
        content = content.replace("{phone_number}", user.phone_number)
        
        # Determinar o tipo de menu e enviá-lo
        menu_options = menu_data.get("options", {})
        menu_type = menu_options.get("menu_type", "text")
        
        # Primeiro enviar o conteúdo principal do menu
        if menu_type == "button":
            await self._send_button_menu(db, user, content, menu_options)
        elif menu_type == "list":
            await self._send_list_menu(db, user, content, menu_options)
        else:
            # Menu de texto simples
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=content,
                log_to_db=True,
                user_id=user.id,
                db=db
            )
        
        # Verificar se há formulário associado
        form_data = menu_data.get("form")
        if form_data:
            # Se há um formulário, marcar que estamos aguardando resposta
            menu_state = await self.get_or_create_menu_state(db, user.id)
            menu_state.awaiting_response = True
            db.commit()
            
            # Se há um texto de envio, enviar
            if "submit_text" in form_data:
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=form_data["submit_text"],
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
        
        # Pequena pausa para evitar problemas de ordem de mensagens
        await asyncio.sleep(0.5)
        
        # Depois enviar ações extras (anexos, contatos, etc.)
        extra_actions = menu_data.get("extra_actions", [])
        for action in extra_actions:
            await self._execute_extra_action(db, user, action)
            # Pequena pausa entre ações extras para garantir a ordem correta
            await asyncio.sleep(0.3)
    
    async def _send_button_menu(
        self, 
        db: Session, 
        user: User, 
        content: str, 
        menu_options: Dict[str, Any]
    ) -> None:
        """
        Envia um menu com botões
        """
        buttons = []
        for button in menu_options.get("buttons", []):
            buttons.append({
                "id": button.get("id"),
                "title": button.get("title")
            })
            
        await whatsapp_service.send_button_message(
            phone_number=user.phone_number,
            body_text=content,
            buttons=buttons,
            log_to_db=True,
            user_id=user.id,
            db=db
        )
    
    async def _send_list_menu(
        self, 
        db: Session, 
        user: User, 
        content: str, 
        menu_options: Dict[str, Any]
    ) -> None:
        """
        Envia um menu com lista
        """
        header = menu_options.get("header", "Menu")
        footer = menu_options.get("footer", "Selecione uma opção")
        button_text = menu_options.get("button_text", "Opções")
        
        sections = []
        for section in menu_options.get("sections", []):
            rows = []
            for row in section.get("rows", []):
                rows.append({
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "description": row.get("description", "")
                })
                
            if rows:
                sections.append({
                    "title": section.get("title", ""),
                    "rows": rows
                })
        
        await whatsapp_service.send_list_message(
            phone_number=user.phone_number,
            header_text=header,
            body_text=content,
            footer_text=footer,
            button_text=button_text,
            sections=sections,
            log_to_db=True,
            user_id=user.id,
            db=db
        )
    
    async def _execute_extra_action(
        self, 
        db: Session, 
        user: User, 
        action: Dict[str, Any]
    ) -> None:
        """
        Executa ações extras definidas no menu
        """
        action_type = action.get("type")
        
        if action_type == "message":
            # Enviar mensagem de texto adicional
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=action.get("content", ""),
                log_to_db=True,
                user_id=user.id if db else None,
                db=db
            )
            
        elif action_type == "image":
            # Enviar imagem
            # Esta implementação depende de como você gerencia o upload e armazenamento de imagens
            pass
            
        elif action_type == "contact":
            # Enviar contato
            await whatsapp_service.send_contact_message(
                phone_number=user.phone_number,
                contact_name=action.get("name", ""),
                contact_phone=action.get("phone", ""),
                log_to_db=True,
                user_id=user.id if db else None,
                db=db
            )
            
        elif action_type == "location":
            # Enviar localização
            await whatsapp_service.send_location_message(
                phone_number=user.phone_number,
                latitude=action.get("latitude", "0"),
                longitude=action.get("longitude", "0"),
                name=action.get("name", ""),
                address=action.get("address", ""),
                log_to_db=True,
                user_id=user.id if db else None,
                db=db
            )
            
        elif action_type == "link":
            # Enviar link interativo
            await whatsapp_service.send_link_message(
                phone_number=user.phone_number,
                title=action.get("title", "Link"),
                body_text=action.get("message", ""),
                url=action.get("url", ""),
                button_text=action.get("button_text", "Clique aqui"),
                log_to_db=True,
                user_id=user.id if db else None,
                db=db
            )
    
    async def _send_admin_notifications(
        self, 
        db: Session, 
        user: User, 
        menu_state: MenuState, 
        menu_name: str
    ) -> None:
        """
        Envia notificações para administradores conforme definido no menu
        """
        menu_data = self._get_menu_data(menu_name)
        if not menu_data:
            return
            
        notifications = menu_data.get("notifications", [])
        
        for notification in notifications:
            if notification.get("type") == "admin_notification":
                admin_key = notification.get("admin", "coordenacao")
                admin_number = self.admin_numbers.get(admin_key, self.admin_numbers["coordenacao"])
                
                if admin_number in notification.get("admin", ""):
                    admin_number = notification.get("admin")
                
                message = notification.get("message", "")
                
                # Formatar a mensagem com dados do usuário
                message = message.replace("{name}", user.name or "")
                message = message.replace("{phone_number}", user.phone_number)
                
                # Adicionar horário atual
                current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                message = message.replace("{timestamp}", current_time)
                
                # Enviar notificação para o administrador
                await whatsapp_service.send_message(
                    phone_number=admin_number,
                    message=message,
                    log_to_db=False
                )
                
                # Se solicitado, enviar o contato do usuário
                if notification.get("send_contact", False):
                    await whatsapp_service.send_contact_message(
                        phone_number=admin_number,
                        contact_name=user.name or "Usuário",
                        contact_phone=user.phone_number,
                        log_to_db=False
                    )
    
    def _get_menu_data(self, menu_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém os dados de um menu pelo nome
        """
        menus = self.menu_templates.get("menus", {})
        return menus.get(menu_name)
    
    def _get_action_or_next_menu(self, current_menu: str, option_id: str) -> Optional[str]:
        """
        Obtém a ação ou o próximo menu baseado na opção selecionada
        """
        menu_data = self._get_menu_data(current_menu)
        if not menu_data:
            return None
            
        menu_options = menu_data.get("options", {})
        
        # Verificar botões
        if "buttons" in menu_options:
            for button in menu_options["buttons"]:
                if button.get("id") == option_id:
                    # Se há uma ação definida, retornar essa ação
                    if "action" in button:
                        return button.get("action")
                    # Caso contrário, retornar o próximo menu
                    return button.get("next_menu")
        
        # Verificar listas
        if "sections" in menu_options:
            for section in menu_options["sections"]:
                if "rows" in section:
                    for row in section["rows"]:
                        if row.get("id") == option_id:
                            # Mapeamento de opções específicas
                            if option_id == "SOBRE":
                                return "sobre"
                            elif option_id == "MISSAO":
                                return "missao"
                            elif option_id == "METODO":
                                return "metodo"
                            elif option_id == "CONTATO":
                                return "contato"
                            elif option_id == "CONTAT2":
                                return "midias"
                            elif option_id == "TREINOS":
                                return "treinos"
                            elif option_id == "PARTICIPAR":
                                return "participar"
                            elif option_id == "INVISTA":
                                return "invista"
                            elif option_id == "GALERIA":
                                return "galeria"
                            elif option_id == "DEPOIMENTO":
                                return "depoimento"
                            # Para outras opções, retornar o next_menu se definido
                            return row.get("next_menu")
        
        return None
    
    def _get_parent_menu(self, current_menu: str) -> Optional[str]:
        """
        Determina o menu pai com base no menu atual
        """
        # Mapeamento de menus para seus pais
        menu_parents = {
            "sobre": "info_geral",
            "missao": "info_geral",
            "metodo": "info_geral",
            "contato": "info_geral",
            "midias": "info_geral",
            "duvidas": "suporte_feedback",
            "fale": "suporte_feedback",
            "ouvidoria": "suporte_feedback",
            "treinos": "participar_menu",
            "participar": "participar_menu",
            "participar_confirmacao": "participar_menu",
            "participar_termo": "participar_menu",
            "participar_treinos_info": "participar_menu",
            "invista": "participar_menu",
            "galeria": "participar_menu",
            "depoimento": "participar_menu"
        }
        
        return menu_parents.get(current_menu, "inicial")