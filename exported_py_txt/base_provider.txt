"""
Clase base para proveedores VoIP
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import uuid

from core.logging_config import get_logger

class CallStatus(Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    FAILED = "failed"
    COMPLETED = "completed"
    VOICEMAIL = "voicemail"

class ProviderStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class CallResult:
    call_id: str
    status: CallStatus
    duration: float = 0.0
    cost: float = 0.0
    provider_response: Dict[str, Any] = None
    error_message: Optional[str] = None
    answered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.provider_response is None:
            self.provider_response = {}

@dataclass
class ProviderConfig:
    name: str
    type: str
    enabled: bool = True
    cost_per_minute: float = 0.01
    max_concurrent_calls: int = 100
    timeout_seconds: int = 30
    retry_attempts: int = 3
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

class BaseProvider(ABC):
    """Clase base para todos los proveedores VoIP"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = get_logger(f"provider.{config.name}")
        self.status = ProviderStatus.UNAVAILABLE
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.total_calls_today = 0
        self.total_cost_today = 0.0
        self.last_error: Optional[str] = None
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Inicializar el proveedor"""
        pass
    
    @abstractmethod
    async def make_call(self, phone_number: str, caller_id: str, 
                       campaign_data: Dict[str, Any] = None) -> CallResult:
        """Realizar llamada"""
        pass
    
    @abstractmethod
    async def hangup_call(self, call_id: str) -> bool:
        """Colgar llamada"""
        pass
    
    def can_make_call(self) -> bool:
        """Verificar si puede hacer una llamada"""
        return (
            self.config.enabled and
            self.status == ProviderStatus.AVAILABLE and
            len(self.active_calls) < self.config.max_concurrent_calls
        )
    
    def _generate_call_id(self) -> str:
        """Generar ID único para llamada"""
        return f"{self.config.name}_{uuid.uuid4().hex[:8]}"
    
    def _calculate_cost(self, duration_seconds: float) -> float:
        """Calcular costo de llamada"""
        duration_minutes = duration_seconds / 60.0
        return duration_minutes * self.config.cost_per_minute
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del proveedor"""
        return {
            "name": self.config.name,
            "type": self.config.type,
            "status": self.status.value,
            "active_calls": len(self.active_calls),
            "max_concurrent_calls": self.config.max_concurrent_calls,
            "total_calls_today": self.total_calls_today,
            "total_cost_today": self.total_cost_today,
            "cost_per_minute": self.config.cost_per_minute,
            "last_error": self.last_error,
            "enabled": self.config.enabled
        }
    
    async def health_check(self) -> bool:
        """Verificar salud del proveedor"""
        try:
            return self.status == ProviderStatus.AVAILABLE
        except Exception as e:
            self.logger.error(f"Error en health check: {e}")
            self.last_error = str(e)
            self.status = ProviderStatus.ERROR
            return False
    
    async def shutdown(self):
        """Cerrar proveedor"""
        self.logger.info(f"Cerrando proveedor {self.config.name}")
        self.status = ProviderStatus.UNAVAILABLE
        self.active_calls.clear()
