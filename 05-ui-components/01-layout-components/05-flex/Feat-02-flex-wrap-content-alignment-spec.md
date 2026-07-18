# 特性规格

> Func-05-01-05-Feat-02 Flex 多行换行与内容对齐：固化 Wrap/WrapReverse 的分行、行内布局、alignContent、多行尺寸和 API 12 自适应行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Flex 多行换行与内容对齐 |
| 特性编号 | Func-05-01-05-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

当 `wrap` 不为 NoWrap 时，FlexLayoutPattern 选择 WrapLayoutAlgorithm。算法在 Measure 阶段按可用主轴容量形成行并记录每行尺寸，在 Layout 阶段先用 alignContent 分配行集合的交叉轴剩余空间，再按 justifyContent/alignItems 定位行内子项。证据见 `frameworks/core/components_ng/pattern/flex/flex_layout_pattern.h:31-50` 和 `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:29-43,68-205,321-359,464-536,571-718`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Wrap 分行与尺寸规格 | 覆盖有效子项、容量边界、超大子项、padding/border 和 API 12 自适应 |
| ADDED | 行内与行集合对齐规格 | 覆盖 justifyContent、alignItems、alignContent 和单行退化 |
| ADDED | WrapReverse 与方向组合规格 | 覆盖四种 direction、RTL 和交叉轴反向 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/05-flex/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/flex.d.ts` | 已核对 |
| Wrap algorithm | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp` | 已核对 |
| Pattern/Model | `frameworks/core/components_ng/pattern/flex/flex_layout_pattern.h`; `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp` | 已核对 |

> 双轴固定间距的解析边界由 Feat-03 定义；本文只说明已解析间距如何参与分行和行间布局。

## 用户故事

### US-1: 按可用主轴容量换行

**作为** 响应式界面开发者  
**我想要** Flex 在一行容纳不下子项时形成多行  
**以便** 内容适配不同窗口宽高

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN wrap=Wrap 或 WrapReverse THEN Pattern 使用 WrapLayoutAlgorithm，并读取 direction、justifyContent、alignItems、alignContent 与双轴间距 | 正常 |
| AC-1.2 | WHEN 下一个有效子项尺寸与行内 main space 会超出当前行可用主轴容量且当前行非空 THEN 结束当前行并在新行加入该子项 | 正常 |
| AC-1.3 | WHEN 首个有效子项自身超过可用主轴容量 THEN 该子项仍独占一行并受最终容器约束，不产生空前置行 | 边界 |
| AC-1.4 | WHEN 子项为 GONE、离流或不参与当前布局策略 THEN 不计入行有效数量、行主轴占用或换行判断 | 边界 |
| AC-1.5 | WHEN 只有一行或没有有效子项 THEN 安全完成测量，不因 alignContent 或行间公式除零 | 边界 |

### US-2: 对齐行内子项和多行内容

**作为** UI 布局开发者  
**我想要** 分别控制每行内部和多行集合的空间分配  
**以便** 形成稳定的响应式排版

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 一行形成后 THEN justifyContent 只在该行的有效子项之间分配该行主轴剩余空间，不跨行共享余量 | 正常 |
| AC-2.2 | WHEN alignItems 或子项 alignSelf 生效 THEN 以当前行交叉轴尺寸计算子项 Start/Center/End/Stretch/Baseline 位置 | 正常 |
| AC-2.3 | WHEN 存在多行且容器交叉轴有剩余空间 THEN alignContent 的 Start/Center/End/SpaceBetween/SpaceAround/SpaceEvenly/Stretch 按当前实现计算行集合 front/between 或行尺寸 | 正常 |
| AC-2.4 | WHEN 仅形成一行 THEN alignContent 不改变行内 justifyContent 或子项 alignItems 语义；固定 cross space 不形成可见行距 | 边界 |
| AC-2.5 | WHEN 多行总交叉轴尺寸超过容器可用交叉轴 THEN 剩余空间不得导致崩溃；行位置沿既有负余量/夹紧路径计算 | 异常 |

### US-3: 组合方向、反向和版本边界

