"""
Agente Detetive - Detecção de fraudes
Responsável por identificar padrões de golpe que vão além dos dados internos
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from groq import Groq
import logging
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

class AgenteDetetive:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"
        
        # Bases de dados de fraudes (em produção seria APIs reais)
        self.bases_fraudes = {
            "golpes_reportados": {},
            "beneficiarios_suspeitos": {},
            "padroes_anomalos": {},
            "reclamacoes_mercado": {}
        }
        
        # Inicializar dados de exemplo
        self._inicializar_bases_fraudes()
    
    def _inicializar_bases_fraudes(self):
        """Inicializa bases de dados de fraudes com exemplos"""
        # Golpes reportados por usuários
        self.bases_fraudes["golpes_reportados"] = {
            "12345678901": [
                {
                    "tipo": "boleto_falso",
                    "valor": 150.00,
                    "beneficiario": "Empresa Falsa LTDA",
                    "data_reportado": "2024-11-20",
                    "status": "confirmado"
                }
            ],
            "98765432100": [
                {
                    "tipo": "pix_suspeito",
                    "chave": "golpista@email.com",
                    "valor": 200.00,
                    "data_reportado": "2024-11-15",
                    "status": "confirmado"
                }
            ]
        }
        
        # Beneficiários suspeitos
        self.bases_fraudes["beneficiarios_suspeitos"] = {
            "Empresa Falsa LTDA": {
                "cnpj": "00.000.000/0001-00",
                "motivo": "CNPJ inválido",
                "relatos": 5,
                "status": "bloqueado"
            },
            "Golpista Silva": {
                "cpf": "000.000.000-00",
                "motivo": "Nome falso",
                "relatos": 3,
                "status": "bloqueado"
            }
        }
        
        # Padrões anômalos conhecidos
        self.bases_fraudes["padroes_anomalos"] = {
            "valores_suspeitos": [300.00, 500.00, 1000.00],  # Valores típicos de golpes
            "horarios_suspeitos": ["03:00", "04:00", "05:00"],  # Horários de madrugada
            "palavras_suspeitas": [
                "urgente", "imediato", "bloqueio", "suspensão",
                "multa", "juros", "desconto", "promoção",
                "limite", "bloqueio", "suspensão"
            ]
        }
        
        # Reclamações do mercado
        self.bases_fraudes["reclamacoes_mercado"] = {
            "procon": [
                {
                    "empresa": "Empresa Falsa LTDA",
                    "reclamacoes": 15,
                    "motivo": "Cobrança indevida"
                }
            ],
            "bacen": [
                {
                    "cnpj": "00.000.000/0001-00",
                    "status": "irregular",
                    "motivo": "CNPJ cancelado"
                }
            ]
        }
    
    async def detectar_fraudes(self, dados_extraidos: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Detecta padrões de fraude nos dados"""
        try:
            logger.info(f"Agente Detetive: Analisando fraudes para usuário {user_id}")
            
            resultado = {
                "agente": "detetive",
                "sucesso": True,
                "analises": {},
                "alertas_fraude": [],
                "pontuacao_risco": 0,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
            # 1. Verificar golpes reportados pelo usuário
            analise_golpes_usuario = await self._verificar_golpes_usuario(user_id, dados_extraidos)
            resultado["analises"]["golpes_usuario"] = analise_golpes_usuario
            
            # 2. Verificar beneficiários suspeitos
            analise_beneficiario = await self._verificar_beneficiario_suspeito(dados_extraidos)
            resultado["analises"]["beneficiario"] = analise_beneficiario
            
            # 3. Detectar padrões anômalos
            analise_padroes = await self._detectar_padroes_anomalos(dados_extraidos)
            resultado["analises"]["padroes"] = analise_padroes
            
            # 4. Verificar reclamações do mercado
            analise_reclamacoes = await self._verificar_reclamacoes_mercado(dados_extraidos)
            resultado["analises"]["reclamacoes"] = analise_reclamacoes
            
            # 5. Análise de horário suspeito
            analise_horario = await self._analisar_horario_suspeito()
            resultado["analises"]["horario"] = analise_horario
            
            # Calcular pontuação de risco
            resultado["pontuacao_risco"] = self._calcular_pontuacao_risco(resultado["analises"])
            
            # Gerar alertas de fraude
            resultado["alertas_fraude"] = self._gerar_alertas_fraude(resultado["analises"])
            
            # Análise final com IA
            analise_final = await self._analisar_fraude_com_ia(resultado)
            resultado["analise_ia"] = analise_final
            
            logger.info(f"Agente Detetive: Análise concluída - Risco: {resultado['pontuacao_risco']}%")
            return resultado
            
        except Exception as e:
            logger.error(f"Agente Detetive: Erro na detecção - {e}")
            return {
                "agente": "detetive",
                "erro": f"Erro na detecção: {str(e)}",
                "sucesso": False
            }
    
    async def _verificar_golpes_usuario(self, user_id: str, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se o usuário já reportou golpes similares"""
        try:
            golpes_usuario = self.bases_fraudes["golpes_reportados"].get(user_id, [])
            
            if not golpes_usuario:
                return {
                    "status": "sem_historico_golpes",
                    "mensagem": "Usuário sem histórico de golpes reportados",
                    "risco": 0
                }
            
            # Verificar padrões similares
            valor_atual = self._extrair_valor_numerico(dados.get("valor_cobrado", ""))
            beneficiario_atual = dados.get("nome_beneficiario", "")
            
            golpes_similares = []
            for golpe in golpes_usuario:
                similaridade = 0
                
                # Verificar valor similar
                if valor_atual and golpe.get("valor"):
                    if abs(valor_atual - golpe["valor"]) < 10:  # Diferença menor que R$ 10
                        similaridade += 40
                
                # Verificar beneficiário similar
                if beneficiario_atual and golpe.get("beneficiario"):
                    if beneficiario_atual.lower() in golpe["beneficiario"].lower():
                        similaridade += 60
                
                if similaridade > 50:
                    golpes_similares.append({
                        "golpe": golpe,
                        "similaridade": similaridade
                    })
            
            if golpes_similares:
                return {
                    "status": "golpes_similares_encontrados",
                    "mensagem": f"Encontrados {len(golpes_similares)} golpe(s) similar(es)",
                    "risco": 90,
                    "golpes_similares": golpes_similares
                }
            
            return {
                "status": "historico_diferente",
                "mensagem": "Histórico de golpes não similar ao atual",
                "risco": 20
            }
            
        except Exception as e:
            return {
                "status": "erro_verificacao",
                "mensagem": f"Erro ao verificar golpes: {str(e)}",
                "risco": 0
            }
    
    async def _verificar_beneficiario_suspeito(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se o beneficiário está na lista de suspeitos"""
        try:
            beneficiario = dados.get("nome_beneficiario", "")
            
            if not beneficiario:
                return {
                    "status": "beneficiario_nao_identificado",
                    "mensagem": "Beneficiário não identificado",
                    "risco": 30
                }
            
            # Verificar se está na lista de suspeitos
            for nome_suspeito, info in self.bases_fraudes["beneficiarios_suspeitos"].items():
                if nome_suspeito.lower() in beneficiario.lower():
                    return {
                        "status": "beneficiario_suspeito",
                        "mensagem": f"Beneficiário '{nome_suspeito}' está na lista de suspeitos",
                        "risco": 95,
                        "dados_suspeito": info
                    }
            
            return {
                "status": "beneficiario_nao_suspeito",
                "mensagem": "Beneficiário não encontrado na lista de suspeitos",
                "risco": 10
            }
            
        except Exception as e:
            return {
                "status": "erro_verificacao",
                "mensagem": f"Erro ao verificar beneficiário: {str(e)}",
                "risco": 0
            }
    
    async def _detectar_padroes_anomalos(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta padrões anômalos nos dados"""
        try:
            anomalias = []
            risco_total = 0
            
            # Verificar valor suspeito
            valor = self._extrair_valor_numerico(dados.get("valor_cobrado", ""))
            if valor:
                if valor in self.bases_fraudes["padroes_anomalos"]["valores_suspeitos"]:
                    anomalias.append({
                        "tipo": "valor_suspeito",
                        "descricao": f"Valor R$ {valor:.2f} é típico de golpes",
                        "risco": 70
                    })
                    risco_total += 70
                elif valor > 500:  # Valores muito altos
                    anomalias.append({
                        "tipo": "valor_muito_alto",
                        "descricao": f"Valor R$ {valor:.2f} muito alto para serviços Bemobi",
                        "risco": 50
                    })
                    risco_total += 50
            
            # Verificar palavras suspeitas no texto
            texto_completo = dados.get("texto_ocr", "")
            palavras_suspeitas = self.bases_fraudes["padroes_anomalos"]["palavras_suspeitas"]
            
            palavras_encontradas = []
            for palavra in palavras_suspeitas:
                if palavra.lower() in texto_completo.lower():
                    palavras_encontradas.append(palavra)
            
            if palavras_encontradas:
                anomalias.append({
                    "tipo": "palavras_suspeitas",
                    "descricao": f"Palavras suspeitas encontradas: {', '.join(palavras_encontradas)}",
                    "risco": 60
                })
                risco_total += 60
            
            # Verificar qualidade da imagem
            if dados.get("qualidade_imagem") == "ruim":
                anomalias.append({
                    "tipo": "qualidade_imagem",
                    "descricao": "Imagem de baixa qualidade pode indicar falsificação",
                    "risco": 40
                })
                risco_total += 40
            
            return {
                "status": "analise_concluida",
                "anomalias": anomalias,
                "risco_total": min(risco_total, 100),
                "mensagem": f"Encontradas {len(anomalias)} anomalia(s)"
            }
            
        except Exception as e:
            return {
                "status": "erro_analise",
                "mensagem": f"Erro na análise: {str(e)}",
                "risco_total": 0
            }
    
    async def _verificar_reclamacoes_mercado(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica reclamações no mercado"""
        try:
            beneficiario = dados.get("nome_beneficiario", "")
            
            if not beneficiario:
                return {
                    "status": "beneficiario_nao_identificado",
                    "mensagem": "Beneficiário não identificado",
                    "risco": 30
                }
            
            # Verificar reclamações no Procon
            reclamacoes_procon = self.bases_fraudes["reclamacoes_mercado"]["procon"]
            for reclamacao in reclamacoes_procon:
                if reclamacao["empresa"].lower() in beneficiario.lower():
                    return {
                        "status": "reclamacoes_encontradas",
                        "mensagem": f"Empresa com {reclamacao['reclamacoes']} reclamações no Procon",
                        "risco": 80,
                        "dados_reclamacao": reclamacao
                    }
            
            return {
                "status": "sem_reclamacoes",
                "mensagem": "Nenhuma reclamação encontrada",
                "risco": 10
            }
            
        except Exception as e:
            return {
                "status": "erro_verificacao",
                "mensagem": f"Erro ao verificar reclamações: {str(e)}",
                "risco": 0
            }
    
    async def _analisar_horario_suspeito(self) -> Dict[str, Any]:
        """Analisa se o horário é suspeito"""
        try:
            hora_atual = datetime.now().hour
            horarios_suspeitos = [3, 4, 5]  # 3h, 4h, 5h da manhã
            
            if hora_atual in horarios_suspeitos:
                return {
                    "status": "horario_suspeito",
                    "mensagem": f"Horário suspeito: {hora_atual:02d}:00",
                    "risco": 60
                }
            
            return {
                "status": "horario_normal",
                "mensagem": f"Horário normal: {hora_atual:02d}:00",
                "risco": 5
            }
            
        except Exception as e:
            return {
                "status": "erro_analise",
                "mensagem": f"Erro na análise de horário: {str(e)}",
                "risco": 0
            }
    
    def _calcular_pontuacao_risco(self, analises: Dict[str, Any]) -> int:
        """Calcula pontuação total de risco"""
        try:
            pontuacao = 0
            
            # Golpes do usuário
            if analises.get("golpes_usuario", {}).get("risco"):
                pontuacao += analises["golpes_usuario"]["risco"] * 0.3
            
            # Beneficiário suspeito
            if analises.get("beneficiario", {}).get("risco"):
                pontuacao += analises["beneficiario"]["risco"] * 0.25
            
            # Padrões anômalos
            if analises.get("padroes", {}).get("risco_total"):
                pontuacao += analises["padroes"]["risco_total"] * 0.2
            
            # Reclamações
            if analises.get("reclamacoes", {}).get("risco"):
                pontuacao += analises["reclamacoes"]["risco"] * 0.15
            
            # Horário
            if analises.get("horario", {}).get("risco"):
                pontuacao += analises["horario"]["risco"] * 0.1
            
            return min(int(pontuacao), 100)
            
        except Exception as e:
            logger.error(f"Erro ao calcular pontuação: {e}")
            return 0
    
    def _gerar_alertas_fraude(self, analises: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera alertas de fraude baseados nas análises"""
        alertas = []
        
        for tipo, analise in analises.items():
            risco = analise.get("risco", 0)
            
            if risco >= 80:
                alertas.append({
                    "tipo": "fraude_alta",
                    "categoria": tipo,
                    "mensagem": f"🚨 ALERTA ALTO: {analise.get('mensagem', '')}",
                    "prioridade": "critica",
                    "risco": risco
                })
            elif risco >= 50:
                alertas.append({
                    "tipo": "fraude_media",
                    "categoria": tipo,
                    "mensagem": f"⚠️ ALERTA MÉDIO: {analise.get('mensagem', '')}",
                    "prioridade": "alta",
                    "risco": risco
                })
            elif risco >= 20:
                alertas.append({
                    "tipo": "fraude_baixa",
                    "categoria": tipo,
                    "mensagem": f"ℹ️ ATENÇÃO: {analise.get('mensagem', '')}",
                    "prioridade": "media",
                    "risco": risco
                })
        
        return alertas
    
    def _extrair_valor_numerico(self, valor_str: str) -> Optional[float]:
        """Extrai valor numérico de string"""
        try:
            if not valor_str:
                return None
                
            # Remover R$ e espaços
            valor_limpo = valor_str.replace("R$", "").replace(" ", "").strip()
            
            # Substituir vírgula por ponto para conversão
            valor_limpo = valor_limpo.replace(",", ".")
            
            return float(valor_limpo)
        except (ValueError, AttributeError):
            return None
    
    async def _analisar_fraude_com_ia(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Análise final usando IA da Groq"""
        try:
            prompt = f"""
            Analise os resultados da detecção de fraudes:
            
            Análises realizadas: {json.dumps(resultado['analises'], ensure_ascii=False, indent=2)}
            Pontuação de risco: {resultado['pontuacao_risco']}%
            Alertas gerados: {json.dumps(resultado['alertas_fraude'], ensure_ascii=False, indent=2)}
            
            Forneça uma análise consolidada incluindo:
            1. Nível de risco geral (baixo/médio/alto/crítico)
            2. Principais indicadores de fraude
            3. Recomendações específicas
            4. Ações preventivas sugeridas
            
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
    
    async def reportar_fraude(self, user_id: str, dados_fraude: Dict[str, Any]) -> Dict[str, Any]:
        """Reporta nova fraude para alimentar a base de dados"""
        try:
            # Adicionar à base de golpes reportados
            if user_id not in self.bases_fraudes["golpes_reportados"]:
                self.bases_fraudes["golpes_reportados"][user_id] = []
            
            fraude_reportada = {
                "tipo": dados_fraude.get("tipo", "desconhecido"),
                "valor": dados_fraude.get("valor"),
                "beneficiario": dados_fraude.get("beneficiario"),
                "data_reportado": datetime.now().isoformat(),
                "status": "reportado"
            }
            
            self.bases_fraudes["golpes_reportados"][user_id].append(fraude_reportada)
            
            logger.info(f"Fraude reportada por usuário {user_id}: {fraude_reportada}")
            
            return {
                "sucesso": True,
                "mensagem": "Fraude reportada com sucesso",
                "fraude_id": len(self.bases_fraudes["golpes_reportados"][user_id])
            }
            
        except Exception as e:
            logger.error(f"Erro ao reportar fraude: {e}")
            return {
                "sucesso": False,
                "erro": f"Erro ao reportar fraude: {str(e)}"
            }
