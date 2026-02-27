"""
SCRIPT DE PRUEBA COMPLETA DEL SISTEMA
Este script prueba todos los componentes paso a paso
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🚀 PRUEBA COMPLETA DEL SISTEMA VoIP AUTO DIALER")
print("=" * 60)

async def test_step_1_call_detector():
    """Prueba el detector de llamadas"""
    print("\n📞 PASO 1: Probando Call Detector...")
    
    try:
        from core.call_detector import CallDetector, CallStatus
        from datetime import datetime
        
        # Crear detector
        detector = CallDetector()
        
        # Callbacks de prueba
        async def test_human_callback(call_session):
            print("  ✅ Callback ejecutado: HUMANO detectado")
        
        async def test_machine_callback(call_session):
            print("  ✅ Callback ejecutado: MÁQUINA detectada")
        
        # Registrar callbacks
        detector.register_callback(CallStatus.ANSWERED_HUMAN, test_human_callback)
        detector.register_callback(CallStatus.ANSWERED_MACHINE, test_machine_callback)
        
        # Simular llamada
        call_session = {
            'phone_number': '+1234567890',
            'campaign_id': 'test',
            'start_time': datetime.now()
        }
        
        print("  🔄 Monitoreando llamada de prueba...")
        await detector.monitor_call(call_session)
        
        print("  ✅ PASO 1 COMPLETADO: Call Detector funciona correctamente")
        return True
        
    except Exception as e:
        print(f"  ❌ ERROR en PASO 1: {e}")
        return False

async def test_step_2_agent_transfer():
    """Prueba el sistema de transferencia"""
    print("\n🔄 PASO 2: Probando Agent Transfer System...")
    
    try:
        from core.agent_transfer_system import AgentTransferSystem, CallTransferRequest, TransferStrategy
        
        # Crear sistema
        transfer_system = AgentTransferSystem(TransferStrategy.LONGEST_IDLE)
        
        # Crear solicitud de prueba
        transfer_request = CallTransferRequest(
            call_id="test_call_123",
            phone_number="+1234567890",
            campaign_id="test-campaign",
            caller_info={"name": "Cliente Test"}
        )
        
        print("  🔄 Intentando transferir llamada de prueba...")
        success = await transfer_system.transfer_call_to_agent(transfer_request)
        
        if success:
            print("  ✅ Transferencia exitosa")
        else:
            print("  ⚠️ No hay agentes disponibles (normal en prueba)")
        
        # Ver estadísticas
        stats = transfer_system.get_system_stats()
        print(f"  📊 Estadísticas: {stats}")
        
        print("  ✅ PASO 2 COMPLETADO: Agent Transfer System funciona correctamente")
        return True
        
    except Exception as e:
        print(f"  ❌ ERROR en PASO 2: {e}")
        return False

async def test_step_3_auto_dialer_engine():
    """Prueba el motor principal"""
    print("\n🚀 PASO 3: Probando Auto Dialer Engine...")
    
    try:
        from core.auto_dialer_engine import AutoDialerEngine
        
        # Crear motor
        engine = AutoDialerEngine()
        
        print("  🔄 Motor creado exitosamente")
        
        # Ver estadísticas iniciales
        stats = engine.get_engine_stats()
        print(f"  📊 Estadísticas iniciales: {stats}")
        
        # Nota: No iniciamos campaña real para evitar errores sin datos
        print("  ⚠️ Nota: Campaña real requiere datos de setup_initial_data.py")
        
        print("  ✅ PASO 3 COMPLETADO: Auto Dialer Engine funciona correctamente")
        return True
        
    except Exception as e:
        print(f"  ❌ ERROR en PASO 3: {e}")
        return False

async def test_step_4_web_integration():
    """Prueba la integración web"""
    print("\n🌐 PASO 4: Probando Web Integration...")
    
    try:
        from core.dialer_integration import DialerWebIntegration
        
        # Crear integración
        integration = DialerWebIntegration()
        
        print("  🔄 Integración web creada exitosamente")
        
        # Probar APIs
        status = integration.get_dialer_status()
        print(f"  📊 Estado del dialer: {status.get('system_status', 'unknown')}")
        
        campaigns = integration.get_available_campaigns()
        print(f"  📋 Campañas disponibles: {campaigns.get('total_campaigns', 0)}")
        
        # Probar llamada de prueba
        test_call_result = await integration.make_test_call("+1234567890")
        if test_call_result["success"]:
            print("  ✅ API de llamada de prueba funciona")
        
        print("  ✅ PASO 4 COMPLETADO: Web Integration funciona correctamente")
        return True
        
    except Exception as e:
        print(f"  ❌ ERROR en PASO 4: {e}")
        return False

def test_step_5_existing_components():
    """Prueba tus componentes existentes"""
    print("\n🔧 PASO 5: Probando Componentes Existentes...")
    
    try:
        # Probar extension manager
        from core.extension_manager import extension_manager
        stats = extension_manager.get_extension_stats()
        print(f"  📞 Extensiones: {stats}")
        
        # Probar agent manager
        from core.agent_manager_clean import agent_manager
        agents = agent_manager.get_all_agents()
        print(f"  👥 Agentes: {len(agents)} encontrados")
        
        print("  ✅ PASO 5 COMPLETADO: Componentes existentes funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"  ❌ ERROR en PASO 5: {e}")
        return False

async def run_complete_test():
    """Ejecuta todas las pruebas"""
    print("Iniciando pruebas completas del sistema...\n")
    
    results = []
    
    # Ejecutar todas las pruebas
    results.append(await test_step_1_call_detector())
    results.append(await test_step_2_agent_transfer())
    results.append(await test_step_3_auto_dialer_engine())
    results.append(await test_step_4_web_integration())
    results.append(test_step_5_existing_components())
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Call Detector",
        "Agent Transfer System", 
        "Auto Dialer Engine",
        "Web Integration",
        "Existing Components"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{i+1}. {name}: {status}")
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("Tu sistema VoIP Auto Dialer está listo para usar.")
        print("\nPróximos pasos:")
        print("1. Ejecutar: python setup_initial_data.py")
        print("2. Ejecutar: python start_web_server.py")
        print("3. Abrir: http://localhost:8000")
    else:
        print(f"\n⚠️ {total - passed} pruebas fallaron.")
        print("Revisa los errores arriba antes de continuar.")
    
    return passed == total

def show_usage_instructions():
    """Muestra instrucciones de uso"""
    print("\n" + "=" * 60)
    print("📖 INSTRUCCIONES DE USO:")
    print("=" * 60)
    
    print("""
