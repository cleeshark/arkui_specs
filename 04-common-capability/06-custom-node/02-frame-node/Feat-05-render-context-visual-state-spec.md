# 特性规格

> Func-04-06-02-Feat-05 FrameNode 渲染上下文与视觉状态：固化 getRenderNode、onDraw、getOpacity、isVisible、isClipToFrame、isAttached、isInRenderState、invalidateAttributes 共 8 个公开 API 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameNode 渲染上下文与视觉状态 |
| 特性编号 | Func-04-06-02-Feat-05 |
| 所属 Epic | 自定义节点能力 / FrameNode |
| 优先级 | P1 |
| 目标版本 | API 12（dynamic 起始）；isInRenderState API 23；invalidateAttributes API 21 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | getRenderNode/onDraw/getOpacity/isVisible/isClipToFrame/isAttached | API 12（getRenderNode 动态 @since 11） |
| ADDED | invalidateAttributes | API 21 |
| ADDED | isInRenderState | API 23 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/02-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `FrameNode.static.d.ets` | — |

## 用户故事

### US-1: 获取关联 RenderNode 与自定义绘制
**作为** 应用开发者，**我想要** 获取关联 RenderNode 并自定义绘制，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `getRenderNode()` 且 renderNode_ 非空且 nodePtr 非空 THEN 返回 renderNode_ | 正常 |
| AC-1.2 | WHEN 节点为 ProxyFrameNode THEN 返回 null | 边界 |
| AC-1.3 | WHEN 定义 onDraw(context) THEN 构造时 SetDrawFunc 注入 CustomFrameNodePattern，绘制时 FireDrawCallback 构建 {size,sizeInPixel,canvas} | 正常 |
| AC-1.4 | WHEN 未定义 onDraw THEN SetDrawFunc 静默返回（不崩溃） | 边界 |

### US-2: 查询视觉状态
**作为** 应用开发者，**我想要** 查询透明度/可见性/裁剪/挂载状态，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `getOpacity()` THEN 返回 renderContext GetOpacityValue，默认 1.0 | 正常 |
| AC-2.2 | WHEN `isVisible()` THEN 沿父链 OR 各祖先 FrameNode::IsVisible，全部 VISIBLE 才 true | 正常 |
| AC-2.3 | WHEN 任一祖先 VisibleType::HIDDEN/GONE THEN isVisible 返回 false | 边界 |
| AC-2.4 | WHEN `isClipToFrame()` THEN 返回 GetClipEdgeValue，默认 false | 正常 |

### US-3: 查询挂载与渲染状态
**作为** 应用开发者，**我想要** 区分节点挂载状态，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `isAttached()` THEN 实际调用 isVisible 父链检查（行为等同 isVisible） | 正常 |
| AC-3.2 | WHEN `isInRenderState()` THEN 返回 rsNode 是否在渲染树（GetIsOnTheTree） | 正常 |
| AC-3.3 | WHEN 无 renderContext/rsNode THEN isInRenderState 返回 false | 边界 |

