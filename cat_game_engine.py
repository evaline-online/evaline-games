#!/usr/bin/env python3
"""
Evaline Games - Коты и Мышь на складе Evaline (10 LLM моделей в реальном времени).
"""

import os
import sys
import json
import random
import time
import urllib.request

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

BOARD_SIZE = 5
MAX_ROUNDS = 5

CATS = [
    {"id": "Cat-01", "name": "Барсик-Технолог", "model": "meta-llama/llama-3.3-70b-instruct:free"},
    {"id": "Cat-02", "name": "Мурзик-Спринтер", "model": "google/gemini-2.0-flash-exp:free"},
    {"id": "Cat-03", "name": "Рыжик-Тактик", "model": "qwen/qwen-2.5-72b-instruct:free"},
]

def query_model_action(cat, board_state):
    prompt = (
        f"Ты кот {cat['name']} в игре на сетке {BOARD_SIZE}x{BOARD_SIZE}.\n"
        f"Позиция мыши: {board_state['mouse']}\n"
        f"Твоя позиция: {cat['pos']}\n"
        f"Другие коты: {[c['pos'] for c in board_state['cats'] if c['id'] != cat['id']]}\n"
        f"Выбери один ход ближе к мыши. Ответь ТОЛЬКО одним словом из списка: up, down, left, right, stay."
    )
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://evaline.online",
        "X-Title": "Evaline Games"
    }
    payload = {
        "model": cat["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 10,
        "temperature": 0.5
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            action = data["choices"][0]["message"]["content"].strip().lower()
            for act in ["up", "down", "left", "right", "stay"]:
                if act in action:
                    return act
            return "stay"
    except Exception:
        return random.choice(["up", "down", "left", "right"])

def play_game():
    print("🎮 ЗАПУСК ИГРЫ: «КОТЫ EVALINE» (Эксперимент с LLM)")
    mouse_pos = [random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)]
    for c in CATS:
        c["pos"] = [random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)]

    print(f"🐭 Мышь стартует на позиции: {mouse_pos}")
    for c in CATS:
        print(f"🐱 {c['name']} ({c['id']}) на позиции: {c['pos']}")

    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"\n--- РАУНД {round_num} ---")
        # Ход мыши (случайный шаг)
        mouse_pos[0] = max(0, min(BOARD_SIZE-1, mouse_pos[0] + random.choice([-1, 0, 1])))
        mouse_pos[1] = max(0, min(BOARD_SIZE-1, mouse_pos[1] + random.choice([-1, 0, 1])))
        print(f"🐭 Мышь переместилась в: {mouse_pos}")

        board_state = {"mouse": mouse_pos, "cats": CATS}

        for c in CATS:
            action = query_model_action(c, board_state)
            if action == "up":
                c["pos"][0] = max(0, c["pos"][0] - 1)
            elif action == "down":
                c["pos"][0] = min(BOARD_SIZE-1, c["pos"][0] + 1)
            elif action == "left":
                c["pos"][1] = max(0, c["pos"][1] - 1)
            elif action == "right":
                c["pos"][1] = min(BOARD_SIZE-1, c["pos"][1] + 1)
            
            print(f"🐱 {c['name']} выбрал [{action}] -> Новая позиция: {c['pos']}")

            if c["pos"] == mouse_pos:
                print(f"\n🏆 ПОБЕДА! Кот {c['name']} ({c['id']}) поймал мышь в раунде {round_num}!")
                return

    print("\n🧀 Ничья! Мышь благополучно спряталась между рулонами ЭВА листов.")

if __name__ == "__main__":
    play_game()
