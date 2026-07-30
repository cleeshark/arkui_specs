# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Refresh 下拉物理、触发/取消手势与偏移观测 |
| 特性编号 | Func-05-03-06-Feat-02 |
| 优先级 | P1 |
| 目标版本 | API 8 ~ 26+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖下拉阻尼物理（offset/friction 弃用 + refreshOffset/pullDownRatio/maxPullDownDistance）、触发/取消手势（pullToRefresh/pullUpToCancelRefresh）、偏移观测（onOffsetChange）与嵌套滚动协调。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/06-refresh/design.md` |
| SDK Dynamic | `ets/dynamic/component/refresh.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/refresh/refresh_pattern.h` / `.cpp` |
| LayoutProperty | `frameworks/core/components_ng/pattern/refresh/refresh_layout_property.h` |
| EventHub Source | `frameworks/core/components_ng/pattern/refresh/refresh_event_hub.h` |
| Model Source | `frameworks/core/components_ng/pattern/refresh/refresh_model_ng.cpp` |
| Native Header | `interfaces/native/native_node.h` |
| Component Rules | `frameworks/core/components_ng/pattern/refresh/CLAUDE.md` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 下拉阻尼与触发阈值

作为**应用开发者**，我想要**通过 refreshOffset/pullDownRatio/maxPullDownDistance 控制下拉触发距离与阻尼灵敏度**，以便**调校刷新手感**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 下拉时 `CalculatePullDownRatio` 计算 `ratio=exp(-ratio_*gamma)`，`gamma=scrollOffset/contentHeight`（CLAUDE.md），下拉位移按 ratio 阻尼 | 正常 |
| AC-1.2 | WHEN 不设 refreshOffset THEN 默认 `refreshOffset_=64.0_vp` 为触发阈值（`refresh_pattern.h:205`） | 正常 |
| AC-1.3 | WHEN 设置 `refreshOffset(value: number)`（@since 12）THEN 触发阈值更新为 value | 正常 |
| AC-1.4 | WHEN 设置 `refreshOffset(number|Resource)`（@since 26 Resource 重载）THEN 资源对象经 `CreateWithResourceObjRefreshOffset` 解析 | 正常 |
| AC-1.5 | WHEN 设置 `pullDownRatio(ratio)`（@since 12）THEN 替代废弃 friction(默认 62) 控制灵敏度 | 正常 |
| AC-1.6 | WHEN 设置 `maxPullDownDistance(distance)`（@since 20）THEN `GetMaxPullDownDistance` 钳位最大下拉距离 | 正常 |
| AC-1.7 | WHEN 设置 `maxPullDownDistance(number|Resource|undefined)`（@since 26 Resource 重载）THEN 资源解析 | 正常 |
| AC-1.8 | WHEN 使用废弃 `offset`（RefreshOptions.offset，@since 11 废弃，默认 16vp 静止距离）THEN 仍生效但语义为静止距离非触发阈值 | 边界 |
| AC-1.9 | WHEN 使用废弃 `friction`（0-100，默认 62，@since 11 废弃 → pullDownRatio）THEN 仍生效但建议迁移 | 边界 |

### US-2: 触发与取消手势

作为**应用开发者**，我想要**用 pullToRefresh 开关手势触发、用 pullUpToCancelRefresh 上拉取消刷新**，以便**控制刷新交互策略**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 不设 pullToRefresh THEN 默认 `pullToRefresh_=true`，下拉手势可触发刷新（`refresh_pattern.h:206`） | 正常 |
| AC-2.2 | WHEN 设置 `pullToRefresh(false)`（@since 12）THEN 下拉手势不触发刷新（仅编程/API 触发） | 正常 |
| AC-2.3 | WHEN 不设 pullUpToCancelRefresh THEN 默认 `pullUpToCancelRefresh_=true`，刷新中上拉可取消（`refresh_pattern.h:207`） | 正常 |
| AC-2.4 | WHEN 设置 `pullUpToCancelRefresh(false)`（@since 23）THEN 刷新中上拉不取消 | 正常 |
| AC-2.5 | WHEN 子节点不在顶部 THEN 下拉由子节点处理，Refresh 不触发（HandleScroll 检查子位置） | 边界 |

### US-3: 嵌套滚动协调

作为**应用开发者**，我想要**Refresh 与子 List/Grid/WaterFlow 协调滚动分发**，以便**避免手势冲突**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 子节点在顶部且下拉 THEN Refresh 经 HandleScroll 处理，返回消费 delta（CLAUDE.md） | 正常 |
| AC-3.2 | WHEN 上滚 THEN 子节点正常滚动，Refresh 不拦截 | 正常 |
| AC-3.3 | WHEN `NestedScrollOutOfBoundary` 被查询 THEN 返回 `!NearZero(scrollOffset_)`（`refresh_pattern.h:116-119`） | 正常 |
| AC-3.4 | WHEN 子节点滚动开始 THEN OnScrollStartRecursive 被通知；结束 OnScrollEndRecursive；速度 HandleScrollVelocity | 正常 |
| AC-3.5 | WHEN 嵌套模式为 SELF_ONLY（子仅自处理）THEN Refresh 不触发下拉 | 边界 |

### US-4: 偏移观测

作为**应用开发者**，我想要**用 onOffsetChange 实时观测下拉偏移**，以便**驱动自定义指示器动画**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 设置 `onOffsetChange(callback)`（@since 12）THEN 拖拽中 FireOnOffsetChange(value) 以 scrollOffset_ 触发 | 正常 |
| AC-4.2 | WHEN 步骤式偏移 THEN FireOnStepOffsetChange(value,isDrag) 触发（RefreshEventHub OffsetStepChangeEvent） | 正常 |
| AC-4.3 | WHEN API11+ THEN 偏移经 `offsetProperty_`(NodeAnimatablePropertyFloat) 驱动；API10- 经 `lowVersionOffset_`+RenderContext.SetOffset（`refresh_pattern.h:208,231`） | 边界 |
| AC-4.4 | WHEN 拖拽开始/结束 THEN UpdateDragFRCSceneInfo 上报 `REFRESH_DRAG_SCENE` 场景与速度（CLAUDE.md FRC） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-3 | 单元测试：阻尼公式 | CLAUDE.md CalculatePullDownRatio |
| AC-1.2 | R-2 | TASK-SKELETON-3 | 单元测试：默认 64vp | `refresh_pattern.h:205` |
| AC-1.3 | R-3 | TASK-SKELETON-3 | 单元测试：refreshOffset 设置 | `refresh_model_ng.cpp` |
| AC-1.4 | R-3 | TASK-SKELETON-3 | 单元测试：Resource 重载 | `refresh_model_ng.cpp` CreateWithResourceObjRefreshOffset |
| AC-1.5 | R-4 | TASK-SKELETON-3 | 单元测试：pullDownRatio | `refresh_layout_property.h` |
| AC-1.6 | R-5 | TASK-SKELETON-3 | 单元测试：maxPullDownDistance 钳位 | `refresh_pattern.cpp` GetMaxPullDownDistance |
| AC-1.7 | R-5 | TASK-SKELETON-3 | 单元测试：Resource 重载 | `refresh_model_ng.cpp` |
| AC-1.8 | R-6 | TASK-SKELETON-3 | 单元测试：废弃 offset 生效 | `refresh.d.ts:235` |
| AC-1.9 | R-6 | TASK-SKELETON-3 | 单元测试：废弃 friction | `refresh.d.ts:262` |
| AC-2.1 | R-7 | TASK-SKELETON-4 | 单元测试：默认 true | `refresh_pattern.h:206` |
| AC-2.2 | R-8 | TASK-SKELETON-4 | 单元测试：false 禁手势 | `refresh_pattern.cpp` |
| AC-2.3 | R-7 | TASK-SKELETON-4 | 单元测试：默认 true | `refresh_pattern.h:207` |
| AC-2.4 | R-8 | TASK-SKELETON-4 | 单元测试：false 不取消 | `refresh_pattern.cpp` |
| AC-2.5 | R-9 | TASK-SKELETON-4 | 单元测试：子非顶部不触发 | CLAUDE.md HandleDragUpdate |
| AC-3.1 | R-10 | TASK-SKELETON-4 | 单元测试：HandleScroll 消费 | `refresh_pattern.h:105` |
| AC-3.2 | R-10 | TASK-SKELETON-4 | 单元测试：上滚不拦截 | `refresh_pattern.cpp` |
| AC-3.3 | R-11 | TASK-SKELETON-4 | 单元测试：OutOfBoundary | `refresh_pattern.h:116-119` |
| AC-3.4 | R-12 | TASK-SKELETON-4 | 单元测试：递归通知 | `refresh_pattern.h:108-112` |
| AC-3.5 | R-13 | TASK-SKELETON-4 | 单元测试：SELF_ONLY 不触发 | nestable_scroll_container.h |
| AC-4.1 | R-14 | TASK-SKELETON-4 | 单元测试：onOffsetChange | `refresh_pattern.cpp` FireOnOffsetChange |
| AC-4.2 | R-14 | TASK-SKELETON-4 | 单元测试：StepOffset | `refresh_pattern.cpp` FireOnStepOffsetChange |
| AC-4.3 | R-15 | TASK-SKELETON-4 | 单元测试：版本双路径 | `refresh_pattern.h:208,231` |
| AC-4.4 | R-16 | TASK-SKELETON-4 | 单元测试：FRC 场景 | CLAUDE.md UpdateDragFRCSceneInfo |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 下拉位移计算 | `ratio=exp(-ratio_*gamma)`，gamma=scrollOffset/contentHeight | 指数阻尼，禁线性 | AC-1.1 |
| R-2 | 行为 | 不设 refreshOffset | 默认 64vp 触发阈值 | `refresh_pattern.h:205` | AC-1.2 |
| R-3 | 行为 | 设置 refreshOffset(number/Resource) | 更新触发阈值；Resource 经 CreateWithResourceObjRefreshOffset | @since 12/26 | AC-1.3, AC-1.4 |
| R-4 | 行为 | 设置 pullDownRatio | 替代废弃 friction 控制灵敏度 | @since 12 | AC-1.5 |
| R-5 | 行为 | 设置 maxPullDownDistance | GetMaxPullDownDistance 钳位最大下拉 | @since 20/26 | AC-1.6, AC-1.7 |
| R-6 | 边界 | 使用废弃 offset/friction | 仍生效；offset=16vp 静止，friction 0-100 默认 62 | @since 11 废弃 | AC-1.8, AC-1.9 |
| R-7 | 行为 | 不设 pullToRefresh/pullUpToCancelRefresh | 默认均 true | `refresh_pattern.h:206-207` | AC-2.1, AC-2.3 |
| R-8 | 行为 | pullToRefresh(false)/pullUpToCancelRefresh(false) | 禁手势触发/禁上拉取消 | @since 12/23 | AC-2.2, AC-2.4 |
| R-9 | 边界 | 子节点不在顶部 | 下拉由子处理，Refresh 不触发 | HandleScroll 检查子位置 | AC-2.5 |
| R-10 | 行为 | 子在顶部下拉/上滚 | 下拉 Refresh 消费 delta；上滚子处理不拦截 | 经 HandleScroll | AC-3.1, AC-3.2 |
| R-11 | 行为 | 查询越界 | NestedScrollOutOfBoundary 返回 !NearZero(scrollOffset_) | `refresh_pattern.h:116-119` | AC-3.3 |
| R-12 | 行为 | 子滚动开始/结束/速度 | OnScrollStartRecursive/OnScrollEndRecursive/HandleScrollVelocity 通知 | `refresh_pattern.h:108-112` | AC-3.4 |
| R-13 | 边界 | 嵌套模式 SELF_ONLY | Refresh 不触发下拉 | 子仅自处理 | AC-3.5 |
| R-14 | 行为 | 设置 onOffsetChange | FireOnOffsetChange/FireOnStepOffsetChange 以 scrollOffset_ 触发 | @since 12 | AC-4.1, AC-4.2 |
| R-15 | 边界 | API 版本分支 | 11+ offsetProperty_；10- lowVersionOffset_+SetOffset | `refresh_pattern.h:208,231` | AC-4.3 |
| R-16 | 行为 | 拖拽开始/结束 | UpdateDragFRCSceneInfo 上报 REFRESH_DRAG_SCENE 速度/状态 | FRC | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-6 阻尼与触发 | 单元测试 | 公式/默认值/Resource |
| VM-2 | R-7~R-9 触发取消手势 | 单元测试 | 默认 true/false 开关 |
| VM-3 | R-10~R-13 嵌套协调 | 单元测试 | HandleScroll/递归/SELF_ONLY |
| VM-4 | R-14~R-16 偏移观测 | 单元测试 | onOffsetChange/版本分支/FRC |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `refreshOffset(value)` / `(number\|Resource)` | Public（@since 12/26） | `number` / `number\|Resource` | `RefreshAttribute` | 无 | 触发阈值距离 | AC-1.3, AC-1.4 |
| `pullDownRatio(ratio)` | Public（@since 12） | `Optional<number>` | `RefreshAttribute` | 无 | 下拉阻尼比率（替代 friction） | AC-1.5 |
| `maxPullDownDistance(distance)` | Public（@since 20/26） | `Optional<number>` / `number\|Resource\|undefined` | `RefreshAttribute` | 无 | 最大下拉距离钳位 | AC-1.6, AC-1.7 |
| `pullToRefresh(value)` | Public（@since 12） | `boolean` | `RefreshAttribute` | 无 | 下拉手势触发开关 | AC-2.2 |
| `pullUpToCancelRefresh(enabled)` | Public（@since 23） | `boolean\|undefined` | `RefreshAttribute` | 无 | 上拉取消刷新开关 | AC-2.4 |
| `onOffsetChange(callback)` | Public（@since 12） | `Callback<number>` | `RefreshAttribute` | 无 | 下拉偏移实时回调 | AC-4.1 |
| C-API `NODE_REFRESH_OFFSET/PULL_DOWN_RATIO/MAX_PULL_DOWN_DISTANCE/PULL_TO_REFRESH/PULL_UP_TO_CANCEL_REFRESH/ON_OFFSET_CHANGE` | Public（推断 @since 12/20/23） | 属性/事件枚举 | — | 无 | NDK 通道 | AC-1.x~4.x |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `RefreshOptions.offset` | 废弃 since 11 | 下拉静止距离(16vp) | 迁移至 `refreshOffset`（触发阈值 64vp，语义不同需重设） | AC-1.8 |
| `RefreshOptions.friction` | 废弃 since 11 | 摩擦系数(0-100,默认 62) | 迁移至 `pullDownRatio` | AC-1.9 |

## 接口规格

### 接口定义

**refreshOffset(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefreshAttribute::refreshOffset(value: number \| Resource): RefreshAttribute` |
| 返回值 | `RefreshAttribute` |
| 开放范围 | Public（@since 12；Resource @26） |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `number` / `number\|Resource` | 是 | 64(vp) | 触发阈值；Resource 经 CreateWithResourceObjRefreshOffset |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 number | 阈值更新 | AC-1.3 |
| 2 | 设置 Resource | 资源解析更新 | AC-1.4 |
| 3 | 不设 | 默认 64vp | AC-1.2 |

