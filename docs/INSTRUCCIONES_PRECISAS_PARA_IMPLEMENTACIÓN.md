
# 🎯 INSTRUCCIONES PRECISAS PARA IMPLEMENTACIÓN

## 📋 **METODOLOGÍA ESTABLECIDA**
- ✅ Instrucciones precisas con código y ubicaciones exactas
- ✅ Verificación de claridad para evitar errores
- ✅ Reducir conversaciones aumentando productividad
- ✅ Funcionamiento antes de pruebas

## 🚀 **IMPLEMENTACIÓN PASO A PASO**

### **PASO 1: ACTUALIZAR README.md**
**UBICACIÓN**: `./voip-auto-dialer/README.md`
**ACCIÓN**: Reemplazar TODO el contenido del archivo

```markdown
# VoIP Auto Dialer - Sistema Profesional Integrado

## 🚀 SISTEMA PRINCIPAL
- **Servidor Principal**: `web/main.py` (Dashboard profesional azul)
- **Dashboard**: http://localhost:8000 (6 agentes, 519 extensiones)
- **Auto Dialer**: Integrado en dashboard principal

## 📊 FUNCIONALIDADES
- ✅ Dashboard profesional con métricas en tiempo real
- ✅ Gestión de 6 agentes registrados
- ✅ Gestión de 519 extensiones SIP
- ✅ Sistema de proveedores VoIP
- ✅ Auto dialer integrado con detección AMD
- ✅ Transferencia automática a agentes

## 🚀 INICIO RÁPIDO
1. `cd voip-auto-dialer`
2. `source venv/bin/activate`
3. `python web/main.py`
4. Abrir: http://localhost:8000

## 🔗 ENDPOINTS AUTO DIALER
- `GET /api/dialer/status` - Estado del sistema
- `POST /api/dialer/campaigns/{id}/start` - Iniciar marcado
- `POST /api/dialer/campaigns/{id}/stop` - Detener marcado
- `POST /api/dialer/test-call` - Llamada de prueba

## 📁 ESTRUCTURA
```
voip-auto-dialer/
├── web/main.py                    # Servidor principal (TU SISTEMA)
├── web/templates/                 # Templates profesionales azules
├── core/                          # Módulos del sistema
└── data/                          # Datos (6 agentes, 519 extensiones)
```

## ⚠️ ARCHIVOS OBSOLETOS
Los siguientes archivos han sido eliminados por conflictos:
- `start_web_server.py` (reemplazaba tu sistema)
- `web/dialer_endpoints.py` (integrado en main.py)
```

### **PASO 2: CORREGIR IMPORTS EN setup_initial_data.py**
**UBICACIÓN**: `./voip-auto-dialer/setup_initial_data.py`
**ACCIÓN**: Buscar y reemplazar las siguientes líneas

**LÍNEA 16 - CAMBIAR:**
```python
# ❌ INCORRECTO:
from core.agent_manager_clean import AgentManager, AgentStatus

# ✅ CORRECTO:
from core.agent_manager_clean import AgentManager
```

**LÍNEAS 101-117 - CAMBIAR:**
```python
# ❌ INCORRECTO:
agents_data = [
    {
        "name": "Juan Pérez",
        "extension": "2001",
        "email": "juan.perez@empresa.com",
        "skills": ["ventas", "soporte"],
        "status": AgentStatus.AVAILABLE,
        "max_concurrent_calls": 1
    },
    # ... más agentes con AgentStatus.AVAILABLE
]

# ✅ CORRECTO:
agents_data = [
    {
        "name": "Juan Pérez",
        "extension": "2001",
        "email": "juan.perez@empresa.com",
        "skills": ["ventas", "soporte"],
        "status": "available",
        "max_concurrent_calls": 1
    },
    # ... más agentes con "available"
]
```

### **PASO 3: CORREGIR IMPORTS EN test_complete_system.py**
**UBICACIÓN**: `./voip-auto-dialer/test_complete_system.py`
**ACCIÓN**: Buscar y reemplazar la línea 16

