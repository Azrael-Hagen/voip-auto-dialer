#!/usr/bin/env python3
"""
🔧 CONFIGURACIÓN SEGURA DE ASTERISK
Aplicar configuraciones del VoIP Auto Dialer de forma incremental
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

def run_command(cmd, capture_output=True):
    """Ejecutar comando con manejo de errores"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def backup_config():
    """Crear backup de la configuración actual"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"/etc/asterisk_backup_{timestamp}"
    
    print(f"💾 Creando backup en: {backup_dir}")
    success, stdout, stderr = run_command(f"sudo cp -r /etc/asterisk {backup_dir}")
    
    if success:
        print(f"✅ Backup creado exitosamente")
        return backup_dir
    else:
        print(f"❌ Error creando backup: {stderr}")
        return None

def verify_asterisk_running():
    """Verificar que Asterisk esté ejecutándose"""
    success, stdout, stderr = run_command("sudo systemctl is-active asterisk")
    if success and "active" in stdout:
        print("✅ Asterisk está ejecutándose")
        return True
    else:
        print("❌ Asterisk no está ejecutándose")
        return False

def apply_config_file(source_file, target_file):
    """Aplicar un archivo de configuración específico"""
    if not os.path.exists(source_file):
        print(f"❌ Archivo fuente no encontrado: {source_file}")
        return False
    
    print(f"📝 Aplicando configuración: {os.path.basename(target_file)}")
    
    # Copiar archivo
    success, stdout, stderr = run_command(f"sudo cp {source_file} {target_file}")
    if not success:
        print(f"❌ Error copiando archivo: {stderr}")
        return False
    
    # Configurar permisos
    success, stdout, stderr = run_command(f"sudo chown asterisk:asterisk {target_file}")
    if not success:
        print(f"⚠️ Advertencia configurando permisos: {stderr}")
    
    print(f"✅ Configuración aplicada: {os.path.basename(target_file)}")
    return True

def reload_asterisk():
    """Recargar configuración de Asterisk"""
    print("🔄 Recargando configuración de Asterisk...")
    success, stdout, stderr = run_command("sudo asterisk -rx 'core reload'")
    
    if success:
        print("✅ Configuración recargada")
        return True
    else:
        print(f"❌ Error recargando configuración: {stderr}")
        return False

def test_configuration():
    """Probar la configuración"""
    print("🧪 Probando configuración...")
    
    # Verificar que Asterisk sigue ejecutándose
    if not verify_asterisk_running():
        return False
    
    # Probar CLI
    success, stdout, stderr = run_command("sudo asterisk -rx 'core show version'")
    if success:
        print("✅ CLI responde correctamente")
        print(f"📋 Versión: {stdout.strip()}")
    else:
        print("❌ CLI no responde")
        return False
    
    # Verificar configuración SIP
    success, stdout, stderr = run_command("sudo asterisk -rx 'sip show peers'")
    if success:
        print("✅ Configuración SIP cargada")
    else:
        print("⚠️ Problemas con configuración SIP")
    
    return True

def main():
    """Función principal"""
    print("🔧 CONFIGURACIÓN SEGURA DE ASTERISK")
    print("=" * 50)
    
    # Verificar permisos
    if os.geteuid() != 0:
        print("❌ Este script necesita permisos de administrador")
        print("💡 Ejecuta: sudo python3 configure_asterisk_safe.py")
        return False
    
    # Verificar que Asterisk esté ejecutándose
    if not verify_asterisk_running():
        print("❌ Asterisk debe estar ejecutándose antes de aplicar configuraciones")
        return False
    
    # Crear backup
    backup_dir = backup_config()
    if not backup_dir:
        print("❌ No se pudo crear backup. Abortando por seguridad.")
        return False
    
    # Aplicar configuraciones una por una
    config_files = [
        ("asterisk/conf/manager.conf", "/etc/asterisk/manager.conf"),
        ("asterisk/conf/sip.conf", "/etc/asterisk/sip.conf"),
        ("asterisk/conf/extensions.conf", "/etc/asterisk/extensions.conf")
    ]
    
    success_count = 0
    for source, target in config_files:
        if apply_config_file(source, target):
            success_count += 1
        else:
            print(f"⚠️ Error aplicando {source}")
    
    print(f"\n📊 Configuraciones aplicadas: {success_count}/{len(config_files)}")
    
    # Recargar configuración
    if success_count > 0:
        if reload_asterisk():
            # Probar configuración
            if test_configuration():
                print("\n🎉 CONFIGURACIÓN APLICADA EXITOSAMENTE")
                print("=" * 50)
                print("✅ Asterisk configurado para VoIP Auto Dialer")
                print(f"💾 Backup disponible en: {backup_dir}")
                print("\n🔄 Próximos pasos:")
                print("1. Probar conexión con proveedor")
                print("2. Configurar extensiones en softphones")
                print("3. Probar llamadas internas y externas")
                return True
            else:
                print("\n❌ PROBLEMAS EN LA CONFIGURACIÓN")
                print(f"💾 Restaurar backup: sudo cp -r {backup_dir}/* /etc/asterisk/")
                return False
        else:
            print("\n❌ ERROR RECARGANDO CONFIGURACIÓN")
            print(f"💾 Restaurar backup: sudo cp -r {backup_dir}/* /etc/asterisk/")
            return False
    else:
        print("\n❌ NO SE APLICARON CONFIGURACIONES")
        return False

if __name__ == "__main__":
    main()