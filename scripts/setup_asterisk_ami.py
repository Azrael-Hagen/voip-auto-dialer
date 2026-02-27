#!/usr/bin/env python3
"""
Script para configurar Asterisk Manager Interface (AMI)
Esto eliminará la necesidad de usar sudo para comandos de Asterisk
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_ami_config():
    """Configurar AMI en Asterisk"""
    
    print("🔧 CONFIGURANDO ASTERISK MANAGER INTERFACE (AMI)")
    print("=" * 60)
    
    # Configuración AMI
    ami_config = """
; Manager Interface Configuration
; This file configures the Asterisk Manager Interface (AMI)

[general]
enabled = yes
port = 5038
bindaddr = 127.0.0.1
displayconnects = no

; Usuario para VoIP Auto Dialer
[voip_dialer]
secret = VoIPDialer2026!
deny = 0.0.0.0/0.0.0.0
permit = 127.0.0.1/255.255.255.0
permit = 192.168.0.0/255.255.0.0
permit = 10.0.0.0/255.0.0.0
read = system,call,log,verbose,command,agent,user,config,dtmf,reporting,cdr,dialplan
write = system,call,log,verbose,command,agent,user,config,dtmf,reporting,cdr,dialplan
writetimeout = 5000
"""
    
    try:
        # Crear backup del archivo actual si existe
        manager_conf = "/etc/asterisk/manager.conf"
        if os.path.exists(manager_conf):
            backup_file = f"{manager_conf}.backup_ami_{int(__import__('time').time())}"
            subprocess.run(["sudo", "cp", manager_conf, backup_file], check=True)
            print(f"✅ Backup creado: {backup_file}")
        
        # Escribir nueva configuración
        with open("/tmp/manager.conf", "w") as f:
            f.write(ami_config)
        
        # Copiar al directorio de Asterisk
        subprocess.run(["sudo", "cp", "/tmp/manager.conf", manager_conf], check=True)
        subprocess.run(["sudo", "chown", "asterisk:asterisk", manager_conf], check=True)
        subprocess.run(["sudo", "chmod", "640", manager_conf], check=True)
        
        print("✅ Configuración AMI creada")
        
        # Recargar configuración de Asterisk
        print("🔄 Recargando configuración de Asterisk...")
        result = subprocess.run(["sudo", "asterisk", "-rx", "manager reload"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ AMI recargado exitosamente")
        else:
            print(f"⚠️  Advertencia al recargar AMI: {result.stderr}")
        
        # Verificar que AMI esté funcionando
        print("🔍 Verificando AMI...")
        result = subprocess.run(["sudo", "asterisk", "-rx", "manager show users"], 
                              capture_output=True, text=True)
        
        if "voip_dialer" in result.stdout:
            print("✅ Usuario AMI 'voip_dialer' configurado correctamente")
        else:
            print("⚠️  Usuario AMI no encontrado en la salida")
        
        print("\n" + "=" * 60)
        print("🎯 CONFIGURACIÓN AMI COMPLETADA")
        print("=" * 60)
        print("📋 CREDENCIALES AMI:")
        print("   Host: 127.0.0.1")
        print("   Puerto: 5038")
        print("   Usuario: voip_dialer")
        print("   Contraseña: VoIPDialer2026!")
        print("\n💡 PRÓXIMO PASO:")
        print("   Ejecutar: python3 scripts/test_ami_connection.py")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False
    except Exception as e:
        print(f"❌ Error configurando AMI: {e}")
        return False

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("❌ Este script necesita ejecutarse con sudo")
        print("   Ejecutar: sudo python3 scripts/setup_asterisk_ami.py")
        sys.exit(1)
    
    setup_ami_config()