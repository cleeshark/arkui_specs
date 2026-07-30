# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 应用自绘组件无障碍接入（NDK Provider） |
| 特性编号 | Func-03-07-01-Feat-06 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 13 起（Custom @since23） |
| SIG 归属 | SIG_ApplicationFramework |
| 状态 | Draft |
| 复杂度 | 复杂 |

> 框架内部能力补录：当前实现即契约。本 Feat 覆盖**应用自绘组件（XComponent/Custom）经 NDK Accessibility Provider 接入系统无障碍的注册、C API 获取与查询/动作/分发限制**；子树挂载管道（ChildTree）与跨进程组件（Form/UIExtension/Isolated/Web）见 **Feat-05**，元素字段填充见 Feat-01、动作执行见 Feat-02、事件上报见 Feat-07。
>
> **术语**：本规格中"**应用自绘组件**"特指经 NDK Accessibility Provider 接入的 ArkUI 应用内 Native 自绘节点，即 `XComponent` 与 `ARKUI_NODE_CUSTOM`（Custom），**不含**系统级跨进程组件（Form/UIExtension/Isolated/Web，见 Feat-05）。代码标识符（`JsThirdProviderInteractionOperation`、`ThirdAccessibilityManager`、`JS_THIRD_PROVIDER` 等）中的 "Third" 为历史命名，对应即"应用自绘组件"。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 应用自绘组件 NDK Provider 接入规格化 | 固化 Provider 注册流程、NDK Provider C API 获取（仅 Custom）、自绘路径查询/动作分发限制（REDUCED 降级、坐标叠加、叶子 no-op） |

## 输入文档

- 设计文档：`03-engine-framework/07-accessibility-mechanism/01-accessibility-capability/design.md`
- 源码定位：`adapter/ohos/osal/js_third_provider_interaction_operation.*`、`adapter/ohos/osal/js_accessibility_manager.cpp`、`frameworks/core/accessibility/native_interface_accessibility_provider.cpp`、`frameworks/core/pattern/xcomponent/xcomponent_pattern.cpp`、`frameworks/core/pattern/custom/custom_pattern.cpp`

## 用户故事

### US-1: 应用自绘组件 Provider 注册流程（XComponent/Custom）

作为应用自绘组件
我想要注册 Provider + SessionAdapter 作为子树接入系统无障碍
以便提供自绘无障碍树

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN XComponent/Custom 的 ChildTreeCallback OnRegister 触发 THEN 创建 AccessibilityProvider + SessionAdapter，构造 `Registration{JS_THIRD_PROVIDER, hostNode, provider}` 调 `RegisterInteractionOperationAsChildTree` | 正常 |
| AC-1.2 | WHEN Registration.operatorType=JS_THIRD_PROVIDER THEN `RegisterThirdProviderInteractionOperationAsChildTree` 构造 `JsThirdProviderInteractionOperation`，回灌 ThirdAccessibilityManager，注册到 hover 管理器与系统 SA | 正常 |
| AC-1.3 | WHEN 注销 THEN `OnAccessibilityChildTreeDeregister` 清 InnerProvider/SessionAdapter/Provider，调 `DeregisterInteractionOperationAsChildTree` | 正常 |
| AC-1.4 | WHEN callback 先挂后注册（或反之） THEN 双向补偿：已注册则立即 OnRegister；注册成功广播 NotifyChildTreeOnRegister | 边界 |

### US-2: NDK Provider 获取（仅 Custom）

作为 Native 开发者
我想要从 ArkUI_NodeHandle 取得无障碍 Provider
以便用 C API 注册自定义无障碍树

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `OH_ArkUI_NativeModule_GetNativeAccessibilityProvider` 节点为 ARKUI_NODE_CUSTOM THEN 返回 Provider 句柄 | 正常 |
| AC-2.2 | WHEN 节点类型非 ARKUI_NODE_CUSTOM THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID | 异常 |
| AC-2.3 | WHEN Provider 句柄同时注册 WithInstance 与普通回调 THEN 查询/动作/事件分发 WithInstance 优先（@since15） | 正常 |

### US-3: 自绘组件路径的查询/动作分发与限制

