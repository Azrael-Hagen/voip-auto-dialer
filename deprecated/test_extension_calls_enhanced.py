#!/usr/bin/env python3
"""
📞 PROBADOR MEJORADO DE LLAMADAS ENTRE EXTENSIONES
================================================================
Prueba llamadas entre extensiones usando AMI de Asterisk
"""

import json
import socket
import time
import random
import asyncio
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def load_system_data():
    """Carga los datos del sistema"""
    try:
        with open('data/agents.json', 'r') as f:
            agents = json.load(f)
        
        with open('data/extensions.json', 'r') as f:
            extensions = json.load(f)
        
        return agents, extensions
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return {}, {}

class AMIClient:
    """Cliente AMI mejorado para Asterisk"""
    
    def __init__(self, host='localhost', port=5038, username='voip_dialer', password='VoipDialer2024!'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.socket = None
        self.connected = False
    
    def connect(self):
        """Conectar al AMI"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            
            # Leer banner
            banner = self.socket.recv(1024).decode('utf-8')
            print(f"📡 Banner AMI: {banner.strip()}")
            
            # Autenticar
            login_msg = f"Action: Login\r\nUsername: {self.username}\r\nSecret: {self.password}\r\n\r\n"
            self.socket.send(login_msg.encode('utf-8'))
            
            # Leer respuesta de login
            response = self.socket.recv(1024).decode('utf-8')
            if "Authentication accepted" in response:
                print("✅ Autenticación AMI exitosa")
                self.connected = True
                return True
            else:
                print(f"❌ Error de autenticación: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando AMI: {e}")
            return False
    
    def send_action(self, action_dict):
        """Enviar acción AMI"""
        if not self.connected:
            return None
        
        try:
            # Construir mensaje
            message = ""
            for key, value in action_dict.items():
                message += f"{key}: {value}\r\n"
            message += "\r\n"
            
            # Enviar
            self.socket.send(message.encode('utf-8'))
            
            # Leer respuesta
            response = ""
            while True:
                data = self.socket.recv(1024).decode('utf-8')
                response += data
                if "\r\n\r\n" in response:
                    break
            
            return response
            
        except Exception as e:
            print(f"❌ Error enviando acción AMI: {e}")
            return None
    
    def get_pjsip_endpoints(self):
        """Obtener endpoints PJSIP registrados"""
        action = {
            'Action': 'PJSIPShowEndpoints'
        }
        
        response = self.send_action(action)
        return response
    
    def get_pjsip_registrations(self):
        """Obtener registros PJSIP"""
        action = {
            'Action': 'PJSIPShowRegistrations'
        }
        
        response = self.send_action(action)
        return response
    
    def originate_call(self, from_ext, to_ext, timeout=30):
        """Originar llamada entre extensiones"""
        call_id = f"test_call_{int(time.time())}"
        
        action = {
            'Action': 'Originate',
            'Channel': f'PJSIP/{from_ext}',
            'Context': 'from-internal',
            'Exten': to_ext,
            'Priority': '1',
            'CallerID': f'Test Call <{from_ext}>',
            'Timeout': str(timeout * 1000),  # Timeout en milisegundos
            'Variable': f'CALL_ID={call_id}',
            'Async': 'true'
        }
        
        response = self.send_action(action)
        return response, call_id
    
    def hangup_all_channels(self):
        """Colgar todos los canales activos"""
        action = {
            'Action': 'CoreShowChannels'
        }
        
        response = self.send_action(action)
        
        # Parsear respuesta para encontrar canales
        if response and "PJSIP" in response:
            lines = response.split('\n')
            for line in lines:
                if "PJSIP/" in line:
                    parts = line.split()
                    if len(parts) > 0:
                        channel = parts[0]
                        hangup_action = {
                            'Action': 'Hangup',
                            'Channel': channel
                        }
                        self.send_action(hangup_action)
    
    def disconnect(self):
        """Desconectar del AMI"""
        if self.connected and self.socket:
            try:
                logout_msg = "Action: Logoff\r\n\r\n"
                self.socket.send(logout_msg.encode('utf-8'))
                self.socket.close()
                self.connected = False
                print("✅ Desconectado del AMI")
            except:
                pass

def test_pjsip_registrations():
    """Probar registros PJSIP"""
    print("\n📋 Verificando registros PJSIP...")
    
    ami = AMIClient()
    if not ami.connect():
        return False
    
    try:
        # Obtener endpoints
        print("🔍 Obteniendo endpoints PJSIP...")
        endpoints_response = ami.get_pjsip_endpoints()
        if endpoints_response:
            print("✅ Endpoints PJSIP obtenidos")
            # Parsear y mostrar endpoints registrados
            if "ObjectType: endpoint" in endpoints_response:
                print("📱 Endpoints encontrados en la respuesta")
            else:
                print("⚠️ No se encontraron endpoints en la respuesta")
        
        # Obtener registros
        print("🔍 Obteniendo registros PJSIP...")
        registrations_response = ami.get_pjsip_registrations()
        if registrations_response:
            print("✅ Registros PJSIP obtenidos")
            if "ObjectType: registration" in registrations_response:
                print("📱 Registros encontrados en la respuesta")
            else:
                print("⚠️ No se encontraron registros activos")
        
    finally:
        ami.disconnect()
    
    return True

def test_call_between_extensions(from_ext, to_ext, agent_from="", agent_to=""):
    """Probar llamada entre dos extensiones específicas"""
    print(f"\n📞 Probando llamada: {from_ext} → {to_ext}")
    if agent_from and agent_to:
        print(f"   {agent_from} llamando a {agent_to}")
    
    ami = AMIClient()
    if not ami.connect():
        return False
    
    try:
        # Limpiar canales existentes
        print("🧹 Limpiando canales existentes...")
        ami.hangup_all_channels()
        time.sleep(1)
        
        # Originar llamada
        print(f"🔄 Originando llamada desde {from_ext} hacia {to_ext}...")
        response, call_id = ami.originate_call(from_ext, to_ext, timeout=15)
        
        if response and "Response: Success" in response:
            print("✅ Llamada originada exitosamente")
            print(f"   Call ID: {call_id}")
            
            # Esperar un poco para que se establezca
            print("⏳ Esperando establecimiento de llamada...")
            time.sleep(3)
            
            # Verificar canales activos
            channels_response = ami.send_action({'Action': 'CoreShowChannels'})
            if channels_response and "PJSIP" in channels_response:
                print("✅ Canales PJSIP activos detectados")
                
                # Contar canales activos
                channel_count = channels_response.count("PJSIP/")
                print(f"   Canales activos: {channel_count}")
            else:
                print("⚠️ No se detectaron canales activos")
            
            # Esperar un poco más y luego colgar
            time.sleep(2)
            print("🔚 Finalizando llamada de prueba...")
            ami.hangup_all_channels()
            
            return True
            
        else:
            print(f"❌ Error originando llamada")
            if response:
                print(f"   Respuesta: {response[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de llamada: {e}")
        return False
        
    finally:
        ami.disconnect()

def test_multiple_calls():
    """Probar múltiples llamadas concurrentes"""
    print("\n📞 Probando múltiples llamadas concurrentes...")
    
    # Cargar datos del sistema
    agents, extensions = load_system_data()
    
    # Filtrar extensiones asignadas
    assigned_extensions = []
    for ext_id, ext_data in extensions.items():
        if ext_data.get('status') == 'assigned':
            extension = ext_data.get('extension')
            assigned_to = ext_data.get('assigned_to')
            agent_name = "Usuario"
            
            if assigned_to and assigned_to in agents:
                agent_name = agents[assigned_to].get('name', 'Usuario')
            
            assigned_extensions.append({
                'extension': extension,
                'agent_name': agent_name,
                'agent_id': assigned_to
            })
    
    if len(assigned_extensions) < 2:
        print("❌ Se necesitan al menos 2 extensiones asignadas para probar llamadas")
        return False
    
    print(f"✅ {len(assigned_extensions)} extensiones asignadas encontradas")
    
    # Probar llamadas entre las primeras extensiones
    success_count = 0
    total_tests = min(3, len(assigned_extensions) - 1)  # Máximo 3 pruebas
    
    for i in range(total_tests):
        ext1 = assigned_extensions[i]
        ext2 = assigned_extensions[i + 1] if i + 1 < len(assigned_extensions) else assigned_extensions[0]
        
        print(f"\n🔄 Prueba {i + 1}/{total_tests}")
        success = test_call_between_extensions(
            ext1['extension'], 
            ext2['extension'],
            ext1['agent_name'],
            ext2['agent_name']
        )
        
        if success:
            success_count += 1
        
        # Esperar entre pruebas
        if i < total_tests - 1:
            time.sleep(2)
    
    print(f"\n📊 Resultados: {success_count}/{total_tests} pruebas exitosas")
    return success_count > 0

def main():
    print_header("📞 PROBADOR MEJORADO DE LLAMADAS ENTRE EXTENSIONES")
    
    # 1. Cargar datos del sistema
    print("\n1. 📋 Cargando datos del sistema...")
    agents, extensions = load_system_data()
    
    if not agents or not extensions:
        print("❌ No se encontraron datos del sistema")
        return False
    
    # Contar extensiones asignadas
    assigned_count = sum(1 for ext in extensions.values() if ext.get('status') == 'assigned')
    print(f"✅ Sistema cargado: {len(agents)} agentes, {assigned_count} extensiones asignadas")
    
    # 2. Probar registros PJSIP
    print("\n2. 🔍 Probando registros PJSIP...")
    if not test_pjsip_registrations():
        print("⚠️ Problemas con los registros PJSIP")
    
    # 3. Probar llamadas entre extensiones
    print("\n3. 📞 Probando llamadas entre extensiones...")
    if not test_multiple_calls():
        print("❌ Problemas con las llamadas entre extensiones")
        return False
    
    print_header("📋 INSTRUCCIONES PARA PRUEBAS MANUALES")
    
    print("Para probar llamadas manualmente con softphones:")
    print("")
    print("1. 📱 CONFIGURAR SOFTPHONES:")
    print("   • Ejecuta: python generate_softphone_configs_enhanced.py")
    print("   • Descarga e instala Zoiper, PortSIP o Linphone")
    print("   • Importa las configuraciones generadas")
    print("   • Verifica que se registren correctamente")
    print("")
    print("2. 🔍 VERIFICAR REGISTROS:")
    print("   sudo asterisk -rx 'pjsip show registrations'")
    print("   sudo asterisk -rx 'pjsip show endpoints'")
    print("")
    print("3. 📞 REALIZAR LLAMADAS:")
    print("   • Desde un softphone, marca el número de otra extensión")
    print("   • La llamada debe conectarse automáticamente")
    print("   • Verifica la calidad de audio en ambas direcciones")
    print("")
    print("4. 📊 MONITOREAR LOGS:")
    print("   sudo tail -f /var/log/asterisk/full")
    print("")
    print("🔧 COMANDOS ÚTILES DE ASTERISK:")
    print("   • Ver canales activos: sudo asterisk -rx 'core show channels'")
    print("   • Ver dialplan: sudo asterisk -rx 'dialplan show from-internal'")
    print("   • Recargar configuración: sudo asterisk -rx 'dialplan reload'")
    print("   • Reiniciar PJSIP: sudo asterisk -rx 'module reload res_pjsip.so'")
    
    print_header("✅ PRUEBAS COMPLETADAS")
    
    return True

if __name__ == "__main__":
    main()
