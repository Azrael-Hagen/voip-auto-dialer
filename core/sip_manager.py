"""
SIP Manager - Gestión de llamadas SIP y integración con Asterisk
Maneja la comunicación real con el servidor SIP/Asterisk
"""

import asyncio
import socket
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import json
import re

from .logging_config import get_logger

class SIPMethod(Enum):
    INVITE = "INVITE"
    ACK = "ACK"
    BYE = "BYE"
    CANCEL = "CANCEL"
    REGISTER = "REGISTER"
    OPTIONS = "OPTIONS"
    REFER = "REFER"

class SIPResponseCode(Enum):
    TRYING = 100
    RINGING = 180
    OK = 200
    MOVED_TEMPORARILY = 302
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    BUSY_HERE = 486
    REQUEST_TERMINATED = 487
    SERVER_ERROR = 500

class CallState(Enum):
    IDLE = "idle"
    CALLING = "calling"
    RINGING = "ringing"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"

class SIPCall:
    def __init__(self, call_id: str, from_uri: str, to_uri: str):
        self.call_id = call_id
        self.from_uri = from_uri
        self.to_uri = to_uri
        self.state = CallState.IDLE
        self.sip_call_id = str(uuid.uuid4())
        self.local_tag = str(uuid.uuid4())[:8]
        self.remote_tag = None
        self.cseq = 1
        self.start_time = datetime.now()
        self.answer_time = None
        self.end_time = None
        self.local_sdp = None
        self.remote_sdp = None
        self.rtp_port = None

