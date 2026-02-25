#!/usr/bin/env python3
"""
Proveedor FreePBX/Asterisk real usando AMI (Asterisk Manager Interface)
"""
import asyncio
import socket
import uuid
import time
from typing import Dict, Any, Optional
from enum import Enum

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from providers.base_provider import BaseProvider, CallResult, CallStatus, ProviderStatus
from core.logging_config import get_logger

class AMIResponse:
    """Respuesta del Asterisk Manager Interface"""
    def __init__(self, data: str):
        self.data = data
        self.headers = {}
        self.parse_response(data)
    
    def parse_response(self, data: str):
        """Parsear respuesta AMI"""
        lines = data.strip().split('\r\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                self.headers[key.strip().lower()] = value.strip()
    
    def get(self, key: str, default: str = "") -> str:
        """Obtener valor de header"""
        return self.headers.get(key.lower(), default)
    
    @property
    def success(self) -> bool:
        """Verificar si la respuesta fue exitosa"""
        response = self.get('response')
        return response.lower() == 'success'

class FreePBXProvider(BaseProvider):
    """Proveedor para FreePBX/Asterisk usando AMI"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        # Crear ProviderConfig temporal para compatibilidad
        from providers.base_provider import ProviderConfig
        provider_config = ProviderConfig(
            name=name,
            type="freepbx",
            enabled=True,
            cost_per_minute=0.005,
            max_concurrent_calls=10
        )
        super().__init__(provider_config)
        
        # Configuración AMI
        self.ami_host = config.get('ami_host', 'localhost')
        self.ami_port = config.get('ami_port', 5038)
        self.ami_username = config.get('ami_username', 'admin')
        self.ami_password = config.get('ami_password', 'admin')
        
        # Configuración de llamadas
        self.context = config.get('context', 'from-internal')
        self.channel_prefix = config.get('channel_prefix', 'PJSIP')
        self.timeout = config.get('timeout', 30000)  # 30 segundos
        
        # Estado de conexión
        self.ami_socket: Optional[socket.socket] = None
        self.ami_connected = False
        self.ami_reader = None
        self.ami_writer = None
        
        # Llamadas activas
        self.active_calls: Dict[str, Dict] = {}
        
        # Estadísticas (compatibilidad con BaseProvider)
        self.stats = {
            'total_calls': 0,
            'active_calls': 0,
            'total_errors': 0,
            'type': 'freepbx',
            'status': 'available',
            'total_calls_today': 0,
            'total_cost_today': 0.0,
            'max_concurrent_calls': 10
        }
        
    async def initialize(self) -> bool:
        """Inicializar conexión AMI"""
        try:
            self.logger.info(f"Inicializando conexión AMI: {self.config.name}")
            
            # Conectar a AMI
            success = await self._connect_ami()
            if not success:
                self.logger.error("Error conectando a AMI")
                return False
            
            # Autenticar
            success = await self._authenticate_ami()
            if not success:
                self.logger.error("Error autenticando AMI")
                await self._disconnect_ami()
                return False
            
            self.logger.info(f"Conexión AMI establecida: {self.config.name}")
            self.status = ProviderStatus.AVAILABLE
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando AMI: {e}")
            return False
    
    async def _connect_ami(self) -> bool:
        """Conectar al Asterisk Manager Interface"""
        try:
            self.logger.info(f"Conectando a AMI: {self.ami_host}:{self.ami_port}")
            
            # Crear conexión TCP
            self.ami_reader, self.ami_writer = await asyncio.open_connection(
                self.ami_host, self.ami_port
            )
            
            # Leer banner de bienvenida
            banner = await self.ami_reader.readline()
            self.logger.info(f"Banner AMI: {banner.decode().strip()}")
            
            self.ami_connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error conectando AMI: {e}")
            return False
    
    async def _authenticate_ami(self) -> bool:
        """Autenticar con AMI"""
        try:
            # Enviar comando de login
            login_cmd = (
                f"Action: Login\r\n"
                f"Username: {self.ami_username}\r\n"
                f"Secret: {self.ami_password}\r\n"
                f"Events: off\r\n"
                f"\r\n"
            )
            
            self.ami_writer.write(login_cmd.encode())
            await self.ami_writer.drain()
            
            # Leer respuesta
            response_data = await self._read_ami_response()
            response = AMIResponse(response_data)
            
            if response.success:
                self.logger.info("Autenticación AMI exitosa")
                return True
            else:
                self.logger.error(f"Error autenticación AMI: {response.get('message')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error autenticando AMI: {e}")
            return False
    
    async def _read_ami_response(self) -> str:
        """Leer respuesta completa de AMI"""
        response_lines = []
        
        while True:
            line = await self.ami_reader.readline()
            line_str = line.decode().strip()
            
            if not line_str:  # Línea vacía indica fin de respuesta
                break
                
            response_lines.append(line_str)
        
        return '\r\n'.join(response_lines)
    
    async def _disconnect_ami(self):
        """Desconectar AMI"""
        try:
            if self.ami_writer:
                # Enviar logout
                logout_cmd = "Action: Logoff\r\n\r\n"
                self.ami_writer.write(logout_cmd.encode())
                await self.ami_writer.drain()
                
                # Cerrar conexión
                self.ami_writer.close()
                await self.ami_writer.wait_closed()
            
            self.ami_connected = False
            self.logger.info("Conexión AMI cerrada")
            
        except Exception as e:
            self.logger.error(f"Error cerrando AMI: {e}")
    
    async def health_check(self) -> bool:
        """Verificar salud de la conexión AMI"""
        if not self.ami_connected or not self.ami_writer:
            return False
        
        try:
            # Enviar comando Ping
            ping_cmd = "Action: Ping\r\n\r\n"
            self.ami_writer.write(ping_cmd.encode())
            await self.ami_writer.drain()
            
            # Leer respuesta
            response_data = await self._read_ami_response()
            response = AMIResponse(response_data)
            
            return response.success
            
        except Exception as e:
            self.logger.error(f"Error en health check AMI: {e}")
            return False
    
    async def make_call(self, phone_number: str, caller_id: str, 
                       campaign_data: Optional[Dict] = None) -> CallResult:
        """Realizar llamada usando AMI Originate"""
        call_id = f"{self.config.name}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        try:
            self.logger.info(f"Iniciando llamada AMI {call_id} a {phone_number}")
            
            # Preparar canal
            channel = f"{self.channel_prefix}/{phone_number}"
            
            # Preparar variables adicionales
            variables = [f"CALL_ID={call_id}"]
            if campaign_data:
                for key, value in campaign_data.items():
                    variables.append(f"{key.upper()}={value}")
            
            # Comando AMI Originate
            originate_cmd = (
                f"Action: Originate\r\n"
                f"Channel: {channel}\r\n"
                f"Context: {self.context}\r\n"
                f"Exten: {phone_number}\r\n"
                f"Priority: 1\r\n"
                f"CallerID: {caller_id}\r\n"
                f"Timeout: {self.timeout}\r\n"
                f"Variable: {','.join(variables)}\r\n"
                f"Async: true\r\n"
                f"\r\n"
            )
            
            self.logger.info(f"Comando AMI: {originate_cmd.strip()}")
            
            # Enviar comando
            self.ami_writer.write(originate_cmd.encode())
            await self.ami_writer.drain()
            
            # Leer respuesta
            response_data = await self._read_ami_response()
            response = AMIResponse(response_data)
            
            if response.success:
                # Registrar llamada activa
                self.active_calls[call_id] = {
                    'phone_number': phone_number,
                    'caller_id': caller_id,
                    'channel': channel,
                    'start_time': start_time,
                    'campaign_data': campaign_data or {}
                }
                
                self.stats['total_calls'] += 1
                self.stats['active_calls'] += 1
                
                self.logger.info(f"Llamada AMI {call_id} iniciada exitosamente")
                
                return CallResult(
                    call_id=call_id,
                    status=CallStatus.INITIATED,
                    duration=0.0,
                    cost=0.0,
                    provider_response={
                        "provider": self.config.name,
                        "ami_response": response.headers,
                        "channel": channel
                    }
                )
            else:
                error_msg = response.get('message', 'Error desconocido')
                self.logger.error(f"Error iniciando llamada AMI {call_id}: {error_msg}")
                
                self.stats['total_errors'] += 1
                
                return CallResult(
                    call_id=call_id,
                    status=CallStatus.FAILED,
                    duration=0.0,
                    cost=0.0,
                    error_message=error_msg,
                    provider_response={
                        "provider": self.config.name,
                        "ami_response": response.headers,
                        "error": error_msg
                    }
                )
                
        except Exception as e:
            error_msg = f"Excepción en llamada AMI: {e}"
            self.logger.error(f"Error en llamada {call_id}: {error_msg}")
            
            self.stats['total_errors'] += 1
            
            return CallResult(
                call_id=call_id,
                status=CallStatus.FAILED,
                duration=0.0,
                cost=0.0,
                error_message=error_msg,
                provider_response={
                    "provider": self.config.name,
                    "error": error_msg
                }
            )
    
    async def hangup_call(self, call_id: str) -> bool:
        """Colgar llamada usando AMI Hangup"""
        try:
            if call_id not in self.active_calls:
                self.logger.warning(f"Llamada {call_id} no encontrada en llamadas activas")
                return False
            
            call_info = self.active_calls[call_id]
            channel = call_info['channel']
            
            self.logger.info(f"Colgando llamada AMI {call_id}")
            
            # Comando AMI Hangup
            hangup_cmd = (
                f"Action: Hangup\r\n"
                f"Channel: {channel}\r\n"
                f"\r\n"
            )
            
            self.ami_writer.write(hangup_cmd.encode())
            await self.ami_writer.drain()
            
            # Leer respuesta
            response_data = await self._read_ami_response()
            response = AMIResponse(response_data)
            
            if response.success:
                # Remover de llamadas activas
                del self.active_calls[call_id]
                self.stats['active_calls'] = max(0, self.stats['active_calls'] - 1)
                
                self.logger.info(f"Llamada AMI {call_id} colgada exitosamente")
                return True
            else:
                error_msg = response.get('message', 'Error desconocido')
                self.logger.error(f"Error colgando llamada AMI {call_id}: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error colgando llamada {call_id}: {e}")
            return False
    
    async def get_call_status(self, call_id: str) -> Optional[CallStatus]:
        """Obtener estado de llamada (requiere eventos AMI)"""
        # Esta implementación básica solo verifica si está en llamadas activas
        if call_id in self.active_calls:
            return CallStatus.INITIATED
        return None
    
    def can_make_call(self) -> bool:
        """Verificar si el proveedor puede realizar llamadas"""
        return (self.status == ProviderStatus.AVAILABLE and 
                self.ami_connected and 
                len(self.active_calls) < self.config.max_concurrent_calls)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del proveedor"""
        return {
            'name': self.config.name,
            'type': self.config.type,
            'status': self.status.value,
            'active_calls': len(self.active_calls),
            'total_calls_today': self.stats['total_calls'],
            'total_cost_today': self.stats.get('total_cost_today', 0.0),
            'max_concurrent_calls': self.config.max_concurrent_calls,
            'ami_connected': self.ami_connected
        }
    
    async def shutdown(self):
        """Cerrar proveedor y conexiones"""
        try:
            self.logger.info(f"Cerrando proveedor {self.config.name}")
            
            # Colgar todas las llamadas activas
            for call_id in list(self.active_calls.keys()):
                await self.hangup_call(call_id)
            
            # Cerrar conexión AMI
            await self._disconnect_ami()
            
            self.status = ProviderStatus.UNAVAILABLE
            self.logger.info(f"Proveedor {self.config.name} cerrado")
            
        except Exception as e:
            self.logger.error(f"Error cerrando proveedor {self.config.name}: {e}")