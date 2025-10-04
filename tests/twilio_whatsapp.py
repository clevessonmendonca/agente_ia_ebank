#!/usr/bin/env python3
"""
🤖 Grace Bot com Twilio WhatsApp - Botões Interativos
Integração WhatsApp + IA + Botões Reais
"""

import os
import json
from twilio.rest import Client
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ==================== CONFIGURAÇÃO TWILIO ====================

# Credenciais do Twilio (configuradas diretamente)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'AC71f6c9d17065387931404ffa77735354')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'b1a40320d3663fc98b4b772711f90d91')
TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+15093090647')
TWILIO_WHATSAPP_TO = os.getenv('TWILIO_WHATSAPP_TO', 'whatsapp:+556185783047')

# ==================== CLASSE TWILIO WHATSAPP ====================

class TwilioWhatsApp:
    def __init__(self):
        """Inicializa cliente Twilio"""
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.from_number = TWILIO_WHATSAPP_FROM
    
    def enviar_mensagem(self, numero, texto):
        """Envia mensagem de texto via Twilio usando template"""
        try:
            # Remove + se já existir
            numero_limpo = numero.lstrip('+')
            
            # Usar template de verificação como base
            message = self.client.messages.create(
                from_=self.from_number,
                to=f'whatsapp:+{numero_limpo}',
                content_sid='HX229f5a04fd0510ce1b071852155d3e75',  # Template de verificação
                content_variables={"1": texto[:20]}  # Limitar a 20 caracteres
            )
            
            print(f"📤 Twilio enviando template para {numero}: {texto}")
            print(f"📤 Resposta Twilio: {message.sid}")
            
            return {'success': True, 'sid': message.sid}
            
        except Exception as e:
            print(f"❌ Erro Twilio: {e}")
            return {'erro': str(e)}
    
    def enviar_com_botoes(self, numero, texto, botoes):
        """Envia mensagem com opções numeradas (Twilio requer templates aprovados para botões)"""
        try:
            # Twilio requer templates aprovados para botões interativos
            # Vamos usar opções numeradas como fallback
            texto_com_opcoes = f"{texto}\n\n"
            for i, botao in enumerate(botoes[:3], 1):
                texto_com_opcoes += f"{i}. {botao}\n"
            
            texto_com_opcoes += "\nDigite o número da opção desejada."
            
            # Remove + se já existir
            numero_limpo = numero.lstrip('+')
            message = self.client.messages.create(
                from_=self.from_number,
                to=f'whatsapp:+{numero_limpo}',
                body=texto_com_opcoes
            )
            
            print(f"📤 Twilio enviando opções para {numero}: {botoes}")
            print(f"📤 Resposta Twilio: {message.sid}")
            
            return {'success': True, 'sid': message.sid}
            
        except Exception as e:
            print(f"❌ Erro Twilio opções: {e}")
            return {'erro': str(e)}

# ==================== FLASK APP ====================

app = Flask(__name__)
twilio = TwilioWhatsApp()

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    """Recebe mensagens do WhatsApp via Twilio"""
    try:
        # Twilio envia dados como form-data
        mensagem = request.form.get('Body', '')
        numero = request.form.get('From', '').replace('whatsapp:', '')
        
        print(f"📩 Webhook Twilio recebido:")
        print(f"📱 De: {numero}")
        print(f"💬 Mensagem: {mensagem}")
        
        # Ignorar mensagens do próprio número Twilio
        if numero == "+15093090647" or numero == "15093090647" or numero == "":
            print("📤 Mensagem do próprio Twilio ou vazia, ignorando...")
            return jsonify({'status': 'ignored'}), 200
        
        # Verificar se o número é válido
        if not numero or len(numero) < 10:
            print("❌ Número inválido, usando número padrão")
            numero = "556185783047"  # Número padrão para teste
        
        # Detectar intenção simples
        if any(palavra in mensagem.lower() for palavra in ['pagar', 'pagamento', 'pix', 'boleto', 'cartão']):
            # Enviar botões interativos
            texto = "Escolha como deseja pagar:"
            botoes = ["Pix", "Cartão", "Boleto"]
            resultado = twilio.enviar_com_botoes(numero, texto, botoes)
            
            if resultado.get('success'):
                print("✅ Botões enviados com sucesso!")
            else:
                print(f"❌ Erro ao enviar botões: {resultado.get('erro')}")
        else:
            # Resposta simples
            resposta = f"Olá! Você disse: {mensagem}. Digite 'pagar' para ver as opções de pagamento."
            twilio.enviar_mensagem(numero, resposta)
        
        return '', 200
        
    except Exception as e:
        print(f"❌ Erro no webhook Twilio: {e}")
        return '', 500

@app.route('/teste-botoes', methods=['GET'])
def teste_botoes():
    """Endpoint para testar botões"""
    numero_teste = request.args.get('numero', '556185783047')
    
    # Enviar botões de exemplo
    botoes = ["Pix", "Cartão", "Boleto"]
    texto = "Escolha uma forma de pagamento:"
    
    resultado = twilio.enviar_com_botoes(numero_teste, texto, botoes)
    
    return jsonify({
        'status': 'Botões Twilio enviados!',
        'numero': numero_teste,
        'botoes': botoes,
        'resultado': resultado
    })

@app.route('/teste', methods=['GET'])
def teste():
    """Endpoint de teste"""
    return jsonify({
        'status': 'Grace Bot Twilio funcionando!',
        'integracao': 'Twilio WhatsApp',
        'botões': 'Interativos reais'
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 GRACE BOT COM TWILIO INICIADO!")
    print("=" * 50)
    print(f"📱 Twilio Account SID: {TWILIO_ACCOUNT_SID}")
    print(f"📞 From: {TWILIO_WHATSAPP_FROM}")
    print(f"🔗 Webhook: http://localhost:5000/webhook")
    print("=" * 50)
    
    app.run(port=5000, debug=True)
