#!/usr/bin/env python3
"""
Script de corrección para problemas de configuración PJSIP
"""

import subprocess
import os
import json
import shutil
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  🔧 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n{step}. 📋 {description}")
    print("-" * 50)

def run_command(cmd, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: OK")
            return True, result.stdout
        else:
            print(f"❌ {description}: FALLÓ")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False, str(e)

def backup_asterisk_config():
    """Crear backup de configuración actual"""
    print("🔧 Creando backup de configuración actual...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"asterisk_backup_{timestamp}"
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup de archivos críticos
        files_to_backup = [
            "/etc/asterisk/pjsip.conf",
            "/etc/asterisk/extensions.conf",
            "/etc/asterisk/pjsip_extensions.conf",
            "/etc/asterisk/extensions_voip.conf"
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                shutil.copy2(file_path, os.path.join(backup_dir, filename))
                print(f"   ✅ Backup: {filename}")
        
        print(f"✅ Backup creado en: {backup_dir}")
        return True, backup_dir
        
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return False, None

def regenerate_pjsip_config():
    """Regenerar configuración PJSIP limpia"""
    print("🔧 Regenerando configuración PJSIP...")
    
    try:
        # Cargar extensiones del sistema
        with open('data/extensions.json', 'r') as f:
            extensions = json.load(f)
        
        # Generar configuración PJSIP limpia
        pjsip_config = []
        pjsip_config.append("; Configuración PJSIP generada automáticamente")
        pjsip_config.append(f"; Generado: {datetime.now()}")
        pjsip_config.append("")
        
        assigned_count = 0
        for ext_id, ext_data in extensions.items():
            if ext_data.get('status') == 'assigned':
                password = ext_data.get('password', 'defaultpass')
                
                # Endpoint
                pjsip_config.append(f"[{ext_id}]")
                pjsip_config.append("type=endpoint")
                pjsip_config.append(f"auth={ext_id}-auth")
                pjsip_config.append(f"aors={ext_id}")
                pjsip_config.append("context=from-internal")
                pjsip_config.append("disallow=all")
                pjsip_config.append("allow=ulaw,alaw,gsm")
                pjsip_config.append("")
                
                # Auth
                pjsip_config.append(f"[{ext_id}-auth]")
                pjsip_config.append("type=auth")
                pjsip_config.append("auth_type=userpass")
                pjsip_config.append(f"username={ext_id}")
                pjsip_config.append(f"password={password}")
                pjsip_config.append("")
                
                # AOR
                pjsip_config.append(f"[{ext_id}]")
                pjsip_config.append("type=aor")
                pjsip_config.append("max_contacts=1")
                pjsip_config.append("remove_existing=yes")
                pjsip_config.append("")
                
                assigned_count += 1
        
        # Guardar configuración
        config_content = "\n".join(pjsip_config)
        
        # Guardar en archivo local
        with open('asterisk_config/pjsip_extensions_clean.conf', 'w') as f:
            f.write(config_content)
        
        print(f"✅ Configuración PJSIP regenerada: {assigned_count} extensiones")
        return True, assigned_count
        
    except Exception as e:
        print(f"❌ Error regenerando configuración: {e}")
        return False, 0

def fix_includes():
    """Corregir includes en archivos principales"""
    print("🔧 Corrigiendo includes en archivos principales...")
    
    try:
        # Verificar y corregir pjsip.conf
        pjsip_conf = "/etc/asterisk/pjsip.conf"
        
        # Leer contenido actual
        with open(pjsip_conf, 'r') as f:
            content = f.read()
        
        # Verificar si ya tiene nuestro include
        if "#include pjsip_extensions_clean.conf" not in content:
            # Agregar include al final
            content += "\n; Include de extensiones generadas automáticamente\n"
            content += "#include pjsip_extensions_clean.conf\n"
            
            # Escribir de vuelta
            subprocess.run(f"echo '{content}' | sudo tee {pjsip_conf} > /dev/null", 
                         shell=True, check=True)
            print("✅ Include agregado a pjsip.conf")
        else:
            print("✅ Include ya existe en pjsip.conf")
        
        return True
        
    except Exception as e:
        print(f"❌ Error corrigiendo includes: {e}")
        return False

def deploy_configuration():
    """Desplegar configuración a Asterisk"""
    print("🔧 Desplegando configuración a Asterisk...")
    
    try:
        # Copiar archivo limpio
        success, _ = run_command(
            "sudo cp asterisk_config/pjsip_extensions_clean.conf /etc/asterisk/",
            "Copiar configuración PJSIP"
        )
        
        if not success:
            return False
        
        # Establecer permisos correctos
        run_command(
            "sudo chown asterisk:asterisk /etc/asterisk/pjsip_extensions_clean.conf",
            "Establecer permisos"
        )
        
        run_command(
            "sudo chmod 644 /etc/asterisk/pjsip_extensions_clean.conf",
            "Establecer permisos de lectura"
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Error desplegando configuración: {e}")
        return False

def reload_asterisk():
    """Recargar configuración de Asterisk"""
    print("🔧 Recargando Asterisk...")
    
    commands = [
        ("sudo asterisk -rx 'module reload res_pjsip.so'", "Recargar módulo PJSIP"),
        ("sudo asterisk -rx 'pjsip reload'", "Recargar configuración PJSIP"),
        ("sudo asterisk -rx 'dialplan reload'", "Recargar dialplan")
    ]
    
    all_success = True
    for cmd, desc in commands:
        success, _ = run_command(cmd, desc)
        if not success:
            all_success = False
    
    return all_success

def verify_fix():
    """Verificar que la corrección funcionó"""
    print("🔧 Verificando corrección...")
    
    # Verificar endpoints
    success, output = run_command(
        "sudo asterisk -rx 'pjsip show endpoints'",
        "Verificar endpoints PJSIP"
    )
    
    if success and "Objects found:" in output:
        # Contar endpoints encontrados
        lines = output.split('\n')
        for line in lines:
            if "Objects found:" in line:
                count = line.split(':')[1].strip()
                print(f"✅ Endpoints encontrados: {count}")
                return True
    
    print("❌ No se encontraron endpoints")
    return False

def main():
    print_header("CORRECCIÓN DE CONFIGURACIÓN PJSIP")
    
    print("Este script corregirá los problemas de configuración PJSIP")
    print("y regenerará una configuración limpia y funcional.")
    
    # Paso 1: Backup
    print_step("1", "Crear backup de configuración actual")
    success, backup_dir = backup_asterisk_config()
    if not success:
        print("❌ No se pudo crear backup. Abortando.")
        return False
    
    # Paso 2: Regenerar configuración
    print_step("2", "Regenerar configuración PJSIP")
    success, count = regenerate_pjsip_config()
    if not success:
        print("❌ No se pudo regenerar configuración. Abortando.")
        return False
    
    # Paso 3: Corregir includes
    print_step("3", "Corregir includes")
    success = fix_includes()
    if not success:
        print("❌ No se pudieron corregir includes. Abortando.")
        return False
    
    # Paso 4: Desplegar configuración
    print_step("4", "Desplegar configuración")
    success = deploy_configuration()
    if not success:
        print("❌ No se pudo desplegar configuración. Abortando.")
        return False
    
    # Paso 5: Recargar Asterisk
    print_step("5", "Recargar Asterisk")
    success = reload_asterisk()
    if not success:
        print("⚠️ Problemas recargando Asterisk. Continuando...")
    
    # Paso 6: Verificar
    print_step("6", "Verificar corrección")
    success = verify_fix()
    
    print_header("CORRECCIÓN COMPLETADA")
    
    if success:
        print("🎉 ¡Configuración PJSIP corregida exitosamente!")
        print(f"📁 Backup guardado en: {backup_dir}")
        print("")
        print("📋 PRÓXIMOS PASOS:")
        print("   1. Configura un softphone con las credenciales")
        print("   2. Verifica que se registre correctamente")
        print("   3. Realiza una llamada de prueba")
    else:
        print("❌ La corrección no fue completamente exitosa")
        print("📋 ACCIONES RECOMENDADAS:")
        print("   1. Revisa los logs de Asterisk")
        print("   2. Verifica la sintaxis de los archivos de configuración")
        print("   3. Considera restaurar desde el backup si es necesario")
    
    return success

if __name__ == "__main__":
    main()