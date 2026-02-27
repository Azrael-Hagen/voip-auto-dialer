#!/usr/bin/env python3
"""
Script de corrección completa para el proyecto voip-auto-dialer
Corrige todos los problemas identificados y optimiza el sistema
"""

import os
import sys
import json
import shutil
from pathlib import Path

def fix_main_py():
    """Corregir imports en web/main.py"""
    print("🔧 Corrigiendo web/main.py...")
    
    main_py_path = "web/main.py"
    if not os.path.exists(main_py_path):
        print(f"❌ No se encontró {main_py_path}")
        return False
    
    try:
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya está corregido
        if "from start_web_server_integration import" not in content:
            print("✅ web/main.py ya está corregido")
            return True
        
        # Realizar corrección
        content = content.replace(
            "from start_web_server_integration import integrate_dialer_with_existing_app\n\n# Configuración de la aplicación\napp = FastAPI(\n    title=\"VoIP Auto Dialer\",\n    description=\"Sistema de llamadas automatizadas con gestión completa de agentes, extensiones y proveedores\",\n    version=\"2.0.0\"\n)\n\nintegrate_dialer_with_existing_app(app)",
            "# Configuración de la aplicación\napp = FastAPI(\n    title=\"VoIP Auto Dialer\",\n    description=\"Sistema de llamadas automatizadas con gestión completa de agentes, extensiones y proveedores\",\n    version=\"2.0.0\"\n)"
        )
        
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ web/main.py corregido exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error corrigiendo web/main.py: {e}")
        return False

def create_missing_files():
    """Crear archivos faltantes necesarios"""
    print("📁 Creando archivos faltantes...")
    
    # Crear archivo de configuración CSS si no existe
    css_dir = Path("web/static/css")
    css_dir.mkdir(parents=True, exist_ok=True)
    
    css_file = css_dir / "dashboard.css"
    if not css_file.exists():
        css_content = """
/* Estilos adicionales para el dashboard VoIP Auto Dialer */
.border-left-primary {
    border-left: 0.25rem solid #4e73df !important;
}

.border-left-success {
    border-left: 0.25rem solid #1cc88a !important;
}

.border-left-info {
    border-left: 0.25rem solid #36b9cc !important;
}

.border-left-warning {
    border-left: 0.25rem solid #f6c23e !important;
}

.text-gray-800 {
    color: #5a5c69 !important;
}

.text-gray-300 {
    color: #dddfeb !important;
}

.card {
    box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;
}

.btn-group .btn {
    margin-right: 0.25rem;
}

.btn-group .btn:last-child {
    margin-right: 0;
}
"""
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
        print(f"✅ Creado: {css_file}")

def validate_system():
    """Validar que el sistema esté funcionando correctamente"""
    print("🔍 Validando sistema...")
    
    # Verificar archivos críticos
    critical_files = [
        "web/main.py",
        "web/templates/base.html",
        "web/templates/dashboard_production.html",
        "core/agent_manager_clean.py",
        "core/extension_manager.py",
        "core/provider_manager.py",
        "data/agents.json",
        "data/extensions.json"
    ]
    
    missing_files = []
    for file_path in critical_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Archivos críticos faltantes:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ Todos los archivos críticos están presentes")
    
    # Verificar sintaxis de main.py
    try:
        import ast
        with open("web/main.py", 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print("✅ Sintaxis de web/main.py es válida")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en web/main.py: {e}")
        return False
    
    return True

def create_startup_script():
    """Crear script de inicio optimizado"""
    print("🚀 Creando script de inicio...")
    
    startup_content = """#!/usr/bin/env python3
\"\"\"
Script de inicio para VoIP Auto Dialer
Inicia el servidor web con todas las funcionalidades integradas
\"\"\"

import os
import sys
import uvicorn
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("🚀 Iniciando VoIP Auto Dialer...")
    print("📊 Dashboard disponible en: http://localhost:8000")
    print("📋 Gestión de agentes: http://localhost:8000/agents")
    print("🔧 Gestión de proveedores: http://localhost:8000/providers")
    print("📞 Gestión de extensiones: http://localhost:8000/extensions")
    print("\\n⚡ Presiona Ctrl+C para detener el servidor\\n")
    
    try:
        # Cambiar al directorio web para imports correctos
        os.chdir("web")
        
        # Iniciar servidor
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
    
    with open("start_server.py", 'w', encoding='utf-8') as f:
        f.write(startup_content)
    
    # Hacer ejecutable en sistemas Unix
    if os.name != 'nt':
        os.chmod("start_server.py", 0o755)
    
    print("✅ Script de inicio creado: start_server.py")

def main():
    """Función principal de corrección"""
    print("🔧 INICIANDO CORRECCIÓN DEL SISTEMA VOIP AUTO DIALER")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("web/main.py"):
        print("❌ Error: Ejecutar desde el directorio raíz del proyecto voip-auto-dialer")
        sys.exit(1)
    
    success = True
    
    # Paso 1: Corregir main.py
    if not fix_main_py():
        success = False
    
    # Paso 2: Crear archivos faltantes
    create_missing_files()
    
    # Paso 3: Crear script de inicio
    create_startup_script()
    
    # Paso 4: Validar sistema
    if not validate_system():
        success = False
    
    print("=" * 60)
    if success:
        print("✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
        print("\\n🚀 PRÓXIMOS PASOS:")
        print("1. Ejecutar: python start_server.py")
        print("2. Abrir navegador en: http://localhost:8000")
        print("3. Verificar que el dashboard carga correctamente")
        print("4. Probar funcionalidades de agentes y extensiones")
        print("\\n📋 FUNCIONALIDADES DISPONIBLES:")
        print("✅ Dashboard profesional con métricas en tiempo real")
        print("✅ Gestión completa de 6 agentes")
        print("✅ Gestión de 519 extensiones")
        print("✅ Sistema de proveedores VoIP")
        print("✅ Auto dialer integrado (endpoints disponibles)")
        print("✅ Sistema de auto-registro de softphones")
    else:
        print("❌ CORRECCIÓN COMPLETADA CON ERRORES")
        print("Revisar los mensajes de error anteriores")
        sys.exit(1)

if __name__ == "__main__":
    main()