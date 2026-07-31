# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | IME 框架交互与弹出收起控制 |
| 特性编号 | Func-04-14-04-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8–12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准-复杂 |

## 本次变更范围（Delta）
重定范围补录（替换此前错误范围的焦点遍历 Feat-01）。本 Feat 覆盖 IME 框架交互与弹出/收起控制。

## 输入文档
- 设计文档：`04-input-method-interaction/design.md`
- 源码定位：`frameworks/core/common/ime/input_method_manager.h`、`adapter/ohos/osal/input_method_manager_ohos.cpp`、`text_field_pattern.cpp`(RequestKeyboard/CloseKeyboard)、`rich_editor_pattern.cpp`、`search_pattern.cpp`、`text_field_event_hub.h`/`rich_editor_event_hub.h`(onWillAttachIME)

## 用户故事

### US-1: 框架驱动收起（HIDE）
作为开发者，我希望焦点变化/场景切换时框架自动收起键盘。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 焦点节点变化 THEN OnFocusNodeChange→ManageFocusNode 编排 | 正常 |
| AC-1.2 | WHEN 失焦且非保留 THEN ProcessKeyboard/ProcessKeyboardInWindowScene→CloseKeyboard(focusNode) | 正常 |
| AC-1.3 | WHEN 窗口场景切换 THEN lastKeep_ 保留/SCB 焦点交接 | 正常 |
| AC-1.4 | WHEN UIExtension 跨进程 THEN HideKeyboardAcrossProcesses | 正常 |
| AC-1.5 | WHEN 模态页失焦 THEN ProcessModalPageScene | 正常 |
| AC-1.6 | WHEN pipeline 销毁 THEN CloseKeyboardInPipelineDestroy | 边界 |
| AC-1.7 | WHEN 离开文本编辑 tag THEN CloseCustomKeyboard(true) | 正常 |

### US-2: 输入框驱动弹出（SHOW）
作为开发者，我希望输入框聚焦时主动 Attach IME。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN RequestKeyboard 且 showKeyBoardOnFocus_+HasFocus+NeedSoftKeyboard THEN 创建 OnTextChangedListenerImpl+GetIMEClientInfo | 正常 |
| AC-2.2 | WHEN 自定义键盘 THEN RequestCustomKeyboard 而非标准 Attach | 正常 |
| AC-2.3 | WHEN 标准 THEN FireOnWillAttachIME(attach 前)→inputMethod->Attach(listener,options,textConfig,INNER_KIT_ARKUI) | 正常 |
| AC-2.4 | WHEN 跨平台 THEN RequestKeyboardCrossPlatForm→InputMethodManager::Attach | 正常 |
| AC-2.5 | WHEN attachOptions.isShowKeyboard=false THEN 不主动拉起面板（IME 决定） | 边界 |

### US-3: 输入框关闭
作为开发者，我希望经 CloseKeyboard 主动关闭。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN TextFieldPattern::CloseKeyboard THEN custom→CloseCustomKeyboard；标准→inputMethod->Close() | 正常 |
| AC-3.2 | WHEN RichEditorPattern::CloseKeyboard THEN 同上 | 正常 |
| AC-3.3 | WHEN 跨平台 THEN InputMethodManager::CloseKeyboard(instanceId) | 正常 |

