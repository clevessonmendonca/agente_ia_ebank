#!/usr/bin/env python3
"""
🤖 Grace Bot com Baileys WhatsApp - Botões Interativos
Integração WhatsApp Web + IA + Botões Reais
"""

import asyncio
import json
from baileys import WhatsApp
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ==================== CONFIGURAÇÃO BAILEYS ====================

WHATSAPP_PHONE = os.getenv('WHATSAPP_PHONE', '556185783047')

# ==================== CLASSE BAILEYS WHATSAPP ====================

class BaileysWhatsApp:
    def __init__(self):
        """Inicializa cliente Baileys"""
        self.whatsapp = WhatsApp()
        self.connected = False
    
    async def conectar(self):
        """Conecta ao WhatsApp Web"""
        try:
            await self.whatsapp.connect()
            self.connected = True
            print("✅ Conectado ao WhatsApp Web!")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    async def enviar_mensagem(self, numero, texto):
        """Envia mensagem de texto via Baileys"""
        try:
            if not self.connected:
                await self.conectar()
            
            await self.whatsapp.send_message(
                chat_id=f"{numero}@s.whatsapp.net",
                message=texto
            )
            
            print(f"📤 Baileys enviando para {numero}: {texto}")
            return {'success': True}
            
        except Exception as e:
            print(f"❌ Erro Baileys: {e}")
            return {'erro': str(e)}
    
    async def enviar_com_botoes(self, numero, texto, botoes):
        """Envia mensagem com botões interativos via Baileys"""
        try:
            if not self.connected:
                await self.conectar()
            
            # Formato correto para botões no Baileys
            buttons_data = []
            for i, btn in enumerate(botoes[:3]):  # Máximo 3 botões
                buttons_data.append({
                    "buttonId": f"btn_{i}",
                    "buttonText": {
                        "displayText": btn
                    },
                    "type": 1
                })
            
            # Mensagem com botões
            message_data = {
                "text": texto,
                "buttons": buttons_data,
                "footer": "Grace - Bemobi"
            }
            
            await self.whatsapp.send_message(
                chat_id=f"{numero}@s.whatsapp.net",
                message=message_data
            )
            
            print(f"📤 Baileys enviando botões para {numero}: {botoes}")
            return {'success': True}
            
        except Exception as e:
            print(f"❌ Erro Baileys botões: {e}")
            return {'erro': str(e)}

# ==================== FLASK APP ====================

app = Flask(__name__)
baileys = BaileysWhatsApp()

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    """Recebe mensagens do WhatsApp via Baileys"""
    try:
        data = request.get_json()
        
        print(f"📩 Webhook Baileys recebido:")
        print(json.dumps(data, indent=2))
        
        # Processar mensagem recebida
        if 'message' in data:
            mensagem = data.get('message', {}).get('text', '')
            numero = data.get('from', '').replace('@s.whatsapp.net', '')
            
            print(f"📱 De: {numero}")
            print(f"💬 Mensagem: {mensagem}")
            
            # Detectar intenção
            if any(palavra in mensagem.lower() for palavra in ['pagar', 'pagamento', 'pix', 'boleto', 'cartão']):
                # Enviar botões interativos
                texto = "Escolha como deseja pagar:"
                botoes = ["Pix", "Cartão", "Boleto"]
                
                # Executar async
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resultado = loop.run_until_complete(baileys.enviar_com_botoes(numero, texto, botoes))
                loop.close()
                
                if resultado.get('success'):
                    print("✅ Botões enviados com sucesso!")
                else:
                    print(f"❌ Erro ao enviar botões: {resultado.get('erro')}")
            else:
                # Resposta simples
                resposta = f"Olá! Você disse: {mensagem}. Digite 'pagar' para ver as opções de pagamento."
                
                # Executar async
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                baileys.enviar_mensagem(numero, resposta)
                loop.close()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"❌ Erro no webhook Baileys: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/teste-botoes', methods=['GET'])
def teste_botoes():
    """Endpoint para testar botões"""
    numero_teste = request.args.get('numero', '556185783047')
    
    # Enviar botões de exemplo
    botoes = ["Pix", "Cartão", "Boleto"]
    texto = "Escolha uma forma de pagamento:"
    
    # Executar async
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    resultado = loop.run_until_complete(baileys.enviar_com_botoes(numero_teste, texto, botoes))
    loop.close()
    
    return jsonify({
        'status': 'Botões Baileys enviados!',
        'numero': numero_teste,
        'botoes': botoes,
        'resultado': resultado
    })

@app.route('/teste', methods=['GET'])
def teste():
    """Endpoint de teste"""
    return jsonify({
        'status': 'Grace Bot Baileys funcionando!',
        'integracao': 'Baileys WhatsApp Web',
        'botões': 'Interativos reais'
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 GRACE BOT COM BAILEYS INICIADO!")
    print("=" * 50)
    print(f"📱 WhatsApp Phone: {WHATSAPP_PHONE}")
    print(f"🔗 Webhook: http://localhost:5010/webhook")
    print("=" * 50)
    
    app.run(port=5010, debug=True)
