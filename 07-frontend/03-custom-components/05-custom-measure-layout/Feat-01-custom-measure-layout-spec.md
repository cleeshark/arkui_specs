# 特性规格

> Func-07-03-05-Feat-01 自定义组件测量与子项放置存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自定义组件测量与子项放置 |
| 特性编号 | Func-07-03-05-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic 新回调 API 10 起，Dynamic 当前标记 API 11；Static API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 测量回调契约 | 补录 `onMeasureSize`、`Measurable`、constraint 与 `SizeResult`。 |
| ADDED | 放置回调契约 | 补录 `onPlaceChildren`、`Layoutable` 与默认布局回退。 |
| ADDED | 范式和历史边界 | 补录 Dynamic/Static 接入、旧 API 兼容实现与相邻能力排除。 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/03-custom-components/05-custom-measure-layout/design.md` | 已核对 |
| Dynamic SDK | `interface_sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Static SDK | `interface_sdk-js/api/arkui/component/customComponent.static.d.ets` | 已核对 |
| Core | `frameworks/core/components_ng/pattern/custom/` | 已核对 |
| Dynamic bridge | `frameworks/bridge/declarative_frontend/jsview/` | 已核对 |
| Static bridge | `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/ani/native/custom/` | 已核对 |

## 用户故事

### US-1: 定义自定义测量与返回宿主尺寸

**作为** 自定义组件开发者  
**我想要** 在 `onMeasureSize` 中按约束测量子项并返回自身尺寸  
**以便** 框架使用该尺寸继续后续布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Dynamic 或 Static 组件定义 `onMeasureSize(self, children, constraint)` THEN 桥接将 self、`Measurable[]` 和 constraint 传给该回调，并消费其 `SizeResult`。 | 正常 |
| AC-1.2 | WHEN 回调对某个 `Measurable` 调用 `measure(constraint)` THEN 子项的测量结果可作为后续布局输入。 | 正常 |
| AC-1.3 | WHEN Dynamic 或 Static 测量桥接无法取得参数对象，或整体回调结果为 undefined THEN 当前实现将宿主 frame size 设为 `(-1,-1)`。 | 异常 |
| AC-1.4 | WHEN 子项提供 `uniqueId` THEN 应将其作为 since 18 的可选标识使用，不以其缺失阻断测量。 | 边界 |

### US-2: 放置已测量的子项

**作为** 自定义组件开发者  
**我想要** 在 `onPlaceChildren` 中取得可放置子项并指定位置  
**以便** 自定义组件控制子项几何位置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Dynamic 或 Static 组件定义 `onPlaceChildren(self, children, constraint)` THEN 桥接传入 `Layoutable[]` 和 placement constraint。 | 正常 |
| AC-2.2 | WHEN 回调对 `Layoutable` 调用 `layout(position)` THEN 该子项采用给定 position 进入布局放置路径。 | 正常 |
| AC-2.3 | WHEN 未定义放置回调 THEN 布局算法执行默认 self layout 并对所有子项执行 layout。 | 恢复 |

### US-3: 区分兼容路径、内部接入与相邻能力

