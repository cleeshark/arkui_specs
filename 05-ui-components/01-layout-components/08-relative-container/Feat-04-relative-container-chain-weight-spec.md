# 特性规格

> Func-05-01-08-Feat-04 RelativeContainer 链式布局与权重：补录 chainMode 成链条件、SPREAD/SPREAD_INSIDE/PACKED、GONE、bias 和 API 14 chainWeight。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RelativeContainer 链式布局与权重 |
| 特性编号 | Func-05-01-08-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 12–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

RelativeContainer 的子项可通过互相匹配的 alignRules 形成水平或垂直链，并由链头的 `chainMode(Axis, ChainStyle)` 选择分布方式。API 14 的 `chainWeight` 可让链中正权重项忽略固有尺寸、按权重占用剩余空间。SDK 声明见 `interface/sdk-js/api/@internal/component/ets/common.d.ts:5725-5767,19894-19915,23162-23177` 和 `interface/sdk-js/api/@internal/component/ets/units.d.ts:3531-3565`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 水平/垂直成链规格 | 覆盖链头、双向相邻规则、合法端点、至少两项和容器依赖 |
| ADDED | ChainStyle 分布规格 | 覆盖 SPREAD、SPREAD_INSIDE、PACKED、内容溢出和 bias |
| ADDED | GONE 与定位规格 | 覆盖有效项计数、尺寸累计和 offset 记录 |
| ADDED | chainWeight 规格 | 覆盖水平/垂直权重、剩余空间、非正值、二次测量和 API 23 modifier |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/08-relative-container/design.md` | 已补录 |
| Common SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Units SDK | `interface/sdk-js/api/@internal/component/ets/units.d.ts` | 已核对 |
| Flex item property | `frameworks/core/components_ng/property/flex_property.h`、`frameworks/core/components_ng/layout/layout_property.cpp` | 已核对 |
| Relative algorithm | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp` | 已核对 |

## 用户故事

### US-1: 形成水平或垂直链

**作为** 相对布局开发者  
**我想要** 把连续子项通过互相锚定组成一条链  
**以便** 由容器统一分配端点之间的空间

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 链头设置 horizontal chainMode 且同时具有合法 left/right 规则 THEN 算法沿 right anchor 查找后继 | 正常 |
| AC-1.2 | WHEN 当前节点 right 对齐后继 START，且后继 left 反向锚定当前节点 END THEN 后继加入水平链；垂直链使用 bottom→TOP 与后继 top→BOTTOM 对应关系 | 正常 |
| AC-1.3 | WHEN 最终尾锚合法且链节点数>1 THEN 登记链端点、节点顺序、style、bias 和权重；否则 chainMode 不形成有效链 | 边界 |
| AC-1.4 | WHEN 链任一端锚定 RelativeContainer THEN 对应轴标记为依赖容器，影响容器 auto 自适应 | 边界 |
| AC-1.5 | WHEN 同一节点同时拥有水平和垂直 chainMode THEN 分别进入两套 chain map，两个轴独立求解 | 正常 |

### US-2: 使用三种 ChainStyle 分配空间

**作为** 页面设计者  
**我想要** 选择均匀外间距、均匀内间距或紧凑排列  
**以便** 用锚点端点控制一组子项

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN anchorDistance>=contentSize 且 style=SPREAD、有效项数 n THEN `gap=(distance-content)/(n+1)`，链首前和链尾后各保留一个 gap | 正常 |
| AC-2.2 | WHEN distance>=content 且 style=SPREAD_INSIDE、n>1 THEN `gap=(distance-content)/(n-1)`，首尾贴端点 | 正常 |
| AC-2.3 | WHEN distance>=content 且 style=PACKED THEN gap=0，整体起点为 `head+(distance-content)*bias` | 正常 |
| AC-2.4 | WHEN contentSize>anchorDistance THEN SPREAD/SPREAD_INSIDE 以超出量的一半向前偏移，PACKED 按 bias 决定溢出起点 | 边界 |
| AC-2.5 | WHEN PACKED bias 缺失 THEN 使用 0.5；0/1 分别把整体靠首/尾端点 | 边界 |

