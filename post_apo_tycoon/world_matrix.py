#!/usr/bin/env python3
"""
World Matrix & Infinite Procedural Canvas Engine for Post-Apo Tycoon.
Simulates a seamless, infinite grid of chunks based on mathematical noise,
physical parameters of nature (radiation, toxicity, moisture, fertility),
and civilizational infrastructure.
"""

import math
import random
import hashlib
from typing import Dict, List, Tuple, Any, Optional

CHUNK_SIZE = 16  # 16x16 tiles per chunk

# Biome definitions with their base ecological signatures
BIOMES = {
    "wasteland": {
        "name": "Радиоактивная Пустошь",
        "char": "░",
        "color": "#9e9d24",
        "base_rad": 65,
        "base_tox": 40,
        "base_moist": 15,
        "base_fert": 5,
    },
    "radioactive_crater": {
        "name": "Эпицентр Взрыва (Кратер)",
        "char": "☣",
        "color": "#76ff03",
        "base_rad": 95,
        "base_tox": 85,
        "base_moist": 5,
        "base_fert": 0,
    },
    "dead_forest": {
        "name": "Обугленный Мертвый Лес",
        "char": "♠",
        "color": "#4e342e",
        "base_rad": 45,
        "base_tox": 30,
        "base_moist": 25,
        "base_fert": 15,
    },
    "regrown_forest": {
        "name": "Возрождённая Дубрава",
        "char": "♣",
        "color": "#2e7d32",
        "base_rad": 10,
        "base_tox": 5,
        "base_moist": 65,
        "base_fert": 80,
    },
    "toxic_marsh": {
        "name": "Кислотное Болото",
        "char": "≈",
        "color": "#00b0ff",
        "base_rad": 55,
        "base_tox": 90,
        "base_moist": 90,
        "base_fert": 10,
    },
    "clean_spring": {
        "name": "Чистый Родник",
        "char": "≋",
        "color": "#00e5ff",
        "base_rad": 5,
        "base_tox": 2,
        "base_moist": 95,
        "base_fert": 90,
    },
    "ruins": {
        "name": "Руины Древнего Мегаполиса",
        "char": "🏛",
        "color": "#78909c",
        "base_rad": 50,
        "base_tox": 35,
        "base_moist": 20,
        "base_fert": 0,
    },
    "fertile_oasis": {
        "name": "Цветущий Оазис",
        "char": "✿",
        "color": "#00e676",
        "base_rad": 5,
        "base_tox": 0,
        "base_moist": 80,
        "base_fert": 95,
    },
    "eva_industrial": {
        "name": "ЭВА-Заводской Комплекс",
        "char": "⚙",
        "color": "#ff9100",
        "base_rad": 15,
        "base_tox": 10,
        "base_moist": 40,
        "base_fert": 30,
    },
}

