# 特性规格

> Func-05-01-03-Feat-01 Column 创建、尺寸与子项间距：固化纵向容器创建、自适应尺寸、显式 space、Resource 更新及非法输入的存量行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Column 创建、尺寸与子项间距 |
| 特性编号 | Func-05-01-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

Column 创建 `LinearLayoutPattern(true)` 并固定 `FlexDirection::COLUMN`，通过 `LinearLayoutAlgorithm -> FlexLayoutAlgorithm` 测量子项。未显式约束尺寸时，主轴由有效子项累计尺寸决定，交叉轴取子项最大尺寸；显式 space 仅插入非 GONE、非离流的相邻子项之间。实现入口见 `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:24-40,128-136`、`frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:34-55` 和 `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1163-1183,1287-1364`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Column 创建与容器身份规格 | 覆盖 FrameNode、Pattern、Property、Algorithm 和 Focus Scope |
| ADDED | Column 自适应尺寸规格 | 覆盖空容器、有子项、padding/border、约束夹紧及 API 26 重测 |
| ADDED | 显式 space 与 Resource 规格 | 覆盖默认值、单位、有效子项、配置更新和非法输入 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/03-column/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/column.d.ts` | 已核对 |
| NG Model | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp` | 已核对 |
| Layout algorithm | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 已核对 |

> 本文档是存量能力补录。当前实现即规格；实现与 SDK 不一致之处只记录为兼容风险。

## 用户故事

### US-1: 创建纵向线性容器

**作为** ArkUI 应用开发者  
**我想要** 创建能够包含子组件的 Column  
**以便** 按声明顺序组织纵向内容

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `Column()` THEN 创建 tag 为 COLUMN 的非原子 FrameNode，Pattern 为 vertical `LinearLayoutPattern`，布局方向为 `FlexDirection::COLUMN` | 正常 |
| AC-1.2 | WHEN Pattern 创建布局对象 THEN 使用 `LinearLayoutProperty` 与继承 `FlexLayoutAlgorithm` 的 `LinearLayoutAlgorithm`，并允许构建多个子节点 | 正常 |
| AC-1.3 | WHEN 未设置 Column 专有属性 THEN 默认 `space=0`、主轴 Start、交叉轴 Center、`reverse=false`；本 Feat 只验收默认 space，其他默认值由 Feat-02 验收 | 边界 |
| AC-1.4 | WHEN Column 参与焦点遍历 THEN Pattern 作为纵向 Flex 类型 Focus Scope，不作为原子节点截断子项遍历 | 正常 |

### US-2: 按内容和约束确定容器尺寸

**作为** ArkUI 布局开发者  
**我想要** Column 在没有显式宽高时按子项自适应并服从父约束  
**以便** 获得可预测的包裹内容尺寸

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Column 未得到显式主轴理想尺寸且包含有效子项 THEN Measure 累计子项主轴尺寸与有效间距，并在无限/auto/wrap/fix 主轴场景把最终主轴尺寸收敛到累计值 | 正常 |
| AC-2.2 | WHEN Column 未得到显式交叉轴理想尺寸 THEN 交叉轴以测量到的最大子项交叉轴尺寸为基础，并加上左右 padding/border 后受 min/max 约束夹紧 | 正常 |
| AC-2.3 | WHEN Column 没有子项 THEN Measure 直接采用由 LayoutConstraint、calc constraint 和 measure type 解析出的理想尺寸并结束，不执行子项测量 | 边界 |
| AC-2.4 | WHEN 测得内容尺寸加 padding/border 超出 min/max 区间 THEN 最终主轴和交叉轴分别钳制在各自约束区间 | 边界 |
| AC-2.5 | WHEN API 26+ 的 Column 子项使用单轴 match-parent 策略 THEN 算法分类并重测对应子项后再确定最终 realSize；低版本沿既有自适应子项路径处理 | 边界 |

### US-3: 配置显式子项间距

