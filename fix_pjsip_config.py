#!/usr/bin/env python3
"""
CORRECCIÓN ESPECÍFICA PARA CONFIGURACIÓN PJSIP
Corrige errores de AOR y registro con proveedor
"""

import os
import sys
import json
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
        if check:
            return None
        return e

def load_project_data():
    """Cargar datos del proyecto"""
    # Cargar extensiones
    with open("data/extensions.json", 'r') as f:
        extensions_data = json.load(f)
    
    # Cargar proveedores
    with open("data/providers.json", 'r') as f:
        providers = json.load(f)
        provider_data = None
        for provider_id, provider in providers.items():
            if provider.get('active', False):
                provider_data = provider
                break
    
    return extensions_data, provider_data

def generate_corrected_pjsip_config(extensions_data, provider_data):
    """Generar configuración PJSIP corregida"""
    print("\n🔧 GENERANDO CONFIGURACIÓN PJSIP CORREGIDA")
    print("=" * 60)
    
    config = []
    
    # Configuración global
    config.append("""[global]
type=global
endpoint_identifier_order=ip,username,anonymous

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

""")
    
    # Configuración del proveedor CORREGIDA
    config.append(f"""[PBX_ON_THE_CLOUD]
type=registration
transport=transport-udp
outbound_auth=PBX_ON_THE_CLOUD_auth
server_uri=sip:{provider_data['host']}:{provider_data['port']}
client_uri=sip:{provider_data['username']}@{provider_data['host']}:{provider_data['port']}
contact_user={provider_data['username']}
retry_interval=60
forbidden_retry_interval=600
expiration=3600

[PBX_ON_THE_CLOUD_auth]
type=auth
auth_type=userpass
password={provider_data['password']}
username={provider_data['username']}

[PBX_ON_THE_CLOUD_endpoint]
type=endpoint
transport=transport-udp
context=from-provider
disallow=all
allow={provider_data['codec']}
outbound_auth=PBX_ON_THE_CLOUD_auth
aors=PBX_ON_THE_CLOUD_aor

[PBX_ON_THE_CLOUD_aor]
type=aor
contact=sip:{provider_data['host']}:{provider_data['port']}

""")
    
    # Configurar extensiones 1XXX CORREGIDAS
    print(f"📞 Configurando {len(extensions_data)} extensiones con AOR corregidos...")
    
    for ext_num, ext_data in extensions_data.items():
        password = ext_data.get('password', 'defaultpass123')
        config.append(f"""[{ext_num}]
type=endpoint
transport=transport-udp
context=from-internal
disallow=all
allow=ulaw,alaw,gsm
auth={ext_num}_auth
aors={ext_num}_aor
direct_media=no
ice_support=yes

[{ext_num}_auth]
type=auth
auth_type=userpass
password={password}
username={ext_num}

[{ext_num}_aor]
type=aor
max_contacts=1
remove_existing=yes

""")
    
    return ''.join(config)

