#!/usr/bin/env bash
# ==============================================================================
# Evaline Post-Apo Tycoon — Runner Script
# Supports:
#   ./run.sh web [port]   - Run Web Server & 2D Canvas (default port: 8098)
#   ./run.sh tui          - Run Terminal TUI & ASCII Radar
#   ./run.sh test         - Run Automated Unit Test Suite
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

MODE="${1:-web}"
PORT="${2:-8098}"

case "$MODE" in
  web)
    echo "[+] Запуск Web Canvas сервера на порту $PORT..."
    echo "[+] Откройте в браузере: http://localhost:$PORT"
    python3 web_server.py "$PORT"
    ;;
  tui)
    echo "[+] Запуск терминального интерфейса TUI..."
    python3 terminal_tui.py --ticks 10 --auto
    ;;
  test)
    echo "[+] Запуск автоматических тестов..."
    python3 -m unittest discover -s tests -p "test_*.py" -v
    ;;
  *)
    echo "Использование: $0 {web|tui|test} [port]"
    exit 1
    ;;
esac
