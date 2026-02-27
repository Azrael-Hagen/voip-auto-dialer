"""
Monitor de Asterisk usando AMI (Asterisk Manager Interface)
Reemplaza los comandos sudo con conexiones AMI profesionales
"""

import asyncio
import socket
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.logging_config import get_logger

class AsteriskAMIMonitor:
    """Monitor profesional de Asterisk usando AMI"""
    
    def __init__(self, host='127.0.0.1', port=5038, username='voip_dialer', secret='VoIPDialer2026!'):
        self.host = host
        self.port = port
        self.username = username
        self.secret = secret
        self.logger = get_logger("asterisk_ami")
        self.connected = False
        self.socket = None
        self.last_update = None
        
        # Cache de datos
        self._cache = {
            'system_status': 'Offline',
            'endpoints': [],
            'active_calls': [],
            'extensions_online': 0,
            'last_refresh': None
        }
    
    def connect(self) -> bool:
        """Conectar a AMI"""
        try:
            if self.socket:
                self.socket.close()
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            
            # Leer banner
            banner = self.socket.recv(1024).decode('utf-8')
            self.logger.debug(f"AMI Banner: {banner.strip()}")
            
            # Login
            login_cmd = (
                f"Action: Login\r\n"
                f"Username: {self.username}\r\n"
                f"Secret: {self.secret}\r\n"
                f"\r\n"
            )
            
            self.socket.send(login_cmd.encode('utf-8'))
            response = self.socket.recv(1024).decode('utf-8')
            
            if "Response: Success" in response:
                self.connected = True
                self.logger.info("Conectado a AMI exitosamente")
                return True
            else:
                self.logger.error(f"Error en login AMI: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error conectando a AMI: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconectar de AMI"""
        try:
            if self.socket and self.connected:
                logout_cmd = "Action: Logoff\r\n\r\n"
                self.socket.send(logout_cmd.encode('utf-8'))
                self.socket.close()
            self.connected = False
            self.socket = None
        except Exception as e:
            self.logger.error(f"Error desconectando AMI: {e}")
    
    def send_action(self, action: str, parameters: Dict[str, str] = None) -> str:
        """Enviar acción AMI y obtener respuesta"""
        if not self.connected:
            if not self.connect():
                return ""
        
        try:
            # Construir comando
            cmd = f"Action: {action}\r\n"
            if parameters:
                for key, value in parameters.items():
                    cmd += f"{key}: {value}\r\n"
            cmd += "\r\n"
            
            # Enviar comando
            self.socket.send(cmd.encode('utf-8'))
            
            # Leer respuesta completa
            response = ""
            while True:
                data = self.socket.recv(4096).decode('utf-8')
                response += data
                
                # Buscar fin de respuesta
                if "\r\n\r\n" in response:
                    break
                
                # Timeout de seguridad
                if len(response) > 50000:
                    break
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error enviando acción AMI {action}: {e}")
            self.connected = False
            return ""
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema"""
        try:
            response = self.send_action("CoreStatus")
            
            if "Response: Success" in response:
                # Parsear respuesta
                status_data = {}
                for line in response.split('\r\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        status_data[key.strip()] = value.strip()
                
                self._cache['system_status'] = 'Online'
                self._cache['last_refresh'] = datetime.now().isoformat()
                
                return {
                    'status': 'Online',
                    'uptime': status_data.get('CoreCurrentCalls', '0'),
                    'calls': status_data.get('CoreCurrentCalls', '0'),
                    'channels': status_data.get('CoreCurrentChannels', '0'),
                    'last_update': datetime.now().isoformat()
                }
            else:
                self._cache['system_status'] = 'Error'
                return {
                    'status': 'Error',
                    'uptime': '0',
                    'calls': '0',
                    'channels': '0',
                    'last_update': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del sistema: {e}")
            self._cache['system_status'] = 'Offline'
            return {
                'status': 'Offline',
                'uptime': '0',
                'calls': '0',
                'channels': '0',
                'last_update': datetime.now().isoformat()
            }
    
    def get_pjsip_endpoints(self) -> List[Dict[str, Any]]:
        """Obtener endpoints PJSIP"""
        try:
            response = self.send_action("PJSIPShowEndpoints")
            
            endpoints = []
            if "Response: Success" in response:
                # Parsear endpoints de la respuesta
                lines = response.split('\r\n')
                for line in lines:
                    if 'Endpoint:' in line and 'Unavailable' in line:
                        # Extraer número de extensión
                        match = re.search(r'Endpoint:\s+(\d+)', line)
                        if match:
                            extension = match.group(1)
                            endpoints.append({
                                'extension': extension,
                                'status': 'Unavailable',
                                'contacts': 0
                            })
                    elif 'Endpoint:' in line and 'Available' in line:
                        match = re.search(r'Endpoint:\s+(\d+)', line)
                        if match:
                            extension = match.group(1)
                            endpoints.append({
                                'extension': extension,
                                'status': 'Available',
                                'contacts': 1
                            })
            
            self._cache['endpoints'] = endpoints
            self._cache['extensions_online'] = len([e for e in endpoints if e['status'] == 'Available'])
            
            return endpoints
            
        except Exception as e:
            self.logger.error(f"Error obteniendo endpoints: {e}")
            return self._cache.get('endpoints', [])
    
    def get_active_calls(self) -> List[Dict[str, Any]]:
        """Obtener llamadas activas"""
        try:
            response = self.send_action("CoreShowChannels")
            
            calls = []
            if "Response: Success" in response:
                # Parsear llamadas activas
                lines = response.split('\r\n')
                for line in lines:
                    if 'Channel:' in line:
                        # Extraer información de canal
                        match = re.search(r'Channel:\s+(\S+)', line)
                        if match:
                            channel = match.group(1)
                            calls.append({
                                'channel': channel,
                                'state': 'Active',
                                'duration': '00:00:00'
                            })
            
            self._cache['active_calls'] = calls
            return calls
            
        except Exception as e:
            self.logger.error(f"Error obteniendo llamadas activas: {e}")
            return self._cache.get('active_calls', [])
    
    def get_realtime_dashboard_data(self) -> Dict[str, Any]:
        """Obtener todos los datos para el dashboard en tiempo real"""
        try:
            # Obtener datos del sistema
            system_status = self.get_system_status()
            endpoints = self.get_pjsip_endpoints()
            active_calls = self.get_active_calls()
            
            # Calcular estadísticas
            total_extensions = len(endpoints)
            online_extensions = len([e for e in endpoints if e['status'] == 'Available'])
            total_calls = len(active_calls)
            
            return {
                'system': {
                    'status': system_status['status'],
                    'uptime': system_status.get('uptime', '0'),
                    'last_update': datetime.now().isoformat()
                },
                'extensions': {
                    'total': total_extensions,
                    'online': online_extensions,
                    'offline': total_extensions - online_extensions,
                    'utilization': round((online_extensions / total_extensions * 100) if total_extensions > 0 else 0, 1)
                },
                'calls': {
                    'active': total_calls,
                    'internal': total_calls,  # Simplificado por ahora
                    'external': 0
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos del dashboard: {e}")
            return {
                'system': {'status': 'Error', 'uptime': '0', 'last_update': datetime.now().isoformat()},
                'extensions': {'total': 0, 'online': 0, 'offline': 0, 'utilization': 0},
                'calls': {'active': 0, 'internal': 0, 'external': 0},
                'timestamp': datetime.now().isoformat()
            }
    
    def __del__(self):
        """Destructor - cerrar conexión"""
        self.disconnect()

# Instancia global
asterisk_ami_monitor = AsteriskAMIMonitor()