#!/usr/bin/env python3
"""
CALVIN - Agente de IA Único com Especialidades Contextuais
Sistema modular que adapta o mesmo agente para diferentes funções através de contextos
"""

import boto3
import json
from typing import Dict, Any, Optional
from enum import Enum
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalvinSpecialty(Enum):
    """Especialidades do agente CALVIN através de contextos"""
    ONBOARDING = "onboarding"      # Boas-vindas e configuração inicial
    PAYMENTS = "payments"          # Pagamentos e educação financeira  
    SECURITY = "security"          # Segurança e antifraude
    RELATIONSHIP = "relationship"  # Relacionamento e retenção
    ASSISTED = "assisted"          # Modalidade inclusiva para idosos

class CalvinAgent:
    """
    Agente CALVIN único que se especializa através de contextos
    Integra com AWS Bedrock e tecnologias Bemobi
    """
    
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.max_tokens = 1500
        self.temperature = 0.7
        
        # Contextos especializados para cada função
        self.specialty_contexts = self._load_specialty_contexts()
        
        logger.info("🤖 CALVIN Agent inicializado com especialidades contextuais")
    
    def _load_specialty_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Define os contextos especializados para cada função do CALVIN"""
        return {
            CalvinSpecialty.ONBOARDING.value: {
                "system_prompt": """
                Você é CALVIN, especialista em ONBOARDING da Bemobi. Sua função é:
                
                🎯 MISSÃO: Receber novos usuários e configurar sua experiência inicial
                
                ESPECIALIDADES:
                • Identificar país, idioma e métodos de pagamento locais
                • Adaptar interface para cultura local (Pix no Brasil, Oxxo no México)
                • Integrar com Smart Checkout personalizado
                • Detectar canal preferido (WhatsApp, App, Web)
                • Configurar programas de fidelidade de parceiros
                
                INTEGRAÇÕES BEMOBI:
                • MCPS (Multi-Channel Platform Service) para omnicanalidade
                • Smart Checkout para personalização de pagamentos
                • Grace para continuidade conversacional
                
                PERSONALIDADE: Acolhedor, paciente, didático
                LINGUAGEM: Adaptada ao país/cultura do usuário
                """,
                "temperature": 0.8,
                "max_tokens": 1200
            },
            
            CalvinSpecialty.PAYMENTS.value: {
                "system_prompt": """
                Você é CALVIN, especialista em PAGAMENTOS da Bemobi. Sua função é:
                
                🎯 MISSÃO: Otimizar pagamentos e educar financeiramente
                
                ESPECIALIDADES:
                • Recomendar melhor método de pagamento (contexto + histórico)
                • Simular custos, taxas, cashback e pontos de fidelidade
                • Explicar impactos financeiros de cada escolha
                • Integrar com programas de parceiros (bancos, cartões)
                • Configurar recorrência, agendamentos e split payments
                
                INTEGRAÇÕES BEMOBI:
                • Smart Checkout como interface visual
                • APIs de parceiros para cashback/pontos
                • Sistema de simulação de custos em tempo real
                
                PERSONALIDADE: Educativo, transparente, orientado a valor
                LINGUAGEM: Clara sobre custos e benefícios
                """,
                "temperature": 0.6,
                "max_tokens": 1000
            },
            
            CalvinSpecialty.SECURITY.value: {
                "system_prompt": """
                Você é CALVIN, especialista em SEGURANÇA da Bemobi. Sua função é:
                
                🎯 MISSÃO: Proteger usuários com segurança adaptativa
                
                ESPECIALIDADES:
                • Detectar comportamentos suspeitos (novo dispositivo, localização)
                • Aplicar autenticação adaptativa (biometria, OTP, voz)
                • Explicar medidas de segurança de forma transparente
                • Prevenir fraudes e golpes com educação
                • Monitorar e alertar sobre acessos incomuns
                
                INTEGRAÇÕES BEMOBI:
                • BeTrusty para análise de risco em tempo real
                • Sistemas de autenticação multimodal
                • Logs transparentes de acesso e atividade
                
                PERSONALIDADE: Vigilante, transparente, educativo sobre segurança
                LINGUAGEM: Clara sobre riscos sem causar pânico
                """,
                "temperature": 0.4,
                "max_tokens": 800
            },
            
            CalvinSpecialty.RELATIONSHIP.value: {
                "system_prompt": """
                Você é CALVIN, especialista em RELACIONAMENTO da Bemobi. Sua função é:
                
                🎯 MISSÃO: Manter engajamento e prevenir churn
                
                ESPECIALIDADES:
                • Manter contexto entre canais (app → WhatsApp → web)
                • Detectar sinais de churn (redução uso, atrasos, reclamações)
                • Oferecer incentivos personalizados e recompensas
                • Retomar fluxos interrompidos automaticamente
                • Gerenciar programas de fidelidade e benefícios
                
                INTEGRAÇÕES BEMOBI:
                • Grace para memória conversacional
                • MCPS para continuidade entre canais
                • APIs de parceiros para ofertas exclusivas
                
                PERSONALIDADE: Empático, proativo, focado em relacionamento
                LINGUAGEM: Personalizada baseada no histórico do usuário
                """,
                "temperature": 0.7,
                "max_tokens": 1200
            },
            
            CalvinSpecialty.ASSISTED.value: {
                "system_prompt": """
                Você é CALVIN, especialista em MODALIDADE ASSISTIDA da Bemobi. Sua função é:
                
                🎯 MISSÃO: Democratizar acesso digital para idosos e pessoas com dificuldades tecnológicas
                
                ESPECIALIDADES:
                • Linguagem ultra-simplificada e empática
                • Explicações passo-a-passo com paciência infinita
                • Interface "tatibitate" - uma informação por vez
                • Conexão fácil com suporte humano quando necessário
                • Proteção extra contra golpes (idosos são alvos frequentes)
                
                CARACTERÍSTICAS ESPECIAIS:
                • Sem pressa - usuário define o ritmo
                • Confirmações redundantes para segurança
                • Linguagem familiar e acolhedora
                • Opção de áudio para quem tem dificuldade de leitura
                • Integração com familiares designados
                
                PERSONALIDADE: Extremamente paciente, carinhoso, protetor
                LINGUAGEM: Simples, sem jargões, como conversar com um neto querido
                """,
                "temperature": 0.9,
                "max_tokens": 1500
            }
        }
    
    def invoke_with_specialty(self, 
                            message: str, 
                            specialty: CalvinSpecialty,
                            user_context: Optional[Dict[str, Any]] = None,
                            custom_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoca o agente CALVIN com especialidade específica
        """
        try:
            # Obter contexto da especialidade
            specialty_config = self.specialty_contexts[specialty.value]
            system_prompt = specialty_config["system_prompt"]
            
            # Adicionar contexto do usuário se fornecido
            if user_context:
                context_info = f"\n\nCONTEXTO DO USUÁRIO:\n{json.dumps(user_context, indent=2, ensure_ascii=False)}"
                system_prompt += context_info
            
            # Adicionar contexto customizado se fornecido
            if custom_context:
                system_prompt += f"\n\nCONTEXTO ADICIONAL:\n{custom_context}"
            
            # Preparar mensagem para Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": specialty_config.get("max_tokens", self.max_tokens),
                "temperature": specialty_config.get("temperature", self.temperature),
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
            
            logger.info(f"🎯 CALVIN ativado com especialidade: {specialty.value}")
            
            # Invocar modelo
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Processar resposta
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            return {
                "status": "success",
                "response": content,
                "specialty": specialty.value,
                "model": self.model_id,
                "usage": response_body.get('usage', {})
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no CALVIN {specialty.value}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "specialty": specialty.value,
                "model": self.model_id
            }
    
    def auto_detect_specialty(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> CalvinSpecialty:
        """
        Detecta automaticamente qual especialidade usar baseado na mensagem e contexto
        """
        message_lower = message.lower()
        
        # Verificar se usuário está em modalidade assistida
        if user_context and user_context.get('assisted_mode', False):
            return CalvinSpecialty.ASSISTED
        
        # Detectar por palavras-chave
        if any(word in message_lower for word in ['começar', 'cadastro', 'primeiro', 'novo', 'boas-vindas', 'configurar']):
            return CalvinSpecialty.ONBOARDING
        
        elif any(word in message_lower for word in ['pagar', 'pagamento', 'pix', 'cartão', 'boleto', 'custo', 'taxa']):
            return CalvinSpecialty.PAYMENTS
        
        elif any(word in message_lower for word in ['segurança', 'fraude', 'suspeito', 'bloqueio', 'senha', 'login']):
            return CalvinSpecialty.SECURITY
        
        elif any(word in message_lower for word in ['problema', 'ajuda', 'suporte', 'reclamação', 'cancelar', 'dúvida']):
            return CalvinSpecialty.RELATIONSHIP
        
        # Default para relacionamento se não detectar especialidade específica
        return CalvinSpecialty.RELATIONSHIP
    
    def smart_response(self, 
                      message: str, 
                      user_context: Optional[Dict[str, Any]] = None,
                      force_specialty: Optional[CalvinSpecialty] = None) -> Dict[str, Any]:
        """
        Resposta inteligente que detecta automaticamente a especialidade necessária
        """
        # Usar especialidade forçada ou detectar automaticamente
        specialty = force_specialty or self.auto_detect_specialty(message, user_context)
        
        # Invocar com a especialidade detectada
        return self.invoke_with_specialty(message, specialty, user_context)
    
    # Métodos de conveniência para cada especialidade
    def onboarding_response(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resposta especializada em onboarding"""
        return self.invoke_with_specialty(message, CalvinSpecialty.ONBOARDING, user_context)
    
    def payments_response(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resposta especializada em pagamentos"""
        return self.invoke_with_specialty(message, CalvinSpecialty.PAYMENTS, user_context)
    
    def security_response(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resposta especializada em segurança"""
        return self.invoke_with_specialty(message, CalvinSpecialty.SECURITY, user_context)
    
    def relationship_response(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resposta especializada em relacionamento"""
        return self.invoke_with_specialty(message, CalvinSpecialty.RELATIONSHIP, user_context)
    
    def assisted_response(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resposta especializada para modalidade assistida"""
        return self.invoke_with_specialty(message, CalvinSpecialty.ASSISTED, user_context)

# Instância global do agente
calvin = CalvinAgent()

# Funções de conveniência para uso direto
def calvin_smart_chat(message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
    """Chat inteligente que detecta automaticamente a especialidade"""
    result = calvin.smart_response(message, user_context)
    return result.get('response', 'Erro na comunicação') if result['status'] == 'success' else f"Erro: {result.get('error')}"

def calvin_onboarding(message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
    """Chat especializado em onboarding"""
    result = calvin.onboarding_response(message, user_context)
    return result.get('response', 'Erro na comunicação') if result['status'] == 'success' else f"Erro: {result.get('error')}"

def calvin_payments(message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
    """Chat especializado em pagamentos"""
    result = calvin.payments_response(message, user_context)
    return result.get('response', 'Erro na comunicação') if result['status'] == 'success' else f"Erro: {result.get('error')}"

def calvin_security(message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
    """Chat especializado em segurança"""
    result = calvin.security_response(message, user_context)
    return result.get('response', 'Erro na comunicação') if result['status'] == 'success' else f"Erro: {result.get('error')}"

def calvin_relationship(message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
    """Chat especializado em relacionamento"""
    result = calvin.relationship_response(message, user_context)
    return result.get('response', 'Erro na comunicação') if result['status'] == 'success' else f"Erro: {result.get('error')}"

def calvin_assisted(message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
    """Chat especializado para modalidade assistida"""
    result = calvin.assisted_response(message, user_context)
    return result.get('response', 'Erro na comunicação') if result['status'] == 'success' else f"Erro: {result.get('error')}"

if __name__ == "__main__":
    print("🤖 CALVIN - Agente de IA com Especialidades Contextuais")
    print("=" * 60)
    
    # Demonstração das diferentes especialidades
    test_scenarios = [
        {
            "message": "Olá! Sou novo aqui, como faço para começar?",
            "context": {"country": "Brazil", "language": "pt-BR"},
            "expected_specialty": "onboarding"
        },
        {
            "message": "Qual a melhor forma de pagar esta conta de R$ 150?",
            "context": {"balance": 500, "preferred_method": "pix"},
            "expected_specialty": "payments"
        },
        {
            "message": "Recebi um alerta de login suspeito, o que faço?",
            "context": {"risk_score": 0.8, "new_device": True},
            "expected_specialty": "security"
        },
        {
            "message": "Estou pensando em cancelar minha conta",
            "context": {"usage_decline": True, "last_payment": "30 days ago"},
            "expected_specialty": "relationship"
        },
        {
            "message": "Não entendo nada de celular, pode me ajudar devagar?",
            "context": {"assisted_mode": True, "age": 78},
            "expected_specialty": "assisted"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}️⃣ Cenário: {scenario['expected_specialty'].upper()}")
        print(f"Usuário: {scenario['message']}")
        
        response = calvin.smart_response(scenario['message'], scenario['context'])
        
        if response['status'] == 'success':
            print(f"CALVIN ({response['specialty']}): {response['response'][:200]}...")
        else:
            print(f"Erro: {response['error']}")
    
    print("\n✅ CALVIN funcionando com especialidades contextuais!")
    print("🎯 Características:")
    print("   • Um único agente que se especializa por contexto")
    print("   • Detecção automática de especialidade necessária")
    print("   • Integração com tecnologias Bemobi")
    print("   • Modalidade assistida para inclusão digital")
    print("   • Arquitetura modular e facilmente extensível")
