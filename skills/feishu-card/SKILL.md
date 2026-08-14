---
name: feishu-card
version: 3.0.0
description: "飞书交互卡片（schema 2.0）：构建和发送卡片消息，含 @提及、流式思考态、原地更新、按钮/选择器交互。通过 lark-cli --as bot 发送，无需手动管理 token。"
metadata:
  requires:
    bins: ["lark-cli", "jq", "python3"]
---

# feishu-card（schema 2.0）

## 关键规则

- 所有卡片使用 **schema 2.0**，元素放在 `body.elements[]`，不是顶层 `elements[]`
- 发送卡片必须 `--as bot`，`--msg-type interactive`，`--content` 传 JSON 字符串
- 卡片内 @人 用 `<at id="ou_xxx">姓名</at>`（不是 `<at user_id>`）
- **JSON 2.0 按钮不再有 `action` 容器**，button 直接放进 `body.elements`，交互用 `behaviors` 数组
- 先发"思考中"卡片拿到 `message_id`，Claude 回答后 PATCH 原地更新，避免刷屏
- **`note` tag 在 schema 2.0 中已不支持**（报错 200861），备注改用 `div + lark_md`（`<font color=grey>备注文字</font>`）
- **构建卡片 JSON 必须用 Python heredoc 或写文件**，禁止用 `$(python3 -c "...")` ——内容含反引号或特殊字符时 bash 会报语法错误

---

## 顶层结构完整字段

```json
{
  "schema": "2.0",
  "config": {
    "streaming_mode": false,
    "enable_forward": true,
    "update_multi": true,
    "width_mode": "default"
  },
  "card_link": {
    "url": "https://...",
    "pc_url": "https://...",
    "ios_url": "https://...",
    "android_url": "https://..."
  },
  "header": { "...": "..." },
  "body": {
    "direction": "vertical",
    "padding": "0px",
    "elements": []
  }
}
```

### config 字段

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `streaming_mode` | bool | false | 流式更新态（思考中占位用） |
| `enable_forward` | bool | true | 允许转发卡片 |
| `update_multi` | bool | false | JSON 2.0 共享卡片模式（多人同步更新需设 true） |
| `width_mode` | string | default（600px）| `compact`（400px）/ `fill`（全宽响应）/ `default` |

---

## Header 字段

```json
{
  "header": {
    "title":    {"tag": "plain_text", "content": "标题"},
    "subtitle": {"tag": "plain_text", "content": "副标题（可选）"},
    "template": "blue",
    "icon": {
      "tag": "standard_icon",
      "token": "robot-outlined",
      "color": "blue"
    },
    "text_tag_list": [
      {"tag": "text_tag", "text": {"tag": "plain_text", "content": "New"}, "color": "blue"}
    ]
  }
}
```

**template 颜色**：`blue` / `wathet` / `turquoise` / `green` / `yellow` / `orange` / `red` / `carmine` / `violet` / `purple` / `indigo` / `grey`

---

## 飞书颜色枚举速查

所有支持颜色枚举的字段（`background_color`、`text_color`、`icon color` 等）均使用以下格式，**不能只写基础色名**（如 `"blue"` 单独使用在某些组件会报错），需带层级后缀：

| 色系 | 浅色（背景推荐） | 中色 | 深色（文字推荐） |
|------|----------------|------|----------------|
| 蓝 blue | `blue-50` `blue-100` `blue-200` | `blue-300`～`blue-500` | `blue-600`～`blue-900` |
| 水蓝 wathet | `wathet-50` `wathet-100` `wathet-200` | `wathet-300`～`wathet-500` | `wathet-600`～`wathet-900` |
| 青 turquoise | `turquoise-50` `turquoise-100` | `turquoise-300`～`turquoise-500` | `turquoise-600`～`turquoise-900` |
| 绿 green | `green-50` `green-100` `green-200` | `green-300`～`green-500` | `green-600`～`green-900` |
| 黄绿 lime | `lime-50` `lime-100` | `lime-300`～`lime-500` | `lime-600`～`lime-900` |
| 黄 yellow | `yellow-50` `yellow-100` | `yellow-300`～`yellow-500` | `yellow-600`～`yellow-900` |
| 橙 orange | `orange-50` `orange-100` | `orange-300`～`orange-500` | `orange-600`～`orange-900` |
| 红 red | `red-50` `red-100` | `red-300`～`red-500` | `red-600`～`red-900` |
| 粉红 carmine | `carmine-50` `carmine-100` | `carmine-300`～`carmine-500` | `carmine-600`～`carmine-900` |
| 紫 purple | `purple-50` `purple-100` | `purple-300`～`purple-500` | `purple-600`～`purple-900` |
| 蓝紫 violet | `violet-50` `violet-100` | `violet-300`～`violet-500` | `violet-600`～`violet-900` |
| 靛 indigo | `indigo-50` `indigo-100` | `indigo-300`～`indigo-500` | `indigo-600`～`indigo-900` |
| 灰 grey | `grey-00` `grey-50` `grey-100` | `grey-300`～`grey-500` | `grey-600`～`grey-1000` |
| 白 | `white` `bg-white` | — | — |

