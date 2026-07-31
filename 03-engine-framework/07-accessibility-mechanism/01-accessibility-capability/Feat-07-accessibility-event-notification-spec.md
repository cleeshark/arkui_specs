# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍事件通知 |
| 特性编号 | Func-03-07-01-Feat-07 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 13 起 |
| SIG 归属 | SIG_ApplicationFramework |
| 状态 | Draft |
| 复杂度 | 复杂 |

> 框架内部能力补录：当前实现即契约。本 Feat 覆盖**ArkUI 组件树变化如何上报为无障碍事件给系统无障碍服务**；动作执行在 Feat-02、元素查询响应在 Feat-01。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无障碍事件通知规格化 | 固化事件上报链路、AccessibilityEventType 清单与转换表、TEXT_CHANGE vs ELEMENT_INFO_CHANGE 触发区分、按帧聚合去重、多重门控、ANNOUNCE/REQUEST_FOCUS、异步/同步与线程切换、NDK 事件上报 |

## 输入文档

- 设计文档：`03-engine-framework/07-accessibility-mechanism/01-accessibility-capability/design.md`
- 源码定位：`adapter/ohos/osal/js_accessibility_manager.cpp`、`frameworks/core/components_ng/property/accessibility_property.cpp`、`frameworks/core/components_ng/base/frame_node.cpp`、`frameworks/core/pipeline/pipeline_base.cpp`、`frameworks/core/accessibility/accessibility_utils.h`、`interfaces/native/native_interface_accessibility.*`

## 用户故事

### US-1: 组件属性变化触发事件上报

**作为** 读屏消费者,
**我想要** 组件无障碍属性变化时收到事件,
**以便** 及时更新朗读内容

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN SetAccessibilityText/Description 值真正变化 THEN 触发 TEXT_CHANGE（NotifyComponentChangeEvent 入队） | 正常 |
| AC-1.2 | WHEN SetAccessibilityGroup/NextFocusInspectorKey/CustomActions 或 SetAccessibilityLevel（值变化）变化 THEN 触发 ELEMENT_INFO_CHANGE | 正常 |
| AC-1.3 | WHEN 同一帧内同一节点多次同类变化 THEN `accessibilityEvents_`（std::set）按 (eventId, nodeId) 去重，合并为一次上报 | 边界 |
| AC-1.4 | WHEN 属性值未变化（与 backup 相同）THEN Setter 提前 return，不发事件 | 边界 |

### US-2: 事件类型与转换

**作为** 框架,
**我想要** 内部事件类型经转换表映射到系统事件类型,
**以便** 保证仅支持的事件类型可上报

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 上报事件 THEN `ConvertAceEventType` 将内部 AccessibilityEventType 映射到系统 EventType（如 CLICK→TYPE_VIEW_CLICKED_EVENT、ELEMENT_INFO_CHANGE→TYPE_ELEMENT_INFO_CHANGE） | 正常 |
| AC-2.2 | WHEN 内部事件类型未在转换表（如 BLUR/MOUSE_*/KEYBOARD_*/TOUCH_*）THEN 映射为 TYPE_VIEW_INVALID，不上报 SA | 边界 |
| AC-2.3 | WHEN 内部枚举值与 NDK 枚举值不同（如 REQUEST_FOCUS=0x800000 vs NDK REQUEST_ACCESSIBILITY_FOCUS=0x2000000）THEN 跨边界映射按各自枚举 | 边界 |

### US-3: 事件门控

**作为** 框架,
**我想要** 多重门控过滤不必要的上报,
**以便** 避免噪音与性能浪费

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `IsAccessibilityEnabled()` 为 false THEN 不入队/不上报（总开关） | 边界 |
| AC-3.2 | WHEN 读屏关闭（无障碍开但 IsAccessibilityScreenReadEnabled=false）THEN 丢弃 ELEMENT_INFO_CHANGE/COMPONENT_CHANGE/TEXT_CHANGE/FOCUS/SCROLLING_EVENT；CLICK/LONG_PRESS/PAGE_CHANGE/ANNOUNCE 仍上报 | 边界 |
| AC-3.3 | WHEN 节点 accessibilityLevel=no 或 !IsActive() THEN 该节点事件不发 | 边界 |
| AC-3.4 | WHEN CLICK 事件且节点为 checked/selected THEN 延时（DELAY_SEND_EVENT_MILLISECOND）经 AfterRender 发送，确保状态先于点击播报更新 | 边界 |

