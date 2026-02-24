
#!/usr/bin/env python3
# Análisis completo del sistema web VoIP Auto Dialer

import os
import json
import re
from pathlib import Path

def analyze_file_structure():
    """Analizar estructura de archivos del proyecto web"""
    print("🔍 ANÁLISIS DE ESTRUCTURA DE ARCHIVOS")
    print("=" * 60)
    
    base_path = Path("/home/azrael/voip-auto-dialer")
    
    # Estructura esperada
    expected_structure = {
        "web/": ["main.py", "templates/", "static/"],
        "web/templates/": ["*.html"],
        "web/static/": ["css/", "js/"],
        "core/": ["agent_manager_clean.py", "extension_manager.py"],
        "data/": ["agents.json", "extensions.json"]
    }
    
    print("📁 ESTRUCTURA ACTUAL:")
    for root_dir, expected_files in expected_structure.items():
        full_path = base_path / root_dir
        print(f"\n📂 {root_dir}")
        
        if full_path.exists():
            print(f"   ✅ Directorio existe")
            
            # Listar archivos reales
            if full_path.is_dir():
                real_files = list(full_path.iterdir())
                for file_path in sorted(real_files):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        print(f"      📄 {file_path.name} ({size} bytes)")
                    elif file_path.is_dir():
                        subfiles = list(file_path.iterdir())
                        print(f"      📁 {file_path.name}/ ({len(subfiles)} archivos)")
        else:
            print(f"   ❌ Directorio NO existe")

