---
name: ComfyUI-Autocomplete-Aaalice
description: 融入 ComfyUI 的本地优先标签创作助手
colors:
  primary: "#5b8cff"
  primary-hover: "#75a0ff"
  surface-popup: "var(--comfy-input-bg)"
  surface-dialog: "#171717"
  surface-raised: "#1e1e1e"
  text-primary: "var(--input-text)"
  text-high: "rgb(255 255 255 / 94%)"
  text-muted: "rgb(255 255 255 / 56%)"
  border-soft: "rgb(255 255 255 / 9%)"
  success: "#4ade80"
  warning: "#facc15"
  danger: "#f87171"
typography:
  title:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "normal"
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.73rem"
    fontWeight: 550
    lineHeight: 1.4
    letterSpacing: "0.01em"
  mono:
    fontFamily: "var(--font-mono, monospace)"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.35
    letterSpacing: "normal"
rounded:
  sm: "4px"
  control: "8px"
  nav: "9px"
  card: "10px"
  panel: "12px"
  dialog: "16px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "6px"
  md: "8px"
  field: "10px"
  card: "12px"
  section: "16px"
  dialog: "24px"
components:
  popup:
    backgroundColor: "{colors.surface-popup}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.control}"
    width: "min(42rem, calc(100vw - 24px))"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "34px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
  button-quiet:
    backgroundColor: "rgb(255 255 255 / 5%)"
    textColor: "rgb(255 255 255 / 78%)"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "34px"
  input:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "9px 11px"
    height: "38px"
  origin-badge:
    backgroundColor: "rgb(255 255 255 / 4%)"
    textColor: "{colors.text-muted}"
    rounded: "3px"
    padding: "0 3px"
    height: "12px"
---

# Design System: ComfyUI-Autocomplete-Aaalice

## Overview

**Creative North Star: "ComfyUI 原生伴侣"**

界面应像 ComfyUI 自身能力的自然延伸，而不是覆盖在宿主上的独立产品。它保持克制、精密、友好、高效与轻盈：平时退居内容之后，在候选、状态或操作真正需要用户注意时才提高对比度。

“安静的创作助手”约束交互噪声，“精密标签工作台”约束高密度信息组织。补全与共现弹层优先快速扫描和键盘操作；在线设置允许更舒展的分区，但仍通过柔和表面层级而非厚重边框建立结构。

**Key Characteristics:**
- 跟随 ComfyUI 主题与宿主 token，而不是建立平行配色系统。
- 高密度列表保持固定节奏、清晰列对齐和稳定选择反馈。
- 圆角无边框表面以轻微内侧高光和柔和环境阴影表达层级。
- 蓝色只承担选择、焦点与主要操作，状态颜色只表达真实状态。
- 动效短促且服务于状态变化，不改变组件尺寸或布局。

## Colors

色彩以宿主主题为底，“工作台蓝”负责聚焦和主要操作，“深墨台面 / 石墨浮层”负责在线设置的暗色层级；分类色和状态色只承担语义，不作为装饰铺色。

### Primary
- **工作台蓝：** 用于选中强调线、焦点环、开关开启态、进度和主要操作；面积保持克制。
- **工作台蓝悬浮态：** 仅用于可交互主操作的 hover，不替代基础强调色。

### Secondary
- **状态绿：** 只表示 ready、success 或完成。
- **状态黄：** 只表示 waiting、checking、downloading 等进行中状态。
- **状态红：** 只表示 error、danger 或破坏性操作。

### Neutral
- **宿主输入表面：** 补全与共现面板直接继承 ComfyUI 输入背景，使弹层融入当前主题。
- **深墨台面：** 在线设置 Dialog 的主背景，承载导航、内容和底部操作区。
- **石墨浮层：** 输入框、状态网格、开关卡片和信息卡的轻度抬升表面。
- **高亮正文：** 标题和关键值使用高透明度白色；普通信息跟随宿主正文色。
- **柔和说明文字：** 帮助、次要状态与元数据降低对比度，但不能承载关键操作结果。
- **呼吸分隔：** 低透明度白色仅用于内侧分隔和边缘高光，不形成显眼描边。

### Named Rules

**The Host-First Rule.** 补全主界面优先继承 ComfyUI 的背景、正文、说明、边界和 hover token；只有产品特有的分类与状态语义使用局部颜色。

**The One Accent Rule.** 工作台蓝只用于选择、焦点、进度和主要操作；同一区域不引入第二套竞争性强调色。

