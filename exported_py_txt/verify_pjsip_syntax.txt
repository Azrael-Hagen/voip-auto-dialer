#!/usr/bin/env python3
# Archivo: ~/voip-auto-dialer/scripts/verify_pjsip_syntax.py

import re
import os

def analyze_pjsip_file(filepath):
    """Analizar sintaxis del archivo PJSIP"""
    print(f"\n🔍 ANALIZANDO: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"❌ Archivo no existe: {filepath}")
        return False
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        print(f"📄 Total líneas: {len(lines)}")
        
        # Contadores
        sections = 0
        endpoints = 0
        auths = 0
        aors = 0
        errors = []
        
        current_section = None
        line_num = 0
        
        for line in lines:
            line_num += 1
            line = line.strip()
            
            # Ignorar comentarios y líneas vacías
            if not line or line.startswith(';') or line.startswith('#'):
                continue
            
            # Detectar secciones [nombre]
            section_match = re.match(r'\[([^\]]+)\]', line)
            if section_match:
                sections += 1
                current_section = section_match.group(1)
                continue
            
            # Detectar tipos
            if line.startswith('type='):
                type_value = line.split('=')[1].strip()
                if type_value == 'endpoint':
                    endpoints += 1
                elif type_value == 'auth':
                    auths += 1
                elif type_value == 'aor':
                    aors += 1
            
            # Verificar sintaxis básica
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Verificar que no haya espacios en claves
                if ' ' in key:
                    errors.append(f"Línea {line_num}: Clave con espacios: '{key}'")
                
                # Verificar valores vacíos críticos
                if not value and key in ['type', 'auth', 'aors', 'username', 'password']:
                    errors.append(f"Línea {line_num}: Valor vacío para clave crítica: '{key}'")
        
        # Mostrar estadísticas
        print(f"📊 ESTADÍSTICAS:")
        print(f"   🔧 Secciones totales: {sections}")
        print(f"   📞 Endpoints: {endpoints}")
        print(f"   🔐 Auths: {auths}")
        print(f"   📍 AORs: {aors}")
        
        # Verificar proporciones esperadas (cada extensión = 3 secciones)
        expected_sections = endpoints * 3  # endpoint + auth + aor
        if sections != expected_sections:
            print(f"   ⚠️  Proporción inesperada: {sections} secciones para {endpoints} endpoints")
            print(f"       (Esperado: {expected_sections} secciones)")
        
        # Mostrar errores
        if errors:
            print(f"❌ ERRORES ENCONTRADOS ({len(errors)}):")
            for error in errors[:10]:  # Solo primeros 10
                print(f"   {error}")
            if len(errors) > 10:
                print(f"   ... y {len(errors) - 10} errores más")
        else:
            print("✅ No se encontraron errores de sintaxis")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ Error analizando archivo: {e}")
        return False

def main():
    print("🔍 VERIFICACIÓN DE SINTAXIS PJSIP")
    print("=" * 50)
    
    files_to_check = [
        "/etc/asterisk/pjsip.conf",
        "/etc/asterisk/pjsip_extensions.conf"
    ]
    
    all_good = True
    for filepath in files_to_check:
        result = analyze_pjsip_file(filepath)
        all_good = all_good and result
    
    print("\n" + "=" * 50)
    if all_good:
        print("✅ TODOS LOS ARCHIVOS TIENEN SINTAXIS CORRECTA")
    else:
        print("❌ SE ENCONTRARON PROBLEMAS DE SINTAXIS")
    print("=" * 50)

if __name__ == "__main__":
    main()