# 特性规格

> Func-05-01-13-Feat-03 DynamicLayout 堆叠与网格布局算法：补录 StackLayoutAlgorithm 的本地化九宫格对齐、GridLayoutAlgorithm 的列模板/填充策略、行列间距、参数互斥、运行时更新和默认回退。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DynamicLayout 堆叠与网格布局算法 |
| 特性编号 | Func-05-01-13-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

`StackLayoutAlgorithm` 将 DynamicLayout 切换为 Stack Pattern，并以 `LocalizedAlignment.CENTER` 为默认对齐；子项 `layoutGravity` 可生效。`GridLayoutAlgorithm` 将列定义解析为 `columnsTemplate` 或 `ItemFillPolicy`，并配置 columnsGap/rowsGap，最终复用 LazyGrid Pattern 执行网格测量。该内部复用不意味着本轮补录 LazyDynamicLayout。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Stack preset 规格 | 覆盖 Center 默认、本地化 Alignment、layoutGravity 与 RTL |
| ADDED | Grid preset 规格 | 覆盖列模板/ItemFillPolicy、行列间距、子项顺序和约束 |
| ADDED | 参数互斥、非法回退与运行时更新 | 覆盖 union 切换、默认 `'1fr'`、0 gap、Dynamic/Static 解析 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/13-dynamic-layout/design.md` | 已补录 |
| LayoutAlgorithm SDK | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/LayoutAlgorithm.static.d.ets` | 已核对 |
| Model | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp` | 已核对 |
| Bridges | `frameworks/core/components_ng/pattern/dynamiclayout/bridge/arkts_native_dynamic_layout_bridge.cpp`、`frameworks/core/components_ng/pattern/dynamiclayout/bridge/dynamic_layout_static_ani_modifier.cpp` | 已核对 |

> Grid 的生产实现可复用 LazyGrid Pattern；本 Feat 只规格化 `GridLayoutAlgorithm` 的公开输入和可观察布局。

## 用户故事

### US-1: 使用 Stack 算法叠放并对齐子项

**作为** 动态界面开发者  
**我想要** 在 DynamicLayout 中切换为叠放布局  
**以便** 在不重建子树的情况下展示覆盖层

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN algorithm 为 `StackLayoutAlgorithm` THEN DynamicLayout 使用 Stack Pattern/Property，多个子项共享内容框并保持后声明覆盖先声明 | 正常 |
| AC-1.2 | WHEN options 缺省或 alignContent 非法 THEN 使用 `LocalizedAlignment.CENTER` | 边界 |
| AC-1.3 | WHEN 设置有效 LocalizedAlignment THEN 子项按内容框和自身尺寸计算九宫格偏移，本地化 Start/End 随布局方向镜像 | 正常 |
| AC-1.4 | WHEN 子项设置 `layoutGravity` THEN 该子项对齐覆盖容器 alignContent；未设置的兄弟继续使用容器值 | 边界 |
| AC-1.5 | WHEN `@Trace alignContent` 运行时变化 THEN 同 Stack Pattern 更新 Alignment 并在下一布局帧重定位，不重建子组件 | 正常 |

### US-2: 使用 Grid 算法按列排列子项

**作为** 响应式网格界面开发者  
**我想要** 使用模板或填充策略定义网格列  
**以便** 根据容器宽度组织多个子组件

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN algorithm 为 `GridLayoutAlgorithm` THEN DynamicLayout 使用 Grid/LazyGrid 对应 Pattern，按子项声明顺序依次填入网格 | 正常 |
| AC-2.2 | WHEN columnsTemplate 是合法模板字符串 THEN 按模板解析列轨道；缺省或非法模板使用默认 `'1fr'`，形成至少一个可用列 | 正常 |
| AC-2.3 | WHEN columnsTemplate 输入为有效 `ItemFillPolicy` THEN 按该 policy 计算列填充并设置对应 LazyGrid 策略，不同时使用旧模板定义 | 正常 |
| AC-2.4 | WHEN 模板字符串与 ItemFillPolicy 之间运行时切换 THEN 二者互斥，最新 union 分支覆盖/清理另一分支的有效影响 | 边界 |
| AC-2.5 | WHEN 列策略在当前约束下无法形成合法列宽 THEN 不产生负列宽或崩溃，按默认/底层安全约束得到可布局网格 | 异常 |

### US-3: 配置网格间距并响应参数变化

**作为** 网格样式开发者  
**我想要** 独立设置行列间距  
**以便** 在不同窗口形态保持一致留白

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN columnsGap/rowsGap 缺省 THEN 有效值分别为 `LengthMetrics.vp(0)` | 边界 |
| AC-3.2 | WHEN columnsGap/rowsGap 为非负有效 LengthMetrics THEN 分别应用在相邻列/行之间，不额外加在网格外边缘 | 正常 |
| AC-3.3 | WHEN gap 为负值或无法解析 THEN 按公开 API 契约将其视为默认值 0，不形成负间距 | 异常 |
| AC-3.4 | WHEN `@Trace columnsTemplate/columnsGap/rowsGap` 任一变化 THEN 同 Grid Pattern 更新参数并标记 Measure，子组件状态保持 | 正常 |
| AC-3.5 | WHEN 多个字段同周期变化 THEN 下一布局使用最新一致参数快照，不把旧列数与新 gap 混用 | 边界 |
| AC-3.6 | WHEN DynamicLayout 从 Grid 切换 Stack 或反向切换 THEN 外层节点与子项身份保持，旧 Grid/Stack 私有属性不污染新 Pattern | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | Stack alignment/layoutGravity/Trace UT | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp:39-56,92-153`; `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:476-553` |
| AC-2.1~AC-2.5 | R-6~R-10 | 已有实现 | Grid template/policy/约束 UT | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp:58-90`; `frameworks/core/components_ng/pattern/dynamiclayout/bridge/arkts_native_dynamic_layout_bridge.cpp:30-183`; `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:555-657` |
| AC-3.1~AC-3.6 | R-11~R-16 | 已有实现 | Gap/Trace/Pattern 切换 UT | `frameworks/core/components_ng/pattern/dynamiclayout/bridge/dynamic_layout_static_ani_modifier.cpp:46-107,176-223`; `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:658-688`; `test/unittest/core/pattern/dynamiclayout/frame_node_test_dynamic_layout.cpp:61-162` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Stack algorithm | 安装 Stack Pattern 并叠放子项 | 后声明保持覆盖 | AC-1.1 |
| R-2 | 边界 | Stack align 缺省/非法 | 使用 LocalizedAlignment.CENTER | SDK 默认 | AC-1.2 |
| R-3 | 行为 | 有效 LocalizedAlignment | 九宫格定位并镜像本地化水平语义 | 不改变子项顺序 | AC-1.3 |
| R-4 | 边界 | child layoutGravity 存在 | 覆盖该 child 的容器对齐 | 只影响当前 child | AC-1.4 |
| R-5 | 行为 | Stack `@Trace` 更新 | 同 Pattern 更新并标记 Measure | 子状态保持 | AC-1.5 |
| R-6 | 行为 | Grid algorithm | 安装 Grid/LazyGrid Pattern 并按声明顺序填充 | 不纳入 LazyDynamicLayout API | AC-2.1 |
| R-7 | 行为 | 合法 template 字符串 | 解析轨道；缺省/非法回退 `'1fr'` | 至少一个可用列 | AC-2.2 |
| R-8 | 行为 | 有效 ItemFillPolicy | 设置 policy 并停止使用模板分支 | union 互斥 | AC-2.3 |
| R-9 | 边界 | template/policy 互切 | 最新分支覆盖另一分支影响 | 不同时生效 | AC-2.4 |
| R-10 | 异常 | 列策略与约束不合法 | 默认/安全约束，不产生负几何 | 不崩溃 | AC-2.5 |
| R-11 | 边界 | gaps 缺省 | columnsGap=rowsGap=0vp | SDK 默认 | AC-3.1 |
| R-12 | 行为 | 合法 gaps | 只添加相邻轨道间距 | 无外边缘额外 gap | AC-3.2 |
| R-13 | 异常 | gap 负值/解析失败 | 按公开 API 契约使用默认值 0 | 默认值为 `LengthMetrics.vp(0)` | AC-3.3 |
| R-14 | 行为 | Grid `@Trace` 字段变化 | 同 Pattern 更新并 Measure dirty | 子状态保持 | AC-3.4 |
| R-15 | 边界 | 多字段同周期变化 | 使用最新一致快照 | 不混合代际 | AC-3.5 |
| R-16 | 恢复 | Grid/Stack 互切 | ReplacePattern 并释放旧私有状态 | 外层 node/children 不变 | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | Stack 参数化 Layout UT | 默认/九宫格/RTL/layoutGravity/Trace |
| VM-2 | R-6~R-10, AC-2.1~AC-2.5 | Grid template × policy × constraint UT | 填充顺序、互斥、默认和负几何保护 |
| VM-3 | R-11~R-15, AC-3.1~AC-3.5 | Gap/Resource/Trace 契约测试 | 0、合法、负值、解析失败和批量更新 |
| VM-4 | R-16, AC-3.6 | Pattern 切换/状态保持 UT | node/child identity 和私有属性隔离 |

## API 变更分析

> 本文档补录 API 24 已有算法类。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `new StackLayoutAlgorithm(options?)` | Public | `alignContent?: LocalizedAlignment` | StackLayoutAlgorithm | N/A | DynamicLayout 叠放算法 | AC-1.1~AC-1.5 |
| `new GridLayoutAlgorithm(options?)` | Public | columnsTemplate/policy、columnsGap、rowsGap | GridLayoutAlgorithm | N/A | DynamicLayout 网格算法 | AC-2.1~AC-3.6 |
| Stack/Grid `@Trace` fields | Public property | Alignment/union/LengthMetrics | void/update | N/A | 运行时更新参数 | AC-1.5, AC-3.4, AC-3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | API 24 首次提供 | 无需迁移 | AC-1.1~AC-3.6 |

## 接口规格

### 接口定义

**StackLayoutAlgorithm(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `new StackLayoutAlgorithm(option?: StackLayoutAlgorithmOptions)` |
| 返回值 | 实现 LayoutAlgorithm 的 StackLayoutAlgorithm |
| 开放范围 | Public、API 24 |
| 错误码 | N/A；非法 align 回退 Center |
| 关联 AC | AC-1.1~AC-1.5 |

**GridLayoutAlgorithm(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `new GridLayoutAlgorithm(option?: GridLayoutAlgorithmOptions)` |
| 返回值 | 实现 LayoutAlgorithm 的 GridLayoutAlgorithm |
| 开放范围 | Public、API 24 |
| 错误码 | N/A；非法字段独立回退 |
| 关联 AC | AC-2.1~AC-3.6 |

**参数约束**

| 参数 | 类型 | 默认值 | 约束/非法处理 |
|------|------|--------|---------------|
| alignContent | LocalizedAlignment | CENTER | 非法回退 Center |
| columnsTemplate | string / ItemFillPolicy | `'1fr'` | union 分支互斥；非法回退默认 |
| columnsGap | LengthMetrics | 0vp | 非负；非法值按公开 API 契约使用默认值 0 |
| rowsGap | LengthMetrics | 0vp | 非负；非法值按公开 API 契约使用默认值 0 |

## 兼容性声明

- **已有 API 行为变更:** 否；Stack/Grid 算法均为 API 24。
- **配置文件格式变更:** 否；LengthMetrics/Resource 沿用既有解析。
- **数据存储格式变更:** 否；参数随算法对象和 Pattern。
- **最低支持版本:** API 24。
- **API 版本号策略:** 不将内部 LazyGrid 复用解释为 LazyDynamicLayout 对外能力。

| 算法 | SDK 位置 |
|------|----------|
| Stack options/class | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:476-553` |
| Grid options/class | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:555-688` |
| Static variants | `interface/sdk-js/api/arkui/LayoutAlgorithm.static.d.ets:252-430` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| Pattern 复用边界 | Stack/Grid 使用成熟 Pattern，DynamicLayout 保持稳定外层节点 | AC-1.1, AC-2.1, AC-3.6 |
| union 互斥 | template 和 ItemFillPolicy 不得同时作为有效列策略 | AC-2.3, AC-2.4 |
| 参数级回退 | 单字段非法不使整个 DynamicLayout 失效；各入口遵循相同公开 API 契约 | AC-1.2, AC-2.2, AC-3.3 |
| Lazy 范围隔离 | 内部 LazyGrid 不扩展为 LazyDynamicLayout 规格 | AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Stack 为 O(n)；Grid 复用现有轨道/可见子项算法，不新增额外子树 | benchmark/trace | Model/Patterns |
| 功耗 | 参数不变时不重复触发 Measure；无后台任务 | 帧计数 | AC-1.5, AC-3.4 |
| 内存 | Pattern 切换释放旧私有状态，子节点不复制 | 泄漏 UT | AC-3.6 |
| 安全 | 非法模板和负 gap 不产生非法几何 | fuzz | AC-2.5, AC-3.3 |
| 可靠性 | 空子树、极小约束、union 快速切换不得崩溃/负几何 | 压力 UT | VM-2~VM-4 |
| 可测试性 | 固定约束可断言轨道、gap、offset 和 Pattern type | Layout UT | VM-1~VM-4 |
| 自动化维测 | dump 当前 type、alignment/template/policy/gaps | Inspector/trace | Property |
| 定界定位 | 区分 bridge union、Model mapping、Stack/LazyGrid algorithm | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 常用于 Stack/单列 Grid | 可用宽度决定轨道，不改变默认值 | 多尺寸测试 | AC-2.2 |
| 平板 | 可形成更多列 | template/policy 按大窗口约束计算 | 大窗口测试 | AC-2.2~AC-2.5 |
| 折叠屏 | 窗口变化可切换 Stack/Grid | 子状态保持，最新参数生效 | 姿态切换测试 | AC-3.4~AC-3.6 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Pattern 切换不重建语义节点；视觉顺序按具体算法 | AC-1.1, AC-2.1, AC-3.6 |
| 大字体 | 是 | 子项尺寸和轨道约束变化后 Grid 重测 | AC-2.2, AC-3.4 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | template/policy/gap 随窗口约束重算 | AC-2.2~AC-3.5 |
| 多用户 | 否 | 无持久状态 | N/A |
| 版本升级 | 是 | API 24 前不可见 | AC-1.1, AC-2.1 |
| 生态兼容 | 是 | Center、`'1fr'`、0 gap 和 union 互斥需稳定 | AC-1.2, AC-2.2~AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DynamicLayout Stack 与 Grid 算法
  Scenario: Stack 本地化对齐
    Given DynamicLayout 使用 StackLayoutAlgorithm(TopStart)
    And 布局方向为 RTL
    When Layout
    Then 水平 Start 按本地化方向镜像
    And 后声明子项保持覆盖

  Scenario: Grid 模板与间距
    Given Grid columnsTemplate 为 "1fr 1fr"
    And columnsGap 为 8vp且rowsGap 为 12vp
    When 布局四个子项
    Then 形成两列
    And gap 只位于相邻列/行之间

  Scenario: 切换 ItemFillPolicy
    Given 当前使用模板字符串
    When columnsTemplate 更新为有效 ItemFillPolicy
    Then policy 分支生效
    And 旧模板不再同时影响列计算
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖 DynamicLayout Stack/Grid preset
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] 内部 LazyGrid 复用未扩大为 LazyDynamicLayout Feat

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DynamicLayout Stack Grid columnsTemplate ItemFillPolicy LazyGrid gaps LocalizedAlignment"
  - repo: "openharmony/interface_sdk-js"
    query: "StackLayoutAlgorithm GridLayoutAlgorithm ItemFillPolicy LengthMetrics API 24"
```

**关键文档：**

- LayoutAlgorithm SDK：`interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/LayoutAlgorithm.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/13-dynamic-layout/design.md`
