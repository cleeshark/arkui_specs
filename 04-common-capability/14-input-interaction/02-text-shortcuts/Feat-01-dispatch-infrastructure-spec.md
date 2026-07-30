# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 文本快捷键分发基础设施 |
| 特性编号 | Func-04-14-02-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+（含 Mac KEY_META/numLock/PREVIEW 分支） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`02-text-shortcuts/design.md`
- 源码定位：`frameworks/core/common/ime/text_input_client.h/.cpp`、`frameworks/core/event/key_event.h/.cpp`、`key_code.h`

## 用户故事

### US-1: 分发器入口与顺序
作为开发者，我希望经 `TextInputClient::HandleKeyEvent` 按固定顺序分发键事件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 收到非 DOWN action THEN 忽略（UpdateShiftFlag 后） | 边界 |
| AC-1.2 | WHEN Ctrl+V 且 msg 非空 THEN 走特殊路径 InsertValue(msg) | 正常 |
| AC-1.3 | WHEN 无修饰或仅 SHIFT 且 ConvertCodeToString 返回字符 THEN InsertValue(value, isIME=true) | 正常 |
| AC-1.4 | WHEN functionKeys_ 命中(ESCAPE/TAB/Shift+TAB) THEN ResetOriginCaretPosition + 调用，返回 bool 可传播 | 正常 |
| AC-1.5 | WHEN keyboardShortCuts_ 命中 THEN IsShortCutBlocked 门控；Shift+UP/DOWN RecordOriginCaretPosition 否则 Reset；调用并消费 | 正常 |
| AC-1.6 | WHEN 无表命中 THEN 返回 false 放行 | 边界 |

### US-2: 修饰键与组合识别
作为开发者，我希望经 KeyComb/modKeyFlags 识别 Ctrl/Shift/Alt/Meta 组合。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN IsCtrlWith 检测 Ctrl THEN 命中 Ctrl 组合 | 正常 |
| AC-2.2 | WHEN Mac 平台 KEY_META THEN 镜像 Ctrl 命中同组合 | 正常 |
| AC-2.3 | WHEN numLock-off 小键盘 0-9/DOT THEN 重映射为对应编辑/导航键(+Ctrl/Shift 变体) | 正常 |

### US-3: 锚点与 Shift 同步
作为开发者，我希望 Shift 选择时锚点保持。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Shift+UP/DOWN THEN RecordOriginCaretPosition 保留锚点 | 正常 |
| AC-3.2 | WHEN 其他 keyboardShortCuts THEN ResetOriginCaretPosition | 正常 |
| AC-3.3 | WHEN UpdateShiftFlag THEN 同步 SelectionContainer 并切换拖拽 | 正常 |

