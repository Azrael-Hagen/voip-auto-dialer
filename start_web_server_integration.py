"""
Integración del Auto Dialer con tu servidor web existente
NO reemplaza tu dashboard profesional - solo agrega endpoints
"""

import sys
import os
from pathlib import Path

# Agregar directorios al path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "web"))
sys.path.append(str(current_dir / "core"))

from web.dialer_endpoints import add_dialer_routes_to_app
from core.logging_config import get_logger

logger = get_logger("dialer_integration")

def integrate_dialer_with_existing_app(app):
    """
    Función para integrar el auto dialer con tu FastAPI existente
    
    Uso en tu web/main.py:
    from start_web_server_integration import integrate_dialer_with_existing_app
    integrate_dialer_with_existing_app(app)
    """
    try:
        # Agregar las rutas del dialer a tu app existente
        add_dialer_routes_to_app(app)
        
        logger.info("✅ Auto Dialer integrado exitosamente con tu servidor web")
        logger.info("🔗 Endpoints del dialer disponibles en /api/dialer/*")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error integrando auto dialer: {e}")
        return False

# Ejemplo de cómo integrar con tu web/main.py existente
"""
INSTRUCCIONES PARA INTEGRAR CON TU SERVIDOR EXISTENTE:

1. En tu archivo web/main.py, agrega estas líneas:

from start_web_server_integration import integrate_dialer_with_existing_app

# Después de crear tu app FastAPI existente
app = FastAPI()  # Tu app existente

# Integrar el auto dialer (mantiene tu dashboard intacto)
integrate_dialer_with_existing_app(app)

2. Reinicia tu servidor web existente

3. Los nuevos endpoints estarán disponibles:
   - POST /api/dialer/campaigns/{id}/start
   - GET /api/dialer/status
   - POST /api/dialer/test-call
   - etc.

4. Tu dashboard profesional seguirá funcionando igual
"""

if __name__ == "__main__":
    print("🔗 Este archivo es para integración con tu servidor existente")
    print("📖 Lee las instrucciones en el código para integrarlo")
    print("🚀 Tu dashboard profesional se mantendrá intacto")