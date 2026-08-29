---
name: xhs-zine-cover
description: >
  小红书推文封面生成器（极简独立杂志 Zine 风格）。用纯代码绘制 3:4 竖版封面：
  浅灰蓝旧纸背景、纸张纤维、扫描颗粒、撕纸边缘、Risograph 印刷颗粒、轻微套色偏移。
  默认用于「模型大评测」系列（大标题 + 本期模型 + 六张竖排撕边纸条模型名），
  文字 100% 拼写准确、风格永远统一。当用户提到 模型大评测封面、小红书封面、
  zine 风格封面、推文配图、系列封面 时使用。
metadata:
  type: project
---

# 小红书 Zine 封面生成器

纯 Python/Pillow 代码绘制，不用 AI 生图——**文字拼写 100% 准确、配色版式永远一致**，适合系列栏目。

## 用法

```powershell
$env:PYTHONUTF8 = '1'
Start-Process -FilePath 'python' `
  -ArgumentList '<skill-dir>\scripts\make_cover.py','--featured','<本期模型>','--models','<模型1>,<模型2>,<模型3>,<模型4>,<模型5>,<模型6>','--issue','01','--days','3','--out','cover.png' `
  -Wait -NoNewWindow -RedirectStandardOutput out.txt -RedirectStandardError err.txt
```

参数：
- `--featured`：本期被评测模型完整名称（必须包含在 --models 六个名字里）
- `--models`：六张纸条的模型名，英文逗号分隔，拼写必须准确
- `--issue`：系列期号（01、02…），期号状态存在 `.tmpfiles\ai-hourly-pulse\sources.json` 的 `series_issue` 字段
- `--days`：生产实测天数
- `--title`：系列大标题，默认「模型大评测」
- `--out`：输出路径（3:4，1620x2160）

## 风格规范（改任何一条都会破坏系列统一性）

- 3:4 竖版；背景浅灰蓝 `#D1DCE2` 旧纸（纤维 + 扫描颗粒 + 复印柔化 + Riso 颗粒）
- 左上大号深海军蓝黑 `#182A3A` 凸版大标题，带轻微套色偏移
- 阅读顺序：大标题 → 本期模型 → 六张纸条
- 六张竖向撕边纸条：本期模型纸条深灰蓝 `#214E78`，面积比其他大 ~20%、向前向上错位；其余暖灰白/浅灰蓝交替
- 留白 58%~65%，标题和本期模型在小红书缩略图里必须一眼可见
- 打字机字体（Consolas）：`MODEL REVIEW / {期号}`、`生产实测 {天数} 天`
- **禁止**：人物、机器人、风景、任何 Logo、AI 科技图标、卡通、3D、霓虹、渐变、玻璃质感、商业光泽、复杂图表、额外文案、水印

## 发送

封面生成后发到飞书群（本地路径）：

```
lark-cli im +messages-send --chat-id oc_xxx --as bot --image <相对路径>
```

注意：发图片必须用 **--as bot**（user 身份缺 im:resource 上传权限，实测报错 99991679）。

注意 `--image` 只接受 cwd 相对路径或 URL，不接受绝对路径。**lark-cli 的 cwd 实测为 `<lark-workdir>\`**：
发图前先把封面复制到 `<lark-workdir>\.tmpfiles\ai-hourly-pulse\covers\<文件名>`，再用 `.tmpfiles\ai-hourly-pulse\covers\<文件名>` 相对路径发送。
另：Start-Process 传参会切碎带空格的值，所有含空格的参数值必须整体加英文双引号。

## 依赖

Pillow（已装）。缺失时：`python -m pip install pillow`。