class SIPManager:
    """Gestor de protocolo SIP para llamadas VoIP"""
    
    def __init__(self, local_ip: str = "127.0.0.1", local_port: int = 5060):
        self.logger = get_logger("sip_manager")
        self.local_ip = local_ip
        self.local_port = local_port
        self.server_socket = None
        
        # Configuración SIP
        self.user_agent = "VoIP-AutoDialer/1.0"
        self.sip_domain = local_ip
        
        # Llamadas activas
        self.active_calls: Dict[str, SIPCall] = {}
        
        # Callbacks para eventos
        self.callbacks: Dict[str, Callable] = {}
        
        # Estado del manager
        self.running = False
        
        self.logger.info(f"SIP Manager inicializado en {local_ip}:{local_port}")
    
    async def start(self):
        """Iniciar el servidor SIP"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind((self.local_ip, self.local_port))
            self.server_socket.setblocking(False)
            
            self.running = True
            
            # Iniciar loop de recepción de mensajes
            asyncio.create_task(self._message_receiver_loop())
            
            self.logger.info(f"Servidor SIP iniciado en {self.local_ip}:{self.local_port}")
            
        except Exception as e:
            self.logger.error(f"Error iniciando servidor SIP: {e}")
            raise
    
    async def stop(self):
        """Detener el servidor SIP"""
        try:
            self.running = False
            
            # Finalizar todas las llamadas activas
            for call in list(self.active_calls.values()):
                await self.hangup_call(call.call_id)
            
            if self.server_socket:
                self.server_socket.close()
            
            self.logger.info("Servidor SIP detenido")
            
        except Exception as e:
            self.logger.error(f"Error deteniendo servidor SIP: {e}")
    
    def register_callback(self, event: str, callback: Callable):
        """Registrar callback para eventos SIP"""
        self.callbacks[event] = callback
    
    async def make_call(self, from_extension: str, to_number: str, caller_id: str = None) -> Optional[str]:
        """Iniciar una llamada SIP"""
        try:
            call_id = f"call_{int(time.time())}_{from_extension}"
            
            from_uri = f"sip:{from_extension}@{self.sip_domain}"
            to_uri = f"sip:{to_number}@{self.sip_domain}"
            
            if caller_id:
                from_uri = f"sip:{caller_id}@{self.sip_domain}"
            
            # Crear objeto de llamada
            sip_call = SIPCall(call_id, from_uri, to_uri)
            self.active_calls[call_id] = sip_call
            
            # Enviar INVITE
            invite_message = self._create_invite_message(sip_call)
            await self._send_sip_message(invite_message, self.sip_domain, 5060)
            
            sip_call.state = CallState.CALLING
            
            self.logger.info(f"Llamada iniciada: {from_extension} -> {to_number} ({call_id})")
            
            # Notificar callback
            await self._trigger_callback("call_initiated", {
                "call_id": call_id,
                "from": from_extension,
                "to": to_number
            })
            
            return call_id
            
        except Exception as e:
            self.logger.error(f"Error iniciando llamada: {e}")
            return None
    
    async def answer_call(self, call_id: str) -> bool:
        """Contestar una llamada entrante"""
        try:
            if call_id not in self.active_calls:
                return False
            
            sip_call = self.active_calls[call_id]
            
            # Enviar 200 OK
            ok_message = self._create_response_message(sip_call, SIPResponseCode.OK)
            await self._send_sip_message(ok_message, self.sip_domain, 5060)
            
            sip_call.state = CallState.CONNECTED
            sip_call.answer_time = datetime.now()
            
            self.logger.info(f"Llamada contestada: {call_id}")
            
            # Notificar callback
            await self._trigger_callback("call_answered", {
                "call_id": call_id,
                "answer_time": sip_call.answer_time
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error contestando llamada {call_id}: {e}")
            return False
    
    async def hangup_call(self, call_id: str) -> bool:
        """Colgar una llamada"""
        try:
            if call_id not in self.active_calls:
                return False
            
            sip_call = self.active_calls[call_id]
            
            # Enviar BYE
            bye_message = self._create_bye_message(sip_call)
            await self._send_sip_message(bye_message, self.sip_domain, 5060)
            
            sip_call.state = CallState.DISCONNECTED
            sip_call.end_time = datetime.now()
            
            # Calcular duración
            duration = 0
            if sip_call.answer_time:
                duration = (sip_call.end_time - sip_call.answer_time).total_seconds()
            
            self.logger.info(f"Llamada finalizada: {call_id} (duración: {duration}s)")
            
            # Notificar callback
            await self._trigger_callback("call_ended", {
                "call_id": call_id,
                "duration": duration,
                "end_time": sip_call.end_time
            })
            
            # Limpiar llamada
            del self.active_calls[call_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error colgando llamada {call_id}: {e}")
            return False
    
    async def transfer_call(self, call_id: str, target_extension: str) -> bool:
        """Transferir una llamada a otra extensión"""
        try:
            if call_id not in self.active_calls:
                return False
            
            sip_call = self.active_calls[call_id]
            
            # Enviar REFER para transferencia
            refer_message = self._create_refer_message(sip_call, target_extension)
            await self._send_sip_message(refer_message, self.sip_domain, 5060)
            
            self.logger.info(f"Llamada transferida: {call_id} -> {target_extension}")
            
            # Notificar callback
            await self._trigger_callback("call_transferred", {
                "call_id": call_id,
                "target": target_extension
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error transfiriendo llamada {call_id}: {e}")
            return False
    
    def _create_invite_message(self, sip_call: SIPCall) -> str:
        """Crear mensaje SIP INVITE"""
        
        # Generar SDP básico
        sdp = f"""v=0
o=- {int(time.time())} {int(time.time())} IN IP4 {self.local_ip}
s=-
c=IN IP4 {self.local_ip}
t=0 0
m=audio 8000 RTP/AVP 0 8
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
"""
        
        sip_call.local_sdp = sdp
        
        invite = f"""INVITE {sip_call.to_uri} SIP/2.0
Via: SIP/2.0/UDP {self.local_ip}:{self.local_port};branch=z9hG4bK-{sip_call.local_tag}
From: <{sip_call.from_uri}>;tag={sip_call.local_tag}
To: <{sip_call.to_uri}>
Call-ID: {sip_call.sip_call_id}
CSeq: {sip_call.cseq} INVITE
Contact: <sip:{self.local_ip}:{self.local_port}>
Max-Forwards: 70
User-Agent: {self.user_agent}
Content-Type: application/sdp
Content-Length: {len(sdp)}