### US-4: 动作期间事件抑制与异步/同步

**作为** 框架,
**我想要** 在动作执行期间抑制冗余变更事件，并正确切换线程,
**以便** 保证播报与动作结果一致

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 执行非 SET_TEXT 动作 THEN 该节点 TEXT_CHANGE/COMPONENT_CHANGE 加入 blockerInAction_ 阻塞，渲染后解除 | 正常 |
| AC-4.2 | WHEN 组件侧调 SendAccessibilityAsyncEvent THEN 经门控/延时/Inner 后汇聚到 `SendAccessibilitySyncEvent`，在 BACKGROUND 线程 `client->SendEvent` IPC 上报 SA | 正常 |

### US-5: 主动播报与请求焦点

**作为** 组件,
**我想要** 主动播报文本与请求无障碍焦点,
**以便** 引导读屏

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 组件发 ANNOUNCE_FOR_ACCESSIBILITY（专用重载）THEN 携带 textAnnouncedForAccessibility 经 SendEventToAccessibilityWithNode 上报 | 正常 |
| AC-5.2 | WHEN 发 ANNOUNCE_FOR_ACCESSIBILITY_NOT_INTERRUPT THEN 不打断当前播报 | 边界 |
| AC-5.3 | WHEN 焦点节点被移除（OnAccessibilityDetachFromMainTree）THEN 缓存候选并经 ON_SEND_DETACH_FOCUS_FALLBACK 回调，发 REQUEST_FOCUS_FOR_ACCESSIBILITY_NOT_INTERRUPT 或 FOCUS_INVISIBLE 回退 | 边界 |

### US-6: NDK 事件上报

