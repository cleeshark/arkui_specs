# 特性规格

> Func-05-01-05-Feat-01 Flex 单行弹性布局与轴向对齐：固化 NoWrap 模式的创建、四种方向、主轴/交叉轴对齐、尺寸收敛、RTL 与视觉反向语义。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Flex 单行弹性布局与轴向对齐 |
| 特性编号 | Func-05-01-05-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Flex 在 `wrap=FlexWrap.NoWrap` 时使用 `FlexLayoutAlgorithm`，由 `direction` 建立主轴和交叉轴，通过 `justifyContent`、`alignItems` 以及子项 `alignSelf` 计算剩余空间和最终偏移。方向反转与 RTL 在 Layout 阶段共同决定视觉起点，不改变声明子项身份。生产链见 `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:22-161`、`frameworks/core/components_ng/pattern/flex/flex_layout_pattern.h:31-50` 和 `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:230-263,1287-1364,1567-1734`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Flex NoWrap 容器身份与默认值规格 | 覆盖 FLEX FrameNode、Pattern、Property、Algorithm 和默认 options |
| ADDED | 四种方向及轴向对齐规格 | 覆盖 Row/RowReverse/Column/ColumnReverse、主轴六种分布和交叉轴对齐 |
| ADDED | 尺寸、RTL、反向与异常输入规格 | 覆盖约束夹紧、API 26 单轴 match-parent、文本方向和 API 10 回退 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/05-flex/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/flex.d.ts` | 已核对 |
| NG Model/Pattern | `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp`; `frameworks/core/components_ng/pattern/flex/flex_layout_pattern.h` | 已核对 |
| Layout algorithm | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 已核对 |

> 本文是存量能力补录；不要求修改实现。Wrap、双轴显式 space、多范式兼容和 PointLight 分别由 Feat-02~05 承接。

## 用户故事

### US-1: 创建单行弹性容器

**作为** ArkUI 应用开发者  
**我想要** 创建可在水平或垂直方向排列子项的 Flex  
**以便** 用同一容器表达单行弹性布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `Flex()` 且未提供 options THEN 创建 tag 为 FLEX 的非原子 FrameNode，默认 direction=Row、wrap=NoWrap、justifyContent=Start、alignItems=Stretch、alignContent=Start | 正常 |
| AC-1.2 | WHEN Pattern 检测到 `wrap=NoWrap` THEN 创建 `FlexLayoutAlgorithm` 而不是 `WrapLayoutAlgorithm`，并由 `FlexLayoutProperty` 提供布局属性 | 正常 |
| AC-1.3 | WHEN Flex 包含多个普通子项 THEN 按声明顺序参与测量和焦点/语义树，视觉反转只改变 Layout offset | 正常 |
| AC-1.4 | WHEN Flex 不包含子项 THEN 采用 LayoutConstraint、calc constraint 和 measure type 解析出的合法容器尺寸并安全结束 | 边界 |

### US-2: 配置方向和主轴分布

**作为** UI 布局开发者  
**我想要** 选择主轴方向并分配剩余空间  
**以便** 在不同阅读方向和容器尺寸下稳定排列内容

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN direction=Row 或 RowReverse THEN 主轴为水平、交叉轴为垂直；WHEN direction=Column 或 ColumnReverse THEN 主轴为垂直、交叉轴为水平 | 正常 |
| AC-2.2 | WHEN justifyContent 为 Start/Center/End THEN 首项前空间分别为 0、剩余空间一半、全部剩余空间 | 正常 |
| AC-2.3 | WHEN justifyContent 为 SpaceBetween 且有效子项数 n>1 THEN 首项前空间为 0，相邻间距为 `remain/(n-1)`；n<=1 时不除零 | 边界 |
| AC-2.4 | WHEN justifyContent 为 SpaceAround 或 SpaceEvenly 且 n>0 THEN 分别使用 `remain/(2n)` 与 `remain/(n+1)` 作为首项前空间，并按对应公式形成相邻间距 | 正常 |
| AC-2.5 | WHEN direction 为 `*_REVERSE` THEN Layout 从相反主轴端定位子项，但 Measure 得到的容器尺寸和子项尺寸不因反向而改变 | 正常 |

### US-3: 配置交叉轴对齐与尺寸

**作为** UI 布局开发者  
**我想要** 控制子项在交叉轴上的定位和拉伸  
**以便** 获得可预测的行高或列宽

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN alignItems 为 Start/Center/End THEN 子项分别位于交叉轴起点、居中或末端，偏移基于容器交叉轴可用尺寸与子项尺寸计算 | 正常 |
| AC-3.2 | WHEN alignItems=Stretch 且子项未在交叉轴提供确定尺寸 THEN 子项按可用交叉轴约束重测；已有确定尺寸不被无条件覆盖 | 边界 |
| AC-3.3 | WHEN 子项设置有效 `alignSelf` THEN 该值覆盖容器 alignItems；未设置或 Auto 时继承容器值 | 正常 |
| AC-3.4 | WHEN 子项为 GONE、离流或被 layout-policy 排除 THEN 不参与有效子项尺寸累计和空间分布 | 边界 |
| AC-3.5 | WHEN 测量结果超出 min/max 约束 THEN 最终主轴和交叉轴尺寸分别被夹紧；API 26+ 的单轴 match-parent 子项在分类后重测 | 边界 |

### US-4: 在 RTL 和非法输入下保持兼容

**作为** 国际化应用开发者  
**我想要** Flex 在 RTL 与版本边界下保持既有行为  
**以便** 避免升级后出现排列漂移

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN layoutDirection=RTL 且主轴为 Row THEN 水平起点按 RTL 镜像，并与 RowReverse 的视觉反向组合计算；不得重复或遗漏子项 | 正常 |
| AC-4.2 | WHEN 主轴为 Column 且 layoutDirection=RTL THEN RTL 只影响水平交叉轴 Start/End 解释，不把垂直主轴自动反转 | 边界 |
| AC-4.3 | WHEN API 10+ Dynamic options 中 direction/wrap/align 枚举越界 THEN 对应字段回退到其默认值且不抛异常 | 异常 |
| AC-4.4 | WHEN 低于 API 10 的目标版本运行既有输入路径 THEN 保留 legacy 参数解释和尺寸分支，不套用 API 10+ 校验结果 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | NG 创建/空容器 UT + 代码审查 | `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:22-90`; `frameworks/core/components_ng/pattern/flex/flex_layout_pattern.h:31-50` |
| AC-2.1~AC-2.5 | R-5~R-8 | 已有实现 | 方向与主轴参数矩阵 Layout UT | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:53-91,230-263,1567-1657` |
| AC-3.1~AC-3.5 | R-9~R-12 | 已有实现 | 交叉轴/约束/子项状态 Layout UT | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1230-1364,1660-1734` |
| AC-4.1~AC-4.4 | R-13~R-16 | 已有实现 | RTL + API level 回归 | `frameworks/bridge/declarative_frontend/jsview/js_flex.cpp:55-92`; `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:230-263,1567-1625` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Flex 创建入口 | 创建 FLEX FrameNode 与 FlexLayoutPattern，写入 options | `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:22-90` | AC-1.1 |
| R-2 | 行为 | wrap 为 NoWrap | Pattern 返回 FlexLayoutAlgorithm | `frameworks/core/components_ng/pattern/flex/flex_layout_pattern.h:31-50` | AC-1.2 |
| R-3 | 行为 | 测量普通子项 | 按有效子项列表累计尺寸，视觉反向留到 Layout | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1287-1364,1567-1625` | AC-1.3 |
| R-4 | 边界 | 无子项 | 直接采用解析并夹紧后的合法容器尺寸 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1230-1285,1311-1313` | AC-1.4 |
| R-5 | 行为 | 解析 direction | Row 系列为水平主轴，Column 系列为垂直主轴 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:230-263` | AC-2.1 |
| R-6 | 行为 | Start/Center/End | frontSpace 分别为 0、remain/2、remain | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` | AC-2.2 |
| R-7 | 边界 | 三种 Space* 对齐 | 按有效子项数计算 front/between，空或单子项路径避免除零 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` | AC-2.3, AC-2.4 |
| R-8 | 行为 | direction 为 RowReverse/ColumnReverse | Layout 翻转主轴起点和推进方向，不重写测量尺寸 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:53-91,1567-1625` | AC-2.5 |
| R-9 | 行为 | 计算交叉轴位置 | 按 Start/Center/End 计算 offset | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1660-1734` | AC-3.1 |
| R-10 | 边界 | Stretch 或 alignSelf | 未确定交叉轴尺寸时允许重测；alignSelf 优先于容器值 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1660-1734` | AC-3.2, AC-3.3 |
| R-11 | 边界 | 子项 GONE/离流/被排除 | 跳过尺寸和有效数量统计 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1287-1364` | AC-3.4 |
| R-12 | 边界 | 尺寸越界或 API 26 单轴 match-parent | clamp 容器尺寸；分类并重测对应子项 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:28-40,1230-1364` | AC-3.5 |
| R-13 | 行为 | RTL + Row/RowReverse | 文本方向与 direction reverse 共同确定水平起点 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:53-91,230-263` | AC-4.1 |
| R-14 | 边界 | RTL + Column 系列 | 仅镜像水平交叉轴语义 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:230-263,1660-1734` | AC-4.2 |
| R-15 | 异常 | API 10+ Dynamic 枚举非法 | 对字段使用既定默认值，不抛异常 | `frameworks/bridge/declarative_frontend/jsview/js_flex.cpp:55-92` | AC-4.3 |
| R-16 | 边界 | 目标 API 低于 10 | 保留 legacy 参数/尺寸版本分支 | `frameworks/bridge/declarative_frontend/jsview/models/flex_model_impl.cpp:26-184`; `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1163-1227` | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | NG UT + 代码审查 | FrameNode、默认值、算法选择、空容器 |
| VM-2 | R-5~R-8, AC-2.1~AC-2.5 | Layout 参数矩阵 | 四方向、六种主轴分布、反向尺寸不变 |
| VM-3 | R-9~R-12, AC-3.1~AC-3.5 | Layout UT | Stretch、alignSelf、GONE、min/max、API 26 重测 |
| VM-4 | R-13~R-16, AC-4.1~AC-4.4 | RTL/API level 回归 | RTL 组合、非法值和 legacy 边界 |

## API 变更分析

> 本文补录已有接口，不引入新 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Flex(value?: FlexOptions)` | Public | direction/wrap/justifyContent/alignItems/alignContent | `FlexAttribute` | N/A | API 7 创建弹性容器并配置轴向布局 | AC-1.1~AC-4.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录单行布局行为 | 无需迁移 | AC-1.1~AC-4.4 |