{sdp}"""
        
        return invite
    
    def _create_response_message(self, sip_call: SIPCall, response_code: SIPResponseCode) -> str:
        """Crear mensaje de respuesta SIP"""
        
        response_text = {
            SIPResponseCode.TRYING: "Trying",
            SIPResponseCode.RINGING: "Ringing",
            SIPResponseCode.OK: "OK",
            SIPResponseCode.BUSY_HERE: "Busy Here",
            SIPResponseCode.NOT_FOUND: "Not Found"
        }.get(response_code, "Unknown")
        
        response = f"""SIP/2.0 {response_code.value} {response_text}
Via: SIP/2.0/UDP {self.local_ip}:{self.local_port};branch=z9hG4bK-{sip_call.local_tag}
From: <{sip_call.from_uri}>;tag={sip_call.local_tag}
To: <{sip_call.to_uri}>;tag={sip_call.remote_tag or sip_call.local_tag}
Call-ID: {sip_call.sip_call_id}
CSeq: {sip_call.cseq} INVITE
Contact: <sip:{self.local_ip}:{self.local_port}>
User-Agent: {self.user_agent}
Content-Length: 0

"""
        
        return response
    
    def _create_bye_message(self, sip_call: SIPCall) -> str:
        """Crear mensaje SIP BYE"""
        
        sip_call.cseq += 1
        
        bye = f"""BYE {sip_call.to_uri} SIP/2.0
Via: SIP/2.0/UDP {self.local_ip}:{self.local_port};branch=z9hG4bK-{sip_call.local_tag}
From: <{sip_call.from_uri}>;tag={sip_call.local_tag}
To: <{sip_call.to_uri}>;tag={sip_call.remote_tag or sip_call.local_tag}
Call-ID: {sip_call.sip_call_id}
CSeq: {sip_call.cseq} BYE
Contact: <sip:{self.local_ip}:{self.local_port}>
Max-Forwards: 70
User-Agent: {self.user_agent}
Content-Length: 0

"""
        
        return bye
    
    def _create_refer_message(self, sip_call: SIPCall, target_extension: str) -> str:
        """Crear mensaje SIP REFER para transferencia"""
        
        sip_call.cseq += 1
        refer_to = f"sip:{target_extension}@{self.sip_domain}"
        
        refer = f"""REFER {sip_call.to_uri} SIP/2.0
Via: SIP/2.0/UDP {self.local_ip}:{self.local_port};branch=z9hG4bK-{sip_call.local_tag}
From: <{sip_call.from_uri}>;tag={sip_call.local_tag}
To: <{sip_call.to_uri}>;tag={sip_call.remote_tag or sip_call.local_tag}
Call-ID: {sip_call.sip_call_id}
CSeq: {sip_call.cseq} REFER
Contact: <sip:{self.local_ip}:{self.local_port}>
Refer-To: <{refer_to}>
Max-Forwards: 70
User-Agent: {self.user_agent}
Content-Length: 0

