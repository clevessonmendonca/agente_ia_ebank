import json
import requests
from datetime import datetime, timedelta
import hashlib

class AgenteConsultor:
    def __init__(self, db_connection=None):
        """Inicializa o Agente Consultor para validação interna"""
        self.db = db_connection
        self.beneficiarios_validos = [
            "Bemobi Mobile",
            "Bemobi Mobile Ltda",
            "Bemobi Serviços",
            "Bemobi Tecnologia",
            "Bemobi Pagamentos"
        ]
        
        # Simulação de base de dados de clientes
        self.clientes_db = {
            "556185783047": {
                "nome": "Clevesson Mendonça",
                "cpf": "123.456.789-00",
                "cobrancas_pendentes": [
                    {
                        "id": "COB001",
                        "valor": 89.90,
                        "vencimento": "2024-12-15",
                        "servico": "Streaming Premium",
                        "beneficiario": "Bemobi Mobile",
                        "status": "pendente"
                    },
                    {
                        "id": "COB002", 
                        "valor": 29.90,
                        "vencimento": "2024-12-20",
                        "servico": "Assinatura Básica",
                        "beneficiario": "Bemobi Mobile",
                        "status": "pendente"
                    }
                ]
            }
        }
    
    def validar_cobranca(self, cliente_id, dados_pagamento):
        """Valida se cobrança existe no sistema Bemobi"""
        try:
            resultado = {
                'existe': False,
                'valor_correto': False,
                'beneficiario_valido': False,
                'vencimento_valido': False,
                'score_confianca': 0,
                'detalhes': {},
                'alertas': []
            }
            
            # Buscar cliente
            cliente = self.clientes_db.get(cliente_id)
            if not cliente:
                resultado['alertas'].append("Cliente não encontrado no sistema")
                return resultado
            
            # Verificar se há cobranças pendentes
            cobrancas_pendentes = cliente.get('cobrancas_pendentes', [])
            if not cobrancas_pendentes:
                resultado['alertas'].append("Nenhuma cobrança pendente encontrada")
                return resultado
            
            # Verificar valor
            valor_solicitado = dados_pagamento.get('valor')
            if valor_solicitado:
                for cobranca in cobrancas_pendentes:
                    if abs(cobranca['valor'] - valor_solicitado) < 0.01:
                        resultado['valor_correto'] = True
                        resultado['existe'] = True
                        resultado['detalhes']['cobranca_encontrada'] = cobranca
                        break
                
                if not resultado['valor_correto']:
                    resultado['alertas'].append(f"Valor R$ {valor_solicitado} não confere com cobranças pendentes")
            
            # Verificar beneficiário
            beneficiario = dados_pagamento.get('beneficiario', '')
            if beneficiario:
                for benef_valido in self.beneficiarios_validos:
                    if benef_valido.lower() in beneficiario.lower():
                        resultado['beneficiario_valido'] = True
                        break
                
                if not resultado['beneficiario_valido']:
                    resultado['alertas'].append(f"Beneficiário '{beneficiario}' não é reconhecido")
            
            # Verificar vencimento
            vencimento = dados_pagamento.get('vencimento')
            if vencimento:
                try:
                    # Converter data para comparação
                    data_vencimento = datetime.strptime(vencimento, "%d/%m/%Y")
                    hoje = datetime.now()
                    
                    # Verificar se vencimento está dentro de 30 dias
                    if abs((data_vencimento - hoje).days) <= 30:
                        resultado['vencimento_valido'] = True
                    else:
                        resultado['alertas'].append("Data de vencimento fora do prazo esperado")
                        
                except ValueError:
                    resultado['alertas'].append("Formato de data inválido")
            
            # Calcular score de confiança
            resultado['score_confianca'] = self._calcular_score_validacao(resultado)
            
            return resultado
            
        except Exception as e:
            return {
                'erro': f'Erro na validação: {str(e)}',
                'score_confianca': 0
            }
    
    def verificar_historico_cliente(self, cliente_id, dados_pagamento):
        """Verifica histórico de pagamentos do cliente"""
        try:
            cliente = self.clientes_db.get(cliente_id)
            if not cliente:
                return {'erro': 'Cliente não encontrado'}
            
            # Simular histórico de pagamentos
            historico = {
                'total_pagamentos': 12,
                'valor_medio': 45.50,
                'ultimo_pagamento': '2024-11-15',
                'metodo_preferido': 'PIX',
                'frequencia': 'mensal'
            }
            
            # Analisar padrões
            valor_atual = dados_pagamento.get('valor', 0)
            alertas = []
            
            if valor_atual > historico['valor_medio'] * 2:
                alertas.append("Valor muito acima da média histórica")
            
            if valor_atual < 10:
                alertas.append("Valor muito baixo, verificar se é legítimo")
            
            return {
                'historico': historico,
                'alertas': alertas,
                'score_historico': 85 if not alertas else 60
            }
            
        except Exception as e:
            return {'erro': f'Erro ao verificar histórico: {str(e)}'}
    
    def verificar_beneficiario_legitimo(self, beneficiario):
        """Verifica se beneficiário é legítimo"""
        try:
            # Verificar se está na lista de beneficiários válidos
            for benef_valido in self.beneficiarios_validos:
                if benef_valido.lower() in beneficiario.lower():
                    return {
                        'legitimo': True,
                        'nome_oficial': benef_valido,
                        'score': 95
                    }
            
            # Verificar padrões suspeitos
            suspeitas = []
            if 'bemob' in beneficiario.lower() and 'bemobi' not in beneficiario.lower():
                suspeitas.append("Nome similar mas não idêntico à Bemobi")
            
            if len(beneficiario) < 5:
                suspeitas.append("Nome muito curto")
            
            if any(char.isdigit() for char in beneficiario):
                suspeitas.append("Nome contém números")
            
            return {
                'legitimo': False,
                'suspeitas': suspeitas,
                'score': 20 if suspeitas else 50
            }
            
        except Exception as e:
            return {'erro': f'Erro ao verificar beneficiário: {str(e)}'}
    
    def verificar_codigo_barras(self, codigo_barras):
        """Verifica se código de barras é válido"""
        try:
            if not codigo_barras:
                return {'valido': False, 'erro': 'Código de barras não fornecido'}
            
            # Verificar tamanho
            if len(codigo_barras) not in [44, 47]:
                return {'valido': False, 'erro': 'Tamanho inválido do código de barras'}
            
            # Verificar se contém apenas dígitos
            if not codigo_barras.isdigit():
                return {'valido': False, 'erro': 'Código contém caracteres inválidos'}
            
            # Verificar dígito verificador (simplificado)
            if self._validar_digito_verificador(codigo_barras):
                return {'valido': True, 'score': 90}
            else:
                return {'valido': False, 'erro': 'Dígito verificador inválido'}
                
        except Exception as e:
            return {'erro': f'Erro ao verificar código: {str(e)}'}
    
    def _calcular_score_validacao(self, resultado):
        """Calcula score de confiança baseado na validação"""
        score = 0
        
        if resultado['existe']:
            score += 40
        if resultado['valor_correto']:
            score += 30
        if resultado['beneficiario_valido']:
            score += 20
        if resultado['vencimento_valido']:
            score += 10
        
        # Penalizar por alertas
        score -= len(resultado['alertas']) * 5
        
        return max(0, min(100, score))
    
    def _validar_digito_verificador(self, codigo):
        """Valida dígito verificador do código de barras (simplificado)"""
        try:
            # Implementação simplificada do módulo 11
            if len(codigo) == 47:
                # Código de 47 dígitos
                sequencia = codigo[:4] + codigo[5:44]
                dv = codigo[4]
                
                # Cálculo módulo 11
                multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
                soma = 0
                
                for i, digito in enumerate(reversed(sequencia)):
                    mult = multiplicadores[i % len(multiplicadores)]
                    soma += int(digito) * mult
                
                resto = soma % 11
                dv_calculado = 11 - resto if resto > 1 else 0
                
                return str(dv_calculado) == dv
            
            return True  # Para códigos de 44 dígitos, aceitar por enquanto
            
        except:
            return False
    
    def gerar_relatorio_validacao(self, cliente_id, dados_pagamento):
        """Gera relatório completo de validação"""
        try:
            # Executar todas as validações
            validacao_cobranca = self.validar_cobranca(cliente_id, dados_pagamento)
            historico = self.verificar_historico_cliente(cliente_id, dados_pagamento)
            beneficiario = self.verificar_beneficiario_legitimo(dados_pagamento.get('beneficiario', ''))
            codigo_barras = self.verificar_codigo_barras(dados_pagamento.get('codigo_barras', ''))
            
            # Consolidar resultados
            relatorio = {
                'cliente_id': cliente_id,
                'timestamp': datetime.now().isoformat(),
                'validacao_cobranca': validacao_cobranca,
                'historico_cliente': historico,
                'beneficiario': beneficiario,
                'codigo_barras': codigo_barras,
                'score_final': self._calcular_score_final(validacao_cobranca, historico, beneficiario, codigo_barras),
                'recomendacao': self._gerar_recomendacao(validacao_cobranca, historico, beneficiario)
            }
            
            return relatorio
            
        except Exception as e:
            return {'erro': f'Erro ao gerar relatório: {str(e)}'}
    
    def _calcular_score_final(self, validacao, historico, beneficiario, codigo_barras):
        """Calcula score final consolidado"""
        scores = []
        
        if 'score_confianca' in validacao:
            scores.append(validacao['score_confianca'])
        
        if 'score_historico' in historico:
            scores.append(historico['score_historico'])
        
        if 'score' in beneficiario:
            scores.append(beneficiario['score'])
        
        if 'score' in codigo_barras:
            scores.append(codigo_barras['score'])
        
        if scores:
            return sum(scores) // len(scores)
        else:
            return 0
    
    def _gerar_recomendacao(self, validacao, historico, beneficiario):
        """Gera recomendação baseada nos resultados"""
        if validacao.get('score_confianca', 0) >= 80:
            return "✅ PAGAMENTO SEGURO - Pode prosseguir"
        elif validacao.get('score_confianca', 0) >= 60:
            return "⚠️ ATENÇÃO - Verificar dados antes de pagar"
        else:
            return "🚨 SUSPEITO - Não recomendado pagar"
