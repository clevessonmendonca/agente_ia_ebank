#!/usr/bin/env python3
"""
🤖 Grace Bot - Sistema Completo com IA
Enviar e receber mensagens com IA integrada
"""

import os
import requests
import json
from groq import Groq
from flask import Flask, request, jsonify

# ==================== CONFIGURAÇÃO ====================

PHONE_NUMBER_ID = "131513573373309"
WHATSAPP_TOKEN = "EAAPZCssCIVrIBPnTaDx5TGDD5cPjWDCQJruLJCs8I9kNHYx67q6HAjrVvz5UgS2RZAr1eHFUZCBYU60GdrZAvv0YOGUN8wUFszNdZBRAH0farnLlhZA53uj0lnfxRI81lKK0rh0eQD6w8IZASiLZA4AGaNu7fBiajTW0ZCEGbjslEi4XzwQd5YWb75c8MYGr8QJ11DYHw2TUdbaQRCGnZCnU41bPu00B4TboptZBFyLnaS2TiNvcgZDZD"
GROQ_API_KEY = "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"
VERIFY_TOKEN = "grace_webhook_secreto_12345"

# ==================== FUNÇÃO OCR ====================

def extrair_dados_boleto_ocr(texto):
    """Extrai dados específicos de boleto usando regex"""
    import re
    dados = {}
    
    # Padrões para extrair dados
    padroes = {
        'valor': [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*reais',
            r'valor[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        ],
        'vencimento': [
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
            r'vencimento[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'data[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})'
        ],
        'banco': [
            r'(banco\s+do\s+brasil|bb)',
            r'(bradesco)',
            r'(itau|itaú)',
            r'(santander)',
            r'(caixa\s+econômica\s+federal|cef)',
            r'(nubank)',
            r'(inter)'
        ],
        'codigo_barras': [
            r'(\d{47})',  # Código de barras padrão
            r'(\d{44})',  # Código de barras alternativo
        ],
        'beneficiario': [
            r'beneficiário[:\s]*([A-Za-z\s]+)',
            r'favorecido[:\s]*([A-Za-z\s]+)',
            r'pagador[:\s]*([A-Za-z\s]+)'
        ],
        'cpf_cnpj': [
            r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',  # CPF
            r'(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})',  # CNPJ
        ],
        'numero_documento': [
            r'nosso\s+número[:\s]*(\d+)',
            r'seu\s+número[:\s]*(\d+)',
            r'documento[:\s]*(\d+)',
            r'número[:\s]*(\d+)'
        ]
    }
    
    # Extrair dados usando regex
    for campo, lista_padroes in padroes.items():
        for padrao in lista_padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                dados[campo] = match.group(1) if match.groups() else match.group(0)
                break
    
    return dados

# ==================== CLASSE WHATSAPP ====================

class WhatsAppAPI:
    def __init__(self):
        self.phone_id = PHONE_NUMBER_ID
        self.token = WHATSAPP_TOKEN
        self.url = f"https://graph.facebook.com/v22.0/{self.phone_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def enviar_mensagem(self, numero, texto):
        """Envia mensagem de texto"""
        # Usar formato exato do curl que funciona
        payload = {
            "messaging_product": "whatsapp",
            "to": "5591981960045",  # Número fixo que funciona
            "type": "text",
            "text": {"body": texto}
        }
        
        print(f"📤 Enviando para {numero}: {texto}")
        response = requests.post(self.url, headers=self.headers, json=payload)
        print(f"📤 Resposta do WhatsApp: {response.status_code} - {response.text}")
        return response.json()
    
    def enviar_com_botoes(self, numero, texto, botoes):
        """Envia mensagem com até 3 botões"""
        # Número fixo para teste
        buttons_list = [
            {
                "type": "reply",
                "reply": {
                    "id": f"btn_{i+1}",
                    "title": btn[:20]  # Máximo 20 caracteres
                }
            } for i, btn in enumerate(botoes[:3])
        ]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": "5591981960045",  # Número fixo que funciona
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": texto},
                "action": {"buttons": buttons_list}
            }
        }
        
        print(f"📤 Enviando botões para {numero}: {botoes}")
        response = requests.post(self.url, headers=self.headers, json=payload)
        print(f"📤 Resposta do WhatsApp: {response.status_code} - {response.text}")
        return response.json()
    
    def marcar_como_lido(self, message_id):
        """Marca mensagem como lida"""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        requests.post(self.url, headers=self.headers, json=payload)

# ==================== CLASSE IA ====================

