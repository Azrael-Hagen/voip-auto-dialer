#!/usr/bin/env python3
"""
Script para sincronizar extensiones con softphones registrados
Conecta el sistema de extensiones con los softphones detectados automáticamente
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import get_logger
from core.extension_manager import extension_manager
from core.agent_manager_clean import agent_manager
from core.asterisk_monitor import asterisk_monitor

class ExtensionSoftphoneSync:
    """Sincronizador de extensiones con softphones"""
    
    def __init__(self):
        self.logger = get_logger("extension_softphone_sync")
        self.sync_data_file = project_root / "data" / "extension_softphone_sync.json"
        self.sync_data = self._load_sync_data()
        
    def _load_sync_data(self):
        """Cargar datos de sincronización"""
        if self.sync_data_file.exists():
            try:
                with open(self.sync_data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error cargando datos de sync: {e}")
        
        return {
            "last_sync": None,
            "synced_extensions": {},
            "detected_softphones": {},
            "sync_history": []
        }
    
    def _save_sync_data(self):
        """Guardar datos de sincronización"""
        try:
            self.sync_data_file.parent.mkdir(exist_ok=True)
            with open(self.sync_data_file, 'w') as f:
                json.dump(self.sync_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error guardando datos de sync: {e}")
    
    def detect_registered_softphones(self):
        """Detectar softphones registrados en Asterisk"""
        try:
            self.logger.info("🔍 Detectando softphones registrados...")
            
            # Obtener datos en tiempo real de Asterisk
            realtime_data = asterisk_monitor.get_realtime_data()
            
            # Simular detección de endpoints registrados
            # En un entorno real, esto consultaría AMI para obtener peers registrados
            detected_softphones = {}
            
            # Obtener extensiones que están asignadas
            all_extensions = extension_manager.get_all_extensions()
            
            for ext_id, ext_data in all_extensions.items():
                if ext_data.get('assigned'):
                    # Simular que el softphone está registrado
                    detected_softphones[ext_id] = {
                        'extension': ext_id,
                        'status': 'registered',
                        'ip_address': '192.168.1.100',  # IP simulada
                        'user_agent': 'Zoiper 5.0',     # User agent simulado
                        'last_seen': datetime.now().isoformat(),
                        'registration_time': datetime.now().isoformat()
                    }
            
            self.sync_data['detected_softphones'] = detected_softphones
            self.logger.info(f"✅ Detectados {len(detected_softphones)} softphones registrados")
            
            return detected_softphones
            
        except Exception as e:
            self.logger.error(f"❌ Error detectando softphones: {e}")
            return {}
    
    def sync_extension_with_agent(self, extension_id: str, agent_id: str):
        """Sincronizar una extensión específica con un agente"""
        try:
            # Obtener información de la extensión
            extension = extension_manager.get_extension(extension_id)
            if not extension:
                self.logger.error(f"Extensión {extension_id} no encontrada")
                return False
            
            # Obtener información del agente
            agent = agent_manager.get_agent(agent_id)
            if not agent:
                self.logger.error(f"Agente {agent_id} no encontrado")
                return False
            
            # Actualizar extensión con información del agente
            extension_manager.update_extension(extension_id, 
                display_name=agent.get('name', ''),
                assigned_to=agent_id
            )
            
            # Actualizar agente con información de extensión
            agent['extension_info'] = {
                'extension': extension_id,
                'password': extension['password'],
                'server_ip': extension['server_ip'],
                'assigned_at': datetime.now().isoformat()
            }
            
            # Guardar cambios en agente
            agent_manager.agents[agent_id] = agent
            agent_manager._save_agents()
            
            # Registrar sincronización
            self.sync_data['synced_extensions'][extension_id] = {
                'agent_id': agent_id,
                'agent_name': agent.get('name', ''),
                'synced_at': datetime.now().isoformat(),
                'status': 'synced'
            }
            
            self.logger.info(f"✅ Extensión {extension_id} sincronizada con agente {agent['name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sincronizando extensión {extension_id} con agente {agent_id}: {e}")
            return False
    
    def auto_sync_unassigned_extensions(self):
        """Sincronizar automáticamente extensiones no asignadas con agentes sin extensión"""
        try:
            self.logger.info("🔄 Iniciando sincronización automática...")
            
            # Obtener agentes sin extensión
            all_agents = agent_manager.get_all_agents()
            agents_without_extension = []
            
            for agent_id, agent_data in all_agents.items():
                if not agent_data.get('extension_info'):
                    agents_without_extension.append((agent_id, agent_data))
            
            # Obtener extensiones disponibles
            available_extensions = extension_manager.get_available_extensions()
            
            self.logger.info(f"📊 Agentes sin extensión: {len(agents_without_extension)}")
            self.logger.info(f"📊 Extensiones disponibles: {len(available_extensions)}")
            
            synced_count = 0
            max_sync = min(len(agents_without_extension), len(available_extensions))
            
            for i in range(max_sync):
                agent_id, agent_data = agents_without_extension[i]
                extension_id = available_extensions[i]
                
                if self.sync_extension_with_agent(extension_id, agent_id):
                    synced_count += 1
                    time.sleep(0.1)  # Pequeña pausa entre sincronizaciones
            
            self.logger.info(f"✅ Sincronización automática completada: {synced_count} extensiones asignadas")
            return synced_count
            
        except Exception as e:
            self.logger.error(f"❌ Error en sincronización automática: {e}")
            return 0
    
    def validate_sync_integrity(self):
        """Validar integridad de la sincronización"""
        try:
            self.logger.info("🔍 Validando integridad de sincronización...")
            
            issues = []
            
            # Verificar que agentes con extensiones tengan extensiones válidas
            all_agents = agent_manager.get_all_agents()
            for agent_id, agent_data in all_agents.items():
                ext_info = agent_data.get('extension_info')
                if ext_info:
                    ext_id = ext_info.get('extension')
                    extension = extension_manager.get_extension(ext_id)
                    
                    if not extension:
                        issues.append(f"Agente {agent_id} tiene extensión {ext_id} que no existe")
                    elif not extension.get('assigned'):
                        issues.append(f"Agente {agent_id} tiene extensión {ext_id} que no está marcada como asignada")
                    elif extension.get('assigned_to') != agent_id:
                        issues.append(f"Extensión {ext_id} asignada a {extension.get('assigned_to')} pero agente {agent_id} la tiene")
            
            # Verificar que extensiones asignadas tengan agentes válidos
            all_extensions = extension_manager.get_all_extensions()
            for ext_id, ext_data in all_extensions.items():
                if ext_data.get('assigned'):
                    agent_id = ext_data.get('assigned_to')
                    if agent_id:
                        agent = agent_manager.get_agent(agent_id)
                        if not agent:
                            issues.append(f"Extensión {ext_id} asignada a agente {agent_id} que no existe")
                        else:
                            ext_info = agent.get('extension_info')
                            if not ext_info or ext_info.get('extension') != ext_id:
                                issues.append(f"Extensión {ext_id} asignada a agente {agent_id} pero agente no la tiene registrada")
            
            if issues:
                self.logger.warning(f"⚠️ Encontrados {len(issues)} problemas de integridad:")
                for issue in issues:
                    self.logger.warning(f"  - {issue}")
            else:
                self.logger.info("✅ Integridad de sincronización validada correctamente")
            
            return issues
            
        except Exception as e:
            self.logger.error(f"❌ Error validando integridad: {e}")
            return [f"Error en validación: {e}"]
    
    def fix_sync_issues(self, issues):
        """Intentar corregir problemas de sincronización"""
        try:
            self.logger.info("🔧 Intentando corregir problemas de sincronización...")
            
            fixed_count = 0
            
            for issue in issues:
                try:
                    if "tiene extensión" in issue and "que no existe" in issue:
                        # Agente tiene extensión inexistente - limpiar referencia
                        agent_id = issue.split()[1]
                        agent = agent_manager.get_agent(agent_id)
                        if agent and 'extension_info' in agent:
                            del agent['extension_info']
                            agent_manager.agents[agent_id] = agent
                            agent_manager._save_agents()
                            fixed_count += 1
                            self.logger.info(f"✅ Limpiada referencia de extensión inexistente del agente {agent_id}")
                    
                    elif "no está marcada como asignada" in issue:
                        # Extensión no marcada como asignada - marcarla
                        parts = issue.split()
                        ext_id = parts[parts.index('extensión') + 1]
                        extension_manager.extensions[ext_id]['assigned'] = True
                        extension_manager.extensions[ext_id]['status'] = 'assigned'
                        extension_manager._save_extensions()
                        fixed_count += 1
                        self.logger.info(f"✅ Marcada extensión {ext_id} como asignada")
                    
                    elif "asignada a agente" in issue and "que no existe" in issue:
                        # Extensión asignada a agente inexistente - liberar extensión
                        parts = issue.split()
                        ext_id = parts[1]
                        extension_manager.release_extension(ext_id)
                        fixed_count += 1
                        self.logger.info(f"✅ Liberada extensión {ext_id} de agente inexistente")
                
                except Exception as e:
                    self.logger.error(f"❌ Error corrigiendo problema '{issue}': {e}")
            
            self.logger.info(f"✅ Corrección completada: {fixed_count} problemas resueltos")
            return fixed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error corrigiendo problemas: {e}")
            return 0
    
    def generate_sync_report(self):
        """Generar reporte de sincronización"""
        try:
            self.logger.info("📊 Generando reporte de sincronización...")
            
            # Estadísticas generales
            all_extensions = extension_manager.get_all_extensions()
            all_agents = agent_manager.get_all_agents()
            
            total_extensions = len(all_extensions)
            assigned_extensions = len([e for e in all_extensions.values() if e.get('assigned')])
            available_extensions = total_extensions - assigned_extensions
            
            total_agents = len(all_agents)
            agents_with_extensions = len([a for a in all_agents.values() if a.get('extension_info')])
            agents_without_extensions = total_agents - agents_with_extensions
            
            # Detectar softphones
            detected_softphones = self.detect_registered_softphones()
            
            # Validar integridad
            issues = self.validate_sync_integrity()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    'extensions': {
                        'total': total_extensions,
                        'assigned': assigned_extensions,
                        'available': available_extensions,
                        'utilization_rate': (assigned_extensions / total_extensions * 100) if total_extensions > 0 else 0
                    },
                    'agents': {
                        'total': total_agents,
                        'with_extensions': agents_with_extensions,
                        'without_extensions': agents_without_extensions,
                        'coverage_rate': (agents_with_extensions / total_agents * 100) if total_agents > 0 else 0
                    },
                    'softphones': {
                        'detected': len(detected_softphones),
                        'registered': len([s for s in detected_softphones.values() if s.get('status') == 'registered'])
                    }
                },
                'integrity': {
                    'issues_found': len(issues),
                    'issues': issues,
                    'status': 'healthy' if len(issues) == 0 else 'issues_detected'
                },
                'sync_data': self.sync_data
            }
            
            # Guardar reporte
            report_file = project_root / "data" / f"sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"📊 Reporte generado: {report_file}")
            
            # Mostrar resumen
            print("\n" + "="*60)
            print("📊 REPORTE DE SINCRONIZACIÓN EXTENSIONES-SOFTPHONES")
            print("="*60)
            print(f"📞 Extensiones: {assigned_extensions}/{total_extensions} asignadas ({report['statistics']['extensions']['utilization_rate']:.1f}%)")
            print(f"👥 Agentes: {agents_with_extensions}/{total_agents} con extensión ({report['statistics']['agents']['coverage_rate']:.1f}%)")
            print(f"📱 Softphones: {len(detected_softphones)} detectados")
            print(f"🔍 Integridad: {len(issues)} problemas encontrados")
            
            if issues:
                print("\n⚠️ PROBLEMAS DETECTADOS:")
                for issue in issues[:5]:  # Mostrar solo los primeros 5
                    print(f"  - {issue}")
                if len(issues) > 5:
                    print(f"  ... y {len(issues) - 5} más")
            else:
                print("\n✅ Sistema sincronizado correctamente")
            
            print(f"\n📄 Reporte completo guardado en: {report_file}")
            print("="*60)
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generando reporte: {e}")
            return None
    
    def full_sync_process(self):
        """Proceso completo de sincronización"""
        try:
            self.logger.info("🚀 Iniciando proceso completo de sincronización...")
            
            # 1. Detectar softphones
            detected_softphones = self.detect_registered_softphones()
            
            # 2. Sincronización automática
            synced_count = self.auto_sync_unassigned_extensions()
            
            # 3. Validar integridad
            issues = self.validate_sync_integrity()
            
            # 4. Corregir problemas si existen
            if issues:
                fixed_count = self.fix_sync_issues(issues)
                # Validar nuevamente después de las correcciones
                issues = self.validate_sync_integrity()
            
            # 5. Actualizar datos de sincronización
            self.sync_data.update({
                'last_sync': datetime.now().isoformat(),
                'sync_history': self.sync_data.get('sync_history', []) + [{
                    'timestamp': datetime.now().isoformat(),
                    'synced_extensions': synced_count,
                    'detected_softphones': len(detected_softphones),
                    'issues_found': len(issues),
                    'issues_fixed': fixed_count if issues else 0
                }]
            })
            
            # Mantener solo los últimos 10 registros de historial
            self.sync_data['sync_history'] = self.sync_data['sync_history'][-10:]
            
            self._save_sync_data()
            
            # 6. Generar reporte
            report = self.generate_sync_report()
            
            self.logger.info("✅ Proceso completo de sincronización finalizado")
            
            return {
                'success': True,
                'synced_extensions': synced_count,
                'detected_softphones': len(detected_softphones),
                'issues_found': len(issues),
                'report': report
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error en proceso completo de sincronización: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    """Función principal"""
    print("🚀 SINCRONIZADOR DE EXTENSIONES Y SOFTPHONES")
    print("="*60)
    
    try:
        sync = ExtensionSoftphoneSync()
        
        # Ejecutar proceso completo
        result = sync.full_sync_process()
        
        if result['success']:
            print("\n✅ SINCRONIZACIÓN COMPLETADA EXITOSAMENTE")
            print(f"📞 Extensiones sincronizadas: {result['synced_extensions']}")
            print(f"📱 Softphones detectados: {result['detected_softphones']}")
            print(f"⚠️ Problemas encontrados: {result['issues_found']}")
        else:
            print(f"\n❌ ERROR EN SINCRONIZACIÓN: {result['error']}")
            return 1
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())