**作为** 后续维护者  
**我想要** 识别新旧回调和前端范式的实际边界  
**以便** 不删除兼容代码，也不将不同能力混写

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 使用旧 `onMeasure/onLayout` THEN SDK 将其视为 deprecated API，但当前 JSView 兼容入口仍可执行。 | 正常 |
| AC-3.2 | WHEN 使用 Static `LayoutCallbacks` 或 `CustomLayoutRoot` modifier THEN 其走 ANI/内部 modifier 接入，不经 Dynamic JSView，且 modifier 不被当作应用侧 C API。 | 正常 |
| AC-3.3 | WHEN 排查 `DynamicLayout.CustomLayoutAlgorithm` THEN 将其按 `FrameNode` 载体的相邻能力处理，不纳入本 Feat。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | 已有实现 | Dynamic/ANI 集成回归 | `common.d.ts:35238-35271`; `customComponent.static.d.ets:453-477` |
| AC-1.2 | R-2 | 已有实现 | 参数对象 UT | `common.d.ts:34534-34599`; `custom_measure_layout_param_test_ng.cpp:563-599` |
| AC-1.3 | R-3 | 已有实现 | bridge 异常注入 | `js_view_functions.cpp:90-105`; `custom_node_module.cpp:261-295` |
| AC-1.4 | R-4 | 已有实现 | SDK 版本断言 | `common.d.ts:34447-34457,34538-34548` |
| AC-2.1 | R-5 | 已有实现 | Dynamic/ANI 集成回归 | `js_view_functions.cpp:66-77`; `custom_node_module.cpp:327-384` |
| AC-2.2 | R-6 | 已有实现 | 子项位置 UT | `common.d.ts:34457-34486` |
| AC-2.3 | R-7 | 已有实现 | Core 节点 UT | `custom_node_layout_algorithm.cpp:90-100` |
| AC-3.1 | R-8 | 已有实现 | SDK 与 JSView 回归 | `common.d.ts:34936-34961`; `js_view_functions.cpp:44-64` |
| AC-3.2 | R-9 | 已有实现 | Static modifier UT | `custom_layout_root_modifier.cpp:186-193`; `custom_layout_root_modifier_test.cpp:129-184` |
| AC-3.3 | R-10 | 已有实现 | 范围审查 | `docs/kb/components/container/dynamic_layout.md` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 定义有效 `onMeasureSize` | 桥接以 self、children、constraint 三个参数调用，并使用 `SizeResult` 更新宿主尺寸 | Dynamic 和 Static 的入口不同 | AC-1.1 |
| R-2 | 行为 | `Measurable.measure` 接收子项 constraint | 返回该子项 `MeasureResult`，供后续放置阶段读取 | 约束由当前 parent layout wrapper 创建 | AC-1.2 |
| R-3 | 异常 | 参数对象不存在或整体结果 undefined | 将宿主 frame size 设为 width=-1、height=-1 | 仅是整体空结果的已证实行为 | AC-1.3 |
| R-4 | 边界 | `uniqueId` 缺失或存在 | 缺失不阻断流程；存在时可用于识别子项 | 可选字段，since 18 | AC-1.4 |
| R-5 | 行为 | 定义有效 `onPlaceChildren` | 桥接以 self、`Layoutable[]`、placement constraint 三个参数调用 | 回调名为复数 `Children` | AC-2.1 |
| R-6 | 行为 | 回调调用 `Layoutable.layout(position)` | 当前子项按 position 进入放置路径 | position 由应用回调提供 | AC-2.2 |
| R-7 | 恢复 | `FireOnLayout` 返回 false | 算法执行默认 self layout，并 layout 全部已构建子项 | 不能把缺失回调视作静默成功 | AC-2.3 |
| R-8 | 行为 | 旧 API 被调用 | JSView 的旧参数对象与 Execute 函数继续执行兼容调用 | SDK 已 deprecated，不推荐新代码 | AC-3.1 |
| R-9 | 行为 | Static 组件订阅两个回调 | ANI 或内部 modifier 将函数连接到 `CustomMeasureLayoutNode` | modifier 不是应用 C API | AC-3.2 |
| R-10 | 边界 | 目标为 `DynamicLayout.CustomLayoutAlgorithm` | 转由 DynamicLayout 规格和 `FrameNode` API 处理 | 不复用本 Feat 的组件回调语义 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.2, AC-1.4 | SDK 对照和参数对象 UT | 三参数签名、测量结果、可选 uniqueId |
| VM-2 | AC-1.3 | Dynamic/ANI 异常回归 | 参数对象和整体 undefined 的负一尺寸降级 |
| VM-3 | AC-2.1, AC-2.2, AC-2.3 | Dynamic/ANI 与 Core UT | 回调分发、`layout(position)`、默认回退 |
| VM-4 | AC-3.1, AC-3.2, AC-3.3 | SDK、modifier UT、范围审查 | deprecated 兼容、Static 内部边界、DynamicLayout 排除 |

## API 变更分析

### 新增 API

N/A；本次仅补录已有 API。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|----------|
| `CustomComponent.onMeasure` | 废弃（since 10） | Dynamic 旧自定义测量 | 使用 `onMeasureSize(self, children, constraint): SizeResult` | AC-3.1 |
| `CustomComponent.onLayout` | 废弃（since 10） | Dynamic 旧自定义放置 | 使用 `onPlaceChildren(self, children, constraint): void` | AC-3.1 |

## 接口规格

### 接口定义

