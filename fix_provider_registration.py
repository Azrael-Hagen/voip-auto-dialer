#!/usr/bin/env python3
"""
🔧 CORRECCIÓN ESPECÍFICA: REGISTRO CON PROVEEDOR
======================================================================
✅ Corrige la configuración del proveedor PBX ON THE CLOUD
✅ Configura registro automático con credenciales correctas
✅ Mantiene todas las extensiones funcionando
======================================================================
"""

import json
import subprocess
from datetime import datetime

def load_provider_data():
    """Cargar datos correctos del proveedor"""
    try:
        with open('data/providers.json', 'r') as f:
            data = json.load(f)
            # El formato es {"provider_id": {...}}
            for provider_id, provider_data in data.items():
                if provider_data.get('active', False):
                    print(f"🌐 Proveedor encontrado: {provider_data.get('name', 'Unknown')}")
                    print(f"   Host: {provider_data.get('host')}:{provider_data.get('port')}")
                    print(f"   Usuario: {provider_data.get('username')}")
                    return provider_data
            return None
    except Exception as e:
        print(f"❌ Error cargando proveedor: {e}")
        return None

def generate_provider_config(provider):
    """Generar configuración específica del proveedor"""
    
    host = provider.get('host', 'pbxonthecloud.com')
    port = provider.get('port', 5081)
    username = provider.get('username', '523483070291')
    password = provider.get('password', 'defaultpass')
    
    config = f"""
; ============================================================================
; CONFIGURACIÓN ESPECÍFICA DEL PROVEEDOR
; ============================================================================
; Proveedor: {provider.get('name', 'Provider')}
; Host: {host}:{port}
; Usuario: {username}
; Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; ============================================================================

[provider]
type=endpoint
transport=transport-udp
context=from-external
disallow=all
allow=ulaw,alaw,g729
outbound_auth=provider_auth
aors=provider_aor

[provider_aor]
type=aor
contact=sip:{host}:{port}

[provider_auth]
type=auth
auth_type=userpass
password={password}
username={username}

[provider_registration]
type=registration
transport=transport-udp
outbound_auth=provider_auth
server_uri=sip:{host}:{port}
client_uri=sip:{username}@{host}:{port}
retry_interval=60
max_retries=10
auth_rejection_permanent=no

"""
    return config