BUILDINGS = {
    "bunker_hq": {
        "name": "Штаб-Бункер Выживших",
        "char": "★",
        "icon": "bunker",
        "cost": {"scrap": 0, "eva_polymer": 0, "energy": 0},
        "prod": {"science": 1},
        "upkeep": {"water": 1, "food": 1},
        "rad_resist": 50,
    },
    "eva_barrier": {
        "name": "Защитный Экран из ЭВА-Полимера",
        "char": "🛡",
        "icon": "barrier",
        "cost": {"scrap": 20, "eva_polymer": 50},
        "prod": {},
        "upkeep": {"energy": 1},
        "rad_resist": 90,
        "decontam_radius": 2,
    },
    "decontaminator": {
        "name": "Очистная Станция Почвы",
        "char": "♨",
        "icon": "decontam",
        "cost": {"scrap": 60, "eva_polymer": 30},
        "prod": {"clean_soil": 5},
        "upkeep": {"energy": 4, "water": 2},
        "decontam_radius": 3,
        "rad_decay": 4.0,
    },
    "solar_collector": {
        "name": "Солнечная Электростанция",
        "char": "⚡",
        "icon": "solar",
        "cost": {"scrap": 40, "eva_polymer": 20},
        "prod": {"energy": 12},
        "upkeep": {},
    },
    "water_purifier": {
        "name": "Опреснитель и Фильтр Воды",
        "char": "💧",
        "icon": "water",
        "cost": {"scrap": 50, "eva_polymer": 40},
        "prod": {"water": 10},
        "upkeep": {"energy": 3},
    },
    "greenhouse": {
        "name": "Гидропонная ЭВА-Теплица",
        "char": "🌾",
        "icon": "farm",
        "cost": {"scrap": 45, "eva_polymer": 60},
        "prod": {"food": 8},
        "upkeep": {"energy": 2, "water": 4},
    },
    "scrap_recycler": {
        "name": "Сортировочный Переработчик Лома",
        "char": "⚒",
        "icon": "recycler",
        "cost": {"scrap": 30, "eva_polymer": 10},
        "prod": {"scrap": 15},
        "upkeep": {"energy": 3},
    },
    "eva_extruder": {
        "name": "Термо-Экструдер Листов ЭВА",
        "char": "🏭",
        "icon": "factory",
        "cost": {"scrap": 100, "eva_polymer": 20},
        "prod": {"eva_polymer": 10},
        "upkeep": {"energy": 6, "scrap": 5},
    },
    "research_dome": {
        "name": "Научный Купол Прогресса",
        "char": "🔬",
        "icon": "lab",
        "cost": {"scrap": 80, "eva_polymer": 75},
        "prod": {"science": 5},
        "upkeep": {"energy": 5, "water": 2},
    }
}


def pseudo_noise2d(x: int, y: int, seed: int = 42) -> float:
    """
    Deterministic multi-octave pseudo-random gradient noise in range [0.0, 1.0].
    Zero external dependencies, fast and reproducible.
    """
    val = 0.0
    freq = 0.05
    amp = 1.0
    total_amp = 0.0

    for octave in range(3):
        n_x = int(x * freq * 100)
        n_y = int(y * freq * 100)
        h = int(hashlib.md5(f"{n_x}_{n_y}_{seed}_{octave}".encode()).hexdigest()[:8], 16)
        normalized = (h % 10000) / 10000.0
        val += normalized * amp
        total_amp += amp
        freq *= 2.0
        amp *= 0.5

    return val / total_amp


class Tile:
    def __init__(self, x: int, y: int, seed: int = 42):
        self.x = x
        self.y = y
        self.seed = seed

        # Generate procedural values based on world coordinates
        elev_noise = pseudo_noise2d(x, y, seed)
        moist_noise = pseudo_noise2d(x + 1000, y + 1000, seed + 1)
        rad_noise = pseudo_noise2d(x + 2000, y + 2000, seed + 2)

        self.elevation = int(elev_noise * 100)  # 0..100
        self.moisture = int(moist_noise * 100)  # 0..100
        self.temperature = int(10 + (1.0 - elev_noise) * 25 + (moist_noise - 0.5) * 10)  # ~10..35 C

        # Determine initial biome
        if rad_noise > 0.85:
            self.biome = "radioactive_crater"
        elif rad_noise > 0.65:
            self.biome = "wasteland"
        elif elev_noise > 0.70 and moist_noise < 0.35:
            self.biome = "ruins"
        elif moist_noise > 0.75:
            self.biome = "toxic_marsh" if rad_noise > 0.40 else "clean_spring"
        elif moist_noise > 0.45:
            self.biome = "dead_forest" if rad_noise > 0.30 else "regrown_forest"
        elif moist_noise > 0.30 and rad_noise < 0.25:
            self.biome = "fertile_oasis"
        else:
            self.biome = "wasteland"

        binfo = BIOMES[self.biome]
        self.radiation = float(binfo["base_rad"])
        self.toxicity = float(binfo["base_tox"])
        self.fertility = float(binfo["base_fert"])
        self.rubble = (self.biome in ["wasteland", "ruins", "dead_forest"])

        # Building & Exploration state
        self.explored = False
        self.building: Optional[str] = None
        self.building_level: int = 1
        self.building_hp: int = 100
        self.assigned_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "biome": self.biome,
            "biome_name": BIOMES[self.biome]["name"],
            "color": BIOMES[self.biome]["color"],
            "char": BIOMES[self.biome]["char"],
            "elevation": self.elevation,
            "moisture": self.moisture,
            "temperature": self.temperature,
            "radiation": round(self.radiation, 1),
            "toxicity": round(self.toxicity, 1),
            "fertility": round(self.fertility, 1),
            "rubble": self.rubble,
            "explored": self.explored,
            "building": self.building,
            "building_name": BUILDINGS[self.building]["name"] if self.building else None,
            "building_char": BUILDINGS[self.building]["char"] if self.building else None,
            "building_level": self.building_level,
            "building_hp": self.building_hp,
            "assigned_agent": self.assigned_agent,
        }


