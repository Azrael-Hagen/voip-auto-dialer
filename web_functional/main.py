#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Union

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Importar integración AMI
from ami_integration import AsteriskAMIIntegration

# Configuración básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

# Funciones auxiliares para manejo seguro de datos
def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Obtener valor de forma segura, manejando tanto dict como str"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    elif isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, dict):
                return parsed.get(key, default)
        except (json.JSONDecodeError, TypeError):
            pass
    elif hasattr(obj, key):
        try:
            return getattr(obj, key, default)
        except (AttributeError, TypeError):
            pass
    return default

def ensure_dict(obj: Any) -> Dict[str, Any]:
    """Asegurar que el objeto sea un diccionario"""
    if isinstance(obj, dict):
        return obj
    elif isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    elif hasattr(obj, '__dict__'):
        try:
            return obj.__dict__
        except (AttributeError, TypeError):
            pass
    return {}

def ensure_list(obj: Any) -> List[Any]:
    """Asegurar que el objeto sea una lista"""
    if isinstance(obj, list):
        return obj
    elif isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, dict)):
        try:
            return list(obj)
        except (TypeError, AttributeError):
            pass
    return []

def safe_len(obj: Any) -> int:
    """Obtener longitud de forma segura"""
    try:
        if obj is None:
            return 0
        return len(obj) if hasattr(obj, '__len__') else 0
    except (TypeError, AttributeError):
        return 0

# Importar managers de forma segura
try:
    from core.extension_manager import extension_manager
    from core.provider_manager import provider_manager
    from core.logging_config import get_logger
    logger.info("✅ Managers importados correctamente")
except ImportError as e:
    logger.warning(f"⚠️ Error importando managers: {e}")
    
    # Crear managers mock para evitar errores
    class MockManager:
        def get_all_extensions(self): 
            try:
                with open("../data/extensions.json", "r") as f:
                    data = json.load(f)
                    return ensure_list(data)
            except:
                return []
        
        def get_all_providers(self): 
            try:
                with open("../data/providers.json", "r") as f:
                    data = json.load(f)
                    return ensure_list(data)
            except:
                return []
    
    extension_manager = MockManager()
    provider_manager = MockManager()

