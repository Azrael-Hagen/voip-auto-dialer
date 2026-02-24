# 🎯 GUÍA COMPLETA DE INSTALACIÓN - SISTEMA VOIP

## 📋 RESUMEN DEL SISTEMA
Sistema VoIP completo para llamadas reales entre extensiones usando softphones.

Generado: 2026-02-21 15:28:07

## 🔧 PASO 1: CONFIGURAR ASTERISK

### 1.1 Copiar archivos de configuración
```bash
# Copiar configuraciones generadas
sudo cp asterisk_config/pjsip_extensions.conf /etc/asterisk/
sudo cp asterisk_config/extensions_voip.conf /etc/asterisk/
```

### 1.2 Incluir configuraciones en archivos principales

**En /etc/asterisk/pjsip.conf:**
```
#include pjsip_extensions.conf
```

**En /etc/asterisk/extensions.conf:**
```
#include extensions_voip.conf
```

### 1.3 Reiniciar Asterisk
```bash
sudo systemctl restart asterisk
sudo asterisk -rx "core reload"
```

## 🔧 PASO 2: VERIFICAR CONFIGURACIÓN

### 2.1 Verificar endpoints
```bash
sudo asterisk -rx "pjsip show endpoints"
```

### 2.2 Verificar dialplan
```bash
sudo asterisk -rx "dialplan show from-internal"
```

## 📱 PASO 3: CONFIGURAR SOFTPHONES

### 3.1 Descargar configuraciones
- Ve a http://localhost:8000/agents
- Haz clic en "Configurar" para un agente
- Descarga la configuración para tu softphone

### 3.2 Aplicaciones recomendadas

**Zoiper (Multiplataforma)**
- Descarga: https://www.zoiper.com/
- Importa el archivo .conf descargado

**PortSIP (Windows/Mac/Mobile)**
- Descarga: https://www.portsip.com/
- Importa el archivo .xml descargado

**Linphone (Código abierto)**
- Descarga: https://www.linphone.org/
- Configura manualmente con los datos del archivo .txt

### 3.3 Configuración manual
Si prefieres configurar manualmente:

1. **Servidor SIP**: localhost (o IP del servidor)
2. **Puerto**: 5060
3. **Transporte**: UDP
4. **Usuario**: Número de extensión (ej: 1500)
5. **Contraseña**: La generada automáticamente
6. **Nombre**: Nombre del agente

## 🧪 PASO 4: PROBAR EL SISTEMA

### 4.1 Ejecutar prueba rápida
```bash
python quick_voip_test.py
```

### 4.2 Probar registro de extensiones
1. Abre tu softphone
2. Verifica que aparezca como "Registrado" o "Online"
3. En Asterisk CLI: `pjsip show endpoints`

### 4.3 Probar llamadas
1. Configura al menos 2 softphones
2. Desde uno, marca el número de extensión del otro
3. Verifica que suene y se pueda contestar

## 🔍 SOLUCIÓN DE PROBLEMAS

### Problema: Extensión no se registra
**Solución:**
```bash
# Verificar configuración PJSIP
sudo asterisk -rx "pjsip show endpoint XXXX"

# Verificar logs
sudo tail -f /var/log/asterisk/full
```

### Problema: Llamada no conecta
**Solución:**
```bash
# Verificar dialplan
sudo asterisk -rx "dialplan show from-internal"

# Probar llamada manualmente
sudo asterisk -rx "channel originate PJSIP/1500 extension 1501@from-internal"
```

### Problema: Audio no funciona
**Solución:**
- Verificar firewall (puertos 5060 UDP, 10000-20000 UDP)
- Configurar NAT si es necesario
- Verificar códecs permitidos

## 📊 MONITOREO

### Ver llamadas activas
```bash
sudo asterisk -rx "core show calls"
```

### Ver estadísticas
```bash
sudo asterisk -rx "pjsip show registrations"
```

## 🎉 ¡LISTO!

Si todo funciona correctamente:
- ✅ Extensiones registradas
- ✅ Llamadas entre extensiones funcionando
- ✅ Audio bidireccional
- ✅ Sistema web operativo

## 📞 PRÓXIMOS PASOS

1. **Configurar proveedores externos** para llamadas salientes
2. **Implementar campañas automatizadas**
3. **Agregar más agentes y extensiones**
4. **Configurar grabación de llamadas**
5. **Implementar reportes avanzados**

---
*Generado automáticamente por el Sistema VoIP Auto Dialer*
