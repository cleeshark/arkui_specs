# 特性规格

> Func-05-09-02-Feat-01 组件初始化与双模式架构：固化 RichEditor 组件两种构造模式（旧框架 `RichEditorOptions` 与 StyledString `RichEditorStyledStringOptions`）、统一选项设置器 `setRichEditorOptions`、通用属性修改器 `attributeModifier` 的行为规格，重点记录双模式架构中 `isSpanStringMode_` 模式标志在 `TextPattern` 基类的存储位置、控制器创建与绑定在 `InitRichEditorModel` 中的耦合设计，以及生命周期中模式相关/无关分支的划分。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件初始化与双模式架构 (Component Init & Dual-Mode Architecture) |
| 特性编号 | Func-05-09-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10+（旧框架模式），API 12+（StyledString 模式） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐双模式构造函数行为规格 | 固化旧框架 `RichEditorOptions` 与 StyledString `RichEditorStyledStringOptions` 两种构造路径的初始化差异 |
| MODIFIED | 补齐模式标志 `isSpanStringMode_` 存储位置说明 | 强调模式标志存储在 `TextPattern` 基类而非 `RichEditorPattern` 自身 |
| MODIFIED | 补齐控制器绑定耦合关系 | 记录控制器创建与绑定在 `InitRichEditorModel` 中耦合完成的设计决策 |
| MODIFIED | 补齐静态版 `setRichEditorOptions` 分发逻辑 | selector 0/1 分发路径和 `CreateFrameNode` 后模式切换能力 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/02-rich-editor/design.md` | 未创建 |

---

## 用户故事

### US-1: 旧框架模式构造初始化

**作为** 应用开发者,
**我想要** 通过 `RichEditor(value: RichEditorOptions)` 构造函数创建 RichEditor 组件,
**以便** 使用旧框架 span 操作接口编辑富文本内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `RichEditor(value: RichEditorOptions)` THEN 创建 FrameNode，tag 为 `V2::RICH_EDITOR_ETS_TAG`，`isStyledStringMode=false`（`rich_editor_model_ng.cpp:24-35`） | 正常 |
| AC-1.2 | WHEN 旧框架模式构造 THEN `RichEditorPattern(isStyledStringMode=false)` 通过 lambda 构造，并调用 `InitRichEditorModel()` 完成初始化（`rich_editor_model_ng.cpp:24-35`） | 正常 |
| AC-1.3 | WHEN `InitRichEditorModel()` 执行 THEN 设置默认布局属性 `TextAlign::START`、`WordBreak::BREAK_WORD`、`Alignment::TOP_LEFT`，注册回调，设置主题边框/圆角，配置拖拽手势（`rich_editor_model_ng.cpp:67-109`） | 正常 |
| AC-1.4 | WHEN 旧框架模式 THEN 创建 `RichEditorController`（非 StyledStringController），设置 pattern 弱引用和 host 弱引用后调用 `pattern->SetRichEditorController()`（`rich_editor_model_ng.cpp:76-86`） | 正常 |
| AC-1.5 | WHEN Pattern 构造且 `isStyledStringMode=false` THEN 调用 `SetSpanStringMode(false)`，不创建 `styledString_` 成员（`rich_editor_pattern.cpp:194, 197-200`） | 正常 |
| AC-1.6 | WHEN Pattern 构造完成 THEN 在构造函数中创建 `undoManager`（`rich_editor_pattern.cpp:204`） | 正常 |

### US-2: StyledString 模式构造初始化

**作为** 应用开发者,
**我想要** 通过 `RichEditor(options: RichEditorStyledStringOptions)` 构造函数创建 RichEditor 组件 (@since 12),
**以便** 使用 StyledString 数据模型驱动富文本编辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `RichEditor(options: RichEditorStyledStringOptions)` (@since 12) THEN 创建 FrameNode，tag 为 `V2::RICH_EDITOR_ETS_TAG`，`isStyledStringMode=true`（`rich_editor_model_ng.cpp:24-35`） | 正常 |
| AC-2.2 | WHEN StyledString 模式构造 THEN `RichEditorPattern(isStyledStringMode=true)` 构造时调用 `SetSpanStringMode(true)`（`rich_editor_pattern.cpp:194`） | 正常 |
| AC-2.3 | WHEN StyledString 模式 THEN 在 Pattern 构造函数中创建 `styledString_` 成员（`rich_editor_pattern.cpp:197-200`） | 正常 |
| AC-2.4 | WHEN StyledString 模式 THEN 创建 `RichEditorStyledStringController`（非 RichEditorController），设置弱引用后调用 `pattern->SetRichEditorStyledStringController()`（`rich_editor_model_ng.cpp:76-86`） | 正常 |
| AC-2.5 | WHEN API 版本 < 12 THEN `RichEditorStyledStringOptions` 构造函数不可用 | 边界 |

### US-3: setRichEditorOptions 统一选项设置器

**作为** 静态 ArkTS 开发者,
**我想要** 通过 `setRichEditorOptions` 设置 RichEditor 选项,
**以便** 在静态前端路径中选择构造模式并绑定控制器。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 静态版调用 `SetRichEditorOptionsImpl()` 且 selector=0 THEN 绑定旧框架 controller（`rich_editor_static_modifier.cpp:256-293`） | 正常 |
| AC-3.2 | WHEN 静态版调用 `SetRichEditorOptionsImpl()` 且 selector=1 THEN 先调用 `RichEditorModelStatic::SetStyledStringMode(frameNode, true)` 再绑定 controller（`rich_editor_static_modifier.cpp:256-293`） | 正常 |
| AC-3.3 | WHEN `SetStyledStringMode()` 被调用 THEN 执行 `SetSpanStringMode`、`RecreateUndoManager`、`CreateStyledString`、重建 controller（`rich_editor_model_static.cpp:83-96`） | 正常 |
| AC-3.4 | WHEN `SetStyledStringMode()` 在 `CreateFrameNode` 之后调用 THEN 模式切换生效，允许静态路径在创建节点后切换模式（`rich_editor_model_static.cpp:83-96`） | 边界 |

### US-4: attributeModifier 通用属性修改器

**作为** 应用开发者,
**我想要** 通过 `attributeModifier` 为 RichEditor 组件应用通用属性修改器,
**以便** 以命令式方式动态修改组件属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `attributeModifier` THEN 通过 `attributeModifierFunc` 创建 `RichEditorModifier(nativePtr, classType)`（`ArkRichEditor.ts:821-825`） | 正常 |
| AC-4.2 | WHEN `RichEditorModifier` 初始化 THEN `LazyArkRichEditorComponent` 加载 NAPI 模块并委托 native（`rich_editor_modifier.ts:16-26`） | 正常 |

### US-5: 双模式架构与模式标志

**作为** 框架开发者,
**我想要** 了解 `isSpanStringMode_` 模式标志的存储位置和生命周期分支的划分,
**以便** 正确维护双模式架构的代码路径。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 查询模式标志 THEN `isSpanStringMode_` 定义在基类 `TextPattern`（`text_pattern.h:669`），非 `RichEditorPattern` 自身成员，通过 `TextPattern::GetSpanStringMode()` 获取（`text_pattern.cpp:9444-9451`） | 正常 |
| AC-5.2 | WHEN `OnAttachToFrameNode()` 执行 THEN 两种模式均创建 `RichEditorContentPattern` 子节点并注册窗口回调（`rich_editor_pattern.cpp:1273-1295`） | 正常 |
| AC-5.3 | WHEN `OnModifyDone()` 执行 THEN 两种模式均初始化事件和手势：鼠标、焦点、点击、长按、触摸、拖拽、滚动、无障碍（`rich_editor_pattern.cpp:705-758`） | 正常 |
| AC-5.4 | WHEN `BeforeCreateLayoutWrapper()` 执行 THEN 首个模式相关分支出现：旧框架模式重建 `spans_` 列表，StyledString 模式调用 `contentMod_->ContentChange()`（`rich_editor_pattern.cpp:790-803`） | 边界 |

### US-6: Controller 层级与委托模式

**作为** 框架开发者,
**我想要** 了解 RichEditor 控制器三层层级和委托调用模式,
**以便** 正确扩展控制器操作接口。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `RichEditorController` 调用 span 操作（AddTextSpan/AddImageSpan/AddSymbolSpan/DeleteSpans/UpdateSpanStyle 等） THEN 通过 `pattern_.Upgrade()` 委托给 `RichEditorPattern` 对应方法（`rich_editor_controller.cpp:20-25`） | 正常 |
| AC-6.2 | WHEN `RichEditorStyledStringController` 调用 `SetStyledString` THEN 通过 `pattern_.Upgrade()` 委托（`rich_editor_styled_string_controller.cpp:20-29`） | 正常 |
| AC-6.3 | WHEN `RichEditorBaseController` 调用共享方法（SetCaretOffset/SetTypingStyle/CloseSelectionMenu/IsEditing/StopEditing 等） THEN 通过 `pattern_.Upgrade()` 委托（`rich_editor_base_controller.cpp:66-73`） | 正常 |
| AC-6.4 | WHEN 控制器持有引用 THEN `RichEditorBaseController` 持有 `WeakPtr<RichEditorPattern> pattern_`（`rich_editor_base_controller.h:57`）和 `WeakPtr<FrameNode> host_`（`rich_editor_base_controller.h:58`），均为弱引用 | 正常 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1, R-2, R-3, R-5 | N/A（存量） | 代码审查 | `rich_editor_model_ng.cpp:24-35, 67-109` |
| AC-2.1~2.5 | R-1, R-3, R-4, R-5 | N/A | 代码审查 | `rich_editor_pattern.cpp:183-200` |
| AC-3.1~3.4 | R-6, R-7, R-8 | N/A | 代码审查 | `rich_editor_static_modifier.cpp:256-293`, `rich_editor_model_static.cpp:83-96` |
| AC-4.1~4.2 | R-9, R-10 | N/A | 代码审查 | `ArkRichEditor.ts:821-825`, `rich_editor_modifier.ts:16-26` |
| AC-5.1~5.4 | R-4, R-11, R-12, R-13 | N/A | 代码审查 | `text_pattern.h:669`, `rich_editor_pattern.cpp:705-803, 1273-1295` |
| AC-6.1~6.4 | R-14, R-15, R-16, R-17 | N/A | 代码审查 | `rich_editor_base_controller.h:29-59`, `rich_editor_controller.cpp:20-25` |

---

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `RichEditorModelNG::Create(isStyledStringMode)` | 创建 FrameNode（tag=`V2::RICH_EDITOR_ETS_TAG`），通过 lambda 构造 `RichEditorPattern(isStyledStringMode)`，调用 `InitRichEditorModel()` | 两种模式共享同一 Create 入口 | AC-1.1, AC-1.2, AC-2.1 |
| R-2 | 行为 | `InitRichEditorModel()` 执行 | 设置布局默认值（`TextAlign::START`、`WordBreak::BREAK_WORD`、`Alignment::TOP_LEFT`），注册回调，设置主题边框/圆角，配置拖拽手势 | 默认值适用于两种模式 | AC-1.3 |
| R-3 | 行为 | `InitRichEditorModel()` 内控制器绑定 | 根据 `isStyledStringMode` 创建对应 Controller，设置 pattern 弱引用和 host 弱引用后调用对应 Setter — 绑定与创建耦合，无独立 `SetController()` 公开入口 | 绑定在 `InitRichEditorModel` 内完成（`rich_editor_model_ng.cpp:76-86`） | AC-1.4, AC-2.4 |
| R-4 | 行为 | 模式标志 `isSpanStringMode_` 存储位置 | 定义在基类 `TextPattern`（`text_pattern.h:669`），非 `RichEditorPattern` 自身成员 — 共享基础设施决策 | 通过 `SetSpanStringMode()`/`GetSpanStringMode()` 访问（`text_pattern.cpp:9444-9451`） | AC-5.1 |
| R-5 | 行为 | Pattern 构造函数执行 | 调用 `SetSpanStringMode(isStyledStringMode)`；仅 span string 模式创建 `styledString_`；构造 `undoManager` | `styledString_` 仅在 `isStyledStringMode=true` 时创建（`rich_editor_pattern.cpp:197-200`） | AC-1.5, AC-1.6, AC-2.2, AC-2.3 |
| R-6 | 行为 | 静态版 `SetRichEditorOptionsImpl()` selector=0 | 绑定旧框架 controller | `Ark_RichEditorOptions` (selector 0) 定义见 `arkoala_api_generated.h:9209-9228` | AC-3.1 |
| R-7 | 行为 | 静态版 `SetRichEditorOptionsImpl()` selector=1 | 先调用 `SetStyledStringMode(frameNode, true)` 再绑定 controller | `Ark_RichEditorStyledStringOptions` (selector 1) 定义见 `arkoala_api_generated.h:9209-9228` | AC-3.2 |
| R-8 | 行为 | `SetStyledStringMode()` 被调用 | 执行 `SetSpanStringMode`、`RecreateUndoManager`、`CreateStyledString`、重建 controller — 允许 `CreateFrameNode` 后切换模式（仅静态路径） | 仅静态路径支持后切（`rich_editor_model_static.cpp:83-96`） | AC-3.3, AC-3.4 |
| R-9 | 行为 | 调用 `attributeModifier` | 通过 `attributeModifierFunc` 创建 `RichEditorModifier(nativePtr, classType)` | `globalThis.RichEditor.attributeModifier`（`ArkRichEditor.ts:821-825`） | AC-4.1 |
| R-10 | 行为 | `RichEditorModifier` 初始化 | `LazyArkRichEditorComponent` 加载 NAPI 模块并委托 native | — | AC-4.2 |
| R-11 | 行为 | `OnAttachToFrameNode()` 执行 | 两种模式均创建 `RichEditorContentPattern` 子节点并注册窗口回调 | 模式无关分支（`rich_editor_pattern.cpp:1273-1295`） | AC-5.2 |
| R-12 | 行为 | `OnModifyDone()` 执行 | 两种模式均初始化事件/手势（鼠标、焦点、点击、长按、触摸、拖拽、滚动、无障碍） | 模式无关分支（`rich_editor_pattern.cpp:705-758`） | AC-5.3 |
| R-13 | 边界 | `BeforeCreateLayoutWrapper()` 执行 | 首个模式相关分支：旧框架重建 `spans_` 列表，StyledString 模式调用 `contentMod_->ContentChange()` | 模式相关分支（`rich_editor_pattern.cpp:790-803`） | AC-5.4 |
| R-14 | 行为 | Controller 持有引用 | `RichEditorBaseController` 持有 `WeakPtr<RichEditorPattern> pattern_` 和 `WeakPtr<FrameNode> host_` | 均为弱引用（`rich_editor_base_controller.h:57-58`） | AC-6.4 |
| R-15 | 行为 | `RichEditorController` 调用 span 操作 | 通过 `pattern_.Upgrade()` 委托给 `RichEditorPattern` 对应方法 | 委托模式（`rich_editor_controller.cpp:20-25`） | AC-6.1 |
| R-16 | 行为 | `RichEditorStyledStringController` 调用 `SetStyledString` 等 | 通过 `pattern_.Upgrade()` 委托 | 委托模式（`rich_editor_styled_string_controller.cpp:20-29`） | AC-6.2 |
| R-17 | 行为 | `RichEditorBaseController` 调用共享方法 | 通过 `pattern_.Upgrade()` 委托 | 委托模式（`rich_editor_base_controller.cpp:66-73`） | AC-6.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.6（旧框架构造） | 代码审查 | Create 入口、`InitRichEditorModel` 默认值、Controller 绑定、Pattern 构造 |
| VM-2 | AC-2.1~2.5（StyledString 构造） | 代码审查 | 模式标志传递、`styledString_` 创建、Controller 类型选择 |
| VM-3 | AC-3.1~3.4（setRichEditorOptions） | 代码审查 | selector 分发、`SetStyledStringMode` 后切 |
| VM-4 | AC-4.1~4.2（attributeModifier） | 代码审查 | `RichEditorModifier` 创建和 NAPI 委托 |
| VM-5 | AC-5.1~5.4（双模式架构） | 代码审查 | 模式标志存储位置、生命周期模式相关/无关分支 |
| VM-6 | AC-6.1~6.4（Controller 委托） | 代码审查 | 三层 Controller 委托模式和弱引用持有 |

## API 变更分析

> 本特性为存量规格补录，记录各 API 的引入版本和当前签名。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `RichEditor(value: RichEditorOptions)` | Public | `RichEditorOptions`（含 controller） | `RichEditorAttribute` | N/A | 旧框架模式构造函数 | AC-1.1~1.6 |
| `RichEditor(options: RichEditorStyledStringOptions)` | Public (@since 12) | `RichEditorStyledStringOptions`（含 controller） | `RichEditorAttribute` | N/A | StyledString 模式构造函数 | AC-2.1~2.5 |
| `setRichEditorOptions` | InnerApi（静态前端） | `Ark_RichEditorOptions` tagged union（selector 0/1） | void | N/A | 统一选项设置器，按 selector 分发模式 | AC-3.1~3.4 |
| `attributeModifier` | Public | `Modifier` | `RichEditorAttribute` | N/A | 通用属性修改器 | AC-4.1~4.2 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。下表汇总各接口的关键行为场景。

| 接口 | 开放范围 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|----------|---------|
| `RichEditor(value: RichEditorOptions)` | Public | `value`: RichEditorOptions（含 `RichEditorController`） | 创建 FrameNode（`isStyledStringMode=false`），构造 Pattern，调用 `InitRichEditorModel()`，创建并绑定 `RichEditorController` | AC-1.1~1.6 |
| `RichEditor(options: RichEditorStyledStringOptions)` | Public (@since 12) | `options`: RichEditorStyledStringOptions（含 `RichEditorStyledStringController`） | 创建 FrameNode（`isStyledStringMode=true`），构造 Pattern 并创建 `styledString_`，创建并绑定 `RichEditorStyledStringController` | AC-2.1~2.5 |
| `setRichEditorOptions` | InnerApi（静态前端） | `options`: `Ark_RichEditorOptions` tagged union（selector 0/1） | selector 0 → 绑定旧框架 controller；selector 1 → 先 `SetStyledStringMode(true)` 再绑定；支持 `CreateFrameNode` 后模式后切 | AC-3.1~3.4 |
| `attributeModifier` | Public | `modifier`: Modifier | 通过 `attributeModifierFunc` 创建 `RichEditorModifier(nativePtr, classType)`，`LazyArkRichEditorComponent` 加载 NAPI 模块 | AC-4.1~4.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — API 12 引入 `RichEditorStyledStringOptions` 构造函数，新增双模式架构；静态版 `setRichEditorOptions` 支持 selector 分发和模式后切
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（旧框架 `RichEditorOptions`），API 12（`RichEditorStyledStringOptions`）
- **API 版本号策略:** 旧框架 `RichEditorOptions` 自 API 10 起；`RichEditorStyledStringOptions` 自 API 12 起；`attributeModifier` 为通用属性修改器，随 RichEditor 组件一同引入

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 模式标志存储在基类 | `isSpanStringMode_` 定义在 `TextPattern` 基类（`text_pattern.h:669`），非 `RichEditorPattern` 自身成员 — 共享基础设施决策，`Text` 和 `RichEditor` 共用同一模式标志 | AC-5.1 |
| 控制器绑定与创建耦合 | Controller 创建和绑定在 `InitRichEditorModel()` 中完成（`rich_editor_model_ng.cpp:76-86`），无独立 `SetController()` 公开入口 — 绑定和创建不可分离 | AC-1.4, AC-2.4 |
| 静态路径支持模式后切 | `SetStyledStringMode()` 允许在 `CreateFrameNode` 之后切换模式，仅静态路径支持（`rich_editor_model_static.cpp:83-96`） | AC-3.4 |
| 弱引用委托模式 | Controller 通过 `WeakPtr<RichEditorPattern>` 委托，Pattern 生命周期独立于 Controller | AC-6.1~6.4 |
| 生命周期模式无关分支 | `OnAttachToFrameNode`、`OnModifyDone` 对两种模式行为一致，不按模式区分 | AC-5.2, AC-5.3 |
| 首个模式相关分支在布局前 | `BeforeCreateLayoutWrapper` 是第一个模式相关分支（`rich_editor_pattern.cpp:790-803`），之前均为模式无关 | AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可测试性 | 双模式通过 `isStyledStringMode` 布尔标志区分，可在 `Create` 时指定 | 代码审查 | `rich_editor_model_ng.cpp:24-35` |
| 可靠性 | Controller 持有 `WeakPtr`，避免循环引用导致内存泄漏 | 代码审查 | `rich_editor_base_controller.h:57-58` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | `OnModifyDone` 初始化无障碍事件，两种模式均支持 | AC-5.3 |
| 大字体 | N/A | 初始化阶段不涉及大字体适配 | — |
| 深色模式 | N/A | 初始化阶段不涉及主题模式切换 | — |
| 多窗口/分屏 | N/A | 初始化阶段不涉及窗口模式 | — |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | API 12 引入 `RichEditorStyledStringOptions`，形成双模式架构 | AC-2.1~2.5 |
| 生态兼容 | N/A | — | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RichEditor 组件初始化与双模式架构
  作为应用开发者
  我想要通过两种构造函数创建 RichEditor 组件
  以便选择适合的富文本编辑模式

  Scenario: 旧框架模式构造
    Given 应用需要使用 span 操作接口编辑富文本
    When 调用 RichEditor(value: RichEditorOptions)
    Then 创建 FrameNode 且 isStyledStringMode=false
    And 创建 RichEditorController 并绑定到 Pattern
    And 设置默认布局属性 TextAlign::START, WordBreak::BREAK_WORD, Alignment::TOP_LEFT
    And 不创建 styledString_ 成员

  Scenario: StyledString 模式构造
    Given 应用需要使用 StyledString 数据模型驱动编辑
    When 调用 RichEditor(options: RichEditorStyledStringOptions)
    Then 创建 FrameNode 且 isStyledStringMode=true
    And 创建 RichEditorStyledStringController 并绑定到 Pattern
    And 在 Pattern 构造函数中创建 styledString_ 成员

  Scenario: 静态版 selector 分发与模式后切
    Given 静态 ArkTS 前端调用 setRichEditorOptions
    When options 为 Ark_RichEditorOptions (selector 0)
    Then 绑定旧框架 controller
    When options 为 Ark_RichEditorStyledStringOptions (selector 1)
    Then 先调用 SetStyledStringMode(frameNode, true) 再绑定 controller
    And 执行 SetSpanStringMode, RecreateUndoManager, CreateStyledString, 重建 controller

  Scenario: 生命周期模式相关与无关分支
    Given 一个已创建的 RichEditor 组件（任一模式）
    When OnAttachToFrameNode 和 OnModifyDone 执行
    Then 两种模式均创建 RichEditorContentPattern 子节点并初始化事件/手势
    When BeforeCreateLayoutWrapper 执行
    Then 旧框架模式重建 spans_ 列表
    But StyledString 模式调用 contentMod_->ContentChange()
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（组件初始化与双模式架构，不含 span 操作细节、布局算法、渲染细节）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RichEditor dual-mode architecture: isSpanStringMode_ in TextPattern base class, controller binding in InitRichEditorModel"
  - repo: "openharmony/ace_engine"
    query: "RichEditor static frontend SetRichEditorOptionsImpl selector dispatch and SetStyledStringMode mode switch"
  - repo: "openharmony/interface_sdk-js"
    query: "RichEditor constructor overloads RichEditorOptions and RichEditorStyledStringOptions API signatures"
```

**关键文档：**
- SDK 动态版声明: `interface/sdk-js/api/@internal/component/ets/rich_editor.d.ts`
- SDK 静态版声明: `interface/sdk-js/api/arkui/component/rich_editor.static.d.ets`
- 控制器基类: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_base_controller.h`
- 模式标志定义: `frameworks/core/components_ng/pattern/text/text_pattern.h`