**LÍNEA 16 - CAMBIAR:**
```python
# ❌ INCORRECTO:
from core.call_detector import CallDetector, CallResult

# ✅ CORRECTO:
from core.call_detector import CallDetector, CallStatus
```

**LÍNEA ~85 - CAMBIAR:**
```python
# ❌ INCORRECTO:
await call_detector._simulate_call_answered(test_call_id, CallResult.ANSWERED_HUMAN)

# ✅ CORRECTO:
await call_detector._execute_callback(CallStatus.ANSWERED_HUMAN, {"call_id": test_call_id})
```

### **PASO 4: INTEGRAR AUTO DIALER EN web/main.py**
**UBICACIÓN**: `./voip-auto-dialer/web/main.py`
**ACCIÓN**: Agregar AL FINAL del archivo (después de la última línea)

```python

# ============================================================================
# AUTO DIALER INTEGRATION - AGREGADO PARA FUNCIONALIDAD DE MARCADO AUTOMÁTICO
# ============================================================================

# Importar componentes del auto dialer
try:
    from core.dialer_integration import dialer_integration
    from core.call_detector import CallDetector
    from core.agent_transfer_system import AgentTransferSystem
    from core.auto_dialer_engine import AutoDialerEngine
    
    auto_dialer_available = True
    logger.info("✅ Componentes del auto dialer cargados exitosamente")
    
except ImportError as e:
    auto_dialer_available = False
    logger.warning(f"⚠️ Auto dialer no disponible: {e}")

# Endpoints del Auto Dialer
if auto_dialer_available:
    
    @app.get("/api/dialer/status")
    async def get_dialer_status():
        """Estado del sistema de marcado automático"""
        try:
            status = dialer_integration.get_dialer_status()
            return {"success": True, "data": status}
        except Exception as e:
            logger.error(f"Error obteniendo estado del dialer: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/dialer/campaigns/{campaign_id}/start")
    async def start_campaign_dialing(campaign_id: str, config: dict = None):
        """Iniciar marcado automático para una campaña"""
        try:
            if not config:
                config = {
                    "calls_per_minute": 10,
                    "max_concurrent_calls": 3,
                    "mode": "power"
                }
            result = await dialer_integration.start_campaign_dialing(campaign_id, config)
            return result
        except Exception as e:
            logger.error(f"Error iniciando campaña: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/dialer/campaigns/{campaign_id}/stop")
    async def stop_campaign_dialing(campaign_id: str):
        """Detener marcado automático para una campaña"""
        try:
            result = await dialer_integration.stop_campaign_dialing(campaign_id)
            return result
        except Exception as e:
            logger.error(f"Error deteniendo campaña: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/dialer/test-call")
    async def make_test_call(call_data: dict):
        """Realizar llamada de prueba"""
        try:
            phone_number = call_data.get("phone_number")
            if not phone_number:
                raise HTTPException(status_code=400, detail="phone_number es requerido")
            result = await dialer_integration.make_test_call(phone_number)
            return result
        except Exception as e:
            logger.error(f"Error en llamada de prueba: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/dialer/campaigns")
    async def get_available_campaigns():
        """Obtener campañas disponibles para marcado"""
        try:
            result = dialer_integration.get_available_campaigns()
            return result
        except Exception as e:
            logger.error(f"Error obteniendo campañas: {e}")
            raise HTTPException(status_code=500, detail=str(e))

else:
    # Endpoints dummy si el auto dialer no está disponible
    @app.get("/api/dialer/status")
    async def dialer_not_available():
        return {"success": False, "message": "Auto dialer no disponible"}
    
    @app.post("/api/dialer/campaigns/{campaign_id}/start")
    async def dialer_not_available_start(campaign_id: str):
        return {"success": False, "message": "Auto dialer no disponible"}
    
    @app.post("/api/dialer/campaigns/{campaign_id}/stop")
    async def dialer_not_available_stop(campaign_id: str):
        return {"success": False, "message": "Auto dialer no disponible"}
    
    @app.post("/api/dialer/test-call")
    async def dialer_not_available_test():
        return {"success": False, "message": "Auto dialer no disponible"}
    
    @app.get("/api/dialer/campaigns")
    async def dialer_not_available_campaigns():
        return {"success": False, "message": "Auto dialer no disponible"}

logger.info("🚀 Servidor VoIP Auto Dialer con integración completa iniciado")
```

