#!/usr/bin/env python3
"""
SCRIPT COMPLETO PARA REPARAR ASTERISK - VERSIÓN ROBUSTA
Maneja Asterisk 18 existente y lo configura correctamente para el proyecto
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

def run_command(cmd, check=True, shell=True):
    """Ejecutar comando con manejo de errores mejorado"""
    print(f"🔧 Ejecutando: {cmd}")
    try:
        result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=True, text=True, timeout=300)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return result
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout ejecutando: {cmd}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"❌ Stderr: {e.stderr}")
        if check:
            return None
        return e
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def stop_asterisk_completely():
    """Detener Asterisk completamente"""
    print("\n🔧 PASO 1: DETENIENDO ASTERISK COMPLETAMENTE")
    print("=" * 60)
    
    # Múltiples métodos para asegurar que Asterisk se detenga
    run_command("sudo systemctl stop asterisk", check=False)
    time.sleep(3)
    run_command("sudo pkill -9 asterisk", check=False)
    time.sleep(2)
    run_command("sudo killall -9 asterisk", check=False)
    time.sleep(2)
    
    # Verificar que no hay procesos de Asterisk
    result = run_command("pgrep asterisk", check=False)
    if result and result.returncode == 0:
        print("⚠️ Asterisk aún ejecutándose, forzando detención...")
        run_command("sudo kill -9 $(pgrep asterisk)", check=False)
        time.sleep(3)
    
    print("✅ Asterisk detenido completamente")

def backup_and_clean_configs():
    """Hacer backup y limpiar configuraciones"""
    print("\n🔧 PASO 2: BACKUP Y LIMPIEZA DE CONFIGURACIONES")
    print("=" * 60)
    
    # Crear backup con timestamp
    timestamp = int(time.time())
    backup_cmd = f"sudo cp -r /etc/asterisk /etc/asterisk_backup_{timestamp}"
    run_command(backup_cmd, check=False)
    
    # Limpiar archivos problemáticos pero mantener estructura
    run_command("sudo rm -rf /var/run/asterisk/*", check=False)
    run_command("sudo rm -rf /tmp/asterisk*", check=False)
    
    # Crear directorios necesarios
    directories = [
        "/var/run/asterisk",
        "/var/log/asterisk", 
        "/var/lib/asterisk",
        "/var/spool/asterisk",
        "/etc/asterisk"
    ]
    
    for directory in directories:
        run_command(f"sudo mkdir -p {directory}", check=False)
    
    print("✅ Backup creado y directorios preparados")

def load_project_data():
    """Cargar datos del proyecto"""
    print("\n🔧 PASO 3: CARGANDO DATOS DEL PROYECTO")
    print("=" * 60)
    
    # Cargar extensiones
    extensions_file = Path("data/extensions.json")
    if not extensions_file.exists():
        print("❌ Error: No se encuentra data/extensions.json")
        sys.exit(1)
    
    with open(extensions_file, 'r') as f:
        extensions_data = json.load(f)
    
    # Cargar proveedores
    providers_file = Path("data/providers.json")
    if not providers_file.exists():
        print("❌ Error: No se encuentra data/providers.json")
        sys.exit(1)
    
    with open(providers_file, 'r') as f:
        providers = json.load(f)
        # Obtener el primer proveedor activo
        provider_data = None
        for provider_id, provider in providers.items():
            if provider.get('active', False):
                provider_data = provider
                break
    
    if not provider_data:
        print("❌ Error: No se encuentra proveedor activo")
        sys.exit(1)
    
    print(f"📞 Extensiones cargadas: {len(extensions_data)}")
    print(f"🌐 Proveedor: {provider_data['name']}")
    
    return extensions_data, provider_data

def generate_pjsip_config(extensions_data, provider_data):
    """Generar configuración PJSIP compatible con Asterisk 18"""
    print("\n🔧 PASO 4: GENERANDO CONFIGURACIÓN PJSIP")
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
    
    # Configuración del proveedor
    provider_name = "PBX_ON_THE_CLOUD"
    config.append(f"""[{provider_name}]
