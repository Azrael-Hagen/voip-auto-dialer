
#!/usr/bin/env python3
# Reparar los errores restantes del servidor web

import os
import re
import shutil
from datetime import datetime

def fix_agent_api_error():
    """Reparar el error 'bool' object has no attribute 'get'"""
    print("🔧 REPARANDO ERROR DE API AGENTES")
    print("=" * 50)
    
    main_py_path = "/home/azrael/voip-auto-dialer/web/main.py"
    
    # Crear backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{main_py_path}.backup_{timestamp}"
    shutil.copy2(main_py_path, backup_path)
    print(f"✅ Backup: {backup_path}")
    
    # Leer archivo
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Buscar y reparar la función get_agents
    old_pattern = '''@app.get("/api/agents")
async def get_agents():
    """Obtener todos los agentes"""
    try:
        agents = agent_manager.get_all_agents()
        # Asegurar que agents es un diccionario
        if not isinstance(agents, dict):
            agents = {}
        return agents
    except Exception as e:
        logger.error(f"Error obteniendo agentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))'''
    
    new_pattern = '''@app.get("/api/agents")
async def get_agents():
    """Obtener todos los agentes"""
    try:
        agents = agent_manager.get_all_agents()
        
        # Asegurar que agents es un diccionario válido
        if not isinstance(agents, dict):
            logger.warning(f"get_all_agents devolvió tipo inesperado: {type(agents)}")
            agents = {}
        
        # Verificar que cada agente es un diccionario válido
        valid_agents = {}
        for agent_id, agent_data in agents.items():
            if isinstance(agent_data, dict):
                valid_agents[agent_id] = agent_data
            else:
                logger.warning(f"Agente {agent_id} tiene datos inválidos: {type(agent_data)}")
        
        return valid_agents
        
    except Exception as e:
        logger.error(f"Error obteniendo agentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("✅ Función get_agents reparada")
    else:
        # Buscar patrón más general
        pattern = r'@app\.get\("/api/agents"\)\s*async def get_agents\(\):[^}]+except[^}]+}'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = content.replace(match.group(0), new_pattern)
            print("✅ Función get_agents reparada (patrón general)")
        else:
            print("⚠️  No se encontró la función get_agents para reparar")
    
    # Reparar función create_agent
    create_agent_pattern = '''@app.post("/api/agents")
async def create_agent(agent: AgentCreate):
    """Crear un nuevo agente"""
    try:
        # Crear agente usando el manager
        agent_data = {
            "name": agent.name,
            "email": agent.email,
            "phone": agent.phone
        }
        
        new_agent = agent_manager.create_agent(**agent_data)
        
        # Asegurar que el agente tiene un ID
        if not new_agent or 'id' not in new_agent:
            raise HTTPException(status_code=500, detail="Error creando agente: ID no generado")
        
        logger.info(f"Agente creado: {new_agent['id']}")
        return new_agent
        
    except Exception as e:
        logger.error(f"Error creando agente: {e}")
        raise HTTPException(status_code=500, detail=str(e))'''
    
    # Buscar función create_agent existente
    create_pattern = r'@app\.post\("/api/agents"\)\s*async def create_agent\([^}]+except[^}]+}'
    match = re.search(create_pattern, content, re.DOTALL)
    if match:
        content = content.replace(match.group(0), create_agent_pattern)
        print("✅ Función create_agent reparada")
    else:
        # Si no existe, agregarla
        # Buscar donde insertar (antes de main)
        main_pos = content.find('if __name__ == "__main__":')
        if main_pos > 0:
            content = content[:main_pos] + create_agent_pattern + "\n\n" + content[main_pos:]
            print("✅ Función create_agent agregada")
    
    # Guardar archivo reparado
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    return True

def verify_agent_manager():
    """Verificar que el AgentManager funciona correctamente"""
    print(f"\n🔍 VERIFICANDO AGENT MANAGER")
    print("=" * 50)
    
    try:
        import sys
        from pathlib import Path
        project_root = Path("/home/azrael/voip-auto-dialer")
        sys.path.insert(0, str(project_root))
        
        from core.agent_manager_clean import agent_manager
        
        # Test básico
        agents = agent_manager.get_all_agents()
        print(f"✅ get_all_agents() funciona: {type(agents)} con {len(agents) if isinstance(agents, dict) else 'N/A'} agentes")
        
        # Test de creación
        test_agent_data = {
            "name": "Test Agent Verification",
            "email": "test@verify.com",
            "phone": "+1234567890"
        }
        
        new_agent = agent_manager.create_agent(**test_agent_data)
        if new_agent and 'id' in new_agent:
            print(f"✅ create_agent() funciona: ID {new_agent['id']} generado")
            return True
        else:
            print(f"❌ create_agent() falla: {new_agent}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando AgentManager: {e}")
        return False

def main():
    print("🔧 REPARACIÓN FINAL DE ERRORES DEL SERVIDOR")
    print("=" * 70)
    
    success = True
    
    # Reparar errores de API
    if not fix_agent_api_error():
        success = False
    
    # Verificar AgentManager
    if not verify_agent_manager():
        success = False
    
    if success:
        print(f"\n✅ TODAS LAS REPARACIONES COMPLETADAS")
        print(f"🔄 REINICIA EL SERVIDOR WEB:")
        print(f"   Ctrl+C en el servidor actual")
        print(f"   python3 web/main.py")
        print(f"\n🧪 DESPUÉS EJECUTA:")
        print(f"   python3 scripts/test_web_interface.py")
        print(f"\n🌐 PRUEBA EN EL NAVEGADOR:")
        print(f"   http://localhost:8000/agents")
    else:
        print(f"\n❌ Algunas reparaciones fallaron")

if __name__ == "__main__":
    main()