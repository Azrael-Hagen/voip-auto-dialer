import os
import re
import sys
import pkgutil
import subprocess
from pathlib import Path

BASE_DIR = Path("/home/azrael/voip-auto-dialer")
REQ_FILE = BASE_DIR / "requirements.txt"

# Regex para detectar imports
IMPORT_PATTERN = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)')

# Scripts principales que sí se usan
MAIN_SCRIPTS = {
    "start_web_server.py",
    "setup_complete_voip_system.py",
    "core", "web", "config", "providers", "campaigns", "data"
}

def get_imports_from_file(file_path):
    imports = set()
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            match = IMPORT_PATTERN.match(line)
            if match:
                module = match.group(1).split('.')[0]
                if module:
                    imports.add(module)
    return imports

def scan_repo_for_imports():
    all_imports = set()
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                all_imports |= get_imports_from_file(file_path)
    return all_imports

def read_requirements():
    if REQ_FILE.exists():
        with open(REQ_FILE, "r") as f:
            return {line.strip().split("==")[0] for line in f if line.strip()}
    return set()

def get_std_libs():
    std_libs = {name for _, name, _ in pkgutil.iter_modules()}
    std_libs |= {"os","sys","re","math","json","pathlib","shutil","logging",
                 "subprocess","datetime","time","argparse","typing","functools",
                 "itertools","collections"}
    return std_libs

def update_requirements(missing_libs):
    with open(REQ_FILE, "a") as f:
        for lib in sorted(missing_libs):
            f.write(f"{lib}\n")
    print(f"✅ Se agregaron {len(missing_libs)} librerías a requirements.txt")

def install_missing(missing_libs):
    for lib in missing_libs:
        print(f"📦 Instalando {lib}...")
        subprocess.run([sys.executable, "-m", "pip", "install", lib])

def regenerate_requirements():
    print("🔄 Regenerando requirements.txt con pip freeze...")
    with open(REQ_FILE, "w") as f:
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=f)
    print("✅ requirements.txt actualizado")

def clean_unused_scripts():
    deprecated_dir = BASE_DIR / "deprecated"
    deprecated_dir.mkdir(exist_ok=True)

    for item in BASE_DIR.iterdir():
        if item.is_file() and item.suffix == ".py":
            if item.name not in MAIN_SCRIPTS:
                print(f"🗂️ Moviendo script no esencial: {item.name}")
                item.rename(deprecated_dir / item.name)

if __name__ == "__main__":
    repo_imports = scan_repo_for_imports()
    current_reqs = read_requirements()
    std_libs = get_std_libs()

    third_party_imports = {lib for lib in repo_imports if lib not in std_libs and lib.strip()}
    missing = third_party_imports - current_reqs

    if missing:
        print("📦 Librerías faltantes detectadas:", missing)
        update_requirements(missing)
        install_missing(missing)
    else:
        print("✅ No faltan librerías en requirements.txt")

    regenerate_requirements()
    clean_unused_scripts()
    print("🏁 Mantenimiento completo: dependencias sincronizadas y scripts ordenados.")
