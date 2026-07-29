# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Scroll 交互/手势与嵌套滚动 |
| 特性编号 | Func-05-03-07-Feat-04 |
| 优先级 | P1 |
| 目标版本 | API 10 ~ 26+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 enableScrollInteraction/friction/enableScrollWithMouse/digitalCrownSensitivity/backToTop/nestedScroll 及对应 C-API。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/07-scroll/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll.d.ts` |
| BasePattern | `frameworks/core/components_ng/pattern/scrollable/scrollable_pattern.h/.cpp` |
| NestedBase | `frameworks/core/components_ng/pattern/scrollable/nestable_scroll_container.h` |
| Pattern Source | `frameworks/core/components_ng/pattern/scroll/scroll_pattern.cpp` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 滚动交互开关与摩擦

作为**应用开发者**，我想要**用 enableScrollInteraction/friction 控制滚动开关与灵敏度**，以便**禁用或调校滚动**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `enableScrollInteraction(true)`（默认，@since 10） THEN 手势可滚动 | 正常 |
| AC-1.2 | WHEN 设置 `enableScrollInteraction(false)` THEN 手势禁用滚动（SetScrollEnabled(false)→Axis::NONE） | 正常 |
| AC-1.3 | WHEN 设置 `friction(number|Resource)`（@since 10，默认 0.6/0.9→0.7(API11)→0.75(API12)） THEN 摩擦系数生效 | 正常 |
| AC-1.4 | WHEN 不设 friction THEN 按版本默认值 | 边界 |

### US-2: 鼠标与表冠交互

作为**应用开发者**，我想要**用 enableScrollWithMouse/digitalCrownSensitivity 支持鼠标滚轮与表冠**，以便**多输入设备适配**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `enableScrollWithMouse(enabled)`（@since 26，继承） THEN 鼠标滚轮滚动启用 | 正常 |
| AC-2.2 | WHEN 设置 `digitalCrownSensitivity(sensitivity)`（@since 18，继承） THEN 表冠灵敏度生效（穿戴） | 正常 |

### US-3: 返回顶部与嵌套滚动

作为**应用开发者**，我想要**用 backToTop/nestedScroll 控制返回顶部与父子滚动分发**，以便**复杂滚动布局**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 `backToTop(true)`（@since 15，继承） THEN 启用返回顶部手势 | 正常 |
| AC-3.2 | WHEN 不设 nestedScroll THEN 默认 `{scrollForward:SELF_ONLY,scrollBackward:SELF_ONLY}`（`scroll.d.ts:1912`） | 正常 |
| AC-3.3 | WHEN 设置 `nestedScroll({scrollForward:PARENT_FIRST,scrollBackward:SELF_ONLY})`（@since 10） THEN 父优先/子自处理 | 正常 |
| AC-3.4 | WHEN 设置 nestedScroll PARALLEL THEN 父子并行处理 | 正常 |
| AC-3.5 | WHEN 设置 nestedScroll SELF_FIRST THEN 子优先再父 | 正常 |
| AC-3.6 | WHEN C-API `NODE_SCROLL_ENABLE_SCROLL_INTERACTION/FRICTION/NESTED_SCROLL/ENABLE_SCROLL_WITH_MOUSE/BACK_TO_TOP/CONTENT_START_OFFSET/CONTENT_END_OFFSET` THEN 经 node_modifier 写基类 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-4 | 单元测试：true 可滚 | `scrollable_pattern.cpp` |
| AC-1.2 | R-1 | TASK-SKELETON-4 | 单元测试：false 禁用 | `scrollable_pattern.cpp` |
| AC-1.3 | R-2 | TASK-SKELETON-4 | 单元测试：friction | `scroll.d.ts:1962` |
| AC-1.4 | R-3 | TASK-SKELETON-4 | 单元测试：版本默认 | `scroll.d.ts:1962` |
| AC-2.1 | R-4 | TASK-SKELETON-4 | 单元测试：mouse | `common.d.ts` |
| AC-2.2 | R-5 | TASK-SKELETON-4 | 单元测试：crown | `common.d.ts` |
| AC-3.1 | R-6 | TASK-SKELETON-4 | 单元测试：backToTop | `common.d.ts` |
| AC-3.2 | R-7 | TASK-SKELETON-4 | 单元测试：默认 SELF_ONLY | `scroll.d.ts:1912` |
| AC-3.3 | R-8 | TASK-SKELETON-4 | 单元测试：PARENT_FIRST | `nestable_scroll_container.h` |
| AC-3.4 | R-8 | TASK-SKELETON-4 | 单元测试：PARALLEL | `nestable_scroll_container.h` |
| AC-3.5 | R-8 | TASK-SKELETON-4 | 单元测试：SELF_FIRST | `nestable_scroll_container.h` |
| AC-3.6 | R-9 | TASK-SKELETON-4 | 单元测试：C-API | `node_scroll_modifier.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | enableScrollInteraction(true/false) | 可滚/禁用；false→Axis::NONE | 默认 true；@since 10 | AC-1.1, AC-1.2 |
| R-2 | 行为 | friction(number/Resource) | 摩擦系数生效 | @since 10 | AC-1.3 |
| R-3 | 边界 | 不设 friction | 按版本默认(0.6→0.7→0.75) | 版本相关 | AC-1.4 |
| R-4 | 行为 | enableScrollWithMouse | 鼠标滚轮启用 | @since 26 | AC-2.1 |
| R-5 | 行为 | digitalCrownSensitivity | 表冠灵敏度 | @since 18，穿戴 | AC-2.2 |
| R-6 | 行为 | backToTop(true) | 返回顶部手势 | @since 15 | AC-3.1 |
| R-7 | 边界 | 不设 nestedScroll | 默认 SELF_ONLY 双向 | — | AC-3.2 |
| R-8 | 行为 | nestedScroll(mode) | 父子分发：SELF_ONLY/SELF_FIRST/PARENT_FIRST/PARALLEL | @since 10 | AC-3.3~3.5 |
| R-9 | 行为 | C-API ENABLE_SCROLL_INTERACTION/FRICTION/NESTED_SCROLL/ENABLE_SCROLL_WITH_MOUSE/BACK_TO_TOP/CONTENT_*_OFFSET | node_modifier 写基类 | — | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-3 交互与摩擦 | 单元测试 | 开关与摩擦 |
| VM-2 | R-4~R-5 鼠标表冠 | 单元测试 | mouse/crown |
| VM-3 | R-6~R-9 返回顶与嵌套 | 单元测试 | backToTop/nestedScroll/C-API |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `enableScrollInteraction(value)` | Public（@since 10） | `boolean` | `ScrollAttribute` | 无 | 滚动开关 | AC-1.1, AC-1.2 |
| `friction(value)` | Public（@since 10） | `number\|Resource` | `ScrollAttribute` | 无 | 摩擦系数 | AC-1.3 |
| `enableScrollWithMouse(enabled)` | Public（@since 26，继承） | `boolean\|undefined` | `ScrollAttribute` | 无 | 鼠标滚轮 | AC-2.1 |
| `digitalCrownSensitivity(sensitivity)` | Public（@since 18，继承） | `Optional<CrownSensitivity>` | `ScrollAttribute` | 无 | 表冠灵敏度 | AC-2.2 |
| `backToTop(value)` | Public（@since 15，继承） | `boolean` | `ScrollAttribute` | 无 | 返回顶部 | AC-3.1 |
| `nestedScroll(value)` | Public（@since 10） | `NestedScrollOptions` | `ScrollAttribute` | 无 | 嵌套滚动 | AC-3.2~3.5 |
| C-API `NODE_SCROLL_ENABLE_SCROLL_INTERACTION/FRICTION/NESTED_SCROLL/ENABLE_SCROLL_WITH_MOUSE/BACK_TO_TOP/CONTENT_START_OFFSET/CONTENT_END_OFFSET` | Public | 属性枚举 | — | 无 | NDK 通道 | AC-3.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无废弃 | — |

