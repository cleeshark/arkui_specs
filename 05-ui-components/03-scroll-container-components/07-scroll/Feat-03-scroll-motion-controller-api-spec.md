# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Scroll 滚动运动控制器 API |
| 特性编号 | Func-05-03-07-Feat-03 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ 26+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 Scroller 控制器全量方法：scrollTo/scrollEdge/fling/scrollPage/scrollBy/scrollToIndex/currentOffset/offset/isAtEnd/getItemRect/getItemIndex/contentSize/getFrameNode/flingSpeedLimit。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/07-scroll/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll.d.ts` |
| ControllerBase | `frameworks/core/components/scroll/scroll_controller_base.h/.cpp` |
| PositionController | `frameworks/core/components/scroll/scroll_position_controller.h/.cpp` |
| ScrollableController | `frameworks/core/components_ng/pattern/scrollable/scrollable_controller.h` |
| Pattern Source | `frameworks/core/components_ng/pattern/scroll/scroll_pattern.cpp` |
| JSScroller | `frameworks/bridge/declarative_frontend/jsview/js_scroller.cpp` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 程序化定位与边界滚动

作为**应用开发者**，我想要**用 scrollTo/scrollEdge 程序化滚动到指定位置或边界**，以便**代码控制滚动位置**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `scrollTo(ScrollOptions)`（@since 18，含 xOffset/yOffset/animation/canOverScroll） THEN 经 ScrollPositionController→ScrollPattern::ScrollTo 滚动 | 正常 |
| AC-1.2 | WHEN 调用 `scrollEdge(Edge, ScrollEdgeOptions?)`（@since 12 velocity） THEN 滚动到指定边界 | 正常 |
| AC-1.3 | WHEN 调用 `fling(velocity)`（@since 12） THEN 以速度 fling 滚动 | 正常 |
| AC-1.4 | WHEN scrollTo 目标越界 THEN 受 edgeEffect 与 canOverScroll 约束 | 边界 |
| AC-1.5 | WHEN 未绑定 scroller THEN 控制器方法不可用 | 边界 |

### US-2: 分页与相对滚动

作为**应用开发者**，我想要**用 scrollPage/scrollBy 做分页与相对滚动**，以便**翻页/微调位置**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 `scrollPage(ScrollPageOptions)`（@since 14，{next,animation?}） THEN 翻一页 | 正常 |
| AC-2.2 | WHEN 调用 `scrollPage({next,direction?})`（@since 7 弃用 9） THEN 仍生效但建议新签名 | 边界 |
| AC-2.3 | WHEN 调用 `scrollBy(dx,dy)`（@since 9） THEN 相对偏移滚动 | 正常 |
| AC-2.4 | WHEN 调用 `scrollToIndex(value, smooth?, align?, options?)`（@since 12） THEN 滚动到子项索引（Scroll 通常单子节点，索引受限） | 正常 |

### US-3: 位置查询与尺寸

作为**应用开发者**，我想要**用 currentOffset/offset/isAtEnd/getItemRect/getItemIndex/contentSize 查询状态**，以便**驱动联动逻辑**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 `currentOffset()`（@since 11） THEN 返回 OffsetResult{xOffset,yOffset} | 正常 |
| AC-3.2 | WHEN 调用 `offset()`（@since 23） THEN 返回 OffsetResult\|undefined | 正常 |
| AC-3.3 | WHEN 调用 `isAtEnd()`（@since 10/11） THEN 返回是否到达末端 | 正常 |
| AC-3.4 | WHEN 调用 `getItemRect(index)`（@since 11/12） THEN 返回子项 RectResult | 正常 |
| AC-3.5 | WHEN 调用 `getItemIndex(x,y)`（@since 14） THEN 返回坐标对应子项索引 | 正常 |
| AC-3.6 | WHEN 调用 `contentSize()`（@since 22） THEN 返回内容尺寸 SizeResult | 正常 |
| AC-3.7 | WHEN 调用 `getFrameNode()`（@since 26） THEN 返回关联 FrameNode\|undefined | 正常 |

### US-4: Fling 速度限制

作为**应用开发者**，我想要**用 flingSpeedLimit 限制 fling 最大速度**，以便**控制滚动惯性**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 设置 `flingSpeedLimit(speed)`（@since 11，默认 9000 vp/s） THEN fling 速度钳位 | 正常 |
| AC-4.2 | WHEN C-API `NODE_SCROLL_OFFSET/EDGE/PAGE/BY/FLING/SIZE/FLING_SPEED_LIMIT` 调用 THEN 经 node_modifier→ScrollPattern 方法 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-3 | 单元测试：scrollTo | `scroll.d.ts:531` |
| AC-1.2 | R-2 | TASK-SKELETON-3 | 单元测试：scrollEdge | `scroll.d.ts:569` |
| AC-1.3 | R-3 | TASK-SKELETON-3 | 单元测试：fling | `scroll.d.ts:588` |
| AC-1.4 | R-4 | TASK-SKELETON-3 | 单元测试：越界约束 | `scroll_pattern.cpp` |
| AC-1.5 | R-5 | TASK-SKELETON-3 | 单元测试：无 scroller | `scroll.d.ts:1217` |
| AC-2.1 | R-6 | TASK-SKELETON-3 | 单元测试：scrollPage 新签名 | `scroll.d.ts:623` |
| AC-2.2 | R-7 | TASK-SKELETON-3 | 单元测试：旧签名弃用 | `scroll.d.ts:636` |
| AC-2.3 | R-8 | TASK-SKELETON-3 | 单元测试：scrollBy | `scroll.d.ts:766` |
| AC-2.4 | R-9 | TASK-SKELETON-3 | 单元测试：scrollToIndex | `scroll.d.ts:733` |
| AC-3.1 | R-10 | TASK-SKELETON-3 | 单元测试：currentOffset | `scroll.d.ts:663` |
| AC-3.2 | R-10 | TASK-SKELETON-3 | 单元测试：offset | `scroll.d.ts:675` |
| AC-3.3 | R-11 | TASK-SKELETON-3 | 单元测试：isAtEnd | `scroll.d.ts:790` |
| AC-3.4 | R-12 | TASK-SKELETON-3 | 单元测试：getItemRect | `scroll.d.ts:829` |
| AC-3.5 | R-12 | TASK-SKELETON-3 | 单元测试：getItemIndex | `scroll.d.ts:851` |
| AC-3.6 | R-13 | TASK-SKELETON-3 | 单元测试：contentSize | `scroll.d.ts:863` |
| AC-3.7 | R-13 | TASK-SKELETON-3 | 单元测试：getFrameNode | `scroll.d.ts:875` |
| AC-4.1 | R-14 | TASK-SKELETON-3 | 单元测试：flingSpeedLimit | `common.d.ts` |
| AC-4.2 | R-15 | TASK-SKELETON-3 | 单元测试：C-API | `node_scroll_modifier.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | scrollTo(ScrollOptions) | ScrollPattern::ScrollTo 滚动 | @since 18；canOverScroll | AC-1.1, AC-1.4 |
| R-2 | 行为 | scrollEdge(Edge, options?) | 滚动到边界 | @since 12 velocity | AC-1.2 |
| R-3 | 行为 | fling(velocity) | 速度 fling | @since 12；受 flingSpeedLimit | AC-1.3 |
| R-4 | 边界 | scrollTo 越界 | 受 edgeEffect/canOverScroll 约束 | — | AC-1.4 |
| R-5 | 边界 | 未绑 scroller | 控制器不可用 | — | AC-1.5 |
| R-6 | 行为 | scrollPage(ScrollPageOptions) | 翻页 | @since 14 | AC-2.1 |
| R-7 | 边界 | scrollPage 旧签名 | 弃用 @9 仍生效 | 建议新签名 | AC-2.2 |
| R-8 | 行为 | scrollBy(dx,dy) | 相对偏移 | @since 9 | AC-2.3 |
| R-9 | 行为 | scrollToIndex | 滚到子项索引 | Scroll 单子节点受限 | AC-2.4 |
| R-10 | 行为 | currentOffset()/offset() | 返回 OffsetResult | @since 11/23 | AC-3.1, AC-3.2 |
| R-11 | 行为 | isAtEnd() | 返回末端布尔 | @since 10/11 | AC-3.3 |
| R-12 | 行为 | getItemRect/getItemIndex | 子项矩形/索引 | @since 11/14 | AC-3.4, AC-3.5 |
| R-13 | 行为 | contentSize()/getFrameNode() | 内容尺寸/FrameNode | @since 22/26 | AC-3.6, AC-3.7 |
| R-14 | 行为 | flingSpeedLimit | fling 速度钳位 9000vp/s | @since 11 | AC-4.1 |
| R-15 | 行为 | C-API NODE_SCROLL_OFFSET/EDGE/PAGE/BY/FLING/SIZE/FLING_SPEED_LIMIT | node_modifier→Pattern | — | AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-5 定位与边界 | 单元测试 | scrollTo/scrollEdge/fling |
| VM-2 | R-6~R-9 分页相对 | 单元测试 | scrollPage/scrollBy/scrollToIndex |
| VM-3 | R-10~R-13 查询 | 单元测试 | offset/isAtEnd/rect/index/size |
| VM-4 | R-14~R-15 速度限制与 C-API | 单元测试 | flingSpeedLimit/C-API |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `scrollTo(options)` | Public（@since 18） | `ScrollOptions` | `void` | 无 | 滚动到位置 | AC-1.1 |
| `scrollEdge(value, options?)` | Public（@since 12） | `Edge, ScrollEdgeOptions?` | `void` | 无 | 滚动到边界 | AC-1.2 |
| `fling(velocity)` | Public（@since 12） | `number` | `void` | 无 | 速度 fling | AC-1.3 |
| `scrollPage(value)` | Public（@since 14） | `ScrollPageOptions` | `void` | 无 | 翻页 | AC-2.1 |
| `scrollBy(dx,dy)` | Public（@since 9） | `Length, Length` | `void` | 无 | 相对偏移 | AC-2.3 |
| `scrollToIndex(value, smooth?, align?, options?)` | Public（@since 12） | `number, boolean?, ScrollAlign?, ScrollToIndexOptions?` | `void` | 无 | 滚到索引 | AC-2.4 |
| `currentOffset()` | Public（@since 11） | — | `OffsetResult` | 无 | 当前偏移 | AC-3.1 |
| `offset()` | Public（@since 23） | — | `OffsetResult\|undefined` | 无 | 偏移查询 | AC-3.2 |
| `isAtEnd()` | Public（@since 10/11） | — | `boolean` | 无 | 末端判断 | AC-3.3 |
| `getItemRect(index)` | Public（@since 11/12） | `number` | `RectResult` | 无 | 子项矩形 | AC-3.4 |
| `getItemIndex(x,y)` | Public（@since 14） | `number, number` | `number` | 无 | 坐标→索引 | AC-3.5 |
| `contentSize()` | Public（@since 22） | — | `SizeResult` | 无 | 内容尺寸 | AC-3.6 |
| `getFrameNode()` | Public（@since 26） | — | `FrameNode\|undefined` | 无 | 关联节点 | AC-3.7 |
| `flingSpeedLimit(speedLimit)` | Public（@since 11，继承） | `number` | `T` | 无 | fling 速度限制 | AC-4.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `scrollPage({next,direction?})` | 废弃 since 9 | 旧签名 | 迁移至 `scrollPage(ScrollPageOptions)` @14 | AC-2.2 |

