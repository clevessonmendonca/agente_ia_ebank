"""
Fluxo de Verificação com IA - Integração completa dos agentes
Orquestra todo o processo de verificação de cobranças usando os agentes especializados
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .agente_leitor import AgenteLeitor
from .agente_consultor import AgenteConsultor
from .agente_detetive import AgenteDetetive
from .agente_orquestrador import AgenteOrquestrador, StatusVerificacao

logger = logging.getLogger(__name__)

class FluxoVerificacaoIA:
    def __init__(self):
        self.agente_leitor = AgenteLeitor()
        self.agente_consultor = AgenteConsultor()
        self.agente_detetive = AgenteDetetive()
        self.agente_orquestrador = AgenteOrquestrador()
    
    async def verificar_cobranca_completa(self, 
                                        image_url: str = None,
                                        texto_pix: str = None,
                                        user_id: str = None) -> Dict[str, Any]:
        """
        Executa o fluxo completo de verificação de cobrança
        
        Args:
            image_url: URL da imagem do boleto/documento
            texto_pix: Texto contendo dados de PIX
            user_id: ID do usuário
            
        Returns:
            Resultado consolidado da verificação
        """
        try:
            logger.info(f"Iniciando verificação completa para usuário {user_id}")
            inicio_processo = datetime.now()
            
            # 1. Agente Leitor - Extração de dados
            logger.info("Etapa 1: Agente Leitor - Extraindo dados")
            if image_url:
                resultado_leitor = await self.agente_leitor.processar_imagem(image_url, user_id)
            elif texto_pix:
                dados_pix = self.agente_leitor.processar_texto_pix(texto_pix)
                resultado_leitor = {
                    "agente": "leitor",
                    "sucesso": True,
                    "dados_extraidos": dados_pix,
                    "texto_ocr": texto_pix,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id
                }
            else:
                return {
                    "erro": "Nenhum dado fornecido para análise",
                    "sucesso": False
                }
            
            if not resultado_leitor.get("sucesso"):
                return {
                    "erro": "Falha na extração de dados",
                    "detalhes": resultado_leitor.get("erro"),
                    "sucesso": False
                }
            
            # 2. Agente Consultor - Validação nos sistemas Bemobi
            logger.info("Etapa 2: Agente Consultor - Validando nos sistemas")
            resultado_consultor = await self.agente_consultor.validar_cobranca(
                resultado_leitor.get("dados_extraidos", {}), 
                user_id
            )
            
            if not resultado_consultor.get("sucesso"):
                logger.warning("Agente Consultor falhou, continuando com dados disponíveis")
            
            # 3. Agente Detetive - Detecção de fraudes
            logger.info("Etapa 3: Agente Detetive - Detectando fraudes")
            resultado_detetive = await self.agente_detetive.detectar_fraudes(
                resultado_leitor.get("dados_extraidos", {}), 
                user_id
            )
            
            if not resultado_detetive.get("sucesso"):
                logger.warning("Agente Detetive falhou, continuando com dados disponíveis")
            
            # 4. Agente Orquestrador - Consolidação final
            logger.info("Etapa 4: Agente Orquestrador - Consolidando análise")
            resultado_final = await self.agente_orquestrador.orquestrar_analise(
                resultado_leitor,
                resultado_consultor,
                resultado_detetive,
                user_id
            )
            
            # 5. Adicionar métricas de tempo
            tempo_total = (datetime.now() - inicio_processo).total_seconds()
            resultado_final["metricas"] = {
                "tempo_total_segundos": tempo_total,
                "tempo_total_formatado": f"{tempo_total:.1f}s",
                "inicio_processo": inicio_processo.isoformat(),
                "fim_processo": datetime.now().isoformat()
            }
            
            # 6. Gerar relatório detalhado
            relatorio_detalhado = await self.agente_orquestrador.gerar_relatorio_detalhado(resultado_final)
            resultado_final["relatorio_detalhado"] = relatorio_detalhado
            
            # 7. Criar botões de interação
            status = StatusVerificacao(resultado_final["status_verificacao"])
            botoes_interacao = self.agente_orquestrador.criar_botoes_interacao(status)
            resultado_final["botoes_interacao"] = botoes_interacao
            
            logger.info(f"Verificação concluída - Status: {resultado_final['status_verificacao']}, "
                       f"Confiança: {resultado_final['pontuacao_confianca']}%, "
                       f"Tempo: {tempo_total:.1f}s")
            
            return resultado_final
            
        except Exception as e:
            logger.error(f"Erro no fluxo de verificação: {e}")
            return {
                "erro": f"Erro no fluxo de verificação: {str(e)}",
                "sucesso": False,
                "timestamp": datetime.now().isoformat()
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
            logger.info(f"Processando resposta do usuário {user_id}: {resposta_id}")
            
            if resposta_id == "pagar_agora":
                return {
                    "mensagem": "💳 **Pagamento Seguro**\n\nVocê pode proceder com o pagamento. O documento foi verificado e é legítimo.",
                    "acoes": [
                        "Redirecionar para gateway de pagamento",
                        "Gerar comprovante automático"
                    ]
                }
            
            elif resposta_id == "salvar_comprovante":
                return {
                    "mensagem": "💾 **Comprovante Salvo**\n\nSeu comprovante foi salvo com sucesso.",
                    "acoes": [
                        "Enviar comprovante por email",
                        "Salvar no histórico do usuário"
                    ]
                }
            
            elif resposta_id == "verificar_suporte":
                return {
                    "mensagem": "📞 **Verificação com Suporte**\n\nConectando você com nosso suporte especializado...",
                    "acoes": [
                        "Abrir chat com suporte",
                        "Agendar ligação de retorno"
                    ]
                }
            
            elif resposta_id == "verificar_dados":
                return {
                    "mensagem": "🔍 **Verificação de Dados**\n\nVamos verificar os dados diretamente com nossos sistemas...",
                    "acoes": [
                        "Consultar sistemas Bemobi",
                        "Validar dados do cliente"
                    ]
                }
            
            elif resposta_id == "reportar_fraude":
                # Reportar fraude para o Agente Detetive
                dados_fraude = contexto_anterior.get("resultados_agentes", {}).get("leitor", {}).get("dados_extraidos", {})
                resultado_report = await self.agente_detetive.reportar_fraude(user_id, dados_fraude)
                
                return {
                    "mensagem": "🚨 **Fraude Reportada**\n\nObrigado por reportar esta fraude. Isso nos ajuda a proteger outros usuários.",
                    "acoes": [
                        "Fraude adicionada à base de dados",
                        "Alertas enviados para outros usuários"
                    ],
                    "resultado_report": resultado_report
                }
            
            elif resposta_id == "contatar_suporte":
                return {
                    "mensagem": "📞 **Suporte de Emergência**\n\nConectando com suporte de emergência para casos de fraude...",
                    "acoes": [
                        "Prioridade alta no atendimento",
                        "Bloqueio preventivo de conta se necessário"
                    ]
                }
            
            elif resposta_id == "ver_relatorio":
                if contexto_anterior:
                    relatorio = contexto_anterior.get("relatorio_detalhado", {})
                    return {
                        "mensagem": "📊 **Relatório Detalhado**\n\nAqui está o relatório completo da verificação:",
                        "relatorio": relatorio,
                        "acoes": [
                            "Enviar relatório por email",
                            "Salvar no histórico"
                        ]
                    }
                else:
                    return {
                        "mensagem": "❌ **Erro**\n\nNão foi possível gerar o relatório. Tente fazer uma nova verificação.",
                        "acoes": ["Iniciar nova verificação"]
                    }
            
            else:
                return {
                    "mensagem": "❓ **Resposta não reconhecida**\n\nPor favor, selecione uma das opções disponíveis.",
                    "acoes": ["Mostrar opções novamente"]
                }
                
        except Exception as e:
            logger.error(f"Erro ao processar resposta do usuário: {e}")
            return {
                "erro": f"Erro ao processar resposta: {str(e)}",
                "mensagem": "❌ **Erro**\n\nOcorreu um erro ao processar sua resposta. Tente novamente."
            }
    
    async def obter_estatisticas_sistema(self) -> Dict[str, Any]:
        """Obtém estatísticas do sistema de verificação"""
        try:
            # Em produção, isso viria de um banco de dados
            estatisticas = {
                "verificacoes_hoje": 0,
                "golpes_detectados_hoje": 0,
                "taxa_sucesso": 0.0,
                "tempo_medio_verificacao": 0.0,
                "agentes_status": {
                    "leitor": "ativo",
                    "consultor": "ativo", 
                    "detetive": "ativo",
                    "orquestrador": "ativo"
                },
                "ultima_atualizacao": datetime.now().isoformat()
            }
            
            return estatisticas
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"erro": f"Erro ao obter estatísticas: {str(e)}"}
    
    def criar_mensagem_inicial(self) -> str:
        """Cria mensagem inicial para o usuário"""
        return """