**`onMeasureSize`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onMeasureSize?(selfLayoutInfo: GeometryInfo, children: Array<Measurable>, constraint: ConstraintSizeOptions): SizeResult` |
| 返回值 | `SizeResult`，作为当前自定义组件的测量尺寸 |
| 开放范围 | Dynamic InnerApi；Static `LayoutCallbacks` |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.4 |

**`onPlaceChildren`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onPlaceChildren?(selfLayoutInfo: GeometryInfo, children: Array<Layoutable>, constraint: ConstraintSizeOptions): void` |
| 返回值 | `void` |
| 开放范围 | Dynamic InnerApi；Static `LayoutCallbacks` |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| selfLayoutInfo | GeometryInfo | 是 | N/A | 框架提供当前组件几何信息。 |
| children for measure | `Array<Measurable>` | 是 | 空数组可出现 | 仅通过 `measure(constraint)` 测量。 |
| children for place | `Array<Layoutable>` | 是 | 空数组可出现 | 通过 `layout(position)` 放置。 |
| constraint | ConstraintSizeOptions | 是 | N/A | 由当前布局上下文生成。 |
| return of measure | SizeResult | 是 | N/A | 整体 undefined 走当前负一尺寸降级。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|----------|
| 1 | 回调测量一个子项并返回尺寸 | 框架使用返回的 width/height 写宿主 frame size | AC-1.1, AC-1.2 |
| 2 | 测量回调整体返回 undefined | 宿主 frame size 为 `(-1,-1)` | AC-1.3 |
| 3 | 放置回调调用 `layout(position)` | 对应子项进入自定义位置放置 | AC-2.2 |
| 4 | 未定义放置回调 | 执行默认 self 和 child layout | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；仅补录当前实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic 新回调 API 10 起，Dynamic 当前标记 API 11；Static API 23。
- **API 版本号策略:** Dynamic 和 Static 分别以各自 SDK `@since` 为准；`uniqueId` 单独标注 since 18。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 生命周期顺序 | 测量先于放置；放置读取已测量子项信息 | AC-1.1, AC-2.1 |
| 节点统一承载 | Dynamic/Static 都由 `CustomMeasureLayoutNode` 与布局算法调度 | AC-1.1, AC-2.1 |
| 回退完整性 | 回调缺失时必须走 Core 默认 measure/layout 路径 | AC-2.3 |
| 兼容保留 | 废弃 SDK API 与现行兼容执行入口不可混同为死代码 | AC-3.1 |
| 能力边界 | `DynamicLayout` 不进入本组件回调规格 | AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 回调运行在既有布局阶段，不新增后台任务或异步队列 | Trace 和布局回归 | `custom_node_layout_algorithm.cpp:24-100` |
| 可靠性 | 整体空测量结果不保留旧尺寸，按当前路径置负一尺寸 | 异常注入 | `js_view_functions.cpp:90-105` |
| 内存 | Dynamic 参数对象复用/更新当前 wrapper；Static 使用本地 ANI scope | 压力与泄漏检查 | `js_view_measure_layout.cpp:459-471`; `custom_node_module.cpp:248-324` |
| 可测试性 | 节点、参数对象和 Static modifier 各有定向 UT | 单元测试 | `custom_measure_layout_*_test*.cpp`; `custom_layout_root_modifier_test.cpp` |
| 定界定位 | SDK、bridge、Core 和 ANI 入口均可独立定位 | 日志与源码审查 | Design 调用链 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无已证实差异 | 使用同一回调与 constraint 契约 | 布局回归 | SDK/Core |
| 平板 | 无已证实差异 | 使用同一回调与 constraint 契约 | 布局回归 | SDK/Core |
| 折叠屏 | 无已证实差异 | 屏幕形态不改变回调签名和默认回退 | 状态切换回归 | SDK/Core |

## 全局特性影响

| 特性 | 是否适用 | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不直接修改语义树或辅助功能接口。 | VM-1 |
| 大字体 | 是 | 字体导致的子项尺寸仍需经 `Measurable` 测量并放置。 | AC-1.2, AC-2.2 |
| 深色模式 | 否 | 不包含颜色或主题决策。 | VM-1 |
| 多窗口/分屏 | 是 | 每个布局上下文独立生成 constraint 和 children。 | AC-1.1, AC-2.1 |
| 多用户 | 否 | 无用户数据或持久化。 | VM-1 |
| 版本升级 | 是 | 旧 API 保持兼容，新旧回调与 Static since 分通道说明。 | AC-3.1 |
| 生态兼容 | 是 | 不将 Static 内部 modifier 误宣称为应用侧 C API。 | AC-3.2 |

## 行为场景（可选，Gherkin）

Feature: 自定义组件测量与放置
  作为 自定义组件开发者
  我想要 在布局生命周期中测量并放置子项
  以便 自定义组件获得可控的几何结果

  Scenario: 测量后放置子项
    Given 一个定义 onMeasureSize 和 onPlaceChildren 的自定义组件
    When 布局算法触发测量并取得 SizeResult
    Then 框架使用该尺寸作为宿主 frame size
    And 放置回调可以对已测量子项调用 layout

  Scenario: 测量结果缺失
    Given 一个 onMeasureSize 整体返回 undefined 的组件
    When Dynamic 或 Static bridge 消费该结果
    Then 宿主 frame size 被设为 negative one 和 negative one

  Scenario: 旧回调兼容
    Given 一个仍定义 onMeasure 和 onLayout 的 Dynamic 组件
    When 框架收集回调并进入布局
    Then 旧 JSView 兼容执行入口仍可被调用
    And 该 API 仍被标记为 deprecated

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围明确覆盖 Dynamic、Static、参数对象和历史边界
- [x] 未将已废弃兼容实现表述为废代码
- [x] 未将 `DynamicLayout.CustomLayoutAlgorithm` 混入本功能域
- [x] AC、规则和 VM 交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "CustomMeasureLayoutNode onMeasureSize onPlaceChildren Measurable Layoutable Dynamic Static ANI"
```

**关键文档：** `docs/kb/capabilities/custom-measure-layout.md`