def analyze_main_py():
    """Analizar el archivo main.py del servidor web"""
    print("\n🔍 ANÁLISIS DE main.py")
    print("=" * 60)
    
    main_py_path = "/home/azrael/voip-auto-dialer/web/main.py"
    
    if not os.path.exists(main_py_path):
        print("❌ main.py NO EXISTE")
        return None
    
    try:
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        print(f"📄 Archivo: {len(content)} caracteres, {len(content.splitlines())} líneas")
        
        # Analizar imports
        imports = re.findall(r'^(?:from|import)\s+([^\s]+)', content, re.MULTILINE)
        print(f"\n📦 IMPORTS DETECTADOS:")
        for imp in sorted(set(imports)):
            print(f"   - {imp}")
        
        # Analizar rutas/endpoints
        routes = re.findall(r'@app\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)
        print(f"\n🛣️  RUTAS/ENDPOINTS DETECTADOS:")
        for method, route in routes:
            print(f"   {method.upper():6} {route}")
        
        # Analizar funciones
        functions = re.findall(r'^def\s+([^(]+)', content, re.MULTILINE)
        print(f"\n🔧 FUNCIONES DETECTADAS:")
        for func in functions:
            print(f"   - {func}()")
        
        return content
        
    except Exception as e:
        print(f"❌ Error leyendo main.py: {e}")
        return None

def analyze_templates():
    """Analizar templates HTML"""
    print("\n🔍 ANÁLISIS DE TEMPLATES")
    print("=" * 60)
    
    templates_path = Path("/home/azrael/voip-auto-dialer/web/templates")
    
    if not templates_path.exists():
        print("❌ Directorio templates NO EXISTE")
        return
    
    html_files = list(templates_path.glob("*.html"))
    print(f"📄 Templates encontrados: {len(html_files)}")
    
    for html_file in sorted(html_files):
        print(f"\n📝 {html_file.name}:")
        try:
            with open(html_file, 'r') as f:
                content = f.read()
            
            # Buscar formularios
            forms = re.findall(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>', content)
            if forms:
                print(f"   📋 Formularios: {forms}")
            
            # Buscar botones/enlaces importantes
            buttons = re.findall(r'<(?:button|a)[^>]*>([^<]+)</(?:button|a)>', content)
            if buttons:
                important_buttons = [btn.strip() for btn in buttons if any(word in btn.lower() for word in ['crear', 'agregar', 'add', 'create', 'edit', 'delete'])]
                if important_buttons:
                    print(f"   🔘 Botones importantes: {important_buttons[:5]}")
            
            print(f"   📏 Tamaño: {len(content)} caracteres")
            
        except Exception as e:
            print(f"   ❌ Error leyendo {html_file.name}: {e}")

def analyze_data_files():
    """Analizar archivos de datos"""
    print("\n🔍 ANÁLISIS DE ARCHIVOS DE DATOS")
    print("=" * 60)
    
    data_files = {
        "agents.json": "/home/azrael/voip-auto-dialer/data/agents.json",
        "extensions.json": "/home/azrael/voip-auto-dialer/data/extensions.json"
    }
    
    for name, path in data_files.items():
        print(f"\n📊 {name}:")
        
        if not os.path.exists(path):
            print(f"   ❌ Archivo NO EXISTE")
            continue
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                print(f"   📋 Tipo: Lista con {len(data)} elementos")
                if len(data) > 0:
                    print(f"   🔍 Primer elemento: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
                    
                    # Mostrar algunos ejemplos
                    for i, item in enumerate(data[:3]):
                        if isinstance(item, dict):
                            key_info = {k: v for k, v in item.items() if k in ['id', 'name', 'extension', 'username', 'email']}
                            print(f"   📄 Elemento {i+1}: {key_info}")
            
            elif isinstance(data, dict):
                print(f"   📋 Tipo: Diccionario con {len(data)} claves")
                print(f"   🔑 Claves: {list(data.keys())}")
            
            size = os.path.getsize(path)
            print(f"   📏 Tamaño: {size} bytes")
            
        except Exception as e:
            print(f"   ❌ Error leyendo {name}: {e}")

def analyze_core_modules():
    """Analizar módulos core"""
    print("\n🔍 ANÁLISIS DE MÓDULOS CORE")
    print("=" * 60)
    
    core_files = {
        "agent_manager_clean.py": "/home/azrael/voip-auto-dialer/core/agent_manager_clean.py",
        "extension_manager.py": "/home/azrael/voip-auto-dialer/core/extension_manager.py"
    }
    
    for name, path in core_files.items():
        print(f"\n🔧 {name}:")
        
        if not os.path.exists(path):
            print(f"   ❌ Archivo NO EXISTE")
            continue
        
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            # Buscar clases
            classes = re.findall(r'^class\s+([^(:\s]+)', content, re.MULTILINE)
            if classes:
                print(f"   🏗️  Clases: {classes}")
            
            # Buscar funciones principales
            functions = re.findall(r'^def\s+([^(]+)', content, re.MULTILINE)
            main_functions = [f for f in functions if not f.startswith('_')]
            if main_functions:
                print(f"   🔧 Funciones públicas: {main_functions[:10]}")
            
            print(f"   📏 Tamaño: {len(content)} caracteres")
            
        except Exception as e:
            print(f"   ❌ Error leyendo {name}: {e}")

def check_web_functionality():
    """Verificar funcionalidades web específicas"""
    print("\n🔍 VERIFICACIÓN DE FUNCIONALIDADES WEB")
    print("=" * 60)
    
    # Verificar si el servidor está corriendo
    import subprocess
    try:
        result = subprocess.run("ps aux | grep 'python.*main.py' | grep -v grep", 
                              shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            print("✅ Servidor web parece estar ejecutándose")
            print(f"   📋 Proceso: {result.stdout.strip()}")
        else:
            print("❌ Servidor web NO está ejecutándose")
    except Exception as e:
        print(f"⚠️  No se pudo verificar estado del servidor: {e}")
    
    # Verificar puerto 8000
    try:
        result = subprocess.run("netstat -tlnp | grep :8000", 
                              shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            print("✅ Puerto 8000 está en uso")
            print(f"   📋 {result.stdout.strip()}")
        else:
            print("❌ Puerto 8000 NO está en uso")
    except Exception as e:
        print(f"⚠️  No se pudo verificar puerto 8000: {e}")

def main():
    print("🔍 ANÁLISIS COMPLETO DEL SISTEMA WEB")
    print("=" * 80)
    
    analyze_file_structure()
    main_content = analyze_main_py()
    analyze_templates()
    analyze_data_files()
    analyze_core_modules()
    check_web_functionality()
    
    print("\n" + "=" * 80)
    print("🎯 ANÁLISIS COMPLETADO")
    print("=" * 80)
    
    # Recomendaciones
    print("\n💡 PRÓXIMOS PASOS RECOMENDADOS:")
    print("1. Revisar la salida del análisis")
    print("2. Identificar funcionalidades faltantes")
    print("3. Decidir si reparar o recrear desde cero")
    print("4. Implementar gestión completa de agentes y campañas")

if __name__ == "__main__":
    main()