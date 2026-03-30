import { CONFIG } from '../../app/config';
import { getToken } from './tokenService';

class WebSocketService {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.listeners = new Set();
        this.currentPath = null;
        this.manualClose = false;
    }

    /**
     * Connect to WebSocket with token authentication.
     * @param {string} path - WebSocket endpoint path.
     */
    connect(path) {
        // Reuse existing connection if path matches and socket is not closed
        if (this.socket && this.socket.readyState !== WebSocket.CLOSED && this.currentPath === path) {
            return;
        }

        // Close old connection if connecting to a different path
        if (this.socket && this.currentPath !== path) {
            this.disconnect();
        }

        this.currentPath = path;
        this.manualClose = false;
        
        const token = getToken();
        // If no token exists, the backend JWTAuthMiddleware will reject the connection
        if (!token) {
            console.warn('Attempted WebSocket connection without token');
            return;
        }

        const wsUrl = `${CONFIG.WS_BASE_URL}${path}?token=${token}`;
        console.log(`Connecting to WebSocket: ${wsUrl.replace(token, 'REDACTED')}`);

        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                console.log(`WebSocket Connected to ${this.currentPath}`);
                this.reconnectAttempts = 0;
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.listeners.forEach(listener => listener(data));
                } catch (parseError) {
                    console.error('WebSocket parse error:', parseError);
                }
            };

            this.socket.onclose = (event) => {
                console.log(`WebSocket Disconnected (Code: ${event.code})`);
                
                // Only attempt reconnect if not a manual disconnect and under limit
                if (!this.manualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
                    const delay = Math.min(10000, 3000 * (this.reconnectAttempts + 1));
                    console.log(`Attempting reconnect in ${delay}ms...`);
                    
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connect(path);
                    }, delay);
                }
            };

            this.socket.onerror = (err) => {
                console.error('WebSocket Error:', err);
            };
        } catch (error) {
            console.error('WebSocket connection initialization error:', error);
        }
    }

    /**
     * Subscribe a callback to WebSocket messages.
     * @param {Function} listener - Callback function.
     * @returns {Function} Unsubscribe function.
     */
    subscribe(listener) {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
            // If no more components are listening, close the socket to save resources
            if (this.listeners.size === 0) {
                this.disconnect();
            }
        };
    }

    /**
     * Send data via WebSocket if connected.
     * @param {Object} data - Payload to send.
     */
    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.warn('Attempted to send data via WebSocket while not connected');
        }
    }

    /**
     * Forcefully disconnect the WebSocket.
     */
    disconnect() {
        if (this.socket) {
            this.manualClose = true;
            this.socket.close();
            this.socket = null;
            this.currentPath = null;
        }
    }
}

export const websocketService = new WebSocketService();
