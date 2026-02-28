#!/bin/bash
# Script de instalación de dependencias
echo "🔧 Instalando dependencias del servidor web funcional..."

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "⚡ Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

echo "✅ Instalación completada!"
echo "🚀 Para iniciar el servidor: python start_server.py"
