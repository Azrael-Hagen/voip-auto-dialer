
"""
Motor Principal del Auto Dialer - VoIP Auto Dialer
Conecta todos los componentes y controla el flujo completo
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from .call_detector import CallDetector, CallStatus
from .agent_transfer_system import AgentTransferSystem, CallTransferRequest, TransferStrategy
from .logging_config import get_logger
from .campaign_manager import CampaignManager, CampaignStatus, LeadResult
from .extension_manager import extension_manager

class DialerMode(Enum):
    PREVIEW = "preview"
    POWER = "power"
    PREDICTIVE = "predictive"

@dataclass
class ActiveCall:
    id: str
    campaign_id: str
    lead_id: str
    phone_number: str
    extension_used: str
    start_time: datetime
    status: CallStatus
    agent_id: Optional[str] = None
    answer_time: Optional[datetime] = None

class AutoDialerEngine:
    def __init__(self):
        self.logger = get_logger("auto_dialer_engine")
        self.call_detector = CallDetector()
        self.transfer_system = AgentTransferSystem(TransferStrategy.LONGEST_IDLE)
        self.campaign_manager = CampaignManager()
        self.mode = DialerMode.POWER
        self.max_concurrent_calls = 5
        self.calls_per_minute = 10
        self.is_running = False
        self.active_calls: Dict[str, ActiveCall] = {}
        self.call_queue: List[str] = []
        self.stats = {
            'calls_made': 0,
            'calls_answered': 0,
            'calls_transferred': 0,
            'calls_failed': 0
        }
        self._setup_callbacks()
        self.logger.info("Auto Dialer Engine inicializado")
    
    def _setup_callbacks(self):
        self.call_detector.register_callback(CallStatus.ANSWERED_HUMAN, self._on_human_answered)
        self.call_detector.register_callback(CallStatus.ANSWERED_MACHINE, self._on_machine_answered)
        self.call_detector.register_callback(CallStatus.NO_ANSWER, self._on_no_answer)
        self.call_detector.register_callback(CallStatus.FAILED, self._on_call_failed)
        self.logger.info("Callbacks configurados entre componentes")
    
    async def start_campaign_dialing(self, campaign_id: str) -> bool:
        try:
            self.logger.info(f"Iniciando marcado para campaña: {campaign_id}")
            await self.campaign_manager.initialize()
            
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if not campaign:
                self.logger.error(f"Campaña {campaign_id} no encontrada")
                return False
            
            if campaign.status != CampaignStatus.ACTIVE:
                self.logger.error(f"Campaña {campaign_id} no está activa")
                return False
            
            self.max_concurrent_calls = campaign.max_concurrent_calls
            self.calls_per_minute = campaign.calls_per_minute
            
            await self._load_campaign_leads(campaign)
            self.is_running = True
            
            asyncio.create_task(self._dialing_loop(campaign_id))
            asyncio.create_task(self._monitoring_loop())
            
            self.logger.info(f"Marcado iniciado - {len(self.call_queue)} leads en cola")
            return True
        except Exception as e:
            self.logger.error(f"Error iniciando campaña: {e}")
            return False
    
    async def stop_campaign_dialing(self, campaign_id: str) -> bool:
        try:
            self.logger.info(f"Deteniendo marcado para campaña: {campaign_id}")
            self.is_running = False
            
            for call_id, active_call in list(self.active_calls.items()):
                if active_call.campaign_id == campaign_id:
                    await self._end_call(active_call, "dialer_stopped")
            
            self.logger.info("Marcado detenido")
            return True
        except Exception as e:
            self.logger.error(f"Error deteniendo campaña: {e}")
            return False
    
    async def _load_campaign_leads(self, campaign):
        try:
            self.call_queue.clear()
            for lead in campaign.leads:
                if (lead.result == LeadResult.PENDING and 
                    lead.attempts < lead.max_attempts and
                    self._should_call_lead(lead)):
                    self.call_queue.append(lead.id)
            self.logger.info(f"Cargados {len(self.call_queue)} leads en cola")
        except Exception as e:
            self.logger.error(f"Error cargando leads: {e}")
    
    def _should_call_lead(self, lead) -> bool:
        try:
            if lead.next_call_time and lead.next_call_time > datetime.now():
                return False
            current_hour = datetime.now().hour
            if current_hour < 9 or current_hour > 18:
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error verificando lead: {e}")
            return False
    
    async def _dialing_loop(self, campaign_id: str):
        try:
            call_interval = 60.0 / self.calls_per_minute
            self.logger.info(f"Iniciando loop de marcado - Intervalo: {call_interval:.2f}s")
            
            while self.is_running and self.call_queue:
                try:
                    if len(self.active_calls) >= self.max_concurrent_calls:
                        await asyncio.sleep(1)
                        continue
                    
                    if self.mode != DialerMode.PREVIEW:
                        available_agents = await self._get_available_agents_count()
                        if available_agents == 0:
                            self.logger.info("Esperando agentes disponibles...")
                            await asyncio.sleep(5)
                            continue
                    
                    if self.call_queue:
                        lead_id = self.call_queue.pop(0)
                        await self._initiate_call(campaign_id, lead_id)
                        await asyncio.sleep(call_interval)
                
                except Exception as e:
                    self.logger.error(f"Error en loop de marcado: {e}")
                    await asyncio.sleep(1)
            
            self.logger.info("Loop de marcado finalizado")
        except Exception as e:
            self.logger.error(f"Error crítico en loop de marcado: {e}")
    
    async def _initiate_call(self, campaign_id: str, lead_id: str):
        try:
            campaign = self.campaign_manager.get_campaign(campaign_id)
            lead = next((l for l in campaign.leads if l.id == lead_id), None)
            
            if not lead:
                self.logger.error(f"Lead {lead_id} no encontrado")
                return
            
            available_extensions = extension_manager.get_available_extensions()
            if not available_extensions:
                self.logger.warning("No hay extensiones disponibles")
                return
            
            extension_id = available_extensions[0]
            call_id = f"call_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            active_call = ActiveCall(
                id=call_id,
                campaign_id=campaign_id,
                lead_id=lead_id,
                phone_number=lead.phone_number,
                extension_used=extension_id,
                start_time=datetime.now(),
                status=CallStatus.DIALING
            )
            
            self.active_calls[call_id] = active_call
            
            success = await self._make_sip_call(active_call, campaign.caller_id)
            
            if success:
                lead.attempts += 1
                lead.last_call_time = datetime.now()
                self.stats['calls_made'] += 1
                
                self.logger.info(f"Llamada iniciada: {lead.phone_number} ({call_id})")
                
                call_session = {
                    'call_id': call_id,
                    'phone_number': lead.phone_number,
                    'campaign_id': campaign_id,
                    'lead_id': lead_id,
                    'start_time': active_call.start_time
                }
                
                asyncio.create_task(self.call_detector.monitor_call(call_session))
            else:
                del self.active_calls[call_id]
                lead.result = LeadResult.FAILED
                self.stats['calls_failed'] += 1
        except Exception as e:
            self.logger.error(f"Error iniciando llamada: {e}")
    
    async def _make_sip_call(self, active_call: ActiveCall, caller_id: str) -> bool:
        try:
            self.logger.info(f"Iniciando llamada SIP: {active_call.phone_number}")
            active_call.status = CallStatus.DIALING
            return True
        except Exception as e:
            self.logger.error(f"Error en llamada SIP: {e}")
            return False
    
    async def _get_available_agents_count(self) -> int:
        try:
            stats = self.transfer_system.get_system_stats()
            return stats.get('available_agents', 0)
        except Exception as e:
            self.logger.error(f"Error contando agentes: {e}")
            return 0
    
    async def _monitoring_loop(self):
        try:
            while self.is_running:
                current_time = time.time()
                for call_id, active_call in list(self.active_calls.items()):
                    call_age = current_time - active_call.start_time.timestamp()
                    if call_age > 300 and active_call.status == CallStatus.DIALING:
                        await self._end_call(active_call, "timeout")
                await asyncio.sleep(10)
        except Exception as e:
            self.logger.error(f"Error en loop de monitoreo: {e}")
    
    async def _on_human_answered(self, call_session):
        try:
            call_id = call_session['call_id']
            if call_id not in self.active_calls:
                return
            
            active_call = self.active_calls[call_id]
            active_call.status = CallStatus.ANSWERED_HUMAN
            active_call.answer_time = datetime.now()
            self.stats['calls_answered'] += 1
            
            self.logger.info(f"🟢 HUMANO CONTESTÓ: {active_call.phone_number}")
            
            transfer_request = CallTransferRequest(
                call_id=call_id,
                phone_number=active_call.phone_number,
                campaign_id=active_call.campaign_id,
                caller_info={'lead_id': call_session['lead_id'], 'phone_number': active_call.phone_number}
            )
            
            success = await self.transfer_system.transfer_call_to_agent(transfer_request)
            
            if success:
                self.stats['calls_transferred'] += 1
                self.logger.info(f"✅ Llamada transferida exitosamente")
            else:
                self.logger.warning(f"⚠️ No se pudo transferir - agregada a cola")
        except Exception as e:
            self.logger.error(f"Error en callback human_answered: {e}")
    
    async def _on_machine_answered(self, call_session):
        try:
            call_id = call_session['call_id']
            if call_id not in self.active_calls:
                return
            active_call = self.active_calls[call_id]
            self.logger.info(f"🔴 MÁQUINA CONTESTÓ: {active_call.phone_number}")
            await self._end_call(active_call, "answering_machine")
        except Exception as e:
            self.logger.error(f"Error en callback machine_answered: {e}")
    
    async def _on_no_answer(self, call_session):
        try:
            call_id = call_session['call_id']
            if call_id not in self.active_calls:
                return
            active_call = self.active_calls[call_id]
            self.logger.info(f"⚪ NO CONTESTARON: {active_call.phone_number}")
            await self._end_call(active_call, "no_answer")
        except Exception as e:
            self.logger.error(f"Error en callback no_answer: {e}")
    
    async def _on_call_failed(self, call_session):
        try:
            call_id = call_session['call_id']
            if call_id not in self.active_calls:
                return
            active_call = self.active_calls[call_id]
            self.logger.info(f"❌ LLAMADA FALLÓ: {active_call.phone_number}")
            await self._end_call(active_call, "failed")
        except Exception as e:
            self.logger.error(f"Error en callback call_failed: {e}")
    
    async def _end_call(self, active_call: ActiveCall, reason: str):
        try:
            campaign = self.campaign_manager.get_campaign(active_call.campaign_id)
            lead = next((l for l in campaign.leads if l.id == active_call.lead_id), None)
            
            if lead:
                if reason == "answering_machine":
                    lead.result = LeadResult.VOICEMAIL
                elif reason == "no_answer":
                    lead.result = LeadResult.NO_ANSWER
                    if lead.attempts < lead.max_attempts:
                        lead.next_call_time = datetime.now() + timedelta(minutes=30)
                elif reason == "failed":
                    lead.result = LeadResult.FAILED
                elif reason == "transferred":
                    lead.result = LeadResult.TRANSFERRED
            
            if active_call.id in self.active_calls:
                del self.active_calls[active_call.id]
            
            self.logger.info(f"Llamada finalizada: {active_call.phone_number} - {reason}")
        except Exception as e:
            self.logger.error(f"Error finalizando llamada: {e}")
    
    def get_engine_stats(self) -> Dict:
        return {
            'is_running': self.is_running,
            'mode': self.mode.value,
            'active_calls': len(self.active_calls),
            'queue_size': len(self.call_queue),
            'max_concurrent_calls': self.max_concurrent_calls,
            'calls_per_minute': self.calls_per_minute,
            'stats': self.stats.copy(),
            'transfer_system_stats': self.transfer_system.get_system_stats()
        }

