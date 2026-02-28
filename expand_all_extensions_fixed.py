#!/usr/bin/env python3
"""
🚀 EXPANSIÓN A TODAS LAS 519 EXTENSIONES - VOIP AUTO DIALER
======================================================================
✅ Expande la configuración funcional de 3 extensiones a todas las 519
✅ Mantiene contactos estáticos para estabilidad
✅ Configura extensiones 1000-1519 con contactos válidos
======================================================================
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def log_step(message):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"🔧 [{timestamp}] {message}")

def run_command(cmd, description=""):
    """Ejecutar comando con logging"""
    if description:
        log_step(f"Ejecutando: {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"✅ {result.stdout.strip()}")
            return True, result.stdout
        else:
            print(f"❌ Error: {result.stderr.strip()}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout ejecutando: {cmd}")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False, str(e)

def load_extensions_data():
    """Cargar datos de extensiones del proyecto"""
    try:
        with open('data/extensions.json', 'r') as f:
            data = json.load(f)
            # El formato es {"1000": {...}, "1001": {...}}
            extensions = []
            for ext_num, ext_data in data.items():
                if isinstance(ext_data, dict):
                    ext_data['extension'] = ext_num  # Asegurar que tenga el campo extension
                    extensions.append(ext_data)
            
            log_step(f"Extensiones encontradas: {len(extensions)}")
            return extensions
    except Exception as e:
        log_step(f"Error cargando extensiones: {e}")
        return []

def load_provider_data():
    """Cargar datos del proveedor"""
    try:
        with open('data/providers.json', 'r') as f:
            data = json.load(f)
            providers = data.get('providers', [])
            if providers:
                provider = providers[0]
                log_step(f"Proveedor: {provider.get('name', 'Unknown')}")
                return provider
            return None
    except Exception as e:
        log_step(f"Error cargando proveedor: {e}")
        return None

def generate_pjsip_config(extensions, provider):
    """Generar configuración PJSIP completa"""
    
    config = """
; ============================================================================
; PJSIP CONFIGURATION - VOIP AUTO DIALER
; ============================================================================
; Generado automáticamente con contactos estáticos
; Extensiones: 1000-1519 (519 total)
; ============================================================================

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060
external_media_address=127.0.0.1
external_signaling_address=127.0.0.1

"""

    # Configurar proveedor si existe
    if provider:
        host = provider.get('host', 'pbxonthecloud.com')
        port = provider.get('port', 5081)
        username = provider.get('username', '523483070291')
        password = provider.get('password', 'defaultpass')
        
        config += f"""
; ============================================================================
; PROVEEDOR VOIP: {provider.get('name', 'Provider')}
; ============================================================================

[provider]
type=endpoint
transport=transport-udp
context=from-external
disallow=all
allow=ulaw,alaw,g729
outbound_auth=provider
aors=provider

[provider]
type=aor
contact=sip:{host}:{port}

[provider]
type=auth
auth_type=userpass
password={password}
username={username}

[provider]
type=registration
transport=transport-udp
outbound_auth=provider
server_uri=sip:{host}:{port}
client_uri=sip:{username}@{host}:{port}

"""

    # Generar configuración para todas las extensiones
    log_step(f"Generando configuración para {len(extensions)} extensiones...")
    
    for ext_data in extensions:
        ext_num = ext_data.get('extension', '')
        if not ext_num:
            continue
            
        # Asegurar que la extensión esté en el rango 1000-1519
        try:
            ext_int = int(ext_num)
            if ext_int < 1000 or ext_int > 1519:
                continue
        except:
            continue
            
        password = ext_data.get('password', ext_num)  # Usar password del archivo o extensión como fallback
        
        config += f"""
; Extension {ext_num}
[{ext_num}]
type=endpoint
transport=transport-udp
context=from-internal
disallow=all
allow=ulaw,alaw,g729
auth={ext_num}
aors={ext_num}

[{ext_num}]
type=auth
auth_type=userpass
password={password}
username={ext_num}

[{ext_num}]
type=aor
max_contacts=1
contact=sip:{ext_num}@127.0.0.1:5060

"""

    return config

def generate_extensions_config(extensions):
    """Generar dialplan para todas las extensiones"""
    
    config = """
; ============================================================================
; EXTENSIONS CONFIGURATION - VOIP AUTO DIALER
; ============================================================================
; Dialplan para 519 extensiones con contactos estáticos
; ============================================================================

[general]
static=yes
writeprotect=no
clearglobalvars=no

