
"""
Endpoints FastAPI para Control del Auto Dialer - VoIP Auto Dialer
Agrega estos endpoints a tu FastAPI existente
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional, List
import sys
import os

# Agregar el directorio padre al path para importar módulos del core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dialer_integration import dialer_integration
from core.logging_config import get_logger

# Router para los endpoints del dialer
dialer_router = APIRouter(prefix="/api/dialer", tags=["Auto Dialer"])
logger = get_logger("dialer_endpoints")

# Modelos Pydantic para las requests
class CampaignStartRequest(BaseModel):
    calls_per_minute: Optional[int] = 10
    max_concurrent_calls: Optional[int] = 5
    mode: Optional[str] = "power"  # preview, power, predictive

class TestCallRequest(BaseModel):
    phone_number: str
    campaign_id: Optional[str] = "test"

# ==================== ENDPOINTS PRINCIPALES ====================

@dialer_router.post("/campaigns/{campaign_id}/start")
async def start_campaign_dialing(
    campaign_id: str, 
    request: CampaignStartRequest,
    background_tasks: BackgroundTasks
):
    """
    Iniciar el marcado automático para una campaña específica
    """
    try:
        logger.info(f"Endpoint: Iniciando marcado para campaña {campaign_id}")
        
        config = {
            "calls_per_minute": request.calls_per_minute,
            "max_concurrent_calls": request.max_concurrent_calls,
            "mode": request.mode
        }
        
        result = await dialer_integration.start_campaign_dialing(campaign_id, config)
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": {
                    "campaign_id": campaign_id,
                    "started_at": result["started_at"],
                    "config": config
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error en endpoint start_campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@dialer_router.post("/campaigns/{campaign_id}/stop")
async def stop_campaign_dialing(campaign_id: str):
    """
    Detener el marcado automático para una campaña específica
    """
    try:
        logger.info(f"Endpoint: Deteniendo marcado para campaña {campaign_id}")
        
        result = await dialer_integration.stop_campaign_dialing(campaign_id)
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": {
                    "campaign_id": campaign_id,
                    "stopped_at": result["stopped_at"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error en endpoint stop_campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@dialer_router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign_dialing(campaign_id: str):
    """
    Pausar el marcado automático para una campaña específica
    """
    try:
        logger.info(f"Endpoint: Pausando marcado para campaña {campaign_id}")
        
        result = await dialer_integration.pause_campaign_dialing(campaign_id)
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": {
                    "campaign_id": campaign_id,
                    "paused_at": result.get("stopped_at")
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error en endpoint pause_campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@dialer_router.post("/campaigns/{campaign_id}/resume")
async def resume_campaign_dialing(campaign_id: str):
    """
    Reanudar el marcado automático para una campaña pausada
    """
    try:
        logger.info(f"Endpoint: Reanudando marcado para campaña {campaign_id}")
        
        result = await dialer_integration.resume_campaign_dialing(campaign_id)
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": {
                    "campaign_id": campaign_id,
                    "resumed_at": result.get("started_at")
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error en endpoint resume_campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ==================== ENDPOINTS DE ESTADO ====================

@dialer_router.get("/status")
async def get_dialer_status():
    """
    Obtener el estado general del sistema de marcado automático
    """
    try:
        status = dialer_integration.get_dialer_status()
        
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Error en endpoint get_dialer_status: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@dialer_router.get("/campaigns/{campaign_id}/status")
async def get_campaign_status(campaign_id: str):
    """
    Obtener el estado específico de una campaña
    """
    try:
        result = dialer_integration.get_campaign_status(campaign_id)
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["campaign_info"]
            }
        else:
            raise HTTPException(status_code=404, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint get_campaign_status: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@dialer_router.get("/campaigns")
async def get_available_campaigns():
    """
    Obtener todas las campañas disponibles para marcado
    """
    try:
        result = dialer_integration.get_available_campaigns()
        
        if result["success"]:
            return {
                "status": "success",
                "data": {
                    "campaigns": result["campaigns"],
                    "total": result["total_campaigns"]
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint get_available_campaigns: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ==================== ENDPOINTS DE PRUEBA ====================

@dialer_router.post("/test-call")
async def make_test_call(request: TestCallRequest):
    """
    Realizar una llamada de prueba a un número específico
    """
    try:
        logger.info(f"Endpoint: Llamada de prueba a {request.phone_number}")
        
        result = await dialer_integration.make_test_call(
            request.phone_number, 
            request.campaign_id
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": {
                    "phone_number": request.phone_number,
                    "test_call_id": result["test_call_id"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint test_call: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ==================== ENDPOINTS DE CONFIGURACIÓN ====================

@dialer_router.get("/config")
async def get_dialer_config():
    """
    Obtener la configuración actual del dialer
    """
    try:
        engine_stats = dialer_integration.engine.get_engine_stats()
        
        return {
            "status": "success",
            "data": {
                "calls_per_minute": dialer_integration.engine.calls_per_minute,
                "max_concurrent_calls": dialer_integration.engine.max_concurrent_calls,
                "mode": dialer_integration.engine.mode.value,
                "current_stats": engine_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error en endpoint get_dialer_config: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ==================== FUNCIÓN PARA INTEGRAR CON TU FASTAPI ====================

def add_dialer_routes_to_app(app):
    """
    Función para agregar las rutas del dialer a tu aplicación FastAPI existente
    
    Uso en tu web/main.py:
    from web.dialer_endpoints import add_dialer_routes_to_app
    add_dialer_routes_to_app(app)
    """
    app.include_router(dialer_router)
    logger.info("Rutas del Auto Dialer agregadas a FastAPI")

# ==================== EJEMPLO DE USO ====================
"""
Para integrar con tu FastAPI existente, agrega esto a tu web/main.py:

from web.dialer_endpoints import add_dialer_routes_to_app

# Después de crear tu app FastAPI
app = FastAPI()

# Agregar las rutas del dialer
add_dialer_routes_to_app(app)

# Ahora tendrás disponibles estos endpoints:
# POST /api/dialer/campaigns/{id}/start
# POST /api/dialer/campaigns/{id}/stop  
# POST /api/dialer/campaigns/{id}/pause
# POST /api/dialer/campaigns/{id}/resume
# GET  /api/dialer/status
# GET  /api/dialer/campaigns/{id}/status
# GET  /api/dialer/campaigns
# POST /api/dialer/test-call
# GET  /api/dialer/config
"""
