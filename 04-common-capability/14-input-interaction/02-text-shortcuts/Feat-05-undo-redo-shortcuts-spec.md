# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 撤销/重做快捷键 |
| 特性编号 | Func-04-14-02-Feat-05 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`02-text-shortcuts/design.md`
- 源码定位：`text_field_pattern.cpp`(HandleOnUndoAction/HandleOnRedoAction/operationRecords_)、`rich_editor_pattern.cpp`(同+HandleOnExtendUndoAction)、`rich_editor_undo_manager.h`(RichEditorUndoManager 三策略)

## 用户故事

### US-1: 撤销/重做触发
作为开发者，我希望经 Ctrl+Z/Y/Shift+Z 撤销/重做。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Ctrl+Z THEN HandleOnUndoAction | 正常 |
| AC-1.2 | WHEN Ctrl+Y THEN HandleOnRedoAction | 正常 |
| AC-1.3 | WHEN Ctrl+Shift+Z THEN HandleOnRedoAction | 正常 |
| AC-1.4 | WHEN Alt+DEL THEN HandleOnExtendUndoAction(RichEditor) | 正常 |
| AC-1.5 | WHEN Mac Cmd+Z/Cmd+Shift+Z/Cmd+Y THEN 镜像撤销/重做 | 正常 |

### US-2: TextField undo 队列
作为开发者，我希望 TextField 经 operationRecords 队列支持撤销/重做。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 撤销 THEN 从 operationRecords_ 弹出恢复 | 正常 |
| AC-2.2 | WHEN 重做 THEN 从 redoOperationRecords_ 弹出恢复 | 正常 |
| AC-2.3 | WHEN 记录超 RECORD_MAX_LENGTH THEN 丢弃最旧 | 边界 |
| AC-2.4 | WHEN OnWillChangePreSetValue=true THEN 不记录 | 边界 |

### US-3: RichEditor 三策略 undo
作为开发者，我希望 RichEditor 经三策略 undo 管理 styled/spans/string。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN styled-string 模式 THEN StyledStringUndoManager 策略 | 正常 |
| AC-3.2 | WHEN spans 模式 THEN SpansUndoManager 策略 | 正常 |
| AC-3.3 | WHEN string 模式 THEN StringUndoManager 策略 | 正常 |
| AC-3.4 | WHEN preview-input 连续 THEN 合并记录 | 正常 |
| AC-3.5 | WHEN drag undo/redo THEN 按 drag 记录恢复 | 正常 |
| AC-3.6 | WHEN UndoRedoRecord 含 restoreBuilderSpan THEN 恢复 builder span | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TS-05 | 单测 | text_field_pattern.cpp:2230 |
| AC-1.3 | R-1 | TASK-TS-05 | 单测 | text_input_client.cpp Ctrl+Shift+Z |
| AC-1.4 | R-2 | TASK-TS-05 | 单测 | rich_editor_pattern.cpp:14692 |
| AC-1.5 | R-1 | TASK-TS-05 | 单测 | text_input_client.cpp:39 |
| AC-2.1 | R-3 | TASK-TS-05 | 单测 | text_field_pattern.cpp:2230 |
| AC-2.3 | R-4 | TASK-TS-05 | 单测 | RECORD_MAX_LENGTH |
| AC-2.4 | R-5 | TASK-TS-05 | 单测 | OnWillChangePreSetValue |
| AC-3.1 | R-6 | TASK-TS-05 | 单测 | rich_editor_undo_manager.h:168 |
| AC-3.2 | R-6 | TASK-TS-05 | 单测 | rich_editor_undo_manager.h:188 |
| AC-3.3 | R-6 | TASK-TS-05 | 单测 | rich_editor_undo_manager.h:209 |
| AC-3.4 | R-7 | TASK-TS-05 | 单测 | preview 合并 |
| AC-3.6 | R-8 | TASK-TS-05 | 单测 | UndoRedoRecord restoreBuilderSpan |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | Ctrl+Z/Y/Shift+Z | HandleOnUndoAction/HandleOnRedoAction | Mac Cmd 镜像 | AC-1.1..1.3,1.5 |
| R-2 | 行为 | Alt+DEL(RichEditor) | HandleOnExtendUndoAction | — | AC-1.4 |
| R-3 | 行为 | TextField 撤销/重做 | operationRecords_/redoOperationRecords_ 弹出恢复 | deque | AC-2.1,2.2 |
| R-4 | 边界 | 记录超 RECORD_MAX_LENGTH | 丢弃最旧 | — | AC-2.3 |
| R-5 | 边界 | OnWillChangePreSetValue=true | 不记录 | — | AC-2.4 |
| R-6 | 行为 | RichEditor 三策略 | StyledString/Spans/StringUndoManager 按模式 | — | AC-3.1..3.3 |
| R-7 | 行为 | preview-input 连续 | 合并记录 | — | AC-3.4 |
| R-8 | 行为 | UndoRedoRecord restoreBuilderSpan | 恢复 builder span | UndoRedoRecord | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 触发 | 单测 | Ctrl+Z/Y/Shift+Z |
| VM-2 | R-3..R-5 TextField 队列 | 单测 | 弹出/上限/不记录 |
| VM-3 | R-6..R-8 RichEditor 三策略 | 单测 | 策略选择/合并/builder 恢复 |

## API 变更分析
无公共 API。内部：`HandleOnUndoAction`、`HandleOnRedoAction`、`HandleOnExtendUndoAction`、`operationRecords_`/`redoOperationRecords_`、`RECORD_MAX_LENGTH`、`OnWillChangePreSetValue`、`RichEditorUndoManager`(StyledString/Spans/StringUndoManager)、`UndoRedoRecord`(rangeBefore/After, styledStringBefore/After, optionsListBefore/After, selectionBefore, caretAffinityBefore, isOnlyStyleChange, restoreBuilderSpan, updateSpanTypes, deleteDirection)、`UndoByRecords`/`RedoByRecords`。

## 接口规格

### 接口定义

**HandleOnUndoAction**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void HandleOnUndoAction()` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | 无参数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Ctrl+Z | 撤销 | AC-1.1 |
| 2 | 记录超限 | 丢弃最旧 | AC-2.3 |
| 3 | RichEditor styled | 三策略 | AC-3.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 框架内部无 @since；Mac Cmd 镜像标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 三策略 undo | RichEditorUndoManager 按数据模型 | AC-3.1..3.3 |
| 队列上限 | RECORD_MAX_LENGTH | AC-2.3 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | undo/redo 无明显延迟 | 性能测试 | rich_editor_undo_manager.h |
| 可测试性 | 三策略可单测 | 单测 | rich_editor_undo_manager.h |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| Mac | Cmd+Z/Cmd+Shift+Z/Cmd+Y 镜像 | 单测 | — | text_input_client.cpp:39 |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 撤销/重做键盘支持 | 全部 |

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
    query: "HandleOnUndo/Redo/ExtendUndoAction 与 RichEditorUndoManager 三策略"
```
**关键文档：** `frameworks/core/components_ng/pattern/rich_editor/rich_editor_undo_manager.h`
