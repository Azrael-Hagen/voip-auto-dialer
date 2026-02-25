"""
Servidor web principal para VoIP Auto Dialer - VERSIÓN LIMPIA Y FUNCIONAL
FastAPI con endpoints completos para agentes, extensiones y campañas
"""
import os
import sys, uvicorn
from pathlib import Path
from typing import Dict, List, Optional


# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime

from core.logging_config import get_logger
from core.extension_manager import extension_manager
from core.agent_manager_clean import agent_manager
from core.asterisk_monitor import asterisk_monitor
from core.provider_manager import provider_manager
from core.softphone_auto_register import softphone_auto_register

# Configuración de la aplicación
app = FastAPI(
    title="VoIP Auto Dialer",
    description="Sistema de llamadas automatizadas con gestión de agentes y extensiones",
    version="1.0.0"
)

# Logger
logger = get_logger("web_server")

# Configurar archivos estáticos y templates
static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"

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

# ============================================================================
# RUTAS WEB (HTML)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal con datos en tiempo real"""
    try:
        # Obtener datos en tiempo real con manejo de errores
        try:
            realtime_data = asterisk_monitor.get_realtime_data()
        except Exception as e:
            logger.warning(f"Error obteniendo datos de Asterisk: {e}")
            realtime_data = {
                "system_status": "Unknown",
                "total_extensions": 0,
                "active_calls": 0,
                "uptime": "Unknown"
            }
        
        # Obtener estadísticas de agentes con manejo de errores
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
            agent_stats = {"total": 0, "online": 0, "offline": 0, "with_extensions": 0}
        
        # Obtener estadísticas de extensiones con manejo de errores
        try:
            extension_stats = extension_manager.get_extension_stats()
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas de extensiones: {e}")
            extension_stats = {"total": 0, "assigned": 0, "available": 0, "utilization": 0}
        
        # Obtener proveedores con manejo de errores
        try:
            providers = provider_manager.get_all_providers()
        except Exception as e:
            logger.warning(f"Error obteniendo proveedores: {e}")
            providers = {}
        
        # Obtener estado de auto-registro con manejo de errores
        try:
            auto_register_status = softphone_auto_register.get_monitoring_status()
        except Exception as e:
            logger.warning(f"Error obteniendo estado de auto-registro: {e}")
            auto_register_status = {
                "monitoring": False,
                "registered_endpoints": 0,
                "endpoints": {}
            }
        
        # Datos adicionales para el template
        template_data = {
            "request": request,
            "realtime_data": realtime_data,
            "agent_stats": agent_stats,
            "extension_stats": extension_stats,
            "providers": providers,
            "provider_count": len(providers),
            "auto_register_status": auto_register_status,
            # Datos adicionales que podrían necesitar los templates
            "campaigns": {},  # Por si el template lo necesita
            "active_campaigns": [],  # Por si el template lo necesita
            "system_info": {
                "version": "1.0.0",
                "environment": "production"
            }
        }
        
        return templates.TemplateResponse("dashboard_production.html", template_data)
        
    except Exception as e:
        logger.error(f"Error crítico en dashboard: {e}")
        # En caso de error crítico, mostrar página de error simple
        error_template = """
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
                    <p>Hay un problema temporal con el sistema. Por favor, intenta nuevamente.</p>
                    <hr>
                    <p class="mb-0">
                        <a href="/dev" class="btn btn-primary">Ir a Herramientas de Desarrollo</a>
                        <a href="/providers" class="btn btn-secondary">Gestión de Proveedores</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_template, status_code=500)

@app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """Página de gestión de agentes"""
    return templates.TemplateResponse("agents_clean.html", {"request": request})

@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request):
    """Página de gestión de campañas"""
    try:
        # Cargar campañas si existe el archivo
        import json
        campaigns_file = project_root / "data" / "campaigns.json"
        campaigns = {}
        
        if campaigns_file.exists():
            with open(campaigns_file, 'r') as f:
                campaigns = json.load(f)
        
        campaign_stats = {
            "total_campaigns": len(campaigns),
            "active_campaigns": sum(1 for c in campaigns.values() if c.get("status") == "active"),
            "completed_campaigns": sum(1 for c in campaigns.values() if c.get("status") == "completed")
        }
        
        return templates.TemplateResponse("campaigns_clean.html", {"request": request})
        
    except Exception as e:
        logger.error(f"Error en página de campañas: {e}")
        return templates.TemplateResponse("campaigns_clean.html", {"request": request})

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/agents")
async def get_agents():
    """Obtener todos los agentes"""
    try:
        agents = agent_manager.get_all_agents()
        
        # Validar que agents es un diccionario
        if not isinstance(agents, dict):
            logger.warning(f"get_all_agents devolvió tipo inesperado: {type(agents)}")
            return {}
        
        # Validar cada agente
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
    try:
        # Crear agente usando el manager
        new_agent = agent_manager.create_agent(
            name=agent.name,
            email=agent.email,
            phone=agent.phone
        )
        
        # Validar resultado
        if not new_agent or not isinstance(new_agent, dict) or 'id' not in new_agent:
            logger.error(f"create_agent devolvió resultado inválido: {new_agent}")
            raise HTTPException(status_code=500, detail="Error creando agente: resultado inválido")
        
        logger.info(f"Agente creado exitosamente: {new_agent['id']}")
        return new_agent
        
    except Exception as e:
        logger.error(f"Error creando agente: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/api/providers/{provider_id}")



@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Obtener un agente específico"""
    try:
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        return agent
    except Exception as e:
        logger.error(f"Error obteniendo agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/agents/{agent_id}")
