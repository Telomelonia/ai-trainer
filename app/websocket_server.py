import asyncio
import json
import websockets
import logging
from typing import Set, Dict, Any
from datetime import datetime
from arduino_connector import ArduinoConnector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StabilityWebSocketServer:
    """
    WebSocket server for broadcasting real-time stability data
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.arduino_connector = None
        self.server = None
        self.is_running = False
        
    async def register_client(self, websocket, path):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send initial connection message
        welcome_message = {
            "type": "connection",
            "message": "Connected to Core Training stability monitor",
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "host": self.host,
                "port": self.port,
                "arduino_mode": "simulation" if self.arduino_connector and self.arduino_connector.simulation_mode else "hardware"
            }
        }
        await websocket.send(json.dumps(welcome_message))
        
        try:
            # Keep connection alive and handle client messages
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def handle_client_message(self, websocket, message):
        """Handle incoming messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            if message_type == "request_data":
                # Send current stability data
                if self.arduino_connector:
                    current_data = self.arduino_connector.get_current_stability_data()
                    response = {
                        "type": "stability_data",
                        "data": current_data,
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(response))
            
            elif message_type == "reset_session":
                # Reset training session
                if self.arduino_connector:
                    self.arduino_connector.reset_session()
                    response = {
                        "type": "session_reset",
                        "message": "Training session has been reset",
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.broadcast_to_all(response)
            
            elif message_type == "get_status":
                # Get server and connection status
                status = {
                    "type": "status_response",
                    "server_status": "running" if self.is_running else "stopped",
                    "client_count": len(self.clients),
                    "arduino_status": self.arduino_connector.get_connection_info() if self.arduino_connector else None,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(status))
            
        except json.JSONDecodeError:
            error_response = {
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def broadcast_to_all(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps(data)
        disconnected_clients = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)
    
    async def arduino_data_callback(self, stability_data: Dict[str, Any]):
        """Callback function for Arduino data updates"""
        broadcast_data = {
            "type": "stability_update",
            "data": stability_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_all(broadcast_data)
    
    async def start_server(self, arduino_connector: ArduinoConnector = None):
        """Start the WebSocket server"""
        self.arduino_connector = arduino_connector or ArduinoConnector(simulation_mode=True)
        
        # Register callback for Arduino data
        if self.arduino_connector:
            self.arduino_connector.add_data_callback(self.arduino_data_callback)
        
        # Start WebSocket server
        self.server = await websockets.serve(
            self.register_client,
            self.host,
            self.port
        )
        self.is_running = True
        
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        
        # Start Arduino monitoring in background
        if self.arduino_connector:
            arduino_task = asyncio.create_task(self.arduino_connector.start_monitoring())
        
        # Start periodic status broadcast
        status_task = asyncio.create_task(self.periodic_status_broadcast())
        
        # Keep server running
        await self.server.wait_closed()
    
    async def periodic_status_broadcast(self):
        """Periodically broadcast server status to clients"""
        while self.is_running:
            try:
                if self.clients and self.arduino_connector:
                    # Broadcast current data every 2 seconds
                    current_data = self.arduino_connector.get_current_stability_data()
                    broadcast_data = {
                        "type": "periodic_update",
                        "data": current_data,
                        "server_info": {
                            "client_count": len(self.clients),
                            "uptime": str(datetime.now() - self.arduino_connector.session_start_time).split('.')[0]
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.broadcast_to_all(broadcast_data)
                
                await asyncio.sleep(2)  # Broadcast every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic broadcast: {e}")
                await asyncio.sleep(5)
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        self.is_running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        if self.arduino_connector:
            self.arduino_connector.close()
        
        logger.info("WebSocket server stopped")

# WebSocket client for Streamlit integration
class StabilityWebSocketClient:
    """
    WebSocket client for connecting to the stability server from Streamlit
    """
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.is_connected = False
        self.latest_data = None
        
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            logger.info(f"Connected to WebSocket server at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from WebSocket server")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the server"""
        if not self.is_connected or not self.websocket:
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def receive_message(self):
        """Receive a message from the server"""
        if not self.is_connected or not self.websocket:
            return None
        
        try:
            message = await self.websocket.recv()
            data = json.loads(message)
            
            # Store latest stability data
            if data.get("type") in ["stability_update", "periodic_update"]:
                self.latest_data = data.get("data")
            
            return data
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    async def request_current_data(self):
        """Request current stability data from server"""
        message = {"type": "request_data"}
        return await self.send_message(message)
    
    async def reset_session(self):
        """Request session reset"""
        message = {"type": "reset_session"}
        return await self.send_message(message)
    
    def get_latest_data(self):
        """Get the latest received stability data"""
        return self.latest_data

# Standalone server runner
async def run_websocket_server():
    """Run the WebSocket server standalone"""
    arduino = ArduinoConnector(simulation_mode=True)
    server = StabilityWebSocketServer()
    
    try:
        await server.start_server(arduino)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await server.stop_server()

if __name__ == "__main__":
    print("Starting Core Training WebSocket Server...")
    asyncio.run(run_websocket_server())