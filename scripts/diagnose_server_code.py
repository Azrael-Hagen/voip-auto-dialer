
#!/usr/bin/env python3
# Diagnóstico directo del código del servidor

import re

def analyze_main_py():
    print("🔍 ANÁLISIS DIRECTO DE main.py")
    print("=" * 60)
    
    with open('/home/azrael/voip-auto-dialer/web/main.py', 'r') as f:
        content = f.read()
    
    print(f"📄 Archivo: {len(content)} caracteres")
    
    # Buscar función get_agents
    get_agents_matches = re.findall(r'@app\.get\("/api/agents"\).*?(?=@app\.|if __name__|$)', content, re.DOTALL)
    print(f"\n🔍 FUNCIÓN get_agents:")
    if get_agents_matches:
        for i, match in enumerate(get_agents_matches):
            print(f"   Coincidencia {i+1}:")
            lines = match.strip().split('\n')[:10]  # Primeras 10 líneas
            for line in lines:
                print(f"      {line}")
            if len(match.strip().split('\n')) > 10:
                print("      ...")
    else:
        print("   ❌ No se encontró función get_agents")
    
    # Buscar función create_agent
    create_agents_matches = re.findall(r'@app\.post\("/api/agents"\).*?(?=@app\.|if __name__|$)', content, re.DOTALL)
    print(f"\n🔍 FUNCIÓN create_agent:")
    if create_agents_matches:
        for i, match in enumerate(create_agents_matches):
            print(f"   Coincidencia {i+1}:")
            lines = match.strip().split('\n')[:10]  # Primeras 10 líneas
            for line in lines:
                print(f"      {line}")
            if len(match.strip().split('\n')) > 10:
                print("      ...")
    else:
        print("   ❌ No se encontró función create_agent")
    
    # Buscar todos los endpoints
    all_endpoints = re.findall(r'@app\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)
    print(f"\n📋 TODOS LOS ENDPOINTS:")
    for method, path in all_endpoints:
        print(f"   {method.upper():6} {path}")

def create_minimal_working_server():
    """Crear un servidor mínimo que funcione"""
    print(f"\n🔧 CREANDO SERVIDOR MÍNIMO FUNCIONAL")
    print("=" * 60)
    
    minimal_server = '''"""
Servidor web mínimo funcional para VoIP Auto Dialer
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

from core.logging_config import get_logger, log_system_event
from core.extension_manager import extension_manager
from core.agent_manager_clean import agent_manager

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
    """Página principal - Dashboard"""
    try:
        agents = agent_manager.get_all_agents()
        if not isinstance(agents, dict):
            agents = {}
        
        agent_count = len(agents)
        
        # Estadísticas de extensiones
        stats = extension_manager.get_extension_stats()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "agent_count": agent_count,
            "extension_stats": stats
        })
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "agent_count": 0,
            "extension_stats": {"total": 0, "assigned": 0, "available": 0}
        })

@app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """Página de gestión de agentes"""
    return templates.TemplateResponse("agents.html", {"request": request})

@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request):
    """Página de gestión de campañas"""
    return templates.TemplateResponse("campaigns.html", {"request": request})

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

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

@app.post("/api/agents/{agent_id}/assign-extension")
async def assign_extension(agent_id: str):
    """Asignar extensión a un agente"""
    try:
        result = agent_manager.assign_extension(agent_id)
        
        if result:
            logger.info(f"Extensión asignada a agente {agent_id}")
            return {"success": True, "message": "Extensión asignada correctamente", "result": result}
        else:
            raise HTTPException(status_code=400, detail="No se pudo asignar extensión")
            
    except Exception as e:
        logger.error(f"Error asignando extensión a {agent_id}: {e}")
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

# ============================================================================
# SERVIDOR
# ============================================================================

if __name__ == "__main__":
    log_system_event("Iniciando servidor web VoIP Auto Dialer")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
'''
    
    # Crear backup del archivo actual
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'/home/azrael/voip-auto-dialer/web/main.py.backup_minimal_{timestamp}'
    shutil.copy2('/home/azrael/voip-auto-dialer/web/main.py', backup_path)
    print(f"✅ Backup del archivo actual: {backup_path}")
    
    # Escribir servidor mínimo
    with open('/home/azrael/voip-auto-dialer/web/main.py', 'w') as f:
        f.write(minimal_server)
    
    print(f"✅ Servidor mínimo funcional creado")
    print(f"🔄 REINICIA EL SERVIDOR:")
    print(f"   Ctrl+C en el servidor actual")
    print(f"   python3 web/main.py")

def main():
    analyze_main_py()
    
    print(f"\n" + "=" * 60)
    response = input("¿Crear servidor mínimo funcional? (y/N): ")
    
    if response.lower() == 'y':
        create_minimal_working_server()
    else:
        print("⏸️  Creación de servidor mínimo cancelada")

if __name__ == "__main__":
    main()