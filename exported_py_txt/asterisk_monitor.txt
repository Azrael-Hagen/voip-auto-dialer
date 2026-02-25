"""
Monitor en tiempo real de Asterisk
Obtiene datos directamente del sistema Asterisk para el dashboard profesional
"""

import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from core.logging_config import get_logger

class AsteriskMonitor:
    def __init__(self):
        self.logger = get_logger("asterisk_monitor")
        self.last_update = None
        self.cached_data = {}
        self.cache_duration = 30  # Cache por 30 segundos
        
    def get_realtime_data(self) -> Dict:
        """Obtener datos en tiempo real de Asterisk con cache"""
        try:
            # Verificar cache
            current_time = time.time()
            if (self.last_update and 
                current_time - self.last_update < self.cache_duration and 
                self.cached_data):
                return self.cached_data
            
            # Obtener datos frescos
            data = self._collect_asterisk_data()
            
            # Actualizar cache
            self.cached_data = data
            self.last_update = current_time
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos en tiempo real: {e}")
            return self._get_fallback_data()
    
    def _collect_asterisk_data(self) -> Dict:
        """Recopilar datos de Asterisk"""
        data = {
            "system_status": "Unknown",
            "total_extensions": 0,
            "active_calls": 0,
            "uptime": "Unknown",
            "last_update": datetime.now().isoformat()
        }
        
        try:
            # Verificar si Asterisk está corriendo
            system_status = self._check_asterisk_status()
            data["system_status"] = system_status
            
            if system_status == "Online":
                # Obtener número de extensiones
                data["total_extensions"] = self._get_total_extensions()
                
                # Obtener llamadas activas
                data["active_calls"] = self._get_active_calls()
                
                # Obtener uptime
                data["uptime"] = self._get_asterisk_uptime()
            
        except Exception as e:
            self.logger.error(f"Error recopilando datos de Asterisk: {e}")
            data["system_status"] = "Error"
        
        return data
    
    def _check_asterisk_status(self) -> str:
        """Verificar si Asterisk está corriendo sin sudo"""
        try:
            # Verificar proceso Asterisk sin sudo
            result = subprocess.run([
                'pgrep', '-f', 'asterisk'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                return "Online"
            else:
                return "Offline"
                
        except subprocess.TimeoutExpired:
            return "Timeout"
        except Exception as e:
            self.logger.error(f"Error verificando estado de Asterisk: {e}")
            return "Error"
    
    def _get_total_extensions(self) -> int:
        """Obtener número total de extensiones desde archivos locales"""
        try:
            # Leer desde extension_manager en lugar de Asterisk directamente
            from core.extension_manager import extension_manager
            stats = extension_manager.get_extension_stats()
            return stats.get('total', 0)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo extensiones: {e}")
            return 0
    
    def _get_active_calls(self) -> int:
        """Obtener número de llamadas activas (simulado por ahora)"""
        try:
            # Por ahora retornamos 0, se puede implementar después
            return 0
                
        except Exception as e:
            self.logger.error(f"Error obteniendo llamadas activas: {e}")
            return 0
    
    def _get_asterisk_uptime(self) -> str:
        """Obtener uptime simulado"""
        try:
            # Verificar si el proceso está corriendo
            result = subprocess.run([
                'pgrep', '-f', 'asterisk'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return "Sistema activo"
            else:
                return "Sistema inactivo"
                
        except Exception as e:
            self.logger.error(f"Error obteniendo uptime: {e}")
            return "Error"
    
    def _get_fallback_data(self) -> Dict:
        """Datos de respaldo en caso de error"""
        return {
            "system_status": "Error",
            "total_extensions": 0,
            "active_calls": 0,
            "uptime": "Unknown",
            "last_update": datetime.now().isoformat(),
            "error": True
        }
    
    def get_extension_status(self, extension: str) -> Dict:
        """Obtener estado específico de una extensión"""
        try:
            # Por ahora retornamos estado simulado
            return {
                "status": "unknown",
                "extension": extension,
                "details": "Estado no disponible sin permisos sudo"
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de extensión {extension}: {e}")
            return {"status": "error", "extension": extension, "error": str(e)}

# Instancia global
asterisk_monitor = AsteriskMonitor()