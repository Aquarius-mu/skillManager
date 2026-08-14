#!/usr/bin/env bash
#
# skillManager 技能安装脚本
#
# 用法:
#   ./install.sh                          # 列出所有可安装的技能
#   ./install.sh <技能名> [目标目录]        # 把技能复制到目标目录
#
# 目标目录默认按常见平台自动推断:
#   - ~/.hermes/skills   (Hermes Agent)
#   - ~/.claude/skills   (Claude Code)
#   若都不存在，回退到 ~/.hermes/skills

set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/skills" && pwd)"

list_skills() {
  echo "可安装的技能："
  local name
  for d in "$SKILLS_DIR"/*/; do
    name="$(basename "$d")"
    if [[ -f "$d/SKILL.md" ]]; then
      echo "  - $name"
    fi
  done
}

detect_target() {
  if [[ -d "$HOME/.hermes/skills" ]]; then
    echo "$HOME/.hermes/skills"
  elif [[ -d "$HOME/.claude/skills" ]]; then
    echo "$HOME/.claude/skills"
  else
    echo "$HOME/.hermes/skills"
  fi
}

if [[ $# -eq 0 ]]; then
  list_skills
  echo
  echo "用法: ./install.sh <技能名> [目标目录]"
  exit 0
fi

SKILL_NAME="$1"
TARGET="${2:-$(detect_target)}"

SRC="$SKILLS_DIR/$SKILL_NAME"
if [[ ! -d "$SRC" || ! -f "$SRC/SKILL.md" ]]; then
  echo "❌ 找不到技能: $SKILL_NAME" >&2
  list_skills
  exit 1
fi

mkdir -p "$TARGET"
rm -rf "$TARGET/$SKILL_NAME"
cp -r "$SRC" "$TARGET/$SKILL_NAME"

echo "✅ 已安装 $SKILL_NAME -> $TARGET/$SKILL_NAME"