**作为** 跨版本应用开发者  
**我想要** Wrap 在方向、文本方向和目标 API 变化下保持可追溯  
**以便** 避免升级后行序漂移

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN direction 为 Row/Column 系列 THEN 分行容量分别使用水平/垂直主轴，行集合沿对应交叉轴推进 | 正常 |
| AC-3.2 | WHEN wrap=WrapReverse THEN 行集合沿交叉轴反向排列；direction 的 `*_REVERSE` 仍独立控制每行主轴视觉顺序 | 正常 |
| AC-3.3 | WHEN layoutDirection=RTL THEN 水平轴 Start/End 按文本方向解释，并与 direction/wrap 的反向组合一次，不重复镜像 | 正常 |
| AC-3.4 | WHEN 目标 API 为 12+ 且 Wrap 容器使用自适应/无限约束 THEN 采用 API 12 分支计算主交叉轴理想尺寸；低版本保持既有分支 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | Wrap Measure UT | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:29-43,68-205` |
| AC-2.1~AC-2.5 | R-6~R-10 | 已有实现 | 行内/多行 Layout 矩阵 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:464-536,571-718` |
| AC-3.1~AC-3.4 | R-11~R-14 | 已有实现 | direction/wrap/RTL/API level 回归 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:321-359,464-718` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | wrap 非 NoWrap | Pattern 创建 WrapLayoutAlgorithm | `frameworks/core/components_ng/pattern/flex/flex_layout_pattern.h:31-50` | AC-1.1 |
| R-2 | 行为 | 新子项将超过非空当前行容量 | 提交当前行并创建下一行 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:68-205` | AC-1.2 |
| R-3 | 边界 | 首项大于主轴容量 | 首项独占当前行，不创建空行 | 同上 | AC-1.3 |
| R-4 | 边界 | GONE/离流/被排除子项 | 跳过占用和有效计数 | 同上 | AC-1.4 |
| R-5 | 边界 | 0 或 1 行 | 使用安全默认 front/between 值，不执行非法除法 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:464-536` | AC-1.5 |
| R-6 | 行为 | 行内主轴布局 | 每行独立应用 justifyContent | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:571-718` | AC-2.1 |
| R-7 | 行为 | 行内交叉轴布局 | 使用 alignSelf 优先，否则 alignItems | 同上 | AC-2.2 |
| R-8 | 行为 | 多行且交叉轴有剩余空间 | alignContent 计算行集合 front/between/Stretch | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:464-536` | AC-2.3 |
| R-9 | 边界 | 单行 | alignContent 不替代行内对齐；无 cross gap | 同上 | AC-2.4 |
| R-10 | 异常 | 多行总尺寸超出交叉轴 | 沿当前负余量或约束路径完成定位，不崩溃 | 同上 | AC-2.5 |
| R-11 | 行为 | Row/Column 系列 | 使用对应主轴容量和交叉轴推进方向 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:29-43,68-205` | AC-3.1 |
| R-12 | 行为 | WrapReverse 或 `*_REVERSE` | 分别反转行集合交叉轴或行内主轴 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:571-718` | AC-3.2 |
| R-13 | 行为 | RTL | 仅对水平轴执行一次 Start/End 镜像并与反向组合 | 同上 | AC-3.3 |
| R-14 | 边界 | API 12+ 自适应约束 | 使用版本分支计算理想尺寸，低版本不回灌 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:321-359` | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | Wrap Measure UT | 算法选择、换行阈值、超大首项、无效子项、空/单行 |
| VM-2 | R-6~R-10, AC-2.1~AC-2.5 | Wrap Layout 参数矩阵 | 每行 justify、alignSelf、七种 alignContent、溢出 |
| VM-3 | R-11~R-14, AC-3.1~AC-3.4 | 方向/RTL/API 回归 | 主交叉轴、两类 reverse、API 12 尺寸 |

## API 变更分析