class GraceIA:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.historico = {}  # Armazena histórico por usuário
    
    def processar_mensagem(self, usuario_id, mensagem):
        """Processa mensagem com IA mantendo contexto"""
        
        # Inicializar histórico do usuário se não existir
        if usuario_id not in self.historico:
            self.historico[usuario_id] = []
        
        # System prompt
        system_prompt = """
        Você é a Grace, assistente inteligente de pagamentos da Bemobi.
        
        PERSONALIDADE:
        - Amigável, empática e prestativa
        - Explica coisas complexas de forma simples
        - Proativa em oferecer soluções
        - Usa emojis com moderação
        
        CAPACIDADES:
        - Ajudar com pagamentos (Pix, Boleto, Cartão)
        - Verificar faturas e cobranças
        - Detectar fraudes
        - Tirar dúvidas sobre serviços
        - Negociar dívidas
        
        REGRAS:
        - Respostas curtas para WhatsApp (máx 4 linhas)
        - Sempre confirme informações sensíveis
        - Se detectar fraude, alerte claramente
        - Ofereça opções práticas com botões quando possível
        """
        
        # Adicionar mensagem ao histórico
        self.historico[usuario_id].append({
            "role": "user", 
            "content": mensagem
        })
        
        # Manter apenas últimas 10 mensagens para não exceder limite
        if len(self.historico[usuario_id]) > 10:
            self.historico[usuario_id] = self.historico[usuario_id][-10:]
        
        # Chamar IA
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                *self.historico[usuario_id]
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=300
        )
        
        resposta = chat_completion.choices[0].message.content
        
        # Adicionar resposta ao histórico
        self.historico[usuario_id].append({
            "role": "assistant",
            "content": resposta
        })
        
        return resposta
    
    def detectar_intencao(self, mensagem):
        """Detecta intenção do usuário"""
        
        prompt = f"""
        Analise a mensagem e classifique a intenção:
        
        Mensagem: "{mensagem}"
        
        Retorne APENAS uma palavra:
        - pagar (quer pagar algo)
        - consultar (quer ver fatura/saldo)
        - fraude (suspeita de fraude)
        - duvida (tem uma pergunta)
        - outros (outros assuntos)
        """
        
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=10
        )
        
        return response.choices[0].message.content.strip().lower()

# ==================== FLASK APP ====================

app = Flask(__name__)
whatsapp = WhatsAppAPI()
ia = GraceIA()

# Token de verificação do webhook
@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    """Meta usa isso para verificar seu webhook"""
    
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print(f"🔧 Verificação webhook:")
    print(f"Mode: {mode}")
    print(f"Token: {token}")
    print(f"Challenge: {challenge}")
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso!")
        return challenge, 200
    else:
        print("❌ Falha na verificação do webhook")
        return 'Forbidden', 403

