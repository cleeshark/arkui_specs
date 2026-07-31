# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 选择快捷键 |
| 特性编号 | Func-04-14-02-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准-复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`02-text-shortcuts/design.md`
- 源码定位：`text_field_pattern.cpp`(HandleSelect/HandleOnSelectAll)、`text_input_client.cpp`(Shift 变体/Ctrl+A)、`text_pattern.cpp`(Shift+DPAD 选择)

## 用户故事

### US-1: Shift 方向选择
作为开发者，我希望经 Shift+方向键扩展选择。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Shift+DPAD_LEFT/RIGHT/UP/DOWN THEN HandleSelect(Left/Right/Up/Down) | 正常 |
| AC-1.2 | WHEN Shift+MOVE_HOME/END THEN HandleSelect(LineBegin/LineEnd) | 正常 |
| AC-1.3 | WHEN Ctrl+Shift+DPAD_LEFT/RIGHT THEN HandleSelect(LeftWord/RightWord) | 正常 |
| AC-1.4 | WHEN Ctrl+Shift+DPAD_UP/DOWN THEN HandleSelectExtend(ParagraghBegin/ParagraghEnd) | 正常 |

### US-2: 全选
作为开发者，我希望经 Ctrl+A 全选。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Ctrl+A THEN HandleOnSelectAll(isKeyEvent/inlineStyle/showMenu 分支) | 正常 |
| AC-2.2 | WHEN 全选完成 THEN ReportSelectionChangeEvent | 正常 |

### US-3: 锚点保持
作为开发者，我希望 Shift 选择时锚点保持方向连续。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Shift+UP/DOWN THEN RecordOriginCaretPosition 保留锚点 | 正常 |
| AC-3.2 | WHEN Text 组件 Shift+DPAD THEN UpdateShiftFlag 同步 SelectionContainer 切换拖拽 | 正常 |

### US-4: 异常行为记录
作为开发者/测试，我希望 Ctrl+Shift+Home/End 的异常行为被记录。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN Ctrl+Shift+MOVE_HOME/END THEN 派发 CursorMove(Home/End) 而非 HandleSelect（既有异常，按实现记录） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TS-03 | 单测 | text_field_pattern.cpp:1785 |
| AC-1.3 | R-1 | TASK-TS-03 | 单测 | text_input_client.cpp |
| AC-1.4 | R-2 | TASK-TS-03 | 单测 | text_input_client.cpp |
| AC-2.1 | R-3 | TASK-TS-03 | 单测 | text_field_pattern.cpp:2309 |
| AC-2.2 | R-3 | TASK-TS-03 | 单测 | — |
| AC-3.1 | R-4 | TASK-TS-03 | 单测 | text_input_client.cpp:206 |
| AC-3.2 | R-4 | TASK-TS-03 | 单测 | text_pattern.cpp:3693 |
| AC-4.1 | R-5 | TASK-TS-03 | 单测 | text_input_client.cpp Ctrl+Shift+MOVE |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | Shift+DPAD/MOVE_HOME/END / Ctrl+Shift+DPAD_LEFT/RIGHT | HandleSelect(对应方向/行/词) | 锚点保持 | AC-1.1..1.3 |
| R-2 | 行为 | Ctrl+Shift+DPAD_UP/DOWN | HandleSelectExtend(ParagraghBegin/End) | — | AC-1.4 |
| R-3 | 行为 | Ctrl+A | HandleOnSelectAll(isKeyEvent/inlineStyle/showMenu)+ReportSelectionChangeEvent | — | AC-2.1,2.2 |
| R-4 | 行为 | Shift 选择锚点 | Shift+UP/DOWN Record；UpdateShiftFlag 同步 SelectionContainer | — | AC-3.1,3.2 |
| R-5 | 边界 | Ctrl+Shift+MOVE_HOME/END | 派发 CursorMove(Home/End) 而非 HandleSelect（异常） | 既有行为 | AC-4.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 Shift 选择 | 单测 | 方向/词/段落 |
| VM-2 | R-3 全选 | 单测 | 分支+事件 |
| VM-3 | R-4 锚点 | 单测 | Record/ShiftFlag |
| VM-4 | R-5 异常 | 单测 | Ctrl+Shift+Home/End |

## API 变更分析
无公共 API。内部：`HandleSelect(CaretMoveIntent)`、`HandleSelectExtend`、`HandleOnSelectAll(isKeyEvent,inlineStyle,showMenu)`、`ReportSelectionChangeEvent`、`RecordOriginCaretPosition`、`UpdateShiftFlag`。边界：选择状态机制归 04-14-01 TextSelector。

## 接口规格

### 接口定义

**HandleSelect(intent)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void HandleSelect(CaretMoveIntent intent)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| intent | CaretMoveIntent | 是 | — | 选择方向 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Shift+LEFT | 左扩选 | AC-1.1 |
| 2 | Ctrl+Shift+LEFT | 左扩选一词 | AC-1.3 |
| 3 | Ctrl+Shift+HOME | CursorMove（异常） | AC-4.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 框架内部无 @since；Ctrl+Shift+Home/End 异常记录

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 锚点保持 | Record/Reset + ShiftFlag | AC-3.1 |
| 选择状态归 04-14-01 | 本域只覆盖快捷键触发 | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 选择快捷键可单测 | 单测 | text_field_pattern.cpp:1785 |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机软键盘 | 方向选择经 on_text_changed_listener | 单测 | — | on_text_changed_listener_impl.cpp:256 |
| 桌面硬键盘 | 全量 Shift/Ctrl+Shift | 单测 | — | — |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 键盘选择支持 | 全部 |

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
    query: "HandleSelect/HandleOnSelectAll 与 Ctrl+Shift+Home/End 异常"
```
**关键文档：** `frameworks/core/components_ng/pattern/text_field/text_field_pattern.cpp`