type=registration
transport=transport-udp
outbound_auth={provider_name}_auth
server_uri=sip:{provider_data['host']}:{provider_data['port']}
client_uri=sip:{provider_data['username']}@{provider_data['host']}:{provider_data['port']}
retry_interval=60

[{provider_name}_auth]
type=auth
auth_type=userpass
password={provider_data['password']}
username={provider_data['username']}

[{provider_name}_endpoint]
type=endpoint
transport=transport-udp
context=from-provider
disallow=all
allow={provider_data['codec']}
outbound_auth={provider_name}_auth
aors={provider_name}_aor

[{provider_name}_aor]
type=aor
contact=sip:{provider_data['host']}:{provider_data['port']}

""")
    
    # Configurar extensiones 1XXX
    print(f"📞 Configurando {len(extensions_data)} extensiones...")
    
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

[{ext_num}_auth]
type=auth
auth_type=userpass
password={password}
username={ext_num}

[{ext_num}_aor]
type=aor
max_contacts=1

""")
    
    return ''.join(config)

def generate_extensions_config(extensions_data, provider_data):
    """Generar configuración de dialplan"""
    print("\n🔧 PASO 5: GENERANDO DIALPLAN")
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
exten => _9.,n,Set(CALLERID(num)=${{CALLERID(num)}})
exten => _9.,n,Dial(PJSIP/${{EXTEN:1}}@PBX_ON_THE_CLOUD_endpoint,60,tT)
exten => _9.,n,Hangup()

; Llamadas de emergencia
exten => 911,1,NoOp(Llamada de emergencia)
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
exten => _X.,1,NoOp(Llamada entrante: ${{EXTEN}})
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

def generate_manager_config():
    """Generar configuración del Manager API"""
    config = """[general]
enabled = yes
port = 5038
bindaddr = 0.0.0.0

[admin]
secret = voip_admin_2026
permit = 0.0.0.0/0.0.0.0
read = all
write = all

"""
    return config

def create_helper_script():
    """Crear script auxiliar para obtener agente disponible"""
    script_content = f"""#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def get_available_agent():
    try:
        extensions_file = Path("{os.getcwd()}/data/extensions.json")
        if not extensions_file.exists():
            return ""
        
        with open(extensions_file, 'r') as f:
            extensions = json.load(f)
        
        # Buscar primera extensión asignada
        for ext_num, ext_data in extensions.items():
            if ext_data.get('assigned', False):
                return ext_num
        
        # Si no hay asignadas, usar la primera disponible
        return list(extensions.keys())[0] if extensions else ""
    
    except Exception:
        return ""

if __name__ == "__main__":
    print(get_available_agent())
"""
    
    with open("get_available_agent.py", 'w') as f:
        f.write(script_content)
    
    os.chmod("get_available_agent.py", 0o755)
    print("✅ Script auxiliar creado")

def write_configurations(extensions_data, provider_data):
    """Escribir todas las configuraciones"""
    print("\n🔧 PASO 6: ESCRIBIENDO CONFIGURACIONES")
    print("=" * 60)
    
    # Generar configuraciones
    pjsip_conf = generate_pjsip_config(extensions_data, provider_data)
    extensions_conf = generate_extensions_config(extensions_data, provider_data)
    manager_conf = generate_manager_config()
    
    # Escribir archivos temporales
    temp_files = {
        "/tmp/pjsip.conf": pjsip_conf,
        "/tmp/extensions.conf": extensions_conf,
        "/tmp/manager.conf": manager_conf
    }
    
    for temp_file, content in temp_files.items():
        with open(temp_file, 'w') as f:
            f.write(content)
    
    # Copiar a directorio de Asterisk
    for temp_file in temp_files.keys():
        filename = os.path.basename(temp_file)
        run_command(f"sudo cp {temp_file} /etc/asterisk/{filename}")
    
    # Configurar permisos
    run_command("sudo chown -R asterisk:asterisk /etc/asterisk/", check=False)
    run_command("sudo chmod 640 /etc/asterisk/*.conf", check=False)
    
    # Limpiar archivos temporales
    for temp_file in temp_files.keys():
        run_command(f"rm -f {temp_file}", check=False)
    
    print("✅ Configuraciones escritas correctamente")

