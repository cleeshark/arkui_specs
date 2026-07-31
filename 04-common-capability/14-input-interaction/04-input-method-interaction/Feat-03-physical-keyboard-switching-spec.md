# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 实体键盘切换（契约 + 外部 IME 框架，经全仓检索确认） |
| 特性编号 | Func-04-14-04-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 低（本仓仅契约面；实体键盘检测经全仓检索确认不在本仓，属外部 IME 框架） |

## 本次变更范围（Delta）
重定范围补录。本 Feat 覆盖本仓与 IME 的面板状态契约 + 物理键路由路径；实体键盘检测经全仓检索（frameworks/+adapter/+interfaces/，排除 test/docs/site）确认不在本仓，属外部 `MiscServices::InputMethodController`（IME 框架）。

## 输入文档
- 设计文档：`04-input-method-interaction/design.md`
- 源码定位：`text_field_pattern.cpp`(RequestKeyboard→`MiscServices::InputMethodController::Attach`+`attachOptions.isShowKeyboard`)、`on_text_changed_listener_impl.cpp`(NotifyPanelStatusInfo/SetKeyboardStatus/NotifyKeyboardHeight/SendKeyEventFromInputMethod)、`text_input_client.h`(HandleKeyEvent)

## 用户故事

### US-1: 面板状态契约（出站）
作为开发者，我希望经 attachOptions.isShowKeyboard 告知 IME 是否需面板。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN RequestKeyboard THEN `attachOptions.isShowKeyboard = needShowSoftKeyboard` 传 IME（text_field_pattern.cpp:5970-5971） | 正常 |
| AC-1.2 | WHEN isShowKeyboard=false THEN 不主动拉面板（IME/实体键盘场景决定） | 边界 |

### US-2: 面板状态消费（入站）
作为开发者，我希望消费 IME 的面板/键盘状态通知（ace 被告知而非决策）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN NotifyPanelStatusInfo THEN 追踪 IME show 状态（含 visible/SetImeShow，on_text_changed_listener_impl.cpp:332/341） | 正常 |
| AC-2.2 | WHEN SetKeyboardStatus(hide)/SendKeyboardStatus THEN NotifyKeyboardHeight(0)（:83/92/142/167） | 正常 |
| AC-2.3 | WHEN NotifyKeyboardHeight(height) THEN 更新键盘高度（:150/157） | 正常 |

### US-3: 物理键路由
作为开发者，我希望实体键盘事件经焦点管道进入输入框。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 实体键盘按下 THEN FocusHub→pattern::OnKeyEvent→TextInputClient::HandleKeyEvent（text_input_client.h:164） | 正常 |
| AC-3.2 | WHEN IME 经 SendKeyEventFromInputMethod 转发 THEN 空{}（on_text_changed_listener_impl.cpp:140，IME 不经此转发键） | 边界 |

