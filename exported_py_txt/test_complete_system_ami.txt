#!/usr/bin/env python3
"""
Script de prueba completa del sistema con AMI
"""

import sys
import requests
import time
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_web_server():
    """Probar que el servidor web esté respondiendo"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor web respondiendo")
            return True
        else:
            print(f"❌ Servidor web error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al servidor web: {e}")
        return False

def test_ami_endpoints():
    """Probar endpoints AMI en tiempo real"""
    print("\n🔍 PROBANDO ENDPOINTS AMI")
    print("=" * 50)
    
    endpoints = [
        "/api/realtime/system-status",
        "/api/realtime/extensions", 
        "/api/realtime/calls",
        "/api/realtime/dashboard"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {"status": "✅", "data": data}
                print(f"✅ {endpoint}: OK")
                
                # Mostrar datos relevantes
                if endpoint == "/api/realtime/system-status":
                    print(f"   📊 Sistema: {data.get('status', 'Unknown')}")
                elif endpoint == "/api/realtime/extensions":
                    print(f"   📞 Extensiones: {data.get('online', 0)}/{data.get('total', 0)} online")
                elif endpoint == "/api/realtime/calls":
                    print(f"   📱 Llamadas activas: {data.get('active', 0)}")
                elif endpoint == "/api/realtime/dashboard":
                    sys_status = data.get('system', {}).get('status', 'Unknown')
                    ext_total = data.get('extensions', {}).get('total', 0)
                    calls_active = data.get('calls', {}).get('active', 0)
                    print(f"   📊 Dashboard: Sistema {sys_status}, {ext_total} ext, {calls_active} llamadas")
                    
            else:
                results[endpoint] = {"status": "❌", "error": f"HTTP {response.status_code}"}
                print(f"❌ {endpoint}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            results[endpoint] = {"status": "❌", "error": str(e)}
            print(f"❌ {endpoint}: {e}")
    
    return results

def test_ami_monitor_directly():
    """Probar el monitor AMI directamente"""
    print("\n🔍 PROBANDO MONITOR AMI DIRECTAMENTE")
    print("=" * 50)
    
    try:
        from core.asterisk_ami_monitor import asterisk_ami_monitor
        
        # Probar conexión
        if asterisk_ami_monitor.connect():
            print("✅ Conexión AMI directa exitosa")
            
            # Probar obtener estado del sistema
            system_status = asterisk_ami_monitor.get_system_status()
            print(f"✅ Estado del sistema: {system_status.get('status', 'Unknown')}")
            
            # Probar obtener endpoints
            endpoints = asterisk_ami_monitor.get_pjsip_endpoints()
            print(f"✅ Endpoints PJSIP: {len(endpoints)} encontrados")
            
            # Probar obtener llamadas
            calls = asterisk_ami_monitor.get_active_calls()
            print(f"✅ Llamadas activas: {len(calls)}")
            
            # Probar dashboard completo
            dashboard = asterisk_ami_monitor.get_realtime_dashboard_data()
            print(f"✅ Dashboard completo: Sistema {dashboard.get('system', {}).get('status', 'Unknown')}")
            
            asterisk_ami_monitor.disconnect()
            return True
            
        else:
            print("❌ Error conectando AMI directamente")
            return False
            
    except Exception as e:
        print(f"❌ Error probando monitor AMI: {e}")
        return False

def test_frontend_pages():
    """Probar que las páginas frontend carguen"""
    print("\n🔍 PROBANDO PÁGINAS FRONTEND")
    print("=" * 50)
    
    pages = [
        ("/", "Dashboard Principal"),
        ("/providers", "Gestión de Proveedores"),
        ("/dev/agents", "Gestión de Agentes (Dev)"),
        ("/dev/campaigns", "Gestión de Campañas (Dev)")
    ]
    
    for url, name in pages:
        try:
            response = requests.get(f"http://localhost:8000{url}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: {e}")

def main():
    """Función principal de pruebas"""
    print("🧪 PRUEBA COMPLETA DEL SISTEMA AMI")
    print("=" * 60)
    
    # Verificar servidor web
    if not test_web_server():
        print("❌ Servidor web no disponible")
        print("💡 Ejecutar: python3 web/main.py")
        return False
    
    # Probar monitor AMI directamente
    ami_direct_ok = test_ami_monitor_directly()
    
    # Probar endpoints AMI
    ami_endpoints = test_ami_endpoints()
    
    # Probar páginas frontend
    test_frontend_pages()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("🎯 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    if ami_direct_ok:
        print("✅ Monitor AMI directo: FUNCIONANDO")
    else:
        print("❌ Monitor AMI directo: ERROR")
    
    ami_endpoints_ok = all(result["status"] == "✅" for result in ami_endpoints.values())
    if ami_endpoints_ok:
        print("✅ Endpoints AMI web: FUNCIONANDO")
    else:
        print("❌ Endpoints AMI web: ALGUNOS ERRORES")
        for endpoint, result in ami_endpoints.items():
            if result["status"] == "❌":
                print(f"   ❌ {endpoint}: {result.get('error', 'Error desconocido')}")
    
    if ami_direct_ok and ami_endpoints_ok:
        print("\n🎉 SISTEMA AMI COMPLETAMENTE FUNCIONAL")
        print("💡 Ahora puedes usar el dashboard sin sudo")
        print("🌐 Acceder a: http://localhost:8000")
        return True
    else:
        print("\n⚠️  SISTEMA AMI CON PROBLEMAS")
        print("💡 Revisar configuración AMI")
        print("💡 Ejecutar: ./scripts/check_ami.sh")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)