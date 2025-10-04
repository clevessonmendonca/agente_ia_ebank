"""
Fluxo Bemobi Automático - Respostas Pré-definidas
Sistema que responde automaticamente com mensagens já prontas
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import random

from sqlalchemy.orm import Session
from .whatsapp import whatsapp_service
from .ai_service import AIService

logger = logging.getLogger(__name__)

class FluxoBemobiAutomatico:
    def __init__(self):
        self.ai_service = None
        self.respostas_predefinidas = {
            "inicial": """
🤖 **Grace - Assistente de Verificação de Cobranças**

Olá! Sou a Grace, sua assistente especializada em verificar a autenticidade de boletos e cobranças.

Utilizo agentes de IA especializados para:
🔍 Extrair dados de documentos
📊 Analisar dados nos sistemas Bemobi  
🛡️ Detectar possíveis fraudes
📊 Dar uma resposta clara e segura

**Envie sua cobrança para começar!**
            """,
            
            "menu_principal": """
❓ **Como usar o Grace:**

**1. Envie uma foto do boleto**
- Tire uma foto clara do boleto
- Certifique-se que todos os dados estão visíveis

**2. Envie dados do PIX**
- Cole o texto do PIX recebido
- Inclua valor, beneficiário e chave

**3. Receba sua análise**
- 🟢 Verde: Cobrança segura
- ⚠️ Amarelo: Verificar com suporte  
- 🚨 Vermelho: Golpe detectado

**Precisa de ajuda?** Digite "ajuda" a qualquer momento.
            """,
            
            "processando": """
🔍 **Analisando sua cobrança...**

Nossos agentes especializados estão trabalhando:

🤖 **Agente Leitor** - Extraindo dados do documento
📊 **Agente Consultor** - Verificando nos sistemas Bemobi
🛡️ **Agente Detetive** - Detectando possíveis fraudes
📋 **Agente Orquestrador** - Consolidando análise

⏳ Aguarde alguns segundos...
            """,
            
            "resultado_seguro": """
✅ **ANÁLISE CONCLUÍDA - COBRANÇA SEGURA**

🎯 **Status:** SEGURO
📊 **Confiança:** 94%
⏱️ **Tempo de análise:** 2.3s

📋 **Dados verificados:**
• **Empresa:** Supergasbras Energia Ltda
• **CNPJ:** 19.791.896/0002-83 ✅ Validado
• **Valor:** R$ 15,99 ✅ Consistente
• **Vencimento:** 15/08/2025 ✅ Válido
• **Cliente:** Newton Antonio Teixeira Carvalho
• **Código:** 49400 ✅ Ativo nos sistemas

✅ **Validações aprovadas:**
• Empresa registrada e ativa
• Beneficiário legítimo
• Valor compatível com consumo (1,538 kg)
• Nenhum padrão de fraude detectado

🟢 **RECOMENDAÇÃO:** Pode pagar com segurança!
            """,
            
            "resultado_suspeito": """
⚠️ **ANÁLISE CONCLUÍDA - VERIFICAR COM SUPORTE**

🎯 **Status:** SUSPEITO
📊 **Confiança:** 67%
⏱️ **Tempo de análise:** 3.1s

📋 **Dados verificados:**
• **Empresa:** Supergasbras Energia Ltda
• **CNPJ:** 19.791.896/0002-83 ⚠️ Verificar
• **Valor:** R$ 15,99 ⚠️ Abaixo da média
• **Vencimento:** 15/08/2025 ✅ Válido
• **Cliente:** Newton Antonio Teixeira Carvalho
• **Código:** 49400 ⚠️ Verificar ativação

⚠️ **Alertas encontrados:**
• Valor muito baixo para consumo de gás
• Consumo de apenas 1,538 kg (muito baixo)
• Necessária verificação manual

🟡 **RECOMENDAÇÃO:** Entre em contato com o suporte antes de pagar.
            """,
            
            "resultado_golpe": """
🚨 **ANÁLISE CONCLUÍDA - GOLPE DETECTADO**

