import requests
import json
from datetime import datetime, timedelta
import hashlib
import re
from mayapi_client import MayAPIClient
import os
from dotenv import load_dotenv

class AgenteDetetive:
    def __init__(self):
        """Inicializa o Agente Detetive para detecção de fraudes"""
        load_dotenv()
        
        # Inicializar MayAPI
        self.mayapi = MayAPIClient(
            os.getenv('MAYAPI_PRODUCT_ID'),
            os.getenv('MAYAPI_TOKEN')
        )
        
        # Base de fraudes conhecidas
        self.fraudes_conhecidas = set()
        self.padroes_suspeitos = [
            'urgente', 'imediato', 'bloqueio', 'suspensão', 'reative',
            'clique aqui', 'link', 'pague agora', 'vencimento hoje',
            'multa', 'juros', 'desconto', 'oferta limitada'
        ]
        
        # Horários suspeitos (madrugada)
        self.horarios_suspeitos = [(0, 6), (22, 24)]
        
        # Valores suspeitos
        self.valores_suspeitos = {
            'muito_alto': 1000,
            'muito_baixo': 5,
            'valores_redondos': [100, 200, 500, 1000]
        }
    
    def analisar_fraude_completa(self, dados_pagamento, cliente_id=None):
        """Análise completa de fraude usando múltiplas camadas"""
        try:
            resultado = {
                'score_fraude': 0,
                'nivel_risco': 'BAIXO',
                'sinais_suspeitos': [],
                'recomendacao': '',
                'timestamp': datetime.now().isoformat(),
                'detalhes': {}
            }
            
            # 1. Análise de padrões de texto
            analise_texto = self._analisar_padroes_texto(dados_pagamento)
            resultado['sinais_suspeitos'].extend(analise_texto['sinais'])
            resultado['score_fraude'] += analise_texto['score']
            
            # 2. Análise de horário
            analise_horario = self._analisar_horario()
            resultado['sinais_suspeitos'].extend(analise_horario['sinais'])
            resultado['score_fraude'] += analise_horario['score']
            
            # 3. Análise de valor
            analise_valor = self._analisar_valor(dados_pagamento.get('valor', 0))
            resultado['sinais_suspeitos'].extend(analise_valor['sinais'])
            resultado['score_fraude'] += analise_valor['score']
            
            # 4. Análise de beneficiário
            analise_beneficiario = self._analisar_beneficiario(dados_pagamento.get('beneficiario', ''))
            resultado['sinais_suspeitos'].extend(analise_beneficiario['sinais'])
            resultado['score_fraude'] += analise_beneficiario['score']
            
            # 5. Análise de código de barras
            analise_codigo = self._analisar_codigo_barras(dados_pagamento.get('codigo_barras', ''))
            resultado['sinais_suspeitos'].extend(analise_codigo['sinais'])
            resultado['score_fraude'] += analise_codigo['score']
            
            # 6. Verificar base de fraudes conhecidas
            analise_base = self._verificar_base_fraudes(dados_pagamento)
            resultado['sinais_suspeitos'].extend(analise_base['sinais'])
            resultado['score_fraude'] += analise_base['score']
            
            # 7. Análise via MayAPI (se disponível)
            try:
                analise_mayapi = self.mayapi.detectar_fraude(dados_pagamento)
                if not analise_mayapi.get('erro'):
                    resultado['score_fraude'] += analise_mayapi.get('score_fraude', 0)
                    resultado['detalhes']['mayapi'] = analise_mayapi
            except:
                pass  # Continuar sem MayAPI se houver erro
            
            # Calcular score final e classificação
            resultado['score_fraude'] = min(100, resultado['score_fraude'])
            resultado['nivel_risco'] = self._classificar_risco(resultado['score_fraude'])
            resultado['recomendacao'] = self._gerar_recomendacao(resultado['score_fraude'])
            
            return resultado
            
        except Exception as e:
            return {
                'erro': f'Erro na análise de fraude: {str(e)}',
                'score_fraude': 50,
                'nivel_risco': 'MÉDIO'
            }
    
    def _analisar_padroes_texto(self, dados_pagamento):
        """Analisa padrões suspeitos no texto"""
        sinais = []
        score = 0
        
        # Combinar todos os textos para análise
        texto_completo = ' '.join([
            str(dados_pagamento.get('beneficiario', '')),
            str(dados_pagamento.get('texto_completo', '')),
            str(dados_pagamento.get('chave_pix', ''))
        ]).lower()
        
        # Verificar padrões suspeitos
        for padrao in self.padroes_suspeitos:
            if padrao in texto_completo:
                sinais.append(f"Linguagem de urgência: '{padrao}'")
                score += 10
        
        # Verificar URLs suspeitas
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', texto_completo)
        for url in urls:
            if any(dominio in url for dominio in ['bit.ly', 'tinyurl', 'short.link']):
                sinais.append(f"URL suspeita: {url}")
                score += 15
        
        # Verificar caracteres especiais excessivos
        if len(re.findall(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?]', texto_completo)) > 10:
            sinais.append("Muitos caracteres especiais")
            score += 5
        
        return {'sinais': sinais, 'score': score}
    
    def _analisar_horario(self):
        """Analisa se o horário é suspeito"""
        sinais = []
        score = 0
        
        hora_atual = datetime.now().hour
        
        for inicio, fim in self.horarios_suspeitos:
            if inicio <= hora_atual < fim:
                sinais.append(f"Cobrança enviada em horário suspeito ({hora_atual:02d}:00)")
                score += 15
                break
        
        return {'sinais': sinais, 'score': score}
    
    def _analisar_valor(self, valor):
        """Analisa se o valor é suspeito"""
        sinais = []
        score = 0
        
        if not valor:
            return {'sinais': sinais, 'score': score}
        
        # Valor muito alto
        if valor > self.valores_suspeitos['muito_alto']:
            sinais.append(f"Valor muito alto: R$ {valor}")
            score += 20
        
        # Valor muito baixo
        if valor < self.valores_suspeitos['muito_baixo']:
            sinais.append(f"Valor muito baixo: R$ {valor}")
            score += 10
        
        # Valores redondos suspeitos
        if valor in self.valores_suspeitos['valores_redondos']:
            sinais.append(f"Valor redondo suspeito: R$ {valor}")
            score += 5
        
        return {'sinais': sinais, 'score': score}
    
    def _analisar_beneficiario(self, beneficiario):
        """Analisa se o beneficiário é suspeito"""
        sinais = []
        score = 0
        
        if not beneficiario:
            return {'sinais': sinais, 'score': score}
        
        # Nomes suspeitos conhecidos
        nomes_suspeitos = [
            'bemob1', 'bemobi1', 'bemobi cobrança', 'bemobi pagamentos',
            'bemobi ltda', 'bemobi mobile ltda', 'bemobi serviços'
        ]
        
        beneficiario_lower = beneficiario.lower()
        
        for nome_suspeito in nomes_suspeitos:
            if nome_suspeito in beneficiario_lower:
                sinais.append(f"Beneficiário suspeito: '{beneficiario}'")
                score += 25
                break
        
        # Verificar se contém números
        if re.search(r'\d', beneficiario):
            sinais.append("Beneficiário contém números")
            score += 10
        
        # Verificar se é muito curto
        if len(beneficiario) < 5:
            sinais.append("Nome do beneficiário muito curto")
            score += 15
        
        return {'sinais': sinais, 'score': score}
    
    def _analisar_codigo_barras(self, codigo_barras):
        """Analisa se o código de barras é suspeito"""
        sinais = []
        score = 0
        
        if not codigo_barras:
            return {'sinais': sinais, 'score': score}
        
        # Verificar tamanho
        if len(codigo_barras) not in [44, 47]:
            sinais.append("Código de barras com tamanho inválido")
            score += 20
        
        # Verificar se contém apenas dígitos
        if not codigo_barras.isdigit():
            sinais.append("Código de barras contém caracteres inválidos")
            score += 15
        
        # Verificar padrões suspeitos
        if codigo_barras.count('0') > len(codigo_barras) * 0.8:
            sinais.append("Código de barras com muitos zeros")
            score += 10
        
        return {'sinais': sinais, 'score': score}
    
    def _verificar_base_fraudes(self, dados_pagamento):
        """Verifica contra base de fraudes conhecidas"""
        sinais = []
        score = 0
        
        # Hash do beneficiário
        beneficiario = dados_pagamento.get('beneficiario', '')
        if beneficiario:
            hash_beneficiario = hashlib.md5(beneficiario.encode()).hexdigest()
            if hash_beneficiario in self.fraudes_conhecidas:
                sinais.append("Beneficiário já reportado como fraude")
                score += 50
        
        # Hash do código de barras
        codigo_barras = dados_pagamento.get('codigo_barras', '')
        if codigo_barras:
            hash_codigo = hashlib.md5(codigo_barras.encode()).hexdigest()
            if hash_codigo in self.fraudes_conhecidas:
                sinais.append("Código de barras já reportado como fraude")
                score += 50
        
        return {'sinais': sinais, 'score': score}
    
    def _classificar_risco(self, score):
        """Classifica nível de risco"""
        if score >= 70:
            return "ALTO"
        elif score >= 40:
            return "MÉDIO"
        else:
            return "BAIXO"
    
    def _gerar_recomendacao(self, score):
        """Gera recomendação baseada no score"""
        if score >= 70:
            return "🚨 NÃO PAGUE! Este pagamento é muito suspeito. Entre em contato com o suporte."
        elif score >= 40:
            return "⚠️ ATENÇÃO! Verifique diretamente com a empresa antes de pagar."
        else:
            return "✅ Pagamento parece seguro, mas sempre confirme os dados."
    
    def reportar_fraude(self, dados_fraude):
        """Reporta fraude para a base de conhecimento"""
        try:
            # Adicionar à base local
            if dados_fraude.get('beneficiario'):
                hash_beneficiario = hashlib.md5(dados_fraude['beneficiario'].encode()).hexdigest()
                self.fraudes_conhecidas.add(hash_beneficiario)
            
            if dados_fraude.get('codigo_barras'):
                hash_codigo = hashlib.md5(dados_fraude['codigo_barras'].encode()).hexdigest()
                self.fraudes_conhecidas.add(hash_codigo)
            
            # Reportar via MayAPI
            try:
                resultado_mayapi = self.mayapi.reportar_fraude(dados_fraude)
                return {
                    'reportado_local': True,
                    'reportado_mayapi': not resultado_mayapi.get('erro', False),
                    'timestamp': datetime.now().isoformat()
                }
            except:
                return {
                    'reportado_local': True,
                    'reportado_mayapi': False,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {'erro': f'Erro ao reportar fraude: {str(e)}'}
    
    def obter_estatisticas_fraudes(self):
        """Obtém estatísticas de fraudes"""
        try:
            # Estatísticas locais
            stats_locais = {
                'fraudes_conhecidas': len(self.fraudes_conhecidas),
                'padroes_suspeitos': len(self.padroes_suspeitos),
                'timestamp': datetime.now().isoformat()
            }
            
            # Tentar obter estatísticas via MayAPI
            try:
                stats_mayapi = self.mayapi.obter_estatisticas()
                if not stats_mayapi.get('erro'):
                    stats_locais['mayapi'] = stats_mayapi
            except:
                pass
            
            return stats_locais
            
        except Exception as e:
            return {'erro': f'Erro ao obter estatísticas: {str(e)}'}
