import os
import shutil
from pathlib import Path

# Ruta base del repositorio
BASE_DIR = Path("/home/azrael/voip-auto-dialer")

# Carpeta externa para respaldos
BACKUP_DIR = Path.home() / "asterisk_backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Carpetas que deben eliminarse
REMOVE_DIRS = ["venv", "logs"]
# Prefijo de carpetas de respaldo
BACKUP_PREFIX = "asterisk_backup_"

# Scripts auxiliares que conviene mover
TOOLS = [
    "diagnose_pjsip_issue.py",
    "fix_pjsip_configuration.py",
    "quick_voip_test.py",
    "restart_asterisk.py",
    "start_clean.py"
]

def remove_dirs():
    for d in REMOVE_DIRS:
        dir_path = BASE_DIR / d
        if dir_path.exists():
            print(f"Eliminando carpeta: {dir_path}")
            shutil.rmtree(dir_path, ignore_errors=True)

def move_backups():
    for item in BASE_DIR.iterdir():
        if item.is_dir() and item.name.startswith(BACKUP_PREFIX):
            dest = BACKUP_DIR / item.name
            print(f"Moviendo respaldo {item} a {dest}")
            try:
                shutil.move(str(item), str(dest))
            except PermissionError:
                print(f"⚠️ No se pudo mover {item} por permisos. Usa 'sudo mv {item} {dest}' manualmente.")

def move_tools():
    tools_dir = BASE_DIR / "tools"
    tools_dir.mkdir(exist_ok=True)
    for script in TOOLS:
        script_path = BASE_DIR / script
        if script_path.exists():
            print(f"Moviendo {script} a tools/")
            shutil.move(str(script_path), str(tools_dir / script))

def create_gitignore():
    gitignore_path = BASE_DIR / ".gitignore"
    content = """# Entorno virtual
venv/
__pycache__/
*.pyc

# Logs
logs/
*.log

# Respaldos
asterisk_backup_*/

# Archivos temporales
*.tmp
"""
    with open(gitignore_path, "w") as f:
        f.write(content)
    print(f".gitignore creado en {gitignore_path}")

if __name__ == "__main__":
    remove_dirs()
    move_backups()
    move_tools()
    create_gitignore()
    print("✅ Limpieza completada. Respaldos movidos a ~/asterisk_backups/")
