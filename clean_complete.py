#!/usr/bin/env python3
"""
Script de Limpieza Completa - VoIP Auto Dialer
Elimina TODOS los archivos problemáticos y configura entorno limpio
"""

import os
import shutil
import sys
import subprocess
from datetime import datetime

def print_status(message, status="INFO"):
    """Imprime mensajes con formato"""
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def remove_problematic_scripts():
    """Elimina scripts problemáticos anteriores"""
    print_status("Eliminando scripts problemáticos anteriores...", "INFO")
    
    scripts_to_remove = [
        "auto_clean.py",
        "clean_restart.py"
    ]
    
    for script in scripts_to_remove:
        if os.path.exists(script):
            try:
                os.remove(script)
                print_status(f"Eliminado script problemático: {script}", "SUCCESS")
            except Exception as e:
                print_status(f"Error eliminando {script}: {e}", "ERROR")

def create_backup():
    """Crea backup solo de archivos esenciales"""
    backup_dir = "backup_essential"
    
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    
    print_status("Creando backup de archivos esenciales...", "INFO")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Solo archivos realmente esenciales
    essential_items = [
        "web_functional/",
        "data/extensions.json",
        "data/agents.json", 
        "data/providers.json",
        "config/",
        "README.md"
    ]
    
    for item in essential_items:
        if os.path.exists(item):
            try:
                if os.path.isdir(item):
                    shutil.copytree(item, os.path.join(backup_dir, item))
                else:
                    os.makedirs(os.path.dirname(os.path.join(backup_dir, item)), exist_ok=True)
                    shutil.copy2(item, os.path.join(backup_dir, item))
                print_status(f"Respaldado: {item}", "SUCCESS")
            except Exception as e:
                print_status(f"Error respaldando {item}: {e}", "WARNING")
    
    return backup_dir

def clean_everything():
    """Limpieza completa y agresiva"""
    print_status("Ejecutando limpieza completa...", "INFO")
    
    # Eliminar TODOS los directorios problemáticos
    dirs_to_remove = [
        "venv/", "__pycache__/", "src/", "tests/", "scripts/", "logs/",
        "core/", "providers/", "tools/", "docs/", "campaigns/",
        "exported_py_txt/", "asterisk_config/", "asterisk_config_generated/"
    ]
    
    # Eliminar backups antiguos
    import glob
    old_backups = glob.glob("backup_*") + glob.glob("asterisk_backup_*")
    dirs_to_remove.extend(old_backups)
    
    for directory in dirs_to_remove:
        if os.path.exists(directory):
            try:
                if directory.startswith("asterisk_backup_"):
                    # Usar sudo para backups de asterisk con permisos de root
                    subprocess.run(["sudo", "rm", "-rf", directory], check=True)
                else:
                    shutil.rmtree(directory)
                print_status(f"Eliminado: {directory}", "SUCCESS")
            except Exception as e:
                print_status(f"Error eliminando {directory}: {e}", "WARNING")
    
    # Eliminar archivos problemáticos
    files_to_remove = [
        "requirements.txt",  # El problemático
        "todo.md"  # Reiniciar tareas
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print_status(f"Eliminado archivo: {file}", "SUCCESS")
            except Exception as e:
                print_status(f"Error eliminando {file}: {e}", "WARNING")

def setup_clean_environment():
    """Configura entorno completamente limpio"""
    print_status("Configurando entorno limpio...", "INFO")
    
    # Usar el requirements limpio
    if os.path.exists("requirements_clean.txt"):
        shutil.copy2("requirements_clean.txt", "requirements.txt")
        print_status("Configurado requirements.txt limpio", "SUCCESS")
    
    # Crear entorno virtual limpio
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_status("Entorno virtual creado", "SUCCESS")
    except Exception as e:
        print_status(f"Error creando venv: {e}", "ERROR")
        return False
    
    # Activar e instalar dependencias
    try:
        if os.name == 'nt':  # Windows
            pip_path = "venv/Scripts/pip"
        else:  # Linux/Mac
            pip_path = "venv/bin/pip"
        
        # Actualizar pip
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        print_status("pip actualizado", "SUCCESS")
        
        # Instalar dependencias limpias
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print_status("Dependencias instaladas exitosamente", "SUCCESS")
        
    except Exception as e:
        print_status(f"Error instalando dependencias: {e}", "ERROR")
        return False
    
    return True

def verify_installation():
    """Verifica que todo esté funcionando"""
    print_status("Verificando instalación...", "INFO")
    
    # Verificar archivos esenciales
    essential_files = [
        "web_functional/main.py",
        "web_functional/ami_integration.py",
        "data/extensions.json",
        "data/agents.json",
        "data/providers.json"
    ]
    
    all_good = True
    for file in essential_files:
        if os.path.exists(file):
            print_status(f"✓ {file}", "SUCCESS")
        else:
            print_status(f"✗ {file} - FALTANTE", "ERROR")
            all_good = False
    
    # Verificar dependencias
    try:
        if os.name == 'nt':
            python_path = "venv/Scripts/python"
        else:
            python_path = "venv/bin/python"
        
        result = subprocess.run([python_path, "-c", 
            "import fastapi, uvicorn, asterisk_ami, websockets; print('Dependencias OK')"], 
            capture_output=True, text=True)
        
        if result.returncode == 0:
            print_status("Dependencias verificadas correctamente", "SUCCESS")
        else:
            print_status(f"Error en dependencias: {result.stderr}", "ERROR")
            all_good = False
            
    except Exception as e:
        print_status(f"Error verificando dependencias: {e}", "ERROR")
        all_good = False
    
    return all_good

def main():
    """Función principal"""
    print("🧹 LIMPIEZA COMPLETA - VoIP Auto Dialer")
    print("=" * 50)
    
    try:
        # Paso 1: Eliminar scripts problemáticos
        remove_problematic_scripts()
        
        # Paso 2: Crear backup esencial
        backup_dir = create_backup()
        print_status(f"Backup esencial creado en: {backup_dir}", "SUCCESS")
        
        # Paso 3: Limpieza completa
        clean_everything()
        
        # Paso 4: Configurar entorno limpio
        if setup_clean_environment():
            print_status("Entorno configurado correctamente", "SUCCESS")
        else:
            print_status("Error configurando entorno", "ERROR")
            return
        
        # Paso 5: Verificar instalación
        if verify_installation():
            print_status("🎉 LIMPIEZA COMPLETA EXITOSA", "SUCCESS")
            print("\n🚀 PROYECTO LISTO PARA USAR:")
            print("1. Activar entorno: source venv/bin/activate")
            print("2. Probar servidor: cd web_functional && python main.py")
            print("3. Acceder a: http://localhost:8000")
        else:
            print_status("⚠️ Limpieza completada con advertencias", "WARNING")
            print("Revisa los errores anteriores")
        
    except Exception as e:
        print_status(f"Error crítico: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()