### US-4: 刷新属性
**作为** 应用开发者，**我想要** 主动刷新属性同步，
**以便** 驱动对应行为。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN `invalidateAttributes()` THEN 调 applyAttributesFinish→MarkModifyDone（重跑 OnModifyDone+同步 renderContext） | 正常 |
| AC-4.2 | WHEN nodePtr 为空 THEN 静默返回（no-op） | 边界 |
| AC-4.3 | WHEN 对比 invalidate()(render 脏+RequestNextFrame，仅 CustomFrameNode) vs invalidateAttributes(MarkModifyDone，无新帧) THEN 二者语义不同 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3 | 单测 | frame_node.ts:184,129; bridge:839; custom_frame_node_pattern.h:77 |
| AC-2.1..2.4 | R-4,R-5,R-6 | 单测 | view_abstract.cpp:10397,10477; frame_node_modifier.cpp:586 |
| AC-3.1..3.3 | R-7,R-8,R-9 | 单测 | bridge:2183; modifier:104; rosen_render_context.h:618 |
| AC-4.1..4.3 | R-10,R-11,R-12 | 单测 | frame_node.ts:967; modifier:97; frame_node.cpp:3433 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | getRenderNode() renderNode_ 非空且 nodePtr 非空 | 返回 renderNode_ | ProxyFrameNode 返 null | AC-1.1,1.2 |
| R-2 | 行为 | 定义 onDraw | onDraw 回调在构造时注入；绘制时回调获 DrawContext（size/sizeInPixel/canvas） | 动态可选；静态必填 | AC-1.3 |
| R-3 | 边界 | 未定义 onDraw | 静默返回 | 不崩溃 | AC-1.4 |
| R-4 | 行为 | getOpacity() | 返回透明度（默认 1.0） | — | AC-2.1 |
| R-5 | 行为 | isVisible() | 沿父链检查可见性 | 任一祖先 HIDDEN/GONE→false | AC-2.2,2.3 |
| R-6 | 行为 | isClipToFrame() | 返回是否裁剪至 frame（默认 false） | — | AC-2.4 |
| R-7 | 行为 | isAttached() | 行为等同 isVisible（父链可见性检查） | 已知 quirk：非主树语义 | AC-3.1 |
| R-8 | 行为 | isInRenderState() | 返回是否在渲染树 | 无底层渲染节点返 false | AC-3.2,3.3 |
| R-9 | 边界 | isAttached vs isOnMainTree | isAttached 等同 isVisible；主树语义由 isOnMainTree(Feat-01) 承载 | bridge 名互换 | AC-3.1 |
| R-10 | 行为 | invalidateAttributes() | 刷新属性同步（重跑 OnModifyDone） | 无新帧 | AC-4.1 |
| R-11 | 边界 | invalidateAttributes nodePtr 空 | 静默 no-op | — | AC-4.2 |
| R-12 | 边界 | invalidateAttributes vs invalidate | 前者刷新属性同步无新帧；后者 render 脏+重绘仅 CustomFrameNode | — | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1,R-2,R-3 RenderNode/onDraw | 单测 | Proxy 返 null、FireDrawCallback 上下文 |
| VM-2 | R-4,R-5,R-6 视觉状态 | 单测 | 默认 1.0/false、父链 HIDDEN |
| VM-3 | R-7,R-8,R-9 挂载/渲染状态 | 单测 | isAttached==isVisible quirk、rsNode |
| VM-4 | R-10,R-11,R-12 刷新 | 单测 | MarkModifyDone vs invalidate |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| getRenderNode() | Public | — | RenderNode\|null | — | 关联 RenderNode | AC-1 |
| onDraw?(context) | Public | context: DrawContext | void | — | 自定义绘制回调 | AC-1 |
| getOpacity() | Public | — | number | — | 透明度(默认1.0) | AC-2 |
| isVisible() | Public | — | boolean | — | 可见性(父链) | AC-2 |
| isClipToFrame() | Public | — | boolean | — | 裁剪(默认false) | AC-2 |
| isAttached() | Public | — | boolean | — | 挂载状态(等同isVisible) | AC-3 |
| isInRenderState() | Public | — | boolean | — | 渲染树状态 | AC-3 |
| invalidateAttributes() | Public | — | void | — | 刷新属性同步 | AC-4 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**getRenderNode / onDraw**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getRenderNode(): RenderNode\|null`(@since 11 dyn); `onDraw?(context: DrawContext): void`(@since 12 dyn/23 static，动态可选/静态必填) |
| 返回值 | RenderNode\|null / void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | renderNode_ 非空 | 返回 renderNode_ | AC-1.1 |
| 2 | ProxyFrameNode | 返回 null | AC-1.2 |
| 3 | 定义 onDraw | SetDrawFunc 注入；FireDrawCallback {size,sizeInPixel,canvas} | AC-1.3 |
| 4 | 未定义 onDraw | 静默返回 | AC-1.4 |

**getOpacity / isVisible / isClipToFrame / isAttached / isInRenderState**

| 属性 | 值 |
|------|-----|
| 函数签名 | 见 API 变更分析 (@since 12/23; isInRenderState @since 23) |
| 返回值 | number / boolean |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-2,3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | getOpacity | 默认 1.0 | AC-2.1 |
| 2 | isVisible 父链全 VISIBLE | true | AC-2.2 |
| 3 | 任一祖先 HIDDEN/GONE | false | AC-2.3 |
| 4 | isClipToFrame | 默认 false | AC-2.4 |
| 5 | isAttached | 等同 isVisible（quirk） | AC-3.1 |
| 6 | isInRenderState | rsNode GetIsOnTheTree | AC-3.2 |

**invalidateAttributes**

| 属性 | 值 |
|------|-----|
| 函数签名 | `invalidateAttributes(): void`(@since 21 dyn/23 static) |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-4 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | nodePtr 非空 | applyAttributesFinish→MarkModifyDone | AC-4.1 |
| 2 | nodePtr 空 | 静默 no-op | AC-4.2 |
| 3 | vs invalidate | MarkModifyDone(无新帧) vs render 脏+RequestNextFrame(仅 CustomFrameNode) | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** getRenderNode API 11；其余 API 12；invalidateAttributes API 21；isInRenderState API 23；静态 @since 23。
- **API 版本号策略:** 逐 API @since 标注；onDraw 动态可选、静态必填。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| isAttached 实际等同 isVisible（非主树语义） | bridge IsAttached 调用 isVisible modifier；主树语义由 isOnMainTree 承载；bridge 函数名与 modifier 调用名互换 | bridge:2183; modifier:586; arkts_native_api_impl_bridge.cpp:1287 |
| onDraw 动态可选/静态必填不一致 | 类型层强制，非运行时检查 | FrameNode.d.ts vs .static.d.ets |
| invalidateAttributes 不触发新帧 | 与 invalidate 不同，仅 MarkModifyDone；用户若期望重绘须用 invalidate | frame_node.cpp:3433 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| isAttached==isVisible | 二者行为等同；主树语义在 Feat-01 isOnMainTree | AC-3.1 |
| onDraw 路径 | SetDrawFunc→CustomFrameNodePattern→RenderNodeModifier（与 RenderNode.draw 独立路径） | AC-1.3 |
| invalidate 仅 CustomFrameNode | 非 CustomFrameNode 静默 no-op | AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | FireDrawCallback 构建 JsCanvas，高频绘制有开销 | 单测 | arkts_native_render_node_bridge.cpp:197 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 否 | 不直接影响（colorMode 在 Feat-08） | — |
| 版本升级 | 是 | invalidateAttributes(21)/isInRenderState(23) 版本演进 | AC-3.2,4.1 |

## 行为场景

```gherkin
Feature: FrameNode 渲染上下文与视觉状态
  Scenario: isAttached 等同 isVisible
    Given 节点 N 父链全 VISIBLE
    When 调用 N.isAttached() 与 N.isVisible()
    Then 二者返回值一致

  Scenario: invalidateAttributes 不触发新帧
    Given 节点 N
    When 调用 N.invalidateAttributes()
    Then 仅 MarkModifyDone，不请求下一帧
    And 若需重绘须另调 invalidate()
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（渲染/视觉状态；不含事件 Feat-06）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "CustomFrameNodePattern SetDrawCallback/RenderNodeModifier 与 RenderNodeBridge FireDrawCallback 绘制链"
  - repo: "openharmony/arkui_ace_engine"
    query: "isAttached bridge 调 isVisible modifier 的名称互换 quirk 与 isOnMainTree 主树语义"
  - repo: "openharmony/arkui_ace_engine"
    query: "MarkModifyDone vs InvalidateInFrameNode(CustomFrameNode) 刷新语义差异"
```
