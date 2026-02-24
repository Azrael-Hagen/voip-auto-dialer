#!/usr/bin/env python3
# Archivo: ~/voip-auto-dialer/scripts/verify_fix.py

import subprocess
import time

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("🔍 VERIFICACIÓN DE LA REPARACIÓN")
    print("=" * 50)
    
    # 1. Recargar PJSIP
    print("1️⃣ Recargando PJSIP...")
    stdout, stderr, code = run_cmd("sudo asterisk -rx 'pjsip reload'")
    print(f"   📤 Código: {code}")
    if stdout.strip():
        print(f"   📥 {stdout.strip()}")
    if stderr.strip():
        print(f"   ⚠️  {stderr.strip()}")
    
    time.sleep(3)
    
    # 2. Verificar endpoints
    print("\n2️⃣ Verificando endpoints...")
    stdout, stderr, code = run_cmd("sudo asterisk -rx 'pjsip show endpoints'")
    
    if "No objects found" in stdout:
        print("   ❌ TODAVÍA NO HAY ENDPOINTS")
        return False
    
    # Contar endpoints
    lines = stdout.split('\n')
    endpoint_lines = [line for line in lines if line.strip() and 
                     not line.startswith('Endpoint:') and 
                     not line.startswith('=') and
                     not 'Objects found' in line and
                     'Endpoint:' not in line]
    
    # Contar líneas que empiezan con espacio (son endpoints)
    endpoints = [line for line in lines if line.startswith(' Endpoint:')]
    
    print(f"   📊 Endpoints encontrados: {len(endpoints)}")
    
    if len(endpoints) > 0:
        print("   ✅ ¡ENDPOINTS CARGADOS EXITOSAMENTE!")
        
        # Mostrar algunos ejemplos
        print("\n   📋 Primeros 3 endpoints:")
        for line in endpoints[:3]:
            print(f"      {line.strip()}")
        
        if len(endpoints) > 3:
            print(f"      ... y {len(endpoints) - 3} más")
    
    # 3. Verificar transports
    print("\n3️⃣ Verificando transports...")
    stdout, stderr, code = run_cmd("sudo asterisk -rx 'pjsip show transports'")
    if "transport-udp" in stdout:
        print("   ✅ Transport UDP funcionando")
    
    # 4. Test de registro (simulado)
    print("\n4️⃣ Información para test de softphone:")
    print("   📞 Para probar registro, usar:")
    print("      - Servidor: IP de este equipo")
    print("      - Puerto: 5060")
    print("      - Usuario: 1000 (o cualquier extensión 1000-1501)")
    print("      - Contraseña: Verificar en extensions.json")
    
    print("\n" + "=" * 50)
    print("🎯 VERIFICACIÓN COMPLETADA")
    print("=" * 50)

if __name__ == "__main__":
    main()