#!/usr/bin/env python3
"""
Script de inicio para VoIP Auto Dialer
Inicia el servidor web con todas las funcionalidades integradas
"""

import os
import sys
import uvicorn
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("🚀 Iniciando VoIP Auto Dialer...")
    print("📊 Dashboard disponible en: http://localhost:8000")
    print("📋 Gestión de agentes: http://localhost:8000/agents")
    print("🔧 Gestión de proveedores: http://localhost:8000/providers")
    print("📞 Gestión de extensiones: http://localhost:8000/extensions")
    print("\n⚡ Presiona Ctrl+C para detener el servidor\n")
    
    try:
        # Cambiar al directorio web para imports correctos
        os.chdir("web")
        
        # Iniciar servidor
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