# Crear aplicación FastAPI
app = FastAPI(
    title="VoIP Auto Dialer",
    description="Sistema profesional de auto-marcado VoIP con Asterisk",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Instancia global de integración AMI
asterisk_ami = AsteriskAMIIntegration(
    host="localhost",
    port=5038,
    username="admin",
    password="secret"
)

# Manager de conexiones WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nueva conexión WebSocket: {len(self.active_connections)} activas")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Conexión WebSocket cerrada: {len(self.active_connections)} activas")

    async def broadcast(self, message: dict):
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # Limpiar conexiones muertas
            for conn in disconnected:
                self.disconnect(conn)

manager = ConnectionManager()

# Configurar callbacks AMI para WebSocket
async def ami_event_callback(event_data: Dict[str, Any]):
    """Callback para eventos AMI - reenviar via WebSocket"""
    await manager.broadcast(event_data)

# Agregar callbacks
asterisk_ami.add_event_callback('extension_status', ami_event_callback)
asterisk_ami.add_event_callback('call_event', ami_event_callback)
asterisk_ami.add_event_callback('provider_status', ami_event_callback)
asterisk_ami.add_event_callback('metrics_update', ami_event_callback)

# Rutas principales
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal con métricas en tiempo real"""
    try:
        # Obtener datos de managers locales
        extensions_raw = extension_manager.get_all_extensions()
        providers_raw = provider_manager.get_all_providers()
        
        extensions_list = ensure_list(extensions_raw)
        providers_list = ensure_list(providers_raw)
        
        # Obtener métricas reales de AMI
        ami_metrics = await asterisk_ami.get_metrics()
        
        # Combinar con datos locales
        total_extensions = max(len(extensions_list), ami_metrics.get('total_extensions', 0))
        extensions_with_passwords = len([e for e in extensions_list if ensure_dict(e).get('password')])
        
        # Obtener estado de extensiones desde AMI
        ami_extensions = await asterisk_ami.get_all_extensions_status()
        
        # Combinar datos locales con estado AMI
        combined_extensions = []
        for ext_data in extensions_list[:10]:  # Mostrar solo las primeras 10
            ext_dict = ensure_dict(ext_data)
            extension_num = str(ext_dict.get('extension', ''))
            
            # Obtener estado desde AMI
            ami_status = ami_extensions.get(extension_num)
            
            combined_ext = {
                'extension': extension_num,
                'password': ext_dict.get('password', 'N/A'),
                'name': ext_dict.get('name', 'N/A'),
                'email': ext_dict.get('email', 'N/A'),
                'status': ami_status.status if ami_status else 'offline',
                'contact': ami_status.contact if ami_status else None,
                'last_seen': ami_status.last_seen.isoformat() if ami_status and ami_status.last_seen else None
            }
            combined_extensions.append(combined_ext)
        
        context = {
            "request": request,
            "title": "Dashboard Profesional",
            "total_extensions": total_extensions,
            "extensions_with_passwords": extensions_with_passwords,
            "active_providers": len([p for p in providers_list if ensure_dict(p).get('active', False)]),
            "asterisk_stats": ami_metrics,
            "extensions": combined_extensions,
            "providers": providers_list,
            "system_status": "online" if asterisk_ami.connected else "offline"
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/extensions", response_class=HTMLResponse)
async def extensions_page(request: Request):
    """Página de gestión de extensiones"""
    try:
        extensions_raw = extension_manager.get_all_extensions()
        extensions_list = ensure_list(extensions_raw)
        
        # Obtener estado AMI
        ami_extensions = await asterisk_ami.get_all_extensions_status()
        ami_metrics = await asterisk_ami.get_metrics()
        
        # Combinar datos
        combined_extensions = []
        for ext_data in extensions_list:
            ext_dict = ensure_dict(ext_data)
            extension_num = str(ext_dict.get('extension', ''))
            
            ami_status = ami_extensions.get(extension_num)
            
            combined_ext = {
                'extension': extension_num,
                'password': ext_dict.get('password', 'N/A'),
                'name': ext_dict.get('name', 'N/A'),
                'email': ext_dict.get('email', 'N/A'),
                'status': ami_status.status if ami_status else 'offline',
                'contact': ami_status.contact if ami_status else None,
                'calls_active': ami_status.calls_active if ami_status else 0
            }
            combined_extensions.append(combined_ext)
        
        context = {
            "request": request,
            "title": "Gestión de Extensiones",
            "extensions": combined_extensions,
            "total_extensions": len(combined_extensions),
            "asterisk_stats": ami_metrics
        }
        
        return templates.TemplateResponse("extensions.html", context)
        
    except Exception as e:
        logger.error(f"Error en extensiones: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/providers", response_class=HTMLResponse)
async def providers_page(request: Request):
    """Página de gestión de proveedores VoIP"""
    try:
        providers_raw = provider_manager.get_all_providers()
        providers_list = ensure_list(providers_raw)
        
        ami_metrics = await asterisk_ami.get_metrics()
        
        # Actualizar estado del proveedor con datos AMI
        for provider in providers_list:
            provider_dict = ensure_dict(provider)
            if 'pbxonthecloud' in provider_dict.get('host', '').lower():
                provider_dict['ami_status'] = ami_metrics.get('provider_status', 'unknown')
        
        context = {
            "request": request,
            "title": "Gestión de Proveedores VoIP",
            "providers": providers_list,
            "total_providers": len(providers_list),
            "asterisk_stats": ami_metrics
        }
        
        return templates.TemplateResponse("providers.html", context)
        
    except Exception as e:
        logger.error(f"Error en proveedores: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request):
    """Página de campañas de auto-marcado"""
    try:
        ami_metrics = await asterisk_ami.get_metrics()
        active_calls = await asterisk_ami.get_active_calls()
        
        context = {
            "request": request,
            "title": "Campañas de Auto-Marcado",
            "asterisk_stats": ami_metrics,
            "active_calls": list(active_calls.values()),
            "campaigns": []  # Por implementar
        }
        
        return templates.TemplateResponse("campaigns.html", context)
        
    except Exception as e:
        logger.error(f"Error en campañas: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

# API REST con integración AMI
@app.get("/api/extensions")
async def api_get_extensions():
    """API para obtener todas las extensiones con estado AMI"""
    try:
        extensions_raw = extension_manager.get_all_extensions()
        extensions_list = ensure_list(extensions_raw)
        
        ami_extensions = await asterisk_ami.get_all_extensions_status()
        
        combined_extensions = []
        for ext_data in extensions_list:
            ext_dict = ensure_dict(ext_data)
            extension_num = str(ext_dict.get('extension', ''))
            
            ami_status = ami_extensions.get(extension_num)
            
            combined_ext = {
                'extension': extension_num,
                'password': ext_dict.get('password', 'N/A'),
                'name': ext_dict.get('name', 'N/A'),
                'email': ext_dict.get('email', 'N/A'),
                'status': ami_status.status if ami_status else 'offline',
                'contact': ami_status.contact if ami_status else None,
                'calls_active': ami_status.calls_active if ami_status else 0,
                'last_seen': ami_status.last_seen.isoformat() if ami_status and ami_status.last_seen else None
            }
            combined_extensions.append(combined_ext)
        
        return {
            "success": True,
            "data": combined_extensions,
            "count": len(combined_extensions)
        }
    except Exception as e:
        logger.error(f"Error API extensiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers")
async def api_get_providers():
    """API para obtener todos los proveedores con estado AMI"""
    try:
        providers_raw = provider_manager.get_all_providers()
        providers_list = ensure_list(providers_raw)
        
        ami_metrics = await asterisk_ami.get_metrics()
        
        for provider in providers_list:
            provider_dict = ensure_dict(provider)
            if 'pbxonthecloud' in provider_dict.get('host', '').lower():
                provider_dict['ami_status'] = ami_metrics.get('provider_status', 'unknown')
        
        return {
            "success": True,
            "data": providers_list,
            "count": len(providers_list)
        }
    except Exception as e:
        logger.error(f"Error API proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/asterisk/stats")
async def api_asterisk_stats():
    """API para obtener estadísticas reales de Asterisk via AMI"""
    try:
        stats = await asterisk_ami.get_metrics()
        return stats
    except Exception as e:
        logger.error(f"Error API stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calls/active")
async def api_active_calls():
    """API para obtener llamadas activas"""
    try:
        active_calls = await asterisk_ami.get_active_calls()
        calls_list = []
        
        for call in active_calls.values():
            calls_list.append({
                'call_id': call.call_id,
                'from_ext': call.from_ext,
                'to_ext': call.to_ext,
                'status': call.status,
                'start_time': call.start_time.isoformat(),
                'duration': call.duration
            })
        
        return {
            "success": True,
            "data": calls_list,
            "count": len(calls_list)
        }
    except Exception as e:
        logger.error(f"Error API llamadas activas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calls/originate")
async def api_originate_call(request: Request):
    """API para originar llamadas via AMI"""
    try:
        data = await request.json()
        from_ext = safe_get(data, 'from', '')
        to_ext = safe_get(data, 'to', '')
        
        if not from_ext or not to_ext:
            raise HTTPException(status_code=400, detail="Faltan parámetros from/to")
        
        # Usar AMI para originar llamada
        result = await asterisk_ami.originate_call(from_ext, to_ext)
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Error desconocido'))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error originando llamada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para actualizaciones en tiempo real"""
    await manager.connect(websocket)
    try:
        # Enviar estado inicial
        initial_metrics = await asterisk_ami.get_metrics()
        await websocket.send_text(json.dumps({
            "type": "metrics_update",
            "data": initial_metrics
        }))
        
        # Mantener conexión viva
        while True:
            await asyncio.sleep(30)
            
            # Enviar ping para mantener conexión
            await websocket.send_text(json.dumps({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error WebSocket: {e}")
        manager.disconnect(websocket)

# Manejadores de error
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {
        "request": request,
        "error": "Página no encontrada"
    }, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "Error interno del servidor"
    }, status_code=500)

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    """Inicializar conexión AMI al iniciar el servidor"""
    logger.info("🚀 Iniciando servidor VoIP Auto Dialer con integración AMI")
    
    # Conectar a AMI en background
    asyncio.create_task(asterisk_ami.connect())
    
    # Iniciar monitoreo continuo
    asyncio.create_task(asterisk_ami.start_monitoring())

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexión AMI al cerrar el servidor"""
    logger.info("🛑 Cerrando servidor VoIP Auto Dialer")
    await asterisk_ami.disconnect()

def main():
    """Función principal para iniciar el servidor"""
    print("🚀 VoIP Auto Dialer - Servidor Web con Integración AMI Completa")
    print("📊 Dashboard: http://localhost:8000")
    print("📞 Extensiones: http://localhost:8000/extensions")
    print("🌐 Proveedores: http://localhost:8000/providers")
    print("📋 Campañas: http://localhost:8000/campaigns")
    print("🔧 API Docs: http://localhost:8000/docs")
    print("🔌 AMI: Conectando a Asterisk en tiempo real...")
    print("\n⚡ Presiona Ctrl+C para detener\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