🤖 **Grace - Assistente de Verificação de Cobranças**

Olá! Sou a Grace, sua assistente especializada em verificar a autenticidade de boletos e cobranças.

**Como posso ajudar:**
📸 Envie uma foto do boleto
📋 Cole os dados do PIX
📄 Envie qualquer documento de cobrança

**O que vou fazer:**
✅ Verificar se a cobrança é legítima
🔍 Analisar dados nos sistemas Bemobi  
🛡️ Detectar possíveis fraudes
📊 Dar uma resposta clara e segura

**Envie sua cobrança para começar!**
        """
    
    def criar_mensagem_ajuda(self) -> str:
        """Cria mensagem de ajuda para o usuário"""
        return """
❓ **Como usar o Grace:**

**1. Envie uma foto do boleto**
- Tire uma foto clara do boleto
- Certifique-se que todos os dados estão visíveis

**2. Cole dados do PIX**
- Cole a chave PIX recebida
- Cole o valor e beneficiário

**3. Aguarde a análise**
- O Grace analisa em segundos
- Verifica nos sistemas Bemobi
- Detecta possíveis fraudes

**4. Receba o resultado**
- ✅ Verde: Pagamento seguro
- ⚠️ Amarelo: Verificar com suporte  
- 🚨 Vermelho: Golpe detectado

**Precisa de ajuda?** Digite "ajuda" a qualquer momento.
        """