## 接口规格

### 接口定义

**nestedScroll(value: NestedScrollOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollAttribute::nestedScroll(value: NestedScrollOptions): ScrollAttribute` |
| 返回值 | `ScrollAttribute` |
| 开放范围 | Public（@since 10） |
| 错误码 | N/A |
| 关联 AC | AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.scrollForward | `NestedScrollMode` | 否 | SELF_ONLY | SELF_ONLY/SELF_FIRST/PARENT_FIRST/PARALLEL |
| value.scrollBackward | `NestedScrollMode` | 否 | SELF_ONLY | 同上 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 不设 | SELF_ONLY 双向 | AC-3.2 |
| 2 | PARENT_FIRST/SELF_ONLY | 父优先/子自 | AC-3.3 |
| 3 | PARALLEL | 并行 | AC-3.4 |
| 4 | SELF_FIRST | 子优先 | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** enableScrollInteraction/friction/nestedScroll @10；digitalCrownSensitivity @18；backToTop @15；enableScrollWithMouse @26
- **API 版本号策略:** 各属性标注 @since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 嵌套经 NestableScrollContainer | 基类分发 | AC-3.x |
| enableScrollInteraction false→Axis::NONE | 禁用滚动 | AC-1.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 嵌套分发无额外开销 | 单元测试 | `nestable_scroll_container.h` |
| 可测试性 | 交互/嵌套可单测 | 单元测试 | TASK-SKELETON-4 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准手势 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |
| 穿戴 | digitalCrownSensitivity 适用 | 表冠交互 | 单元测试 | AC-2.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无差异 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | @10/15/18/26 门槛 | AC-1.x~3.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（交互/手势/嵌套；事件在 Feat-05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollablePattern SetScrollEnabled/SetFriction 与 NestableScrollContainer 嵌套分发实现"
```

**关键文档:** `scroll.d.ts`、`scrollable_pattern.h/.cpp`、`nestable_scroll_container.h`、`design.md`
