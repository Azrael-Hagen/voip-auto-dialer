
#!/usr/bin/env python3
"""
Script de limpieza para eliminar archivos conflictivos del proyecto voip-auto-dialer
Ejecutar desde el directorio raíz del proyecto
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Eliminar archivos conflictivos y obsoletos"""
    
    # Archivos a eliminar
    files_to_remove = [
        "start_web_server.py",
        "start_web_server_integration.py", 
        "setup_initial_data.py",
        "test_complete_system.py",
        "todo.md"  # El temporal del docs/
    ]
    
    # Directorios a limpiar
    dirs_to_clean = [
        "__pycache__",
        "*.pyc",
        ".pytest_cache"
    ]
    
    print("🧹 Iniciando limpieza del proyecto voip-auto-dialer...")
    
    # Eliminar archivos específicos
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Eliminado: {file_path}")
            except Exception as e:
                print(f"❌ Error eliminando {file_path}: {e}")
        else:
            print(f"ℹ️  No encontrado: {file_path}")
    
    # Limpiar cache de Python
    for root, dirs, files in os.walk("."):
        # Eliminar __pycache__
        if "__pycache__" in dirs:
            cache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(cache_path)
                print(f"✅ Eliminado cache: {cache_path}")
            except Exception as e:
                print(f"❌ Error eliminando cache {cache_path}: {e}")
        
        # Eliminar archivos .pyc
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                try:
                    os.remove(pyc_path)
                    print(f"✅ Eliminado: {pyc_path}")
                except Exception as e:
                    print(f"❌ Error eliminando {pyc_path}: {e}")
    
    print("\n🎯 Limpieza completada!")
    print("📋 Archivos principales mantenidos:")
    print("   ✅ web/main.py (tu servidor principal)")
    print("   ✅ web/templates/ (tus templates profesionales)")
    print("   ✅ core/ (módulos del sistema)")
    print("   ✅ data/ (datos de agentes y extensiones)")

if __name__ == "__main__":
    cleanup_project()