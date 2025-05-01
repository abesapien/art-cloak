import uvicorn
import socket
import sys
import random

def find_available_port():
    """Find an available port to run the server on."""
    # First try some common ports
    common_ports = [8001, 8080, 8888, 9000, 5000, 3000]
    for port in common_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    
    # Try a wider range with random sampling first
    range_start = 8000
    range_end = 9999
    
    # Try 20 random ports first for better distribution
    for _ in range(20):
        port = random.randint(range_start, range_end)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    
    # Methodically try ports in sequence as a fallback
    port = range_start
    while port <= range_end:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            port += 1
            # Skip ahead for efficiency after first 100 ports
            if port > range_start + 100:
                port += 9
    
    print("Error: Could not find any available port. Please close some applications and try again.")
    sys.exit(1)

if __name__ == "__main__":
    port = find_available_port()
    print(f"Starting backend server on port {port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
