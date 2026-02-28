#!/usr/bin/env python3
"""
🚀 GENERADOR DE CONFIGURACIÓN ASTERISK - VOIP AUTO DIALER
======================================================================
✅ Genera configuración PJSIP y Extensions para todas las 519 extensiones
✅ Mantiene contactos estáticos para estabilidad
✅ Crea archivos listos para aplicar manualmente
======================================================================
"""

import json
import os
from datetime import datetime

def load_extensions_data():
    """Cargar datos de extensiones del proyecto"""
    try:
        with open('data/extensions.json', 'r') as f:
            data = json.load(f)
            extensions = []
            for ext_num, ext_data in data.items():
                if isinstance(ext_data, dict):
                    ext_data['extension'] = ext_num
                    extensions.append(ext_data)
            
            print(f"📞 Extensiones encontradas: {len(extensions)}")
            return extensions
    except Exception as e:
        print(f"❌ Error cargando extensiones: {e}")
        return []

def load_provider_data():
    """Cargar datos del proveedor"""
    try:
        with open('data/providers.json', 'r') as f:
            data = json.load(f)
            providers = data.get('providers', [])
            if providers:
                provider = providers[0]
                print(f"🌐 Proveedor: {provider.get('name', 'Unknown')}")
                return provider
            return None
    except Exception as e:
        print(f"❌ Error cargando proveedor: {e}")
        return None

def generate_pjsip_config(extensions, provider):
    """Generar configuración PJSIP completa"""
    
    config = f"""
; ============================================================================
; PJSIP CONFIGURATION - VOIP AUTO DIALER
; ============================================================================
; Generado automáticamente: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; Extensiones: 1000-1519 ({len(extensions)} total)
; Contactos estáticos para estabilidad
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
    print(f"🔧 Generando configuración PJSIP para {len(extensions)} extensiones...")
    
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
            
        password = ext_data.get('password', ext_num)
        
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
    
    config = f"""
; ============================================================================
; EXTENSIONS CONFIGURATION - VOIP AUTO DIALER
; ============================================================================
; Generado automáticamente: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; Dialplan para {len(extensions)} extensiones con contactos estáticos
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

    print(f"🔧 Generando dialplan para {len(extensions)} extensiones...")

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
    print("🚀 GENERADOR DE CONFIGURACIÓN ASTERISK - VOIP AUTO DIALER")
    print("=" * 70)
    print("✅ Generando configuración para todas las 519 extensiones")
    print("✅ Contactos estáticos para máxima estabilidad")
    print("=" * 70)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('data/extensions.json'):
        print("❌ Error: No se encuentra data/extensions.json")
        print("   Ejecutar desde el directorio voip-auto-dialer")
        return
    
    # Cargar datos
    extensions = load_extensions_data()
    provider = load_provider_data()
    
    if not extensions:
        print("❌ Error: No se pudieron cargar las extensiones")
        return
    
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
    
    print(f"✅ Extensiones válidas (1000-1519): {len(valid_extensions)}")
    
    if len(valid_extensions) == 0:
        print("❌ Error: No hay extensiones válidas en el rango 1000-1519")
        return
    
    # Mostrar algunas extensiones de ejemplo
    print(f"\n📋 EXTENSIONES DE EJEMPLO:")
    for i, ext in enumerate(valid_extensions[:10]):
        ext_num = ext.get('extension', 'N/A')
        password = ext.get('password', 'N/A')
        print(f"   {i+1:2d}. {ext_num} (password: {password[:8]}...)")
    
    if len(valid_extensions) > 10:
        print(f"   ... y {len(valid_extensions) - 10} más")
    
    print(f"\n🔧 GENERANDO ARCHIVOS DE CONFIGURACIÓN")
    print("=" * 60)
    
    # Generar configuraciones
    pjsip_config = generate_pjsip_config(valid_extensions, provider)
    extensions_config = generate_extensions_config(valid_extensions)
    
    # Crear directorio de salida
    output_dir = "asterisk_config_generated"
    os.makedirs(output_dir, exist_ok=True)
    
    # Guardar archivos
    pjsip_file = f"{output_dir}/pjsip.conf"
    extensions_file = f"{output_dir}/extensions.conf"
    
    with open(pjsip_file, 'w') as f:
        f.write(pjsip_config)
    
    with open(extensions_file, 'w') as f:
        f.write(extensions_config)
    
    print(f"✅ Archivo PJSIP generado: {pjsip_file}")
    print(f"✅ Archivo Extensions generado: {extensions_file}")
    
    # Crear script de aplicación
    apply_script = f"{output_dir}/apply_config.sh"
    with open(apply_script, 'w') as f:
        f.write(f"""#!/bin/bash
# Script para aplicar configuración de Asterisk
# Generado automáticamente: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🚀 APLICANDO CONFIGURACIÓN ASTERISK - {len(valid_extensions)} EXTENSIONES"
echo "=" * 70

# Crear backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "📋 Creando backup..."
sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup.$TIMESTAMP
sudo cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup.$TIMESTAMP

# Detener Asterisk
echo "🛑 Deteniendo Asterisk..."
sudo systemctl stop asterisk
sudo pkill -9 asterisk

# Aplicar nueva configuración
echo "🔧 Aplicando nueva configuración..."
sudo cp {pjsip_file} /etc/asterisk/pjsip.conf
sudo cp {extensions_file} /etc/asterisk/extensions.conf

# Configurar permisos
sudo chown asterisk:asterisk /etc/asterisk/pjsip.conf
sudo chown asterisk:asterisk /etc/asterisk/extensions.conf

# Iniciar Asterisk
echo "🚀 Iniciando Asterisk..."
sudo systemctl start asterisk

# Verificar estado
echo "🧪 Verificando estado..."
sleep 3
sudo systemctl is-active asterisk
sudo asterisk -rx 'core show version'

echo "✅ Configuración aplicada exitosamente"
echo "🧪 Pruebas recomendadas:"
echo "   sudo asterisk -rx 'pjsip show endpoints' | head -20"
echo "   sudo asterisk -rx 'originate PJSIP/1000 extension *99@from-internal'"
echo "   sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'"
""")
    
    # Hacer ejecutable el script
    os.chmod(apply_script, 0o755)
    
    print(f"✅ Script de aplicación: {apply_script}")
    
    print(f"\n🎉 CONFIGURACIÓN GENERADA EXITOSAMENTE")
    print("=" * 70)
    print(f"✅ {len(valid_extensions)} extensiones configuradas (1000-1519)")
    print(f"✅ Contactos estáticos para máxima estabilidad")
    print(f"✅ Proveedor integrado para llamadas salientes")
    print(f"✅ Archivos listos en: {output_dir}/")
    
    print(f"\n🚀 PARA APLICAR LA CONFIGURACIÓN:")
    print(f"   cd {output_dir}")
    print(f"   ./apply_config.sh")
    
    print(f"\n📋 ARCHIVOS GENERADOS:")
    print(f"   📄 {pjsip_file}")
    print(f"   📄 {extensions_file}")
    print(f"   🔧 {apply_script}")
    
    print(f"\n🧪 DESPUÉS DE APLICAR, PROBAR:")
    print("   sudo asterisk -rx 'pjsip show endpoints' | head -20")
    print("   sudo asterisk -rx 'originate PJSIP/1000 extension *99@from-internal'")
    print("   sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'")

if __name__ == "__main__":
    main()

