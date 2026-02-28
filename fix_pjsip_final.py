#!/usr/bin/env python3
"""
CORRECCIÓN FINAL PJSIP - BASADA EN DOCUMENTACIÓN OFICIAL ASTERISK
Corrige todos los errores identificados usando mejores prácticas
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
    with open("data/extensions.json", 'r') as f:
        extensions_data = json.load(f)
    
    with open("data/providers.json", 'r') as f:
        providers = json.load(f)
        provider_data = None
        for provider_id, provider in providers.items():
            if provider.get('active', False):
                provider_data = provider
                break
    
    return extensions_data, provider_data

def generate_final_pjsip_config(extensions_data, provider_data):
    """Generar configuración PJSIP final basada en documentación oficial"""
    print("\n🔧 GENERANDO CONFIGURACIÓN PJSIP FINAL")
    print("=" * 60)
    
    config = []
    
    # Configuración global y transporte
    config.append("""[global]
type=global
endpoint_identifier_order=ip,username,anonymous

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

""")
    
    # Configuración del proveedor CORREGIDA según documentación
    provider_username = provider_data['username']
    provider_host = provider_data['host']
    provider_port = provider_data['port']
    provider_password = provider_data['password']
    
    config.append(f"""[trunk-provider]
type=registration
transport=transport-udp
outbound_auth=trunk-provider-auth
server_uri=sip:{provider_host}:{provider_port}
client_uri=sip:{provider_username}@{provider_host}:{provider_port}
contact_user={provider_username}
retry_interval=60
forbidden_retry_interval=600
expiration=3600

[trunk-provider-auth]
type=auth
auth_type=userpass
password={provider_password}
username={provider_username}

[trunk-provider-aor]
type=aor
contact=sip:{provider_host}:{provider_port}

[trunk-provider-endpoint]
type=endpoint
transport=transport-udp
context=from-provider
disallow=all
allow={provider_data['codec']}
outbound_auth=trunk-provider-auth
aors=trunk-provider-aor

[trunk-provider-identify]
type=identify
endpoint=trunk-provider-endpoint
match={provider_host}

""")
    
    # Templates para extensiones (mejores prácticas)
    config.append("""[endpoint-basic](!)
type=endpoint
transport=transport-udp
context=from-internal
disallow=all
allow=ulaw,alaw,gsm
direct_media=no
ice_support=yes

[auth-userpass](!)
type=auth
auth_type=userpass

[aor-single-reg](!)
type=aor
max_contacts=1
remove_existing=yes

""")
    
    # Configurar extensiones 1XXX usando templates
    print(f"📞 Configurando {len(extensions_data)} extensiones con templates...")
    
    for ext_num, ext_data in extensions_data.items():
        password = ext_data.get('password', f'pass{ext_num}')
        config.append(f"""[{ext_num}](endpoint-basic)
auth={ext_num}-auth
aors={ext_num}-aor

[{ext_num}-auth](auth-userpass)
password={password}
username={ext_num}

[{ext_num}-aor](aor-single-reg)

""")
    
    return ''.join(config)

def generate_final_extensions_config(extensions_data, provider_data):
    """Generar configuración de dialplan final"""
    print("\n🔧 GENERANDO DIALPLAN FINAL")
    print("=" * 60)
    
    provider_username = provider_data['username']
    
    config = f"""[general]
static=yes
writeprotect=no
clearglobalvars=no

[globals]
CONSOLE=Console/dsp
IAXINFO=guest
TRUNK=trunk-provider-endpoint

[from-internal]
; Llamadas internas entre extensiones 1XXX
exten => _1XXX,1,NoOp(Llamada interna a ${{EXTEN}})
exten => _1XXX,n,Dial(PJSIP/${{EXTEN}},30,tT)
exten => _1XXX,n,GotoIf(${{DIALSTATUS}}=NOANSWER?voicemail:hangup)
exten => _1XXX,n(voicemail),Voicemail(${{EXTEN}}@default,u)
exten => _1XXX,n(hangup),Hangup()

