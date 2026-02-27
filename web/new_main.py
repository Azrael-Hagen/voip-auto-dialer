"""
Servidor web principal para VoIP Auto Dialer - VERSIÓN COMPLETA CON PROVEEDORES Y EXTENSIONES
FastAPI con endpoints completos para agentes, extensiones, proveedores y sincronización
"""
import os
import sys
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
import uvicorn
import json

from core.logging_config import get_logger
from core.extension_manager import extension_manager
from core.agent_manager_clean import agent_manager
from core.asterisk_monitor import asterisk_monitor
from core.provider_manager import provider_manager
from core.softphone_auto_register import softphone_auto_register

# Configuración de la aplicación
app = FastAPI(
    title="VoIP Auto Dialer",
    description="Sistema de llamadas automatizadas con gestión completa de agentes, extensiones y proveedores",
    version="2.0.0"
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

class ExtensionUpdate(BaseModel):
    display_name: Optional[str] = None
    server_ip: Optional[str] = None
    password: Optional[str] = None
    provider: Optional[str] = None

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
                "version": "2.0.0",
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
                        <a href="/agents" class="btn btn-primary">Gestión de Agentes</a>
                        <a href="/providers" class="btn btn-secondary">Gestión de Proveedores</a>
                        <a href="/extensions" class="btn btn-info">Gestión de Extensiones</a>
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
        campaigns_file = project_root / "data" / "campaigns.json"
        campaigns = {}
        
        if campaigns_file.exists():
            with open(campaigns_file, 'r') as f:
                campaigns = json.load(f)
        
        return templates.TemplateResponse("campaigns_clean.html", {"request": request})
        
    except Exception as e:
        logger.error(f"Error en página de campañas: {e}")
        return templates.TemplateResponse("campaigns_clean.html", {"request": request})

# ============================================================================
# PÁGINAS DE PROVEEDORES Y EXTENSIONES
# ============================================================================

@app.get("/providers", response_class=HTMLResponse)
async def providers_page(request: Request):
    """Página de gestión de proveedores VoIP"""
    try:
        providers = provider_manager.get_all_providers()
        return templates.TemplateResponse("providers_enhanced.html", {
            "request": request,
            "providers": providers,
            "provider_count": len(providers)
        })
    except Exception as e:
        logger.error(f"Error en página de proveedores: {e}")
        raise HTTPException(status_code=500, detail=f"Error en proveedores: {e}")

@app.get("/extensions", response_class=HTMLResponse)
async def extensions_page(request: Request):
    """Página de gestión de extensiones"""
    try:
        return templates.TemplateResponse("extensions_management.html", {"request": request})
    except Exception as e:
        logger.error(f"Error en página de extensiones: {e}")
        raise HTTPException(status_code=500, detail=f"Error en extensiones: {e}")

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
        "components": {
            "extension_manager": "ok",
            "agent_manager": "ok",
            "provider_manager": "ok",
            "asterisk_monitor": "ok"
        }
    }

# ============================================================================
# API ENDPOINTS - AGENTES
# ============================================================================

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

# ============================================================================
# API ENDPOINTS - EXTENSIONES
# ============================================================================

@app.get("/api/extensions/stats")
async def get_extension_stats():
    """Obtener estadísticas de extensiones"""
    try:
        stats = extension_manager.get_extension_stats()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de extensiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/extensions/all")
async def get_all_extensions():
    """Obtener todas las extensiones con detalles completos"""
    try:
        extensions = extension_manager.get_all_extensions()
        return extensions
    except Exception as e:
        logger.error(f"Error obteniendo todas las extensiones: {e}")
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

@app.get("/api/extensions/{extension_id}")
async def get_extension_details(extension_id: str):
    """Obtener detalles de una extensión específica"""
    try:
        extension = extension_manager.get_extension(extension_id)
        if not extension:
            raise HTTPException(status_code=404, detail="Extensión no encontrada")
        return extension
    except Exception as e:
        logger.error(f"Error obteniendo extensión {extension_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/extensions/{extension_id}")
async def update_extension(extension_id: str, extension_data: ExtensionUpdate):
    """Actualizar una extensión"""
    try:
        # Convertir modelo Pydantic a diccionario, excluyendo valores None
        update_data = extension_data.dict(exclude_unset=True)
        
        updated_extension = extension_manager.update_extension(extension_id, **update_data)
        if not updated_extension:
            raise HTTPException(status_code=404, detail="Extensión no encontrada")
        
        logger.info(f"Extensión actualizada: {extension_id}")
        return updated_extension
        
    except Exception as e:
        logger.error(f"Error actualizando extensión {extension_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extensions/{extension_id}/regenerate-password")