**常用浅色背景推荐**（collapsible_panel、column 背景等）：
```
blue-100    wathet-100    green-100    yellow-100
orange-100  red-100       purple-100   carmine-100
turquoise-100    violet-100    indigo-100    lime-100
```

---

## 组件速查表

| tag | 类型 | 说明 |
|-----|------|------|
| `div` | 内容 | 文本块（plain_text / lark_md），支持前缀 icon |
| `markdown` | 内容 | 纯 Markdown 文本（不支持 @，@用 div+lark_md） |
| `img` | 内容 | 图片 |
| `table` | 内容 | 数据表格（最多 5 个/卡片，不可嵌套） |
| `hr` | 布局 | 分割线 |
| `note` | 布局 | ❌ schema 2.0 已废弃，改用 `div + lark_md` + `<font color=grey>` |
| `column_set` | 容器 | 多列布局 |
| `collapsible_panel` | 容器 | 折叠面板 |
| `button` | 交互 | 按钮（JSON 2.0 直接放 elements，不用 action 容器） |
| `input` | 交互 | 文本输入框（须在 form 内使用） |
| `select_static` | 交互 | 静态下拉选择器 |

---

## div（文本块）

```json
{
  "tag": "div",
  "text": {
    "tag": "lark_md",
    "content": "**加粗** _斜体_ `代码`",
    "text_size": "normal",
    "text_color": "default",
    "text_align": "left",
    "lines": 3
  },
  "icon": {"tag": "standard_icon", "token": "robot-outlined", "color": "blue"}
}
```

`text.tag`：`plain_text`（纯文本）或 `lark_md`（Markdown + @）
`text_size`：`heading-0` / `heading` / `normal`（默认）/ `notation` / `x-small`
`text_align`：`left` / `center` / `right`

---

## img（图片）

```json
{
  "tag": "img",
  "img_key": "img_xxx",
  "alt": {"tag": "plain_text", "content": "悬停说明"},
  "title": {"tag": "plain_text", "content": "图片标题"},
  "scale_type": "crop_center",
  "size": "medium",
  "corner_radius": "4px",
  "preview": true
}
```

`scale_type`：`crop_center` / `crop_top` / `fit_horizontal`
`size`：`stretch`（全宽）/ `large` / `medium` / `small` / `tiny` / `"300px 200px"`（自定义）
> JSON 2.0 不支持 `stretch_without_padding`，全宽效果改用负 margin

---

## column_set（多列布局）

```json
{
  "tag": "column_set",
  "flex_mode": "bisect",
  "horizontal_spacing": "medium",
  "background_style": "default",
  "columns": [
    {
      "tag": "column",
      "width": "weighted",
      "weight": 1,
      "vertical_align": "top",
      "elements": [{"tag": "div", "text": {"tag": "plain_text", "content": "左列"}}]
    },
    {
      "tag": "column",
      "width": "weighted",
      "weight": 1,
      "elements": [{"tag": "div", "text": {"tag": "plain_text", "content": "右列"}}]
    }
  ]
}
```

`flex_mode`：`none`（按比例压缩）/ `stretch`（窄屏纵排）/ `flow`（自动换行）/ `bisect`（等宽两列）/ `trisect`（等宽三列）
`horizontal_spacing`：`small`(4px) / `medium`(8px) / `large`(12px) / `extra_large`(16px)
`column.width`：`auto` / `weighted`（配合 weight 1-5）/ `"200px"`

> 最大嵌套 5 层，列内不可放 form 容器和 table

---

## collapsible_panel（折叠面板）

