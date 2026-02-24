"""
Provider Manager - Gestor centralizado de proveedores VoIP
"""
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pathlib import Path

from core.logging_config import get_logger
from providers.base_provider import BaseProvider, ProviderConfig, CallResult, CallStatus, ProviderStatus
from providers.implementations.mock_provider import MockProvider

class LoadBalanceStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_COST = "least_cost"
    LEAST_BUSY = "least_busy"

class ProviderManager:
    """Gestor centralizado de proveedores VoIP"""
    
    def __init__(self, config_path: str = "config/providers.json"):
        self.logger = get_logger("provider_manager")
        self.config_path = Path(config_path)
        self.providers: Dict[str, BaseProvider] = {}
        self.provider_configs: Dict[str, ProviderConfig] = {}
        self.load_balance_strategy = LoadBalanceStrategy.ROUND_ROBIN
        self.round_robin_index = 0
        self.health_check_interval = 60
        self.health_check_task = None
        
        # Estadísticas globales
        self.total_calls_today = 0
        self.total_cost_today = 0.0
        self.total_errors_today = 0
        
    async def initialize(self) -> bool:
        """Inicializar el gestor de proveedores"""
        try:
            self.logger.info("Inicializando Provider Manager...")
            
            # Cargar configuración
            await self._load_config()
            
            # Inicializar proveedores
            success_count = 0
            for name, config in self.provider_configs.items():
                if await self._initialize_provider(name, config):
                    success_count += 1
            
            if success_count == 0:
                self.logger.error("No se pudo inicializar ningún proveedor")
                return False
            
            self.logger.info(f"Provider Manager inicializado: {success_count}/{len(self.provider_configs)} proveedores activos")
            
            # Iniciar monitoreo de salud
            await self._start_health_monitoring()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando Provider Manager: {e}")
            return False
    
    async def _load_config(self):
        """Cargar configuración de proveedores"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                for provider_data in config_data.get("providers", []):
                    config = ProviderConfig(
                        name=provider_data["name"],
                        type=provider_data["type"],
                        enabled=provider_data.get("enabled", True),
                        cost_per_minute=provider_data.get("cost_per_minute", 0.01),
                        max_concurrent_calls=provider_data.get("max_concurrent_calls", 10),
                        timeout_seconds=provider_data.get("timeout_seconds", 30),
                        retry_attempts=provider_data.get("retry_attempts", 3),
                        config=provider_data.get("config", {})
                    )
                    self.provider_configs[config.name] = config
                
                # Configuración global
                self.load_balance_strategy = LoadBalanceStrategy(
                    config_data.get("load_balance_strategy", "round_robin")
                )
                self.health_check_interval = config_data.get("health_check_interval", 60)
                
            else:
                self.logger.warning(f"Archivo de configuración no encontrado: {self.config_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            return False
    
    async def _initialize_provider(self, name: str, config: ProviderConfig) -> bool:
        """Inicializar un proveedor específico"""
        try:
            if not config.enabled:
                self.logger.info(f"Proveedor {name} deshabilitado, saltando inicialización")
                return False
            
            self.logger.info(f"Inicializando proveedor: {name} ({config.type})")
            
            # Crear instancia del proveedor según el tipo
            if config.type == "mock":
                provider = MockProvider(config)
            else:
                self.logger.error(f"Tipo de proveedor no soportado: {config.type}")
                return False
            
            # Inicializar proveedor
            if await provider.initialize():
                self.providers[name] = provider
                self.logger.info(f"Proveedor {name} inicializado correctamente")
                return True
            else:
                self.logger.error(f"Error inicializando proveedor {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error inicializando proveedor {name}: {e}")
            return False
    
    async def make_call(self, phone_number: str, caller_id: str, 
                       campaign_data: Dict[str, Any] = None,
                       preferred_provider: str = None) -> CallResult:
        """Realizar llamada usando el mejor proveedor disponible"""
        try:
            # Seleccionar proveedor
            provider = await self._select_provider(preferred_provider)
            
            if not provider:
                self.logger.error("No hay proveedores disponibles para realizar la llamada")
                return CallResult(
                    call_id="no_provider",
                    status=CallStatus.FAILED,
                    error_message="No hay proveedores disponibles"
                )
            
            # Realizar llamada
            self.logger.info(f"Realizando llamada a {phone_number} usando proveedor {provider.config.name}")
            
            result = await provider.make_call(phone_number, caller_id, campaign_data)
            
            # Actualizar estadísticas
            self.total_calls_today += 1
            self.total_cost_today += result.cost
            
            if result.status == CallStatus.FAILED:
                self.total_errors_today += 1
            
            self.logger.info(f"Llamada completada: {result.call_id} - {result.status.value}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error realizando llamada: {e}")
            self.total_errors_today += 1
            
            return CallResult(
                call_id="error",
                status=CallStatus.FAILED,
                error_message=str(e)
            )
    
    async def _select_provider(self, preferred_provider: str = None) -> Optional[BaseProvider]:
        """Seleccionar el mejor proveedor según la estrategia configurada"""
        try:
            available_providers = [
                provider for provider in self.providers.values()
                if provider.can_make_call()
            ]
            
            if not available_providers:
                return None
            
            # Si se especifica un proveedor preferido
            if preferred_provider and preferred_provider in self.providers:
                provider = self.providers[preferred_provider]
                if provider.can_make_call():
                    return provider
            
            # Aplicar estrategia de balanceo de carga
            if self.load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
                return self._select_round_robin(available_providers)
            elif self.load_balance_strategy == LoadBalanceStrategy.LEAST_COST:
                return self._select_least_cost(available_providers)
            elif self.load_balance_strategy == LoadBalanceStrategy.LEAST_BUSY:
                return self._select_least_busy(available_providers)
            else:
                return available_providers[0]  # Fallback
                
        except Exception as e:
            self.logger.error(f"Error seleccionando proveedor: {e}")
            return None
    
    def _select_round_robin(self, providers: List[BaseProvider]) -> BaseProvider:
        """Selección round-robin"""
        if not providers:
            return None
        
        provider = providers[self.round_robin_index % len(providers)]
        self.round_robin_index += 1
        return provider
    
    def _select_least_cost(self, providers: List[BaseProvider]) -> BaseProvider:
        """Seleccionar proveedor con menor costo"""
        return min(providers, key=lambda p: p.config.cost_per_minute)
    
    def _select_least_busy(self, providers: List[BaseProvider]) -> BaseProvider:
        """Seleccionar proveedor menos ocupado"""
        return min(providers, key=lambda p: len(p.active_calls))
    
    async def _start_health_monitoring(self):
        """Iniciar monitoreo de salud de proveedores"""
        self.logger.info(f"Iniciando monitoreo de salud (intervalo: {self.health_check_interval}s)")
        
        async def health_check_loop():
            while True:
                try:
                    await self._perform_health_checks()
                    await asyncio.sleep(self.health_check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error en monitoreo de salud: {e}")
                    await asyncio.sleep(5)
        
        self.health_check_task = asyncio.create_task(health_check_loop())
    
    async def _perform_health_checks(self):
        """Realizar verificaciones de salud en todos los proveedores"""
        self.logger.debug("Realizando verificaciones de salud...")
        
        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                if not is_healthy:
                    self.logger.warning(f"Proveedor {name} falló health check")
                else:
                    self.logger.debug(f"Proveedor {name} health check OK")
            except Exception as e:
                self.logger.error(f"Error en health check de {name}: {e}")
    
    def get_provider_stats(self) -> List[Dict[str, Any]]:
        """Obtener estadísticas de todos los proveedores"""
        stats = []
        
        for name, provider in self.providers.items():
            provider_stats = provider.get_stats()
            stats.append(provider_stats)
        
        return stats
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas globales del sistema"""
        active_providers = len([p for p in self.providers.values() if p.status == ProviderStatus.AVAILABLE])
        total_active_calls = sum(len(p.active_calls) for p in self.providers.values())
        
        return {
            "total_providers": len(self.providers),
            "active_providers": active_providers,
            "total_calls_today": self.total_calls_today,
            "total_cost_today": self.total_cost_today,
            "total_errors_today": self.total_errors_today,
            "total_active_calls": total_active_calls,
            "load_balance_strategy": self.load_balance_strategy.value,
            "last_updated": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Cerrar el gestor de proveedores"""
        self.logger.info("Cerrando Provider Manager...")
        
        # Cancelar monitoreo de salud
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cerrar todos los proveedores
        for name, provider in self.providers.items():
            try:
                await provider.shutdown()
            except Exception as e:
                self.logger.error(f"Error cerrando proveedor {name}: {e}")
        
        self.providers.clear()
        self.logger.info("Provider Manager cerrado")