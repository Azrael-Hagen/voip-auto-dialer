#!/usr/bin/env python3
"""
🎯 CONFIGURADOR COMPLETO DEL SISTEMA VOIP
================================================================
Configura todo el sistema VoIP para llamadas reales entre extensiones
"""

import json
import os
import subprocess
import time
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step, description):
    print(f"\n{step}. 📋 {description}")
    print("-" * 50)

def load_system_data():
    """Cargar datos del sistema"""
    try:
        agents = {}
        extensions = {}
        
        if os.path.exists('data/agents.json'):
            with open('data/agents.json', 'r') as f:
                agents = json.load(f)
        
        if os.path.exists('data/extensions.json'):
            with open('data/extensions.json', 'r') as f:
                extensions = json.load(f)
        
        return agents, extensions
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return {}, {}

def create_asterisk_integration():
    """Crear integración completa con Asterisk"""
    print("🔧 Creando integración con Asterisk...")
    
    # Script de sincronización
    sync_script = '''#!/usr/bin/env python3
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
        f.write('\\n'.join(pjsip_config))
    
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
        f.write('\\n'.join(extensions_config))
    
    print(f"✅ Dialplan guardado: {config_file}")
    return True

def main():
    print("🎯 SINCRONIZACIÓN CON ASTERISK")
    print("="*50)
    
    if generate_pjsip_config() and generate_extensions_config():
        print("\\n✅ Sincronización completada exitosamente")
        print("\\n📋 PRÓXIMOS PASOS:")
        print("1. Copia asterisk_config/pjsip_extensions.conf a /etc/asterisk/")
        print("2. Copia asterisk_config/extensions_voip.conf a /etc/asterisk/")
        print("3. Incluye los archivos en tu configuración principal")
        print("4. Reinicia Asterisk: sudo systemctl restart asterisk")
        return True
    else:
        print("\\n❌ Error en la sincronización")
        return False

if __name__ == "__main__":
    main()
'''
    
    with open('sync_extensions_to_asterisk.py', 'w') as f:
        f.write(sync_script)
    
    os.chmod('sync_extensions_to_asterisk.py', 0o755)
    print("✅ Script de sincronización creado")

def create_softphone_configs():
    """Crear generador de configuraciones de softphone"""
    print("📱 Creando generador de configuraciones...")
    
    config_script = '''#!/usr/bin/env python3
"""
Generador de configuraciones de softphone
Crea archivos de configuración para Zoiper, PortSIP, etc.
"""

import json
import os
from datetime import datetime

def generate_zoiper_config(extension, password, agent_name):
    """Generar configuración para Zoiper"""
    config = f"""[{extension}]
username={extension}
password={password}
domain=localhost
proxy=localhost:5060
transport=UDP
display_name={agent_name}
enabled=1
register=1
"""
    return config

def generate_portsip_config(extension, password, agent_name):
    """Generar configuración para PortSIP"""
    config = f"""<?xml version="1.0" encoding="UTF-8"?>
<PortSIP>
    <Account>
        <DisplayName>{agent_name}</DisplayName>
        <UserName>{extension}</UserName>
        <Password>{password}</Password>
        <SIPServer>localhost</SIPServer>
        <SIPServerPort>5060</SIPServerPort>
        <Transport>UDP</Transport>
        <RegisterServer>localhost</RegisterServer>
        <RegisterServerPort>5060</RegisterServerPort>
    </Account>
</PortSIP>
"""
    return config

def generate_generic_config(extension, password, agent_name):
    """Generar configuración genérica"""
    config = f"""=== CONFIGURACIÓN SIP ===
Extensión: {extension}
Contraseña: {password}
Servidor SIP: localhost
Puerto: 5060
Transporte: UDP
Nombre: {agent_name}

=== INSTRUCCIONES ===
1. Instala tu aplicación SIP favorita
2. Crea una nueva cuenta SIP
3. Usa los datos de arriba
4. Guarda y registra la cuenta
5. ¡Ya puedes hacer llamadas!

=== APLICACIONES RECOMENDADAS ===
• Zoiper (Windows, Mac, Linux, Mobile)
• PortSIP (Windows, Mac, Mobile)
• Linphone (Multiplataforma)
• X-Lite (Windows, Mac)
"""
    return config

def main():
    print("🎯 GENERANDO CONFIGURACIONES DE SOFTPHONE")
    print("="*50)
    
    # Cargar datos
    if not os.path.exists('data/agents.json'):
        print("❌ No se encontró data/agents.json")
        return False
    
    with open('data/agents.json', 'r') as f:
        agents = json.load(f)
    
    # Crear directorio de configuraciones
    config_dir = 'data/softphone_configs'
    os.makedirs(config_dir, exist_ok=True)
    
    configs_generated = 0
    
    for agent_id, agent_data in agents.items():
        extension_info = agent_data.get('extension_info')
        if not extension_info:
            continue
        
        extension = extension_info['extension']
        password = extension_info['password']
        agent_name = agent_data['name']
        
        # Generar configuraciones
        zoiper_config = generate_zoiper_config(extension, password, agent_name)
        portsip_config = generate_portsip_config(extension, password, agent_name)
        generic_config = generate_generic_config(extension, password, agent_name)
        
        # Guardar archivos
        with open(f"{config_dir}/zoiper_config_{extension}.conf", 'w') as f:
            f.write(zoiper_config)
        
        with open(f"{config_dir}/portsip_config_{extension}.xml", 'w') as f:
            f.write(portsip_config)
        
        with open(f"{config_dir}/sip_config_{extension}.txt", 'w') as f:
            f.write(generic_config)
        
        configs_generated += 1
        print(f"✅ Configuraciones generadas para {agent_name} (Ext: {extension})")
    
    print(f"\\n📊 Total configuraciones generadas: {configs_generated}")
    print(f"📁 Archivos guardados en: {config_dir}/")
    
    return True

if __name__ == "__main__":
    main()
'''
    
    with open('generate_softphone_configs_enhanced.py', 'w') as f:
        f.write(config_script)
    
    os.chmod('generate_softphone_configs_enhanced.py', 0o755)
    print("✅ Generador de configuraciones creado")