**作为** 应用自绘组件组件,
**我想要** 经 NDK 主动上报事件,
**以便** 为自绘内容提供播报

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 应用自绘组件调 `OH_ArkUI_SendAccessibilityAsyncEvent(provider, eventInfo, callback)` THEN provider→SendAccessibilityAsyncEvent，经 ThirdAccessibilityManager→JsThirdProviderInteractionOperation 转 OHOS EventInfo 在 BACKGROUND 线程 SendEvent | 正常 |
| AC-6.2 | WHEN ArkUI_AccessibilityEventInfo 设置 THEN 经 SetEventType/SetTextAnnouncedForAccessibility/SetRequestFocusId/SetElementInfo 填充 | 正常 |
| AC-6.3 | WHEN 发送完成 THEN 回调一次性返回错误码（成功 0，失败 SEND_EVENT_FAILED） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-2 | TASK-7 | 单测 | accessibility_property.cpp:1492, 1534 |
| AC-1.2 | R-1, R-2 | TASK-7 | 单测 | accessibility_property.cpp:1466, 1599, 1892 |
| AC-1.3 | R-3 | TASK-7 | 单测 | pipeline_base.cpp:1066 |
| AC-1.4 | R-2 | TASK-7 | 单测 | accessibility_property.cpp:1494 |
| AC-2.1 | R-4 | TASK-7 | 单测 | js_accessibility_manager.cpp:427 |
| AC-2.2 | R-4 | TASK-7 | 单测 | js_accessibility_manager.cpp:2994 |
| AC-2.3 | R-4 | TASK-7 | 单测 | accessibility_utils.h:111, native_interface_accessibility.h:152 |
| AC-3.1 | R-5 | TASK-7 | 单测 | accessibility_property.cpp:389, pipeline_base.cpp:1068 |
| AC-3.2 | R-5 | TASK-7 | 单测 | js_accessibility_manager.cpp:4048 |
| AC-3.3 | R-5 | TASK-7 | 单测 | js_accessibility_manager.cpp:4123 |
| AC-3.4 | R-5 | TASK-7 | 单测 | js_accessibility_manager.cpp:4020 |
| AC-4.1 | R-6 | TASK-7 | 单测 | js_accessibility_manager.cpp:7967 |
| AC-4.2 | R-7 | TASK-7 | 单测 | js_accessibility_manager.cpp:3910 |
| AC-5.1 | R-8 | TASK-7 | 单测 | frame_node.cpp:5402 |
| AC-5.2 | R-8 | TASK-7 | 单测 | accessibility_utils.h:117 |
| AC-5.3 | R-9 | TASK-7 | 单测 | accessibility_property.cpp:1804, js_accessibility_manager.cpp:10783 |
| AC-6.1 | R-10 | TASK-7 | 单测 | native_interface_accessibility.cpp:77, js_third_provider_interaction_operation.cpp:1045 |
| AC-6.2 | R-10 | TASK-7 | 单测 | native_interface_accessibility.cpp:696, 707, 722, 733 |
| AC-6.3 | R-10 | TASK-7 | 单测 | js_third_provider_interaction_operation.cpp:1068 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 属性 Setter 写入且值变化 | 调 `NotifyComponentChangeEvent`→`AddAccessibilityCallbackEvent` 按帧入队 | CustomAccessibilityProperty 的 Set 不发事件（Custom 侧自行上报） | AC-1.1, AC-1.2 |
| R-2 | 行为 | TEXT_CHANGE vs ELEMENT_INFO_CHANGE 触发 | SetText/Description→TEXT_CHANGE；SetGroup/NextFocusInspectorKey/CustomActions/SetLevel(变化)→ELEMENT_INFO_CHANGE | Setter 内自身比对，未变化不发 | AC-1.1, AC-1.2, AC-1.4 |
| R-3 | 边界 | 同帧同节点多次同类变化 | `accessibilityEvents_`(set<pair>) emplace 去重，合并为一次回调→一次上报 | 最小上报粒度：每节点每帧一次 | AC-1.3 |
| R-4 | 行为 | 事件类型转换 | `ConvertAceEventType` 映射内部→系统 EventType；未列出类型→TYPE_VIEW_INVALID 丢弃 | 内部枚举值 ≠ NDK 枚举值，跨边界各自映射 | AC-2.1, AC-2.2, AC-2.3 |
| R-5 | 边界 | 多重门控 | 总开关 IsAccessibilityEnabled；读屏关闭窄门控（仅丢 5 类）；level=no/!IsActive 不发；CLICK+checked/selected 延时 AfterRender | 白名单 eventWhiteList_、blockerInAction_ 阻塞、SA 侧 IsRegister/IsEnabled | AC-3.1, AC-3.2, AC-3.3, AC-3.4 |
| R-6 | 行为 | 非 SET_TEXT 动作执行 | 该节点 TEXT_CHANGE/COMPONENT_CHANGE 加入 blockerInAction_ 阻塞，渲染后 ResetBlockedEvent | SET_TEXT 跳过阻塞 | AC-4.1 |
| R-7 | 行为 | 异步上报汇聚同步 | SendAccessibilityAsyncEvent（含 WithNode/虚拟节点/Web/UIExtension 变体）→Inner→`SendAccessibilitySyncEvent` BACKGROUND 线程 client->SendEvent IPC | CLICK 走 AfterRender 变体；FillEventInfo 实时组装快照 | AC-4.2 |
| R-8 | 行为 | ANNOUNCE_FOR_ACCESSIBILITY / NOT_INTERRUPT | 专用重载携带 textAnnouncedForAccessibility 上报；NOT_INTERRUPT 不打断当前播报 | 应用层 JS API 在仓外 SDK，语义以 SDK 为准 | AC-5.1, AC-5.2 |
| R-9 | 行为 | 焦点节点 detach/不可见 | OnAccessibilityDetachFromMainTree 缓存候选，ON_SEND_DETACH_FOCUS_FALLBACK 回调发 REQUEST_FOCUS_FOR_ACCESSIBILITY_NOT_INTERRUPT 或 FOCUS_INVISIBLE | IsDetachFocusCacheClearEvent 定义清缓存事件 | AC-5.3 |
| R-10 | 行为 | NDK 事件上报 | `OH_ArkUI_SendAccessibilityAsyncEvent`→provider→ThirdAccessibilityManager→JsThirdProviderInteractionOperation 转 OHOS EventInfo BACKGROUND SendEvent；EventInfo 经 SetEventType/Set* 填充；完成回调一次错误码 | Custom SendEvent 走 ThirdAccessibilityManager（非 native） | AC-6.1, AC-6.2, AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.x（属性触发） | 单测：accessibility_property setter | TEXT/ELEMENT_INFO 触发、未变化不发 |
| VM-2 | AC-1.3, AC-2.x（聚合/转换） | 单测：pipeline_base + ConvertAceEventType | 按帧去重、转换表丢弃 |
| VM-3 | AC-3.x（门控） | 单测 | 总开关、读屏关闭窄门控、CLICK 延时 |
| VM-4 | AC-4.x（阻塞/线程） | 单测 | blockerInAction_、BACKGROUND IPC |
| VM-5 | AC-5.x（ANNOUNCE/回退） | 单测 | 主动播报、detach 焦点回退 |
| VM-6 | AC-6.x（NDK 事件） | 单测：应用自绘组件事件上报 | EventInfo 填充、完成回调 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `OH_ArkUI_SendAccessibilityAsyncEvent` (@since13) | Public(NDK) | provider, eventInfo, callback | void | — | 异步上报事件，完成回调错误码 | AC-6.1, AC-6.3 |
| `OH_ArkUI_CreateAccessibilityEventInfo` / `DestoryAccessibilityEventInfo` (@since13) | Public(NDK) | — | EventInfo* / void | — | EventInfo 创建/销毁 | AC-6.2 |
| `OH_ArkUI_AccessibilityEventSetEventType/SetTextAnnouncedForAccessibility/SetRequestFocusId/SetElementInfo` (@since13) | Public(NDK) | eventInfo, value | int32_t | BAD_PARAMETER | EventInfo 字段 setter | AC-6.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

