# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 光标与选择 |
| 特性编号 | Func-05-09-08-Feat-05 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7–23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`text_field_model_ng.h`（SetCaretColor/SetCaretStyle/SetCaretPosition/SetSelectedBackgroundColor/SetSelectedDragPreviewStyle）、`text_field_paint_property.h`（CursorColor/CursorWidth/SelectedBackgroundColor/FirstHandleInfo/SecondHandleInfo）、`TextInputController`（caretPosition/setTextSelection/stopEditing）

## 用户故事

### US-1: 光标
作为开发者，我希望控制光标颜色/样式/位置。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `caretColor(value)` THEN 写入 CursorColor | 正常 |
| AC-1.2 | WHEN `caretStyle(value)`（CaretStyle 含 width）THEN 写入 CursorWidth | 正常 |
| AC-1.3 | WHEN `caretPosition(n)` 或 controller.caretPosition(n) THEN 移动光标 | 正常 |
| AC-1.4 | WHEN caretPosition 越界 THEN 按文本长度 clamp | 边界 |

### US-2: 选择
作为开发者，我希望控制选中底色与文本选择。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `selectedBackgroundColor(value)` THEN 写入 SelectedBackgroundColor | 正常 |
| AC-2.2 | WHEN `controller.setTextSelection(start, end, options?)` THEN 选中文本 | 正常 |
| AC-2.3 | WHEN `selectedDragPreviewStyle(value)`（@since 23）THEN 设置拖拽预览样式 | 正常 |
| AC-2.4 | WHEN `onTextSelectionChange(callback)` THEN 选择变化回调（@since 10/18） | 正常 |

### US-3: 内容滚动/尺寸
作为开发者，我希望监听内容滚动与尺寸。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `onContentScroll(callback)` THEN 内容滚动回调（@since 10/18） | 正常 |
| AC-3.2 | WHEN C-API `NODE_TEXT_INPUT_CONTENT_RECT`/`CONTENT_LINE_COUNT` THEN 获取内容矩形与行数 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-05 | 单测 | text_field_paint_property.h |
| AC-1.2 | R-1 | TASK-TI-05 | 单测 | text_field_model_ng.h:51 |
| AC-1.3 | R-2 | TASK-TI-05 | 单测 | TextInputController caretPosition |
| AC-1.4 | R-3 | TASK-TI-05 | 单测 | — |
| AC-2.1 | R-4 | TASK-TI-05 | 单测 | text_field_model_ng.h:53 |
| AC-2.2 | R-2 | TASK-TI-05 | 单测 | TextInputController setTextSelection |
| AC-2.3 | R-4 | TASK-TI-05 | 单测 | text_field_model_ng.h:183 |
| AC-2.4 | R-5 | TASK-TI-05 | 单测 | text_input.d.ts onTextSelectionChange |
| AC-3.1 | R-5 | TASK-TI-05 | 单测 | text_input.d.ts onContentScroll |
| AC-3.2 | R-6 | TASK-TI-05 | C-API 单测 | native_node.h:4060/4068 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | caretColor/caretStyle | 写入 CursorColor/CursorWidth | width≥0 | AC-1.1,1.2 |
| R-2 | 行为 | caretPosition/setTextSelection | 移动光标/选中文本 | 越界 clamp | AC-1.3,2.2 |
| R-3 | 边界 | caretPosition 越界 | clamp 到文本长度 | — | AC-1.4 |
| R-4 | 行为 | selectedBackgroundColor/selectedDragPreviewStyle | 写入底色/预览样式（@since 23） | — | AC-2.1,2.3 |
| R-5 | 行为 | onTextSelectionChange/onContentScroll | 回调（@since 10/18） | — | AC-2.4,3.1 |
| R-6 | 行为 | C-API CONTENT_RECT/CONTENT_LINE_COUNT | 获取矩形/行数 | — | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 光标 | 单测 | paint 属性 |
| VM-2 | R-2 选择 | 单测 | setTextSelection |
| VM-3 | R-6 C-API | C-API 单测 | CONTENT_RECT |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `caretColor(value)` | Public | ResourceColor | this | 无 | 光标色 @since 7 | AC-1.1 |
| `caretStyle(value)` | Public | CaretStyle | this | 无 | 光标样式 @since 11 | AC-1.2 |
| `caretPosition(value)`（属性） | Public | number | this | 无 | 光标位置 @since 11 | AC-1.3 |
| `TextInputController.caretPosition(value)` | Public | number | void | 无 | 光标位置 @since 8 | AC-1.3 |
| `TextInputController.setTextSelection(start,end,options?)` | Public | number,number,SelectionOptions? | void | 无 | 选中文本 @since 10/12 | AC-2.2 |
| `selectedBackgroundColor(value)` | Public | ResourceColor | this | 无 | 选中底色 @since 11 | AC-2.1 |
| `selectedDragPreviewStyle(value)` | Public | — | this | 无 | 拖拽预览样式 @since 23 | AC-2.3 |
| `onTextSelectionChange(callback)` | Public | OnTextSelectionChangeCallback | this | 无 | 选择回调 @since 10/18 | AC-2.4 |
| `onContentScroll(callback)` | Public | OnContentScrollCallback | this | 无 | 滚动回调 @since 10/18 | AC-3.1 |
| C-API `NODE_TEXT_INPUT_CARET_COLOR`/`CARET_STYLE`/`CARET_OFFSET`/`SELECTED_BACKGROUND_COLOR`/`TEXT_SELECTION`/`CONTENT_RECT`/`CONTENT_LINE_COUNT`/`SELECTED_DRAG_PREVIEW_STYLE` | System | KNode, ... | void/value | 无 | C-API 对应 @since 12/23 | 全部 |

## 接口规格

### 接口定义

**setTextSelection(selectionStart, selectionEnd, options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setTextSelection(selectionStart: number, selectionEnd: number, options?: SelectionOptions): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| selectionStart | number | 是 | — | 越界 clamp |
| selectionEnd | number | 是 | — | 越界 clamp |
| options | SelectionOptions | 否 | — | @since 12 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法区间 | 选中文本 | AC-2.2 |
| 2 | 越界 | clamp | AC-1.4 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** caretColor @since 7；caretStyle/caretPosition/controller @since 8–11；selectedBackgroundColor @since 11；setTextSelection options @since 12；selectedDragPreviewStyle @since 23
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| paint 属性存光标 | CursorColor/Width 在 PaintProperty | AC-1.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 光标移动流畅 | 帧率测试 | — |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 选择支持无障碍 | AC-2.2 |

## Spec 自审清单
- [x] 无占位符
- [x] AC 用 WHEN/THEN
- [x] 范围明确
- [x] 无模糊表述
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项检查

## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "TextInput 光标/选择 paint 属性与 controller"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