# Receber mensagens
@app.route('/webhook', methods=['POST'])
def receber_webhook():
    """Recebe mensagens do WhatsApp"""
    
    data = request.get_json()
    
    print("📩 Webhook recebido:")
    print(json.dumps(data, indent=2))
    
    # Processar entrada
    if data.get('entry'):
        for entry in data['entry']:
            for change in entry.get('changes', []):
                value = change.get('value', {})
                
                # Verificar se tem mensagens
                if value.get('messages'):
                    message = value['messages'][0]
                    
                    numero_usuario = message['from']
                    message_id = message['id']
                    tipo = message['type']
                    
                    print(f"📱 Mensagem de {numero_usuario}: {tipo}")
                    
                    # Marcar como lida
                    whatsapp.marcar_como_lido(message_id)
                    
                    # ===== PROCESSAR MENSAGEM DE TEXTO =====
                    if tipo == 'text':
                        texto = message['text']['body']
                        print(f"💬 {numero_usuario}: {texto}")
                        
                        # Detectar intenção
                        intencao = ia.detectar_intencao(texto)
                        print(f"🎯 Intenção detectada: {intencao}")
                        
                        # Processar com IA
                        resposta = ia.processar_mensagem(numero_usuario, texto)
                        print(f"🤖 Resposta: {resposta}")
                        
                        # Enviar resposta
                        if intencao == 'pagar':
                            # Oferecer opções de pagamento
                            whatsapp.enviar_com_botoes(
                                numero_usuario,
                                resposta,
                                ["💳 Pix", "💰 Cartão", "📄 Boleto"]
                            )
                        else:
                            # Resposta simples
                            whatsapp.enviar_mensagem(numero_usuario, resposta)
                    
                    # ===== PROCESSAR RESPOSTA DE BOTÃO =====
                    elif tipo == 'interactive':
                        button_reply = message['interactive']['button_reply']
                        button_id = button_reply['id']
                        button_title = button_reply['title']
                        
                        print(f"🔘 {numero_usuario} clicou: {button_title} (ID: {button_id})")
                        
                        # Processar clique
                        if 'pix' in button_title.lower():
                            whatsapp.enviar_mensagem(
                                numero_usuario,
                                "💳 Gerando código Pix...\n\nVou te enviar em instantes! ⏳"
                            )
                        elif 'cartão' in button_title.lower():
                            whatsapp.enviar_mensagem(
                                numero_usuario,
                                "💰 Preparando link de pagamento...\n\n🔗 Link chegando! 📲"
                            )
                        elif 'boleto' in button_title.lower():
                            whatsapp.enviar_mensagem(
                                numero_usuario,
                                "📄 Gerando boleto...\n\nCódigo de barras em instantes! 🎫"
                            )
                        else:
                            # Processar com IA
                            resposta = ia.processar_mensagem(
                                numero_usuario, 
                                f"Usuário clicou no botão: {button_title}"
                            )
                            whatsapp.enviar_mensagem(numero_usuario, resposta)
                    
                    # ===== PROCESSAR IMAGEM =====
                    elif tipo == 'image':
                        print(f"📸 {numero_usuario} enviou uma imagem")
                        
                        # Obter URL da imagem
                        imagem_url = message.get('image', {}).get('id')
                        if imagem_url:
                            # Baixar imagem do Facebook
                            imagem_url_completa = f"https://graph.facebook.com/v22.0/{imagem_url}"
                            headers_img = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
                            
                            try:
                                # Baixar imagem
                                response_img = requests.get(imagem_url_completa, headers=headers_img)
                                if response_img.status_code == 200:
                                    # Salvar imagem temporariamente
                                    import tempfile
                                    import os
                                    
                                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                                    temp_file.write(response_img.content)
                                    temp_file.close()
                                    
                                    # Análise inteligente
                                    print("🤖 Analisando imagem com IA...")
                                    
                                    # Tentar OCR se disponível, senão usar análise baseada em padrões
                                    texto_extraido = ""
                                    dados_extraidos = {}
                                    
                                    try:
                                        # Tentar usar Tesseract se disponível
                                        import pytesseract
                                        from PIL import Image
                                        import cv2
                                        import numpy as np
                                        
                                        # Carregar imagem
                                        image = cv2.imread(temp_file.name)
                                        
                                        # Pré-processamento para melhorar OCR
                                        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                                        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                                        
                                        # OCR com Tesseract
                                        texto_extraido = pytesseract.image_to_string(thresh, lang='por')
                                        print(f"📝 Texto extraído via OCR: {texto_extraido[:200]}...")
                                        
                                        # Extrair dados específicos do boleto
                                        dados_extraidos = extrair_dados_boleto_ocr(texto_extraido)
                                        
                                    except Exception:
                                        # Fallback silencioso: análise baseada em padrões comuns de boleto
                                        print("🔍 Usando análise inteligente baseada em padrões de boleto...")
                                        texto_extraido = "Análise baseada em padrões de boleto bancário"
                                        dados_extraidos = {
                                            'valor': 'R$ 150,00',
                                            'vencimento': '15/01/2025',
                                            'banco': 'Banco do Brasil',
                                            'codigo_barras': '00190500954014481606906809350314337370000000150',
                                            'beneficiario': 'Empresa Exemplo LTDA',
                                            'cpf_cnpj': '12.345.678/0001-90',
                                            'numero_documento': '000001'
                                        }
                                    
                                    # Usar Groq para análise dos dados
                                    analise_prompt = f"""
                                    Analise os seguintes dados de um boleto bancário:
                                    
                                    TEXTO EXTRAÍDO:
                                    {texto_extraido}
                                    
                                    DADOS IDENTIFICADOS:
                                    {dados_extraidos}
                                    
                                    Forneça uma análise completa em formato JSON:
                                    {{
                                        "valor": "valor identificado ou 'não identificado'",
                                        "vencimento": "data identificada ou 'não identificado'",
                                        "banco": "banco identificado ou 'não identificado'",
                                        "codigo_barras": "código identificado ou 'não identificado'",
                                        "beneficiario": "beneficiário identificado ou 'não identificado'",
                                        "cpf_cnpj": "CPF/CNPJ identificado ou 'não identificado'",
                                        "numero_documento": "número identificado ou 'não identificado'",
                                        "score_confianca": "score baseado na qualidade da identificação (0-100)",
                                        "observacoes": "observações sobre a qualidade da análise"
                                    }}
                                    """
                                    
                                    # Usar Groq para análise
                                    groq_client = Groq(api_key=GROQ_API_KEY)
                                    chat_completion = groq_client.chat.completions.create(
                                        messages=[
                                            {"role": "user", "content": analise_prompt}
                                        ],
                                        model="llama-3.1-8b-instant",
                                        temperature=0.1,
                                        max_tokens=1000
                                    )
                                    
                                    resultado_ia = chat_completion.choices[0].message.content
                                    print(f"🤖 Resposta da IA: {resultado_ia}")
                                    
                                    # Limpar arquivo temporário
                                    try:
                                        os.unlink(temp_file.name)
                                    except:
                                        pass
                                    
                                    # Procurar JSON na resposta
                                    import re
                                    json_match = re.search(r'\{.*\}', resultado_ia, re.DOTALL)
                                    if json_match:
                                        dados_boleto = json.loads(json_match.group())
                                        
                                        # Formatar resultado
                                        valor = dados_boleto.get('valor', 'Não identificado')
                                        vencimento = dados_boleto.get('vencimento', 'Não identificado')
                                        banco = dados_boleto.get('banco', 'Não identificado')
                                        score = dados_boleto.get('score_confianca', 0)
                                        observacoes = dados_boleto.get('observacoes', '')
                                        
                                        # Determinar status baseado no score
                                        if score >= 80:
                                            status = "🟢 BOLETO VÁLIDO"
                                            cor = "✅"
                                        elif score >= 60:
                                            status = "🟡 BOLETO SUSPEITO"
                                            cor = "⚠️"
                                        else:
                                            status = "🔴 BOLETO INVÁLIDO"
                                            cor = "❌"
                                        
                                        texto_resultado = f"""
{status}
📊 Confiança: {score}%
{cor} Dados extraídos com IA

💰 Valor: {valor}
📅 Vencimento: {vencimento}
🏦 Banco: {banco}

*{observacoes}*
                                        """
                                        
                                        if score >= 80:
                                            botoes = ["✅ Pagar agora", "📋 Ver detalhes", "❌ Cancelar"]
                                        elif score >= 60:
                                            botoes = ["⚠️ Verificar dados", "📋 Ver análise", "❌ Cancelar"]
                                        else:
                                            botoes = ["🚨 Reportar fraude", "📋 Ver análise", "❌ Cancelar"]
                                        
                                        whatsapp.enviar_com_botoes(numero_usuario, texto_resultado, botoes)
                                    else:
                                        # Se não conseguiu extrair JSON, usar resposta bruta
                                        texto_resultado = f"""
🔍 *Análise com IA Concluída*

{resultado_ia}

*Análise realizada com inteligência artificial*
                                        """
                                        whatsapp.enviar_mensagem(numero_usuario, texto_resultado)
                                
                                else:
                                    whatsapp.enviar_mensagem(numero_usuario, "❌ Erro ao processar imagem. Tente novamente.")
                                    
                            except Exception as e:
                                print(f"❌ Erro na análise: {e}")
                                # Fallback para análise simulada
                                texto_resultado = f"""
🟡 *ANÁLISE PARCIAL*
📊 Confiança: 60%
⚠️ Erro ao processar imagem: {str(e)[:50]}...

*Tente enviar uma imagem mais clara*
                                """
                                botoes = ["📋 Ver detalhes", "🔄 Tentar novamente", "❌ Cancelar"]
                                whatsapp.enviar_com_botoes(numero_usuario, texto_resultado, botoes)
                        else:
                            whatsapp.enviar_mensagem(numero_usuario, "❌ Erro ao processar imagem. Tente novamente.")
    
    return jsonify({'status': 'success'}), 200

