#!/usr/bin/env python3
"""
INTEGRACIÓN WEB-ASTERISK PARA AUTO-MARCADO
Sistema completo de auto-marcado controlado desde servidor web
"""

import json
import asyncio
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import socket

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsteriskIntegration:
    """Integración completa con Asterisk para auto-marcado"""
    
    def __init__(self):
        self.project_root = Path("/workspace/voip-auto-dialer")
        self.extensions_file = self.project_root / "data" / "extensions.json"
        self.providers_file = self.project_root / "data" / "providers.json"
        self.campaigns_dir = self.project_root / "campaigns"
        
        # Configuración Manager API
        self.ami_host = "127.0.0.1"
        self.ami_port = 5038
        self.ami_username = "admin"
        self.ami_secret = "voip_admin_2026"
        
        # Estado del sistema
        self.active_campaigns = {}
        self.call_statistics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'active_calls': 0,
            'last_update': datetime.now().isoformat()
        }
    
    def load_extensions(self) -> Dict[str, Any]:
        """Cargar extensiones desde JSON"""
        try:
            if self.extensions_file.exists():
                with open(self.extensions_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error cargando extensiones: {e}")
            return {}
    
    def load_providers(self) -> Dict[str, Any]:
        """Cargar proveedores desde JSON"""
        try:
            if self.providers_file.exists():
                with open(self.providers_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error cargando proveedores: {e}")
            return {}
    
    def get_available_agents(self) -> List[str]:
        """Obtener lista de agentes disponibles"""
        try:
            extensions = self.load_extensions()
            available = []
            
            # Verificar estado de extensiones usando Asterisk CLI
            for ext_num, ext_data in extensions.items():
                if ext_data.get('assigned', False):
                    # Verificar si la extensión está registrada
                    result = subprocess.run([
                        'sudo', 'asterisk', '-rx', f'pjsip show endpoint {ext_num}'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0 and 'Unavailable' not in result.stdout:
                        available.append(ext_num)
            
            return available[:10]  # Limitar a 10 agentes
            
        except Exception as e:
            logger.error(f"Error obteniendo agentes disponibles: {e}")
            return []
    
    def get_call_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de llamadas"""
        try:
            # Actualizar estadísticas desde Asterisk
            result = subprocess.run([
                'sudo', 'asterisk', '-rx', 'core show channels'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                active_calls = 0
                for line in lines:
                    if 'active call' in line.lower():
                        # Extraer número de llamadas activas
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'active' in part.lower() and i > 0:
                                try:
                                    active_calls = int(parts[i-1])
                                    break
                                except ValueError:
                                    continue
                
                self.call_statistics['active_calls'] = active_calls
                self.call_statistics['last_update'] = datetime.now().isoformat()
            
            # Agregar información de extensiones
            extensions = self.load_extensions()
            self.call_statistics['total_extensions'] = len(extensions)
            self.call_statistics['timestamp'] = datetime.now().isoformat()
            
            return self.call_statistics
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return self.call_statistics
    
    def make_call(self, from_extension: str, to_number: str) -> bool:
        """Realizar una llamada individual"""
        try:
            # Limpiar número de destino
            to_number = to_number.strip().replace('+', '').replace('-', '').replace(' ', '')
            
            # Comando para originar llamada
            cmd = [
                'sudo', 'asterisk', '-rx',
                f'originate PJSIP/{from_extension} extension 9{to_number}@from-internal'
            ]
            
            logger.info(f"Iniciando llamada: {from_extension} -> {to_number}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.call_statistics['total_calls'] += 1
                self.call_statistics['successful_calls'] += 1
                logger.info(f"Llamada exitosa: {from_extension} -> {to_number}")
                return True
            else:
                self.call_statistics['total_calls'] += 1
                self.call_statistics['failed_calls'] += 1
                logger.error(f"Error en llamada: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error realizando llamada: {e}")
            self.call_statistics['total_calls'] += 1
            self.call_statistics['failed_calls'] += 1
            return False
    
    def auto_dial_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar campaña de auto-marcado"""
        try:
            campaign_id = campaign_data.get('id', f"campaign_{int(time.time())}")
            phone_numbers = campaign_data.get('phone_numbers', [])
            
            if not phone_numbers:
                return {
                    'success': False,
                    'message': 'No hay números para marcar',
                    'campaign_id': campaign_id
                }
            
            # Obtener agentes disponibles
            available_agents = self.get_available_agents()
            if not available_agents:
                return {
                    'success': False,
                    'message': 'No hay agentes disponibles',
                    'campaign_id': campaign_id
                }
            
            logger.info(f"Iniciando campaña {campaign_id}: {len(phone_numbers)} números, {len(available_agents)} agentes")
            
            # Distribuir llamadas entre agentes
            results = []
            agent_index = 0
            
            for phone_number in phone_numbers[:20]:  # Limitar a 20 llamadas por campaña
                agent = available_agents[agent_index % len(available_agents)]
                
                # Realizar llamada
                success = self.make_call(agent, phone_number)
                
                results.append({
                    'phone_number': phone_number,
                    'agent': agent,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })
                
                agent_index += 1
                
                # Pausa entre llamadas para evitar sobrecarga
                time.sleep(2)
            
            # Guardar resultados de campaña
            campaign_result = {
                'campaign_id': campaign_id,
                'total_numbers': len(phone_numbers),
                'processed_numbers': len(results),
                'successful_calls': sum(1 for r in results if r['success']),
                'failed_calls': sum(1 for r in results if not r['success']),
                'agents_used': list(set(r['agent'] for r in results)),
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
            # Guardar en archivo
            campaign_file = self.campaigns_dir / f"{campaign_id}_results.json"
            self.campaigns_dir.mkdir(exist_ok=True)
            
            with open(campaign_file, 'w') as f:
                json.dump(campaign_result, f, indent=2)
            
            logger.info(f"Campaña {campaign_id} completada: {campaign_result['successful_calls']}/{campaign_result['processed_numbers']} exitosas")
            
            return {
                'success': True,
                'message': f'Campaña ejecutada: {campaign_result["successful_calls"]}/{campaign_result["processed_numbers"]} llamadas exitosas',
                'data': campaign_result
            }
            
        except Exception as e:
            logger.error(f"Error en campaña de auto-marcado: {e}")
            return {
                'success': False,
                'message': f'Error ejecutando campaña: {str(e)}',
                'campaign_id': campaign_data.get('id', 'unknown')
            }
    
    def configure_asterisk_from_web(self) -> bool:
        """Reconfigurar Asterisk desde el servidor web"""
        try:
            logger.info("Reconfigurando Asterisk desde servidor web...")
            
            # Recargar configuración de Asterisk
            commands = [
                'sudo asterisk -rx "module reload"',
                'sudo asterisk -rx "dialplan reload"',
                'sudo asterisk -rx "pjsip reload"'
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    logger.error(f"Error ejecutando {cmd}: {result.stderr}")
                    return False
                logger.info(f"Ejecutado: {cmd}")
            
            logger.info("Asterisk reconfigurado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error reconfigurando Asterisk: {e}")
            return False
    
    def test_provider_connection(self) -> Dict[str, Any]:
        """Probar conexión con proveedor VoIP"""
        try:
            providers = self.load_providers()
            if not providers:
                return {'success': False, 'message': 'No hay proveedores configurados'}
            
            # Obtener primer proveedor activo
            provider = None
            for p_id, p_data in providers.items():
                if p_data.get('active', False):
                    provider = p_data
                    break
            
            if not provider:
                return {'success': False, 'message': 'No hay proveedores activos'}
            
            # Probar registro SIP
            result = subprocess.run([
                'sudo', 'asterisk', '-rx', 'pjsip show registrations'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                if provider['host'] in result.stdout:
                    return {
                        'success': True,
                        'message': f'Conexión exitosa con {provider["name"]}',
                        'provider': provider['name'],
                        'host': provider['host']
                    }
            
            return {
                'success': False,
                'message': f'Sin conexión con {provider["name"]}',
                'provider': provider['name']
            }
            
        except Exception as e:
            logger.error(f"Error probando conexión con proveedor: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        try:
            # Estado de Asterisk
            asterisk_result = subprocess.run([
                'sudo', 'systemctl', 'is-active', 'asterisk'
            ], capture_output=True, text=True)
            
            asterisk_active = asterisk_result.returncode == 0 and 'active' in asterisk_result.stdout
            
            # Estadísticas de llamadas
            call_stats = self.get_call_statistics()
            
            # Agentes disponibles
            available_agents = self.get_available_agents()
            
            # Conexión con proveedor
            provider_status = self.test_provider_connection()
            
            return {
                'asterisk_status': 'active' if asterisk_active else 'inactive',
                'available_agents': len(available_agents),
                'agents_list': available_agents,
                'call_statistics': call_stats,
                'provider_connection': provider_status,
                'system_ready': asterisk_active and len(available_agents) > 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Instancia global para usar en el servidor web
asterisk_integration = AsteriskIntegration()

def main():
    """Función principal para pruebas"""
    print("🔧 PROBANDO INTEGRACIÓN WEB-ASTERISK")
    print("=" * 50)
    
    # Probar estado del sistema
    status = asterisk_integration.get_system_status()
    print(f"📊 Estado del sistema: {json.dumps(status, indent=2)}")
    
    # Probar agentes disponibles
    agents = asterisk_integration.get_available_agents()
    print(f"👥 Agentes disponibles: {agents}")
    
    # Probar estadísticas
    stats = asterisk_integration.get_call_statistics()
    print(f"📈 Estadísticas: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    main()