async def update_agent(agent_id: str, agent_update: AgentUpdate):
    """Actualizar un agente"""
    try:
        # Obtener datos actuales
        current_agent = agent_manager.get_agent(agent_id)
        if not current_agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        # Preparar datos de actualización
        update_data = {}
        if agent_update.name is not None:
            update_data['name'] = agent_update.name
        if agent_update.email is not None:
            update_data['email'] = agent_update.email
        if agent_update.phone is not None:
            update_data['phone'] = agent_update.phone
        
        # Actualizar agente
        updated_agent = agent_manager.update_agent(agent_id, **update_data)
        if not updated_agent:
            raise HTTPException(status_code=500, detail="Error actualizando agente")
        
        logger.info(f"Agente actualizado: {agent_id}")
        return updated_agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Eliminar un agente"""
    try:
        success = agent_manager.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        logger.info(f"Agente eliminado: {agent_id}")
        return {"message": "Agente eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/assign-extension")
async def assign_extension(agent_id: str):
    """Asignar extensión a un agente"""
    try:
        # Verificar que el agente existe
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        # Asignar extensión
        result = agent_manager.assign_extension(agent_id)
        
        if result:
            logger.info(f"Extensión asignada a agente {agent_id}")
            return {
                "success": True, 
                "message": "Extensión asignada correctamente", 
                "result": result
            }
        else:
            raise HTTPException(status_code=400, detail="No se pudo asignar extensión - no hay extensiones disponibles")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error asignando extensión a {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/release-extension")
async def release_extension(agent_id: str):
    """Liberar extensión de un agente"""
    try:
        # Verificar que el agente existe
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        # Liberar extensión
        success = agent_manager.release_extension(agent_id)
        
        if success:
            logger.info(f"Extensión liberada del agente {agent_id}")
            return {"success": True, "message": "Extensión liberada correctamente"}
        else:
            raise HTTPException(status_code=400, detail="El agente no tiene extensión asignada")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error liberando extensión del agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/extensions/stats")
async def get_extension_stats():
    """Obtener estadísticas de extensiones"""
    try:
        stats = extension_manager.get_extension_stats()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de extensiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/extensions/available")
async def get_available_extensions():
    """Obtener extensiones disponibles"""
    try:
        available = extension_manager.get_available_extensions()
        return {
            "available_extensions": available,
            "count": len(available)
        }
    except Exception as e:
        logger.error(f"Error obteniendo extensiones disponibles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns")
async def get_campaigns():
    """Obtener todas las campañas"""
    try:
        import json
        campaigns_file = project_root / "data" / "campaigns.json"
        
        if not campaigns_file.exists():
            return {}
        
        with open(campaigns_file, 'r') as f:
            campaigns = json.load(f)
        
        return campaigns
        
    except Exception as e:
        logger.error(f"Error obteniendo campañas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns")
async def create_campaign(campaign_data: dict):
    """Crear una nueva campaña"""
    try:
        import json
        import uuid
        from datetime import datetime
        
        campaigns_file = project_root / "data" / "campaigns.json"
        
        # Cargar campañas existentes
        campaigns = {}
        if campaigns_file.exists():
            with open(campaigns_file, 'r') as f:
                campaigns = json.load(f)
        
        # Generar ID único
        campaign_id = f"campaign_{uuid.uuid4().hex[:8]}"
        
        # Crear nueva campaña
        new_campaign = {
            "id": campaign_id,
            "name": campaign_data["name"],
            "description": campaign_data.get("description", ""),
            "status": campaign_data.get("status", "inactive"),
            "phone_list": campaign_data.get("phone_list", []),
            "assigned_agents": campaign_data.get("assigned_agents", []),
            "created_at": datetime.now().isoformat(),
            "calls_made": 0,
            "progress": 0
        }
        
        # Agregar a la lista
        campaigns[campaign_id] = new_campaign
        
        # Guardar archivo
        campaigns_file.parent.mkdir(exist_ok=True)
        with open(campaigns_file, 'w') as f:
            json.dump(campaigns, f, indent=2)
        
        logger.info(f"Campaña creada: {new_campaign['name']} ({campaign_id})")
        return new_campaign
        
    except Exception as e:
        logger.error(f"Error creando campaña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, campaign_data: dict):
    """Actualizar una campaña"""
    try:
        import json
        from datetime import datetime
        
        campaigns_file = project_root / "data" / "campaigns.json"
        
        if not campaigns_file.exists():
            raise HTTPException(status_code=404, detail="No hay campañas registradas")
        
        # Cargar campañas
        with open(campaigns_file, 'r') as f:
            campaigns = json.load(f)
        
        if campaign_id not in campaigns:
            raise HTTPException(status_code=404, detail="Campaña no encontrada")
        
        # Actualizar campaña
        campaign = campaigns[campaign_id]
        campaign.update({
            "name": campaign_data.get("name", campaign["name"]),
            "description": campaign_data.get("description", campaign.get("description", "")),
            "status": campaign_data.get("status", campaign["status"]),
            "phone_list": campaign_data.get("phone_list", campaign.get("phone_list", [])),
            "assigned_agents": campaign_data.get("assigned_agents", campaign.get("assigned_agents", [])),
            "updated_at": datetime.now().isoformat()
        })
        
        # Guardar archivo
        with open(campaigns_file, 'w') as f:
            json.dump(campaigns, f, indent=2)
        
        logger.info(f"Campaña actualizada: {campaign['name']} ({campaign_id})")
        return campaign
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando campaña {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/campaigns/{campaign_id}/status")
async def change_campaign_status(campaign_id: str, status_data: dict):
    """Cambiar estado de una campaña"""
    try:
        import json
        from datetime import datetime
        
        campaigns_file = project_root / "data" / "campaigns.json"
        
        if not campaigns_file.exists():
            raise HTTPException(status_code=404, detail="No hay campañas registradas")
        
        # Cargar campañas
        with open(campaigns_file, 'r') as f:
            campaigns = json.load(f)
        
        if campaign_id not in campaigns:
            raise HTTPException(status_code=404, detail="Campaña no encontrada")
        
        # Cambiar estado
        new_status = status_data.get("status")
        if new_status not in ["active", "inactive", "paused", "completed"]:
            raise HTTPException(status_code=400, detail="Estado inválido")
        
        campaigns[campaign_id]["status"] = new_status
        campaigns[campaign_id]["updated_at"] = datetime.now().isoformat()
        
        # Guardar archivo
        with open(campaigns_file, 'w') as f:
            json.dump(campaigns, f, indent=2)
        
        logger.info(f"Estado de campaña cambiado: {campaigns[campaign_id]['name']} -> {new_status}")
        return {"message": f"Estado cambiado a {new_status}", "campaign": campaigns[campaign_id]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando estado de campaña {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Eliminar una campaña"""
    try:
        import json
        
        campaigns_file = project_root / "data" / "campaigns.json"
        
        if not campaigns_file.exists():
            raise HTTPException(status_code=404, detail="No hay campañas registradas")
        
        # Cargar campañas
        with open(campaigns_file, 'r') as f:
            campaigns = json.load(f)
        
        if campaign_id not in campaigns:
            raise HTTPException(status_code=404, detail="Campaña no encontrada")
        
        # Eliminar campaña
        campaign_name = campaigns[campaign_id]["name"]
        del campaigns[campaign_id]
        
        # Guardar archivo
        with open(campaigns_file, 'w') as f:
            json.dump(campaigns, f, indent=2)
        
        logger.info(f"Campaña eliminada: {campaign_name} ({campaign_id})")
        return {"message": "Campaña eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando campaña {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PROVEEDORES VoIP ENDPOINTS
# ============================================================================
@app.get("/providers", response_class=HTMLResponse)
async def providers_page(request: Request):
    """Página de gestión de proveedores VoIP"""
    try:
        providers = provider_manager.get_all_providers()
        return templates.TemplateResponse("providers_clean.html", {
            "request": request,
            "providers": providers,
            "provider_count": len(providers)
        })
    except Exception as e:
        logger.error(f"Error en página de proveedores: {e}")
        raise HTTPException(status_code=500, detail=f"Error en proveedores: {e}")

@app.get("/api/providers")
async def get_providers():
    """Obtener todos los proveedores"""
    try:
        providers = provider_manager.get_all_providers()
        return providers
    except Exception as e:
        logger.error(f"Error obteniendo proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers")
async def create_provider(provider_data: dict):
    """Crear un nuevo proveedor VoIP"""
    try:
        # Validar datos requeridos
        required_fields = ["name", "type", "host"]
        for field in required_fields:
            if field not in provider_data:
                raise HTTPException(status_code=400, detail=f"Campo requerido: {field}")
        
        new_provider = provider_manager.create_provider(
            name=provider_data["name"],
            type=provider_data["type"],   # ✅ ahora sí existe en la firma
            host=provider_data["host"],
            port=provider_data.get("port", 5060),
            username=provider_data.get("username", ""),
            password=provider_data.get("password", ""),
            transport=provider_data.get("transport", "UDP"),
            context=provider_data.get("context", "from-trunk"),  # ✅ ahora sí existe en la firma
            codec=provider_data.get("codec", "ulaw,alaw,gsm"),
            description=provider_data.get("description", "")
        )

        
        
        logger.info(f"Proveedor creado: {new_provider['name']} ({new_provider['id']})")
        return new_provider
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creando proveedor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers/{provider_id}")
async def get_provider(provider_id: str):
    """Obtener un proveedor específico"""
    try:
        provider = provider_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        return provider
    except Exception as e:
        logger.error(f"Error obteniendo proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/providers/{provider_id}")
async def update_provider(provider_id: str, provider_data: dict):
    """Actualizar un proveedor"""
    try:
        updated_provider = provider_manager.update_provider(provider_id, **provider_data)
        if not updated_provider:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
        logger.info(f"Proveedor actualizado: {updated_provider['name']} ({provider_id})")
        return updated_provider
        
    except Exception as e:
        logger.error(f"Error actualizando proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: str):
    """Eliminar un proveedor"""
    try:
        success = provider_manager.delete_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
        logger.info(f"Proveedor eliminado: {provider_id}")
        return {"message": "Proveedor eliminado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error eliminando proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers/{provider_id}/activate")
async def activate_provider(provider_id: str):
    """Activar un proveedor"""
    try:
        success = provider_manager.activate_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
        return {"message": "Proveedor activado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error activando proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers/{provider_id}/deactivate")
async def deactivate_provider(provider_id: str):
    """Desactivar un proveedor"""
    try:
        success = provider_manager.deactivate_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
        return {"message": "Proveedor desactivado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error desactivando proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers/{provider_id}/test")
async def test_provider(provider_id: str):
    """Probar conexión con un proveedor"""
    try:
        result = provider_manager.test_provider_connection(provider_id)
        return result
        
    except Exception as e:
        logger.error(f"Error probando proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers/stats")
async def get_provider_stats():
    """Obtener estadísticas de proveedores"""
    try:
        stats = provider_manager.get_provider_stats()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers/asterisk-config")
async def get_asterisk_config():
    """Generar configuración de Asterisk para proveedores"""
    try:
        config = provider_manager.generate_asterisk_config()
        return {"config": config}
    except Exception as e:
        logger.error(f"Error generando configuración de Asterisk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SOFTPHONE CONFIGURATION ENDPOINTS
# ============================================================================

@app.get("/api/agents/{agent_id}/softphone-config/{config_type}")
async def get_softphone_config(agent_id: str, config_type: str):
    """Obtener configuración de softphone para un agente"""
    try:
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        extension_info = agent.get("extension_info")
        if not extension_info:
            raise HTTPException(status_code=400, detail="Agente no tiene extensión asignada")
        
        # Obtener IP del servidor (puedes configurar esto)
        server_ip = "127.0.0.1"  # Cambiar por la IP real del servidor
        
        extension = extension_info["extension"]
        password = extension_info["password"]
        
        if config_type.lower() == "zoiper":
            config = {
                "type": "Zoiper",
                "account_name": f"Agent {agent['name']} - Ext {extension}",
                "username": extension,
                "password": password,
                "domain": server_ip,
                "proxy": server_ip,
                "port": 5060,
                "transport": "UDP",
                "instructions": [
                    "1. Abrir Zoiper",
                    "2. Ir a Settings > Accounts",
                    "3. Agregar nueva cuenta SIP",
                    f"4. Username: {extension}",
                    f"5. Password: {password}",
                    f"6. Domain: {server_ip}",
                    "7. Guardar configuración",
                    "8. La extensión debería registrarse automáticamente"
                ]
            }
        elif config_type.lower() == "portsip":
            config = {
                "type": "PortSIP",
                "account_name": f"Agent {agent['name']} - Ext {extension}",
                "username": extension,
                "password": password,
                "sip_server": server_ip,
                "port": 5060,
                "transport": "UDP",
                "instructions": [
                    "1. Abrir PortSIP Softphone",
                    "2. Ir a Account > Add Account",
                    f"3. User Name: {extension}",
                    f"4. Password: {password}",
                    f"5. SIP Server: {server_ip}",
                    "6. Port: 5060",
                    "7. Transport: UDP",
                    "8. Click OK para guardar",
                    "9. La cuenta debería aparecer como 'Online'"
                ]
            }
        elif config_type.lower() == "generic":
            config = {
                "type": "Generic SIP",
                "account_name": f"Agent {agent['name']} - Ext {extension}",
                "username": extension,
                "password": password,
                "server": server_ip,
                "port": 5060,
                "transport": "UDP",
                "codec": "ulaw, alaw, gsm",
                "instructions": [
                    "Configuración genérica para cualquier softphone SIP:",
                    f"- Username/Account: {extension}",
                    f"- Password: {password}",
                    f"- Server/Domain: {server_ip}",
                    "- Port: 5060",
                    "- Transport: UDP",
                    "- Codec: ulaw, alaw, gsm"
                ]
            }
        else:
            raise HTTPException(status_code=400, detail="Tipo de configuración no soportado")
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando configuración de softphone: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ============================================================================
# SOFTPHONE AUTO-REGISTRATION ENDPOINTS
# ============================================================================

from core.softphone_monitor import softphone_monitor

@app.post("/api/softphones/scan")
async def scan_softphone_registrations():
    """Escanear y auto-registrar softphones conectados"""
    try:
        results = softphone_monitor.scan_and_auto_register()
        
        message = f"Escaneo completado: {results['new_agents_created']} nuevos agentes creados"
        if results['errors'] > 0:
            message += f", {results['errors']} errores"
        
        return {
            "success": True,
            "message": message,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error en escaneo de softphones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/softphones/registered")
async def get_registered_softphones():
    """Obtener todos los softphones registrados"""
    try:
        softphones = softphone_monitor.get_registered_softphones()
        return softphones
    except Exception as e:
        logger.error(f"Error obteniendo softphones registrados: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/softphones/{extension}")
async def unregister_softphone(extension: str):
    """Desregistrar un softphone"""
    try:
        success = softphone_monitor.unregister_softphone(extension)
        if not success:
            raise HTTPException(status_code=404, detail="Softphone no encontrado")
        
        return {"message": "Softphone desregistrado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error desregistrando softphone {extension}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/softphones/stats")
async def get_softphone_stats():
    """Obtener estadísticas de softphones"""
    try:
        stats = softphone_monitor.get_softphone_stats()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de softphones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PROVIDER-AGENT LINKING ENDPOINTS
# ============================================================================

@app.post("/api/agents/{agent_id}/link-provider")
async def link_agent_to_provider(agent_id: str, link_data: dict):
    """Vincular un agente a un proveedor VoIP"""
    try:
        provider_id = link_data.get("provider_id")
        if not provider_id:
            raise HTTPException(status_code=400, detail="provider_id es requerido")
        
        # Verificar que el agente existe
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        # Verificar que el proveedor existe
        provider = provider_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
        # Verificar que el proveedor está activo
        if provider.get("status") != "active":
            raise HTTPException(status_code=400, detail="El proveedor debe estar activo")
        
        # Actualizar agente con información del proveedor
        if "provider_info" not in agent:
            agent["provider_info"] = {}
        
        agent["provider_info"] = {
            "provider_id": provider_id,
            "provider_name": provider["name"],
            "linked_at": datetime.now().isoformat(),
            "status": "linked"
        }
        
        # Guardar cambios
        agent_manager.agents[agent_id] = agent
        agent_manager._save_agents()
        
        logger.info(f"Agente {agent_id} vinculado al proveedor {provider_id}")
        return {
            "message": "Agente vinculado al proveedor exitosamente",
            "agent": agent,
            "provider": provider
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error vinculando agente {agent_id} al proveedor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agents/{agent_id}/unlink-provider")
async def unlink_agent_from_provider(agent_id: str):
    """Desvincular un agente de su proveedor"""
    try:
        # Verificar que el agente existe
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        # Verificar que el agente tiene proveedor vinculado
        if "provider_info" not in agent:
            raise HTTPException(status_code=400, detail="El agente no tiene proveedor vinculado")
        
        # Remover información del proveedor
        del agent["provider_info"]
        
        # Guardar cambios
        agent_manager.agents[agent_id] = agent
        agent_manager._save_agents()
        
        logger.info(f"Agente {agent_id} desvinculado de su proveedor")
        return {"message": "Agente desvinculado del proveedor exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error desvinculando agente {agent_id} del proveedor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# REAL-TIME ASTERISK MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/realtime/dashboard")
async def get_realtime_dashboard_data():
    """Obtener todos los datos del dashboard en una sola llamada"""
    try:
        # Obtener todos los datos necesarios para el dashboard
        realtime_data = asterisk_monitor.get_realtime_data()
        extension_stats = extension_manager.get_extension_stats()
        
        agents = agent_manager.get_all_agents()
        agent_stats = {
            "total": len(agents),
            "online": len([a for a in agents.values() if a.get("status") == "online"]),
            "offline": len([a for a in agents.values() if a.get("status") == "offline"]),
            "with_extensions": len([a for a in agents.values() if a.get("extension_info")])
        }
        
        auto_register_status = softphone_auto_register.get_monitoring_status()
        
        return {
            "success": True,
            "realtime_data": realtime_data,
            "extension_stats": extension_stats,
            "agent_stats": agent_stats,
            "auto_register_status": auto_register_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo datos del dashboard: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/realtime/dashboard")
async def get_realtime_dashboard():
    """Obtener datos completos del dashboard en tiempo real"""
    try:
        data = asterisk_monitor.get_realtime_dashboard_data()
        return data
    except Exception as e:
        logger.error(f"Error obteniendo datos en tiempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/system")
async def get_system_status():
    """Obtener estado del sistema Asterisk"""
    try:
        status = asterisk_monitor.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/extensions")
async def get_realtime_extensions():
    """Obtener estado de extensiones en tiempo real"""
    try:
        extension_stats = extension_manager.get_extension_stats()
        return {
            "success": True,
            "extensions": extension_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo extensiones en tiempo real: {e}")
        return {
            "success": False,
            "error": str(e),
            "extensions": {"total": 0, "assigned": 0, "available": 0, "utilization": 0}
        }

@app.get("/api/realtime/calls")
async def get_realtime_calls():
    """Obtener llamadas activas en tiempo real"""
    try:
        # Obtener datos de llamadas desde asterisk_monitor
        realtime_data = asterisk_monitor.get_realtime_data()
        calls_data = {
            "active_calls": realtime_data.get("active_calls", 0),
            "total_calls_today": 0,  # Por implementar
            "successful_calls": 0,   # Por implementar
            "failed_calls": 0        # Por implementar
        }
        return {
            "success": True,
            "calls": calls_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo llamadas en tiempo real: {e}")
        return {
            "success": False,
            "error": str(e),
            "calls": {"active_calls": 0, "total_calls_today": 0, "successful_calls": 0, "failed_calls": 0}
        }

@app.get("/api/realtime/calls")
async def get_active_calls_realtime():
    """Obtener llamadas activas en tiempo real"""
    try:
        calls = asterisk_monitor.get_active_calls()
        return calls
    except Exception as e:
        logger.error(f"Error obteniendo llamadas activas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/providers")
async def get_providers_realtime():
    """Obtener estado en tiempo real de proveedores SIP"""
    try:
        providers = asterisk_monitor.get_sip_peers_status()
        return providers
    except Exception as e:
        logger.error(f"Error obteniendo estado de proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/extension/{extension}")
async def get_extension_details_realtime(extension: str):
    """Obtener detalles específicos de una extensión"""
    try:
        details = asterisk_monitor.get_extension_details(extension)
        if not details:
            raise HTTPException(status_code=404, detail="Extensión no encontrada")
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo detalles de extensión {extension}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/realtime/refresh")
async def refresh_realtime_cache():
    """Forzar actualización del cache de datos en tiempo real"""
    try:
        asterisk_monitor.clear_cache()
        return {"message": "Cache actualizado exitosamente"}
    except Exception as e:
        logger.error(f"Error actualizando cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DEVELOPMENT/TESTING ROUTES (HIDDEN)
# ============================================================================

@app.get("/dev", response_class=HTMLResponse)
async def dev_dashboard(request: Request):
    """Dashboard de desarrollo (oculto)"""
    try:
        agents = agent_manager.get_all_agents()
        if not isinstance(agents, dict):
            agents = {}
        
        agent_count = len(agents)
        agent_stats = {
            "total": agent_count,
            "total_agents": agent_count,
            "active": sum(1 for a in agents.values() if a.get("status") == "active"),
            "with_extensions": sum(1 for a in agents.values() if a.get("extension_info"))
        }
        
        # Estadísticas de extensiones
        extension_stats = extension_manager.get_extension_stats()
        
        # Cargar campañas si existe el archivo
        import json
        campaigns_file = project_root / "data" / "campaigns.json"
        campaigns = {}
        
        if campaigns_file.exists():
            with open(campaigns_file, 'r') as f:
                campaigns = json.load(f)
        
        active_campaigns = [c for c in campaigns.values() if c.get("status") == "active"]
        
        return templates.TemplateResponse("dashboard_clean.html", {
            "request": request,
            "agent_stats": agent_stats,
            "extension_stats": extension_stats,
            "campaigns": campaigns,
            "active_campaigns": active_campaigns
        })
        
    except Exception as e:
        logger.error(f"Error en dashboard de desarrollo: {e}")
        return templates.TemplateResponse("dashboard_clean.html", {
            "request": request,
            "agent_stats": {"total": 0, "total_agents": 0, "active": 0, "with_extensions": 0},
            "extension_stats": {"total": 0, "assigned": 0, "available": 0, "utilization": 0},
            "campaigns": {},
            "active_campaigns": []
        })


@app.get("/dev/agents", response_class=HTMLResponse)
async def dev_agents(request: Request):
    """Gestión de agentes para desarrollo"""
    return templates.TemplateResponse("agents_clean.html", {"request": request})

@app.get("/dev/campaigns", response_class=HTMLResponse)
async def dev_campaigns(request: Request):
    """Gestión de campañas para desarrollo"""
    return templates.TemplateResponse("campaigns_clean.html", {"request": request})


# ============================================================================
# API ENDPOINTS - PROVEEDORES VOIP
# ============================================================================

@app.get("/api/providers")
async def get_providers():
    """Obtener todos los proveedores VoIP"""
    try:
        from core.provider_manager import provider_manager
        providers = provider_manager.get_all_providers()
        
        return {
            "success": True,
            "providers": providers,
            "count": len(providers)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo proveedores: {e}")
        # Devolver estructura vacía si no existe el módulo
        return {
            "success": True,
            "providers": {},
            "count": 0
        }

@app.post("/api/providers")
async def create_provider(provider_data: dict):
    """Crear nuevo proveedor VoIP"""
    try:
        from core.provider_manager import provider_manager
        
        new_provider = provider_manager.create_provider(
            name=provider_data["name"],
            host=provider_data["host"],
            username=provider_data["username"],
            password=provider_data["password"],
            port=provider_data.get("port", 5060),
            transport=provider_data.get("transport", "udp"),
            codec=provider_data.get("codec", "ulaw"),
            description=provider_data.get("description", ""),
            active=provider_data.get("active", True)
        )
        
        logger.info(f"Proveedor creado: {provider_data['name']}")
        return {"success": True, "message": "Proveedor creado exitosamente", "provider": new_provider}
        
    except Exception as e:
        logger.error(f"Error creando proveedor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers/{provider_id}/test")
async def test_provider_connection(provider_id: str):
    """Probar conexión con proveedor VoIP"""
    try:
        from core.provider_manager import provider_manager
        
        result = provider_manager.test_connection(provider_id)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "details": result.get("details", {})
        }
        
    except Exception as e:
        logger.error(f"Error probando conexión del proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers/{provider_id}/toggle")
async def toggle_provider(provider_id: str):
    """Activar/Desactivar proveedor VoIP"""
    try:
        from core.provider_manager import provider_manager
        
        result = provider_manager.toggle_provider(provider_id)
        
        if result:
            provider = provider_manager.get_provider(provider_id)
            status = "activado" if provider["active"] else "desactivado"
            return {"success": True, "message": f"Proveedor {status} exitosamente"}
        else:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando estado del proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: str):
    """Eliminar proveedor VoIP"""
    try:
        from core.provider_manager import provider_manager
        
        success = provider_manager.delete_provider(provider_id)
        
        if success:
            logger.info(f"Proveedor eliminado: {provider_id}")
            return {"success": True, "message": "Proveedor eliminado exitosamente"}
        else:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# API ENDPOINTS - AUTO-REGISTRO
# ===============================

@app.get("/api/auto-register/status")
async def get_auto_register_status():
    """Obtener estado del sistema de auto-registro"""
    try:
        status = softphone_auto_register.get_monitoring_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado de auto-registro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-register/start")
async def start_auto_register():
    """Iniciar monitoreo de auto-registro"""
    try:
        softphone_auto_register.start_monitoring()
        return {
            "success": True,
            "message": "Monitoreo de auto-registro iniciado"
        }
    except Exception as e:
        logger.error(f"Error iniciando auto-registro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-register/stop")
async def stop_auto_register():
    """Detener monitoreo de auto-registro"""
    try:
        softphone_auto_register.stop_monitoring()
        return {
            "success": True,
            "message": "Monitoreo de auto-registro detenido"
        }
    except Exception as e:
        logger.error(f"Error deteniendo auto-registro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-register/registered-endpoints")
async def get_registered_endpoints():
    """Obtener lista de endpoints registrados"""
    try:
        status = softphone_auto_register.get_monitoring_status()
        return {
            "success": True,
            "endpoints": status.get("endpoints", {}),
            "count": status.get("registered_endpoints", 0)
        }
    except Exception as e:
        logger.error(f"Error obteniendo endpoints registrados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# API ENDPOINTS - TIEMPO REAL
# ===============================

@app.get("/api/realtime/system-status")
async def get_realtime_system_status():
    """Obtener estado del sistema en tiempo real"""
    try:
        realtime_data = asterisk_monitor.get_realtime_data()
        return realtime_data
    except Exception as e:
        logger.error(f"Error obteniendo estado en tiempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/extensions")
async def get_realtime_extensions():
    """Obtener estado de extensiones en tiempo real"""
    try:
        extension_stats = extension_manager.get_extension_stats()
        return {
            "success": True,
            "extensions": extension_stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo extensiones en tiempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/agents")
async def get_realtime_agents():
    """Obtener estado de agentes en tiempo real"""
    try:
        agents = agent_manager.get_all_agents()
        agent_stats = {
            "total": len(agents),
            "online": len([a for a in agents.values() if a.get("status") == "online"]),
            "offline": len([a for a in agents.values() if a.get("status") == "offline"]),
            "with_extensions": len([a for a in agents.values() if a.get("extension_info")])
        }
        return {
            "success": True,
            "agent_stats": agent_stats,
            "agents": list(agents.values())
        }
    except Exception as e:
        logger.error(f"Error obteniendo agentes en tiempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/calls")
async def get_realtime_calls():
    """Obtener llamadas activas en tiempo real"""
    try:
        # Por ahora retornamos datos simulados, después se puede conectar a Asterisk
        calls_data = {
            "active_calls": 0,
            "total_calls_today": 0,
            "successful_calls": 0,
            "failed_calls": 0
        }
        return {
            "success": True,
            "calls": calls_data
        }
    except Exception as e:
        logger.error(f"Error obteniendo llamadas en tiempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))


#-----------------------------------------------------------------------------------------
async def edit_provider(provider_id: str, provider_data: dict):
    try:
        updated_provider = provider_manager.update_provider(provider_id, provider_data)
        return updated_provider
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#-----------------------------------------------------------------------------------------




# ============================================================================
# SERVIDOR
# ============================================================================

if __name__ == "__main__":
    logger.info("Iniciando servidor web VoIP Auto Dialer")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )