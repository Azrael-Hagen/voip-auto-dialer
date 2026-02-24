"""
Sistema básico de monitoreo para VoIP Auto Dialer
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque

try:
    import psutil
except ImportError:
    psutil = None

from core.logging_config import get_logger

@dataclass
class CallMetrics:
    call_id: str
    timestamp: datetime
    phone_number: str
    provider: str
    status: str
    duration: float
    cost: float
    error_message: Optional[str] = None

class SimpleMetricsCollector:
    """Recolector básico de métricas"""
    
    def __init__(self):
        self.logger = get_logger("metrics_collector")
        self.call_metrics = deque(maxlen=1000)
        self.start_time = datetime.now()
        
    async def start_collection(self):
        """Iniciar recolección"""
        self.logger.info("Iniciando recolección de métricas")
    
    def record_call(self, call_id: str, phone_number: str, provider: str, 
                   status: str, duration: float, cost: float, error_message: str = None):
        """Registrar métrica de llamada"""
        try:
            call_metric = CallMetrics(
                call_id=call_id,
                timestamp=datetime.now(),
                phone_number=phone_number,
                provider=provider,
                status=status,
                duration=duration,
                cost=cost,
                error_message=error_message
            )
            
            self.call_metrics.append(call_metric)
            self.logger.debug(f"Llamada registrada: {call_id} - {status}")
            
        except Exception as e:
            self.logger.error(f"Error registrando llamada: {e}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Obtener resumen de estadísticas"""
        try:
            if not self.call_metrics:
                return {"calls": {"total": 0, "success_rate": 0, "total_cost": 0}}
            
            total_calls = len(self.call_metrics)
            successful = len([c for c in self.call_metrics if c.status in ['completed', 'answered']])
            total_cost = sum(c.cost for c in self.call_metrics)
            
            # Métricas del sistema si psutil está disponible
            system_metrics = {}
            if psutil:
                system_metrics = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent
                }
            else:
                system_metrics = {
                    "cpu_percent": 0,
                    "memory_percent": 0,
                    "disk_percent": 0
                }
            
            return {
                "calls": {
                    "total": total_calls,
                    "success_rate": successful / total_calls if total_calls > 0 else 0,
                    "total_cost": total_cost
                },
                "system": system_metrics,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando estadísticas: {e}")
            return {}
    
    async def export_metrics(self, filepath: str, hours: int = 24):
        """Exportar métricas a archivo"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_metrics = [
                asdict(m) for m in self.call_metrics 
                if m.timestamp >= cutoff_time
            ]
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "period_hours": hours,
                "call_metrics": recent_metrics,
                "summary": self.get_summary_stats()
            }
            
            # Convertir datetime a string para JSON
            def datetime_converter(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=datetime_converter)
            
            self.logger.info(f"Métricas exportadas a {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exportando métricas: {e}")
    
    async def stop_collection(self):
        """Detener recolección"""
        self.logger.info("Recolección de métricas detenida")
