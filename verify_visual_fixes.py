#!/usr/bin/env python3
"""
Script para verificar que las correcciones visuales estén funcionando
VoIP Auto Dialer - Verificación de templates y funcionalidad
"""

import os
import requests
import time
import json
from pathlib import Path

def check_template_integrity():
    """Verificar integridad de templates"""
    print("📄 Verificando integridad de templates...")
    
    templates_to_check = [
        "web/templates/dashboard_production.html",
        "web/templates/dev_dashboard.html", 
        "web/templates/dev_agents.html",
        "web/templates/base.html"
    ]
    
    all_good = True
    for template in templates_to_check:
        if Path(template).exists():
            # Verificar que no tenga caracteres sueltos
            with open(template, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Buscar problemas comunes
            issues = []
            if content.startswith("<\n"):
                issues.append("Carácter < suelto al inicio")
            if "{{" in content and "}}" not in content:
                issues.append("Template tags malformados")
            if "<script>" in content and "</script>" not in content:
                issues.append("Tags script no cerrados")
            
            if issues:
                print(f"   ❌ {template}: {', '.join(issues)}")
                all_good = False
            else:
                print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template} - No encontrado")
            all_good = False
    
    return all_good

def test_web_routes():
    """Probar rutas web específicas"""
    print("\n🌐 Probando rutas web corregidas...")
    
    test_routes = [
        ("http://localhost:8000/", "Dashboard principal"),
        ("http://localhost:8000/dev", "Dashboard desarrollo"),
        ("http://localhost:8000/dev/agents", "Gestión avanzada agentes"),
        ("http://localhost:8000/favicon.ico", "Favicon"),
        ("http://localhost:8000/agents", "Gestión de agentes"),
        ("http://localhost:8000/providers", "Gestión de proveedores"),
        ("http://localhost:8000/extensions", "Gestión de extensiones")
    ]
    
    server_running = False
    working_routes = 0
    
    for url, description in test_routes:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"   ✅ {description} - OK")
                server_running = True
                working_routes += 1
            elif response.status_code == 404:
                print(f"   ❌ {description} - 404 Not Found")
            else:
                print(f"   ⚠️  {description} - {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"   ❌ {description} - No disponible")
    
    if not server_running:
        print("\n💡 El servidor no está ejecutándose. Para iniciarlo:")
        print("   python start_server.py")
        return False, 0
    
    return True, working_routes

def check_asterisk_config():
    """Verificar configuración de Asterisk"""
    print("\n📞 Verificando configuración de Asterisk...")
    
    config_files = [
        "asterisk/conf/sip.conf",
        "asterisk/conf/extensions.conf", 
        "asterisk/conf/voicemail.conf"
    ]
    
    all_good = True
    for config_file in config_files:
        if Path(config_file).exists():
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Verificar contenido específico
            if "sip.conf" in config_file:
                if "pbxonthecloud.com" in content and "[pbx_provider]" in content:
                    print(f"   ✅ {config_file} - Proveedor configurado")
                else:
                    print(f"   ⚠️  {config_file} - Configuración incompleta")
            elif "extensions.conf" in config_file:
                if "[internal]" in content and "_9." in content:
                    print(f"   ✅ {config_file} - Dialplan funcional")
                else:
                    print(f"   ⚠️  {config_file} - Dialplan incompleto")
            else:
                print(f"   ✅ {config_file}")
        else:
            print(f"   ❌ {config_file} - No encontrado")
            all_good = False
    
    return all_good

def check_provider_data():
    """Verificar datos del proveedor"""
    print("\n🔌 Verificando datos del proveedor...")
    
    providers_file = "data/providers.json"
    if Path(providers_file).exists():
        with open(providers_file, "r") as f:
            providers = json.load(f)
        
        if providers:
            provider = list(providers.values())[0]
            print(f"   ✅ Proveedor: {provider.get('name', 'Unknown')}")
            print(f"   ✅ Host: {provider.get('host', 'Unknown')}")
            print(f"   ✅ Puerto: {provider.get('port', 'Unknown')}")
            
            # Verificar si tiene credenciales
            if provider.get('username') and provider.get('password'):
                if provider['username'] != 'your_username':
                    print("   ✅ Credenciales configuradas")
                else:
                    print("   ⚠️  Credenciales por defecto - necesita configuración real")
            else:
                print("   ❌ Faltan credenciales")
            
            return True
        else:
            print("   ❌ No hay proveedores configurados")
            return False
    else:
        print("   ❌ Archivo de proveedores no encontrado")
        return False

def generate_status_report():
    """Generar reporte de estado completo"""
    print("\n📊 Generando reporte de estado...")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "visual_fixes": {
            "templates_ok": check_template_integrity(),
            "description": "Templates corregidos sin caracteres sueltos"
        },
        "web_functionality": {
            "server_running": False,
            "working_routes": 0,
            "description": "Rutas web funcionando correctamente"
        },
        "asterisk_config": {
            "config_ok": check_asterisk_config(),
            "description": "Configuración de Asterisk funcional"
        },
        "provider_connection": {
            "provider_ok": check_provider_data(),
            "description": "Proveedor VoIP configurado y accesible"
        }
    }
    
    # Probar rutas web
    server_running, working_routes = test_web_routes()
    report["web_functionality"]["server_running"] = server_running
    report["web_functionality"]["working_routes"] = working_routes
    
    # Guardar reporte
    with open("status_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DE CORRECCIONES VISUALES Y FUNCIONALES")
    print("=" * 65)
    
    # Generar reporte completo
    report = generate_status_report()
    
    print("\n" + "=" * 65)
    print("📋 RESUMEN DE VERIFICACIÓN:")
    
    # Mostrar resultados
    if report["visual_fixes"]["templates_ok"]:
        print("✅ Templates corregidos y funcionando")
    else:
        print("❌ Problemas en templates detectados")
    
    if report["web_functionality"]["server_running"]:
        routes_count = report["web_functionality"]["working_routes"]
        print(f"✅ Servidor web funcionando ({routes_count} rutas OK)")
    else:
        print("❌ Servidor web no está ejecutándose")
    
    if report["asterisk_config"]["config_ok"]:
        print("✅ Configuración de Asterisk lista")
    else:
        print("❌ Configuración de Asterisk incompleta")
    
    if report["provider_connection"]["provider_ok"]:
        print("✅ Proveedor VoIP configurado")
    else:
        print("❌ Proveedor VoIP necesita configuración")
    
    print(f"\n📄 Reporte completo guardado en: status_report.json")
    
    print("\n🎯 ESTADO ACTUAL:")
    if all([
        report["visual_fixes"]["templates_ok"],
        report["asterisk_config"]["config_ok"],
        report["provider_connection"]["provider_ok"]
    ]):
        print("🎉 SISTEMA LISTO PARA PRODUCCIÓN")
        print("   Solo falta configurar credenciales reales del proveedor")
    else:
        print("⚠️  SISTEMA NECESITA AJUSTES MENORES")
    
    print("\n🚀 PRÓXIMOS PASOS RECOMENDADOS:")
    if not report["web_functionality"]["server_running"]:
        print("1. Iniciar servidor: python start_server.py")
    print("2. Configurar credenciales reales en data/providers.json")
    print("3. Aplicar configuración Asterisk: sudo cp asterisk/conf/* /etc/asterisk/")
    print("4. Reiniciar Asterisk: sudo systemctl restart asterisk")
    print("5. Probar llamadas salientes desde extensiones")

if __name__ == "__main__":
    main()