#!/usr/bin/env bash
# run.sh — UX Maturity Analysis launcher
#
# Automatically runs inside a persistent tmux session so the analysis
# survives VS Code disconnects, SSH drops, or closing your laptop.
# All arguments are forwarded to cli.py.
#
# Usage:
#   ./run.sh                                    # interactive guided menu
#   ./run.sh --reanalyze <audit_folder>         # non-interactive reanalyse
#   ./run.sh --reanalyze <audit_folder> --force
#   ./run.sh --reanalyze <audit_folder> --force-observe
#   ./run.sh --deploy                           # non-interactive deploy
#   ./run.sh --deploy --draft
#   ./run.sh --deploy --verbose                 # non-interactive deploy with full logs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
SESSION_NAME="analysis"
LOG_DIR="$SCRIPT_DIR/output/logs"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Run: cd $SCRIPT_DIR && uv sync"
    exit 1
fi

CMD="$VENV_PYTHON '$SCRIPT_DIR/cli.py' $*"
LOG_FILE="$LOG_DIR/${SESSION_NAME}_$(date +%Y%m%d_%H%M%S).log"

# If already in tmux or screen, run directly
if [ -n "${TMUX:-}" ] || [ -n "${STY:-}" ]; then
    eval "$CMD"
    exit $?
fi

echo ""
echo "  Starting inside tmux session \"$SESSION_NAME\" so the run survives"
echo "  any connection drop. Detach with: Ctrl+B then D"
echo "  Reattach with: tmux attach -t $SESSION_NAME"
echo "  Logs will be written to: $LOG_FILE"
echo ""

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    PANE_PID=$(tmux list-panes -t "$SESSION_NAME" -F "#{pane_pid}" 2>/dev/null | head -1)
    CHILDREN=$(pgrep -P "$PANE_PID" 2>/dev/null | wc -l)
    if [ "$CHILDREN" -gt 0 ]; then
        echo "  Warning: session \"$SESSION_NAME\" already has a process running."
        echo "  Attaching to the existing session instead."
        echo ""
        tmux attach -t "$SESSION_NAME"
        exit 0
    fi
    tmux set-option -t "$SESSION_NAME" mouse on >/dev/null 2>&1 || true
    tmux set-window-option -t "$SESSION_NAME" history-limit 200000 >/dev/null 2>&1 || true
    tmux pipe-pane -t "$SESSION_NAME" >/dev/null 2>&1 || true
    tmux pipe-pane -t "$SESSION_NAME" "cat >> '$LOG_FILE'"
    tmux send-keys -t "$SESSION_NAME" "$CMD" Enter
else
    tmux new-session -d -s "$SESSION_NAME" -x 220 -y 50
    tmux set-option -t "$SESSION_NAME" mouse on >/dev/null 2>&1 || true
    tmux set-window-option -t "$SESSION_NAME" history-limit 200000 >/dev/null 2>&1 || true
    tmux pipe-pane -t "$SESSION_NAME" "cat >> '$LOG_FILE'"
    tmux send-keys -t "$SESSION_NAME" "$CMD" Enter
fi

tmux attach -t "$SESSION_NAME"
