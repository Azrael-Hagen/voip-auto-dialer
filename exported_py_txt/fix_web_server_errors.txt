#!/usr/bin/env python3
# Reparar errores en el servidor web

import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_file(file_path):
    """Crear backup de un archivo"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_main_py():
    """Reparar errores en main.py"""
    print("🔧 REPARANDO main.py")
    print("=" * 50)
    
    main_py_path = "/home/azrael/voip-auto-dialer/web/main.py"
    
    # Crear backup
    backup_path = backup_file(main_py_path)
    print(f"✅ Backup creado: {backup_path}")
    
    # Leer archivo actual
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Buscar y reparar errores comunes
    fixes_applied = []
    
    # Fix 1: Reparar el endpoint de API agents
    if "def get_agents():" in content:
        # Buscar la función problemática
        old_pattern = '''@app.get("/api/agents")
async def get_agents():
    """Obtener todos los agentes"""
    try:
        agents = agent_manager.get_all_agents()
        return agents
    except Exception as e:
        logger.error(f"Error obteniendo agentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))'''
        
        new_pattern = '''@app.get("/api/agents")
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
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            fixes_applied.append("API agents endpoint")
    
    # Fix 2: Reparar el endpoint de creación de agentes
    if "def create_agent(" in content:
        # Buscar patrón de creación de agente
        import re
        pattern = r'(@app\.post\("/api/agents"\)\s*async def create_agent\([^}]+})'
        
        # Reemplazar con versión corregida
        new_create_agent = '''@app.post("/api/agents")
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
        
        # Buscar y reemplazar la función completa
        match = re.search(r'@app\.post\("/api/agents"\)\s*async def create_agent\([^}]+\n    except[^}]+}', content, re.DOTALL)
        if match:
            content = content.replace(match.group(0), new_create_agent)
            fixes_applied.append("Create agent endpoint")
    
    # Fix 3: Agregar método get_available_extensions si no existe
    if "get_available_extensions" not in content:
        # Agregar endpoint para extensiones disponibles
        extensions_endpoint = '''
@app.get("/api/extensions/available")
async def get_available_extensions():
    """Obtener extensiones disponibles"""
    try:
        # Cargar extensiones desde el archivo
        import json
        extensions_file = project_root / "data" / "extensions.json"
        
        with open(extensions_file, 'r') as f:
            extensions = json.load(f)
        
        # Filtrar solo las disponibles
        available = []
        for ext_num, ext_data in extensions.items():
            if isinstance(ext_data, dict) and not ext_data.get('assigned', False):
                available.append(ext_num)
            elif not isinstance(ext_data, dict):
                # Formato antiguo, asumir disponible
                available.append(ext_num)
        
        return {
            "available_extensions": available,
            "count": len(available)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo extensiones disponibles: {e}")
        raise HTTPException(status_code=500, detail=str(e))
'''
        
        # Insertar antes de la función main
        main_function_pos = content.find("if __name__ == \"__main__\":")
        if main_function_pos > 0:
            content = content[:main_function_pos] + extensions_endpoint + "\n\n" + content[main_function_pos:]
            fixes_applied.append("Available extensions endpoint")
    
    # Guardar archivo reparado
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Reparaciones aplicadas: {fixes_applied}")
    return len(fixes_applied) > 0

def add_extension_manager_method():
    """Agregar método faltante al ExtensionManager"""
    print(f"\n🔧 REPARANDO ExtensionManager")
    print("=" * 50)
    
    extension_manager_path = "/home/azrael/voip-auto-dialer/core/extension_manager.py"
    
    # Crear backup
    backup_path = backup_file(extension_manager_path)
    print(f"✅ Backup creado: {backup_path}")
    
    # Leer archivo
    with open(extension_manager_path, 'r') as f:
        content = f.read()
    
    # Verificar si el método ya existe
    if "def get_available_extensions(" in content:
        print("✅ Método get_available_extensions ya existe")
        return True
    
    # Agregar el método faltante
    new_method = '''
    def get_available_extensions(self):
        """Obtener lista de extensiones disponibles"""
        try:
            available = []
            for ext_num, ext_data in self.extensions.items():
                if isinstance(ext_data, dict):
                    if not ext_data.get('assigned', False):
                        available.append(ext_num)
                else:
                    # Formato antiguo, verificar si está asignada
                    # Por ahora asumir disponible si no está en formato dict
                    available.append(ext_num)
            
            self.logger.info(f"Extensiones disponibles encontradas: {len(available)}")
            return available
            
        except Exception as e:
            self.logger.error(f"Error obteniendo extensiones disponibles: {e}")
            return []
    
    def get_extension_stats(self):
        """Obtener estadísticas de extensiones"""
        try:
            total = len(self.extensions)
            assigned = 0
            available = 0
            
            for ext_num, ext_data in self.extensions.items():
                if isinstance(ext_data, dict) and ext_data.get('assigned', False):
                    assigned += 1
                else:
                    available += 1
            
            return {
                'total': total,
                'assigned': assigned,
                'available': available,
                'utilization': (assigned / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {'total': 0, 'assigned': 0, 'available': 0, 'utilization': 0}
'''
    
    # Buscar el final de la clase (antes del último método o del final del archivo)
    class_end_pattern = r'(\n\s+def [^:]+:[^}]+\n\s+except[^}]+\n[^}]+\n)'
    import re
    matches = list(re.finditer(class_end_pattern, content))
    
    if matches:
        # Insertar después del último método
        last_match = matches[-1]
        insert_pos = last_match.end()
        content = content[:insert_pos] + new_method + content[insert_pos:]
    else:
        # Insertar antes del final de la clase
        class_end = content.rfind("# Fin de ExtensionManager")
        if class_end > 0:
            content = content[:class_end] + new_method + "\n    " + content[class_end:]
        else:
            # Insertar al final del archivo
            content += new_method
    
    # Guardar archivo
    with open(extension_manager_path, 'w') as f:
        f.write(content)
    
    print("✅ Métodos agregados al ExtensionManager")
    return True

def main():
    print("🔧 REPARACIÓN DE ERRORES DEL SERVIDOR WEB")
    print("=" * 70)
    
    success = True
    
    # Reparar main.py
    if not fix_main_py():
        print("❌ Error reparando main.py")
        success = False
    
    # Reparar extension_manager.py
    if not add_extension_manager_method():
        print("❌ Error reparando extension_manager.py")
        success = False
    
    if success:
        print(f"\n✅ TODAS LAS REPARACIONES COMPLETADAS")
        print(f"🔄 PRÓXIMOS PASOS:")
        print(f"1. Reiniciar el servidor web:")
        print(f"   Ctrl+C en el servidor actual")
        print(f"   python3 web/main.py")
        print(f"2. Probar la creación de agentes en http://localhost:8000/agents")
    else:
        print(f"\n❌ Algunas reparaciones fallaron")

if __name__ == "__main__":
    main()

