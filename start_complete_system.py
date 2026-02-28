#!/usr/bin/env python3
"""
SCRIPT DE INICIO COMPLETO DEL SISTEMA VOIP AUTO DIALER
Inicia servidor web con integración completa de Asterisk
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_asterisk_status():
    """Verificar estado de Asterisk"""
    try:
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'asterisk'], 
                              capture_output=True, text=True)
        return result.returncode == 0 and 'active' in result.stdout
    except:
        return False

def check_asterisk_cli():
    """Verificar CLI de Asterisk"""
    try:
        result = subprocess.run(['sudo', 'asterisk', '-rx', 'core show version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def main():
    """Función principal"""
    print("🚀 INICIANDO SISTEMA VOIP AUTO DIALER COMPLETO")
    print("=" * 60)
    
    # Verificar directorio
    if not Path("data/extensions.json").exists():
        print("❌ Error: Ejecutar desde directorio voip-auto-dialer")
        sys.exit(1)
    
    # Verificar estado de Asterisk
    print("🔍 Verificando estado de Asterisk...")
    
    if not check_asterisk_status():
        print("⚠️  Asterisk no está activo")
        print("💡 Ejecuta primero: python3 fix_asterisk_emergency.py")
        
        response = input("¿Quieres ejecutar la reparación ahora? (y/N): ")
        if response.lower() == 'y':
            print("🔧 Ejecutando reparación de Asterisk...")
            result = subprocess.run([sys.executable, 'fix_asterisk_emergency.py'])
            if result.returncode != 0:
                print("❌ Error en reparación de Asterisk")
                sys.exit(1)
        else:
            print("❌ Asterisk debe estar funcionando para continuar")
            sys.exit(1)
    
    if not check_asterisk_cli():
        print("❌ Error: CLI de Asterisk no responde")
        print("💡 Ejecuta: sudo systemctl restart asterisk")
        sys.exit(1)
    
    print("✅ Asterisk funcionando correctamente")
    
    # Verificar integración web-asterisk
    print("🔍 Verificando integración web-asterisk...")
    try:
        from web_asterisk_integration import asterisk_integration
        status = asterisk_integration.get_system_status()
        
        if status.get('system_ready', False):
            print("✅ Sistema de integración listo")
            print(f"👥 Agentes disponibles: {status.get('available_agents', 0)}")
        else:
            print("⚠️  Sistema de integración con problemas")
            print(f"📊 Estado: {status}")
    except Exception as e:
        print(f"⚠️  Error verificando integración: {e}")
    
    # Crear directorio de logs si no existe
    logs_dir = Path("web/logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Iniciar servidor web
    print("\n🌐 INICIANDO SERVIDOR WEB CON AUTO-MARCADO")
    print("=" * 60)
    print("📊 Dashboard: http://localhost:8000")
    print("📞 Auto-marcado: http://localhost:8000/api/dialer/")
    print("🔧 Gestión: http://localhost:8000/agents")
    print("=" * 60)
    print("⚡ Presiona Ctrl+C para detener")
    print()
    
    # Cambiar al directorio web e iniciar servidor
    os.chdir("web")
    
    try:
        # Usar uvicorn para iniciar el servidor
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error iniciando servidor: {e}")
        print("💡 Intenta: cd web && python main.py")

if __name__ == "__main__":
    main()