**The Semantic Color Rule.** 绿、黄、红必须对应真实状态，不作为普通装饰或分类背景。

## Typography

**Display Font:** 不使用独立展示字体；标题沿用 Inter 与系统无衬线栈。
**Body Font:** Inter（回退至 ui-sans-serif、system-ui、sans-serif）
**Label/Mono Font:** 标签使用 Inter；查询文本和标签别名使用宿主等宽字体。

**Character:** 字体服务于高密度扫描，使用紧凑字号、清晰字重和有限层级。标题有足够权重建立分区，正文和元数据逐级降低对比度，而不是依赖夸张字号。

### Hierarchy
- **Title：** 仅用于在线设置 Dialog 主标题；紧凑、明确，不做营销式展示。
- **Headline：** 分区标题使用略高于正文的字号和中等偏强字重，承担页面内导航。
- **Body：** 用于说明、字段值和操作文案，保持适合设置面板的紧凑行高。
- **Label：** 用于字段标签、按钮和状态，短、直接、可快速扫描。
- **Mono：** 仅用于用户查询、标签别名、模型或 API 等需要保持字符结构的内容。

### Named Rules

**The Scan-First Rule.** 列表与设置界面的字号层级必须帮助用户从标题到标签再到元数据快速扫读，不能用大字号牺牲有效信息密度。

**The Mono-With-Purpose Rule.** 等宽字体只表达查询、标签和机器可读值，不用于普通说明文案。

## Layout

补全与共现面板是最大宽度 42rem 的高密度纵向弹层：34px Header、32px 候选行和 28px Footer 形成稳定节奏。列表以 subgrid 对齐标签、Wiki、别名、指标与来源；在 34rem 和 23rem 容器阈值逐步压缩间距、隐藏低优先级提示和 Wiki 列，而不截断主要标签与指标。

在线设置 Dialog 最大宽度 900px，桌面采用 190px 导航与弹性内容区的双栏结构。Section 使用 18px × 24px 内边距，卡片和字段以 8–16px 间距组织；620px 以下切换为纵向结构、横向滚动导航和单列网格，并将视口边距收紧至 8px。

**The Content-Preservation Rule.** 响应式收缩先压缩 gap、padding 和低优先级辅助信息，不能通过横向溢出、遮挡或缩小主要内容来维持桌面结构。

**The Stable-Dimensions Rule.** hover、focus、loading 和 selected 状态不得改变边框宽度、组件尺寸、列表宽度或列结构。

## Elevation & Depth

系统采用柔和环境阴影与轻微内侧高光的分层方式。弹层和 Dialog 使用较宽、低锐度的外阴影从复杂画布中分离；卡片、字段和按钮只使用浅抬升，不通过厚边框切割。在线设置允许比补全弹层更明显的层级，但所有阴影仍保持暗色、低噪声和功能性。

### Shadow Vocabulary
- **Popup Ambient：** 顶部内高光叠加中等范围环境阴影，用于补全与共现弹层。
- **Dialog Ambient：** 内高光、近距离柔光与大范围深阴影叠加，用于模态 Dialog 和 backdrop 分离。
- **Raised Surface：** 小范围低透明度阴影，用于状态网格、字典卡、Toggle 和字段。
- **Focus Lift：** 2px 工作台蓝焦点环叠加轻微外阴影，只在键盘焦点或字段编辑时出现。

### Named Rules

**The Borderless Layer Rule.** 面板、卡片、输入框和按钮默认无高对比度边框；优先用背景明度、间距、内侧高光和柔和阴影建立层级。

**The Ambient-Only Rule.** 阴影用于分离表面和反馈状态，不制造厚重黑边、强光晕或悬浮卡片墙。

## Shapes

形状语言从紧凑控件到大容器逐级放松：微型徽章和图标按钮使用 3–4px 圆角，常规按钮与输入框使用 8px，导航和紧凑卡片使用 9–10px，较完整卡片使用 12px，Dialog 使用 16px。Switch、进度条和状态胶囊使用完整 pill 圆角。

边缘默认无描边；只有语义消息、徽章或必须明确边界的状态使用低对比度线。圆角变化表达组件尺度，而不是任意装饰。

**The Scale-Follows-Radius Rule.** 组件越大，圆角可越宽；同一层级的同类控件必须保持一致圆角。

## Components

