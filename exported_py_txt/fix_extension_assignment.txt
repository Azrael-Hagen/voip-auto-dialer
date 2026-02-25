#!/usr/bin/env python3
# Reparar el sistema de asignación de extensiones

import json
import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.extension_manager import extension_manager
from core.agent_manager_clean import agent_manager

def analyze_extension_problem():
    """Analizar el problema de extensiones"""
    print("🔍 ANÁLISIS DEL PROBLEMA DE EXTENSIONES")
    print("=" * 60)
    
    # 1. Cargar datos actuales
    try:
        with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'r') as f:
            extensions_data = json.load(f)
        print(f"✅ Extensiones en archivo: {len(extensions_data)}")
    except Exception as e:
        print(f"❌ Error cargando extensions.json: {e}")
        return False
    
    try:
        with open('/home/azrael/voip-auto-dialer/data/agents.json', 'r') as f:
            agents_data = json.load(f)
        print(f"✅ Agentes en archivo: {len(agents_data)}")
    except Exception as e:
        print(f"❌ Error cargando agents.json: {e}")
        return False
    
    # 2. Analizar asignaciones reales
    print(f"\n📊 ANÁLISIS DE ASIGNACIONES:")
    
    assigned_extensions = []
    agents_with_extensions = []
    
    for agent_id, agent in agents_data.items():
        ext_info = agent.get('extension_info')
        if ext_info and ext_info.get('extension'):
            extension_num = ext_info['extension']
            assigned_extensions.append(extension_num)
            agents_with_extensions.append(f"{agent['name']} -> {extension_num}")
    
    print(f"   🔢 Extensiones realmente asignadas: {len(assigned_extensions)}")
    for assignment in agents_with_extensions:
        print(f"      {assignment}")
    
    # 3. Verificar estado en extensions.json
    assigned_in_file = 0
    available_in_file = 0
    
    for ext_num, ext_data in extensions_data.items():
        if isinstance(ext_data, dict) and ext_data.get('assigned'):
            assigned_in_file += 1
        else:
            available_in_file += 1
    
    print(f"\n📋 ESTADO EN extensions.json:")
    print(f"   ✅ Marcadas como asignadas: {assigned_in_file}")
    print(f"   🆓 Marcadas como disponibles: {available_in_file}")
    
    # 4. Identificar el problema
    print(f"\n🎯 DIAGNÓSTICO:")
    if assigned_in_file == len(extensions_data) and len(assigned_extensions) == 1:
        print("   ❌ PROBLEMA: Todas las extensiones están marcadas como asignadas")
        print("   💡 CAUSA: Error en el sistema de tracking de asignaciones")
        print("   🔧 SOLUCIÓN: Resetear el estado de asignaciones")
        return True
    
    return False

def fix_extension_assignments():
    """Reparar las asignaciones de extensiones"""
    print(f"\n🔧 REPARANDO ASIGNACIONES DE EXTENSIONES")
    print("=" * 60)
    
    # 1. Cargar datos
    with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'r') as f:
        extensions_data = json.load(f)
    
    with open('/home/azrael/voip-auto-dialer/data/agents.json', 'r') as f:
        agents_data = json.load(f)
    
    # 2. Crear lista de extensiones realmente asignadas
    really_assigned = set()
    for agent_id, agent in agents_data.items():
        ext_info = agent.get('extension_info')
        if ext_info and ext_info.get('extension'):
            really_assigned.add(ext_info['extension'])
    
    print(f"   📋 Extensiones realmente asignadas: {really_assigned}")
    
    # 3. Resetear todas las extensiones
    fixed_extensions = {}
    for ext_num, ext_data in extensions_data.items():
        if ext_num in really_assigned:
            # Mantener como asignada
            if isinstance(ext_data, dict):
                fixed_extensions[ext_num] = ext_data
                fixed_extensions[ext_num]['assigned'] = True
            else:
                # Crear estructura correcta
                fixed_extensions[ext_num] = {
                    'extension': ext_num,
                    'password': ext_data if isinstance(ext_data, str) else 'defaultpass',
                    'assigned': True,
                    'server_ip': '127.0.0.1'
                }
        else:
            # Marcar como disponible
            if isinstance(ext_data, dict):
                fixed_extensions[ext_num] = ext_data
                fixed_extensions[ext_num]['assigned'] = False
            else:
                # Crear estructura correcta
                fixed_extensions[ext_num] = {
                    'extension': ext_num,
                    'password': ext_data if isinstance(ext_data, str) else 'defaultpass',
                    'assigned': False,
                    'server_ip': '127.0.0.1'
                }
    
    # 4. Guardar backup y archivo corregido
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'/home/azrael/voip-auto-dialer/data/extensions.json.backup_{timestamp}'
    
    shutil.copy2('/home/azrael/voip-auto-dialer/data/extensions.json', backup_path)
    print(f"   ✅ Backup creado: {backup_path}")
    
    with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'w') as f:
        json.dump(fixed_extensions, f, indent=2)
    
    print(f"   ✅ Archivo extensions.json corregido")
    
    # 5. Verificar resultado
    assigned_count = sum(1 for ext in fixed_extensions.values() if ext.get('assigned', False))
    available_count = len(fixed_extensions) - assigned_count
    
    print(f"   📊 Resultado:")
    print(f"      🔢 Extensiones asignadas: {assigned_count}")
    print(f"      🆓 Extensiones disponibles: {available_count}")
    
    return True

def main():
    print("🔧 REPARACIÓN DEL SISTEMA DE EXTENSIONES")
    print("=" * 80)
    
    # Analizar el problema
    if analyze_extension_problem():
        print(f"\n" + "=" * 60)
        response = input("¿Proceder con la reparación? (y/N): ")
        
        if response.lower() == 'y':
            if fix_extension_assignments():
                print(f"\n✅ REPARACIÓN COMPLETADA")
                print(f"💡 Ahora deberías poder asignar extensiones a los agentes")
                print(f"🔄 Reinicia el servidor web para aplicar los cambios:")
                print(f"   Ctrl+C en el servidor actual")
                print(f"   python3 web/main.py")
            else:
                print(f"\n❌ Error en la reparación")
        else:
            print(f"\n⏸️  Reparación cancelada")
    else:
        print(f"\n❌ No se pudo identificar el problema claramente")

if __name__ == "__main__":
    main()