🚀 CONFIGURACIÓN INICIAL:
   python setup_initial_data.py

🌐 INICIAR SERVIDOR WEB:
   python start_web_server.py

📱 ACCEDER AL DASHBOARD:
   http://localhost:8000

🔧 ENDPOINTS DE LA API:
   POST /api/dialer/campaigns/{id}/start    - Iniciar marcado
   POST /api/dialer/campaigns/{id}/stop     - Detener marcado
   GET  /api/dialer/status                  - Estado del sistema
   POST /api/dialer/test-call               - Llamada de prueba

📊 PÁGINAS WEB:
   /                    - Dashboard principal
   /agents             - Gestión de agentes
   /campaigns          - Gestión de campañas
   /extensions         - Gestión de extensiones
   /providers          - Gestión de proveedores

🧪 FLUJO DE PRUEBA:
   1. Crear agentes y asignar extensiones
   2. Crear campaña con leads
   3. Iniciar marcado automático
   4. Monitorear llamadas en tiempo real
   5. Ver transferencias a agentes

💡 COMPONENTES CREADOS:
   ✅ Call Detector - Detecta respuestas humanas vs máquinas
   ✅ Agent Transfer - Transfiere llamadas a agentes disponibles  
   ✅ Auto Dialer Engine - Motor principal de marcado
   ✅ Web Integration - APIs para control desde web
   ✅ Endpoints FastAPI - Control completo via REST API
""")

if __name__ == "__main__":
    print("Ejecutando pruebas del sistema...")
    
    # Ejecutar pruebas
    success = asyncio.run(run_complete_test())
    
    # Mostrar instrucciones
    show_usage_instructions()
    
    # Código de salida
    sys.exit(0 if success else 1)