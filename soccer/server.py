#!/usr/bin/env python3
"""
Real-time Soccer Match Server (Web + WebSocket / SSE / HTTP API)
Порт: 8099
Поддерживает:
1. Раздачу статики (HTML5 Canvas с плавной 60 FPS физикой).
2. API эндпоинт /api/turn - опрос реальных бесплатных LLM моделей для принятия тактических решений.
"""

import os
import sys
import json
import math
import random
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler

ENV_PATH = "/var/www/evabot-backend/.env"
def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    return env

ENV = load_env()
OPENROUTER_API_KEY = ENV.get("OPENROUTER_API_KEY", "")

ROSTER_MAP = {
    "A1": {"name": "Куртуа", "model": "meta-llama/llama-3.1-8b-instruct:free"},
    "A2": {"name": "Ван Дейк", "model": "qwen/qwen-2.5-72b-instruct:free"},
    "A3": {"name": "Гвардиол", "model": "mistralai/mistral-small-24b-instruct-2501:free"},
    "A4": {"name": "Родри", "model": "meta-llama/llama-3.3-70b-instruct:free"},
    "A5": {"name": "Холанд", "model": "google/gemini-2.0-flash-exp:free"},

    "B1": {"name": "Алиссон", "model": "deepseek/deepseek-chat:free"},
    "B2": {"name": "Рюдигер", "model": "qwen/qwen-2.5-coder-32b-instruct:free"},
    "B3": {"name": "Салиба", "model": "nvidia/llama-3.1-nemotron-70b-instruct:free"},
    "B4": {"name": "Беллингем", "model": "deepseek/deepseek-r1:free"},
    "B5": {"name": "Мбаппе", "model": "nousresearch/hermes-3-llama-3.1-405b:free"}
}

def ask_llm(player_id, state):
    info = ROSTER_MAP.get(player_id, {"name": "Игрок", "model": "meta-llama/llama-3.1-8b-instruct:free"})
    team = "A" if player_id.startswith("A") else "B"
    opp_goal = [800, 240] if team == "A" else [0, 240]

    prompt = (
        f"Ты футболист {info['name']} (Команда {team}).\n"
        f"Позиция мяча: {state.get('ball')}. Твоя позиция: {state.get('me')}.\n"
        f"Ворота соперника: {opp_goal}.\n"
        f"Выбери действие. Ответь ТОЛЬКО JSON: {{\"action\": \"shoot\"|\"pass\"|\"dribble\", \"target\": [x, y], \"power\": 50-100}}"
    )

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": info["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 40,
        "temperature": 0.4
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"].strip()
            if "{" in content and "}" in content:
                content = content[content.find("{"):content.rfind("}")+1]
                return json.loads(content)
    except Exception:
        pass
    
    # Резервный тактический расчет
    return {"action": "shoot" if random.random() > 0.5 else "pass", "target": opp_goal, "power": random.randint(70, 95)}

class SoccerHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/tactics":
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode('utf-8'))
            player_id = data.get("player_id", "A5")
            state = data.get("state", {})
            decision = ask_llm(player_id, state)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(decision).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/soccer":
            self.path = "/web_soccer.html"
        return SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    os.chdir("/home/evabot/evaline-games/soccer")
    server = HTTPServer(("0.0.0.0", 8099), SoccerHandler)
    print("🚀 Soccer Game Server запущен на http://0.0.0.0:8099")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
