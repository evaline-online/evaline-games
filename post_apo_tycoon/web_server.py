#!/usr/bin/env python3
"""
Web Server & REST API for Post-Apo Tycoon.
Serves static Canvas interface and exposes JSON endpoints for real-time
world state, viewport streaming, tick advancement, and LLM council actions.
"""

import os
import sys
import json
from typing import Any, Dict, List, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from world_matrix import WorldMatrix, BUILDINGS, BIOMES
from simulation_engine import SimulationEngine
from llm_governors import LLMGovernorsCouncil, MINISTRIES

PORT = 8098
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Global singleton instances for the server
WORLD = WorldMatrix(seed=42)
SIM = SimulationEngine(WORLD)
COUNCIL = LLMGovernorsCouncil(WORLD, SIM)


class PostApoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_path = os.path.join(STATIC_DIR, "canvas_world.html")
            with open(html_path, "rb") as f:
                self.wfile.write(f.read())
            return

        elif path == "/api/state":
            data = {
                "sim": SIM.get_state(),
                "world_summary": WORLD.get_world_summary(),
                "ministries": MINISTRIES,
                "buildings_catalog": BUILDINGS,
                "biomes_catalog": BIOMES,
                "decisions": COUNCIL.decisions_history[-10:],
            }
            self._send_json(data)
            return

        elif path == "/api/viewport":
            min_x = int(query.get("min_x", ["-8"])[0])
            min_y = int(query.get("min_y", ["-8"])[0])
            w = int(query.get("w", ["16"])[0])
            h = int(query.get("h", ["16"])[0])
            # Cap maximum viewport to prevent abuse
            w = max(4, min(48, w))
            h = max(4, min(48, h))

            tiles = WORLD.get_viewport(min_x, min_y, w, h)
            self._send_json({"min_x": min_x, "min_y": min_y, "w": w, "h": h, "tiles": tiles})
            return

        elif path == "/api/tile":
            x = int(query.get("x", ["0"])[0])
            y = int(query.get("y", ["0"])[0])
            tile = WORLD.get_tile(x, y)
            self._send_json(tile.to_dict())
            return

        # Fallback to static files
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/tick":
            # Advance 1 tick and run council
            SIM.step_tick()
            decisions = COUNCIL.step_council_turn()
            self._send_json({
                "status": "ok",
                "tick": SIM.tick_count,
                "decisions": decisions,
                "sim": SIM.get_state()
            })
            return

        elif path == "/api/action":
            action = payload.get("action")
            x = int(payload.get("x", 0))
            y = int(payload.get("y", 0))
            res = False

            if action == "explore":
                res = SIM.explore_tile(x, y)
            elif action == "clear":
                res = SIM.clear_rubble(x, y)
            elif action == "build":
                btype = payload.get("building_type", "")
                res = SIM.build_facility(x, y, btype, agent_name="Игрок-Архитектор")
            elif action == "upgrade":
                res = SIM.upgrade_facility(x, y)

            self._send_json({"status": "ok" if res else "failed", "action": action, "x": x, "y": y, "sim": SIM.get_state()})
            return

        self.send_error(404, "Endpoint not found")

    def _send_json(self, data: Any):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = PORT):
    server = HTTPServer(("0.0.0.0", port), PostApoHandler)
    print(f"[+] Post-Apo Tycoon Server running at http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped.")


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(p)