### US-4: IME 合成边界
作为开发者，我希望 isPreIme 正确拦截 IME 合成。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN isPreIme 事件 THEN 不进入纯字符 InsertValue | 边界 |
| AC-4.2 | WHEN IsShortCutBlocked 返回 true THEN 跳过该组合 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TS-01 | 单测 | text_input_client.cpp:170 |
| AC-1.2 | R-2 | TASK-TS-01 | 单测 | text_input_client.cpp:179 |
| AC-1.3 | R-3 | TASK-TS-01 | 单测 | text_input_client.cpp:188 |
| AC-1.4 | R-4 | TASK-TS-01 | 单测 | text_input_client.cpp:197 |
| AC-1.5 | R-5 | TASK-TS-01 | 单测 | text_input_client.cpp:203 |
| AC-1.6 | R-6 | TASK-TS-01 | 单测 | text_input_client.cpp:216 |
| AC-2.1 | R-7 | TASK-TS-01 | 单测 | key_event.h:106 |
| AC-2.2 | R-7 | TASK-TS-01 | 单测 | text_input_client.cpp:39 |
| AC-2.3 | R-8 | TASK-TS-01 | 单测 | text_input_client.cpp:110 |
| AC-3.1 | R-9 | TASK-TS-01 | 单测 | text_input_client.cpp:206 |
| AC-3.2 | R-9 | TASK-TS-01 | 单测 | text_input_client.cpp:207 |
| AC-4.1 | R-10 | TASK-TS-01 | 单测 | key_event.h isPreIme |
| AC-4.2 | R-11 | TASK-TS-01 | 单测 | text_input_client.cpp IsShortCutBlocked |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 非 DOWN action | 忽略（先 UpdateShiftFlag） | — | AC-1.1 |
| R-2 | 行为 | Ctrl+V + msg 非空 | InsertValue(msg) 特殊路径 | — | AC-1.2 |
| R-3 | 行为 | 无修饰/仅 SHIFT + 可转换字符 | InsertValue(value, isIME=true) | — | AC-1.3 |
| R-4 | 行为 | functionKeys_ 命中 | ResetOriginCaretPosition + 调用，返回 bool 可传播 | ESCAPE/TAB/Shift+TAB | AC-1.4 |
| R-5 | 行为 | keyboardShortCuts_ 命中 | IsShortCutBlocked 门控；Shift+UP/DOWN Record 否则 Reset；消费 | ~70 组合 | AC-1.5 |
| R-6 | 边界 | 无表命中 | 返回 false 放行 | — | AC-1.6 |
| R-7 | 行为 | IsCtrlWith / Mac KEY_META | 识别 Ctrl/Meta 组合 | Mac 镜像 Ctrl | AC-2.1,2.2 |
| R-8 | 行为 | numLock-off 小键盘 | 重映射为编辑/导航键(+Ctrl/Shift) | 0-9/DOT | AC-2.3 |
| R-9 | 行为 | Shift 选择锚点 | Shift+UP/DOWN Record；其他 Reset；UpdateShiftFlag 同步 SelectionContainer | — | AC-3.1..3.3 |
| R-10 | 边界 | isPreIme | 不进入纯字符插入 | — | AC-4.1 |
| R-11 | 边界 | IsShortCutBlocked=true | 跳过该组合 | — | AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-6 分发顺序 | 单测 | 五级顺序 |
| VM-2 | R-7/R-8 平台分支 | 单测 | Mac/numLock |
| VM-3 | R-9 锚点 | 单测 | Record/Reset |
| VM-4 | R-10/R-11 边界 | 单测 | isPreIme/Blocked |

## API 变更分析
无公共 API。内部接口：`TextInputClient::HandleKeyEvent`、`KeyComb`、`CaretMoveIntent`、`functionKeys_`/`keyboardShortCuts_` 静态表、`IsShortCutBlocked`、`RecordOriginCaretPosition`/`ResetOriginCaretPosition`、`UpdateShiftFlag`。

## 接口规格

### 接口定义

**TextInputClient::HandleKeyEvent(keyEvent)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool HandleKeyEvent(const KeyEvent& keyEvent)` |
| 返回值 | `bool` — 是否消费 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1..1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| keyEvent | KeyEvent | 是 | — | action/pressedCodes/msg/isPreIme |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Ctrl+V+msg | InsertValue(msg) | AC-1.2 |
| 2 | functionKeys | 可传播 | AC-1.4 |
| 3 | shortCuts | 消费 | AC-1.5 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** API 8+；Mac KEY_META/numLock/PREVIEW 平台分支按平台演进
- **API 版本号策略:** 框架内部无公共 @since；标注平台分支行为

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 分发顺序敏感 | 五级顺序不可调换 | 全部 |
| 跨 4 组件共享 | Text/TextField/RichEditor/Search 复用 | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 加速表查表 O(log n) 无明显开销 | 性能测试 | text_input_client.cpp |
| 可测试性 | 分发顺序可单测 | 单测 | text_input_client.cpp |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 软键盘 DPAD 经 on_text_changed_listener | 单测 | — | on_text_changed_listener_impl.cpp |
| 平板/桌面外接键盘 | 硬键盘全量组合 | 单测 | — | — |
| Mac | KEY_META 镜像 Ctrl | 单测 | — | text_input_client.cpp:39 |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 键盘操作支持无障碍 | 全部 |

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
    query: "TextInputClient HandleKeyEvent 分发顺序与加速表"
```
**关键文档：** `frameworks/core/common/ime/text_input_client.cpp`