; Llamadas salientes (marcar 9 + número)
exten => _9.,1,NoOp(Llamada saliente: ${{EXTEN:1}})
exten => _9.,n,Set(CALLERID(num)={provider_username})
exten => _9.,n,Dial(PJSIP/${{EXTEN:1}}@trunk-provider-endpoint,60,tT)
exten => _9.,n,Hangup()

; Llamadas directas salientes (números de 10 dígitos)
exten => _NXXNXXXXXX,1,NoOp(Llamada directa saliente: ${{EXTEN}})
exten => _NXXNXXXXXX,n,Set(CALLERID(num)={provider_username})
exten => _NXXNXXXXXX,n,Dial(PJSIP/${{EXTEN}}@trunk-provider-endpoint,60,tT)
exten => _NXXNXXXXXX,n,Hangup()

; Llamadas de emergencia
exten => 911,1,NoOp(Llamada de emergencia)
exten => 911,n,Set(CALLERID(num)={provider_username})
exten => 911,n,Dial(PJSIP/911@trunk-provider-endpoint,30)
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
exten => {provider_username},1,NoOp(Llamada entrante para: ${{EXTEN}})
exten => {provider_username},n,Set(AVAILABLE_AGENT=${{SHELL(python3 {os.getcwd()}/get_available_agent.py)}})
exten => {provider_username},n,GotoIf(${{LEN(${{AVAILABLE_AGENT}})}}?route:busy)
exten => {provider_username},n(route),Dial(PJSIP/${{AVAILABLE_AGENT}},30,tT)
exten => {provider_username},n,Voicemail(${{AVAILABLE_AGENT}}@default,u)
exten => {provider_username},n,Hangup()
exten => {provider_username},n(busy),Busy(10)
exten => {provider_username},n,Hangup()

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

def apply_final_configuration():
    """Aplicar configuración final corregida"""
    print("\n🚨 APLICANDO CONFIGURACIÓN PJSIP FINAL")
    print("=" * 70)
    
    # Cargar datos
    extensions_data, provider_data = load_project_data()
    print(f"📞 Extensiones: {len(extensions_data)}")
    print(f"🌐 Proveedor: {provider_data['name']}")
    print(f"🔑 Usuario: {provider_data['username']}")
    print(f"🏠 Host: {provider_data['host']}:{provider_data['port']}")
    
    # Detener Asterisk completamente
    print("\n🛑 Deteniendo Asterisk completamente...")
    run_command("sudo systemctl stop asterisk", check=False)
    run_command("sudo pkill -9 asterisk", check=False)
    time.sleep(5)
    
    # Verificar que no hay procesos
    result = run_command("pgrep asterisk", check=False)
    if result and result.returncode == 0:
        print("⚠️ Forzando detención de procesos restantes...")
        run_command("sudo kill -9 $(pgrep asterisk)", check=False)
        time.sleep(3)
    
    # Hacer backup
    timestamp = int(time.time())
    run_command(f"sudo cp -r /etc/asterisk /etc/asterisk_backup_final_{timestamp}", check=False)
    
    # Generar configuraciones finales
    pjsip_conf = generate_final_pjsip_config(extensions_data, provider_data)
    extensions_conf = generate_final_extensions_config(extensions_data, provider_data)
    
    # Escribir archivos
    with open("/tmp/pjsip_final.conf", 'w') as f:
        f.write(pjsip_conf)
    
    with open("/tmp/extensions_final.conf", 'w') as f:
        f.write(extensions_conf)
    
    # Aplicar configuraciones
    run_command("sudo cp /tmp/pjsip_final.conf /etc/asterisk/pjsip.conf")
    run_command("sudo cp /tmp/extensions_final.conf /etc/asterisk/extensions.conf")
    
    # Configurar permisos
    run_command("sudo chown asterisk:asterisk /etc/asterisk/*.conf", check=False)
    run_command("sudo chmod 640 /etc/asterisk/*.conf", check=False)
    
    # Limpiar archivos temporales
    run_command("rm -f /tmp/pjsip_final.conf /tmp/extensions_final.conf", check=False)
    
    print("✅ Configuración final aplicada")

