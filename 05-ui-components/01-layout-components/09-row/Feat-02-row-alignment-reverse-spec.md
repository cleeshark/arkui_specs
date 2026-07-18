# 特性规格

> Func-05-01-09-Feat-02 Row 对齐与反向排列：固化水平主轴空间分布、垂直交叉轴对齐、alignSelf、RTL 与 API 12 reverse 组合语义。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Row 对齐与反向排列 |
| 特性编号 | Func-05-01-09-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Row 固定水平主轴：`justifyContent` 分配水平剩余空间，`alignItems(VerticalAlign)` 决定垂直交叉轴位置，子项 alignSelf 可覆盖容器交叉轴值。API 12 `reverse` 与 RTL 共同确定水平视觉起点；算法在 Layout 阶段改变 offset，不重写 Measure 尺寸或声明子项身份。证据见 `interface/sdk-js/api/@internal/component/ets/row.d.ts:159-212` 和 `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:53-91,230-263,1567-1734`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 水平主轴分布规格 | 覆盖 Start/Center/End/SpaceBetween/SpaceAround/SpaceEvenly 与 space 组合 |
| ADDED | 垂直交叉轴对齐规格 | 覆盖 Top/Center/Bottom、子项 alignSelf、拉伸和基线内部路径 |
| ADDED | reverse/RTL/版本规格 | 覆盖 API 12、Dynamic undefined、reset、LTR/RTL 和视觉/语义顺序 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/09-row/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/row.d.ts` | 已核对 |
| Dynamic bridge | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp` | 已核对 |
| Shared layout algorithm | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 已核对 |

## 用户故事

### US-1: 分配水平主轴剩余空间

**作为** UI 布局开发者  
**我想要** 控制 Row 子项在水平方向的整体与相邻分布  
**以便** 适配不同容器宽度

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 未调用 justifyContent THEN Row 主轴默认 Start，有效子项从当前水平起点开始排列 | 边界 |
| AC-1.2 | WHEN justifyContent 为 Start/Center/End THEN 首项前空间分别为 0、水平剩余空间一半、全部剩余空间 | 正常 |
| AC-1.3 | WHEN justifyContent=SpaceBetween 且 n>1 THEN 首项前空间为 0，相邻间距为 `remain/(n-1)`；n<=1 时安全退化 | 边界 |
| AC-1.4 | WHEN justifyContent=SpaceAround 且 n>0 THEN 首项前空间为 `remain/(2n)`，相邻间距为 `remain/n` | 正常 |
| AC-1.5 | WHEN justifyContent=SpaceEvenly 且 n>0 THEN 首项前、相邻和末项后空间均以 `remain/(n+1)` 为基础 | 正常 |
| AC-1.6 | WHEN 三种 Space* 与显式 space 同时设置 THEN 固定 space 不叠加；Start/Center/End 下固定 space 保持生效 | 边界 |

### US-2: 对齐垂直交叉轴子项

**作为** UI 布局开发者  
**我想要** 控制不同高度子项在 Row 内的垂直位置  
**以便** 形成一致的水平排版

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 未调用 alignItems THEN Row 使用交叉轴 Center 默认值 | 边界 |
| AC-2.2 | WHEN alignItems 为 Top/Center/Bottom THEN 子项分别位于可用垂直交叉轴的起点、居中或末端 | 正常 |
| AC-2.3 | WHEN 子项具有有效 alignSelf THEN 该值覆盖 Row alignItems；未设置/Auto 时继承容器值 | 正常 |
| AC-2.4 | WHEN 内部交叉轴值为 Stretch 且子项未确定高度 THEN 子项按可用交叉轴约束重测；确定高度不被无条件覆盖 | 边界 |
| AC-2.5 | WHEN alignSelf/内部算法使用 Baseline 且子项提供基线 THEN 按当前基线距离对齐；无有效基线时沿既有回退路径定位 | 边界 |
| AC-2.6 | WHEN Dynamic API 10+ alignItems 原始值非法 THEN 回退到 Center 并记录错误，不抛应用异常 | 异常 |

### US-3: 组合 reverse 与 RTL

