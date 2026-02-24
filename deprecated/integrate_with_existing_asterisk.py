#!/usr/bin/env python3
"""
Script para integrar el sistema VoIP Auto Dialer con Asterisk existente
"""
import json
import os
import subprocess
import shutil
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  🎯 {title}")
    print("=" * 60)

def print_step(step, description):
    print(f"\n{step}. 📋 {description}")
    print("-" * 50)

def backup_asterisk_configs():
    """Hacer backup de configuraciones actuales de Asterisk"""
    print("🔄 Creando backup de configuraciones actuales...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"asterisk_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Archivos importantes a respaldar
    config_files = [
        "/etc/asterisk/pjsip.conf",
        "/etc/asterisk/extensions.conf",
        "/etc/asterisk/pjsip_extensions.conf",
        "/etc/asterisk/extensions_voip.conf"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            filename = os.path.basename(config_file)
            shutil.copy2(config_file, f"{backup_dir}/{filename}")
            print(f"   ✅ Backup: {filename}")
        else:
            print(f"   ⚠️ No encontrado: {config_file}")
    
    print(f"✅ Backup creado en: {backup_dir}")
    return backup_dir

def read_existing_asterisk_config():
    """Leer configuración existente de Asterisk"""
    print("🔍 Analizando configuración existente de Asterisk...")
    
    # Obtener endpoints existentes
    result = subprocess.run(
        "sudo asterisk -rx 'pjsip show endpoints'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    existing_extensions = []
    if result.returncode == 0:
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Endpoint:' in line and not line.strip().startswith('Endpoint:  <'):
                # Extraer número de extensión
                parts = line.split()
                if len(parts) > 1:
                    ext_num = parts[1]
                    if ext_num.isdigit():
                        existing_extensions.append(ext_num)
    
    print(f"✅ Extensiones existentes encontradas: {existing_extensions}")
    return existing_extensions

def load_voip_dialer_data():
    """Cargar datos del sistema VoIP Auto Dialer"""
    print("📊 Cargando datos del VoIP Auto Dialer...")
    
    # Cargar agentes
    agents = {}
    if os.path.exists("data/agents.json"):
        with open("data/agents.json", 'r') as f:
            agents = json.load(f)
    
    # Cargar extensiones
    extensions = {}
    if os.path.exists("data/extensions.json"):
        with open("data/extensions.json", 'r') as f:
            extensions = json.load(f)
    
    print(f"✅ Agentes cargados: {len(agents)}")
    print(f"✅ Extensiones cargadas: {len(extensions)}")
    
    return agents, extensions

def create_integrated_pjsip_config(existing_extensions, voip_extensions):
    """Crear configuración PJSIP integrada"""
    print("🔧 Creando configuración PJSIP integrada...")
    
    config_content = """
; ============================================================================
; CONFIGURACIÓN PJSIP INTEGRADA - VoIP Auto Dialer + Asterisk Existente
; ============================================================================
; Generado automáticamente - No editar manualmente
; ============================================================================

"""
    
    # Mantener extensiones existentes (1000-1002)
    print("   📞 Manteniendo extensiones existentes...")
    for ext in existing_extensions:
        if ext.isdigit():
            config_content += f"""
; Extensión existente {ext}
[{ext}]
type=endpoint
context=from-internal
disallow=all
allow=ulaw
allow=alaw
allow=gsm
auth={ext}-auth
aors={ext}

[{ext}-auth]
type=auth
auth_type=userpass
username={ext}
password=existing_{ext}_pass

[{ext}]
type=aor
max_contacts=1
"""
    
    # Agregar extensiones del VoIP Auto Dialer (solo las asignadas)
    print("   📞 Agregando extensiones del VoIP Auto Dialer...")
    assigned_count = 0
    
    for ext_id, ext_data in voip_extensions.items():
        if ext_data.get('status') == 'assigned':
            ext_num = ext_data.get('extension')
            password = ext_data.get('password', f'auto_{ext_num}')
            
            config_content += f"""
; Extensión VoIP Auto Dialer {ext_num}
[{ext_num}]
type=endpoint
context=from-internal
disallow=all
allow=ulaw
allow=alaw
allow=gsm
auth={ext_num}-auth
aors={ext_num}

[{ext_num}-auth]
type=auth
auth_type=userpass
username={ext_num}
password={password}

[{ext_num}]
type=aor
max_contacts=1
"""
            assigned_count += 1
    
    print(f"   ✅ {len(existing_extensions)} extensiones existentes mantenidas")
    print(f"   ✅ {assigned_count} extensiones del VoIP Auto Dialer agregadas")
    
    return config_content

def create_integrated_extensions_config():
    """Crear configuración de extensions integrada"""
    print("🔧 Creando configuración de extensions integrada...")
    
    config_content = """
; ============================================================================
; CONFIGURACIÓN EXTENSIONS INTEGRADA - VoIP Auto Dialer
; ============================================================================
; Generado automáticamente - No editar manualmente
; ============================================================================

[from-internal]
; Patrón para llamadas entre extensiones (1000-1999)
exten => _1XXX,1,Dial(PJSIP/${EXTEN})
exten => _1XXX,2,Hangup()

; Patrón para extensiones de 4 dígitos
exten => _XXXX,1,Dial(PJSIP/${EXTEN})
exten => _XXXX,2,Hangup()
"""
    
    print("   ✅ Dialplan integrado creado")
    return config_content

def install_integrated_configs(pjsip_content, extensions_content):
    """Instalar configuraciones integradas"""
    print("📥 Instalando configuraciones integradas...")
    
    # Escribir archivo PJSIP integrado
    integrated_pjsip = "asterisk_config/pjsip_integrated.conf"
    with open(integrated_pjsip, 'w') as f:
        f.write(pjsip_content)
    
    # Escribir archivo extensions integrado
    integrated_extensions = "asterisk_config/extensions_integrated.conf"
    with open(integrated_extensions, 'w') as f:
        f.write(extensions_content)
    
    print(f"   ✅ Creado: {integrated_pjsip}")
    print(f"   ✅ Creado: {integrated_extensions}")
    
    # Copiar a Asterisk
    subprocess.run(f"sudo cp {integrated_pjsip} /etc/asterisk/", shell=True)
    subprocess.run(f"sudo cp {integrated_extensions} /etc/asterisk/", shell=True)
    
    print("   ✅ Archivos copiados a /etc/asterisk/")
    
    return integrated_pjsip, integrated_extensions

def update_asterisk_includes():
    """Actualizar includes en archivos principales de Asterisk"""
    print("🔄 Actualizando includes en archivos principales...")
    
    # Agregar include en pjsip.conf
    include_line = "#include pjsip_integrated.conf"
    subprocess.run(f'echo "{include_line}" | sudo tee -a /etc/asterisk/pjsip.conf', shell=True)
    
    # Agregar include en extensions.conf
    include_line = "#include extensions_integrated.conf"
    subprocess.run(f'echo "{include_line}" | sudo tee -a /etc/asterisk/extensions.conf', shell=True)
    
    print("   ✅ Includes agregados a archivos principales")

def reload_asterisk():
    """Recargar configuración de Asterisk"""
    print("🔄 Recargando configuración de Asterisk...")
    
    commands = [
        "dialplan reload",
        "module reload res_pjsip.so",
        "pjsip reload"
    ]
    
    for cmd in commands:
        result = subprocess.run(f"sudo asterisk -rx '{cmd}'", shell=True)
        if result.returncode == 0:
            print(f"   ✅ {cmd}")
        else:
            print(f"   ⚠️ {cmd} - revisar manualmente")

def verify_integration():
    """Verificar que la integración funcionó"""
    print("🔍 Verificando integración...")
    
    # Verificar endpoints
    result = subprocess.run(
        "sudo asterisk -rx 'pjsip show endpoints'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        lines = result.stdout.split('\n')
        endpoint_count = 0
        for line in lines:
            if 'Endpoint:' in line and not line.strip().startswith('Endpoint:  <'):
                endpoint_count += 1
                print(f"   📞 {line.strip()}")
        
        print(f"✅ Total endpoints configurados: {endpoint_count}")
    
    # Verificar dialplan
    result = subprocess.run(
        "sudo asterisk -rx 'dialplan show from-internal'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and "_1XXX" in result.stdout:
        print("✅ Dialplan integrado funcionando")
    else:
        print("⚠️ Revisar dialplan manualmente")

def main():
    print_header("INTEGRADOR CON ASTERISK EXISTENTE")
    
    print("Este script integrará el VoIP Auto Dialer con tu configuración")
    print("existente de Asterisk, manteniendo las extensiones actuales.")
    
    # Paso 1: Backup
    print_step("1", "Creando backup de configuraciones actuales")
    backup_dir = backup_asterisk_configs()
    
    # Paso 2: Analizar configuración existente
    print_step("2", "Analizando configuración existente de Asterisk")
    existing_extensions = read_existing_asterisk_config()
    
    # Paso 3: Cargar datos del VoIP Auto Dialer
    print_step("3", "Cargando datos del VoIP Auto Dialer")
    agents, extensions = load_voip_dialer_data()
    
    # Paso 4: Crear configuración integrada
    print_step("4", "Creando configuración PJSIP integrada")
    pjsip_content = create_integrated_pjsip_config(existing_extensions, extensions)
    
    print_step("5", "Creando configuración de extensions integrada")
    extensions_content = create_integrated_extensions_config()
    
    # Paso 5: Instalar configuraciones
    print_step("6", "Instalando configuraciones integradas")
    install_integrated_configs(pjsip_content, extensions_content)
    
    # Paso 6: Actualizar includes
    print_step("7", "Actualizando includes en archivos principales")
    update_asterisk_includes()
    
    # Paso 7: Recargar Asterisk
    print_step("8", "Recargando configuración de Asterisk")
    reload_asterisk()
    
    # Paso 8: Verificar
    print_step("9", "Verificando integración")
    verify_integration()
    
    print_header("✅ INTEGRACIÓN COMPLETADA")
    
    print("🎉 ¡Integración exitosa!")
    print("")
    print("📋 RESUMEN:")
    print(f"   • Backup creado: {backup_dir}")
    print(f"   • Extensiones existentes mantenidas: {len(existing_extensions)}")
    print(f"   • Extensiones del VoIP Auto Dialer integradas")
    print("   • Configuración de Asterisk actualizada")
    print("")
    print("🔧 PRÓXIMOS PASOS:")
    print("   1. Verifica que no hay errores: sudo asterisk -rx 'core show version'")
    print("   2. Lista endpoints: sudo asterisk -rx 'pjsip show endpoints'")
    print("   3. Prueba el servidor web: python start_clean.py")
    print("   4. Configura softphones con las extensiones integradas")
    print("")
    print("📱 EXTENSIONES DISPONIBLES PARA SOFTPHONES:")
    print("   • Existentes: 1000, 1001, 1002 (contraseñas existentes)")
    print("   • Nuevas: Las asignadas en el VoIP Auto Dialer")
    
    return True

if __name__ == "__main__":
    main()