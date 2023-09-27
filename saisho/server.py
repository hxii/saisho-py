from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from .engine import TerminalPrint, saisho_engine


# class RequestHandler(BaseHTTPRequestHandler):
class RequestHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        ".html": "text/html",
        ".css": "text/css",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".ico": "image/vnd.microsoft.icon",
        "": "application/octet-stream",
    }

    def do_GET(self):
        response_code, filepath, filetype = self._parse_request(self.path)
        if response_code == 200:
            content = bytes(filepath.read_text(encoding="utf-8"), encoding="utf-8")
        elif response_code == 301:
            self._send_response(301)
            self.send_header("Location", self.path.rstrip("/"))
        else:
            content = bytes(
                "<html><h1>404 Not Found</h1><a href='/'>Go Back</a><hr><code>Saisho Serve</code></html>",
                encoding="utf-8",
            )
        self._send_response(response_code, content, filetype)

    def _parse_request(self, path: str) -> tuple[int, Path, str]:
        if path == "/":
            page_path = saisho_engine.OUTPUT_FOLDER / "index.html"
            if page_path.exists():
                return 200, page_path, "text/html"
            else:
                return 404, saisho_engine.OUTPUT_FOLDER, "text/html"
            return 200, saisho_engine.OUTPUT_FOLDER / "index.html"
        elif path.endswith("/"):
            self.send_response(301)
            return 301, saisho_engine.OUTPUT_FOLDER, "application/octet-stream"
        else:
            ext = self.path.split(".")[-1]
            if not self.extensions_map.get(f".{ext}"):
                path += ".html"
            path = path.lstrip("/")
            page_path = saisho_engine.OUTPUT_FOLDER / path
            if page_path.exists():
                return 200, page_path, self.guess_type(page_path)
            else:
                return 404, saisho_engine.OUTPUT_FOLDER, "text/html"

    def _send_response(self, response_code: int, content: str, filetype: str):
        self.send_response(response_code)
        if "Content-Type" not in self.headers:
            self.send_header("Content-Type", filetype)
        self.end_headers()
        self.wfile.write(content)


class Server:
    def __init__(self, port: int = 8000) -> None:
        self.port = port

    def run(self):
        self._server = HTTPServer(("localhost", self.port), RequestHandler)
        try:
            TerminalPrint.success(f"Starting Server ,Port: {self.port}")
            self._server.serve_forever()
        except KeyboardInterrupt:
            pass
        TerminalPrint.info("Stopping Server")
        self._server.socket.close()
