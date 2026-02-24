import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
from core.logging_config import get_logger

class CampaignStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"

class LeadResult(Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    VOICEMAIL = "voicemail"
    FAILED = "failed"
    TRANSFERRED = "transferred"

@dataclass
class Lead:
    id: str
    phone_number: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    company: str = ""
    attempts: int = 0
    max_attempts: int = 3
    result: LeadResult = LeadResult.PENDING
    last_call_time: Optional[datetime] = None
    next_call_time: Optional[datetime] = None
    total_talk_time: float = 0.0
    custom_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_data is None:
            self.custom_data = {}

@dataclass
class Campaign:
    id: str
    name: str
    description: str = ""
    status: CampaignStatus = CampaignStatus.DRAFT
    caller_id: str = ""
    max_concurrent_calls: int = 5
    calls_per_minute: int = 10
    calling_hours_start: str = "09:00"
    calling_hours_end: str = "17:00"
    calling_days: List[int] = None
    timezone: str = "UTC"
    leads: List[Lead] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    calls_made: int = 0
    calls_answered: int = 0
    total_leads: int = 0
    
    def __post_init__(self):
        if self.calling_days is None:
            self.calling_days = [0, 1, 2, 3, 4]  # Lun-Vie
        if self.leads is None:
            self.leads = []
        if self.created_at is None:
            self.created_at = datetime.now()

class CampaignManager:
    """Gestor de campañas de llamadas"""
    
    def __init__(self, data_dir: str = "campaigns"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.campaigns: Dict[str, Campaign] = {}
        self.logger = get_logger("campaign.manager")
    
    async def initialize(self):
        """Inicializar el manager y cargar campañas existentes"""
        try:
            await self._load_campaigns()
            self.logger.info(f"Campaign Manager inicializado con {len(self.campaigns)} campañas")
        except Exception as e:
            self.logger.error(f"Error inicializando Campaign Manager: {e}")
            raise
    
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Campaign:
        """Crear nueva campaña"""
        try:
            campaign_id = str(uuid.uuid4())
            
            campaign = Campaign(
                id=campaign_id,
                name=campaign_data["name"],
                description=campaign_data.get("description", ""),
                caller_id=campaign_data["caller_id"],
                max_concurrent_calls=campaign_data.get("max_concurrent_calls", 5),
                calls_per_minute=campaign_data.get("calls_per_minute", 10),
                calling_hours_start=campaign_data.get("calling_hours_start", "09:00"),
                calling_hours_end=campaign_data.get("calling_hours_end", "17:00"),
                calling_days=campaign_data.get("calling_days", [0, 1, 2, 3, 4]),
                timezone=campaign_data.get("timezone", "UTC")
            )
            
            self.campaigns[campaign_id] = campaign
            await self._save_campaign(campaign)
            
            self.logger.info(f"Campaña creada: {campaign.name} ({campaign_id})")
            return campaign
            
        except Exception as e:
            self.logger.error(f"Error creando campaña: {e}")
            raise
    
    async def import_leads(self, campaign_id: str, leads_data: List[Dict[str, Any]]) -> int:
        """Importar leads a una campaña"""
        try:
            if campaign_id not in self.campaigns:
                raise ValueError(f"Campaña {campaign_id} no encontrada")
            
            campaign = self.campaigns[campaign_id]
            imported_count = 0
            
            for lead_data in leads_data:
                if not lead_data.get("phone_number"):
                    continue
                
                lead = Lead(
                    id=str(uuid.uuid4()),
                    phone_number=lead_data["phone_number"],
                    first_name=lead_data.get("first_name", ""),
                    last_name=lead_data.get("last_name", ""),
                    email=lead_data.get("email", ""),
                    company=lead_data.get("company", ""),
                    custom_data=lead_data.get("custom_data", {})
                )
                
                campaign.leads.append(lead)
                imported_count += 1
            
            campaign.total_leads = len(campaign.leads)
            await self._save_campaign(campaign)
            
            self.logger.info(f"Importados {imported_count} leads a campaña {campaign.name}")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"Error importando leads: {e}")
            raise
    
    async def start_campaign(self, campaign_id: str) -> bool:
        """Iniciar campaña"""
        try:
            if campaign_id not in self.campaigns:
                return False
            
            campaign = self.campaigns[campaign_id]
            campaign.status = CampaignStatus.ACTIVE
            campaign.started_at = datetime.now()
            
            await self._save_campaign(campaign)
            
            self.logger.info(f"Campaña iniciada: {campaign.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando campaña {campaign_id}: {e}")
            return False
    
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pausar campaña"""
        try:
            if campaign_id not in self.campaigns:
                return False
            
            campaign = self.campaigns[campaign_id]
            campaign.status = CampaignStatus.PAUSED
            
            await self._save_campaign(campaign)
            
            self.logger.info(f"Campaña pausada: {campaign.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausando campaña {campaign_id}: {e}")
            return False
    
    async def resume_campaign(self, campaign_id: str) -> bool:
        """Reanudar campaña"""
        try:
            if campaign_id not in self.campaigns:
                return False
            
            campaign = self.campaigns[campaign_id]
            campaign.status = CampaignStatus.ACTIVE
            
            await self._save_campaign(campaign)
            
            self.logger.info(f"Campaña reanudada: {campaign.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reanudando campaña {campaign_id}: {e}")
            return False
    
    async def stop_campaign(self, campaign_id: str) -> bool:
        """Detener campaña"""
        try:
            if campaign_id not in self.campaigns:
                return False
            
            campaign = self.campaigns[campaign_id]
            campaign.status = CampaignStatus.STOPPED
            campaign.completed_at = datetime.now()
            
            await self._save_campaign(campaign)
            
            self.logger.info(f"Campaña detenida: {campaign.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo campaña {campaign_id}: {e}")
            return False
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Obtener campaña por ID"""
        return self.campaigns.get(campaign_id)
    
    def get_all_campaigns(self) -> List[Campaign]:
        """Obtener todas las campañas"""
        return list(self.campaigns.values())
    
    def get_active_campaigns(self) -> List[Campaign]:
        """Obtener campañas activas"""
        return [c for c in self.campaigns.values() if c.status == CampaignStatus.ACTIVE]
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Obtener estadísticas de campaña"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return {}
        
        completion_rate = 0
        if campaign.total_leads > 0:
            completion_rate = (campaign.calls_made / campaign.total_leads) * 100
        
        answer_rate = 0
        if campaign.calls_made > 0:
            answer_rate = (campaign.calls_answered / campaign.calls_made) * 100
        
        return {
            "completion_rate": completion_rate,
            "answer_rate": answer_rate,
            "calls_made": campaign.calls_made,
            "calls_answered": campaign.calls_answered,
            "total_leads": campaign.total_leads,
            "status": campaign.status.value
        }
    
    async def _load_campaigns(self):
        """Cargar campañas desde archivos"""
        try:
            for campaign_file in self.data_dir.glob("*.json"):
                with open(campaign_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convertir datos a objetos
                campaign_data = data.copy()
                
                # Convertir leads
                leads = []
                for lead_data in campaign_data.get("leads", []):
                    lead = Lead(**lead_data)
                    if lead.last_call_time:
                        lead.last_call_time = datetime.fromisoformat(lead.last_call_time)
                    if lead.next_call_time:
                        lead.next_call_time = datetime.fromisoformat(lead.next_call_time)
                    leads.append(lead)
                
                campaign_data["leads"] = leads
                campaign_data["status"] = CampaignStatus(campaign_data["status"])
                campaign_data["created_at"] = datetime.fromisoformat(campaign_data["created_at"])
                
                if campaign_data.get("started_at"):
                    campaign_data["started_at"] = datetime.fromisoformat(campaign_data["started_at"])
                if campaign_data.get("completed_at"):
                    campaign_data["completed_at"] = datetime.fromisoformat(campaign_data["completed_at"])
                
                campaign = Campaign(**campaign_data)
                self.campaigns[campaign.id] = campaign
                
        except Exception as e:
            self.logger.error(f"Error cargando campañas: {e}")
    
    async def _save_campaign(self, campaign: Campaign):
        """Guardar campaña en archivo"""
        try:
            # Convertir a diccionario serializable
            data = asdict(campaign)
            
            # Convertir enums y fechas
            data["status"] = campaign.status.value
            data["created_at"] = campaign.created_at.isoformat()
            
            if campaign.started_at:
                data["started_at"] = campaign.started_at.isoformat()
            if campaign.completed_at:
                data["completed_at"] = campaign.completed_at.isoformat()
            
            # Convertir leads
            leads_data = []
            for lead in campaign.leads:
                lead_data = asdict(lead)
                lead_data["result"] = lead.result.value
                if lead.last_call_time:
                    lead_data["last_call_time"] = lead.last_call_time.isoformat()
                if lead.next_call_time:
                    lead_data["next_call_time"] = lead.next_call_time.isoformat()
                leads_data.append(lead_data)
            
            data["leads"] = leads_data
            
            # Guardar archivo
            campaign_file = self.data_dir / f"{campaign.id}.json"
            with open(campaign_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando campaña {campaign.id}: {e}")
            raise