**作为** ArkUI 应用开发者  
**我想要** 设置相邻有效子项之间的固定间距  
**以便** 无需逐个设置 margin 即可形成一致留白

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `space` 为非负 number 或可转换 string THEN 按 vp 或显式单位转为 px，并在 n 个有效子项之间累计 `space * max(n-1, 0)` | 正常 |
| AC-3.2 | WHEN 子项为 GONE、离流或不参与当前 layout-policy 统计 THEN 该子项不增加有效计数或已占用主轴尺寸，间距只连接其余有效子项 | 边界 |
| AC-3.3 | WHEN Dynamic 构造参数为负数或 API 10+ 无法解析的值 THEN 构造入口按 0 间距处理且不抛异常 | 异常 |
| AC-3.4 | WHEN direct NG Model 收到负 space THEN 记录错误日志且不覆盖既有 space 属性 | 异常 |
| AC-3.5 | WHEN space 内部形成 PERCENT 或 CALC Dimension THEN 当前无百分比参照长度的 `ConvertToPx()` 路径得到 0，不能表现为相对 Column 高度的间距 | 边界 |
| AC-3.6 | WHEN `justifyContent` 为 SpaceBetween/SpaceAround/SpaceEvenly THEN 显式 space 不生效；具体分布公式和组合验收归 Feat-02 | 边界 |

### US-4: 响应 Resource space 配置变化

**作为** 使用资源化尺寸的应用开发者  
**我想要** Column 在资源配置变化时更新间距  
**以便** 适配密度、语言或资源限定符变化

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 18+ 的 `ColumnOptionsV2.space` 是可解析 Resource THEN 初次解析并以 `column.space` 为 key 注册弱引用资源更新器 | 正常 |
| AC-4.2 | WHEN 配置变化后 Resource 解析为非负值 THEN 更新 space 并显式标记 `PROPERTY_UPDATE_MEASURE` | 正常 |
| AC-4.3 | WHEN Resource 构造首次解析为负值 THEN 不写入 space；WHEN setter 的配置更新回调解析为负值 THEN reset space 属性 | 异常 |
| AC-4.4 | WHEN FrameNode 已销毁或 Pattern 不可用 THEN 资源更新器弱引用升级失败后直接退出，不访问失效节点 | 恢复 |
| AC-4.5 | WHEN 后续切换为普通数值或执行 reset THEN Node modifier 移除 `column.space` 资源对象，避免配置更新再次覆盖显式值 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-3 | 已有实现 | NG 创建/焦点 UT + 代码审查 | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:24-40,128-136`; `frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:34-69` |
| AC-2.1~AC-2.5 | R-4~R-7 | 已有实现 | Layout UT + 约束矩阵 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1163-1285,1287-1364` |
| AC-3.1~AC-3.6 | R-8~R-12 | 已有实现 | NG/Layout UT + 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_column.cpp:44-57`; `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1531-1554` |
| AC-4.1~AC-4.5 | R-13~R-16 | 已有实现 | Resource 配置更新 UT | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:43-125,139-148`; `frameworks/core/interfaces/native/node/column_modifier.cpp:75-96` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 Column 创建入口 | 创建 COLUMN FrameNode、`LinearLayoutPattern(true)` 并写 `FlexDirection::COLUMN` | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:24-40,128-136` | AC-1.1 |
| R-2 | 行为 | Pattern 创建 Property/Algorithm | 返回 `LinearLayoutProperty` 和 `LinearLayoutAlgorithm`，容器非原子 | `frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:34-55` | AC-1.2 |
| R-3 | 行为 | Column 参与焦点遍历 | 返回纵向 Flex ScopeFocusAlgorithm | `frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:57-69` | AC-1.4 |
| R-4 | 行为 | 无显式主轴尺寸且 main axis 为 infinite/auto/wrap/fix | 最终主轴尺寸使用累计 allocatedSize | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1163-1183,1196-1228` | AC-2.1 |
| R-5 | 行为 | 测量有效子项 | 主轴累计子项尺寸，交叉轴维护最大值 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:773-798,883-890` | AC-2.1, AC-2.2 |
| R-6 | 边界 | 子项为空或最终尺寸越界 | 空容器直接写 realSize；非空容器最终尺寸 clamp 到 min/max | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1230-1285,1311-1313` | AC-2.3, AC-2.4 |
| R-7 | 边界 | API 26+ 且子项使用单轴 match-parent | 分类重测 match-parent 子项后写 frame size | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:28-40,1351-1363` | AC-2.5 |
| R-8 | 行为 | n 个有效子项且 main align 不是三种 Space* | 已占用尺寸增加 `space * (n-1)`，n<=1 时不形成可见间距 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1531-1554` | AC-3.1 |
| R-9 | 边界 | 子项 GONE、离流或被排除的 layout-policy child | 跳过该子项的已占用尺寸统计 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1545-1553` | AC-3.2 |
| R-10 | 异常 | Dynamic 构造 space 解析失败或值无效 | API 10+ 使用 0；direct NG negative 不覆盖属性 | `frameworks/bridge/declarative_frontend/jsview/js_column.cpp:44-57`; `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:35-40,84-92` | AC-3.3, AC-3.4 |
| R-11 | 边界 | space 单位为 PERCENT/CALC | 无参 `ConvertToPx()` 返回 0 | `frameworks/base/geometry/dimension.cpp:209-229`; `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:241-248` | AC-3.5 |
| R-12 | 边界 | main align 是 SpaceBetween/Around/Evenly | 清空显式 space 的占用贡献，分布由 Feat-02 定义 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1538-1544` | AC-3.6 |
| R-13 | 行为 | Resource space 首次设置 | 注册 `column.space` updater 并写入非负解析值 | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:43-81,94-125` | AC-4.1 |
| R-14 | 行为 | Resource 配置变化得到非负值 | 更新属性并标记 Measure | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:57-75,100-118` | AC-4.2 |
| R-15 | 异常 | Resource 初次/更新解析得到负值 | 初次不覆盖；setter 更新回调 reset | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:77-81,113-125` | AC-4.3 |
| R-16 | 恢复 | 节点失效或移除 Resource | WeakPtr 升级失败退出；ResetResObj 删除 keyed updater | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:57-63,100-105,139-148`; `frameworks/core/interfaces/native/node/column_modifier.cpp:75-96` | AC-4.4, AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~AC-1.4 | NG UT | FrameNode、Pattern、Property、Algorithm 与 Focus Scope |
| VM-2 | R-4~R-7, AC-2.1~AC-2.5 | Layout UT | 内容自适应、空容器、padding/border、min/max、API 26 match-parent |
| VM-3 | R-8~R-12, AC-3.1~AC-3.6 | Layout UT + 参数矩阵 | 有效子项计数、0/负数、单位和 Space* 边界 |
| VM-4 | R-13~R-16, AC-4.1~AC-4.5 | Resource 更新 UT | 初次解析、配置变化、负值、弱引用和 updater 移除 |

