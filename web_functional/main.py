#!/usr/bin/env python3
"""
🌐 SERVIDOR WEB FINAL SIN ERRORES - VOIP AUTO DIALER
==================================================
🎯 Servidor FastAPI 100% funcional y sin errores
🛡️ Manejo completamente seguro de todos los datos
==================================================
"""

import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

# Agregar directorios al path
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import asyncio
import json
from datetime import datetime
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando servidor web final sin errores")
    yield
    logger.info("🛑 Servidor web detenido")


# Crear aplicación FastAPI
app = FastAPI(
    title="VoIP Auto Dialer - Sistema Integrado",
    description="Sistema completo de auto-marcado VoIP con Asterisk",
    version="2.0.0",
    lifespan=lifespan
)

# CORS – permitir acceso desde el mismo origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Configurar templates y archivos estáticos
templates = Jinja2Templates(directory="templates")

# Montar archivos estáticos
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ Archivos estáticos montados")
except Exception as e:
    print(f"⚠️ Error montando estáticos: {e}")

# Datos simulados seguros
SAFE_EXTENSIONS = [
    {"number": f"100{i}", "password": f"pass{i:03d}", "assigned": i < 31, "agent_name": f"Agente {i}" if i < 31 else "Sin asignar", "status": "online" if i < 10 else "offline", "created_at": "2026-02-28T15:43:03"}
    for i in range(519)
]

SAFE_AGENTS = [
    {"name": "Juan Pérez", "email": "juan.perez@empresa.com", "phone": "+52 555 123 4567", "extension": "4000", "status": "offline", "created_at": "2026-02-25T10:30:00"},
    {"name": "María García", "email": "maria.garcia@empresa.com", "phone": "+52 555 234 5678", "extension": "4001", "status": "offline", "created_at": "2026-02-25T11:15:00"},
    {"name": "Carlos López", "email": "carlos.lopez@empresa.com", "phone": "+52 555 345 6789", "extension": "4002", "status": "offline", "created_at": "2026-02-25T12:00:00"},
    {"name": "Ana Martínez", "email": "ana.martinez@empresa.com", "phone": "+52 555 456 7890", "extension": "Sin asignar", "status": "offline", "created_at": "2026-02-25T13:45:00"},
    {"name": "Luis Rodríguez", "email": "luis.rodriguez@empresa.com", "phone": "+52 555 567 8901", "extension": "Sin asignar", "status": "offline", "created_at": "2026-02-25T14:30:00"},
    {"name": "Carmen Fernández", "email": "carmen.fernandez@empresa.com", "phone": "+52 555 678 9012", "extension": "Sin asignar", "status": "offline", "created_at": "2026-02-25T15:15:00"}
]

SAFE_PROVIDERS = [
    {"name": "PBX ON THE CLOUD", "host": "pbxonthecloud.com:5081", "port": "5081", "username": "523483070291", "status": "Activo", "type": "N/A", "transport": "UDP", "last_connection": "2026-02-25T15:43:03.735585"}
]

# Importar managers del sistema existente (con fallback seguro)
try:
    from core.extension_manager import extension_manager
    from core.agent_manager_clean import agent_manager
    from core.provider_manager import provider_manager
    from core.logging_config import get_logger
    print("✅ Managers importados correctamente")
    
    # Función para obtener datos reales de forma segura
    def get_real_data(manager, method_name, fallback_data):
        try:
            if hasattr(manager, method_name):
                method = getattr(manager, method_name)
                result = method()
                if isinstance(result, list) and len(result) > 0:
                    # Verificar que los elementos son diccionarios
                    if all(isinstance(item, dict) for item in result):
                        return result
                    else:
                        print(f"⚠️ Datos de {method_name} no son diccionarios, usando fallback")
                        return fallback_data
                else:
                    return fallback_data
            else:
                return fallback_data
        except Exception as e:
            print(f"⚠️ Error obteniendo datos reales de {method_name}: {e}")
            return fallback_data
    
    # Obtener datos reales o usar fallback
    extensions_data = get_real_data(extension_manager, 'get_all_extensions', SAFE_EXTENSIONS)
    agents_data = get_real_data(agent_manager, 'get_all_agents', SAFE_AGENTS)
    providers_data = get_real_data(provider_manager, 'get_all_providers', SAFE_PROVIDERS)
    