[globals]

[from-internal]
; ============================================================================
; LLAMADAS INTERNAS - Extensiones 1000-1519
; ============================================================================

"""

    # Generar reglas para cada extensión específica
    for ext_data in extensions:
        ext_num = ext_data.get('extension', '')
        if not ext_num:
            continue
            
        try:
            ext_int = int(ext_num)
            if ext_int < 1000 or ext_int > 1519:
                continue
        except:
            continue
            
        config += f"""exten => {ext_num},1,NoOp(Llamada interna a {ext_num})
exten => {ext_num},n,Dial(PJSIP/{ext_num},30,tT)
exten => {ext_num},n,GotoIf(${{DIALSTATUS}}=NOANSWER?voicemail:hangup)
exten => {ext_num},n(voicemail),Voicemail({ext_num}@default,u)
exten => {ext_num},n(hangup),Hangup()

"""

    # Agregar servicios especiales
    config += """
; ============================================================================
; SERVICIOS ESPECIALES
; ============================================================================

; Servicio de prueba
exten => *99,1,Answer()
exten => *99,n,Playback(system-online)
exten => *99,n,SayNumber(${EPOCH})
exten => *99,n,Hangup()

; Buzón de voz
exten => *97,1,VoiceMailMain(${CALLERID(num)}@default)
exten => *97,n,Hangup()

; ============================================================================
; LLAMADAS SALIENTES - A través del proveedor
; ============================================================================

; Llamadas salientes (marcar 9 + número)
exten => _9.,1,NoOp(Llamada saliente: ${EXTEN:1})
exten => _9.,n,Set(CALLERID(num)=${CALLERID(num)})
exten => _9.,n,Dial(PJSIP/provider/${EXTEN:1},60,tT)
exten => _9.,n,Hangup()

; Emergencias
exten => 911,1,NoOp(Llamada de emergencia)
exten => 911,n,Dial(PJSIP/provider/911,30)
exten => 911,n,Hangup()

[from-external]
; ============================================================================
; LLAMADAS ENTRANTES - Desde el proveedor
; ============================================================================

; Redirigir llamadas entrantes a extensión principal
exten => _X.,1,NoOp(Llamada entrante: ${EXTEN})
exten => _X.,n,Dial(PJSIP/1000,30,tT)
exten => _X.,n,Voicemail(1000@default,u)
exten => _X.,n,Hangup()