class WorldMatrix:
    """
    Manages chunks and global environmental logic across an infinite canvas.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.chunks: Dict[Tuple[int, int], List[List[Tile]]] = {}
        # Spawn initial headquarters at (0, 0)
        self.spawn_initial_outpost()

    def get_chunk_coords(self, x: int, y: int) -> Tuple[int, int, int, int]:
        cx = x // CHUNK_SIZE
        cy = y // CHUNK_SIZE
        tx = x % CHUNK_SIZE
        ty = y % CHUNK_SIZE
        return cx, cy, tx, ty

    def load_or_generate_chunk(self, cx: int, cy: int) -> List[List[Tile]]:
        if (cx, cy) in self.chunks:
            return self.chunks[(cx, cy)]

        grid = []
        for ty in range(CHUNK_SIZE):
            row = []
            for tx in range(CHUNK_SIZE):
                wx = cx * CHUNK_SIZE + tx
                wy = cy * CHUNK_SIZE + ty
                tile = Tile(wx, wy, self.seed)
                row.append(tile)
            grid.append(row)

        self.chunks[(cx, cy)] = grid
        return grid

    def get_tile(self, x: int, y: int) -> Tile:
        cx, cy, tx, ty = self.get_chunk_coords(x, y)
        chunk = self.load_or_generate_chunk(cx, cy)
        return chunk[ty][tx]

    def spawn_initial_outpost(self):
        """Initial settlement and discovered zone around (0, 0)."""
        center = self.get_tile(0, 0)
        center.biome = "eva_industrial"
        center.radiation = 8.0
        center.toxicity = 5.0
        center.fertility = 50.0
        center.rubble = False
        center.explored = True
        center.building = "bunker_hq"
        center.building_level = 1
        center.building_hp = 100

        # Explore 5x5 starting perimeter
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                t = self.get_tile(dx, dy)
                t.explored = True
                if (dx, dy) != (0, 0):
                    t.radiation = max(5.0, t.radiation - 30.0)

        # Build initial solar and water nearby
        t_solar = self.get_tile(1, 0)
        t_solar.building = "solar_collector"
        t_solar.rubble = False

        t_water = self.get_tile(0, 1)
        t_water.building = "water_purifier"
        t_water.rubble = False

    def get_viewport(self, min_x: int, min_y: int, width: int, height: int) -> List[Dict[str, Any]]:
        tiles = []
        for y in range(min_y, min_y + height):
            for x in range(min_x, min_x + width):
                t = self.get_tile(x, y)
                tiles.append(t.to_dict())
        return tiles

    def get_world_summary(self) -> Dict[str, Any]:
        total_explored = 0
        total_buildings = 0
        sum_rad = 0.0
        explored_tiles = []

        for chunk in self.chunks.values():
            for row in chunk:
                for tile in row:
                    if tile.explored:
                        total_explored += 1
                        sum_rad += tile.radiation
                        explored_tiles.append(tile)
                        if tile.building:
                            total_buildings += 1

        avg_rad = (sum_rad / total_explored) if total_explored > 0 else 0.0
        return {
            "seed": self.seed,
            "total_chunks_loaded": len(self.chunks),
            "total_explored_tiles": total_explored,
            "total_buildings": total_buildings,
            "average_radiation": round(avg_rad, 2),
        }