## API 变更分析

> 本文档补录已有接口，不引入新的 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Column(options?: ColumnOptions)` | Public | `space?: string \| number` | `ColumnAttribute` | N/A | API 7 创建纵向容器并设置固定间距 | AC-1.1, AC-3.1~AC-3.4 |
| `Column(options?: ColumnOptions \| ColumnOptionsV2)` | Public | V2 的 space 增加 Resource | `ColumnAttribute` | N/A | API 18 支持资源化间距 | AC-4.1~AC-4.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录存量创建与间距行为 | 无需迁移 | AC-1.1~AC-4.5 |

## 接口规格

### 接口定义

**Column(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Column(options?: ColumnOptions \| ColumnOptionsV2): ColumnAttribute` |
| 返回值 | `ColumnAttribute` — 创建并配置纵向容器 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | ColumnOptions/ColumnOptionsV2 | 否 | 空 options | Dynamic 构造参数；Static 更新语义归 Feat-03 |
| options.space | string/number/Resource | 否 | 0vp | 公开契约要求可转换且非负；Resource 仅 V2/API 18+ |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 创建、固定值、Resource 或非法 space | 依输入执行默认、更新、配置响应或恢复；详细组合见本节 Gherkin | AC-1.1, AC-3.1~AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录，API 10/18/26 差异按既有版本边界保留。
- **配置文件格式变更:** 否；Resource updater 复用既有资源系统。
- **数据存储格式变更:** 否；space 随 LayoutProperty 和 Pattern 生命周期存在。
- **最低支持版本:** API 7。
- **API 版本号策略:** 以 canonical SDK `@since` 为准；布局算法版本分支作为实现兼容边界记录。