### US-4: onWillAttachIME 回调
作为开发者，我希望在 IME attach 前经 onWillAttachIME 拦截/配置。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN Attach 前 THEN FireOnWillAttachIME(IMEClient{nodeId,extraInfo}) | 正常 |
| AC-4.2 | WHEN 仅 onWillAttachIME 已实现 THEN 无 Will-Detach/Did-Attach（按实现记录） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-KC-01 | 单测 | input_method_manager_ohos.cpp:58 |
| AC-1.2 | R-2 | TASK-KC-01 | 单测 | input_method_manager_ohos.cpp:191/317 |
| AC-1.4 | R-3 | TASK-KC-01 | 单测 | input_method_manager_ohos.cpp:333 |
| AC-1.6 | R-4 | TASK-KC-01 | 单测 | input_method_manager_ohos.cpp:303 |
| AC-2.1 | R-5 | TASK-KC-01 | 单测 | text_field_pattern.cpp:5907 |
| AC-2.3 | R-6 | TASK-KC-01 | 单测 | text_field_pattern.cpp:5937/5974 |
| AC-3.1 | R-7 | TASK-KC-01 | 单测 | text_field_pattern.cpp:6170 |
| AC-4.1 | R-8 | TASK-KC-01 | 单测 | text_field_pattern.cpp:13482 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 焦点节点变化 | OnFocusNodeChange→ManageFocusNode 编排 | 容器为 IME 时 bail | AC-1.1 |
| R-2 | 行为 | 失焦非保留 | ProcessKeyboard/WindowScene→CloseKeyboard(focusNode) | NeedSoftKeyboard 判定 | AC-1.2 |
| R-3 | 行为 | UIExtension 跨进程 | HideKeyboardAcrossProcesses | systemWindowId/displayId | AC-1.4 |
| R-4 | 边界 | pipeline 销毁 | CloseKeyboardInPipelineDestroy | — | AC-1.6 |
| R-5 | 行为 | RequestKeyboard 聚焦 | OnTextChangedListenerImpl+GetIMEClientInfo | showKeyBoardOnFocus_+HasFocus+NeedSoftKeyboard | AC-2.1 |
| R-6 | 行为 | 标准 attach | FireOnWillAttachIME→inputMethod->Attach | isShowKeyboard 标志 | AC-2.3,2.5 |
| R-7 | 行为 | CloseKeyboard | custom→CloseCustomKeyboard；标准→Close() | — | AC-3.1,3.2 |
| R-8 | 行为 | onWillAttachIME | attach 前 fire IMEClient | 仅 Will-attach 实现 | AC-4.1,4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-4 框架 HIDE | 单测 | 焦点/场景编排 |
| VM-2 | R-5..R-7 输入框 SHOW/CLOSE | 单测 | RequestKeyboard/CloseKeyboard |
| VM-3 | R-8 onWillAttachIME | 单测 | attach 前 fire |

## API 变更分析
公共 API：`onWillAttachIME(Callback<IMEClient>)`（@since 12 动态/@since 23 静态）、`onEditChange`(@since 8)、`enableKeyboardOnFocus`(@since 10)（语义归本域，见 Feat-05）。内部：InputMethodManager::*、TextFieldPattern::RequestKeyboard/CloseKeyboard、FireOnWillAttachIME。

## 接口规格

### 接口定义

**RequestKeyboard(isFocusViewChanged, needStartTwinkling, needShowSoftKeyboard, sourceType)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void RequestKeyboard(bool isFocusViewChanged, bool needStartTwinkling, bool needShowSoftKeyboard, RequestKeyboardReason sourceType)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| needShowSoftKeyboard | bool | 是 | — | isShowKeyboard 传 IME |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 聚焦+showKeyBoardOnFocus | Attach IME | AC-2.1 |
| 2 | 自定义键盘 | RequestCustomKeyboard | AC-2.2 |
| 3 | isShowKeyboard=false | 不拉面板 | AC-2.5 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** onWillAttachIME @since 12/23；enableKeyboardOnFocus/onEditChange @since 8–10/23
- **API 版本号策略:** 公共 API 全量 @since 标注（@since 源自 03-text-interaction design + modifier bridge，需外部 SDK 仓确认）

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SHOW 输入框驱动 / HIDE 框架驱动 | 双向职责 | 全部 |
| adapter 分发 | InputMethodManager 跨平台/ohos/preview | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可靠性 | pipeline 销毁关闭键盘 | 单测 | CloseKeyboardInPipelineDestroy |
| 可测试性 | show/hide 可单测 | 单测 | input_method_manager_ohos.cpp |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 跨平台 | InputMethodManager::Attach 跨平台 | 单测 | — | input_method_manager.h:53 |
| OHOS | MiscServices::InputMethodController | 单测 | — | input_method_manager_ohos.cpp |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口 | 是 | 窗口场景焦点交接 | AC-1.3 |

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
    query: "InputMethodManager 焦点驱动 show/hide 与 RequestKeyboard/Attach/onWillAttachIME"
```
**关键文档：** `frameworks/core/common/ime/input_method_manager.h`、`adapter/ohos/osal/input_method_manager_ohos.cpp`
