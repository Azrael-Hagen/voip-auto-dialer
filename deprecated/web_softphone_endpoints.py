#!/usr/bin/env python3
"""
Endpoints web para descargar configuraciones de softphone
Agregar estas rutas a tu servidor web principal
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import json

router = APIRouter()

@router.get("/api/softphone-config/{agent_id}/{app_type}")
async def download_softphone_config(agent_id: str, app_type: str):
    """Descargar configuración de softphone para un agente"""
    
    # Validar tipo de aplicación
    valid_apps = ['zoiper', 'portsip', 'generic']
    if app_type not in valid_apps:
        raise HTTPException(status_code=400, detail="Tipo de aplicación no válido")
    
    # Buscar agente
    if not os.path.exists('data/agents.json'):
        raise HTTPException(status_code=404, detail="Datos de agentes no encontrados")
    
    with open('data/agents.json', 'r') as f:
        agents = json.load(f)
    
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agents[agent_id]
    extension_info = agent.get('extension_info')
    
    if not extension_info:
        raise HTTPException(status_code=400, detail="Agente sin extensión asignada")
    
    # Determinar archivo de configuración
    extension = extension_info['extension']
    
    if app_type == 'zoiper':
        filename = f"zoiper_config_{extension}.conf"
        content_type = "text/plain"
    elif app_type == 'portsip':
        filename = f"portsip_config_{extension}.xml"
        content_type = "application/xml"
    else:  # generic
        filename = f"sip_config_{extension}.txt"
        content_type = "text/plain"
    
    config_path = f"data/softphone_configs/{filename}"
    
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    # Retornar archivo
    return FileResponse(
        path=config_path,
        filename=filename,
        media_type=content_type
    )

# Agregar estas rutas a tu aplicación FastAPI principal:
# app.include_router(router)
