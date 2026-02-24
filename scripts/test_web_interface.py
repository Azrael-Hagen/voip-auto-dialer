#!/usr/bin/env python3
# Test completo de la interfaz web

import requests
import json
import sys
from datetime import datetime

def test_web_server():
    """Test del servidor web"""
    base_url = "http://localhost:8000"
    
    print("🌐 TESTING SERVIDOR WEB")
    print("=" * 50)
    
    # Test 1: Página principal
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Página principal: {response.status_code}")
    except Exception as e:
        print(f"❌ Error página principal: {e}")
        return False
    
    # Test 2: API de agentes
    try:
        response = requests.get(f"{base_url}/api/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ API agentes: {len(agents)} agentes encontrados")
            
            # Mostrar agentes
            for agent_id, agent in agents.items():
                ext_info = agent.get('extension_info')
                ext_status = f"Ext: {ext_info['extension']}" if ext_info else "Sin extensión"
                print(f"   📞 {agent['name']} ({agent_id}) - {ext_status}")
        else:
            print(f"❌ API agentes error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error API agentes: {e}")
    
    # Test 3: Estadísticas de extensiones
    try:
        response = requests.get(f"{base_url}/api/extensions/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Extensiones stats: {stats}")
        else:
            print(f"❌ Extensions stats error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error extensions stats: {e}")
    
    # Test 4: Crear agente de prueba
    print(f"\n🧪 TESTING CREACIÓN DE AGENTE")
    test_agent = {
        "name": f"Test Agent {datetime.now().strftime('%H%M%S')}",
        "email": "test@example.com",
        "phone": "+1234567890"
    }
    
    try:
        response = requests.post(f"{base_url}/api/agents", json=test_agent)
        if response.status_code == 200:
            new_agent = response.json()
            print(f"✅ Agente creado: {new_agent['id']}")
            
            # Test 5: Asignar extensión
            agent_id = new_agent['id']
            response = requests.post(f"{base_url}/api/agents/{agent_id}/assign-extension")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Extensión asignada: {result}")
            else:
                print(f"❌ Error asignando extensión: {response.status_code} - {response.text}")
        else:
            print(f"❌ Error creando agente: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error en test de creación: {e}")
    
    return True

def check_web_pages():
    """Verificar que las páginas web cargan correctamente"""
    print(f"\n📄 TESTING PÁGINAS WEB")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    pages = [
        ("/", "Dashboard"),
        ("/agents", "Gestión de Agentes"),
        ("/campaigns", "Gestión de Campañas")
    ]
    
    for path, name in pages:
        try:
            response = requests.get(f"{base_url}{path}")
            if response.status_code == 200:
                print(f"✅ {name}: Carga correctamente")
                # Verificar si contiene formularios
                if "form" in response.text.lower():
                    print(f"   📋 Contiene formularios")
                if "button" in response.text.lower():
                    print(f"   🔘 Contiene botones")
            else:
                print(f"❌ {name}: Error {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error {e}")

def main():
    print("🔍 TEST COMPLETO DE INTERFAZ WEB")
    print("=" * 60)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        print("✅ Servidor web está respondiendo")
    except Exception as e:
        print(f"❌ Servidor web no responde: {e}")
        print("💡 Asegúrate de que el servidor esté corriendo:")
        print("   cd ~/voip-auto-dialer && python3 web/main.py")
        return
    
    test_web_server()
    check_web_pages()
    
    print(f"\n" + "=" * 60)
    print("🎯 TEST COMPLETADO")
    print("=" * 60)
    
    print(f"\n💡 PARA ACCEDER A LA INTERFAZ WEB:")
    print("   🌐 Abrir navegador en: http://localhost:8000")
    print("   📞 Gestión de agentes: http://localhost:8000/agents")
    print("   📋 Gestión de campañas: http://localhost:8000/campaigns")

if __name__ == "__main__":
    main()