> 应用层 announceForAccessibility/请求焦点的 JS API 在 ace_engine 仓内未检索到对应实现，属 `interface_sdk-js` 仓 `common.d.ts`，仓未检出，语义以 SDK 声明为准。

## 接口规格

> L1：事件上报行为同规则定义；NDK 接口签名见 API 变更分析。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 13
- **API 版本号策略:** 保留既有 @since 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 支持事件类型 = 转换表覆盖集合 | 未在 ConvertAceEventType 列出的内部类型永不到达 SA | AC-2.2 |
| 按帧聚合 | 每节点每帧同类事件合并为一次上报 | AC-1.3 |
| FillEventInfo 实时组装 | 事件携带快照为发送时刻最新状态 | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 事件按帧聚合去重，避免重复 IPC | 单测 | pipeline_base.cpp:1066 |
| 可靠性 | 多重门控（总开关/读屏/level/SA 态）防止无效上报 | 单测 | js_accessibility_manager.cpp:4048 |
| 自动化维测 | 事件可经 hidumper/mock 注入验证 | 单测 | test/unittest/core/accessibility/ |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本特性即事件通知 | 全部 |
| 多窗口/分屏 | 是 | treeId/windowId 拼接、UIExtension/Web 独立路径 | AC-4.2 |
| 版本升级 | 是 | NDK @since13 | AC-6.x |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（事件上报；不含动作执行 Feat-02、元素查询响应 Feat-01）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityEventType 枚举与 ConvertAceEventType 转换表"
  - repo: "openharmony/arkui_ace_engine"
    query: "JsAccessibilityManager SendAccessibilityAsyncEvent 链路与按帧聚合"
  - repo: "openharmony/arkui_ace_engine"
    query: "OH_ArkUI_SendAccessibilityAsyncEvent NDK 事件上报与 ArkUI_AccessibilityEventInfo"
```

**关键文档：** design.md（同目录）、`interfaces/native/native_interface_accessibility.h`
