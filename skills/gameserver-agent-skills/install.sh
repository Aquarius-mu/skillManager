#!/usr/bin/env bash
# Install gameserver-agent-skills by symlinking each skill into ~/.agents/skills/
set -e

PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.agents/skills"

SKILLS=(guide brainstorm plan implement review debug grill architect prototype to-prd to-issues triage zoom-out handoff caveman)

mkdir -p "$SKILLS_DIR"

for skill in "${SKILLS[@]}"; do
  target="$SKILLS_DIR/$skill"
  if [ -L "$target" ] || [ -d "$target" ]; then
    rm -rf "$target"
  fi
  ln -s "$PACK_DIR/$skill" "$target"
  echo "  ✓ $skill"
done

echo ""
echo "gameserver-agent-skills installed to $SKILLS_DIR"
echo "Restart Claude Code to pick up the new skills."