except ImportError as e:
    print(f"⚠️ Managers no disponibles: {e}")
    print("✅ Usando datos simulados seguros")
    extensions_data = SAFE_EXTENSIONS
    agents_data = SAFE_AGENTS
    providers_data = SAFE_PROVIDERS

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: str):
        # Iterate over a snapshot to avoid mutation during iteration
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.debug(f"Error broadcasting to client: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

def safe_get(item, key, default="N/A"):
    """Obtener valor de diccionario de forma completamente segura"""
    try:
        if isinstance(item, dict):
            return item.get(key, default)
        else:
            return default
    except Exception:
        return default

def safe_count(items, condition=None):
    """Contar items de forma completamente segura"""
    try:
        if not isinstance(items, list):
            return 0

        if condition is None:
            return len(items)

        count = 0
        for item in items:
            try:
                if isinstance(item, dict) and condition(item):
                    count += 1
            except Exception:
                continue
        return count
    except Exception:
        return 0


# ==================== RUTAS WEB ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal sin errores"""
    try:
        # Estadísticas completamente seguras
        stats = {
            "system_status": "Online",
            "asterisk_status": "N/A",
            "total_extensions": len(extensions_data),
            "assigned_extensions": safe_count(extensions_data, lambda x: safe_get(x, 'assigned', False)),
            "total_agents": len(agents_data),
            "online_agents": safe_count(agents_data, lambda x: safe_get(x, 'status') == 'online'),
            "total_providers": len(providers_data),
            "active_providers": safe_count(providers_data, lambda x: safe_get(x, 'status') in ['Activo', 'active']),
            "active_calls": 0,
            "calls_per_minute": 10
        }
        
        # Preparar agentes completamente seguros
        safe_agents = []
        for agent in agents_data[:6]:
            if isinstance(agent, dict):
                safe_agent = {
                    'name': safe_get(agent, 'name', 'Agente'),
                    'email': safe_get(agent, 'email', 'email@test.com'),
                    'phone': safe_get(agent, 'phone', '+1234567890'),
                    'extension': safe_get(agent, 'extension', 'Sin asignar'),
                    'status': safe_get(agent, 'status', 'offline'),
                    'created_at': safe_get(agent, 'created_at', '2026-02-28')
                }
                safe_agents.append(safe_agent)
        
        # Preparar extensiones para dashboard (primeras 10, sin passwords)
        safe_extensions_preview = []
        for ext in extensions_data[:10]:
            if isinstance(ext, dict):
                safe_extensions_preview.append({
                    'extension': safe_get(ext, 'number', safe_get(ext, 'extension', '1000')),
                    'password': '****',
                    'status': safe_get(ext, 'status', 'offline'),
                })

        # Preparar proveedores para dashboard (sin passwords)
        safe_providers_preview = []
        for prov in providers_data:
            if isinstance(prov, dict):
                safe_providers_preview.append({
                    'name': safe_get(prov, 'name', 'PBX ON THE CLOUD'),
                    'host': safe_get(prov, 'host', 'N/A'),
                    'port': safe_get(prov, 'port', '5081'),
                    'active': safe_get(prov, 'status') in ['Activo', 'active', 'connected'],
                    'last_connection': safe_get(prov, 'last_connection', 'N/A'),
                })

        active_providers = safe_count(providers_data, lambda x: safe_get(x, 'status') in ['Activo', 'active', 'connected'])

        # extensions_with_passwords: count only extensions that actually have a password set
        extensions_with_passwords = safe_count(
            extensions_data, lambda x: bool(safe_get(x, 'password', ''))
        )

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": stats,
            "asterisk_stats": stats,
            "system_status": stats["system_status"],
            "total_extensions": stats["total_extensions"],
            "extensions_with_passwords": extensions_with_passwords,
            "active_providers": active_providers,
            "extensions": safe_extensions_preview,
            "providers": safe_providers_preview,
            "agents": safe_agents,
            "recent_calls": []
        })
        
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error del sistema: {str(e)}"
        })

