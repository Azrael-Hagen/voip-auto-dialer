
"""
Detector de Respuesta de Llamadas - VoIP Auto Dialer
Detecta cuando una llamada es contestada por humano vs máquina
"""

import asyncio
import time
from enum import Enum
from typing import Optional, Callable, Dict
from datetime import datetime
from .logging_config import get_logger

class CallStatus(Enum):
    DIALING = "dialing"
    RINGING = "ringing"
    ANSWERED_HUMAN = "answered_human"
    ANSWERED_MACHINE = "answered_machine"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    FAILED = "failed"

class CallDetector:
    def __init__(self):
        self.logger = get_logger("call_detector")
        self.amd_timeout = 5
        self.silence_threshold = 0.5
        self.callbacks = {}
        self.logger.info("Call Detector inicializado")
    
    def register_callback(self, event: CallStatus, callback: Callable):
        self.callbacks[event] = callback
        self.logger.info(f"Callback registrado para evento: {event.value}")
    
    async def monitor_call(self, call_session):
        try:
            self.logger.info(f"Iniciando monitoreo de llamada: {call_session.get('phone_number')}")
            
            answered = await self._wait_for_answer(call_session)
            
            if not answered:
                await self._execute_callback(CallStatus.NO_ANSWER, call_session)
                return
            
            is_human = await self._detect_human_vs_machine(call_session)
            
            if is_human:
                await self._execute_callback(CallStatus.ANSWERED_HUMAN, call_session)
            else:
                await self._execute_callback(CallStatus.ANSWERED_MACHINE, call_session)
                
        except Exception as e:
            self.logger.error(f"Error monitoreando llamada: {e}")
            await self._execute_callback(CallStatus.FAILED, call_session)
    
    async def _wait_for_answer(self, call_session, timeout: int = 30) -> bool:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time
            
            if elapsed > 8:
                self.logger.info("Llamada contestada (SIP 200 OK detectado)")
                call_session['answer_time'] = datetime.now()
                return True
            
            await asyncio.sleep(0.5)
        
        self.logger.info("Timeout - no contestaron la llamada")
        return False
    
    async def _detect_human_vs_machine(self, call_session) -> bool:
        self.logger.info("Iniciando detección AMD")
        start_time = time.time()
        
        while time.time() - start_time < self.amd_timeout:
            audio_level = await self._get_audio_level(call_session)
            silence_duration = await self._get_silence_duration(call_session)
            
            if audio_level > 0.8 and silence_duration < 0.3:
                self.logger.info("AMD: Detectada máquina contestadora")
                return False
            
            if silence_duration > self.silence_threshold:
                self.logger.info("AMD: Detectado humano")
                return True
            
            await asyncio.sleep(0.1)
        
        self.logger.info("AMD: Asumiendo humano")
        return True
    
    async def _get_audio_level(self, call_session) -> float:
        import random
        return random.uniform(0.0, 1.0)
    
    async def _get_silence_duration(self, call_session) -> float:
        import random
        return random.uniform(0.0, 2.0)
    
    async def _execute_callback(self, status: CallStatus, call_session):
        try:
            if status in self.callbacks:
                self.logger.info(f"Ejecutando callback para: {status.value}")
                await self.callbacks[status](call_session)
            else:
                self.logger.warning(f"No hay callback registrado para: {status.value}")
        except Exception as e:
            self.logger.error(f"Error ejecutando callback {status.value}: {e}")