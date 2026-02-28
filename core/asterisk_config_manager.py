#!/usr/bin/env python3
"""
🔧 GESTOR AUTOMÁTICO DE CONFIGURACIÓN ASTERISK
Genera configuraciones dinámicamente desde el servidor web
"""

import os
import json
import subprocess
from datetime import datetime
from core.extension_manager import extension_manager
from core.provider_manager import provider_manager
from core.agent_manager_clean import agent_manager
from core.logging_config import get_logger

logger = get_logger(__name__)

class AsteriskConfigManager:
    def __init__(self):
        self.config_path = "/etc/asterisk"
        self.backup_path = "/etc/asterisk_backups"
        
    def generate_pjsip_config(self):
        """Generar configuración PJSIP dinámica"""
        logger.info("Generando configuración PJSIP dinámica")
        
        config = []
        config.append("[global]")
        config.append("type=global")
        config.append("endpoint_identifier_order=ip,username,anonymous")
        config.append("")
        
        config.append("[transport-udp]")
        config.append("type=transport")
        config.append("protocol=udp")
        config.append("bind=0.0.0.0:5060")
        config.append("")
        
        # Configurar proveedores
        providers = provider_manager.get_all_providers()
        for provider in providers:
            if provider['status'] == 'active':
                config.extend(self._generate_provider_config(provider))
        
        # Configurar extensiones dinámicamente
        extensions = extension_manager.get_available_extensions()[:50]  # Primeras 50 extensiones
        for ext in extensions:
            config.extend(self._generate_extension_config(ext))
        
        return "\n".join(config)
    
    def _generate_provider_config(self, provider):
        """Generar configuración de proveedor"""
        name = provider['name'].lower().replace(' ', '_')
        config = []
        
        # Endpoint
        config.append(f"[{name}]")
        config.append("type=endpoint")
        config.append("context=from-provider")
        config.append("disallow=all")
        config.append("allow=ulaw,alaw")
        config.append(f"auth={name}")
        config.append(f"aors={name}")
        config.append("direct_media=no")
        config.append("")
        
        # Auth
        config.append(f"[{name}]")
        config.append("type=auth")
        config.append("auth_type=userpass")
        config.append(f"password={provider.get('password', 'password')}")
        config.append(f"username={provider.get('username', 'user')}")
        config.append("")
        
        # AOR
        config.append(f"[{name}]")
        config.append("type=aor")
        config.append(f"contact=sip:{provider.get('username', 'user')}@{provider['host']}:{provider['port']}")
        config.append("")
        
        # Registration
        config.append(f"[{name}]")
        config.append("type=registration")
        config.append("transport=transport-udp")
        config.append(f"outbound_auth={name}")
        config.append(f"server_uri=sip:{provider['host']}:{provider['port']}")
        config.append(f"client_uri=sip:{provider.get('username', 'user')}@{provider['host']}:{provider['port']}")
        config.append("")
        
        return config
    
    def _generate_extension_config(self, extension):
        """Generar configuración de extensión"""
        ext_num = extension['extension']
        password = f"ext{ext_num}"
        config = []
        
        # Endpoint
        config.append(f"[{ext_num}]")
        config.append("type=endpoint")
        config.append("context=from-internal")
        config.append("disallow=all")
        config.append("allow=ulaw,alaw")
        config.append(f"auth={ext_num}")
        config.append(f"aors={ext_num}")
        config.append("")
        
        # Auth
        config.append(f"[{ext_num}]")
        config.append("type=auth")
        config.append("auth_type=userpass")
        config.append(f"password={password}")
        config.append(f"username={ext_num}")
        config.append("")
        
        # AOR
        config.append(f"[{ext_num}]")
        config.append("type=aor")
        config.append("max_contacts=1")
        config.append("")
        
        return config
    
    def generate_extensions_config(self):
        """Generar dialplan dinámico"""
        logger.info("Generando dialplan dinámico")
        
        config = []
        config.append("[general]")
        config.append("static=yes")
        config.append("writeprotect=no")
        config.append("clearglobalvars=no")
        config.append("")
        
        config.append("[globals]")
        config.append("")
        
        # Contexto interno
        config.append("[from-internal]")
        
        # Extensiones dinámicas
        extensions = extension_manager.get_available_extensions()[:50]
        for ext in extensions:
            ext_num = ext['extension']
            config.append(f"exten => {ext_num},1,Dial(PJSIP/{ext_num},20)")
            config.append(f"exten => {ext_num},n,Voicemail({ext_num}@default,u)")
            config.append(f"exten => {ext_num},n,Hangup()")
            config.append("")
        
        # Llamadas salientes
        config.append("exten => _9.,1,Set(OUTNUM=${EXTEN:1})")
        config.append("exten => _9.,n,Dial(PJSIP/pbx_on_the_cloud/sip:${OUTNUM}@pbxonthecloud.com:5081,60)")
        config.append("exten => _9.,n,Hangup()")
        config.append("")
        
        # Servicios especiales
        config.append("exten => 911,1,Dial(PJSIP/pbx_on_the_cloud/sip:911@pbxonthecloud.com:5081,60)")
        config.append("exten => 911,n,Hangup()")
        config.append("")
        
        config.append("exten => *97,1,VoiceMailMain(${CALLERID(num)}@default)")
        config.append("exten => *97,n,Hangup()")
        config.append("")
        
        config.append("exten => *43,1,Echo()")
        config.append("exten => *43,n,Hangup()")
        config.append("")
        
        # Contexto para llamadas entrantes
        config.append("[from-provider]")
        config.append("exten => _X.,1,Goto(autodialer-incoming,${EXTEN},1)")
        config.append("")
        
        # Contexto para auto-dialer
        config.append("[autodialer-incoming]")
        config.append("exten => _X.,1,Set(INCOMING_NUMBER=${CALLERID(num)})")
        config.append("exten => _X.,n,AGI(autodialer_handler.py,${INCOMING_NUMBER})")
        config.append("exten => _X.,n,Hangup()")
        config.append("")
        
        config.append("[default]")
        config.append("include => from-internal")
        config.append("")
        
        return "\n".join(config)
    
    def apply_configuration(self):
        """Aplicar configuración generada a Asterisk"""
        logger.info("Aplicando configuración automática a Asterisk")
        
        try:
            # Crear backup
            self._create_backup()
            
            # Generar configuraciones
            pjsip_config = self.generate_pjsip_config()
            extensions_config = self.generate_extensions_config()
            
            # Escribir archivos
            with open(f"{self.config_path}/pjsip.conf", 'w') as f:
                f.write(pjsip_config)
            
            with open(f"{self.config_path}/extensions.conf", 'w') as f:
                f.write(extensions_config)
            
            # Recargar Asterisk
            self._reload_asterisk()
            
            logger.info("Configuración aplicada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando configuración: {e}")
            return False
    
    def _create_backup(self):
        """Crear backup de configuración actual"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{self.backup_path}/backup_{timestamp}"
        
        os.makedirs(backup_dir, exist_ok=True)
        subprocess.run(f"cp -r {self.config_path}/* {backup_dir}/", shell=True)
        logger.info(f"Backup creado: {backup_dir}")
    
    def _reload_asterisk(self):
        """Recargar configuración de Asterisk"""
        commands = [
            "module reload res_pjsip.so",
            "dialplan reload",
            "core reload"
        ]
        
        for cmd in commands:
            result = subprocess.run(f"asterisk -rx '{cmd}'", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Advertencia ejecutando '{cmd}': {result.stderr}")

# Instancia global
asterisk_config_manager = AsteriskConfigManager()