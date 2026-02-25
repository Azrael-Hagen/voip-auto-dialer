
#!/usr/bin/env python3
"""
Script simple para eliminar líneas específicas de extension_manager.py
"""

from pathlib import Path

def fix_extension_manager_simple():
    """Eliminar líneas específicas conocidas"""
    
    project_root = Path(__file__).parent.parent
    extension_manager_file = project_root / "core" / "extension_manager.py"
    
    print("🔧 Eliminando líneas duplicadas específicas...")
    
    # Leer todas las líneas
    with open(extension_manager_file, 'r') as f:
        lines = f.readlines()
    
    print(f"📄 Archivo original: {len(lines)} líneas")
    
    # Eliminar líneas 351-561 (métodos duplicados fuera de clase)
    # Ajustar índices (líneas empiezan en 0)
    start_line = 350  # línea 351
    end_line = 561    # línea 562
    
    # Crear archivo sin las líneas problemáticas
    clean_lines = lines[:start_line] + lines[end_line:]
    
    print(f"🗑️ Eliminando líneas {start_line+1} a {end_line}")
    print(f"📄 Archivo limpio: {len(clean_lines)} líneas")
    
    # Escribir archivo limpio
    with open(extension_manager_file, 'w') as f:
        f.writelines(clean_lines)
    
    print("✅ Archivo reparado")
    
    # Verificar sintaxis
    try:
        import ast
        with open(extension_manager_file, 'r') as f:
            content = f.read()
        ast.parse(content)
        print("✅ Sintaxis verificada")
        return True
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False

if __name__ == "__main__":
    success = fix_extension_manager_simple()
    if success:
        print("\n🎉 REPARACIÓN EXITOSA")
    else:
        print("\n❌ REPARACIÓN FALLIDA")
