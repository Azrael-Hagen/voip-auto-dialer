#!/usr/bin/env python3
"""
SOLUCIÓN SIMPLE Y FUNCIONAL - SIN COMPLICACIONES
Configuración PJSIP básica que realmente funciona
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

def run_command(cmd, check=True, shell=True):
    """Ejecutar comando con manejo de errores"""
    print(f"🔧 {cmd}")
    try:
        result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        return None

def create_simple_working_config():
    """Crear configuración simple que funciona"""
    print("\n🔧 CREANDO CONFIGURACIÓN SIMPLE QUE FUNCIONA")
    print("=" * 60)
    
    # Cargar datos básicos
    with open("data/extensions.json", 'r') as f:
        extensions = json.load(f)
    
    with open("data/providers.json", 'r') as f:
        providers = json.load(f)
        provider = None
        for p_id, p_data in providers.items():
            if p_data.get('active', False):
                provider = p_data
                break
    
    print(f"📞 Configurando {len(extensions)} extensiones")
    print(f"🌐 Proveedor: {provider['name']}")
    
    # Configuración PJSIP SIMPLE
    pjsip_config = """[global]
type=global
endpoint_identifier_order=username,ip,anonymous

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

"""
    
    # Agregar solo las primeras 5 extensiones para probar
    test_extensions = list(extensions.keys())[:5]
    print(f"🧪 Configurando {len(test_extensions)} extensiones de prueba: {test_extensions}")
    
    for ext in test_extensions:
        ext_data = extensions[ext]
        password = ext_data.get('password', f'pass{ext}')
        
        pjsip_config += f"""[{ext}]
type=endpoint
transport=transport-udp
context=from-internal
disallow=all
allow=ulaw
auth={ext}
aors={ext}

[{ext}]
type=auth
auth_type=userpass
password={password}
username={ext}

[{ext}]
type=aor
max_contacts=1

"""
    
    # Configuración del proveedor SIMPLE
    pjsip_config += f"""[provider]
type=registration
transport=transport-udp
outbound_auth=provider
server_uri=sip:{provider['host']}:{provider['port']}
client_uri=sip:{provider['username']}@{provider['host']}:{provider['port']}
retry_interval=60

[provider]
type=auth
auth_type=userpass
password={provider['password']}
username={provider['username']}

[provider]
type=aor
contact=sip:{provider['host']}:{provider['port']}

[provider]
type=endpoint
transport=transport-udp
context=from-provider
disallow=all
allow={provider['codec']}
outbound_auth=provider
aors=provider

[provider]
type=identify
endpoint=provider
match={provider['host']}

"""
    
    # Dialplan SIMPLE
    extensions_config = f"""[general]
static=yes
writeprotect=no

[from-internal]
; Llamadas internas
exten => _1XXX,1,Dial(PJSIP/${{EXTEN}},30)
exten => _1XXX,n,Hangup()

; Llamadas salientes
exten => _9.,1,Dial(PJSIP/${{EXTEN:1}}@provider,60)
exten => _9.,n,Hangup()

; Test
exten => *99,1,Answer()
exten => *99,n,Playback(demo-congrats)
exten => *99,n,Hangup()

[from-provider]
; Llamadas entrantes
exten => {provider['username']},1,Dial(PJSIP/{test_extensions[0]},30)
exten => {provider['username']},n,Hangup()

exten => _X.,1,Dial(PJSIP/{test_extensions[0]},30)
exten => _X.,n,Hangup()

