# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Scroll 滚动事件与可观测性 |
| 特性编号 | Func-05-03-07-Feat-05 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ 21+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 onScroll(弃用)/onWillScroll/onDidScroll/onScrollEdge/onScrollStart/onScrollStop/onScrollFrameBegin/onReachStart/onReachEnd/onWillStartDragging/onDidStopDragging/onWillStartFling/onDidStopFling 及 C-API 事件。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/07-scroll/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll.d.ts` + `common.d.ts` |
| EventHub | `frameworks/core/components_ng/pattern/scroll/scroll_event_hub.h` |
| BaseEventHub | `frameworks/core/components_ng/pattern/scrollable/scrollable_event_hub.h` |
| Pattern Source | `frameworks/core/components_ng/pattern/scroll/scroll_pattern.cpp` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 滚动过程回调

作为**应用开发者**，我想要**用 onWillScroll/onDidScroll 感知并控制滚动偏移**，以便**联动 UI/拦截滚动**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `onWillScroll(handler)`（@since 12） THEN 每帧滚动触发，handler 可返回 OffsetResult 拦截控制最终偏移 | 正常 |
| AC-1.2 | WHEN 设置 `onDidScroll(handler)`（@since 12） THEN 滚动后触发，仅通知不可拦截 | 正常 |
| AC-1.3 | WHEN 使用 `onScroll`（@since 7，弃用 12） THEN 仍触发但仅通知，建议迁移 onWillScroll | 边界 |
| AC-1.4 | WHEN onWillScroll 返回 OffsetResult THEN 最终偏移按返回值调整 | 正常 |

### US-2: 边界与起停回调

作为**应用开发者**，我想要**用 onScrollEdge/onReachStart/onReachEnd 感知边界**，以便**加载更多/标记首尾**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 到达边缘 THEN `onScrollEdge(side: Edge)` 触发（@since 7/18 签名） | 正常 |
| AC-2.2 | WHEN 到达起始 THEN `onReachStart` 触发（@since 11，继承） | 正常 |
| AC-2.3 | WHEN 到达末端 THEN `onReachEnd` 触发（@since 11，继承） | 正常 |
| AC-2.4 | WHEN 滚动开始 THEN `onScrollStart` 触发（@since 9/18） | 正常 |
| AC-2.5 | WHEN 滚动停止 THEN `onScrollStop` 触发（@since 9/18）；旧 `onScrollEnd` 弃用 9 | 正常 |
| AC-2.6 | WHEN 帧滚动前 THEN `onScrollFrameBegin(offset,state)` 触发，可返回 offsetRemain 调整剩余（@since 9/18） | 正常 |

### US-3: 拖拽与 fling 回调

作为**应用开发者**，我想要**用拖拽/fling 起停回调感知手势阶段**，以便**精细化交互**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 拖拽将开始 THEN `onWillStartDragging` 触发（@since 21，继承） | 正常 |
| AC-3.2 | WHEN 拖拽将停止 THEN `onWillStopDragging(handler)` 触发（@since 20，继承），handler 可决定是否停止 | 正常 |
| AC-3.3 | WHEN 拖拽已停止 THEN `onDidStopDragging` 触发（@since 21，继承） | 正常 |
| AC-3.4 | WHEN fling 将开始 THEN `onWillStartFling` 触发（@since 21，继承） | 正常 |
| AC-3.5 | WHEN fling 已停止 THEN `onDidStopFling` 触发（@since 21，继承） | 正常 |
| AC-3.6 | WHEN C-API 注册 `NODE_SCROLL_EVENT_ON_SCROLL/WILL_SCROLL/DID_SCROLL/SCROLL_FRAME_BEGIN/SCROLL_START/SCROLL_STOP/SCROLL_EDGE/REACH_START/REACH_END/WILL_STOP_DRAGGING/DID_STOP_DRAGGING/WILL_START_DRAGGING/WILL_START_FLING/DID_STOP_FLING` THEN 事件经 event_converter 触发 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-5 | 单元测试：onWillScroll 拦截 | `scroll.d.ts:1490` |
| AC-1.2 | R-2 | TASK-SKELETON-5 | 单元测试：onDidScroll | `scroll.d.ts:1509` |
| AC-1.3 | R-3 | TASK-SKELETON-5 | 单元测试：onScroll 弃用 | `scroll.d.ts:1471` |
| AC-1.4 | R-1 | TASK-SKELETON-5 | 单元测试：OffsetResult 拦截 | `scroll.d.ts:2066` |
| AC-2.1 | R-4 | TASK-SKELETON-5 | 单元测试：onScrollEdge | `scroll.d.ts:1556` |
| AC-2.2 | R-5 | TASK-SKELETON-5 | 单元测试：onReachStart | `common.d.ts` |
| AC-2.3 | R-5 | TASK-SKELETON-5 | 单元测试：onReachEnd | `common.d.ts` |
| AC-2.4 | R-6 | TASK-SKELETON-5 | 单元测试：onScrollStart | `scroll.d.ts:1601` |
| AC-2.5 | R-7 | TASK-SKELETON-5 | 单元测试：onScrollStop | `scroll.d.ts:1663` |
| AC-2.6 | R-8 | TASK-SKELETON-5 | 单元测试：onScrollFrameBegin | `scroll.d.ts:1889` |
| AC-3.1 | R-9 | TASK-SKELETON-5 | 单元测试：onWillStartDragging | `common.d.ts` |
| AC-3.2 | R-10 | TASK-SKELETON-5 | 单元测试：onWillStopDragging | `common.d.ts` |
| AC-3.3 | R-11 | TASK-SKELETON-5 | 单元测试：onDidStopDragging | `common.d.ts` |
| AC-3.4 | R-12 | TASK-SKELETON-5 | 单元测试：onWillStartFling | `common.d.ts` |
| AC-3.5 | R-12 | TASK-SKELETON-5 | 单元测试：onDidStopFling | `common.d.ts` |
| AC-3.6 | R-13 | TASK-SKELETON-5 | 单元测试：C-API 事件 | `node_scroll_modifier.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | onWillScroll | 每帧触发，可返回 OffsetResult 拦截 | @since 12 | AC-1.1, AC-1.4 |
| R-2 | 行为 | onDidScroll | 滚动后通知，不可拦截 | @since 12 | AC-1.2 |
| R-3 | 边界 | onScroll(弃用) | 仅通知，建议迁移 | @since 7，弃用 12 | AC-1.3 |
| R-4 | 行为 | onScrollEdge | 到边触发 side:Edge | @since 7/18 | AC-2.1 |
| R-5 | 行为 | onReachStart/onReachEnd | 到首尾触发 | @since 11 | AC-2.2, AC-2.3 |
| R-6 | 行为 | onScrollStart | 滚动开始触发 | @since 9/18 | AC-2.4 |
| R-7 | 行为 | onScrollStop/onScrollEnd(弃用) | 滚动停止触发 | onScrollEnd 弃用 9 | AC-2.5 |
| R-8 | 行为 | onScrollFrameBegin | 帧前触发，可返回 offsetRemain | @since 9/18 | AC-2.6 |
| R-9 | 行为 | onWillStartDragging | 拖拽将开始 | @since 21 | AC-3.1 |
| R-10 | 行为 | onWillStopDragging | 拖拽将停止，handler 可决定 | @since 20 | AC-3.2 |
| R-11 | 行为 | onDidStopDragging | 拖拽已停止 | @since 21 | AC-3.3 |
| R-12 | 行为 | onWillStartFling/onDidStopFling | fling 起停 | @since 21 | AC-3.4, AC-3.5 |
| R-13 | 行为 | C-API NODE_SCROLL_EVENT_ON_* | event_converter 触发 | 17 事件 | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-3 滚动回调 | 单元测试 | will/did/弃用 |
| VM-2 | R-4~R-8 边界起停 | 单元测试 | edge/reach/start/stop/frame |
| VM-3 | R-9~R-13 拖拽 fling 与 C-API | 单元测试 | drag/fling/C-API |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `onWillScroll(handler)` | Public（@since 12） | `ScrollOnWillScrollCallback` | `ScrollAttribute` | 无 | 可拦截滚动 | AC-1.1 |
| `onDidScroll(handler)` | Public（@since 12） | `ScrollOnScrollCallback` | `ScrollAttribute` | 无 | 滚动后通知 | AC-1.2 |
| `onScrollEdge(event)` | Public（@since 7/18） | `OnScrollEdgeCallback` | `ScrollAttribute` | 无 | 边缘回调 | AC-2.1 |
| `onScrollStart/onScrollStop(event)` | Public（@since 9/18） | `VoidCallback` | `ScrollAttribute` | 无 | 滚动起停 | AC-2.4, AC-2.5 |
| `onScrollFrameBegin(event)` | Public（@since 9/18） | `OnScrollFrameBeginCallback` | `ScrollAttribute` | 无 | 帧前回调 | AC-2.6 |
| `onReachStart/onReachEnd` | Public（@since 11，继承） | `()=>void` | `ScrollAttribute` | 无 | 首尾回调 | AC-2.2, AC-2.3 |
| `onWillStartDragging/onDidStopDragging/onWillStartFling/onDidStopFling` | Public（@since 21，继承） | `VoidCallback` | `ScrollAttribute` | 无 | 拖拽/fling 起停 | AC-3.1~3.5 |
| `onWillStopDragging(handler)` | Public（@since 20，继承） | `OnWillStopDraggingCallback` | `ScrollAttribute` | 无 | 拖拽将停可决定 | AC-3.2 |
| C-API 17 个 `NODE_SCROLL_EVENT_ON_*` | Public | 事件枚举 | — | 无 | NDK 事件 | AC-3.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `onScroll` | 废弃 since 12 | 滚动通知 | 迁移至 `onWillScroll`/`onDidScroll` | AC-1.3 |
| `onScrollEnd` | 废弃 since 9 | 滚动结束 | 迁移至 `onScrollStop` | AC-2.5 |

