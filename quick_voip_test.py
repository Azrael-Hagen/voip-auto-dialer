#!/usr/bin/env python3
"""
Script de prueba rápida del sistema VoIP
"""

import subprocess
import time

def test_asterisk():
    """Probar que Asterisk esté funcionando"""
    print("🔍 Probando Asterisk...")
    result = subprocess.run("sudo asterisk -rx 'core show version'", 
                          shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Asterisk funcionando")
        return True
    else:
        print("❌ Asterisk no responde")
        return False

def test_extensions():
    """Probar extensiones registradas"""
    print("🔍 Probando extensiones...")
    result = subprocess.run("sudo asterisk -rx 'pjsip show endpoints'", 
                          shell=True, capture_output=True, text=True)
    if "Endpoint:" in result.stdout:
        print("✅ Extensiones encontradas")
        return True
    else:
        print("❌ No se encontraron extensiones")
        return False

def main():
    print("🎯 PRUEBA RÁPIDA DEL SISTEMA VOIP")
    print("="*50)
    
    tests = [
        ("Asterisk", test_asterisk),
        ("Extensiones", test_extensions)
    ]
    
    passed = 0
    for name, test_func in tests:
        if test_func():
            passed += 1
        time.sleep(1)
    
    print(f"\n📊 Resultado: {passed}/{len(tests)} pruebas pasaron")
    
    if passed == len(tests):
        print("🎉 Sistema VoIP listo para usar!")
    else:
        print("⚠️ Revisa la configuración antes de continuar")

if __name__ == "__main__":
    main()
