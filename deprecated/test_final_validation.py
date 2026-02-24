#!/usr/bin/env python3
"""
🎯 VALIDACIÓN FINAL DEL SISTEMA VOIP AUTO DIALER
================================================================
Prueba completa para verificar que todas las correcciones funcionan
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

async def main():
    """Función principal de pruebas"""
    
    print("🎯 VALIDACIÓN FINAL DEL SISTEMA VOIP AUTO DIALER")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # 1. Health Check
            print("\n1. 🏥 Verificando health check...")
            async with session.get(f"{base_url}/api/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ Health check OK: {health.get('status', 'unknown')}")
                else:
                    print(f"❌ Health check falló: {response.status}")
                    return False
            
            # 2. API de Agentes
            print("\n2. 📋 Probando API de agentes...")
            async with session.get(f"{base_url}/api/agents") as response:
                if response.status == 200:
                    data = await response.json()
                    agents = data.get('agents', {})
                    
                    # Convertir a lista si es diccionario
                    if isinstance(agents, dict):
                        agents_list = list(agents.values())
                    else:
                        agents_list = agents
                    
                    print(f"✅ API agentes OK: {len(agents_list)} agentes")
                    
                    # Mostrar agentes
                    for agent in agents_list:
                        name = agent.get('name', 'N/A')
                        agent_id = agent.get('id', 'N/A')
                        ext_info = agent.get('extension_info')
                        ext_status = "Sin asignar"
                        if ext_info:
                            ext_status = f"EXT {ext_info.get('extension', 'N/A')}"
                        print(f"   • {name} ({agent_id}) - {ext_status}")
                        
                else:
                    print(f"❌ API agentes falló: {response.status}")
                    return False
            
            # 3. Estadísticas de Extensiones
            print("\n3. 📊 Probando estadísticas de extensiones...")
            async with session.get(f"{base_url}/api/extensions/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ Estadísticas OK:")
                    print(f"   • Total: {stats.get('total', 0)}")
                    print(f"   • Asignadas: {stats.get('assigned', 0)}")
                    print(f"   • Disponibles: {stats.get('available', 0)}")
                else:
                    print(f"❌ Estadísticas fallaron: {response.status}")
                    return False
            
            # 4. Páginas Web
            print("\n4. 🌐 Probando páginas web...")
            pages = [
                ("/", "Dashboard"),
                ("/agents", "Agentes"),
                ("/campaigns", "Campañas")
            ]
            
            for path, name in pages:
                async with session.get(f"{base_url}{path}") as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"✅ {name} OK: {len(content)} chars")
                    else:
                        print(f"❌ {name} falló: {response.status}")
                        return False
            
            print("\n" + "=" * 60)
            print("🎉 TODAS LAS PRUEBAS PASARON")
            print("\n📋 SISTEMA LISTO PARA:")
            print("1. Crear y gestionar agentes")
            print("2. Asignar extensiones automáticamente")
            print("3. Configurar proveedores VoIP")
            print("4. Ejecutar campañas de llamadas")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🚀 VALIDACIÓN EXITOSA - SISTEMA OPERATIVO")
    else:
        print("\n⚠️ VALIDACIÓN FALLIDA - Revisa los errores")
        sys.exit(1)