作为应用自绘组件 Provider
我想要查询/动作/事件经我的回调处理
以便自治无障碍树

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 自绘组件路径查询 THEN provider→FindAccessibilityNodeInfosById 等，结果经 CopyNativeInfosToAccessibilityElementInfos（Transform+FillNodeConfig）转换 | 正常 |
| AC-3.2 | WHEN 查询 mode 含 PREFETCH_RECURSIVE_CHILDREN_REDUCED THEN 自绘组件路径强制降级为 PREFETCH_RECURSIVE_CHILDREN | 边界 |
| AC-3.3 | WHEN 自绘组件路径坐标 THEN 默认叠加 host offset/scale；DrawBound/FOCUS_NODE_UPDATE 场景 ignoreHostOffset=true 跳过叠加 | 边界 |
| AC-3.4 | WHEN 自绘组件路径 SetChildTreeIdAndWinId / GetParentWindowId THEN 为 no-op（仅日志 / 恒 0），不向上回灌 childTree | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-6 | 单测 | xcomponent_pattern.cpp:1220, custom_pattern.cpp:102 |
| AC-1.2 | R-1 | TASK-6 | 单测 | js_accessibility_manager.cpp:8941 |
| AC-1.3 | R-1 | TASK-6 | 单测 | xcomponent_pattern.cpp:1258 |
| AC-1.4 | R-1 | TASK-6 | 单测 | xcomponent_pattern.cpp:1187, js_accessibility_manager.cpp:9136 |
| AC-2.1 | R-2 | TASK-6 | 单测 | native_interface_accessibility.cpp:789 |
| AC-2.2 | R-2 | TASK-6 | 单测 | native_interface_accessibility.cpp:807 |
| AC-2.3 | R-3 | TASK-6 | 单测 | native_interface_accessibility_provider.cpp:159 |
| AC-3.1 | R-3 | TASK-6 | 单测 | js_third_provider_interaction_operation.cpp:123 |
| AC-3.2 | R-4 | TASK-6 | 单测 | js_third_provider_interaction_operation.cpp:335 |
| AC-3.3 | R-4 | TASK-6 | 单测 | js_third_provider_interaction_operation.cpp:683, 804 |
| AC-3.4 | R-4 | TASK-6 | 单测 | js_third_provider_interaction_operation.cpp:854, 867 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | XComponent/Custom Provider 注册 | ChildTreeCallback.OnRegister→创建 Provider+SessionAdapter→`RegisterInteractionOperationAsChildTree(JS_THIRD_PROVIDER)`→`RegisterThirdProviderInteractionOperationAsChildTree` 构造 JsThirdProviderInteractionOperation 并注册 SA | 注册与 callback 挂载双向补偿；子树挂载管道见 Feat-05 | AC-1.1, AC-1.2, AC-1.3, AC-1.4 |
| R-2 | 边界 | NDK Provider 获取 | `OH_ArkUI_NativeModule_GetNativeAccessibilityProvider` 仅 ARKUI_NODE_CUSTOM 返回句柄，其余 PARAM_INVALID；XComponent 另有 NodeHandle V2 与 Legacy 双路径 | @since23 | AC-2.1, AC-2.2 |
| R-3 | 行为 | Provider 分发优先级 | 所有 Provider 方法 WithInstance(@since15) 优先回退普通；CustomAccessibilityProvider 各方法委托 native provider，NOT_REGISTERED 转 0 | IsRegister 对两套回调取 OR | AC-2.3, AC-3.1 |
| R-4 | 边界 | 自绘组件路径限制 | REDUCED 强制降级为全量递归；坐标默认叠加 host 变换，DrawBound/FOCUS_NODE_UPDATE 跳过；SetChildTreeIdAndWinId/GetParentWindowId 为 no-op（不向上回灌 childTree） | Web 路径独立，见 Feat-05 | AC-3.2, AC-3.3, AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.x（Provider 注册） | 单测：XComponent/Custom 注册链 | Registration 分发、双向补偿 |
| VM-2 | AC-2.x（NDK Provider） | 单测：GetNativeAccessibilityProvider | Custom 限制、WithInstance 优先 |
| VM-3 | AC-3.x（自绘路径限制） | 单测：JsThirdProviderInteractionOperation | REDUCED 降级、坐标、no-op |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `OH_ArkUI_NativeModule_GetNativeAccessibilityProvider` (@since23) | Public(NDK) | node, provider* | int32_t | ARKUI_ERROR_CODE_* | 取 Provider（仅 Custom） | AC-2.1, AC-2.2 |
| `ArkUI_AccessibilityProviderCallbacks` (@since13) / `...WithInstance` (@since15) | Public(NDK) | 7 回调表 | int32_t | NOT_REGISTERED/COPY_FAILED | Provider 回调注册 | AC-2.3, AC-3.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

## 接口规格

> L1：Provider 注册/分发行为同规则定义；NDK Provider 接口签名见 Feat-01 API 变更分析。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 13（Custom Provider @since23）
- **API 版本号策略:** WithInstance @since15、GetNativeAccessibilityProvider @since23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 应用自绘组件子树为"叶子" | SetChildTreeIdAndWinId/GetParentWindowId 为 no-op，不向上回灌 | AC-3.4 |
| Provider 注册经共享 ChildTree 管道 | 以 `JS_THIRD_PROVIDER` operatorType 挂载（管道见 Feat-05） | AC-1.x |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可靠性 | Provider 未注册时返回 NOT_REGISTERED 不崩溃 | 单测 | native_interface_accessibility_provider.cpp |
| 可测试性 | Provider 注册与分发可独立单测 | 单测 | js_third_provider_interaction_operation_* |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本特性即应用自绘组件 Provider 接入 | 全部 |
| 多窗口/分屏 | 是 | childTreeId/windowId 编码、坐标 host 叠加 | AC-3.x |
| 生态兼容 | 是 | 应用 Native 自绘节点接入 | AC-1.x, AC-2.x |
| 版本升级 | 是 | Custom @since23、WithInstance @since15 | AC-2.x |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（应用自绘组件 Provider 注册 + NDK C API + 自绘路径分发限制；不含子树挂载管道 Feat-05、字段填充 Feat-01、动作执行 Feat-02、事件上报 Feat-07）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "JsThirdProviderInteractionOperation 应用自绘组件 Provider 注册与 REDUCED 降级"
  - repo: "openharmony/arkui_ace_engine"
    query: "OH_ArkUI_NativeModule_GetNativeAccessibilityProvider Custom 限制与 WithInstance 优先"
```

**关键文档：** design.md（同目录）、Feat-05（子树注册与跨进程接入）、`interfaces/native/native_interface_accessibility.h`
