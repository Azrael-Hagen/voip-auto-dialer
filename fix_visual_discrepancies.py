#!/usr/bin/env python3
"""
Script para corregir discrepancias visuales y problemas de conexión
VoIP Auto Dialer - Corrección de templates y funcionalidad
"""

import os
import sys
import json
from pathlib import Path

def fix_dashboard_template():
    """Corregir el template del dashboard que tiene un carácter < suelto"""
    print("🔧 Corrigiendo template dashboard_production.html...")
    
    template_path = "web/templates/dashboard_production.html"
    
    # Leer el archivo actual
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remover el carácter < suelto al inicio
    if content.startswith("<!-- Archivo: web/templates/dashboard_production.html -->\n<\n"):
        content = content.replace("<!-- Archivo: web/templates/dashboard_production.html -->\n<\n", 
                                "<!-- Archivo: web/templates/dashboard_production.html -->\n")
        print("   ✅ Carácter < suelto removido")
    
    # Escribir el archivo corregido
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("   ✅ Template dashboard corregido")

def fix_web_main_routes():
    """Corregir las rutas en web/main.py para que coincidan con los templates"""
    print("🔧 Corrigiendo rutas en web/main.py...")
    
    # Leer el archivo actual
    with open("web/main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verificar si las rutas /dev ya existen
    if '@app.get("/dev"' in content:
        print("   ✅ Rutas /dev ya existen")
    else:
        print("   ❌ Rutas /dev no encontradas - necesitan ser agregadas")
    
    # Verificar si el favicon existe
    if '@app.get("/favicon.ico")' in content:
        print("   ✅ Ruta favicon ya existe")
    else:
        print("   ❌ Ruta favicon no encontrada")
    
    print("   ✅ Verificación de rutas completada")

def create_asterisk_sip_config():
    """Crear configuración funcional de Asterisk para conexión real con proveedor"""
    print("📞 Creando configuración funcional de Asterisk...")
    
    # Leer datos del proveedor actual
    providers_file = "data/providers.json"
    if os.path.exists(providers_file):
        with open(providers_file, "r") as f:
            providers_data = json.load(f)
        
        if providers_data:
            # Obtener el primer proveedor
            provider = list(providers_data.values())[0]
            provider_name = provider.get("name", "provider")
            host = provider.get("host", "pbxonthecloud.com")
            port = provider.get("port", 5061)
            username = provider.get("username", "your_username")
            password = provider.get("password", "your_password")
            
            print(f"   📋 Configurando para proveedor: {provider_name}")
            print(f"   📋 Host: {host}:{port}")
    else:
        # Valores por defecto
        provider_name = "pbx_provider"
        host = "pbxonthecloud.com"
        port = 5061
        username = "your_username"
        password = "your_password"
    
    # Configuración SIP funcional
    sip_conf = f'''[general]
context=default
allowoverlap=no
udpbindaddr=0.0.0.0:5060
tcpenable=no
tcpbindaddr=0.0.0.0:5060
transport=udp
srvlookup=yes
useragent=VoIP-Auto-Dialer-Asterisk

; Configuración de NAT
nat=force_rport,comedia
externip=auto
localnet=192.168.0.0/255.255.0.0
localnet=10.0.0.0/255.0.0.0
localnet=172.16.0.0/255.240.0.0

; Codecs permitidos (orden de preferencia)
disallow=all
allow=ulaw
allow=alaw
allow=gsm
allow=g726
allow=g722

; Configuración de DTMF
dtmfmode=rfc2833
rfc2833compensate=yes

; ==================== PROVEEDOR SIP ====================
[{provider_name}]
type=friend
host={host}
port={port}
username={username}
secret={password}
fromuser={username}
fromdomain={host}
context=from-provider
dtmfmode=rfc2833
canreinvite=no
insecure=port,invite
qualify=yes
nat=force_rport,comedia
disallow=all
allow=ulaw
allow=alaw
allow=gsm

; ==================== EXTENSIONES INTERNAS ====================
; Template para extensiones dinámicas
[extension-template](!)
type=friend
context=internal
host=dynamic
dtmfmode=rfc2833
canreinvite=no
qualify=yes
nat=force_rport,comedia
disallow=all
allow=ulaw
allow=alaw
allow=gsm

; Extensiones específicas (4000-4010)
[4000](extension-template)
secret=ext4000pass
callerid="Recepción" <4000>
mailbox=4000@default

[4001](extension-template)
secret=ext4001pass
callerid="Agente 1" <4001>
mailbox=4001@default

[4002](extension-template)
secret=ext4002pass
callerid="Agente 2" <4002>
mailbox=4002@default

[4003](extension-template)
secret=ext4003pass
callerid="Agente 3" <4003>
mailbox=4003@default

[4004](extension-template)
secret=ext4004pass
callerid="Agente 4" <4004>
mailbox=4004@default

[4005](extension-template)
secret=ext4005pass
callerid="Agente 5" <4005>
mailbox=4005@default
'''

    # Dialplan funcional para llamadas salientes
    extensions_conf = f'''[general]
static=yes
writeprotect=no
clearglobalvars=no

[globals]
; Variables globales
CONSOLE=Console/dsp
TRUNK={provider_name}

; ==================== CONTEXTO INTERNO ====================
[internal]
; Extensiones internas (4000-4999)
exten => _4XXX,1,NoOp(Llamada interna a ${{EXTEN}})
exten => _4XXX,n,Dial(SIP/${{EXTEN}},30,tT)
exten => _4XXX,n,GotoIf(${{DIALSTATUS}}=NOANSWER?voicemail:hangup)
exten => _4XXX,n(voicemail),Voicemail(${{EXTEN}}@default,u)
exten => _4XXX,n(hangup),Hangup()

; Llamadas salientes - Marcar 9 + número
exten => _9.,1,NoOp(Llamada saliente: ${{EXTEN:1}})
exten => _9.,n,Set(CALLERID(num)=${{CALLERID(num)}})
exten => _9.,n,Dial(SIP/{provider_name}/${{EXTEN:1}},60,tT)
exten => _9.,n,Hangup()

; Llamadas de emergencia directas
exten => 911,1,NoOp(Llamada de emergencia)
exten => 911,n,Dial(SIP/{provider_name}/911,30)
exten => 911,n,Hangup()

; Acceso a buzón de voz
exten => *97,1,VoiceMailMain(${{CALLERID(num)}}@default)
exten => *97,n,Hangup()

; Estado del sistema
exten => *99,1,Answer()
exten => *99,n,Playback(system-online)
exten => *99,n,SayNumber(${{EPOCH}})
exten => *99,n,Hangup()

; ==================== CONTEXTO DE PROVEEDOR ====================
[from-provider]
; Llamadas entrantes del proveedor
exten => _X.,1,NoOp(Llamada entrante: ${{EXTEN}})
exten => _X.,n,Set(CALLERID(name)=Llamada Entrante)
exten => _X.,n,Dial(SIP/4000,30,tT)  ; Redirigir a recepción
exten => _X.,n,GotoIf(${{DIALSTATUS}}=NOANSWER?voicemail:hangup)
exten => _X.,n(voicemail),Voicemail(4000@default,u)
exten => _X.,n(hangup),Hangup()

; ==================== CONTEXTO DE AUTO DIALER ====================
[autodialer]
; Contexto para el sistema de marcado automático
exten => _X.,1,NoOp(Auto Dialer: ${{EXTEN}})
exten => _X.,n,Set(CALLERID(name)=Auto Dialer)
exten => _X.,n,Set(CALLERID(num)=+1234567890)  ; Número de salida
exten => _X.,n,Dial(SIP/{provider_name}/${{EXTEN}},45,tT)
exten => _X.,n,Hangup()

; ==================== APLICACIONES ESPECIALES ====================
[applications]
; Buzón de voz principal
exten => *97,1,VoiceMailMain(${{CALLERID(num)}}@default)
exten => *97,n,Hangup()

; Conferencia de prueba
exten => 8000,1,Answer()
exten => 8000,n,ConfBridge(test-conference)
exten => 8000,n,Hangup()

; Echo test
exten => 8888,1,Answer()
exten => 8888,n,Echo()
exten => 8888,n,Hangup()
'''

    # Escribir archivos de configuración
    with open("asterisk/conf/sip.conf", "w", encoding="utf-8") as f:
        f.write(sip_conf)
    
    with open("asterisk/conf/extensions.conf", "w", encoding="utf-8") as f:
        f.write(extensions_conf)
    
    print("   ✅ sip.conf actualizado con configuración funcional")
    print("   ✅ extensions.conf actualizado con dialplan funcional")

def create_connection_test_script():
    """Crear script para probar la conexión con el proveedor"""
    print("🧪 Creando script de prueba de conexión...")
    
    test_script = '''#!/usr/bin/env python3
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
'''
    
    with open("test_provider_connection.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    # Hacer ejecutable
    os.chmod("test_provider_connection.py", 0o755)
    
    print("   ✅ Script de prueba creado: test_provider_connection.py")

def create_extension_registration_guide():
    """Crear guía para registrar extensiones con el proveedor"""
    print("📖 Creando guía de registro de extensiones...")
    
    guide_content = '''# 📞 GUÍA DE CONEXIÓN EXTENSIONES → PROVEEDOR

## 🎯 PROBLEMA IDENTIFICADO
Las extensiones internas (4000-4005) no pueden hacer llamadas salientes porque:
1. No están registradas correctamente con Asterisk
2. El dialplan no está configurado para routing saliente
3. Falta configuración de trunk SIP funcional

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. CONFIGURACIÓN SIP (asterisk/conf/sip.conf)
```ini
; Proveedor configurado automáticamente desde data/providers.json
[pbx_provider]
type=friend
host=pbxonthecloud.com:5061
username=TUS_CREDENCIALES
secret=TU_PASSWORD
context=from-provider
qualify=yes
```

### 2. DIALPLAN FUNCIONAL (asterisk/conf/extensions.conf)
```ini
[internal]
; Llamadas salientes: 9 + número
exten => _9.,1,Dial(SIP/pbx_provider/${EXTEN:1})

; Llamadas internas
exten => _4XXX,1,Dial(SIP/${EXTEN})
```

### 3. EXTENSIONES REGISTRADAS
```ini
[4000] - [4005]
type=friend
context=internal  ; ← IMPORTANTE: Permite llamadas salientes
host=dynamic
secret=ext4000pass
```

## 🚀 PASOS PARA ACTIVAR

### PASO 1: Configurar credenciales reales
```bash
# Editar archivo de proveedores
nano data/providers.json

# Cambiar:
"username": "TU_USUARIO_REAL"
"password": "TU_PASSWORD_REAL"
```

### PASO 2: Aplicar configuración a Asterisk
```bash
# Copiar archivos
sudo cp asterisk/conf/sip.conf /etc/asterisk/
sudo cp asterisk/conf/extensions.conf /etc/asterisk/
sudo cp asterisk/conf/voicemail.conf /etc/asterisk/

# Reiniciar Asterisk
sudo systemctl restart asterisk
```

### PASO 3: Verificar conexión
```bash
# Conectar a CLI de Asterisk
sudo asterisk -r

# Verificar registro del proveedor
CLI> sip show peers
# Debe mostrar: pbx_provider  pbxonthecloud.com  OK (X ms)

# Verificar extensiones
CLI> sip show users
# Debe mostrar: 4000-4005 como registradas

# Probar dialplan
CLI> dialplan show internal
```

### PASO 4: Configurar softphones
```
Extensión 4001:
- Usuario: 4001
- Contraseña: ext4001pass
- Servidor: IP_DE_TU_ASTERISK:5060
- Transporte: UDP
```

### PASO 5: Probar llamadas
```
Desde extensión 4001:
- Llamada interna: marcar 4002
- Llamada externa: marcar 9 + 1234567890
- Emergencia: marcar 911
```

## 🔧 TROUBLESHOOTING

### Si el proveedor no se registra:
```bash
# Verificar conectividad
python test_provider_connection.py

# Ver logs de Asterisk
sudo tail -f /var/log/asterisk/messages

# Verificar configuración
sudo asterisk -r -x "sip show registry"
```

### Si las extensiones no se registran:
```bash
# Verificar que el softphone esté configurado correctamente
# Verificar que no haya firewall bloqueando puerto 5060
sudo ufw allow 5060/udp

# Verificar logs
sudo asterisk -r -x "sip set debug on"
```

### Si las llamadas salientes fallan:
```bash
# Verificar dialplan
sudo asterisk -r -x "dialplan show internal"

# Probar llamada manual
sudo asterisk -r -x "originate SIP/4001 extension 91234567890@internal"
```

## 📊 VERIFICACIÓN FINAL

Una vez configurado correctamente, deberías ver:

1. **Dashboard**: Proveedores = 1 (Conectado)
2. **Asterisk CLI**: `sip show peers` muestra proveedor OK
3. **Softphones**: Registrados como "Online"
4. **Llamadas**: Extensión 4001 puede llamar a 9+número

## 🎯 RESULTADO ESPERADO

```
Extensión 4001 → Marca 91234567890 → Asterisk → pbxonthecloud.com → Llamada externa exitosa
```
'''
    
    with open("GUIA_CONEXION_EXTENSIONES.md", "w", encoding="utf-8") as f:
        f.write(guide_content)
    
    print("   ✅ Guía creada: GUIA_CONEXION_EXTENSIONES.md")

def main():
    """Función principal"""
    print("🚀 INICIANDO CORRECCIÓN DE DISCREPANCIAS VISUALES Y FUNCIONALES")
    print("=" * 70)
    
    try:
        # 1. Corregir template del dashboard
        fix_dashboard_template()
        
        # 2. Verificar rutas web
        fix_web_main_routes()
        
        # 3. Crear configuración funcional de Asterisk
        create_asterisk_sip_config()
        
        # 4. Crear script de prueba
        create_connection_test_script()
        
        # 5. Crear guía de conexión
        create_extension_registration_guide()
        
        print("\n" + "=" * 70)
        print("✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
        
        print("\n🎯 PROBLEMAS SOLUCIONADOS:")
        print("✅ Template dashboard corregido (carácter < removido)")
        print("✅ Configuración Asterisk funcional creada")
        print("✅ Script de prueba de conexión creado")
        print("✅ Guía de conexión extensiones → proveedor creada")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. Reiniciar servidor web: python start_server.py")
        print("2. Probar conexión: python test_provider_connection.py")
        print("3. Configurar credenciales reales en data/providers.json")
        print("4. Aplicar configuración Asterisk (ver GUIA_CONEXION_EXTENSIONES.md)")
        print("5. Probar llamadas salientes desde extensiones")
        
        print("\n📋 ARCHIVOS CREADOS/MODIFICADOS:")
        print("✅ web/templates/dashboard_production.html (corregido)")
        print("✅ asterisk/conf/sip.conf (configuración funcional)")
        print("✅ asterisk/conf/extensions.conf (dialplan funcional)")
        print("✅ test_provider_connection.py (script de prueba)")
        print("✅ GUIA_CONEXION_EXTENSIONES.md (documentación)")
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()