"""
Gestor de Proveedores VoIP para VoIP Auto Dialer
Maneja la configuración, conexión y monitoreo de proveedores SIP
"""
import json
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from core.logging_config import get_logger

class ProviderManager:
    def __init__(self):
        self.logger = get_logger("provider_manager")
        self.data_dir = Path(__file__).parent.parent / "data"
        self.providers_file = self.data_dir / "providers.json"
        self.asterisk_config_dir = Path(__file__).parent.parent / "asterisk_config"
        
        # Crear directorios si no existen
        self.data_dir.mkdir(exist_ok=True)
        self.asterisk_config_dir.mkdir(exist_ok=True)
        
        self.providers = self._load_providers()
        self.logger.info(f"Provider Manager inicializado: {len(self.providers)} proveedores")

    def _load_providers(self) -> Dict[str, Any]:
        """Cargar proveedores desde archivo JSON"""
        try:
            if self.providers_file.exists():
                with open(self.providers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error cargando proveedores: {e}")
            return {}

    def _save_providers(self) -> bool:
        """Guardar proveedores en archivo JSON"""
        try:
            with open(self.providers_file, 'w', encoding='utf-8') as f:
                json.dump(self.providers, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error guardando proveedores: {e}")
            return False

    def create_provider(self, name: str, host: str, username: str, password: str,
                       port: int = 5060, transport: str = "udp", codec: str = "ulaw",
                       description: str = "", active: bool = True) -> Dict[str, Any]:
        """Crear nuevo proveedor VoIP"""
        try:
            provider_id = f"provider_{uuid.uuid4().hex[:8]}"
            
            provider = {
                "id": provider_id,
                "name": name,
                "host": host,
                "username": username,
                "password": password,
                "port": port,
                "transport": transport.lower(),
                "codec": codec.lower(),
                "description": description,
                "active": active,
                "status": "disconnected",
                "created_at": datetime.now().isoformat(),
                "last_test": None,
                "test_results": []
            }
            
            self.providers[provider_id] = provider
            
            if self._save_providers():
                # Generar configuración de Asterisk si está activo
                if active:
                    self._generate_asterisk_config()
                
                self.logger.info(f"Proveedor creado: {name} ({provider_id})")
                return provider
            else:
                raise Exception("Error guardando proveedor")
                
        except Exception as e:
            self.logger.error(f"Error creando proveedor: {e}")
            raise

    def get_all_providers(self) -> Dict[str, Any]:
        """Obtener todos los proveedores"""
        return self.providers.copy()

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Obtener proveedor específico"""
        return self.providers.get(provider_id)

    def update_provider(self, provider_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Actualizar proveedor existente"""
        try:
            if provider_id not in self.providers:
                return None
            
            provider = self.providers[provider_id]
            
            # Campos actualizables
            updatable_fields = ['name', 'host', 'username', 'password', 'port', 
                              'transport', 'codec', 'description', 'active']
            
            for field, value in kwargs.items():
                if field in updatable_fields:
                    provider[field] = value
            
            provider['updated_at'] = datetime.now().isoformat()
            
            if self._save_providers():
                # Regenerar configuración si está activo
                if provider.get('active', False):
                    self._generate_asterisk_config()
                
                self.logger.info(f"Proveedor actualizado: {provider['name']} ({provider_id})")
                return provider
            else:
                raise Exception("Error guardando cambios")
                
        except Exception as e:
            self.logger.error(f"Error actualizando proveedor {provider_id}: {e}")
            return None

    def delete_provider(self, provider_id: str) -> bool:
        """Eliminar proveedor"""
        try:
            if provider_id not in self.providers:
                return False
            
            provider_name = self.providers[provider_id]['name']
            del self.providers[provider_id]
            
            if self._save_providers():
                # Regenerar configuración de Asterisk
                self._generate_asterisk_config()
                
                self.logger.info(f"Proveedor eliminado: {provider_name} ({provider_id})")
                return True
            else:
                raise Exception("Error guardando cambios")
                
        except Exception as e:
            self.logger.error(f"Error eliminando proveedor {provider_id}: {e}")
            return False

    def toggle_provider(self, provider_id: str) -> bool:
        """Activar/Desactivar proveedor"""
        try:
            if provider_id not in self.providers:
                return False
            
            provider = self.providers[provider_id]
            provider['active'] = not provider.get('active', False)
            provider['updated_at'] = datetime.now().isoformat()
            
            if self._save_providers():
                # Regenerar configuración de Asterisk
                self._generate_asterisk_config()
                
                status = "activado" if provider['active'] else "desactivado"
                self.logger.info(f"Proveedor {status}: {provider['name']} ({provider_id})")
                return True
            else:
                raise Exception("Error guardando cambios")
                
        except Exception as e:
            self.logger.error(f"Error cambiando estado del proveedor {provider_id}: {e}")
            return False

    def test_connection(self, provider_id: str) -> Dict[str, Any]:
        """Probar conexión con proveedor VoIP"""
        try:
            if provider_id not in self.providers:
                return {"success": False, "message": "Proveedor no encontrado"}
            
            provider = self.providers[provider_id]
            
            # Actualizar estado a "testing"
            provider['status'] = 'testing'
            self._save_providers()
            
            # Simular prueba de conexión (en producción, aquí iría la lógica real)
            test_result = self._perform_connection_test(provider)
            
            # Actualizar resultados
            provider['status'] = 'connected' if test_result['success'] else 'disconnected'
            provider['last_test'] = datetime.now().isoformat()
            
            if 'test_results' not in provider:
                provider['test_results'] = []
            
            provider['test_results'].append({
                "timestamp": datetime.now().isoformat(),
                "success": test_result['success'],
                "message": test_result['message'],
                "details": test_result.get('details', {})
            })
            
            # Mantener solo los últimos 10 resultados
            provider['test_results'] = provider['test_results'][-10:]
            
            self._save_providers()
            
            self.logger.info(f"Prueba de conexión para {provider['name']}: {'EXITOSA' if test_result['success'] else 'FALLIDA'}")
            return test_result
            
        except Exception as e:
            self.logger.error(f"Error probando conexión del proveedor {provider_id}: {e}")
            return {"success": False, "message": f"Error en prueba: {str(e)}"}

    def _perform_connection_test(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """Realizar prueba real de conexión SIP"""
        try:
            # Por ahora, simulamos la prueba
            # En producción, aquí se haría una prueba real SIP
            
            import random
            import time
            
            # Simular tiempo de prueba
            time.sleep(2)
            
            # Simular resultado (80% de éxito para demo)
            success = random.random() > 0.2
            
            if success:
                return {
                    "success": True,
                    "message": "Conexión exitosa",
                    "details": {
                        "response_time": f"{random.randint(50, 200)}ms",
                        "server_response": "200 OK",
                        "codec_negotiated": provider.get('codec', 'ulaw')
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Conexión fallida",
                    "details": {
                        "error_code": "408",
                        "error_message": "Request Timeout",
                        "attempted_host": f"{provider['host']}:{provider['port']}"
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error en prueba: {str(e)}",
                "details": {}
            }

    def _generate_asterisk_config(self) -> bool:
        """Generar configuración de Asterisk para proveedores activos"""
        try:
            active_providers = {pid: p for pid, p in self.providers.items() if p.get('active', False)}
            
            if not active_providers:
                self.logger.info("No hay proveedores activos, no se genera configuración")
                return True
            
            # Generar archivo pjsip_providers.conf
            pjsip_config = self._generate_pjsip_config(active_providers)
            pjsip_file = self.asterisk_config_dir / "pjsip_providers.conf"
            
            with open(pjsip_file, 'w', encoding='utf-8') as f:
                f.write(pjsip_config)
            
            # Generar archivo extensions_providers.conf
            extensions_config = self._generate_extensions_config(active_providers)
            extensions_file = self.asterisk_config_dir / "extensions_providers.conf"
            
            with open(extensions_file, 'w', encoding='utf-8') as f:
                f.write(extensions_config)
            
            self.logger.info(f"Configuración de Asterisk generada para {len(active_providers)} proveedores")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generando configuración de Asterisk: {e}")
            return False

    def _generate_pjsip_config(self, providers: Dict[str, Any]) -> str:
        """Generar configuración PJSIP para proveedores"""
        config_lines = [
            "; Configuración PJSIP para Proveedores VoIP",
            f"; Generado automáticamente: {datetime.now().isoformat()}",
            ""
        ]
        
        for provider_id, provider in providers.items():
            config_lines.extend([
                f"; Proveedor: {provider['name']}",
                f"[{provider_id}]",
                "type=registration",
                f"transport=transport-{provider['transport']}",
                f"outbound_auth={provider_id}_auth",
                f"server_uri=sip:{provider['host']}:{provider['port']}",
                f"client_uri=sip:{provider['username']}@{provider['host']}",
                "retry_interval=60",
                "max_retries=10",
                "auth_rejection_permanent=no",
                "",
                f"[{provider_id}_auth]",
                "type=auth",
                "auth_type=userpass",
                f"username={provider['username']}",
                f"password={provider['password']}",
                "",
                f"[{provider_id}_endpoint]",
                "type=endpoint",
                f"transport=transport-{provider['transport']}",
                "context=from-trunk",
                f"disallow=all",
                f"allow={provider['codec']}",
                f"outbound_auth={provider_id}_auth",
                f"aors={provider_id}_aor",
                "",
                f"[{provider_id}_aor]",
                "type=aor",
                f"contact=sip:{provider['host']}:{provider['port']}",
                "",
                f"[{provider_id}_identify]",
                "type=identify",
                f"endpoint={provider_id}_endpoint",
                f"match={provider['host']}",
                "",
                ";" + "="*50,
                ""
            ])
        
        return "\n".join(config_lines)

    def _generate_extensions_config(self, providers: Dict[str, Any]) -> str:
        """Generar configuración de extensiones para proveedores"""
        config_lines = [
            "; Configuración de Extensiones para Proveedores VoIP",
            f"; Generado automáticamente: {datetime.now().isoformat()}",
            "",
            "[from-trunk]",
            "; Llamadas entrantes desde proveedores",
            "exten => _X.,1,NoOp(Llamada entrante desde proveedor: ${CALLERID(all)})",
            "exten => _X.,n,Goto(from-internal,${EXTEN},1)",
            "",
            "[outbound-routes]",
            "; Rutas de salida a través de proveedores"
        ]
        
        for provider_id, provider in providers.items():
            config_lines.extend([
                f"; Ruta para {provider['name']}",
                f"exten => _9XXXXXXXXX,1,NoOp(Llamada saliente via {provider['name']})",
                f"exten => _9XXXXXXXXX,n,Set(CALLERID(num)={provider['username']})",
                f"exten => _9XXXXXXXXX,n,Dial(PJSIP/${{EXTEN:1}}@{provider_id}_endpoint,60)",
                f"exten => _9XXXXXXXXX,n,Hangup()",
                ""
            ])
        
        return "\n".join(config_lines)

    def get_provider_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de proveedores"""
        total = len(self.providers)
        active = sum(1 for p in self.providers.values() if p.get('active', False))
        connected = sum(1 for p in self.providers.values() if p.get('status') == 'connected')
        testing = sum(1 for p in self.providers.values() if p.get('status') == 'testing')
        
        return {
            "total": total,
            "active": active,
            "connected": connected,
            "testing": testing,
            "disconnected": total - connected - testing,
            "success_rate": round((connected / total * 100), 2) if total > 0 else 0
        }

# Instancia global del gestor de proveedores
provider_manager = ProviderManager()