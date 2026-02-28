#!/usr/bin/env python3
"""
Script para probar la conexión con el proveedor VoIP
"""

import socket
import json
import sys
from pathlib import Path

def test_provider_connection():
    """Probar conexión con el proveedor VoIP"""
    print("🔍 PROBANDO CONEXIÓN CON PROVEEDOR VoIP")
    print("=" * 50)
    
    # Leer configuración del proveedor
    providers_file = Path("data/providers.json")
    if not providers_file.exists():
        print("❌ Archivo de proveedores no encontrado")
        return False
    
    with open(providers_file, "r") as f:
        providers = json.load(f)
    
    if not providers:
        print("❌ No hay proveedores configurados")
        return False
    
    # Obtener primer proveedor
    provider = list(providers.values())[0]
    host = provider.get("host", "").replace(":5061", "")
    port = provider.get("port", 5061)
    
    print(f"📋 Proveedor: {provider.get('name', 'Unknown')}")
    print(f"📋 Host: {host}")
    print(f"📋 Puerto: {port}")
    print()
    
    # Test 1: Resolución DNS
    print("1. Probando resolución DNS...")
    try:
        import socket
        ip = socket.gethostbyname(host)
        print(f"   ✅ DNS OK: {host} → {ip}")
    except Exception as e:
        print(f"   ❌ Error DNS: {e}")
        return False
    
    # Test 2: Conectividad TCP
    print("2. Probando conectividad TCP...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Puerto {port} abierto")
        else:
            print(f"   ❌ Puerto {port} cerrado o filtrado")
            return False
    except Exception as e:
        print(f"   ❌ Error conectividad: {e}")
        return False
    
    # Test 3: Ping básico
    print("3. Probando ping...")
    import subprocess
    try:
        result = subprocess.run(
            ["ping", "-c", "3", host], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print("   ✅ Ping exitoso")
        else:
            print("   ⚠️  Ping falló (puede ser normal si ICMP está bloqueado)")
    except Exception as e:
        print(f"   ⚠️  Error ping: {e}")
    
    print()
    print("✅ CONEXIÓN BÁSICA EXITOSA")
    print()
    print("📋 PRÓXIMOS PASOS:")
    print("1. Configurar credenciales reales en data/providers.json")
    print("2. Aplicar configuración: sudo cp asterisk/conf/* /etc/asterisk/")
    print("3. Reiniciar Asterisk: sudo systemctl restart asterisk")
    print("4. Verificar registro: sudo asterisk -r -x 'sip show peers'")
    
    return True

if __name__ == "__main__":
    test_provider_connection()
