#!/usr/bin/env python3
"""
Script de limpieza para VoIP Auto Dialer
Elimina archivos de debug, fix y temporales innecesarios
"""

import os
import sys
from pathlib import Path
import shutil
import json
from datetime import datetime

def identify_cleanup_files():
    """Identificar archivos para limpieza"""
    
    # Archivos específicos para eliminar (basado en tu listado anterior)
    files_to_remove = [
        # Scripts de diagnóstico y fix ya no necesarios
        "diagnose_pjsip_issue.py",
        "fix_pjsip_configuration.py", 
        "fix_pjsip_integration.py",
        "integrate_with_existing_asterisk.py",
        "restart_asterisk.py",
        "setup_complete_voip_system.py",
        "start_clean.py",
        "sync_extensions_to_asterisk.py",
        "test_extension_calls_enhanced.py",
        "test_final_validation.py",
        "verify_integration.py",
        "web_softphone_endpoints.py",
        "quick_voip_test.py",
        "generate_softphone_configs_enhanced.py",
        
        # Scripts en /scripts/ que son de debug/fix
        "scripts/analyze_web_system.py",
        "scripts/debug_dashboard.py", 
        "scripts/debug_extension_issue.py",
        "scripts/diagnose_current_state.py",
        "scripts/diagnose_frontend.py",
        "scripts/diagnose_server_code.py",
        "scripts/fix_extension_assignment.py",
        "scripts/fix_extension_format_mismatch.py",
        "scripts/fix_pjsip_includes.py",
        "scripts/fix_remaining_server_errors.py",
        "scripts/fix_web_server_errors.py",
        "scripts/get_extension_credentials.py",
        "scripts/test_manual_load.py",
        "scripts/test_production_system.py",
        "scripts/test_web_interface.py",
        "scripts/verify_fix.py",
        "scripts/verify_pjsip_syntax.py",
        
        # Archivos de backup
        "core/agent_manager_clean.py.backup",
        "core/extension_manager.py.backup_20260223_144512",
        "web/main.py.backup_20260223_144512",
        "web/main.py.backup_20260223_150731", 
        "web/main.py.backup_minimal_20260223_151158",
        "data/extensions.json.backup_20260223_150452"
    ]
    
    # Directorios para limpiar
    dirs_to_remove = [
        "asterisk_backup_20260221_235028"
    ]
    
    return files_to_remove, dirs_to_remove

def clean_pycache():
    """Limpiar directorios __pycache__"""
    print("🧹 Limpiando archivos __pycache__...")
    
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            print(f"   Eliminando: {pycache_path}")
            shutil.rmtree(pycache_path)
            dirs.remove("__pycache__")

def clean_log_files():
    """Limpiar archivos de log antiguos (mantener solo los recientes)"""
    print("📋 Limpiando logs antiguos...")
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            # Mantener archivos de log, pero limpiar su contenido si son muy grandes
            if log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
                print(f"   Truncando log grande: {log_file}")
                with open(log_file, 'w') as f:
                    f.write(f"# Log truncado por limpieza - {datetime.now()}\n")

def main():
    """Función principal de limpieza"""
    
    print("🚀 SCRIPT DE LIMPIEZA - VoIP Auto Dialer")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("web/main.py"):
        print("❌ Error: No se encuentra web/main.py")
        print("   Ejecutar desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Obtener archivos para limpiar
    files_to_remove, dirs_to_remove = identify_cleanup_files()
    
    print("\n🔍 ARCHIVOS IDENTIFICADOS PARA LIMPIEZA:")
    print("-" * 40)
    
    # Mostrar archivos que se van a eliminar
    files_found = []
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            files_found.append(file_path)
            print(f"   📄 {file_path}")
    
    dirs_found = []
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            dirs_found.append(dir_path)
            print(f"   📁 {dir_path}/")
    
    if not files_found and not dirs_found:
        print("   ✅ No se encontraron archivos innecesarios")
        return
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN:")
    print(f"   Archivos a eliminar: {len(files_found)}")
    print(f"   Directorios a eliminar: {len(dirs_found)}")
    
    response = input("\n¿Proceder con la limpieza? (s/N): ").lower().strip()
    
    if response != 's':
        print("❌ Limpieza cancelada")
        return
    
    print("\n🧹 INICIANDO LIMPIEZA...")
    print("-" * 40)
    
    # Eliminar archivos
    removed_files = 0
    for file_path in files_found:
        try:
            os.remove(file_path)
            print(f"   ✅ Eliminado: {file_path}")
            removed_files += 1
        except Exception as e:
            print(f"   ❌ Error eliminando {file_path}: {e}")
    
    # Eliminar directorios
    removed_dirs = 0
    for dir_path in dirs_found:
        try:
            shutil.rmtree(dir_path)
            print(f"   ✅ Eliminado: {dir_path}/")
            removed_dirs += 1
        except Exception as e:
            print(f"   ❌ Error eliminando {dir_path}: {e}")
    
    # Limpiar __pycache__
    clean_pycache()
    
    # Limpiar logs
    clean_log_files()
    
    print("\n" + "=" * 60)
    print("🎯 LIMPIEZA COMPLETADA")
    print("=" * 60)
    print(f"✅ Archivos eliminados: {removed_files}")
    print(f"✅ Directorios eliminados: {removed_dirs}")
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("1. Probar que el sistema funcione: python web/main.py")
    print("2. Hacer commit de los cambios al repositorio")
    
    # Crear reporte de limpieza
    report = {
        "timestamp": datetime.now().isoformat(),
        "files_removed": files_found,
        "dirs_removed": dirs_found,
        "files_count": removed_files,
        "dirs_count": removed_dirs
    }
    
    with open("cleanup_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"📋 Reporte guardado en: cleanup_report.json")

if __name__ == "__main__":
    main()
