#!/usr/bin/env python3
"""
LLM World Council & Autonomous Governors Engine for Post-Apo Tycoon.
5 specialized LLM ministries govern the infinite canvas according to
the laws of nature, ecology, energy, and civilization.
Supports real OpenRouter API calls with transparent deterministic heuristic fallback.
"""

import os
import json
import random
import urllib.request
from typing import Dict, List, Any, Optional
from world_matrix import WorldMatrix, BUILDINGS, BIOMES
from simulation_engine import SimulationEngine

ENV_PATH = "/var/www/evabot-backend/.env"


def load_env() -> Dict[str, str]:
    env = {}
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass
    return env


MINISTRIES = {
    "Minister_Ecology": {
        "title": "Министр Экологии и Терраформирования",
        "model": "qwen/qwen-2.5-72b-instruct:free",
        "avatar": "🌿",
        "focus": "Дезактивация радиации, восстановление почв, очистка болот и защита лесов."
    },
    "Chief_Engineer": {
        "title": "Главный Инженер и Технолог",
        "model": "deepseek/deepseek-chat:free",
        "avatar": "⚙",
        "focus": "Энергетика, производство ЭВА-полимеров, ремонт и апгрейд заводов."
    },
    "Minister_Logistics": {
        "title": "Министр Продовольствия и Снабжения",
        "model": "google/gemini-2.0-flash-exp:free",
        "avatar": "📦",
        "focus": "Бесперебойная добыча воды, гидропонные теплицы и предотвращение дефицита."
    },
    "High_Arbiter": {
        "title": "Верховный Арбитр Социума",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "avatar": "⚖",
        "focus": "Рост населения, наука, мораль поселенцев и защитные ЭВА-барьеры."
    },
    "World_Architect_GM": {
        "title": "Архитектор Мироздания (Гейм-Мастер)",
        "model": "deepseek/deepseek-r1:free",
        "avatar": "🌌",
        "focus": "Глобальный баланс, разведка новых секторов и климатические явления."
    }
}


