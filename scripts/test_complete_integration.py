#!/usr/bin/env python3
"""
Script de pruebas de integración completa del sistema VoIP Auto Dialer
Verifica que todos los componentes funcionen correctamente
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import get_logger

# Logger
logger = get_logger("integration_test")

class IntegrationTester:
    """Clase para ejecutar pruebas de integración completa"""
    
    def __init__(self):
        self.project_root = project_root
        self.base_url = "http://localhost:8000"
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': [],
            'summary': {}
        }
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Ejecutar una prueba individual"""
        self.test_results['tests_run'] += 1
        
        try:
            print(f"🧪 Ejecutando: {test_name}")
            result = test_func(*args, **kwargs)
            
            if result:
                print(f"✅ PASÓ: {test_name}")
                self.test_results['tests_passed'] += 1
                self.test_results['test_details'].append({
                    'name': test_name,
                    'status': 'PASSED',
                    'message': 'Test ejecutado exitosamente'
                })
                return True
            else:
                print(f"❌ FALLÓ: {test_name}")
                self.test_results['tests_failed'] += 1
                self.test_results['test_details'].append({
                    'name': test_name,
                    'status': 'FAILED',
                    'message': 'Test falló sin excepción'
                })
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {str(e)}")
            self.test_results['tests_failed'] += 1
            self.test_results['test_details'].append({
                'name': test_name,
                'status': 'ERROR',
                'message': str(e)
            })
            return False
    
    def test_api_health(self) -> bool:
        """Probar endpoint de salud de la API"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200 and response.json().get('status') == 'ok'
        except Exception:
            return False
    
    def test_web_pages(self) -> bool:
        """Probar que las páginas web respondan correctamente"""
        pages = [
            '/',
            '/agents',
            '/providers',
            '/extensions',
            '/campaigns'
        ]
        
        for page in pages:
            try:
                response = requests.get(f"{self.base_url}{page}", timeout=10)
                if response.status_code != 200:
                    print(f"  ❌ Página {page} devolvió código {response.status_code}")
                    return False
                print(f"  ✅ Página {page} responde correctamente")
            except Exception as e:
                print(f"  ❌ Error accediendo a {page}: {e}")
                return False
        
        return True
    
    def test_agents_api(self) -> bool:
        """Probar API de agentes"""
        try:
            # Obtener agentes
            response = requests.get(f"{self.base_url}/api/agents", timeout=5)
            if response.status_code != 200:
                return False
            
            agents = response.json()
            print(f"  📊 Agentes encontrados: {len(agents)}")
            
            # Crear agente de prueba
            test_agent = {
                "name": "Agente Test Integration",
                "email": "test@integration.com",
                "phone": "+1234567890"
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents",
                json=test_agent,
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"  ❌ Error creando agente de prueba: {response.status_code}")
                return False
            
            created_agent = response.json()
            agent_id = created_agent.get('id')
            print(f"  ✅ Agente de prueba creado: {agent_id}")
            
            # Eliminar agente de prueba
            response = requests.delete(
                f"{self.base_url}/api/agents/{agent_id}",
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"  ⚠️ No se pudo eliminar agente de prueba: {agent_id}")
            else:
                print(f"  🗑️ Agente de prueba eliminado")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error en prueba de agentes: {e}")
            return False
    
    def test_extensions_api(self) -> bool:
        """Probar API de extensiones"""
        try:
            # Obtener estadísticas de extensiones
            response = requests.get(f"{self.base_url}/api/extensions/stats", timeout=5)
            if response.status_code != 200:
                return False
            
            stats = response.json()
            print(f"  📊 Extensiones totales: {stats.get('total', 0)}")
            print(f"  📊 Extensiones asignadas: {stats.get('assigned', 0)}")
            print(f"  📊 Extensiones disponibles: {stats.get('available', 0)}")
            
            # Obtener todas las extensiones
            response = requests.get(f"{self.base_url}/api/extensions/all", timeout=10)
            if response.status_code != 200:
                return False
            
            extensions = response.json()
            print(f"  📋 Extensiones cargadas: {len(extensions)}")
            
            # Probar obtener extensiones disponibles
            response = requests.get(f"{self.base_url}/api/extensions/available", timeout=5)
            if response.status_code != 200:
                return False
            
            available = response.json()
            print(f"  🆓 Extensiones disponibles: {available.get('count', 0)}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error en prueba de extensiones: {e}")
            return False
    
    def test_providers_api(self) -> bool:
        """Probar API de proveedores"""
        try:
            # Obtener proveedores
            response = requests.get(f"{self.base_url}/api/providers", timeout=5)
            if response.status_code != 200:
                return False
            
            providers = response.json()
            print(f"  📊 Proveedores encontrados: {len(providers)}")
            
            # Crear proveedor de prueba
            test_provider = {
                "name": "Test Provider Integration",
                "type": "sip",
                "host": "test.example.com",
                "port": 5060,
                "username": "testuser",
                "password": "testpass",
                "transport": "UDP",
                "context": "from-trunk",
                "codec": "ulaw,alaw",
                "description": "Proveedor de prueba para integración"
            }
            
            response = requests.post(
                f"{self.base_url}/api/providers",
                json=test_provider,
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"  ❌ Error creando proveedor de prueba: {response.status_code}")
                return False
            
            created_provider = response.json()
            provider_id = created_provider.get('id')
            print(f"  ✅ Proveedor de prueba creado: {provider_id}")
            
            # Probar conexión (debería fallar pero no dar error)
            response = requests.post(
                f"{self.base_url}/api/providers/{provider_id}/test",
                timeout=10
            )
            print(f"  🔌 Prueba de conexión ejecutada (código: {response.status_code})")
            
            # Eliminar proveedor de prueba
            response = requests.delete(
                f"{self.base_url}/api/providers/{provider_id}",
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"  ⚠️ No se pudo eliminar proveedor de prueba: {provider_id}")
            else:
                print(f"  🗑️ Proveedor de prueba eliminado")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error en prueba de proveedores: {e}")
            return False
    
    def test_sync_endpoints(self) -> bool:
        """Probar endpoints de sincronización"""
        try:
            # Obtener estado de sincronización
            response = requests.get(f"{self.base_url}/api/sync/status", timeout=5)
            if response.status_code != 200:
                return False
            
            sync_status = response.json()
            print(f"  📊 Estado de sincronización obtenido")
            print(f"  📊 Última sincronización: {sync_status.get('sync_data', {}).get('last_sync', 'Nunca')}")
            
            # Obtener reporte de sincronización
            response = requests.get(f"{self.base_url}/api/sync/report", timeout=5)
            if response.status_code == 200:
                print(f"  📄 Reporte de sincronización disponible")
            else:
                print(f"  ℹ️ No hay reportes de sincronización previos")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error en prueba de sincronización: {e}")
            return False
    
    def test_asterisk_connection(self) -> bool:
        """Probar conexión con Asterisk"""
        try:
            # Verificar que Asterisk esté ejecutándose
            result = subprocess.run([
                "pgrep", "-f", "asterisk"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("  ❌ Asterisk no está ejecutándose")
                return False
            
            print("  ✅ Asterisk está ejecutándose")
            
            # Probar comando básico de Asterisk
            result = subprocess.run([
                "sudo", "asterisk", "-rx", "core show version"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0] if result.stdout else "Versión desconocida"
                print(f"  📋 {version_line}")
                return True
            else:
                print("  ❌ No se pudo obtener versión de Asterisk")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ Timeout conectando con Asterisk")
            return False
        except Exception as e:
            print(f"  ❌ Error probando Asterisk: {e}")
            return False
    
    def test_file_permissions(self) -> bool:
        """Probar permisos de archivos críticos"""
        critical_files = [
            self.project_root / "data" / "extensions.json",
            self.project_root / "data" / "agents.json",
            self.project_root / "data" / "providers.json",
            self.project_root / "logs",
            self.project_root / "web" / "main.py"
        ]
        
        for file_path in critical_files:
            try:
                if file_path.exists():
                    if file_path.is_file():
                        # Probar lectura
                        with open(file_path, 'r') as f:
                            f.read(1)  # Leer solo 1 byte
                        print(f"  ✅ Archivo legible: {file_path.name}")
                    else:
                        # Es directorio
                        list(file_path.iterdir())  # Probar listado
                        print(f"  ✅ Directorio accesible: {file_path.name}")
                else:
                    print(f"  ⚠️ Archivo no existe: {file_path.name}")
                    
            except PermissionError:
                print(f"  ❌ Sin permisos: {file_path.name}")
                return False
            except Exception as e:
                print(f"  ❌ Error accediendo a {file_path.name}: {e}")
                return False
        
        return True
    
    def test_web_server_running(self) -> bool:
        """Verificar que el servidor web esté ejecutándose"""
        try:
            # Verificar proceso del servidor
            result = subprocess.run([
                "pgrep", "-f", "python.*web/main.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"  ✅ Servidor web ejecutándose (PIDs: {', '.join(pids)})")
                return True
            else:
                print("  ❌ Servidor web no está ejecutándose")
                return False
                
        except Exception as e:
            print(f"  ❌ Error verificando servidor web: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generar reporte de pruebas"""
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run'] * 100) if self.test_results['tests_run'] > 0 else 0
        
        report_lines = [
            "=" * 80,
            "📊 REPORTE DE PRUEBAS DE INTEGRACIÓN",
            "=" * 80,
            f"🕐 Fecha y hora: {self.test_results['timestamp']}",
            "",
            "📈 ESTADÍSTICAS GENERALES:",
            f"  • Pruebas ejecutadas: {self.test_results['tests_run']}",
            f"  • Pruebas exitosas: {self.test_results['tests_passed']}",
            f"  • Pruebas fallidas: {self.test_results['tests_failed']}",
            f"  • Tasa de éxito: {success_rate:.1f}%",
            ""
        ]
        
        # Detalles de pruebas
        if self.test_results['test_details']:
            report_lines.extend([
                "📋 DETALLES DE PRUEBAS:",
                ""
            ])
            
            for test in self.test_results['test_details']:
                status_icon = "✅" if test['status'] == 'PASSED' else "❌"
                report_lines.append(f"  {status_icon} {test['name']}: {test['status']}")
                if test['status'] != 'PASSED' and test['message']:
                    report_lines.append(f"      └─ {test['message']}")
            
            report_lines.append("")
        
        # Resumen final
        if success_rate >= 90:
            status = "🎉 EXCELENTE"
            message = "El sistema está funcionando correctamente"
        elif success_rate >= 70:
            status = "✅ BUENO"
            message = "El sistema funciona con algunos problemas menores"
        elif success_rate >= 50:
            status = "⚠️ REGULAR"
            message = "El sistema tiene problemas que requieren atención"
        else:
            status = "❌ CRÍTICO"
            message = "El sistema tiene problemas graves que requieren atención inmediata"
        
        report_lines.extend([
            "🎯 EVALUACIÓN FINAL:",
            f"  Estado: {status}",
            f"  Mensaje: {message}",
            "",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def save_report(self):
        """Guardar reporte en archivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.project_root / "data" / f"integration_test_{timestamp}.json"
            
            # Asegurar que el directorio existe
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            print(f"📄 Reporte guardado en: {report_file}")
            
            # También guardar reporte en texto
            text_report_file = self.project_root / "data" / f"integration_test_{timestamp}.txt"
            text_report = self.generate_report()
            
            with open(text_report_file, 'w') as f:
                f.write(text_report)
            
            print(f"📄 Reporte de texto guardado en: {text_report_file}")
            
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")

def main():
    """Función principal"""
    print("🚀 PRUEBAS DE INTEGRACIÓN COMPLETA - VoIP Auto Dialer")
    print("=" * 70)
    
    tester = IntegrationTester()
    
    # Lista de pruebas a ejecutar
    tests = [
        ("Verificar servidor web ejecutándose", tester.test_web_server_running),
        ("Probar salud de API", tester.test_api_health),
        ("Probar páginas web", tester.test_web_pages),
        ("Probar API de agentes", tester.test_agents_api),
        ("Probar API de extensiones", tester.test_extensions_api),
        ("Probar API de proveedores", tester.test_providers_api),
        ("Probar endpoints de sincronización", tester.test_sync_endpoints),
        ("Probar conexión con Asterisk", tester.test_asterisk_connection),
        ("Verificar permisos de archivos", tester.test_file_permissions)
    ]
    
    print(f"📋 Se ejecutarán {len(tests)} pruebas\n")
    
    # Ejecutar todas las pruebas
    for test_name, test_func in tests:
        tester.run_test(test_name, test_func)
        print()  # Línea en blanco entre pruebas
    
    # Generar y mostrar reporte
    report = tester.generate_report()
    print(report)
    
    # Guardar reporte
    tester.save_report()
    
    # Código de salida basado en resultados
    if tester.test_results['tests_failed'] == 0:
        print("🎉 TODAS LAS PRUEBAS PASARON")
        return 0
    else:
        print(f"❌ {tester.test_results['tests_failed']} PRUEBAS FALLARON")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Pruebas canceladas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error crítico en pruebas: {e}")
        sys.exit(1)