def create_web_endpoints():
    """Crear endpoints web para descargar configuraciones"""
    print("🌐 Creando endpoints web...")
    
    web_endpoints = '''#!/usr/bin/env python3
"""
Endpoints web para descargar configuraciones de softphone
Agregar estas rutas a tu servidor web principal
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import json

router = APIRouter()

@router.get("/api/softphone-config/{agent_id}/{app_type}")
async def download_softphone_config(agent_id: str, app_type: str):
    """Descargar configuración de softphone para un agente"""
    
    # Validar tipo de aplicación
    valid_apps = ['zoiper', 'portsip', 'generic']
    if app_type not in valid_apps:
        raise HTTPException(status_code=400, detail="Tipo de aplicación no válido")
    
    # Buscar agente
    if not os.path.exists('data/agents.json'):
        raise HTTPException(status_code=404, detail="Datos de agentes no encontrados")
    
    with open('data/agents.json', 'r') as f:
        agents = json.load(f)
    
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agents[agent_id]
    extension_info = agent.get('extension_info')
    
    if not extension_info:
        raise HTTPException(status_code=400, detail="Agente sin extensión asignada")
    
    # Determinar archivo de configuración
    extension = extension_info['extension']
    
    if app_type == 'zoiper':
        filename = f"zoiper_config_{extension}.conf"
        content_type = "text/plain"
    elif app_type == 'portsip':
        filename = f"portsip_config_{extension}.xml"
        content_type = "application/xml"
    else:  # generic
        filename = f"sip_config_{extension}.txt"
        content_type = "text/plain"
    
    config_path = f"data/softphone_configs/{filename}"
    
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    # Retornar archivo
    return FileResponse(
        path=config_path,
        filename=filename,
        media_type=content_type
    )

# Agregar estas rutas a tu aplicación FastAPI principal:
# app.include_router(router)
'''
    
    with open('web_softphone_endpoints.py', 'w') as f:
        f.write(web_endpoints)
    
    print("✅ Endpoints web creados")

