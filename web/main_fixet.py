
"""
Servidor web principal para VoIP Auto Dialer - VERSIÓN CORREGIDA
FastAPI con endpoints completos para agentes, extensiones, proveedores y auto dialer
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import json

# Imports con manejo de errores
try:
    from core.logging_config import get_logger
    from core.extension_manager import extension_manager
    from core.agent_manager_clean import agent_manager
    from core.asterisk_monitor import asterisk_monitor
    from core.provider_manager import provider_manager
    from core.softphone_auto_register import softphone_auto_register
    core_modules_available = True
except ImportError as e:
    print(f"⚠️ Algunos módulos del core no están disponibles: {e}")
    core_modules_available = False

# Configuración de la aplicación
app = FastAPI(
    title="VoIP Auto Dialer",
    description="Sistema de llamadas automatizadas con gestión completa",
    version="2.0.0"
)

# Logger con fallback
if core_modules_available:
    logger = get_logger("web_server")
else:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("web_server")

# Configurar archivos estáticos y templates
static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"

# Crear directorios si no existen
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Modelos Pydantic
class AgentCreate(BaseModel):
    name: str
    email: str
    phone: str

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class ProviderCreate(BaseModel):
    name: str
    type: str
    host: str
    port: Optional[int] = 5060
    username: Optional[str] = ""
    password: Optional[str] = ""
    transport: Optional[str] = "UDP"
    context: Optional[str] = "from-trunk"
    codec: Optional[str] = "ulaw,alaw,gsm"
    description: Optional[str] = ""

# ============================================================================
# RUTAS WEB (HTML)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal con datos en tiempo real"""
    try:
        # Datos por defecto en caso de error
        default_data = {
            "request": request,
            "realtime_data": {"system_status": "Unknown", "total_extensions": 0, "active_calls": 0, "uptime": "Unknown"},
            "agent_stats": {"total": 0, "online": 0, "offline": 0, "with_extensions": 0},
            "extension_stats": {"total": 0, "assigned": 0, "available": 0, "utilization": 0},
            "providers": {},
            "provider_count": 0,
            "auto_register_status": {"monitoring": False, "registered_endpoints": 0, "endpoints": {}},
            "campaigns": {},
            "active_campaigns": [],
            "system_info": {"version": "2.0.0", "environment": "production"}
        }
        
        if not core_modules_available:
            logger.warning("Módulos del core no disponibles, usando datos por defecto")
            return templates.TemplateResponse("dashboard_production.html", default_data)
        
        # Obtener datos reales con manejo de errores
        try:
            realtime_data = asterisk_monitor.get_realtime_data()
        except Exception as e:
            logger.warning(f"Error obteniendo datos de Asterisk: {e}")
            realtime_data = default_data["realtime_data"]
        
        try:
            agents = agent_manager.get_all_agents()
            agent_stats = {
                "total": len(agents),
                "online": len([a for a in agents.values() if a.get("status") == "online"]),
                "offline": len([a for a in agents.values() if a.get("status") == "offline"]),
                "with_extensions": len([a for a in agents.values() if a.get("extension_info")])
            }
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas de agentes: {e}")
            agent_stats = default_data["agent_stats"]
        
        try:
            extension_stats = extension_manager.get_extension_stats()
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas de extensiones: {e}")
            extension_stats = default_data["extension_stats"]
        
        try:
            providers = provider_manager.get_all_providers()
        except Exception as e:
            logger.warning(f"Error obteniendo proveedores: {e}")
            providers = {}
        
        try:
            auto_register_status = softphone_auto_register.get_monitoring_status()
        except Exception as e:
            logger.warning(f"Error obteniendo estado de auto-registro: {e}")
            auto_register_status = default_data["auto_register_status"]
        
        template_data = {
            "request": request,
            "realtime_data": realtime_data,
            "agent_stats": agent_stats,
            "extension_stats": extension_stats,
            "providers": providers,
            "provider_count": len(providers),
            "auto_register_status": auto_register_status,
            "campaigns": {},
            "active_campaigns": [],
            "system_info": {"version": "2.0.0", "environment": "production"}
        }
        
        return templates.TemplateResponse("dashboard_production.html", template_data)
        
    except Exception as e:
        logger.error(f"Error crítico en dashboard: {e}")
        # Página de error simple
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>VoIP Auto Dialer - Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-danger">
                    <h4>Error en el Dashboard</h4>
                    <p>Error: {str(e)}</p>
                    <hr>
                    <p class="mb-0">
                        <a href="/api/health" class="btn btn-primary">Health Check</a>
                        <a href="/agents" class="btn btn-secondary">Agentes</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """Página de gestión de agentes"""
    try:
        return templates.TemplateResponse("agents_clean.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"<h1>Error cargando página de agentes: {e}</h1>", status_code=500)

@app.get("/providers", response_class=HTMLResponse)
async def providers_page(request: Request):
    """Página de gestión de proveedores VoIP"""
    try:
        if core_modules_available:
            providers = provider_manager.get_all_providers()
        else:
            providers = {}
        
        return templates.TemplateResponse("providers_enhanced.html", {
            "request": request,
            "providers": providers,
            "provider_count": len(providers)
        })
    except Exception as e:
        return HTMLResponse(f"<h1>Error cargando página de proveedores: {e}</h1>", status_code=500)

@app.get("/extensions", response_class=HTMLResponse)
async def extensions_page(request: Request):
    """Página de gestión de extensiones"""
    try:
        return templates.TemplateResponse("extensions_management.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"<h1>Error cargando página de extensiones: {e}</h1>", status_code=500)

# ============================================================================
# API ENDPOINTS - SALUD Y SISTEMA
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "core_modules_available": core_modules_available,
        "components": {
            "extension_manager": "ok" if core_modules_available else "unavailable",
            "agent_manager": "ok" if core_modules_available else "unavailable",
            "provider_manager": "ok" if core_modules_available else "unavailable",
            "asterisk_monitor": "ok" if core_modules_available else "unavailable"
        }
    }

# ============================================================================
# API ENDPOINTS - AGENTES
# ============================================================================

@app.get("/api/agents")
async def get_agents():
    """Obtener todos los agentes"""
    if not core_modules_available:
        return {"error": "Módulos del core no disponibles"}
    
    try:
        agents = agent_manager.get_all_agents()
        
        if not isinstance(agents, dict):
            logger.warning(f"get_all_agents devolvió tipo inesperado: {type(agents)}")
            return {}
        
        valid_agents = {}
        for agent_id, agent_data in agents.items():
            if isinstance(agent_data, dict) and 'name' in agent_data:
                valid_agents[agent_id] = agent_data
            else:
                logger.warning(f"Agente {agent_id} tiene datos inválidos")
        
        return valid_agents
        
    except Exception as e:
        logger.error(f"Error obteniendo agentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents")
async def create_agent(agent: AgentCreate):
    """Crear un nuevo agente"""
    if not core_modules_available:
        raise HTTPException(status_code=503, detail="Módulos del core no disponibles")
    
    try:
        new_agent = agent_manager.create_agent(
            name=agent.name,
            email=agent.email,
            phone=agent.phone
        )
        
        if not new_agent or not isinstance(new_agent, dict) or 'id' not in new_agent:
            logger.error(f"create_agent devolvió resultado inválido: {new_agent}")
            raise HTTPException(status_code=500, detail="Error creando agente: resultado inválido")
        
        logger.info(f"Agente creado exitosamente: {new_agent['id']}")
        return new_agent
        
    except Exception as e:
        logger.error(f"Error creando agente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API ENDPOINTS - EXTENSIONES
# ============================================================================

@app.get("/api/extensions/stats")
async def get_extension_stats():
    """Obtener estadísticas de extensiones"""
    if not core_modules_available:
        return {"total": 0, "assigned": 0, "available": 0, "utilization": 0}
    
    try:
        stats = extension_manager.get_extension_stats()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de extensiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/extensions")
async def get_all_extensions():
    """Obtener todas las extensiones"""
    if not core_modules_available:
        return {}
    
    try:
        extensions = extension_manager.get_all_extensions()
        return extensions
    except Exception as e:
        logger.error(f"Error obteniendo extensiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API ENDPOINTS - PROVEEDORES
# ============================================================================

@app.get("/api/providers")
async def get_providers():
    """Obtener todos los proveedores"""
    if not core_modules_available:
        return {}
    
    try:
        providers = provider_manager.get_all_providers()
        return providers
    except Exception as e:
        logger.error(f"Error obteniendo proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AUTO DIALER INTEGRATION
# ============================================================================

# Importar componentes del auto dialer con manejo de errores
auto_dialer_available = False
try:
    if core_modules_available:
        from core.dialer_integration import dialer_integration
        auto_dialer_available = True
        logger.info("✅ Auto dialer cargado exitosamente")
except ImportError as e:
    logger.warning(f"⚠️ Auto dialer no disponible: {e}")

# Endpoints del Auto Dialer
@app.get("/api/dialer/status")
async def get_dialer_status():
    """Estado del sistema de marcado automático"""
    if not auto_dialer_available:
        return {"success": False, "message": "Auto dialer no disponible"}
    
    try:
        status = dialer_integration.get_dialer_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error obteniendo estado del dialer: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/dialer/campaigns/{campaign_id}/start")
async def start_campaign_dialing(campaign_id: str, config: dict = None):
    """Iniciar marcado automático para una campaña"""
    if not auto_dialer_available:
        return {"success": False, "message": "Auto dialer no disponible"}
    
    try:
        if not config:
            config = {
                "calls_per_minute": 10,
                "max_concurrent_calls": 3,
                "mode": "power"
            }
        result = await dialer_integration.start_campaign_dialing(campaign_id, config)
        return result
    except Exception as e:
        logger.error(f"Error iniciando campaña: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/dialer/campaigns/{campaign_id}/stop")
async def stop_campaign_dialing(campaign_id: str):
    """Detener marcado automático para una campaña"""
    if not auto_dialer_available:
        return {"success": False, "message": "Auto dialer no disponible"}
    
    try:
        result = await dialer_integration.stop_campaign_dialing(campaign_id)
        return result
    except Exception as e:
        logger.error(f"Error deteniendo campaña: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/dialer/test-call")
async def make_test_call(call_data: dict):
    """Realizar llamada de prueba"""
    if not auto_dialer_available:
        return {"success": False, "message": "Auto dialer no disponible"}
    
    try:
        phone_number = call_data.get("phone_number")
        if not phone_number:
            return {"success": False, "message": "phone_number es requerido"}
        result = await dialer_integration.make_test_call(phone_number)
        return result
    except Exception as e:
        logger.error(f"Error en llamada de prueba: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/dialer/campaigns")
async def get_available_campaigns():
    """Obtener campañas disponibles para marcado"""
    if not auto_dialer_available:
        return {"success": False, "message": "Auto dialer no disponible", "campaigns": []}
    
    try:
        result = dialer_integration.get_available_campaigns()
        return result
    except Exception as e:
        logger.error(f"Error obteniendo campañas: {e}")
        return {"success": False, "message": str(e), "campaigns": []}

logger.info("🚀 Servidor VoIP Auto Dialer iniciado correctamente")

# ============================================================================
# SERVIDOR
# ============================================================================

if __name__ == "__main__":
    logger.info("Iniciando servidor web VoIP Auto Dialer v2.0")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
