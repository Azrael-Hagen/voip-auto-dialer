
#!/usr/bin/env python3
# Debug específico del problema de extensiones

import json
import sys
from pathlib import Path

def debug_extensions():
    print("🔍 DEBUG ESPECÍFICO DE EXTENSIONES")
    print("=" * 60)
    
    # Cargar extensions.json
    with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'r') as f:
        extensions = json.load(f)
    
    print(f"📊 Total extensiones: {len(extensions)}")
    
    # Analizar estructura de las primeras 5 extensiones
    print(f"\n🔍 ESTRUCTURA DE DATOS:")
    for i, (ext_num, ext_data) in enumerate(list(extensions.items())[:5]):
        print(f"   {ext_num}: {type(ext_data)} = {ext_data}")
    
    # Contar tipos
    dict_count = 0
    str_count = 0
    assigned_count = 0
    
    for ext_num, ext_data in extensions.items():
        if isinstance(ext_data, dict):
            dict_count += 1
            if ext_data.get('assigned', False):
                assigned_count += 1
        elif isinstance(ext_data, str):
            str_count += 1
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"   📋 Formato dict: {dict_count}")
    print(f"   📝 Formato string: {str_count}")
    print(f"   ✅ Marcadas como asignadas: {assigned_count}")
    
    # El problema: si todas son strings, el sistema las cuenta como asignadas
    if str_count == len(extensions):
        print(f"\n🎯 PROBLEMA IDENTIFICADO:")
        print(f"   ❌ Todas las extensiones están en formato string")
        print(f"   ❌ El sistema las interpreta como asignadas")
        print(f"   💡 SOLUCIÓN: Convertir a formato dict con campo 'assigned'")
        return True
    
    return False

def fix_extensions_format():
    print(f"\n🔧 CONVIRTIENDO FORMATO DE EXTENSIONES")
    print("=" * 60)
    
    # Cargar datos
    with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'r') as f:
        extensions = json.load(f)
    
    with open('/home/azrael/voip-auto-dialer/data/agents.json', 'r') as f:
        agents = json.load(f)
    
    # Encontrar extensiones realmente asignadas
    assigned_extensions = set()
    for agent_id, agent in agents.items():
        ext_info = agent.get('extension_info')
        if ext_info and ext_info.get('extension'):
            assigned_extensions.add(ext_info['extension'])
    
    print(f"   🔢 Extensiones realmente asignadas: {assigned_extensions}")
    
    # Convertir formato
    fixed_extensions = {}
    for ext_num, ext_data in extensions.items():
        if isinstance(ext_data, str):
            # Convertir de string a dict
            fixed_extensions[ext_num] = {
                'extension': ext_num,
                'password': ext_data,
                'assigned': ext_num in assigned_extensions,
                'server_ip': '127.0.0.1'
            }
        else:
            # Ya es dict, solo actualizar assigned
            fixed_extensions[ext_num] = ext_data.copy()
            fixed_extensions[ext_num]['assigned'] = ext_num in assigned_extensions
    
    # Crear backup
    import shutil
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'/home/azrael/voip-auto-dialer/data/extensions.json.backup_{timestamp}'
    shutil.copy2('/home/azrael/voip-auto-dialer/data/extensions.json', backup_path)
    print(f"   ✅ Backup: {backup_path}")
    
    # Guardar formato corregido
    with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'w') as f:
        json.dump(fixed_extensions, f, indent=2)
    
    # Verificar resultado
    assigned = sum(1 for ext in fixed_extensions.values() if ext.get('assigned', False))
    available = len(fixed_extensions) - assigned
    
    print(f"   ✅ Conversión completada:")
    print(f"      🔢 Asignadas: {assigned}")
    print(f"      🆓 Disponibles: {available}")
    
    return True

def main():
    if debug_extensions():
        response = input("\n¿Proceder con la corrección? (y/N): ")
        if response.lower() == 'y':
            fix_extensions_format()
            print(f"\n✅ CORRECCIÓN COMPLETADA")
            print(f"🔄 REINICIA EL SERVIDOR WEB PARA APLICAR CAMBIOS")
        else:
            print(f"\n⏸️  Corrección cancelada")

if __name__ == "__main__":
    main()