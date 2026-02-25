#!/usr/bin/env python3
"""
Script para reiniciar y verificar Asterisk
"""
import subprocess
import time
import os

def run_command(cmd, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: OK")
            if result.stdout.strip():
                print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description}: FALLÓ")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description}: Error - {e}")
        return False

def main():
    print("🎯 REINICIANDO Y VERIFICANDO ASTERISK")
    print("=" * 50)
    
    # 1. Verificar estado actual
    print("\n1. 📋 Verificando estado actual de Asterisk")
    run_command("sudo systemctl status asterisk", "Estado del servicio")
    
    # 2. Detener Asterisk si está ejecutándose
    print("\n2. 🛑 Deteniendo Asterisk")
    run_command("sudo systemctl stop asterisk", "Detener servicio")
    time.sleep(2)
    
    # 3. Limpiar archivos de socket
    print("\n3. 🧹 Limpiando archivos temporales")
    run_command("sudo rm -f /var/run/asterisk/asterisk.ctl", "Limpiar socket")
    run_command("sudo rm -f /var/run/asterisk/asterisk.pid", "Limpiar PID")
    
    # 4. Verificar configuración
    print("\n4. 🔍 Verificando configuración")
    run_command("sudo asterisk -T -C /etc/asterisk/asterisk.conf", "Verificar sintaxis")
    
    # 5. Iniciar Asterisk
    print("\n5. 🚀 Iniciando Asterisk")
    if run_command("sudo systemctl start asterisk", "Iniciar servicio"):
        time.sleep(3)
        
        # 6. Verificar que esté ejecutándose
        print("\n6. ✅ Verificando funcionamiento")
        if run_command("sudo systemctl is-active asterisk", "Servicio activo"):
            run_command("sudo asterisk -rx 'core show version'", "Versión de Asterisk")
            run_command("sudo asterisk -rx 'pjsip show endpoints'", "Endpoints PJSIP")
            run_command("sudo asterisk -rx 'dialplan show from-internal'", "Dialplan")
            
            print("\n🎉 ¡ASTERISK REINICIADO EXITOSAMENTE!")
            print("\n📋 COMANDOS ÚTILES:")
            print("   • Conectar al CLI: sudo asterisk -rvvv")
            print("   • Ver registros: sudo asterisk -rx 'pjsip show registrations'")
            print("   • Ver endpoints: sudo asterisk -rx 'pjsip show endpoints'")
            print("   • Ver canales: sudo asterisk -rx 'core show channels'")
        else:
            print("\n❌ Asterisk no se pudo iniciar correctamente")
            print("📋 REVISAR:")
            print("   • Logs: sudo journalctl -u asterisk -f")
            print("   • Configuración: sudo asterisk -T")
    else:
        print("\n❌ No se pudo iniciar Asterisk")
        print("📋 REVISAR:")
        print("   • Permisos: sudo chown -R asterisk:asterisk /var/lib/asterisk")
        print("   • Configuración: sudo asterisk -T")

if __name__ == "__main__":
    main()

