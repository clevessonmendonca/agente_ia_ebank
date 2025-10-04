import requests
import json
from datetime import datetime

class MayAPIClient:
    def __init__(self, product_id, token):
        """Inicializa cliente MayAPI"""
        self.product_id = product_id
        self.token = token
        self.base_url = f"https://api.maytapi.com/api/{product_id}"
        self.headers = {
            "x-maytapi-key": token,
            "accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def verificar_cobranca(self, dados_pagamento):
        """Verifica cobrança via MayAPI"""
        try:
            payload = {
                "product_id": self.product_id,
                "dados_pagamento": {
                    "valor": dados_pagamento.get('valor'),
                    "beneficiario": dados_pagamento.get('beneficiario'),
                    "vencimento": dados_pagamento.get('vencimento'),
                    "codigo_barras": dados_pagamento.get('codigo_barras'),
                    "chave_pix": dados_pagamento.get('chave_pix')
                }
            }
            
            response = requests.post(
                f"{self.base_url}/verificar-cobranca",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'erro': f'Erro na API: {response.status_code}',
                    'detalhes': response.text
                }
                
        except Exception as e:
            return {
                'erro': f'Erro na comunicação: {str(e)}',
                'fallback': True
            }
    
    def detectar_fraude(self, dados_pagamento):
        """Detecta fraudes via MayAPI"""
        try:
            payload = {
                "product_id": self.product_id,
                "dados_pagamento": dados_pagamento,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.base_url}/detectar-fraude",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'erro': f'Erro na API: {response.status_code}',
                    'score_fraude': 50,  # Score neutro em caso de erro
                    'fallback': True
                }
                
        except Exception as e:
            return {
                'erro': f'Erro na comunicação: {str(e)}',
                'score_fraude': 50,
                'fallback': True
            }
    
    def validar_beneficiario(self, beneficiario):
        """Valida beneficiário via MayAPI"""
        try:
            payload = {
                "product_id": self.product_id,
                "beneficiario": beneficiario
            }
            
            response = requests.post(
                f"{self.base_url}/validar-beneficiario",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'erro': f'Erro na API: {response.status_code}',
                    'valido': False,
                    'fallback': True
                }
                
        except Exception as e:
            return {
                'erro': f'Erro na comunicação: {str(e)}',
                'valido': False,
                'fallback': True
            }
    
    def gerar_score_confianca(self, dados_pagamento):
        """Gera score de confiança via MayAPI"""
        try:
            payload = {
                "product_id": self.product_id,
                "dados_pagamento": dados_pagamento,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.base_url}/score-confianca",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'erro': f'Erro na API: {response.status_code}',
                    'score': 50,  # Score neutro
                    'fallback': True
                }
                
        except Exception as e:
            return {
                'erro': f'Erro na comunicação: {str(e)}',
                'score': 50,
                'fallback': True
            }
    
    def reportar_fraude(self, dados_fraude):
        """Reporta fraude via MayAPI"""
        try:
            payload = {
                "product_id": self.product_id,
                "dados_fraude": dados_fraude,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.base_url}/reportar-fraude",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'erro': f'Erro na API: {response.status_code}',
                    'reportado': False
                }
                
        except Exception as e:
            return {
                'erro': f'Erro na comunicação: {str(e)}',
                'reportado': False
            }
    
    def obter_estatisticas(self):
        """Obtém estatísticas via MayAPI"""
        try:
            response = requests.get(
                f"{self.base_url}/estatisticas",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'erro': f'Erro na API: {response.status_code}',
                    'fallback': True
                }
                
        except Exception as e:
            return {
                'erro': f'Erro na comunicação: {str(e)}',
                'fallback': True
            }