### US-3: 忽略 GONE 链项

**作为** 构建条件内容的开发者  
**我想要** 隐藏链中某项时自动重排其余项  
**以便** 不留下由 GONE 节点造成的空槽

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 链节点 visibility=GONE THEN 该节点不计入有效 itemCount 和 contentSize | 正常 |
| AC-3.2 | WHEN 记录链 offset THEN 跳过 GONE 节点，不为其推进 offset；后续可见节点紧接前一有效项和 gap | 正常 |
| AC-3.3 | WHEN 全部链项均 GONE THEN 算法不应除以负数或访问缺失 itemSize，布局保持安全 | 异常 |

### US-4: 按 chainWeight 分配剩余尺寸

**作为** 响应式布局开发者  
**我想要** 为链项设置水平或垂直权重  
**以便** 固定项保留固有尺寸，加权项按比例填满剩余空间

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API>=14 且链项某轴 chainWeight>0 THEN 该项进入该轴权重模式，其固有尺寸不从剩余空间预扣 | 正常 |
| AC-4.2 | WHEN 同轴存在固定项和正权重项 THEN 先从端点距离扣除固定可见项尺寸，再按 `remaining*itemWeight/totalWeight` 设置加权项理想尺寸 | 正常 |
| AC-4.3 | WHEN remainingSpace<=0 THEN 加权项该轴理想尺寸设为 0，不产生负尺寸 | 边界 |
| AC-4.4 | WHEN 某轴权重缺失、等于 0 或小于 0 THEN 该轴不作为正权重项，保留普通测量尺寸 | 异常 |
| AC-4.5 | WHEN 加权项得到新理想尺寸 THEN 算法二次 Measure 并更新 chain itemSize，再重新计算 offset | 正常 |
| AC-4.6 | WHEN API>=23 通过 attributeModifier 动态设置 chainWeight THEN 触发 LayoutProperty `PROPERTY_UPDATE_MEASURE` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | horizontal/vertical chain formation UT | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:410-623` |
| AC-2.1~AC-2.5 | R-6~R-9 | 已有实现 | ChainStyle 数值 UT | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:768-879` |
| AC-3.1~AC-3.3 | R-10~R-11 | 已有实现 | visibility chain UT | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:807-863` |
| AC-4.1~AC-4.6 | R-12~R-16 | 已有实现 | weight/remeasure/API level UT | `interface/sdk-js/api/@internal/component/ets/common.d.ts:19894-19915`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:625-645,1144-1254` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 |链头有 Horizontal chain style 和左右规则 |从 right anchor 开始检查后继 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:454-486` | AC-1.1 |
| R-2 | 行为 |相邻节点水平/垂直规则双向匹配 |后继加入对应 chainNodes 并继续遍历 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:410-451,505-546` | AC-1.2 |
| R-3 | 边界 |尾锚合法且 chainNodes.size>1 |创建 ChainParam；不满足时退出不登记链 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:487-503,581-598` | AC-1.3 |
| R-4 | 边界 |链头或尾 anchor 为容器 |设置对应 axis relyOnContainer | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:487-490,582-585` | AC-1.4 |
| R-5 | 行为 |节点同时有水平/垂直 chain style |CheckChain 分别调用两个检查器 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:600-623` | AC-1.5 |
| R-6 | 行为 |distance>=content 且 SPREAD |gap=(distance-content)/(n+1)，start=gap | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:768-779` | AC-2.1 |
| R-7 | 行为 |distance>=content 且 SPREAD_INSIDE |n>1 时 gap=(distance-content)/(n-1)，start=0 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:780-783` | AC-2.2 |
| R-8 | 行为 |PACKED |gap=0，start=(distance-content)*bias | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:784-787,797-799` | AC-2.3, AC-2.5 |
| R-9 | 边界 |content>distance |SPREAD/INSIDE start 为差值一半；PACKED 按 bias | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:791-803` | AC-2.4 |
| R-10 | 行为 |链项为 GONE |itemCount 减 1，不累计 contentSize | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:838-863` | AC-3.1, AC-3.3 |
| R-11 | 行为 |记录 chain offset 遇到 GONE |跳过该节点，不写 offset/推进距离 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:807-835` | AC-3.2 |
| R-12 | 行为 |chainWeight 某轴>0 |标记 weight mode，固定项尺寸从 remainingSpace 扣除 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:437-445,625-645` | AC-4.1 |
| R-13 | 行为 |remaining>0 且有正权重项 |理想尺寸=remaining*directionWeight/totalWeight | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1200-1254` | AC-4.2 |
| R-14 | 边界 |remaining<=0 |对应轴 selfIdealSize=0 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1240-1254` | AC-4.3 |
| R-15 | 异常 |weight 缺失或<=0 |HasWeight 返回 false，按固定项记录固有尺寸 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:625-645,1218-1227` | AC-4.4 |
| R-16 | 行为 |权重尺寸算出 |二次 Measure，更新 itemSize 后重新 CalcOffsetParam；属性更新标记 Measure | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1144-1197`；`frameworks/core/components_ng/layout/layout_property.cpp:1433-1440` | AC-4.5, AC-4.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | Chain formation UT |水平/垂直、规则断链、非法尾锚、单节点、双轴 |
| VM-2 | R-6~R-9, AC-2.1~AC-2.5 |数值公式 UT |三种 style、n=1/2/3、distance 等于/小于 content、bias |
| VM-3 | R-10~R-11, AC-3.1~AC-3.3 | GONE UT |中间项、首尾项、全部 GONE |
| VM-4 | R-12~R-16, AC-4.1~AC-4.6 | Weight UT/SDK compile |固定+权重、0/负数、remaining<=0、双轴、API 14/23 |

