import http.server
import socketserver
import os
import sys

PORT = 5500
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

class DevHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Force no-cache so browsers always get fresh CSS and JS
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))
        sys.stdout.flush()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == '__main__':
    with ThreadedHTTPServer(('0.0.0.0', PORT), DevHandler) as httpd:
        print(f"SkillSync Dev Server running on http://localhost:{PORT} (Serving {DIRECTORY})", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
