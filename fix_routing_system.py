
#!/usr/bin/env python3
"""
Script para corregir rutas 404 y problemas de configuración
VoIP Auto Dialer - Sistema de corrección de routing
"""

import os
import sys
import json
from pathlib import Path

def create_missing_directories():
    """Crear directorios faltantes"""
    print("📁 Creando directorios faltantes...")
    
    directories = [
        "web/logs",
        "web/static/images",
        "asterisk/conf",
        "asterisk/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")

def create_favicon():
    """Crear favicon básico"""
    print("🎨 Creando favicon...")
    
    favicon_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
    <rect width="32" height="32" fill="#2563eb"/>
    <text x="16" y="20" text-anchor="middle" fill="white" font-family="Arial" font-size="16" font-weight="bold">V</text>
</svg>'''
    
    with open("web/static/images/favicon.svg", "w") as f:
        f.write(favicon_content)
    print("   ✅ favicon.svg creado")

def fix_web_routes():
    """Corregir rutas faltantes en web/main.py"""
    print("🔧 Corrigiendo rutas web...")
    
    # Leer el archivo actual
    with open("web/main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Agregar rutas faltantes antes del último bloque
    additional_routes = '''
# ==================== RUTAS DE DESARROLLO ====================
@app.get("/dev", response_class=HTMLResponse)
async def dev_dashboard(request: Request):
    """Dashboard de desarrollo"""
    return templates.TemplateResponse("dev_dashboard.html", {
        "request": request,
        "title": "Dashboard de Desarrollo"
    })

@app.get("/dev/agents", response_class=HTMLResponse)
async def dev_agents(request: Request):
    """Gestión avanzada de agentes"""
    agents = agent_manager.get_all_agents()
    return templates.TemplateResponse("dev_agents.html", {
        "request": request,
        "title": "Desarrollo - Agentes",
        "agents": agents
    })

@app.get("/favicon.ico")
async def favicon():
    """Servir favicon"""
    return FileResponse("web/static/images/favicon.svg", media_type="image/svg+xml")