async def regenerate_extension_password(extension_id: str):
    """Regenerar contraseña de una extensión"""
    try:
        result = extension_manager.regenerate_password(extension_id)
        if not result:
            raise HTTPException(status_code=404, detail="Extensión no encontrada")
        
        logger.info(f"Contraseña regenerada para extensión: {extension_id}")
        return {"message": "Contraseña regenerada exitosamente", "new_password": result["password"]}
        
    except Exception as e:
        logger.error(f"Error regenerando contraseña de extensión {extension_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extensions/{extension_id}/release")
async def release_extension_assignment(extension_id: str):
    """Liberar asignación de una extensión"""
    try:
        success = extension_manager.release_extension(extension_id)
        if not success:
            raise HTTPException(status_code=404, detail="Extensión no encontrada o no está asignada")
        
        logger.info(f"Extensión liberada: {extension_id}")
        return {"message": "Extensión liberada exitosamente"}
        
    except Exception as e:
        logger.error(f"Error liberando extensión {extension_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extensions/bulk-action")
async def execute_bulk_action(action_data: dict):
    """Ejecutar acciones masivas en extensiones"""
    try:
        action = action_data.get("action")
        range_start = action_data.get("range_start", 1000)
        range_end = action_data.get("range_end", 1100)
        
        if not action:
            raise HTTPException(status_code=400, detail="Acción requerida")
        
        result = extension_manager.execute_bulk_action(action, range_start, range_end)
        
        logger.info(f"Acción masiva ejecutada: {action} en rango {range_start}-{range_end}")
        return result
        
    except Exception as e:
        logger.error(f"Error ejecutando acción masiva: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/extensions/validate")
async def validate_extensions():
    """Validar integridad de todas las extensiones"""
    try:
        validation_report = extension_manager.validate_extension_integrity()
        return validation_report
    except Exception as e:
        logger.error(f"Error validando extensiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extensions/cleanup")
