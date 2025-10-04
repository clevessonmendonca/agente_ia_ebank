import cv2
import pytesseract
import re
import base64
from PIL import Image
import numpy as np
import requests
import json

class AgenteLeitorOCR:
    def __init__(self):
        """Inicializa o Agente Leitor para extração de dados de boletos e PIX"""
        self.config_tesseract = '--oem 3 --psm 6'
        
    def extrair_dados_boleto(self, imagem_path):
        """Extrai dados de boleto usando OCR"""
        try:
            # Carregar imagem
            img = cv2.imread(imagem_path)
            if img is None:
                return {'erro': 'Imagem não encontrada'}
            
            # Pré-processamento
            img_processada = self._preprocessar_imagem(img)
            
            # OCR
            texto = pytesseract.image_to_string(img_processada, lang='por', config=self.config_tesseract)
            
            # Extrair dados específicos
            dados = {
                'codigo_barras': self._extrair_codigo_barras(texto),
                'valor': self._extrair_valor(texto),
                'vencimento': self._extrair_data_vencimento(texto),
                'beneficiario': self._extrair_beneficiario(texto),
                'texto_completo': texto,
                'qualidade_imagem': self._avaliar_qualidade_imagem(img)
            }
            
            return dados
            
        except Exception as e:
            return {'erro': f'Erro no OCR: {str(e)}'}
    
    def extrair_dados_pix(self, codigo_pix):
        """Decodifica PIX copia e cola"""
        try:
            # PIX é base64, decodificar
            if len(codigo_pix) < 50:
                return {'erro': 'Código PIX muito curto'}
            
            # Adicionar padding se necessário
            codigo_completo = codigo_pix + '=='
            decoded = base64.b64decode(codigo_completo)
            texto = decoded.decode('utf-8', errors='ignore')
            
            # Extrair campos do PIX
            dados = {
                'chave_pix': self._extrair_campo_pix(texto, '59'),  # Beneficiário
                'valor': self._extrair_campo_pix(texto, '54'),      # Valor
                'cidade': self._extrair_campo_pix(texto, '60'),     # Cidade
                'identificador': self._extrair_campo_pix(texto, '05'), # ID
                'texto_completo': texto
            }
            
            return dados
            
        except Exception as e:
            return {'erro': f'Erro ao decodificar PIX: {str(e)}'}
    
    def _preprocessar_imagem(self, img):
        """Melhora a qualidade da imagem para OCR"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Reduzir ruído
        denoised = cv2.medianBlur(gray, 3)
        
        # Melhorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Binarização
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def _extrair_codigo_barras(self, texto):
        """Extrai código de barras (44 ou 47 dígitos)"""
        # Remover espaços e quebras de linha
        texto_limpo = re.sub(r'\s+', '', texto)
        
        # Buscar sequência de 44-47 dígitos
        match = re.search(r'\d{44,47}', texto_limpo)
        if match:
            return match.group(0)
        
        # Buscar padrão alternativo
        match = re.search(r'\d{5}\.\d{5}\.\d{5}\.\d{6}\.\d{5}\.\d{6}\.\d{1}\.\d{14}', texto_limpo)
        if match:
            return match.group(0).replace('.', '')
        
        return None
    
    def _extrair_valor(self, texto):
        """Extrai valor monetário"""
        # Padrões de valor
        padroes = [
            r'R\$\s*(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*reais',
            r'valor[:\s]*(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    return float(valor_str)
                except:
                    continue
        
        return None
    
    def _extrair_data_vencimento(self, texto):
        """Extrai data de vencimento"""
        # Padrões de data
        padroes = [
            r'(\d{2})/(\d{2})/(\d{4})',
            r'(\d{2})-(\d{2})-(\d{4})',
            r'vencimento[:\s]*(\d{2})/(\d{2})/(\d{4})'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extrair_beneficiario(self, texto):
        """Extrai nome do beneficiário"""
        linhas = texto.split('\n')
        
        # Palavras-chave que indicam beneficiário
        palavras_chave = ['beneficiário', 'cedente', 'empresa', 'favorecido', 'recebedor']
        
        for linha in linhas:
            linha_limpa = linha.strip()
            if len(linha_limpa) > 5:  # Ignorar linhas muito curtas
                for palavra in palavras_chave:
                    if palavra.lower() in linha_limpa.lower():
                        return linha_limpa
        
        # Se não encontrou, pegar a linha mais longa que não seja número
        linhas_validas = [l for l in linhas if len(l.strip()) > 10 and not l.strip().isdigit()]
        if linhas_validas:
            return max(linhas_validas, key=len).strip()
        
        return None
    
    def _extrair_campo_pix(self, texto, id_campo):
        """Extrai campo específico do PIX"""
        pattern = f"{id_campo}(\\d{{2}})(.+?)"
        match = re.search(pattern, texto)
        if match:
            tamanho = int(match.group(1))
            return match.group(2)[:tamanho]
        return None
    
    def _avaliar_qualidade_imagem(self, img):
        """Avalia qualidade da imagem"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calcular variância do Laplaciano (medida de nitidez)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Classificar qualidade
        if laplacian_var > 100:
            return "ALTA"
        elif laplacian_var > 50:
            return "MÉDIA"
        else:
            return "BAIXA"
    
    def detectar_suspeitas_visuais(self, img):
        """Detecta características suspeitas na imagem"""
        suspeitas = []
        
        # Verificar resolução
        height, width = img.shape[:2]
        if height < 200 or width < 200:
            suspeitas.append("Resolução muito baixa")
        
        # Verificar qualidade
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 30:
            suspeitas.append("Imagem muito borrada")
        
        # Verificar se há muito ruído
        noise = cv2.fastNlMeansDenoising(gray)
        diff = cv2.absdiff(gray, noise)
        noise_level = np.mean(diff)
        if noise_level > 30:
            suspeitas.append("Muito ruído na imagem")
        
        return suspeitas
