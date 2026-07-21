# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 组件共享元素动画 (Geometry Transition) 全量规格 |
| 特性编号 | Func-03-02-07-Feat-01 |
| FuncID | 03-02-07 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | geometryTransition(id) 属性方法 | @since 7，common.d.ts:24152 |
| ADDED | GeometryTransition 类（Build/Update/OnReSync/WillLayout/DidLayout/SyncGeometry） | `geometry_transition.h:29` |
| ADDED | State 状态机（IDLE/ACTIVE/IDENTITY） | `geometry_transition.h:68-72` |
| MODIFIED | geometryTransition(id, options?) 新增 GeometryTransitionOptions 参数 | @since 11，common.d.ts:24168 |
| ADDED | GeometryTransitionOptions.follow（boolean，默认 false） | @since 11，common.d.ts:4751 |
| ADDED | GeometryTransitionOptions.hierarchyStrategy（TransitionHierarchyStrategy，默认 ADAPTIVE） | @since 12 systemapi，common.d.ts:4769 |
| ADDED | TransitionHierarchyStrategy 枚举（NONE / ADAPTIVE） | @since 12 systemapi，common.d.ts:5108 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/07-geometry-transition/design.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础 Hero 动画

**角色**: 应用开发者
**期望**: 我想要在 if/else 条件分支间实现组件的 Hero 动画过渡
**价值**: 以便在条件切换时提供连贯的视觉焦点引导

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在 if 分支组件 A 和 else 分支组件 B 上设置 `geometryTransition("heroId")` THEN 条件切换时 Build 阶段匹配 inNode_ 和 outNode_（`geometry_transition.cpp:138-209`） | 正常 |
| AC-1.2 | WHEN inNode 出现且 outNode 消失 THEN inNode 从 outNode 尺寸/位置开始（active），动画到自身位置（identity）；outNode 从自身开始，动画到 inNode 尺寸/位置（`geometry_transition.cpp:28-33` 注释） | 正常 |
| AC-1.3 | WHEN id 为空字符串 THEN 清除绑定关系，不产生 Hero 动画（`common.d.ts:24143-24144`） | 边界 |
| AC-1.4 | WHEN 一个 id 绑定超过两个组件 THEN 仅前两个组件作为 in/out 生效（`common.d.ts:24145` 注明 one ID bound to only two components） | 边界 |

### US-2: 状态机驱动

**角色**: 框架开发者
**期望**: 我想要了解 GeometryTransition 的状态机如何驱动布局和动画
**价值**: 以便理解布局修改和恢复时机

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Build 阶段 isNodeIn=true 且 isImplicitAnimationOpen THEN state_ 从 IDLE 转为 ACTIVE，MarkLayoutDirty(inNode, 1)（`geometry_transition.cpp:192-193`） | 正常 |
| AC-2.2 | WHEN DidLayout 检测到 IsNodeInAndActive THEN state_ 转为 IDENTITY，恢复 layoutPropertyIn_，AddAfterLayoutTask → SyncGeometry（`geometry_transition.cpp:252-261`） | 正常 |
| AC-2.3 | WHEN DidLayout 检测到 IsNodeInAndIdentity THEN state_ 转为 IDLE，hasInAnim_ = false（`geometry_transition.cpp:262-266`） | 正常 |
| AC-2.4 | WHEN isImplicitAnimationOpen 为 false 且 follow 为 false THEN hasInAnim_ 设为 false，inNode LayoutPriority=0，不产生动画（`geometry_transition.cpp:195-198`） | 边界 |

### US-3: Layout 协同与 SyncGeometry

**角色**: 框架开发者
**期望**: 我想要了解 WillLayout/DidLayout 如何协同修改布局约束
**价值**: 以便理解 active 状态下的尺寸匹配机制

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN WillLayout 检测到 IsNodeInAndActive THEN Clone LayoutProperty 到 layoutPropertyIn_，ModifyLayoutConstraint 将 inNode 尺寸约束修改为 target(outNode) 尺寸（`geometry_transition.cpp:236-237, 295-327`） | 正常 |
| AC-3.2 | WHEN SyncGeometry 执行 THEN 计算 activeFrameRect = RectF(targetPos - parentPos, inNodeActiveFrameSize_)，SetFrameWithoutAnimation 设置 inNode 帧（`geometry_transition.cpp:358-364`） | 正常 |
| AC-3.3 | WHEN SyncGeometry 中 target->IsRemoving() 为 true THEN RegisterSharedTransition(targetRenderContext, isInSameWindow)（`geometry_transition.cpp:365-372`） | 正常 |
| AC-3.4 | WHEN SyncGeometry 执行 propertyCallback THEN SyncGeometryProperties(activeFrameRect) + SetBorderRadius + SetSandBox(parentPos)（`geometry_transition.cpp:390-409`） | 正常 |
| AC-3.5 | WHEN 动画完成 finishCallback 执行 THEN DecrementGeometryTransitionCounter + SetSandBox(nullopt) + UnregisterSharedTransition（`geometry_transition.cpp:414-438`） | 正常 |

