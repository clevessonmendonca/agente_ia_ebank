"""
Agente Consultor - Validação nos sistemas Bemobi
Responsável por verificar se o dado existe e é legítimo nos sistemas internos
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from groq import Groq
import logging
from datetime import datetime, timedelta
import httpx
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

class AgenteConsultor:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"
        
        # Simulação de sistemas Bemobi (em produção seria APIs reais)
        self.sistemas_bemobi = {
            "clientes_ativos": {},
            "cobrancas_pendentes": {},
            "beneficiarios_legitimos": {},
            "historico_pagamentos": {}
        }
        
        # Inicializar dados de exemplo
        self._inicializar_dados_exemplo()
    
    def _inicializar_dados_exemplo(self):
        """Inicializa dados de exemplo para simulação"""
        # Clientes ativos
        self.sistemas_bemobi["clientes_ativos"] = {
            "12345678901": {
                "nome": "João Silva",
                "servicos": ["streaming", "internet"],
                "status": "ativo",
                "ultimo_pagamento": "2024-11-15"
            },
            "98765432100": {
                "nome": "Maria Santos",
                "servicos": ["streaming"],
                "status": "ativo", 
                "ultimo_pagamento": "2024-11-10"
            }
        }
        
        # Cobranças pendentes
        self.sistemas_bemobi["cobrancas_pendentes"] = {
            "12345678901": [
                {
                    "valor": 89.90,
                    "servico": "streaming",
                    "vencimento": "2024-12-15",
                    "status": "pendente"
                }
            ],
            "98765432100": [
                {
                    "valor": 89.90,
                    "servico": "streaming", 
                    "vencimento": "2024-12-10",
                    "status": "pendente"
                }
            ]
        }
        
        # Beneficiários legítimos
        self.sistemas_bemobi["beneficiarios_legitimos"] = {
            "Bemobi Tecnologia": {
                "cnpj": "12.345.678/0001-90",
                "status": "ativo",
                "servicos": ["streaming", "internet"]
            },
            "Bemobi Streaming": {
                "cnpj": "98.765.432/0001-10", 
                "status": "ativo",
                "servicos": ["streaming"]
            }
        }
    
    async def validar_cobranca(self, dados_extraidos: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Valida cobrança nos sistemas Bemobi"""
        try:
            logger.info(f"Agente Consultor: Validando cobrança para usuário {user_id}")
            
            resultado = {
                "agente": "consultor",
                "sucesso": True,
                "validacoes": {},
                "alertas": [],
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
            # 1. Verificar se cliente tem cobrança aberta
            validacao_cliente = await self._verificar_cliente(user_id, dados_extraidos)
            resultado["validacoes"]["cliente"] = validacao_cliente
            
            # 2. Verificar se beneficiário é legítimo
            validacao_beneficiario = await self._verificar_beneficiario(dados_extraidos)
            resultado["validacoes"]["beneficiario"] = validacao_beneficiario
            
            # 3. Verificar valor da cobrança
            validacao_valor = await self._verificar_valor(user_id, dados_extraidos)
            resultado["validacoes"]["valor"] = validacao_valor
            
            # 4. Verificar histórico do cliente
            validacao_historico = await self._verificar_historico(user_id, dados_extraidos)
            resultado["validacoes"]["historico"] = validacao_historico
            
            # Gerar alertas baseados nas validações
            resultado["alertas"] = self._gerar_alertas(resultado["validacoes"])
            
            # Análise final com IA
            analise_final = await self._analisar_validacao_com_ia(resultado)
            resultado["analise_ia"] = analise_final
            
            logger.info(f"Agente Consultor: Validação concluída para usuário {user_id}")
            return resultado
            
        except Exception as e:
            logger.error(f"Agente Consultor: Erro na validação - {e}")
            return {
                "agente": "consultor",
                "erro": f"Erro na validação: {str(e)}",
                "sucesso": False
            }
    
    async def _verificar_cliente(self, user_id: str, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se o cliente tem cobranças pendentes"""
        try:
            # Simular consulta ao sistema de clientes
            cliente = self.sistemas_bemobi["clientes_ativos"].get(user_id)
            
            if not cliente:
                return {
                    "status": "cliente_nao_encontrado",
                    "mensagem": "Cliente não encontrado no sistema",
                    "confiabilidade": 0
                }
            
            cobrancas = self.sistemas_bemobi["cobrancas_pendentes"].get(user_id, [])
            
            if not cobrancas:
                return {
                    "status": "sem_cobrancas_pendentes",
                    "mensagem": "Cliente não possui cobranças pendentes",
                    "confiabilidade": 20
                }
            
            return {
                "status": "cliente_com_cobrancas",
                "mensagem": f"Cliente possui {len(cobrancas)} cobrança(s) pendente(s)",
                "confiabilidade": 80,
                "cobrancas": cobrancas
            }
            
        except Exception as e:
            return {
                "status": "erro_verificacao",
                "mensagem": f"Erro ao verificar cliente: {str(e)}",
                "confiabilidade": 0
            }
    
    async def _verificar_beneficiario(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se o beneficiário é legítimo"""
        try:
            beneficiario = dados.get("nome_beneficiario", "")
            
            if not beneficiario:
                return {
                    "status": "beneficiario_nao_identificado",
                    "mensagem": "Beneficiário não identificado no documento",
                    "confiabilidade": 10
                }
            
            # Verificar se está na lista de beneficiários legítimos
            for nome_legitimo, info in self.sistemas_bemobi["beneficiarios_legitimos"].items():
                if nome_legitimo.lower() in beneficiario.lower():
                    return {
                        "status": "beneficiario_legitimo",
                        "mensagem": f"Beneficiário {nome_legitimo} é legítimo",
                        "confiabilidade": 90,
                        "dados_beneficiario": info
                    }
            
            return {
                "status": "beneficiario_nao_legitimo",
                "mensagem": f"Beneficiário '{beneficiario}' não é legítimo",
                "confiabilidade": 5
            }
            
        except Exception as e:
            return {
                "status": "erro_verificacao",
                "mensagem": f"Erro ao verificar beneficiário: {str(e)}",
                "confiabilidade": 0
            }
    
    async def _verificar_valor(self, user_id: str, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se o valor da cobrança está correto"""
        try:
            valor_cobranca = dados.get("valor_cobrado", "")
            
            if not valor_cobranca:
                return {
                    "status": "valor_nao_identificado",
                    "mensagem": "Valor não identificado no documento",
                    "confiabilidade": 10
                }
            
            # Extrair valor numérico
            valor_numerico = self._extrair_valor_numerico(valor_cobranca)
            
            if not valor_numerico:
                return {
                    "status": "valor_invalido",
                    "mensagem": "Valor em formato inválido",
                    "confiabilidade": 5
                }
            
            # Verificar se valor bate com cobranças pendentes
            cobrancas = self.sistemas_bemobi["cobrancas_pendentes"].get(user_id, [])
            
            for cobranca in cobrancas:
                if abs(cobranca["valor"] - valor_numerico) < 0.01:  # Tolerância de 1 centavo
                    return {
                        "status": "valor_correto",
                        "mensagem": f"Valor R$ {valor_numerico:.2f} confere com cobrança pendente",
                        "confiabilidade": 95,
                        "cobranca_correspondente": cobranca
                    }
            
            # Verificar se valor está dentro de faixa esperada
            if 50 <= valor_numerico <= 200:  # Faixa típica de serviços Bemobi
                return {
                    "status": "valor_suspeito",
                    "mensagem": f"Valor R$ {valor_numerico:.2f} não confere com cobranças pendentes",
                    "confiabilidade": 30
                }
            
            return {
                "status": "valor_muito_alto",
                "mensagem": f"Valor R$ {valor_numerico:.2f} muito alto para serviços Bemobi",
                "confiabilidade": 10
            }
            
        except Exception as e:
            return {
                "status": "erro_verificacao",
                "mensagem": f"Erro ao verificar valor: {str(e)}",
                "confiabilidade": 0
            }
    
    async def _verificar_historico(self, user_id: str, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica histórico do cliente"""
        try:
            cliente = self.sistemas_bemobi["clientes_ativos"].get(user_id)
            
            if not cliente:
                return {
                    "status": "cliente_nao_encontrado",
                    "mensagem": "Cliente não encontrado",
                    "confiabilidade": 0
                }
            
            # Verificar último pagamento
            ultimo_pagamento = cliente.get("ultimo_pagamento")
            if ultimo_pagamento:
                data_ultimo = datetime.strptime(ultimo_pagamento, "%Y-%m-%d")
                dias_desde_ultimo = (datetime.now() - data_ultimo).days
                
                if dias_desde_ultimo <= 30:
                    return {
                        "status": "historico_recente",
                        "mensagem": f"Último pagamento há {dias_desde_ultimo} dias",
                        "confiabilidade": 85
                    }
                elif dias_desde_ultimo <= 60:
                    return {
                        "status": "historico_moderado",
                        "mensagem": f"Último pagamento há {dias_desde_ultimo} dias",
                        "confiabilidade": 70
                    }
                else:
                    return {
                        "status": "historico_antigo",
                        "mensagem": f"Último pagamento há {dias_desde_ultimo} dias",
                        "confiabilidade": 40
                    }
            
            return {
                "status": "sem_historico",
                "mensagem": "Cliente sem histórico de pagamentos",
                "confiabilidade": 20
            }
            
        except Exception as e:
            return {
                "status": "erro_verificacao",
                "mensagem": f"Erro ao verificar histórico: {str(e)}",
                "confiabilidade": 0
            }
    
    def _extrair_valor_numerico(self, valor_str: str) -> Optional[float]:
        """Extrai valor numérico de string"""
        try:
            # Remover R$ e espaços
            valor_limpo = valor_str.replace("R$", "").replace(" ", "").strip()
            
            # Substituir vírgula por ponto para conversão
            valor_limpo = valor_limpo.replace(",", ".")
            
            return float(valor_limpo)
        except (ValueError, AttributeError):
            return None
    
    def _gerar_alertas(self, validacoes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera alertas baseados nas validações"""
        alertas = []
        
        for tipo, validacao in validacoes.items():
            confiabilidade = validacao.get("confiabilidade", 0)
            
            if confiabilidade < 30:
                alertas.append({
                    "tipo": "alerta_alto",
                    "categoria": tipo,
                    "mensagem": f"⚠️ {validacao.get('mensagem', '')}",
                    "prioridade": "alta"
                })
            elif confiabilidade < 60:
                alertas.append({
                    "tipo": "alerta_medio",
                    "categoria": tipo,
                    "mensagem": f"⚠️ {validacao.get('mensagem', '')}",
                    "prioridade": "media"
                })
        
        return alertas
    
    async def _analisar_validacao_com_ia(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Análise final usando IA da Groq"""
        try:
            prompt = f"""
            Analise os resultados da validação nos sistemas Bemobi:
            
            Validações realizadas: {json.dumps(resultado['validacoes'], ensure_ascii=False, indent=2)}
            Alertas gerados: {json.dumps(resultado['alertas'], ensure_ascii=False, indent=2)}
            
            Forneça uma análise consolidada incluindo:
            1. Pontuação geral de confiabilidade (0-100)
            2. Principais riscos identificados
            3. Recomendações para o cliente
            4. Próximos passos sugeridos
            
            Responda em formato JSON estruturado.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1
            )
            
            analise = response.choices[0].message.content
            
            try:
                return json.loads(analise)
            except json.JSONDecodeError:
                return {"analise_texto": analise, "tipo": "texto"}
                
        except Exception as e:
            logger.error(f"Erro na análise com IA: {e}")
            return {"erro": f"Erro na análise IA: {str(e)}"}
