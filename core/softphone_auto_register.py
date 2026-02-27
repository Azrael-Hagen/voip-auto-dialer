# Archivo: core/softphone_auto_register.py

"""
Sistema de auto-registro de softphones
Detecta registros automáticamente y crea agentes con extensiones asignadas
"""

import json
import subprocess
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from core.logging_config import get_logger
from core.agent_manager_clean import agent_manager
from core.extension_manager import extension_manager

class SoftphoneAutoRegister:
    def __init__(self):
        self.logger = get_logger("softphone_auto_register")
        self.registered_endpoints = {}
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Iniciar monitoreo de registros de softphones"""
        if self.monitoring:
            self.logger.warning("El monitoreo ya está activo")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Monitoreo de auto-registro iniciado")
        
    def stop_monitoring(self):
        """Detener monitoreo de registros"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Monitoreo de auto-registro detenido")
        
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self.monitoring:
            try:
                self._check_new_registrations()
                time.sleep(10)  # Verificar cada 10 segundos
            except Exception as e:
                self.logger.error(f"Error en loop de monitoreo: {e}")
                time.sleep(30)  # Esperar más tiempo si hay error
                
    def _check_new_registrations(self):
        """Verificar nuevos registros de endpoints"""
        try:
            # Obtener endpoints registrados desde Asterisk
            current_endpoints = self._get_registered_endpoints()
            
            # Detectar nuevos registros
            for endpoint_id, endpoint_info in current_endpoints.items():
                if endpoint_id not in self.registered_endpoints:
                    self._handle_new_registration(endpoint_id, endpoint_info)
                    
            # Detectar desregistros
            for endpoint_id in list(self.registered_endpoints.keys()):
                if endpoint_id not in current_endpoints:
                    self._handle_unregistration(endpoint_id)
                    
            self.registered_endpoints = current_endpoints
            
        except Exception as e:
            self.logger.error(f"Error verificando registros: {e}")
            
    def _get_registered_endpoints(self) -> Dict:
        """Obtener lista de endpoints registrados desde Asterisk"""
        try:
            # Ejecutar comando Asterisk para obtener endpoints
            result = subprocess.run([
                'sudo', 'asterisk', '-rx', 'pjsip show endpoints'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.logger.error(f"Error ejecutando comando Asterisk: {result.stderr}")
                return {}
                
            return self._parse_endpoints_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout ejecutando comando Asterisk")
            return {}
        except Exception as e:
            self.logger.error(f"Error obteniendo endpoints: {e}")
            return {}
            
    def _parse_endpoints_output(self, output: str) -> Dict:
        """Parsear salida del comando pjsip show endpoints"""
        endpoints = {}
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or 'Endpoint:' not in line:
                continue
                
            try:
                # Parsear línea de endpoint
                parts = line.split()
                if len(parts) >= 3:
                    endpoint_id = parts[1]
                    status = parts[2] if len(parts) > 2 else "Unknown"
                    
                    # Solo considerar endpoints registrados/disponibles
                    if status.lower() in ['available', 'online', 'registered']:
                        endpoints[endpoint_id] = {
                            'status': status,
                            'detected_at': datetime.now().isoformat()
                        }
                        
            except Exception as e:
                self.logger.debug(f"Error parseando línea: {line} - {e}")
                continue
                
        return endpoints
        
    def _handle_new_registration(self, endpoint_id: str, endpoint_info: Dict):
        """Manejar nuevo registro de softphone"""
        try:
            self.logger.info(f"Nuevo registro detectado: {endpoint_id}")
            
            # Verificar si ya existe un agente para esta extensión
            existing_agent = self._find_agent_by_extension(endpoint_id)
            if existing_agent:
                self.logger.info(f"Agente existente encontrado para extensión {endpoint_id}: {existing_agent['name']}")
                return existing_agent
                
            # Crear nuevo agente automáticamente
            agent_data = self._create_auto_agent(endpoint_id, endpoint_info)
            
            if agent_data:
                self.logger.info(f"Agente auto-creado: {agent_data['name']} con extensión {endpoint_id}")
                return agent_data
                
        except Exception as e:
            self.logger.error(f"Error manejando nuevo registro {endpoint_id}: {e}")
            
    def _handle_unregistration(self, endpoint_id: str):
        """Manejar desregistro de softphone"""
        try:
            self.logger.info(f"Desregistro detectado: {endpoint_id}")
            
            # Opcional: Marcar agente como offline
            agent = self._find_agent_by_extension(endpoint_id)
            if agent:
                # Actualizar estado del agente a offline
                agent_manager.update_agent_status(agent['id'], 'offline')
                self.logger.info(f"Agente {agent['name']} marcado como offline")
                
        except Exception as e:
            self.logger.error(f"Error manejando desregistro {endpoint_id}: {e}")
            
    def _find_agent_by_extension(self, extension: str) -> Optional[Dict]:
        """Buscar agente por número de extensión"""
        try:
            agents = agent_manager.get_all_agents()
            for agent_id, agent_data in agents.items():
                ext_info = agent_data.get('extension_info', {})
                if ext_info and ext_info.get('extension') == extension:
                    return agent_data
            return None
        except Exception as e:
            self.logger.error(f"Error buscando agente por extensión {extension}: {e}")
            return None
            
    def _create_auto_agent(self, extension: str, endpoint_info: Dict) -> Optional[Dict]:
        """Crear agente automáticamente para nueva extensión"""
        try:
            # Generar nombre automático
            agent_name = f"Auto Agent {extension}"
            agent_email = f"auto.agent.{extension}@voip.local"
            agent_phone = f"+auto{extension}"
            
            # Crear agente
            new_agent = agent_manager.create_agent(
                name=agent_name,
                email=agent_email,
                phone=agent_phone
            )
            
            if not new_agent:
                self.logger.error(f"Error creando agente automático para extensión {extension}")
                return None
                
            # Asignar extensión específica
            extension_result = self._assign_specific_extension(new_agent['id'], extension)
            
            if extension_result:
                self.logger.info(f"Extensión {extension} asignada automáticamente a agente {new_agent['id']}")
                
                # Actualizar agente con información de extensión
                new_agent['extension_info'] = extension_result
                return new_agent
            else:
                self.logger.error(f"Error asignando extensión {extension} a agente {new_agent['id']}")
                return new_agent
                
        except Exception as e:
            self.logger.error(f"Error creando agente automático: {e}")
            return None
            
    def _assign_specific_extension(self, agent_id: str, extension: str) -> Optional[Dict]:
        """Asignar extensión específica a un agente"""
        try:
            # Verificar que la extensión existe en el sistema
            all_extensions = extension_manager.extensions
            if extension not in all_extensions:
                self.logger.error(f"Extensión {extension} no existe en el sistema")
                return None
                
            # Asignar extensión
            result = extension_manager.assign_extension(extension, agent_id)
            if result:
                # Actualizar información del agente
                agents = agent_manager.get_all_agents()
                if agent_id in agents:
                    agents[agent_id]['extension_info'] = {
                        'extension': extension,
                        'password': result.get('password', ''),
                        'status': 'assigned',
                        'assigned_at': datetime.now().isoformat()
                    }
                    agent_manager._save_agents()
                    
                return {
                    'extension': extension,
                    'password': result.get('password', ''),
                    'status': 'assigned',
                    'assigned_at': datetime.now().isoformat()
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Error asignando extensión específica {extension}: {e}")
            return None
            
    def get_monitoring_status(self) -> Dict:
        """Obtener estado del monitoreo"""
        return {
            'monitoring': self.monitoring,
            'registered_endpoints': len(self.registered_endpoints),
            'endpoints': self.registered_endpoints
        }

# Instancia global
softphone_auto_register = SoftphoneAutoRegister()