## API 变更分析

> 本次只补录已有 Common API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `chainMode(direction, style)` | Public | Axis、ChainStyle |当前组件类型 | N/A | API 12 在链头设置方向和分布 | AC-1.1~AC-2.5 |
| `ChainStyle` | Public | SPREAD/SPREAD_INSIDE/PACKED | N/A | N/A | API 12 三种链分布 | AC-2.1~AC-2.5 |
| `chainWeight(options)` | Public | horizontal/vertical number |当前组件类型 | N/A | API 14 按权重分配尺寸 | AC-4.1~AC-4.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `chainWeight` attributeModifier | 变更 |运行时动态 modifier 设置 |API 23 起可动态配置；低版本在声明阶段设置 | AC-4.6 |

## 接口规格

### 接口定义

**chainMode(direction, style)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `chainMode(direction: Axis, style: ChainStyle): T` |
| 返回值 |当前组件类型 T |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| direction | Axis |是 |无 |Horizontal/Vertical，需与成链规则轴一致 |
| style | ChainStyle |是 |无 |SPREAD/SPREAD_INSIDE/PACKED |

**chainWeight(options)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `chainWeight(chainWeight: ChainWeightOptions): T` |
| 返回值 |当前组件类型 T |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| horizontal | number |否 |无正权重 |仅在水平链中 >0 时分配宽度 |
| vertical | number |否 |无正权重 |仅在垂直链中 >0 时分配高度 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 |互相匹配/断裂的 alignRules |形成链或按普通规则布局 | AC-1.1~AC-1.5 |
| 2 |三种 style 与不同余量 |按公式计算 gap/start | AC-2.1~AC-2.5 |
| 3 |固定项+正权重项 |扣固定尺寸、按权重重测并定位 | AC-4.1~AC-4.6 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 14 增加 chainWeight，API 23 增加其 attributeModifier 动态配置。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** chainMode/ChainStyle 为 API 12；chainWeight 为 API 14。
- **API 版本号策略:** 以 Common/Units canonical `@since` 为准。

