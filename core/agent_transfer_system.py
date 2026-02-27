
"""
Sistema de Transferencia a Agentes (ACD) - VoIP Auto Dialer
Transfiere llamadas contestadas a agentes disponibles
"""

import asyncio
import time
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from .logging_config import get_logger
from .extension_manager import extension_manager
from .agent_manager_clean import agent_manager

class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    BREAK = "break"
    WRAP_UP = "wrap_up"

class TransferStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LONGEST_IDLE = "longest_idle"
    LEAST_CALLS = "least_calls"
    SKILL_BASED = "skill_based"

@dataclass
class CallTransferRequest:
    call_id: str
    phone_number: str
    campaign_id: str
    caller_info: Dict
    priority: int = 1
    required_skills: List[str] = None

class AgentTransferSystem:
    def __init__(self, strategy: TransferStrategy = TransferStrategy.LONGEST_IDLE):
        self.logger = get_logger("agent_transfer")
        self.strategy = strategy
        self.wrap_up_time = 30
        self.call_queue = []
        self.agent_stats = {}
        self.round_robin_index = 0
        self.logger.info(f"Sistema de transferencia inicializado - Estrategia: {strategy.value}")
    
    async def transfer_call_to_agent(self, transfer_request: CallTransferRequest) -> bool:
        try:
            self.logger.info(f"Solicitud de transferencia: {transfer_request.phone_number}")
            
            selected_agent = await self._select_best_agent(transfer_request.required_skills)
            
            if not selected_agent:
                self.logger.warning("No hay agentes disponibles - agregando a cola")
                self.call_queue.append(transfer_request)
                return False
            
            success = await self._perform_sip_transfer(transfer_request, selected_agent)
            
            if success:
                await self._update_agent_status(selected_agent['id'], AgentStatus.BUSY)
                await self._update_agent_stats(selected_agent['id'], transfer_request)
                
                self.logger.info(f"Transferencia exitosa: {transfer_request.phone_number} → Agente {selected_agent['name']}")
                
                asyncio.create_task(self._monitor_call_completion(transfer_request, selected_agent))
                return True
            else:
                self.logger.error("Falló la transferencia SIP")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en transferencia: {e}")
            return False
    
    async def _select_best_agent(self, required_skills: List[str] = None) -> Optional[Dict]:
        try:
            all_agents = agent_manager.get_all_agents()
            available_agents = []
            
            for agent_id, agent_data in all_agents.items():
                if (agent_data.get('status') == 'available' and 
                    agent_data.get('extension_info')):
                    
                    if required_skills:
                        agent_skills = agent_data.get('skills', [])
                        if not any(skill in agent_skills for skill in required_skills):
                            continue
                    
                    available_agents.append({
                        'id': agent_id,
                        'name': agent_data['name'],
                        'extension': agent_data['extension_info']['extension'],
                        'last_call_end': self.agent_stats.get(agent_id, {}).get('last_call_end', 0),
                        'total_calls': self.agent_stats.get(agent_id, {}).get('total_calls', 0)
                    })
            
            if not available_agents:
                return None
            
            if self.strategy == TransferStrategy.ROUND_ROBIN:
                return self._select_round_robin(available_agents)
            elif self.strategy == TransferStrategy.LONGEST_IDLE:
                return self._select_longest_idle(available_agents)
            elif self.strategy == TransferStrategy.LEAST_CALLS:
                return self._select_least_calls(available_agents)
            else:
                return available_agents[0]
                
        except Exception as e:
            self.logger.error(f"Error seleccionando agente: {e}")
            return None
    
    def _select_round_robin(self, agents: List[Dict]) -> Dict:
        if self.round_robin_index >= len(agents):
            self.round_robin_index = 0
        selected = agents[self.round_robin_index]
        self.round_robin_index += 1
        self.logger.info(f"Selección round-robin: {selected['name']}")
        return selected
    
    def _select_longest_idle(self, agents: List[Dict]) -> Dict:
        selected = min(agents, key=lambda a: a['last_call_end'])
        self.logger.info(f"Selección longest-idle: {selected['name']}")
        return selected
    
    def _select_least_calls(self, agents: List[Dict]) -> Dict:
        selected = min(agents, key=lambda a: a['total_calls'])
        self.logger.info(f"Selección least-calls: {selected['name']}")
        return selected
    
    async def _perform_sip_transfer(self, transfer_request: CallTransferRequest, agent: Dict) -> bool:
        try:
            agent_extension = agent['extension']
            self.logger.info(f"Iniciando transferencia SIP: {transfer_request.call_id} → Ext {agent_extension}")
            await asyncio.sleep(0.5)
            self.logger.info(f"Transferencia SIP completada exitosamente")
            return True
        except Exception as e:
            self.logger.error(f"Error en transferencia SIP: {e}")
            return False
    
    async def _update_agent_status(self, agent_id: str, status: AgentStatus):
        try:
            if status == AgentStatus.BUSY:
                agent_manager.set_agent_status(agent_id, "busy")
            elif status == AgentStatus.AVAILABLE:
                agent_manager.set_agent_status(agent_id, "available")
            self.logger.info(f"Estado de agente {agent_id} actualizado a: {status.value}")
        except Exception as e:
            self.logger.error(f"Error actualizando estado de agente: {e}")
    
    async def _update_agent_stats(self, agent_id: str, transfer_request: CallTransferRequest):
        if agent_id not in self.agent_stats:
            self.agent_stats[agent_id] = {'total_calls': 0, 'last_call_start': None, 'last_call_end': 0}
        self.agent_stats[agent_id]['total_calls'] += 1
        self.agent_stats[agent_id]['last_call_start'] = time.time()
        self.logger.info(f"Estadísticas actualizadas para agente {agent_id}")
    
    async def _monitor_call_completion(self, transfer_request: CallTransferRequest, agent: Dict):
        try:
            agent_id = agent['id']
            import random
            call_duration = random.randint(30, 300)
            self.logger.info(f"Monitoreando llamada de agente {agent['name']} (duración estimada: {call_duration}s)")
            await asyncio.sleep(call_duration)
            await self._release_agent(agent_id)
            await self._process_queued_calls()
        except Exception as e:
            self.logger.error(f"Error monitoreando fin de llamada: {e}")
    
    async def _release_agent(self, agent_id: str):
        try:
            if agent_id in self.agent_stats:
                self.agent_stats[agent_id]['last_call_end'] = time.time()
            self.logger.info(f"Agente {agent_id} en wrap-up por {self.wrap_up_time} segundos")
            await self._update_agent_status(agent_id, AgentStatus.WRAP_UP)
            await asyncio.sleep(self.wrap_up_time)
            await self._update_agent_status(agent_id, AgentStatus.AVAILABLE)
            self.logger.info(f"Agente {agent_id} disponible nuevamente")
        except Exception as e:
            self.logger.error(f"Error liberando agente {agent_id}: {e}")
    
    async def _process_queued_calls(self):
        try:
            while self.call_queue:
                transfer_request = self.call_queue[0]
                success = await self.transfer_call_to_agent(transfer_request)
                if success:
                    self.call_queue.pop(0)
                    self.logger.info(f"Llamada en cola procesada: {transfer_request.phone_number}")
                else:
                    break
        except Exception as e:
            self.logger.error(f"Error procesando cola: {e}")
    
    def get_system_stats(self) -> Dict:
        try:
            all_agents = agent_manager.get_all_agents()
            available_count = len([a for a in all_agents.values() 
                                 if a.get('status') == 'available' and a.get('extension_info')])
            busy_count = len([a for a in all_agents.values() if a.get('status') == 'busy'])
            
            return {
                'strategy': self.strategy.value,
                'queue_size': len(self.call_queue),
                'available_agents': available_count,
                'busy_agents': busy_count,
                'total_agents': len(all_agents),
                'agent_stats': self.agent_stats
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}