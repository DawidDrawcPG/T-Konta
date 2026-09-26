#!/usr/bin/env python3
"""Lokalny serwer HTTP aplikacji T-konta."""

from __future__ import annotations

import base64
import json
import sys
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from t_konta import SilnikKont
from xlsx_export import build_xlsx, read_xlsx_state

ROOT = Path(__file__).resolve().parent
SILNIK = SilnikKont()


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
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
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_download(self, body: bytes, filename: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Niepoprawne dane żądania.")
        return data

    def _error(self, message: str, code: int = 400) -> None:
        self._send_json(code, {"error": message})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            return self._send_file(ROOT / "index.html", "text/html; charset=utf-8")
        if parsed.path == "/assets/pg-wzie-granat.png":
            return self._send_file(ROOT / "assets" / "pg-wzie-granat.png", "image/png")
        if parsed.path == "/assets/pg-wzie-tlo.jpeg":
            return self._send_file(ROOT / "assets" / "pg-wzie-tlo.jpeg", "image/jpeg")
        if parsed.path == "/api/state":
            return self._send_json(200, SILNIK.as_dict())
        if parsed.path == "/api/export/xlsx":
            workbook = build_xlsx(SILNIK.as_dict()["konta"])
            return self._send_download(workbook, "t-konta.xlsx")
        if parsed.path == "/favicon.ico":
            return self.send_error(HTTPStatus.NOT_FOUND)
        return self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            data = self._read_json()
            if parsed.path == "/api/accounts":
                konto = SILNIK.dodaj_konto(
                    str(data.get("name", "")), str(data.get("number", "")),
                    str(data.get("type", "Aktywne")), str(data.get("openingBalance", "0")),
                    str(data.get("openingSide", "W")), bool(data.get("active", True)),
                )
                return self._send_json(201, konto.as_dict())

            if parsed.path == "/api/import/xlsx":
                encoded = data.get("file", "")
                if not isinstance(encoded, str) or not encoded:
                    raise ValueError("Wybierz plik XLSX wyeksportowany z T-kont.")
                SILNIK.wczytaj_stan(read_xlsx_state(base64.b64decode(encoded)))
                return self._send_json(200, SILNIK.as_dict())

            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 4 and parts[:2] == ["api", "accounts"] and parts[3] == "entries":
                zapis = SILNIK.dodaj_zapis(
                    int(parts[2]), str(data.get("operationNumber", "")), str(data.get("side", "")), str(data.get("amount", "")),
                    str(data.get("date") or date.today().isoformat()), str(data.get("description", "")),
                )
                return self._send_json(201, {"id": zapis.id})
            return self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            return self._error(str(exc), 400)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        try:
            data = self._read_json()
            if len(parts) == 3 and parts[:2] == ["api", "accounts"]:
                konto = SILNIK.zmien_dane_konta(int(parts[2]), data)
                return self._send_json(200, konto.as_dict())
            if len(parts) == 5 and parts[:2] == ["api", "accounts"] and parts[3] == "entries":
                zapis = SILNIK.edytuj_zapis(
                    int(parts[2]), int(parts[4]), str(data.get("operationNumber", "")), str(data.get("side", "")), str(data.get("amount", "")),
                    str(data.get("date") or date.today().isoformat()), str(data.get("description", "")),
                )
                return self._send_json(200, {"id": zapis.id})
            return self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            return self._error(str(exc), 400)

    def do_DELETE(self) -> None:
        parts = [p for p in urlparse(self.path).path.split("/") if p]
        try:
            if len(parts) == 2 and parts == ["api", "accounts"]:
                SILNIK.wyczysc_konta()
                return self._send_json(200, {"ok": True})
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
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"T-konta działają: http://localhost:{port}")
    server.serve_forever()