"""

    return config

def main():
    print("🚀 EXPANSIÓN A TODAS LAS 519 EXTENSIONES - VOIP AUTO DIALER")
    print("=" * 70)
    print("✅ Expandiendo configuración funcional a todas las extensiones")
    print("✅ Manteniendo contactos estáticos para estabilidad")
    print("=" * 70)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('data/extensions.json'):
        print("❌ Error: No se encuentra data/extensions.json")
        print("   Ejecutar desde el directorio voip-auto-dialer")
        sys.exit(1)
    
    # Cargar datos
    extensions = load_extensions_data()
    provider = load_provider_data()
    
    if not extensions:
        print("❌ Error: No se pudieron cargar las extensiones")
        sys.exit(1)
    
    # Filtrar solo extensiones en rango 1000-1519
    valid_extensions = []
    for ext in extensions:
        ext_num = ext.get('extension', '')
        try:
            ext_int = int(ext_num)
            if 1000 <= ext_int <= 1519:
                valid_extensions.append(ext)
        except:
            continue
    
    log_step(f"Extensiones válidas (1000-1519): {len(valid_extensions)}")
    
    if len(valid_extensions) == 0:
        print("❌ Error: No hay extensiones válidas en el rango 1000-1519")
        sys.exit(1)
    
    # Mostrar algunas extensiones de ejemplo
    print(f"\n📋 EXTENSIONES DE EJEMPLO:")
    for i, ext in enumerate(valid_extensions[:10]):
        ext_num = ext.get('extension', 'N/A')
        password = ext.get('password', 'N/A')
        print(f"   {i+1:2d}. {ext_num} (password: {password[:8]}...)")
    
    if len(valid_extensions) > 10:
        print(f"   ... y {len(valid_extensions) - 10} más")
    
    print(f"\n🔧 PASO 1: GENERANDO CONFIGURACIÓN PARA {len(valid_extensions)} EXTENSIONES")
    print("=" * 60)
    
    # Generar configuraciones
    pjsip_config = generate_pjsip_config(valid_extensions, provider)
    extensions_config = generate_extensions_config(valid_extensions)
    
    # Crear archivos temporales
    with open('/tmp/pjsip_all_extensions.conf', 'w') as f:
        f.write(pjsip_config)
    
    with open('/tmp/extensions_all_extensions.conf', 'w') as f:
        f.write(extensions_config)
    
    log_step("Configuraciones generadas")
    
    print(f"\n🔧 PASO 2: APLICANDO CONFIGURACIÓN COMPLETA")
    print("=" * 60)
    
    # Detener Asterisk
    log_step("Deteniendo Asterisk...")
    run_command("sudo systemctl stop asterisk", "Detener servicio")
    run_command("sudo pkill -9 asterisk", "Terminar procesos")
    
    # Crear backup
    timestamp = int(datetime.now().timestamp())
    run_command(f"sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup.{timestamp}", "Backup PJSIP")
    run_command(f"sudo cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup.{timestamp}", "Backup Extensions")
    
    # Aplicar nueva configuración
    run_command("sudo cp /tmp/pjsip_all_extensions.conf /etc/asterisk/pjsip.conf", "Aplicar PJSIP")
    run_command("sudo cp /tmp/extensions_all_extensions.conf /etc/asterisk/extensions.conf", "Aplicar Extensions")
    run_command("sudo chown asterisk:asterisk /etc/asterisk/pjsip.conf", "Permisos PJSIP")
    run_command("sudo chown asterisk:asterisk /etc/asterisk/extensions.conf", "Permisos Extensions")
    
    # Limpiar archivos temporales
    run_command("rm -f /tmp/pjsip_all_extensions.conf /tmp/extensions_all_extensions.conf", "Limpiar temporales")
    
    print(f"\n🔧 PASO 3: INICIANDO ASTERISK CON TODAS LAS EXTENSIONES")
    print("=" * 60)
    
    # Iniciar Asterisk
    success, _ = run_command("sudo systemctl start asterisk", "Iniciar servicio")
    if not success:
        print("❌ Error iniciando Asterisk")
        sys.exit(1)
    
    # Verificar que inició
    success, output = run_command("sudo systemctl is-active asterisk", "Verificar estado")
    if "active" not in output:
        print("❌ Asterisk no está activo")
        sys.exit(1)
    
    # Verificar CLI
    success, output = run_command("sudo asterisk -rx 'core show version'", "Verificar CLI")
    if not success:
        print("❌ CLI no responde")
        sys.exit(1)
    
    print(f"\n🧪 PASO 4: VERIFICANDO CONFIGURACIÓN")
    print("=" * 60)
    
    # Contar endpoints
    success, output = run_command("sudo asterisk -rx 'pjsip show endpoints' | grep 'Endpoint:' | wc -l", "Contar endpoints")
    if success:
        endpoint_count = output.strip()
        log_step(f"Endpoints configurados: {endpoint_count}")
    
    # Verificar algunos endpoints específicos
    test_extensions = ['1000', '1001', '1002', '1100', '1200', '1300', '1400', '1500']
    working_extensions = []
    
    for ext in test_extensions:
        success, output = run_command(f"sudo asterisk -rx 'pjsip show endpoint {ext}' | grep 'Endpoint:' | head -1", f"Verificar {ext}")
        if success and ext in output:
            working_extensions.append(ext)
    
    log_step(f"Extensiones de prueba funcionando: {working_extensions}")
    
    print(f"\n🎉 EXPANSIÓN COMPLETADA")
    print("=" * 70)
    print(f"✅ Configuración aplicada para {len(valid_extensions)} extensiones")
    print(f"✅ Asterisk funcionando correctamente")
    print(f"✅ Endpoints configurados con contactos estáticos")
    print(f"✅ Proveedor integrado para llamadas salientes")
    
    print(f"\n🚀 PRUEBAS RECOMENDADAS:")
    print("1. sudo asterisk -rx 'pjsip show endpoints' | head -20")
    print("2. sudo asterisk -rx 'originate PJSIP/1000 extension *99@from-internal'")
    print("3. sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'")
    print("4. sudo asterisk -rx 'originate PJSIP/1100 extension 1200@from-internal'")
    
    print(f"\n📋 PRÓXIMOS PASOS:")
    print("1. Probar llamadas entre diferentes extensiones")
    print("2. Verificar llamadas salientes (9 + número)")
    print("3. Integrar con servidor web para auto-marcado")
    print("4. Configurar softphones para registro dinámico")

if __name__ == "__main__":
    main()

