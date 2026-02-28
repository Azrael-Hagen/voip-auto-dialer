# 📞 GUÍA DE CONEXIÓN EXTENSIONES → PROVEEDOR

## 🎯 PROBLEMA IDENTIFICADO
Las extensiones internas (4000-4005) no pueden hacer llamadas salientes porque:
1. No están registradas correctamente con Asterisk
2. El dialplan no está configurado para routing saliente
3. Falta configuración de trunk SIP funcional

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. CONFIGURACIÓN SIP (asterisk/conf/sip.conf)
```ini
; Proveedor configurado automáticamente desde data/providers.json
[pbx_provider]
type=friend
host=pbxonthecloud.com:5061
username=TUS_CREDENCIALES
secret=TU_PASSWORD
context=from-provider
qualify=yes
```

### 2. DIALPLAN FUNCIONAL (asterisk/conf/extensions.conf)
```ini
[internal]
; Llamadas salientes: 9 + número
exten => _9.,1,Dial(SIP/pbx_provider/${EXTEN:1})

; Llamadas internas
exten => _4XXX,1,Dial(SIP/${EXTEN})
```

### 3. EXTENSIONES REGISTRADAS
```ini
[4000] - [4005]
type=friend
context=internal  ; ← IMPORTANTE: Permite llamadas salientes
host=dynamic
secret=ext4000pass
```

## 🚀 PASOS PARA ACTIVAR

### PASO 1: Configurar credenciales reales
```bash
# Editar archivo de proveedores
nano data/providers.json

# Cambiar:
"username": "TU_USUARIO_REAL"
"password": "TU_PASSWORD_REAL"
```

### PASO 2: Aplicar configuración a Asterisk
```bash
# Copiar archivos
sudo cp asterisk/conf/sip.conf /etc/asterisk/
sudo cp asterisk/conf/extensions.conf /etc/asterisk/
sudo cp asterisk/conf/voicemail.conf /etc/asterisk/

# Reiniciar Asterisk
sudo systemctl restart asterisk
```

### PASO 3: Verificar conexión
```bash
# Conectar a CLI de Asterisk
sudo asterisk -r

# Verificar registro del proveedor
CLI> sip show peers
# Debe mostrar: pbx_provider  pbxonthecloud.com  OK (X ms)

# Verificar extensiones
CLI> sip show users
# Debe mostrar: 4000-4005 como registradas

# Probar dialplan
CLI> dialplan show internal
```

### PASO 4: Configurar softphones
```
Extensión 4001:
- Usuario: 4001
- Contraseña: ext4001pass
- Servidor: IP_DE_TU_ASTERISK:5060
- Transporte: UDP
```

### PASO 5: Probar llamadas
```
Desde extensión 4001:
- Llamada interna: marcar 4002
- Llamada externa: marcar 9 + 1234567890
- Emergencia: marcar 911
```

## 🔧 TROUBLESHOOTING

### Si el proveedor no se registra:
```bash
# Verificar conectividad
python test_provider_connection.py

# Ver logs de Asterisk
sudo tail -f /var/log/asterisk/messages

# Verificar configuración
sudo asterisk -r -x "sip show registry"
```

### Si las extensiones no se registran:
```bash
# Verificar que el softphone esté configurado correctamente
# Verificar que no haya firewall bloqueando puerto 5060
sudo ufw allow 5060/udp

# Verificar logs
sudo asterisk -r -x "sip set debug on"
```

### Si las llamadas salientes fallan:
```bash
# Verificar dialplan
sudo asterisk -r -x "dialplan show internal"

# Probar llamada manual
sudo asterisk -r -x "originate SIP/4001 extension 91234567890@internal"
```

## 📊 VERIFICACIÓN FINAL

Una vez configurado correctamente, deberías ver:

1. **Dashboard**: Proveedores = 1 (Conectado)
2. **Asterisk CLI**: `sip show peers` muestra proveedor OK
3. **Softphones**: Registrados como "Online"
4. **Llamadas**: Extensión 4001 puede llamar a 9+número

## 🎯 RESULTADO ESPERADO

```
Extensión 4001 → Marca 91234567890 → Asterisk → pbxonthecloud.com → Llamada externa exitosa
```
