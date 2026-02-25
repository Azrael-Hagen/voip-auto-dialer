#!/usr/bin/env python3
"""
Script para probar la conexión AMI con Asterisk
"""

import socket
import time
import hashlib

def test_ami_connection():
    """Probar conexión AMI básica"""
    
    print("🔍 PROBANDO CONEXIÓN AMI")
    print("=" * 50)
    
    try:
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
        print(f"🔐 Respuesta login:\n{response}")
        
        if "Response: Success" in response:
            print("✅ Login AMI exitoso")
            
            # Probar comando básico
            status_cmd = (
                "Action: CoreStatus\r\n"
                "\r\n"
            )
            
            sock.send(status_cmd.encode('utf-8'))
            status_response = sock.recv(2048).decode('utf-8')
            print(f"📊 Estado del sistema:\n{status_response}")
            
            # Logout
            logout_cmd = "Action: Logoff\r\n\r\n"
            sock.send(logout_cmd.encode('utf-8'))
            
        else:
            print("❌ Error en login AMI")
            return False
        
        sock.close()
        print("✅ Conexión AMI funcionando correctamente")
        return True
        
    except socket.timeout:
        print("❌ Timeout conectando a AMI")
        return False
    except ConnectionRefusedError:
        print("❌ Conexión rechazada - AMI no está escuchando en puerto 5038")
        return False
    except Exception as e:
        print(f"❌ Error probando AMI: {e}")
        return False

def install_ami_library():
    """Instalar librería AMI para Python"""
    import subprocess
    import sys
    
    print("📦 INSTALANDO LIBRERÍA AMI")
    print("=" * 50)
    
    try:
        # Instalar asterisk-ami
        subprocess.check_call([sys.executable, "-m", "pip", "install", "asterisk-ami"])
        print("✅ Librería asterisk-ami instalada")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando librería: {e}")
        return False

if __name__ == "__main__":
    # Instalar librería si es necesario
    try:
        import asterisk.ami
        print("✅ Librería AMI ya instalada")
    except ImportError:
        if not install_ami_library():
            exit(1)
    
    # Probar conexión
    if test_ami_connection():
        print("\n🎯 AMI CONFIGURADO CORRECTAMENTE")
        print("💡 Ahora puedes ejecutar el sistema sin sudo")
    else:
        print("\n❌ PROBLEMAS CON AMI")
        print("💡 Verificar que Asterisk esté ejecutándose")
        print("💡 Ejecutar: sudo asterisk -rx 'manager show users'")