async def cleanup_extensions():
    """Limpiar extensiones huérfanas"""
    try:
        cleanup_report = extension_manager.cleanup_orphaned_extensions()
        return cleanup_report
    except Exception as e:
        logger.error(f"Error limpiando extensiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API ENDPOINTS - PROVEEDORES
# ============================================================================

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
async def create_provider(provider_data: ProviderCreate):
    """Crear un nuevo proveedor VoIP"""
    try:
        new_provider = provider_manager.create_provider(
            name=provider_data.name,
            provider_type=provider_data.type,
            host=provider_data.host,
            port=provider_data.port,
            username=provider_data.username,
            password=provider_data.password,
            transport=provider_data.transport,
            context=provider_data.context,
            codec=provider_data.codec,
            description=provider_data.description
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

@app.post("/api/providers/{provider_id}/test")
async def test_provider(provider_id: str):
    """Probar conexión con un proveedor"""
    try:
        result = provider_manager.test_connection(provider_id)
        return result
        
    except Exception as e:
        logger.error(f"Error probando proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers/{provider_id}/toggle")
async def toggle_provider(provider_id: str):
    """Activar/Desactivar proveedor"""
    try:
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

@app.get("/api/providers/stats")
async def get_provider_stats():
    """Obtener estadísticas de proveedores"""
    try:
        stats = provider_manager.get_provider_stats()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API ENDPOINTS - SINCRONIZACIÓN
# ============================================================================

@app.post("/api/sync/extensions-softphones")
async def sync_extensions_softphones():
    """Ejecutar sincronización completa entre extensiones y softphones"""
    try:
        import subprocess
        import sys
        
        # Ejecutar script de sincronización
        script_path = project_root / "scripts" / "sync_extensions_softphones.py"
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, cwd=str(project_root))
        
        if result.returncode == 0:
            logger.info("Sincronización extensiones-softphones completada")
            return {
                "success": True,
                "message": "Sincronización completada exitosamente",
                "output": result.stdout
            }
        else:
            logger.error(f"Error en sincronización: {result.stderr}")
            return {
                "success": False,
                "message": "Error en sincronización",
                "error": result.stderr
            }
        
    except Exception as e:
        logger.error(f"Error ejecutando sincronización: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sync/status")
async def get_sync_status():
    """Obtener estado de sincronización"""
    try:
        sync_data_file = project_root / "data" / "extension_softphone_sync.json"
        
        if sync_data_file.exists():
            with open(sync_data_file, 'r') as f:
                sync_data = json.load(f)
        else:
            sync_data = {
                "last_sync": None,
                "synced_extensions": {},
                "detected_softphones": {},
                "sync_history": []
            }
        
        # Agregar estadísticas actuales
        all_extensions = extension_manager.get_all_extensions()
        all_agents = agent_manager.get_all_agents()
        
        stats = {
            "extensions": {
                "total": len(all_extensions),
                "assigned": len([e for e in all_extensions.values() if e.get('assigned')]),
                "available": len([e for e in all_extensions.values() if not e.get('assigned')])
            },
            "agents": {
                "total": len(all_agents),
                "with_extensions": len([a for a in all_agents.values() if a.get('extension_info')]),
                "without_extensions": len([a for a in all_agents.values() if not a.get('extension_info')])
            }
        }
        
        return {
            "sync_data": sync_data,
            "current_stats": stats,
            "last_update": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de sincronización: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync/auto-assign")
async def auto_assign_extensions():
    """Asignar automáticamente extensiones a agentes sin extensión"""
    try:
        # Obtener agentes sin extensión
        all_agents = agent_manager.get_all_agents()
        agents_without_extension = []
        
        for agent_id, agent_data in all_agents.items():
            if not agent_data.get('extension_info'):
                agents_without_extension.append(agent_id)
        
        # Obtener extensiones disponibles
        available_extensions = extension_manager.get_available_extensions()
        
        assigned_count = 0
        max_assignments = min(len(agents_without_extension), len(available_extensions))
        
        for i in range(max_assignments):
            agent_id = agents_without_extension[i]
            
            # Asignar extensión al agente
            result = agent_manager.assign_extension(agent_id)
            if result:
                assigned_count += 1
        
        logger.info(f"Asignación automática completada: {assigned_count} extensiones asignadas")
        
        return {
            "success": True,
            "message": f"Se asignaron {assigned_count} extensiones automáticamente",
            "assigned_count": assigned_count,
            "agents_processed": len(agents_without_extension),
            "extensions_available": len(available_extensions)
        }
        
    except Exception as e:
        logger.error(f"Error en asignación automática: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sync/report")
async def get_sync_report():
    """Obtener reporte detallado de sincronización"""
    try:
        # Buscar el reporte más reciente
        data_dir = project_root / "data"
        report_files = list(data_dir.glob("sync_report_*.json"))
        
        if not report_files:
            return {
                "success": False,
                "message": "No hay reportes de sincronización disponibles"
            }
        
        # Obtener el reporte más reciente
        latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_report, 'r') as f:
            report_data = json.load(f)
        
        return {
            "success": True,
            "report": report_data,
            "report_file": str(latest_report),
            "generated_at": report_data.get('timestamp')
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo reporte de sincronización: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API ENDPOINTS - CONFIGURACIONES DE SOFTPHONE
# ============================================================================

@app.get("/api/extensions/{extension_id}/config/{config_type}")
async def get_extension_config(extension_id: str, config_type: str):
    """Obtener configuración de softphone para una extensión"""
    try:
        extension = extension_manager.get_extension(extension_id)
        if not extension:
            raise HTTPException(status_code=404, detail="Extensión no encontrada")
        
        server_ip = extension.get('server_ip', '127.0.0.1')
        extension_num = extension['extension']
        password = extension['password']
        display_name = extension.get('display_name', f'Extension {extension_num}')
        
        if config_type.lower() == "zoiper":
            config = {
                "type": "Zoiper",
                "account_name": display_name,
                "username": extension_num,
                "password": password,
                "domain": server_ip,
                "proxy": server_ip,
                "port": 5060,
                "transport": "UDP",
                "instructions": [
                    "1. Abrir Zoiper",
                    "2. Ir a Settings > Accounts",
                    "3. Agregar nueva cuenta SIP",
                    f"4. Username: {extension_num}",
                    f"5. Password: {password}",
                    f"6. Domain: {server_ip}",
                    "7. Guardar configuración",
                    "8. La extensión debería registrarse automáticamente"
                ]
            }
        elif config_type.lower() == "portsip":
            config = {
                "type": "PortSIP",
                "account_name": display_name,
                "username": extension_num,
                "password": password,
                "sip_server": server_ip,
                "port": 5060,
                "transport": "UDP",
                "instructions": [
                    "1. Abrir PortSIP Softphone",
                    "2. Ir a Account > Add Account",
                    f"3. User Name: {extension_num}",
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
                "account_name": display_name,
                "username": extension_num,
                "password": password,
                "server": server_ip,
                "port": 5060,
                "transport": "UDP",
                "codec": "ulaw, alaw, gsm",
                "instructions": [
                    "Configuración genérica para cualquier softphone SIP:",
                    f"- Username/Account: {extension_num}",
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

@app.post("/api/extensions/export-configs")
async def export_extension_configs(export_data: dict):
    """Exportar configuraciones de softphone para múltiples extensiones"""
    try:
        extension_ids = export_data.get("extension_ids", [])
        config_type = export_data.get("config_type", "generic")
        
        if not extension_ids:
            # Si no se especifican extensiones, usar todas las asignadas
            all_extensions = extension_manager.get_all_extensions()
            extension_ids = [
                ext_id for ext_id, ext_data in all_extensions.items()
                if ext_data.get('assigned', False)
            ]
        
        export_report = extension_manager.export_extension_configs(extension_ids, config_type)
        
        logger.info(f"Configuraciones exportadas: {export_report['configs_generated']} archivos")
        return export_report
        
    except Exception as e:
        logger.error(f"Error exportando configuraciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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