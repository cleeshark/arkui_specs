# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Scroll 核心几何/方向与布局 |
| 特性编号 | Func-05-03-07-Feat-01 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ 22+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 Scroll 创建、Scroller 绑定、scrollable 方向、initialOffset/contentStartOffset/contentEndOffset 与 ScrollLayoutAlgorithm 布局管线。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/07-scroll/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/scroll/scroll_pattern.h/.cpp` |
| LayoutAlgorithm | `frameworks/core/components_ng/pattern/scroll/scroll_layout_algorithm.h/.cpp` |
| LayoutProperty | `frameworks/core/components_ng/pattern/scroll/scroll_layout_property.h` |
| Model Source | `frameworks/core/components_ng/pattern/scroll/scroll_model_ng.cpp` |
| JSView Source | `frameworks/bridge/declarative_frontend/jsview/js_scroll.cpp` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 创建 Scroll 并绑定方向

作为**应用开发者**，我想要**通过 `Scroll({scroller})` 创建滚动容器并用 scrollable 指定方向**，以便**承载可滚动内容**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 传入 `Scroll({scroller: myScroller})` THEN ScrollPattern 创建，Scroller 与 ScrollPositionController 绑定（`scroll.d.ts:1217`、`scroll_pattern.h:48`） | 正常 |
| AC-1.2 | WHEN 不传 scroller THEN 仍可创建，控制器方法不可用直至后续绑定 | 边界 |
| AC-1.3 | WHEN 设置 `scrollable(ScrollDirection.Vertical)` THEN ScrollLayoutProperty::Axis 写 VERTICAL（默认） | 正常 |
| AC-1.4 | WHEN 设置 `scrollable(ScrollDirection.Horizontal)` THEN Axis 写 HORIZONTAL | 正常 |
| AC-1.5 | WHEN 设置 `scrollable(ScrollDirection.None)` THEN `IsScrollable()` 返回 false（`scroll_pattern.h:92-95`），不滚动 | 边界 |
| AC-1.6 | WHEN 设置 `scrollable(ScrollDirection.Free)`（小写，@since 9 弃用） THEN 仍生效但建议迁移 FREE | 边界 |
| AC-1.7 | WHEN 设置 `scrollable(ScrollDirection.FREE)`（@since 20） THEN 启用 FreeScrollController 2D 自由滚动（见 Feat-07） | 正常 |

### US-2: 初始偏移与内容区偏移

作为**应用开发者**，我想要**用 initialOffset/contentStartOffset/contentEndOffset 设定初始位置与内容区起止偏移**，以便**进入页面定位到指定位置或预留安全区**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `initialOffset(OffsetOptions)`（@since 12） THEN 首帧经 `ScrollLayoutAlgorithm::UseInitialOffset` 应用初始偏移 | 正常 |
| AC-2.2 | WHEN 不设 initialOffset THEN currentOffset_ 默认 0 | 正常 |
| AC-2.3 | WHEN 设置 `contentStartOffset(offset)`（@since 22） THEN 内容区起始偏移生效，影响 scrollableDistance 计算 | 正常 |
| AC-2.4 | WHEN 设置 `contentEndOffset(offset)`（@since 22） THEN 内容区结束偏移生效 | 正常 |
| AC-2.5 | WHEN initialOffset 越过 scrollableDistance THEN 经 ValidateOffset/EstimateInitialOffset 钳位 | 边界 |

### US-3: 布局测量管线

作为**应用开发者**，我想要**Scroll 正确测量内容尺寸与可滚动距离**，以便**滚动量计算准确**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|
| AC-3.1 | WHEN 内容尺寸大于视口 THEN scrollableDistance_=contentExtent-viewPort，可滚动 | 正常 |
| AC-3.2 | WHEN 内容尺寸≤视口 THEN scrollableDistance_=0，不可滚动（IsPositiveScrollableDistance false） | 边界 |
| AC-3.3 | WHEN FREE 模式 THEN CreateLayoutAlgorithm 用 freeScroll_ 的 2D offset 构造（`scroll_pattern.h:69-72`） | 正常 |
| AC-3.4 | WHEN Measure/Layout 执行 THEN CalcContentOffset/GetAlignmentPosition 计算偏移与对齐 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-1 | 单元测试：Create + Scroller 绑定 | `scroll_pattern.h:48` |
| AC-1.2 | R-2 | TASK-SKELETON-1 | 单元测试：无 scroller 创建 | `scroll.d.ts:1217` |
| AC-1.3 | R-3 | TASK-SKELETON-1 | 单元测试：Vertical Axis | `scroll_pattern.h` |
| AC-1.4 | R-3 | TASK-SKELETON-1 | 单元测试：Horizontal Axis | `scroll_pattern.h` |
| AC-1.5 | R-4 | TASK-SKELETON-1 | 单元测试：None 不可滚 | `scroll_pattern.h:92-95` |
| AC-1.6 | R-5 | TASK-SKELETON-1 | 单元测试：Free 弃用 | `scroll.d.ts:100` |
| AC-1.7 | R-6 | TASK-SKELETON-1 | 单元测试：FREE 启用 free | `scroll.d.ts:133` |
| AC-2.1 | R-7 | TASK-SKELETON-1 | 单元测试：initialOffset 应用 | `scroll_layout_algorithm.cpp` UseInitialOffset |
| AC-2.2 | R-8 | TASK-SKELETON-1 | 单元测试：默认 0 | `scroll_layout_algorithm.h` |
| AC-2.3 | R-9 | TASK-SKELETON-1 | 单元测试：contentStartOffset | `scroll_layout_algorithm.h` contentStartOffset_ |
| AC-2.4 | R-9 | TASK-SKELETON-1 | 单元测试：contentEndOffset | `scroll_layout_algorithm.h` |
| AC-2.5 | R-10 | TASK-SKELETON-1 | 单元测试：越界钳位 | `scroll_layout_algorithm.cpp` ValidateOffset |
| AC-3.1 | R-11 | TASK-SKELETON-1 | 单元测试：scrollableDistance | `scroll_layout_algorithm.h` |
| AC-3.2 | R-12 | TASK-SKELETON-1 | 单元测试：内容≤视口 | `scroll_pattern.h:97-100` |
| AC-3.3 | R-13 | TASK-SKELETON-1 | 单元测试：FREE 算法 | `scroll_pattern.h:69-72` |
| AC-3.4 | R-14 | TASK-SKELETON-1 | 单元测试：CalcContentOffset | `scroll_layout_algorithm.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Scroll({scroller}) 创建 | 绑定 Scroller→ScrollPositionController | scroller 可选 | AC-1.1 |
| R-2 | 边界 | 不传 scroller | 仍创建，控制器待绑定 | 后续绑定才可用 | AC-1.2 |
| R-3 | 行为 | scrollable(Vertical/Horizontal) | 写 Axis | 默认 Vertical | AC-1.3, AC-1.4 |
| R-4 | 边界 | scrollable(None) | IsScrollable false，不滚 | Axis==NONE | AC-1.5 |
| R-5 | 边界 | scrollable(Free 小写) | 弃用 @9，仍生效 | 建议迁移 FREE | AC-1.6 |
| R-6 | 行为 | scrollable(FREE) | 启用 FreeScrollController 2D | @since 20 | AC-1.7 |
| R-7 | 行为 | initialOffset(OffsetOptions) | 首帧 UseInitialOffset 应用 | @since 12 | AC-2.1 |
| R-8 | 边界 | 不设 initialOffset | currentOffset_ 默认 0 | — | AC-2.2 |
| R-9 | 行为 | contentStartOffset/EndOffset | 影响内容区起止与 scrollableDistance | @since 22 | AC-2.3, AC-2.4 |
| R-10 | 边界 | initialOffset 越界 | ValidateOffset/EstimateInitialOffset 钳位 | 不超 scrollableDistance | AC-2.5 |
| R-11 | 行为 | 内容>视口 | scrollableDistance=contentExtent-viewPort | 正 | AC-3.1 |
| R-12 | 边界 | 内容≤视口 | scrollableDistance=0，不可滚 | IsPositiveScrollableDistance false | AC-3.2 |
| R-13 | 行为 | FREE 模式 | 算法用 freeScroll_ 2D offset | `scroll_pattern.h:69-72` | AC-3.3 |
| R-14 | 行为 | Measure/Layout | CalcContentOffset/GetAlignmentPosition | — | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-6 创建与方向 | 单元测试 | Scroller 绑定与 Axis |
| VM-2 | R-7~R-10 偏移 | 单元测试 | initialOffset 应用与钳位 |
| VM-3 | R-11~R-14 布局 | 单元测试 | scrollableDistance 与算法 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `Scroll(scroller?)` | Public（@since 7） | `{scroller?: Scroller}` | `ScrollAttribute` | 无 | 创建滚动容器 | AC-1.1, AC-1.2 |
| `scrollable(value)` | Public | `ScrollDirection` | `ScrollAttribute` | 无 | 滚动方向 | AC-1.3~1.7 |
| `initialOffset(value)` | Public（@since 12） | `OffsetOptions` | `ScrollAttribute` | 无 | 初始偏移 | AC-2.1 |
| `contentStartOffset`/`contentEndOffset` | Public（@since 22，继承） | `number\|Resource` | `ScrollAttribute` | 无 | 内容区起止偏移 | AC-2.3, AC-2.4 |
| C-API `NODE_SCROLL_SCROLL_DIRECTION` | Public | 属性枚举 | — | 无 | 方向设置 | AC-1.x |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ScrollDirection.Free` | 废弃 since 9 | 小写 Free | 迁移至 `FREE`（@since 20） | AC-1.6 |

## 接口规格

### 接口定义

**scrollable(value: ScrollDirection)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollAttribute::scrollable(value: ScrollDirection): ScrollAttribute` |
| 返回值 | `ScrollAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `ScrollDirection` | 是 | Vertical | Vertical/Horizontal/None；Free 弃用9；FREE@20 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Vertical/Horizontal | 写对应 Axis | AC-1.3, AC-1.4 |
| 2 | None | 不可滚 | AC-1.5 |
| 3 | Free(小写) | 弃用生效 | AC-1.6 |
| 4 | FREE | 启用 2D free | AC-1.7 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 创建族自 API 7 连续
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（initialOffset @12；contentStart/EndOffset @22；FREE @20）
- **API 版本号策略:** 各属性标注 @since；Free 弃用 9 → FREE@20

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 基类复用 | ScrollablePattern 提供滚动基础设施 | AC-3.x |
| FREE 启用独立算法 | FreeScrollController 2D | AC-1.7, AC-3.3 |
| 越界钳位 | initialOffset 不超 scrollableDistance | AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 布局测量单帧完成 | 单元测试 | `scroll_layout_algorithm.cpp` |
| 内存 | 视口/extent 尺寸字段轻量 | 代码审查 | `scroll_layout_algorithm.h` |
| 可测试性 | 几何可单测覆盖 | 单元测试 | TASK-SKELETON-1 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准纵向 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | ScrollAccessibilityProperty 提供滚动动作 | AC-1.x |
| 大字体 | 否 | 几何不随字体 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | initialOffset @12、contentOffset @22、FREE @20 门槛 | AC-2.x, AC-1.7 |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（创建/方向/偏移/布局；滚动条/控制器/事件等在后续 Feat）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollPattern CreateLayoutAlgorithm FREE 模式与 ScrollLayoutAlgorithm UseInitialOffset/ValidateOffset 实现"
```

**关键文档:** `scroll.d.ts`、`scroll_pattern.h`、`scroll_layout_algorithm.h/.cpp`、`design.md`
