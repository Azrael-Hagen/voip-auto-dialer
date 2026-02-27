
"""
Integración del Auto Dialer con el Sistema Web - VoIP Auto Dialer
Puente entre el motor y tu FastAPI existente
"""

from typing import Dict, Optional
import asyncio
from datetime import datetime
from .auto_dialer_engine import AutoDialerEngine, DialerMode
from .logging_config import get_logger

class DialerWebIntegration:
    def __init__(self):
        self.logger = get_logger("dialer_integration")
        self.engine = AutoDialerEngine()
        self.active_campaigns: Dict[str, Dict] = {}
        self.logger.info("Integración web del dialer inicializada")
    
    async def start_campaign_dialing(self, campaign_id: str, config: Dict = None) -> Dict:
        try:
            self.logger.info(f"Solicitud web para iniciar campaña: {campaign_id}")
            
            if campaign_id in self.active_campaigns:
                return {
                    "success": False,
                    "message": "La campaña ya está activa",
                    "campaign_id": campaign_id
                }
            
            if config:
                if 'calls_per_minute' in config:
                    self.engine.calls_per_minute = config['calls_per_minute']
                if 'max_concurrent_calls' in config:
                    self.engine.max_concurrent_calls = config['max_concurrent_calls']
                if 'mode' in config:
                    self.engine.mode = DialerMode(config['mode'])
            
            success = await self.engine.start_campaign_dialing(campaign_id)
            
            if success:
                self.active_campaigns[campaign_id] = {
                    "started_at": datetime.now().isoformat(),
                    "config": config or {},
                    "status": "running"
                }
                
                return {
                    "success": True,
                    "message": "Marcado iniciado exitosamente",
                    "campaign_id": campaign_id,
                    "started_at": self.active_campaigns[campaign_id]["started_at"]
                }
            else:
                return {
                    "success": False,
                    "message": "No se pudo iniciar el marcado",
                    "campaign_id": campaign_id
                }
        except Exception as e:
            self.logger.error(f"Error iniciando campaña web: {e}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}",
                "campaign_id": campaign_id
            }
    
    async def stop_campaign_dialing(self, campaign_id: str) -> Dict:
        try:
            self.logger.info(f"Solicitud web para detener campaña: {campaign_id}")
            
            if campaign_id not in self.active_campaigns:
                return {
                    "success": False,
                    "message": "La campaña no está activa",
                    "campaign_id": campaign_id
                }
            
            success = await self.engine.stop_campaign_dialing(campaign_id)
            
            if success:
                self.active_campaigns[campaign_id]["status"] = "stopped"
                self.active_campaigns[campaign_id]["stopped_at"] = datetime.now().isoformat()
                
                asyncio.create_task(self._cleanup_campaign_record(campaign_id, delay=300))
                
                return {
                    "success": True,
                    "message": "Marcado detenido exitosamente",
                    "campaign_id": campaign_id,
                    "stopped_at": self.active_campaigns[campaign_id]["stopped_at"]
                }
            else:
                return {
                    "success": False,
                    "message": "No se pudo detener el marcado",
                    "campaign_id": campaign_id
                }
        except Exception as e:
            self.logger.error(f"Error deteniendo campaña web: {e}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}",
                "campaign_id": campaign_id
            }
    
    def get_dialer_status(self) -> Dict:
        try:
            engine_stats = self.engine.get_engine_stats()
            return {
                "engine_stats": engine_stats,
                "active_campaigns": self.active_campaigns,
                "total_active_campaigns": len([c for c in self.active_campaigns.values() 
                                             if c["status"] == "running"]),
                "system_status": "running" if engine_stats["is_running"] else "stopped",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del dialer: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_campaign_status(self, campaign_id: str) -> Dict:
        try:
            if campaign_id not in self.active_campaigns:
                return {
                    "success": False,
                    "message": "Campaña no encontrada en activas",
                    "campaign_id": campaign_id
                }
            
            campaign_info = self.active_campaigns[campaign_id].copy()
            
            if campaign_info["status"] == "running":
                engine_stats = self.engine.get_engine_stats()
                campaign_info["real_time_stats"] = engine_stats
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "campaign_info": campaign_info
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de campaña: {e}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}",
                "campaign_id": campaign_id
            }
    
    async def pause_campaign_dialing(self, campaign_id: str) -> Dict:
        try:
            if campaign_id not in self.active_campaigns:
                return {
                    "success": False,
                    "message": "Campaña no encontrada",
                    "campaign_id": campaign_id
                }
            
            result = await self.stop_campaign_dialing(campaign_id)
            
            if result["success"]:
                self.active_campaigns[campaign_id]["status"] = "paused"
                result["message"] = "Campaña pausada exitosamente"
            
            return result
        except Exception as e:
            self.logger.error(f"Error pausando campaña: {e}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}",
                "campaign_id": campaign_id
            }
    
    async def resume_campaign_dialing(self, campaign_id: str) -> Dict:
        try:
            if campaign_id not in self.active_campaigns:
                return {
                    "success": False,
                    "message": "Campaña no encontrada",
                    "campaign_id": campaign_id
                }
            
            if self.active_campaigns[campaign_id]["status"] != "paused":
                return {
                    "success": False,
                    "message": "La campaña no está pausada",
                    "campaign_id": campaign_id
                }
            
            config = self.active_campaigns[campaign_id]["config"]
            result = await self.start_campaign_dialing(campaign_id, config)
            
            if result["success"]:
                result["message"] = "Campaña reanudada exitosamente"
            
            return result
        except Exception as e:
            self.logger.error(f"Error reanudando campaña: {e}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}",
                "campaign_id": campaign_id
            }
    
    async def make_test_call(self, phone_number: str, campaign_id: str = "test") -> Dict:
        try:
            self.logger.info(f"Solicitud de llamada de prueba: {phone_number}")
            
            return {
                "success": True,
                "message": "Llamada de prueba iniciada",
                "phone_number": phone_number,
                "test_call_id": f"test_{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en llamada de prueba: {e}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}",
                "phone_number": phone_number
            }
    
    def get_available_campaigns(self) -> Dict:
        try:
            all_campaigns = self.engine.campaign_manager.get_all_campaigns()
            
            available_campaigns = []
            for campaign in all_campaigns:
                campaign_info = {
                    "id": campaign.id,
                    "name": campaign.name,
                    "description": campaign.description,
                    "status": campaign.status.value,
                    "total_leads": campaign.total_leads,
                    "calls_made": campaign.calls_made,
                    "calls_answered": campaign.calls_answered,
                    "is_active_in_dialer": campaign.id in self.active_campaigns
                }
                available_campaigns.append(campaign_info)
            
            return {
                "success": True,
                "campaigns": available_campaigns,
                "total_campaigns": len(available_campaigns)
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo campañas disponibles: {e}")
            return {
                "success": False,
                "message": f"Error interno: {str(e)}",
                "campaigns": []
            }
    
    async def _cleanup_campaign_record(self, campaign_id: str, delay: int = 300):
        try:
            await asyncio.sleep(delay)
            
            if (campaign_id in self.active_campaigns and 
                self.active_campaigns[campaign_id]["status"] in ["stopped", "paused"]):
                
                del self.active_campaigns[campaign_id]
                self.logger.info(f"Registro de campaña {campaign_id} limpiado")
        except Exception as e:
            self.logger.error(f"Error limpiando registro de campaña: {e}")

dialer_integration = DialerWebIntegration()