## 接口规格

### 接口定义

**scrollTo(options: ScrollOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Scroller::scrollTo(options: ScrollOptions): void` |
| 返回值 | `void` |
| 开放范围 | Public（@since 18） |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options.xOffset | `Dimension` | 是 | — | 目标 x |
| options.yOffset | `Dimension` | 是 | — | 目标 y |
| options.animation | `boolean` | 否 | true | 是否动画 |
| options.canOverScroll | `boolean` | 否 | false | 是否允许越界（@since 20） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 options | ScrollTo 滚动 | AC-1.1 |
| 2 | 越界 | edgeEffect/canOverScroll 约束 | AC-1.4 |
| 3 | 未绑 scroller | 不可用 | AC-1.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（scrollPage 旧签名弃用 9）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** scrollBy @9；scrollEdge/fling/scrollToIndex/currentOffset/isAtEnd @10/11/12；scrollPage @14；scrollTo @18；offset @23；contentSize @22；getFrameNode @26
- **API 版本号策略:** 各方法标注 @since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 控制器经 ScrollableController→ScrollPositionController | 抽象复用 | AC-1.x |
| fling 受 flingSpeedLimit 钳位 | 默认 9000vp/s | AC-4.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | scrollTo 动画单帧推进 | 单元测试 | `scroll_position_controller.cpp` |
| 可测试性 | 控制器方法可单测 | 单元测试 | TASK-SKELETON-3 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 滚动动作经无障碍可达 | AC-1.x |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | @9/10/11/12/14/18/22/23/26 门槛 | AC-2.x~3.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（控制器方法；事件在 Feat-05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollPositionController scrollTo/scrollEdge/fling/scrollPage 与 ScrollPattern::ScrollTo/ScrollBy 实现"
```

**关键文档:** `scroll.d.ts`、`scroll_position_controller.cpp`、`scrollable_controller.h`、`design.md`
