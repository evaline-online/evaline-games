#!/usr/bin/env python3
"""
Simulation & Idle Tycoon Engine.
Handles economic production cycles, upkeep, environmental remediation,
population dynamics, and global world events for Post-Apo Tycoon.
"""

import random
from typing import Dict, List, Any, Optional
from world_matrix import WorldMatrix, BUILDINGS, BIOMES, Tile


class SimulationEngine:
    def __init__(self, world: WorldMatrix):
        self.world = world
        self.tick_count = 0

        # Global stockpiles
        self.resources = {
            "energy": 80.0,
            "max_energy": 250.0,
            "water": 120.0,
            "max_water": 300.0,
            "food": 100.0,
            "max_food": 300.0,
            "scrap": 150.0,
            "max_scrap": 500.0,
            "eva_polymer": 90.0,
            "max_eva_polymer": 400.0,
            "science": 15.0,
            "population": 12,
            "morality": 90.0,  # 0..100%
        }

        # Net per-tick delta for UI inspection
        self.last_net_delta = {k: 0.0 for k in self.resources if k != "population" and k != "morality"}

        # Event log
        self.event_log: List[Dict[str, Any]] = [
            {"tick": 0, "type": "system", "message": "Основан передовой Штаб-Бункер выживших (0, 0). Защитные экраны активированы."}
        ]

    def log_event(self, message: str, event_type: str = "info"):
        self.event_log.append({
            "tick": self.tick_count,
            "type": event_type,
            "message": message
        })
        if len(self.event_log) > 60:
            self.event_log.pop(0)

    def can_afford(self, cost: Dict[str, float]) -> bool:
        for res, amount in cost.items():
            if self.resources.get(res, 0.0) < amount:
                return False
        return True

    def deduct_cost(self, cost: Dict[str, float]):
        for res, amount in cost.items():
            self.resources[res] = max(0.0, self.resources.get(res, 0.0) - amount)

    def add_resources(self, prod: Dict[str, float], multiplier: float = 1.0):
        for res, amount in prod.items():
            if res in self.resources:
                max_key = f"max_{res}"
                max_val = self.resources.get(max_key, 999999.0)
                self.resources[res] = min(max_val, self.resources[res] + amount * multiplier)

    def explore_tile(self, x: int, y: int) -> bool:
        tile = self.world.get_tile(x, y)
        if tile.explored:
            return False

        cost = {"energy": 2.0}
        if not self.can_afford(cost):
            return False

        self.deduct_cost(cost)
        tile.explored = True
        self.log_event(f"Разведан новый сектор ({x}, {y}): {BIOMES[tile.biome]['name']}.", "explore")
        return True

    def clear_rubble(self, x: int, y: int) -> bool:
        tile = self.world.get_tile(x, y)
        if not tile.rubble:
            return False

        cost = {"energy": 4.0}
        if not self.can_afford(cost):
            return False

        self.deduct_cost(cost)
        tile.rubble = False
        scavenged_scrap = random.randint(8, 20)
        self.resources["scrap"] = min(self.resources["max_scrap"], self.resources["scrap"] + scavenged_scrap)
        self.log_event(f"Расчищены завалы на ({x}, {y}). Найдено +{scavenged_scrap} лома.", "economy")
        return True

    def build_facility(self, x: int, y: int, building_type: str, agent_name: Optional[str] = None) -> bool:
        if building_type not in BUILDINGS:
            return False

        tile = self.world.get_tile(x, y)
        if not tile.explored or tile.building is not None or tile.rubble:
            return False

        binfo = BUILDINGS[building_type]
        if not self.can_afford(binfo["cost"]):
            return False

        self.deduct_cost(binfo["cost"])
        tile.building = building_type
        tile.building_level = 1
        tile.building_hp = 100
        tile.assigned_agent = agent_name

        agent_tag = f"[{agent_name}] " if agent_name else ""
        self.log_event(f"{agent_tag}Возведено здание: {binfo['name']} на координатах ({x}, {y}).", "construction")
        return True

    def upgrade_facility(self, x: int, y: int) -> bool:
        tile = self.world.get_tile(x, y)
        if not tile.building:
            return False

        binfo = BUILDINGS[tile.building]
        upgrade_cost = {k: v * 1.5 * tile.building_level for k, v in binfo["cost"].items()}
        if not self.can_afford(upgrade_cost):
            return False

        self.deduct_cost(upgrade_cost)
        tile.building_level += 1
        tile.building_hp = 100
        self.log_event(f"Улучшено здание {binfo['name']} на ({x}, {y}) до уровня {tile.building_level}!", "construction")
        return True

    def step_tick(self):
        """Advances the simulation by 1 tick (day/cycle)."""
        self.tick_count += 1
        delta = {k: 0.0 for k in self.resources if k not in ["population", "morality"]}

        # 1. Facility Production & Upkeep
        active_buildings = []
        for chunk in self.world.chunks.values():
            for row in chunk:
                for tile in row:
                    if tile.building:
                        active_buildings.append(tile)

        for tile in active_buildings:
            binfo = BUILDINGS[tile.building]
            level_mult = 1.0 + (tile.building_level - 1) * 0.5

            # Check upkeep
            upkeep_met = True
            for u_res, u_val in binfo.get("upkeep", {}).items():
                if self.resources.get(u_res, 0.0) < u_val:
                    upkeep_met = False
                    break

            if upkeep_met:
                # Deduct upkeep
                for u_res, u_val in binfo.get("upkeep", {}).items():
                    self.resources[u_res] -= u_val
                    delta[u_res] -= u_val

                # Produce resources
                for p_res, p_val in binfo.get("prod", {}).items():
                    if p_res in self.resources:
                        amount = p_val * level_mult
                        max_key = f"max_{p_res}"
                        max_val = self.resources.get(max_key, 999999.0)
                        self.resources[p_res] = min(max_val, self.resources[p_res] + amount)
                        if p_res in delta:
                            delta[p_res] += amount

                # Environmental effects of buildings
                if tile.building == "decontaminator":
                    radius = binfo.get("decontam_radius", 2)
                    decay = binfo.get("rad_decay", 3.0) * level_mult
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            nt = self.world.get_tile(tile.x + dx, tile.y + dy)
                            nt.radiation = max(0.0, nt.radiation - decay)
                            nt.toxicity = max(0.0, nt.toxicity - (decay * 0.8))

                elif tile.building == "eva_barrier":
                    radius = binfo.get("decontam_radius", 2)
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            nt = self.world.get_tile(tile.x + dx, tile.y + dy)
                            nt.radiation = max(0.0, nt.radiation - 1.5)

        # 2. Colonist Life Support & Morality
        pop = self.resources["population"]
        water_needed = pop * 0.4
        food_needed = pop * 0.3

        if self.resources["water"] >= water_needed and self.resources["food"] >= food_needed:
            self.resources["water"] -= water_needed
            self.resources["food"] -= food_needed
            delta["water"] -= water_needed
            delta["food"] -= food_needed
            self.resources["morality"] = min(100.0, self.resources["morality"] + 1.0)
            # Natural population growth
            if self.resources["morality"] > 80.0 and self.tick_count % 5 == 0:
                self.resources["population"] += 1
                self.log_event("В поселение прибыли новые выжившие (+1 житель).", "society")
        else:
            # Deficit penalties
            self.resources["water"] = max(0.0, self.resources["water"] - water_needed)
            self.resources["food"] = max(0.0, self.resources["food"] - food_needed)
            self.resources["morality"] = max(10.0, self.resources["morality"] - 5.0)
            if self.resources["morality"] < 30.0 and pop > 5:
                self.resources["population"] -= 1
                self.log_event("Кризис снабжения: житель покинул убежище (-1 житель).", "danger")

        # 3. Nature Transformation
        # If a dead forest has low radiation and high moisture, it regrows!
        for chunk in self.world.chunks.values():
            for row in chunk:
                for tile in row:
                    if tile.explored:
                        if tile.biome == "dead_forest" and tile.radiation < 15.0 and tile.moisture > 40:
                            tile.biome = "regrown_forest"
                            tile.fertility = 75.0
                            self.log_event(f"Природа исцелилась! На ({tile.x}, {tile.y}) зазеленела Возрождённая Дубрава.", "nature")
                        elif tile.biome == "wasteland" and tile.radiation < 10.0 and tile.fertility > 60:
                            tile.biome = "fertile_oasis"
                            self.log_event(f"Оазис жизни на ({tile.x}, {tile.y}): пустошь превратилась в плодородную землю.", "nature")

        # 4. Procedural World Events (every 10 ticks)
        if self.tick_count % 10 == 0:
            self.trigger_random_world_event()

        self.last_net_delta = delta

    def trigger_random_world_event(self):
        events = [
            ("solar_burst", "Вспышка солнечной активности: солнечные батареи дали +60 энергии!", {"energy": 60.0}),
            ("acid_rain", "Кислотные осадки: токсичность открытых секторов выросла на 10%.", {}),
            ("cache_found", "Разведчики обнаружили склад древних ЭВА-матов: +40 ЭВА-полимера, +50 лома!", {"eva_polymer": 40.0, "scrap": 50.0}),
            ("nomads", "Торговый караван кочевников предложил обмен семян: +30 пищи.", {"food": 30.0}),
        ]
        evt_id, msg, bonus = random.choice(events)
        self.log_event(f"⚡ СОБЫТИЕ МИРА: {msg}", "event")

        for res, amt in bonus.items():
            if res in self.resources:
                self.resources[res] = min(self.resources[f"max_{res}"], self.resources[res] + amt)

        if evt_id == "acid_rain":
            for chunk in self.world.chunks.values():
                for row in chunk:
                    for tile in row:
                        if tile.explored and not tile.building:
                            tile.toxicity = min(100.0, tile.toxicity + 8.0)

    def get_state(self) -> Dict[str, Any]:
        world_summary = self.world.get_world_summary()
        return {
            "tick": self.tick_count,
            "resources": {k: round(v, 1) if isinstance(v, float) else v for k, v in self.resources.items()},
            "net_delta": {k: round(v, 1) for k, v in self.last_net_delta.items()},
            "world_summary": world_summary,
            "recent_events": self.event_log[-15:],
        }
