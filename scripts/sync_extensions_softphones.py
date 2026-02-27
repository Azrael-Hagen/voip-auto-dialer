#!/usr/bin/env python3
"""
Script de sincronización entre extensiones y softphones
Detecta softphones conectados y los sincroniza con las extensiones asignadas
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import get_logger
from core.extension_manager import extension_manager
from core.agent_manager_clean import agent_manager

# Logger
logger = get_logger("sync_extensions_softphones")

class ExtensionSoftphoneSync:
    """Clase para sincronizar extensiones con softphones"""
    
    def __init__(self):
        self.project_root = project_root
        self.data_dir = self.project_root / "data"
        self.sync_data_file = self.data_dir / "extension_softphone_sync.json"
        self.sync_data = self._load_sync_data()
        
    def _load_sync_data(self) -> Dict[str, Any]:
        """Cargar datos de sincronización previos"""
        try:
            if self.sync_data_file.exists():
                with open(self.sync_data_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "last_sync": None,
                    "synced_extensions": {},
                    "detected_softphones": {},
                    "sync_history": []
                }
        except Exception as e:
            logger.error(f"Error cargando datos de sincronización: {e}")
            return {
                "last_sync": None,
                "synced_extensions": {},
                "detected_softphones": {},
                "sync_history": []
            }
    
    def _save_sync_data(self):
        """Guardar datos de sincronización"""
        try:
            self.data_dir.mkdir(exist_ok=True)
            with open(self.sync_data_file, 'w') as f:
                json.dump(self.sync_data, f, indent=2)
            logger.info(f"Datos de sincronización guardados en {self.sync_data_file}")
        except Exception as e:
            logger.error(f"Error guardando datos de sincronización: {e}")
    
    def detect_softphones(self) -> Dict[str, Dict[str, Any]]:
        """Detectar softphones conectados usando comandos de Asterisk"""
        detected_softphones = {}
        
        try:
            # Usar AMI o comandos CLI de Asterisk para detectar endpoints
            logger.info("🔍 Detectando softphones conectados...")
            
            # Comando para obtener endpoints PJSIP
            try:
                result = subprocess.run([
                    "sudo", "asterisk", "-rx", "pjsip show endpoints"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    endpoints = self._parse_pjsip_endpoints(result.stdout)
                    detected_softphones.update(endpoints)
                    logger.info(f"✅ Detectados {len(endpoints)} endpoints PJSIP")
                else:
                    logger.warning("⚠️ No se pudieron obtener endpoints PJSIP")
                    
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Timeout obteniendo endpoints PJSIP")
            except Exception as e:
                logger.error(f"❌ Error obteniendo endpoints PJSIP: {e}")
            
            # Comando para obtener peers SIP (si está configurado)
            try:
                result = subprocess.run([
                    "sudo", "asterisk", "-rx", "sip show peers"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    peers = self._parse_sip_peers(result.stdout)
                    detected_softphones.update(peers)
                    logger.info(f"✅ Detectados {len(peers)} peers SIP")
                else:
                    logger.info("ℹ️ No hay peers SIP configurados")
                    
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Timeout obteniendo peers SIP")
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo peers SIP: {e}")
            
            # Actualizar datos de sincronización
            self.sync_data["detected_softphones"] = detected_softphones
            self.sync_data["last_detection"] = datetime.now().isoformat()
            
            logger.info(f"🎯 Total de softphones detectados: {len(detected_softphones)}")
            
        except Exception as e:
            logger.error(f"❌ Error detectando softphones: {e}")
        
        return detected_softphones
    
    def _parse_pjsip_endpoints(self, output: str) -> Dict[str, Dict[str, Any]]:
        """Parsear salida de 'pjsip show endpoints'"""
        endpoints = {}
        
        try:
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('=') or 'Endpoint:' in line:
                    continue
                
                # Formato típico: "1001/1001    Not in use    0 of inf"
                parts = line.split()
                if len(parts) >= 3:
                    endpoint_info = parts[0]
                    status = ' '.join(parts[1:-2]) if len(parts) > 3 else parts[1]
                    
                    if '/' in endpoint_info:
                        endpoint_id = endpoint_info.split('/')[0]
                        
                        # Verificar si es una extensión válida (número)
                        if endpoint_id.isdigit():
                            endpoints[endpoint_id] = {
                                'type': 'pjsip',
                                'endpoint_id': endpoint_id,
                                'status': status,
                                'detected_at': datetime.now().isoformat(),
                                'connection_info': endpoint_info
                            }
                            
        except Exception as e:
            logger.error(f"Error parseando endpoints PJSIP: {e}")
        
        return endpoints
    
    def _parse_sip_peers(self, output: str) -> Dict[str, Dict[str, Any]]:
        """Parsear salida de 'sip show peers'"""
        peers = {}
        
        try:
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('Name/') or line.startswith('='):
                    continue
                
                # Formato típico: "1001/1001    D  A  5060     OK (1 ms)"
                parts = line.split()
                if len(parts) >= 4:
                    peer_info = parts[0]
                    
                    if '/' in peer_info:
                        peer_id = peer_info.split('/')[0]
                        
                        # Verificar si es una extensión válida (número)
                        if peer_id.isdigit():
                            status = 'OK' if 'OK' in line else 'UNREACHABLE'
                            
                            peers[peer_id] = {
                                'type': 'sip',
                                'peer_id': peer_id,
                                'status': status,
                                'detected_at': datetime.now().isoformat(),
                                'connection_info': peer_info
                            }
                            
        except Exception as e:
            logger.error(f"Error parseando peers SIP: {e}")
        
        return peers
    
    def sync_extensions_with_softphones(self) -> Dict[str, Any]:
        """Sincronizar extensiones con softphones detectados"""
        sync_report = {
            'timestamp': datetime.now().isoformat(),
            'extensions_processed': 0,
            'softphones_detected': 0,
            'matches_found': 0,
            'issues_detected': [],
            'actions_taken': [],
            'summary': {}
        }
        
        try:
            logger.info("🔄 Iniciando sincronización extensiones-softphones...")
            
            # Obtener todas las extensiones
            all_extensions = extension_manager.get_all_extensions()
            sync_report['extensions_processed'] = len(all_extensions)
            
            # Detectar softphones
            detected_softphones = self.detect_softphones()
            sync_report['softphones_detected'] = len(detected_softphones)
            
            # Obtener todos los agentes
            all_agents = agent_manager.get_all_agents()
            
            # Procesar cada extensión
            for ext_id, ext_data in all_extensions.items():
                try:
                    self._process_extension_sync(
                        ext_id, ext_data, detected_softphones, all_agents, sync_report
                    )
                except Exception as e:
                    error_msg = f"Error procesando extensión {ext_id}: {e}"
                    logger.error(error_msg)
                    sync_report['issues_detected'].append(error_msg)
            
            # Detectar softphones sin extensión asignada
            self._detect_orphaned_softphones(detected_softphones, all_extensions, sync_report)
            
            # Generar resumen
            sync_report['summary'] = {
                'total_extensions': len(all_extensions),
                'total_softphones': len(detected_softphones),
                'matched_pairs': sync_report['matches_found'],
                'issues_count': len(sync_report['issues_detected']),
                'actions_count': len(sync_report['actions_taken'])
            }
            
            # Actualizar datos de sincronización
            self.sync_data["last_sync"] = sync_report['timestamp']
            self.sync_data["synced_extensions"] = {
                ext_id: {
                    'extension_data': ext_data,
                    'softphone_detected': ext_id in detected_softphones,
                    'sync_status': 'synced' if ext_id in detected_softphones else 'no_softphone'
                }
                for ext_id, ext_data in all_extensions.items()
            }
            
            # Agregar a historial
            self.sync_data["sync_history"].append({
                'timestamp': sync_report['timestamp'],
                'summary': sync_report['summary']
            })
            
            # Mantener solo los últimos 10 registros de historial
            if len(self.sync_data["sync_history"]) > 10:
                self.sync_data["sync_history"] = self.sync_data["sync_history"][-10:]
            
            self._save_sync_data()
            
            logger.info("✅ Sincronización completada exitosamente")
            
        except Exception as e:
            error_msg = f"Error en sincronización: {e}"
            logger.error(error_msg)
            sync_report['issues_detected'].append(error_msg)
        
        return sync_report
    
    def _process_extension_sync(self, ext_id: str, ext_data: Dict[str, Any], 
                               detected_softphones: Dict[str, Dict[str, Any]], 
                               all_agents: Dict[str, Dict[str, Any]], 
                               sync_report: Dict[str, Any]):
        """Procesar sincronización de una extensión específica"""
        
        # Verificar si hay softphone detectado para esta extensión
        if ext_id in detected_softphones:
            sync_report['matches_found'] += 1
            softphone_info = detected_softphones[ext_id]
            
            action_msg = f"✅ Extensión {ext_id} sincronizada con softphone {softphone_info['type']}"
            logger.info(action_msg)
            sync_report['actions_taken'].append(action_msg)
            
            # Verificar si la extensión está asignada a un agente
            if ext_data.get('assigned') and ext_data.get('assigned_to'):
                agent_id = ext_data['assigned_to']
                if agent_id in all_agents:
                    agent_name = all_agents[agent_id].get('name', 'Desconocido')
                    action_msg = f"📱 Softphone de extensión {ext_id} conectado para agente {agent_name}"
                    logger.info(action_msg)
                    sync_report['actions_taken'].append(action_msg)
                else:
                    issue_msg = f"⚠️ Extensión {ext_id} asignada a agente inexistente: {agent_id}"
                    logger.warning(issue_msg)
                    sync_report['issues_detected'].append(issue_msg)
            else:
                # Extensión disponible con softphone conectado
                action_msg = f"🔄 Extensión {ext_id} disponible pero con softphone conectado"
                logger.info(action_msg)
                sync_report['actions_taken'].append(action_msg)
        else:
            # No hay softphone detectado para esta extensión
            if ext_data.get('assigned'):
                issue_msg = f"⚠️ Extensión {ext_id} asignada pero sin softphone detectado"
                logger.warning(issue_msg)
                sync_report['issues_detected'].append(issue_msg)
    
    def _detect_orphaned_softphones(self, detected_softphones: Dict[str, Dict[str, Any]], 
                                   all_extensions: Dict[str, Dict[str, Any]], 
                                   sync_report: Dict[str, Any]):
        """Detectar softphones conectados sin extensión correspondiente"""
        
        for softphone_id, softphone_info in detected_softphones.items():
            if softphone_id not in all_extensions:
                issue_msg = f"🔍 Softphone detectado sin extensión correspondiente: {softphone_id}"
                logger.warning(issue_msg)
                sync_report['issues_detected'].append(issue_msg)
    
    def generate_sync_report(self, sync_result: Dict[str, Any]) -> str:
        """Generar reporte detallado de sincronización"""
        
        report_lines = [
            "=" * 80,
            "📊 REPORTE DE SINCRONIZACIÓN EXTENSIONES-SOFTPHONES",
            "=" * 80,
            f"🕐 Fecha y hora: {sync_result['timestamp']}",
            "",
            "📈 ESTADÍSTICAS GENERALES:",
            f"  • Extensiones procesadas: {sync_result['extensions_processed']}",
            f"  • Softphones detectados: {sync_result['softphones_detected']}",
            f"  • Coincidencias encontradas: {sync_result['matches_found']}",
            f"  • Problemas detectados: {len(sync_result['issues_detected'])}",
            f"  • Acciones realizadas: {len(sync_result['actions_taken'])}",
            ""
        ]
        
        if sync_result['actions_taken']:
            report_lines.extend([
                "✅ ACCIONES REALIZADAS:",
                *[f"  • {action}" for action in sync_result['actions_taken']],
                ""
            ])
        
        if sync_result['issues_detected']:
            report_lines.extend([
                "⚠️ PROBLEMAS DETECTADOS:",
                *[f"  • {issue}" for issue in sync_result['issues_detected']],
                ""
            ])
        
        report_lines.extend([
            "📋 RESUMEN:",
            f"  • Tasa de sincronización: {sync_result['matches_found']}/{sync_result['extensions_processed']} extensiones",
            f"  • Softphones huérfanos: {sync_result['softphones_detected'] - sync_result['matches_found']}",
            "",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def save_report_to_file(self, sync_result: Dict[str, Any]):
        """Guardar reporte en archivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.data_dir / f"sync_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(sync_result, f, indent=2)
            
            logger.info(f"📄 Reporte guardado en: {report_file}")
            
            # También guardar reporte en texto
            text_report_file = self.data_dir / f"sync_report_{timestamp}.txt"
            text_report = self.generate_sync_report(sync_result)
            
            with open(text_report_file, 'w') as f:
                f.write(text_report)
            
            logger.info(f"📄 Reporte de texto guardado en: {text_report_file}")
            
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")

def main():
    """Función principal"""
    print("🚀 SINCRONIZACIÓN EXTENSIONES-SOFTPHONES")
    print("=" * 60)
    
    try:
        # Crear instancia del sincronizador
        sync_manager = ExtensionSoftphoneSync()
        
        # Ejecutar sincronización
        print("🔄 Ejecutando sincronización...")
        sync_result = sync_manager.sync_extensions_with_softphones()
        
        # Generar y mostrar reporte
        report = sync_manager.generate_sync_report(sync_result)
        print(report)
        
        # Guardar reporte en archivo
        sync_manager.save_report_to_file(sync_result)
        
        print("✅ SINCRONIZACIÓN COMPLETADA")
        print("💡 Revisa los archivos de reporte en la carpeta 'data/'")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Sincronización cancelada por el usuario")
        return 1
    except Exception as e:
        print(f"❌ Error en sincronización: {e}")
        logger.error(f"Error crítico en sincronización: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)