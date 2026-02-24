# Archivo: scripts/debug_dashboard.py

"""
Script de debug específico para el dashboard
"""

import requests
import json

def debug_dashboard():
    """Debug específico del dashboard"""
    base_url = "http://localhost:8000"
    
    print("🔍 DEBUG DEL DASHBOARD")
    print("=" * 40)
    
    # Test dashboard principal
    print("\n1️⃣ TESTING DASHBOARD PRINCIPAL")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   📊 Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Dashboard carga correctamente")
            print(f"   📄 Tamaño de respuesta: {len(response.content)} bytes")
        else:
            print(f"   ❌ Error en dashboard: {response.status_code}")
            print(f"   📄 Respuesta: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # Test APIs individuales
    apis_to_test = [
        "/api/realtime/system-status",
        "/api/realtime/extensions", 
        "/api/realtime/agents",
        "/api/realtime/calls",
        "/api/auto-register/status"
    ]
    
    print("\n2️⃣ TESTING APIs INDIVIDUALES")
    for api in apis_to_test:
        try:
            response = requests.get(f"{base_url}{api}")
            if response.status_code == 200:
                print(f"   ✅ {api}: OK")
            else:
                print(f"   ❌ {api}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {api}: Error - {e}")
    
    print("\n" + "=" * 40)
    print("🎯 DEBUG COMPLETADO")

if __name__ == "__main__":
    debug_dashboard()