# 特性规格

> Func-05-16-01-Feat-02 NodeController 生命周期回调：固化 NodeController 生命周期方法（`aboutToResize`/`aboutToAppear`/`aboutToDisappear`/`onTouchEvent` `@since11`；`onAttach`/`onDetach`/`onWillBind`/`onWillUnbind`/`onBind`/`onUnbind` `@since18`，containerId=NodeContainer element id）、EventHub 存储 + Fire*（`aboutToAppear` 异步 PostTask、其余同步 copy-then-invoke；`aboutToResize` 在 Pattern `resizeFunc_`）、bind/unbind 状态机（`onWillBind→state→onBind`→makeNode、`onWillUnbind→state→onUnbind`）、idempotency 与跨 container 重绑、两轴独立（bind/unbind vs appear/detach）、纯通知无 dirty 行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | NodeController 生命周期回调 |
| 特性编号 | Func-05-16-01-Feat-02 |
| 优先级 | P1 |
| 目标版本 | dynamic `@since11`（aboutToResize/Appear/Disappear/onTouchEvent）/ `@since18`（onAttach/onDetach/onWillBind/onWillUnbind/onBind/onUnbind）；static `@since23`（整套，方法非可选、containerId:long） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01（渲染宿主与 FrameNode 桥接）；本特性聚焦 NodeController 生命周期回调。复用与纹理导出（Feat-03）由后续 Feat 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/16-custom-placeholder-components/01-node-container/design.md` | Baselined |
| Dynamic API（NodeController） | `interface/sdk-js/api/arkui/NodeController.d.ts` | — |
| Static API | `interface/sdk-js/api/arkui/NodeController.static.d.ets` | — |
| NG EventHub | `frameworks/core/components_ng/pattern/node_container/node_container_event_hub.cpp` / `.h` | — |
| NG Pattern（OnResize） | `frameworks/core/components_ng/pattern/node_container/node_container_pattern.cpp` / `.h` | — |
| JS 桥接（SetOn*Func + bind 状态机） | `frameworks/bridge/declarative_frontend/jsview/js_node_container.cpp` | — |
| FrameNode 触发（attach/detach） | `frameworks/core/components_ng/base/frame_node.cpp`、`event/event_hub.cpp` | — |

> 需求基线详见 proposal.md。design.md 与本文档增量合并，互不依赖。

---

## 用户故事

### US-1: 基础生命周期（appear/disappear/attach/detach/touch）

**作为** 应用开发者,
**我想要** 实现 `aboutToAppear`/`aboutToDisappear`/`onAttach`/`onDetach`/`onTouchEvent` 回调,
**以便** NodeContainer 进出主树与触摸时执行自定义逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN NodeContainer `OnAttachToMainTree` THEN `FireOnAttach()`（sync）+`FireOnAppear()`（`frame_node.cpp:1882-1883`） | 正常 |
| AC-1.2 | WHEN `aboutToAppear` 触发 THEN `FireOnAppear`（`event_hub.cpp:22-44`）**异步** PostTask（UI，tag `ArkUINodeControllerAboutToAppearEvent`），先 copy 回调再调（防重入覆写，`:36-38`） | 边界 |
| AC-1.3 | WHEN NodeContainer `OnDetachFromMainTree` THEN `OnDetachClear`（`event_hub.cpp:723-728`）`FireOnDetach()`（sync）+`FireOnDisappear()`（sync） | 正常 |
| AC-1.4 | WHEN `onAttach`/`onDetach` 提供（`@since18`）THEN EventHub `FireOnAttach`/`FireOnDetach`（sync copy-then-invoke，`event_hub.cpp:88-104`）触发；未提供则空 | 正常 |
| AC-1.5 | WHEN `onTouchEvent(event)` 提供（`@since11`）THEN 经 gesture hub dispatch（`node_container_model_ng.cpp:64-69`）sync 触发；未提供跳过 | 正常 |

### US-2: aboutToResize

**作为** 应用开发者,
**我想要** NodeContainer 尺寸变化时收到 `aboutToResize(size)`,
**以便** 按新尺寸调整嵌入节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `OnDirtyLayoutWrapperSwap`（`node_container_pattern.cpp:82-112`）且 `config.frameSizeChange` 为真 THEN 投 after-layout task 调 `FireOnResize(size)`（`:91-98`）；`skipMeasure&&skipLayout` 提前 return（`:84-86`） | 正常 |
| AC-2.2 | WHEN `frameSizeChange` 为假 THEN 不触发 `aboutToResize` | 边界 |
| AC-2.3 | WHEN `FireOnResize(size)`（`pattern.h:89-93`）THEN `resizeFunc_(size)`（size 为 px，`GetFrameSize`）；`resizeFunc_` 存于 **Pattern**（非 EventHub），未注册则 no-op | 边界 |
| AC-2.4 | WHEN size 传给 TS THEN `NodeContainerResizeCallback`（`js_node_container.cpp:127-142`）转 vp（`Px2VpWithCurrentDensity` `:137-138`）建 `{width,height}` 对象传入 | 正常 |

### US-3: bind/unbind 状态机

**作为** 应用开发者,
**我想要** controller 绑定/解绑 NodeContainer 时收到 `onWillBind`/`onBind`/`onWillUnbind`/`onUnbind`,
**以便** 感知绑定关系变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN controller 绑定 NodeContainer（`JSNodeContainer::Create:215-223`）THEN 顺序：`FireOnWillBind(nodeContainerId)`→`AddToNodeControllerMap`+设 `_value=nodeContainerId`（`:220`）→`FireOnBind(nodeContainerId)`→`FireMakeNode()`（makeNode 在 onBind 后） | 正常 |
| AC-3.2 | WHEN containerId 传入 THEN 为 **NodeContainer FrameNode element id**（`frameNode->GetId()`，`js_node_container.cpp:184`；SDK 注「uniqueId of the NodeContainer」），非 controller/子节点 id | 边界 |
| AC-3.3 | WHEN 解绑触发（node-destroy `BindFunc:161-163`/controller-rebind `ResetNodeContainerId:240-243`）THEN 顺序：`FireOnWillUnbind`→`RemoveFromNodeControllerMap`/复位 `_value`→`FireOnUnbind` | 正常 |
| AC-3.4 | WHEN `onWillBind`/`onBind`/`onWillUnbind`/`onUnbind` 触发 THEN EventHub `FireOn*`（`event_hub.cpp:56-86`）sync copy-then-invoke（`@since18`）；未提供则空 | 正常 |
| AC-3.5 | WHEN bind/unbind 与 appear/detach THEN **两轴独立**——bind/unbind 是 controller↔container 身份，appear/detach 是 container↔主树可见性，互不依赖 | 边界 |

### US-4: idempotency 与跨 container 重绑

**作为** 应用开发者,
**我想要** 同 controller 重绑同一 container 幂等、跨 container 重绑先解绑旧,
**以便** 绑定关系正确维护。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN controller 的 `_nodeContainerId._value == nodeContainerId` THEN `Create` 幂等 short-circuit return（`js_node_container.cpp:189-195`），不重绑 | 边界 |
| AC-4.2 | WHEN `_value != -1`（已绑别 container）THEN 先对当前 containerId 触发 unbind 序列（`FireOnWillUnbind`→`RemoveFromNodeControllerMap`→`FireOnUnbind`，`:197-199`），再绑新 | 正常 |
| AC-4.3 | WHEN controller 为 null/非对象 THEN `Create` 早退：`RemoveChildAtIndex(0)`+`MarkNeedFrameFlushDirty(MEASURE)`+`ResetNodeController()`（`:175-180`） | 异常 |
| AC-4.4 | WHEN `ResetNodeController()`（`:294-312`）THEN null 所有 model setter（对称 teardown） | 正常 |
| AC-4.5 | WHEN controller-rebind `resetFunc` 触发（`ResetNodeContainerId:226-244`）THEN 若 `_value` 已变（绑别处）则早退不解绑（`:236-238`）；否则 unbind 序列+复位 `_value=-1`（`:240-243`） | 边界 |

### US-5: 回调存储/同步性与纯通知语义

**作为** 框架维护者,
**我想要** 了解回调存储位置、同步性与脏标记语义,
**以便** 正确理解生命周期对渲染的影响。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 回调存储 THEN `aboutToAppear/Disappear/onAttach/Detach/onWillBind/Unbind/Bind/Unbind` 存于 **EventHub**（`event_hub.h:84-91` `std::function`）；`aboutToResize` 存于 **Pattern** `resizeFunc_`（`pattern.h:142`） | 正常 |
| AC-5.2 | WHEN 同步性 THEN `aboutToAppear` **异步**（PostTask UI），其余生命周期回调 **同步** copy-then-invoke | 边界 |
| AC-5.3 | WHEN JS 绑定（`js_node_container.cpp:314-431`）THEN 各 `SetOn*Func` 读 controller 可选方法，`IsFunction` 守卫跳过缺失，包 `NodeContainerJsFunctionCallback`/`TouchCallback`/`ResizeCallback` 转发 model | 正常 |
| AC-5.4 | WHEN 生命周期回调触发 THEN **纯通知，不置 dirty/PROPERTY_UPDATE**；dirty 仅由 makeNode 路径（`AddBaseNode:71`/`CleanChild:79`）置 `PROPERTY_UPDATE_MEASURE` | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.5 | R-1,R-2,R-10 | T-2 | UT + SDK 比对 | `frame_node.cpp:1874-1889,2162-2180`、`event_hub.cpp:22-104` |
| AC-2.1~2.4 | R-3,R-4 | T-2 | UT：OnDirtyLayoutWrapperSwap→OnResize | `node_container_pattern.cpp:82-112`、`js_node_container.cpp:127-142` |
| AC-3.1~3.5 | R-5,R-6,R-11 | T-2 | UT：bind/unbind 状态机 | `js_node_container.cpp:168-224,145-166` |
| AC-4.1~4.5 | R-7,R-8 | T-2 | UT：idempotency/跨 container 重绑 | `js_node_container.cpp:189-244,294-312` |
| AC-5.1~5.4 | R-9,R-12 | T-2 | UT：存储/同步性/纯通知 | `event_hub.h:84-91`、`pattern.h:142` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | OnAttachToMainTree | FireOnAttach(sync)+FireOnAppear(async) | onAttach @since18 | AC-1.1,AC-1.2 |
| R-2 | 行为 | OnDetachFromMainTree | OnDetachClear: FireOnDetach(sync)+FireOnDisappear(sync) | — | AC-1.3,AC-1.4 |
| R-3 | 行为 | OnDirtyLayoutWrapperSwap + frameSizeChange | after-layout task→FireOnResize(px) | skipMeasure&&skipLayout 提前 return | AC-2.1,AC-2.2 |
| R-4 | 行为 | aboutToResize 回调 | resizeFunc_ 在 Pattern；size px→vp 转 {width,height} | 未注册 no-op | AC-2.3,AC-2.4 |
| R-5 | 行为 | controller 绑定 | onWillBind→set _value→onBind→makeNode | containerId=NodeContainer element id | AC-3.1,AC-3.2 |
| R-6 | 行为 | 解绑触发 | onWillUnbind→state→onUnbind | node-destroy/controller-rebind | AC-3.3 |
| R-7 | 边界 | _value==nodeContainerId | 幂等 short-circuit | — | AC-4.1 |
| R-8 | 行为 | _value!=-1（绑别处） | 先 unbind 当前 containerId 再绑新 | null controller 早退 ResetNodeController | AC-4.2,AC-4.3 |
| R-9 | 行为 | 回调存储 | appear/disappear/attach/detach/bind 系列在 EventHub；resize 在 Pattern | — | AC-5.1 |
| R-10 | 边界 | onTouchEvent | gesture hub dispatch sync；未提供跳过 | @since11 | AC-1.5 |
| R-11 | 边界 | bind/unbind vs appear/detach | 两轴独立 | controller↔container vs container↔主树 | AC-3.5 |
| R-12 | 行为 | 生命周期回调 | 纯通知，无 dirty；dirty 仅 makeNode 路径 MEASURE | aboutToAppear 异步，其余同步 | AC-5.2,AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 基础生命周期 | UT + SDK | appear async/Disappear sync、attach/detach @since18、touch |
| VM-2 | AC-2.x aboutToResize | UT | frameSizeChange、after-layout、px→vp、Pattern resizeFunc_ |
| VM-3 | AC-3.x bind/unbind | UT | 状态机顺序、makeNode 在 onBind 后、containerId=element id |
| VM-4 | AC-4.x idempotency/重绑 | UT | short-circuit、跨 container 先 unbind、null 早退 |
| VM-5 | AC-5.x 存储/纯通知 | UT | EventHub vs Pattern、同步性、无 dirty |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `NodeController.aboutToResize/aboutToAppear/aboutToDisappear/onTouchEvent`（dyn `@since11`/static `@since23`） | 既有 | 基础生命周期 | 可选（dyn）/非可选（static） | AC-1.1~1.5,AC-2.1 |
| `NodeController.onAttach/onDetach`（dyn `@since18`/static `@since23`） | 既有 | 主树 attach/detach | — | AC-1.4 |
| `NodeController.onWillBind/onWillUnbind/onBind/onUnbind(containerId)`（dyn `@since18`/static `@since23`） | 既有 | bind/unbind 状态机 | containerId=NodeContainer uniqueId | AC-3.1~3.4 |

> SDK：dynamic `NodeController.d.ts:88-241`；static `NodeController.static.d.ets:69-184`。

## 接口规格

### 接口定义

**NodeController 生命周期方法（`NodeController.d.ts`）**

| 属性 | 值 |
|------|-----|
| 方法签名 | `aboutToResize?(size: Size): void`/`aboutToAppear?(): void`/`aboutToDisappear?(): void`/`onTouchEvent?(event): void`（@since11）；`onAttach?()`/`onDetach?()`/`onWillBind?(containerId: number): void`/`onWillUnbind?`/`onBind?`/`onUnbind?`（@since18） |
| 返回值 | void |
| 开放范围 | Public（dyn `@since11/18`，static `@since23`） |
| 错误码 | N/A（纯通知，缺失跳过） |
| 关联 AC | AC-1.1~1.5,AC-3.1~3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| size（aboutToResize） | Size | — | — | vp 单位（C++ px 经转换） |
| containerId（onWillBind/...） | number/long | — | — | NodeContainer uniqueId（element id） |
| event（onTouchEvent） | TouchEvent | — | — | 触摸事件 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | attach 主树 | onAttach(sync)+aboutToAppear(async) | AC-1.1,AC-1.2 |
| 2 | frameSizeChange | after-layout aboutToResize(vp) | AC-2.1,AC-2.4 |
| 3 | controller 绑定 | onWillBind→onBind→makeNode | AC-3.1 |
| 4 | 同 controller 重绑同 container | 幂等 short-circuit | AC-4.1 |
| 5 | 跨 container 重绑 | 先 unbind 当前再绑新 | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意既有行为：`aboutToAppear` 异步、其余同步；`aboutToResize` 在 Pattern 非 EventHub；bind/unbind 与 appear/detach 两轴独立；生命周期回调纯通知无 dirty。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dyn `@since11`（基础）/`@since18`（attach/bind）；static `@since23`。
- **API 版本号策略:** 按 SDK `@since11/18/23` 标注。

> **两轴独立风险（F-axes）：** bind/unbind（controller↔container 身份，`@since18`）与 appear/detach（container↔主树可见性）是**两个独立轴**，下游勿假设绑定即可见或可见即绑定（风险 RISK-F2-1）。`aboutToResize` 存于 Pattern 非 EventHub，与其它回调存储位置不同（RISK-F2-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| aboutToAppear 异步 | PostTask UI，先 copy 防重入 | AC-1.2 |
| aboutToResize 在 Pattern | resizeFunc_，非 EventHub | AC-2.3,AC-5.1 |
| bind 状态机顺序 | onWillBind→state→onBind→makeNode | AC-3.1 |
| containerId=element id | NodeContainer FrameNode GetId | AC-3.2 |
| 两轴独立 | bind/unbind vs appear/detach | AC-3.5 |
| 纯通知无 dirty | dirty 仅 makeNode 路径 MEASURE | AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 缺失回调安全跳过（IsFunction 守卫）；null controller 早退不崩 | UT 异常 | `js_node_container.cpp:175-180,314-431` |
| 性能 | 生命周期回调纯通知无渲染开销 | UT | `event_hub.cpp:22-104` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 是 | frameSizeChange 易触发 aboutToResize | XTS | `node_container_pattern.cpp:91` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 回调为通知，无直接映射 | — |
| 大字体 | 否 | frameSizeChange 触发 aboutToResize | AC-2.1 |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 是 | attach/detach 触发 onAttach/Detach + aboutToAppear/Disappear | AC-1.1,AC-1.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 基础 `@since11`、attach/bind `@since18`、static `@since23` | AC-1.4,AC-3.4 |
| 生态兼容 | 是 | dyn `@since11/18`、`@atomicservice since12` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: NodeController 生命周期回调
  作为 应用开发者
  我想要 实现 aboutTo*/onAttach/Detach/bind 系列回调
  以便 感知 NodeContainer 生命周期与绑定关系

  Scenario Outline: attach/detach
    Given NodeContainer <事件>
    When EventHub Fire
    Then <回调>

    Examples:
      | 事件 | 回调 |
      | OnAttachToMainTree | onAttach(sync)+aboutToAppear(async) |
      | OnDetachFromMainTree | onDetach(sync)+aboutToDisappear(sync) |

  Scenario: bind 状态机
    Given controller 绑定 NodeContainer
    When Create
    Then onWillBind(cid)→set _value=cid→onBind(cid)→makeNode

  Scenario: 跨 container 重绑
    Given controller 已绑 containerA（_value=A）
    When 绑 containerB
    Then 先对 B 触发 onWillUnbind(B)→onUnbind(B)，再绑 B

  Scenario: 同 controller 重绑
    Given controller._value == nodeContainerId
    When Create
    Then 幂等 short-circuit，不重绑

  Scenario: aboutToResize
    Given NodeContainer 尺寸变化（frameSizeChange=true）
    When after-layout
    Then aboutToResize({width,height} vp)
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做生命周期回调；渲染宿主见 Feat-01、复用+纹理导出见 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainerEventHub FireOnAppear async PostTask FireOnDisappear sync copy-then-invoke"
  - repo: "openharmony/arkui_ace_engine"
    query: "JSNodeContainer Create bind/unbind 状态机 onWillBind onBind makeNode containerId GetId"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainerPattern OnDirtyLayoutWrapperSwap frameSizeChange FireOnResize resizeFunc_ px vp"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainer idempotency _nodeContainerId _value 跨 container 重绑 unbind old"
```

**关键文档：** `interface/sdk-js/api/arkui/NodeController.d.ts`、`frameworks/core/components_ng/pattern/node_container/node_container_event_hub.cpp`、`frameworks/bridge/declarative_frontend/jsview/js_node_container.cpp`、`frameworks/core/components_ng/base/frame_node.cpp`
