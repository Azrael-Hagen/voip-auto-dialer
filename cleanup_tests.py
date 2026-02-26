#!/usr/bin/env python3
"""
Limpieza de archivos de test duplicados y obsoletos
"""
import os
from pathlib import Path

# Archivos de test a eliminar (obsoletos/duplicados)
files_to_remove = [
    "scripts/test_manual_load.py",
    "scripts/test_web_interface.py", 
    "scripts/test_production_system.py",
    "scripts/test_complete_system_ami.py",
    "scripts/test_ami_connection.py",
    "test_extension_calls_enhanced.py",
    "test_final_validation.py"
]

print("🧹 LIMPIEZA DE ARCHIVOS DE TEST")
print("=" * 50)

for file_path in files_to_remove:
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"✅ Eliminado: {file_path}")
        except Exception as e:
            print(f"❌ Error eliminando {file_path}: {e}")
    else:
        print(f"⚠️  No existe: {file_path}")

print("\n🎯 ARCHIVOS DE TEST FINALES:")
print("- scripts/test_current_system.py (PRINCIPAL)")
print("- scripts/test_complete_integration.py (INTEGRACIÓN)")

print("\n✅ LIMPIEZA COMPLETADA")
