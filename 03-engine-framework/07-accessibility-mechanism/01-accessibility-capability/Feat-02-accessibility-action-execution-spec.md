# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍动作执行 |
| 特性编号 | Func-03-07-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 13 起（NDK Provider 基线） |
| SIG 归属 | SIG_ApplicationFramework |
| 状态 | Draft |
| 复杂度 | 复杂 |

> 框架内部能力补录：当前实现即契约。所有行为结论可溯源至 ace_engine 源码（标注 `file:line`）。本 Feat 覆盖**系统无障碍服务请求的动作如何在组件上分发与执行**；动作集的**提供**在 Feat-01，事件上报在 Feat-07。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无障碍动作执行规格化 | 固化 SA→ExecuteAction→组件 的执行链路、布尔动作 vs 属性动作分发、disabled/IgnoreAllAction 双重门控、带参动作参数解析、NDK Provider 动作回调 |

## 输入文档

- 设计文档：`03-engine-framework/07-accessibility-mechanism/01-accessibility-capability/design.md`
- 源码定位：`adapter/ohos/osal/js_accessibility_manager.cpp`、`frameworks/core/components_ng/property/accessibility_property.cpp`、`frameworks/core/accessibility/native_interface_accessibility_provider.cpp`、`interfaces/native/native_interface_accessibility.h`

## 用户故事

### US-1: 系统无障碍服务在组件上执行动作

作为系统无障碍服务
我想要对指定节点下发动作（点击/长按/设值/滚动/复制等）并在组件上执行
以便辅助技术代替用户完成交互

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN SA 对 enabled 节点下发 CLICK THEN 经 `ConvertActionTypeToBoolen`→`ActClick` 执行手势点击，并在内部执行属性 `ActActionClick` 回调（结果取或） | 正常 |
| AC-1.2 | WHEN SA 下发 FOCUS / CLEAR_FOCUS THEN 调 `RequestFocus` / `LostFocus` 改变输入焦点 | 正常 |
| AC-1.3 | WHEN SA 下发 ACCESSIBILITY_FOCUS / CLEAR_ACCESSIBILITY_FOCUS THEN 调 `ActAccessibilityFocus` 设置/清除无障碍焦点 | 正常 |
| AC-1.4 | WHEN SA 下发带参动作（SET_TEXT/SET_SELECTION/SET_CURSOR_POSITION/SCROLL_*/SPAN_CLICK/CUSTOM/NEXT_TEXT/PREVIOUS_TEXT）THEN 经 `ActAccessibilityAction` 解析参数并分发到对应 `ActActionXxx` 属性回调 | 正常 |
| AC-1.5 | WHEN 动作到达 THEN 在 UI 线程执行（`PostTask` UI），结果异步经 `SetExecuteActionResult` 回写 SA | 正常 |

### US-2: 动作门控（disabled 与 IgnoreAllAction）

作为框架
我想要在节点禁用或预览态时正确门控动作
以避免在不可交互节点上执行副作用

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 节点 disabled（FocusHub::IsEnabled 为 false）且动作为 CLICK/SET_TEXT/SCROLL 等 THEN 拒绝执行返回 false | 异常 |
| AC-2.2 | WHEN 节点 disabled 且动作为 ACCESSIBILITY_FOCUS / CLEAR_ACCESSIBILITY_FOCUS THEN 仍放行执行 | 边界 |
| AC-2.3 | WHEN `IsIgnoreAllAction()` 为 true（预览 UIExtension 场景）且动作为 CLICK/SET_TEXT 等 THEN 拒绝执行 | 异常 |
| AC-2.4 | WHEN `IsIgnoreAllAction()` 为 true 且动作为 FOCUS / CLEAR_FOCUS THEN 仍放行 | 边界 |
| AC-2.5 | WHEN 虚拟节点容器收到非 ACCESSIBILITY_FOCUS/CLEAR_ACCESSIBILITY_FOCUS 动作 THEN 直接返回 false | 边界 |

### US-3: 动作执行期间的事件抑制

作为框架
我想要在执行动作期间临时抑制该节点的冗余变更事件
以避免与动作结果重复播报

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 执行非 SET_TEXT 动作 THEN 该节点的 TEXT_CHANGE/COMPONENT_CHANGE 事件被加入阻塞集，渲染后解除 | 正常 |
| AC-3.2 | WHEN 执行 SET_TEXT 动作 THEN 不进入事件阻塞（跳过） | 边界 |

### US-4: NDK Provider 动作执行