# ==================== API ADICIONALES ====================
@app.get("/api/system/status")
async def system_status():
    """Estado del sistema completo"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "web_server": "running",
            "asterisk": "checking",
            "database": "connected",
            "auto_dialer": "ready"
        }
    }

@app.get("/api/campaigns")
async def get_campaigns():
    """Obtener campañas activas"""
    return {
        "campaigns": [],
        "active_count": 0,
        "total_calls": 0,
        "success_rate": 0.0
    }

'''
    
    # Insertar antes de la línea que contiene 'if __name__ == "__main__":'
    if 'if __name__ == "__main__":' in content:
        parts = content.split('if __name__ == "__main__":')
        new_content = parts[0] + additional_routes + '\nif __name__ == "__main__":' + parts[1]
    else:
        new_content = content + additional_routes
    
    # Escribir el archivo corregido
    with open("web/main.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("   ✅ Rutas web corregidas")

def create_dev_templates():
    """Crear templates de desarrollo faltantes"""
    print("📄 Creando templates de desarrollo...")
    
    # Template para dev dashboard
    dev_dashboard_template = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - VoIP Auto Dialer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .navbar-brand { font-weight: bold; color: #2563eb !important; }
        .card-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .status-online { color: #10b981; }
        .dev-section { border-left: 4px solid #f59e0b; padding-left: 1rem; margin: 0; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-phone-alt me-2"></i>VoIP Auto Dialer
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text status-online">
                    <i class="fas fa-circle me-1"></i>Sistema Online
                </span>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h4 class="mb-0"><i class="fas fa-code me-2"></i>Dashboard de Desarrollo</h4>
                    </div>
                    <div class="card-body">
                        <div class="dev-section">
                            <h5><i class="fas fa-tools me-2"></i>Herramientas de Desarrollo</h5>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="list-group">
                                        <a href="/dev/agents" class="list-group-item list-group-item-action">
                                            <i class="fas fa-users me-2"></i>Gestión Avanzada de Agentes
                                        </a>
                                        <a href="/api/system/status" class="list-group-item list-group-item-action">
                                            <i class="fas fa-heartbeat me-2"></i>Estado del Sistema (API)
                                        </a>
                                        <a href="/api/campaigns" class="list-group-item list-group-item-action">
                                            <i class="fas fa-bullhorn me-2"></i>Campañas (API)
                                        </a>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="alert alert-info">
                                        <h6><i class="fas fa-info-circle me-2"></i>Información</h6>
                                        <p class="mb-0">Este es el dashboard de desarrollo para pruebas y configuración avanzada del sistema VoIP.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # Template para dev agents
    dev_agents_template = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - VoIP Auto Dialer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .navbar-brand { font-weight: bold; color: #2563eb !important; }
        .card-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .status-online { color: #10b981; }
        .agent-card { border-left: 4px solid #10b981; }
        .agent-offline { border-left-color: #ef4444; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-phone-alt me-2"></i>VoIP Auto Dialer
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dev">Dashboard Dev</a>
                <span class="navbar-text status-online">
                    <i class="fas fa-circle me-1"></i>Sistema Online
                </span>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h4 class="mb-0"><i class="fas fa-users-cog me-2"></i>Gestión Avanzada de Agentes</h4>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            {% for agent in agents %}
                            <div class="col-md-6 mb-3">
                                <div class="card agent-card {% if agent.status != 'online' %}agent-offline{% endif %}">
                                    <div class="card-body">
                                        <h6 class="card-title">{{ agent.name }}</h6>
                                        <p class="card-text">
                                            <small class="text-muted">
                                                <i class="fas fa-envelope me-1"></i>{{ agent.email }}<br>
                                                <i class="fas fa-phone me-1"></i>{{ agent.phone }}<br>
                                                <i class="fas fa-hashtag me-1"></i>Ext: {{ agent.extension or 'Sin asignar' }}
                                            </small>
                                        </p>
                                        <span class="badge {% if agent.status == 'online' %}bg-success{% else %}bg-secondary{% endif %}">
                                            {{ agent.status }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # Crear los archivos de template
    with open("web/templates/dev_dashboard.html", "w", encoding="utf-8") as f:
        f.write(dev_dashboard_template)
    
    with open("web/templates/dev_agents.html", "w", encoding="utf-8") as f:
        f.write(dev_agents_template)
    
    print("   ✅ Templates de desarrollo creados")

def create_asterisk_config():
    """Crear configuración básica de Asterisk para routing"""
    print("📞 Creando configuración de Asterisk...")
    
    # extensions.conf - Dialplan básico
    extensions_conf = '''[general]
static=yes
writeprotect=no
clearglobalvars=no

[globals]
; Configuración global
CONSOLE=Console/dsp
IAXINFO=guest
TRUNK=DAHDI/G2

; ==================== CONTEXTO INTERNO ====================
[internal]
; Extensiones internas (4000-4999)
exten => _4XXX,1,Dial(SIP/${EXTEN},20)
exten => _4XXX,n,Voicemail(${EXTEN}@default,u)
exten => _4XXX,n,Hangup()

; Acceso a líneas externas
exten => _9NXXNXXXXXX,1,Dial(SIP/provider/${EXTEN:1})
exten => _9NXXNXXXXXX,n,Hangup()

; Llamadas de emergencia
exten => 911,1,Dial(SIP/provider/911)
exten => 911,n,Hangup()

; ==================== CONTEXTO DE PROVEEDOR ====================
[from-provider]
; Llamadas entrantes del proveedor
exten => _X.,1,Dial(SIP/4000,20)  ; Redirigir a recepción
exten => _X.,n,Voicemail(4000@default,u)
exten => _X.,n,Hangup()

; ==================== CONTEXTO DE AUTO DIALER ====================
[autodialer]
; Contexto para el sistema de marcado automático
exten => _X.,1,Set(CALLERID(name)=Auto Dialer)
exten => _X.,2,Dial(SIP/provider/${EXTEN})
exten => _X.,3,Hangup()

; ==================== APLICACIONES ESPECIALES ====================
[applications]
; Buzón de voz
exten => *97,1,VoiceMailMain(${CALLERID(num)}@default)
exten => *97,n,Hangup()

; Estado del sistema
exten => *99,1,Answer()
exten => *99,n,Playback(system-status)
exten => *99,n,Hangup()
'''

    # sip.conf - Configuración SIP
    sip_conf = '''[general]
context=internal
allowoverlap=no
udpbindaddr=0.0.0.0
tcpenable=no
tcpbindaddr=0.0.0.0
transport=udp
srvlookup=yes
useragent=VoIP-Auto-Dialer-Asterisk

; Codecs permitidos
disallow=all
allow=ulaw
allow=alaw
allow=gsm
allow=g726
allow=g722

; ==================== PROVEEDOR SIP ====================
[provider]
type=friend
host=pbxonthecloud.com
port=5061
username=your_username
secret=your_password
fromuser=your_username
fromdomain=pbxonthecloud.com
context=from-provider
dtmfmode=rfc2833
canreinvite=no
insecure=port,invite
qualify=yes

; ==================== EXTENSIONES INTERNAS ====================
[4000]
type=friend
context=internal
host=dynamic
secret=ext4000pass
callerid="Recepción" <4000>
mailbox=4000@default

[4001]
type=friend
context=internal
host=dynamic
secret=ext4001pass
callerid="Agente 1" <4001>
mailbox=4001@default

[4002]
type=friend
context=internal
host=dynamic
secret=ext4002pass
callerid="Agente 2" <4002>
mailbox=4002@default

; ==================== TEMPLATE PARA EXTENSIONES DINÁMICAS ====================
[extension-template](!)
type=friend
context=internal
host=dynamic
dtmfmode=rfc2833
canreinvite=no
qualify=yes
nat=force_rport,comedia
'''

    # voicemail.conf - Configuración de buzón de voz
    voicemail_conf = '''[general]
format=wav49|gsm|wav
serveremail=asterisk
attach=yes
skipms=3000
maxsilence=10
silencethreshold=128
maxlogins=3

[default]
4000 => 1234,Recepción,recepcion@company.com
4001 => 1234,Agente 1,agente1@company.com
4002 => 1234,Agente 2,agente2@company.com
'''

    # Crear archivos de configuración
    configs = {
        "asterisk/conf/extensions.conf": extensions_conf,
        "asterisk/conf/sip.conf": sip_conf,
        "asterisk/conf/voicemail.conf": voicemail_conf
    }
    
    for filename, content in configs.items():
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ {filename}")

def main():
    """Función principal"""
    print("🚀 INICIANDO CORRECCIÓN DEL SISTEMA DE ROUTING")
    print("=" * 60)
    
    try:
        create_missing_directories()
        create_favicon()
        fix_web_routes()
        create_dev_templates()
        create_asterisk_config()
        
        print("\n" + "=" * 60)
        print("✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. Reiniciar el servidor: python start_server.py")
        print("2. Probar rutas: http://localhost:8000/dev")
        print("3. Configurar Asterisk con los archivos en asterisk/conf/")
        print("4. Verificar que no hay más errores 404")
        
        print("\n📋 RUTAS CORREGIDAS:")
        print("✅ /dev - Dashboard de desarrollo")
        print("✅ /dev/agents - Gestión avanzada de agentes")
        print("✅ /favicon.ico - Icono del sitio")
        print("✅ /api/system/status - Estado del sistema")
        print("✅ /api/campaigns - Información de campañas")
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