### US-4: Follow 模式

**角色**: 应用开发者
**期望**: 我想要让不在过渡中的组件也跟随匹配节点的动画
**价值**: 以便在 if 语法中实现组件持续在树上的跟随效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `geometryTransition(id, { follow: true })` 且节点始终在组件树中 THEN OnFollowWithoutTransition 创建 holder 替换 outNode，outNode 加入 disappearing 列表（`geometry_transition.cpp:493-545`，`common.d.ts:4751`） | 正常 |
| AC-4.2 | WHEN follow=true 且 direction=true（inNode 出现）THEN 创建 holder 替换 outNode，MarkLayoutDirty(outNode, -1)，hasOutAnim_=true（`geometry_transition.cpp:514-527`） | 正常 |
| AC-4.3 | WHEN follow=true 且 direction=false（inNode 消失）THEN holder 替换回 inNode，RemoveDisappearingChild，state_=ACTIVE，MarkLayoutDirty(inNode, 1)（`geometry_transition.cpp:529-543`） | 正常 |
| AC-4.4 | WHEN follow 未设置或为 false THEN OnFollowWithoutTransition 返回 false，不创建 holder（`geometry_transition.cpp:495`） | 边界 |

### US-5: ReSync 动态同步

**角色**: 框架开发者
**期望**: 我想要在 outNode 动画运行中 inNode 尺寸变化时自动重新同步
**价值**: 以便保证动画期间双向贴合的一致性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN outNode 动画运行中 inNode 的 size 或 pos 变化超过 1px THEN OnReSync 触发 AnimateWithSandBox 重新驱动 outNode（`geometry_transition.cpp:626-681`） | 正常 |
| AC-5.2 | WHEN 仅 posChanged（size 未变）THEN 直接 SyncGeometryProperties(activeFrameRect) 更新位置（`geometry_transition.cpp:664-668`） | 正常 |
| AC-5.3 | WHEN sizeChanged THEN hasOutAnim_=true，inNodeAbsRect_ 更新，MarkLayoutDirty(outNode)（`geometry_transition.cpp:670-675`） | 正常 |
| AC-5.4 | WHEN isSynced_ 为 false 或 outNodeTargetAbsRect_ 无效 THEN OnReSync 直接返回不处理（`geometry_transition.cpp:628`） | 边界 |
| AC-5.5 | WHEN animationOption_ 有效 THEN 使用 animationOption_ 驱动 ReSync 动画；否则使用 AnimationOption(Curves::LINEAR, RESYNC_DURATION=1)（`geometry_transition.cpp:662`） | 正常 |

### US-6: hierarchyStrategy 层级策略

