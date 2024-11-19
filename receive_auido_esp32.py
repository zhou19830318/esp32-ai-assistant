from machine import I2S, Pin
import network
import gc
import time
import asyncio
import socket
import struct

# WebSocket server URL
WS_HOST = "192.168.2.110"
WS_PORT = 8765
# Constants
BUFFER_SIZE = 4096
# I2S configuration max98357
SCK_PIN = 27
WS_PIN = 33
SD_PIN = 21
SAMPLE_RATE = 16000
BITS = 16

# Initialize I2S
audio_out = I2S(0,
                sck=Pin(SCK_PIN),
                ws=Pin(WS_PIN),
                sd=Pin(SD_PIN),
                mode=I2S.TX,
                bits=BITS,
                format=I2S.MONO,
                rate=SAMPLE_RATE,
                ibuf=BUFFER_SIZE)

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid, password)
        
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            time.sleep(1)
            
        if wlan.isconnected():
            print('Network connection successful')
            print('Network config:', wlan.ifconfig())
            return True
        else:
            print('Connection failed')
            return False
    else:
        print('Already connected to network')
        print('Network config:', wlan.ifconfig())
        return True

class AudioPlayer:
    def __init__(self):
        self.audio_buffer = bytearray()

    def play_audio_chunk(self, chunk):
        try:
            self.audio_buffer.extend(chunk)
            if len(self.audio_buffer) >= BUFFER_SIZE:
                audio_out.write(self.audio_buffer)
                self.audio_buffer = bytearray()
        except Exception as e:
            print(f"Error playing audio: {e}")
            self.audio_buffer = bytearray()
            
    def flush(self):
        if len(self.audio_buffer) > 0:
            audio_out.write(self.audio_buffer)
            self.audio_buffer = bytearray()

class WebSocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.audio_player = AudioPlayer()
        self.connected = False
        self.data_received = False

    def connect(self):
        try:
            print(f"Connecting to {self.host}:{self.port}")
            self.socket = socket.socket()
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            
            key = "dGhlIHNhbXBsZSBub25jZQ=="
            handshake = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "\r\n"
            )
            print("Sending handshake...")
            self.socket.send(handshake.encode())
            
            response = self.socket.recv(1024).decode()
            print(f"Received response: {response}")
            
            if "101 Switching Protocols" in response:
                print("WebSocket connection established")
                self.connected = True
                return True
            else:
                print("WebSocket handshake failed")
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self.connected = False
        if self.socket:
            try:
                # Send close frame
                self.socket.send(bytes([0x88, 0x00]))
                self.socket.close()
            except:
                pass
            self.socket = None
        self.audio_player.flush()  # Flush any remaining audio data

    def receive_frame(self):
        try:
            header = self.socket.recv(2)
            if not header or len(header) < 2:
                print("No header received")
                return None

            first_byte = header[0]
            fin = (first_byte & 0x80) != 0
            opcode = first_byte & 0x0F

            second_byte = header[1]
            is_masked = (second_byte & 0x80) != 0
            payload_length = second_byte & 0x7F

            if payload_length == 126:
                length_data = self.socket.recv(2)
                payload_length = struct.unpack("!H", length_data)[0]
            elif payload_length == 127:
                length_data = self.socket.recv(8)
                payload_length = struct.unpack("!Q", length_data)[0]

            if is_masked:
                masking_key = self.socket.recv(4)

            payload = b""
            remaining = payload_length
            while remaining > 0:
                chunk = self.socket.recv(remaining)
                if not chunk:
                    break
                payload += chunk
                remaining -= len(chunk)

            if is_masked:
                unmasked = bytearray(payload_length)
                for i in range(payload_length):
                    unmasked[i] = payload[i] ^ masking_key[i % 4]
                payload = bytes(unmasked)

            if opcode == 0x8:  # Close frame
                print("Received close frame")
                self.connected = False
                return None
            elif opcode == 0x9:  # Ping frame
                self.send_pong()
                return None
            elif opcode == 0xA:  # Pong frame
                return None

            self.data_received = True
            return payload

        except Exception as e:
            print(f"Error receiving frame: {e}")
            self.connected = False
            return None

    def send_pong(self):
        try:
            self.socket.send(bytes([0x8A, 0x00]))
        except Exception as e:
            print(f"Error sending pong: {e}")
            self.connected = False

async def handle_websocket():
    client = WebSocketClient(WS_HOST, WS_PORT)
    
    try:
        if not client.connect():
            print("Connection failed")
            return

        print("Starting to receive data...")
        no_data_count = 0
        while client.connected and no_data_count < 50:  # Add timeout mechanism
            audio_chunk = client.receive_frame()
            if not audio_chunk:
                no_data_count += 1
                await asyncio.sleep_ms(100)
                continue
                
            print(f"Received chunk of size: {len(audio_chunk)}")
            client.audio_player.play_audio_chunk(audio_chunk)
            no_data_count = 0
            await asyncio.sleep_ms(10)
            gc.collect()

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        client.disconnect()
        print("Connection closed")

def main():
    ssid = 'Prefoco'
    password = '18961210318'
    if not connect_wifi(ssid, password):
        print("WiFi connection failed. Exiting...")
        return
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(handle_websocket())
    loop.close()
    
    print("Program finished")
    # Optional: deep sleep or reset

if __name__ == '__main__':
    main()
