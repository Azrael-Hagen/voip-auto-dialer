
#!/usr/bin/env python3
# Diagnóstico de la interfaz web frontend

import os
import re

def analyze_agents_html():
    """Analizar el archivo agents.html para ver qué funcionalidades tiene"""
    print("🔍 ANÁLISIS DE agents.html")
    print("=" * 50)
    
    agents_file = "/home/azrael/voip-auto-dialer/web/templates/agents.html"
    
    if not os.path.exists(agents_file):
        print("❌ agents.html no existe")
        return
    
    with open(agents_file, 'r') as f:
        content = f.read()
    
    # Buscar formularios
    forms = re.findall(r'<form[^>]*>(.*?)</form>', content, re.DOTALL)
    print(f"📋 Formularios encontrados: {len(forms)}")
    
    for i, form in enumerate(forms):
        print(f"\n   Formulario {i+1}:")
        # Buscar action
        action = re.search(r'action=["\']([^"\']*)["\']', form)
        if action:
            print(f"      Action: {action.group(1)}")
        
        # Buscar method
        method = re.search(r'method=["\']([^"\']*)["\']', form)
        if method:
            print(f"      Method: {method.group(1)}")
        
        # Buscar inputs
        inputs = re.findall(r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>', form)
        if inputs:
            print(f"      Inputs: {inputs}")
    
    # Buscar JavaScript
    js_scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    print(f"\n🔧 Scripts JavaScript: {len(js_scripts)}")
    
    for i, script in enumerate(js_scripts):
        if 'fetch' in script or 'ajax' in script or 'XMLHttpRequest' in script:
            print(f"   Script {i+1}: Contiene llamadas AJAX/Fetch")
        elif 'function' in script:
            functions = re.findall(r'function\s+(\w+)', script)
            print(f"   Script {i+1}: Funciones: {functions}")
    
    # Buscar botones importantes
    buttons = re.findall(r'<button[^>]*onclick=["\']([^"\']*)["\'][^>]*>([^<]*)</button>', content)
    print(f"\n🔘 Botones con onclick: {len(buttons)}")
    for onclick, text in buttons:
        print(f"   '{text.strip()}' -> {onclick}")

def check_static_files():
    """Verificar archivos estáticos (CSS, JS)"""
    print(f"\n🔍 ARCHIVOS ESTÁTICOS")
    print("=" * 50)
    
    static_dir = "/home/azrael/voip-auto-dialer/web/static"
    
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, static_dir)
            size = os.path.getsize(file_path)
            print(f"   📄 {rel_path} ({size} bytes)")

def main():
    print("🔍 DIAGNÓSTICO DE FRONTEND")
    print("=" * 60)
    
    analyze_agents_html()
    check_static_files()
    
    print(f"\n💡 PRÓXIMOS PASOS:")
    print("1. Verificar si hay JavaScript funcional")
    print("2. Comprobar conexión entre frontend y API")
    print("3. Reparar formularios si es necesario")

if __name__ == "__main__":
    main()

