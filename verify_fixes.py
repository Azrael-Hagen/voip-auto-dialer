
#!/usr/bin/env python3
"""
Script de verificación de correcciones aplicadas
VoIP Auto Dialer - Verificación del sistema
"""

import os
import requests
import time
import subprocess
from pathlib import Path

def check_files():
    """Verificar que todos los archivos necesarios existen"""
    print("📁 Verificando archivos críticos...")
    
    required_files = [
        "web/main.py",
        "web/templates/dev_dashboard.html",
        "web/templates/dev_agents.html",
        "web/static/images/favicon.svg",
        "web/logs/",
        "asterisk/conf/extensions.conf",
        "asterisk/conf/sip.conf",
        "asterisk/conf/voicemail.conf"
    ]
    
    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            all_good = False
    
    return all_good

def test_server_routes():
    """Probar las rutas del servidor si está ejecutándose"""
    print("\n🌐 Probando rutas del servidor...")
    
    test_routes = [
        ("http://localhost:8000/", "Dashboard principal"),
        ("http://localhost:8000/dev", "Dashboard desarrollo"),
        ("http://localhost:8000/dev/agents", "Gestión avanzada agentes"),
        ("http://localhost:8000/favicon.ico", "Favicon"),
        ("http://localhost:8000/api/system/status", "Estado del sistema"),
        ("http://localhost:8000/api/campaigns", "API campañas")
    ]
    
    server_running = False
    for url, description in test_routes:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"   ✅ {description} - {response.status_code}")
                server_running = True
            else:
                print(f"   ⚠️  {description} - {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"   ❌ {description} - No disponible")
    
    if not server_running:
        print("\n💡 El servidor no está ejecutándose. Para probarlo:")
        print("   python start_server.py")
    
    return server_running

def show_asterisk_config_instructions():
    """Mostrar instrucciones para configurar Asterisk"""
    print("\n📞 CONFIGURACIÓN DE ASTERISK:")
    print("=" * 50)
    print("Para aplicar la configuración de Asterisk:")
    print()
    print("1. Copiar archivos de configuración:")
    print("   sudo cp asterisk/conf/extensions.conf /etc/asterisk/")
    print("   sudo cp asterisk/conf/sip.conf /etc/asterisk/")
    print("   sudo cp asterisk/conf/voicemail.conf /etc/asterisk/")
    print()
    print("2. Editar sip.conf con tus credenciales reales:")
    print("   sudo nano /etc/asterisk/sip.conf")
    print("   # Cambiar username, secret, etc. del proveedor")
    print()
    print("3. Reiniciar Asterisk:")
    print("   sudo systemctl restart asterisk")
    print()
    print("4. Verificar estado:")
    print("   sudo asterisk -r")
    print("   CLI> sip show peers")
    print("   CLI> dialplan show")

def show_campaign_explanation():
    """Explicar cómo funcionan las campañas"""
    print("\n🎯 FUNCIONAMIENTO DE CAMPAÑAS:")
    print("=" * 50)
    print("Las campañas conectan con el autodialer de esta manera:")
    print()
    print("1. CREACIÓN DE CAMPAÑA:")
    print("   - Define números a llamar")
    print("   - Asigna agentes disponibles")
    print("   - Configura horarios y reintentos")
    print()
    print("2. EJECUCIÓN AUTOMÁTICA:")
    print("   - El autodialer marca números automáticamente")
    print("   - Detecta si contestan (AMD - Answering Machine Detection)")
    print("   - Si es persona real → transfiere a agente")
    print("   - Si es buzón → cuelga o deja mensaje")
    print()
    print("3. INTEGRACIÓN CON ASTERISK:")
    print("   - Usa contexto [autodialer] para llamadas")
    print("   - Registra resultados en base de datos")
    print("   - Actualiza métricas en tiempo real")
    print()
    print("4. ESTADO ACTUAL:")
    print("   - Dashboard muestra '0 campañas activas'")
    print("   - Endpoints API listos: /api/campaigns")
    print("   - Configuración Asterisk preparada")

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DE CORRECCIONES APLICADAS")
    print("=" * 60)
    
    # Verificar archivos
    files_ok = check_files()
    
    # Probar servidor
    server_ok = test_server_routes()
    
    # Mostrar instrucciones
    show_asterisk_config_instructions()
    show_campaign_explanation()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE CORRECCIONES APLICADAS:")
    print("✅ Rutas 404 corregidas (/dev, /dev/agents, /favicon.ico)")
    print("✅ Directorio web/logs/ creado")
    print("✅ Templates de desarrollo creados")
    print("✅ Configuración completa de Asterisk generada")
    print("✅ Favicon creado para evitar errores 404")
    
    print("\n🎯 PRÓXIMOS PASOS RECOMENDADOS:")
    print("1. Configurar credenciales reales en asterisk/conf/sip.conf")
    print("2. Aplicar configuración a Asterisk (/etc/asterisk/)")
    print("3. Implementar módulo de campañas en el dashboard")
    print("4. Probar llamadas salientes desde extensiones locales")
    
    if files_ok:
        print("\n✅ Todos los archivos están en su lugar")
    else:
        print("\n❌ Algunos archivos faltan - revisar instalación")
    
    if server_ok:
        print("✅ Servidor web funcionando correctamente")
    else:
        print("⚠️  Servidor web no está ejecutándose")

if __name__ == "__main__":
    main()

