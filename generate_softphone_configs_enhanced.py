#!/usr/bin/env python3
"""
Generador de configuraciones de softphone
Crea archivos de configuración para Zoiper, PortSIP, etc.
"""

import json
import os
from datetime import datetime

def generate_zoiper_config(extension, password, agent_name):
    """Generar configuración para Zoiper"""
    config = f"""[{extension}]
username={extension}
password={password}
domain=localhost
proxy=localhost:5060
transport=UDP
display_name={agent_name}
enabled=1
register=1
"""
    return config

def generate_portsip_config(extension, password, agent_name):
    """Generar configuración para PortSIP"""
    config = f"""<?xml version="1.0" encoding="UTF-8"?>
<PortSIP>
    <Account>
        <DisplayName>{agent_name}</DisplayName>
        <UserName>{extension}</UserName>
        <Password>{password}</Password>
        <SIPServer>localhost</SIPServer>
        <SIPServerPort>5060</SIPServerPort>
        <Transport>UDP</Transport>
        <RegisterServer>localhost</RegisterServer>
        <RegisterServerPort>5060</RegisterServerPort>
    </Account>
</PortSIP>
"""
    return config

def generate_generic_config(extension, password, agent_name):
    """Generar configuración genérica"""
    config = f"""=== CONFIGURACIÓN SIP ===
Extensión: {extension}
Contraseña: {password}
Servidor SIP: localhost
Puerto: 5060
Transporte: UDP
Nombre: {agent_name}

=== INSTRUCCIONES ===
1. Instala tu aplicación SIP favorita
2. Crea una nueva cuenta SIP
3. Usa los datos de arriba
4. Guarda y registra la cuenta
5. ¡Ya puedes hacer llamadas!

=== APLICACIONES RECOMENDADAS ===
• Zoiper (Windows, Mac, Linux, Mobile)
• PortSIP (Windows, Mac, Mobile)
• Linphone (Multiplataforma)
• X-Lite (Windows, Mac)
"""
    return config

def main():
    print("🎯 GENERANDO CONFIGURACIONES DE SOFTPHONE")
    print("="*50)
    
    # Cargar datos
    if not os.path.exists('data/agents.json'):
        print("❌ No se encontró data/agents.json")
        return False
    
    with open('data/agents.json', 'r') as f:
        agents = json.load(f)
    
    # Crear directorio de configuraciones
    config_dir = 'data/softphone_configs'
    os.makedirs(config_dir, exist_ok=True)
    
    configs_generated = 0
    
    for agent_id, agent_data in agents.items():
        extension_info = agent_data.get('extension_info')
        if not extension_info:
            continue
        
        extension = extension_info['extension']
        password = extension_info['password']
        agent_name = agent_data['name']
        
        # Generar configuraciones
        zoiper_config = generate_zoiper_config(extension, password, agent_name)
        portsip_config = generate_portsip_config(extension, password, agent_name)
        generic_config = generate_generic_config(extension, password, agent_name)
        
        # Guardar archivos
        with open(f"{config_dir}/zoiper_config_{extension}.conf", 'w') as f:
            f.write(zoiper_config)
        
        with open(f"{config_dir}/portsip_config_{extension}.xml", 'w') as f:
            f.write(portsip_config)
        
        with open(f"{config_dir}/sip_config_{extension}.txt", 'w') as f:
            f.write(generic_config)
        
        configs_generated += 1
        print(f"✅ Configuraciones generadas para {agent_name} (Ext: {extension})")
    
    print(f"\n📊 Total configuraciones generadas: {configs_generated}")
    print(f"📁 Archivos guardados en: {config_dir}/")
    
    return True

if __name__ == "__main__":
    main()
