#!/usr/bin/env python3
# Archivo: ~/voip-auto-dialer/scripts/diagnose_current_state.py

import os
import subprocess
import json

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def check_file_content(filepath, description):
    print(f"\n--- {description} ---")
    if not os.path.exists(filepath):
        print(f"❌ {filepath} NO EXISTE")
        return False
    
    size = os.path.getsize(filepath)
    print(f"✅ {filepath} existe ({size} bytes)")
    
    # Mostrar primeras y últimas líneas
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            total_lines = len(lines)
            print(f"   📄 Total líneas: {total_lines}")
            
            if total_lines > 0:
                print("   🔝 Primeras 3 líneas:")
                for i, line in enumerate(lines[:3]):
                    print(f"      {i+1}: {line.rstrip()}")
                
                if total_lines > 6:
                    print("   ...")
                    print("   🔚 Últimas 3 líneas:")
                    for i, line in enumerate(lines[-3:], total_lines-2):
                        print(f"      {i}: {line.rstrip()}")
    except Exception as e:
        print(f"   ❌ Error leyendo archivo: {e}")
    
    return True

def main():
    print("🔍 DIAGNÓSTICO COMPLETO DEL ESTADO ACTUAL")
    print("=" * 60)
    
    # 1. Verificar estructura del proyecto
    print("\n1️⃣ ESTRUCTURA DEL PROYECTO:")
    project_files = [
        "~/voip-auto-dialer/data/extensions.json",
        "~/voip-auto-dialer/asterisk_config/pjsip_extensions.conf",
        "~/voip-auto-dialer/asterisk_config/extensions_voip.conf"
    ]
    
    for file_path in project_files:
        expanded_path = os.path.expanduser(file_path)
        if os.path.exists(expanded_path):
            size = os.path.getsize(expanded_path)
            print(f"   ✅ {file_path} ({size} bytes)")
        else:
            print(f"   ❌ {file_path} NO EXISTE")
    
    # 2. Verificar archivos en /etc/asterisk/
    print("\n2️⃣ ARCHIVOS EN /etc/asterisk/:")
    asterisk_files = [
        "/etc/asterisk/pjsip.conf",
        "/etc/asterisk/pjsip_extensions.conf", 
        "/etc/asterisk/extensions.conf",
        "/etc/asterisk/extensions_voip.conf"
    ]
    
    for file_path in asterisk_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size} bytes)")
        else:
            print(f"   ❌ {file_path} NO EXISTE")
    
    # 3. Analizar contenido de pjsip.conf
    check_file_content("/etc/asterisk/pjsip.conf", "CONTENIDO DE pjsip.conf")
    
    # 4. Verificar includes en pjsip.conf
    print("\n3️⃣ VERIFICANDO INCLUDES EN pjsip.conf:")
    try:
        with open("/etc/asterisk/pjsip.conf", 'r') as f:
            content = f.read()
            include_lines = [line.strip() for line in content.split('\n') if '#include' in line.lower()]
            if include_lines:
                print("   ✅ Includes encontrados:")
                for line in include_lines:
                    print(f"      {line}")
            else:
                print("   ❌ NO se encontraron includes")
    except Exception as e:
        print(f"   ❌ Error leyendo pjsip.conf: {e}")
    
    # 5. Verificar contenido de pjsip_extensions.conf
    check_file_content("/etc/asterisk/pjsip_extensions.conf", "CONTENIDO DE pjsip_extensions.conf")
    
    # 6. Contar extensiones en el archivo
    print("\n4️⃣ CONTANDO EXTENSIONES:")
    try:
        with open("/etc/asterisk/pjsip_extensions.conf", 'r') as f:
            content = f.read()
            # Contar secciones [XXXX] que parecen extensiones
            import re
            extensions = re.findall(r'\[(\d{4})\]', content)
            print(f"   📊 Extensiones encontradas en archivo: {len(extensions)}")
            if len(extensions) > 0:
                print(f"   🔢 Rango: {min(extensions)} - {max(extensions)}")
    except Exception as e:
        print(f"   ❌ Error contando extensiones: {e}")
    
    # 7. Estado de Asterisk
    print("\n5️⃣ ESTADO DE ASTERISK:")
    stdout, stderr, code = run_cmd("sudo systemctl status asterisk --no-pager -l")
    if code == 0:
        print("   ✅ Servicio Asterisk activo")
    else:
        print("   ❌ Problema con servicio Asterisk")
    
    # 8. Verificar módulos PJSIP
    print("\n6️⃣ MÓDULOS PJSIP:")
    stdout, stderr, code = run_cmd("sudo asterisk -rx 'module show like pjsip'")
    if code == 0:
        print("   📋 Módulos PJSIP cargados:")
        for line in stdout.split('\n'):
            if 'pjsip' in line.lower() and line.strip():
                print(f"      {line.strip()}")
    
    # 9. Verificar endpoints (el problema principal)
    print("\n7️⃣ ENDPOINTS PJSIP (PROBLEMA PRINCIPAL):")
    stdout, stderr, code = run_cmd("sudo asterisk -rx 'pjsip show endpoints'")
    print(f"   📤 Comando ejecutado (código: {code})")
    print(f"   📥 Salida: {stdout.strip()}")
    if stderr:
        print(f"   ⚠️  Error: {stderr.strip()}")
    
    # 10. Verificar transports
    print("\n8️⃣ TRANSPORTS PJSIP:")
    stdout, stderr, code = run_cmd("sudo asterisk -rx 'pjsip show transports'")
    print(f"   📤 Salida: {stdout.strip()}")
    
    # 11. Verificar logs de Asterisk
    print("\n9️⃣ ÚLTIMOS LOGS DE ASTERISK:")
    stdout, stderr, code = run_cmd("sudo tail -10 /var/log/asterisk/messages")
    if code == 0 and stdout.strip():
        print("   📋 Últimas 10 líneas del log:")
        for line in stdout.split('\n')[-5:]:  # Solo últimas 5 para no saturar
            if line.strip():
                print(f"      {line.strip()}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNÓSTICO COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    main()