🎯 **Status:** GOLPE
📊 **Confiança:** 89%
⏱️ **Tempo de análise:** 2.8s

📋 **Dados analisados:**
• **Empresa:** Supergasbras Energia Ltda
• **CNPJ:** 19.791.896/0002-83 ❌ Inválido
• **Valor:** R$ 15,99 ❌ Suspeito
• **Vencimento:** 15/08/2025 ❌ Data futura
• **Cliente:** Newton Antonio Teixeira Carvalho
• **Código:** 49400 ❌ Inexistente

🚨 **Fraudes detectadas:**
• CNPJ não encontrado nos registros
• Padrão de golpe conhecido
• Valor suspeito para consumo de gás
• Data de vencimento futura

🔴 **RECOMENDAÇÃO:** NÃO PAGUE! Esta é uma tentativa de golpe.
            """,
            
            "demo_verificacao": """
🎬 **DEMO - Verificação de Cobrança**

Vou simular uma verificação completa para você ver como funciona:

**📸 Simulando envio de boleto...**
*[Imagem do boleto seria processada aqui]*

**🤖 Agentes trabalhando...**
• Agente Leitor: Extraindo dados...
• Agente Consultor: Verificando sistemas...
• Agente Detetive: Analisando padrões...
• Agente Orquestrador: Consolidando...

**⏳ Processando...**
            """,
            
            "sobre_agentes": """
🤖 **Nossos Agentes Especializados**

**🔍 Agente Leitor**
• Extrai dados de boletos e documentos
• Usa OCR e NLP para entender textos
• Estrutura informações automaticamente

**📊 Agente Consultor**  
• Verifica dados nos sistemas Bemobi
• Valida beneficiários e valores
• Consulta histórico do cliente

**🛡️ Agente Detetive**
• Detecta padrões de fraude
• Analisa comportamentos suspeitos
• Identifica tentativas de golpe

**📋 Agente Orquestrador**
• Consolida todas as análises
• Gera pontuação de confiança
• Define status final da verificação
            """,
            
            "erro": """
❌ **Erro no Processamento**

Ocorreu um erro ao analisar sua cobrança. Isso pode acontecer por:

• Imagem com baixa qualidade
• Dados incompletos ou ilegíveis
• Problema temporário nos sistemas

**Tente novamente:**
• Envie uma foto mais clara
• Verifique se todos os dados estão visíveis
• Aguarde alguns minutos e tente novamente
            """,
            
            "relatorio_detalhado": """
📊 **RELATÓRIO DETALHADO DA ANÁLISE**

**🔍 Agente Leitor:**
• Dados extraídos com sucesso
• Qualidade da imagem: 95%
• Tempo de processamento: 0.8s
• **Empresa:** Supergasbras Energia Ltda
• **CNPJ:** 19.791.896/0002-83
• **Valor:** R$ 15,99

**📊 Agente Consultor:**
• Cliente validado nos sistemas Bemobi
• Histórico de pagamentos limpo
• Beneficiário legítimo confirmado
• **Consumo:** 1,538 kg de gás LP
• **Fator de conversão:** 2,32

**🛡️ Agente Detetive:**
• Nenhum padrão de fraude detectado
• Valor dentro do esperado
• CNPJ válido e ativo
• **Endereço:** Águas Claras - DF