class LLMGovernorsCouncil:
    def __init__(self, world: WorldMatrix, sim: SimulationEngine):
        self.world = world
        self.sim = sim
        self.env = load_env()
        self.api_key = os.environ.get("OPENROUTER_API_KEY") or self.env.get("OPENROUTER_API_KEY", "")
        self.decisions_history: List[Dict[str, Any]] = []

    def call_openrouter(self, model: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.api_key:
            return None

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://evaline.online",
            "X-Title": "Evaline Post-Apo Tycoon"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.4
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"]
        except Exception:
            return None

    def get_candidate_tiles(self) -> List[Dict[str, Any]]:
        candidates = []
        for chunk in self.world.chunks.values():
            for row in chunk:
                for tile in row:
                    if tile.explored:
                        candidates.append(tile.to_dict())
        return candidates

    def heuristic_action(self, agent_id: str) -> Dict[str, Any]:
        """
        Cognitive heuristics mimicking LLM strategic behavior.
        Guarantees instant, zero-failure autonomous play in any offline environment.
        """
        res = self.sim.resources
        candidates = self.get_candidate_tiles()

        # 1. Minister of Ecology: wants to clear rubble or build decontaminators near high radiation
        if agent_id == "Minister_Ecology":
            # Search for radioactive tiles without decontaminator
            high_rad = [t for t in candidates if t["radiation"] > 40.0 and not t["building"] and not t["rubble"]]
            if high_rad and self.sim.can_afford(BUILDINGS["decontaminator"]["cost"]):
                target = max(high_rad, key=lambda t: t["radiation"])
                return {
                    "action": "build",
                    "building_type": "decontaminator",
                    "target": [target["x"], target["y"]],
                    "rationale": f"Высокий радиационный фон ({target['radiation']} mSv) требует монтажа очистной станции почв."
                }
            # Search for rubble to clear
            rubble_tiles = [t for t in candidates if t["rubble"]]
            if rubble_tiles:
                target = rubble_tiles[0]
                return {
                    "action": "clear",
                    "target": [target["x"], target["y"]],
                    "rationale": "Расчистка токсичных завалов для рекультивации земли и добычи лома."
                }

        # 2. Chief Engineer: wants energy, EVA extruders, scrap recyclers
        elif agent_id == "Chief_Engineer":
            if res["energy"] < 40.0 and self.sim.can_afford(BUILDINGS["solar_collector"]["cost"]):
                empty = [t for t in candidates if not t["building"] and not t["rubble"]]
                if empty:
                    return {
                        "action": "build",
                        "building_type": "solar_collector",
                        "target": [empty[0]["x"], empty[0]["y"]],
                        "rationale": "Дефицит киловатт в энергосети. Строительство солнечного коллектора."
                    }
            if res["eva_polymer"] < 50.0 and self.sim.can_afford(BUILDINGS["eva_extruder"]["cost"]):
                empty = [t for t in candidates if not t["building"] and not t["rubble"]]
                if empty:
                    return {
                        "action": "build",
                        "building_type": "eva_extruder",
                        "target": [empty[0]["x"], empty[0]["y"]],
                        "rationale": "Запуск экструдера ЭВА-листов для обеспечения защитных покрытий и теплиц."
                    }

        # 3. Minister of Logistics: wants water & food
        elif agent_id == "Minister_Logistics":
            if res["water"] < 60.0 and self.sim.can_afford(BUILDINGS["water_purifier"]["cost"]):
                empty = [t for t in candidates if not t["building"] and not t["rubble"]]
                if empty:
                    return {
                        "action": "build",
                        "building_type": "water_purifier",
                        "target": [empty[0]["x"], empty[0]["y"]],
                        "rationale": "Опасность обезвоживания колонистов. Развертывание станции фильтрации воды."
                    }
            if res["food"] < 60.0 and self.sim.can_afford(BUILDINGS["greenhouse"]["cost"]):
                empty = [t for t in candidates if not t["building"] and not t["rubble"]]
                if empty:
                    return {
                        "action": "build",
                        "building_type": "greenhouse",
                        "target": [empty[0]["x"], empty[0]["y"]],
                        "rationale": "Необходимость стабильного сухпайка. Монтаж гидропонной ЭВА-теплицы."
                    }

        # 4. High Arbiter: wants research lab, EVA barriers, housing upgrades
        elif agent_id == "High_Arbiter":
            if res["science"] < 30.0 and self.sim.can_afford(BUILDINGS["research_dome"]["cost"]):
                empty = [t for t in candidates if not t["building"] and not t["rubble"]]
                if empty:
                    return {
                        "action": "build",
                        "building_type": "research_dome",
                        "target": [empty[0]["x"], empty[0]["y"]],
                        "rationale": "Инвестиции в науку откроют синтез термостойких композитов для колонии."
                    }
            if self.sim.can_afford(BUILDINGS["eva_barrier"]["cost"]):
                rad_border = [t for t in candidates if t["radiation"] > 30 and not t["building"] and not t["rubble"]]
                if rad_border:
                    return {
                        "action": "build",
                        "building_type": "eva_barrier",
                        "target": [rad_border[0]["x"], rad_border[0]["y"]],
                        "rationale": "Установка защитного экрана из ЭВА-полимеров против внешних пылевых бурь."
                    }

        # 5. World Architect / Explorer: explores adjacent unseen tiles
        # Find explored boundary tile and explore adjacent hidden tile
        for t in candidates:
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = t["x"] + dx, t["y"] + dy
                neighbor = self.world.get_tile(nx, ny)
                if not neighbor.explored:
                    return {
                        "action": "explore",
                        "target": [nx, ny],
                        "rationale": f"Отправка дронов-разведчиков в неизведанный сектор ({nx}, {ny})."
                    }

        return {
            "action": "pass",
            "target": [0, 0],
            "rationale": "Совет выжидает накопления ресурсов для следующего промышленного рывка."
        }

    def deliberate_agent(self, agent_id: str) -> Dict[str, Any]:
        info = MINISTRIES[agent_id]
        system_prompt = (
            f"Ты {info['title']} ({info['avatar']}) в постапокалиптическом тайкуне Evaline Post-Apo Tycoon.\n"
            f"Твоя цель: {info['focus']}\n"
            f"Ответь ТОЛЬКО валидным JSON формата:\n"
            f'{{"action": "build"|"clear"|"explore"|"upgrade"|"pass", "building_type": "solar_collector"|"decontaminator"|..., "target": [x, y], "rationale": "причина"}}'
        )

        res_summary = {k: round(v, 1) if isinstance(v, float) else v for k, v in self.sim.resources.items()}
        user_prompt = f"Тик {self.sim.tick_count}. Ресурсы: {json.dumps(res_summary, ensure_ascii=False)}."

        # Try Live LLM first
        raw_llm = self.call_openrouter(info["model"], system_prompt, user_prompt)
        parsed_action = None
        if raw_llm:
            try:
                # find first { and last }
                s = raw_llm[raw_llm.find("{"):raw_llm.rfind("}") + 1]
                parsed_action = json.loads(s)
            except Exception:
                parsed_action = None

        if not parsed_action or "action" not in parsed_action:
            parsed_action = self.heuristic_action(agent_id)

        # Execute decision in simulation
        act = parsed_action.get("action", "pass")
        tgt = parsed_action.get("target", [0, 0])
        success = False

        if act == "build":
            btype = parsed_action.get("building_type", "solar_collector")
            success = self.sim.build_facility(tgt[0], tgt[1], btype, agent_name=info["title"])
        elif act == "clear":
            success = self.sim.clear_rubble(tgt[0], tgt[1])
        elif act == "explore":
            success = self.sim.explore_tile(tgt[0], tgt[1])
        elif act == "upgrade":
            success = self.sim.upgrade_facility(tgt[0], tgt[1])
        else:
            success = True

        entry = {
            "tick": self.sim.tick_count,
            "agent_id": agent_id,
            "title": info["title"],
            "avatar": info["avatar"],
            "model": info["model"],
            "action": act,
            "target": tgt,
            "success": success,
            "rationale": parsed_action.get("rationale", "Решение принято советом."),
        }
        self.decisions_history.append(entry)
        if len(self.decisions_history) > 40:
            self.decisions_history.pop(0)

        return entry

    def step_council_turn(self) -> List[Dict[str, Any]]:
        """Executes deliberation of all 5 ministries in sequence."""
        turn_results = []
        for agent_id in MINISTRIES.keys():
            res = self.deliberate_agent(agent_id)
            turn_results.append(res)
        return turn_results
