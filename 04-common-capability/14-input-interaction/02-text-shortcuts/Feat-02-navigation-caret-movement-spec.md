# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 导航与光标移动快捷键 |
| 特性编号 | Func-04-14-02-Feat-02 |
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
- 源码定位：`text_field_pattern.cpp`(CursorMove/HandleSelect/PageUp-Down)、`text_input_client.cpp`(加速表 DPAD/MOVE_HOME/END/Ctrl 变体)、`rich_editor_pattern.cpp`(CursorMove)

## 用户故事

### US-1: 方向键光标移动
作为开发者，我希望经方向键移动光标。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN DPAD_LEFT/RIGHT/UP/DOWN THEN CursorMove(Left/Right/Up/Down) | 正常 |
| AC-1.2 | WHEN MOVE_HOME/END THEN CursorMove(LineBegin/LineEnd) | 正常 |

### US-2: 词/段落/文档级移动
作为开发者，我希望经 Ctrl 组合跨词/段落/文档移动。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Ctrl+DPAD_LEFT/RIGHT THEN CursorMove(LeftWord/RightWord) | 正常 |
| AC-2.2 | WHEN Ctrl+DPAD_UP/DOWN THEN CursorMove(ParagraghBegin/ParagraghEnd) | 正常 |
| AC-2.3 | WHEN Ctrl+MOVE_HOME/END THEN CursorMove(Home/End) | 正常 |

### US-3: 翻页
作为开发者，我希望经 PageUp/Down 翻页并重定位光标。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN PAGE_UP THEN HandleOnPageUp（IsTextArea 门控，滚动+光标重定位） | 正常 |
| AC-3.2 | WHEN PAGE_DOWN THEN HandleOnPageDown | 正常 |
| AC-3.3 | WHEN 非 TextArea(单行) THEN PageUp/Down 不滚动 | 边界 |

### US-4: 焦点外移
作为开发者，我希望光标到边界时方向键焦点外移。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN directionKeysMoveFocusOut_ 且光标在边界 THEN 方向键焦点外移（IsMoveFocusOutFromLeft/Right） | 正常 |

### US-5: RTL 与单行/多行
作为开发者，我希望 RTL 与单行/多行行为正确。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN RTL THEN 左/右方向语义交换 | 正常 |
| AC-5.2 | WHEN 单行 TextInput THEN 上下方向不跨行 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TS-02 | 单测 | text_field_pattern.cpp:1728 |
| AC-1.2 | R-1 | TASK-TS-02 | 单测 | text_input_client.cpp 加速表 |
| AC-2.1 | R-2 | TASK-TS-02 | 单测 | text_input_client.cpp |
| AC-2.3 | R-2 | TASK-TS-02 | 单测 | text_input_client.cpp |
| AC-3.1 | R-3 | TASK-TS-02 | 单测 | text_field_pattern.cpp:7847 |
| AC-3.3 | R-3 | TASK-TS-02 | 单测 | — |
| AC-4.1 | R-4 | TASK-TS-02 | 单测 | text_field_pattern.cpp:2145 |
| AC-5.1 | R-5 | TASK-TS-02 | 单测 | — |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | DPAD_*/MOVE_HOME/END | CursorMove(对应方向/LineBegin/End) | 12 CaretMoveIntent | AC-1.1,1.2 |
| R-2 | 行为 | Ctrl+DPAD/MOVE_HOME/END | CursorMove(Word/Paragragh/Home/End) | Ctrl 修饰 | AC-2.1..2.3 |
| R-3 | 行为 | PAGE_UP/DOWN | HandleOnPageUp/Down（IsTextArea 门控） | 单行不滚动 | AC-3.1..3.3 |
| R-4 | 行为 | 方向键到边界 + directionKeysMoveFocusOut_ | 焦点外移 | IsMoveFocusOutFromLeft/Right | AC-4.1 |
| R-5 | 行为 | RTL / 单行 | 左右语义交换；单行不跨行 | — | AC-5.1,5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 12 方向 | 单测 | CaretMoveIntent 映射 |
| VM-2 | R-3 翻页 | 单测 | IsTextArea 门控 |
| VM-3 | R-4 焦点外移 | 单测 | directionKeysMoveFocusOut_ |
| VM-4 | R-5 RTL | 单测 | 语义交换 |

## API 变更分析
无公共 API。内部：`CursorMove(CaretMoveIntent)`、12 `CursorMoveXxx`、`HandleOnPageUp/Down`、`GetWordLength`、`directionKeysMoveFocusOut_`、`IsMoveFocusOutFromLeft/Right`。

## 接口规格

### 接口定义

**CursorMove(intent)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void CursorMove(CaretMoveIntent intent)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| intent | CaretMoveIntent | 是 | — | 12 枚举值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | DPAD_LEFT | 左移 | AC-1.1 |
| 2 | Ctrl+DPAD_LEFT | 左移一词 | AC-2.1 |
| 3 | 单行+UP | 不跨行 | AC-5.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 框架内部无 @since

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 焦点外移边界 | 与 04-keyboard-control 衔接 | AC-4.1 |
| IsTextArea 门控 | 单行/多行差异 | AC-3.3 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 12 方向可单测 | 单测 | text_field_pattern.cpp:1728 |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机软键盘 | DPAD 经 on_text_changed_listener | 单测 | — | on_text_changed_listener_impl.cpp:256 |
| 桌面硬键盘 | 全量方向/词/段落 | 单测 | — | — |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 键盘导航支持 | 全部 |

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
    query: "CursorMove 12 方向与 PageUp/Down/焦点外移"
```
**关键文档：** `frameworks/core/components_ng/pattern/text_field/text_field_pattern.cpp`