**作为** 国际化应用开发者  
**我想要** 在 LTR/RTL 中反转 Row 的视觉排列  
**以便** 支持时间线、工具栏等方向需求

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API 12+ 调用 `reverse(true)` THEN Row 水平主轴的视觉推进方向反转；`reverse(false)` 保持正常方向 | 正常 |
| AC-3.2 | WHEN Dynamic direct `reverse()` 或传入非 boolean/undefined THEN 现有入口按 true 处理；仅创建 Row 且未调用 reverse 时内部默认 false | 边界 |
| AC-3.3 | WHEN AttributeModifier/Static/Native 执行 reverse reset THEN 按对应通道恢复 false 或其实现默认，不把 Dynamic direct undefined 规则扩散到其他通道 | 边界 |
| AC-3.4 | WHEN layoutDirection=RTL THEN 水平 Start/End 发生镜像，并与 reverse 组合一次；四种 LTR/RTL×true/false 组合均不得重复/遗漏子项 | 正常 |
| AC-3.5 | WHEN reverse 状态变化 THEN 子项 frame size 与 Row Measure 尺寸不变，只重新计算视觉 offset | 正常 |
| AC-3.6 | WHEN 视觉顺序反转 THEN 声明语义树和焦点子项身份不因 Layout offset 自动重排 | 边界 |

### US-4: 处理非法主轴对齐和版本边界