### 接口定义

**onOffsetChange(callback: Callback<number>)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefreshAttribute::onOffsetChange(callback: Callback<number>): RefreshAttribute` |
| 返回值 | `RefreshAttribute` |
| 开放范围 | Public（@since 12） |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | `Callback<number>` | 是 | — | 以 scrollOffset_(px) 触发；API 版本双路径驱动 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 拖拽中 | FireOnOffsetChange | AC-4.1 |
| 2 | 步骤式 | FireOnStepOffsetChange | AC-4.2 |
| 3 | API11+ | offsetProperty_ 驱动 | AC-4.3 |
| 4 | API10- | lowVersionOffset_+SetOffset | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 是 — offset/friction 废弃 since 11，迁移至 refreshOffset/pullDownRatio；语义不同（offset 静止 vs refreshOffset 触发）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** offset/friction API 8（废弃 11）；refreshOffset/pullToRefresh/onOffsetChange/pullDownRatio @12；maxPullDownDistance @20；pullUpToCancelRefresh @23；Resource 重载 @26
- **API 版本号策略:** 各属性标注 @since；API10-/11+ 偏移属性双路径

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 阻尼公式不可变 | ratio=exp(-ratio_*gamma) | AC-1.1 |
| 弹簧参数固定 | InterpolatingSpring(velocity,1.0,228.0,30.0) | AC-1.x |
| 嵌套协调 | 子在顶部才触发；尊重 NestedScrollMode | AC-3.x |
| 版本双路径 | 11+ offsetProperty_ / 10- lowVersionOffset_ | AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 拖拽热路径保 60FPS，禁字符串操作 | 性能基准 | CLAUDE.md |
| 功耗 | FRC 场景上报优化帧率 | 代码审查 | R-16 |
| 内存 | 弹簧动画控制器复用 | 代码审查 | CLAUDE.md |
| 可测试性 | 阻尼/嵌套/偏移可单测 | 单元测试 | TASK-SKELETON-3/4 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准阻尼 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 物理参数不影响无障碍 | — |
| 大字体 | 否 | 阻尼基于 contentHeight 非字体 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | offset/friction 弃用 11；@12/20/23/26 门槛 | AC-1.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（物理/手势/偏移/嵌套；创建与状态机在 Feat-01）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RefreshPattern CalculatePullDownRatio 指数阻尼公式与 InterpolatingSpring 弹簧参数"
  - repo: "openharmony/arkui_ace_engine"
    query: "Refresh HandleScroll 嵌套滚动协调与 API10-/11+ 偏移属性双路径"
```

**关键文档:** `refresh.d.ts`、`refresh_pattern.h/.cpp`、`refresh_layout_property.h`、`CLAUDE.md`、`design.md`
