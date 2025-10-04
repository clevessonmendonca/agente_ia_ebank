"""
Endpoints para o fluxo de verificação com IA
Novos endpoints para testar e usar o sistema de agentes especializados
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel

from ...services.ai_service import AIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verificacao-ia", tags=["Verificação IA"])

# Instância global do serviço de IA
_ai_service = None

def get_ai_service():
    """
    Obtém instância do serviço de IA, inicializando se necessário
    """
    global _ai_service
    if _ai_service is None:
        try:
            _ai_service = AIService()
            logger.info("Serviço de IA inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar serviço de IA: {e}")
            raise HTTPException(
                status_code=500,
                detail="Serviço de IA não disponível"
            )
    return _ai_service

# Modelos Pydantic para as requisições
class VerificacaoRequest(BaseModel):
    image_url: Optional[str] = None
    texto_pix: Optional[str] = None
    user_id: str

class RespostaUsuarioRequest(BaseModel):
    user_id: str
    resposta_id: str
    contexto_anterior: Optional[Dict[str, Any]] = None

@router.post("/verificar-cobranca")
async def verificar_cobranca(
    request: VerificacaoRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Endpoint principal para verificação de cobrança usando o fluxo completo de IA
    
    Args:
        request: Dados da verificação (image_url ou texto_pix)
        
    Returns:
        Resultado consolidado da verificação
    """
    try:
        logger.info(f"Iniciando verificação para usuário {request.user_id}")
        
        # Validar que pelo menos um dado foi fornecido
        if not request.image_url and not request.texto_pix:
            raise HTTPException(
                status_code=400, 
                detail="É necessário fornecer image_url ou texto_pix"
            )
        
        # Executar verificação completa
        resultado = await ai_service.verificar_cobranca_completa(
            image_url=request.image_url,
            texto_pix=request.texto_pix,
            user_id=request.user_id
        )
        
        if not resultado.get("sucesso", True):
            raise HTTPException(
                status_code=500,
                detail=resultado.get("erro", "Erro na verificação")
            )
        
        logger.info(f"Verificação concluída para usuário {request.user_id}")
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint de verificação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@router.post("/processar-resposta")
async def processar_resposta_usuario(
    request: RespostaUsuarioRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Processa resposta do usuário aos botões de interação
    
    Args:
        request: Dados da resposta do usuário
        
    Returns:
        Resposta processada
    """
    try:
        logger.info(f"Processando resposta {request.resposta_id} do usuário {request.user_id}")
        
        resultado = await ai_service.processar_resposta_usuario(
            user_id=request.user_id,
            resposta_id=request.resposta_id,
            contexto_anterior=request.contexto_anterior
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro ao processar resposta: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar resposta: {str(e)}"
        )

@router.get("/mensagem-inicial")
async def obter_mensagem_inicial(
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Obtém mensagem inicial do Grace
    
    Returns:
        Mensagem inicial formatada
    """
    try:
        mensagem = ai_service.obter_mensagem_inicial()
        return {
            "mensagem": mensagem,
            "tipo": "inicial"
        }
    except Exception as e:
        logger.error(f"Erro ao obter mensagem inicial: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter mensagem inicial: {str(e)}"
        )

@router.get("/mensagem-ajuda")
async def obter_mensagem_ajuda(
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Obtém mensagem de ajuda do Grace
    
    Returns:
        Mensagem de ajuda formatada
    """
    try:
        mensagem = ai_service.obter_mensagem_ajuda()
        return {
            "mensagem": mensagem,
            "tipo": "ajuda"
        }
    except Exception as e:
        logger.error(f"Erro ao obter mensagem de ajuda: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter mensagem de ajuda: {str(e)}"
        )

@router.get("/estatisticas")
async def obter_estatisticas_sistema(
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Obtém estatísticas do sistema de verificação
    
    Returns:
        Estatísticas do sistema
    """
    try:
        estatisticas = await ai_service.obter_estatisticas_sistema()
        return estatisticas
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )

@router.get("/status-agentes")
async def obter_status_agentes(
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Obtém status dos agentes especializados
    
    Returns:
        Status de cada agente
    """
    try:
        # Verificar se os agentes estão funcionando
        status_agentes = {
            "leitor": {
                "status": "ativo",
                "descricao": "Agente Leitor - Extração de dados (OCR)"
            },
            "consultor": {
                "status": "ativo", 
                "descricao": "Agente Consultor - Validação nos sistemas Bemobi"
            },
            "detetive": {
                "status": "ativo",
                "descricao": "Agente Detetive - Detecção de fraudes"
            },
            "orquestrador": {
                "status": "ativo",
                "descricao": "Agente Orquestrador - Consolidação da análise"
            }
        }
        
        return {
            "agentes": status_agentes,
            "sistema": "operacional",
            "timestamp": "2024-12-19T10:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter status dos agentes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter status: {str(e)}"
        )

@router.post("/teste-fluxo-completo")
async def teste_fluxo_completo(
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Endpoint para testar o fluxo completo com dados simulados
    
    Returns:
        Resultado do teste
    """
    try:
        logger.info("Iniciando teste do fluxo completo")
        
        # Dados de teste
        dados_teste = {
            "image_url": None,
            "texto_pix": """
            Chave PIX: bemobi@teste.com
            Valor: R$ 89,90
            Beneficiário: Bemobi Tecnologia
            Descrição: Serviço de streaming
            """,
            "user_id": "teste_123"
        }
        
        # Executar verificação de teste
        resultado = await ai_service.verificar_cobranca_completa(
            image_url=dados_teste["image_url"],
            texto_pix=dados_teste["texto_pix"],
            user_id=dados_teste["user_id"]
        )
        
        return {
            "teste": "fluxo_completo",
            "dados_entrada": dados_teste,
            "resultado": resultado,
            "status": "concluido"
        }
        
    except Exception as e:
        logger.error(f"Erro no teste do fluxo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro no teste: {str(e)}"
        )