[default]
include => from-internal
"""
    
    return pjsip_config, extensions_config

def apply_simple_config():
    """Aplicar configuración simple"""
    print("\n🚀 APLICANDO CONFIGURACIÓN SIMPLE")
    print("=" * 60)
    
    # Detener Asterisk
    print("🛑 Deteniendo Asterisk...")
    run_command("sudo systemctl stop asterisk", check=False)
    run_command("sudo pkill -9 asterisk", check=False)
    time.sleep(3)
    
    # Backup
    timestamp = int(time.time())
    run_command(f"sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup.{timestamp}", check=False)
    run_command(f"sudo cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup.{timestamp}", check=False)
    
    # Crear configuraciones
    pjsip_config, extensions_config = create_simple_working_config()
    
    # Escribir archivos
    with open("/tmp/pjsip_simple.conf", 'w') as f:
        f.write(pjsip_config)
    
    with open("/tmp/extensions_simple.conf", 'w') as f:
        f.write(extensions_config)
    
    # Aplicar
    run_command("sudo cp /tmp/pjsip_simple.conf /etc/asterisk/pjsip.conf")
    run_command("sudo cp /tmp/extensions_simple.conf /etc/asterisk/extensions.conf")
    
    # Permisos
    run_command("sudo chown asterisk:asterisk /etc/asterisk/pjsip.conf", check=False)
    run_command("sudo chown asterisk:asterisk /etc/asterisk/extensions.conf", check=False)
    
    # Limpiar
    run_command("rm -f /tmp/pjsip_simple.conf /tmp/extensions_simple.conf", check=False)
    
    print("✅ Configuración simple aplicada")

def start_and_test_simple():
    """Iniciar y probar configuración simple"""
    print("\n🚀 INICIANDO ASTERISK CON CONFIGURACIÓN SIMPLE")
    print("=" * 60)
    
    # Iniciar
    run_command("sudo systemctl start asterisk")
    time.sleep(10)
    
    # Verificar
    result = run_command("sudo systemctl is-active asterisk", check=False)
    if result and "active" in result.stdout:
        print("✅ Asterisk iniciado")
    else:
        print("❌ Error iniciando Asterisk")
        return False
    
    # CLI
    time.sleep(5)
    result = run_command("sudo asterisk -rx 'core show version'", check=False)
    if result and result.returncode == 0:
        print("✅ CLI funcional")
    else:
        print("❌ CLI no responde")
        return False
    
    return True

def test_simple_functionality():
    """Probar funcionalidad simple"""
    print("\n🧪 PROBANDO FUNCIONALIDAD SIMPLE")
    print("=" * 60)
    
    # Endpoints
    print("📞 Endpoints:")
    result = run_command("sudo asterisk -rx 'pjsip show endpoints' | head -10", check=False)
    
    # Registraciones
    print("\n🌐 Registraciones:")
    result = run_command("sudo asterisk -rx 'pjsip show registrations'", check=False)
    
    # Probar llamada interna
    print("\n📞 Probando llamada interna:")
    result = run_command("sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'", check=False)
    
    # Probar servicio test
    print("\n🧪 Probando servicio test:")
    result = run_command("sudo asterisk -rx 'originate PJSIP/1000 extension *99@from-internal'", check=False)

def main():
    """Función principal"""
    print("🚨 SOLUCIÓN SIMPLE Y FUNCIONAL - SIN COMPLICACIONES")
    print("=" * 70)
    print("🎯 Configuración básica que realmente funciona")
    print("🎯 Solo 5 extensiones de prueba para empezar")
    print("=" * 70)
    
    if not Path("data/extensions.json").exists():
        print("❌ Error: Ejecutar desde directorio voip-auto-dialer")
        sys.exit(1)
    
    try:
        apply_simple_config()
        
        if start_and_test_simple():
            test_simple_functionality()
            
            print("\n🎉 CONFIGURACIÓN SIMPLE APLICADA")
            print("=" * 70)
            print("🚀 PRUEBAS MANUALES:")
            print("1. sudo asterisk -rx 'pjsip show endpoints'")
            print("2. sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'")
            print("3. sudo asterisk -rx 'originate PJSIP/1000 extension *99@from-internal'")
            print("4. sudo asterisk -rx 'originate PJSIP/1000 extension 9555123456@from-internal'")
            
        else:
            print("\n❌ ERROR EN CONFIGURACIÓN SIMPLE")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()