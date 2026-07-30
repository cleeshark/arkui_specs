# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 键盘输入处理契约 |
| 特性编号 | Func-04-14-04-Feat-04 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
重定范围补录。本 Feat 覆盖 IME→输入框处理契约（TextInputClient 抽象 + OnTextChangedListenerImpl 桥）。

## 输入文档
- 设计文档：`04-input-method-interaction/design.md`
- 源码定位：`frameworks/core/common/ime/text_input_client.h`、`frameworks/core/components_ng/pattern/text_field/on_text_changed_listener_impl.h/.cpp`、`text_editing_value.h`/`text_compose.h`

## 用户故事

### US-1: TextInputClient 抽象契约
作为开发者，我希望 IME 框架经 TextInputClient 调入输入框。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN IME 插入文本 THEN UpdateEditingValue/InsertValue(isIME) | 正常 |
| AC-1.2 | WHEN 删除 THEN DeleteBackward/DeleteForward | 正常 |
| AC-1.3 | WHEN 查询光标文 THEN GetLeft/RightTextOfCursor/GetTextIndexAtCursor | 正常 |
| AC-1.4 | WHEN 设置选区 THEN HandleSetSelection/SetSelection | 正常 |
| AC-1.5 | WHEN 扩展动作 THEN HandleExtendAction | 正常 |
| AC-1.6 | WHEN 键盘状态 THEN SetInputMethodStatus/NotifyKeyboardClosed* | 正常 |
| AC-1.7 | WHEN 物理键 THEN HandleKeyEvent（与 04-14-02 共用） | 正常 |
| AC-1.8 | WHEN 预览文本 THEN SetPreviewText/FinishTextPreview | 正常 |

### US-2: OnTextChangedListenerImpl 桥
作为开发者，我希望经 OnTextChangedListenerImpl 桥接 IME→TextInputClient（跨线程）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN InsertText THEN PostTaskToUI→client->InsertValue(isIME=true) | 正常 |
| AC-2.2 | WHEN DeleteBackward/DeleteForward THEN →client->DeleteBackward/Forward | 正常 |
| AC-2.3 | WHEN MoveCursor(Direction) THEN 映射 CaretMoveIntent→CursorMove/HandleSelect | 正常 |
| AC-2.4 | WHEN HandleSelect(keyCode) THEN DPAD→CaretMoveIntent→HandleSelect | 正常 |
| AC-2.5 | WHEN HandleSetSelection/HandleExtendAction THEN 转发 client | 正常 |
| AC-2.6 | WHEN SetPreviewText/FinishTextPreview THEN 转发 | 正常 |
| AC-2.7 | WHEN ReceivePrivateCommand/AutoFillReceivePrivateCommand THEN 处理（与 04-14-05 交叉） | 正常 |
| AC-2.8 | WHEN OnDetach THEN IME detach 回调 | 正常 |
| AC-2.9 | WHEN 任意 IME 回调 THEN PostTaskToUI 跨线程 | 边界 |

