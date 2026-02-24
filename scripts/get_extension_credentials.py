#!/usr/bin/env python3
import json
import sys

def get_credentials(extension_number):
    try:
        with open('/home/azrael/voip-auto-dialer/data/extensions.json', 'r') as f:
            extensions = json.load(f)
        
        for ext in extensions:
            if ext['extension'] == extension_number:
                print(f"🔐 CREDENCIALES PARA EXTENSIÓN {extension_number}:")
                print(f"   📞 Usuario: {ext['extension']}")
                print(f"   🔑 Contraseña: {ext['password']}")
                print(f"   🌐 Servidor: {ext['server_ip']} (o IP de tu equipo)")
                print(f"   🔌 Puerto: 5060")
                print(f"   📋 Contexto: from-internal")
                return True
        
        print(f"❌ Extensión {extension_number} no encontrada")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 get_extension_credentials.py <numero_extension>")
        print("Ejemplo: python3 get_extension_credentials.py 1000")
        sys.exit(1)
    
    extension = sys.argv[1]
    get_credentials(extension)
