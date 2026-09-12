#!/usr/bin/env python3
"""
Terminal TUI & ASCII Radar Viewport for Post-Apo Tycoon.
Provides a rich retro-futuristic terminal HUD with ANSI colors,
live mini-map, resource gauges, and council deliberation log.
"""

import sys
import time
import argparse
from typing import Dict, Any
from world_matrix import WorldMatrix, BIOMES, BUILDINGS
from simulation_engine import SimulationEngine
from llm_governors import LLMGovernorsCouncil, MINISTRIES

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[38;5;196m"
GREEN = "\033[38;5;46m"
YELLOW = "\033[38;5;226m"
BLUE = "\033[38;5;39m"
MAGENTA = "\033[38;5;201m"
CYAN = "\033[38;5;51m"
WHITE = "\033[38;5;255m"
GRAY = "\033[38;5;240m"
ORANGE = "\033[38;5;208m"
BG_DARK = "\033[48;5;234m"


def rad_color(rad: float) -> str:
    if rad < 20:
        return GREEN
    elif rad < 50:
        return YELLOW
    elif rad < 80:
        return ORANGE
    else:
        return RED


def render_tui(world: WorldMatrix, sim: SimulationEngine, council: LLMGovernorsCouncil, view_x: int = 0, view_y: int = 0, w: int = 21, h: int = 11) -> str:
    lines = []
    lines.append(f"{BOLD}{CYAN}╔═══════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    lines.append(f"{BOLD}{CYAN}║    EVALINE POST-APO TYCOON — INFINITE LIVING CANVAS (TUI ENGINE)                  ║{RESET}")
    lines.append(f"{BOLD}{CYAN}╚═══════════════════════════════════════════════════════════════════════════════════╝{RESET}")

    # Top stats
    r = sim.resources
    d = sim.last_net_delta
    pop = r["population"]
    mor = r["morality"]
    mor_col = GREEN if mor > 70 else (YELLOW if mor > 40 else RED)

    lines.append(
        f" {BOLD}ЦИКЛ:{RESET} {sim.tick_count:<4} │ "
        f"{YELLOW}⚡ Энергия:{RESET} {r['energy']:>4.0f}/{r['max_energy']:<4.0f} ({d.get('energy',0):+3.0f}) │ "
        f"{CYAN}💧 Вода:{RESET} {r['water']:>4.0f}/{r['max_water']:<4.0f} ({d.get('water',0):+3.0f}) │ "
        f"{GREEN}🌾 Пайки:{RESET} {r['food']:>4.0f}/{r['max_food']:<4.0f} ({d.get('food',0):+3.0f})"
    )
    lines.append(
        f" {WHITE}⚒ Лом:{RESET} {r['scrap']:>4.0f}/{r['max_scrap']:<4.0f} │ "
        f"{ORANGE}🏭 ЭВА-Полимер:{RESET} {r['eva_polymer']:>4.0f}/{r['max_eva_polymer']:<4.0f} │ "
        f"{MAGENTA}🔬 Наука:{RESET} {r['science']:>4.0f} │ "
        f"{mor_col}👥 Поселенцы:{RESET} {pop} (Боевой дух: {mor:.0f}%)"
    )
    lines.append(f"{GRAY}─────────────────────────────────────────────────────────────────────────────────────{RESET}")

    # Radar Viewport & Legend side-by-side
    lines.append(f"{BOLD} РАДАР СЕКТОРА (Центр: [{view_x}, {view_y}]):{RESET}")

    half_w = w // 2
    half_h = h // 2

    for dy in range(-half_h, half_h + 1):
        row_str = " "
        cur_y = view_y + dy
        for dx in range(-half_w, half_w + 1):
            cur_x = view_x + dx
            tile = world.get_tile(cur_x, cur_y)

            if not tile.explored:
                row_str += f"{GRAY}· {RESET}"
            elif tile.building:
                binfo = BUILDINGS[tile.building]
                row_str += f"{BOLD}{WHITE}{binfo['char']} {RESET}"
            elif tile.rubble:
                row_str += f"{GRAY}▧ {RESET}"
            else:
                binfo = BIOMES[tile.biome]
                col = rad_color(tile.radiation)
                row_str += f"{col}{binfo['char']} {RESET}"

        # Attach side info
        if dy == -half_h:
            row_str += f"  │ {BOLD}БИОМЫ & ОБОЗНАЧЕНИЯ:{RESET}"
        elif dy == -half_h + 1:
            row_str += f"  │ {WHITE}★{RESET} Штаб  {WHITE}⚡{RESET} СЭС  {WHITE}💧{RESET} Фильтр  {WHITE}🌾{RESET} Теплица"
        elif dy == -half_h + 2:
            row_str += f"  │ {WHITE}🏭{RESET} ЭВА-Экструдер  {WHITE}♨{RESET} Очистная станция"
        elif dy == -half_h + 3:
            row_str += f"  │ {GREEN}♣{RESET} Возрождённый лес  {YELLOW}░{RESET} Пустошь  {RED}☣{RESET} Кратер"
        elif dy == -half_h + 4:
            row_str += f"  │ {GRAY}·{RESET} Неразведанная зона (Туман войны)"
        elif dy == -half_h + 5:
            row_str += f"  │ {BOLD}МАТРИЦА СОВЕТА (5 LLM):{RESET}"
        elif dy == -half_h + 6:
            row_str += f"  │ 🌿 Qwen 72B (Экология)    ⚙ DeepSeek (Инженерия)"
        elif dy == -half_h + 7:
            row_str += f"  │ 📦 Gemini Flash (Снабжение) ⚖ Llama 3.3 (Социум)"
        else:
            row_str += "  │"

        lines.append(row_str)

    lines.append(f"{GRAY}─────────────────────────────────────────────────────────────────────────────────────{RESET}")
    lines.append(f"{BOLD} ПОСЛЕДНИЕ РЕШЕНИЯ МИНИСТЕРСТВ СОВЕТА:{RESET}")

    recent_decisions = council.decisions_history[-4:]
    if not recent_decisions:
        lines.append(f"  {GRAY}(Ожидание первого тактического хода совета...){RESET}")
    else:
        for dec in recent_decisions:
            col = GREEN if dec["success"] else RED
            status = "✓ УСПЕХ" if dec["success"] else "✗ ОТЛОЖЕНО"
            lines.append(
                f"  {dec['avatar']} {BOLD}{dec['title']}{RESET} [{dec['action'].upper()} -> {dec['target']}]: "
                f"{col}{status}{RESET} — {DIM}{dec['rationale']}{RESET}"
            )

    lines.append(f"{GRAY}─────────────────────────────────────────────────────────────────────────────────────{RESET}")
    lines.append(f"{BOLD} СОБЫТИЯ В МИРЕ:{RESET}")
    for evt in sim.event_log[-3:]:
        lines.append(f"  [{evt['tick']}] {evt['message']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaline Post-Apo Tycoon TUI")
    parser.add_argument("--ticks", type=int, default=3, help="Number of ticks to simulate")
    parser.add_argument("--auto", action="store_true", help="Run automated simulation loop")
    args = parser.parse_args()

    world = WorldMatrix(seed=42)
    sim = SimulationEngine(world)
    council = LLMGovernorsCouncil(world, sim)

    print(render_tui(world, sim, council))

    for i in range(args.ticks):
        time.sleep(0.5)
        sim.step_tick()
        council.step_council_turn()
        # Clear screen on ANSI
        print("\033[2J\033[H", end="")
        print(render_tui(world, sim, council))


if __name__ == "__main__":
    main()
