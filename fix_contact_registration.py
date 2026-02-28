#!/usr/bin/env python3
"""
SOLUCIÓN ESPECÍFICA: PROBLEMA DE CONTACTOS NO REGISTRADOS
El error "invalid URI" indica que los endpoints no tienen contactos
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

def create_working_pjsip_config():
    """Crear configuración PJSIP que realmente funciona con contactos"""
    print("\n🔧 CREANDO CONFIGURACIÓN PJSIP CON CONTACTOS ESTÁTICOS")
    print("=" * 60)
    
    # Cargar datos
    with open("data/extensions.json", 'r') as f:
        extensions = json.load(f)
    
    with open("data/providers.json", 'r') as f:
        providers = json.load(f)
        provider = None
        for p_id, p_data in providers.items():
            if p_data.get('active', False):
                provider = p_data
                break
    
    # Configuración PJSIP con contactos estáticos
    config = """[global]
type=global
endpoint_identifier_order=username,ip,anonymous

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

"""
    
    # Solo 3 extensiones para probar
    test_extensions = ['1000', '1001', '1002']
    print(f"🧪 Configurando {len(test_extensions)} extensiones: {test_extensions}")
    
    for ext in test_extensions:
        ext_data = extensions.get(ext, {})
        password = ext_data.get('password', f'pass{ext}')
        
        # Configuración con contacto estático
        config += f"""[{ext}]
type=endpoint
transport=transport-udp
context=from-internal
disallow=all
allow=ulaw,alaw
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
contact=sip:{ext}@127.0.0.1:5060

"""
    
    # Proveedor simplificado
    config += f"""[provider]
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

"""
    
    return config

def create_working_extensions_config():
    """Crear dialplan que funciona"""
    config = """[general]
static=yes
writeprotect=no

[from-internal]
; Test básico
exten => *99,1,Answer()
exten => *99,n,Playback(demo-congrats)
exten => *99,n,Hangup()

; Llamadas internas
exten => 1000,1,Dial(PJSIP/1000,30)
exten => 1000,n,Hangup()

exten => 1001,1,Dial(PJSIP/1001,30)
exten => 1001,n,Hangup()

exten => 1002,1,Dial(PJSIP/1002,30)
exten => 1002,n,Hangup()

; Llamadas salientes
exten => _9.,1,Dial(PJSIP/${EXTEN:1}@provider,60)
exten => _9.,n,Hangup()

[from-provider]
; Llamadas entrantes
exten => _X.,1,Dial(PJSIP/1000,30)
exten => _X.,n,Hangup()

[default]
include => from-internal
"""
    
    return config

def apply_contact_fix():
    """Aplicar corrección de contactos"""
    print("\n🚀 APLICANDO CORRECCIÓN DE CONTACTOS")
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
    pjsip_config = create_working_pjsip_config()
    extensions_config = create_working_extensions_config()
    
    # Escribir archivos
    with open("/tmp/pjsip_contacts.conf", 'w') as f:
        f.write(pjsip_config)
    
    with open("/tmp/extensions_contacts.conf", 'w') as f:
        f.write(extensions_config)
    
    # Aplicar
    run_command("sudo cp /tmp/pjsip_contacts.conf /etc/asterisk/pjsip.conf")
    run_command("sudo cp /tmp/extensions_contacts.conf /etc/asterisk/extensions.conf")
    
    # Permisos
    run_command("sudo chown asterisk:asterisk /etc/asterisk/pjsip.conf", check=False)
    run_command("sudo chown asterisk:asterisk /etc/asterisk/extensions.conf", check=False)
    
    # Limpiar
    run_command("rm -f /tmp/pjsip_contacts.conf /tmp/extensions_contacts.conf", check=False)
    
    print("✅ Configuración con contactos aplicada")

def start_and_test_contacts():
    """Iniciar y probar configuración con contactos"""
    print("\n🚀 INICIANDO ASTERISK CON CONTACTOS ESTÁTICOS")
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

def test_contact_functionality():
    """Probar funcionalidad con contactos"""
    print("\n🧪 PROBANDO FUNCIONALIDAD CON CONTACTOS")
    print("=" * 60)
    
    # Endpoints con contactos
    print("📞 Endpoints con contactos:")
    result = run_command("sudo asterisk -rx 'pjsip show endpoints'", check=False)
    
    # AOR con contactos
    print("\n📋 AOR con contactos:")
    result = run_command("sudo asterisk -rx 'pjsip show aors'", check=False)
    
    # Contactos específicos
    print("\n📱 Contactos específicos:")
    for ext in ['1000', '1001', '1002']:
        result = run_command(f"sudo asterisk -rx 'pjsip show aor {ext}'", check=False)
    
    # Probar servicio test
    print("\n🧪 Probando servicio test (*99):")
    result = run_command("sudo asterisk -rx 'originate PJSIP/1000 extension *99@from-internal'", check=False)
    
    # Probar llamada directa
    print("\n📞 Probando llamada directa (1000 → 1001):")
    result = run_command("sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'", check=False)

def main():
    """Función principal"""
    print("🚨 CORRECCIÓN ESPECÍFICA: CONTACTOS NO REGISTRADOS")
    print("=" * 70)
    print("🎯 El error 'invalid URI' indica falta de contactos")
    print("🎯 Configurando contactos estáticos para 3 extensiones")
    print("=" * 70)
    
    if not Path("data/extensions.json").exists():
        print("❌ Error: Ejecutar desde directorio voip-auto-dialer")
        sys.exit(1)
    
    try:
        apply_contact_fix()
        
        if start_and_test_contacts():
            test_contact_functionality()
            
            print("\n🎉 CORRECCIÓN DE CONTACTOS APLICADA")
            print("=" * 70)
            print("🚀 PRUEBAS MANUALES:")
            print("1. sudo asterisk -rx 'pjsip show endpoints'")
            print("2. sudo asterisk -rx 'pjsip show aors'")
            print("3. sudo asterisk -rx 'originate PJSIP/1000 extension *99@from-internal'")
            print("4. sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'")
            print("\n📋 EXPLICACIÓN:")
            print("- Contactos estáticos configurados: sip:1000@127.0.0.1:5060")
            print("- Esto evita el error 'invalid URI' por falta de registro")
            print("- Una vez que funcione, se puede cambiar a registro dinámico")
            
        else:
            print("\n❌ ERROR EN CORRECCIÓN DE CONTACTOS")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()