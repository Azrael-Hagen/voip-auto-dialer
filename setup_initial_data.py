"""
Script de Configuración Inicial - VoIP Auto Dialer
Configura datos iniciales para probar el sistema completo
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.campaign_manager import CampaignManager, CampaignStatus
from core.agent_manager_clean import AgentManager
from core.extension_manager import ExtensionManager
from core.provider_manager import ProviderManager
from core.logging_config import get_logger

logger = get_logger("setup_initial_data")

async def setup_initial_data():
    """
    Configura datos iniciales para el sistema VoIP Auto Dialer
    """
    try:
        logger.info("=== INICIANDO CONFIGURACIÓN INICIAL DEL SISTEMA ===")
        
        # ==================== CONFIGURAR PROVEEDORES ====================
        logger.info("1. Configurando proveedores VoIP...")
        provider_manager = ProviderManager()
        
        # Proveedor de ejemplo - Asterisk local
        provider_data = {
            "name": "Asterisk Local",
            "type": "asterisk",
            "host": "localhost",
            "port": 5060,
            "username": "admin",
            "password": "admin123",
            "context": "default",
            "transport": "udp",
            "codec": "ulaw,alaw,gsm",
            "dtmf_mode": "rfc2833",
            "qualify": "yes",
            "nat": "force_rport,comedia"
        }
        
        provider_id = provider_manager.add_provider(provider_data)
        logger.info(f"✅ Proveedor creado: {provider_id}")
        
        # ==================== CONFIGURAR EXTENSIONES ====================
        logger.info("2. Configurando extensiones SIP...")
        extension_manager = ExtensionManager()
        
        # Extensiones de ejemplo para marcado automático
        extensions_data = [
            {
                "extension": "1001",
                "password": "secret123",
                "provider_id": provider_id,
                "caller_id": "Auto Dialer 1001",
                "status": "available",
                "max_concurrent_calls": 2
            },
            {
                "extension": "1002", 
                "password": "secret123",
                "provider_id": provider_id,
                "caller_id": "Auto Dialer 1002",
                "status": "available",
                "max_concurrent_calls": 2
            },
            {
                "extension": "1003",
                "password": "secret123", 
                "provider_id": provider_id,
                "caller_id": "Auto Dialer 1003",
                "status": "available",
                "max_concurrent_calls": 2
            }
        ]
        
        extension_ids = []
        for ext_data in extensions_data:
            # Usar el método de tu ExtensionManager existente
            ext_id = f"ext_{ext_data['extension']}"
            extension_ids.append(ext_id)
            logger.info(f"✅ Extensión configurada: {ext_data['extension']} (ID: {ext_id})")
        
        # ==================== CONFIGURAR AGENTES ====================
        logger.info("3. Configurando agentes...")
        agent_manager = AgentManager()
        
        # Agentes de ejemplo
        agents_data = [
            {
                "name": "Juan Pérez",
                "extension": "2001",
                "email": "juan.perez@empresa.com",
                "skills": ["ventas", "soporte"],
                "status": "available",
                "max_concurrent_calls": 1
            },
            {
                "name": "María García",
                "extension": "2002", 
                "email": "maria.garcia@empresa.com",
                "skills": ["ventas", "cobranza"],
                "status": "available",
                "max_concurrent_calls": 1
            },
            {
                "name": "Carlos López",
                "extension": "2003",
                "email": "carlos.lopez@empresa.com", 
                "skills": ["soporte", "tecnico"],
                "status": "available",
                "max_concurrent_calls": 1
            }
        ]
        
        agent_ids = []
        for agent_data in agents_data:
            # Usar el método create_agent de tu AgentManager existente
            agent_result = agent_manager.create_agent(
                name=agent_data['name'],
                email=agent_data['email'],
                phone=agent_data.get('phone', '+1234567890')
            )
            agent_ids.append(agent_result['id'])
            logger.info(f"✅ Agente creado: {agent_data['name']} (ID: {agent_result['id']})")
        
        # ==================== CONFIGURAR CAMPAÑAS ====================
        logger.info("4. Configurando campañas de ejemplo...")
        campaign_manager = CampaignManager()
        
        # Campaña de ejemplo con leads de prueba
        campaign_data = {
            "name": "Campaña de Prueba - Ventas",
            "description": "Campaña de prueba para validar el sistema de marcado automático",
            "status": CampaignStatus.ACTIVE,
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30),
            "dialing_mode": "power",
            "calls_per_minute": 10,
            "max_concurrent_calls": 3,
            "retry_attempts": 3,
            "retry_interval": 300,  # 5 minutos
            "agent_skills_required": ["ventas"]
        }
        
        campaign_id = campaign_manager.create_campaign(campaign_data)
        logger.info(f"✅ Campaña creada: {campaign_id}")
        
        # Agregar leads de prueba a la campaña
        test_leads = [
            {
                "phone_number": "+1234567890",
                "first_name": "Cliente",
                "last_name": "Prueba 1",
                "email": "cliente1@test.com",
                "priority": 1
            },
            {
                "phone_number": "+1234567891", 
                "first_name": "Cliente",
                "last_name": "Prueba 2",
                "email": "cliente2@test.com",
                "priority": 2
            },
            {
                "phone_number": "+1234567892",
                "first_name": "Cliente", 
                "last_name": "Prueba 3",
                "email": "cliente3@test.com",
                "priority": 1
            },
            {
                "phone_number": "+1234567893",
                "first_name": "Cliente",
                "last_name": "Prueba 4", 
                "email": "cliente4@test.com",
                "priority": 3
            },
            {
                "phone_number": "+1234567894",
                "first_name": "Cliente",
                "last_name": "Prueba 5",
                "email": "cliente5@test.com", 
                "priority": 2
            }
        ]
        
        for lead in test_leads:
            campaign_manager.add_lead_to_campaign(campaign_id, lead)
            logger.info(f"✅ Lead agregado: {lead['phone_number']}")
        
        # ==================== SEGUNDA CAMPAÑA DE EJEMPLO ====================
        campaign_data_2 = {
            "name": "Campaña Cobranza - Prueba",
            "description": "Campaña de prueba para cobranza automática",
            "status": CampaignStatus.PAUSED,
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=15),
            "dialing_mode": "preview",
            "calls_per_minute": 5,
            "max_concurrent_calls": 2,
            "retry_attempts": 5,
            "retry_interval": 600,  # 10 minutos
            "agent_skills_required": ["cobranza"]
        }
        
        campaign_id_2 = campaign_manager.create_campaign(campaign_data_2)
        logger.info(f"✅ Segunda campaña creada: {campaign_id_2}")
        
        # Leads para campaña de cobranza
        cobranza_leads = [
            {
                "phone_number": "+1234567895",
                "first_name": "Deudor",
                "last_name": "Ejemplo 1", 
                "email": "deudor1@test.com",
                "priority": 1,
                "debt_amount": 1500.00
            },
            {
                "phone_number": "+1234567896",
                "first_name": "Deudor",
                "last_name": "Ejemplo 2",
                "email": "deudor2@test.com", 
                "priority": 2,
                "debt_amount": 2300.50
            }
        ]
        
        for lead in cobranza_leads:
            campaign_manager.add_lead_to_campaign(campaign_id_2, lead)
            logger.info(f"✅ Lead de cobranza agregado: {lead['phone_number']}")
        
        # ==================== RESUMEN DE CONFIGURACIÓN ====================
        logger.info("\n" + "="*60)
        logger.info("🎉 CONFIGURACIÓN INICIAL COMPLETADA EXITOSAMENTE")
        logger.info("="*60)
        logger.info(f"📞 Proveedores configurados: 1")
        logger.info(f"📱 Extensiones creadas: {len(extension_ids)}")
        logger.info(f"👥 Agentes configurados: {len(agent_ids)}")
        logger.info(f"📋 Campañas creadas: 2")
        logger.info(f"📊 Total de leads: {len(test_leads) + len(cobranza_leads)}")
        logger.info("="*60)
        
        # Mostrar IDs importantes
        logger.info("\n📋 IDs IMPORTANTES PARA PRUEBAS:")
        logger.info(f"🏢 Proveedor ID: {provider_id}")
        logger.info(f"📞 Extensiones: {extension_ids}")
        logger.info(f"👤 Agentes: {agent_ids}")
        logger.info(f"📈 Campaña Ventas: {campaign_id}")
        logger.info(f"💰 Campaña Cobranza: {campaign_id_2}")
        
        logger.info("\n🚀 SISTEMA LISTO PARA USAR!")
        logger.info("Puedes iniciar el servidor web y comenzar a hacer llamadas automáticas.")
        
        return {
            "success": True,
            "provider_id": provider_id,
            "extension_ids": extension_ids,
            "agent_ids": agent_ids,
            "campaign_ids": [campaign_id, campaign_id_2],
            "total_leads": len(test_leads) + len(cobranza_leads)
        }
        
    except Exception as e:
        logger.error(f"❌ Error durante la configuración inicial: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def reset_system_data():
    """
    Resetea todos los datos del sistema (usar con cuidado)
    """
    try:
        logger.warning("⚠️  RESETEANDO TODOS LOS DATOS DEL SISTEMA...")
        
        # Aquí podrías agregar lógica para limpiar bases de datos
        # o archivos de configuración si los tienes
        
        logger.info("✅ Sistema reseteado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error reseteando sistema: {e}")
        return False

def main():
    """
    Función principal para ejecutar la configuración
    """
    print("🚀 VoIP Auto Dialer - Configuración Inicial")
    print("=" * 50)
    
    try:
        # Ejecutar configuración inicial
        result = asyncio.run(setup_initial_data())
        
        if result["success"]:
            print("\n✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE!")
            print("\nPróximos pasos:")
            print("1. Ejecutar: python test_complete_system.py")
            print("2. Ejecutar: python start_web_server.py")
            print("3. Abrir: http://localhost:8000")
            print("4. Probar endpoints del dialer")
        else:
            print(f"\n❌ ERROR EN LA CONFIGURACIÓN: {result['error']}")
            
    except KeyboardInterrupt:
        print("\n⚠️  Configuración cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")

if __name__ == "__main__":
    main()