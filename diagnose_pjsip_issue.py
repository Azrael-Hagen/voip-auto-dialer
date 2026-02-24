#!/usr/bin/env python3
"""
Diagnóstico completo del problema PJSIP
"""

import subprocess
import os
import json

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  🔍 {title}")
    print(f"{'='*60}")

def run_command(cmd, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: OK")
            if result.stdout.strip():
                print(f"   {result.stdout.strip()}")
            return True, result.stdout
        else:
            print(f"❌ {description}: FALLÓ")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False, str(e)

def check_file_content(filepath, description):
    """Verificar contenido de archivo"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: OK ({size} bytes)")
        
        # Mostrar primeras líneas si es archivo de configuración
        if filepath.endswith('.conf'):
            try:
                with open(filepath, 'r') as f:
                    lines = f.readlines()[:10]
                    print("   Primeras líneas:")
                    for i, line in enumerate(lines, 1):
                        print(f"   {i:2d}: {line.rstrip()}")
            except Exception as e:
                print(f"   Error leyendo archivo: {e}")
        return True
    else:
        print(f"❌ {description}: NO ENCONTRADO")
        return False

def main():
    print_header("DIAGNÓSTICO COMPLETO DEL PROBLEMA PJSIP")
    
    # 1. Verificar archivos de configuración
    print_header("1. ARCHIVOS DE CONFIGURACIÓN")
    
    config_files = [
        ("/etc/asterisk/pjsip.conf", "Archivo principal PJSIP"),
        ("/etc/asterisk/pjsip_extensions.conf", "Nuestras extensiones PJSIP"),
        ("/etc/asterisk/extensions.conf", "Archivo principal Extensions"),
        ("/etc/asterisk/extensions_voip.conf", "Nuestras extensiones VoIP"),
        ("asterisk_config/pjsip_extensions.conf", "Archivo local PJSIP"),
    ]
    
    for filepath, description in config_files:
        check_file_content(filepath, description)
    
    # 2. Verificar includes
    print_header("2. VERIFICANDO INCLUDES")
    
    # Verificar si nuestros archivos están incluidos
    run_command("sudo grep -n 'pjsip_extensions.conf' /etc/asterisk/pjsip.conf", 
                "Include PJSIP en pjsip.conf")
    
    run_command("sudo grep -n 'extensions_voip.conf' /etc/asterisk/extensions.conf", 
                "Include Extensions en extensions.conf")
    
    # 3. Verificar sintaxis de Asterisk
    print_header("3. VERIFICANDO SINTAXIS DE ASTERISK")
    
    run_command("sudo asterisk -rx 'module show like pjsip'", 
                "Módulos PJSIP cargados")
    
    run_command("sudo asterisk -rx 'pjsip show endpoints'", 
                "Endpoints PJSIP actuales")
    
    # 4. Verificar nuestros datos
    print_header("4. VERIFICANDO NUESTROS DATOS")
    
    # Cargar datos de extensiones
    try:
        with open('data/extensions.json', 'r') as f:
            extensions = json.load(f)
        
        assigned_extensions = [ext_id for ext_id, ext_data in extensions.items() 
                             if ext_data.get('status') == 'assigned']
        
        print(f"✅ Extensiones en nuestro sistema: {len(extensions)}")
        print(f"✅ Extensiones asignadas: {len(assigned_extensions)}")
        
        if assigned_extensions:
            print("   Primeras 5 extensiones asignadas:")
            for ext_id in assigned_extensions[:5]:
                ext_data = extensions[ext_id]
                print(f"   • {ext_id}: {ext_data.get('password', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Error cargando extensiones: {e}")
    
    # 5. Verificar permisos
    print_header("5. VERIFICANDO PERMISOS")
    
    run_command("sudo ls -la /etc/asterisk/pjsip_extensions.conf", 
                "Permisos archivo PJSIP")
    
    run_command("sudo ls -la /etc/asterisk/extensions_voip.conf", 
                "Permisos archivo Extensions")
    
    # 6. Verificar logs de Asterisk
    print_header("6. LOGS DE ASTERISK")
    
    # Buscar errores relacionados con PJSIP
    run_command("sudo journalctl -u asterisk --no-pager -n 10 | grep -i pjsip", 
                "Logs PJSIP recientes")
    
    print_header("DIAGNÓSTICO COMPLETADO")
    print("📋 PRÓXIMOS PASOS:")
    print("   1. Revisa los resultados arriba")
    print("   2. Identifica el problema específico")
    print("   3. Ejecuta el script de corrección correspondiente")

if __name__ == "__main__":
    main()