### US-4: 实体键盘检测（经全仓检索确认不在本仓）
作为开发者/测试，我需知道实体键盘检测的责任归属（经代码仓确认，非推测）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 全仓检索实体键盘检测标识（IsPhysicalKeyboard/HasPhysicalKeyboard/physicalKeyboard/hardwareKeyboard/InputDeviceManager/InputDeviceType/GetInputDevice/KEYBOARD device 等）THEN frameworks/+adapter/+interfaces/（排除 test/docs/site）均无匹配——确认本仓无实体键盘检测实现 | 边界 |
| AC-4.2 | WHEN ace 附挂 IME THEN 经 `MiscServices::InputMethodController::GetInstance()->Attach(listener, attachOptions, textConfig, INNER_KIT_ARKUI)`（text_field_pattern.cpp:2547/2576/5974），仅传 `attachOptions.isShowKeyboard=needShowSoftKeyboard`（:5970-5971），不基于实体键盘检测计算该值 | 正常 |
| AC-4.3 | WHEN IME 框架据是否接实体键盘决定是否弹软面板 THEN ace 经入站通知得知结果：NotifyPanelStatusInfo/SendKeyboardStatus/SetKeyboardStatus/NotifyKeyboardHeight（on_text_changed_listener_impl.cpp:341/142/83/150） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-KC-03 | 单测 | text_field_pattern.cpp:5970-5971 |
| AC-2.1 | R-2 | TASK-KC-03 | 单测 | on_text_changed_listener_impl.cpp:341 |
| AC-2.2 | R-2 | TASK-KC-03 | 单测 | on_text_changed_listener_impl.cpp:83/92/142/167 |
| AC-3.1 | R-3 | TASK-KC-03 | 单测 | text_input_client.h:164 |
| AC-3.2 | R-4 | TASK-KC-03 | 单测 | on_text_changed_listener_impl.cpp:140 |
| AC-4.1 | R-5 | TASK-KC-03 | 全仓检索确认 | 全仓 grep 无 IsPhysicalKeyboard/InputDeviceManager 等 |
| AC-4.2 | R-5 | TASK-KC-03 | 单测 | text_field_pattern.cpp:2547/2576/5970-5974 |
| AC-4.3 | R-5 | TASK-KC-03 | 单测 | on_text_changed_listener_impl.cpp:341/142/83/150 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | RequestKeyboard | attachOptions.isShowKeyboard 传 IME | needShowSoftKeyboard 入参直传 | AC-1.1,1.2 |
| R-2 | 行为 | NotifyPanelStatusInfo/SetKeyboardStatus/NotifyKeyboardHeight | 追踪/消费面板状态与高度 | 入站回调，ace 被告知 | AC-2.1..2.3 |
| R-3 | 行为 | 实体键盘按下 | FocusHub→OnKeyEvent→HandleKeyEvent | 焦点管道 | AC-3.1 |
| R-4 | 边界 | SendKeyEventFromInputMethod | 空{}，IME 不转发键 | — | AC-3.2 |
| R-5 | 边界 | 实体键盘检测 | 经全仓检索确认本仓无实现；键盘显示决策属外部 `MiscServices::InputMethodController`；ace 仅传 isShowKeyboard + 消费入站状态通知 | 全仓 grep 无匹配；Attach:text_field_pattern.cpp:5974；入站:on_text_changed_listener_impl.cpp | AC-4.1..4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 出站 isShowKeyboard | 单测 | attach 标志直传 |
| VM-2 | R-2 入站状态 | 单测 | 面板/高度 |
| VM-3 | R-3/R-4 路由 | 单测 | 焦点管道 + 空转发 |
| VM-4 | R-5 实体键盘检测归属 | 全仓检索确认 | 无本仓检测实现 + Attach+入站证据链 |

## API 变更分析
无公共 API。内部：`attachOptions.isShowKeyboard`、`MiscServices::InputMethodController::Attach`（外部 IME 框架，INNER_KIT_ARKUI）、`OnTextChangedListenerImpl::NotifyPanelStatusInfo/SetKeyboardStatus/SendKeyboardStatus/NotifyKeyboardHeight/SendKeyEventFromInputMethod`、`TextInputClient::HandleKeyEvent`。边界：物理键快捷键分发归 04-14-02；实体键盘检测经全仓检索确认不在本仓，属外部 `MiscServices::InputMethodController`（IME 框架决策软面板显隐）。

## 接口规格

### 接口定义

**attachOptions.isShowKeyboard（出站契约）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `attachOptions.isShowKeyboard = needShowSoftKeyboard` |
| 返回值 | — |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isShowKeyboard | bool | 是 | — | false 时不主动拉面板；实际显隐由 IME 框架决定 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | isShowKeyboard=true | ace 传 true，IME 决定面板（含实体键盘场景抑制） | AC-1.1 |
| 2 | IME 通知面板状态 | ace 消费 | AC-2.1 |
| 3 | 实体键按下 | 焦点管道 | AC-3.1 |
| 4 | 全仓检索检测标识 | 无匹配（确认不在本仓） | AC-4.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 框架内部无 @since；实体键盘检测归属经全仓检索确认（不在本仓，属外部 IME 框架）

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 检测不在本仓（确认） | 经全仓检索确认无实体键盘检测实现；决策属外部 `MiscServices::InputMethodController` | AC-4.1..4.3 |
| ace 仅契约面 | 传 isShowKeyboard + 消费入站状态 | 全部 |
| 物理键路由与 04-14-02 共用 | HandleKeyEvent 契约 | AC-3.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 面板状态消费可单测 | 单测 | on_text_changed_listener_impl.cpp |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 软键盘为主 | 单测 | — | — |
| 桌面/外接键盘 | 物理键路由为主；软面板显隐由外部 IME 决定 | 单测 | — | FocusHub + InputMethodController |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 物理键支持无障碍 | AC-3.1 |

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
    query: "isShowKeyboard 出站 + NotifyPanelStatusInfo/SetKeyboardStatus 入站 + 实体键路由 + 实体键盘检测全仓检索"
```
**关键文档：** `frameworks/core/components_ng/pattern/text_field/text_field_pattern.cpp`、`frameworks/core/components_ng/pattern/text_field/on_text_changed_listener_impl.cpp`
