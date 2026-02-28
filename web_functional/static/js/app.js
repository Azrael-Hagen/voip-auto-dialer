
// VoIP Auto Dialer - JavaScript Funcional y Profesional

class VoIPDashboard {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.init();
    }

    init() {
        console.log('🚀 Inicializando VoIP Dashboard');
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadInitialData();
        this.startPeriodicUpdates();
    }

    setupEventListeners() {
        // Botones de acción
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                this.handleAction(e.target.dataset.action, e.target);
            }
        });

        // Formularios
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.ajax-form')) {
                e.preventDefault();
                this.handleFormSubmit(e.target);
            }
        });

        // Navegación
        document.addEventListener('click', (e) => {
            if (e.target.matches('.nav-link')) {
                this.updateActiveNavigation(e.target);
            }
        });

        // Manejo de errores globales
        window.addEventListener('error', (e) => {
            console.error('Error global:', e.error);
            this.showNotification('Error del sistema', 'danger');
        });
    }

    connectWebSocket() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('✅ WebSocket conectado');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error procesando mensaje WebSocket:', error);
                }
            };

            this.websocket.onclose = () => {
                console.log('❌ WebSocket desconectado');
                this.updateConnectionStatus(false);
                this.scheduleReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('Error WebSocket:', error);
                this.updateConnectionStatus(false);
            };

        } catch (error) {
            console.error('Error creando WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`🔄 Reintentando conexión en ${delay}ms (intento ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        } else {
            console.error('❌ Máximo de reintentos alcanzado');
            this.showNotification('Conexión perdida. Recarga la página.', 'danger');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'metrics_update':
                this.updateMetrics(data.data);
                break;
            case 'extension_status':
                this.updateExtensionStatus(data.data);
                break;
            case 'call_event':
                this.handleCallEvent(data.data);
                break;
            case 'system_alert':
                this.showNotification(data.message, data.level || 'info');
                break;
            default:
                console.log('Mensaje WebSocket no manejado:', data);
        }
    }

    updateConnectionStatus(connected) {
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.system-status span');
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${connected ? '' : 'offline'}`;
        }
        
        if (statusText) {
            statusText.textContent = connected ? 'Sistema Online' : 'Sistema Offline';
        }
    }

    updateMetrics(metrics) {
        Object.entries(metrics).forEach(([key, value]) => {
            const element = document.querySelector(`[data-metric="${key}"]`);
            if (element) {
                this.animateValue(element, parseInt(element.textContent) || 0, value);
            }
        });
    }

    animateValue(element, start, end, duration = 1000) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
    }

    updateExtensionStatus(data) {
        const row = document.querySelector(`[data-extension="${data.extension}"]`);
        if (row) {
            const statusBadge = row.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.className = `badge ${data.online ? 'success' : 'secondary'}`;
                statusBadge.textContent = data.online ? 'Online' : 'Offline';
            }
        }
    }

    handleCallEvent(data) {
        console.log('Evento de llamada:', data);
        this.showNotification(`Llamada ${data.event}: ${data.details}`, 'info');
        
        // Actualizar contadores de llamadas
        if (data.event === 'started') {
            this.incrementMetric('active_calls');
        } else if (data.event === 'ended') {
            this.decrementMetric('active_calls');
        }
    }

    incrementMetric(metricName) {
        const element = document.querySelector(`[data-metric="${metricName}"]`);
        if (element) {
            const current = parseInt(element.textContent) || 0;
            this.animateValue(element, current, current + 1);
        }
    }

    decrementMetric(metricName) {
        const element = document.querySelector(`[data-metric="${metricName}"]`);
        if (element) {
            const current = parseInt(element.textContent) || 0;
            if (current > 0) {
                this.animateValue(element, current, current - 1);
            }
        }
    }

    async handleAction(action, element) {
        console.log(`Ejecutando acción: ${action}`);
        
        try {
            switch (action) {
                case 'originate_call':
                    await this.originateCall(element);
                    break;
                case 'reload_data':
                    await this.loadInitialData();
                    break;
                case 'test_connection':
                    await this.testConnection();
                    break;
                case 'refresh_extensions':
                    await this.refreshExtensions();
                    break;
                case 'refresh_providers':
                    await this.refreshProviders();
                    break;
                default:
                    console.warn(`Acción no reconocida: ${action}`);
            }
        } catch (error) {
            console.error(`Error ejecutando acción ${action}:`, error);
            this.showNotification(`Error: ${error.message}`, 'danger');
        }
    }

    async originateCall(element) {
        const from = element.dataset.from;
        const to = element.dataset.to;
        
        if (!from || !to) {
            throw new Error('Faltan parámetros para la llamada');
        }

        const response = await fetch('/api/calls/originate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ from, to })
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }

        const result = await response.json();
        this.showNotification(`Llamada iniciada: ${from} → ${to}`, 'success');
        return result;
    }

    async loadInitialData() {
        try {
            console.log('📊 Cargando datos iniciales...');
            
            // Cargar métricas básicas
            await this.loadMetrics();
            
            // Cargar datos específicos según la página
            const currentPage = this.getCurrentPage();
            switch (currentPage) {
                case 'extensions':
                    await this.loadExtensions();
                    break;
                case 'providers':
                    await this.loadProviders();
                    break;
                case 'campaigns':
                    await this.loadCampaigns();
                    break;
            }
            
            console.log('✅ Datos iniciales cargados');
        } catch (error) {
            console.error('Error cargando datos iniciales:', error);
            this.showNotification('Error cargando datos', 'danger');
        }
    }

    async loadMetrics() {
        try {
            const response = await fetch('/api/asterisk/stats');
            if (response.ok) {
                const data = await response.json();
                this.updateMetrics(data);
            }
        } catch (error) {
            console.error('Error cargando métricas:', error);
        }
    }

    async loadExtensions() {
        try {
            const response = await fetch('/api/extensions');
            if (response.ok) {
                const data = await response.json();
                this.updateExtensionsTable(data.data);
            }
        } catch (error) {
            console.error('Error cargando extensiones:', error);
        }
    }

    async loadProviders() {
        try {
            const response = await fetch('/api/providers');
            if (response.ok) {
                const data = await response.json();
                this.updateProvidersTable(data.data);
            }
        } catch (error) {
            console.error('Error cargando proveedores:', error);
        }
    }

    async loadCampaigns() {
        // Implementar cuando esté disponible la API de campañas
        console.log('Cargando campañas...');
    }

    updateExtensionsTable(extensions) {
        const tbody = document.querySelector('#extensions-table tbody');
        if (!tbody) return;

        tbody.innerHTML = extensions.map(ext => `
            <tr data-extension="${ext.extension}">
                <td>${ext.extension}</td>
                <td>${ext.password || 'N/A'}</td>
                <td><span class="badge secondary status-badge">Offline</span></td>
                <td>${ext.created_at || 'N/A'}</td>
                <td>
                    <button class="btn btn-primary btn-sm" data-action="originate_call" 
                            data-from="${ext.extension}" data-to="*99">
                        Probar
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updateProvidersTable(providers) {
        const container = document.querySelector('#providers-container');
        if (!container) return;

        container.innerHTML = providers.map(provider => `
            <div class="provider-card">
                <h3>${provider.name}</h3>
                <p>Host: ${provider.host}</p>
                <p>Estado: <span class="badge ${provider.active ? 'success' : 'secondary'}">
                    ${provider.active ? 'Activo' : 'Inactivo'}
                </span></p>
            </div>
        `).join('');
    }

    getCurrentPage() {
        const path = window.location.pathname;
        if (path.includes('extensions')) return 'extensions';
        if (path.includes('providers')) return 'providers';
        if (path.includes('campaigns')) return 'campaigns';
        return 'dashboard';
    }

    startPeriodicUpdates() {
        // Actualizar métricas cada 30 segundos
        setInterval(() => {
            this.loadMetrics();
        }, 30000);

        // Verificar conexión WebSocket cada 10 segundos
        setInterval(() => {
            if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
                this.connectWebSocket();
            }
        }, 10000);
    }

    async testConnection() {
        try {
            const response = await fetch('/api/asterisk/stats');
            if (response.ok) {
                this.showNotification('Conexión exitosa', 'success');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.showNotification(`Error de conexión: ${error.message}`, 'danger');
        }
    }

    async refreshExtensions() {
        await this.loadExtensions();
        this.showNotification('Extensiones actualizadas', 'success');
    }

    async refreshProviders() {
        await this.loadProviders();
        this.showNotification('Proveedores actualizados', 'success');
    }

    showNotification(message, type = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;

        // Agregar al DOM
        document.body.appendChild(notification);

        // Remover después de 5 segundos
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    updateActiveNavigation(activeLink) {
        // Remover clase activa de todos los enlaces
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Agregar clase activa al enlace clickeado
        activeLink.classList.add('active');
    }

    async handleFormSubmit(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        try {
            const response = await fetch(form.action, {
                method: form.method || 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                this.showNotification('Operación exitosa', 'success');
                
                // Recargar datos si es necesario
                await this.loadInitialData();
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'danger');
        }
    }
}

// Estilos CSS para animaciones (inyectados dinámicamente)
const styles = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .notification {
        transition: all 0.3s ease;
    }
    
    .nav-link.active {
        background-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    .provider-card {
        background: white;
        padding: 0;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
`;

// Inyectar estilos
const styleSheet = document.createElement('style');
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.voipDashboard = new VoIPDashboard();
});

// Exportar para uso global
window.VoIPDashboard = VoIPDashboard;