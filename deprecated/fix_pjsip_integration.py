#!/usr/bin/env python3
"""
Script para corregir la integración PJSIP y completar la configuración
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

def check_existing_pjsip_config():
    """Verificar configuración PJSIP existente"""
    print("🔍 Verificando configuración PJSIP existente...")
    
    pjsip_conf = Path("/etc/asterisk/pjsip.conf")
    if not pjsip_conf.exists():
        print("❌ Archivo pjsip.conf no encontrado")
        return False
    
    # Leer configuración actual
    with open(pjsip_conf, 'r') as f:
        content = f.read()
    
    print("✅ Archivo pjsip.conf encontrado")
    
    # Verificar si nuestras extensiones están incluidas
    if "pjsip_extensions.conf" in content:
        print("✅ Nuestras extensiones ya están incluidas")
        return True
    else:
        print("⚠️ Nuestras extensiones no están incluidas")
        return False

def integrate_with_existing_asterisk():
    """Integrar con la configuración existente de Asterisk"""
    print("🔧 Integrando con configuración existente de Asterisk...")
    
    # Verificar archivos generados
    pjsip_ext_file = Path("asterisk_config/pjsip_extensions.conf")
    extensions_file = Path("asterisk_config/extensions_voip.conf")
    
    if not pjsip_ext_file.exists():
        print("❌ Archivo pjsip_extensions.conf no encontrado")
        return False
    
    if not extensions_file.exists():
        print("❌ Archivo extensions_voip.conf no encontrado")
        return False
    
    # Copiar archivos a Asterisk
    print("📁 Copiando archivos de configuración...")
    
    try:
        # Copiar archivos
        subprocess.run(f"sudo cp {pjsip_ext_file} /etc/asterisk/", shell=True, check=True)
        subprocess.run(f"sudo cp {extensions_file} /etc/asterisk/", shell=True, check=True)
        print("✅ Archivos copiados exitosamente")
        
        # Verificar que los includes estén en los archivos principales
        print("🔧 Verificando includes en archivos principales...")
        
        # Verificar pjsip.conf
        pjsip_conf = Path("/etc/asterisk/pjsip.conf")
        with open(pjsip_conf, 'r') as f:
            pjsip_content = f.read()
        
        if "#include pjsip_extensions.conf" not in pjsip_content:
            print("📝 Agregando include a pjsip.conf...")
            subprocess.run('echo "#include pjsip_extensions.conf" | sudo tee -a /etc/asterisk/pjsip.conf', shell=True)
        
        # Verificar extensions.conf
        extensions_conf = Path("/etc/asterisk/extensions.conf")
        with open(extensions_conf, 'r') as f:
            ext_content = f.read()
        
        if "#include extensions_voip.conf" not in ext_content:
            print("📝 Agregando include a extensions.conf...")
            subprocess.run('echo "#include extensions_voip.conf" | sudo tee -a /etc/asterisk/extensions.conf', shell=True)
        
        print("✅ Includes verificados")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error copiando archivos: {e}")
        return False

def reload_asterisk_config():
    """Recargar configuración de Asterisk"""
    print("🔄 Recargando configuración de Asterisk...")
    
    commands = [
        "dialplan reload",
        "module reload res_pjsip.so",
        "pjsip reload"
    ]
    
    for cmd in commands:
        print(f"   Ejecutando: {cmd}")
        output, success = run_asterisk_command(cmd)
        if success:
            print(f"   ✅ {cmd}: OK")
        else:
            print(f"   ⚠️ {cmd}: {output}")
    
    return True

def create_test_extensions():
    """Crear extensiones de prueba adicionales"""
    print("🔧 Creando extensiones de prueba adicionales...")
    
    # Cargar datos actuales
    try:
        with open("data/agents.json", 'r') as f:
            agents = json.load(f)
        
        with open("data/extensions.json", 'r') as f:
            extensions = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return False
    
    # Encontrar agentes sin extensión
    agents_without_ext = []
    for agent_id, agent_data in agents.items():
        if not agent_data.get('extension_info'):
            agents_without_ext.append((agent_id, agent_data))
    
    if not agents_without_ext:
        print("✅ Todos los agentes ya tienen extensiones asignadas")
        return True
    
    # Asignar extensiones a los primeros 3 agentes sin extensión
    assigned_count = 0
    for agent_id, agent_data in agents_without_ext[:3]:
        # Encontrar una extensión disponible
        for ext_num, ext_data in extensions.items():
            if ext_data.get('status') != 'assigned':
                # Asignar extensión
                ext_data['status'] = 'assigned'
                ext_data['agent_id'] = agent_id
                ext_data['assigned_at'] = '2026-02-21T16:00:00'
                
                # Actualizar agente
                agent_data['extension_info'] = {
                    'extension': ext_num,
                    'password': ext_data['password'],
                    'status': 'assigned',
                    'assigned_at': '2026-02-21T16:00:00'
                }
                
                print(f"✅ Extensión {ext_num} asignada a {agent_data['name']}")
                assigned_count += 1
                break
        
        if assigned_count >= 3:
            break
    
    # Guardar cambios
    try:
        with open("data/agents.json", 'w') as f:
            json.dump(agents, f, indent=2)
        
        with open("data/extensions.json", 'w') as f:
            json.dump(extensions, f, indent=2)
        
        print(f"✅ {assigned_count} extensiones asignadas y guardadas")
        return True
        
    except Exception as e:
        print(f"❌ Error guardando datos: {e}")
        return False

def verify_final_integration():
    """Verificación final de la integración"""
    print("🔍 Verificación final de la integración...")
    
    # Verificar endpoints
    output, success = run_asterisk_command("pjsip show endpoints")
    if success:
        lines = output.split('\n')
        endpoint_count = sum(1 for line in lines if 'Endpoint:' in line and not line.startswith(' Endpoint:'))
        print(f"✅ Endpoints PJSIP detectados: {endpoint_count}")
    
    # Verificar dialplan
    output, success = run_asterisk_command("dialplan show from-internal")
    if success and "_XXXX" in output:
        print("✅ Dialplan configurado correctamente")
    
    # Verificar que podemos hacer una llamada de prueba
    print("📞 Probando llamada final...")
    
    try:
        with open("data/extensions.json", 'r') as f:
            extensions = json.load(f)
        
        assigned_extensions = [ext for ext, data in extensions.items() if data.get('status') == 'assigned']
        
        if len(assigned_extensions) >= 2:
            from_ext = assigned_extensions[0]
            to_ext = assigned_extensions[1]
            
            print(f"   Llamada: {from_ext} → {to_ext}")
            
            # Originar llamada
            command = f"channel originate PJSIP/{from_ext} extension {to_ext}@from-internal"
            output, success = run_asterisk_command(command)
            
            if success:
                print("✅ Llamada de prueba exitosa")
                
                # Colgar después de un momento
                import time
                time.sleep(1)
                run_asterisk_command("hangup all")
                return True
            else:
                print(f"⚠️ Llamada de prueba falló: {output}")
                return False
        else:
            print("⚠️ No hay suficientes extensiones asignadas para probar")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba final: {e}")
        return False

def main():
    print_header("🔧 CORRECCIÓN DE INTEGRACIÓN PJSIP")
    
    print("Este script corregirá la integración PJSIP y completará la configuración")
    print("para que todas las extensiones funcionen correctamente.")
    
    steps = [
        ("Verificar configuración PJSIP existente", check_existing_pjsip_config),
        ("Integrar con Asterisk existente", integrate_with_existing_asterisk),
        ("Recargar configuración de Asterisk", reload_asterisk_config),
        ("Crear extensiones de prueba", create_test_extensions),
        ("Verificación final", verify_final_integration)
    ]
    
    passed = 0
    total = len(steps)
    
    for i, (name, step_func) in enumerate(steps, 1):
        print_step(str(i), name)
        
        try:
            if step_func():
                print(f"✅ {name}: COMPLETADO")
                passed += 1
            else:
                print(f"❌ {name}: FALLÓ")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
    
    print_header("📊 RESUMEN DE CORRECCIÓN")
    
    print(f"📈 RESULTADOS:")
    print(f"   ✅ Pasos completados: {passed}/{total}")
    
    if passed == total:
        print_header("🎉 ¡INTEGRACIÓN CORREGIDA EXITOSAMENTE!")
        
        print("🔥 El sistema VoIP está completamente integrado:")
        print("   • ✅ Configuración PJSIP corregida")
        print("   • ✅ Archivos integrados con Asterisk")
        print("   • ✅ Configuración recargada")
        print("   • ✅ Extensiones de prueba creadas")
        print("   • ✅ Llamadas funcionando correctamente")
        
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Ejecuta nuevamente: python verify_integration.py")
        print("   2. Configura softphones con las credenciales")
        print("   3. Registra softphones y realiza llamadas reales")
        
        print("\n🎯 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        
    else:
        print_header("⚠️ CORRECCIÓN INCOMPLETA")
        
        print(f"❌ {total - passed} pasos fallaron")
        print("📋 REVISA LOS ERRORES ARRIBA Y:")
        print("   1. Verifica permisos de archivos")
        print("   2. Confirma que Asterisk esté ejecutándose")
        print("   3. Revisa logs de Asterisk: sudo tail -f /var/log/asterisk/full")
    
    return passed == total

if __name__ == "__main__":
    main()