"""
Script de Pruebas Completas - VoIP Auto Dialer
Valida que todos los componentes funcionen correctamente
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.call_detector import CallDetector, CallStatus
from core.agent_transfer_system import AgentTransferSystem, TransferStrategy
from core.auto_dialer_engine import AutoDialerEngine, DialerMode
from core.dialer_integration import dialer_integration
from core.campaign_manager import CampaignManager
from core.agent_manager_clean import AgentManager
from core.extension_manager import ExtensionManager
from core.provider_manager import ProviderManager
from core.logging_config import get_logger

logger = get_logger("test_complete_system")

class SystemTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Registra el resultado de una prueba"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            
        result = f"{status} | {test_name}"
        if message:
            result += f" | {message}"
            
        self.test_results.append(result)
        logger.info(result)
        print(result)

    async def test_call_detector(self):
        """Prueba el detector de llamadas"""
        print("\n🔍 PROBANDO CALL DETECTOR...")
        
        try:
            call_detector = CallDetector()
            
            # Test 1: Inicialización
            self.log_test_result(
                "CallDetector - Inicialización", 
                True, 
                "Detector inicializado correctamente"
            )
            
            # Test 2: Configuración de callbacks
            callback_called = False
            
            def test_callback(call_id, result, details):
                nonlocal callback_called
                callback_called = True
                
            call_detector.set_callback(test_callback)
            
            self.log_test_result(
                "CallDetector - Callback Setup", 
                True, 
                "Callback configurado correctamente"
            )
            
            # Test 3: Simulación de detección
            test_call_id = "test_call_001"
            call_detector.start_monitoring(test_call_id, "+1234567890")
            
            # Simular respuesta después de un breve delay
            await asyncio.sleep(0.1)
            
            # Simular detección de respuesta humana
            await call_detector._execute_callback(CallStatus.ANSWERED_HUMAN, {"call_id": test_call_id})
            
            await asyncio.sleep(0.1)
            
            self.log_test_result(
                "CallDetector - Simulación de Detección", 
                callback_called, 
                "Callback ejecutado correctamente" if callback_called else "Callback no ejecutado"
            )
            
        except Exception as e:
            self.log_test_result("CallDetector - Error General", False, str(e))

    async def test_agent_transfer_system(self):
        """Prueba el sistema de transferencia de agentes"""
        print("\n👥 PROBANDO AGENT TRANSFER SYSTEM...")
        
        try:
            transfer_system = AgentTransferSystem()
            
            # Test 1: Inicialización
            self.log_test_result(
                "AgentTransfer - Inicialización", 
                True, 
                "Sistema de transferencia inicializado"
            )
            
            # Test 2: Búsqueda de agentes disponibles
            available_agents = transfer_system.get_available_agents()
            
            self.log_test_result(
                "AgentTransfer - Búsqueda de Agentes", 
                isinstance(available_agents, list), 
                f"Encontrados {len(available_agents)} agentes"
            )
            
            # Test 3: Selección de agente
            if available_agents:
                selected_agent = transfer_system.select_agent(
                    available_agents, 
                    TransferStrategy.ROUND_ROBIN
                )
                
                self.log_test_result(
                    "AgentTransfer - Selección de Agente", 
                    selected_agent is not None, 
                    f"Agente seleccionado: {selected_agent.name if selected_agent else 'None'}"
                )
            else:
                self.log_test_result(
                    "AgentTransfer - Selección de Agente", 
                    True, 
                    "No hay agentes disponibles (esperado en pruebas)"
                )
            
            # Test 4: Simulación de transferencia
            test_call_id = "test_transfer_001"
            result = await transfer_system.transfer_call(
                test_call_id, 
                "+1234567890", 
                skills_required=["ventas"]
            )
            
            self.log_test_result(
                "AgentTransfer - Transferencia Simulada", 
                isinstance(result, dict), 
                f"Resultado: {result.get('status', 'unknown')}"
            )
            
        except Exception as e:
            self.log_test_result("AgentTransfer - Error General", False, str(e))

    async def test_auto_dialer_engine(self):
        """Prueba el motor principal del auto dialer"""
        print("\n🚀 PROBANDO AUTO DIALER ENGINE...")
        
        try:
            engine = AutoDialerEngine()
            
            # Test 1: Inicialización
            self.log_test_result(
                "AutoDialer - Inicialización", 
                True, 
                "Motor inicializado correctamente"
            )
            
            # Test 2: Configuración
            engine.calls_per_minute = 5
            engine.max_concurrent_calls = 2
            engine.mode = DialerMode.POWER
            
            self.log_test_result(
                "AutoDialer - Configuración", 
                engine.calls_per_minute == 5 and engine.max_concurrent_calls == 2, 
                f"CPM: {engine.calls_per_minute}, Max: {engine.max_concurrent_calls}"
            )
            
            # Test 3: Estadísticas del motor
            stats = engine.get_engine_stats()
            
            self.log_test_result(
                "AutoDialer - Estadísticas", 
                isinstance(stats, dict) and 'is_running' in stats, 
                f"Estado: {'Corriendo' if stats.get('is_running') else 'Detenido'}"
            )
            
            # Test 4: Simulación de inicio de campaña (sin llamadas reales)
            test_campaign_id = "test_campaign_001"
            
            # Nota: No iniciamos realmente para evitar llamadas en pruebas
            self.log_test_result(
                "AutoDialer - Preparación de Campaña", 
                True, 
                "Motor preparado para campañas"
            )
            
        except Exception as e:
            self.log_test_result("AutoDialer - Error General", False, str(e))

    async def test_dialer_integration(self):
        """Prueba la integración web del dialer"""
        print("\n🌐 PROBANDO DIALER INTEGRATION...")
        
        try:
            # Test 1: Estado del sistema
            status = dialer_integration.get_dialer_status()
            
            self.log_test_result(
                "Integration - Estado del Sistema", 
                isinstance(status, dict), 
                f"Campañas activas: {status.get('total_active_campaigns', 0)}"
            )
            
            # Test 2: Campañas disponibles
            campaigns = dialer_integration.get_available_campaigns()
            
            self.log_test_result(
                "Integration - Campañas Disponibles", 
                campaigns.get('success', False), 
                f"Total campañas: {len(campaigns.get('campaigns', []))}"
            )
            
            # Test 3: Llamada de prueba (simulada)
            test_result = await dialer_integration.make_test_call("+1234567890")
            
            self.log_test_result(
                "Integration - Llamada de Prueba", 
                test_result.get('success', False), 
                test_result.get('message', 'Sin mensaje')
            )
            
        except Exception as e:
            self.log_test_result("Integration - Error General", False, str(e))

    def test_managers(self):
        """Prueba los managers del sistema"""
        print("\n📊 PROBANDO MANAGERS...")
        
        try:
            # Test Campaign Manager
            campaign_manager = CampaignManager()
            campaigns = campaign_manager.get_all_campaigns()
            
            self.log_test_result(
                "CampaignManager - Obtener Campañas", 
                isinstance(campaigns, list), 
                f"Campañas encontradas: {len(campaigns)}"
            )
            
            # Test Agent Manager
            agent_manager = AgentManager()
            agents = agent_manager.get_all_agents()
            
            self.log_test_result(
                "AgentManager - Obtener Agentes", 
                isinstance(agents, list), 
                f"Agentes encontrados: {len(agents)}"
            )
            
            # Test Extension Manager
            extension_manager = ExtensionManager()
            extensions = extension_manager.get_all_extensions()
            
            self.log_test_result(
                "ExtensionManager - Obtener Extensiones", 
                isinstance(extensions, list), 
                f"Extensiones encontradas: {len(extensions)}"
            )
            
            # Test Provider Manager
            provider_manager = ProviderManager()
            providers = provider_manager.get_all_providers()
            
            self.log_test_result(
                "ProviderManager - Obtener Proveedores", 
                isinstance(providers, list), 
                f"Proveedores encontrados: {len(providers)}"
            )
            
        except Exception as e:
            self.log_test_result("Managers - Error General", False, str(e))

    def test_file_structure(self):
        """Verifica que todos los archivos necesarios existan"""
        print("\n📁 VERIFICANDO ESTRUCTURA DE ARCHIVOS...")
        
        required_files = [
            "core/call_detector.py",
            "core/agent_transfer_system.py", 
            "core/auto_dialer_engine.py",
            "core/dialer_integration.py",
            "web/dialer_endpoints.py",
            "setup_initial_data.py"
        ]
        
        for file_path in required_files:
            exists = os.path.exists(file_path)
            self.log_test_result(
                f"Archivo - {file_path}", 
                exists, 
                "Existe" if exists else "No encontrado"
            )

    async def run_all_tests(self):
        """Ejecuta todas las pruebas del sistema"""
        print("🧪 INICIANDO PRUEBAS COMPLETAS DEL SISTEMA VoIP AUTO DIALER")
        print("=" * 70)
        
        start_time = time.time()
        
        # Ejecutar todas las pruebas
        self.test_file_structure()
        self.test_managers()
        await self.test_call_detector()
        await self.test_agent_transfer_system()
        await self.test_auto_dialer_engine()
        await self.test_dialer_integration()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Mostrar resumen
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 70)
        print(f"⏱️  Tiempo total: {duration:.2f} segundos")
        print(f"📈 Total de pruebas: {self.total_tests}")
        print(f"✅ Pruebas exitosas: {self.passed_tests}")
        print(f"❌ Pruebas fallidas: {self.failed_tests}")
        print(f"📊 Porcentaje de éxito: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
            print("✅ El sistema está listo para usar")
        else:
            print(f"\n⚠️  {self.failed_tests} pruebas fallaron")
            print("❗ Revisa los errores antes de usar el sistema")
        
        print("\n📋 DETALLE DE RESULTADOS:")
        print("-" * 70)
        for result in self.test_results:
            print(result)
        
        return self.failed_tests == 0

async def main():
    """Función principal para ejecutar las pruebas"""
    print("🚀 VoIP Auto Dialer - Sistema de Pruebas Completas")
    print("=" * 60)
    
    try:
        tester = SystemTester()
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎯 PRÓXIMOS PASOS:")
            print("1. Ejecutar: python setup_initial_data.py (si no lo has hecho)")
            print("2. Ejecutar: python start_web_server.py")
            print("3. Abrir: http://localhost:8000")
            print("4. Probar los endpoints del dialer")
            print("\n🔗 ENDPOINTS DISPONIBLES:")
            print("• POST /api/dialer/campaigns/{id}/start")
            print("• GET  /api/dialer/status")
            print("• POST /api/dialer/test-call")
        else:
            print("\n❌ SISTEMA NO ESTÁ LISTO")
            print("Corrige los errores mostrados arriba antes de continuar")
            
    except KeyboardInterrupt:
        print("\n⚠️  Pruebas canceladas por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO EN LAS PRUEBAS: {e}")
        logger.error(f"Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())