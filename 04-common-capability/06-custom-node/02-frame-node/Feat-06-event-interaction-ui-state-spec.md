# 特性规格

> Func-04-06-02-Feat-06 FrameNode 事件交互与 UIState：固化 commonEvent、gestureEvent、commonAttribute、getInteractionEventBindingInfo、addSupportedUIStates、removeSupportedUIStates 共 6 个公开 API 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameNode 事件交互与 UIState |
| 特性编号 | Func-04-06-02-Feat-06 |
| 所属 Epic | 自定义节点能力 / FrameNode |
| 优先级 | P1 |
| 目标版本 | API 12（commonEvent/commonAttribute 起始）；gestureEvent API 14；getInteractionEventBindingInfo API 19；add/removeSupportedUIStates API 20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | commonEvent/commonAttribute | API 12 |
| ADDED | gestureEvent | API 14 |
| ADDED | getInteractionEventBindingInfo | API 19 |
| ADDED | addSupportedUIStates/removeSupportedUIStates | API 20 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/02-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `FrameNode.static.d.ets` | — |

## 用户故事

### US-1: 获取事件/属性句柄
**作为** 应用开发者，**我想要** 获取通用事件、手势、通用属性句柄以注册回调/设置属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `get commonEvent()` THEN 懒创建 UICommonEvent(node)，缓存并返回 | 正常 |
| AC-1.2 | WHEN `get gestureEvent()` THEN 懒创建 UIGestureEvent，创建 native weak ref + registerFrameNodeDeletedCallback | 正常 |
| AC-1.3 | WHEN `get commonAttribute()` THEN 懒创建 ArkComponent(nodePtr, FRAME_NODE) 修饰器门面 | 正常 |
| AC-1.4 | WHEN ImmutableFrameNode 访问 commonAttribute THEN 创建 ArkComponent(undefined)，nodePtr 置空（阻断属性变更） | 边界 |

### US-2: 查询事件绑定信息
**作为** 应用开发者，**我想要** 查询某事件类型在各层的注册状态。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `getInteractionEventBindingInfo(EventQueryType.ON_CLICK)` THEN 返回 {baseEventRegistered, nodeEventRegistered, nativeEventRegistered, builtInEventRegistered} | 正常 |
| AC-2.2 | WHEN 四个标志全 false THEN 返回 undefined | 边界 |
| AC-2.3 | WHEN eventType 非 ON_CLICK THEN 返回 undefined（仅 ON_CLICK 有效） | 边界 |
| AC-2.4 | WHEN eventType null THEN 返回 undefined | 边界 |

### US-3: 注册/移除 UIState 支持
**作为** 应用开发者，**我想要** 注册/移除支持的 UIState 并接收状态变化回调。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `addSupportedUIStates(uiStates, handler, excludeInner?)` 且 uiStates 非 NORMAL THEN 注册 userStateStyleSubscribers，supportedStates_ |= uiStates，返回 true | 正常 |
| AC-3.2 | WHEN uiStates 为 NORMAL(0) THEN 返回 false 并 warn（不支持注册 NORMAL） | 异常 |
| AC-3.3 | WHEN excludeInner=true THEN 抑制内部组件该状态的处理（外层 handler 胜出） | 正常 |
| AC-3.4 | WHEN `removeSupportedUIStates(uiStates)` 且 uiStates 非 NORMAL THEN 清除 userStateStyleSubscribers，重算 supportedStates_，返回 true | 正常 |
| AC-3.5 | WHEN uiStates 为 NORMAL THEN 返回 false 并 warn | 异常 |
| AC-3.6 | WHEN supportedStates_ 归零(=NORMAL) THEN 清空 statesChangeHandler_ | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3,R-4 | 单测 | frame_node.ts:885,895,876; ImmutableFrameNode:1157 |
| AC-2.1..2.4 | R-5,R-6,R-7 | 单测 | modifier:853; ui_node.h:1127,96-116 |
| AC-3.1..3.6 | R-8,R-9,R-10,R-11,R-12 | 单测 | modifier:1225,1242; state_style_manager.cpp:183,210; event_hub.cpp:93,105 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | get commonEvent() | 懒创建通用事件句柄并缓存 | 每实例缓存 | AC-1.1 |
| R-2 | 行为 | get gestureEvent() | 懒创建手势事件句柄并缓存（绑定节点生命周期） | — | AC-1.2 |
| R-3 | 行为 | get commonAttribute() | 懒创建通用属性修饰器门面 | @noninterop 内部门面 | AC-1.3 |
| R-4 | 边界 | ImmutableFrameNode.commonAttribute | 创建空修饰器，阻断属性变更 | 不可改节点属性变更被阻 | AC-1.4 |
| R-5 | 行为 | getInteractionEventBindingInfo(ON_CLICK) | 返回 {baseEventRegistered, nodeEventRegistered, nativeEventRegistered, builtInEventRegistered} | 反映 onClick 各层注册 | AC-2.1 |
| R-6 | 边界 | 四标志全 false 或 eventType 非 ON_CLICK | 返回 undefined | 仅 ON_CLICK 有效 | AC-2.2,2.3 |
| R-7 | 边界 | eventType null | 返回 undefined | — | AC-2.4 |
| R-8 | 行为 | addSupportedUIStates(states, handler, excludeInner?) 非 NORMAL | 注册状态处理器；返回 true | bit flags | AC-3.1 |
| R-9 | 异常 | add/remove states==NORMAL(0) | 返回 false 并 warn（不支持 NORMAL） | — | AC-3.2,3.5 |
| R-10 | 行为 | excludeInner=true | 抑制内部组件该状态处理（外层胜出） | — | AC-3.3 |
| R-11 | 行为 | removeSupportedUIStates(states) 非 NORMAL | 移除状态处理器；返回 true | — | AC-3.4 |
| R-12 | 边界 | supportedStates_ 归零 | 清空状态变化回调 | — | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-4 句柄 | 单测 | 懒创建缓存、Immutable 阻断 |
| VM-2 | R-5..R-7 绑定信息 | 单测 | 四标志、仅 ON_CLICK |
| VM-3 | R-8..R-12 UIState | 单测 | NORMAL 失败、excludeInner、归零清 handler |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| get commonEvent() | Public | — | UICommonEvent | — | 通用事件句柄 | AC-1 |
| get gestureEvent() | Public | — | UIGestureEvent | — | 手势事件句柄 | AC-1 |
| get commonAttribute() | Public(@noninterop) | — | CommonAttribute | — | 通用属性句柄 | AC-1 |
| getInteractionEventBindingInfo(eventType) | Public | eventType: EventQueryType | InteractionEventBindingInfo\|undefined | — | 事件绑定信息 | AC-2 |
| addSupportedUIStates(uiStates, handler, excludeInner?) | Public | uiStates: number; handler; excludeInner?: boolean | void | — | 注册 UIState | AC-3 |
| removeSupportedUIStates(uiStates) | Public | uiStates: number | void | — | 移除 UIState | AC-3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**commonEvent / gestureEvent / commonAttribute**