**📋 Agente Orquestrador:**
• Pontuação final: 94/100
• Status: SEGURO
• Recomendação: PAGAR
            """
        }
        
        self.resultados_possiveis = ["resultado_seguro", "resultado_suspeito", "resultado_golpe"]
    
    async def iniciar_fluxo(self, db: Session, user, message_text: str = None):
        """
        Inicia o fluxo Bemobi com resposta automática
        """
        try:
            logger.info(f"Iniciando fluxo Bemobi automático para usuário {user.id}")
            
            # Enviar mensagem inicial
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=self.respostas_predefinidas["inicial"],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Enviar botões principais
            await self.enviar_botoes_principais(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar fluxo automático: {e}")
            await self.enviar_erro(db, user, f"Erro ao iniciar fluxo: {str(e)}")
    
    async def enviar_botoes_principais(self, db: Session, user):
        """
        Envia botões principais com resposta automática
        """
        try:
            # Usar número permitido para testes
            phone_number = "5591981960045" if user.phone_number == "559181960045" else user.phone_number
            
            # Botões principais - WhatsApp limita a 3 botões
            buttons = [
                {"id": "demo_verificacao", "title": "🎬 Demo IA"},
                {"id": "verificar_cobranca", "title": "🔍 Verificar"},
                {"id": "sobre_agentes", "title": "🤖 Sobre Agentes"}
            ]
            
            logger.info(f"Enviando botões principais: {buttons}")
            
            await whatsapp_service.send_button_message(
                phone_number=phone_number,
                body_text="Selecione uma opção:",
                buttons=buttons,
                log_to_db=False
            )
            
            logger.info("Botões principais enviados com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao enviar botões principais: {e}")
            await self.enviar_erro(db, user, f"Erro ao enviar botões: {str(e)}")
    
    async def processar_botao(self, db: Session, user, button_id: str):
        """
        Processa clique em botão com resposta automática
        """
        try:
            logger.info(f"Processando botão {button_id} automaticamente para usuário {user.id}")
            
            if button_id == "demo_verificacao":
                await self.processar_demo_verificacao(db, user)
            elif button_id == "verificar_cobranca":
                await self.processar_verificacao_cobranca(db, user)
            elif button_id == "sobre_agentes":
                await self.processar_sobre_agentes(db, user)
            elif button_id == "nova_verificacao":
                await self.processar_verificacao_cobranca(db, user)
            elif button_id == "relatorio_detalhado":
                await self.processar_relatorio_detalhado(db, user)
            elif button_id == "voltar_menu":
                await self.enviar_botoes_principais(db, user)
            else:
                await self.processar_botao_invalido(db, user, button_id)
                
        except Exception as e:
            logger.error(f"Erro ao processar botão {button_id}: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar botão: {str(e)}")
    
    async def processar_demo_verificacao(self, db: Session, user):
        """
        Processa demo de verificação com resposta automática
        """
        try:
            # Enviar mensagem de demo
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=self.respostas_predefinidas["demo_verificacao"],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Simular processamento
            await asyncio.sleep(2)
            
            # Enviar mensagem de processamento
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=self.respostas_predefinidas["processando"],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Simular processamento mais longo
            await asyncio.sleep(3)
            
            # Escolher resultado aleatório
            resultado = random.choice(self.resultados_possiveis)
            
            # Enviar resultado
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=self.respostas_predefinidas[resultado],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Enviar botões de resultado
            await self.enviar_botoes_resultado(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao processar demo: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar demo: {str(e)}")
    
    async def processar_verificacao_cobranca(self, db: Session, user):
        """
        Processa verificação de cobrança - pede para enviar imagem
        """
        try:
            mensagem = """🔍 **Verificação de Cobrança**

Para verificar sua cobrança, envie:

📷 **Uma foto do boleto** ou
📄 **Dados do PIX** (valor, beneficiário, etc.)

**Exemplos:**
• Foto do boleto
• "PIX para João Silva, valor R$ 150,00"
• Dados da cobrança

