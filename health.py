#!/usr/bin/env python3
"""
Simple health check server to test AppRunner connectivity.
Run this instead of Streamlit to test basic HTTP functionality.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "healthy",
                "message": "LLM Stress Test App is running",
                "path": self.path,
                "headers": dict(self.headers)
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        print(f"[HEALTH] {format % args}")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"Health check server starting on port {port}")
    print(f"Visit http://localhost:{port}/health to test")
    server.serve_forever() 