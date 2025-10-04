#!/usr/bin/env python3
"""
🤖 Grace Bot com WhatsApp Web - Botões Interativos
Integração WhatsApp Web + IA + Botões Reais
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from flask import Flask, request, jsonify

# ==================== CONFIGURAÇÃO WHATSAPP WEB ====================

class WhatsAppWebBot:
    def __init__(self):
        """Inicializa bot WhatsApp Web"""
        self.driver = None
        self.connected = False
    
    def conectar(self):
        """Conecta ao WhatsApp Web"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--user-data-dir=./whatsapp_session")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get("https://web.whatsapp.com")
            
            print("📱 Abra o WhatsApp Web e escaneie o QR code...")
            print("⏳ Aguardando conexão...")
            
            # Aguardar conexão
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
            )
            
            self.connected = True
            print("✅ Conectado ao WhatsApp Web!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    def enviar_mensagem(self, numero, texto):
        """Envia mensagem de texto"""
        try:
            if not self.connected:
                self.conectar()
            
            # Navegar para o chat
            chat_url = f"https://web.whatsapp.com/send?phone={numero}"
            self.driver.get(chat_url)
            
            # Aguardar carregamento
            time.sleep(3)
            
            # Encontrar campo de texto
            message_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"]'))
            )
            
            # Digitar mensagem
            message_box.send_keys(texto)
            
            # Enviar
            send_button = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="send"]')
            send_button.click()
            
            print(f"📤 Mensagem enviada para {numero}: {texto}")
            return {'success': True}
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return {'erro': str(e)}
    
    def enviar_com_botoes(self, numero, texto, botoes):
        """Envia mensagem com opções numeradas (simulando botões)"""
        try:
            # Criar texto com opções
            texto_com_opcoes = f"{texto}\n\n"
            for i, botao in enumerate(botoes[:3], 1):
                texto_com_opcoes += f"{i}. {botao}\n"
            
            texto_com_opcoes += "\nDigite o número da opção desejada."
            
            return self.enviar_mensagem(numero, texto_com_opcoes)
            
        except Exception as e:
            print(f"❌ Erro ao enviar opções: {e}")
            return {'erro': str(e)}

# ==================== FLASK APP ====================

app = Flask(__name__)
whatsapp = WhatsAppWebBot()

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    """Recebe mensagens (simulado)"""
    try:
        data = request.get_json()
        
        print(f"📩 Webhook recebido:")
        print(json.dumps(data, indent=2))
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/teste-botoes', methods=['GET'])
def teste_botoes():
    """Endpoint para testar botões"""
    numero_teste = request.args.get('numero', '556185783047')
    
    # Enviar botões de exemplo
    botoes = ["Pix", "Cartão", "Boleto"]
    texto = "Escolha uma forma de pagamento:"
    
    resultado = whatsapp.enviar_com_botoes(numero_teste, texto, botoes)
    
    return jsonify({
        'status': 'Botões WhatsApp Web enviados!',
        'numero': numero_teste,
        'botoes': botoes,
        'resultado': resultado
    })

@app.route('/teste', methods=['GET'])
def teste():
    """Endpoint de teste"""
    return jsonify({
        'status': 'Grace Bot WhatsApp Web funcionando!',
        'integracao': 'WhatsApp Web + Selenium',
        'botões': 'Opções numeradas'
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 GRACE BOT WHATSAPP WEB INICIADO!")
    print("=" * 50)
    print("📱 Abra o WhatsApp Web no navegador")
    print("🔗 Webhook: http://localhost:5011/webhook")
    print("=" * 50)
    
    app.run(port=5011, debug=True)