作为应用自绘组件自绘组件
我想要经 NDK Provider 接收并自行处理动作执行
以便为自绘内容提供交互

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN SA 经应用自绘组件路径下发动作 THEN `JsThirdProviderInteractionOperation::ExecuteAction` 调 provider→`ExecuteAccessibilityAction`，WithInstance 优先 | 正常 |
| AC-4.2 | WHEN 动作为 ACCESSIBILITY_FOCUS/CLEAR_ACCESSIBILITY_FOCUS 且经应用自绘组件路径 THEN 调 `ActThirdAccessibilityFocus` 画/清焦点框 | 正常 |
| AC-4.3 | WHEN 应用自绘组件路径转发 CLICK 动作 THEN 转发前剥离 `CLICK_ENHANCE_DATA`/`CLICK_TIMESTAMP` 安全组件参数 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-2 | TASK-2 | 单测（ActClick） | js_accessibility_manager.cpp:2576, 2604 |
| AC-1.2 | R-2 | TASK-2 | 单测 | js_accessibility_manager.cpp:8128, 2536 |
| AC-1.3 | R-2 | TASK-2 | 单测 | js_accessibility_manager.cpp:8145, 2762 |
| AC-1.4 | R-3 | TASK-2 | 单测（ActAccessibilityAction） | js_accessibility_manager.cpp:7990, 251 |
| AC-1.5 | R-1 | TASK-2 | 单测（线程切换） | js_accessibility_manager.cpp:7765, 8233 |
| AC-2.1 | R-4 | TASK-2 | 单测 | js_accessibility_manager.cpp:8108 |
| AC-2.2 | R-4 | TASK-2 | 单测 | js_accessibility_manager.cpp:8108 |
| AC-2.3 | R-5 | TASK-2 | 单测 | js_accessibility_manager.cpp:8079 |
| AC-2.4 | R-5 | TASK-2 | 单测 | js_accessibility_manager.cpp:8079 |
| AC-2.5 | R-6 | TASK-2 | 单测 | js_accessibility_manager.cpp:8197 |
| AC-3.1 | R-7 | TASK-2 | 单测 | js_accessibility_manager.cpp:7967 |
| AC-3.2 | R-7 | TASK-2 | 单测 | js_accessibility_manager.cpp:7971 |
| AC-4.1 | R-8 | TASK-2 | 单测 | js_third_provider_interaction_operation.cpp:695, 704 |
| AC-4.2 | R-8 | TASK-2 | 单测 | js_third_provider_interaction_operation.cpp:724 |
| AC-4.3 | R-9 | TASK-2 | 单测 | js_third_provider_interaction_operation.cpp:170 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | SA 在 UI 线程对节点执行动作 | `ExecuteActionNG`→先 `ConvertActionTypeToBoolen`（布尔/焦点动作），失败再 `ActAccessibilityAction`（属性动作兜底） | 结果异步回写 SA | AC-1.1, AC-1.5 |
| R-2 | 行为 | 布尔/焦点动作（FOCUS/CLEAR_FOCUS/CLICK/LONG_CLICK/ACCESSIBILITY_FOCUS/CLEAR_ACCESSIBILITY_FOCUS） | 由 `ConvertActionTypeToBoolen` 处理；CLICK 内部既执行手势点击又执行属性 `ActActionClick`（结果取或） | LONG_CLICK 仅手势，失败才属性兜底 | AC-1.1, AC-1.2, AC-1.3 |
| R-3 | 行为 | 带参动作（SET_TEXT/SET_SELECTION/SET_CURSOR_POSITION/SCROLL_*/SPAN_CLICK/CUSTOM/NEXT_TEXT/PREVIOUS_TEXT/COPY/CUT/PASTE/SELECT/CLEAR_SELECTION） | `ActAccessibilityAction` 按 key 解析参数填 `AccessibilityActionParam`，经 ACTIONS 分发表调 `ActActionXxx` | 缺参使用默认值（start/end=-1、dir=backward、moveUnit=STEP_CHARACTER、scrollType=SCROLL_DEFAULT、spanId=-1、setText=空） | AC-1.4 |
| R-4 | 边界 | 节点 `FocusHub::IsEnabled()` 为 false | 拒绝除 `ACCESSIBILITY_FOCUS`/`CLEAR_ACCESSIBILITY_FOCUS` 外的全部动作 | 无 FocusHub 时默认 enabled=true | AC-2.1, AC-2.2 |
| R-5 | 边界 | `IsIgnoreAllAction()` 为 true（预览 UIExtension） | 拒绝除 `FOCUS`/`CLEAR_FOCUS` 外的全部动作 | 例外动作组与 disabled 不同 | AC-2.3, AC-2.4 |
| R-6 | 边界 | 动作目标为虚拟节点容器且动作非 ACCESSIBILITY_FOCUS/CLEAR_ACCESSIBILITY_FOCUS | 直接返回 false | 虚拟节点仅响应无障碍焦点对 | AC-2.5 |
| R-7 | 行为 | 执行非 SET_TEXT 动作 | 该节点 TEXT_CHANGE/COMPONENT_CHANGE 加入 `blockerInAction_` 阻塞集，渲染后 `ResetBlockedEvent` 解除 | SET_TEXT 显式跳过阻塞 | AC-3.1, AC-3.2 |
| R-8 | 行为 | 应用自绘组件路径动作执行 | `ExecuteActionFromProvider`→provider→`ExecuteAccessibilityAction`，WithInstance 优先回退普通；ACCESSIBILITY_FOCUS 对先 `ActThirdAccessibilityFocus` 画框 | 未注册返回 NOT_REGISTERED | AC-4.1, AC-4.2 |
| R-9 | 边界 | 应用自绘组件路径转发 CLICK | `RemoveKeysForClickAction` 转发前剥离安全组件 hmac/timestamp 参数 | NG 自身 CLICK 路径仍消费这两个 key | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.x（执行链路） | 单元测试：`js_accessibility_manager_*` 动作执行用例 | 布尔/属性分发、CLICK 双执行、带参解析、UI 线程 |
| VM-2 | AC-2.x（门控） | 单元测试：disabled/IgnoreAllAction/虚拟节点门控 | 例外动作组差异 |
| VM-3 | AC-3.x（事件抑制） | 单元测试：`blockerInAction_` 阻塞/解除 | SET_TEXT 跳过 |
| VM-4 | AC-4.x（NDK Provider） | 单元测试：应用自绘组件路径动作分发 | WithInstance 优先、CLICK 参数剥离 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `executeAccessibilityAction` (@since13) | Public(NDK) | elementId, action, actionArguments, requestId | int32_t | ARKUI_ACCESSIBILITY_NATIVE_RESULT_* / NOT_REGISTERED | Provider 动作执行回调 | AC-4.1 |
| `OH_ArkUI_FindAccessibilityActionArgumentByKey` (@since13) | Public(NDK) | arguments, key, value* | int32_t | BAD_PARAMETER | 动作参数按键取值 | AC-1.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

