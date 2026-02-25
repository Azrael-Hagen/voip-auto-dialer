# Archivo: scripts/test_production_system.py

"""
Script de prueba completa del sistema de producción VoIP
Verifica dashboard profesional, auto-registro, proveedores y funcionalidad completa
"""

import requests
import json
import time
from datetime import datetime

def test_production_system():
    """Prueba completa del sistema de producción"""
    base_url = "http://localhost:8000"
    
    print("🔍 PRUEBA COMPLETA DEL SISTEMA DE PRODUCCIÓN")
    print("=" * 60)
    
    # 1. Test Dashboard Profesional
    print("\n1️⃣ TESTING DASHBOARD PROFESIONAL")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   ✅ Dashboard profesional carga correctamente")
        else:
            print(f"   ❌ Error en dashboard: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error conectando al dashboard: {e}")
    
    # 2. Test API en tiempo real
    print("\n2️⃣ TESTING API EN TIEMPO REAL")
    try:
        response = requests.get(f"{base_url}/api/realtime/system-status")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API en tiempo real funciona")
            print(f"   📊 Sistema: {data.get('system_status', 'Unknown')}")
            print(f"   📞 Extensiones: {data.get('total_extensions', 0)}")
            print(f"   📱 Llamadas activas: {data.get('active_calls', 0)}")
        else:
            print(f"   ❌ Error en API tiempo real: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en API tiempo real: {e}")
    
    # 3. Test Sistema de Auto-Registro
    print("\n3️⃣ TESTING SISTEMA DE AUTO-REGISTRO")
    try:
        # Verificar estado
        response = requests.get(f"{base_url}/api/auto-register/status")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API de auto-registro funciona")
            status = data.get('status', {})
            print(f"   🔄 Monitoreo: {'Activo' if status.get('monitoring') else 'Inactivo'}")
            print(f"   📱 Endpoints registrados: {status.get('registered_endpoints', 0)}")
            
            # Test iniciar monitoreo
            start_response = requests.post(f"{base_url}/api/auto-register/start")
            if start_response.status_code == 200:
                print("   ✅ Inicio de monitoreo funciona")
            else:
                print(f"   ⚠️ Advertencia en inicio de monitoreo: {start_response.status_code}")
                
        else:
            print(f"   ❌ Error en API auto-registro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en auto-registro: {e}")
    
    # 4. Test Gestión de Proveedores
    print("\n4️⃣ TESTING GESTIÓN DE PROVEEDORES")
    try:
        response = requests.get(f"{base_url}/providers")
        if response.status_code == 200:
            print("   ✅ Página de proveedores carga correctamente")
        else:
            print(f"   ❌ Error en página proveedores: {response.status_code}")
            
        # Test API proveedores
        api_response = requests.get(f"{base_url}/api/providers")
        if api_response.status_code == 200:
            providers = api_response.json()
            print(f"   ✅ API proveedores funciona: {len(providers)} proveedores")
        else:
            print(f"   ❌ Error en API proveedores: {api_response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en proveedores: {e}")
    
    # 5. Test Rutas de Desarrollo
    print("\n5️⃣ TESTING RUTAS DE DESARROLLO")
    dev_routes = ["/dev", "/dev/agents", "/dev/campaigns"]
    for route in dev_routes:
        try:
            response = requests.get(f"{base_url}{route}")
            if response.status_code == 200:
                print(f"   ✅ Ruta {route} accesible")
            else:
                print(f"   ❌ Error en {route}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error en {route}: {e}")
    
    # 6. Test Funcionalidad de Agentes
    print("\n6️⃣ TESTING FUNCIONALIDAD DE AGENTES")
    try:
        # Listar agentes
        response = requests.get(f"{base_url}/api/agents")
        if response.status_code == 200:
            agents_data = response.json()
            if isinstance(agents_data, dict):
                agents_count = len(agents_data)
            else:
                agents_count = len(agents_data.get('agents', []))
            print(f"   ✅ API agentes funciona: {agents_count} agentes")
            
            # Test crear agente
            test_agent = {
                "name": f"Test Agent {int(time.time()) % 100000}",
                "email": "test@production.com",
                "phone": "+1234567890"
            }
            
            create_response = requests.post(f"{base_url}/api/agents", json=test_agent)
            if create_response.status_code == 200:
                agent_data = create_response.json()
                agent_id = agent_data.get('id') or agent_data.get('agent', {}).get('id')
                print(f"   ✅ Creación de agente funciona: {agent_id}")
                
                # Test asignar extensión
                if agent_id:
                    assign_response = requests.post(f"{base_url}/api/agents/{agent_id}/assign-extension")
                    if assign_response.status_code == 200:
                        print("   ✅ Asignación de extensión funciona")
                    else:
                        print(f"   ⚠️ Advertencia asignando extensión: {assign_response.status_code}")
            else:
                print(f"   ❌ Error creando agente: {create_response.status_code}")
        else:
            print(f"   ❌ Error en API agentes: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en funcionalidad agentes: {e}")
    
    # 7. Test Estadísticas de Extensiones
    print("\n7️⃣ TESTING ESTADÍSTICAS DE EXTENSIONES")
    try:
        response = requests.get(f"{base_url}/api/extensions/stats")
        if response.status_code == 200:
            stats = response.json()
            print("   ✅ Estadísticas de extensiones:")
            print(f"      📊 Total: {stats.get('total', 0)}")
            print(f"      📊 Asignadas: {stats.get('assigned', 0)}")
            print(f"      📊 Disponibles: {stats.get('available', 0)}")
            print(f"      📊 Utilización: {stats.get('utilization', 0):.1f}%")
        else:
            print(f"   ❌ Error en estadísticas: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en estadísticas: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 PRUEBA COMPLETA FINALIZADA")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Verificar que todas las pruebas pasen ✅")
    print("   2. Acceder a http://localhost:8000 para ver dashboard profesional")
    print("   3. Acceder a http://localhost:8000/providers para gestión de proveedores")
    print("   4. Usar http://localhost:8000/dev para herramientas de desarrollo")
    print("   5. Configurar softphones para probar auto-registro")

if __name__ == "__main__":
    test_production_system()