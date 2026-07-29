# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SpanString 宿主集成 |
| 特性编号 | Func-05-09-10-Feat-08 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 12–14 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`10-attributed-string/design.md`
- 源码定位：`rich_editor_pattern.h`（~40 styled-string 方法）、`rich_editor_styled_string_controller.h:25`、`rich_editor_undo_manager.h:168`（StyledStringUndoManager）、`rich_editor_event_hub.h:93–119`、`text/styled_string_change_value.h`、`text_field_pattern.h:1903`（SetPlaceholderStyledString）、`js_text_layout.h`、`text_common.d.ts:594/627/660/704`

## 用户故事

### US-1: Controller 与监听
作为开发者，我希望经 `StyledStringController` 设置/获取并监听变更。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `controller.setStyledString(styledString)` THEN 设置属性字符串（@since 12） | 正常 |
| AC-1.2 | WHEN `controller.getStyledString()` THEN 返回 MutableStyledString（@since 12） | 正常 |
| AC-1.3 | WHEN `onWillChange` 返回 false THEN 拦截变更（@since 12） | 正常 |
| AC-1.4 | WHEN `onDidChange` THEN 通知变更（@since 12） | 正常 |

### US-2: Text 集成
作为开发者，我希望经 `TextController` 在 Text 消费 StyledString。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `TextController.setStyledString(value)` THEN Text 渲染属性字符串（@since 12） | 正常 |
| AC-2.2 | WHEN `TextController.getLayoutManager()` THEN 返回 LayoutManager（@since 12） | 正常 |

### US-3: RichEditor 集成
作为开发者，我希望经 `RichEditorStyledStringController` 在 RichEditor styled-string-mode 消费。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `RichEditorStyledStringController.setStyledString`/`getStyledString` THEN 设置/获取（@since 12） | 正常 |
| AC-3.2 | WHEN `onContentChanged(listener)` THEN 监听内容变更（@since 12） | 正常 |
| AC-3.3 | WHEN `RichEditorController.fromStyledString`/`toStyledString` THEN 与 RichEditorSpan 互转（@since 12） | 正常 |
| AC-3.4 | WHEN 编辑（IME 插入/删除）THEN StyledStringUndoManager 支持 undo/redo | 正常 |
| AC-3.5 | WHEN 拖拽/复制/粘贴 THEN 含 HTML 转换 | 正常 |

### US-4: TextField 集成
作为开发者，我希望经 TextField placeholder StyledString 设置占位属性字符串。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN `TextField SetPlaceholderStyledString` THEN 设置占位属性字符串 | 正常 |

### US-5: LayoutManager
作为开发者，我希望经 LayoutManager 查询行/字形/矩形。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN `getLineCount`/`getGlyphPositionAtCoordinate`/`getLineMetrics`（@since 12）THEN 返回行/字形/度量 | 正常 |
| AC-5.2 | WHEN `getRectsForRange`（@since 14）THEN 返回区间矩形 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-08 | 单测 | text_common.d.ts:594 |
| AC-1.3 | R-2 | TASK-AS-08 | 单测 | text_common.d.ts:627 |
| AC-2.1 | R-3 | TASK-AS-08 | 单测 | text.d.ts:1763 |
| AC-2.2 | R-4 | TASK-AS-08 | 单测 | text.d.ts:1774 |
| AC-3.1 | R-5 | TASK-AS-08 | 单测 | rich_editor.d.ts:3417/3427 |
| AC-3.2 | R-5 | TASK-AS-08 | 单测 | rich_editor.d.ts:3449 |
| AC-3.3 | R-5 | TASK-AS-08 | 单测 | rich_editor.d.ts:3369/3383 |
| AC-3.4 | R-6 | TASK-AS-08 | 单测 | rich_editor_undo_manager.h:168 |
| AC-3.5 | R-7 | TASK-AS-08 | 单测 | rich_editor_pattern.h |
| AC-4.1 | R-8 | TASK-AS-08 | 单测 | text_field_pattern.h:1903 |
| AC-5.1 | R-9 | TASK-AS-08 | 单测 | text_common.d.ts:704 |
| AC-5.2 | R-9 | TASK-AS-08 | 单测 | text_common.d.ts:704 |