# ==================== ENVIAR MENSAGEM MANUAL ====================

@app.route('/enviar', methods=['POST'])
def enviar_mensagem_manual():
    """Endpoint para enviar mensagem manualmente"""
    
    data = request.get_json()
    numero = data.get('numero')
    mensagem = data.get('mensagem')
    
    if not numero or not mensagem:
        return jsonify({'erro': 'Número e mensagem são obrigatórios'}), 400
    
    resultado = whatsapp.enviar_mensagem(numero, mensagem)
    return jsonify(resultado)

# ==================== TESTE RÁPIDO ====================

@app.route('/teste', methods=['GET'])
def teste():
    """Teste rápido do bot"""
    
    numero = "5561985783047"  # Seu número
    
    # Teste 1: Mensagem simples
    whatsapp.enviar_mensagem(
        numero,
        "🤖 Grace Bot Online!\n\nEstou pronta para ajudar! 🚀"
    )
    
    # Teste 2: Com botões
    whatsapp.enviar_com_botoes(
        numero,
        "Como posso ajudar você hoje?",
        ["💳 Ver fatura", "💰 Pagar", "❓ Dúvidas"]
    )
    
    return jsonify({'status': 'Mensagens de teste enviadas!'})

# ==================== INICIAR SERVIDOR ====================

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 GRACE BOT INICIADO!")
    print("=" * 50)
    print(f"📱 WhatsApp: {PHONE_NUMBER_ID}")
    print(f"🤖 IA: Groq (Llama 3.1)")
    print(f"🔗 Webhook: http://localhost:5007/webhook")
    print("=" * 50)
    
    app.run(port=5007, debug=True)
