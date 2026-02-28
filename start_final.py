
#!/usr/bin/env python3
"""
Script de inicio definitivo para VoIP Auto Dialer
Versión robusta con diagnóstico automático
"""

import os
import sys
import uvicorn
from pathlib import Path

def check_system():
    """Verificar que el sistema esté listo"""
    print("🔍 Verificando sistema...")
    
    # Verificar archivos críticos
    critical_files = [
        "web/main.py",
        "core/agent_manager_clean.py",
        "data/agents.json"
    ]
    
    missing = []
    for file_path in critical_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print("❌ Archivos críticos faltantes:")
        for f in missing:
            print(f"   - {f}")
        return False
    
    print("✅ Archivos críticos verificados")
    return True

def main():
    print("🚀 VoIP Auto Dialer - Inicio Definitivo")
    print("=" * 50)
    
    # Verificar directorio
    if not Path("web/main.py").exists():
        print("❌ Error: Ejecutar desde el directorio raíz voip-auto-dialer/")
        sys.exit(1)
    
    # Verificar sistema
    if not check_system():
        print("\n🔧 Ejecuta primero: python fix_system.py")
        sys.exit(1)
    
    # Configurar paths
    project_root = Path.cwd()
    sys.path.insert(0, str(project_root))
    
    print(f"📁 Directorio: {project_root}")
    print("\n🌐 URLs disponibles:")
    print("   📊 Dashboard: http://localhost:8000")
    print("   👥 Agentes: http://localhost:8000/agents")
    print("   📞 Extensiones: http://localhost:8000/extensions")
    print("   🔧 Proveedores: http://localhost:8000/providers")
    print("   🔍 Health Check: http://localhost:8000/api/health")
    print("\n⚡ Presiona Ctrl+C para detener\n")
    
    try:
        # Iniciar servidor
        uvicorn.run(
            "web.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            reload_dirs=[str(project_root)]
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Alternativas:")
        print("   1. cd web && python main.py")
        print("   2. python diagnose.py")

if __name__ == "__main__":
    main()