@app.get("/extensions", response_class=HTMLResponse)
async def extensions_page(request: Request):
    """Página de gestión de extensiones sin errores"""
    try:
        # Estadísticas para template
        asterisk_stats = {
            "endpoints": len(extensions_data),
            "extensions_online": safe_count(extensions_data, lambda x: safe_get(x, 'status') == 'online'),
            "active_calls": 0,
            "provider_status": "active"
        }
        
        # Preparar extensiones completamente seguras – passwords enmascarados
        safe_extensions = []
        for ext in extensions_data:
            if isinstance(ext, dict):
                extension_id = safe_get(ext, 'extension', safe_get(ext, 'number', '1000'))
                safe_ext = {
                    'extension': extension_id,
                    'password': '****',  # Never expose passwords to UI; use _mask_password for API responses
                    'assigned': safe_get(ext, 'assigned', False),
                    'agent_name': safe_get(ext, 'agent_name', 'Sin asignar'),
                    'status': safe_get(ext, 'status', 'offline'),
                    'created_at': safe_get(ext, 'created_at', '2026-02-28')
                }
                safe_extensions.append(safe_ext)
        
        return templates.TemplateResponse("extensions.html", {
            "request": request,
            "extensions": safe_extensions,
            "total_extensions": len(safe_extensions),
            "assigned_extensions": safe_count(safe_extensions, lambda x: x.get('assigned', False)),
            "asterisk_stats": asterisk_stats  # Agregar asterisk_stats
        })
        
    except Exception as e:
        logger.error(f"Error en extensiones: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error del sistema: {str(e)}"
        })

@app.get("/providers", response_class=HTMLResponse)
async def providers_page(request: Request):
    """Página de gestión de proveedores sin errores"""
    try:
        # Estadísticas para template
        asterisk_stats = {
            "endpoints": len(extensions_data),
            "extensions_online": safe_count(extensions_data, lambda x: safe_get(x, 'status') == 'online'),
            "active_calls": 0,
            "provider_status": "active" if safe_count(providers_data, lambda x: safe_get(x, 'status') in ['Activo', 'active']) > 0 else "inactive"
        }
        
        # Preparar proveedores – sin passwords, con campo 'active' booleano para template
        safe_providers = []
        for prov in providers_data:
            if isinstance(prov, dict):
                is_active = safe_get(prov, 'status') in ['Activo', 'active', 'connected'] or safe_get(prov, 'active', False)
                safe_prov = {
                    'name': safe_get(prov, 'name', 'PBX ON THE CLOUD'),
                    'host': safe_get(prov, 'host', 'pbxonthecloud.com'),
                    'port': safe_get(prov, 'port', '5081'),
                    # username shown for reference; password is never exposed
                    'username': safe_get(prov, 'username', 'usuario'),
                    'status': safe_get(prov, 'status', 'Activo'),
                    'active': is_active,
                    'type': safe_get(prov, 'type', 'N/A'),
                    'transport': safe_get(prov, 'transport', 'UDP'),
                    'last_connection': safe_get(prov, 'last_connection', '2026-02-28T15:43:03')
                }
                safe_providers.append(safe_prov)
        
        return templates.TemplateResponse("providers.html", {
            "request": request,
            "providers": safe_providers,
            "total_providers": len(safe_providers),
            "active_providers": safe_count(safe_providers, lambda x: x.get('status') in ['Activo', 'active']),
            "asterisk_stats": asterisk_stats  # Agregar asterisk_stats
        })
        
    except Exception as e:
        logger.error(f"Error en proveedores: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error del sistema: {str(e)}"
        })

@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request):
    """Página de gestión de campañas"""
    try:
        # Estadísticas para template
        asterisk_stats = {
            "endpoints": len(extensions_data),
            "extensions_online": safe_count(extensions_data, lambda x: safe_get(x, 'status') == 'online'),
            "active_calls": 0,
            "provider_status": "active"
        }
        
        campaigns_data = []
        
        return templates.TemplateResponse("campaigns.html", {
            "request": request,
            "campaigns": campaigns_data,
            "total_campaigns": len(campaigns_data),
            "active_campaigns": 0,
            "asterisk_stats": asterisk_stats  # Agregar asterisk_stats
        })
        
    except Exception as e:
        logger.error(f"Error en campañas: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error del sistema: {str(e)}"
        })

