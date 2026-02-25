"""
Monitor de Softphones para VoIP Auto Dialer
Detecta registros de extensiones y crea agentes automáticamente
"""
import json
import uuid
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from core.logging_config import get_logger
from core.agent_manager_clean import agent_manager
from core.extension_manager import extension_manager

class SoftphoneMonitor:
    def __init__(self):
        self.logger = get_logger("softphone_monitor")
        self.data_dir = Path(__file__).parent.parent / "data"
        self.registered_file = self.data_dir / "registered_softphones.json"
        self.registered_softphones = {}
        
        # Crear directorio si no existe
        self.data_dir.mkdir(exist_ok=True)
        
        # Cargar softphones registrados
        self._load_registered_softphones()
        
        self.logger.info("Softphone Monitor inicializado")

    def _load_registered_softphones(self):
        """Cargar softphones registrados desde archivo"""
        try:
            if self.registered_file.exists():
                with open(self.registered_file, 'r', encoding='utf-8') as f:
                    self.registered_softphones = json.load(f)
                self.logger.info(f"Softphones registrados cargados: {len(self.registered_softphones)}")
            else:
                self.registered_softphones = {}
                self._save_registered_softphones()
        except Exception as e:
            self.logger.error(f"Error cargando softphones registrados: {e}")
            self.registered_softphones = {}

    def _save_registered_softphones(self):
        """Guardar softphones registrados en archivo"""
        try:
            with open(self.registered_file, 'w', encoding='utf-8') as f:
                json.dump(self.registered_softphones, f, indent=2, ensure_ascii=False)
            self.logger.debug("Softphones registrados guardados")
        except Exception as e:
            self.logger.error(f"Error guardando softphones registrados: {e}")

    def check_asterisk_registrations(self) -> List[Dict[str, Any]]:
        """Verificar registros activos en Asterisk"""
        try:
            # Ejecutar comando para obtener endpoints registrados
            result = subprocess.run(
                ['sudo', 'asterisk', '-rx', 'pjsip show endpoints'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error ejecutando comando Asterisk: {result.stderr}")
                return []
            
            # Parsear salida para encontrar extensiones registradas
            registered_extensions = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                # Buscar líneas que contengan información de endpoints
                if re.match(r'^\s*\d{4}\s+', line):  # Líneas que empiecen con número de extensión
                    parts = line.split()
                    if len(parts) >= 2:
                        extension = parts[0].strip()
                        status = parts[1].strip() if len(parts) > 1 else 'Unknown'
                        
                        # Solo considerar extensiones "Available" o "In use"
                        if status in ['Unavailable', 'Available'] and extension.isdigit():
                            registered_extensions.append({
                                'extension': extension,
                                'status': status,
                                'timestamp': datetime.now().isoformat()
                            })
            
            return registered_extensions
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout ejecutando comando Asterisk")
            return []
        except Exception as e:
            self.logger.error(f"Error verificando registros de Asterisk: {e}")
            return []

    def get_extension_details(self, extension: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles adicionales de una extensión desde Asterisk"""
        try:
            result = subprocess.run(
                ['sudo', 'asterisk', '-rx', f'pjsip show endpoint {extension}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            # Parsear información del endpoint
            details = {
                'extension': extension,
                'contact_info': None,
                'user_agent': None,
                'ip_address': None
            }
            
            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                if 'Contact:' in line:
                    # Extraer información de contacto
                    contact_match = re.search(r'sip:(\d+)@([\d\.]+):(\d+)', line)
                    if contact_match:
                        details['contact_info'] = line
                        details['ip_address'] = contact_match.group(2)
                elif 'User-Agent:' in line or 'UserAgent:' in line:
                    details['user_agent'] = line.split(':', 1)[1].strip()
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error obteniendo detalles de extensión {extension}: {e}")
            return None

    def create_auto_agent(self, extension: str, extension_details: Dict[str, Any]) -> Optional[str]:
        """Crear agente automáticamente para una extensión registrada"""
        try:
            # Generar información del agente
            agent_name = f"Auto Agent {extension}"
            agent_email = f"agent{extension}@voip-autodialer.local"
            agent_phone = f"+1-EXT-{extension}"
            
            # Detectar tipo de softphone desde User-Agent
            user_agent = extension_details.get('user_agent', '')
            softphone_type = 'Unknown'
            
            if 'zoiper' in user_agent.lower():
                softphone_type = 'Zoiper'
                agent_name = f"Zoiper Agent {extension}"
            elif 'portsip' in user_agent.lower():
                softphone_type = 'PortSIP'
                agent_name = f"PortSIP Agent {extension}"
            elif 'linphone' in user_agent.lower():
                softphone_type = 'Linphone'
                agent_name = f"Linphone Agent {extension}"
            elif 'x-lite' in user_agent.lower() or 'xlite' in user_agent.lower():
                softphone_type = 'X-Lite'
                agent_name = f"X-Lite Agent {extension}"
            
            # Crear agente
            new_agent = agent_manager.create_agent(
                name=agent_name,
                email=agent_email,
                phone=agent_phone
            )
            
            if not new_agent:
                self.logger.error(f"No se pudo crear agente para extensión {extension}")
                return None
            
            agent_id = new_agent['id']
            
            # Asignar la extensión específica al agente
            success = self._assign_specific_extension(agent_id, extension)
            
            if success:
                # Registrar el softphone
                self.registered_softphones[extension] = {
                    'extension': extension,
                    'agent_id': agent_id,
                    'agent_name': agent_name,
                    'softphone_type': softphone_type,
                    'ip_address': extension_details.get('ip_address'),
                    'user_agent': user_agent,
                    'registered_at': datetime.now().isoformat(),
                    'auto_created': True,
                    'status': 'active'
                }
                
                self._save_registered_softphones()
                
                self.logger.info(f"Agente auto-creado: {agent_name} ({agent_id}) para extensión {extension}")
                return agent_id
            else:
                # Si no se pudo asignar la extensión, eliminar el agente
                agent_manager.delete_agent(agent_id)
                self.logger.error(f"No se pudo asignar extensión {extension} al agente {agent_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creando agente automático para extensión {extension}: {e}")
            return None

    def _assign_specific_extension(self, agent_id: str, extension: str) -> bool:
        """Asignar una extensión específica a un agente"""
        try:
            # Obtener información de la extensión
            extensions = extension_manager.extensions
            
            if extension not in extensions:
                self.logger.error(f"Extensión {extension} no existe en el sistema")
                return False
            
            extension_data = extensions[extension]
            
            # Verificar si la extensión ya está asignada
            if extension_data.get('assigned', False):
                self.logger.warning(f"Extensión {extension} ya está asignada")
                return False
            
            # Asignar extensión al agente
            result = extension_manager.assign_extension(extension, agent_id)
            
            if result:
                # Actualizar información del agente
                agent = agent_manager.get_agent(agent_id)
                if agent:
                    agent['extension_info'] = {
                        'extension': extension,
                        'password': extension_data.get('password', ''),
                        'status': 'assigned',
                        'assigned_at': datetime.now().isoformat()
                    }
                    agent_manager.agents[agent_id] = agent
                    agent_manager._save_agents()
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error asignando extensión {extension} a agente {agent_id}: {e}")
            return False

    def scan_and_auto_register(self) -> Dict[str, Any]:
        """Escanear registros de Asterisk y crear agentes automáticamente"""
        try:
            self.logger.info("Iniciando escaneo de registros automáticos...")
            
            # Obtener extensiones registradas en Asterisk
            registered_extensions = self.check_asterisk_registrations()
            
            results = {
                'scanned_extensions': len(registered_extensions),
                'new_agents_created': 0,
                'existing_agents': 0,
                'errors': 0,
                'details': []
            }
            
            for ext_info in registered_extensions:
                extension = ext_info['extension']
                
                try:
                    # Verificar si ya existe un agente para esta extensión
                    if extension in self.registered_softphones:
                        results['existing_agents'] += 1
                        results['details'].append({
                            'extension': extension,
                            'status': 'existing',
                            'agent_id': self.registered_softphones[extension]['agent_id']
                        })
                        continue
                    
                    # Obtener detalles adicionales de la extensión
                    extension_details = self.get_extension_details(extension)
                    if not extension_details:
                        extension_details = {'extension': extension}
                    
                    # Crear agente automáticamente
                    agent_id = self.create_auto_agent(extension, extension_details)
                    
                    if agent_id:
                        results['new_agents_created'] += 1
                        results['details'].append({
                            'extension': extension,
                            'status': 'created',
                            'agent_id': agent_id,
                            'softphone_type': self.registered_softphones[extension]['softphone_type']
                        })
                    else:
                        results['errors'] += 1
                        results['details'].append({
                            'extension': extension,
                            'status': 'error',
                            'message': 'No se pudo crear agente'
                        })
                        
                except Exception as e:
                    results['errors'] += 1
                    results['details'].append({
                        'extension': extension,
                        'status': 'error',
                        'message': str(e)
                    })
                    self.logger.error(f"Error procesando extensión {extension}: {e}")
            
            self.logger.info(f"Escaneo completado: {results['new_agents_created']} nuevos agentes creados")
            return results
            
        except Exception as e:
            self.logger.error(f"Error en escaneo automático: {e}")
            return {
                'scanned_extensions': 0,
                'new_agents_created': 0,
                'existing_agents': 0,
                'errors': 1,
                'details': [{'status': 'error', 'message': str(e)}]
            }

    def get_registered_softphones(self) -> Dict[str, Any]:
        """Obtener todos los softphones registrados"""
        return self.registered_softphones.copy()

    def unregister_softphone(self, extension: str) -> bool:
        """Desregistrar un softphone y opcionalmente eliminar el agente"""
        try:
            if extension not in self.registered_softphones:
                return False
            
            softphone_info = self.registered_softphones[extension]
            agent_id = softphone_info.get('agent_id')
            
            # Marcar como inactivo en lugar de eliminar
            softphone_info['status'] = 'inactive'
            softphone_info['unregistered_at'] = datetime.now().isoformat()
            
            self._save_registered_softphones()
            
            self.logger.info(f"Softphone desregistrado: extensión {extension}, agente {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error desregistrando softphone {extension}: {e}")
            return False

    def get_softphone_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de softphones"""
        active_softphones = [s for s in self.registered_softphones.values() if s.get('status') == 'active']
        inactive_softphones = [s for s in self.registered_softphones.values() if s.get('status') == 'inactive']
        
        # Contar por tipo de softphone
        softphone_types = {}
        for softphone in active_softphones:
            stype = softphone.get('softphone_type', 'Unknown')
            softphone_types[stype] = softphone_types.get(stype, 0) + 1
        
        return {
            'total_registered': len(self.registered_softphones),
            'active_softphones': len(active_softphones),
            'inactive_softphones': len(inactive_softphones),
            'softphone_types': softphone_types,
            'auto_created_agents': len([s for s in active_softphones if s.get('auto_created', False)])
        }

# Instancia global del monitor de softphones
softphone_monitor = SoftphoneMonitor()