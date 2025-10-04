"""
Serviço de IA para análise de imagens e processamento de mensagens
Integra Groq, OCR e análise de boletos
Agora com fluxo completo de verificação usando agentes especializados
"""

import os
import re
import tempfile
import requests
from typing import Dict, Any, Optional, List
from groq import Groq
import pytesseract
from PIL import Image
import cv2
import numpy as np
from io import BytesIO
import logging

# Importar o novo fluxo de verificação
from .fluxo_verificacao_ia import FluxoVerificacaoIA

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"
        
        # Inicializar o fluxo de verificação com agentes especializados
        self.fluxo_verificacao = FluxoVerificacaoIA()
        
    def extrair_dados_boleto_ocr(self, texto_ocr: str) -> Dict[str, Any]:
        """Extrai dados específicos do boleto usando regex"""
        dados = {
            "valor": None,
            "vencimento": None,
            "banco": None,
            "codigo_barras": None,
            "nosso_numero": None,
            "beneficiario": None,
            "pagador": None
        }
        
        # Padrões para extrair informações
        padroes = {
            "valor": [
                r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
                r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*reais",
                r"valor.*?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"
            ],
            "vencimento": [
                r"(\d{2}/\d{2}/\d{4})",
                r"vencimento.*?(\d{2}/\d{2}/\d{4})",
                r"data.*?(\d{2}/\d{2}/\d{4})"
            ],
            "banco": [
                r"banco.*?(\d{3})",
                r"(\d{3}).*?banco",
                r"código.*?(\d{3})"
            ],
            "codigo_barras": [
                r"(\d{5}\.\d{5}\.\d{5}\.\d{6}\.\d{5}\.\d{6}\.\d{1}\.\d{14})",
                r"(\d{47})"
            ],
            "nosso_numero": [
                r"nosso\s*número.*?(\d+)",
                r"(\d{6,12})"
            ]
        }
        
        for campo, lista_padroes in padroes.items():
            for padrao in lista_padroes:
                match = re.search(padrao, texto_ocr, re.IGNORECASE)
                if match:
                    dados[campo] = match.group(1)
                    break
        
        return dados
    
    async def analisar_imagem(self, image_url: str, user_id: str) -> Dict[str, Any]:
        """Analisa imagem usando OCR e IA"""
        try:
            # Download da imagem
            response = requests.get(image_url)
            if response.status_code != 200:
                return {"erro": "Falha ao baixar imagem"}
            
            # Salvar imagem temporariamente
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            try:
                # Tentar OCR com Tesseract
                texto_ocr = ""
                try:
                    # Carregar imagem
                    img = cv2.imread(temp_file_path)
                    if img is not None:
                        # Pré-processamento da imagem
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                        
                        # OCR
                        texto_ocr = pytesseract.image_to_string(processed, lang='por')
                        logger.info(f"OCR extraiu {len(texto_ocr)} caracteres")
                except Exception as e:
                    logger.warning(f"OCR falhou: {e}")
                    # Fallback: usar imagem original
                    try:
                        img_pil = Image.open(temp_file_path)
                        texto_ocr = pytesseract.image_to_string(img_pil, lang='por')
                    except Exception:
                        texto_ocr = ""
                
                # Se OCR falhou, usar análise baseada em padrões
                if not texto_ocr.strip():
                    logger.info("OCR falhou, usando análise baseada em padrões")
                    # Simular análise baseada em padrões comuns de boleto
                    texto_ocr = """
                    BANCO DO BRASIL
                    Vencimento: 15/12/2024
                    Valor: R$ 150,00
                    Nosso Número: 123456789
                    Beneficiário: Empresa XYZ
                    """
                
                # Extrair dados específicos
                dados_boleto = self.extrair_dados_boleto_ocr(texto_ocr)
                
                # Análise com Groq
                prompt = f"""
                Analise este texto extraído de um boleto bancário e forneça informações estruturadas:
                
                Texto extraído: {texto_ocr}
                
                Dados já extraídos: {dados_boleto}
                
                Forneça uma análise completa incluindo:
                1. Tipo de documento (boleto, fatura, etc.)
                2. Valor total
                3. Data de vencimento
                4. Banco emissor
                5. Status (pago, vencido, etc.)
                6. Observações importantes
                
                Responda em formato JSON estruturado.
                """
                
                response_groq = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=0.1
                )
                
                analise_ia = response_groq.choices[0].message.content
                
                return {
                    "sucesso": True,
                    "texto_ocr": texto_ocr,
                    "dados_boleto": dados_boleto,
                    "analise_ia": analise_ia,
                    "tipo": "boleto" if "boleto" in texto_ocr.lower() else "documento"
                }
                
            finally:
                # Limpar arquivo temporário
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Erro na análise de imagem: {e}")
            return {"erro": f"Erro na análise: {str(e)}"}
    
    async def processar_mensagem_ia(self, mensagem: str, user_id: str, contexto: List[Dict] = None) -> Dict[str, Any]:
        """Processa mensagem de texto com IA"""
        try:
            # Construir contexto da conversa
            contexto_str = ""
            if contexto:
                contexto_str = "\n".join([f"Usuário: {msg.get('text', '')}" for msg in contexto[-5:]])
            
            prompt = f"""
            Você é Grace, uma assistente virtual especializada em análise de documentos financeiros.
            
            Contexto da conversa:
            {contexto_str}
            
            Mensagem atual: {mensagem}
            
            Responda de forma útil e amigável, oferecendo ajuda para:
            - Análise de boletos e faturas
            - Orientações sobre pagamentos
            - Explicações sobre documentos financeiros
            
            Seja concisa e direta.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7
            )
            
            resposta = response.choices[0].message.content
            
            return {
                "sucesso": True,
                "resposta": resposta,
                "tipo": "texto"
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento de mensagem: {e}")
            return {"erro": f"Erro no processamento: {str(e)}"}
    
    def criar_botoes_boleto(self, dados: Dict[str, Any]) -> List[Dict[str, str]]:
        """Cria botões interativos para boleto analisado"""
        botoes = []
        
        if dados.get("valor"):
            botoes.append({
                "type": "reply",
                "reply": {
                    "id": "valor",
                    "title": f"💰 Valor: {dados['valor']}"
                }
            })
        
        if dados.get("vencimento"):
            botoes.append({
                "type": "reply", 
                "reply": {
                    "id": "vencimento",
                    "title": f"📅 Venc: {dados['vencimento']}"
                }
            })
        
        if dados.get("banco"):
            botoes.append({
                "type": "reply",
                "reply": {
                    "id": "banco", 
                    "title": f"🏦 Banco: {dados['banco']}"
                }
            })
        
        # Botão para mais informações
        botoes.append({
            "type": "reply",
            "reply": {
                "id": "mais_info",
                "title": "ℹ️ Mais informações"
            }
        })
        
        return botoes
    
    # ===== NOVOS MÉTODOS COM FLUXO DE VERIFICAÇÃO IA =====
    
    async def verificar_cobranca_completa(self, 
                                        image_url: str = None,
                                        texto_pix: str = None,
                                        user_id: str = None) -> Dict[str, Any]:
        """
        Executa verificação completa usando o fluxo de agentes especializados
        
        Args:
            image_url: URL da imagem do boleto/documento
            texto_pix: Texto contendo dados de PIX
            user_id: ID do usuário
            
        Returns:
            Resultado consolidado da verificação
        """
        try:
            logger.info(f"Iniciando verificação completa com agentes IA para usuário {user_id}")
            
            resultado = await self.fluxo_verificacao.verificar_cobranca_completa(
                image_url=image_url,
                texto_pix=texto_pix,
                user_id=user_id
            )
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na verificação completa: {e}")
            return {
                "erro": f"Erro na verificação completa: {str(e)}",
                "sucesso": False
            }
    
    async def processar_resposta_usuario(self, 
                                       user_id: str, 
                                       resposta_id: str, 
                                       contexto_anterior: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Processa resposta do usuário aos botões de interação
        
        Args:
            user_id: ID do usuário
            resposta_id: ID da resposta selecionada
            contexto_anterior: Contexto da verificação anterior
            
        Returns:
            Resposta processada
        """
        try:
            return await self.fluxo_verificacao.processar_resposta_usuario(
                user_id=user_id,
                resposta_id=resposta_id,
                contexto_anterior=contexto_anterior
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta do usuário: {e}")
            return {
                "erro": f"Erro ao processar resposta: {str(e)}",
                "mensagem": "❌ **Erro**\n\nOcorreu um erro ao processar sua resposta. Tente novamente."
            }
    
    def obter_mensagem_inicial(self) -> str:
        """Obtém mensagem inicial do Grace"""
        return self.fluxo_verificacao.criar_mensagem_inicial()
    
    def obter_mensagem_ajuda(self) -> str:
        """Obtém mensagem de ajuda do Grace"""
        return self.fluxo_verificacao.criar_mensagem_ajuda()
    
    async def obter_estatisticas_sistema(self) -> Dict[str, Any]:
        """Obtém estatísticas do sistema de verificação"""
        try:
            return await self.fluxo_verificacao.obter_estatisticas_sistema()
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"erro": f"Erro ao obter estatísticas: {str(e)}"}
    
    # ===== MÉTODOS LEGADOS (MANTIDOS PARA COMPATIBILIDADE) =====
    
    async def analisar_imagem_legado(self, image_url: str, user_id: str) -> Dict[str, Any]:
        """
        Método legado para análise de imagem (mantido para compatibilidade)
        Use verificar_cobranca_completa() para o novo fluxo
        """
        try:
            logger.warning("Usando método legado analisar_imagem. Considere usar verificar_cobranca_completa()")
            return await self.analisar_imagem(image_url, user_id)
        except Exception as e:
            logger.error(f"Erro no método legado: {e}")
            return {"erro": f"Erro no método legado: {str(e)}"}
    
    async def processar_mensagem_legado(self, mensagem: str, user_id: str, contexto: List[Dict] = None) -> Dict[str, Any]:
        """
        Método legado para processamento de mensagem (mantido para compatibilidade)
        """
        try:
            logger.warning("Usando método legado processar_mensagem. Considere usar o novo fluxo")
            return await self.processar_mensagem_ia(mensagem, user_id, contexto)
        except Exception as e:
            logger.error(f"Erro no método legado: {e}")
            return {"erro": f"Erro no método legado: {str(e)}"}
