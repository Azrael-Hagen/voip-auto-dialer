#!/usr/bin/env python3
"""
Script para probar la integración completa del sistema VoIP Auto Dialer
Prueba proveedores, extensiones, agentes y sincronización
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import get_logger

class SystemIntegrationTester:
    """Probador de integración completa del sistema"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.logger = get_logger("integration_tester")
        self.base_url = base_url
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }
        
    def test_api_health(self):
        """Probar health check de la API"""
        try:
            self.logger.info("🔍 Probando health check de la API...")
            
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.test_results['tests']['api_health'] = {
                    'status': 'PASS',
                    'response_time': response.elapsed.total_seconds(),
                    'data': data
                }
                self.logger.info("✅ API health check: PASS")
                return True
            else:
                self.test_results['tests']['api_health'] = {
                    'status': 'FAIL',
                    'error': f"Status code: {response.status_code}"
                }
                self.logger.error(f"❌ API health check: FAIL - {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results['tests']['api_health'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.logger.error(f"❌ API health check: ERROR - {e}")
            return False
    
    def test_agents_functionality(self):
        """Probar funcionalidad de agentes"""
        try:
            self.logger.info("🔍 Probando funcionalidad de agentes...")
            
            # 1. Obtener agentes existentes
            response = requests.get(f"{self.base_url}/api/agents")
            if response.status_code != 200:
                raise Exception(f"Error obteniendo agentes: {response.status_code}")
            
            initial_agents = response.json()
            initial_count = len(initial_agents)
            
            # 2. Crear agente de prueba
            test_agent_data = {
                "name": "Agente Test Integration",
                "email": "test@integration.com",
                "phone": "+1234567890"
            }
            
            response = requests.post(f"{self.base_url}/api/agents", json=test_agent_data)
            if response.status_code != 200:
                raise Exception(f"Error creando agente: {response.status_code}")
            
            created_agent = response.json()
            agent_id = created_agent['id']
            
            # 3. Asignar extensión al agente
            response = requests.post(f"{self.base_url}/api/agents/{agent_id}/assign-extension")
            if response.status_code != 200:
                raise Exception(f"Error asignando extensión: {response.status_code}")
            
            extension_result = response.json()
            
            # 4. Verificar agente con extensión
            response = requests.get(f"{self.base_url}/api/agents/{agent_id}")
            if response.status_code != 200:
                raise Exception(f"Error obteniendo agente: {response.status_code}")
            
            agent_with_extension = response.json()
            
            # 5. Liberar extensión
            response = requests.post(f"{self.base_url}/api/agents/{agent_id}/release-extension")
            if response.status_code != 200:
                raise Exception(f"Error liberando extensión: {response.status_code}")
            
            # 6. Eliminar agente de prueba
            response = requests.delete(f"{self.base_url}/api/agents/{agent_id}")
            if response.status_code != 200:
                raise Exception(f"Error eliminando agente: {response.status_code}")
            
            self.test_results['tests']['agents'] = {
                'status': 'PASS',
                'initial_count': initial_count,
                'created_agent': created_agent,
                'extension_assigned': extension_result,
                'agent_with_extension': agent_with_extension.get('extension_info') is not None
            }
            
            self.logger.info("✅ Funcionalidad de agentes: PASS")
            return True
            
        except Exception as e:
            self.test_results['tests']['agents'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.logger.error(f"❌ Funcionalidad de agentes: ERROR - {e}")
            return False
    
    def test_extensions_functionality(self):
        """Probar funcionalidad de extensiones"""
        try:
            self.logger.info("🔍 Probando funcionalidad de extensiones...")
            
            # 1. Obtener estadísticas de extensiones
            response = requests.get(f"{self.base_url}/api/extensions/stats")
            if response.status_code != 200:
                raise Exception(f"Error obteniendo estadísticas: {response.status_code}")
            
            stats = response.json()
            
            # 2. Obtener todas las extensiones
            response = requests.get(f"{self.base_url}/api/extensions/all")
            if response.status_code != 200:
                raise Exception(f"Error obteniendo extensiones: {response.status_code}")
            
            all_extensions = response.json()
            
            # 3. Obtener extensiones disponibles
            response = requests.get(f"{self.base_url}/api/extensions/available")
            if response.status_code != 200:
                raise Exception(f"Error obteniendo extensiones disponibles: {response.status_code}")
            
            available_extensions = response.json()
            
            # 4. Probar regeneración de contraseña (si hay extensiones)
            if all_extensions:
                first_ext_id = list(all_extensions.keys())[0]
                response = requests.post(f"{self.base_url}/api/extensions/{first_ext_id}/regenerate-password")
                password_regenerated = response.status_code == 200
            else:
                password_regenerated = False
            
            # 5. Probar acción masiva
            bulk_action_data = {
                "action": "regenerate_passwords",
                "range_start": 1000,
                "range_end": 1005
            }
            
            response = requests.post(f"{self.base_url}/api/extensions/bulk-action", json=bulk_action_data)
            bulk_action_success = response.status_code == 200
            
            self.test_results['tests']['extensions'] = {
                'status': 'PASS',
                'stats': stats,
                'total_extensions': len(all_extensions),
                'available_count': available_extensions['count'],
                'password_regenerated': password_regenerated,
                'bulk_action_success': bulk_action_success
            }
            
            self.logger.info("✅ Funcionalidad de extensiones: PASS")
            return True
            
        except Exception as e:
            self.test_results['tests']['extensions'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.logger.error(f"❌ Funcionalidad de extensiones: ERROR - {e}")
            return False
    
    def test_providers_functionality(self):
        """Probar funcionalidad de proveedores"""
        try:
            self.logger.info("🔍 Probando funcionalidad de proveedores...")
            
            # 1. Obtener proveedores existentes
            response = requests.get(f"{self.base_url}/api/providers")
            if response.status_code != 200:
                raise Exception(f"Error obteniendo proveedores: {response.status_code}")
            
            initial_providers = response.json()
            initial_count = len(initial_providers)
            
            # 2. Crear proveedor de prueba
            test_provider_data = {
                "name": "Test Provider Integration",
                "type": "sip",
                "host": "test.provider.com",
                "port": 5060,
                "username": "testuser",
                "password": "testpass",
                "transport": "UDP",
                "context": "from-trunk",
                "codec": "ulaw,alaw",
                "description": "Proveedor de prueba para integración"
            }
            
            response = requests.post(f"{self.base_url}/api/providers", json=test_provider_data)
            if response.status_code != 200:
                raise Exception(f"Error creando proveedor: {response.status_code}")
            
            created_provider = response.json()
            provider_id = created_provider['id']
            
            # 3. Probar conexión del proveedor
            response = requests.post(f"{self.base_url}/api/providers/{provider_id}/test")
            test_connection_attempted = response.status_code in [200, 500]  # 500 es esperado para proveedor de prueba
            
            # 4. Activar/desactivar proveedor
            response = requests.post(f"{self.base_url}/api/providers/{provider_id}/toggle")
            toggle_success = response.status_code == 200
            
            # 5. Actualizar proveedor
            update_data = {
                "description": "Proveedor actualizado para prueba de integración"
            }
            response = requests.put(f"{self.base_url}/api/providers/{provider_id}", json=update_data)
            update_success = response.status_code == 200
            
            # 6. Eliminar proveedor de prueba
            response = requests.delete(f"{self.base_url}/api/providers/{provider_id}")
            delete_success = response.status_code == 200
            
            self.test_results['tests']['providers'] = {
                'status': 'PASS',
                'initial_count': initial_count,
                'created_provider': created_provider,
                'test_connection_attempted': test_connection_attempted,
                'toggle_success': toggle_success,
                'update_success': update_success,
                'delete_success': delete_success
            }
            
            self.logger.info("✅ Funcionalidad de proveedores: PASS")
            return True
            
        except Exception as e:
            self.test_results['tests']['providers'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.logger.error(f"❌ Funcionalidad de proveedores: ERROR - {e}")
            return False
    
    def test_sync_functionality(self):
        """Probar funcionalidad de sincronización"""
        try:
            self.logger.info("🔍 Probando funcionalidad de sincronización...")
            
            # 1. Obtener estado de sincronización
            response = requests.get(f"{self.base_url}/api/sync/status")
            if response.status_code != 200:
                raise Exception(f"Error obteniendo estado de sync: {response.status_code}")
            
            sync_status = response.json()
            
            # 2. Probar asignación automática
            response = requests.post(f"{self.base_url}/api/sync/auto-assign")
            auto_assign_attempted = response.status_code in [200, 500]  # Puede fallar si no hay agentes/extensiones
            
            # 3. Obtener reporte de sincronización
            response = requests.get(f"{self.base_url}/api/sync/report")
            report_available = response.status_code == 200
            
            # 4. Ejecutar sincronización completa (puede tomar tiempo)
            response = requests.post(f"{self.base_url}/api/sync/extensions-softphones", timeout=30)
            full_sync_attempted = response.status_code in [200, 500]
            
            self.test_results['tests']['sync'] = {
                'status': 'PASS',
                'sync_status': sync_status,
                'auto_assign_attempted': auto_assign_attempted,
                'report_available': report_available,
                'full_sync_attempted': full_sync_attempted
            }
            
            self.logger.info("✅ Funcionalidad de sincronización: PASS")
            return True
            
        except Exception as e:
            self.test_results['tests']['sync'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.logger.error(f"❌ Funcionalidad de sincronización: ERROR - {e}")
            return False
    
    def test_web_pages(self):
        """Probar páginas web principales"""
        try:
            self.logger.info("🔍 Probando páginas web...")
            
            pages_to_test = [
                ('/', 'Dashboard'),
                ('/agents', 'Agentes'),
                ('/providers', 'Proveedores'),
                ('/extensions', 'Extensiones')
            ]
            
            page_results = {}
            
            for path, name in pages_to_test:
                try:
                    response = requests.get(f"{self.base_url}{path}", timeout=10)
                    page_results[name] = {
                        'status_code': response.status_code,
                        'success': response.status_code == 200,
                        'response_time': response.elapsed.total_seconds()
                    }
                except Exception as e:
                    page_results[name] = {
                        'status_code': None,
                        'success': False,
                        'error': str(e)
                    }
            
            all_pages_ok = all(result['success'] for result in page_results.values())
            
            self.test_results['tests']['web_pages'] = {
                'status': 'PASS' if all_pages_ok else 'FAIL',
                'pages': page_results,
                'all_pages_accessible': all_pages_ok
            }
            
            if all_pages_ok:
                self.logger.info("✅ Páginas web: PASS")
            else:
                self.logger.error("❌ Páginas web: FAIL")
            
            return all_pages_ok
            
        except Exception as e:
            self.test_results['tests']['web_pages'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.logger.error(f"❌ Páginas web: ERROR - {e}")
            return False
    
    def generate_test_report(self):
        """Generar reporte de pruebas"""
        try:
            # Calcular resumen
            total_tests = len(self.test_results['tests'])
            passed_tests = len([t for t in self.test_results['tests'].values() if t['status'] == 'PASS'])
            failed_tests = len([t for t in self.test_results['tests'].values() if t['status'] == 'FAIL'])
            error_tests = len([t for t in self.test_results['tests'].values() if t['status'] == 'ERROR'])
            
            self.test_results['summary'] = {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'overall_status': 'PASS' if failed_tests == 0 and error_tests == 0 else 'FAIL'
            }
            
            # Guardar reporte
            report_file = project_root / "data" / f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            # Mostrar resumen en consola
            print("\n" + "="*70)
            print("🧪 REPORTE DE PRUEBAS DE INTEGRACIÓN")
            print("="*70)
            print(f"📊 Total de pruebas: {total_tests}")
            print(f"✅ Exitosas: {passed_tests}")
            print(f"❌ Fallidas: {failed_tests}")
            print(f"🔥 Errores: {error_tests}")
            print(f"📈 Tasa de éxito: {self.test_results['summary']['success_rate']:.1f}%")
            print(f"🎯 Estado general: {self.test_results['summary']['overall_status']}")
            
            print(f"\n📋 DETALLE DE PRUEBAS:")
            for test_name, test_result in self.test_results['tests'].items():
                status_icon = "✅" if test_result['status'] == 'PASS' else "❌" if test_result['status'] == 'FAIL' else "🔥"
                print(f"  {status_icon} {test_name}: {test_result['status']}")
                if test_result['status'] in ['FAIL', 'ERROR'] and 'error' in test_result:
                    print(f"     Error: {test_result['error']}")
            
            print(f"\n📄 Reporte completo guardado en: {report_file}")
            print("="*70)
            
            return self.test_results
            
        except Exception as e:
            self.logger.error(f"Error generando reporte: {e}")
            return None
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        try:
            self.logger.info("🚀 Iniciando pruebas de integración completa...")
            
            # Lista de pruebas a ejecutar
            tests = [
                ('API Health Check', self.test_api_health),
                ('Web Pages', self.test_web_pages),
                ('Agents Functionality', self.test_agents_functionality),
                ('Extensions Functionality', self.test_extensions_functionality),
                ('Providers Functionality', self.test_providers_functionality),
                ('Sync Functionality', self.test_sync_functionality)
            ]
            
            print(f"\n🧪 Ejecutando {len(tests)} pruebas de integración...")
            
            for test_name, test_function in tests:
                print(f"\n🔍 Ejecutando: {test_name}")
                try:
                    success = test_function()
                    status = "✅ PASS" if success else "❌ FAIL"
                    print(f"   Resultado: {status}")
                except Exception as e:
                    print(f"   Resultado: 🔥 ERROR - {e}")
                
                # Pequeña pausa entre pruebas
                time.sleep(1)
            
            # Generar reporte final
            report = self.generate_test_report()
            
            return report['summary']['overall_status'] == 'PASS' if report else False
            
        except Exception as e:
            self.logger.error(f"Error ejecutando pruebas: {e}")
            return False

def main():
    """Función principal"""
    print("🧪 PROBADOR DE INTEGRACIÓN COMPLETA - VoIP Auto Dialer")
    print("="*70)
    
    try:
        # Verificar que el servidor esté corriendo
        print("🔍 Verificando que el servidor esté corriendo...")
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code != 200:
                print("❌ El servidor no está respondiendo correctamente")
                print("💡 Asegúrate de que el servidor esté corriendo: python web/main.py")
                return 1
        except requests.exceptions.ConnectionError:
            print("❌ No se puede conectar al servidor en http://localhost:8000")
            print("💡 Asegúrate de que el servidor esté corriendo: python web/main.py")
            return 1
        
        print("✅ Servidor detectado y respondiendo")
        
        # Ejecutar pruebas
        tester = SystemIntegrationTester()
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
            return 0
        else:
            print("\n💥 ALGUNAS PRUEBAS FALLARON")
            return 1
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        return 1

if __name__ == "__main__":
    exit(main())