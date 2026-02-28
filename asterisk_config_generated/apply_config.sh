#!/bin/bash
# Script para aplicar configuración de Asterisk
# Generado automáticamente: 2026-02-27 21:13:52

echo "🚀 APLICANDO CONFIGURACIÓN ASTERISK - 519 EXTENSIONES"
echo "=" * 70

# Crear backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "📋 Creando backup..."
sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup.$TIMESTAMP
sudo cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup.$TIMESTAMP

# Detener Asterisk
echo "🛑 Deteniendo Asterisk..."
sudo systemctl stop asterisk
sudo pkill -9 asterisk

# Aplicar nueva configuración
echo "🔧 Aplicando nueva configuración..."
sudo cp asterisk_config_generated/pjsip.conf /etc/asterisk/pjsip.conf
sudo cp asterisk_config_generated/extensions.conf /etc/asterisk/extensions.conf

# Configurar permisos
sudo chown asterisk:asterisk /etc/asterisk/pjsip.conf
sudo chown asterisk:asterisk /etc/asterisk/extensions.conf

# Iniciar Asterisk
echo "🚀 Iniciando Asterisk..."
sudo systemctl start asterisk

# Verificar estado
echo "🧪 Verificando estado..."
sleep 3
sudo systemctl is-active asterisk
sudo asterisk -rx 'core show version'

echo "✅ Configuración aplicada exitosamente"
echo "🧪 Pruebas recomendadas:"
echo "   sudo asterisk -rx 'pjsip show endpoints' | head -20"
echo "   sudo asterisk -rx 'originate PJSIP/1000 extension *99@from-internal'"
echo "   sudo asterisk -rx 'originate PJSIP/1000 extension 1001@from-internal'"
