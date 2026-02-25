
#!/usr/bin/env python3
"""
Script para analizar el estado actual de los proveedores en el frontend
Revisará templates, endpoints y funcionalidad actual
"""

import os
import json
from pathlib import Path

def analyze_provider_templates():
    """Analizar templates relacionados con proveedores"""
    print("🔍 ANALIZANDO TEMPLATES DE PROVEEDORES")
    print("=" * 60)
    
    templates_dir = Path("web/templates")
    if not templates_dir.exists():
        print("❌ Directorio de templates no encontrado")
        return
    
    # Buscar templates relacionados con proveedores
    provider_templates = []
    for template_file in templates_dir.glob("*.html"):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if any(keyword in content.lower() for keyword in ['provider', 'proveedor', 'voip']):
                provider_templates.append(template_file.name)
                print(f"✅ Encontrado: {template_file.name}")
    
    if not provider_templates:
        print("❌ No se encontraron templates de proveedores")
    
    return provider_templates

def analyze_provider_endpoints():
    """Analizar endpoints de proveedores en main.py"""
    print("\n🔍 ANALIZANDO ENDPOINTS DE PROVEEDORES")
    print("=" * 60)
    
    main_py = Path("web/main.py")
    if not main_py.exists():
        print("❌ Archivo main.py no encontrado")
        return
    
    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar endpoints relacionados con proveedores
    provider_endpoints = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if '/api/providers' in line or '/providers' in line:
            # Extraer información del endpoint
            if '@app.' in line:
                method = line.split('@app.')[1].split('(')[0]
                endpoint = line.split('"')[1] if '"' in line else "N/A"
                provider_endpoints.append({
                    'method': method,
                    'endpoint': endpoint,
                    'line': i + 1
                })
                print(f"✅ {method.upper()}: {endpoint} (línea {i + 1})")
    
    if not provider_endpoints:
        print("❌ No se encontraron endpoints de proveedores")
    
    return provider_endpoints

def analyze_provider_data():
    """Analizar datos de proveedores existentes"""
    print("\n🔍 ANALIZANDO DATOS DE PROVEEDORES")
    print("=" * 60)
    
    providers_file = Path("data/providers.json")
    if not providers_file.exists():
        print("❌ Archivo providers.json no encontrado")
        return {}
    
    with open(providers_file, 'r', encoding='utf-8') as f:
        providers = json.load(f)
    
    print(f"📊 Total de proveedores: {len(providers)}")
    
    for provider_id, provider_data in providers.items():
        print(f"  🏢 {provider_data.get('name', 'Sin nombre')} ({provider_id})")
        print(f"     Tipo: {provider_data.get('type', 'N/A')}")
        print(f"     Host: {provider_data.get('host', 'N/A')}")
        print(f"     Estado: {provider_data.get('status', 'N/A')}")
        print()
    
    return providers

def analyze_provider_manager():
    """Analizar funcionalidad del provider_manager"""
    print("🔍 ANALIZANDO PROVIDER MANAGER")
    print("=" * 60)
    
    provider_manager_file = Path("core/provider_manager.py")
    if not provider_manager_file.exists():
        print("❌ Archivo provider_manager.py no encontrado")
        return
    
    with open(provider_manager_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar métodos principales
    methods = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def ') and not line.strip().startswith('def __'):
            method_name = line.strip().split('def ')[1].split('(')[0]
            methods.append(method_name)
            print(f"✅ Método: {method_name}")
    
    print(f"\n📊 Total de métodos: {len(methods)}")
    return methods

def check_frontend_functionality():
    """Verificar funcionalidad del frontend"""
    print("\n🔍 VERIFICANDO FUNCIONALIDAD DEL FRONTEND")
    print("=" * 60)
    
    # Verificar si existe página de proveedores
    templates_dir = Path("web/templates")
    provider_page_exists = False
    
    for template_file in templates_dir.glob("*provider*.html"):
        provider_page_exists = True
        print(f"✅ Página de proveedores encontrada: {template_file.name}")
        
        # Analizar contenido del template
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Buscar funcionalidades
        functionalities = {
            'crear_proveedor': 'create' in content.lower() or 'crear' in content.lower(),
            'editar_proveedor': 'edit' in content.lower() or 'editar' in content.lower(),
            'eliminar_proveedor': 'delete' in content.lower() or 'eliminar' in content.lower(),
            'listar_proveedores': 'list' in content.lower() or 'table' in content.lower(),
            'activar_proveedor': 'activate' in content.lower() or 'activar' in content.lower(),
            'probar_conexion': 'test' in content.lower() or 'probar' in content.lower()
        }
        
        print("\n📋 Funcionalidades detectadas:")
        for func, exists in functionalities.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {func.replace('_', ' ').title()}")
    
    if not provider_page_exists:
        print("❌ No se encontró página específica de proveedores")
    
    return provider_page_exists

def generate_analysis_report():
    """Generar reporte completo del análisis"""
    print("\n" + "=" * 60)
    print("📋 REPORTE DE ANÁLISIS - PROVEEDORES")
    print("=" * 60)
    
    # Ejecutar todos los análisis
    templates = analyze_provider_templates()
    endpoints = analyze_provider_endpoints()
    providers = analyze_provider_data()
    methods = analyze_provider_manager()
    frontend_ok = check_frontend_functionality()
    
    # Generar reporte
    report = {
        'templates_encontrados': len(templates) if templates else 0,
        'endpoints_disponibles': len(endpoints) if endpoints else 0,
        'proveedores_configurados': len(providers) if providers else 0,
        'metodos_disponibles': len(methods) if methods else 0,
        'frontend_funcional': frontend_ok,
        'problemas_detectados': []
    }
    
    # Detectar problemas
    if not templates:
        report['problemas_detectados'].append("No hay templates de proveedores")
    
    if not endpoints:
        report['problemas_detectados'].append("No hay endpoints de proveedores")
    
    if not providers:
        report['problemas_detectados'].append("No hay proveedores configurados")
    
    if not frontend_ok:
        report['problemas_detectados'].append("Frontend de proveedores incompleto")
    
    # Mostrar resumen
    print(f"\n🎯 RESUMEN:")
    print(f"  📄 Templates: {report['templates_encontrados']}")
    print(f"  🔗 Endpoints: {report['endpoints_disponibles']}")
    print(f"  🏢 Proveedores: {report['proveedores_configurados']}")
    print(f"  ⚙️  Métodos: {report['metodos_disponibles']}")
    print(f"  🖥️  Frontend: {'✅ Funcional' if report['frontend_funcional'] else '❌ Incompleto'}")
    
    if report['problemas_detectados']:
        print(f"\n⚠️  PROBLEMAS DETECTADOS:")
        for problema in report['problemas_detectados']:
            print(f"  • {problema}")
    
    # Guardar reporte
    with open('provider_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Reporte guardado en: provider_analysis_report.json")
    
    return report

if __name__ == "__main__":
    print("🚀 ANÁLISIS DE PROVEEDORES - VoIP Auto Dialer")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not Path("web/main.py").exists():
        print("❌ Error: Ejecutar desde el directorio raíz del proyecto")
        exit(1)
    
    # Generar análisis completo
    report = generate_analysis_report()
    
    print("\n" + "=" * 60)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 60)
    print("💡 PRÓXIMO PASO:")
    print("   Revisar el reporte y planificar mejoras del frontend")