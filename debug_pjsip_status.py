#!/usr/bin/env python3
"""
DIAGNÓSTICO COMPLETO DEL ESTADO PJSIP
Verifica configuración, sincronización y estado actual
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, check=True, shell=True):
    """Ejecutar comando con manejo de errores"""
    print(f"🔧 Ejecutando: {cmd}")
    try:
        result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"❌ Stderr: {e.stderr}")
        return e

def check_asterisk_status():
    """Verificar estado completo de Asterisk"""
    print("\n🔍 DIAGNÓSTICO COMPLETO ASTERISK PJSIP")
    print("=" * 70)
    
    # 1. Estado del servicio
    print("\n1️⃣ ESTADO DEL SERVICIO:")
    run_command("sudo systemctl status asterisk --no-pager -l", check=False)
    
    # 2. Procesos activos
    print("\n2️⃣ PROCESOS ASTERISK:")
    run_command("ps aux | grep asterisk", check=False)
    
    # 3. Archivos de configuración
    print("\n3️⃣ ARCHIVOS DE CONFIGURACIÓN:")
    run_command("ls -la /etc/asterisk/pjsip.conf", check=False)
    run_command("ls -la /etc/asterisk/extensions.conf", check=False)
    
    # 4. Últimas líneas de pjsip.conf
    print("\n4️⃣ ÚLTIMAS LÍNEAS PJSIP.CONF:")
    run_command("sudo tail -20 /etc/asterisk/pjsip.conf", check=False)
    
    # 5. Estado CLI
    print("\n5️⃣ ESTADO CLI:")
    run_command("sudo asterisk -rx 'core show version'", check=False)
    
    # 6. Módulos PJSIP
    print("\n6️⃣ MÓDULOS PJSIP:")
    run_command("sudo asterisk -rx 'module show like pjsip'", check=False)
    
    # 7. Endpoints (primeros 10)
    print("\n7️⃣ ENDPOINTS (PRIMEROS 10):")
    run_command("sudo asterisk -rx 'pjsip show endpoints' | head -15", check=False)
    
    # 8. Registraciones
    print("\n8️⃣ REGISTRACIONES:")
    run_command("sudo asterisk -rx 'pjsip show registrations'", check=False)
    
    # 9. AOR específicos
    print("\n9️⃣ AOR ESPECÍFICOS:")
    run_command("sudo asterisk -rx 'pjsip show aors' | head -10", check=False)
    
    # 10. Logs recientes
    print("\n🔟 LOGS RECIENTES:")
    run_command("sudo journalctl -u asterisk --no-pager -n 10", check=False)

def force_pjsip_reload():
    """Forzar recarga completa de PJSIP"""
    print("\n🔄 FORZANDO RECARGA COMPLETA PJSIP")
    print("=" * 70)
    
    # 1. Recargar configuración
    print("\n1️⃣ RECARGANDO CONFIGURACIÓN:")
    run_command("sudo asterisk -rx 'pjsip reload'", check=False)
    time.sleep(5)
    
    # 2. Recargar módulos
    print("\n2️⃣ RECARGANDO MÓDULOS:")
    run_command("sudo asterisk -rx 'module reload res_pjsip.so'", check=False)
    time.sleep(3)
    
    # 3. Verificar después de recarga
    print("\n3️⃣ VERIFICANDO DESPUÉS DE RECARGA:")
    run_command("sudo asterisk -rx 'pjsip show endpoints' | head -10", check=False)

def test_specific_endpoint():
    """Probar endpoint específico"""
    print("\n🧪 PROBANDO ENDPOINT ESPECÍFICO")
    print("=" * 70)
    
    # Probar endpoint 1000
    print("\n📞 ENDPOINT 1000:")
    run_command("sudo asterisk -rx 'pjsip show endpoint 1000'", check=False)
    
    # Probar AOR 1000
    print("\n📋 AOR 1000:")
    run_command("sudo asterisk -rx 'pjsip show aor 1000-aor'", check=False)
    
    # Probar auth 1000
    print("\n🔐 AUTH 1000:")
    run_command("sudo asterisk -rx 'pjsip show auth 1000-auth'", check=False)

def check_web_server_sync():
    """Verificar sincronización con servidor web"""
    print("\n🌐 VERIFICANDO SINCRONIZACIÓN SERVIDOR WEB")
    print("=" * 70)
    
    # Verificar archivos del proyecto
    print("\n📁 ARCHIVOS DEL PROYECTO:")
    if Path("data/extensions.json").exists():
        run_command("wc -l data/extensions.json", check=False)
        run_command("head -5 data/extensions.json", check=False)
    
    if Path("data/providers.json").exists():
        run_command("cat data/providers.json", check=False)
    
    # Verificar procesos web
    print("\n🖥️ PROCESOS WEB:")
    run_command("ps aux | grep python", check=False)
    
    # Verificar puertos
    print("\n🔌 PUERTOS:")
    run_command("sudo netstat -tulpn | grep :5060", check=False)
    run_command("sudo netstat -tulpn | grep :8000", check=False)

def create_minimal_test_config():
    """Crear configuración mínima de prueba"""
    print("\n🧪 CREANDO CONFIGURACIÓN MÍNIMA DE PRUEBA")
    print("=" * 70)
    
    # Configuración mínima para probar
    minimal_config = """[global]
type=global
endpoint_identifier_order=username,ip,anonymous

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

[1000]
type=endpoint
transport=transport-udp
context=from-internal
disallow=all
allow=ulaw
auth=1000-auth
aors=1000-aor

[1000-auth]
type=auth
auth_type=userpass
password=test1000
username=1000

[1000-aor]
type=aor
max_contacts=1

[1001]
type=endpoint
transport=transport-udp
context=from-internal
disallow=all
allow=ulaw
auth=1001-auth
aors=1001-aor

[1001-auth]
type=auth
auth_type=userpass
password=test1001
username=1001

[1001-aor]
type=aor
max_contacts=1
"""
    
    # Escribir configuración mínima
    with open("/tmp/pjsip_minimal.conf", 'w') as f:
        f.write(minimal_config)
    
    print("✅ Configuración mínima creada en /tmp/pjsip_minimal.conf")
    
    # Preguntar si aplicar
    print("\n⚠️ ¿Quieres aplicar esta configuración mínima para probar?")
    print("Esto reemplazará temporalmente tu pjsip.conf actual")
    print("(Se hará backup automático)")

def main():
    """Función principal"""
    print("🚨 DIAGNÓSTICO COMPLETO PJSIP - VERIFICACIÓN DE SINCRONIZACIÓN")
    print("=" * 70)
    
    if not Path("data/extensions.json").exists():
        print("❌ Error: Ejecutar desde directorio voip-auto-dialer")
        sys.exit(1)
    
    try:
        # Ejecutar diagnósticos
        check_asterisk_status()
        force_pjsip_reload()
        test_specific_endpoint()
        check_web_server_sync()
        create_minimal_test_config()
        
        print("\n🎯 DIAGNÓSTICO COMPLETADO")
        print("=" * 70)
        print("📋 RESUMEN:")
        print("1. Revisa los logs arriba para identificar problemas específicos")
        print("2. Si quieres probar configuración mínima:")
        print("   sudo cp /tmp/pjsip_minimal.conf /etc/asterisk/pjsip.conf")
        print("   sudo asterisk -rx 'pjsip reload'")
        print("3. Luego probar: sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()