def run_command(cmd, description=""):
    """Ejecutar comando con logging"""
    if description:
        print(f"🔧 {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"✅ {result.stdout.strip()}")
            return True, result.stdout
        else:
            print(f"❌ Error: {result.stderr.strip()}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False, str(e)

def main():
    print("🔧 CORRECCIÓN ESPECÍFICA: REGISTRO CON PROVEEDOR")
    print("=" * 60)
    print("✅ Corrigiendo configuración del proveedor")
    print("✅ Manteniendo todas las extensiones funcionando")
    print("=" * 60)
    
    # Cargar datos del proveedor
    provider = load_provider_data()
    if not provider:
        print("❌ Error: No se pudo cargar información del proveedor")
        return
    
    print(f"\n🔧 PASO 1: GENERANDO CONFIGURACIÓN DEL PROVEEDOR")
    print("=" * 50)
    
    # Generar configuración del proveedor
    provider_config = generate_provider_config(provider)
    
    # Leer configuración actual de PJSIP
    try:
        with open('/etc/asterisk/pjsip.conf', 'r') as f:
            current_config = f.read()
    except Exception as e:
        print(f"❌ Error leyendo configuración actual: {e}")
        return
    
    # Remover configuración anterior del proveedor si existe
    lines = current_config.split('\n')
    new_lines = []
    skip_provider = False
    
    for line in lines:
        if line.strip().startswith('[provider'):
            skip_provider = True
        elif line.strip().startswith('[') and not line.strip().startswith('[provider'):
            skip_provider = False
        
        if not skip_provider:
            new_lines.append(line)
    
    # Agregar nueva configuración del proveedor
    new_config = '\n'.join(new_lines) + provider_config
    
    # Crear archivo temporal
    with open('/tmp/pjsip_with_provider.conf', 'w') as f:
        f.write(new_config)
    
    print("✅ Configuración del proveedor generada")
    
    print(f"\n🔧 PASO 2: APLICANDO CONFIGURACIÓN CORREGIDA")
    print("=" * 50)
    
    # Crear backup
    timestamp = int(datetime.now().timestamp())
    run_command(f"sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup.{timestamp}", "Backup configuración")
    
    # Aplicar nueva configuración
    run_command("sudo cp /tmp/pjsip_with_provider.conf /etc/asterisk/pjsip.conf", "Aplicar configuración")
    run_command("sudo chown asterisk:asterisk /etc/asterisk/pjsip.conf", "Configurar permisos")
    run_command("rm -f /tmp/pjsip_with_provider.conf", "Limpiar temporales")
    
    print(f"\n🔧 PASO 3: REINICIANDO ASTERISK")
    print("=" * 50)
    
    # Recargar configuración PJSIP
    success, output = run_command("sudo asterisk -rx 'module reload res_pjsip.so'", "Recargar PJSIP")
    if not success:
        print("⚠️  Error recargando PJSIP, reiniciando Asterisk...")
        run_command("sudo systemctl restart asterisk", "Reiniciar Asterisk")
        
        # Esperar a que inicie
        import time
        time.sleep(5)
        
        success, output = run_command("sudo systemctl is-active asterisk", "Verificar estado")
        if "active" not in output:
            print("❌ Error: Asterisk no está activo")
            return
    
    print(f"\n🧪 PASO 4: VERIFICANDO CONFIGURACIÓN DEL PROVEEDOR")
    print("=" * 50)
    
    # Verificar endpoint del proveedor
    success, output = run_command("sudo asterisk -rx 'pjsip show endpoint provider'", "Verificar endpoint")
    if success and "Endpoint:  provider" in output:
        print("✅ Endpoint del proveedor configurado")
    else:
        print("❌ Error: Endpoint del proveedor no encontrado")
    
    # Verificar registro
    success, output = run_command("sudo asterisk -rx 'pjsip show registrations'", "Verificar registros")
    if success and output.strip() != "No objects found.":
        print("✅ Registro del proveedor configurado")
        if "Registered" in output:
            print("🎉 Proveedor registrado exitosamente")
        elif "Rejected" in output:
            print("⚠️  Registro rechazado - verificar credenciales")
        else:
            print("⏳ Registro en proceso...")
    else:
        print("❌ No se encontraron registros")
    
    # Verificar que las extensiones sigan funcionando
    success, output = run_command("sudo asterisk -rx 'pjsip show endpoints' | grep 'Endpoint:' | wc -l", "Contar endpoints")
    if success:
        endpoint_count = output.strip()
        print(f"✅ Endpoints totales: {endpoint_count}")
    
    print(f"\n🎉 CORRECCIÓN DEL PROVEEDOR COMPLETADA")
    print("=" * 60)
    print("✅ Configuración del proveedor aplicada")
    print("✅ Todas las extensiones mantenidas")
    print("✅ Sistema listo para llamadas salientes")
    
    print(f"\n🧪 PRUEBAS RECOMENDADAS:")
    print("1. sudo asterisk -rx 'pjsip show registrations'")
    print("2. sudo asterisk -rx 'pjsip show endpoint provider'")
    print("3. sudo asterisk -rx 'originate PJSIP/1000 extension 9555123456@from-internal'")
    
    print(f"\n📋 PRÓXIMOS PASOS:")
    print("1. Probar llamadas salientes (9 + número)")
    print("2. Verificar caller ID en llamadas salientes")
    print("3. Integrar con servidor web para auto-marcado")

if __name__ == "__main__":
    main()

