"""
Sistema de gestión de agentes para VoIP Auto Dialer
Maneja CRUD de agentes con integración de extensiones
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from core.logging_config import get_logger
from core.extension_manager import extension_manager

class AgentManager:
    """Gestor de agentes con operaciones CRUD"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Inicializar gestor de agentes
        
        Args:
            data_dir: Directorio para almacenar datos
        """
        self.logger = get_logger("agent_manager")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Archivo de datos
        self.agents_file = self.data_dir / "agents.json"
        
        # Cargar agentes existentes
        self.agents = self._load_agents()
        
        self.logger.info("Agent Manager inicializado")
    
    def _load_agents(self) -> Dict[str, Dict]:
        """Cargar agentes desde archivo JSON"""
        if self.agents_file.exists():
            try:
                with open(self.agents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error cargando agentes: {e}")
        
        # Crear agente de ejemplo si no existe ninguno
        default_agents = {
            "agent_001": {
                "id": "agent_001",
                "name": "Juan Pérez",
                "email": "juan@example.com",
                "phone": "+1234567890",
                "status": "offline",
                "created_at": datetime.now().isoformat(),
                "last_activity": None,
                "extension_info": None
            }
        }
        
        self._save_agents(default_agents)
        return default_agents
    
    def _save_agents(self, agents_data: Dict = None):
        """Guardar agentes a archivo JSON"""
        data_to_save = agents_data if agents_data is not None else self.agents
        
        try:
            with open(self.agents_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error guardando agentes: {e}")
    
    def create_agent(self, name: str, email: str, phone: str) -> Dict:
        """
        Crear nuevo agente
        
        Args:
            name: Nombre del agente
            email: Email del agente
            phone: Teléfono del agente
            
        Returns:
            Dict con información del agente creado
        """
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        agent_data = {
            "id": agent_id,
            "name": name,
            "email": email,
            "phone": phone,
            "status": "offline",
            "created_at": datetime.now().isoformat(),
            "last_activity": None,
            "extension_info": None
        }
        
        self.agents[agent_id] = agent_data
        self._save_agents()
        
        self.logger.info(f"Agente creado: {name} ({agent_id})")
        return agent_data
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Obtener agente por ID"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> Dict:
        """Obtener diccionario de todos los agentes"""
        return self.agents
    
    def update_agent(self, agent_id: str, **kwargs) -> Optional[Dict]:
        """
        Actualizar información de agente
        
        Args:
            agent_id: ID del agente
            **kwargs: Campos a actualizar
            
        Returns:
            Dict con información actualizada o None si no existe
        """
        if agent_id not in self.agents:
            self.logger.warning(f"Agente {agent_id} no encontrado para actualizar")
            return None
        
        # Campos permitidos para actualizar
        allowed_fields = ['name', 'email', 'phone', 'status', 'last_activity']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                self.agents[agent_id][field] = value
        
        # Actualizar timestamp de modificación
        self.agents[agent_id]['updated_at'] = datetime.now().isoformat()
        
        self._save_agents()
        
        self.logger.info(f"Agente {agent_id} actualizado")
        return self.agents[agent_id]
    
    def delete_agent(self, agent_id: str) -> bool:
        """
        Eliminar agente
        
        Args:
            agent_id: ID del agente
            
        Returns:
            True si se eliminó exitosamente
        """
        if agent_id not in self.agents:
            self.logger.warning(f"Agente {agent_id} no encontrado para eliminar")
            return False
        
        # Liberar extensión si tiene una asignada
        if self.agents[agent_id].get('extension_info'):
            extension_manager.release_extension(agent_id)
        
        # Eliminar agente
        agent_name = self.agents[agent_id]['name']
        del self.agents[agent_id]
        self._save_agents()
        
        self.logger.info(f"Agente eliminado: {agent_name} ({agent_id})")
        return True
    

    def assign_extension(self, agent_id):
        """Asignar extensión disponible a un agente"""
        try:
            # Obtener extensión disponible
            available_extensions = extension_manager.get_available_extensions()
            if not available_extensions:
                return None
            
            extension_num = available_extensions[0]
            
            # Asignar extensión
            result = extension_manager.assign_extension(extension_num, agent_id)
            if result:
                # Actualizar agente
                if agent_id in self.agents:
                    self.agents[agent_id]["extension_info"] = {
                        "extension": extension_num,
                        "password": result.get("password", ""),
                        "status": "assigned",
                        "assigned_at": datetime.now().isoformat()
                    }
                    self._save_agents()
                    self.logger.info(f"Extensión {extension_num} asignada a agente {agent_id}")
                    return result
            return None
        except Exception as e:
            self.logger.error(f"Error asignando extensión: {e}")
            return None


# Crear instancia global del manager
agent_manager = AgentManager()
