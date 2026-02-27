# VoIP Auto Dialer - Sistema Configurado

## 🚀 Sistema Listo para Usar

El sistema ha sido configurado con datos de prueba y está listo para funcionar.

### Componentes Configurados:

#### ✅ Extensiones (1000-1020)
- 21 extensiones SIP creadas
- Contraseñas: pass1000, pass1001, etc.
- Servidor: 127.0.0.1:5060

#### ✅ Agentes de Prueba
- 5 agentes creados
- 3 agentes con extensiones asignadas
- 2 agentes disponibles para asignación

#### ✅ Campaña de Prueba
- Campaña "Campaña de Prueba" creada
- 3 leads de prueba incluidos
- Lista para activar y probar

#### ✅ Proveedores
- Asterisk local configurado
- Proveedor de prueba incluido

### Cómo Usar:

1. **Iniciar el servidor:**
   ```bash
   python start_web_server.py
   ```

2. **Acceder al dashboard:**
   ```
   http://localhost:8000
   ```

3. **Probar funcionalidades:**
   - Gestión de agentes: http://localhost:8000/agents
   - Gestión de extensiones: http://localhost:8000/extensions
   - Gestión de proveedores: http://localhost:8000/providers
   - Gestión de campañas: http://localhost:8000/campaigns

### API Endpoints Principales:

#### Auto Dialer:
- `GET /api/dialer/stats` - Estadísticas del dialer
- `POST /api/dialer/start/{campaign_id}` - Iniciar marcado
- `POST /api/dialer/stop/{campaign_id}` - Detener marcado
- `POST /api/dialer/test-call` - Llamada de prueba

#### Campañas:
- `GET /api/campaigns` - Listar campañas
- `POST /api/campaigns` - Crear campaña
- `POST /api/campaigns/{id}/start` - Iniciar campaña

#### Agentes:
- `GET /api/agents` - Listar agentes
- `POST /api/agents` - Crear agente
- `POST /api/agents/{id}/assign-extension` - Asignar extensión

#### Extensiones:
- `GET /api/extensions/all` - Listar extensiones
- `POST /api/extensions/{id}/regenerate-password` - Nueva contraseña

### Próximos Pasos:

1. **Configurar Asterisk real** (opcional)
2. **Importar leads reales** a las campañas
3. **Configurar proveedores VoIP** reales
4. **Personalizar horarios** de llamada
5. **Configurar grabación** de llamadas

### Estructura de Archivos:

```
voip-auto-dialer/
├── core/                    # Lógica principal
│   ├── auto_dialer.py      # Sistema de marcado automático
│   ├── sip_manager.py      # Gestión de llamadas SIP
│   ├── extension_manager.py # Gestión de extensiones
│   └── agent_manager_clean.py # Gestión de agentes
├── web/                     # Interfaz web
│   └── main.py             # Servidor FastAPI
├── data/                    # Datos del sistema
│   ├── extensions.json     # Extensiones configuradas
│   └── agents.json         # Agentes creados
├── campaigns/               # Campañas
│   └── test-campaign-001.json
├── config/                  # Configuración
│   └── providers.json      # Proveedores VoIP
└── start_web_server.py     # Punto de entrada principal
```

¡El sistema está listo para usar! 🎉