**作为** 跨版本维护者  
**我想要** 对齐能力在历史 API 下保持兼容  
**以便** 避免升级产生不可解释变化

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 10+ Dynamic justifyContent 原始值非法 THEN 回退 Start 并记录错误；低目标版本保留旧路径 | 异常 |
| AC-4.2 | WHEN 目标 API 为 7 THEN alignItems 可用；WHEN 为 8+ THEN justifyContent 可用；WHEN 为 12+ THEN reverse 可用 | 边界 |
| AC-4.3 | WHEN 有效子项为 0 或 1 THEN 所有空间公式与 reverse/RTL 路径安全完成，不除零或访问不存在子项 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.6 | R-1~R-5 | 已有实现 | justify/space Layout 矩阵 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` |
| AC-2.1~AC-2.6 | R-6~R-10 | 已有实现 | cross align/alignSelf/baseline UT | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1660-1734`; `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:78-145` |
| AC-3.1~AC-3.6 | R-11~R-15 | 已有实现 | LTR/RTL×reverse 参数矩阵 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:53-91,230-263,1567-1625` |
| AC-4.1~AC-4.3 | R-16~R-18 | 已有实现 | Dynamic/API level/空集合测试 | `interface/sdk-js/api/@internal/component/ets/row.d.ts:159-212`; `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:100-128`; `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Start/Center/End | frontSpace 为 0/remain÷2/remain | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` | AC-1.1, AC-1.2 |
| R-2 | 边界 | SpaceBetween | n>1 时 between=remain÷(n-1)，否则 0 | 同上 | AC-1.3 |
| R-3 | 行为 | SpaceAround | front=remain÷(2n)，between=remain÷n | 同上 | AC-1.4 |
| R-4 | 行为 | SpaceEvenly | front=between=remain÷(n+1) | 同上 | AC-1.5 |
| R-5 | 边界 | Space* 与固定 space | Space* 忽略固定 space，其他模式保留 | 同上 | AC-1.6 |
| R-6 | 行为 | 未设置/Top/Center/Bottom | 默认 Center，并按容器/子项交叉轴差计算 offset | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1660-1734` | AC-2.1, AC-2.2 |
| R-7 | 行为 | 子项 alignSelf | 有效值覆盖容器交叉轴对齐 | 同上 | AC-2.3 |
| R-8 | 边界 | Stretch 且子项交叉轴未确定 | 使用可用交叉约束重测 | 同上 | AC-2.4 |
| R-9 | 边界 | Baseline | 使用子项基线距离；缺失时走回退 | 同上 | AC-2.5 |
| R-10 | 异常 | API 10+ Dynamic alignItems 非法 | 写 Center 并记录错误 | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:78-98` | AC-2.6 |
| R-11 | 行为 | reverse true/false | Layout 分别反向/正常推进水平主轴 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:53-91,1567-1625` | AC-3.1 |
| R-12 | 边界 | Dynamic direct 非 bool/undefined | `SetReverse` 写 true；未调用时默认 false | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:119-128` | AC-3.2 |
| R-13 | 恢复 | modifier/static/native reset | 按通道 reset 到 false/当前默认 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_row_bridge.cpp:119-143`; `frameworks/core/components_ng/pattern/linear_layout/row_model_ng_static.cpp:23-51` | AC-3.3 |
| R-14 | 行为 | RTL×reverse | 解析水平起点并组合一次视觉反向 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:53-91,230-263` | AC-3.4 |
| R-15 | 行为 | reverse 更新 | Measure 尺寸不变，Layout 重算 offset；声明身份不重排 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1567-1625` | AC-3.5, AC-3.6 |
| R-16 | 异常 | API 10+ justifyContent 非法 | 回退 Start 并记录错误 | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:100-117` | AC-4.1 |
| R-17 | 边界 | API 7/8/12 | 分别开放 alignItems/justifyContent/reverse | `interface/sdk-js/api/@internal/component/ets/row.d.ts:159-212` | AC-4.2 |
| R-18 | 边界 | 有效子项 n<=1 | 使用安全公式并完成 reverse/RTL 布局 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.6 | Layout 参数矩阵 | 六种 justify、n=0/1/多子项、固定 space |
| VM-2 | R-6~R-10, AC-2.1~AC-2.6 | Cross align UT | Top/Center/Bottom、alignSelf、Stretch、Baseline、非法值 |
| VM-3 | R-11~R-15, AC-3.1~AC-3.6 | LTR/RTL×reverse×通道测试 | direct undefined、reset、尺寸和声明身份 |
| VM-4 | R-16~R-18, AC-4.1~AC-4.3 | Dynamic/API 编译/边界 UT | Start 回退、7/8/12 可见性、空/单子项 |

## API 变更分析

> 本文补录已有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `alignItems(value: VerticalAlign)` | Public | Top/Center/Bottom | RowAttribute | N/A | API 7 设置垂直交叉轴对齐 | AC-2.1~AC-2.6 |
| `justifyContent(value: FlexAlign)` | Public | 六种公开主轴对齐值 | RowAttribute | N/A | API 8 设置水平主轴分布 | AC-1.1~AC-1.6, AC-4.1 |
| `reverse(isReversed: Optional<boolean>)` | Public | true/false/undefined | RowAttribute | N/A | API 12 设置水平反向排列 | AC-3.1~AC-3.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次无接口变更 | 跨通道迁移显式传 reverse boolean | AC-3.2~AC-3.3 |

## 接口规格

### 接口定义

| 接口 | 签名 | 默认/未调用 | 开放范围 | 关联 AC |
|------|------|-------------|----------|---------|
| alignItems | `(value: VerticalAlign): RowAttribute` | Center | Public API 7+ | AC-2.1~AC-2.6 |
| justifyContent | `(value: FlexAlign): RowAttribute` | Start | Public API 8+ | AC-1.1~AC-1.6 |
| reverse | `(isReversed: Optional<boolean>): RowAttribute` | 未调用时 false；Dynamic 调用未传值时 true | Public API 12+ | AC-3.1~AC-3.6 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 六种 justify + 固定 space | 按主轴公式定位 | AC-1.1~AC-1.6 |
| 2 | VerticalAlign + alignSelf | 按交叉轴策略定位/重测 | AC-2.1~AC-2.5 |
| 3 | LTR/RTL×reverse | 组合一次水平起点与推进方向 | AC-3.1~AC-3.6 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** alignItems API 7；justifyContent API 8；reverse API 12。
- **API 版本号策略:** canonical SDK `@since` 为权威；Dynamic API 10 非法值回退作为运行边界。

| 风险 | 当前证据 | 兼容处理 |
|------|----------|----------|
| Dynamic direct `reverse(undefined/non-bool)` 为 true，而 modifier/native reset 为 false | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:119-128`; `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_row_bridge.cpp:119-143` | 按通道分别验收；跨范式迁移显式传 boolean |
| Native 连续枚举范围可能包含 SDK 未公开空洞 | `interfaces/native/node/style_modifier.cpp:20466-20540,23049-23077` | 正常契约只覆盖 SDK 公开枚举，raw 空洞作为风险/fuzz 输入 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 水平主轴固定 | Row direction 固定为 ROW，justify/reverse/RTL 均作用于水平轴 | AC-1.1~AC-1.6, AC-3.1~AC-3.5 |
| Measure/Layout 分离 | reverse 不重算尺寸，只改变视觉定位 | AC-3.5~AC-3.6 |
| 子项覆盖 | alignSelf 优先于 alignItems | AC-2.3~AC-2.5 |
| 通道隔离 | Dynamic undefined 与 reset 语义不得互相推断 | AC-3.2~AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增复杂度；空间与交叉轴定位按子项线性执行 | Trace | FlexLayoutAlgorithm |
| 功耗 | 属性变化只触发既有布局帧 | 代码审查 | VM-1~VM-4 |
| 内存 | 不复制持久子项顺序，reverse 仅使用算法状态 | 内存审查 | AC-3.5~AC-3.6 |
| 安全 | 不涉及权限/敏感数据；非法枚举有回退/校验 | fuzz | AC-2.6, AC-4.1 |
| 可靠性 | n=0/1、非法值、RTL/reverse 组合不得崩溃 | 边界 UT | AC-3.4, AC-4.3 |
| 可测试性 | frame offset、属性和声明 identity 可断言 | 追溯审查 | VM-1~VM-4 |
| 自动化维测 | 沿用 LinearLayoutProperty/Pattern dump | Inspector/Dump | LinearLayoutPattern |
| 定界定位 | 可区分 parser、Property、Measure、Layout 和文本方向 | 源码定位 | `05-ui-components/01-layout-components/09-row/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无专有差异 | 窄宽度改变 remain，不改变公式 | 多宽度测试 | AC-1.2~AC-1.5 |
| 平板 | 无专有差异 | 大窗口增加水平剩余空间 | 可变窗口测试 | AC-1.2~AC-1.5 |
| 折叠屏 | 约束/文本方向可触发重新布局 | 重算 offset，不改变属性契约 | 折叠态测试 | AC-3.4~AC-3.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 视觉 reverse/RTL 不自动重排声明语义与焦点身份 | AC-3.6 |
| 大字体 | 是 | 子项高度/宽度改变 remain 与交叉轴位置 | AC-1.2, AC-2.2 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | 可用宽度变化重新分配水平余量 | AC-1.2~AC-1.5 |
| 多用户 | 否 | 无持久用户状态 | N/A |
| 版本升级 | 是 | API 7/8/10/12 边界需回归 | AC-2.6, AC-4.1~AC-4.2 |
| 生态兼容 | 是 | reverse undefined/reset 与 Native raw 值需定界 | AC-3.2~AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Row 对齐与反向排列
  Scenario: SpaceAround 分布三个子项
    Given Row 水平剩余空间为 120vp
    And 有三个有效子项
    When justifyContent 为 SpaceAround
    Then 首项前空间为 20vp
    And 相邻间距为 40vp

  Scenario: LTR 与 RTL 中切换 reverse
    Given 一个含三个子项的 Row
    When 依次验证 LTR/RTL 与 reverse false/true
    Then 每种组合中三个子项各出现一次
    And reverse 只改变视觉 offset

  Scenario: alignSelf 覆盖容器
    Given Row alignItems 为 Top
    And 第二个子项 alignSelf 为 End
    When Layout 完成
    Then 第二个子项位于交叉轴末端
    And 其他子项位于交叉轴起点
```

## Spec 自审清单

- [x] 无占位文本
- [x] 六种主轴分布、VerticalAlign、alignSelf、reverse、RTL 和版本均有 AC
- [x] Dynamic undefined 与其他通道 reset 差异未被错误归一
- [x] 每个 AC 映射规则和 VM
- [x] 视觉顺序与声明语义身份边界明确

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Row justifyContent alignItems VerticalAlign reverse RTL FlexLayoutAlgorithm"
  - repo: "openharmony/interface_sdk-js"
    query: "RowAttribute alignItems justifyContent reverse API 7 8 12"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/row.d.ts`
- 架构设计：`05-ui-components/01-layout-components/09-row/design.md`