### Popup Shell
- **Character:** 紧凑、主题自适应、始终贴近当前输入上下文。
- **Shape:** 8px 圆角，无外边框。
- **Background:** 继承宿主输入表面和正文色。
- **Depth:** 顶部内高光与柔和环境阴影。
- **Behavior:** 位置受视口约束；Header、列表和 Footer 保持固定信息层级。

### Candidate Rows
- **Character:** 像精密标签表格，而不是宽松卡片列表。
- **Layout:** 32px 固定行高，subgrid 对齐标签、辅助操作、别名、指标和来源。
- **Selected:** 柔和蓝色混合背景与左侧 3px 强调线同时出现。
- **Hover:** 仅未选中项使用宿主 hover 背景。
- **Disabled / Existing:** 降低文字对比度，不移除必要内容。

### Origin Badges
- **Shape:** 3px 圆角、12px 高度的微型文字徽章。
- **Style:** 继承当前语义色，以低透明度边缘和背景保持低调。
- **Hover:** 只提高边缘、背景和文字可见度，不放大尺寸。

### Header, Footer & Icon Buttons
- **Shape:** 24px 方形点击区域，4px 圆角，透明默认背景。
- **Hover:** 使用正文色约 10% 的背景并提高图标对比度。
- **Focus:** 清晰的 2px 工作台蓝 outline，不改变布局。
- **Content:** Header 只保留查询上下文、数量和关闭；Footer 只保留数据状态与设置入口。

### Online Navigation
- **Shape:** 42px 最小高度、9px 圆角的整行 Tab。
- **Default:** 透明背景与柔和说明文字。
- **Hover / Active:** hover 轻微提亮；active 使用低透明度蓝色表面和 3px 强调线。
- **Responsive:** 桌面强调线位于左侧，移动端移至底部。

### Inputs / Fields
- **Style:** 石墨浮层、8px 圆角、无边框、轻微内高光和浅阴影。
- **Focus:** 2px 工作台蓝光环与略增强的环境阴影。
- **Sizing:** input/select 最小高度 38px，textarea 保持可垂直调整。
- **Secret Field:** 右侧图标按钮嵌入同一表面，不额外扩大字段。

### Toggles
- **Container:** 使用 10px 圆角浮层卡片承载标题、说明和 Switch。
- **Switch:** 38px × 22px pill 轨道，14px 圆形滑块。
- **Checked:** 工作台蓝轨道与白色滑块；focus 使用外置蓝色 outline。
- **Hover:** 仅轻微提高表面亮度和阴影，不改变尺寸。

### Buttons
- **Shape:** 34px 最小高度、8px 圆角、水平内边距 12px。
- **Primary:** 工作台蓝背景、白色文字和柔和蓝色环境阴影。
- **Quiet:** 低透明度白色表面与柔和文字，hover 时提高背景和文字对比度。
- **Danger:** 默认透明，仅以红色文字提示风险；hover 才显示淡红表面。
- **Disabled / Busy:** disabled 降低透明度；异步执行同时使用 disabled、`aria-busy` 和可见文字反馈。

### Status Cards & Messages
- **Status Card:** 两列紧凑网格，使用文本与彩色圆点双重表达 ready、waiting 和 error。
- **Message:** 8px 圆角和低对比度边缘；success/error 同时改变边缘、背景和文字色。
- **Accessibility:** 状态不能只依赖颜色，关键结果必须保留可读文本。

## Do's and Don'ts

### Do:
- **Do** 让补全弹层继承 ComfyUI 主题 token，并把局部固定色限制在在线设置与明确语义状态。
- **Do** 使用 4、6、8、12、16、24px 的既有节奏组织紧凑控件、卡片和 Section。
- **Do** 为 hover、focus、selected、disabled、busy、success 和 error 提供清晰且不抖动的反馈。
- **Do** 在窄空间优先隐藏低优先级提示，保留标签、翻译、指标和来源等主要内容。
- **Do** 保持键盘焦点可见，并让状态文字、ARIA 与视觉反馈表达同一事实。

### Don't:
- **Don't** 使用厚重边框或高对比度分割线切割面板、卡片、输入框和按钮。
- **Don't** 用大面积高饱和色铺满普通表面；工作台蓝和状态色必须保持稀缺且有语义。
- **Don't** 添加无功能目的的装饰、光晕、持续动画或布局位移。
- **Don't** 为追求留白而降低候选列表的信息密度，或让面板遮挡、溢出和压缩主要内容。
- **Don't** 在同一功能中建立独立于 ComfyUI 的第二套字体、基础背景或交互语言。
