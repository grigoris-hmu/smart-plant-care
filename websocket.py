import subprocess
import threading

def start_websocket_server():
    try:
        print("Starting WebSocket server...")
        subprocess.run(["node", "websocket.js"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"WebSocket server failed to start: {e}")
    except FileNotFoundError:
        print("Node.js is not installed or 'websocket.js' file is missing.")

def websocket_server_thread():
    websocket_thread = threading.Thread(target=start_websocket_server)
    websocket_thread.daemon = True  
    websocket_thread.start()
    print("WebSocket server thread started.")

if __name__ == '__main__':
    websocket_server_thread()