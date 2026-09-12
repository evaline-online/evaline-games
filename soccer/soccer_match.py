#!/usr/bin/env python3
"""
2D Soccer Simulation: 10 бесплатных LLM-моделей (5 vs 5)
Команда A (Синие - Завод Черноморск) vs Команда B (Красные - Склад Братислава)
"""

import os
import sys
import json
import math
import random
import time
import urllib.request
from soccer_physics import Ball, Player, FIELD_WIDTH, FIELD_HEIGHT, GOAL_Y_MIN, GOAL_Y_MAX

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

# 10 Бесплатных моделей для 10 игроков
ROSTER = [
    # КОМАНДА A: ЭВА Черноморск (Синие)
    {"id": "A1", "name": "Яшин-Llama", "team": "A", "role": "Вратарь", "x": 5.0, "y": 30.0, "model": "meta-llama/llama-3.1-8b-instruct:free"},
    {"id": "A2", "name": "Барези-Qwen", "team": "A", "role": "Левый защитник", "x": 25.0, "y": 18.0, "model": "qwen/qwen-2.5-72b-instruct:free"},
    {"id": "A3", "name": "Мальдини-Mistral", "team": "A", "role": "Правый защитник", "x": 25.0, "y": 42.0, "model": "mistralai/mistral-small-24b-instruct-2501:free"},
    {"id": "A4", "name": "Зидан-Llama70B", "team": "A", "role": "Полузащитник", "x": 45.0, "y": 30.0, "model": "meta-llama/llama-3.3-70b-instruct:free"},
    {"id": "A5", "name": "Шевченко-Gemini", "team": "A", "role": "Форвард", "x": 65.0, "y": 30.0, "model": "google/gemini-2.0-flash-exp:free"},

    # КОМАНДА B: ЭВА Братислава (Красные)
    {"id": "B1", "name": "Буффон-DeepSeek", "team": "B", "role": "Вратарь", "x": 95.0, "y": 30.0, "model": "deepseek/deepseek-chat:free"},
    {"id": "B2", "name": "Рамос-Coder", "team": "B", "role": "Левый защитник", "x": 75.0, "y": 18.0, "model": "qwen/qwen-2.5-coder-32b-instruct:free"},
    {"id": "B3", "name": "Пуйоль-Nemotron", "team": "B", "role": "Правый защитник", "x": 75.0, "y": 42.0, "model": "nvidia/llama-3.1-nemotron-70b-instruct:free"},
    {"id": "B4", "name": "Хави-DeepSeekR1", "team": "B", "role": "Полузащитник", "x": 55.0, "y": 30.0, "model": "deepseek/deepseek-r1:free"},
    {"id": "B5", "name": "Роналдо-Hermes", "team": "B", "role": "Форвард", "x": 35.0, "y": 30.0, "model": "nousresearch/hermes-3-llama-3.1-405b:free"}
]