### **PASO 5: AGREGAR SECCIÓN AUTO DIALER AL DASHBOARD**
**UBICACIÓN**: `./voip-auto-dialer/web/templates/dashboard_production.html`
**ACCIÓN**: Buscar la línea que contiene `<!-- Sistema de Auto-Registro -->` (aproximadamente línea 100) y agregar ANTES de esa sección:

```html
    <!-- AUTO DIALER SECTION - AGREGADO PARA FUNCIONALIDAD DE MARCADO AUTOMÁTICO -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card shadow">
                <div class="card-header py-3 d-flex justify-content-between align-items-center">
                    <h6 class="m-0 font-weight-bold text-primary">
                        <i class="fas fa-robot me-2"></i>Auto Dialer - Marcado Automático
                    </h6>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-success btn-sm" id="startAutoDialer">
                            <i class="fas fa-play me-1"></i>Iniciar
                        </button>
                        <button type="button" class="btn btn-danger btn-sm" id="stopAutoDialer">
                            <i class="fas fa-stop me-1"></i>Detener
                        </button>
                        <button type="button" class="btn btn-info btn-sm" id="testCall">
                            <i class="fas fa-phone me-1"></i>Llamada de Prueba
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="text-center">
                                <div class="text-xs font-weight-bold text-uppercase mb-1">Estado</div>
                                <div class="h6 mb-0" id="autoDialerStatus">
                                    <span class="text-secondary">Detenido</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <div class="text-xs font-weight-bold text-uppercase mb-1">Llamadas Activas</div>
                                <div class="h6 mb-0" id="activeCalls">0</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <div class="text-xs font-weight-bold text-uppercase mb-1">Campañas Activas</div>
                                <div class="h6 mb-0" id="activeCampaigns">0</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <div class="text-xs font-weight-bold text-uppercase mb-1">Llamadas/Min</div>
                                <div class="h6 mb-0" id="callsPerMinute">0</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
```

### **PASO 6: AGREGAR JAVASCRIPT PARA AUTO DIALER**
**UBICACIÓN**: `./voip-auto-dialer/web/templates/dashboard_production.html`
**ACCIÓN**: Buscar el final del script existente (antes de `</script>`) y agregar:

