from SmartPlantCare import app
import subprocess
import threading
import signal
import sys

# Define the paths or commands for Celery worker and beat
CELERY_WORKER_CMD = app.config['CELERY_WORKER_CMD']
CELERY_BEAT_CMD = app.config['CELERY_BEAT_CMD']

# Global variables to store Celery processes
worker_process = None
beat_process = None

def start_celery_worker():
    """Start the Celery worker process."""
    global worker_process
    worker_process = subprocess.Popen(CELERY_WORKER_CMD)
    print("Celery Worker is up.")

def start_celery_beat():
    """Start the Celery beat process."""
    global beat_process
    beat_process = subprocess.Popen(CELERY_BEAT_CMD)
    print("Celery Beat is up.")

def start_flask_app():
    """Start the Flask app."""
    app.run(debug=True)

def signal_handler(sig, frame):
    """Handle termination signals and clean up Celery processes."""
    print("Terminating Celery processes...")
    if worker_process:
        worker_process.terminate()
    if beat_process:
        beat_process.terminate()
    sys.exit(0)


# Function to start the WebSocket server
def start_websocket_server():
    try:
        # Run the websocket.js script
        subprocess.run(["node", "websocket.js"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"WebSocket server failed to start: {e}")
    except FileNotFoundError:
        print("Node.js is not installed or 'websocket.js' file is missing.")

# Start the WebSocket server in a separate thread
websocket_thread = threading.Thread(target=start_websocket_server)
websocket_thread.daemon = True  # Daemonize thread to exit when the main program exits
websocket_thread.start()

@app.route('/')
def index():
    return "Flask app running alongside WebSocket server!"


if __name__ == '__main__':
    # Register signal handlers for graceful termination
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signals

    # Start Celery worker and beat in separate threads
    worker_thread = threading.Thread(target=start_celery_worker)
    beat_thread = threading.Thread(target=start_celery_beat)
    worker_thread.start()
    beat_thread.start()

    # Start the Flask app in the main thread
    start_flask_app()