**角色**: 应用开发者
**期望**: 我想要控制 in/out 组件在动画期间的层级提升策略
**价值**: 以便修正复杂组件树中层叠关系错误

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 未设置 hierarchyStrategy THEN 使用默认 TransitionHierarchyStrategy.ADAPTIVE，低层级组件提升到高层级（`common.d.ts:4762`） | 正常 |
| AC-6.2 | WHEN 设置 hierarchyStrategy = TransitionHierarchyStrategy.NONE THEN in/out 组件保持原层级，受父组件缩放/位置影响（`common.d.ts:5119`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2 | TASK-GEOMETRY-01 | UT | geometry_transition 单测 |
| AC-2.1 ~ AC-2.4 | R-3, R-4 | TASK-GEOMETRY-01 | UT | 状态机转换测试 |
| AC-3.1 ~ AC-3.5 | R-5, R-6 | TASK-GEOMETRY-01 | UT | Layout 协同测试 |
| AC-4.1 ~ AC-4.4 | R-7, R-8 | TASK-GEOMETRY-01 | UT | follow 模式测试 |
| AC-5.1 ~ AC-5.5 | R-9, R-10 | TASK-GEOMETRY-01 | UT | ReSync 测试 |
| AC-6.1 ~ AC-6.2 | R-11 | TASK-GEOMETRY-01 | 手工 | hierarchyStrategy 视觉验证 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 两组件设置相同 id，条件切换 | Build 匹配 inNode_/outNode_，state_=ACTIVE，hasInAnim_=true | id 非空，两组件有效 | AC-1.1 |
| R-2 | 行为 | inNode active | inNode 从 outNode 尺寸/位置开始，DidLayout 后 state_=IDENTITY，SyncGeometry 驱动动画到自身位置 | `geometry_transition.cpp:28-33, 252-261` | AC-1.2 |
| R-3 | 行为 | Build 中 isNodeIn=true 且 isImplicitAnimationOpen | state_ IDLE→ACTIVE，MarkLayoutDirty(inNode, 1) | `geometry_transition.cpp:192-193` | AC-2.1 |
| R-4 | 边界 | isImplicitAnimationOpen=false 且 follow=false | hasInAnim_=false，inNode LayoutPriority=0，SetFrameSize(SizeF())，不产生动画 | `geometry_transition.cpp:195-198` | AC-2.4 |
| R-5 | 行为 | WillLayout 检测 IsNodeInAndActive | Clone LayoutProperty → layoutPropertyIn_，ModifyLayoutConstraint 修改尺寸为 target 尺寸 | `geometry_transition.cpp:236-237` | AC-3.1 |
| R-6 | 行为 | SyncGeometry 执行 | 计算 activeFrameRect，SetFrameWithoutAnimation，propertyCallback: SyncGeometryProperties + SetBorderRadius + SetSandBox | `geometry_transition.cpp:358-409` | AC-3.2, AC-3.4 |
| R-7 | 行为 | follow=true 且 direction=true | 创建 holder 替换 outNode，AddDisappearingChild，MarkLayoutDirty(outNode, -1) | `geometry_transition.cpp:514-527` | AC-4.1, AC-4.2 |
| R-8 | 边界 | follow=false 或未设置 | OnFollowWithoutTransition 返回 false，不创建 holder | `geometry_transition.cpp:495` | AC-4.4 |
| R-9 | 行为 | outNode 动画中 inNode size/pos 变化 >1px | OnReSync → AnimateWithSandBox 重新驱动 outNode | sizeChanged || posChanged | AC-5.1 |
| R-10 | 边界 | isSynced_=false 或 outNodeTargetAbsRect_ 无效 | OnReSync 直接返回，不处理 | `geometry_transition.cpp:628` | AC-5.4 |
| R-11 | 行为 | 未设置 hierarchyStrategy | 使用 ADAPTIVE，低层级提升到高层级，解耦父组件 | 默认值 common.d.ts:4762 | AC-6.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | id 匹配、空 id 清除、超过两组件限制 |
| VM-2 | AC-2.1 ~ AC-2.4 | UT | 状态机 IDLE→ACTIVE→IDENTITY→IDLE 转换 |
| VM-3 | AC-3.1 ~ AC-3.5 | UT | WillLayout Clone/Modify、DidLayout 状态推进、SyncGeometry activeFrameRect |
| VM-4 | AC-4.1 ~ AC-4.4 | UT | follow holder 创建/销毁、disappearing 管理 |
| VM-5 | AC-5.1 ~ AC-5.5 | UT | ReSync 触发条件、posChanged/sizeChanged 分支 |
| VM-6 | AC-6.1 ~ AC-6.2 | 手工 | hierarchyStrategy ADAPTIVE/NONE 视觉效果 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| geometryTransition(id) | Public | id: string | T | N/A | 设置组件级 Hero 动画绑定 | AC-1.1 |
| geometryTransition(id, options?) | Public | id: string, options?: GeometryTransitionOptions | T | N/A | 带选项的 Hero 动画绑定 | AC-4.1, AC-6.1 |
| GeometryTransitionOptions | Public/System | follow?: boolean, hierarchyStrategy?: TransitionHierarchyStrategy | — | N/A | 过渡选项 | AC-4.1, AC-6.1 |
| TransitionHierarchyStrategy | System | NONE=0 / ADAPTIVE | — | N/A | 层级策略枚举 | AC-6.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| geometryTransition(id) | MODIFIED | @since 11 新增 options 重载 | 新增可选参数，行为兼容 | AC-1.1 |

> 截至当前版本，geometryTransition 未发现任何 @deprecated 标注的 API。

## 接口规格

### 接口定义

**geometryTransition**

