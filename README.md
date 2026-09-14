# evaline-games — LLM-игры для 10 моделей

Терминальные и пошаговые многопользовательские игры, в которых 10 бесплатных LLM-моделей соревнуются, обучаются на своих ошибках и прокачивают когнитивные навыки в реальном времени.

## Быстрый старт

```bash
# Футбольный матч 10 LLM (сервер + физика)
python3 soccer/server.py

# Post-Apo Tycoon — бесконечный симулятор (TUI + 2D Canvas)
cd post_apo_tycoon && ./run.sh

# Коты и Мышь на складе Evaline
python3 cat_game_engine.py
```

## Основные функции

- **Soccer** — футбольный движок для 10 моделей (`soccer/`: сервер, физика, web-просмотр `web_soccer.html`)
- **Post-Apo Tycoon** — бесконечный процедурный мир (шум по чанкам), Совет из 5 LLM-министерств, нулевая сборка ассетов (Canvas 2D)
- **Cat game engine** — «Коты и Мышь» на складе Evaline, real-time
- **Концепты** — «Мафия/Шпион», «Складская биржа», «Warehouse Battle Royale» и др. (`GAME_CONCEPTS.md`)
- **Интеграция с Консилиумом** — консилиум выступает гейм-мастером и разбирает матчи моделей (`INTEGRATION_CONSILIUM.md`)
- Канбан задач (`KANBAN.md`)

## Связанные репозитории

- [evaline-agents](https://github.com/evaline-online/evaline-agents) — workspace агентов (сборка/запуск LLM-агентов)
- [business-tier-api](https://github.com/evaline-online/business-tier-api) — API-доступ к моделям

## Статус

Активная разработка. Движок Post-Apo Tycoon автономен (когнитивные эвристики при отсутствии API-ключа).
