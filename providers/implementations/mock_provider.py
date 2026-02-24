"""
Proveedor simulado para pruebas
"""
import asyncio
import random
from datetime import datetime
from typing import Dict, Any, Optional

from providers.base_provider import BaseProvider, ProviderConfig, CallResult, CallStatus, ProviderStatus

class MockProvider(BaseProvider):
    """Proveedor simulado para pruebas"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.simulation_config = {
            "answer_rate": 0.7,
            "busy_rate": 0.15,
            "no_answer_rate": 0.10,
            "voicemail_rate": 0.05,
            "min_call_duration": 10,
            "max_call_duration": 300,
            "connection_delay": (1, 3),
            "simulate_real_timing": False
        }
        
        if "simulation" in self.config.config:
            self.simulation_config.update(self.config.config["simulation"])
    
    async def initialize(self) -> bool:
        """Inicializar proveedor mock"""
        try:
            self.logger.info(f"Inicializando proveedor mock: {self.config.name}")
            await asyncio.sleep(0.5)
            self.status = ProviderStatus.AVAILABLE
            self.logger.info(f"Proveedor mock {self.config.name} inicializado")
            return True
        except Exception as e:
            self.logger.error(f"Error inicializando proveedor mock: {e}")
            self.status = ProviderStatus.ERROR
            self.last_error = str(e)
            return False
    
    async def make_call(self, phone_number: str, caller_id: str, 
                       campaign_data: Dict[str, Any] = None) -> CallResult:
        """Simular llamada"""
        call_id = self._generate_call_id()
        
        try:
            self.logger.info(f"Iniciando llamada simulada {call_id} a {phone_number}")
            
            if not self.can_make_call():
                return CallResult(
                    call_id=call_id,
                    status=CallStatus.FAILED,
                    error_message="Proveedor no disponible"
                )
            
            # Registrar llamada activa
            call_start_time = datetime.now()
            self.active_calls[call_id] = {
                "phone_number": phone_number,
                "caller_id": caller_id,
                "start_time": call_start_time,
                "status": CallStatus.INITIATED,
                "campaign_data": campaign_data or {}
            }
            
            # Simular tiempo de conexión
            connection_delay = random.uniform(*self.simulation_config["connection_delay"])
            await asyncio.sleep(connection_delay)
            
            # Determinar resultado
            result_status = self._simulate_call_outcome()
            
            # Simular duración
            duration = 0.0
            answered_at = None
            completed_at = datetime.now()
            
            if result_status == CallStatus.ANSWERED:
                answered_at = datetime.now()
                
                if self.simulation_config["simulate_real_timing"]:
                    duration = random.uniform(
                        self.simulation_config["min_call_duration"],
                        self.simulation_config["max_call_duration"]
                    )
                    duration = min(duration, 5)  # Máximo 5s para pruebas
                    await asyncio.sleep(duration)
                else:
                    duration = random.uniform(
                        self.simulation_config["min_call_duration"],
                        self.simulation_config["max_call_duration"]
                    )
                
                completed_at = datetime.now()
                result_status = CallStatus.COMPLETED
            
            # Calcular costo
            cost = self._calculate_cost(duration)
            
            # Actualizar estadísticas
            self.total_calls_today += 1
            self.total_cost_today += cost
            
            # Remover de llamadas activas
            if call_id in self.active_calls:
                del self.active_calls[call_id]
            
            result = CallResult(
                call_id=call_id,
                status=result_status,
                duration=duration,
                cost=cost,
                answered_at=answered_at,
                completed_at=completed_at,
                provider_response={
                    "provider": self.config.name,
                    "phone_number": phone_number,
                    "caller_id": caller_id,
                    "simulation": True
                }
            )
            
            self.logger.info(f"Llamada {call_id} completada: {result_status.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error en llamada {call_id}: {e}")
            if call_id in self.active_calls:
                del self.active_calls[call_id]
            
            return CallResult(
                call_id=call_id,
                status=CallStatus.FAILED,
                error_message=str(e)
            )
    
    def _simulate_call_outcome(self) -> CallStatus:
        """Simular resultado de llamada"""
        rand = random.random()
        
        if rand < self.simulation_config["answer_rate"]:
            return CallStatus.ANSWERED
        elif rand < self.simulation_config["answer_rate"] + self.simulation_config["busy_rate"]:
            return CallStatus.BUSY
        elif rand < (self.simulation_config["answer_rate"] + 
                    self.simulation_config["busy_rate"] + 
                    self.simulation_config["voicemail_rate"]):
            return CallStatus.VOICEMAIL
        else:
            return CallStatus.NO_ANSWER
    
    async def hangup_call(self, call_id: str) -> bool:
        """Simular colgar llamada"""
        try:
            if call_id in self.active_calls:
                self.logger.info(f"Colgando llamada simulada {call_id}")
                del self.active_calls[call_id]
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error colgando llamada {call_id}: {e}")
            return False