| 属性 | 值 |
|------|-----|
| 函数签名 | `get commonEvent(): UICommonEvent`; `get gestureEvent(): UIGestureEvent`; `get commonAttribute(): CommonAttribute` (@since 12/14; commonAttribute @noninterop) |
| 返回值 | UICommonEvent / UIGestureEvent / CommonAttribute |
| 开放范围 | Public（commonAttribute @noninterop 内部） |
| 错误码 | — |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 首次访问 | 懒创建并缓存 | AC-1.1,1.2,1.3 |
| 2 | ImmutableFrameNode.commonAttribute | nodePtr 置空阻断 | AC-1.4 |

**getInteractionEventBindingInfo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getInteractionEventBindingInfo(eventType: EventQueryType): InteractionEventBindingInfo\|undefined` (@since 19 dyn/26 static) |
| 返回值 | InteractionEventBindingInfo\|undefined |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| eventType | EventQueryType | 是 | — | 仅 ON_CLICK=0 有效；null→undefined |

**addSupportedUIStates / removeSupportedUIStates**

| 属性 | 值 |
|------|-----|
| 函数签名 | `addSupportedUIStates(uiStates: number, handler: UIStatesChangeHandler, excludeInner?: boolean): void`; `removeSupportedUIStates(uiStates: number): void` (@since 20 dyn/24-26 static) |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiStates | number(int) | 是 | — | UIState bit flags(PRESSED=1/FOCUSED=2/DISABLED=4/SELECTED=8/HOVERED=16)；NORMAL(0) 返 false |
| handler | UIStatesChangeHandler | 是(add) | — | function(node, currentUIStates) |
| excludeInner | boolean | 否 | false | true 抑制内部组件该状态处理 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** commonEvent/commonAttribute API 12；gestureEvent API 14；getInteractionEventBindingInfo API 19；add/removeSupportedUIStates API 20；静态 @since 24-26。
- **API 版本号策略:** 逐 API @since；UIState HOVERED @since 26.0.0；getInteractionEventBindingInfo 静态 @since 26.0.0。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| commonAttribute @noninterop | 返回 ArkComponent 内部门面，非可序列化跨语言值类型 | FrameNode.d.ts:1046 |
| getInteractionEventBindingInfo 仅支持 ON_CLICK | 其他 EventQueryType 值返 undefined | modifier:853 |
| addSupportedUIStates NORMAL 返 false 无错误码 | 仅 warn，不抛异常 | state_style_manager.cpp:183 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UIState bit flags | 位掩码，可组合；NORMAL=0 不可注册 | AC-3.1,3.2 |
| excludeInner 优先级 | true 时外层 handler 胜出，抑制内部 | AC-3.3 |
| 句柄懒创建缓存 | 每实例缓存；Immutable 阻断属性 | AC-1.1,1.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | gestureEvent 绑定 native 生命周期回调，节点删除时清理 | 单测 | frame_node.ts:895 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | UIState 含 FOCUSED/DISABLED 但不直接改无障碍树 | — |
| 版本升级 | 是 | gestureEvent(14)/getInteractionEventBindingInfo(19)/UIState(20-26) 演进 | AC-1.2,2.1,3 |

## 行为场景

```gherkin
Feature: FrameNode 事件交互与 UIState
  Scenario Outline: addSupportedUIStates NORMAL 失败
    When 调用 node.addSupportedUIStates(<states>, handler)
    Then <期望>

    Examples:
      | states | 期望 |
      | UIState.PRESSED | 返回 true，supportedStates_|=PRESSED |
      | UIState.NORMAL | 返回 false 并 warn |

  Scenario: excludeInner 抑制内部
    Given 外层注册 SELECTED + excludeInner=true
    When SELECTED 状态变化
    Then 内部组件 SELECTED handler 不触发
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（事件/UIState；不含动画 Feat-07）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "EventHub::AddSupportedUIStateWithCallback 与 StateStyleManager userStateStyleSubscribers/excludeInner"
  - repo: "openharmony/arkui_ace_engine"
    query: "UINode::GetInteractionEventBindingInfo 四层标志(base/native/node/builtIn)与 EventQueryType.ON_CLICK"
  - repo: "openharmony/arkui_ace_engine"
    query: "UIState bit flags 与 frame_node.ts supportedStates_ 累积/清除"
```
