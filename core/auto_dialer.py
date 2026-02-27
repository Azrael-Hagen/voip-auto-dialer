"""
Auto Dialer Core - Sistema principal de marcado automático
Integra detección de respuesta, transferencia a agentes y gestión de campañas
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import json
from pathlib import Path

from .logging_config import get_logger
from .extension_manager import extension_manager
from .agent_manager_clean import agent_manager
from .campaign_manager import CampaignManager, Campaign, Lead, LeadResult, CampaignStatus

class CallStatus(Enum):
    DIALING = "dialing"
    RINGING = "ringing"
    ANSWERED_HUMAN = "answered_human"
    ANSWERED_MACHINE = "answered_machine"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    FAILED = "failed"
    TRANSFERRED = "transferred"

class DialerMode(Enum):
    PREVIEW = "preview"      # Agente ve info antes de llamar
    POWER = "power"          # Marca automáticamente, conecta cuando contestan
    PREDICTIVE = "predictive" # Predice disponibilidad de agentes

@dataclass
class CallSession:
    id: str
    campaign_id: str
    lead_id: str
    phone_number: str
    agent_id: Optional[str] = None
    extension_id: Optional[str] = None
    status: CallStatus = CallStatus.DIALING
    start_time: datetime = None
    answer_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0
    sip_call_id: Optional[str] = None
    provider_id: Optional[str] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()

class AutoDialer:
    """Sistema principal de marcado automático"""
    
    def __init__(self):
        self.logger = get_logger("auto_dialer")
        self.campaign_manager = CampaignManager()
        
        # Estado del dialer
        self.active_calls: Dict[str, CallSession] = {}
        self.call_queue: List[str] = []  # IDs de leads pendientes
        self.dialer_running = False
        self.max_concurrent_calls = 10
        self.calls_per_minute = 30
        self.mode = DialerMode.POWER
        
        # Configuración AMD (Answering Machine Detection)
        self.amd_enabled = True
        self.amd_timeout = 5  # segundos
        self.silence_threshold = 0.5
        
        # Callbacks para eventos
        self.callbacks = {}
        
        # Estadísticas
        self.stats = {
            'calls_made': 0,
            'calls_answered': 0,
            'calls_transferred': 0,
            'calls_failed': 0,
            'total_talk_time': 0.0
        }
        
        self.logger.info("Auto Dialer inicializado")
    
    async def _on_call_answered(self, data: Dict):
        """Callback cuando una llamada es contestada"""
        try:
            call_id = data.get("call_id")
            
            # Buscar la llamada en nuestras llamadas activas
            for session_id, call_session in self.active_calls.items():
                if call_session.sip_call_id == call_id:
                    call_session.status = CallStatus.ANSWERED_HUMAN
                    call_session.answer_time = datetime.now()
                    
                    # Detectar si es humano o máquina
                    if self.amd_enabled:
                        is_human = await self._detect_answering_machine(call_session)
                        if not is_human:
                            call_session.status = CallStatus.ANSWERED_MACHINE
                            await self._end_call(call_session, "answering_machine")
                            return
                    
                    # Transferir a agente
                    await self._transfer_to_agent(call_session)
                    break
                    
        except Exception as e:
            self.logger.error(f"Error en callback call_answered: {e}")
    
    async def _on_call_ended(self, data: Dict):
        """Callback cuando una llamada termina"""
        try:
            call_id = data.get("call_id")
            duration = data.get("duration", 0)
            
            # Buscar y finalizar la llamada
            for session_id, call_session in list(self.active_calls.items()):
                if call_session.sip_call_id == call_id:
                    await self._end_call(call_session, "completed")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error en callback call_ended: {e}")
    
    async def _on_call_failed(self, data: Dict):
        """Callback cuando una llamada falla"""
        try:
            call_id = data.get("call_id")
            error_code = data.get("error_code")
            
            # Buscar y marcar como fallida
            for session_id, call_session in list(self.active_calls.items()):
                if call_session.sip_call_id == call_id:
                    if error_code == 486:  # Busy
                        await self._end_call(call_session, "busy")
                    else:
                        await self._end_call(call_session, "failed")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error en callback call_failed: {e}")
    
    async def initialize(self):
        """Inicializar el auto dialer"""
        try:
            await self.campaign_manager.initialize()
            self.logger.info("Auto Dialer inicializado completamente")
        except Exception as e:
            self.logger.error(f"Error inicializando Auto Dialer: {e}")
            raise
    
    def register_callback(self, event: str, callback: Callable):
        """Registrar callback para eventos del dialer"""
        self.callbacks[event] = callback
    
    async def start_dialing(self, campaign_id: str) -> bool:
        """Iniciar marcado automático para una campaña"""
        try:
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if not campaign:
                self.logger.error(f"Campaña {campaign_id} no encontrada")
                return False
            
            if campaign.status != CampaignStatus.ACTIVE:
                self.logger.error(f"Campaña {campaign_id} no está activa")
                return False
            
            # Cargar leads pendientes en cola
            await self._load_campaign_leads(campaign)
            
            # Iniciar proceso de marcado
            self.dialer_running = True
            self.max_concurrent_calls = campaign.max_concurrent_calls
            self.calls_per_minute = campaign.calls_per_minute
            
            # Iniciar tareas asíncronas
            asyncio.create_task(self._dialing_loop(campaign_id))
            asyncio.create_task(self._call_monitoring_loop())
            
            self.logger.info(f"Marcado automático iniciado para campaña {campaign.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando marcado: {e}")
            return False
    
    async def stop_dialing(self, campaign_id: str) -> bool:
        """Detener marcado automático"""
        try:
            self.dialer_running = False
            
            # Finalizar llamadas activas
            for call_id, call_session in list(self.active_calls.items()):
                if call_session.campaign_id == campaign_id:
                    await self._end_call(call_session, "dialer_stopped")
            
            self.logger.info(f"Marcado automático detenido para campaña {campaign_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo marcado: {e}")
            return False
    
    async def _load_campaign_leads(self, campaign: Campaign):
        """Cargar leads de campaña en cola de marcado"""
        try:
            self.call_queue.clear()
            
            for lead in campaign.leads:
                # Solo agregar leads que necesitan ser llamados
                if (lead.result == LeadResult.PENDING and 
                    lead.attempts < lead.max_attempts and
                    self._should_call_lead(lead)):
                    self.call_queue.append(lead.id)
            
            self.logger.info(f"Cargados {len(self.call_queue)} leads en cola de marcado")
            
        except Exception as e:
            self.logger.error(f"Error cargando leads: {e}")
    
    def _should_call_lead(self, lead: Lead) -> bool:
        """Determinar si un lead debe ser llamado ahora"""
        try:
            # Verificar si es hora de llamar
            if lead.next_call_time and lead.next_call_time > datetime.now():
                return False
            
            # Verificar horarios de llamada (implementar según campaign.calling_hours)
            current_hour = datetime.now().hour
            # Por ahora, permitir llamadas entre 9 AM y 6 PM
            if current_hour < 9 or current_hour > 18:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando si llamar lead {lead.id}: {e}")
            return False
    
    async def _dialing_loop(self, campaign_id: str):
        """Loop principal de marcado"""
        try:
            call_interval = 60.0 / self.calls_per_minute  # Intervalo entre llamadas
            
            while self.dialer_running and self.call_queue:
                try:
                    # Verificar si podemos hacer más llamadas
                    if len(self.active_calls) >= self.max_concurrent_calls:
                        await asyncio.sleep(1)
                        continue
                    
                    # Verificar si hay agentes disponibles
                    available_agents = self._get_available_agents()
                    if not available_agents and self.mode != DialerMode.PREVIEW:
                        await asyncio.sleep(5)  # Esperar agentes disponibles
                        continue
                    
                    # Tomar siguiente lead de la cola
                    if self.call_queue:
                        lead_id = self.call_queue.pop(0)
                        await self._initiate_call(campaign_id, lead_id)
                        
                        # Esperar intervalo entre llamadas
                        await asyncio.sleep(call_interval)
                
                except Exception as e:
                    self.logger.error(f"Error en loop de marcado: {e}")
                    await asyncio.sleep(1)
            
            self.logger.info("Loop de marcado finalizado")
            
        except Exception as e:
            self.logger.error(f"Error crítico en loop de marcado: {e}")
    
    async def _initiate_call(self, campaign_id: str, lead_id: str):
        """Iniciar una llamada a un lead"""
        try:
            # Obtener información del lead
            campaign = self.campaign_manager.get_campaign(campaign_id)
            lead = next((l for l in campaign.leads if l.id == lead_id), None)
            
            if not lead:
                self.logger.error(f"Lead {lead_id} no encontrado")
                return
            
            # Crear sesión de llamada
            call_session = CallSession(
                id=f"call_{int(time.time())}_{lead_id[:8]}",
                campaign_id=campaign_id,
                lead_id=lead_id,
                phone_number=lead.phone_number
            )
            
            # Obtener extensión disponible
            extension_info = await self._get_available_extension()
            if not extension_info:
                self.logger.warning("No hay extensiones disponibles para llamada")
                return
            
            call_session.extension_id = extension_info['extension']
            
            # Registrar llamada activa
            self.active_calls[call_session.id] = call_session
            
            # Iniciar llamada SIP
            success = await self._make_sip_call(call_session, campaign.caller_id)
            
            if success:
                lead.attempts += 1
                lead.last_call_time = datetime.now()
                self.stats['calls_made'] += 1
                
                self.logger.info(f"Llamada iniciada: {call_session.phone_number} ({call_session.id})")
                
                # Monitorear llamada para detección de respuesta
                asyncio.create_task(self._monitor_call_answer(call_session))
            else:
                # Limpiar si falló
                del self.active_calls[call_session.id]
                lead.result = LeadResult.FAILED
                self.stats['calls_failed'] += 1
                
        except Exception as e:
            self.logger.error(f"Error iniciando llamada a lead {lead_id}: {e}")
    
    async def _make_sip_call(self, call_session: CallSession, caller_id: str) -> bool:
        """Realizar llamada SIP real"""
        try:
            # TODO: Implementar llamada SIP real usando Asterisk AMI o similar
            # Por ahora, simular llamada exitosa
            
            # Ejemplo de comando Asterisk AMI:
            # Action: Originate
            # Channel: SIP/{extension_id}
            # Context: from-internal
            # Exten: {phone_number}
            # Priority: 1
            # CallerID: {caller_id}
            # Timeout: 30000
            # Variable: CALL_SESSION_ID={call_session.id}
            
            self.logger.info(f"Iniciando llamada SIP: {call_session.phone_number}")
            
            # Simular éxito por ahora
            call_session.sip_call_id = f"sip_{call_session.id}"
            call_session.status = CallStatus.DIALING
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error en llamada SIP: {e}")
            return False
    
    async def _monitor_call_answer(self, call_session: CallSession):
        """Monitorear llamada para detectar respuesta"""
        try:
            timeout = 30  # Timeout de llamada en segundos
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # TODO: Verificar estado real de llamada SIP
                # Por ahora, simular respuesta después de 5-10 segundos
                
                if time.time() - start_time > 8:  # Simular respuesta
                    call_session.status = CallStatus.ANSWERED_HUMAN
                    call_session.answer_time = datetime.now()
                    
                    # Detectar si es humano o máquina
                    if self.amd_enabled:
                        is_human = await self._detect_answering_machine(call_session)
                        if not is_human:
                            call_session.status = CallStatus.ANSWERED_MACHINE
                            await self._end_call(call_session, "answering_machine")
                            return
                    
                    # Transferir a agente disponible
                    await self._transfer_to_agent(call_session)
                    return
                
                await asyncio.sleep(0.5)
            
            # Timeout - no answer
            call_session.status = CallStatus.NO_ANSWER
            await self._end_call(call_session, "no_answer")
            
        except Exception as e:
            self.logger.error(f"Error monitoreando llamada {call_session.id}: {e}")
            await self._end_call(call_session, "error")
    
    async def _detect_answering_machine(self, call_session: CallSession) -> bool:
        """Detectar si contestó humano o máquina contestadora"""
        try:
            # TODO: Implementar detección real de AMD usando análisis de audio
            # Por ahora, simular detección (80% humano, 20% máquina)
            
            await asyncio.sleep(self.amd_timeout)
            
            import random
            is_human = random.random() > 0.2  # 80% probabilidad de humano
            
            self.logger.info(f"AMD resultado: {'Humano' if is_human else 'Máquina'} - {call_session.id}")
            return is_human
            
        except Exception as e:
            self.logger.error(f"Error en detección AMD: {e}")
            return True  # Por defecto asumir humano
    
    async def _transfer_to_agent(self, call_session: CallSession):
        """Transferir llamada contestada a agente disponible"""
        try:
            # Obtener agente disponible
            available_agents = self._get_available_agents()
            
            if not available_agents:
                self.logger.warning("No hay agentes disponibles para transferencia")
                await self._end_call(call_session, "no_agents")
                return
            
            # Seleccionar agente (por ahora, el primero disponible)
            agent_id = available_agents[0]
            agent_info = agent_manager.get_agent(agent_id)
            
            if not agent_info or not agent_info.get('extension_info'):
                self.logger.error(f"Agente {agent_id} no tiene extensión asignada")
                await self._end_call(call_session, "agent_no_extension")
                return
            
            # Realizar transferencia SIP
            success = await self._perform_sip_transfer(call_session, agent_info)
            
            if success:
                call_session.agent_id = agent_id
                call_session.status = CallStatus.TRANSFERRED
                self.stats['calls_answered'] += 1
                self.stats['calls_transferred'] += 1
                
                # Marcar agente como ocupado
                agent_manager.set_agent_status(agent_id, "busy")
                
                self.logger.info(f"Llamada transferida a agente {agent_id}: {call_session.id}")
                
                # Monitorear fin de llamada
                asyncio.create_task(self._monitor_call_end(call_session))
            else:
                await self._end_call(call_session, "transfer_failed")
                
        except Exception as e:
            self.logger.error(f"Error transfiriendo llamada: {e}")
            await self._end_call(call_session, "transfer_error")
    
    async def _perform_sip_transfer(self, call_session: CallSession, agent_info: Dict) -> bool:
        """Realizar transferencia SIP real"""
        try:
            # TODO: Implementar transferencia SIP real
            # Ejemplo usando Asterisk AMI:
            # Action: Redirect
            # Channel: {call_session.sip_call_id}
            # Context: from-internal
            # Exten: {agent_extension}
            # Priority: 1
            
            agent_extension = agent_info['extension_info']['extension']
            self.logger.info(f"Transfiriendo llamada a extensión {agent_extension}")
            
            # Simular éxito por ahora
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            self.logger.error(f"Error en transferencia SIP: {e}")
            return False
    
    async def _monitor_call_end(self, call_session: CallSession):
        """Monitorear fin de llamada para liberar recursos"""
        try:
            # TODO: Monitorear eventos SIP para detectar fin de llamada
            # Por ahora, simular llamada de 60-300 segundos
            
            import random
            call_duration = random.randint(60, 300)
            await asyncio.sleep(call_duration)
            
            await self._end_call(call_session, "completed")
            
        except Exception as e:
            self.logger.error(f"Error monitoreando fin de llamada: {e}")
    
    async def _end_call(self, call_session: CallSession, reason: str):
        """Finalizar llamada y limpiar recursos"""
        try:
            call_session.end_time = datetime.now()
            
            if call_session.answer_time:
                call_session.duration = (call_session.end_time - call_session.answer_time).total_seconds()
                self.stats['total_talk_time'] += call_session.duration
            
            # Actualizar resultado del lead
            campaign = self.campaign_manager.get_campaign(call_session.campaign_id)
            lead = next((l for l in campaign.leads if l.id == call_session.lead_id), None)
            
            if lead:
                if reason == "completed" or reason == "transfer_success":
                    lead.result = LeadResult.TRANSFERRED
                    lead.total_talk_time += call_session.duration
                elif reason == "answering_machine":
                    lead.result = LeadResult.VOICEMAIL
                elif reason == "no_answer":
                    lead.result = LeadResult.NO_ANSWER
                elif reason == "busy":
                    lead.result = LeadResult.BUSY
                else:
                    lead.result = LeadResult.FAILED
                
                # Programar siguiente intento si es necesario
                if (lead.result in [LeadResult.NO_ANSWER, LeadResult.BUSY] and 
                    lead.attempts < lead.max_attempts):
                    lead.next_call_time = datetime.now() + timedelta(minutes=30)
            
            # Liberar agente si estaba asignado
            if call_session.agent_id:
                agent_manager.set_agent_status(call_session.agent_id, "available")
            
            # Limpiar llamada activa
            if call_session.id in self.active_calls:
                del self.active_calls[call_session.id]
            
            self.logger.info(f"Llamada finalizada: {call_session.id} - {reason}")
            
        except Exception as e:
            self.logger.error(f"Error finalizando llamada: {e}")
    
    def _get_available_agents(self) -> List[str]:
        """Obtener lista de agentes disponibles"""
        try:
            all_agents = agent_manager.get_all_agents()
            available = []
            
            for agent_id, agent_data in all_agents.items():
                if (agent_data.get('status') == 'available' and 
                    agent_data.get('extension_info')):
                    available.append(agent_id)
            
            return available
            
        except Exception as e:
            self.logger.error(f"Error obteniendo agentes disponibles: {e}")
            return []
    
    async def _get_available_extension(self) -> Optional[Dict]:
        """Obtener extensión disponible para llamada saliente"""
        try:
            available_extensions = extension_manager.get_available_extensions()
            
            if available_extensions:
                extension_id = available_extensions[0]
                extension_info = extension_manager.get_extension(extension_id)
                return extension_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo extensión disponible: {e}")
            return None
    
    async def _call_monitoring_loop(self):
        """Loop de monitoreo general de llamadas"""
        try:
            while self.dialer_running:
                # Limpiar llamadas colgadas o con timeout
                current_time = time.time()
                
                for call_id, call_session in list(self.active_calls.items()):
                    call_age = current_time - call_session.start_time.timestamp()
                    
                    # Timeout de llamadas sin respuesta (5 minutos)
                    if call_age > 300 and call_session.status in [CallStatus.DIALING, CallStatus.RINGING]:
                        await self._end_call(call_session, "timeout")
                
                await asyncio.sleep(10)  # Verificar cada 10 segundos
                
        except Exception as e:
            self.logger.error(f"Error en loop de monitoreo: {e}")
    
    def get_dialer_stats(self) -> Dict:
        """Obtener estadísticas del dialer"""
        return {
            'active_calls': len(self.active_calls),
            'queue_size': len(self.call_queue),
            'dialer_running': self.dialer_running,
            'mode': self.mode.value,
            'max_concurrent_calls': self.max_concurrent_calls,
            'calls_per_minute': self.calls_per_minute,
            'stats': self.stats.copy(),
            'available_agents': len(self._get_available_agents())
        }
    
    def get_active_calls(self) -> Dict[str, Dict]:
        """Obtener información de llamadas activas"""
        active_calls_info = {}
        
        for call_id, call_session in self.active_calls.items():
            active_calls_info[call_id] = {
                'phone_number': call_session.phone_number,
                'status': call_session.status.value,
                'duration': (datetime.now() - call_session.start_time).total_seconds(),
                'agent_id': call_session.agent_id,
                'extension_id': call_session.extension_id
            }
        
        return active_calls_info

# Instancia global del auto dialer
auto_dialer = AutoDialer()