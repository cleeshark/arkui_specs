# 特性规格

> Func-05-01-13-Feat-02 DynamicLayout 行列线性布局算法：补录 RowLayoutAlgorithm 与 ColumnLayoutAlgorithm 的 space、交叉/主轴对齐、reverse、RTL、子项 Flex 属性和运行时 `@Trace` 更新。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DynamicLayout 行列线性布局算法 |
| 特性编号 | Func-05-01-13-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

`RowLayoutAlgorithm` 与 `ColumnLayoutAlgorithm` 在 API 24 提供可观察布局参数。Model 将二者映射为横向/纵向 `LinearLayoutProperty` 并复用 FlexLayoutAlgorithm；因此固定间距、主/交叉轴对齐、reverse、RTL 以及子项 Flex 布局属性沿用线性容器生产语义。Dynamic/Static bridge 分别负责枚举、LengthMetrics 与 Resource 转换。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Row/Column 算法创建与默认值规格 | 覆盖 API 24 options、方向和 Linear Pattern 映射 |
| ADDED | space、alignItems、justifyContent、reverse 规格 | 覆盖参数生效、非法值、有效子项、RTL 和边界 |
| ADDED | `@Trace` 更新与子项 Flex 属性规格 | 覆盖同类型参数刷新、状态保持和子项属性参与 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/13-dynamic-layout/design.md` | 已补录 |
| LayoutAlgorithm SDK | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/LayoutAlgorithm.static.d.ets` | 已核对 |
| Model | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp` | 已核对 |
| Bridges | `frameworks/core/components_ng/pattern/dynamiclayout/bridge/arkts_native_dynamic_layout_bridge.cpp`、`frameworks/core/components_ng/pattern/dynamiclayout/bridge/dynamic_layout_static_ani_modifier.cpp` | 已核对 |

> 本文档只覆盖 DynamicLayout 使用的 Row/Column preset，不替代 Row/Column 组件各自完整功能域规格。

## 用户故事

### US-1: 使用横向或纵向线性算法

**作为** 响应式界面开发者  
**我想要** 在同一 DynamicLayout 中选择 Row 或 Column  
**以便** 随窗口形态改变主轴方向而保持子组件状态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN algorithm 为 `RowLayoutAlgorithm` THEN DynamicLayout 使用横向 LinearLayout Pattern/Property，子项按主轴横向排列 | 正常 |
| AC-1.2 | WHEN algorithm 为 `ColumnLayoutAlgorithm` THEN DynamicLayout 使用纵向 LinearLayout Pattern/Property，子项按主轴纵向排列 | 正常 |
| AC-1.3 | WHEN Row/Column options 缺省 THEN space 为 0vp、justifyContent 为 FlexAlign.Start、isReverse 为 false；Row alignItems 为 VerticalAlign.Center，Column 为 HorizontalAlign.Center | 边界 |
| AC-1.4 | WHEN Row 与 Column 互相切换 THEN 外层节点和子组件身份保持，Pattern 方向替换并在下一次布局应用相应轴语义 | 正常 |

### US-2: 配置间距和轴向对齐

**作为** ArkUI 布局开发者  
**我想要** 配置相邻子项间距及主/交叉轴对齐  
**以便** 在两种方向下获得可预测的线性排列

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN space 为非负有效 LengthMetrics THEN 只在相邻有效、非 GONE、非离流子项之间加入固定主轴间距 | 正常 |
| AC-2.2 | WHEN space 为负值或无法解析 THEN Dynamic/Static 按入口既有默认/钳制语义使用 0，不形成负间距 | 异常 |
| AC-2.3 | WHEN justifyContent 为 Start/Center/End/SpaceBetween/SpaceAround/SpaceEvenly THEN 按剩余主轴空间计算前置与子项间分布；Space* 模式不重复叠加固定 space | 正常 |
| AC-2.4 | WHEN alignItems 设置有效值 THEN Row 在垂直交叉轴、Column 在水平交叉轴对齐所有未单独覆盖的子项 | 正常 |
| AC-2.5 | WHEN 子项具有对应 Flex 布局属性（如 layoutWeight、alignSelf 等） THEN 在 Row/Column 算法下生效；单个 alignSelf 覆盖容器 alignItems | 边界 |
| AC-2.6 | WHEN options 枚举非法 THEN 各字段独立回退 SDK 默认，不使整个 algorithm 对象失效 | 异常 |

### US-3: 反向排列并响应运行时参数变化

**作为** 动态状态驱动界面开发者  
**我想要** 切换 reverse、对齐和间距而不重建子树  
**以便** 动画或模式变化能够保持组件状态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN isReverse=true THEN 线性算法在 Layout 阶段反转主轴视觉排列，子组件声明身份不重排 | 正常 |
| AC-3.2 | WHEN Row 同时受 RTL/common direction 影响 THEN 水平主轴方向按 SDK 说明再次反转组合；Column 的纵向 reverse 不因 RTL 反转主轴 | 边界 |
| AC-3.3 | WHEN `@Trace` space/alignItems/justifyContent/isReverse 任一字段变化 THEN 同类型 Pattern/Property 更新并标记 Measure，下一布局帧使用新值 | 正常 |
| AC-3.4 | WHEN 多个字段同一状态更新周期变化 THEN 最终布局使用同一最新快照，不混用旧 space 与新 alignment | 边界 |
| AC-3.5 | WHEN 算法对象或节点在更新前失效 THEN bridge/model 安全退出，不访问已销毁 FrameNode | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Model/Pattern 类型 UT | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp:28-37,116-199`; `test/unittest/core/pattern/dynamiclayout/dynamic_layout_model_test_ng.cpp:69-220` |
| AC-2.1~AC-2.6 | R-5~R-10 | 已有实现 | Linear/Flex 参数化 Layout UT | `frameworks/core/components_ng/pattern/dynamiclayout/bridge/arkts_native_dynamic_layout_bridge.cpp:30-183`; `frameworks/core/components_ng/pattern/dynamiclayout/bridge/dynamic_layout_static_ani_modifier.cpp:46-107`; `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:115-474` |
| AC-3.1~AC-3.5 | R-11~R-15 | 已有实现 | reverse/RTL/Trace/lifecycle UT | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp:116-199`; Row SDK `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:354-373,455-473` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Row algorithm | 创建横向 LinearLayout 状态 | 主轴水平 | AC-1.1 |
| R-2 | 行为 | Column algorithm | 创建纵向 LinearLayout 状态 | 主轴垂直 | AC-1.2 |
| R-3 | 边界 | options 缺省 | 应用各算法 SDK 默认 | space 0、main Start、reverse false、cross Center | AC-1.3 |
| R-4 | 行为 | Row/Column 互切 | ReplacePattern 但保持 DynamicLayoutNode/children | 下一帧重新 Measure | AC-1.4 |
| R-5 | 行为 | 合法 space | 在相邻有效子项之间加入固定间距 | n<=1 无可见 gap | AC-2.1 |
| R-6 | 异常 | space 负值/解析失败 | 使用 0/default | Static negative 转 0 | AC-2.2 |
| R-7 | 行为 | 有效 justifyContent | 按 Flex 主轴分布计算 | Space* 不重复加固定 space | AC-2.3 |
| R-8 | 行为 | 有效 alignItems | Row 作用垂直轴，Column 作用水平轴 | alignSelf 可覆盖 | AC-2.4 |
| R-9 | 边界 | 子项 Flex 属性存在 | 由共享 Flex 算法消费 | 仅在线性 preset 生效 | AC-2.5 |
| R-10 | 异常 | 某枚举字段非法 | 该字段回退默认，其他字段保留 | 不使整个 algorithm 失效 | AC-2.6 |
| R-11 | 行为 | isReverse=true | 反转视觉主轴位置 | 不重排声明节点 | AC-3.1 |
| R-12 | 边界 | Row + RTL/direction | 按 SDK 组合反转；Column 主轴不受 RTL | 交叉轴仍可镜像 | AC-3.2 |
| R-13 | 行为 | `@Trace` 字段变化 | 更新现有状态并标记 Measure | 同 type 不 ReplacePattern | AC-3.3 |
| R-14 | 边界 | 多字段同周期变化 | 使用最新一致快照 | 不跨帧混合字段 | AC-3.4 |
| R-15 | 异常 | node/algorithm 上下文失效 | 安全退出 | 不持有悬空节点 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | Model/Pattern UT | 横纵方向、默认值、互切和子状态 |
| VM-2 | R-5~R-10, AC-2.1~AC-2.6 | Flex Layout 参数矩阵 | space、GONE、主/交叉轴对齐、Space*、非法值 |
| VM-3 | R-11~R-12, AC-3.1~AC-3.2 | reverse × RTL 参数化 UT | 视觉顺序与声明身份 |
| VM-4 | R-13~R-15, AC-3.3~AC-3.5 | Trace/批量更新/销毁 UT | 同 Pattern 更新、一致快照和生命周期 |

## API 变更分析

> 本文档补录 API 24 既有算法类。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `new RowLayoutAlgorithm(options?)` | Public | space、alignItems、justifyContent、isReverse | RowLayoutAlgorithm | N/A | 创建横向线性算法 | AC-1.1~AC-3.5 |
| `new ColumnLayoutAlgorithm(options?)` | Public | space、alignItems、justifyContent、isReverse | ColumnLayoutAlgorithm | N/A | 创建纵向线性算法 | AC-1.2~AC-3.5 |
| 四个 `@Trace` 字段 | Public property | LengthMetrics/enums/boolean | void/update | N/A | 运行时更新同类型算法参数 | AC-3.3~AC-3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | API 24 首次提供 | 无需迁移 | AC-1.1~AC-3.5 |

## 接口规格

### 接口定义

**RowLayoutAlgorithm(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `new RowLayoutAlgorithm(option?: RowLayoutAlgorithmOptions)` |
| 返回值 | 实现 LayoutAlgorithm 的 RowLayoutAlgorithm |
| 开放范围 | Public、API 24 |
| 错误码 | N/A；字段非法按默认值 |
| 关联 AC | AC-1.1~AC-3.5 |

**ColumnLayoutAlgorithm(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `new ColumnLayoutAlgorithm(option?: ColumnLayoutAlgorithmOptions)` |
| 返回值 | 实现 LayoutAlgorithm 的 ColumnLayoutAlgorithm |
| 开放范围 | Public、API 24 |
| 错误码 | N/A；字段非法按默认值 |
| 关联 AC | AC-1.2~AC-3.5 |

**参数约束**

| 参数 | Row | Column | 默认值 | 非法处理 |
|------|-----|--------|--------|----------|
| space | LengthMetrics，横向 gap | LengthMetrics，纵向 gap | `LengthMetrics.vp(0)` | 默认/钳制 0 |
| alignItems | VerticalAlign | HorizontalAlign | Center | 字段回退 Center |
| justifyContent | FlexAlign | FlexAlign | Start | 字段回退 Start |
| isReverse | boolean | boolean | false | 字段回退 false |

## 兼容性声明

- **已有 API 行为变更:** 否；两类算法及字段均为 API 24。
- **配置文件格式变更:** 否；Resource/LengthMetrics 通过既有转换。
- **数据存储格式变更:** 否；参数随算法对象/Property。
- **最低支持版本:** API 24。
- **API 版本号策略:** 不向 API 23 及以下暴露；Dynamic/Static 以同一 API 24 SDK 类型为准。

| 算法 | SDK 位置 |
|------|----------|
| Column options/class | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:115-290` |
| Row options/class | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:292-474` |
| Static 映射 | `interface/sdk-js/api/arkui/LayoutAlgorithm.static.d.ets:28-250` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 共享 Flex 生产链 | DynamicLayout 不复制线性算法 | AC-1.1~AC-2.6 |
| 轴语义明确 | Row 水平/垂直，Column 垂直/水平 | AC-2.3, AC-2.4 |
| 同类型增量更新 | `@Trace` 不应触发 Pattern 替换 | AC-3.3, AC-3.4 |
| 状态身份分离 | reverse 改变几何不改变子节点声明身份 | AC-3.1, AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 线性 Measure/Layout 保持 O(n)，同类型更新不重建 Pattern | benchmark/trace | Model/Flex |
| 功耗 | 仅参数变化触发布局，无后台任务 | 帧计数 | VM-4 |
| 内存 | 复用已有 Linear Pattern/Property，不复制子树 | 内存 UT | AC-1.4, AC-3.3 |
| 安全 | 无权限/敏感数据；非法值字段级回退 | fuzz | AC-2.2, AC-2.6 |
| 可靠性 | 空/GONE、负值、RTL/reverse 与销毁不得崩溃 | 参数化压力 UT | VM-2~VM-4 |
| 可测试性 | 固定子项尺寸可精确断言每个 offset | Layout UT | VM-1~VM-3 |
| 自动化维测 | 可 dump 当前 direction、space、align、reverse | Inspector/trace | LayoutProperty |
| 定界定位 | 区分 SDK object、Bridge parsing、Model mapping、Flex calculation | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无专有差异 | 窗口宽度可驱动 Row/Column 切换 | 响应式测试 | AC-1.4 |
| 平板 | 无专有差异 | 大窗口只改变约束/剩余空间 | 多尺寸测试 | AC-2.3 |
| 折叠屏 | RTL/窗口变化组合 | 最新 algorithm/params 生效且状态保持 | 姿态/RTL 测试 | AC-3.2~AC-3.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | reverse 不重排语义声明顺序；应用需关注视觉/焦点差异 | AC-3.1 |
| 大字体 | 是 | 子项尺寸和剩余空间变化后重新布局 | AC-2.1~AC-2.5 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | 适合 Row/Column 运行时切换且保留状态 | AC-1.4 |
| 多用户 | 否 | 无持久状态 | N/A |
| 版本升级 | 是 | API 24 前不可见 | AC-1.1 |
| 生态兼容 | 是 | 默认值、Space*、RTL/reverse 和子项 Flex 语义需稳定 | AC-1.3~AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DynamicLayout 行列线性算法
  Scenario: Row 默认布局
    Given DynamicLayout 使用无 options 的 RowLayoutAlgorithm
    When 布局三个有效子项
    Then space 为 0
    And 主轴从 Start 排列
    And 子项在垂直交叉轴 Center

  Scenario: Column 参数运行时更新
    Given 当前使用 ColumnLayoutAlgorithm 且 space 为 8vp
    When space 更新为 16vp且 isReverse 更新为 true
    Then Pattern 身份保持
    And 下一帧以 16vp 反向排列

  Scenario: Row RTL 与 reverse 组合
    Given Row isReverse 为 true且 common direction 为 RTL
    When Layout
    Then 按 SDK 的再次反转组合计算视觉主轴
    And 子节点声明身份不变
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖 DynamicLayout 的 Row/Column preset
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] Stack/Grid/Custom 已路由至 Feat-03/04

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DynamicLayout Row Column LinearLayoutProperty space alignItems justifyContent reverse"
  - repo: "openharmony/interface_sdk-js"
    query: "RowLayoutAlgorithm ColumnLayoutAlgorithm LengthMetrics Trace API 24"
```

**关键文档：**

- LayoutAlgorithm SDK：`interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/LayoutAlgorithm.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/13-dynamic-layout/design.md`