| API/目标版本 | 既有行为 | 证据 | 关联 AC |
|--------------|----------|------|---------|
| API 7 | Column、number/string space | `interface/sdk-js/api/@internal/component/ets/column.d.ts:110-171` | AC-1.1, AC-3.1 |
| API 10 | Dynamic space 解析失败回退 0；自适应主轴约束分支更新 | `frameworks/bridge/declarative_frontend/jsview/js_column.cpp:44-57`; `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1196-1228` | AC-2.1, AC-3.3 |
| API 18 | V2 options 支持 Resource space | `interface/sdk-js/api/@internal/component/ets/column.d.ts:21-108,145-159` | AC-4.1 |
| API 26 | 单轴 match-parent 子项分类重测 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:28-40,1351-1363` | AC-2.5 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 共享 Flex 算法 | Column 生产链是 `LinearLayoutAlgorithm -> FlexLayoutAlgorithm` | AC-1.2, AC-2.1~AC-3.6 |
| 属性分层 | space 存入 LinearLayoutProperty，Resource updater 存在 Pattern | AC-3.1, AC-4.1 |
| Measure 脏标记 | space 属性声明及资源更新均触发 `PROPERTY_UPDATE_MEASURE` | AC-3.1, AC-4.2 |
| 弱引用生命周期 | Resource updater 不拥有 FrameNode | AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增性能指标；继续使用一次子项遍历累计尺寸 | Trace/现有 benchmark | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1287-1364,1531-1554` |
| 功耗 | 不新增后台任务或定时器 | 代码审查 | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:43-125` |
| 内存 | 每个 Resource space 仅注册一个 keyed updater，且回调持有 WeakPtr | 内存/生命周期 UT | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:57-76,100-120` |
| 安全 | 不处理敏感数据或权限 | 代码审查 | VM-1~VM-4 |
| 可靠性 | 合法 SDK 输入不得崩溃；失效节点回调安全退出 | 异常 UT/fuzz | AC-4.4 |
| 可测试性 | 每条 AC 均映射到 NG、Layout 或 Resource 测试 | 追溯审查 | VM-1~VM-4 |
| 自动化维测 | Pattern dump 输出 space、frontSpace、betweenSpace | Inspector/Dump | `frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:94-120` |
| 定界定位 | 区分 parser、Model、Property、Pattern、Algorithm 五层 | 日志/源码定位 | `05-ui-components/01-layout-components/03-column/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无 Column 专有差异 | density/fontScale 与父约束影响单位换算和尺寸 | 多密度 Layout UT | AC-2.1~AC-3.5 |
| 平板 | 无 Column 专有差异 | 大窗口只改变父约束，不改变自适应公式 | 可变窗口集成测试 | AC-2.1~AC-2.4 |
| 折叠屏 | 无 Column 专有差异 | 窗口/资源配置变化后重新 Measure | 折叠态 + Resource 更新测试 | AC-4.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Pattern 是纵向 Focus Scope，子节点保持声明顺序 | AC-1.4 |
| 大字体 | 是 | FP space 随 fontScale 转 px，子项字体改变自适应尺寸 | AC-2.1, AC-3.1 |
| 深色模式 | 否 | 本 Feat 不涉及颜色或主题光效 | N/A |
| 多窗口/分屏 | 是 | 父约束变化会重新测量自适应尺寸 | AC-2.1~AC-2.4 |
| 多用户 | 否 | 无用户级持久状态 | N/A |
| 版本升级 | 是 | API 7/10/18/26 的行为边界需要回归 | AC-2.5, AC-3.3, AC-4.1 |
| 生态兼容 | 是 | Resource 和非法值行为必须保持当前实现 | AC-3.3~AC-4.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Column 创建、尺寸与子项间距
  作为 ArkUI 应用开发者
  我想要 获得可预测的纵向容器尺寸和固定间距
  以便 跨版本组织内容

  Scenario: 按子项自适应尺寸
    Given 一个未显式设置宽高的 Column
    And 两个有效子项的尺寸分别为 40x20vp 和 60x30vp
    When Measure 完成
    Then Column 内容主轴尺寸包含两个子项高度与一个显式间距
    And 内容交叉轴尺寸以 60vp 为基础并服从父约束

  Scenario: GONE 子项不形成间距
    Given Column space 为 10vp
    And 三个子项中间一个为 GONE
    When Measure 完成
    Then 只在两个有效子项之间累计一次 10vp 间距

  Scenario: Resource 配置变化
    Given API 18+ Column 使用可解析 Resource space
    When 配置变化后资源值由 8vp 变为 12vp
    Then column.space 更新为 12vp
    And FrameNode 标记 PROPERTY_UPDATE_MEASURE
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖创建、自适应尺寸、显式 space 和 Resource 生命周期
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] 对齐/反向、多范式、PointLight 已明确路由到 Feat-02/03/04

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Column creation LinearLayoutPattern adaptive size space Resource updater"
  - repo: "openharmony/interface_sdk-js"
    query: "ColumnOptions ColumnOptionsV2 space Resource API 7 API 18"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/column.d.ts`
- 架构设计：`05-ui-components/01-layout-components/03-column/design.md`