def create_installation_guide():
    """Crear guía de instalación completa"""
    print("📖 Creando guía de instalación...")
    
    guide = f'''# 🎯 GUÍA COMPLETA DE INSTALACIÓN - SISTEMA VOIP

## 📋 RESUMEN DEL SISTEMA
Sistema VoIP completo para llamadas reales entre extensiones usando softphones.

Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 🔧 PASO 1: CONFIGURAR ASTERISK

### 1.1 Copiar archivos de configuración
```bash
# Copiar configuraciones generadas
sudo cp asterisk_config/pjsip_extensions.conf /etc/asterisk/
sudo cp asterisk_config/extensions_voip.conf /etc/asterisk/
```

### 1.2 Incluir configuraciones en archivos principales

**En /etc/asterisk/pjsip.conf:**
```
#include pjsip_extensions.conf
```

**En /etc/asterisk/extensions.conf:**
```
#include extensions_voip.conf
```

### 1.3 Reiniciar Asterisk
```bash
sudo systemctl restart asterisk
sudo asterisk -rx "core reload"
```

## 🔧 PASO 2: VERIFICAR CONFIGURACIÓN

### 2.1 Verificar endpoints
```bash
sudo asterisk -rx "pjsip show endpoints"
```

### 2.2 Verificar dialplan
```bash
sudo asterisk -rx "dialplan show from-internal"
```

## 📱 PASO 3: CONFIGURAR SOFTPHONES

### 3.1 Descargar configuraciones
- Ve a http://localhost:8000/agents
- Haz clic en "Configurar" para un agente
- Descarga la configuración para tu softphone

### 3.2 Aplicaciones recomendadas

**Zoiper (Multiplataforma)**
- Descarga: https://www.zoiper.com/
- Importa el archivo .conf descargado

**PortSIP (Windows/Mac/Mobile)**
- Descarga: https://www.portsip.com/
- Importa el archivo .xml descargado

**Linphone (Código abierto)**
- Descarga: https://www.linphone.org/
- Configura manualmente con los datos del archivo .txt

### 3.3 Configuración manual
Si prefieres configurar manualmente:

1. **Servidor SIP**: localhost (o IP del servidor)
2. **Puerto**: 5060
3. **Transporte**: UDP
4. **Usuario**: Número de extensión (ej: 1500)
5. **Contraseña**: La generada automáticamente
6. **Nombre**: Nombre del agente

## 🧪 PASO 4: PROBAR EL SISTEMA

### 4.1 Ejecutar prueba rápida
```bash
python quick_voip_test.py
```

### 4.2 Probar registro de extensiones
1. Abre tu softphone
2. Verifica que aparezca como "Registrado" o "Online"
3. En Asterisk CLI: `pjsip show endpoints`

### 4.3 Probar llamadas
1. Configura al menos 2 softphones
2. Desde uno, marca el número de extensión del otro
3. Verifica que suene y se pueda contestar

## 🔍 SOLUCIÓN DE PROBLEMAS

### Problema: Extensión no se registra
**Solución:**
```bash
# Verificar configuración PJSIP
sudo asterisk -rx "pjsip show endpoint XXXX"

# Verificar logs
sudo tail -f /var/log/asterisk/full
```

### Problema: Llamada no conecta
**Solución:**
```bash
# Verificar dialplan
sudo asterisk -rx "dialplan show from-internal"

# Probar llamada manualmente
sudo asterisk -rx "channel originate PJSIP/1500 extension 1501@from-internal"
```

### Problema: Audio no funciona
**Solución:**
- Verificar firewall (puertos 5060 UDP, 10000-20000 UDP)
- Configurar NAT si es necesario
- Verificar códecs permitidos

## 📊 MONITOREO

### Ver llamadas activas
```bash
sudo asterisk -rx "core show calls"
```

### Ver estadísticas
```bash
sudo asterisk -rx "pjsip show registrations"
```

## 🎉 ¡LISTO!

Si todo funciona correctamente:
- ✅ Extensiones registradas
- ✅ Llamadas entre extensiones funcionando
- ✅ Audio bidireccional
- ✅ Sistema web operativo

## 📞 PRÓXIMOS PASOS

1. **Configurar proveedores externos** para llamadas salientes
2. **Implementar campañas automatizadas**
3. **Agregar más agentes y extensiones**
4. **Configurar grabación de llamadas**
5. **Implementar reportes avanzados**

---
*Generado automáticamente por el Sistema VoIP Auto Dialer*
'''
    
    with open('INSTALLATION_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("✅ Guía de instalación creada")

def create_quick_test_script():
    """Crear script de prueba rápida"""
    print("🧪 Creando script de prueba rápida...")
    
    test_script = '''#!/usr/bin/env python3
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
    
    print(f"\\n📊 Resultado: {passed}/{len(tests)} pruebas pasaron")
    
    if passed == len(tests):
        print("🎉 Sistema VoIP listo para usar!")
    else:
        print("⚠️ Revisa la configuración antes de continuar")

if __name__ == "__main__":
    main()
'''
    
    with open('quick_voip_test.py', 'w') as f:
        f.write(test_script)
    
    os.chmod('quick_voip_test.py', 0o755)
    print("✅ Script de prueba creado")

def main():
    print_header("🎯 CONFIGURADOR COMPLETO DEL SISTEMA VOIP")
    
    print("Este script configurará todo el sistema VoIP para llamadas reales")
    print("entre extensiones usando softphones como Zoiper, PortSIP, etc.")
    
    # Cargar datos del sistema
    print_step("1", "Verificando datos del sistema")
    agents, extensions = load_system_data()
    
    if not agents:
        print("❌ No se encontraron agentes en el sistema")
        print("   Crea agentes desde la interfaz web primero")
        return False
    
    assigned_count = sum(1 for ext in extensions.values() if ext.get('status') == 'assigned')
    print(f"✅ Sistema cargado: {len(agents)} agentes, {assigned_count} extensiones asignadas")
    
    # Crear integración con Asterisk
    print_step("2", "Creando integración con Asterisk")
    create_asterisk_integration()
    
    # Crear generador de configuraciones
    print_step("3", "Creando generador de configuraciones de softphone")
    create_softphone_configs()
    
    # Ejecutar sincronización
    print_step("4", "Ejecutando sincronización con Asterisk")
    try:
        result = subprocess.run("python sync_extensions_to_asterisk.py", 
                              shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Sincronización con Asterisk completada")
        else:
            print("⚠️ Problemas en la sincronización")
    except Exception as e:
        print(f"⚠️ Error ejecutando sincronización: {e}")
    
    # Generar configuraciones de softphone
    print_step("5", "Generando configuraciones de softphone")
    try:
        result = subprocess.run("python generate_softphone_configs_enhanced.py", 
                              shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Configuraciones de softphone generadas")
        else:
            print("⚠️ Problemas generando configuraciones")
    except Exception as e:
        print(f"⚠️ Error generando configuraciones: {e}")
    
    # Crear endpoints web
    print_step("6", "Creando endpoints web")
    create_web_endpoints()
    
    # Crear guía de instalación
    print_step("7", "Creando guía de instalación")
    create_installation_guide()
    
    # Crear script de prueba rápida
    print_step("8", "Creando script de prueba rápida")
    create_quick_test_script()
    
    print_header("✅ CONFIGURACIÓN COMPLETA FINALIZADA")
    
    print("🎉 ¡Sistema VoIP completamente configurado!")
    print("")
    print("📋 ARCHIVOS GENERADOS:")
    print("   • sync_extensions_to_asterisk.py - Sincronización con Asterisk")
    print("   • generate_softphone_configs_enhanced.py - Generador de configs")
    print("   • web_softphone_endpoints.py - Endpoints para descargar configs")
    print("   • INSTALLATION_GUIDE.md - Guía completa de instalación")
    print("   • quick_voip_test.py - Script de prueba rápida")
    print("")
    print("🔧 PRÓXIMOS PASOS:")
    print("   1. Lee INSTALLATION_GUIDE.md para instrucciones detalladas")
    print("   2. Configura Asterisk con los archivos generados")
    print("   3. Ejecuta: python quick_voip_test.py")
    print("   4. Configura softphones con las configuraciones generadas")
    print("   5. ¡Realiza llamadas reales entre extensiones!")
    print("")
    print("📱 CONFIGURACIONES DE SOFTPHONE EN:")
    print("   data/softphone_configs/")
    print("")
    print("🎯 ¡SISTEMA LISTO PARA LLAMADAS REALES!")
    
    return True

if __name__ == "__main__":
    main()

