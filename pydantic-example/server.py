import http.server
import socketserver

PORT = 8001

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Set the response status code
            self.send_response(200)
            # Set the headers
            self.send_header("Content-type", "text/html")
            self.end_headers()
            # Write the response body
            self.wfile.write(b"Hello, World")
        else:
            # Use the default handler for other paths
            super().do_GET()

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