## 接口规格

### 接口定义

**Flex(value?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Flex(value?: FlexOptions): FlexAttribute` |
| 返回值 | `FlexAttribute` — 创建并配置 Flex 容器 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value.direction | FlexDirection | 否 | Row | Row/RowReverse/Column/ColumnReverse |
| value.wrap | FlexWrap | 否 | NoWrap | 本 Feat 验收 NoWrap；Wrap 路由 Feat-02 |
| value.justifyContent | FlexAlign | 否 | Start | Start/Center/End/SpaceBetween/SpaceAround/SpaceEvenly |
| value.alignItems | ItemAlign | 否 | Stretch | 子项 alignSelf 可覆盖 |
| value.alignContent | FlexAlign | 否 | Start | NoWrap 下不产生多行内容分布 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | NoWrap + 四种 direction + LTR/RTL | 按主轴方向和文本方向定位，不改变声明子项身份 | AC-2.1, AC-2.5, AC-4.1~AC-4.2 |
| 2 | 六种 justifyContent | 按剩余空间和有效子项数计算 front/between | AC-2.2~AC-2.4 |
| 3 | alignItems/alignSelf/Stretch | 计算交叉轴 offset 或重测 | AC-3.1~AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；只固化当前 API 7–26 行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；属性随 LayoutProperty 生命周期存在。
- **最低支持版本:** API 7。
- **API 版本号策略:** 对外以 canonical SDK `@since` 为准，算法的目标 API 分支作为运行兼容边界。

| API/目标版本 | 既有行为 | 证据 | 关联 AC |
|--------------|----------|------|---------|
| API 7 | FlexOptions 与五个轴向字段开放 | `interface/sdk-js/api/@internal/component/ets/flex.d.ts:30-95,150-172` | AC-1.1, AC-2.1 |
| API 10 | Dynamic 非法枚举使用校验后默认值；主轴自适应约束分支变化 | `frameworks/bridge/declarative_frontend/jsview/js_flex.cpp:55-92`; `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1163-1227` | AC-4.3~AC-4.4 |
| API 26 | Flex/Row/Column 单轴 match-parent 子项分类重测 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:28-40,1351-1363` | AC-3.5 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| Pattern 选算法 | NoWrap 必须使用 FlexLayoutAlgorithm | AC-1.2 |
| 属性驱动 | direction/align 属性由 FlexLayoutProperty 持有并触发 Measure | AC-2.1~AC-3.3 |
| Measure/Layout 分离 | 尺寸计算不因视觉反向重排子项身份 | AC-1.3, AC-2.5 |
| 版本隔离 | API 10/26 分支不得无条件影响低目标版本 | AC-3.5, AC-4.3~AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增指标；单行 Measure/Layout 继续按有效子项线性遍历 | Trace/现有 benchmark | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1287-1364,1567-1625` |
| 功耗 | 不新增定时器、后台任务或额外帧请求 | 代码审查 | VM-1~VM-4 |
| 内存 | 不复制持久 child list；算法中间量随布局周期释放 | 内存 UT | FlexLayoutAlgorithm 调用链 |
| 安全 | 不访问权限、敏感数据或外部输入源 | 代码审查 | VM-1~VM-4 |
| 可靠性 | 合法 SDK 输入不得崩溃；空容器、单子项和非法枚举安全收敛 | 异常 UT/fuzz | AC-1.4, AC-2.3~AC-2.4, AC-4.3 |
| 可测试性 | 每组 AC 映射到独立 VM，可检查 frame size/offset/property | 追溯审查 | VM-1~VM-4 |
| 自动化维测 | 沿用布局属性 Inspector/Dump，不新增维测协议 | Inspector/Dump UT | `frameworks/core/components_ng/pattern/flex/flex_layout_property.h:56-75` |
| 定界定位 | 能区分 SDK parser、Model、Pattern、Measure 和 Layout 层 | 源码/日志定位 | `05-ui-components/01-layout-components/05-flex/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无 Flex 专有差异 | 可用窗口约束与 density 影响尺寸，不改变轴向公式 | 多密度 Layout UT | AC-2.1~AC-3.5 |
| 平板 | 无 Flex 专有差异 | 大窗口增加 remain，六种分布公式保持一致 | 可变窗口测试 | AC-2.2~AC-2.4 |
| 折叠屏 | 无 Flex 专有差异 | 折叠态约束变化触发重新 Measure/Layout | 折叠态切换测试 | AC-3.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 视觉 reverse 不重排声明语义/焦点身份，需验证阅读顺序 | AC-1.3, AC-2.5 |
| 大字体 | 是 | 子项尺寸变化会重新参与主/交叉轴测量 | AC-3.5 |
| 深色模式 | 否 | 本 Feat 不涉及颜色或主题 | N/A |
| 多窗口/分屏 | 是 | remain 与最终尺寸随父约束重新计算 | AC-2.2~AC-3.5 |
| 多用户 | 否 | 无用户级持久状态 | N/A |
| 版本升级 | 是 | API 7/10/26 边界必须回归 | AC-3.5, AC-4.3~AC-4.4 |
| 生态兼容 | 是 | RTL、非法枚举和默认值须保持当前路径事实 | AC-4.1~AC-4.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Flex 单行弹性布局与轴向对齐
  Scenario: 水平容器按 SpaceBetween 分布
    Given 一个宽 300vp 的 NoWrap Row Flex
    And 三个有效子项总宽为 180vp
    When justifyContent 设置为 SpaceBetween
    Then 首项前空间为 0
    And 两个相邻间距均为 60vp

  Scenario: RowReverse 与 RTL 组合
    Given 一个 layoutDirection 为 RTL 的 NoWrap Flex
    And direction 为 RowReverse
    When Layout 完成
    Then 每个有效子项只出现一次
    And 视觉起点由 RTL 与 RowReverse 的组合规则确定
    And 声明语义顺序不变

  Scenario: 子项 alignSelf 覆盖容器
    Given Flex alignItems 为 Start
    And 第二个子项 alignSelf 为 End
    When Layout 完成
    Then 第二个子项位于交叉轴末端
    And 其他子项仍位于交叉轴起点
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可由属性、尺寸或 offset 观测
- [x] 范围只覆盖 NoWrap 单行布局，Wrap/space/多范式/PointLight 已路由
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 默认值、空容器、单子项、RTL、非法枚举和 API 分支均有边界
- [x] 实现偏差仅作为风险/兼容边界记录，不伪装为新增需求

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Flex NoWrap FlexLayoutAlgorithm direction justifyContent alignItems RTL reverse"
  - repo: "openharmony/interface_sdk-js"
    query: "FlexOptions FlexDirection FlexWrap FlexAlign ItemAlign API 7"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/flex.d.ts`
- 架构设计：`05-ui-components/01-layout-components/05-flex/design.md`
