
#!/usr/bin/env python3
"""
Diagnóstico rápido del sistema VoIP Auto Dialer
"""

import os
import sys
from pathlib import Path

def diagnose_system():
    print("🔍 DIAGNÓSTICO DEL SISTEMA VOIP AUTO DIALER")
    print("=" * 50)
    
    # Verificar directorio actual
    current_dir = Path.cwd()
    print(f"📁 Directorio actual: {current_dir}")
    
    # Verificar estructura de archivos
    critical_files = [
        "web/main.py",
        "core/agent_manager_clean.py",
        "core/extension_manager.py", 
        "data/agents.json",
        "data/extensions.json"
    ]
    
    print("\n📋 ARCHIVOS CRÍTICOS:")
    all_exist = True
    for file_path in critical_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {file_path}")
        if not exists:
            all_exist = False
    
    # Verificar imports de Python
    print("\n🐍 VERIFICACIÓN DE IMPORTS:")
    
    # Agregar paths
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(current_dir / "web"))
    
    imports_to_test = [
        ("core.agent_manager_clean", "agent_manager"),
        ("core.extension_manager", "extension_manager"),
        ("core.provider_manager", "provider_manager"),
        ("core.logging_config", "get_logger")
    ]
    
    import_success = True
    for module_name, item_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print(f"   ✅ {module_name}.{item_name}")
        except ImportError as e:
            print(f"   ❌ {module_name}.{item_name} - Error: {e}")
            import_success = False
        except AttributeError as e:
            print(f"   ⚠️  {module_name}.{item_name} - Atributo no encontrado: {e}")
    
    # Verificar web/main.py específicamente
    print("\n🌐 VERIFICACIÓN DE WEB/MAIN.PY:")
    web_main = Path("web/main.py")
    if web_main.exists():
        try:
            # Cambiar al directorio web temporalmente
            original_dir = os.getcwd()
            os.chdir("web")
            
            # Intentar importar
            sys.path.insert(0, os.getcwd())
            import main
            print("   ✅ web/main.py se puede importar correctamente")
            
            # Verificar que tiene la app
            if hasattr(main, 'app'):
                print("   ✅ FastAPI app encontrada")
            else:
                print("   ❌ FastAPI app no encontrada")
            
            os.chdir(original_dir)
            
        except Exception as e:
            print(f"   ❌ Error importando web/main.py: {e}")
            os.chdir(original_dir)
    else:
        print("   ❌ web/main.py no existe")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    if not all_exist:
        print("   🔧 Algunos archivos críticos faltan - verificar estructura del proyecto")
    
    if not import_success:
        print("   🔧 Problemas de imports - verificar dependencias y paths")
    
    print("\n🚀 COMANDOS PARA PROBAR:")
    print("   1. python run_server.py")
    print("   2. cd web && python main.py") 
    print("   3. python start_server_fixed.py")
    
    print(f"\n📊 Python version: {sys.version}")
    print(f"📊 Python path: {sys.path[:3]}...")

if __name__ == "__main__":
    diagnose_system()