> 应用侧动作参数 key（如 SET_TEXT/MOVE_UNIT 等）字面值定义在仓外 OHOS 无障碍 SDK 头文件，本仓仅引用。

## 接口规格

### 接口定义

**OH_ArkUI_FindAccessibilityActionArgumentByKey**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_FindAccessibilityActionArgumentByKey(ArkUI_AccessibilityActionArguments* arguments, const char* key, char** value)` |
| 返回值 | `int32_t` — 0 成功 |
| 开放范围 | Public (NDK, @since13) |
| 错误码 | BAD_PARAMETER（任一参数为 null） |
| 关联 AC | AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| arguments | ArkUI_AccessibilityActionArguments* | 是 | — | nullptr 返回 BAD_PARAMETER |
| key | const char* | 是 | — | nullptr 返回 BAD_PARAMETER |
| value | char** | 是 | — | 命中返回 c_str()，未命中返回 nullptr |

> L1 标准：动作执行分发链路行为同规则定义，此处不重复展开。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 13
- **API 版本号策略:** 保留既有 @since 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UI 线程单线程执行 | 动作在 UI 线程串行执行，结果异步回写 | AC-1.5 |
| 布尔动作优先属性动作兜底 | `ConvertActionTypeToBoolen` 失败才走 `ActAccessibilityAction` | AC-1.1, AC-1.4 |
| NG 为标准路径 | 旧 DOM 走 `AccessibilityActionEvent`，仅兼容 | AC-1.x |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可靠性 | disabled/IgnoreAllAction 节点动作不产生副作用 | 单测 | js_accessibility_manager.cpp:8108 |
| 可测试性 | 动作分发各层可独立单测 | 单测 | test/unittest/core/accessibility/ |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本特性即动作执行 | 全部 |
| 安全组件 | 是 | CLICK 安全组件 hmac 参数不透传应用自绘组件 | AC-4.3 |
| 多窗口/分屏 | 是 | UIExtension 预览态 IgnoreAllAction 门控 | AC-2.3 |
| 版本升级 | 是 | NDK @since13/15 | AC-4.x |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（动作执行；不含动作集提供 Feat-01、事件上报 Feat-07）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "JsAccessibilityManager::ExecuteActionNG 的门控与布尔/属性动作分发"
  - repo: "openharmony/arkui_ace_engine"
    query: "AceAction 枚举与 ConvertAceAction 映射表"
  - repo: "openharmony/arkui_ace_engine"
    query: "JsThirdProviderInteractionOperation::ExecuteAction 应用自绘组件动作分发与 CLICK 参数剥离"
```

**关键文档：** design.md（同目录）、`interfaces/native/native_interface_accessibility.h`
