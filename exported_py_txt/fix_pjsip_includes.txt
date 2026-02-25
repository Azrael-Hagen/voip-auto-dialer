#!/usr/bin/env python3
# Archivo: ~/voip-auto-dialer/scripts/fix_pjsip_includes.py

import os
import shutil
from datetime import datetime

def create_clean_pjsip_conf():
    """Crear pjsip.conf limpio con solo el include correcto"""
    
    clean_config = """
;=================================================================
; PJSIP Configuration for VoIP Auto Dialer - LIMPIO
; Generado automáticamente - NO EDITAR MANUALMENTE
;=================================================================

;===============TRANSPORT===============
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060
local_net=192.168.0.0/16
local_net=10.0.0.0/8
local_net=172.16.0.0/12
external_media_address=127.0.0.1
external_signaling_address=127.0.0.1

;===============GLOBAL SETTINGS===============
[global]
type=global
endpoint_identifier_order=ip,username,anonymous

;===============INCLUDE EXTENSIONS===============
; SOLO incluir el archivo que realmente existe
#include pjsip_extensions.conf

;===============END OF MAIN CONFIG===============
""".strip()
    
    return clean_config

def main():
    print("🔧 REPARACIÓN DE INCLUDES EN pjsip.conf")
    print("=" * 60)
    
    # 1. Crear backup con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"/etc/asterisk/pjsip.conf.backup_{timestamp}"
    
    print("1️⃣ Creando backup...")
    try:
        shutil.copy2("/etc/asterisk/pjsip.conf", backup_path)
        print(f"   ✅ Backup creado: {backup_path}")
    except Exception as e:
        print(f"   ❌ Error creando backup: {e}")
        return False
    
    # 2. Verificar que pjsip_extensions.conf existe
    print("\n2️⃣ Verificando archivo de extensiones...")
    if not os.path.exists("/etc/asterisk/pjsip_extensions.conf"):
        print("   ❌ ERROR: pjsip_extensions.conf no existe")
        return False
    
    size = os.path.getsize("/etc/asterisk/pjsip_extensions.conf")
    print(f"   ✅ pjsip_extensions.conf existe ({size} bytes)")
    
    # 3. Crear nueva configuración limpia
    print("\n3️⃣ Creando configuración limpia...")
    clean_config = create_clean_pjsip_conf()
    
    try:
        with open("/etc/asterisk/pjsip.conf", "w") as f:
            f.write(clean_config)
        print("   ✅ pjsip.conf actualizado con configuración limpia")
    except Exception as e:
        print(f"   ❌ Error escribiendo archivo: {e}")
        return False
    
    # 4. Verificar permisos
    print("\n4️⃣ Configurando permisos...")
    try:
        os.chmod("/etc/asterisk/pjsip.conf", 0o644)
        print("   ✅ Permisos configurados")
    except Exception as e:
        print(f"   ❌ Error configurando permisos: {e}")
    
    # 5. Mostrar el nuevo contenido
    print("\n5️⃣ Nuevo contenido de pjsip.conf:")
    print("-" * 40)
    with open("/etc/asterisk/pjsip.conf", "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if line.strip():  # Solo líneas no vacías
                print(f"   {i:2d}: {line.rstrip()}")
    
    print("\n" + "=" * 60)
    print("✅ REPARACIÓN COMPLETADA")
    print("=" * 60)
    print("\n🚀 PRÓXIMOS PASOS:")
    print("1. Ejecutar: sudo asterisk -rx 'pjsip reload'")
    print("2. Verificar: sudo asterisk -rx 'pjsip show endpoints'")
    print("3. Deberías ver las 502 extensiones cargadas")
    
    return True

if __name__ == "__main__":
    main()