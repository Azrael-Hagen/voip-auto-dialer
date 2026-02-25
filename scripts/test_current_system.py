
#!/usr/bin/env python3
"""
Script de pruebas del sistema actual antes de migración
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
logger = get_logger("test_current_system")

class CurrentSystemTester:
    """Clase para probar el sistema actual antes de migración"""
    
    def __init__(self):
        self.project_root = project_root
        self.base_url = "http://localhost:8000"
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': [],
            'warnings': [],
            'test_details': [],
            'system_status': 'unknown'
        }
    
    def run_test(self, test_name: str, test_func, critical: bool = False) -> bool:
        """Ejecutar una prueba individual"""
        self.test_results['tests_run'] += 1
        
        try:
            print(f"🧪 Probando: {test_name}")
            result = test_func()
            
            if result:
                print(f"✅ PASÓ: {test_name}")
                self.test_results['tests_passed'] += 1
                self.test_results['test_details'].append({
                    'name': test_name,
                    'status': 'PASSED',
                    'critical': critical,
                    'message': 'Test ejecutado exitosamente'
                })
                return True
            else:
                print(f"❌ FALLÓ: {test_name}")
                self.test_results['tests_failed'] += 1
                message = f"Test falló: {test_name}"
                
                if critical:
                    self.test_results['critical_issues'].append(message)
                else:
                    self.test_results['warnings'].append(message)
                
                self.test_results['test_details'].append({
                    'name': test_name,
                    'status': 'FAILED',
                    'critical': critical,
                    'message': message
                })
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {str(e)}")
            self.test_results['tests_failed'] += 1
            error_msg = f"Error en {test_name}: {str(e)}"
            
            if critical:
                self.test_results['critical_issues'].append(error_msg)
            else:
                self.test_results['warnings'].append(error_msg)
            
            self.test_results['test_details'].append({
                'name': test_name,
                'status': 'ERROR',
                'critical': critical,
                'message': error_msg
            })
            return False
    
    def test_server_running(self) -> bool:
        """Verificar que el servidor web esté ejecutándose"""
        try:
            # Verificar proceso del servidor
            result = subprocess.run([
                "pgrep", "-f", "python.*web/main.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"  ✅ Servidor ejecutándose (PIDs: {', '.join(pids)})")
                return True
            else:
                print("  ❌ Servidor web no está ejecutándose")
                print("  💡 Ejecutar: python web/main.py")
                return False
                
        except Exception as e:
            print(f"  ❌ Error verificando servidor: {e}")
            return False
    
    def test_api_health(self) -> bool:
        """Probar endpoint de salud de la API"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ API responde - Status: {data.get('status', 'unknown')}")
                return data.get('status') == 'ok'
            else:
                print(f"  ❌ API devolvió código {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("  ❌ No se puede conectar al servidor")
            print("  💡 ¿Está ejecutándose el servidor en puerto 8000?")
            return False
        except Exception as e:
            print(f"  ❌ Error probando API: {e}")
            return False
    
    def test_core_modules(self) -> bool:
        """Probar que los módulos core se puedan importar"""
        modules_to_test = [
            'core.extension_manager',
            'core.agent_manager_clean',
            'core.provider_manager',
            'core.asterisk_monitor'
        ]
        
        failed_imports = []
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"  ✅ Módulo importado: {module_name}")
            except Exception as e:
                print(f"  ❌ Error importando {module_name}: {e}")
                failed_imports.append(module_name)
        
        return len(failed_imports) == 0
    
    def test_data_files(self) -> bool:
        """Verificar archivos de datos críticos"""
        critical_files = [
            "data/extensions.json",
            "data/agents.json", 
            "data/providers.json"
        ]
        
        missing_files = []
        corrupted_files = []
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                missing_files.append(file_path)
                print(f"  ⚠️ Archivo faltante: {file_path}")
                continue
            
            try:
                with open(full_path, 'r') as f:
                    json.load(f)
                print(f"  ✅ Archivo válido: {file_path}")
            except json.JSONDecodeError as e:
                corrupted_files.append(file_path)
                print(f"  ❌ Archivo corrupto: {file_path} - {e}")
            except Exception as e:
                print(f"  ❌ Error leyendo {file_path}: {e}")
                corrupted_files.append(file_path)
        
        if corrupted_files:
            self.test_results['critical_issues'].append(f"Archivos corruptos: {', '.join(corrupted_files)}")
        
        if missing_files:
            self.test_results['warnings'].append(f"Archivos faltantes: {', '.join(missing_files)}")
        
        return len(corrupted_files) == 0
    
    def test_extension_manager(self) -> bool:
        """Probar funcionalidad del extension manager"""
        try:
            from core.extension_manager import extension_manager
            
            # Probar métodos básicos
            stats = extension_manager.get_extension_stats()
            print(f"  📊 Extensiones: {stats.get('total', 0)} total, {stats.get('available', 0)} disponibles")
            
            # Verificar que tenga extensiones
            if stats.get('total', 0) == 0:
                print("  ⚠️ No hay extensiones configuradas")
                return False
            
            # Probar obtener extensiones disponibles
            available = extension_manager.get_available_extensions()
            print(f"  🆓 Extensiones disponibles: {len(available)}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error probando extension_manager: {e}")
            return False
    
    def test_agent_manager(self) -> bool:
        """Probar funcionalidad del agent manager"""
        try:
            from core.agent_manager_clean import agent_manager
            
            # Probar obtener agentes
            agents = agent_manager.get_all_agents()
            print(f"  👥 Agentes: {len(agents)} total")
            
            # Verificar estructura de datos
            if not isinstance(agents, dict):
                print(f"  ❌ Formato de agentes inválido: {type(agents)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error probando agent_manager: {e}")
            return False
    
    def test_provider_manager(self) -> bool:
        """Probar funcionalidad del provider manager"""
        try:
            from core.provider_manager import provider_manager
            
            # Probar obtener proveedores
            providers = provider_manager.get_all_providers()
            print(f"  🏢 Proveedores: {len(providers)} total")
            
            # Verificar estructura de datos
            if not isinstance(providers, dict):
                print(f"  ❌ Formato de proveedores inválido: {type(providers)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error probando provider_manager: {e}")
            return False
    
    def test_asterisk_connection(self) -> bool:
        """Probar conexión con Asterisk"""
        try:
            # Verificar que Asterisk esté ejecutándose
            result = subprocess.run([
                "pgrep", "-f", "asterisk"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("  ⚠️ Asterisk no está ejecutándose")
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
                print("  ⚠️ No se pudo obtener versión de Asterisk")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ⚠️ Timeout conectando con Asterisk")
            return False
        except Exception as e:
            print(f"  ⚠️ Error probando Asterisk: {e}")
            return False
    
    def test_web_pages(self) -> bool:
        """Probar que las páginas web respondan"""
        pages = [
            ('/', 'Dashboard'),
            ('/agents', 'Agentes'),
            ('/providers', 'Proveedores'),
            ('/campaigns', 'Campañas')
        ]
        
        failed_pages = []
        
        for page_url, page_name in pages:
            try:
                response = requests.get(f"{self.base_url}{page_url}", timeout=10)
                if response.status_code == 200:
                    print(f"  ✅ Página {page_name} responde correctamente")
                else:
                    print(f"  ❌ Página {page_name} devolvió código {response.status_code}")
                    failed_pages.append(page_name)
            except Exception as e:
                print(f"  ❌ Error accediendo a {page_name}: {e}")
                failed_pages.append(page_name)
        
        return len(failed_pages) == 0
    
    def test_api_endpoints(self) -> bool:
        """Probar endpoints básicos de la API"""
        endpoints = [
            ('/api/agents', 'Agentes API'),
            ('/api/extensions/stats', 'Estadísticas de Extensiones'),
            ('/api/providers', 'Proveedores API')
        ]
        
        failed_endpoints = []
        
        for endpoint_url, endpoint_name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint_url}", timeout=5)
                if response.status_code == 200:
                    print(f"  ✅ {endpoint_name} responde correctamente")
                else:
                    print(f"  ❌ {endpoint_name} devolvió código {response.status_code}")
                    failed_endpoints.append(endpoint_name)
            except Exception as e:
                print(f"  ❌ Error en {endpoint_name}: {e}")
                failed_endpoints.append(endpoint_name)
        
        return len(failed_endpoints) == 0
    
    def test_new_methods_availability(self) -> bool:
        """Verificar que los nuevos métodos estén disponibles"""
        try:
            from core.extension_manager import extension_manager
            
            # Verificar métodos nuevos
            new_methods = [
                'get_all_extensions',
                'get_extension', 
                'update_extension',
                'regenerate_password',
                'release_extension',
                'execute_bulk_action'
            ]
            
            missing_methods = []
            
            for method_name in new_methods:
                if hasattr(extension_manager, method_name):
                    print(f"  ✅ Método disponible: {method_name}")
                else:
                    print(f"  ❌ Método faltante: {method_name}")
                    missing_methods.append(method_name)
            
            if missing_methods:
                print(f"  ⚠️ Métodos faltantes: {', '.join(missing_methods)}")
                print("  💡 Necesitas agregar los métodos nuevos a extension_manager.py")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error verificando métodos nuevos: {e}")
            return False
    
    def test_templates_exist(self) -> bool:
        """Verificar que los templates necesarios existan"""
        templates = [
            'web/templates/providers_enhanced.html',
            'web/templates/extensions_management.html'
        ]
        
        missing_templates = []
        
        for template_path in templates:
            full_path = self.project_root / template_path
            if full_path.exists():
                print(f"  ✅ Template existe: {template_path}")
            else:
                print(f"  ❌ Template faltante: {template_path}")
                missing_templates.append(template_path)
        
        if missing_templates:
            print(f"  💡 Templates faltantes: {', '.join(missing_templates)}")
            return False
        
        return True
    
    def test_scripts_exist(self) -> bool:
        """Verificar que los scripts de sincronización existan"""
        scripts = [
            'scripts/sync_extensions_softphones.py',
            'scripts/test_complete_integration.py'
        ]
        
        missing_scripts = []
        
        for script_path in scripts:
            full_path = self.project_root / script_path
            if full_path.exists():
                print(f"  ✅ Script existe: {script_path}")
            else:
                print(f"  ❌ Script faltante: {script_path}")
                missing_scripts.append(script_path)
        
        if missing_scripts:
            print(f"  💡 Scripts faltantes: {', '.join(missing_scripts)}")
            return False
        
        return True
    
    def determine_system_status(self):
        """Determinar el estado general del sistema"""
        critical_issues = len(self.test_results['critical_issues'])
        warnings = len(self.test_results['warnings'])
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run'] * 100) if self.test_results['tests_run'] > 0 else 0
        
        if critical_issues > 0:
            self.test_results['system_status'] = 'CRÍTICO'
        elif success_rate >= 90 and warnings <= 2:
            self.test_results['system_status'] = 'LISTO_PARA_MIGRACIÓN'
        elif success_rate >= 70:
            self.test_results['system_status'] = 'NECESITA_AJUSTES'
        else:
            self.test_results['system_status'] = 'NO_LISTO'
    
    def generate_report(self) -> str:
        """Generar reporte de pruebas"""
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run'] * 100) if self.test_results['tests_run'] > 0 else 0
        
        report_lines = [
            "=" * 80,
            "📊 REPORTE DE PRUEBAS DEL SISTEMA ACTUAL",
            "=" * 80,
            f"🕐 Fecha y hora: {self.test_results['timestamp']}",
            "",
            "📈 ESTADÍSTICAS GENERALES:",
            f"  • Pruebas ejecutadas: {self.test_results['tests_run']}",
            f"  • Pruebas exitosas: {self.test_results['tests_passed']}",
            f"  • Pruebas fallidas: {self.test_results['tests_failed']}",
            f"  • Tasa de éxito: {success_rate:.1f}%",
            f"  • Estado del sistema: {self.test_results['system_status']}",
            ""
        ]
        
        # Problemas críticos
        if self.test_results['critical_issues']:
            report_lines.extend([
                "🚨 PROBLEMAS CRÍTICOS (DEBEN RESOLVERSE ANTES DE MIGRAR):",
                ""
            ])
            for issue in self.test_results['critical_issues']:
                report_lines.append(f"  ❌ {issue}")
            report_lines.append("")
        
        # Advertencias
        if self.test_results['warnings']:
            report_lines.extend([
                "⚠️ ADVERTENCIAS:",
                ""
            ])
            for warning in self.test_results['warnings']:
                report_lines.append(f"  ⚠️ {warning}")
            report_lines.append("")
        
        # Recomendaciones
        report_lines.extend([
            "💡 RECOMENDACIONES:",
            ""
        ])
        
        if self.test_results['system_status'] == 'LISTO_PARA_MIGRACIÓN':
            report_lines.extend([
                "  ✅ El sistema está listo para migración",
                "  ✅ Puedes proceder con el script de migración",
                "  ✅ Todos los componentes críticos funcionan correctamente"
            ])
        elif self.test_results['system_status'] == 'NECESITA_AJUSTES':
            report_lines.extend([
                "  🔧 El sistema necesita algunos ajustes menores",
                "  🔧 Revisa las advertencias antes de migrar",
                "  🔧 La migración es posible pero con precaución"
            ])
        elif self.test_results['system_status'] == 'CRÍTICO':
            report_lines.extend([
                "  🚨 NO MIGRAR - Hay problemas críticos",
                "  🚨 Resuelve todos los problemas críticos primero",
                "  🚨 El sistema actual puede tener fallas graves"
            ])
        else:
            report_lines.extend([
                "  ❌ El sistema no está listo para migración",
                "  ❌ Demasiados problemas detectados",
                "  ❌ Revisa y corrige los problemas antes de continuar"
            ])
        
        report_lines.extend([
            "",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def save_report(self):
        """Guardar reporte en archivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.project_root / "data" / f"system_test_{timestamp}.json"
            
            # Asegurar que el directorio existe
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            print(f"📄 Reporte guardado en: {report_file}")
            
            # También guardar reporte en texto
            text_report_file = self.project_root / "data" / f"system_test_{timestamp}.txt"
            text_report = self.generate_report()
            
            with open(text_report_file, 'w') as f:
                f.write(text_report)
            
            print(f"📄 Reporte de texto guardado en: {text_report_file}")
            
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")

def main():
    """Función principal"""
    print("🚀 PRUEBAS DEL SISTEMA ACTUAL - VoIP Auto Dialer")
    print("=" * 70)
    print("Este script verifica que el sistema actual funcione correctamente")
    print("antes de proceder con la migración a la nueva versión.")
    print("=" * 70)
    
    tester = CurrentSystemTester()
    
    # Lista de pruebas críticas (deben pasar para migrar)
    critical_tests = [
        ("Verificar servidor web ejecutándose", tester.test_server_running),
        ("Probar salud de API", tester.test_api_health),
        ("Probar módulos core", tester.test_core_modules),
        ("Verificar archivos de datos", tester.test_data_files),
    ]
    
    # Lista de pruebas importantes (recomendadas pero no críticas)
    important_tests = [
        ("Probar Extension Manager", tester.test_extension_manager),
        ("Probar Agent Manager", tester.test_agent_manager),
        ("Probar Provider Manager", tester.test_provider_manager),
        ("Probar páginas web", tester.test_web_pages),
        ("Probar endpoints API", tester.test_api_endpoints),
    ]
    
    # Lista de pruebas de preparación (para migración)
    preparation_tests = [
        ("Verificar métodos nuevos disponibles", tester.test_new_methods_availability),
        ("Verificar templates existen", tester.test_templates_exist),
        ("Verificar scripts existen", tester.test_scripts_exist),
        ("Probar conexión con Asterisk", tester.test_asterisk_connection),
    ]
    
    print(f"📋 Se ejecutarán {len(critical_tests + important_tests + preparation_tests)} pruebas\n")
    
    # Ejecutar pruebas críticas
    print("🚨 PRUEBAS CRÍTICAS (deben pasar para migrar):")
    print("-" * 50)
    for test_name, test_func in critical_tests:
        tester.run_test(test_name, test_func, critical=True)
        print()
    
    # Ejecutar pruebas importantes
    print("⚠️ PRUEBAS IMPORTANTES:")
    print("-" * 50)
    for test_name, test_func in important_tests:
        tester.run_test(test_name, test_func, critical=False)
        print()
    
    # Ejecutar pruebas de preparación
    print("🔧 PRUEBAS DE PREPARACIÓN PARA MIGRACIÓN:")
    print("-" * 50)
    for test_name, test_func in preparation_tests:
        tester.run_test(test_name, test_func, critical=False)
        print()
    
    # Determinar estado del sistema
    tester.determine_system_status()
    
    # Generar y mostrar reporte
    report = tester.generate_report()
    print(report)
    
    # Guardar reporte
    tester.save_report()
    
    # Mensaje final
    if tester.test_results['system_status'] == 'LISTO_PARA_MIGRACIÓN':
        print("🎉 ¡SISTEMA LISTO PARA MIGRACIÓN!")
        print("💡 Puedes ejecutar el script de migración cuando estés listo.")
        return 0
    elif tester.test_results['system_status'] == 'NECESITA_AJUSTES':
        print("⚠️ SISTEMA NECESITA AJUSTES MENORES")
        print("💡 Revisa las advertencias pero puedes proceder con precaución.")
        return 0
    else:
        print("❌ SISTEMA NO LISTO PARA MIGRACIÓN")
        print("💡 Resuelve los problemas críticos antes de continuar.")
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
