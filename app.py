#!/usr/bin/env python3
"""Prosty backend HTTP dla interfejsu index.html."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from t_konta import SilnikKont

ROOT = Path(__file__).resolve().parent
SILNIK = SilnikKont()
SILNIK.dodaj_konto("Kasa")


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _error(self, message: str, code: int = 400) -> None:
        self._send_json(code, {"error": message})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            return self._send_file(ROOT / "index.html", "text/html; charset=utf-8")
        if parsed.path == "/api/state":
            return self._send_json(200, SILNIK.as_dict())
        return self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            data = self._read_json()
            if parsed.path == "/api/accounts":
                konto = SILNIK.dodaj_konto(str(data.get("name", "")))
                return self._send_json(201, konto.as_dict())

            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 4 and parts[:2] == ["api", "accounts"] and parts[3] == "entries":
                konto_id = int(parts[2])
                zapis = SILNIK.dodaj_zapis(konto_id, str(data.get("side", "")), str(data.get("amount", "")))
                return self._send_json(201, {"id": zapis.id})

            return self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, KeyError) as exc:
            return self._error(str(exc), 400)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        try:
            data = self._read_json()
            if len(parts) == 3 and parts[:2] == ["api", "accounts"]:
                konto = SILNIK.zmien_nazwe_konta(int(parts[2]), str(data.get("name", "")))
                return self._send_json(200, konto.as_dict())

            if len(parts) == 5 and parts[:2] == ["api", "accounts"] and parts[3] == "entries":
                SILNIK.edytuj_zapis(int(parts[2]), int(parts[4]), str(data.get("side", "")), str(data.get("amount", "")))
                return self._send_json(200, {"ok": True})

            return self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, KeyError) as exc:
            return self._error(str(exc), 400)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        try:
            if len(parts) == 3 and parts[:2] == ["api", "accounts"]:
                SILNIK.usun_konto(int(parts[2]))
                return self._send_json(200, {"ok": True})

            if len(parts) == 5 and parts[:2] == ["api", "accounts"] and parts[3] == "entries":
                SILNIK.usun_zapis(int(parts[2]), int(parts[4]))
                return self._send_json(200, {"ok": True})

            return self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, KeyError) as exc:
            return self._error(str(exc), 400)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("Serwer uruchomiony: http://localhost:8000")
    server.serve_forever()
