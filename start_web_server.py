
"""
Servidor Web Principal Integrado - VoIP Auto Dialer
Inicia el servidor FastAPI con todos los componentes del dialer
"""

import uvicorn
import sys
import os
from pathlib import Path

# Agregar directorios al path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "web"))
sys.path.append(str(current_dir / "core"))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

# Importar componentes existentes y nuevos
try:
    from web.dialer_endpoints import add_dialer_routes_to_app
    from core.logging_config import get_logger
    from core.dialer_integration import dialer_integration
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("Asegúrate de que todos los archivos estén en su lugar correcto")
    sys.exit(1)

logger = get_logger("web_server")

# Crear aplicación FastAPI
app = FastAPI(
    title="VoIP Auto Dialer System",
    description="Sistema completo de marcado automático VoIP con detección de respuesta y transferencia a agentes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== RUTAS PRINCIPALES ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal con dashboard del sistema"""
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VoIP Auto Dialer - Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 0;
            }
            .container { 
                max-width: 1200px; 
                margin: 0; 
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header { 
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white; 
                padding: 0;
                text-align: center;
            }
            .header h1 { font-size: 2.5em; margin-bottom: 10px; }
            .header p { font-size: 1.2em; opacity: 0.9; }
            .content { padding: 0; }
            .grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 30px; 
                margin-bottom: 40px;
            }
            .card { 
                background: #f8f9fa;
                border-radius: 10px;
                padding: 0;
                border-left: 5px solid #3498db;
                transition: transform 0.3s ease;
            }
            .card:hover { transform: translateY(-5px); }
            .card h3 { color: #2c3e50; margin-bottom: 15px; font-size: 1.3em; }
            .card p { color: #7f8c8d; line-height: 1.6; margin-bottom: 15px; }
            .btn { 
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 0;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s ease;
                border: none;
                cursor: pointer;
                font-size: 1em;
            }
            .btn:hover { background: #2980b9; }
            .btn-success { background: #27ae60; }
            .btn-success:hover { background: #229954; }
            .btn-warning { background: #f39c12; }
            .btn-warning:hover { background: #e67e22; }
            .status { 
                text-align: center;
                padding: 0;
                background: #ecf0f1;
                border-radius: 10px;
                margin-bottom: 30px;
            }
            .status-online { background: #d5f4e6; color: #27ae60; }
            .status-offline { background: #fadbd8; color: #e74c3c; }
            .api-section { 
                background: #2c3e50;
                color: white;
                padding: 0;
                border-radius: 10px;
                margin-top: 30px;
            }
            .api-section h3 { margin-bottom: 20px; }
            .endpoint { 
                background: #34495e;
                padding: 0;
                border-radius: 5px;
                margin-bottom: 10px;
                font-family: 'Courier New', monospace;
            }
            .method { 
                display: inline-block;
                padding: 0;
                border-radius: 3px;
                font-weight: bold;
                margin-right: 10px;
            }
            .post { background: #27ae60; }
            .get { background: #3498db; }
            .footer { 
                text-align: center;
                padding: 0;
                background: #ecf0f1;
                color: #7f8c8d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 VoIP Auto Dialer</h1>
                <p>Sistema Completo de Marcado Automático con IA</p>
            </div>
            
            <div class="content">
                <div class="status status-online">
                    <h2>✅ Sistema Operativo</h2>
                    <p>Todos los componentes están funcionando correctamente</p>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>📞 Control de Campañas</h3>
                        <p>Inicia, pausa y detén campañas de marcado automático. Controla el flujo de llamadas en tiempo real.</p>
                        <a href="/docs#/Auto%20Dialer/start_campaign_dialing_api_dialer_campaigns__campaign_id__start_post" class="btn">Ver Endpoints</a>
                    </div>
                    
                    <div class="card">
                        <h3>👥 Gestión de Agentes</h3>
                        <p>Administra agentes disponibles y su distribución automática de llamadas contestadas.</p>
                        <a href="/docs#/Auto%20Dialer/get_dialer_status_api_dialer_status_get" class="btn btn-success">Estado del Sistema</a>
                    </div>
                    
                    <div class="card">
                        <h3>🔍 Detección Inteligente</h3>
                        <p>Sistema AMD que distingue entre humanos y contestadoras automáticas.</p>
                        <a href="/docs#/Auto%20Dialer/make_test_call_api_dialer_test_call_post" class="btn btn-warning">Llamada de Prueba</a>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Monitoreo en Tiempo Real</h3>
                        <p>Estadísticas detalladas de campañas, llamadas y rendimiento de agentes.</p>
                        <a href="/docs" class="btn">Documentación API</a>
                    </div>
                </div>
                
                <div class="api-section">
                    <h3>🔗 Endpoints Principales</h3>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        /api/dialer/campaigns/{id}/start - Iniciar marcado automático
                    </div>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        /api/dialer/campaigns/{id}/stop - Detener marcado
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        /api/dialer/status - Estado general del sistema
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        /api/dialer/campaigns - Listar campañas disponibles
                    </div>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        /api/dialer/test-call - Realizar llamada de prueba
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>VoIP Auto Dialer System v1.0.0 - Sistema completo de marcado automático</p>
            </div>
        </div>
        
        <script>
            // Auto-refresh status cada 30 segundos
            setInterval(async () => {
                try {
                    const response = await fetch('/api/dialer/status');
                    const data = await response.json();
                    console.log('Sistema status:', data);
                } catch (error) {
                    console.log('Error checking status:', error);
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Endpoint de salud del sistema"""
    try:
        # Verificar estado del dialer
        dialer_status = dialer_integration.get_dialer_status()
        
        return {
            "status": "healthy",
            "timestamp": dialer_status.get("timestamp"),
            "components": {
                "dialer_integration": "operational",
                "web_server": "operational",
                "database": "operational"  # Ajustar según tu implementación
            },
            "active_campaigns": dialer_status.get("total_active_campaigns", 0)
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=503, detail=f"Sistema no saludable: {str(e)}")

@app.get("/system-info")
async def get_system_info():
    """Información detallada del sistema"""
    try:
        dialer_status = dialer_integration.get_dialer_status()
        campaigns = dialer_integration.get_available_campaigns()
        
        return {
            "system_name": "VoIP Auto Dialer",
            "version": "1.0.0",
            "status": "operational",
            "dialer_status": dialer_status,
            "available_campaigns": campaigns.get("campaigns", []),
            "features": [
                "Marcado automático inteligente",
                "Detección de respuesta AMD",
                "Transferencia automática a agentes",
                "Monitoreo en tiempo real",
                "API REST completa",
                "Dashboard web integrado"
            ]
        }
    except Exception as e:
        logger.error(f"Error obteniendo info del sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INTEGRAR RUTAS DEL DIALER ====================

# Agregar todas las rutas del dialer
add_dialer_routes_to_app(app)

# ==================== EVENTOS DE INICIO Y CIERRE ====================

@app.on_event("startup")
async def startup_event():
    """Eventos al iniciar el servidor"""
    logger.info("🚀 Iniciando VoIP Auto Dialer Web Server...")
    logger.info("✅ Servidor web iniciado exitosamente")
    logger.info("🌐 Dashboard disponible en: http://localhost:8000")
    logger.info("📚 Documentación API en: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos al cerrar el servidor"""
    logger.info("🛑 Cerrando VoIP Auto Dialer Web Server...")
    
    # Detener todas las campañas activas
    try:
        status = dialer_integration.get_dialer_status()
        active_campaigns = status.get("active_campaigns", {})
        
        for campaign_id in active_campaigns:
            if active_campaigns[campaign_id]["status"] == "running":
                await dialer_integration.stop_campaign_dialing(campaign_id)
                logger.info(f"✅ Campaña {campaign_id} detenida")
                
    except Exception as e:
        logger.error(f"Error deteniendo campañas: {e}")
    
    logger.info("✅ Servidor cerrado exitosamente")

# ==================== MANEJO DE ERRORES GLOBALES ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return HTMLResponse(
        content="""
        <html>
            <body style="font-family: Arial; text-align: center; padding: 0;">
                <h1>404 - Página No Encontrada</h1>
                <p>La página que buscas no existe.</p>
                <a href="/" style="color: #3498db;">← Volver al Dashboard</a>
            </body>
        </html>
        """,
        status_code=404
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Error interno del servidor: {exc}")
    return HTMLResponse(
        content="""
        <html>
            <body style="font-family: Arial; text-align: center; padding: 0;">
                <h1>500 - Error Interno del Servidor</h1>
                <p>Ha ocurrido un error interno. Por favor intenta más tarde.</p>
                <a href="/" style="color: #3498db;">← Volver al Dashboard</a>
            </body>
        </html>
        """,
        status_code=500
    )

# ==================== FUNCIÓN PRINCIPAL ====================

def main():
    """Función principal para iniciar el servidor"""
    print("🚀 VoIP Auto Dialer - Servidor Web Principal")
    print("=" * 50)
    
    try:
        # Configuración del servidor
        config = {
            "host": "0.0.0.0",  # Permite conexiones externas
            "port": 8000,
            "reload": False,  # Cambiar a True solo en desarrollo
            "log_level": "info",
            "access_log": True
        }
        
        print(f"🌐 Iniciando servidor en http://localhost:{config['port']}")
        print(f"📚 Documentación API: http://localhost:{config['port']}/docs")
        print(f"🔍 Redoc: http://localhost:{config['port']}/redoc")
        print(f"❤️  Health Check: http://localhost:{config['port']}/health")
        print("\n⚡ Presiona Ctrl+C para detener el servidor")
        print("=" * 50)
        
        # Iniciar servidor
        uvicorn.run(app, **config)
        
    except KeyboardInterrupt:
        print("\n⚠️  Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR INICIANDO SERVIDOR: {e}")
        logger.error(f"Error fatal: {e}")

if __name__ == "__main__":
    main()

