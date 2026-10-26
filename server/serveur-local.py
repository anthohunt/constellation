"""Serveur de developpement.

Sert public/ et route /profil/<etape> vers wizard.html, comme server.js en prod.
Multi-thread : un serveur mono-connexion se bloquait des que le navigateur
gardait plusieurs connexions ouvertes (page + iframe + modules), et la page
ne rechargeait plus.
"""
import http.server, os, sys

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

class H(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"          # connexions persistantes gerees proprement
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=RACINE, **kw)
    def do_GET(self):
        chemin = self.path.split("?")[0]
        if chemin == "/" or chemin == "/profil" or chemin.startswith("/profil/"):
            self.path = "/wizard.html"
        return super().do_GET()
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = http.server.ThreadingHTTPServer(("", port), H)
    srv.daemon_threads = True
    print("http://localhost:%d/  et  /profil/<etape>" % port, flush=True)
    srv.serve_forever()