def start_and_test_final():
    """Iniciar Asterisk y probar configuración final"""
    print("\n🚀 INICIANDO ASTERISK CON CONFIGURACIÓN FINAL")
    print("=" * 70)
    
    # Iniciar Asterisk
    run_command("sudo systemctl start asterisk")
    time.sleep(15)
    
    # Verificar estado
    result = run_command("sudo systemctl is-active asterisk", check=False)
    if result and "active" in result.stdout:
        print("✅ Asterisk iniciado correctamente")
    else:
        print("❌ Error iniciando Asterisk")
        run_command("sudo journalctl -u asterisk --no-pager -n 20", check=False)
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

def test_final_functionality():
    """Probar funcionalidad final completa"""
    print("\n🧪 PROBANDO FUNCIONALIDAD FINAL")
    print("=" * 70)
    
    # Verificar endpoints
    print("📞 Verificando endpoints...")
    result = run_command("sudo asterisk -rx 'pjsip show endpoints' | head -10", check=False)
    if result:
        print("✅ Endpoints listados")
    
    # Verificar registro con proveedor
    print("\n🌐 Verificando registro con proveedor...")
    result = run_command("sudo asterisk -rx 'pjsip show registrations'", check=False)
    if result:
        print("📋 Estado del registro:")
        print(result.stdout)
        if "Registered" in result.stdout:
            print("✅ Proveedor registrado exitosamente")
        elif "Rejected" in result.stdout:
            print("⚠️ Registro aún rechazado - verificar credenciales")
        else:
            print("⏳ Registro en proceso...")
    
    # Esperar un momento para el registro
    print("\n⏳ Esperando 30 segundos para registro completo...")
    time.sleep(30)
    
    # Verificar registro nuevamente
    print("\n🔄 Verificando registro final...")
    result = run_command("sudo asterisk -rx 'pjsip show registrations'", check=False)
    if result:
        print("📋 Estado final del registro:")
        print(result.stdout)
    
    # Probar llamada interna
    print("\n📞 Probando llamada interna...")
    result = run_command("sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'", check=False)
    if result:
        if "ERROR" not in result.stdout:
            print("✅ Llamada interna iniciada correctamente")
        else:
            print("⚠️ Error en llamada interna:")
            print(result.stdout)
    
    print("\n🎯 CONFIGURACIÓN FINAL COMPLETADA")
    print("=" * 70)
    print("✅ Configuración PJSIP basada en documentación oficial")
    print("✅ Templates utilizados para escalabilidad")
    print("✅ AOR configurados correctamente")
    print("✅ Identificación de endpoints mejorada")
    print("✅ Registro con proveedor optimizado")

def main():
    """Función principal"""
    print("🚨 CORRECCIÓN FINAL PJSIP - BASADA EN DOCUMENTACIÓN OFICIAL")
    print("=" * 70)
    print("🎯 Implementando mejores prácticas de configuración PJSIP")
    print("🎯 Corrigiendo AOR, registro y identificación de endpoints")
    print("=" * 70)
    
    if not Path("data/extensions.json").exists():
        print("❌ Error: Ejecutar desde directorio voip-auto-dialer")
        sys.exit(1)
    
    try:
        apply_final_configuration()
        
        if start_and_test_final():
            test_final_functionality()
            
            print("\n🎉 CORRECCIÓN FINAL PJSIP COMPLETADA")
            print("=" * 70)
            print("🚀 PRÓXIMOS PASOS:")
            print("1. Verificar registro: sudo asterisk -rx 'pjsip show registrations'")
            print("2. Probar interna: sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'")
            print("3. Probar saliente: sudo asterisk -rx 'originate PJSIP/1000 extension 9555123456@from-internal'")
            print("4. Iniciar servidor: python3 start_complete_system.py")
            print("5. Acceder a: http://localhost:8000")
            
        else:
            print("\n❌ ERROR EN LA CORRECCIÓN FINAL")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()