## 接口规格

### 接口定义

**onWillScroll(handler)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollAttribute::onWillScroll(handler: ScrollOnWillScrollCallback): ScrollAttribute` |
| 返回值 | `ScrollAttribute` |
| 开放范围 | Public（@since 12） |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| handler | `(xOffset,yOffset,scrollState,scrollSource)=>void\|OffsetResult` | 是 | — | 返回 OffsetResult 拦截 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 每帧滚动 | 触发 handler | AC-1.1 |
| 2 | 返回 OffsetResult | 调整最终偏移 | AC-1.4 |

## 兼容性声明

- **已有 API 行为变更:** 是 — onScroll 弃用 12→onWillScroll（新可拦截）；onScrollEnd 弃用 9→onScrollStop
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** onScroll/onScrollEdge @7；onScrollFrameBegin/onScrollStart/onScrollStop @9；onReachStart/End @11；onWillScroll/onDidScroll @12；签名 rectify @18；drag/fling @20/21
- **API 版本号策略:** 各事件标注 @since；弃用迁移

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| onWillScroll 可拦截 | 返回 OffsetResult 控制偏移 | AC-1.1, AC-1.4 |
| 事件经 ScrollEventHub | 继承 ScrollableEventHub | AC-2.x~3.x |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 回调热路径保帧，避免昂贵操作 | 性能基准 | `scroll_event_hub.h` |
| 可测试性 | 事件触发可单测 | 单元测试 | TASK-SKELETON-5 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准事件 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无差异 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | onScroll 弃用 12；drag/fling @20/21 | AC-1.3, AC-3.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（事件；控制器在 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollEventHub onWillScroll 拦截 OffsetResult 与 FireOnDidScroll/FireOnReachStart/End 触发时机"
```

**关键文档:** `scroll.d.ts`、`scroll_event_hub.h`、`scrollable_event_hub.h`、`design.md`
