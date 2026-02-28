#!/usr/bin/env python3
"""
Integración AMI Avanzada para VoIP Auto Dialer
Conexión en tiempo real con Asterisk usando múltiples métodos
"""

import asyncio
import json
import logging
import socket
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import re
import subprocess

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtensionStatus:
    extension: str
    status: str  # online, offline, busy, ringing
    contact: Optional[str] = None
    user_agent: Optional[str] = None
    last_seen: Optional[datetime] = None
    calls_active: int = 0
    password: Optional[str] = None

@dataclass
class CallEvent:
    call_id: str
    from_ext: str
    to_ext: str
    status: str  # ringing, answered, hangup
    start_time: datetime
    duration: Optional[int] = None

class AsteriskCLIClient:
    """Cliente para ejecutar comandos Asterisk CLI"""
    
    def __init__(self):
        self.asterisk_cmd = "sudo asterisk -rx"
    
    async def execute_command(self, command: str) -> str:
        """Ejecutar comando Asterisk CLI"""
        try:
            full_cmd = f'{self.asterisk_cmd} "{command}"'
            result = subprocess.run(
                full_cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Error ejecutando comando: {result.stderr}")
                return ""
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ejecutando comando: {command}")
            return ""
        except Exception as e:
            logger.error(f"Error ejecutando comando {command}: {e}")
            return ""
    
    async def get_pjsip_endpoints(self) -> List[Dict[str, str]]:
        """Obtener endpoints PJSIP"""
        try:
            output = await self.execute_command("pjsip show endpoints")
            endpoints = []
            
            lines = output.split('\n')
            for line in lines:
                if 'Endpoint:' in line and 'Not in use' in line:
                    # Parsear línea de endpoint
                    parts = line.split()
                    if len(parts) >= 2:
                        endpoint_name = parts[1]
                        if endpoint_name.isdigit():  # Solo extensiones numéricas
                            endpoints.append({
                                'name': endpoint_name,
                                'status': 'offline',
                                'type': 'extension'
                            })
            
            return endpoints
            
        except Exception as e:
            logger.error(f"Error obteniendo endpoints: {e}")
            return []
    
    async def get_pjsip_contacts(self) -> Dict[str, str]:
        """Obtener contactos PJSIP"""
        try:
            output = await self.execute_command("pjsip show contacts")
            contacts = {}
            
            lines = output.split('\n')
            for line in lines:
                if 'Contact:' in line and 'sip:' in line:
                    # Parsear contacto
                    match = re.search(r'Contact:\s+(\d+)/sip:(\d+)@([\d\.]+):(\d+)', line)
                    if match:
                        ext_name = match.group(1)
                        ext_num = match.group(2)
                        ip = match.group(3)
                        port = match.group(4)
                        
                        contacts[ext_name] = f"sip:{ext_num}@{ip}:{port}"
            
            return contacts
            
        except Exception as e:
            logger.error(f"Error obteniendo contactos: {e}")
            return {}
    
    async def originate_call(self, from_ext: str, to_ext: str) -> Dict[str, Any]:
        """Originar llamada usando CLI"""
        try:
            command = f"originate PJSIP/{from_ext} extension {to_ext}@from-internal"
            result = await self.execute_command(command)
            
            if "Called" in result or result == "":
                return {
                    "success": True,
                    "message": f"Llamada iniciada: {from_ext} → {to_ext}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Error: {result}"
                }
                
        except Exception as e:
            logger.error(f"Error originando llamada: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class SimpleAMIClient:
    """Cliente AMI simple usando sockets"""
    
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.socket = None
        self.connected = False
        self.event_callbacks = []
        self.running = False
        self.thread = None
    
    async def connect(self) -> bool:
        """Conectar al AMI"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            
            # Leer banner
            banner = self.socket.recv(1024).decode('utf-8')
            logger.info(f"AMI Banner: {banner.strip()}")
            
            # Login
            login_action = f"Action: Login\r\nUsername: {self.username}\r\nSecret: {self.password}\r\n\r\n"
            self.socket.send(login_action.encode('utf-8'))
            
            # Leer respuesta de login
            response = self.socket.recv(1024).decode('utf-8')
            if "Response: Success" in response:
                self.connected = True
                logger.info("✅ Conectado a AMI")
                
                # Iniciar thread de escucha
                self.running = True
                self.thread = threading.Thread(target=self._listen_events, daemon=True)
                self.thread.start()
                
                return True
            else:
                logger.error(f"❌ Error login AMI: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando AMI: {e}")
            return False
    
    def _listen_events(self):
        """Escuchar eventos AMI en thread separado"""
        buffer = ""
        
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                # Procesar eventos completos
                while "\r\n\r\n" in buffer:
                    event_data, buffer = buffer.split("\r\n\r\n", 1)
                    self._process_event(event_data)
                    
            except Exception as e:
                logger.error(f"Error escuchando eventos: {e}")
                break
        
        self.connected = False
    
    def _process_event(self, event_data: str):
        """Procesar evento AMI"""
        try:
            lines = event_data.strip().split("\r\n")
            event = {}
            
            for line in lines:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    event[key] = value
            
            # Notificar callbacks
            for callback in self.event_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error en callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error procesando evento: {e}")
    
    def add_event_listener(self, callback):
        """Agregar listener de eventos"""
        self.event_callbacks.append(callback)
    
    async def send_action(self, action: Dict[str, str]) -> Dict[str, str]:
        """Enviar acción AMI"""
        if not self.connected:
            return {"Response": "Error", "Message": "No conectado"}
        
        try:
            # Construir acción
            action_str = ""
            for key, value in action.items():
                action_str += f"{key}: {value}\r\n"
            action_str += "\r\n"
            
            # Enviar
            self.socket.send(action_str.encode('utf-8'))
            
            # Leer respuesta (simplificado)
            response = self.socket.recv(1024).decode('utf-8')
            
            # Parsear respuesta básica
            result = {}
            for line in response.split("\r\n"):
                if ": " in line:
                    key, value = line.split(": ", 1)
                    result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error enviando acción: {e}")
            return {"Response": "Error", "Message": str(e)}
    
    async def disconnect(self):
        """Desconectar AMI"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)

class AsteriskAMIIntegration:
    """Integración completa con Asterisk AMI usando múltiples métodos"""
    
    def __init__(self, host: str = "localhost", port: int = 5038, 
                 username: str = "admin", password: str = "secret"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        # Clientes
        self.ami_client: Optional[SimpleAMIClient] = None
        self.cli_client = AsteriskCLIClient()
        
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Estado en tiempo real
        self.extensions: Dict[str, ExtensionStatus] = {}
        self.active_calls: Dict[str, CallEvent] = {}
        self.provider_status = "unknown"
        
        # Callbacks para eventos
        self.event_callbacks: Dict[str, List[Callable]] = {
            'extension_status': [],
            'call_event': [],
            'provider_status': [],
            'metrics_update': []
        }
        
        # Métricas
        self.metrics = {
            "endpoints": 0,
            "extensions_online": 0,
            "active_calls": 0,
            "provider_status": "unknown",
            "total_extensions": 0,
            "extensions_with_passwords": 0
        }
        
        # Cargar datos del sistema existente
        self._load_system_data()
    
    def _load_system_data(self):
        """Cargar datos del sistema existente"""
        try:
            # Cargar extensiones desde el sistema
            extensions_file = "voip-auto-dialer/data/extensions.json"
            if os.path.exists(extensions_file):
                with open(extensions_file, 'r') as f:
                    extensions_data = json.load(f)
                    
                for ext_id, ext_data in extensions_data.items():
                    if ext_id.isdigit():
                        self.extensions[ext_id] = ExtensionStatus(
                            extension=ext_id,
                            status='offline',
                            password=ext_data.get('password', f'pass{ext_id}')
                        )
                
                self.metrics["total_extensions"] = len(self.extensions)
                self.metrics["extensions_with_passwords"] = len(self.extensions)
                logger.info(f"📞 Cargadas {len(self.extensions)} extensiones del sistema")
            
            # Cargar proveedores
            providers_file = "voip-auto-dialer/data/providers.json"
            if os.path.exists(providers_file):
                with open(providers_file, 'r') as f:
                    providers_data = json.load(f)
                    if providers_data:
                        self.provider_status = "configured"
                        logger.info("🌐 Proveedor cargado del sistema")
            
        except Exception as e:
            logger.error(f"Error cargando datos del sistema: {e}")
            # Datos por defecto
            for i in range(1000, 1020):
                self.extensions[str(i)] = ExtensionStatus(
                    extension=str(i),
                    status='offline',
                    password=f'pass{i}'
                )
            
            self.metrics.update({
                "total_extensions": 20,
                "extensions_with_passwords": 20
            })
    
    async def connect(self) -> bool:
        """Conectar usando múltiples métodos"""
        logger.info(f"🔌 Conectando a Asterisk: {self.host}:{self.port}")
        
        # Método 1: Intentar AMI
        ami_success = await self._try_ami_connection()
        
        # Método 2: Usar CLI siempre disponible
        cli_success = await self._try_cli_connection()
        
        if ami_success or cli_success:
            self.connected = True
            self.reconnect_attempts = 0
            
            # Cargar estado inicial
            await self._load_initial_state()
            
            logger.info("✅ Integración AMI inicializada")
            return True
        else:
            logger.warning("⚠️ Conexión directa no disponible, usando modo demo")
            self.connected = True  # Modo demo
            await self._simulate_demo_data()
            return True
    
    async def _try_ami_connection(self) -> bool:
        """Intentar conexión AMI"""
        try:
            self.ami_client = SimpleAMIClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            success = await self.ami_client.connect()
            if success:
                # Configurar listeners de eventos
                self.ami_client.add_event_listener(self._on_ami_event)
                logger.info("✅ Conexión AMI establecida")
                return True
            else:
                self.ami_client = None
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conexión AMI: {e}")
            self.ami_client = None
            return False
    
    async def _try_cli_connection(self) -> bool:
        """Intentar conexión CLI"""
        try:
            # Probar comando simple
            result = await self.cli_client.execute_command("core show version")
            if "Asterisk" in result:
                logger.info("✅ Conexión CLI establecida")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conexión CLI: {e}")
            return False
    
    async def _simulate_demo_data(self):
        """Simular datos para demo cuando conexiones no están disponibles"""
        # Simular algunas extensiones online
        online_extensions = ['1000', '1001', '1002']
        for ext in online_extensions:
            if ext in self.extensions:
                self.extensions[ext].status = 'online'
                self.extensions[ext].contact = f'sip:{ext}@192.168.1.100:5060'
                self.extensions[ext].last_seen = datetime.now()
        
        # Actualizar métricas
        self.metrics.update({
            "endpoints": len(self.extensions) + 1,  # +1 para proveedor
            "extensions_online": len(online_extensions),
            "active_calls": 0,
            "provider_status": "demo"
        })
        
        # Notificar actualización
        await self._notify_metrics_update()
        
        logger.info("📊 Datos demo inicializados")
    
    def _on_ami_event(self, event: Dict[str, str]):
        """Manejar eventos AMI"""
        try:
            event_type = event.get('Event', '')
            
            if event_type == 'ContactStatus':
                asyncio.create_task(self._on_contact_status(event))
            elif event_type == 'Newstate':
                asyncio.create_task(self._on_newstate(event))
            elif event_type == 'Hangup':
                asyncio.create_task(self._on_hangup(event))
            elif event_type == 'Registry':
                asyncio.create_task(self._on_registry(event))
                
        except Exception as e:
            logger.error(f"Error procesando evento AMI: {e}")
    
    async def _on_contact_status(self, event: Dict[str, str]):
        """Manejar eventos de estado de contacto"""
        try:
            uri = event.get('URI', '')
            status = event.get('ContactStatus', 'Unknown')
            
            # Extraer extensión del URI
            match = re.search(r'sip:(\d+)@', uri)
            if not match:
                return
            
            extension = match.group(1)
            
            if extension not in self.extensions:
                self.extensions[extension] = ExtensionStatus(
                    extension=extension,
                    status='offline',
                    password=f'pass{extension}'
                )
            
            ext_status = self.extensions[extension]
            old_status = ext_status.status
            
            if status == 'Reachable':
                ext_status.status = 'online'
                ext_status.contact = uri
                ext_status.last_seen = datetime.now()
            elif status == 'Unreachable':
                ext_status.status = 'offline'
                ext_status.contact = None
            
            if old_status != ext_status.status:
                logger.info(f"📞 Extensión {extension}: {old_status} → {ext_status.status}")
                await self._notify_extension_status(extension, ext_status)
            
            await self._update_metrics()
            
        except Exception as e:
            logger.error(f"Error procesando ContactStatus: {e}")
    
    async def _on_newstate(self, event: Dict[str, str]):
        """Manejar eventos de nuevos estados de llamada"""
        try:
            channel = event.get('Channel', '')
            uniqueid = event.get('Uniqueid', '')
            channel_state_desc = event.get('ChannelStateDesc', '')
            
            match = re.search(r'PJSIP/(\d+)-', channel)
            if not match:
                return
            
            extension = match.group(1)
            
            if uniqueid not in self.active_calls:
                self.active_calls[uniqueid] = CallEvent(
                    call_id=uniqueid,
                    from_ext=extension,
                    to_ext='unknown',
                    status='ringing',
                    start_time=datetime.now()
                )
            
            call_event = self.active_calls[uniqueid]
            
            if channel_state_desc in ['Ring', 'Ringing']:
                call_event.status = 'ringing'
                if extension in self.extensions:
                    self.extensions[extension].status = 'ringing'
            elif channel_state_desc in ['Up']:
                call_event.status = 'answered'
                if extension in self.extensions:
                    self.extensions[extension].status = 'busy'
                    self.extensions[extension].calls_active += 1
            
            await self._notify_call_event(call_event)
            await self._update_metrics()
            
        except Exception as e:
            logger.error(f"Error procesando Newstate: {e}")
    
    async def _on_hangup(self, event: Dict[str, str]):
        """Manejar eventos de colgado"""
        try:
            uniqueid = event.get('Uniqueid', '')
            channel = event.get('Channel', '')
            
            match = re.search(r'PJSIP/(\d+)-', channel)
            if match:
                extension = match.group(1)
                
                if extension in self.extensions:
                    if self.extensions[extension].calls_active > 0:
                        self.extensions[extension].calls_active -= 1
                    
                    if self.extensions[extension].calls_active == 0:
                        if self.extensions[extension].contact:
                            self.extensions[extension].status = 'online'
                        else:
                            self.extensions[extension].status = 'offline'
            
            if uniqueid in self.active_calls:
                call_event = self.active_calls[uniqueid]
                call_event.status = 'hangup'
                call_event.duration = int((datetime.now() - call_event.start_time).total_seconds())
                
                await self._notify_call_event(call_event)
                del self.active_calls[uniqueid]
            
            await self._update_metrics()
            
        except Exception as e:
            logger.error(f"Error procesando Hangup: {e}")
    
    async def _on_registry(self, event: Dict[str, str]):
        """Manejar eventos de registro de proveedores"""
        try:
            domain = event.get('Domain', '')
            status = event.get('Status', '')
            
            if 'pbxonthecloud' in domain.lower():
                old_status = self.provider_status
                
                if status == 'Registered':
                    self.provider_status = 'registered'
                elif status == 'Rejected':
                    self.provider_status = 'rejected'
                else:
                    self.provider_status = 'unknown'
                
                if old_status != self.provider_status:
                    logger.info(f"🌐 Proveedor: {old_status} → {self.provider_status}")
                    await self._notify_provider_status()
            
        except Exception as e:
            logger.error(f"Error procesando Registry: {e}")
    
    async def _load_initial_state(self):
        """Cargar estado inicial de Asterisk"""
        try:
            # Usar CLI para obtener estado actual
            endpoints = await self.cli_client.get_pjsip_endpoints()
            contacts = await self.cli_client.get_pjsip_contacts()
            
            # Actualizar extensiones con estado real
            for endpoint in endpoints:
                ext_name = endpoint['name']
                if ext_name in self.extensions:
                    if ext_name in contacts:
                        self.extensions[ext_name].status = 'online'
                        self.extensions[ext_name].contact = contacts[ext_name]
                        self.extensions[ext_name].last_seen = datetime.now()
                    else:
                        self.extensions[ext_name].status = 'offline'
            
            # Actualizar métricas
            await self._update_metrics()
            
            logger.info("📊 Estado inicial cargado desde Asterisk")
            
        except Exception as e:
            logger.error(f"Error cargando estado inicial: {e}")
    
    async def _update_metrics(self):
        """Actualizar métricas del sistema"""
        online_count = len([e for e in self.extensions.values() if e.status == 'online'])
        
        self.metrics.update({
            "endpoints": len(self.extensions) + 1,  # +1 para proveedor
            "extensions_online": online_count,
            "active_calls": len(self.active_calls),
            "provider_status": self.provider_status,
            "total_extensions": len(self.extensions),
            "extensions_with_passwords": len(self.extensions)
        })
        
        await self._notify_metrics_update()
    
    async def _notify_extension_status(self, extension: str, status: ExtensionStatus):
        """Notificar cambio de estado de extensión"""
        for callback in self.event_callbacks['extension_status']:
            try:
                await callback({
                    'type': 'extension_status',
                    'extension': extension,
                    'status': status.status,
                    'contact': status.contact,
                    'last_seen': status.last_seen.isoformat() if status.last_seen else None
                })
            except Exception as e:
                logger.error(f"Error en callback extension_status: {e}")
    
    async def _notify_call_event(self, call_event: CallEvent):
        """Notificar evento de llamada"""
        for callback in self.event_callbacks['call_event']:
            try:
                await callback({
                    'type': 'call_event',
                    'call_id': call_event.call_id,
                    'from_ext': call_event.from_ext,
                    'to_ext': call_event.to_ext,
                    'status': call_event.status,
                    'start_time': call_event.start_time.isoformat(),
                    'duration': call_event.duration
                })
            except Exception as e:
                logger.error(f"Error en callback call_event: {e}")
    
    async def _notify_provider_status(self):
        """Notificar cambio de estado del proveedor"""
        for callback in self.event_callbacks['provider_status']:
            try:
                await callback({
                    'type': 'provider_status',
                    'status': self.provider_status
                })
            except Exception as e:
                logger.error(f"Error en callback provider_status: {e}")
    
    async def _notify_metrics_update(self):
        """Notificar actualización de métricas"""
        for callback in self.event_callbacks['metrics_update']:
            try:
                await callback({
                    'type': 'metrics_update',
                    'data': self.metrics.copy()
                })
            except Exception as e:
                logger.error(f"Error en callback metrics_update: {e}")
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Agregar callback para eventos"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    async def originate_call(self, from_ext: str, to_ext: str, context: str = "from-internal") -> Dict[str, Any]:
        """Originar una llamada desde la interfaz web"""
        if not self.connected:
            return {"success": False, "error": "Sistema no conectado"}
        
        try:
            # Método 1: Usar AMI si está disponible
            if self.ami_client and self.ami_client.connected:
                response = await self.ami_client.send_action({
                    'Action': 'Originate',
                    'Channel': f'PJSIP/{from_ext}',
                    'Exten': to_ext,
                    'Context': context,
                    'Priority': '1',
                    'CallerID': f'Web Call <{from_ext}>',
                    'Timeout': '30000'
                })
                
                if response.get('Response') == 'Success':
                    logger.info(f"📞 Llamada AMI originada: {from_ext} → {to_ext}")
                    return {
                        "success": True,
                        "message": f"Llamada iniciada: {from_ext} → {to_ext}",
                        "method": "AMI"
                    }
            
            # Método 2: Usar CLI
            result = await self.cli_client.originate_call(from_ext, to_ext)
            if result["success"]:
                result["method"] = "CLI"
                logger.info(f"📞 Llamada CLI originada: {from_ext} → {to_ext}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Excepción originando llamada: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_extension_status(self, extension: str) -> Optional[ExtensionStatus]:
        """Obtener estado de una extensión específica"""
        return self.extensions.get(extension)
    
    async def get_all_extensions_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtener estado de todas las extensiones"""
        result = {}
        for ext_id, ext_status in self.extensions.items():
            result[ext_id] = {
                'extension': ext_status.extension,
                'status': ext_status.status,
                'contact': ext_status.contact,
                'password': ext_status.password,
                'last_seen': ext_status.last_seen.isoformat() if ext_status.last_seen else None,
                'calls_active': ext_status.calls_active
            }
        return result
    
    async def get_active_calls(self) -> Dict[str, CallEvent]:
        """Obtener llamadas activas"""
        return self.active_calls.copy()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas actuales"""
        return self.metrics.copy()
    
    async def disconnect(self):
        """Desconectar del AMI"""
        if self.ami_client:
            await self.ami_client.disconnect()
        self.connected = False
    
    async def start_monitoring(self):
        """Iniciar monitoreo continuo"""
        while True:
            try:
                if not self.connected:
                    await self.connect()
                
                # Actualizar estado periódicamente
                if self.connected:
                    await self._load_initial_state()
                    await asyncio.sleep(30)  # Actualizar cada 30 segundos
                else:
                    await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                await asyncio.sleep(5)