```json
{
  "tag": "collapsible_panel",
  "expanded": false,
  "background_color": "default",
  "header": {
    "title": {"tag": "plain_text", "content": "点击展开"},
    "background_color": "grey",
    "icon": {"tag": "standard_icon", "token": "arrow-down-outlined"},
    "icon_expanded_angle": -180
  },
  "elements": [
    {"tag": "div", "text": {"tag": "plain_text", "content": "折叠内容"}}
  ]
}
```

---

## table（数据表格）

```json
{
  "tag": "table",
  "page_size": 5,
  "row_height": "low",
  "freeze_first_column": false,
  "header_style": {
    "text_align": "left",
    "text_size": "normal",
    "background_style": "grey",
    "bold": true
  },
  "columns": [
    {"name": "name", "display_name": "姓名", "data_type": "text", "width": "auto"},
    {"name": "status", "display_name": "状态", "data_type": "options", "width": "120px"},
    {"name": "count", "display_name": "数量", "data_type": "number",
     "format": {"precision": 0, "separator": true}},
    {"name": "ts", "display_name": "时间", "data_type": "date",
     "format": "YYYY/MM/DD HH:mm"}
  ],
  "rows": [
    {"name": "张三", "status": [{"name": "进行中", "color": "blue"}], "count": 42, "ts": 1700000000000}
  ]
}
```

`data_type`：`text` / `lark_md` / `markdown` / `options` / `number` / `persons` / `date`
`row_height`：`low` / `middle` / `high` / `auto` / `"48px"`（32-124px）
> 每张卡片最多 5 个 table，不可嵌套

---

## button（JSON 2.0）

```json
{
  "tag": "button",
  "text": {"tag": "plain_text", "content": "确认"},
  "type": "primary",
  "size": "medium",
  "width": "default",
  "disabled": false,
  "behaviors": [
    {
      "type": "callback",
      "value": {"action": "confirm", "data": "payload"}
    }
  ],
  "confirm": {
    "title": {"tag": "plain_text", "content": "二次确认"},
    "text":  {"tag": "plain_text", "content": "确认执行此操作？"}
  }
}
```

`type`：`default`（灰）/ `primary`（蓝）/ `danger`（红）/ `text` / `primary_text` / `danger_text` / `primary_filled` / `danger_filled` / `laser`
`size`：`tiny` / `small` / `medium` / `large`
`behaviors[].type`：`callback`（触发事件）/ `open_url`（跳转链接）

> **JSON 2.0 变化**：不再有 `action` 容器，button 直接放 `body.elements` 或 `column.elements`；交互用 `behaviors` 替代旧的 `value`

---

## input（文本输入）

```json
{
  "tag": "input",
  "name": "field_name",
  "placeholder": {"tag": "plain_text", "content": "请输入..."},
  "default_value": "",
  "input_type": "text",
  "max_length": 200,
  "required": false,
  "disabled": false,
  "label": {"tag": "plain_text", "content": "标签"},
  "label_position": "top",
  "width": "fill"
}
```

`input_type`：`text` / `multiline_text` / `password`
用户提交触发 `card.action.trigger` 事件，事件含 `input_value`

---

## @提及语法

| 消息类型 | @人语法 | @全体 |
|---------|---------|-------|
| 卡片 `interactive` lark_md | `<at id="ou_xxx">姓名</at>` | `<at id="all">所有人</at>` |
| 文本 `text` / `post` | `<at user_id="ou_xxx">姓名</at>` | `<at user_id="all"></at>` |

**卡片内 @mention 经验证可用的元素结构**（`div + lark_md`，不要用裸 `markdown` tag）：
```json
{
  "tag": "div",
  "text": {
    "tag": "lark_md",
    "content": "<at id=\"ou_xxx\">姓名</at> 消息内容"
  }
}
```

---

## Markdown 语法速查（lark_md / markdown tag 内）

### 文字样式
```
**加粗**    *斜体*    ~~删除线~~    `行内代码`
```

### 颜色文字
```
<font color=red>红色</font>
<font color=green>绿色</font>
<font color=grey>灰色</font>
<font color=blue>蓝色</font>
<font color=orange>橙色</font>
<font color=wathet>水蓝</font>
<font color=purple>紫色</font>
```
完整颜色：`red` / `green` / `grey` / `blue` / `orange` / `wathet` / `purple` / `yellow` / `turquoise` / `indigo` / `violet` / `lime`

### 标签 / 数字徽章
```
<text_tag color='red'>标签</text_tag>
<number_tag>99</number_tag>
```