> 本文补录已有接口，不新增或废弃 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Flex({ wrap, direction, justifyContent, alignItems, alignContent })` | Public | FlexOptions 的换行与对齐字段 | `FlexAttribute` | N/A | API 7 创建多行弹性容器 | AC-1.1~AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 存量 Wrap 行为补录 | 无需迁移 | AC-1.1~AC-3.4 |

## 接口规格

### 接口定义

**Flex(value?) — Wrap 模式**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Flex(value?: FlexOptions): FlexAttribute` |
| 返回值 | `FlexAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.4 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| wrap | FlexWrap | 否 | NoWrap | 本 Feat 使用 Wrap/WrapReverse |
| direction | FlexDirection | 否 | Row | 决定分行主轴和行集合交叉轴 |
| justifyContent | FlexAlign | 否 | Start | 每行独立应用 |
| alignItems | ItemAlign | 否 | Stretch | 子项 alignSelf 优先 |
| alignContent | FlexAlign | 否 | Start | 仅多行集合产生可见分布 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 子项累计占用跨越主轴容量 | 在当前非空行之后换行 | AC-1.2~AC-1.3 |
| 2 | 多行 + alignContent | 按行集合交叉轴剩余空间定位 | AC-2.3~AC-2.5 |
| 3 | WrapReverse + direction reverse + RTL | 各维度反向只应用一次 | AC-3.1~AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；行信息仅存在于布局周期。
- **最低支持版本:** API 7。
- **API 版本号策略:** SDK `@since` 定义公开边界，API 12 算法分支保持目标版本隔离。

| API/目标版本 | 既有行为 | 证据 | 关联 AC |
|--------------|----------|------|---------|
| API 7 | Wrap、WrapReverse、alignContent 等 FlexOptions 开放 | `interface/sdk-js/api/@internal/component/ets/flex.d.ts:30-95` | AC-1.1, AC-2.3, AC-3.2 |
| API 12 | Wrap 自适应尺寸使用新版本分支 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:321-359` | AC-3.4 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| Pattern 分派 | wrap 非 NoWrap 才进入 WrapLayoutAlgorithm | AC-1.1 |
| Measure 先于 Layout | 行分组与每行尺寸是 alignContent/行内定位的输入 | AC-1.2~AC-2.5 |
| 双重反向分离 | direction reverse 管行内，WrapReverse 管行集合 | AC-3.2 |
| 版本隔离 | API 12 自适应分支不影响低目标版本 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增指标；分行与定位继续按子项/行线性处理 | Trace/benchmark | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:68-205,571-718` |
| 功耗 | 不新增后台任务或定时器 | 代码审查 | VM-1~VM-3 |
| 内存 | 行分组中间状态仅在算法/布局周期持有 | 内存 UT | WrapLayoutAlgorithm |
| 安全 | 不涉及权限和敏感数据 | 代码审查 | VM-1~VM-3 |
| 可靠性 | 空行、单行、超大子项、负余量不得崩溃 | 边界 UT/fuzz | AC-1.3~AC-1.5, AC-2.5 |
| 可测试性 | 行数、行尺寸和 child offset 均可观测 | 追溯审查 | VM-1~VM-3 |
| 自动化维测 | 沿用 LayoutProperty/Pattern dump | Inspector/Dump | `frameworks/core/components_ng/pattern/flex/flex_layout_property.h:56-75` |
| 定界定位 | 可区分 options 解析、分行、行集合和行内定位 | 代码路径审查 | `05-ui-components/01-layout-components/05-flex/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 窄窗口更易形成多行 | 换行阈值只由可用主轴容量和子项占用决定 | 多宽度 Layout UT | AC-1.2 |
| 平板 | 宽窗口可能退化为单行 | 单行时 alignContent 不产生额外行分布 | 可变窗口测试 | AC-2.4 |
| 折叠屏 | 展开/折叠会重新分行 | 约束变化触发 Measure/Layout | 折叠态切换测试 | AC-1.2, AC-3.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 换行/反向改变视觉位置，不重建声明语义身份 | AC-3.2~AC-3.3 |
| 大字体 | 是 | 子项增大可能跨越换行阈值 | AC-1.2~AC-1.3 |
| 深色模式 | 否 | 不涉及颜色或主题 | N/A |
| 多窗口/分屏 | 是 | 主轴容量变化会重新形成行 | AC-1.2, AC-3.4 |
| 多用户 | 否 | 无持久用户状态 | N/A |
| 版本升级 | 是 | API 7/12 自适应差异需回归 | AC-3.4 |
| 生态兼容 | 是 | direction/wrap/RTL 组合是跨语言通道稳定性边界 | AC-3.1~AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Flex 多行换行与内容对齐
  Scenario: 超出容量后换行
    Given 一个主轴容量为 200vp 的 Wrap Flex
    And 三个子项含间距后的占用依次为 80vp 80vp 80vp
    When Measure 完成
    Then 前两个子项位于第一行
    And 第三个子项位于第二行

  Scenario: WrapReverse 与 RowReverse 独立
    Given direction 为 RowReverse
    And wrap 为 WrapReverse
    When Layout 完成
    Then 每行子项沿水平主轴反向
    And 行集合沿交叉轴反向
```

## Spec 自审清单

- [x] 无占位文本，状态为 Draft
- [x] AC 覆盖算法选择、换行阈值、行内/行集合对齐和版本边界
- [x] 每个 AC 均可通过行数、尺寸或 offset 观测
- [x] 双轴 space 解析、多范式与 PointLight 已路由到 Feat-03~05
- [x] 所有 AC 与规则、VM 建立追溯关系

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "WrapLayoutAlgorithm line grouping alignContent WrapReverse adaptive API 12"
  - repo: "openharmony/interface_sdk-js"
    query: "FlexWrap WrapReverse alignContent FlexOptions API 7"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/flex.d.ts`
- 架构设计：`05-ui-components/01-layout-components/05-flex/design.md`
