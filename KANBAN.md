# KANBAN: Evaline Games

## 📌 Backlog
- [ ] 3D / Canvas визуализация на WebGL / Three.js
- [ ] Турнирная таблица ELO рейтингов между LLM моделями
- [ ] Генерация новых правил и квестов через Evaline Consilium

## 📋 To Do
- [ ] `INTEGRATION_CONSILIUM.md`: Архитектура подключения консилиума к играм (консилиум как Гейм-мастер, арбитр, сценарист).
- [ ] `game_engine.py`: Ядро многоагентной игры в реальном времени (до 10-30 моделей одновременно).
- [ ] `cat_game.py` / `web_game.html`: Пошаговая/реалтайм игра "Коты и Мышь" с веб-интерфейсом и WebSocket/SSE.
- [ ] Подключение API консилиума (роли, память, база знаний Evaline).
- [ ] Git init & GitHub репозиторий `evaline-games`.

## 🔄 In Progress
- [x] Формирование структуры репозитория и KANBAN.

## 🔍 Testing & Verification
- [ ] Тестовый запуск матча с 10 бесплатными моделями.

## ✅ Done
- [x] Создана директория `/home/evabot/evaline-games`
- [x] Симулятор «LLM Soccer 5x5» (HTML5 Canvas 60 FPS, физика, сервер 8099)
- [x] Симулятор «Evaline Post-Apo Tycoon: Infinite Living Canvas» (`post_apo_tycoon`):
  - [x] Процедурный мультиоктавный генератор бесконечного мира (`world_matrix.py`)
  - [x] Симуляционный экономический движок цепочек ЭВА-производства (`simulation_engine.py`)
  - [x] Совет из 5 LLM моделей с вызовами через OpenRouter и эвристикой (`llm_governors.py`)
  - [x] Терминальный ANSI TrueColor радар (`terminal_tui.py`)
  - [x] Интерактивный 2D HTML5 Canvas веб-интерфейс без сторонних ассетов (`static/canvas_world.html`)
  - [x] Автоматический набор юнит-тестов из 13 тестов (`tests/test_post_apo_tycoon.py`) — 100% OK!
