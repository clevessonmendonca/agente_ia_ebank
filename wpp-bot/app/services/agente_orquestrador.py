"""
Agente Orquestrador - Consolidação da análise
Responsável por consolidar resultados dos três agentes e gerar decisão final
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from groq import Groq
import logging
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

class StatusVerificacao(Enum):
    SEGURO = "seguro"
    SUSPEITO = "suspeito"
    GOLPE = "golpe"

class AgenteOrquestrador:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"
        
        # Pesos para cálculo da pontuação final
        self.pesos = {
            "leitor": 0.2,      # 20% - Qualidade da extração
            "consultor": 0.4,   # 40% - Validação nos sistemas
            "detetive": 0.4     # 40% - Detecção de fraudes
        }
    
    async def orquestrar_analise(self, 
                                resultado_leitor: Dict[str, Any],
                                resultado_consultor: Dict[str, Any], 
                                resultado_detetive: Dict[str, Any],
                                user_id: str) -> Dict[str, Any]:
        """Orquestra a análise final consolidando todos os agentes"""
        try:
            logger.info(f"Agente Orquestrador: Consolidando análise para usuário {user_id}")
            
            resultado_final = {
                "agente": "orquestrador",
                "sucesso": True,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "resultados_agentes": {
                    "leitor": resultado_leitor,
                    "consultor": resultado_consultor,
                    "detetive": resultado_detetive
                }
            }
            
            # 1. Calcular pontuação de confiança
            pontuacao_confianca = self._calcular_pontuacao_confianca(
                resultado_leitor, resultado_consultor, resultado_detetive
            )
            resultado_final["pontuacao_confianca"] = pontuacao_confianca
            
            # 2. Determinar status da verificação
            status_verificacao = self._determinar_status_verificacao(pontuacao_confianca)
            resultado_final["status_verificacao"] = status_verificacao.value
            
            # 3. Gerar mensagem para o usuário
            mensagem_usuario = self._gerar_mensagem_usuario(status_verificacao, pontuacao_confianca)
            resultado_final["mensagem_usuario"] = mensagem_usuario
            
            # 4. Gerar recomendações
            recomendacoes = self._gerar_recomendacoes(status_verificacao, resultado_final)
            resultado_final["recomendacoes"] = recomendacoes
            
            # 5. Gerar alertas consolidados
            alertas_consolidados = self._consolidar_alertas(resultado_final)
            resultado_final["alertas_consolidados"] = alertas_consolidados
            
            # 6. Análise final com IA
            analise_final_ia = await self._analise_final_com_ia(resultado_final)
            resultado_final["analise_final_ia"] = analise_final_ia
            
            # 7. Gerar dados para interface visual
            dados_visuais = self._gerar_dados_visuais(status_verificacao, pontuacao_confianca)
            resultado_final["dados_visuais"] = dados_visuais
            
            logger.info(f"Agente Orquestrador: Análise consolidada - Status: {status_verificacao.value}, Confiança: {pontuacao_confianca}%")
            return resultado_final
            
        except Exception as e:
            logger.error(f"Agente Orquestrador: Erro na consolidação - {e}")
            return {
                "agente": "orquestrador",
                "erro": f"Erro na consolidação: {str(e)}",
                "sucesso": False
            }
    
    def _calcular_pontuacao_confianca(self, 
                                    resultado_leitor: Dict[str, Any],
                                    resultado_consultor: Dict[str, Any],
                                    resultado_detetive: Dict[str, Any]) -> int:
        """Calcula pontuação final de confiança (0-100)"""
        try:
            pontuacao_total = 0
            
            # Pontuação do Agente Leitor (20%)
            if resultado_leitor.get("sucesso"):
                qualidade_imagem = resultado_leitor.get("dados_extraidos", {}).get("qualidade_imagem", "boa")
                if qualidade_imagem == "boa":
                    pontuacao_total += 20
                elif qualidade_imagem == "ruim":
                    pontuacao_total += 5
                else:
                    pontuacao_total += 10
            else:
                pontuacao_total += 0
            
            # Pontuação do Agente Consultor (40%)
            if resultado_consultor.get("sucesso"):
                validacoes = resultado_consultor.get("validacoes", {})
                pontuacao_consultor = 0
                
                for tipo, validacao in validacoes.items():
                    confiabilidade = validacao.get("confiabilidade", 0)
                    pontuacao_consultor += confiabilidade
                
                # Média das validações
                if validacoes:
                    pontuacao_consultor = pontuacao_consultor / len(validacoes)
                
                pontuacao_total += int(pontuacao_consultor * 0.4)
            else:
                pontuacao_total += 0
            
            # Pontuação do Agente Detetive (40%)
            if resultado_detetive.get("sucesso"):
                risco_fraude = resultado_detetive.get("pontuacao_risco", 0)
                # Inverter a pontuação de risco (100 - risco = confiança)
                confianca_detetive = max(0, 100 - risco_fraude)
                pontuacao_total += int(confianca_detetive * 0.4)
            else:
                pontuacao_total += 0
            
            return min(pontuacao_total, 100)
            
        except Exception as e:
            logger.error(f"Erro ao calcular pontuação: {e}")
            return 0
    
    def _determinar_status_verificacao(self, pontuacao_confianca: int) -> StatusVerificacao:
        """Determina o status da verificação baseado na pontuação"""
        if pontuacao_confianca >= 90:
            return StatusVerificacao.SEGURO
        elif pontuacao_confianca >= 60:
            return StatusVerificacao.SUSPEITO
        else:
            return StatusVerificacao.GOLPE
    
    def _gerar_mensagem_usuario(self, status: StatusVerificacao, pontuacao: int) -> str:
        """Gera mensagem personalizada para o usuário"""
        if status == StatusVerificacao.SEGURO:
            return f"✅ **PAGAMENTO SEGURO**\n\nConfiança: {pontuacao}%\n\nVocê pode pagar com tranquilidade. Este documento foi verificado e é legítimo."
        
        elif status == StatusVerificacao.SUSPEITO:
            return f"⚠️ **ATENÇÃO - VERIFICAÇÃO SUSPEITA**\n\nConfiança: {pontuacao}%\n\nRecomendamos verificar diretamente com o suporte antes de pagar. Alguns dados não conferem."
        
        else:  # GOLPE
            return f"🚨 **GOLPE DETECTADO**\n\nConfiança: {pontuacao}%\n\n**NÃO PAGUE!** Este documento é falso. Entre em contato com o suporte imediatamente."
    
    def _gerar_recomendacoes(self, status: StatusVerificacao, resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera recomendações baseadas no status"""
        recomendacoes = []
        
        if status == StatusVerificacao.SEGURO:
            recomendacoes.extend([
                {
                    "tipo": "acao",
                    "titulo": "Pagar com segurança",
                    "descricao": "Você pode proceder com o pagamento",
                    "prioridade": "baixa"
                },
                {
                    "tipo": "info",
                    "titulo": "Salvar comprovante",
                    "descricao": "Guarde o comprovante de pagamento",
                    "prioridade": "baixa"
                }
            ])
        
        elif status == StatusVerificacao.SUSPEITO:
            recomendacoes.extend([
                {
                    "tipo": "alerta",
                    "titulo": "Verificar com suporte",
                    "descricao": "Entre em contato com o suporte antes de pagar",
                    "prioridade": "alta"
                },
                {
                    "tipo": "acao",
                    "titulo": "Verificar dados",
                    "descricao": "Confirme os dados diretamente com a Bemobi",
                    "prioridade": "media"
                }
            ])
        
        else:  # GOLPE
            recomendacoes.extend([
                {
                    "tipo": "critico",
                    "titulo": "NÃO PAGAR",
                    "descricao": "Este documento é falso - não proceda com o pagamento",
                    "prioridade": "critica"
                },
                {
                    "tipo": "acao",
                    "titulo": "Reportar fraude",
                    "descricao": "Reporte este golpe para ajudar outros usuários",
                    "prioridade": "alta"
                },
                {
                    "tipo": "contato",
                    "titulo": "Contatar suporte",
                    "descricao": "Entre em contato com o suporte imediatamente",
                    "prioridade": "alta"
                }
            ])
        
        return recomendacoes
    
    def _consolidar_alertas(self, resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Consolida alertas de todos os agentes"""
        alertas = []
        
        # Alertas do Consultor
        if resultado["resultados_agentes"]["consultor"].get("alertas"):
            for alerta in resultado["resultados_agentes"]["consultor"]["alertas"]:
                alertas.append({
                    "fonte": "consultor",
                    "tipo": alerta.get("tipo", "alerta"),
                    "mensagem": alerta.get("mensagem", ""),
                    "prioridade": alerta.get("prioridade", "media")
                })
        
        # Alertas do Detetive
        if resultado["resultados_agentes"]["detetive"].get("alertas_fraude"):
            for alerta in resultado["resultados_agentes"]["detetive"]["alertas_fraude"]:
                alertas.append({
                    "fonte": "detetive",
                    "tipo": alerta.get("tipo", "alerta"),
                    "mensagem": alerta.get("mensagem", ""),
                    "prioridade": alerta.get("prioridade", "media")
                })
        
        # Ordenar por prioridade
        prioridades = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}
        alertas.sort(key=lambda x: prioridades.get(x.get("prioridade", "media"), 2))
        
        return alertas
    
    def _gerar_dados_visuais(self, status: StatusVerificacao, pontuacao: int) -> Dict[str, Any]:
        """Gera dados para interface visual"""
        cores = {
            StatusVerificacao.SEGURO: {
                "cor_principal": "#28a745",  # Verde
                "cor_secundaria": "#d4edda",
                "icone": "✅"
            },
            StatusVerificacao.SUSPEITO: {
                "cor_principal": "#ffc107",  # Amarelo
                "cor_secundaria": "#fff3cd",
                "icone": "⚠️"
            },
            StatusVerificacao.GOLPE: {
                "cor_principal": "#dc3545",  # Vermelho
                "cor_secundaria": "#f8d7da",
                "icone": "🚨"
            }
        }
        
        return {
            "status": status.value,
            "pontuacao": pontuacao,
            "cores": cores[status],
            "barra_progresso": {
                "valor": pontuacao,
                "maximo": 100,
                "cor": cores[status]["cor_principal"]
            }
        }
    
    async def _analise_final_com_ia(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Análise final consolidada usando IA da Groq"""
        try:
            prompt = f"""
            Analise os resultados consolidados da verificação de cobrança:
            
            Status: {resultado['status_verificacao']}
            Pontuação de confiança: {resultado['pontuacao_confianca']}%
            Mensagem para usuário: {resultado['mensagem_usuario']}
            
            Resultados dos agentes:
            - Leitor: {json.dumps(resultado['resultados_agentes']['leitor'], ensure_ascii=False, indent=2)}
            - Consultor: {json.dumps(resultado['resultados_agentes']['consultor'], ensure_ascii=False, indent=2)}
            - Detetive: {json.dumps(resultado['resultados_agentes']['detetive'], ensure_ascii=False, indent=2)}
            
            Forneça uma análise final consolidada incluindo:
            1. Resumo executivo da verificação
            2. Principais pontos de atenção
            3. Justificativa para a decisão tomada
            4. Próximos passos recomendados
            5. Lições aprendidas para melhorias futuras
            
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
            logger.error(f"Erro na análise final com IA: {e}")
            return {"erro": f"Erro na análise final IA: {str(e)}"}
    
    async def gerar_relatorio_detalhado(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Gera relatório detalhado da verificação"""
        try:
            relatorio = {
                "resumo_executivo": {
                    "status": resultado["status_verificacao"],
                    "pontuacao_confianca": resultado["pontuacao_confianca"],
                    "timestamp": resultado["timestamp"],
                    "user_id": resultado["user_id"]
                },
                "detalhamento_agentes": {
                    "leitor": {
                        "sucesso": resultado["resultados_agentes"]["leitor"].get("sucesso", False),
                        "dados_extraidos": resultado["resultados_agentes"]["leitor"].get("dados_extraidos", {}),
                        "qualidade_ocr": resultado["resultados_agentes"]["leitor"].get("dados_extraidos", {}).get("qualidade_imagem", "desconhecida")
                    },
                    "consultor": {
                        "sucesso": resultado["resultados_agentes"]["consultor"].get("sucesso", False),
                        "validacoes": resultado["resultados_agentes"]["consultor"].get("validacoes", {}),
                        "alertas": resultado["resultados_agentes"]["consultor"].get("alertas", [])
                    },
                    "detetive": {
                        "sucesso": resultado["resultados_agentes"]["detetive"].get("sucesso", False),
                        "pontuacao_risco": resultado["resultados_agentes"]["detetive"].get("pontuacao_risco", 0),
                        "alertas_fraude": resultado["resultados_agentes"]["detetive"].get("alertas_fraude", [])
                    }
                },
                "recomendacoes": resultado.get("recomendacoes", []),
                "alertas_consolidados": resultado.get("alertas_consolidados", []),
                "dados_visuais": resultado.get("dados_visuais", {}),
                "analise_final_ia": resultado.get("analise_final_ia", {})
            }
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return {"erro": f"Erro ao gerar relatório: {str(e)}"}
    
    def criar_botoes_interacao(self, status: StatusVerificacao) -> List[Dict[str, Any]]:
        """Cria botões de interação baseados no status"""
        botoes = []
        
        if status == StatusVerificacao.SEGURO:
            botoes.extend([
                {
                    "type": "reply",
                    "reply": {
                        "id": "pagar_agora",
                        "title": "💳 Pagar agora"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "salvar_comprovante",
                        "title": "💾 Salvar comprovante"
                    }
                }
            ])
        
        elif status == StatusVerificacao.SUSPEITO:
            botoes.extend([
                {
                    "type": "reply",
                    "reply": {
                        "id": "verificar_suporte",
                        "title": "📞 Verificar com suporte"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "verificar_dados",
                        "title": "🔍 Verificar dados"
                    }
                }
            ])
        
        else:  # GOLPE
            botoes.extend([
                {
                    "type": "reply",
                    "reply": {
                        "id": "reportar_fraude",
                        "title": "🚨 Reportar fraude"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "contatar_suporte",
                        "title": "📞 Contatar suporte"
                    }
                }
            ])
        
        # Botão sempre presente
        botoes.append({
            "type": "reply",
            "reply": {
                "id": "ver_relatorio",
                "title": "📊 Ver relatório detalhado"
            }
        })
        
        return botoes
