#!/usr/bin/env python3
# Archivo: ~/voip-auto-dialer/scripts/test_manual_load.py

import subprocess
import time
import os

def run_asterisk_cmd(cmd):
    """Ejecutar comando de Asterisk y capturar salida"""
    full_cmd = f"sudo asterisk -rx '{cmd}'"
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1
    except Exception as e:
        return "", str(e), 1

def test_pjsip_reload():
    """Test específico de recarga PJSIP"""
    print("🔄 TESTING RECARGA PJSIP")
    print("-" * 40)
    
    commands = [
        ("pjsip show endpoints", "Endpoints ANTES de recarga"),
        ("module unload res_pjsip.so", "Descargar módulo PJSIP"),
        ("module load res_pjsip.so", "Cargar módulo PJSIP"),
        ("pjsip show endpoints", "Endpoints DESPUÉS de recarga"),
        ("pjsip show transports", "Verificar transports"),
    ]
    
    for cmd, description in commands:
        print(f"\n📋 {description}:")
        print(f"   🔧 Ejecutando: {cmd}")
        
        stdout, stderr, code = run_asterisk_cmd(cmd)
        
        print(f"   📤 Código: {code}")
        if stdout.strip():
            # Mostrar solo líneas relevantes
            lines = stdout.strip().split('\n')
            relevant_lines = [line for line in lines if line.strip() and 
                            not line.startswith('Endpoint:') and 
                            'Objects found' not in line][:5]
            for line in relevant_lines:
                print(f"   📥 {line}")
        
        if stderr.strip():
            print(f"   ⚠️  Error: {stderr.strip()}")
        
        time.sleep(2)

def test_config_syntax():
    """Test de sintaxis de configuración"""
    print("\n🔍 TESTING SINTAXIS DE CONFIGURACIÓN")
    print("-" * 40)
    
    # Test de sintaxis con Asterisk
    stdout, stderr, code = run_asterisk_cmd("core show config mappings")
    print(f"📋 Config mappings disponibles: {code == 0}")
    
    # Intentar recargar solo PJSIP
    stdout, stderr, code = run_asterisk_cmd("module reload res_pjsip.so")
    print(f"🔄 Recarga res_pjsip.so: {code == 0}")
    if stderr:
        print(f"   ⚠️  Error: {stderr}")

def create_minimal_test():
    """Crear configuración mínima para test"""
    print("\n🧪 CREANDO TEST MÍNIMO")
    print("-" * 40)
    
    minimal_config = """
;=== TEST MÍNIMO ===
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

[1000]
type=endpoint
context=from-internal
disallow=all
allow=ulaw
auth=1000
aors=1000

[1000]
type=auth
auth_type=userpass
password=test123
username=1000

[1000]
type=aor
max_contacts=1
"""
    
    test_file = "/tmp/pjsip_test.conf"
    try:
        with open(test_file, 'w') as f:
            f.write(minimal_config)
        print(f"✅ Archivo test creado: {test_file}")
        
        # Backup del archivo actual
        if os.path.exists("/etc/asterisk/pjsip.conf"):
            subprocess.run("sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup", shell=True)
            print("✅ Backup creado: pjsip.conf.backup")
        
        # Copiar test
        subprocess.run(f"sudo cp {test_file} /etc/asterisk/pjsip.conf", shell=True)
        print("✅ Configuración test copiada")
        
        # Recargar
        stdout, stderr, code = run_asterisk_cmd("pjsip reload")
        print(f"🔄 Recarga test: {code == 0}")
        
        # Verificar
        stdout, stderr, code = run_asterisk_cmd("pjsip show endpoints")
        print("📋 Resultado test:")
        if stdout:
            print(f"   {stdout.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def main():
    print("🧪 TEST DE CARGA MANUAL PJSIP")
    print("=" * 50)
    
    # Test 1: Recarga normal
    test_pjsip_reload()
    
    # Test 2: Sintaxis
    test_config_syntax()
    
    # Test 3: Configuración mínima
    print("\n" + "=" * 50)
    print("⚠️  ADVERTENCIA: El siguiente test modificará pjsip.conf temporalmente")
    response = input("¿Continuar con test mínimo? (y/N): ")
    
    if response.lower() == 'y':
        success = create_minimal_test()
        
        if success:
            print("\n🔄 RESTAURANDO CONFIGURACIÓN ORIGINAL...")
            subprocess.run("sudo cp /etc/asterisk/pjsip.conf.backup /etc/asterisk/pjsip.conf", shell=True)
            run_asterisk_cmd("pjsip reload")
            print("✅ Configuración original restaurada")
    
    print("\n" + "=" * 50)
    print("🎯 TEST COMPLETADO")
    print("=" * 50)

if __name__ == "__main__":
    main()