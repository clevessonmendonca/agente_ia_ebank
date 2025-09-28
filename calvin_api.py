#!/usr/bin/env python3
"""
CALVIN API - Servidor robusto e modular para integração
Backend facilmente adaptável para diferentes tecnologias
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from calvin_agent import calvin, CalvinSpecialty
import json
import logging
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Simulação de integrações Bemobi (interfaces modulares)
class BemobiIntegrations:
    """
    Interfaces modulares para tecnologias Bemobi
    Facilmente substituíveis por implementações reais
    """
    
    @staticmethod
    def smart_checkout_config(user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Simula integração com Smart Checkout"""
        country = user_context.get('country', 'Brazil')
        
        if country == 'Brazil':
            return {
                "methods": ["pix", "cartao_credito", "cartao_debito", "boleto"],
                "recommended": "pix",
                "cashback_partners": ["Nubank", "Inter", "C6"],
                "ui_theme": "brazilian"
            }
        elif country == 'Mexico':
            return {
                "methods": ["oxxo", "spei", "tarjeta_credito", "tarjeta_debito"],
                "recommended": "oxxo",
                "cashback_partners": ["BBVA", "Santander"],
                "ui_theme": "mexican"
            }
        else:
            return {
                "methods": ["credit_card", "debit_card", "bank_transfer"],
                "recommended": "credit_card",
                "cashback_partners": [],
                "ui_theme": "international"
            }
    
    @staticmethod
    def grace_context(user_id: str) -> Dict[str, Any]:
        """Simula integração com Grace para contexto conversacional"""
        return {
            "user_id": user_id,
            "conversation_history": ["Último pagamento há 15 dias", "Preferência por WhatsApp"],
            "language_preference": "pt-BR",
            "tone_preference": "casual",
            "last_interaction": "2024-01-15T10:30:00Z"
        }
    
    @staticmethod
    def betrusty_risk_score(user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Simula integração com BeTrusty para análise de risco"""
        # Simular score baseado em contexto
        risk_factors = []
        score = 0.1  # Base baixa
        
        if user_context.get('new_device'):
            risk_factors.append("Novo dispositivo")
            score += 0.3
        
        if user_context.get('unusual_location'):
            risk_factors.append("Localização incomum")
            score += 0.4
        
        if user_context.get('high_amount'):
            risk_factors.append("Valor alto")
            score += 0.2
        
        return {
            "risk_score": min(score, 1.0),
            "risk_level": "high" if score > 0.7 else "medium" if score > 0.3 else "low",
            "factors": risk_factors,
            "recommended_auth": "biometric" if score > 0.7 else "otp" if score > 0.3 else "none"
        }
    
    @staticmethod
    def mcps_channel_optimization(user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Simula integração com MCPS para otimização de canal"""
        age = user_context.get('age', 30)
        
        if age >= 65:
            return {
                "preferred_channel": "whatsapp",
                "backup_channels": ["phone", "sms"],
                "ui_mode": "assisted",
                "response_time": "slow"
            }
        elif age >= 40:
            return {
                "preferred_channel": "app",
                "backup_channels": ["whatsapp", "email"],
                "ui_mode": "standard",
                "response_time": "medium"
            }
        else:
            return {
                "preferred_channel": "app",
                "backup_channels": ["whatsapp", "push"],
                "ui_mode": "advanced",
                "response_time": "fast"
            }

# Rotas da API
@app.route('/', methods=['GET'])
def home():
    """Documentação da API CALVIN"""
    return jsonify({
        "name": "🤖 CALVIN API - Agente de IA Contextual",
        "version": "1.0.0",
        "description": "Backend modular para agente de IA com especialidades contextuais",
        "hackathon": "Bemobi 2025",
        "specialties": [
            "onboarding - Boas-vindas e configuração inicial",
            "payments - Pagamentos e educação financeira",
            "security - Segurança e antifraude",
            "relationship - Relacionamento e retenção",
            "assisted - Modalidade inclusiva para idosos"
        ],
        "integrations": [
            "AWS Bedrock - Motor de IA",
            "Smart Checkout - Interface de pagamentos",
            "Grace - Contexto conversacional",
            "BeTrusty - Análise de risco",
            "MCPS - Otimização multicanal"
        ],
        "endpoints": {
            "smart_chat": "POST /calvin/chat - Chat inteligente com detecção automática",
            "specialty_chat": "POST /calvin/{specialty} - Chat com especialidade específica",
            "health": "GET /health - Status dos serviços",
            "demo": "GET /demo/* - Demonstrações para hackathon"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Status de saúde da API"""
    try:
        # Teste rápido do CALVIN
        test_response = calvin.smart_response("teste", {"country": "Brazil"})
        calvin_status = "healthy" if test_response["status"] == "success" else "degraded"
        
        return jsonify({
            "status": "healthy",
            "calvin_agent": calvin_status,
            "bedrock_model": calvin.model_id,
            "specialties_available": len(calvin.specialty_contexts),
            "integrations": {
                "smart_checkout": "simulated",
                "grace": "simulated", 
                "betrusty": "simulated",
                "mcps": "simulated"
            }
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/calvin/chat', methods=['POST'])
def smart_chat():
    """Chat inteligente com detecção automática de especialidade"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        user_context = data.get('user_context', {})
        
        if not message:
            return jsonify({"error": "Mensagem é obrigatória"}), 400
        
        # Enriquecer contexto com integrações Bemobi
        enriched_context = _enrich_user_context(user_context)
        
        # Resposta inteligente do CALVIN
        response = calvin.smart_response(message, enriched_context)
        
        # Adicionar recomendações contextuais
        recommendations = _generate_contextual_recommendations(response, enriched_context)
        
        return jsonify({
            "status": response["status"],
            "response": response.get("response", ""),
            "specialty_used": response.get("specialty", ""),
            "model": response.get("model", ""),
            "user_context": enriched_context,
            "recommendations": recommendations
        })
        
    except Exception as e:
        logger.error(f"Erro no smart chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/calvin/<specialty>', methods=['POST'])
def specialty_chat(specialty):
    """Chat com especialidade específica"""
    try:
        # Validar especialidade
        try:
            calvin_specialty = CalvinSpecialty(specialty)
        except ValueError:
            return jsonify({"error": f"Especialidade '{specialty}' não existe"}), 400
        
        data = request.get_json()
        message = data.get('message', '')
        user_context = data.get('user_context', {})
        
        if not message:
            return jsonify({"error": "Mensagem é obrigatória"}), 400
        
        # Enriquecer contexto
        enriched_context = _enrich_user_context(user_context)
        
        # Resposta com especialidade forçada
        response = calvin.invoke_with_specialty(message, calvin_specialty, enriched_context)
        
        # Adicionar recomendações
        recommendations = _generate_contextual_recommendations(response, enriched_context)
        
        return jsonify({
            "status": response["status"],
            "response": response.get("response", ""),
            "specialty_forced": specialty,
            "model": response.get("model", ""),
            "user_context": enriched_context,
            "recommendations": recommendations
        })
        
    except Exception as e:
        logger.error(f"Erro no specialty chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

def _enrich_user_context(user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Enriquece contexto do usuário com integrações Bemobi"""
    enriched = user_context.copy()
    
    # Adicionar configuração Smart Checkout
    enriched['smart_checkout'] = BemobiIntegrations.smart_checkout_config(user_context)
    
    # Adicionar contexto Grace se tiver user_id
    if user_context.get('user_id'):
        enriched['grace_context'] = BemobiIntegrations.grace_context(user_context['user_id'])
    
    # Adicionar análise de risco BeTrusty
    enriched['risk_analysis'] = BemobiIntegrations.betrusty_risk_score(user_context)
    
    # Adicionar otimização de canal MCPS
    enriched['channel_optimization'] = BemobiIntegrations.mcps_channel_optimization(user_context)
    
    return enriched

def _generate_contextual_recommendations(response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Gera recomendações baseadas na resposta e contexto"""
    recommendations = {}
    
    specialty = response.get('specialty', '')
    
    if specialty == 'onboarding':
        recommendations['next_steps'] = [
            "Configurar método de pagamento preferido",
            "Ativar notificações",
            "Explorar programas de fidelidade"
        ]
        recommendations['smart_checkout'] = context.get('smart_checkout', {})
    
    elif specialty == 'payments':
        recommendations['payment_optimization'] = {
            "recommended_method": context.get('smart_checkout', {}).get('recommended', 'pix'),
            "cashback_available": True,
            "estimated_savings": "R$ 5,00 por mês"
        }
    
    elif specialty == 'security':
        risk_level = context.get('risk_analysis', {}).get('risk_level', 'low')
        recommendations['security_actions'] = {
            "risk_level": risk_level,
            "recommended_auth": context.get('risk_analysis', {}).get('recommended_auth', 'none'),
            "immediate_action": risk_level == 'high'
        }
    
    elif specialty == 'relationship':
        recommendations['retention_offers'] = [
            "Desconto de 10% na próxima fatura",
            "Upgrade gratuito por 3 meses",
            "Suporte prioritário"
        ]
    
    elif specialty == 'assisted':
        recommendations['assistance_options'] = {
            "human_support": "Disponível via telefone",
            "family_notification": "Pode avisar familiar designado",
            "simplified_interface": "Ativada automaticamente"
        }
    
    return recommendations

# Rotas de demonstração para hackathon
@app.route('/demo/yduqs-students', methods=['GET'])
def demo_yduqs():
    """Demo: Estudantes YDUQS em risco"""
    context = {
        "country": "Brazil",
        "user_type": "student",
        "risk_profile": "medium",
        "overdue_days": 12
    }
    
    message = "Tenho uma mensalidade em atraso, mas sou estudante e está difícil pagar"
    response = calvin.smart_response(message, context)
    
    return jsonify({
        "scenario": "YDUQS - Estudantes em Risco",
        "message": message,
        "calvin_response": response.get("response", ""),
        "specialty_used": response.get("specialty", ""),
        "context": context,
        "bemobi_integration": "Grace + Smart Checkout com desconto estudantil"
    })

@app.route('/demo/sabesp-recovery', methods=['GET'])
def demo_sabesp():
    """Demo: Recuperação automática Sabesp"""
    context = {
        "country": "Brazil",
        "service_type": "utilities",
        "payment_history": "good",
        "preferred_method": "pix"
    }
    
    message = "Preciso pagar minha conta da Sabesp, qual a melhor forma?"
    response = calvin.smart_response(message, context)
    
    return jsonify({
        "scenario": "Sabesp - Recuperação Automática",
        "message": message,
        "calvin_response": response.get("response", ""),
        "specialty_used": response.get("specialty", ""),
        "context": context,
        "bemobi_integration": "Smart Checkout + PIX Automático"
    })

@app.route('/demo/assisted-mode', methods=['GET'])
def demo_assisted():
    """Demo: Modalidade assistida para idosos"""
    context = {
        "assisted_mode": True,
        "age": 78,
        "tech_comfort": "low",
        "family_support": True
    }
    
    message = "Meu neto disse que posso pagar as contas pelo celular, mas não sei como"
    response = calvin.smart_response(message, context)
    
    return jsonify({
        "scenario": "Modalidade Assistida - Inclusão Digital",
        "message": message,
        "calvin_response": response.get("response", ""),
        "specialty_used": response.get("specialty", ""),
        "context": context,
        "bemobi_integration": "Interface simplificada + Suporte humano integrado"
    })

@app.route('/demo/security-alert', methods=['GET'])
def demo_security():
    """Demo: Alerta de segurança"""
    context = {
        "new_device": True,
        "unusual_location": True,
        "risk_score": 0.8
    }
    
    message = "Recebi um alerta de login suspeito, o que devo fazer?"
    response = calvin.smart_response(message, context)
    
    return jsonify({
        "scenario": "Alerta de Segurança - BeTrusty Integration",
        "message": message,
        "calvin_response": response.get("response", ""),
        "specialty_used": response.get("specialty", ""),
        "context": context,
        "bemobi_integration": "BeTrusty + Autenticação adaptativa"
    })

if __name__ == '__main__':
    print("🚀 Iniciando CALVIN API...")
    print("📡 API disponível em: http://localhost:8000")
    print("📖 Documentação: http://localhost:8000")
    print("🏥 Health check: http://localhost:8000/health")
    print("\n🎯 Endpoints principais:")
    print("   POST /calvin/chat - Chat inteligente")
    print("   POST /calvin/onboarding - Especialidade onboarding")
    print("   POST /calvin/payments - Especialidade pagamentos")
    print("   POST /calvin/security - Especialidade segurança")
    print("   POST /calvin/relationship - Especialidade relacionamento")
    print("   POST /calvin/assisted - Modalidade assistida")
    print("\n🎪 Demos para hackathon:")
    print("   GET /demo/yduqs-students - Demo estudantes")
    print("   GET /demo/sabesp-recovery - Demo Sabesp")
    print("   GET /demo/assisted-mode - Demo modalidade assistida")
    print("   GET /demo/security-alert - Demo segurança")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
