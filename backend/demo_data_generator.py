#!/usr/bin/env python3
"""
Demo Data Generator for GreenPulse Dashboard
Generates realistic energy consumption patterns and anomalies for demo purposes
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List
import math

class DemoDataGenerator:
    def __init__(self):
        self.connected_clients: Dict[websockets.WebSocketServerProtocol, int] = {}
        self.buildings = list(range(1, 51))  # 50 buildings
        self.base_consumption = {building_id: random.uniform(50, 200) for building_id in self.buildings}
        self.anomaly_probability = 0.05  # 5% chance of anomaly per data point
        
    def generate_energy_reading(self, building_id: int) -> Dict:
        """Generate realistic energy consumption data"""
        current_time = datetime.now()
        
        # Base consumption with daily and seasonal patterns
        hour = current_time.hour
        day_factor = 0.7 + 0.3 * math.sin((hour - 6) * math.pi / 12)  # Peak during day
        
        # Weekly pattern (lower on weekends)
        weekday = current_time.weekday()
        week_factor = 0.8 if weekday >= 5 else 1.0
        
        # Seasonal pattern (higher in summer/winter)
        month = current_time.month
        seasonal_factor = 1.0 + 0.3 * abs(math.sin((month - 3) * math.pi / 6))
        
        # Random variation
        noise = random.uniform(0.85, 1.15)
        
        base = self.base_consumption[building_id]
        meter_reading = base * day_factor * week_factor * seasonal_factor * noise
        
        # Occasional anomalies
        is_anomaly = random.random() < self.anomaly_probability
        if is_anomaly:
            anomaly_factor = random.choice([0.3, 2.5, 3.0])  # Sudden drop or spike
            meter_reading *= anomaly_factor
        
        return {
            "type": "energy_update",
            "building_id": building_id,
            "timestamp": current_time.isoformat(),
            "meter_reading": round(meter_reading, 2),
            "meter_type": random.randint(1, 4),
            "air_temperature": round(random.uniform(18, 26), 1),
            "is_anomaly": is_anomaly,
            "anomaly_score": random.uniform(0.8, 1.0) if is_anomaly else random.uniform(0.0, 0.3)
        }
    
    def generate_system_status(self) -> Dict:
        """Generate system status updates"""
        return {
            "type": "system_status",
            "timestamp": datetime.now().isoformat(),
            "total_buildings": len(self.buildings),
            "active_connections": len(self.connected_clients),
            "system_health": random.choice(["excellent", "good", "fair"]),
            "data_quality": random.uniform(0.95, 1.0),
            "processing_time_ms": random.uniform(10, 50)
        }
    
    async def handle_client(self, websocket, path):
        """Handle individual WebSocket client connections"""
        print(f"New client connected: {websocket.remote_address}")
        building_id = 1  # Default building
        self.connected_clients[websocket] = building_id
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to GreenPulse Demo Data Stream",
                "timestamp": datetime.now().isoformat()
            }))
            
            async for raw_message in websocket:
                try:
                    message = json.loads(raw_message)
                    
                    if message.get("type") == "subscribe_building":
                        building_id = message.get("building_id", 1)
                        self.connected_clients[websocket] = building_id
                        print(f"Client subscribed to building {building_id}")
                        
                        # Send current building data
                        data = self.generate_energy_reading(building_id)
                        await websocket.send(json.dumps(data))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            if websocket in self.connected_clients:
                del self.connected_clients[websocket]
    
    async def broadcast_data(self):
        """Broadcast data to all connected clients"""
        while True:
            try:
                if self.connected_clients:
                    # Send energy updates to each client based on their subscribed building
                    for websocket, building_id in list(self.connected_clients.items()):
                        try:
                            data = self.generate_energy_reading(building_id)
                            await websocket.send(json.dumps(data))
                            
                            # Occasionally send anomaly alerts
                            if data.get("is_anomaly"):
                                alert = {
                                    "type": "anomaly_alert",
                                    "building_id": building_id,
                                    "timestamp": data["timestamp"],
                                    "anomaly_score": data["anomaly_score"],
                                    "energy_value": data["meter_reading"],
                                    "severity": "high" if data["meter_reading"] > self.base_consumption[building_id] * 2 else "medium",
                                    "description": f"Unusual energy consumption detected in building {building_id}"
                                }
                                await websocket.send(json.dumps(alert))
                                
                        except websockets.exceptions.ConnectionClosed:
                            continue
                        except Exception as e:
                            print(f"Error sending data to client: {e}")
                    
                    # Send system status every 30 seconds
                    if int(time.time()) % 30 == 0:
                        status = self.generate_system_status()
                        for websocket in list(self.connected_clients.keys()):
                            try:
                                await websocket.send(json.dumps(status))
                            except:
                                continue
                
                await asyncio.sleep(5)  # Send updates every 5 seconds
                
            except Exception as e:
                print(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)
    
    async def start_server(self, host="0.0.0.0", port=8765):
        """Start the WebSocket server"""
        print(f"Starting demo data generator on {host}:{port}")
        
        # Start the broadcast task
        broadcast_task = asyncio.create_task(self.broadcast_data())
        
        # Start the WebSocket server
        server = await websockets.serve(self.handle_client, host, port)
        
        print("Demo data generator started. Press Ctrl+C to stop.")
        
        try:
            await asyncio.gather(server.wait_closed(), broadcast_task)
        except KeyboardInterrupt:
            print("\nStopping demo data generator...")
            broadcast_task.cancel()
            server.close()
            await server.wait_closed()

def main():
    """Run the demo data generator"""
    generator = DemoDataGenerator()
    
    try:
        asyncio.run(generator.start_server())
    except KeyboardInterrupt:
        print("\nShutdown complete.")

if __name__ == "__main__":
    main()