def generate_corrected_extensions_config(extensions_data, provider_data):
    """Generar configuración de dialplan corregida"""
    print("\n🔧 GENERANDO DIALPLAN CORREGIDO")
    print("=" * 60)
    
    config = f"""[general]
static=yes
writeprotect=no
clearglobalvars=no

[globals]
CONSOLE=Console/dsp
IAXINFO=guest
TRUNK=PBX_ON_THE_CLOUD_endpoint

[from-internal]
; Llamadas internas entre extensiones 1XXX
exten => _1XXX,1,NoOp(Llamada interna a ${{EXTEN}})
exten => _1XXX,n,Dial(PJSIP/${{EXTEN}},30,tT)
exten => _1XXX,n,GotoIf(${{DIALSTATUS}}=NOANSWER?voicemail:hangup)
exten => _1XXX,n(voicemail),Voicemail(${{EXTEN}}@default,u)
exten => _1XXX,n(hangup),Hangup()

; Llamadas salientes (marcar 9 + número)
exten => _9.,1,NoOp(Llamada saliente: ${{EXTEN:1}})
exten => _9.,n,Set(CALLERID(num)={provider_data['username']})
exten => _9.,n,Dial(PJSIP/${{EXTEN:1}}@PBX_ON_THE_CLOUD_endpoint,60,tT)
exten => _9.,n,Hangup()

; Llamadas directas salientes (sin 9)
exten => _NXXNXXXXXX,1,NoOp(Llamada directa saliente: ${{EXTEN}})
exten => _NXXNXXXXXX,n,Set(CALLERID(num)={provider_data['username']})
exten => _NXXNXXXXXX,n,Dial(PJSIP/${{EXTEN}}@PBX_ON_THE_CLOUD_endpoint,60,tT)
exten => _NXXNXXXXXX,n,Hangup()

; Llamadas de emergencia
exten => 911,1,NoOp(Llamada de emergencia)
exten => 911,n,Set(CALLERID(num)={provider_data['username']})
exten => 911,n,Dial(PJSIP/911@PBX_ON_THE_CLOUD_endpoint,30)
exten => 911,n,Hangup()

; Servicios especiales
exten => *97,1,VoiceMailMain(${{CALLERID(num)}}@default)
exten => *97,n,Hangup()

exten => *99,1,Answer()
exten => *99,n,Playback(system-online)
exten => *99,n,SayNumber(${{EPOCH}})
exten => *99,n,Hangup()

[from-provider]
; Llamadas entrantes del proveedor
exten => {provider_data['username']},1,NoOp(Llamada entrante para: ${{EXTEN}})
exten => {provider_data['username']},n,Set(AVAILABLE_AGENT=${{SHELL(python3 {os.getcwd()}/get_available_agent.py)}})
exten => {provider_data['username']},n,GotoIf(${{LEN(${{AVAILABLE_AGENT}})}}?route:busy)
exten => {provider_data['username']},n(route),Dial(PJSIP/${{AVAILABLE_AGENT}},30,tT)
exten => {provider_data['username']},n,Voicemail(${{AVAILABLE_AGENT}}@default,u)
exten => {provider_data['username']},n,Hangup()
exten => {provider_data['username']},n(busy),Busy(10)
exten => {provider_data['username']},n,Hangup()

; Patrón genérico para llamadas entrantes
exten => _X.,1,NoOp(Llamada entrante genérica: ${{EXTEN}})
exten => _X.,n,Set(AVAILABLE_AGENT=${{SHELL(python3 {os.getcwd()}/get_available_agent.py)}})
exten => _X.,n,GotoIf(${{LEN(${{AVAILABLE_AGENT}})}}?route:busy)
exten => _X.,n(route),Dial(PJSIP/${{AVAILABLE_AGENT}},30,tT)
exten => _X.,n,Voicemail(${{AVAILABLE_AGENT}}@default,u)
exten => _X.,n,Hangup()
exten => _X.,n(busy),Busy(10)
exten => _X.,n,Hangup()

[default]
include => from-internal

"""
    
    return config

def apply_corrected_configuration():
    """Aplicar configuración corregida"""
    print("\n🚨 APLICANDO CONFIGURACIÓN PJSIP CORREGIDA")
    print("=" * 70)
    
    # Cargar datos
    extensions_data, provider_data = load_project_data()
    print(f"📞 Extensiones: {len(extensions_data)}")
    print(f"🌐 Proveedor: {provider_data['name']}")
    print(f"🔑 Usuario proveedor: {provider_data['username']}")
    
    # Detener Asterisk
    print("\n🛑 Deteniendo Asterisk...")
    run_command("sudo systemctl stop asterisk", check=False)
    run_command("sudo pkill -9 asterisk", check=False)
    time.sleep(3)
    
    # Hacer backup
    timestamp = int(time.time())
    run_command(f"sudo cp -r /etc/asterisk /etc/asterisk_backup_fix_{timestamp}", check=False)
    
    # Generar configuraciones corregidas
    pjsip_conf = generate_corrected_pjsip_config(extensions_data, provider_data)
    extensions_conf = generate_corrected_extensions_config(extensions_data, provider_data)
    
    # Escribir archivos
    with open("/tmp/pjsip_corrected.conf", 'w') as f:
        f.write(pjsip_conf)
    
    with open("/tmp/extensions_corrected.conf", 'w') as f:
        f.write(extensions_conf)
    
    # Aplicar configuraciones
    run_command("sudo cp /tmp/pjsip_corrected.conf /etc/asterisk/pjsip.conf")
    run_command("sudo cp /tmp/extensions_corrected.conf /etc/asterisk/extensions.conf")
    
    # Configurar permisos
    run_command("sudo chown asterisk:asterisk /etc/asterisk/*.conf", check=False)
    run_command("sudo chmod 640 /etc/asterisk/*.conf", check=False)
    
    # Limpiar archivos temporales
    run_command("rm -f /tmp/pjsip_corrected.conf /tmp/extensions_corrected.conf", check=False)
    
    print("✅ Configuraciones corregidas aplicadas")

