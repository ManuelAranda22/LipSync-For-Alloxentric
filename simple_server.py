import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs
import subprocess
import asyncio
import websockets
import threading
import signal
import sys
import os
import time

PORT = 8056
WEBSOCKET_PORT = 8057

connected_clients = set()

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        text = data.get('text', '')

        result = generate_audio(text)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

        # Notify connected WebSocket clients
        asyncio.run(notify_clients(result))

    def do_GET(self):
        if self.path == '/get_transcription_files':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                transcription_files = os.listdir('Public/transcriptions')
                transcription_files.sort(key=lambda x: os.path.getmtime(f'Public/transcriptions/{x}'), reverse=True)
                print("Archivos de transcripción encontrados:", transcription_files)  # Log para depuración
                self.wfile.write(json.dumps(transcription_files).encode())
            except Exception as e:
                print(f"Error al obtener archivos de transcripción: {str(e)}")  # Log para depuración
                self.wfile.write(json.dumps([]).encode())
        else:
            super().do_GET()


def generate_audio(text):
    try:
        # Execute the apiAudio.py script with the text as an argument
        result = subprocess.run(['python', 'apiAudio.py', text], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Read the ultimo_archivo.txt to get the latest audio and mapping files
            with open('public/ultimo_archivo.txt', 'r') as f:
                lines = f.readlines()
                audio_file = lines[0].strip()
                mapping_file = lines[1].strip()
            
            return {
                'success': True, 
                'message': 'Audio generado correctamente',
                'audioUrl': audio_file,
                'mappingUrl': mapping_file
            }
        else:
            return {'success': False, 'error': result.stderr}
    except Exception as e:
        return {'success': False, 'error': str(e)}

class FileChangeHandler:
    def __init__(self):
        self.last_modified = 0
        self.last_content = ''

    def check_file(self):
        try:
            current_modified = os.path.getmtime('public/ultimo_archivo.txt')
            if current_modified > self.last_modified:
                self.last_modified = current_modified
                with open('public/ultimo_archivo.txt', 'r') as f:
                    content = f.read()
                if content != self.last_content:
                    self.last_content = content
                    lines = content.strip().split('\n')
                    audio_file = lines[0].strip()
                    mapping_file = lines[1].strip()
                    asyncio.run(notify_clients({
                        'audioUrl': audio_file,
                        'mappingUrl': mapping_file
                    }))
        except Exception as e:
            print(f"Error checking file: {e}")

async def websocket_handler(websocket, path):
    connected_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        connected_clients.remove(websocket)

async def notify_clients(data):
    disconnected_clients = []
    for client in connected_clients:
        try:
            await client.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosedOK:
            print("Cliente desconectado.")
            disconnected_clients.append(client)
    
    # Remover clientes desconectados
    for client in disconnected_clients:
        connected_clients.remove(client)

def run_http_server(httpd):
    print(f"Serving HTTP on port {PORT}")
    httpd.serve_forever()

def run_websocket_server(loop):
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(websocket_handler, "localhost", WEBSOCKET_PORT)
    loop.run_until_complete(start_server)
    print(f"WebSocket server running on port {WEBSOCKET_PORT}")
    loop.run_forever()

def run_file_checker():
    file_handler = FileChangeHandler()
    while True:
        file_handler.check_file()
        time.sleep(1)  # Check every second

def shutdown_servers(httpd, websocket_loop):
    print("\nShutting down servers...")
    httpd.shutdown()
    websocket_loop.call_soon_threadsafe(websocket_loop.stop)
    print("Servers successfully stopped.")

if __name__ == "__main__":
    # Setup HTTP server with ThreadingTCPServer
    handler = MyHandler
    httpd = socketserver.ThreadingTCPServer(("", PORT), handler)

    # Setup WebSocket server
    websocket_loop = asyncio.new_event_loop()

    # Start servers in separate threads
    http_thread = threading.Thread(target=run_http_server, args=(httpd,))
    websocket_thread = threading.Thread(target=run_websocket_server, args=(websocket_loop,))
    file_checker_thread = threading.Thread(target=run_file_checker)
    
    http_thread.start()
    websocket_thread.start()
    file_checker_thread.start()

    # Register signal handler for graceful shutdown
    def signal_handler(sig, frame):
        shutdown_servers(httpd, websocket_loop)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Wait for threads to complete
    http_thread.join()
    websocket_thread.join()
    file_checker_thread.join()