### 本地化时间
```
<local_datetime millisecond='1700000000000' format_type='date_num'></local_datetime>
```
`format_type`：`date_num`（2023/11/15）/ `date_full`（2023年11月15日）/ `datetime`（含时分秒）

### 标题 / 列表 / 引用
```
# H1  ## H2  ### H3  #### H4  ##### H5  ###### H6

- 无序  1. 有序  > 引用
```

### 代码块
````
```python
print("hello")
```
````

### 图片（Markdown 内）
```
![悬停文字](img_xxx)
```

### 表格（最多 5 行数据）
```
| 列1 | 列2 |
|-----|-----|
| A   | B   |
```

### 链接
```
[文字](https://url)    [电话](tel://13800138000)
```

### 分割线 / 换行
```
---   或   <hr>
<br/>  或  两次回车（段落换行）
```

### Emoji

#### ⚠️ 严格规则

1. **只能使用[官方列表](https://open.feishu.cn/document/server-docs/im-v1/message-reaction/emojis-introduce)中的 key**，未收录的 key（如 `:WAITING:`、`:PROCESSING:`）会渲染成纯文本，禁止使用。
2. **key 大小写必须与官方完全一致**（如 `Fire` 不是 `FIRE`，`Trophy` 不是 `TROPHY`，`Shrug` 不是 `SHRUG`）。
3. **`<text_tag>` 内部不渲染 `:KEY:`**，须改用 Unicode emoji（如 `✅`）。
4. `:KEY:` 仅在 `lark_md` 普通文本区域生效。

#### 发版通知常用
```
:DONE:        :OK:           :THUMBSUP:     :APPLAUSE:
:PARTY:       :FIREWORKS:    :MUSCLE:       :THANKS:
:Trophy:      :Fire:         :Hundred:      :CheckMark:
```

#### 工作 & 状态
```
:LGTM:        :OnIt:         :OneSecond:    :Get:
:ERROR:        :CrossMark:    :Pin:          :Alarm:
:Loudspeaker: :OKR:          :Yes:          :No:
:HEADSET:     :Typing:       :MeMeMe:       :Sigh:
:Lemon:       :AWESOMEN:     :VRHeadset:    :YouAreTheBest:
:SALUTE:      :HIGHFIVE:     :FISTBUMP:     :FINGERHEART:
:WAVE:        :ThumbsDown:
```

#### 表情 - 正面
```
:SMILE:       :LAUGH:        :LOL:          :LOVE:
:WINK:        :PROUD:        :WITTY:        :JOYFUL:
:WOW:         :BLUSH:        :HUG:          :BeamingFace:
:Delighted:   :ThanksFace:   :SaluteFace:   :PRAISE:
:CLAP:        :JIAYI:        :FACEPALM:     :YEAH:
```

#### 表情 - 负面 / 搞怪
```
:CRY:         :SOB:          :ANGRY:        :SHOCKED:
:Shrug:       :THINKING:     :DIZZY:        :SLEEP:
:YAWN:        :SICK:         :SWEAT:        :EMBARRASSED:
:SKULL:       :RAINBOWPUKE:  :PUKE:         :ClownFace:
:ColdSweat:   :SMUG:         :SILENT:       :TERROR:
:PETRIFIED:   :BETRAYED:     :WRONGED:
```

#### 庆祝 & 节日
```
:PARTY:       :FIREWORKS:    :REDPACKET:    :FORTUNE:
:FIRECRACKER: :XmasTree:     :XmasHat:      :Snowman:
:Pumpkin:     :Mooncake:     :MoonRabbit:   :Partying:
:StickyRiceBalls:            :JubilantRabbit:  :LUCK:
:FullMoonFace: :GoGoGo:      :HappyDragon:
```

#### 物品 & 食物
```
:ROSE:        :HEART:        :BEER:         :CAKE:
:GIFT:        :BOMB:         :Fire:         :Trophy:
:Coffee:      :BubbleTea:    :Drumstick:    :Pepper:
:CUCUMBER:    :CANDIEDHAWS:  :Soccer:       :Basketball:
:Music:       :CLEAVER:      :EatingFood:   :LIPS:
```

#### 状态指示（勿频繁使用，仅状态场景）
```
:GeneralDoNotDisturb:        :GeneralInMeetingBusy:
:StatusReading:              :GeneralWorkFromHome:
:GeneralBusinessTrip:        :StatusInFlight:
:GeneralSun:                 :GeneralMoonRest:
:StatusFlashOfInspiration:   :Status_PrivateMessage:
:GeneralTravellingCar:       :StatusBus:
```

#### Unicode Emoji（标题、text_tag 内、header subtitle 中使用）
```
🎉 ✅ ❌ ⚠️ 🚀 📦 💬 ⏳ 🔔 📝 🛠️ 🔍 👋 🎯 💡 🌟
👥 📅 🤖 🏆 🔥 💯 📣 🎁 ☕ 🍺
```

> **推荐风格**：标题用 Unicode emoji 增强视觉，状态/反馈用飞书 `:DONE:` `:LGTM:` 等专属语法

---

## 发送 / 回复 / 更新

### 发送到群（新消息）
```bash
CARD=$(python3 -c "
import json
card = {
  'schema': '2.0',
  'header': {'title': {'tag': 'plain_text', 'content': '标题'}, 'template': 'blue'},
  'body': {'elements': [{'tag': 'markdown', 'content': '内容'}]}
}
print(json.dumps(card))
")
lark-cli im +messages-send \
  --chat-id oc_xxx \
  --msg-type interactive \
  --content "$CARD" \
  --as bot
```

### 回复指定消息（获取 message_id 供后续更新）
```bash
MSG_ID=$(lark-cli im +messages-reply \
  --message-id om_xxx \
  --msg-type interactive \
  --content "$CARD" \
  --as bot \
  --jq '.data.message_id')
```

### 回复到 thread（不出现在主聊天流）
```bash
lark-cli im +messages-reply \
  --message-id om_xxx \
  --msg-type interactive \
  --content "$CARD" \
  --reply-in-thread \
  --as bot
```

### 防重复发送（1小时内相同 key 只发一次）
```bash
lark-cli im +messages-send \
  --chat-id oc_xxx \
  --msg-type interactive \
  --content "$CARD" \
  --idempotency-key "deploy-654.0-notify" \
  --as bot
```

### 原地更新卡片（PATCH）
```bash
PAYLOAD=$(jq -n --argjson card "$CARD" '{"msg_type":"interactive","content":($card|tojson)}')
lark-cli api PATCH "/open-apis/im/v1/messages/${MSG_ID}" \
  --data "$PAYLOAD" \
  --as bot
```

---

## 卡片模板

### 思考中（流式态，先发占位）
```bash
make_thinking_card() {
  local name="$1" question="$2"
  jq -n --arg name "$name" --arg q "$question" '{
    schema:"2.0",
    header:{title:{tag:"plain_text",content:("💬 "+$name+" 问")},template:"grey"},
    config:{streaming_mode:true},
    body:{elements:[
      {tag:"markdown",content:("> "+$q)},
      {tag:"hr"},
      {tag:"markdown",content:"⏳ **思考中…**"}
    ]}
  }'
}
```

### 回答完成（更新思考中卡片）
```bash
make_reply_card() {
  local name="$1" question="$2" answer="$3" duration="$4"
  jq -n --arg name "$name" --arg q "$question" --arg ans "$answer" --arg dur "$duration" '{
    schema:"2.0",
    header:{title:{tag:"plain_text",content:("💬 "+$name+" 问")},template:"blue"},
    config:{streaming_mode:false},
    body:{elements:[
      {tag:"markdown",content:("> "+$q)},
      {tag:"hr"},
      {tag:"markdown",content:$ans},
      {tag:"hr"},
      {tag:"markdown",content:("✅ 耗时 **"+$dur+"**")}
    ]}
  }'
}
```

### 错误提示
```bash
make_error_card() {
  local msg="${1:-抱歉，我暂时无法回答，请稍后再试。}" hint="${2:-}"
  local content="$msg"
  [[ -n "$hint" ]] && content+="\\n\\n💡 _${hint}_"
  jq -n --arg content "$content" '{
    schema:"2.0",
    header:{title:{tag:"plain_text",content:"❌ 出错了"},template:"red"},
    config:{streaming_mode:false},
    body:{elements:[{tag:"markdown",content:$content}]}
  }'
}
```

### 成功通知
```bash
make_success_card() {
  jq -n --arg title "$1" --arg content "$2" '{
    schema:"2.0",
    header:{title:{tag:"plain_text",content:$title},template:"green"},
    config:{streaming_mode:false},
    body:{elements:[{tag:"markdown",content:$content}]}
  }'
}
```

### 权限不足
```bash
make_noperm_card() {
  jq -n '{
    schema:"2.0",
    header:{title:{tag:"plain_text",content:"⛔ 权限不足"},template:"red"},
    config:{streaming_mode:false},
    body:{elements:[{tag:"markdown",content:"抱歉，你没有使用该 Bot 的权限。"}]}
  }'
}
```

### 发版通知（含 @人）

布局：顶部三列信息栏（版本号/环境/状态）+ 版本负责人 + 活动负责人。
**图标一律用 Unicode emoji 写在 lark_md content 里，禁止用 `icon.token`**（token 名称不可靠，会静默消失）。

```bash
send_deploy_notify() {
  local chat_id="$1" version="$2" env="$3"
  shift 3
  # 剩余参数格式：open_id1 name1 open_id2 name2 ...
  local at_owners=""
  while [[ $# -ge 2 ]]; do
    at_owners+="<at id=\"$1\">$2</at>  "
    shift 2
  done

  local now; now=$(date '+%Y-%m-%d %H:%M')

  python3 /tmp/_deploy_card.py "$version" "$env" "$now" "$at_owners" > /tmp/_deploy_card.json
  lark-cli im +messages-send \
    --chat-id "$chat_id" \
    --msg-type interactive \
    --content "$(cat /tmp/_deploy_card.json)" \
    --as bot
}
```

`/tmp/_deploy_card.py`（构建脚本，避免 heredoc 内变量展开问题）：

```python
import json, sys
version, env, now, at_owners = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

card = {
    "schema": "2.0",
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": f"🚀 {version} · {env} 发版通知"},
        "template": "wathet",
        "subtitle": {"tag": "plain_text", "content": f"MLA · {env} · {now}"}
    },
    "body": {"elements": [
        {
            "tag": "column_set", "flex_mode": "trisect",
            "columns": [
                {"tag": "column", "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": f"<font color=grey>版本号</font>\n**{version}**"}}]},
                {"tag": "column", "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": f"<font color=grey>环境</font>\n<text_tag color='blue'>{env}</text_tag>"}}]},
                {"tag": "column", "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "<font color=grey>状态</font>\n<text_tag color='green'>:DONE: 已发好</text_tag>"}}]},
            ]
        },
        {"tag": "hr"},
        {"tag": "div", "text": {"tag": "lark_md",
            "content": '👥 **版本负责人知悉**\n<at id="ou_f4d8024b035c78431a9bfdfce82a4cfb">王同乐(Atlas)</at>  <at id="ou_0bf729df814255c9ba18191d077ecfb1">张超(Scott)</at>\n请知悉～'}},
        {"tag": "hr"},
        {"tag": "div", "text": {"tag": "lark_md",
            "content": f"📅 **活动配置请跟进**\n{at_owners}\n麻烦配置活动，辛苦了！:THUMBSUP:"}},
        {"tag": "hr"},
        {"tag": "div", "text": {"tag": "lark_md", "content": f"<font color=grey>:DONE: {version} · {env} · 由 lucky后端ai 自动发送</font>"}}
    ]}
}
print(json.dumps(card, ensure_ascii=False))
```

### 按钮确认（JSON 2.0）
```bash
jq -n '{
  schema:"2.0",
  header:{title:{tag:"plain_text",content:"请确认"},template:"orange"},
  body:{elements:[
    {tag:"markdown",content:"是否执行此操作？"},
    {tag:"button",
     text:{tag:"plain_text",content:"确认"},
     type:"primary",
     behaviors:[{type:"callback",value:{action:"confirm"}}]},
    {tag:"button",
     text:{tag:"plain_text",content:"取消"},
     type:"default",
     behaviors:[{type:"callback",value:{action:"cancel"}}]}
  ]}
}'
```

---

## 错误处理

```bash
result=$(lark-cli api PATCH "/open-apis/im/v1/messages/${MSG_ID}" \
  --data "$PAYLOAD" --as bot 2>/dev/null)
code=$(echo "$result" | jq -r '.code // 0')
if [[ "$code" != "0" ]]; then
  # PATCH 失败（消息过期/权限问题），降级为发新消息
  lark-cli im +messages-send --chat-id "$CHAT_ID" --msg-type interactive \
    --content "$CARD" --as bot
fi
```

常见错误码：
| code | 含义 | 处理 |
|------|------|------|
| 230002 | 没有操作权限 | 检查 bot 是否在群内 |
| 10012 | 消息不存在或已过期 | 降级发新消息 |
| 99991663 | token 过期 | 重新 `lark-cli auth login --as bot` |