"""
        
        return refer
    
    async def _send_sip_message(self, message: str, host: str, port: int):
        """Enviar mensaje SIP"""
        try:
            if self.server_socket:
                self.server_socket.sendto(message.encode(), (host, port))
                self.logger.debug(f"Mensaje SIP enviado a {host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Error enviando mensaje SIP: {e}")
    
    async def _message_receiver_loop(self):
        """Loop para recibir mensajes SIP"""
        try:
            while self.running:
                try:
                    # Recibir mensaje SIP
                    data, addr = await asyncio.get_event_loop().sock_recvfrom(self.server_socket, 4096)
                    message = data.decode()
                    
                    # Procesar mensaje
                    await self._process_sip_message(message, addr)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error recibiendo mensaje SIP: {e}")
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Error en loop receptor SIP: {e}")
    
    async def _process_sip_message(self, message: str, addr: tuple):
        """Procesar mensaje SIP recibido"""
        try:
            lines = message.strip().split('\n')
            if not lines:
                return
            
            first_line = lines[0].strip()
            
            # Extraer headers
            headers = {}
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            call_id = headers.get('call-id', '')
            
            if first_line.startswith('SIP/2.0'):
                # Es una respuesta
                await self._handle_sip_response(first_line, headers, call_id)
            else:
                # Es una petición
                method = first_line.split()[0]
                await self._handle_sip_request(method, headers, call_id, addr)
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje SIP: {e}")
    
    async def _handle_sip_response(self, status_line: str, headers: Dict, call_id: str):
        """Manejar respuesta SIP"""
        try:
            parts = status_line.split()
            if len(parts) >= 2:
                status_code = int(parts[1])
                
                # Buscar llamada correspondiente
                sip_call = None
                for call in self.active_calls.values():
                    if call.sip_call_id == call_id:
                        sip_call = call
                        break
                
                if not sip_call:
                    return
                
                if status_code == 180:  # Ringing
                    sip_call.state = CallState.RINGING
                    await self._trigger_callback("call_ringing", {"call_id": sip_call.call_id})
                    
                elif status_code == 200:  # OK
                    sip_call.state = CallState.CONNECTED
                    sip_call.answer_time = datetime.now()
                    await self._trigger_callback("call_answered", {"call_id": sip_call.call_id})
                    
                elif status_code == 486:  # Busy
                    sip_call.state = CallState.FAILED
                    await self._trigger_callback("call_busy", {"call_id": sip_call.call_id})
                    
                elif status_code >= 400:  # Error
                    sip_call.state = CallState.FAILED
                    await self._trigger_callback("call_failed", {
                        "call_id": sip_call.call_id,
                        "error_code": status_code
                    })
                    
        except Exception as e:
            self.logger.error(f"Error manejando respuesta SIP: {e}")
    
    async def _handle_sip_request(self, method: str, headers: Dict, call_id: str, addr: tuple):
        """Manejar petición SIP"""
        try:
            if method == "INVITE":
                # Llamada entrante
                from_header = headers.get('from', '')
                to_header = headers.get('to', '')
                
                # Extraer URIs
                from_uri = self._extract_uri(from_header)
                to_uri = self._extract_uri(to_header)
                
                # Crear nueva llamada
                new_call_id = f"incoming_{int(time.time())}"
                sip_call = SIPCall(new_call_id, from_uri, to_uri)
                sip_call.sip_call_id = call_id
                sip_call.state = CallState.RINGING
                
                self.active_calls[new_call_id] = sip_call
                
                # Enviar 180 Ringing
                ringing_response = self._create_response_message(sip_call, SIPResponseCode.RINGING)
                await self._send_sip_message(ringing_response, addr[0], addr[1])
                
                # Notificar llamada entrante
                await self._trigger_callback("incoming_call", {
                    "call_id": new_call_id,
                    "from": from_uri,
                    "to": to_uri
                })
                
            elif method == "BYE":
                # Fin de llamada
                sip_call = None
                for call in self.active_calls.values():
                    if call.sip_call_id == call_id:
                        sip_call = call
                        break
                
                if sip_call:
                    await self.hangup_call(sip_call.call_id)
                    
        except Exception as e:
            self.logger.error(f"Error manejando petición SIP {method}: {e}")
    
    def _extract_uri(self, header: str) -> str:
        """Extraer URI SIP de un header"""
        try:
            # Buscar URI entre < >
            match = re.search(r'<([^>]+)>', header)
            if match:
                return match.group(1)
            
            # Si no hay < >, tomar la primera parte
            return header.split(';')[0].strip()
            
        except Exception:
            return header
    
    async def _trigger_callback(self, event: str, data: Dict):
        """Ejecutar callback para evento"""
        try:
            if event in self.callbacks:
                await self.callbacks[event](data)
                
        except Exception as e:
            self.logger.error(f"Error ejecutando callback {event}: {e}")
    
    def get_call_info(self, call_id: str) -> Optional[Dict]:
        """Obtener información de una llamada"""
        if call_id in self.active_calls:
            call = self.active_calls[call_id]
            return {
                "call_id": call.call_id,
                "from_uri": call.from_uri,
                "to_uri": call.to_uri,
                "state": call.state.value,
                "start_time": call.start_time.isoformat(),
                "answer_time": call.answer_time.isoformat() if call.answer_time else None,
                "duration": (datetime.now() - call.start_time).total_seconds()
            }
        return None
    
    def get_active_calls_info(self) -> Dict[str, Dict]:
        """Obtener información de todas las llamadas activas"""
        calls_info = {}
        for call_id, call in self.active_calls.items():
            calls_info[call_id] = self.get_call_info(call_id)
        return calls_info

# Instancia global del SIP manager
sip_manager = SIPManager()