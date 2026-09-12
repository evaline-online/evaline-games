#!/usr/bin/env python3
"""
Automated Test Suite for Evaline Post-Apo Tycoon.
Tests procedural world matrix, deterministic noise, simulation engine,
LLM council deliberation, and web server endpoints.
"""

import os
import sys
import unittest
import json
from io import BytesIO

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from world_matrix import WorldMatrix, Tile, BUILDINGS, BIOMES, CHUNK_SIZE
from simulation_engine import SimulationEngine
from llm_governors import LLMGovernorsCouncil, MINISTRIES


class TestWorldMatrix(unittest.TestCase):
    def setUp(self):
        self.world = WorldMatrix(seed=42)

    def test_chunk_determinism(self):
        """Verify that identical seed generates identical biomes and parameters."""
        w2 = WorldMatrix(seed=42)
        tile1 = self.world.get_tile(10, 15)
        tile2 = w2.get_tile(10, 15)

        self.assertEqual(tile1.biome, tile2.biome)
        self.assertEqual(tile1.elevation, tile2.elevation)
        self.assertEqual(tile1.moisture, tile2.moisture)
        self.assertAlmostEqual(tile1.radiation, tile2.radiation, places=2)

    def test_initial_outpost(self):
        """Verify HQ at (0, 0) is properly initialized."""
        hq = self.world.get_tile(0, 0)
        self.assertTrue(hq.explored)
        self.assertEqual(hq.building, "bunker_hq")
        self.assertEqual(hq.biome, "eva_industrial")
        self.assertFalse(hq.rubble)

    def test_viewport_retrieval(self):
        """Verify viewport window extraction."""
        vp = self.world.get_viewport(-5, -5, 10, 10)
        self.assertEqual(len(vp), 100)
        coords = [(t["x"], t["y"]) for t in vp]
        self.assertIn((0, 0), coords)
        self.assertIn((-5, -5), coords)


class TestSimulationEngine(unittest.TestCase):
    def setUp(self):
        self.world = WorldMatrix(seed=42)
        self.sim = SimulationEngine(self.world)

    def test_initial_resources(self):
        self.assertGreater(self.sim.resources["energy"], 0)
        self.assertGreater(self.sim.resources["water"], 0)
        self.assertGreater(self.sim.resources["scrap"], 0)
        self.assertEqual(self.sim.resources["population"], 12)

    def test_step_tick_advances_and_produces(self):
        init_energy = self.sim.resources["energy"]
        self.sim.step_tick()
        self.assertEqual(self.sim.tick_count, 1)
        # Solar collector at (1, 0) should produce energy
        self.assertGreaterEqual(self.sim.resources["energy"], init_energy - 5)

    def test_build_and_upkeep_decontamination(self):
        # Target a clean explored tile
        t = self.world.get_tile(-1, 0)
        t.rubble = False
        t.building = None
        init_rad = t.radiation

        # Build decontaminator
        self.sim.resources["scrap"] = 200.0
        self.sim.resources["eva_polymer"] = 100.0
        success = self.sim.build_facility(-1, 0, "decontaminator")
        self.assertTrue(success)
        self.assertEqual(t.building, "decontaminator")

        # Run 3 ticks
        for _ in range(3):
            self.sim.step_tick()

        # Neighbor radiation should decay
        neighbor = self.world.get_tile(-1, 1)
        self.assertLessEqual(neighbor.radiation, 95.0)


class TestLLMGovernors(unittest.TestCase):
    def setUp(self):
        self.world = WorldMatrix(seed=42)
        self.sim = SimulationEngine(self.world)
        self.council = LLMGovernorsCouncil(self.world, self.sim)

    def test_ministries_configuration(self):
        self.assertEqual(len(MINISTRIES), 5)
        self.assertIn("Minister_Ecology", MINISTRIES)
        self.assertIn("Chief_Engineer", MINISTRIES)

    def test_heuristic_action_fallback(self):
        """Verify heuristic decision generation without external network requirement."""
        dec = self.council.heuristic_action("Minister_Ecology")
        self.assertIn("action", dec)
        self.assertIn("target", dec)
        self.assertIn("rationale", dec)

    def test_step_council_turn(self):
        results = self.council.step_council_turn()
        self.assertEqual(len(results), 5)
        for r in results:
            self.assertIn(r["action"], ["build", "clear", "explore", "upgrade", "pass"])
            self.assertTrue(len(r["target"]) == 2)


class TestWebServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from web_server import run_server
        import threading
        import time
        from http.server import HTTPServer
        from web_server import PostApoHandler

        cls.server = HTTPServer(("127.0.0.1", 8097), PostApoHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_root_html(self):
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8097/") as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("Evaline Post-Apo Tycoon", content)
            self.assertIn("worldCanvas", content)

    def test_api_state(self):
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8097/api/state") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("sim", data)
            self.assertIn("ministries", data)

    def test_api_viewport(self):
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8097/api/viewport?min_x=-2&min_y=-2&w=4&h=4") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(len(data["tiles"]), 16)

    def test_api_tick(self):
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8097/api/tick", data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "ok")
            self.assertGreaterEqual(len(data["decisions"]), 1)


if __name__ == "__main__":
    unittest.main()
