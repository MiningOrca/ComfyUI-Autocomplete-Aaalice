# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

主要面向在 ComfyUI 中编写图像生成提示词、需要快速查找和组织 Danbooru、LoRA、Embedding、Wildcard 等标签的用户。产品同时服务使用 Classic、Nodes 2.0、子图提升输入和受支持第三方输入框的工作流。

## Product Purpose

为 ComfyUI 文本输入框提供标签补全、共现标签探索、翻译和提示词格式化，降低查找、输入、理解和整理标签的成本。成功意味着用户无需离开当前提示词输入流程，也能稳定、快速地获得可插入的相关标签，并在本地数据尚未完成索引或在线服务不可用时继续工作。

## Positioning

以本地数据为主、在线数据为补充：优先立即展示稳定的本地候选，再异步合入 Danbooru、中文词典和 LoRA Manager 等结果，不因大型索引或在线配置阻塞 ComfyUI 启动和本地补全。项目是 `newtextdoc1111/ComfyUI-Autocomplete-Plus` 的持续维护分支，重点保持对新版 ComfyUI 输入载体和实际工作流的兼容。

## Operating Context

- 作为 ComfyUI custom node 安装，Python 模块注册 API 与前端资源，主要交互发生在 ComfyUI 浏览器界面的文本输入框内。
- 用户输入标签或中文名称后查看候选，通过鼠标、方向键、Enter 或 Tab 插入；可继续探索共现标签、打开 Wiki 或格式化提示词。
- 数据来自内置或自定义 CSV、可选 e621 数据、LoRA Manager、本地中文词典及按需启用的在线服务。
- 设置入口位于 ComfyUI 的 `Autocomplete Plus` 分类中。

## Capabilities and Constraints

- 支持标签与别名补全、已存在标签去重提示、分类/引用量/来源展示、中文反查英文 Tag、共现标签、Wiki 跳转、翻译和自动格式化。
- 支持 Danbooru、本地 LoRA、Embedding、Wildcard，以及用户手动提供的 e621 标签数据；当前不支持 e621 共现标签。
- 支持英文、简体中文、繁体中文和日文界面。简体与繁体中文可使用 ffdkj 本地汉化数据库，简体中文额外支持中文输入反查英文 Tag。
- `setup()` 必须同步返回；CSV、模型索引、翻译目录和在线服务必须在后台初始化，并保留分阶段可用、失败可重试和并发请求去重。
- 本地补全不能等待在线状态确定；在线结果只能补充本地结果，不能破坏当前列表顺序和键盘选择。
- 大型 CSV 仍会消耗索引时间和内存；索引期间必须提供安全回退。
- Danbooru 数据可能包含 SFW 与 NSFW 标签。
- 动态提示词在通配符解析前可能无法提供可靠的共现标签。
- 兼容范围包括 Classic、Nodes 2.0、右侧参数面板、子图提升输入，以及通过公开集成属性接入的第三方文本框。

## Brand Commitments

- 仓库与发布名称为 `ComfyUI-Autocomplete-Aaalice`。
- ComfyUI 扩展 ID 为 `AutocompletePlus`，用户可见设置名称为 `Autocomplete Plus`。
- 保留持续维护分支的产品事实与对上游项目的致谢关系。
- 用户文案保持简洁、直接、可操作，并与 ComfyUI 宿主界面和当前语言一致。
- 现有品牌资源位于 `assets/icon.png` 与 `assets/banner.png`。

## Evidence on Hand

- `README.md` 包含自动补全和共现标签的真实界面预览与完整用户操作说明。
- `assets/icon.png` 与 `assets/banner.png` 是当前发布资源。
- `docs/development/testing.md` 记录启动生命周期、在线服务可靠性和人工验收边界。
- `docs/development/design-qa.md` 记录现有界面的设计 QA 证据。
- `tests/js/` 与 `tests/python/` 覆盖数据加载、输入交互、在线服务、翻译和兼容集成等行为。
- 当前没有经确认的客户案例、使用量、性能基准、推荐语或其他商业证明；未来内容不得虚构这些信息。

## Product Principles

1. 本地结果优先可用，在线能力只做增量补充。
2. 不阻塞 ComfyUI 启动或用户当前输入流程。
3. 在不同 ComfyUI 输入载体中保持一致、可预期的交互。
4. 对加载、网络和数据失败提供明确状态与可恢复路径。
5. 保持工作流兼容，同时让设置、反馈和用户文案尽量简单。

## Accessibility & Inclusion

- 核心操作必须支持键盘完成，包括候选移动、插入、关闭面板和快捷操作。
- 交互控件应保留可见焦点状态，并使用适当的 ARIA label、role、live region 和隐藏状态。
- 所有用户可见界面事实应在英文、简体中文、繁体中文和日文目录中保持一致；语言回退不能破坏核心功能。
