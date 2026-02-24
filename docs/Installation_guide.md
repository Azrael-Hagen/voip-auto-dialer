# 🎯 GUÍA COMPLETA DE INSTALACIÓN - SISTEMA VOIP

## 📋 RESUMEN DEL SISTEMA
Sistema VoIP completo para llamadas reales entre extensiones usando softphones.

## 🔧 PASO 1: CONFIGURAR ASTERISK

### 1.1 Copiar archivos de configuración
```bash
# Copiar configuraciones generadas
sudo cp asterisk_config/pjsip_extensions.conf /etc/asterisk/
sudo cp asterisk_config/extensions_voip.conf /etc/asterisk/
