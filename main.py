#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configuración básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

# Mock managers para evitar errores de import
class MockManager:
    def get_all_extensions(self): 
        try:
            with open("../data/extensions.json", "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except:
            return []
    
    def get_all_providers(self): 
        try:
            with open("../data/providers.json", "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except:
            return []

extension_manager = MockManager()
provider_manager = MockManager()

# Crear aplicación FastAPI
app = FastAPI(title="VoIP Auto Dialer", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Funciones auxiliares
def safe_get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def safe_len(obj):
    try:
        return len(obj) if obj else 0
    except:
        return 0

# Rutas principales
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        extensions = extension_manager.get_all_extensions()
        providers = provider_manager.get_all_providers()
        
        # Asegurar que sean listas
        if not isinstance(extensions, list):
            extensions = []
        if not isinstance(providers, list):
            providers = []
        
        # Calcular métricas de forma segura
        total_extensions = len(extensions)
        extensions_with_passwords = 0
        
        for ext in extensions:
            if isinstance(ext, dict) and ext.get('password'):
                extensions_with_passwords += 1
        
        active_providers = 0
        for provider in providers:
            if isinstance(provider, dict) and provider.get('active', False):
                active_providers += 1
        
        asterisk_stats = {
            "endpoints": 521,
            "active_calls": 0,
            "extensions_online": 0,
            "provider_status": "unknown"
        }
        
        context = {
            "request": request,
            "title": "Dashboard Profesional",
            "total_extensions": total_extensions,
            "extensions_with_passwords": extensions_with_passwords,
            "active_providers": active_providers,
            "asterisk_stats": asterisk_stats,
            "extensions": extensions[:10],
            "providers": providers,
            "system_status": "online"
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/extensions", response_class=HTMLResponse)
async def extensions_page(request: Request):
    try:
        extensions = extension_manager.get_all_extensions()
        if not isinstance(extensions, list):
            extensions = []
        
        asterisk_stats = {
            "endpoints": 521,
            "active_calls": 0,
            "extensions_online": 0,
            "provider_status": "unknown"
        }
        
        context = {
            "request": request,
            "title": "Gestión de Extensiones",
            "extensions": extensions,
            "total_extensions": len(extensions),
            "asterisk_stats": asterisk_stats
        }
        
        return templates.TemplateResponse("extensions.html", context)
        
    except Exception as e:
        logger.error(f"Error en extensiones: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/providers", response_class=HTMLResponse)
async def providers_page(request: Request):
    try:
        providers = provider_manager.get_all_providers()
        if not isinstance(providers, list):
            providers = []
        
        asterisk_stats = {
            "endpoints": 521,
            "active_calls": 0,
            "extensions_online": 0,
            "provider_status": "rejected"
        }
        
        context = {
            "request": request,
            "title": "Gestión de Proveedores VoIP",
            "providers": providers,
            "total_providers": len(providers),
            "asterisk_stats": asterisk_stats
        }
        
        return templates.TemplateResponse("providers.html", context)
        
    except Exception as e:
        logger.error(f"Error en proveedores: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request):
    try:
        asterisk_stats = {
            "endpoints": 521,
            "active_calls": 0,
            "extensions_online": 0,
            "provider_status": "unknown"
        }
        
        context = {
            "request": request,
            "title": "Campañas de Auto-Marcado",
            "asterisk_stats": asterisk_stats,
            "campaigns": []
        }
        
        return templates.TemplateResponse("campaigns.html", context)
        
    except Exception as e:
        logger.error(f"Error en campañas: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

# API REST básica
@app.get("/api/extensions")
async def api_get_extensions():
    try:
        extensions = extension_manager.get_all_extensions()
        if not isinstance(extensions, list):
            extensions = []
        return {"success": True, "data": extensions, "count": len(extensions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers")
async def api_get_providers():
    try:
        providers = provider_manager.get_all_providers()
        if not isinstance(providers, list):
            providers = []
        return {"success": True, "data": providers, "count": len(providers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

def main():
    print("🚀 VoIP Auto Dialer - Servidor Web (Versión Corregida)")
    print("📊 Dashboard: http://localhost:8000")
    print("📞 Extensiones: http://localhost:8000/extensions")
    print("🌐 Proveedores: http://localhost:8000/providers")
    print("📋 Campañas: http://localhost:8000/campaigns")
    print("\n⚡ Presiona Ctrl+C para detener\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

if __name__ == "__main__":
    main()
