#!/usr/bin/env python3
"""
🚀 SCRIPT DE INICIO CORREGIDO - SERVIDOR WEB FUNCIONAL
======================================================================
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Iniciando VoIP Auto Dialer - Servidor Web Funcional (Corregido)")
    print("📊 Dashboard: http://localhost:8000")
    print("📞 Extensiones: http://localhost:8000/extensions")
    print("🌐 Proveedores: http://localhost:8000/providers")
    print("📋 Campañas: http://localhost:8000/campaigns")
    print("🔧 API Docs: http://localhost:8000/docs")
    print("\n⚡ Presiona Ctrl+C para detener\n")
    
    try:
        from main import main as server_main
        server_main()
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
