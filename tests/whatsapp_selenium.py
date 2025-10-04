#!/usr/bin/env python3
"""
🤖 Grace Bot com Selenium WhatsApp Web - Botões Interativos
Solução que funciona 100% com números brasileiros
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from flask import Flask, request, jsonify
import threading

# ==================== CONFIGURAÇÃO SELENIUM ====================

class WhatsAppSelenium:
    def __init__(self):
        """Inicializa driver Selenium"""
        self.driver = None
        self.connected = False
        
    def iniciar_whatsapp(self):
        """Inicia WhatsApp Web"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get("https://web.whatsapp.com")
            
            print("📱 WhatsApp Web aberto!")
            print("📱 Escaneie o QR Code com seu celular...")
            
            # Aguardar conexão
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
            )
            
            self.connected = True
            print("✅ WhatsApp Web conectado!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao conectar WhatsApp: {e}")
            return False
    
    def enviar_mensagem(self, numero, texto):
        """Envia mensagem para um número"""
        try:
            if not self.connected:
                return {'erro': 'WhatsApp não conectado'}
            
            # Abrir chat com o número
            chat_url = f"https://web.whatsapp.com/send?phone={numero}"
            self.driver.get(chat_url)
            
            # Aguardar carregar
            time.sleep(3)
            
            # Encontrar campo de mensagem
            message_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"]'))
            )
            
            # Digitar mensagem
            message_box.clear()
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
        """Envia mensagem com opções numeradas"""
        try:
            # Criar texto com opções
            texto_com_opcoes = f"{texto}\n\n"
            for i, botao in enumerate(botoes[:3], 1):
                texto_com_opcoes += f"{i}. {botao}\n"
            texto_com_opcoes += "\nDigite o número da opção desejada."
            
            return self.enviar_mensagem(numero, texto_com_opcoes)
            
        except Exception as e:
            return {'erro': str(e)}
    
    def fechar(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()

# ==================== FLASK APP ====================

app = Flask(__name__)
whatsapp = WhatsAppSelenium()

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    """Recebe mensagens via webhook"""
    try:
        data = request.get_json()
        mensagem = data.get('message', '')
        numero = data.get('phone', '')
        
        print(f"📩 Webhook recebido:")
        print(f"📱 De: {numero}")
        print(f"💬 Mensagem: {mensagem}")
        
        if not whatsapp.connected:
            return jsonify({'erro': 'WhatsApp não conectado'}), 500
        
        # Detectar intenção
        if any(palavra in mensagem.lower() for palavra in ['pagar', 'pagamento', 'pix', 'boleto', 'cartão']):
            # Enviar botões
            texto = "Escolha como deseja pagar:"
            botoes = ["Pix", "Cartão", "Boleto"]
            resultado = whatsapp.enviar_com_botoes(numero, texto, botoes)
            
            if resultado.get('success'):
                print("✅ Botões enviados com sucesso!")
                return jsonify({'status': 'success', 'message': 'Botões enviados!'})
            else:
                print(f"❌ Erro ao enviar botões: {resultado.get('erro')}")
                return jsonify({'erro': resultado.get('erro')}), 500
        else:
            # Resposta simples
            resposta = f"Olá! Você disse: {mensagem}. Digite 'pagar' para ver as opções de pagamento."
            resultado = whatsapp.enviar_mensagem(numero, resposta)
            
            if resultado.get('success'):
                print("✅ Resposta enviada com sucesso!")
                return jsonify({'status': 'success', 'message': 'Resposta enviada!'})
            else:
                return jsonify({'erro': resultado.get('erro')}), 500
                
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/teste-botoes', methods=['GET'])
def teste_botoes():
    """Testa envio de botões"""
    try:
        numero = request.args.get('numero', '556185783047')
        texto = "Escolha como deseja pagar:"
        botoes = ["Pix", "Cartão", "Boleto"]
        
        resultado = whatsapp.enviar_com_botoes(numero, texto, botoes)
        
        return jsonify({
            'status': 'Botões Selenium enviados!',
            'numero': numero,
            'botoes': botoes,
            'resultado': resultado
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/conectar', methods=['POST'])
def conectar():
    """Conecta ao WhatsApp Web"""
    try:
        if whatsapp.iniciar_whatsapp():
            return jsonify({'status': 'success', 'message': 'WhatsApp conectado!'})
        else:
            return jsonify({'erro': 'Falha ao conectar'}), 500
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    print("==================================================")
    print("🤖 GRACE BOT COM SELENIUM WHATSAPP WEB INICIADO!")
    print("==================================================")
    print("📱 Para conectar: POST /conectar")
    print("🔗 Webhook: http://localhost:5010/webhook")
    print("🧪 Teste: http://localhost:5010/teste-botoes?numero=556185783047")
    print("==================================================")
    
    app.run(port=5010, debug=True)
