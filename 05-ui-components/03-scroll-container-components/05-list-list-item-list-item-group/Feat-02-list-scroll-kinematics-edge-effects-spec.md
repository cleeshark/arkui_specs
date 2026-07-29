# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | List 滚动运动学与边缘效果 |
| 特性编号 | Func-05-03-05-Feat-02 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ 26+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 scrollBar/edgeEffect/enableScrollInteraction/friction/nestedScroll/scrollSnapAlign/scrollSnapAnimationSpeed/chainAnimation+chainAnimationOptions(systemapi)/focusWrapMode/backPressBehavior。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/design.md` |
| SDK Dynamic | `ets/dynamic/component/list.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/list/list_pattern.cpp` |
| Properties | `frameworks/core/components_ng/pattern/list/list_properties.h` |
| BasePattern | `frameworks/core/components_ng/pattern/scrollable/scrollable_pattern.h` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 滚动条与边缘效果

作为**应用开发者**，我想要**用 scrollBar/edgeEffect 控制滚动条与回弹**，以便**列表反馈**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `scrollBar(BarState)`（@since 7） THEN 滚动条显隐 | 正常 |
| AC-1.2 | WHEN 不设 edgeEffect THEN 默认 `EdgeEffect.Spring`（`list_pattern.h:62`） | 正常 |
| AC-1.3 | WHEN 设置 `edgeEffect(EdgeEffect.None)` THEN 无回弹 | 正常 |
| AC-1.4 | WHEN 设置 `edgeEffect(EdgeEffect.Spring, options?)`（options @since 11） THEN 弹簧回弹 | 正常 |
| AC-1.5 | WHEN 设置 `edgeEffect(EdgeEffect.Fade)` THEN 渐隐 | 正常 |

### US-2: 滚动交互与摩擦

作为**应用开发者**，我想要**用 enableScrollInteraction/friction 控制滚动开关与灵敏度**，以便**调校列表**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `enableScrollInteraction(boolean)`（@since 10，默认 true） THEN 滚动开关 | 正常 |
| AC-2.2 | WHEN 设置 `friction(number|Resource)`（@since 10） THEN 摩擦系数生效 | 正常 |
| AC-2.3 | WHEN 设置 `nestedScroll(NestedScrollOptions)`（@since 10） THEN 嵌套滚动分发 | 正常 |

### US-3: 吸附与链动画

作为**应用开发者**，我想要**用 scrollSnapAlign/scrollSnapAnimationSpeed/chainAnimation 配置吸附与链动画**，以便**特殊滚动效果**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 `scrollSnapAlign(ScrollSnapAlign)`（@since 10） THEN 吸附对齐 | 正常 |
| AC-3.2 | WHEN 设置 `scrollSnapAnimationSpeed(ScrollSnapAnimationSpeed)`（@since 22） THEN 吸附动画速度 | 正常 |
| AC-3.3 | WHEN 设置 `chainAnimation(boolean)`（@since 7） THEN 启用链动画 | 正常 |
| AC-3.4 | WHEN 设置 `chainAnimationOptions(ChainAnimationOptions)`（@since 10，**systemapi**） THEN 链动画参数（minSpace/maxSpace/conductivity/intensity/edgeEffect/stiffness/damping） | 正常 |
| AC-3.5 | WHEN 非系统应用设置 chainAnimationOptions THEN 不生效（systemapi 限制） | 边界 |

### US-4: 焦点包装与返回键

作为**应用开发者**，我想要**用 focusWrapMode/backPressBehavior 控制焦点与返回键**，以便**焦点与返回交互**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 设置 `focusWrapMode(Optional<FocusWrapMode>)`（@since 20） THEN 焦点包装模式 | 正常 |
| AC-4.2 | WHEN 设置 `backPressBehavior(ListBackPressBehavior)`（@since 26） THEN 系统返回键行为（含 closeSwipeAction 选项） | 正常 |
| AC-4.3 | WHEN 不设 backPressBehavior THEN 默认返回键行为 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-2 | 单元测试：scrollBar | `list.d.ts:1735` |
| AC-1.2 | R-2 | TASK-SKELETON-2 | 单元测试：默认 Spring | `list_pattern.h:62` |
| AC-1.3 | R-2 | TASK-SKELETON-2 | 单元测试：None | `list_pattern.h:62` |
| AC-1.4 | R-2 | TASK-SKELETON-2 | 单元测试：Spring options | `list.d.ts:1785` |
| AC-1.5 | R-2 | TASK-SKELETON-2 | 单元测试：Fade | `list.d.ts:1785` |
| AC-2.1 | R-3 | TASK-SKELETON-2 | 单元测试：enableScrollInteraction | `list.d.ts:2198` |
| AC-2.2 | R-4 | TASK-SKELETON-2 | 单元测试：friction | `list.d.ts:2225` |
| AC-2.3 | R-5 | TASK-SKELETON-2 | 单元测试：nestedScroll | `list.d.ts:2175` |
| AC-3.1 | R-6 | TASK-SKELETON-2 | 单元测试：scrollSnapAlign | `list.d.ts:2153` |
| AC-3.2 | R-7 | TASK-SKELETON-2 | 单元测试：snapAnimSpeed | `list.d.ts:2321` |
| AC-3.3 | R-8 | TASK-SKELETON-2 | 单元测试：chainAnimation | `list.d.ts:2082` |
| AC-3.4 | R-9 | TASK-SKELETON-2 | 单元测试：chainOptions | `list.d.ts:2093` |
| AC-3.5 | R-9 | TASK-SKELETON-2 | 单元测试：非系统不生效 | `list.d.ts:2093` systemapi |
| AC-4.1 | R-10 | TASK-SKELETON-2 | 单元测试：focusWrapMode | `list.d.ts:2296` |
| AC-4.2 | R-11 | TASK-SKELETON-2 | 单元测试：backPressBehavior | `list.d.ts:2391` |
| AC-4.3 | R-11 | TASK-SKELETON-2 | 单元测试：默认 | `list_pattern.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | scrollBar(BarState) | 滚动条显隐 | @since 7 | AC-1.1 |
| R-2 | 行为 | edgeEffect | 默认 Spring；None/Fade/Spring+options | 默认 SPRING；options @11 | AC-1.2~1.5 |
| R-3 | 行为 | enableScrollInteraction | 滚动开关；默认 true | @since 10 | AC-2.1 |
| R-4 | 行为 | friction(number/Resource) | 摩擦系数 | @since 10 | AC-2.2 |
| R-5 | 行为 | nestedScroll(NestedScrollOptions) | 嵌套分发 | @since 10 | AC-2.3 |
| R-6 | 行为 | scrollSnapAlign | 吸附对齐 | @since 10 | AC-3.1 |
| R-7 | 行为 | scrollSnapAnimationSpeed | 吸附动画速度 | @since 22 | AC-3.2 |
| R-8 | 行为 | chainAnimation(boolean) | 链动画开关 | @since 7 | AC-3.3 |
| R-9 | 行为 | chainAnimationOptions(ChainAnimationOptions) | 链动画参数；**systemapi** | @since 10，仅系统 | AC-3.4, AC-3.5 |
| R-10 | 行为 | focusWrapMode(Optional<FocusWrapMode>) | 焦点包装 | @since 20 | AC-4.1 |
| R-11 | 行为 | backPressBehavior(ListBackPressBehavior) | 系统返回键行为；含 closeSwipeAction 选项 | @since 26，非滑动 | AC-4.2, AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-2 滚动条与边缘 | 单元测试 | scrollBar/edgeEffect 默认 Spring |
| VM-2 | R-3~R-5 交互摩擦嵌套 | 单元测试 | interaction/friction/nested |
| VM-3 | R-6~R-9 吸附与链动画 | 单元测试 | snap/chain+systemapi |
| VM-4 | R-10~R-11 焦点返回 | 单元测试 | focusWrap/backPress |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `scrollBar(value)` | Public（@since 7） | `BarState` | `ListAttribute` | 无 | 滚动条显隐 | AC-1.1 |
| `edgeEffect(value, options?)` | Public（@since 7/11） | `EdgeEffect, EdgeEffectOptions?` | `ListAttribute` | 无 | 边缘效果 | AC-1.2~1.5 |
| `enableScrollInteraction(value)` | Public（@since 10） | `boolean` | `ListAttribute` | 无 | 滚动开关 | AC-2.1 |
| `friction(value)` | Public（@since 10） | `number\|Resource` | `ListAttribute` | 无 | 摩擦 | AC-2.2 |
| `nestedScroll(value)` | Public（@since 10） | `NestedScrollOptions` | `ListAttribute` | 无 | 嵌套滚动 | AC-2.3 |
| `scrollSnapAlign(value)` | Public（@since 10） | `ScrollSnapAlign` | `ListAttribute` | 无 | 吸附对齐 | AC-3.1 |
| `scrollSnapAnimationSpeed(speed)` | Public（@since 22） | `ScrollSnapAnimationSpeed` | `ListAttribute` | 无 | 吸附速度 | AC-3.2 |
| `chainAnimation(value)` | Public（@since 7） | `boolean` | `ListAttribute` | 无 | 链动画开关 | AC-3.3 |
| `chainAnimationOptions(value)` | System（@since 10） | `ChainAnimationOptions` | `ListAttribute` | 无 | 链动画参数 | AC-3.4 |
| `focusWrapMode(mode)` | Public（@since 20） | `Optional<FocusWrapMode>` | `ListAttribute` | 无 | 焦点包装 | AC-4.1 |
| `backPressBehavior(behavior)` | Public（@since 26） | `ListBackPressBehavior\|undefined` | `ListAttribute` | 无 | 返回键行为 | AC-4.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 本 Feat 无废弃（editMode 在 Feat-05） | — |

