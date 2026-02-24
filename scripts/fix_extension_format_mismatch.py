#!/usr/bin/env python3
# Reparar el desajuste de formato en extensiones

import json
import shutil
from datetime import datetime

def fix_extension_format():
    print("🔧 REPARANDO FORMATO DE EXTENSIONES")
    print("=" * 60)
    
    # Cargar datos actuales
    with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'r') as f:
        extensions = json.load(f)
    
    with open('/home/azrael/voip-auto-dialer/data/agents.json', 'r') as f:
        agents = json.load(f)
    
    # Encontrar extensiones realmente asignadas según agents.json
    really_assigned = set()
    for agent_id, agent in agents.items():
        ext_info = agent.get('extension_info')
        if ext_info and ext_info.get('extension'):
            really_assigned.add(ext_info['extension'])
    
    print(f"📋 Extensiones realmente asignadas según agents.json: {really_assigned}")
    
    # Crear backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'/home/azrael/voip-auto-dialer/data/extensions.json.backup_{timestamp}'
    shutil.copy2('/home/azrael/voip-auto-dialer/data/extensions.json', backup_path)
    print(f"✅ Backup creado: {backup_path}")
    
    # Convertir formato
    fixed_extensions = {}
    assigned_count = 0
    available_count = 0
    
    for ext_num, ext_data in extensions.items():
        # Crear nueva estructura estándar
        fixed_ext = {
            'extension': ext_num,
            'password': ext_data.get('password', 'defaultpass'),
            'assigned': ext_num in really_assigned,  # Usar la verdad de agents.json
            'server_ip': '127.0.0.1'
        }
        
        # Mantener información adicional si existe
        if 'display_name' in ext_data:
            fixed_ext['display_name'] = ext_data['display_name']
        if 'provider' in ext_data:
            fixed_ext['provider'] = ext_data['provider']
        
        # Solo mantener agent_id si realmente está asignada
        if ext_num in really_assigned and 'agent_id' in ext_data:
            fixed_ext['agent_id'] = ext_data['agent_id']
            fixed_ext['assigned_at'] = ext_data.get('assigned_at', datetime.now().isoformat())
        
        fixed_extensions[ext_num] = fixed_ext
        
        if fixed_ext['assigned']:
            assigned_count += 1
        else:
            available_count += 1
    
    # Guardar formato corregido
    with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'w') as f:
        json.dump(fixed_extensions, f, indent=2)
    
    print(f"✅ Formato corregido:")
    print(f"   🔢 Extensiones asignadas: {assigned_count}")
    print(f"   🆓 Extensiones disponibles: {available_count}")
    
    # Mostrar ejemplo del nuevo formato
    print(f"\n📋 EJEMPLO DEL NUEVO FORMATO:")
    first_assigned = None
    first_available = None
    
    for ext_num, ext_data in fixed_extensions.items():
        if ext_data['assigned'] and not first_assigned:
            first_assigned = (ext_num, ext_data)
        elif not ext_data['assigned'] and not first_available:
            first_available = (ext_num, ext_data)
        
        if first_assigned and first_available:
            break
    
    if first_assigned:
        print(f"   ✅ Asignada: {first_assigned[0]} = {first_assigned[1]}")
    if first_available:
        print(f"   🆓 Disponible: {first_available[0]} = {first_available[1]}")
    
    return True

def main():
    print("🔧 REPARACIÓN DE FORMATO DE EXTENSIONES")
    print("=" * 70)
    
    if fix_extension_format():
        print(f"\n✅ REPARACIÓN COMPLETADA")
        print(f"🔄 REINICIA EL SERVIDOR WEB:")
        print(f"   Ctrl+C en el servidor")
        print(f"   python3 web/main.py")
        print(f"\n🧪 DESPUÉS EJECUTA:")
        print(f"   python3 scripts/test_web_interface.py")
    else:
        print(f"\n❌ Error en la reparación")

if __name__ == "__main__":
    main()