| 属性 | 值 |
|------|-----|
| 函数签名 | `geometryTransition(id: string, options?: GeometryTransitionOptions): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id | string | 是 | — | 空字符串 → 清除绑定；非空 → 匹配同 id 的另一组件 |
| options.follow | boolean | 否 | false | 仅 if 语法中生效 |
| options.hierarchyStrategy | TransitionHierarchyStrategy | 否 | ADAPTIVE | systemapi @since 12 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 两组件同 id，条件切换 | Build 匹配 in/out，ACTIVE 状态，SyncGeometry 驱动动画 | AC-1.1, AC-1.2 |
| 2 | id 为空字符串 | 清除绑定，不产生动画 | AC-1.3 |
| 3 | follow=true 且节点始终在树上 | 创建 holder 替换 outNode，outNode 加入 disappearing | AC-4.1 |
| 4 | isImplicitAnimationOpen=false | 不产生动画，hasInAnim_=false | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 11+: geometryTransition 新增 options 重载，follow 参数
  - API 12+: hierarchyStrategy systemapi 新增
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 基础 @since 7，options @since 11，hierarchyStrategy @since 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| id 唯一配对 | 一个 id 最多绑定两个组件作为 in/out | AC-1.4 |
| State 三态 | IDLE/ACTIVE/IDENTITY 由 Build/DidLayout 驱动 | AC-2.1 ~ AC-2.3 |
| isImplicitAnimationOpen 前置 | 无隐式动画上下文时不产生 Hero 动画 | AC-2.4 |
| follow 仅 if 语法 | followWithoutTransition_ 仅在节点始终在树上时生效 | AC-4.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Hero 动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | holder 节点在动画结束后销毁 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | ReSync 期间不崩溃，IsGeometryTransitionAnimating 防重入 | UT | ReSync 测试 |
| 问题定位 | TAG_LOGD/TAG_LOGI ACE_GEOMETRY_TRANSITION 标签覆盖 | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | Hero 动画为视觉效果，不影响无障碍属性 | — |
| 大字体 | 否 | Hero 动画不涉及字体 | — |
| 深色模式 | 否 | Hero 动画不涉及颜色属性 | — |
| 多窗口/分屏 | 是 | isInSameWindow 判断影响 RegisterSharedTransition | AC-3.3 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | @since 7/11/12 版本策略 | AC-1.1, AC-4.1 |
| 生态兼容 | 否 | 无 C API | — |

## 行为场景（Gherkin）

```gherkin
Feature: 组件共享元素动画
  作为应用开发者
  我想要在 if/else 条件分支间实现 Hero 动画
  以便在条件切换时提供连贯的视觉焦点引导

  Scenario: 基础 Hero 动画
    Given if 分支组件 A 和 else 分支组件 B 设置了 geometryTransition("heroId")
    When 条件从 A 切换到 B
    Then Build 阶段匹配 inNode(B) 和 outNode(A)
    And state_ = ACTIVE
    And inNode 从 outNode 尺寸/位置开始
    And 动画到 inNode 自身位置（identity）

  Scenario: 空 id 清除绑定
    Given 组件设置了 geometryTransition("")
    When 条件切换
    Then 不产生 Hero 动画
    And 组件正常切换

  Scenario: 无隐式动画上下文
    Given 组件设置了 geometryTransition("heroId")
    When 条件切换但不在 AnimationUtils::Animate 上下文中
    Then hasInAnim_ = false
    And 不产生 Hero 动画

  Scenario: follow 模式
    Given 组件设置了 geometryTransition("heroId", { follow: true })
    When 节点始终在组件树中，条件切换
    Then 创建 holder 替换 outNode
    And outNode 加入 disappearing 列表
    And outNode 独立动画

  Scenario: ReSync 动态同步
    Given outNode 动画正在运行
    When inNode 尺寸变化超过 1px
    Then OnReSync 触发
    And AnimateWithSandBox 重新驱动 outNode
    And outNode 平滑过渡到新的 inNode 尺寸/位置

  Scenario Outline: hierarchyStrategy 策略
    Given 组件设置了 geometryTransition("heroId", { hierarchyStrategy: <strategy> })
    When 条件切换
    Then 层级关系按 <expected> 处理

    Examples:
      | strategy | expected |
      | ADAPTIVE | 低层级组件提升到高层级 |
      | NONE | 保持原层级 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "GeometryTransition Build 阶段 inNode/outNode 匹配和 SwapInAndOut 逻辑"
  - repo: "openharmony/ace_engine"
    query: "GeometryTransition State 状态机 IDLE/ACTIVE/IDENTITY 转换"
  - repo: "openharmony/ace_engine"
    query: "GeometryTransition SyncGeometry 和 AnimateWithSandBox 实现"
  - repo: "openharmony/ace_engine"
    query: "GeometryTransition OnFollowWithoutTransition holder 创建/销毁"
  - repo: "openharmony/ace_engine"
    query: "GeometryTransition OnReSync 动态同步机制"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 源码入口: `frameworks/core/components_ng/animation/geometry_transition.h/.cpp`
