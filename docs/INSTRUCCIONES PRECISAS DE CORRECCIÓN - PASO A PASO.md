
# INSTRUCCIONES PRECISAS DE CORRECCIÓN - PASO A PASO

## CORRECCIÓN 1: Arreglar import crítico

**ARCHIVO**: `start_web_server_integration.py`
**LÍNEA**: 16
**ACCIÓN**: Cambiar la línea 16

**ANTES**:
```python
from web.dialer_endpoints import add_dialer_routes_to_app
```

**DESPUÉS**:
```python
from dialer_endpoints import add_dialer_routes_to_app
```

---

## CORRECCIÓN 2: Arreglar template roto

**ARCHIVO**: `web/templates/dashboard_production.html`
**LÍNEA**: 2
**ACCIÓN**: Eliminar el carácter `<` suelto

**ANTES**:
```html
<!-- Archivo: web/templates/dashboard_production.html -->
<
{% extends "base.html" %}
```

**DESPUÉS**:
```html
<!-- Archivo: web/templates/dashboard_production.html -->
{% extends "base.html" %}
```

---

## CORRECCIÓN 3: Agregar rutas faltantes a main.py

**ARCHIVO**: `web/main.py`
**UBICACIÓN**: Después de la línea que contiene `@app.get("/extensions", response_class=HTMLResponse)`
**ACCIÓN**: Agregar estas rutas completas

```python
@app.get("/dev", response_class=HTMLResponse)
async def dev_panel_page(request: Request):
    """Panel de desarrollo principal"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Panel de Desarrollo - VoIP Auto Dialer</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Panel de Desarrollo</h1>
            <p class="lead">Herramientas de desarrollo y configuración avanzada</p>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Gestión de Agentes</h5>
                            <p class="card-text">Administrar agentes del sistema</p>
                            <a href="/dev/agents" class="btn btn-primary">Ir a Agentes</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Gestión de Campañas</h5>
                            <p class="card-text">Administrar campañas de llamadas</p>
                            <a href="/dev/campaigns" class="btn btn-primary">Ir a Campañas</a>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-3">
                <a href="/" class="btn btn-secondary">Volver al Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/dev/agents", response_class=HTMLResponse)
async def dev_agents_page(request: Request):
    """Página de desarrollo para gestión de agentes"""
    return templates.TemplateResponse("agents_clean.html", {"request": request})

@app.get("/dev/campaigns", response_class=HTMLResponse)
async def dev_campaigns_page(request: Request):
    """Página de desarrollo para gestión de campañas"""
    return templates.TemplateResponse("campaigns_clean.html", {"request": request})
```

---

## CORRECCIÓN 4: Integrar auto dialer con servidor principal

**ARCHIVO**: `web/main.py`
**UBICACIÓN**: Después de las importaciones (alrededor de línea 30)
**ACCIÓN**: Agregar estas líneas

```python
# Integración del Auto Dialer
try:
    from start_web_server_integration import integrate_dialer_with_existing_app
    integrate_dialer_with_existing_app(app)
    logger.info("✅ Auto Dialer integrado exitosamente")
except Exception as e:
    logger.warning(f"⚠️ Auto Dialer no pudo integrarse: {e}")
```

---

## VERIFICACIÓN DE CORRECCIONES

### Después de aplicar las correcciones, ejecutar:

```bash
# 1. Probar que no hay errores de import
python -c "from start_web_server_integration import integrate_dialer_with_existing_app; print('Import OK')"

# 2. Iniciar servidor principal
python web/main.py

# 3. Verificar rutas en navegador:
# http://localhost:8000/ (Dashboard principal)
# http://localhost:8000/dev (Panel desarrollo)
# http://localhost:8000/dev/agents (Gestión agentes)
# http://localhost:8000/providers (Proveedores)
```

---

## RESULTADO ESPERADO

1. **Sin errores de ModuleNotFoundError**
2. **Dashboard profesional funcionando** (imagen 2 - azul corporativo)
3. **Rutas de desarrollo accesibles** (/dev/agents, /dev/campaigns)
4. **Auto dialer integrado** sin reemplazar interfaz principal
5. **Templates renderizando correctamente** sin errores HTML

---

## NOTAS IMPORTANTES

- **MANTENER** el diseño azul corporativo del dashboard profesional
- **NO REEMPLAZAR** la interfaz existente
- **SOLO AGREGAR** funcionalidad de auto dialer como endpoints adicionales
- **VERIFICAR** cada corrección antes de continuar con la siguiente
