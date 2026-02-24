#!/usr/bin/env python3
"""
Sincronización de extensiones con Asterisk
Genera configuraciones PJSIP automáticamente
"""

import json
import os
from datetime import datetime

def generate_pjsip_config():
    """Generar configuración PJSIP para Asterisk"""
    print("🔧 Generando configuración PJSIP...")
    
    # Cargar extensiones asignadas
    if not os.path.exists('data/extensions.json'):
        print("❌ No se encontró data/extensions.json")
        return False
    
    with open('data/extensions.json', 'r') as f:
        extensions = json.load(f)
    
    # Generar configuración PJSIP
    pjsip_config = []
    pjsip_config.append("; Configuración PJSIP generada automáticamente")
    pjsip_config.append(f"; Generado: {datetime.now()}")
    pjsip_config.append("")
    
    assigned_extensions = {k: v for k, v in extensions.items() if v.get('status') == 'assigned'}
    
    for ext_num, ext_data in assigned_extensions.items():
        password = ext_data.get('password', 'defaultpass')
        agent_id = ext_data.get('agent_id', 'unknown')
        
        # Endpoint
        pjsip_config.append(f"[{ext_num}]")
        pjsip_config.append("type=endpoint")
        pjsip_config.append("context=from-internal")
        pjsip_config.append("disallow=all")
        pjsip_config.append("allow=ulaw,alaw,gsm")
        pjsip_config.append(f"auth={ext_num}")
        pjsip_config.append(f"aors={ext_num}")
        pjsip_config.append("")
        
        # Auth
        pjsip_config.append(f"[{ext_num}]")
        pjsip_config.append("type=auth")
        pjsip_config.append("auth_type=userpass")
        pjsip_config.append(f"password={password}")
        pjsip_config.append(f"username={ext_num}")
        pjsip_config.append("")
        
        # AOR
        pjsip_config.append(f"[{ext_num}]")
        pjsip_config.append("type=aor")
        pjsip_config.append("max_contacts=1")
        pjsip_config.append("")
    
    # Guardar configuración
    os.makedirs('asterisk_config', exist_ok=True)
    config_file = 'asterisk_config/pjsip_extensions.conf'
    
    with open(config_file, 'w') as f:
        f.write('\n'.join(pjsip_config))
    
    print(f"✅ Configuración PJSIP guardada: {config_file}")
    print(f"📊 Extensiones configuradas: {len(assigned_extensions)}")
    
    return True

def generate_extensions_config():
    """Generar configuración de dialplan"""
    print("📞 Generando dialplan...")
    
    extensions_config = []
    extensions_config.append("; Dialplan generado automáticamente")
    extensions_config.append(f"; Generado: {datetime.now()}")
    extensions_config.append("")
    extensions_config.append("[from-internal]")
    extensions_config.append("exten => _XXXX,1,Dial(PJSIP/${EXTEN})")
    extensions_config.append("exten => _XXXX,n,Hangup()")
    extensions_config.append("")
    
    config_file = 'asterisk_config/extensions_voip.conf'
    with open(config_file, 'w') as f:
        f.write('\n'.join(extensions_config))
    
    print(f"✅ Dialplan guardado: {config_file}")
    return True

def main():
    print("🎯 SINCRONIZACIÓN CON ASTERISK")
    print("="*50)
    
    if generate_pjsip_config() and generate_extensions_config():
        print("\n✅ Sincronización completada exitosamente")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Copia asterisk_config/pjsip_extensions.conf a /etc/asterisk/")
        print("2. Copia asterisk_config/extensions_voip.conf a /etc/asterisk/")
        print("3. Incluye los archivos en tu configuración principal")
        print("4. Reinicia Asterisk: sudo systemctl restart asterisk")
        return True
    else:
        print("\n❌ Error en la sincronización")
        return False

if __name__ == "__main__":
    main()