def query_llm_tactics(player, ball, teammates, opponents):
    """Модель принимает тактическое решение на поле"""
    target_goal = [100.0, 30.0] if player.team == 'A' else [0.0, 30.0]
    
    prompt = (
        f"Ты футболист {player.name} ({player.role}, Команда {player.team}).\n"
        f"Координаты поля 100x60. Ворота соперника на {target_goal}.\n"
        f"Твоя позиция: [{player.x:.1f}, {player.y:.1f}]. Мяч на [{ball.x:.1f}, {ball.y:.1f}].\n"
        f"Напарники: {[{'id': t.id, 'pos': [round(t.x, 1), round(t.y, 1)]} for t in teammates]}\n"
        f"Выбери действие. Ответь ТОЛЬКО валидным JSON без маркдауна:\n"
        f'{{"action": "shoot" | "pass" | "dribble" | "tackle", "target": [x, y], "power": 1-100}}'
    )

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://evaline.online",
        "X-Title": "Evaline 2D Soccer"
    }
    payload = {
        "model": player.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 40,
        "temperature": 0.4
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"].strip()
            # Очистка от маркдауна если модель добавила ```json
            if "{" in content and "}" in content:
                json_str = content[content.find("{"):content.rfind("}")+1]
                return json.loads(json_str)
    except Exception:
        pass
    
    # Резервная эвристика если API медлит
    if player.dist_to(ball.x, ball.y) < 3.0:
        return {"action": "shoot", "target": target_goal, "power": 90}
    return {"action": "dribble", "target": [ball.x, ball.y], "power": 80}

def render_ascii_field(ball, players, score_a, score_b, minute):
    W, H = 50, 15
    grid = [[" " for _ in range(W)] for _ in range(H)]

    # Границы поля и ворота
    for x in range(W):
        grid[0][x] = "-"
        grid[H-1][x] = "-"
    for y in range(H):
        grid[y][0] = "|"
        grid[y][W-1] = "|"

    # Ворота
    for y in range(int(H*0.4), int(H*0.6)+1):
        grid[y][0] = "#"
        grid[y][W-1] = "#"

    # Игроки
    for p in players:
        gx = max(1, min(W-2, int((p.x / FIELD_WIDTH) * (W-1))))
        gy = max(1, min(H-2, int((p.y / FIELD_HEIGHT) * (H-1))))
        grid[gy][gx] = p.id[0] # 'A' or 'B'

    # Мяч
    bx = max(1, min(W-2, int((ball.x / FIELD_WIDTH) * (W-1))))
    by = max(1, min(H-2, int((ball.y / FIELD_HEIGHT) * (H-1))))
    grid[by][bx] = "⚽"

    print(f"\n⏱️ МИНУТА {minute}' | ТАБЛО: 🔵 Черноморск {score_a} : {score_b} Братислава 🔴")
    print("-" * (W + 2))
    for row in grid:
        print("".join(row))
    print("-" * (W + 2))

def run_soccer_simulation(total_minutes=5):
    print("================================================================")
    print("⚽ СТАРТ МАТЧА 2D SOCCER: 10 БЕСПЛАТНЫХ LLM В РЕАЛЬНОМ ВРЕМЕНИ")
    print("🔵 Черноморск (5 LLM) vs 🔴 Братислава (5 LLM)")
    print("================================================================")

    ball = Ball(50.0, 30.0)
    players = [Player(r["id"], r["name"], r["team"], r["role"], r["x"], r["y"], r["model"]) for r in ROSTER]
    score_a = 0
    score_b = 0

    for minute in range(1, total_minutes + 1):
        # 1. Поиск игрока, владеющего мячом или ближайшего к нему
        nearest_player = min(players, key=lambda p: p.dist_to(ball.x, ball.y))
        dist = nearest_player.dist_to(ball.x, ball.y)

        print(f"\n[Мин {minute}'] Мяч у/около: {nearest_player.name} ({nearest_player.id}, Команда {nearest_player.team}, модель: {nearest_player.model})")

        teammates = [p for p in players if p.team == nearest_player.team and p.id != nearest_player.id]
        opponents = [p for p in players if p.team != nearest_player.team]

        # LLM принимает решение
        decision = query_llm_tactics(nearest_player, ball, teammates, opponents)
        action = decision.get("action", "dribble")
        power = decision.get("power", 75)
        target = decision.get("target", [50.0, 30.0])

        print(f"🧠 {nearest_player.name} обдумал ситуацию и решил: [{action.upper()}] в точку {target} с силой {power}%")

        # 2. Физика удара или движения
        if dist <= 3.0: # Игрок бьет по мячу
            dx = target[0] - ball.x
            dy = target[1] - ball.y
            angle = math.atan2(dy, dx)
            ball.kick(angle, power)
        else: # Игрок бежит к мячу
            nearest_player.move_towards(ball.x, ball.y, speed_pct=power)

        # 3. Физический шаг мяча и игроков
        for _ in range(5):
            ball.step()
            for p in players:
                # Все полевые игроки подтягиваются по тактике
                if p.team == 'A':
                    p.move_towards(min(90.0, ball.x + (15 if p.role == 'FWD' else -10)), ball.y, speed_pct=40)
                else:
                    p.move_towards(max(10.0, ball.x - (15 if p.role == 'FWD' else -10)), ball.y, speed_pct=40)

        # 4. Проверка взятия ворот
        goal_status = ball.check_goal()
        if goal_status == "GOAL_TEAM_A":
            score_a += 1
            print(f"\n🎉 ГООООООООООЛ! 🔵 Команда Черноморск забивает гол! Автограф модели {nearest_player.model}!")
            ball = Ball(50.0, 30.0)
        elif goal_status == "GOAL_TEAM_B":
            score_b += 1
            print(f"\n🎉 ГООООООООООЛ! 🔴 Команда Братислава забивает гол! Автограф модели {nearest_player.model}!")
            ball = Ball(50.0, 30.0)

        # 5. Отрисовка поля
        render_ascii_field(ball, players, score_a, score_b, minute)
        time.sleep(1)

    print("\n🏁 ФИНАЛЬНЫЙ СВИСТОК!")
    print(f"ИТОГОВЫЙ СЧЁТ: 🔵 Черноморск {score_a} : {score_b} Братислава 🔴\n")

if __name__ == "__main__":
    run_soccer_simulation(total_minutes=5)
