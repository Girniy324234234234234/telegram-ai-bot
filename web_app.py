import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", 8080))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Mini App is alive")

if __name__ == "__main__":
    server = HTTPServer(("", PORT), Handler)
    print(f"Web server running on port {PORT}")
    server.serve_forever()
