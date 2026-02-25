"""
Extension Manager - Gestión de extensiones VoIP
Versión limpia sin métodos duplicados
"""

import json
import logging
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .logging_config import get_logger

class ExtensionManager:
    """Gestor de extensiones VoIP"""
    
    def __init__(self, extensions_file: str = None):
        """Inicializar el gestor de extensiones"""
        self.logger = get_logger("extension_manager")
        
        # Configuración por defecto
        self.project_root = Path(__file__).parent.parent
        self.extensions_file = extensions_file or self.project_root / "data" / "extensions.json"
        self.sip_server = "127.0.0.1"
        
        # Cargar extensiones
        self.extensions = self._load_extensions()
        
        self.logger.info(f"Extension Manager inicializado: {len(self.extensions)} extensiones")
    
    def _load_extensions(self) -> Dict[str, Dict[str, Any]]:
        """Cargar extensiones desde archivo JSON"""
        try:
            if self.extensions_file.exists():
                with open(self.extensions_file, 'r') as f:
                    extensions = json.load(f)
                    
                # Validar formato de extensiones
                validated_extensions = {}
                for ext_id, ext_data in extensions.items():
                    if isinstance(ext_data, dict):
                        validated_extensions[ext_id] = ext_data
                    else:
                        # Formato antiguo, convertir
                        validated_extensions[ext_id] = {
                            'extension': ext_id,
                            'password': self._generate_password(),
                            'assigned': False,
                            'server_ip': self.sip_server,
                            'display_name': '',
                            'provider': 'local'
                        }
                
                return validated_extensions
            else:
                self.logger.warning(f"Archivo de extensiones no encontrado: {self.extensions_file}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error cargando extensiones: {e}")
            return {}
    
    def _save_extensions(self):
        """Guardar extensiones en archivo JSON"""
        try:
            # Crear directorio si no existe
            self.extensions_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.extensions_file, 'w') as f:
                json.dump(self.extensions, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error guardando extensiones: {e}")
    
    def _generate_password(self, length: int = 12) -> str:
        """Generar contraseña aleatoria para extensión"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(characters) for _ in range(length))
    
    def get_extension_stats(self):
        """Obtener estadísticas de extensiones"""
        try:
            total = len(self.extensions)
            assigned = sum(1 for ext in self.extensions.values() 
                          if ext.get('assigned', False) or ext.get('status') == 'assigned')
            available = total - assigned
            utilization = (assigned / total * 100) if total > 0 else 0
            
            return {
                'total': total,
                'assigned': assigned,
                'available': available,
                'utilization': round(utilization, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {'total': 0, 'assigned': 0, 'available': 0, 'utilization': 0}
    
    def get_available_extensions(self) -> List[str]:
        """Obtener lista de extensiones disponibles"""
        try:
            available = []
            for ext_id, ext_data in self.extensions.items():
                if not (ext_data.get('assigned', False) or ext_data.get('status') == 'assigned'):
                    available.append(ext_id)
            
            self.logger.info(f"Extensiones disponibles encontradas: {len(available)}")
            return available
            
        except Exception as e:
            self.logger.error(f"Error obteniendo extensiones disponibles: {e}")
            return []
    
    def assign_extension(self, agent_id: str, agent_name: str = None) -> Optional[Dict[str, Any]]:
        """Asignar una extensión disponible a un agente"""
        try:
            available_extensions = self.get_available_extensions()
            
            if not available_extensions:
                self.logger.warning("No hay extensiones disponibles")
                return None
            
            # Tomar la primera extensión disponible
            extension_id = available_extensions[0]
            extension_data = self.extensions[extension_id]
            
            # Asignar extensión
            extension_data.update({
                'assigned': True,
                'status': 'assigned',
                'assigned_to': agent_id,
                'assigned_at': datetime.now().isoformat(),
                'agent_name': agent_name or f"Agent {agent_id}",
                'display_name': agent_name or f"Agent {agent_id}"
            })
            
            self._save_extensions()
            
            result = {
                'extension': extension_id,
                'password': extension_data['password'],
                'server_ip': extension_data.get('server_ip', self.sip_server),
                'assigned_to': agent_id,
                'assigned_at': extension_data['assigned_at']
            }
            
            self.logger.info(f"Extensión {extension_id} asignada a agente {agent_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error asignando extensión: {e}")
            return None
    
    def release_extension_by_agent(self, agent_id: str) -> bool:
        """Liberar extensión asignada a un agente específico"""
        try:
            for ext_id, ext_data in self.extensions.items():
                if ext_data.get('assigned_to') == agent_id:
                    # Liberar extensión
                    ext_data.update({
                        'assigned': False,
                        'status': 'available',
                        'assigned_to': None,
                        'assigned_at': None,
                        'agent_name': None,
                        'display_name': '',
                        'released_at': datetime.now().isoformat()
                    })
                    
                    self._save_extensions()
                    self.logger.info(f"Extensión {ext_id} liberada del agente {agent_id}")
                    return True
            
            self.logger.warning(f"No se encontró extensión asignada al agente {agent_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error liberando extensión del agente {agent_id}: {e}")
            return False
    
    def get_extension_by_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Obtener extensión asignada a un agente"""
        try:
            for ext_id, ext_data in self.extensions.items():
                if ext_data.get('assigned_to') == agent_id:
                    return {
                        'extension': ext_id,
                        'password': ext_data['password'],
                        'server_ip': ext_data.get('server_ip', self.sip_server),
                        'display_name': ext_data.get('display_name', ''),
                        'assigned_at': ext_data.get('assigned_at')
                    }
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo extensión del agente {agent_id}: {e}")
            return None
    
    def get_all_extensions(self) -> Dict[str, Dict[str, Any]]:
        """Obtener todas las extensiones con información completa"""
        try:
            # Asegurar que todas las extensiones tengan el formato correcto
            formatted_extensions = {}
            for ext_num, ext_data in self.extensions.items():
                if isinstance(ext_data, dict):
                    # Asegurar campos requeridos
                    formatted_ext = {
                        'extension': ext_num,
                        'password': ext_data.get('password', self._generate_password()),
                        'assigned': ext_data.get('status') == 'assigned' or ext_data.get('assigned', False),
                        'server_ip': ext_data.get('server_ip', self.sip_server),
                        'display_name': ext_data.get('display_name', ext_data.get('agent_name', '')),
                        'provider': ext_data.get('provider', 'local'),
                        'assigned_to': ext_data.get('assigned_to'),
                        'assigned_at': ext_data.get('assigned_at'),
                        'created_at': ext_data.get('created_at', datetime.now().isoformat())
                    }
                    formatted_extensions[ext_num] = formatted_ext
                else:
                    # Formato antiguo, convertir
                    formatted_extensions[ext_num] = {
                        'extension': ext_num,
                        'password': self._generate_password(),
                        'assigned': False,
                        'server_ip': self.sip_server,
                        'display_name': '',
                        'provider': 'local',
                        'assigned_to': None,
                        'assigned_at': None,
                        'created_at': datetime.now().isoformat()
                    }
            
            return formatted_extensions
            
        except Exception as e:
            self.logger.error(f"Error obteniendo todas las extensiones: {e}")
            return {}
    
    def get_extension(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles de una extensión específica"""
        try:
            if extension_id in self.extensions:
                ext_data = self.extensions[extension_id]
                if isinstance(ext_data, dict):
                    return {
                        'extension': extension_id,
                        'password': ext_data.get('password', ''),
                        'assigned': ext_data.get('status') == 'assigned' or ext_data.get('assigned', False),
                        'server_ip': ext_data.get('server_ip', self.sip_server),
                        'display_name': ext_data.get('display_name', ext_data.get('agent_name', '')),
                        'provider': ext_data.get('provider', 'local'),
                        'assigned_to': ext_data.get('assigned_to'),
                        'assigned_at': ext_data.get('assigned_at'),
                        'created_at': ext_data.get('created_at', datetime.now().isoformat())
                    }
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo extensión {extension_id}: {e}")
            return None

    def update_extension(self, extension_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Actualizar una extensión"""
        try:
            if extension_id not in self.extensions:
                return None
            
            # Campos actualizables
            updatable_fields = ['display_name', 'server_ip', 'password', 'provider']
            
            for field, value in kwargs.items():
                if field in updatable_fields:
                    self.extensions[extension_id][field] = value
            
            # Actualizar timestamp
            self.extensions[extension_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_extensions()
            
            self.logger.info(f"Extensión {extension_id} actualizada")
            return self.get_extension(extension_id)
            
        except Exception as e:
            self.logger.error(f"Error actualizando extensión {extension_id}: {e}")
            return None

    def regenerate_password(self, extension_id: str) -> Optional[Dict[str, str]]:
        """Regenerar contraseña de una extensión"""
        try:
            if extension_id not in self.extensions:
                return None
            
            new_password = self._generate_password()
            self.extensions[extension_id]['password'] = new_password
            self.extensions[extension_id]['password_updated_at'] = datetime.now().isoformat()
            
            self._save_extensions()
            
            self.logger.info(f"Contraseña regenerada para extensión {extension_id}")
            return {'password': new_password}
            
        except Exception as e:
            self.logger.error(f"Error regenerando contraseña de extensión {extension_id}: {e}")
            return None

    def release_extension(self, extension_id: str) -> bool:
        """Liberar una extensión específica por ID"""
        try:
            if extension_id not in self.extensions:
                return False
            
            ext_data = self.extensions[extension_id]
            if not (ext_data.get('status') == 'assigned' or ext_data.get('assigned', False)):
                return False  # Ya está disponible
            
            # Liberar extensión
            ext_data.update({
                'status': 'available',
                'assigned': False,
                'assigned_to': None,
                'assigned_at': None,
                'agent_name': None,
                'display_name': '',
                'released_at': datetime.now().isoformat()
            })
            
            self._save_extensions()
            
            self.logger.info(f"Extensión {extension_id} liberada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error liberando extensión {extension_id}: {e}")
            return False

    def execute_bulk_action(self, action: str, range_start: int, range_end: int) -> Dict[str, Any]:
        """Ejecutar acciones masivas en un rango de extensiones"""
        try:
            affected_extensions = []
            errors = []
            
            for ext_num in range(range_start, range_end + 1):
                ext_id = str(ext_num)
                
                try:
                    if action == 'regenerate_passwords':
                        if ext_id in self.extensions:
                            result = self.regenerate_password(ext_id)
                            if result:
                                affected_extensions.append(ext_id)
                            else:
                                errors.append(f"Error regenerando contraseña de {ext_id}")
                    
                    elif action == 'release_all':
                        if ext_id in self.extensions:
                            if self.release_extension(ext_id):
                                affected_extensions.append(ext_id)
                            else:
                                errors.append(f"Error liberando extensión {ext_id}")
                    
                    elif action == 'reset_display_names':
                        if ext_id in self.extensions:
                            result = self.update_extension(ext_id, display_name='')
                            if result:
                                affected_extensions.append(ext_id)
                            else:
                                errors.append(f"Error reseteando nombre de {ext_id}")
                    
                except Exception as e:
                    errors.append(f"Error procesando {ext_id}: {str(e)}")
            
            return {
                'action': action,
                'range': f"{range_start}-{range_end}",
                'affected_extensions': affected_extensions,
                'success_count': len(affected_extensions),
                'error_count': len(errors),
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error ejecutando acción masiva {action}: {e}")
            return {
                'action': action,
                'range': f"{range_start}-{range_end}",
                'affected_extensions': [],
                'success_count': 0,
                'error_count': 1,
                'errors': [str(e)],
                'timestamp': datetime.now().isoformat()
            }

    def get_extensions_by_range(self, start: int, end: int) -> Dict[str, Dict[str, Any]]:
        """Obtener extensiones en un rango específico"""
        try:
            range_extensions = {}
            for ext_num in range(start, end + 1):
                ext_id = str(ext_num)
                if ext_id in self.extensions:
                    range_extensions[ext_id] = self.get_extension(ext_id)
            
            return range_extensions
            
        except Exception as e:
            self.logger.error(f"Error obteniendo extensiones en rango {start}-{end}: {e}")
            return {}

    def generate_softphone_config(self, extension_id: str, config_type: str = 'generic') -> str:
        """Generar configuración para softphone"""
        try:
            if extension_id not in self.extensions:
                return "Extensión no encontrada"
            
            ext_data = self.extensions[extension_id]
            extension = extension_id
            password = ext_data.get('password', '')
            server_ip = ext_data.get('server_ip', self.sip_server)
            display_name = ext_data.get('display_name', f'Extension {extension}')
            
            if config_type == 'zoiper':
                return f"""Configuración Zoiper
====================
Nombre de cuenta: {display_name}
Username: {extension}
Password: {password}
Domain: {server_ip}
Proxy: {server_ip}
Port: 5060
Transport: UDP

Instrucciones:
1. Abrir Zoiper
2. Ir a Settings > Accounts
3. Agregar nueva cuenta SIP
4. Usar los datos de arriba
5. Guardar configuración
"""
            
            elif config_type == 'portsip':
                return f"""Configuración PortSIP
=====================
Account Name: {display_name}
User Name: {extension}
Password: {password}
SIP Server: {server_ip}
Port: 5060
Transport: UDP

Instrucciones:
1. Abrir PortSIP Softphone
2. Ir a Account > Add Account
3. Usar los datos de arriba
4. Click OK para guardar
"""
            
            else:  # generic
                return f"""Configuración SIP Genérica
==========================
Account: {extension}
Password: {password}
Server: {server_ip}
Port: 5060
Transport: UDP
Display Name: {display_name}
Codec: ulaw, alaw, gsm

Esta configuración es compatible con la mayoría de softphones SIP.
"""
            
        except Exception as e:
            self.logger.error(f"Error generando configuración de softphone: {e}")
            return f"Error generando configuración: {str(e)}"

# Instancia global del gestor de extensiones
extension_manager = ExtensionManager()