## 觅则定义

| 觅则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | setStyledString/getStyledString | 设置/获取 MutableStyledString（@since 12） | — | AC-1.1,1.2 |
| R-2 | 行为 | onWillChange（返回 bool）/onDidChange | 拦截/通知变更（@since 12） | will 返回 bool | AC-1.3,1.4 |
| R-3 | 行为 | TextController.setStyledString | Text 渲染属性字符串（@since 12） | — | AC-2.1 |
| R-4 | 行为 | TextController.getLayoutManager | 返回 LayoutManager（@since 12） | — | AC-2.2 |
| R-5 | 行为 | RichEditorStyledStringController set/get/onContentChanged/from/toStyledString | RichEditor styled-string-mode（@since 12） | — | AC-3.1..3.3 |
| R-6 | 行为 | IME 插入/删除 | StyledStringUndoManager undo/redo | — | AC-3.4 |
| R-7 | 行为 | 拖拽/复制/粘贴 | 含 HTML 转换 | — | AC-3.5 |
| R-8 | 行为 | TextField SetPlaceholderStyledString | 设置占位属性字符串 | — | AC-4.1 |
| R-9 | 行为 | LayoutManager getLineCount/getGlyphPositionAtCoordinate/getLineMetrics/getRectsForRange | 行/字形/度量/矩形（@since 12/14） | getRectsForRange @since 14 | AC-5.1,5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 Controller | 单测 | will/did |
| VM-2 | R-3/R-4 Text | 单测 | LayoutManager |
| VM-3 | R-5..R-7 RichEditor | 单测 | undo/HTML |
| VM-4 | R-9 LayoutManager | 单测 | getRectsForRange |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `interface StyledStringController` | Public | setStyledString/getStyledString | void/MutableStyledString | 无 | Controller @since 12 | AC-1.1,1.2 |
| `interface StyledStringChangedListener` | Public | onWillChange?/onDidChange? | bool/void | 无 | 监听 @since 12 | AC-1.3,1.4 |
| `interface StyledStringChangeValue` | Public | range/replacementString/previewText? | — | 无 | 变更值 @since 12 | AC-1.3 |
| `TextController.setStyledString`/`getLayoutManager` | Public | StyledString | void/LayoutManager | 无 | Text 集成 @since 12 | AC-2.1,2.2 |
| `RichEditorStyledStringOptions`/`RichEditorStyledStringController` | Public | controller | — / 实例 | 无 | RichEditor 集成 @since 12 | AC-3.1,3.2 |
| `RichEditorController.fromStyledString`/`toStyledString` | Public | StyledString/RichEditorRange | RichEditorSpan[]/StyledString | 无 | 互转 @since 12 | AC-3.3 |
| `interface LayoutManager` | Public | — | — | 无 | 布局查询 @since 12/14 | AC-5.1,5.2 |

## 接口规格

### 接口定义

**StyledStringChangedListener.onWillChange**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onWillChange?: Callback<StyledStringChangeValue, boolean>` |
| 返回值 | `boolean` — false 拦截 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| changeValue | StyledStringChangeValue | 是 | — | range/replacementString/previewText? |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | onWillChange true | 应用变更 | AC-1.3 |
| 2 | onWillChange false | 拦截 | AC-1.3 |
| 3 | IME 插入 | undo/redo | AC-3.4 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** Controller/Listener/Text/RichEditor 集成 @since 12；getRectsForRange @since 14
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| RichEditor styled-string-mode | ~40 方法 + Undo/Redo | AC-3.1..3.5 |
| 跨 3 宿主 | Text/RichEditor/TextField | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | undo/redo 无明显延迟 | 性能测试 | rich_editor_undo_manager.h |
| 可测试性 | 宿主集成可单测 | 单测 | rich_editor_styled_string_test_ng.cpp |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Selection 可访问 | AC-5.1 |

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
    query: "StyledString 宿主集成 Text/RichEditor/TextField + LayoutManager"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`、`text_common.d.ts`、`rich_editor.d.ts`、`text.d.ts`