| 版本 | 能力 | 证据 |
|------|------|------|
| API 12 |chainMode、ChainStyle | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5725-5767,23162-23177` |
| API 14 |ChainWeightOptions、chainWeight | `interface/sdk-js/api/@internal/component/ets/units.d.ts:3531-3565`；`interface/sdk-js/api/@internal/component/ets/common.d.ts:19894-19915` |
| API 23 |chainWeight 支持 attributeModifier；Static ChainWeightOptions | `interface/sdk-js/api/@internal/component/ets/common.d.ts:19899-19915`；`interface/sdk-js/api/arkui/component/units.static.d.ets:1599-1628` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
|双向成链 |chainMode 本身不足以成链，必须有匹配的相邻 alignRules | AC-1.1~AC-1.3 |
|轴隔离 |水平/垂直 chain map、style、weight 独立 | AC-1.5, AC-4.1 |
|可见项语义 |GONE 不参与计数、内容尺寸或 offset 推进 | AC-3.1~AC-3.3 |
|权重二次测量 |权重改变理想尺寸后必须重测并更新 chain itemSize | AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |每条链线性识别/定位；仅有正权重时执行额外测量 |Trace/benchmark | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:600-623,1144-1197` |
| 功耗 |无后台任务 |代码审查 | VM-1~VM-4 |
| 内存 |每条链保存节点 ID、itemSize、端点和少量标量 |内存基线 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.h:60-74` |
| 安全 |不涉及权限/敏感数据 |API 审查 | VM-4 |
| 可靠性 |断链、全部 GONE、remaining<=0 均有安全路径 |异常 UT/fuzz | AC-1.3, AC-3.3, AC-4.3 |
| 可测试性 |style/weight 均有闭式公式可断言 |数值 UT | VM-2, VM-4 |
| 自动化维测 |可通过 child frame size/offset 观察链结果 |Inspector/Layout | VM-1~VM-4 |
| 定界定位 |区分成链、普通测量、权重重测和 chain offset |设计审查 | `05-ui-components/01-layout-components/08-relative-container/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 |无算法差异 |较短 anchorDistance 可能进入 content>distance 分支 |手机约束 UT | AC-2.4 |
| 平板 |无算法差异 |较长距离增加 gap 或加权剩余空间 |平板约束 UT | AC-2.1~AC-2.3, AC-4.2 |
| 折叠屏 |尺寸变化重算链余量 |成链关系不变，gap/weight size 重新计算 |折叠集成测试 | AC-2.1~AC-4.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 |链改变视觉位置但不重排声明树，GONE 仍需保持语义一致 | AC-3.1, AC-3.2 |
| 大字体 | 是 |固有尺寸变化会改变 contentSize/remainingSpace | AC-2.1, AC-4.2 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |anchorDistance 变化后重算 gap/weight | AC-2.1~AC-4.5 |
| 多用户 | 否 |无用户状态 |
| 版本升级 | 是 |API 12/14/23 可见性需回归 | AC-1.1, AC-4.1, AC-4.6 |
| 生态兼容 | 是 |双向成链和三种闭式公式必须保留 | AC-1.2, AC-2.1~AC-2.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RelativeContainer 链式布局与权重
  Scenario Outline: 三种 ChainStyle 分配 100vp 余量
    Given三个可见链项内容总尺寸为 200vp
    And两端锚点距离为 300vp
    When ChainStyle 为 <style>
    Then首项起始余量为 <start>
    And相邻 gap 为 <gap>

    Examples:
      | style | start | gap |
      | SPREAD | 25vp | 25vp |
      | SPREAD_INSIDE | 0vp | 50vp |
      | PACKED | 50vp | 0vp |

  Scenario: 固定项与权重项共享空间
    Given端点距离为 300vp
    And固定项宽度为 60vp
    And两个权重项水平权重为 1 和 2
    When权重测量完成
    Then两个权重项宽度分别为 80vp 和 160vp
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x]成链、分布、GONE、权重边界清晰
- [x] API 12/14/23 版本边界明确
- [x]每个 AC 与规则、VM 双向追溯
- [x]包含 n=1、溢出、全部 GONE、非正权重和负剩余边界

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RelativeContainer chain SPREAD SPREAD_INSIDE PACKED chainWeight"
  - repo: "openharmony/interface_sdk-js"
    query: "chainMode ChainStyle ChainWeightOptions chainWeight API 12 14 23"
```

**关键文档：**

- Common SDK：`interface/sdk-js/api/@internal/component/ets/common.d.ts`
- Units SDK：`interface/sdk-js/api/@internal/component/ets/units.d.ts`
- 共享设计：`05-ui-components/01-layout-components/08-relative-container/design.md`
