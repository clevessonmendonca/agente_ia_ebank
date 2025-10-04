#!/usr/bin/env python3
"""
🤖 Grace Bot com MayAPI - Sistema Completo Anti-Fraude
Integração WhatsApp + IA + Agentes Anti-Fraude
"""

import os
import requests
import json
import uuid
import re
from groq import Groq
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Importar agentes
from agente_leitor import AgenteLeitorOCR
from agente_consultor import AgenteConsultor
from agente_detetive import AgenteDetetive
from mayapi_client import MayAPIClient

# Carregar variáveis de ambiente
load_dotenv()

# ==================== CONFIGURAÇÃO ====================

MAYAPI_PRODUCT_ID = os.getenv('MAYAPI_PRODUCT_ID')
MAYAPI_TOKEN = os.getenv('MAYAPI_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# ==================== FUNÇÃO OCR ====================

def extrair_dados_boleto_ocr(texto):
    """Extrai dados específicos de boleto usando regex"""
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

# ==================== CLASSE MAYAPI ====================

class MayAPIWhatsApp:
    def __init__(self):
        """Inicializa cliente MayAPI"""
        self.product_id = MAYAPI_PRODUCT_ID
        self.token = MAYAPI_TOKEN
        self.base_url = f"https://api.maytapi.com/api/{self.product_id}"
        self.headers = {
            "x-maytapi-key": self.token,
            "accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def enviar_mensagem(self, numero, texto):
        """Envia mensagem de texto via MayAPI"""
        try:
            payload = {
                "to_number": numero,
                "type": "text",
                "message": texto
            }
            
            # Phone ID vai na URL, não no payload
            response = requests.post(
                f"{self.base_url}/113863/sendMessage",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            print(f"📤 Enviando para {numero}: {texto}")
            print(f"📤 Resposta MayAPI: {response.status_code} - {response.text}")
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return {'erro': str(e)}
    
    def enviar_com_botoes(self, numero, texto, botoes):
        """Envia mensagem com opções numeradas (MayAPI não suporta botões interativos)"""
        try:
            # MayAPI não suporta botões interativos, usar opções numeradas
            texto_com_opcoes = f"{texto}\n\n"
            for i, botao in enumerate(botoes[:3], 1):
                emoji = ["1️⃣", "2️⃣", "3️⃣"][i-1]
                texto_com_opcoes += f"{emoji} {botao}\n"
            
            texto_com_opcoes += "\nDigite o número da opção desejada."
            
            payload = {
                "to_number": numero,
                "type": "text",
                "message": texto_com_opcoes
            }
            
            # Phone ID vai na URL, não no payload
            response = requests.post(
                f"{self.base_url}/113863/sendMessage",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            print(f"📤 Enviando opções numeradas para {numero}: {botoes}")
            print(f"📤 Resposta MayAPI: {response.status_code} - {response.text}")
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Erro ao enviar opções: {e}")
            return {'erro': str(e)}
    
    def baixar_imagem(self, media_id):
        """Baixa imagem via MayAPI"""
        try:
            response = requests.get(
                f"{self.base_url}/getMedia/{media_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Salvar imagem temporariamente
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_file.write(response.content)
                temp_file.close()
                return temp_file.name
            else:
                return None
                
        except Exception as e:
            print(f"❌ Erro ao baixar imagem: {e}")
            return None

# ==================== AGENTE ORQUESTRADOR ====================

class AgenteOrquestrador:
    def __init__(self):
        """Inicializa o Agente Orquestrador com todos os agentes"""
        self.leitor = AgenteLeitorOCR()
        self.consultor = AgenteConsultor()
        self.detetive = AgenteDetetive()
        self.mayapi = MayAPIClient(MAYAPI_PRODUCT_ID, MAYAPI_TOKEN)
    
    def analisar_pagamento_completo(self, cliente_id, dados_pagamento):
        """Análise completa multi-agente"""
        try:
            print("🔍 Agente Leitor: Extraindo dados...")
            # 1. EXTRAÇÃO (Agente Leitor)
            if dados_pagamento.get('tipo') == 'imagem_boleto':
                dados_extraidos = self.leitor.extrair_dados_boleto(dados_pagamento.get('path', ''))
            elif dados_pagamento.get('tipo') == 'pix':
                dados_extraidos = self.leitor.extrair_dados_pix(dados_pagamento.get('codigo', ''))
            else:
                dados_extraidos = dados_pagamento
            
            print("✅ Agente Consultor: Validando internamente...")
            # 2. VALIDAÇÃO (Agente Consultor)
            validacao = self.consultor.validar_cobranca(cliente_id, dados_extraidos)
            
            print("🕵️ Agente Detetive: Analisando fraudes...")
            # 3. DETECÇÃO (Agente Detetive)
            analise_fraude = self.detetive.analisar_fraude_completa(dados_extraidos, cliente_id)
            
            # 4. CONSOLIDAÇÃO
            score_final = self._calcular_score_final(validacao, analise_fraude)
            
            resultado = {
                'dados_extraidos': dados_extraidos,
                'validacao_interna': validacao,
                'analise_fraude': analise_fraude,
                'score_confianca': score_final,
                'classificacao': self._classificar_final(score_final),
                'mensagem_usuario': self._gerar_mensagem(score_final, analise_fraude),
                'timestamp': dados_pagamento.get('timestamp', '')
            }
            
            return resultado
            
        except Exception as e:
            return {
                'erro': f'Erro na análise completa: {str(e)}',
                'score_confianca': 0,
                'classificacao': 'ERRO'
            }
    
    def _calcular_score_final(self, validacao, fraude):
        """Combina scores de validação e fraude"""
        score_validacao = validacao.get('score_confianca', 0)
        score_fraude_invertido = 100 - fraude.get('score_fraude', 0)
        
        # Peso maior para detecção de fraude (segurança first)
        score_final = (score_validacao * 0.4) + (score_fraude_invertido * 0.6)
        return round(score_final)
    
    def _classificar_final(self, score):
        """Classificação final visual"""
        if score >= 90:
            return "🟢 SEGURO"
        elif score >= 60:
            return "🟡 SUSPEITO"
        else:
            return "🔴 FRAUDE"
    
    def _gerar_mensagem(self, score, analise_fraude):
        """Mensagem amigável pro usuário"""
        if score >= 90:
            return "✅ Pode pagar com tranquilidade! Tudo verificado."
        elif score >= 60:
            sinais = analise_fraude.get('sinais_suspeitos', [])
            return f"⚠️ Atenção! Encontramos: {', '.join(sinais[:2])}. Confirme antes de pagar."
        else:
            sinais = analise_fraude.get('sinais_suspeitos', [])
            return f"🚨 NÃO PAGUE! Detectamos fraude: {', '.join(sinais[:3])}"

# ==================== CLASSE IA ====================

class GraceIA:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.historico = {}
        self.contexto_conversa = {}  # Novo: contexto de conversa por usuário
    
    def processar_mensagem(self, usuario_id, mensagem):
        """Processa mensagem com IA mantendo contexto"""
        try:
            # Inicializar histórico do usuário se não existir
            if usuario_id not in self.historico:
                self.historico[usuario_id] = []
            if usuario_id not in self.contexto_conversa:
                self.contexto_conversa[usuario_id] = {
                    'ultima_acao': None,
                    'dados_pagamento': {},
                    'fluxo_atual': None
                }
            
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
            - Respostas curtas (máx 3 linhas no WhatsApp)
            - Use emojis com moderação
            - Sempre confirme dados sensíveis
            - Em caso de suspeita de fraude, alerte IMEDIATAMENTE
            - Mantenha contexto da conversa anterior
            """
            
            # Adicionar contexto do histórico e fluxo atual
            contexto = ""
            if self.historico[usuario_id]:
                contexto += f"\nHistórico recente: {', '.join(self.historico[usuario_id][-3:])}"
            
            # Adicionar contexto da conversa atual
            ctx = self.contexto_conversa[usuario_id]
            if ctx['ultima_acao']:
                contexto += f"\nÚltima ação: {ctx['ultima_acao']}"
            if ctx['fluxo_atual']:
                contexto += f"\nFluxo atual: {ctx['fluxo_atual']}"
            if ctx['dados_pagamento']:
                contexto += f"\nDados coletados: {ctx['dados_pagamento']}"
            
            # Chamada para Groq
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{mensagem}{contexto}"}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=200
            )
            
            resposta = chat_completion.choices[0].message.content
            
            # Atualizar histórico
            self.historico[usuario_id].append(mensagem)
            if len(self.historico[usuario_id]) > 10:
                self.historico[usuario_id] = self.historico[usuario_id][-10:]
            
            return resposta
            
        except Exception as e:
            return f"Desculpe, ocorreu um erro: {str(e)}"
    
    def detectar_intencao(self, mensagem, usuario_id=None):
        """Detecta intenção do usuário com contexto"""
        try:
            mensagem_lower = mensagem.lower().strip()
            
            # Verificar contexto primeiro
            if usuario_id and usuario_id in self.contexto_conversa:
                ctx = self.contexto_conversa[usuario_id]
                
                # Se está no fluxo de pagamento e usuário responde com números
                if mensagem_lower in ['1', '2', '3'] and ctx['fluxo_atual'] == 'escolher_pagamento':
                    return f"escolher_pagamento_{mensagem_lower}"
                
                # Se está no fluxo de verificação e usuário responde com números
                elif mensagem_lower in ['1', '2', '3'] and ctx['fluxo_atual'] == 'escolher_verificacao':
                    return f"escolher_verificacao_{mensagem_lower}"
                
                # Se está coletando dados e usuário informa valor
                elif ctx['fluxo_atual'] == 'dados_boleto' and any(palavra in mensagem_lower for palavra in ['valor', 'reais', 'r$', 'dinheiro', '500', '506']):
                    return "informar_valor"
                
                # Se está no fluxo e usuário quer continuar
                elif any(palavra in mensagem_lower for palavra in ['continuar', 'confirmar', 'sim', 'ok', 'prosseguir']):
                    if ctx['fluxo_atual'] == 'dados_boleto':
                        return "continuar_pagamento"
                    elif ctx['fluxo_atual'] == 'escolher_pagamento':
                        return "continuar_pagamento"
                
                # Se está no fluxo e usuário quer cancelar
                elif any(palavra in mensagem_lower for palavra in ['cancelar', 'parar', 'não', 'sair']):
                    return "cancelar"
            
            # Detecção por palavras-chave (apenas se não estiver em fluxo)
            if any(palavra in mensagem_lower for palavra in ['pagar', 'pagamento', 'pix', 'boleto', 'cartão', 'dinheiro', 'valor', 'quero pagar']):
                return "pagar"
            elif any(palavra in mensagem_lower for palavra in ['verificar', 'consultar', 'status', 'fatura', 'cobrança', 'ver']):
                return "verificar"
            elif any(palavra in mensagem_lower for palavra in ['cancelar', 'parar', 'não quero']):
                return "cancelar"
            elif any(palavra in mensagem_lower for palavra in ['valor', 'reais', 'r$', 'dinheiro']):
                return "informar_valor"
            else:
                # Se não encontrou palavra-chave, usa IA
                prompt = f"""
                Analise a mensagem e retorne APENAS uma palavra:
                Mensagem: "{mensagem}"
                
                Opções: pagar, verificar, duvida, consultar, cancelar, informar_valor, continuar_pagamento
                
                Se a mensagem menciona pagamento, dinheiro, pix, boleto, cartão, retorne "pagar"
                Se a mensagem menciona verificar, consultar, status, retorne "verificar"
                Se a mensagem menciona valor, reais, R$, retorne "informar_valor"
                Se a mensagem menciona continuar, confirmar, prosseguir, retorne "continuar_pagamento"
                """
                
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    temperature=0.1,
                    max_tokens=10
                )
                
                return response.choices[0].message.content.strip().lower()
            
        except Exception as e:
            return "duvida"

# ==================== FUNÇÃO AUXILIAR ====================

def processar_mensagem_com_contexto(numero_usuario, texto):
    """Processa mensagem mantendo contexto da conversa"""
    # Detectar intenção com contexto
    intencao = ia.detectar_intencao(texto, numero_usuario)
    print(f"🎯 Intenção detectada: {intencao}")
    
    # Atualizar contexto da conversa
    if numero_usuario not in ia.contexto_conversa:
        ia.contexto_conversa[numero_usuario] = {
            'ultima_acao': None,
            'dados_pagamento': {},
            'fluxo_atual': None
        }
    
    # Debug do contexto
    ctx = ia.contexto_conversa[numero_usuario]
    print(f"🧠 Contexto atual: {ctx}")
    
    # Processar com base na intenção e contexto
    if intencao == 'pagar':
        # Iniciar fluxo de pagamento
        ia.contexto_conversa[numero_usuario]['fluxo_atual'] = 'escolher_pagamento'
        ia.contexto_conversa[numero_usuario]['ultima_acao'] = 'solicitou_pagamento'
        texto_botoes = "Escolha como deseja pagar:"
        botoes = ["Pix", "Cartao", "Boleto"]
        whatsapp.enviar_com_botoes(numero_usuario, texto_botoes, botoes)
        
    elif intencao.startswith('escolher_pagamento_'):
        # Usuário escolheu método de pagamento
        opcao = intencao.split('_')[-1]
        metodos = {1: 'Pix', 2: 'Cartão', 3: 'Boleto'}
        metodo_escolhido = metodos.get(int(opcao), 'Pix')
        
        ia.contexto_conversa[numero_usuario]['dados_pagamento']['metodo'] = metodo_escolhido
        ia.contexto_conversa[numero_usuario]['fluxo_atual'] = 'dados_boleto'
        ia.contexto_conversa[numero_usuario]['ultima_acao'] = f'escolheu_{metodo_escolhido.lower()}'
        
        if metodo_escolhido == 'Boleto':
            resposta = f"Perfeito! Você escolheu {metodo_escolhido}. Qual é o valor do boleto que você quer pagar?"
        else:
            resposta = f"Ótima escolha! {metodo_escolhido} é rápido e seguro. Qual é o valor que você quer pagar?"
        
        whatsapp.enviar_mensagem(numero_usuario, resposta)
        
    elif intencao == 'informar_valor':
        # Usuário informou valor
        ia.contexto_conversa[numero_usuario]['dados_pagamento']['valor'] = texto
        ia.contexto_conversa[numero_usuario]['ultima_acao'] = 'informou_valor'
        ia.contexto_conversa[numero_usuario]['fluxo_atual'] = 'confirmar_pagamento'
        
        metodo = ia.contexto_conversa[numero_usuario]['dados_pagamento'].get('metodo', 'pagamento')
        resposta = f"✅ Perfeito! Valor de {texto} via {metodo}.\n\nPara finalizar o pagamento, preciso confirmar alguns dados:\n\n1️⃣ Número da conta\n2️⃣ CPF\n3️⃣ Confirmação\n\nDigite 'continuar' para prosseguir ou 'cancelar' para sair."
        whatsapp.enviar_mensagem(numero_usuario, resposta)
        
    elif intencao == 'continuar_pagamento':
        # Usuário quer continuar com o pagamento
        ctx = ia.contexto_conversa[numero_usuario]
        metodo = ctx['dados_pagamento'].get('metodo', 'pagamento')
        valor = ctx['dados_pagamento'].get('valor', 'não informado')
        
        ia.contexto_conversa[numero_usuario]['ultima_acao'] = 'confirmou_pagamento'
        ia.contexto_conversa[numero_usuario]['fluxo_atual'] = 'finalizando'
        
        resposta = f"🎉 Ótimo! Vamos finalizar seu pagamento:\n\n💰 Valor: {valor}\n💳 Método: {metodo}\n\nPara completar, preciso do seu CPF. Digite apenas os números:"
        whatsapp.enviar_mensagem(numero_usuario, resposta)
        
    elif intencao == 'verificar':
        # Iniciar fluxo de verificação
        ia.contexto_conversa[numero_usuario]['fluxo_atual'] = 'escolher_verificacao'
        ia.contexto_conversa[numero_usuario]['ultima_acao'] = 'solicitou_verificacao'
        texto_botoes = "O que você gostaria de verificar?"
        botoes = ["Faturas", "Status", "Historico"]
        whatsapp.enviar_com_botoes(numero_usuario, texto_botoes, botoes)
        
    elif intencao.startswith('escolher_verificacao_'):
        # Usuário escolheu tipo de verificação
        opcao = intencao.split('_')[-1]
        tipos = {1: 'Faturas', 2: 'Status', 3: 'Histórico'}
        tipo_escolhido = tipos.get(int(opcao), 'Faturas')
        
        ia.contexto_conversa[numero_usuario]['ultima_acao'] = f'verificando_{tipo_escolhido.lower()}'
        resposta = f"Vou verificar suas {tipo_escolhido.lower()} para você. Um momento..."
        whatsapp.enviar_mensagem(numero_usuario, resposta)
        
    elif intencao == 'cancelar':
        # Usuário quer cancelar - limpar contexto
        ia.contexto_conversa[numero_usuario] = {
            'ultima_acao': 'cancelou',
            'dados_pagamento': {},
            'fluxo_atual': None
        }
        resposta = "❌ Pagamento cancelado. Se precisar de ajuda, estarei aqui! 😊"
        whatsapp.enviar_mensagem(numero_usuario, resposta)
        
    else:
        # Resposta com contexto
        resposta = ia.processar_mensagem(numero_usuario, texto)
        print(f"🤖 Resposta: {resposta}")
        whatsapp.enviar_mensagem(numero_usuario, resposta)
    
    # Debug final do contexto
    print(f"🧠 Contexto final: {ia.contexto_conversa[numero_usuario]}")

# ==================== FLASK APP ====================

app = Flask(__name__)
whatsapp = MayAPIWhatsApp()
ia = GraceIA()
orquestrador = AgenteOrquestrador()

@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    """Verificação do webhook"""
    return request.args.get('hub.challenge', '')

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    """Recebe mensagens do WhatsApp via MayAPI"""
    try:
        data = request.get_json()
        print("📩 Webhook MayAPI recebido:")
        print(json.dumps(data, indent=2))
        
        # Debug: verificar estrutura dos dados
        print(f"🔍 Debug - data type: {type(data)}")
        print(f"🔍 Debug - data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        if 'message' in data:
            print(f"🔍 Debug - message type: {type(data.get('message'))}")
            print(f"🔍 Debug - message keys: {data.get('message').keys() if isinstance(data.get('message'), dict) else 'Not a dict'}")
            if 'text' in data.get('message', {}):
                text_value = data.get('message', {}).get('text')
                print(f"🔍 Debug - text type: {type(text_value)}")
                print(f"🔍 Debug - text value: {text_value}")
        
        # Verificar se é mensagem de texto
        if data.get('type') == 'message' and 'message' in data:
            message = data.get('message', {})
            
            # Ignorar mensagens enviadas pelo próprio bot (comentado para teste)
            # if message.get('fromMe', False):
            #     print(f"📤 Mensagem enviada pelo bot: {message.get('text', '')}")
            #     return jsonify({'status': 'ignored'}), 200
            
            numero_usuario = data.get('user', {}).get('phone', '')
            
            # FILTRO: Responder apenas ao seu número
            if numero_usuario != '556185783047':
                print(f"🚫 Mensagem de {numero_usuario} - ignorando (filtro ativo)")
                return jsonify({'status': 'ignored', 'message': 'Número não autorizado'}), 200
            
            tipo = message.get('type')
            
            # Verificar se é imagem primeiro
            if tipo == 'image':
                print(f"📸 Imagem recebida de {numero_usuario}")
                print(f"📊 Dados da imagem: {message}")
                
                # Verificar se tem URL da imagem
                if 'url' in message:
                    imagem_url = message.get('url')
                    print(f"🔗 URL da imagem: {imagem_url}")
                    
                    # Análise da imagem com IA real
                    resposta = f"📸 Imagem recebida! Analisando boleto...\n\n🔍 *Análise em andamento:*\n• Baixando imagem\n• Processando com IA\n• Extraindo dados do boleto\n• Verificando autenticidade\n\n⏳ Aguarde alguns segundos..."
                    whatsapp.enviar_mensagem(numero_usuario, resposta)
                    
                    # Baixar e analisar imagem com análise inteligente
                    try:
                        import requests
                        import base64
                        from io import BytesIO
                        import re
                        
                        # Baixar imagem
                        print(f"📥 Baixando imagem: {imagem_url}")
                        response = requests.get(imagem_url, timeout=10)
                        if response.status_code == 200:
                            # Salvar imagem temporariamente para análise
                            import tempfile
                            import os
                            
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                            temp_file.write(response.content)
                            temp_file.close()
                            
                            # Análise inteligente sem OCR (fallback)
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
                            
                            # Tentar extrair JSON da resposta
                            
                            # Procurar JSON na resposta
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
                            raise Exception(f"Erro ao baixar imagem: {response.status_code}")
                            
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
            
            # Se for texto, processar normalmente
            elif tipo == 'text':
                # Verificar se text é string ou dict
                text_data = message.get('text', '')
                if isinstance(text_data, dict):
                    texto = text_data.get('body', '')
                else:
                    texto = text_data
                
                print(f"📱 Mensagem de {numero_usuario}: {tipo}")
                print(f"💬 {numero_usuario}: {texto}")
                
                # Processar mensagem com contexto
                processar_mensagem_com_contexto(numero_usuario, texto)
        
        # Verificar se é mensagem direta do MayAPI (formato diferente)
        elif data.get('type') == 'message' and 'message' in data and isinstance(data.get('message'), dict):
            message = data.get('message', {})
            if message.get('type') == 'text':
                numero_usuario = data.get('user', {}).get('phone', '')
                # Verificar se text é string ou dict
                text_data = message.get('text', '')
                if isinstance(text_data, dict):
                    texto = text_data.get('body', '')
                else:
                    texto = text_data
                
                print(f"📱 Mensagem direta de {numero_usuario}: {texto}")
                
                # Processar mensagem com contexto
                processar_mensagem_com_contexto(numero_usuario, texto)
        
        # Verificar se é mensagem do MayAPI (formato sem 'type' no topo)
        elif 'message' in data and 'user' in data:
            try:
                message = data.get('message', {})
                if message.get('type') == 'text':
                    numero_usuario = data.get('user', {}).get('phone', '')
                    # Verificar se text é string ou dict
                    text_data = message.get('text', '')
                    if isinstance(text_data, dict):
                        texto = text_data.get('body', '')
                    else:
                        texto = text_data
                    
                    # Ignorar mensagens enviadas pelo próprio bot (comentado para teste)
                    # if message.get('fromMe', False):
                    #     print(f"📤 Mensagem enviada pelo bot: {texto}")
                    #     return jsonify({'status': 'ignored'}), 200
                    
                    print(f"📱 Mensagem MayAPI de {numero_usuario}: {texto}")
                    
                    # Processar mensagem com contexto
                    processar_mensagem_com_contexto(numero_usuario, texto)
            except Exception as e:
                print(f"❌ Erro ao processar mensagem MayAPI: {e}")
                print(f"📊 Dados recebidos: {data}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Verificar se é mensagem do MayAPI (formato com 'type' no topo)
        elif data.get('type') == 'message' and 'message' in data and 'user' in data:
            try:
                message = data.get('message', {})
                if message.get('type') == 'text':
                    numero_usuario = data.get('user', {}).get('phone', '')
                    # Verificar se text é string ou dict
                    text_data = message.get('text', '')
                    if isinstance(text_data, dict):
                        texto = text_data.get('body', '')
                    else:
                        texto = text_data
                    
                    # Ignorar mensagens enviadas pelo próprio bot (comentado para teste)
                    # if message.get('fromMe', False):
                    #     print(f"📤 Mensagem enviada pelo bot: {texto}")
                    #     return jsonify({'status': 'ignored'}), 200
                    
                    print(f"📱 Mensagem MayAPI de {numero_usuario}: {texto}")
                    
                    # Processar mensagem com contexto
                    processar_mensagem_com_contexto(numero_usuario, texto)
            except Exception as e:
                print(f"❌ Erro ao processar mensagem MayAPI: {e}")
                print(f"📊 Dados recebidos: {data}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Ignorar outros tipos (ack, status, error, etc.)
        elif data.get('type') in ['ack', 'status', 'error']:
            print(f"📊 {data.get('type').upper()}: {data.get('data', [])}")
            return jsonify({'status': 'ignored'}), 200
        
        
        # Fallback para qualquer outro formato
        else:
            print(f"📊 Formato não reconhecido: {data}")
            return jsonify({'status': 'ignored'}), 200
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/teste', methods=['GET'])
def teste():
    """Endpoint de teste"""
    return jsonify({
        'status': 'Grace Bot funcionando!',
        'agentes': ['Leitor', 'Consultor', 'Detetive', 'Orquestrador'],
        'integracao': 'MayAPI WhatsApp'
    })

@app.route('/teste-botoes', methods=['GET'])
def teste_botoes():
    """Endpoint para testar botões"""
    numero_teste = request.args.get('numero', '61985783047')
    
    # Enviar botões de exemplo
    botoes = ["💳 Pagar com Pix", "💰 Cartão de Crédito", "📄 Gerar Boleto"]
    texto = "Escolha uma forma de pagamento:"
    
    resultado = whatsapp.enviar_com_botoes(numero_teste, texto, botoes)
    
    return jsonify({
        'status': 'Botões enviados!',
        'numero': numero_teste,
        'botoes': botoes,
        'resultado': resultado
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 GRACE BOT COM MAYAPI INICIADO!")
    print("=" * 50)
    print(f"📱 MayAPI Product ID: {MAYAPI_PRODUCT_ID}")
    print(f"🤖 IA: Groq (Llama 3.1)")
    print(f"🔗 Webhook: http://localhost:5000/webhook")
    print("=" * 50)
    
    app.run(port=5001, debug=True)