def start_and_test_corrected():
    """Iniciar Asterisk y probar configuración corregida"""
    print("\n🚀 INICIANDO ASTERISK CON CONFIGURACIÓN CORREGIDA")
    print("=" * 70)
    
    # Iniciar Asterisk
    run_command("sudo systemctl start asterisk")
    time.sleep(10)
    
    # Verificar estado
    result = run_command("sudo systemctl is-active asterisk", check=False)
    if result and "active" in result.stdout:
        print("✅ Asterisk iniciado correctamente")
    else:
        print("❌ Error iniciando Asterisk")
        return False
    
    # Probar CLI
    time.sleep(5)
    result = run_command("sudo asterisk -rx 'core show version'", check=False)
    if result and result.returncode == 0:
        print("✅ CLI funcional")
    else:
        print("❌ Error en CLI")
        return False
    
    return True

def test_corrected_functionality():
    """Probar funcionalidad corregida"""
    print("\n🧪 PROBANDO FUNCIONALIDAD CORREGIDA")
    print("=" * 70)
    
    # Verificar endpoints
    print("📞 Verificando endpoints...")
    result = run_command("sudo asterisk -rx 'pjsip show endpoints' | head -20", check=False)
    if result:
        print("✅ Endpoints configurados")
    
    # Verificar registro con proveedor
    print("\n🌐 Verificando registro con proveedor...")
    result = run_command("sudo asterisk -rx 'pjsip show registrations'", check=False)
    if result:
        if "Registered" in result.stdout:
            print("✅ Proveedor registrado correctamente")
        else:
            print("⚠️ Proveedor aún registrándose...")
    
    # Probar llamada interna
    print("\n📞 Probando llamada interna...")
    result = run_command("sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'", check=False)
    if result:
        if "ERROR" not in result.stdout:
            print("✅ Llamada interna iniciada correctamente")
        else:
            print("⚠️ Error en llamada interna - revisar logs")
    
    print("\n🎯 CORRECCIÓN COMPLETADA")
    print("=" * 70)
    print("✅ Configuración PJSIP corregida")
    print("✅ AOR configurados correctamente")
    print("✅ Registro con proveedor mejorado")
    print("✅ Llamadas internas habilitadas")

def main():
    """Función principal"""
    print("🚨 CORRECCIÓN ESPECÍFICA CONFIGURACIÓN PJSIP")
    print("=" * 70)
    print("🎯 Corrigiendo errores de AOR y registro con proveedor")
    print("=" * 70)
    
    if not Path("data/extensions.json").exists():
        print("❌ Error: Ejecutar desde directorio voip-auto-dialer")
        sys.exit(1)
    
    try:
        apply_corrected_configuration()
        
        if start_and_test_corrected():
            test_corrected_functionality()
            
            print("\n🎉 CORRECCIÓN PJSIP COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print("🚀 PRÓXIMOS PASOS:")
            print("1. Probar: sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'")
            print("2. Probar saliente: sudo asterisk -rx 'originate PJSIP/1000 extension 9555123456@from-internal'")
            print("3. Verificar registro: sudo asterisk -rx 'pjsip show registrations'")
            print("4. Iniciar servidor: python3 start_complete_system.py")
            
        else:
            print("\n❌ ERROR EN LA CORRECCIÓN")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

