#!/usr/bin/env python3
"""
Script completo para configurar el sistema AMI y eliminar dependencias de sudo
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Ejecutar comando con manejo de errores"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                              capture_output=capture_output, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando: {cmd}")
        print(f"   Salida: {e.stdout}")
        print(f"   Error: {e.stderr}")
        return None

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
            backup_file = f"{manager_conf}.backup_ami_{int(time.time())}"
            result = run_command(f"sudo cp {manager_conf} {backup_file}")
            if result:
                print(f"✅ Backup creado: {backup_file}")
        
        # Escribir nueva configuración
        with open("/tmp/manager.conf", "w") as f:
            f.write(ami_config)
        
        # Copiar al directorio de Asterisk
        commands = [
            f"sudo cp /tmp/manager.conf {manager_conf}",
            f"sudo chown asterisk:asterisk {manager_conf}",
            f"sudo chmod 640 {manager_conf}"
        ]
        
        for cmd in commands:
            result = run_command(cmd)
            if not result:
                return False
        
        print("✅ Configuración AMI creada")
        
        # Recargar configuración de Asterisk
        print("🔄 Recargando configuración de Asterisk...")
        result = run_command("sudo asterisk -rx 'manager reload'")
        
        if result and result.returncode == 0:
            print("✅ AMI recargado exitosamente")
        else:
            print(f"⚠️  Advertencia al recargar AMI")
        
        # Verificar que AMI esté funcionando
        print("🔍 Verificando AMI...")
        result = run_command("sudo asterisk -rx 'manager show users'")
        
        if result and "voip_dialer" in result.stdout:
            print("✅ Usuario AMI 'voip_dialer' configurado correctamente")
            return True
        else:
            print("⚠️  Usuario AMI no encontrado en la salida")
            return False
        
    except Exception as e:
        print(f"❌ Error configurando AMI: {e}")
        return False

def install_ami_library():
    """Instalar librería AMI para Python"""
    print("\n📦 INSTALANDO LIBRERÍAS AMI")
    print("=" * 60)
    
    libraries = [
        "asterisk-ami",
        "websockets"  # Para futuras mejoras en tiempo real
    ]
    
    for lib in libraries:
        print(f"📦 Instalando {lib}...")
        result = run_command(f"{sys.executable} -m pip install {lib}")
        if result and result.returncode == 0:
            print(f"✅ {lib} instalado correctamente")
        else:
            print(f"❌ Error instalando {lib}")
            return False
    
    return True

def test_ami_connection():
    """Probar conexión AMI básica"""
    print("\n🔍 PROBANDO CONEXIÓN AMI")
    print("=" * 60)
    
    try:
        import socket
        
        # Conectar a AMI
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 5038))
        
        # Leer banner de bienvenida
        banner = sock.recv(1024).decode('utf-8')
        print(f"📡 Banner AMI: {banner.strip()}")
        
        # Enviar login
        login_cmd = (
            "Action: Login\r\n"
            "Username: voip_dialer\r\n"
            "Secret: VoIPDialer2026!\r\n"
            "\r\n"
        )
        
        sock.send(login_cmd.encode('utf-8'))
        
        # Leer respuesta de login
        response = sock.recv(1024).decode('utf-8')
        
        if "Response: Success" in response:
            print("✅ Login AMI exitoso")
            
            # Probar comando básico
            status_cmd = (
                "Action: CoreStatus\r\n"
                "\r\n"
            )
            
            sock.send(status_cmd.encode('utf-8'))
            status_response = sock.recv(2048).decode('utf-8')
            print("✅ Comando CoreStatus ejecutado correctamente")
            
            # Logout
            logout_cmd = "Action: Logoff\r\n\r\n"
            sock.send(logout_cmd.encode('utf-8'))
            
            sock.close()
            print("✅ Conexión AMI funcionando correctamente")
            return True
            
        else:
            print("❌ Error en login AMI")
            print(f"   Respuesta: {response}")
            sock.close()
            return False
        
    except socket.timeout:
        print("❌ Timeout conectando a AMI")
        return False
    except ConnectionRefusedError:
        print("❌ Conexión rechazada - AMI no está escuchando en puerto 5038")
        return False
    except Exception as e:
        print(f"❌ Error probando AMI: {e}")
        return False

def create_ami_service_script():
    """Crear script de servicio para AMI"""
    print("\n🔧 CREANDO SCRIPT DE SERVICIO AMI")
    print("=" * 60)
    
    service_script = """#!/bin/bash
# Script para verificar y mantener AMI funcionando

AMI_HOST="127.0.0.1"
AMI_PORT="5038"
AMI_USER="voip_dialer"
AMI_SECRET="VoIPDialer2026!"

check_ami() {
    # Verificar si AMI está respondiendo
    timeout 5 bash -c "</dev/tcp/$AMI_HOST/$AMI_PORT" 2>/dev/null
    return $?
}

restart_ami() {
    echo "Reiniciando AMI..."
    sudo asterisk -rx "manager reload"
    sleep 2
}

# Verificar AMI
if ! check_ami; then
    echo "AMI no responde, reiniciando..."
    restart_ami
    
    if check_ami; then
        echo "AMI reiniciado exitosamente"
    else
        echo "Error: AMI no pudo reiniciarse"
        exit 1
    fi
else
    echo "AMI funcionando correctamente"
fi
"""
    
    try:
        script_path = Path.cwd() / "scripts" / "check_ami.sh"
        with open(script_path, "w") as f:
            f.write(service_script)
        
        # Hacer ejecutable
        os.chmod(script_path, 0o755)
        print(f"✅ Script de servicio creado: {script_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando script de servicio: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 CONFIGURACIÓN COMPLETA DEL SISTEMA AMI")
    print("=" * 70)
    print("Este script configurará AMI para eliminar dependencias de sudo")
    print("=" * 70)
    
    if os.geteuid() == 0:
        print("❌ NO ejecutar este script como root")
        print("   El script usará sudo cuando sea necesario")
        sys.exit(1)
    
    # Verificar que Asterisk esté ejecutándose
    result = run_command("sudo asterisk -rx 'core show version'")
    if not result or result.returncode != 0:
        print("❌ Asterisk no está ejecutándose")
        print("   Iniciar Asterisk: sudo systemctl start asterisk")
        sys.exit(1)
    
    print("✅ Asterisk está ejecutándose")
    
    # Paso 1: Configurar AMI
    if not setup_ami_config():
        print("❌ Error configurando AMI")
        sys.exit(1)
    
    # Paso 2: Instalar librerías
    if not install_ami_library():
        print("❌ Error instalando librerías")
        sys.exit(1)
    
    # Paso 3: Probar conexión
    if not test_ami_connection():
        print("❌ Error probando conexión AMI")
        sys.exit(1)
    
    # Paso 4: Crear script de servicio
    if not create_ami_service_script():
        print("❌ Error creando script de servicio")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("🎯 CONFIGURACIÓN AMI COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print("📋 CREDENCIALES AMI:")
    print("   Host: 127.0.0.1")
    print("   Puerto: 5038")
    print("   Usuario: voip_dialer")
    print("   Contraseña: VoIPDialer2026!")
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Reiniciar el servidor web: python3 web/main.py")
    print("   2. Acceder al dashboard: http://localhost:8000")
    print("   3. Verificar datos en tiempo real sin sudo")
    print("\n🔧 MANTENIMIENTO:")
    print("   - Verificar AMI: ./scripts/check_ami.sh")
    print("   - Logs AMI: sudo asterisk -rx 'manager show connected'")

if __name__ == "__main__":
    main()