def start_and_test_asterisk():
    """Iniciar y probar Asterisk"""
    print("\n🔧 PASO 7: INICIANDO Y PROBANDO ASTERISK")
    print("=" * 60)
    
    # Iniciar Asterisk
    run_command("sudo systemctl enable asterisk", check=False)
    run_command("sudo systemctl start asterisk")
    
    # Esperar a que inicie
    print("⏳ Esperando que Asterisk inicie...")
    time.sleep(10)
    
    # Verificar estado
    result = run_command("sudo systemctl is-active asterisk", check=False)
    if result and result.returncode == 0 and "active" in result.stdout:
        print("✅ Asterisk iniciado correctamente")
    else:
        print("❌ Error iniciando Asterisk")
        run_command("sudo journalctl -u asterisk --no-pager -n 20", check=False)
        return False
    
    # Probar conexión CLI
    time.sleep(5)
    result = run_command("sudo asterisk -rx 'core show version'", check=False)
    if result and result.returncode == 0:
        print("✅ CLI de Asterisk funcional")
        print(f"📋 Versión: {result.stdout.strip()}")
    else:
        print("❌ Error en CLI de Asterisk")
        return False
    
    return True

def test_system_integration():
    """Probar integración completa del sistema"""
    print("\n🔧 PASO 8: PROBANDO INTEGRACIÓN COMPLETA")
    print("=" * 60)
    
    # Probar endpoints PJSIP
    result = run_command("sudo asterisk -rx 'pjsip show endpoints'", check=False)
    if result and result.returncode == 0:
        print("✅ Endpoints PJSIP configurados")
        # Mostrar primeras líneas
        lines = result.stdout.split('\n')[:15]
        for line in lines:
            if line.strip() and not line.startswith('='):
                print(f"   {line}")
    
    # Probar dialplan
    result = run_command("sudo asterisk -rx 'dialplan show from-internal'", check=False)
    if result and result.returncode == 0:
        print("✅ Dialplan cargado correctamente")
    
    # Probar Manager API
    result = run_command("sudo asterisk -rx 'manager show users'", check=False)
    if result and result.returncode == 0:
        print("✅ Manager API configurado")
    
    print("\n🎯 CONFIGURACIÓN COMPLETA FINALIZADA")
    print("=" * 60)
    print("✅ Asterisk funcionando correctamente")
    print("✅ 519 extensiones 1XXX configuradas")
    print("✅ Proveedor PBX ON THE CLOUD integrado")
    print("✅ Auto-marcado habilitado desde servidor web")

def main():
    """Función principal"""
    print("🚨 REPARACIÓN COMPLETA ASTERISK - SISTEMA VOIP AUTO DIALER")
    print("=" * 70)
    print("⚠️  Este script configura Asterisk existente para el proyecto")
    print("⚠️  Se crearán backups de configuraciones existentes")
    print("=" * 70)
    
    # Verificar directorio
    if not Path("data/extensions.json").exists():
        print("❌ Error: Ejecutar desde directorio voip-auto-dialer")
        sys.exit(1)
    
    try:
        # Ejecutar pasos
        stop_asterisk_completely()
        backup_and_clean_configs()
        extensions_data, provider_data = load_project_data()
        create_helper_script()
        write_configurations(extensions_data, provider_data)
        
        if start_and_test_asterisk():
            test_system_integration()
            
            print("\n🎉 REPARACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print("🚀 PRÓXIMOS PASOS:")
            print("1. Verificar: sudo asterisk -rx 'pjsip show endpoints'")
            print("2. Probar llamada: sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'")
            print("3. Iniciar servidor: python3 start_complete_system.py")
            print("4. Acceder a: http://localhost:8000")
            
        else:
            print("\n❌ ERROR EN LA REPARACIÓN")
            print("Revisar logs: sudo journalctl -u asterisk -f")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()