#!/usr/bin/env python3
"""
🚀 INICIADOR DEL SERVIDOR WEB INTEGRADO
==================================================
"""

import sys
from pathlib import Path

def main():
    # Cambiar al directorio correcto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Iniciando VoIP Auto Dialer - Servidor Web Integrado")
    print("=" * 60)
    print("📊 Dashboard: http://localhost:8000")
    print("📞 Extensiones: http://localhost:8000/extensions")
    print("🌐 Proveedores: http://localhost:8000/providers")
    print("📋 Campañas: http://localhost:8000/campaigns")
    print("🔧 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    print("⚡ Presiona Ctrl+C para detener")
    print()
    
    # Ejecutar el servidor
    try:
        import subprocess
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