### US-3: 合成态
作为开发者，我希望经 text_editing_value/text_compose 维护 IME 合成态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN FinishComposing THEN 仅 CROSS_PLATFORM InputMethodManager 提供 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-KC-04 | 单测 | text_input_client.h:92/98 |
| AC-1.4 | R-1 | TASK-KC-04 | 单测 | text_input_client.h:123/252 |
| AC-1.7 | R-1 | TASK-KC-04 | 单测 | text_input_client.h:164 |
| AC-2.1 | R-2 | TASK-KC-04 | 单测 | on_text_changed_listener_impl.cpp:32/44 |
| AC-2.3 | R-3 | TASK-KC-04 | 单测 | on_text_changed_listener_impl.cpp:199/284 |
| AC-2.4 | R-3 | TASK-KC-04 | 单测 | on_text_changed_listener_impl.cpp:256/284 |
| AC-2.7 | R-4 | TASK-KC-04 | 单测 | on_text_changed_listener_impl.cpp:445/382 |
| AC-2.8 | R-2 | TASK-KC-04 | 单测 | on_text_changed_listener_impl.cpp:524 |
| AC-2.9 | R-5 | TASK-KC-04 | 单测 | on_text_changed_listener_impl.cpp:289 |
| AC-3.1 | R-6 | TASK-KC-04 | 单测 | input_method_manager.h:58 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | TextInputClient 抽象 | IME 调入（UpdateEditingValue/Insert/Delete/Select/KeyEvent/Preview） | isIME 标志 | AC-1.1..1.8 |
| R-2 | 行为 | OnTextChangedListenerImpl 桥 | InsertText/Delete/Selection/ExtendAction/Preview/Detach 转发 | PostTaskToUI | AC-2.1,2.5,2.6,2.8 |
| R-3 | 行为 | MoveCursor/HandleSelect | Direction/keyCode→CaretMoveIntent→CursorMove/HandleSelect | DPAD 映射 | AC-2.3,2.4 |
| R-4 | 行为 | PrivateCommand | ReceivePrivateCommand/AutoFillReceivePrivateCommand | 与 04-14-05 交叉 | AC-2.7 |
| R-5 | 边界 | 跨线程 | 所有 IME 回调 PostTaskToUI | UI 线程 | AC-2.9 |
| R-6 | 边界 | FinishComposing | 仅 CROSS_PLATFORM InputMethodManager | — | AC-3.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 TextInputClient 契约 | 单测 | IME 调入面 |
| VM-2 | R-2..R-5 桥 + 跨线程 | 单测 | PostTaskToUI |
| VM-3 | R-3 方向映射 | 单测 | CaretMoveIntent |
| VM-4 | R-6 FinishComposing | 单测 | CROSS_PLATFORM |

## API 变更分析
无公共 API。内部：`TextInputClient`（UpdateEditingValue/PerformAction/InsertValue(isIME)/DeleteBackward/Forward/SetInputMethodStatus/NotifyKeyboardClosed*/NotifyKeyboardHeight/GetLeft-RightTextOfCursor/GetTextIndexAtCursor/HandleSetSelection/HandleExtendAction/HandleKeyEvent/CursorMove/HandleSelect/HandleSelectExtend/SetSelection/DeleteRange/SetPreviewText/FinishTextPreview）、`OnTextChangedListenerImpl`（InsertText/Delete/MoveCursor/HandleSelect/HandleSetSelection/HandleExtendAction/SetKeyboardStatus/NotifyKeyboardHeight/NotifyPanelStatusInfo/SetPreviewText/FinishTextPreview/ReceivePrivateCommand/OnDetach）、`text_editing_value`/`text_compose`。边界：快捷键表归 04-14-02；编辑拦截回调（onWillInsert 等）归 04-14-03 Feat-04（消费本契约）。

## 接口规格

### 接口定义

**TextInputClient::InsertValue(value, isIME)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void InsertValue(const std::u16string& value, bool isIME)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | u16string | 是 | — | 插入文本 |
| isIME | bool | 是 | false | true=IME 来源 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | IME InsertText | PostTaskToUI→InsertValue(isIME=true) | AC-2.1 |
| 2 | IME Delete | DeleteBackward | AC-2.2 |
| 3 | 物理键 | HandleKeyEvent | AC-1.7 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 框架内部无 @since

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 跨线程 PostTaskToUI | IME 回调线程→UI | AC-2.9 |
| 与 04-14-02 共用 HandleKeyEvent | 物理键路径 | AC-1.7 |
| 编辑拦截回调归 04-14-03 Feat-04 | 本域拥有契约 | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 跨线程无丢失 | 单测 | PostTaskToUI |
| 可测试性 | 桥可单测 | 单测 | on_text_changed_listener_impl.cpp |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | IME 输入支持 | 全部 |

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
    query: "TextInputClient 抽象 + OnTextChangedListenerImpl IME→输入框桥"
```
**关键文档：** `frameworks/core/common/ime/text_input_client.h`、`frameworks/core/components_ng/pattern/text_field/on_text_changed_listener_impl.cpp`
