#!/usr/bin/env python3
"""
Script de inicio limpio para VoIP Auto Dialer
Verifica el sistema y ejecuta el servidor web
"""
import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    """Imprimir encabezado formateado"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_system():
    """Verificar que el sistema esté listo"""
    print_header("🔍 VERIFICANDO SISTEMA")
    
    # Verificar directorio actual
    current_dir = Path.cwd()
    print(f"📁 Directorio actual: {current_dir}")
    
    # Verificar estructura de directorios
    required_dirs = ["core", "web", "web/templates", "web/static/css", "data"]
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directorio {directory}: OK")
        else:
            print(f"❌ Directorio {directory}: FALTANTE")
            return False
    
    # Verificar archivos críticos
    required_files = [
        "core/agent_manager_clean.py",
        "core/extension_manager.py",
        "web/main.py",
        "web/templates/base.html",
        "web/templates/agents.html",
        "web/static/css/dashboard.css"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ Archivo {file_path}: OK ({size} bytes)")
        else:
            print(f"❌ Archivo {file_path}: FALTANTE")
            return False
    
    return True

def start_server():
    """Iniciar el servidor web"""
    print_header("🚀 INICIANDO SERVIDOR WEB")
    
    print("🔧 Verificando entorno virtual...")
    if 'VIRTUAL_ENV' in os.environ:
        print(f"✅ Entorno virtual activo: {os.environ['VIRTUAL_ENV']}")
    else:
        print("⚠️  Entorno virtual no detectado")
        print("   Ejecuta: source venv/bin/activate")
        return False
    
    print("\n🌐 Iniciando servidor...")
    print("   URL: http://localhost:8000")
    print("   Presiona Ctrl+C para detener")
    print("\n" + "="*60)
    
    try:
        # Ejecutar servidor
        subprocess.run([sys.executable, "web/main.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error ejecutando servidor: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print_header("🎯 VoIP AUTO DIALER - INICIO LIMPIO")
    
    # Verificar sistema
    if not check_system():
        print("\n❌ SISTEMA NO ESTÁ LISTO")
        print("   Verifica que todos los archivos estén en su lugar")
        return
    
    print("\n✅ SISTEMA VERIFICADO CORRECTAMENTE")
    
    # Iniciar servidor
    if start_server():
        print("\n✅ SERVIDOR EJECUTADO EXITOSAMENTE")
    else:
        print("\n❌ ERROR INICIANDO SERVIDOR")

if __name__ == "__main__":
    main()