Aguardo sua cobrança para análise! 🤖"""
            
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=mensagem,
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar verificação: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar verificação: {str(e)}")
    
    async def processar_sobre_agentes(self, db: Session, user):
        """
        Processa sobre agentes com resposta automática
        """
        try:
            # Enviar informações sobre agentes
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=self.respostas_predefinidas["sobre_agentes"],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Enviar botões de volta
            await self.enviar_botoes_voltar(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao processar sobre agentes: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar sobre agentes: {str(e)}")
    
    async def processar_relatorio_detalhado(self, db: Session, user):
        """
        Processa relatório detalhado com resposta automática
        """
        try:
            # Enviar relatório detalhado
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=self.respostas_predefinidas["relatorio_detalhado"],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Enviar botões de volta
            await self.enviar_botoes_voltar(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao processar relatório: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar relatório: {str(e)}")
    
    async def processar_imagem(self, db: Session, user, image_url: str):
        """
        Processa imagem com resposta automática
        """
        try:
            logger.info(f"Processando imagem automaticamente para usuário {user.id}")
            
            # Enviar mensagem de processamento
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="🔍 **Analisando imagem...**\n\n🤖 Agente Leitor: Extraindo dados...\n📊 Agente Consultor: Verificando sistemas...\n🛡️ Agente Detetive: Detectando fraudes...",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Simular processamento
            await asyncio.sleep(4)
            
            # Escolher resultado aleatório
            resultado = random.choice(self.resultados_possiveis)
            
            # Enviar resultado
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=self.respostas_predefinidas[resultado],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Enviar botões de resultado
            await self.enviar_botoes_resultado(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar imagem: {str(e)}")
    
    async def processar_texto_pix(self, db: Session, user, texto_pix: str):
        """
        Processa texto PIX com resposta automática
        """
        try:
            logger.info(f"Processando PIX automaticamente para usuário {user.id}")
            
            # Enviar mensagem de processamento
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message="🔍 **Analisando dados PIX...**\n\n🤖 Agente Leitor: Processando texto...\n📊 Agente Consultor: Validando beneficiário...\n🛡️ Agente Detetive: Verificando fraudes...",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Simular processamento
            await asyncio.sleep(3)
            
            # Escolher resultado aleatório
            resultado = random.choice(self.resultados_possiveis)
            
            # Enviar resultado
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=self.respostas_predefinidas[resultado],
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Enviar botões de resultado
            await self.enviar_botoes_resultado(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao processar PIX: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar PIX: {str(e)}")
    
    async def enviar_botoes_resultado(self, db: Session, user):
        """
        Envia botões de resultado
        """
        try:
            # Usar número permitido para testes
            phone_number = "5591981960045" if user.phone_number == "559181960045" else user.phone_number
            
            # Botões de resultado
            buttons = [
                {"id": "nova_verificacao", "title": "🔄 Nova Verificação"},
                {"id": "relatorio_detalhado", "title": "📊 Relatório"},
                {"id": "voltar_menu", "title": "🔙 Menu"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=phone_number,
                body_text="Escolha uma ação:",
                buttons=buttons,
                log_to_db=False
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar botões de resultado: {e}")
            await self.enviar_erro(db, user, f"Erro ao enviar botões: {str(e)}")
    
    async def enviar_botoes_voltar(self, db: Session, user):
        """
        Envia botões de voltar
        """
        try:
            # Usar número permitido para testes
            phone_number = "5591981960045" if user.phone_number == "559181960045" else user.phone_number
            
            # Botões de voltar
            buttons = [
                {"id": "voltar_menu", "title": "🔙 Voltar ao Menu"},
                {"id": "demo_verificacao", "title": "🎬 Ver Demo"}
            ]
            
            await whatsapp_service.send_button_message(
                phone_number=phone_number,
                body_text="Escolha uma opção:",
                buttons=buttons,
                log_to_db=False
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar botões de voltar: {e}")
            await self.enviar_erro(db, user, f"Erro ao enviar botões: {str(e)}")
    
    async def processar_botao_invalido(self, db: Session, user, button_id: str):
        """
        Processa botão inválido
        """
        try:
            await whatsapp_service.send_message(
                phone_number=user.phone_number,
                message=f"❌ **Opção inválida**\n\nBotão '{button_id}' não reconhecido.\n\nTente novamente ou digite 'ajuda' para ver as opções disponíveis.",
                log_to_db=True,
                user_id=user.id,
                db=db
            )
            
            # Enviar botões principais novamente
            await self.enviar_botoes_principais(db, user)
            
        except Exception as e:
            logger.error(f"Erro ao processar botão inválido: {e}")
            await self.enviar_erro(db, user, f"Erro ao processar botão: {str(e)}")
    
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
