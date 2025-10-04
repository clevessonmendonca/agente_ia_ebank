"""
Fluxo Bemobi - Sistema de Botões Interativos
Fluxo completo para demonstração e validação da IA
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from .whatsapp import whatsapp_service
from .ai_service import AIService

logger = logging.getLogger(__name__)

class FluxoBemobi:
    def __init__(self):
        self.ai_service = None
        
        # Estados do fluxo
        self.estados_fluxo = {
            "inicial": "inicial",
            "menu_principal": "menu_principal", 
            "verificacao": "verificacao",
            "resultado": "resultado",
            "suporte": "suporte"
        }
    
    def get_ai_service(self):
        """
        Obtém instância do serviço de IA, inicializando se necessário
        """
        if self.ai_service is None:
            try:
                # Carregar variáveis de ambiente antes de inicializar
                from dotenv import load_dotenv
                load_dotenv()
                
                self.ai_service = AIService()
                logger.info("Serviço de IA inicializado no fluxo Bemobi")
            except Exception as e:
                logger.error(f"Erro ao inicializar serviço de IA no fluxo: {e}")
                return None
        return self.ai_service
    
    async def iniciar_fluxo(self, db: Session, user, message_text: str = None):
        """
        Inicia o fluxo Bemobi com IA
        """
        try:
            logger.info(f"Iniciando fluxo Bemobi com IA para usuário {user.id}")
            
            # Usar IA para gerar resposta personalizada
            ai_service = self.get_ai_service()
            if ai_service:
                # Gerar resposta da IA baseada na mensagem do usuário
                resposta_ia = ai_service.obter_mensagem_inicial()
                
                # Enviar resposta da IA
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            else:
                # Fallback se IA não estiver disponível
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message="🏦 **Bemobi - Sistema Financeiro Inteligente**\n\n"
                           "Olá! Sou a Grace, sua assistente financeira especializada.\n\n"
                           "Utilizo agentes de IA especializados para:\n"
                           "🔍 Verificar autenticidade de cobranças\n"
                           "🛡️ Detectar fraudes e golpes\n"
                           "📊 Analisar documentos financeiros\n\n"
                           "Como posso ajudar você hoje?",
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar menu principal com IA
            await self.enviar_menu_principal_ia(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar fluxo Bemobi com IA: {e}")
            await self.enviar_erro(db, user, f"Erro ao iniciar fluxo: {str(e)}")
    
    async def enviar_menu_principal_ia(self, db: Session, user):
        """
        Envia menu principal com IA e botões
        """
        try:
            logger.info(f"Enviando menu principal com IA para usuário {user.id}")
            
            # Usar IA para gerar resposta do menu
            ai_service = self.get_ai_service()
            if ai_service:
                # Gerar resposta da IA para o menu
                resposta_menu = ai_service.obter_mensagem_ajuda()
                
                # Enviar resposta da IA
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_menu,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            else:
                # Fallback se IA não estiver disponível
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message="Escolha uma opção:",
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar botões
            await self.enviar_botoes_principais(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao enviar menu principal com IA: {e}")
            await self.enviar_erro(db, user, f"Erro ao enviar menu: {str(e)}")
    
    async def enviar_botoes_principais(self, db: Session, user):
        """
        Envia botões principais decididos pela IA (máximo 3)
        """
        try:
            # Usar número permitido para testes
            phone_number = "5591981960045" if user.phone_number == "559181960045" else user.phone_number
            
            # Usar IA para decidir os botões (com fallback robusto)
            ai_service = self.get_ai_service()
            buttons = None
            
            if ai_service:
                try:
                    # Pedir para a IA gerar os botões (máximo 3)
                    prompt_botoes = """
                    Você é a Grace, assistente financeira da Bemobi. 
                    Crie exatamente 3 botões para o menu principal do WhatsApp.
                    
                    IMPORTANTE: 
                    - Máximo 3 botões (limite do WhatsApp)
                    - Títulos curtos (máximo 20 caracteres)
                    - IDs simples (sem espaços)
                    - Foco em verificação financeira
                    
                    Responda APENAS no formato JSON:
                    {
                        "buttons": [
                            {"id": "id1", "title": "Título 1"},
                            {"id": "id2", "title": "Título 2"},
                            {"id": "id3", "title": "Título 3"}
                        ]
                    }
                    """
                    
                    resposta_ia = ai_service.groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt_botoes}],
                        temperature=0.3
                    )
                    
                    # Extrair JSON da resposta
                    import json
                    import re
                    
                    json_match = re.search(r'\{.*\}', resposta_ia.choices[0].message.content, re.DOTALL)
                    if json_match:
                        buttons_data = json.loads(json_match.group())
                        buttons = buttons_data.get("buttons", [])
                        
                        # Garantir que temos exatamente 3 botões válidos
                        if len(buttons) == 3 and all("id" in b and "title" in b for b in buttons):
                            # Validar títulos (máximo 20 caracteres)
                            for button in buttons:
                                if len(button["title"]) > 20:
                                    button["title"] = button["title"][:17] + "..."
                        else:
                            buttons = None
                    
                except Exception as e:
                    logger.warning(f"Erro ao gerar botões com IA: {e}")
                    buttons = None
            
            # Fallback se IA não funcionar ou gerar botões inválidos
            if not buttons:
                buttons = [
                    {"id": "demo_verificacao", "title": "Demo IA"},
                    {"id": "verificar_cobranca", "title": "Verificar"},
                    {"id": "sobre_agentes", "title": "Sobre Agentes"}
                ]
            
            logger.info(f"Enviando botões decididos pela IA: {buttons}")
            
            try:
                await whatsapp_service.send_button_message(
                    phone_number=phone_number,
                    body_text="Selecione uma opção:",
                    buttons=buttons,
                    log_to_db=False
                )
                logger.info("Botões principais decididos pela IA enviados com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao enviar botões via WhatsApp API: {e}")
                # Fallback: enviar mensagem simples com opções
                opcoes_texto = "\n".join([f"• {button['title']}" for button in buttons])
                await whatsapp_service.send_message(
                    phone_number=phone_number,
                    message=f"Selecione uma opção:\n\n{opcoes_texto}",
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
                logger.info("Fallback: mensagem de texto enviada com opções")
            
        except Exception as e:
            logger.error(f"Erro ao enviar botões principais: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await self.enviar_erro(db, user, f"Erro ao enviar botões: {str(e)}")
    
    async def enviar_menu_principal(self, db: Session, user):
        """
        Envia menu principal com botões de ação do WhatsApp
        """
        try:
            logger.info(f"Enviando menu principal para usuário {user.id}")
            
            # Usar número permitido para testes
            phone_number = "5591981960045" if user.phone_number == "559181960045" else user.phone_number
            
            # Implementação direta e simples - WhatsApp limita a 3 botões
            buttons = [
                {"id": "demo_verificacao", "title": "Demo IA"},
                {"id": "verificar_cobranca", "title": "Verificar"},
                {"id": "sobre_agentes", "title": "Sobre Agentes"}
            ]
            
            logger.info(f"Botões definidos: {buttons}")
            logger.info(f"Enviando para número: {phone_number}")
            
            await whatsapp_service.send_button_message(
                phone_number=phone_number,
                body_text="Escolha uma opção:",
                buttons=buttons,
                log_to_db=False
            )
            
            logger.info("Menu principal enviado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao enviar menu principal: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Enviar mensagem de erro
            await whatsapp_service.send_message(
                phone_number=phone_number,
                message="❌ Erro ao carregar opções. Tente novamente.",
                log_to_db=False
            )
    
    async def processar_botao(self, db: Session, user, button_id: str):
        """
        Processa clique em botão do fluxo com IA
        """
        try:
            logger.info(f"Processando botão {button_id} com IA para usuário {user.id}")
            
            # Usar IA para gerar resposta baseada no botão clicado
            ai_service = self.get_ai_service()
            if ai_service:
                # Gerar resposta da IA baseada no botão
                resposta_ia = ai_service.obter_mensagem_ajuda()
                
                # Enviar resposta da IA
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            else:
                # Fallback se IA não estiver disponível
                await self.processar_botao_fallback(db, user, button_id)
            
            # Processar ação específica do botão
            await self.processar_acao_botao(db, user, button_id)
                
        except Exception as e:
            logger.error(f"Erro ao processar botão {button_id} com IA: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar botão: {str(e)}")
    
    async def processar_acao_botao(self, db: Session, user, button_id: str):
        """
        Processa a ação específica do botão
        """
        try:
            if button_id == "demo_verificacao":
                await self.iniciar_demo_verificacao_ia(db, user)
            elif button_id == "verificar_cobranca":
                await self.iniciar_verificacao_real_ia(db, user)
            elif button_id == "sobre_agentes":
                await self.mostrar_sobre_agentes_ia(db, user)
            elif button_id == "voltar_menu":
                await self.enviar_menu_principal_ia(db, user)
            elif button_id == "teste_imagem":
                await self.iniciar_teste_imagem_ia(db, user)
            elif button_id == "teste_pix":
                await self.iniciar_teste_pix_ia(db, user)
            elif button_id == "ver_relatorio":
                await self.mostrar_relatorio_ia(db, user)
            else:
                await self.enviar_opcao_invalida_ia(db, user)
                
        except Exception as e:
            logger.error(f"Erro ao processar ação do botão {button_id}: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar ação: {str(e)}")
    
    async def processar_botao_fallback(self, db: Session, user, button_id: str):
        """
        Processamento de fallback quando IA não está disponível
        """
        try:
            if button_id == "demo_verificacao":
                await self.iniciar_demo_verificacao(db, user)
            elif button_id == "verificar_cobranca":
                await self.iniciar_verificacao_real(db, user)
            elif button_id == "sobre_agentes":
                await self.mostrar_sobre_agentes(db, user)
            elif button_id == "voltar_menu":
                await self.enviar_menu_principal(db, user)
            elif button_id == "teste_imagem":
                await self.iniciar_teste_imagem(db, user)
            elif button_id == "teste_pix":
                await self.iniciar_teste_pix(db, user)
            elif button_id == "ver_relatorio":
                await self.mostrar_relatorio(db, user)
            else:
                await self.enviar_opcao_invalida(db, user)
                
        except Exception as e:
            logger.error(f"Erro no fallback do botão {button_id}: {e}")
            await self.enviar_erro(db, user, f"Erro no fallback: {str(e)}")
    
    # Métodos com IA
    async def iniciar_demo_verificacao_ia(self, db: Session, user):
        """
        Inicia demonstração da verificação IA com IA
        """
        try:
            # Usar IA para gerar resposta
            ai_service = self.get_ai_service()
            if ai_service:
                resposta_ia = ai_service.obter_mensagem_ajuda()
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar botões
            await self.enviar_botoes_demo(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar demo com IA: {e}")
            await self.enviar_erro(db, user, f"Erro na demo: {str(e)}")
    
    async def iniciar_verificacao_real_ia(self, db: Session, user):
        """
        Inicia verificação real com IA
        """
        try:
            # Usar IA para gerar resposta
            ai_service = self.get_ai_service()
            if ai_service:
                resposta_ia = ai_service.obter_mensagem_ajuda()
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar botões
            await self.enviar_botoes_verificacao(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar verificação com IA: {e}")
            await self.enviar_erro(db, user, f"Erro na verificação: {str(e)}")
    
    async def mostrar_sobre_agentes_ia(self, db: Session, user):
        """
        Mostra informações sobre agentes com IA
        """
        try:
            # Usar IA para gerar resposta
            ai_service = self.get_ai_service()
            if ai_service:
                resposta_ia = ai_service.obter_mensagem_ajuda()
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar botões
            await self.enviar_botoes_voltar(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar agentes com IA: {e}")
            await self.enviar_erro(db, user, f"Erro nos agentes: {str(e)}")
    
    async def iniciar_teste_imagem_ia(self, db: Session, user):
        """
        Inicia teste de imagem com IA
        """
        try:
            # Usar IA para gerar resposta
            ai_service = self.get_ai_service()
            if ai_service:
                resposta_ia = ai_service.obter_mensagem_ajuda()
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar botões
            await self.enviar_botoes_voltar(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar teste de imagem com IA: {e}")
            await self.enviar_erro(db, user, f"Erro no teste: {str(e)}")
    
    async def iniciar_teste_pix_ia(self, db: Session, user):
        """
        Inicia teste de PIX com IA
        """
        try:
            # Usar IA para gerar resposta
            ai_service = self.get_ai_service()
            if ai_service:
                resposta_ia = ai_service.obter_mensagem_ajuda()
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar botões
            await self.enviar_botoes_voltar(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar teste de PIX com IA: {e}")
            await self.enviar_erro(db, user, f"Erro no teste: {str(e)}")
    
    async def mostrar_relatorio_ia(self, db: Session, user):
        """
        Mostra relatório com IA
        """
        try:
            # Usar IA para gerar resposta
            ai_service = self.get_ai_service()
            if ai_service:
                resposta_ia = ai_service.obter_mensagem_ajuda()
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar botões
            await self.enviar_botoes_voltar(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar relatório com IA: {e}")
            await self.enviar_erro(db, user, f"Erro no relatório: {str(e)}")
    
    async def enviar_opcao_invalida_ia(self, db: Session, user):
        """
        Envia mensagem de opção inválida com IA
        """
        try:
            # Usar IA para gerar resposta
            ai_service = self.get_ai_service()
            if ai_service:
                resposta_ia = ai_service.obter_mensagem_ajuda()
                await whatsapp_service.send_message(
                    phone_number=user.phone_number,
                    message=resposta_ia,
                    log_to_db=True,
                    user_id=user.id,
                    db=db
                )
            
            # Enviar botões
            await self.enviar_botoes_voltar(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao enviar opção inválida com IA: {e}")
            await self.enviar_erro(db, user, f"Erro na opção: {str(e)}")
    
    # Métodos auxiliares para botões
    async def enviar_botoes_demo(self, db: Session, user):
        """
        Envia botões para demo
        """
        try:
            phone_number = "5591981960045" if user.phone_number == "559181960045" else user.phone_number
            
            buttons = [
                {"id": "teste_imagem", "title": "Imagem"},
                {"id": "teste_pix", "title": "PIX"},
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=phone_number,
                body_text="Escolha o tipo de teste:",
                buttons=buttons,
                log_to_db=False
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar botões demo: {e}")
    
    async def enviar_botoes_verificacao(self, db: Session, user):
        """
        Envia botões para verificação
        """
        try:
            phone_number = "5591981960045" if user.phone_number == "559181960045" else user.phone_number
            
            buttons = [
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=phone_number,
                body_text="Envie seu documento ou clique para voltar:",
                buttons=buttons,
                log_to_db=False
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar botões verificação: {e}")
    
    async def enviar_botoes_voltar(self, db: Session, user):
        """
        Envia botão de voltar
        """
        try:
            phone_number = "5591981960045" if user.phone_number == "559181960045" else user.phone_number
            
            buttons = [
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=phone_number,
                body_text="Clique para voltar ao menu:",
                buttons=buttons,
                log_to_db=False
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar botão voltar: {e}")
    
    async def iniciar_demo_verificacao(self, db: Session, user):
        """
        Inicia demonstração da verificação IA
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="🎯 **Demo - Verificação IA**\n\n"
                       "Vou demonstrar como nossos agentes especializados funcionam:\n\n"
                       "1️⃣ **Agente Leitor** - Extrai dados com OCR\n"
                       "2️⃣ **Agente Consultor** - Valida nos sistemas Bemobi\n"
                       "3️⃣ **Agente Detetive** - Detecta fraudes\n"
                       "4️⃣ **Agente Orquestrador** - Consolida resultado\n\n"
                       "Escolha o tipo de teste:",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Botões para tipos de teste
            buttons = [
                {"id": "teste_imagem", "title": "Imagem"},
                {"id": "teste_pix", "title": "PIX"},
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=user.phone_number,
                body_text="Escolha o tipo de teste:",
                buttons=buttons,
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao iniciar demo: {e}")
            await self.enviar_erro(db, user, f"Erro ao iniciar demo: {str(e)}")
    
    async def iniciar_teste_imagem(self, db: Session, user):
        """
        Inicia teste com imagem simulada
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="📸 **Teste com Imagem**\n\n"
                       "Para testar com uma imagem real, envie uma foto de boleto.\n\n"
                       "Para demonstração, vou simular uma verificação:",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Simular verificação
            await self.simular_verificacao(db, user, "imagem")
            
        except Exception as e:
            logger.error(f"Erro no teste de imagem: {e}")
            await self.enviar_erro(db, user, f"Erro no teste: {str(e)}")
    
    async def iniciar_teste_pix(self, db: Session, user):
        """
        Inicia teste com dados PIX simulados
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="📋 **Teste com PIX**\n\n"
                       "Para testar com dados PIX reais, envie os dados.\n\n"
                       "Para demonstração, vou simular uma verificação:",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Simular verificação
            await self.simular_verificacao(db, user, "pix")
            
        except Exception as e:
            logger.error(f"Erro no teste PIX: {e}")
            await self.enviar_erro(db, user, f"Erro no teste: {str(e)}")
    
    async def simular_verificacao(self, db: Session, user, tipo: str):
        """
        Simula verificação completa para demonstração
        """
        try:
            # Dados simulados para demonstração
            dados_simulados = {
                "valor": "R$ 89,90",
                "beneficiario": "Bemobi Tecnologia",
                "vencimento": "15/12/2024",
                "status": "seguro"
            }
            
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="🤖 **Iniciando Análise com Agentes IA**\n\n"
                       "⏳ Agente Leitor: Extraindo dados...\n"
                       "⏳ Agente Consultor: Validando sistemas...\n"
                       "⏳ Agente Detetive: Detectando fraudes...\n"
                       "⏳ Agente Orquestrador: Consolidando...",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Simular tempo de processamento
            import asyncio
            await asyncio.sleep(2)
            
            # Enviar resultado simulado
            await self.enviar_resultado_simulado(db, user, dados_simulados)
            
        except Exception as e:
            logger.error(f"Erro na simulação: {e}")
            await self.enviar_erro(db, user, f"Erro na simulação: {str(e)}")
    
    async def enviar_resultado_simulado(self, db: Session, user, dados: Dict[str, Any]):
        """
        Envia resultado simulado da verificação
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="✅ **Verificação Concluída**\n\n"
                       f"📊 **Resultado:** {dados['status'].upper()}\n"
                       f"💰 **Valor:** {dados['valor']}\n"
                       f"🏢 **Beneficiário:** {dados['beneficiario']}\n"
                       f"📅 **Vencimento:** {dados['vencimento']}\n\n"
                       "**Análise dos Agentes:**\n"
                       "🔍 Leitor: Dados extraídos com sucesso\n"
                       "🏦 Consultor: Validação nos sistemas OK\n"
                       "🛡️ Detetive: Nenhuma fraude detectada\n"
                       "📊 Orquestrador: Confiança 95%",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Botões de ação
            buttons = [
                {"id": "ver_relatorio", "title": "Relatório"},
                {"id": "nova_verificacao", "title": "Nova Verificação"},
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=user.phone_number,
                body_text="Escolha uma ação:",
                buttons=buttons,
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar resultado: {e}")
            await self.enviar_erro(db, user, f"Erro ao enviar resultado: {str(e)}")
    
    async def iniciar_verificacao_real(self, db: Session, user):
        """
        Inicia verificação real com agentes
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="🔍 **Verificação Real**\n\n"
                       "Para verificar uma cobrança real, envie:\n"
                       "📸 Uma foto do boleto\n"
                       "📋 Os dados do PIX\n"
                       "📄 Um documento\n\n"
                       "Nossos agentes especializados irão analisar automaticamente!",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Botão para voltar
            buttons = [
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=user.phone_number,
                body_text="Envie seu documento ou clique para voltar:",
                buttons=buttons,
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao iniciar verificação real: {e}")
            await self.enviar_erro(db, user, f"Erro ao iniciar verificação: {str(e)}")
    
    async def mostrar_sobre_agentes(self, db: Session, user):
        """
        Mostra informações sobre os agentes
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="🤖 **Sobre os Agentes IA**\n\n"
                       "**🔍 Agente Leitor**\n"
                       "• Extrai dados usando OCR avançado\n"
                       "• Detecta características suspeitas\n"
                       "• Analisa qualidade da imagem\n\n"
                       "**🏦 Agente Consultor**\n"
                       "• Valida nos sistemas Bemobi\n"
                       "• Verifica beneficiários legítimos\n"
                       "• Confere valores de cobrança\n\n"
                       "**🛡️ Agente Detetive**\n"
                       "• Detecta padrões de fraude\n"
                       "• Consulta bases de golpes\n"
                       "• Analisa reclamações do mercado\n\n"
                       "**📊 Agente Orquestrador**\n"
                       "• Consolida resultados\n"
                       "• Calcula pontuação de confiança\n"
                       "• Gera decisão final",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Botão para voltar
            buttons = [
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=user.phone_number,
                body_text="Clique para voltar ao menu:",
                buttons=buttons,
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao mostrar sobre agentes: {e}")
            await self.enviar_erro(db, user, f"Erro ao mostrar informações: {str(e)}")
    
    async def mostrar_suporte(self, db: Session, user):
        """
        Mostra informações de suporte
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="📞 **Suporte Bemobi**\n\n"
                       "**Horário de Atendimento:**\n"
                       "Segunda a Sexta: 8h às 18h\n\n"
                       "**Canais de Contato:**\n"
                       "📧 Email: suporte@bemobi.com\n"
                       "📱 WhatsApp: (11) 99999-9999\n"
                       "🌐 Site: www.bemobi.com\n\n"
                       "**Emergências:**\n"
                       "Para casos de fraude, contate imediatamente!",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Botão para voltar
            buttons = [
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=user.phone_number,
                body_text="Clique para voltar ao menu:",
                buttons=buttons,
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao mostrar suporte: {e}")
            await self.enviar_erro(db, user, f"Erro ao mostrar suporte: {str(e)}")
    
    async def mostrar_relatorio(self, db: Session, user):
        """
        Mostra relatório detalhado
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="📊 **Relatório Detalhado**\n\n"
                       "**Análise dos Agentes:**\n\n"
                       "🔍 **Agente Leitor**\n"
                       "• Status: ✅ Sucesso\n"
                       "• Dados extraídos: 8/8 campos\n"
                       "• Qualidade OCR: 95%\n\n"
                       "🏦 **Agente Consultor**\n"
                       "• Status: ✅ Sucesso\n"
                       "• Cliente validado: ✅\n"
                       "• Beneficiário legítimo: ✅\n"
                       "• Valor conferido: ✅\n\n"
                       "🛡️ **Agente Detetive**\n"
                       "• Status: ✅ Sucesso\n"
                       "• Fraudes detectadas: 0\n"
                       "• Padrões suspeitos: 0\n"
                       "• Risco: Baixo (5%)\n\n"
                       "📊 **Agente Orquestrador**\n"
                       "• Pontuação final: 95%\n"
                       "• Status: SEGURO\n"
                       "• Recomendação: Pode pagar",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Botões de ação
            buttons = [
                {"id": "nova_verificacao", "title": "Nova Verificação"},
                {"id": "voltar_menu", "title": "Voltar"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=user.phone_number,
                body_text="Escolha uma ação:",
                buttons=buttons,
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao mostrar relatório: {e}")
            await self.enviar_erro(db, user, f"Erro ao mostrar relatório: {str(e)}")
    
    async def enviar_opcao_invalida(self, db: Session, user):
        """
        Envia mensagem para opção inválida
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="❌ **Opção Inválida**\n\n"
                       "Por favor, selecione uma das opções disponíveis nos botões.",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar opção inválida: {e}")
    
    async def enviar_erro(self, db: Session, user, erro: str):
        """
        Envia mensagem de erro
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=f"❌ **Erro**\n\n{erro}\n\nTente novamente ou entre em contato com o suporte.",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de erro: {e}")