```javascript

// ============================================================================
// AUTO DIALER FUNCTIONS - AGREGADO PARA FUNCIONALIDAD DE MARCADO AUTOMÁTICO
// ============================================================================

// Cargar estado del auto dialer
async function loadAutoDialerStatus() {
    try {
        const response = await fetch('/api/dialer/status');
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.data) {
                updateAutoDialerUI(data.data);
            }
        }
    } catch (error) {
        console.error('Error cargando estado del auto dialer:', error);
    }
}

function updateAutoDialerUI(dialerData) {
    if (dialerData && dialerData.engine_stats) {
        const stats = dialerData.engine_stats;
        
        // Actualizar estado
        const statusElement = document.getElementById('autoDialerStatus');
        if (statusElement) {
            statusElement.innerHTML = stats.is_running ? 
                '<span class="text-success">Activo</span>' : 
                '<span class="text-secondary">Detenido</span>';
        }
        
        // Actualizar métricas
        const activeCallsElement = document.getElementById('activeCalls');
        if (activeCallsElement) {
            activeCallsElement.textContent = stats.active_calls || 0;
        }
        
        const activeCampaignsElement = document.getElementById('activeCampaigns');
        if (activeCampaignsElement) {
            activeCampaignsElement.textContent = dialerData.total_active_campaigns || 0;
        }
        
        const callsPerMinuteElement = document.getElementById('callsPerMinute');
        if (callsPerMinuteElement) {
            callsPerMinuteElement.textContent = stats.calls_per_minute || 0;
        }
    }
}

// Event listeners para botones del auto dialer
document.addEventListener('DOMContentLoaded', function() {
    // Tu código existente se mantiene...
    
    // Agregar funcionalidad del auto dialer
    loadAutoDialerStatus();
    
    // Botón Iniciar Auto Dialer
    const startButton = document.getElementById('startAutoDialer');
    if (startButton) {
        startButton.addEventListener('click', async () => {
            const campaignId = prompt('ID de la campaña a iniciar (ejemplo: test-campaign):');
            if (campaignId) {
                try {
                    const response = await fetch(`/api/dialer/campaigns/${campaignId}/start`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            calls_per_minute: 10,
                            max_concurrent_calls: 3,
                            mode: 'power'
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        showNotification('Auto dialer iniciado exitosamente', 'success');
                        loadAutoDialerStatus();
                    } else {
                        showNotification(result.message || 'Error iniciando auto dialer', 'error');
                    }
                } catch (error) {
                    showNotification('Error de conexión', 'error');
                }
            }
        });
    }
    
    // Botón Detener Auto Dialer
    const stopButton = document.getElementById('stopAutoDialer');
    if (stopButton) {
        stopButton.addEventListener('click', async () => {
            const campaignId = prompt('ID de la campaña a detener:');
            if (campaignId) {
                try {
                    const response = await fetch(`/api/dialer/campaigns/${campaignId}/stop`, {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        showNotification('Auto dialer detenido exitosamente', 'success');
                        loadAutoDialerStatus();
                    } else {
                        showNotification(result.message || 'Error deteniendo auto dialer', 'error');
                    }
                } catch (error) {
                    showNotification('Error de conexión', 'error');
                }
            }
        });
    }
    
    // Botón Llamada de Prueba
    const testButton = document.getElementById('testCall');
    if (testButton) {
        testButton.addEventListener('click', async () => {
            const phoneNumber = prompt('Número de teléfono para llamada de prueba (ejemplo: +1234567890):');
            if (phoneNumber) {
                try {
                    const response = await fetch('/api/dialer/test-call', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({phone_number: phoneNumber})
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        showNotification('Llamada de prueba iniciada', 'success');
                    } else {
                        showNotification(result.message || 'Error en llamada de prueba', 'error');
                    }
                } catch (error) {
                    showNotification('Error de conexión', 'error');
                }
            }
        });
    }
    
    // Auto-refresh cada 30 segundos (agregar a tu setInterval existente)
    setInterval(() => {
        loadAgents();
        loadAutoDialerStatus(); // Agregar esta línea al setInterval existente
    }, 30000);
});
```

### **PASO 7: ELIMINAR ARCHIVOS CONFLICTIVOS**
**UBICACIÓN**: `./voip-auto-dialer/`
**ACCIÓN**: Ejecutar estos comandos en terminal

```bash
cd voip-auto-dialer
rm start_web_server.py
rm -f web/dialer_endpoints.py
rm -rf deprecated/
rm -f cleanup_project.py
rm -f cleanup_tests.py
```

## ✅ **VERIFICACIÓN DE IMPLEMENTACIÓN**

### **CHECKLIST DE VERIFICACIÓN:**
- [ ] README.md actualizado con información correcta
- [ ] setup_initial_data.py sin errores de import
- [ ] test_complete_system.py sin errores de import
- [ ] web/main.py con endpoints del auto dialer agregados
- [ ] dashboard_production.html con sección Auto Dialer
- [ ] Archivos conflictivos eliminados
- [ ] `python web/main.py` inicia sin errores
- [ ] Dashboard azul profesional carga correctamente
- [ ] Sección "Auto Dialer" visible en dashboard
- [ ] Botones del auto dialer responden

### **RESULTADO ESPERADO:**
1. **Tu dashboard profesional azul** se mantiene intacto
2. **Sección Auto Dialer** integrada con 3 botones funcionales
3. **6 agentes y 519 extensiones** siguen funcionando
4. **Endpoints `/api/dialer/*`** disponibles
5. **Una sola interfaz unificada** y profesional

## 🚨 **SI ALGO FALLA:**
1. Verificar que seguiste cada paso exactamente
2. Revisar logs de error en terminal
3. Confirmar que no hay errores de sintaxis en archivos modificados
4. Verificar que los imports están correctos

**¡IMPLEMENTACIÓN LISTA PARA EJECUTAR!** 🚀