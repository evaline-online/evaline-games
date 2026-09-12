#!/usr/bin/env python3
"""
2D Soccer Physics Engine
Поле: 100 x 60.
Координаты: X [0..100], Y [0..60]
Ворота Команды A: X=0, Y=[25..35]
Ворота Команды B: X=100, Y=[25..35]
"""

import math

FIELD_WIDTH = 100.0
FIELD_HEIGHT = 60.0
GOAL_Y_MIN = 24.0
GOAL_Y_MAX = 36.0
FRICTION = 0.96
BALL_MAX_SPEED = 6.0
PLAYER_MAX_SPEED = 2.5

class Ball:
    def __init__(self, x=50.0, y=30.0):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0

    def kick(self, angle_rad, power):
        speed = min(power * 0.06, BALL_MAX_SPEED)
        self.vx = math.cos(angle_rad) * speed
        self.vy = math.sin(angle_rad) * speed

    def step(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= FRICTION
        self.vy *= FRICTION

        if abs(self.vx) < 0.02: self.vx = 0.0
        if abs(self.vy) < 0.02: self.vy = 0.0

        # Отскок от верхнего и нижнего борта
        if self.y < 1.0:
            self.y = 1.0
            self.vy = -self.vy * 0.8
        elif self.y > FIELD_HEIGHT - 1.0:
            self.y = FIELD_HEIGHT - 1.0
            self.vy = -self.vy * 0.8

        # Боковые границы (вне ворот)
        if self.x < 1.0:
            if not (GOAL_Y_MIN <= self.y <= GOAL_Y_MAX):
                self.x = 1.0
                self.vx = -self.vx * 0.8
        elif self.x > FIELD_WIDTH - 1.0:
            if not (GOAL_Y_MIN <= self.y <= GOAL_Y_MAX):
                self.x = FIELD_WIDTH - 1.0
                self.vx = -self.vx * 0.8

    def check_goal(self):
        if self.x <= 0.0 and GOAL_Y_MIN <= self.y <= GOAL_Y_MAX:
            return "GOAL_TEAM_B" # Забили команде A
        elif self.x >= FIELD_WIDTH and GOAL_Y_MIN <= self.y <= GOAL_Y_MAX:
            return "GOAL_TEAM_A" # Забили команде B
        return None

class Player:
    def __init__(self, pid, name, team, role, x, y, model):
        self.id = pid
        self.name = name
        self.team = team # 'A' or 'B'
        self.role = role # 'GK', 'DEF_L', 'DEF_R', 'MID', 'FWD'
        self.x = x
        self.y = y
        self.model = model
        self.stamina = 100.0

    def move_towards(self, target_x, target_y, speed_pct=100.0):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.5:
            return
        speed = (speed_pct / 100.0) * PLAYER_MAX_SPEED
        step = min(dist, speed)
        self.x += (dx / dist) * step
        self.y += (dy / dist) * step

        # Границы поля для игрока
        self.x = max(1.0, min(FIELD_WIDTH - 1.0, self.x))
        self.y = max(1.0, min(FIELD_HEIGHT - 1.0, self.y))

    def dist_to(self, target_x, target_y):
        return math.hypot(target_x - self.x, target_y - self.y)
