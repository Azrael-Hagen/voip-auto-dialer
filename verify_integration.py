#!/usr/bin/env python3
"""
Script para verificar la integración completa del sistema VoIP
"""

import subprocess
import json
import os
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n{step}. 📋 {description}")
    print("-" * 50)

def run_asterisk_command(command):
    """Ejecutar comando de Asterisk"""
    try:
        result = subprocess.run(
            f"sudo asterisk -rx '{command}'",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout, result.returncode == 0
    except Exception as e:
        return str(e), False

def check_asterisk_status():
    """Verificar estado de Asterisk"""
    print("🔍 Verificando estado de Asterisk...")
    
    # Verificar que Asterisk esté corriendo
    result = subprocess.run("pgrep asterisk", shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ Asterisk no está ejecutándose")
        return False
    
    print("✅ Asterisk está ejecutándose")
    
    # Verificar versión
    output, success = run_asterisk_command("core show version")
    if success:
        version_line = output.split('\n')[0]
        print(f"✅ {version_line}")
    
    return True

def check_pjsip_endpoints():
    """Verificar endpoints PJSIP"""
    print("🔍 Verificando endpoints PJSIP...")
    
    output, success = run_asterisk_command("pjsip show endpoints")
    if not success:
        print("❌ Error obteniendo endpoints PJSIP")
        return False
    
    # Contar endpoints
    lines = output.split('\n')
    endpoint_count = 0
    registered_count = 0
    
    for line in lines:
        if 'Endpoint:' in line and not line.startswith(' Endpoint:'):
            endpoint_count += 1
            if 'Available' in line:
                registered_count += 1
    
    print(f"✅ Endpoints encontrados: {endpoint_count}")
    print(f"✅ Endpoints registrados: {registered_count}")
    
    return endpoint_count > 0

def check_dialplan():
    """Verificar dialplan"""
    print("🔍 Verificando dialplan...")
    
    output, success = run_asterisk_command("dialplan show from-internal")
    if not success:
        print("❌ Error obteniendo dialplan")
        return False
    
    if "No such context" in output:
        print("❌ Contexto 'from-internal' no encontrado")
        return False
    
    print("✅ Contexto 'from-internal' configurado")
    
    # Verificar extensiones
    if "_XXXX" in output or "XXXX" in output:
        print("✅ Patrón de extensiones configurado")
        return True
    else:
        print("⚠️ Patrón de extensiones no encontrado")
        return False

def load_system_data():
    """Cargar datos del sistema"""
    print("🔍 Cargando datos del sistema...")
    
    # Cargar agentes
    agents_file = Path("data/agents.json")
    extensions_file = Path("data/extensions.json")
    
    if not agents_file.exists():
        print("❌ Archivo de agentes no encontrado")
        return None, None
    
    if not extensions_file.exists():
        print("❌ Archivo de extensiones no encontrado")
        return None, None
    
    with open(agents_file, 'r') as f:
        agents = json.load(f)
    
    with open(extensions_file, 'r') as f:
        extensions = json.load(f)
    
    # Contar extensiones asignadas
    assigned_count = 0
    for ext_data in extensions.values():
        if ext_data.get('status') == 'assigned':
            assigned_count += 1
    
    print(f"✅ Agentes cargados: {len(agents)}")
    print(f"✅ Extensiones totales: {len(extensions)}")
    print(f"✅ Extensiones asignadas: {assigned_count}")
    
    return agents, extensions

def check_softphone_configs():
    """Verificar configuraciones de softphone"""
    print("🔍 Verificando configuraciones de softphone...")
    
    config_dir = Path("data/softphone_configs")
    if not config_dir.exists():
        print("❌ Directorio de configuraciones no encontrado")
        return False
    
    # Contar archivos de configuración
    zoiper_configs = list(config_dir.glob("zoiper_config_*.conf"))
    portsip_configs = list(config_dir.glob("portsip_config_*.xml"))
    sip_configs = list(config_dir.glob("sip_config_*.txt"))
    
    print(f"✅ Configuraciones Zoiper: {len(zoiper_configs)}")
    print(f"✅ Configuraciones PortSIP: {len(portsip_configs)}")
    print(f"✅ Configuraciones SIP genéricas: {len(sip_configs)}")
    
    return len(zoiper_configs) > 0 or len(portsip_configs) > 0

def test_extension_call():
    """Probar llamada entre extensiones"""
    print("🔍 Probando llamada de prueba...")
    
    # Cargar extensiones asignadas
    try:
        with open("data/extensions.json", 'r') as f:
            extensions = json.load(f)
        
        assigned_extensions = []
        for ext_num, ext_data in extensions.items():
            if ext_data.get('status') == 'assigned':
                assigned_extensions.append(ext_num)
        
        if len(assigned_extensions) < 2:
            print("⚠️ Se necesitan al menos 2 extensiones asignadas para probar llamadas")
            return False
        
        # Tomar las primeras dos extensiones
        from_ext = assigned_extensions[0]
        to_ext = assigned_extensions[1]
        
        print(f"📞 Probando llamada: {from_ext} → {to_ext}")
        
        # Originar llamada de prueba
        command = f"channel originate PJSIP/{from_ext} extension {to_ext}@from-internal"
        output, success = run_asterisk_command(command)
        
        if success:
            print("✅ Llamada de prueba iniciada")
            
            # Esperar un momento y verificar canales
            import time
            time.sleep(2)
            
            channels_output, _ = run_asterisk_command("core show channels")
            if "PJSIP" in channels_output:
                print("✅ Canales PJSIP activos detectados")
                
                # Colgar la llamada
                run_asterisk_command("hangup all")
                print("✅ Llamada de prueba finalizada")
                return True
            else:
                print("⚠️ No se detectaron canales activos")
                return False
        else:
            print(f"❌ Error en llamada de prueba: {output}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando llamada: {e}")
        return False

def main():
    print_header("🎯 VERIFICACIÓN DE INTEGRACIÓN VOIP")
    
    print("Este script verificará que la integración con Asterisk esté funcionando correctamente")
    print("y que las extensiones puedan realizar llamadas entre sí.")
    
    # Lista de verificaciones
    checks = [
        ("Estado de Asterisk", check_asterisk_status),
        ("Endpoints PJSIP", check_pjsip_endpoints),
        ("Dialplan", check_dialplan),
        ("Datos del sistema", lambda: load_system_data() != (None, None)),
        ("Configuraciones de softphone", check_softphone_configs),
        ("Llamada de prueba", test_extension_call)
    ]
    
    passed = 0
    total = len(checks)
    
    for i, (name, check_func) in enumerate(checks, 1):
        print_step(str(i), f"Verificando {name}")
        
        try:
            if check_func():
                print(f"✅ {name}: PASÓ")
                passed += 1
            else:
                print(f"❌ {name}: FALLÓ")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
    
    print_header("📊 RESUMEN DE VERIFICACIÓN")
    
    print(f"📈 RESULTADOS:")
    print(f"   ✅ Verificaciones exitosas: {passed}/{total}")
    
    if passed == total:
        print_header("🎉 ¡INTEGRACIÓN COMPLETAMENTE FUNCIONAL!")
        
        print("🔥 El sistema VoIP está completamente integrado:")
        print("   • ✅ Asterisk funcionando correctamente")
        print("   • ✅ Endpoints PJSIP configurados")
        print("   • ✅ Dialplan operativo")
        print("   • ✅ Extensiones asignadas")
        print("   • ✅ Configuraciones de softphone disponibles")
        print("   • ✅ Llamadas entre extensiones funcionando")
        
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Configura softphones con las credenciales generadas")
        print("   2. Registra los softphones en el servidor")
        print("   3. Realiza llamadas reales entre extensiones")
        print("   4. Configura proveedores VoIP externos si es necesario")
        
        print("\n📱 CONFIGURACIONES DISPONIBLES EN:")
        print("   data/softphone_configs/")
        
        print("\n🎯 ¡SISTEMA LISTO PARA LLAMADAS REALES!")
        
    else:
        print_header("⚠️ INTEGRACIÓN INCOMPLETA")
        
        print(f"❌ {total - passed} verificaciones fallaron")
        print("📋 ACCIONES REQUERIDAS:")
        
        if passed < 3:
            print("   1. Verifica que Asterisk esté configurado correctamente")
            print("   2. Revisa los archivos de configuración en /etc/asterisk/")
            print("   3. Reinicia Asterisk: sudo systemctl restart asterisk")
        
        if passed >= 3:
            print("   1. Ejecuta: python generate_softphone_configs_enhanced.py")
            print("   2. Verifica que las extensiones estén asignadas a agentes")
            print("   3. Prueba registrar un softphone manualmente")
    
    return passed == total

if __name__ == "__main__":
    main()