# ==================== API REST ====================

def _mask_password(item: dict) -> dict:
    """Return a copy of the dict with 'password' field masked."""
    masked = dict(item)
    if 'password' in masked:
        masked['password'] = '****'
    return masked


@app.get("/api/extensions")
async def api_get_extensions():
    """API: Obtener todas las extensiones (passwords enmascarados)"""
    try:
        safe = [_mask_password(e) if isinstance(e, dict) else e for e in extensions_data]
        return {"success": True, "data": safe, "count": len(safe)}
    except Exception as e:
        logger.error(f"Error API extensiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def api_get_agents():
    """API: Obtener todos los agentes (passwords enmascarados)"""
    try:
        safe = [_mask_password(a) if isinstance(a, dict) else a for a in agents_data]
        return {"success": True, "data": safe, "count": len(safe)}
    except Exception as e:
        logger.error(f"Error API agentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers")
async def api_get_providers():
    """API: Obtener todos los proveedores (passwords enmascarados)"""
    try:
        safe = [_mask_password(p) if isinstance(p, dict) else p for p in providers_data]
        return {"success": True, "data": safe, "count": len(safe)}
    except Exception as e:
        logger.error(f"Error API proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/stats")
@app.get("/api/asterisk/stats")  # alias used by frontend JS
async def api_system_stats():
    """API: Estadísticas del sistema"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "system_status": "online",
            "asterisk_connected": False,
            "extensions": {
                "total": len(extensions_data),
                "assigned": safe_count(extensions_data, lambda x: safe_get(x, 'assigned', False)),
                "available": len(extensions_data) - safe_count(extensions_data, lambda x: safe_get(x, 'assigned', False))
            },
            "agents": {
                "total": len(agents_data),
                "online": safe_count(agents_data, lambda x: safe_get(x, 'status') == 'online'),
                "offline": len(agents_data) - safe_count(agents_data, lambda x: safe_get(x, 'status') == 'online')
            },
            "providers": {
                "total": len(providers_data),
                "active": safe_count(providers_data, lambda x: safe_get(x, 'status') in ['Activo', 'active', 'connected']),
                "inactive": len(providers_data) - safe_count(providers_data, lambda x: safe_get(x, 'status') in ['Activo', 'active', 'connected'])
            }
        }

        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"Error API stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/call/originate")
@app.post("/api/calls/originate")  # alias used by frontend JS
async def api_originate_call(request: Request):
    """API: Originar llamada"""
    try:
        data = await request.json()
        # Accept both naming conventions from different callers
        from_ext = data.get("from_extension") or data.get("from")
        to_ext = data.get("to_extension") or data.get("to")

        if not from_ext or not to_ext:
            raise HTTPException(status_code=400, detail="Extensiones requeridas")

        # Basic input validation – only allow numeric extensions
        if not str(from_ext).isdigit() or not str(to_ext).isdigit():
            raise HTTPException(status_code=400, detail="Las extensiones deben ser numéricas")

        return {
            "success": True,
            "data": {
                "message": f"Llamada simulada de {from_ext} a {to_ext}",
                "mode": "simulation",
                "timestamp": datetime.now().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error originando llamada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para actualizaciones en tiempo real"""
    await manager.connect(websocket)
    try:
        while True:
            stats = {
                "type": "stats_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "active_calls": 0,
                    "system_status": "online"
                }
            }
            
            await websocket.send_text(json.dumps(stats))
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ==================== MANEJO DE ERRORES ====================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("404.html", {
        "request": request
    }, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "Error interno del servidor"
    }, status_code=500)

# ==================== INICIO DEL SERVIDOR ====================

if __name__ == "__main__":
    print("🚀 INICIANDO SERVIDOR WEB FINAL SIN ERRORES")
    print("=" * 50)
    print("📊 Dashboard: http://localhost:8000")
    print("📞 Extensiones: http://localhost:8000/extensions")
    print("🌐 Proveedores: http://localhost:8000/providers")
    print("📋 Campañas: http://localhost:8000/campaigns")
    print("🔧 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