## 接口规格

### 接口定义

**edgeEffect(value, options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ListAttribute::edgeEffect(value: EdgeEffect, options?: EdgeEffectOptions): ListAttribute` |
| 返回值 | `ListAttribute` |
| 开放范围 | Public（@since 7；options @11） |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `EdgeEffect` | 是 | Spring(默认) | None/Spring/Fade |
| options | `EdgeEffectOptions` | 否 | — | @since 11 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 不设 | 默认 Spring | AC-1.2 |
| 2 | None | 无回弹 | AC-1.3 |
| 3 | Spring | 弹簧 | AC-1.4 |
| 4 | Fade | 渐隐 | AC-1.5 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** scrollBar/edgeEffect/chainAnimation @7；enableScrollInteraction/friction/nestedScroll/scrollSnapAlign/chainOptions(systemapi) @10；edgeEffect options @11；scrollSnapAnimationSpeed @22；focusWrapMode @20；backPressBehavior @26
- **API 版本号策略:** chainAnimationOptions 为 systemapi；各属性标注 @since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 默认 edgeEffect SPRING | `list_pattern.h:62` | AC-1.2 |
| chainAnimationOptions systemapi | 仅系统应用 | AC-3.4, AC-3.5 |
| backPressBehavior 系统返回键非滑动 | 区分滑动操作 | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 滚动/回弹单帧 | 单元测试 | `list_pattern.cpp` |
| 可测试性 | 运动学属性可单测 | 单元测试 | TASK-SKELETON-2 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 | 单元测试 | — |
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
| 版本升级 | 是 | @7~26 门槛 | AC-3.x~4.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（运动学/边缘；事件与控制器在 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ListPattern 默认 SPRING edgeEffect 与 chainAnimationOptions systemapi 限制"
```

**关键文档:** `list.d.ts`、`list_pattern.cpp`、`list_properties.h`、`design.md`
