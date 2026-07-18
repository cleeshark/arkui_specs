# 特性规格

> Func-05-01-08-Feat-01 RelativeContainer 锚定与自适应尺寸：补录创建、alignRules、容器/兄弟锚点、默认 100%、API 11 auto、API 20 LayoutPolicy 和 margin 语义。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RelativeContainer 锚定与自适应尺寸 |
| 特性编号 | Func-05-01-08-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

RelativeContainer 是支持多个子组件的相对布局容器。子组件使用 Common `alignRules` 把自身 left/right/middle/top/bottom/center 对齐到容器或兄弟锚点；未设置宽高时容器默认占满父约束，API 11 起 `auto` 可按不依赖容器的子项包围盒自适应，API 20 起同时支持 LayoutPolicy。公开说明见 `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:424-465`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | RelativeContainer 创建规格 | 覆盖节点、Pattern、Property、Algorithm、多个子项和默认尺寸 |
| ADDED | 基础 alignRules 规格 | 覆盖容器/兄弟锚点、六个方向、水平/垂直计算 |
| ADDED | 自适应尺寸规格 | 覆盖 API 11 auto、空容器、容器依赖抑制、API 20 LayoutPolicy |
| ADDED | margin/position 交互规格 | 覆盖 API 11 锚点距离和 alignRules 覆盖显式 position |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/08-relative-container/design.md` | 已补录 |
| Relative SDK | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts` | 已核对 |
| Common SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Model/Property/Pattern | `frameworks/core/components_ng/pattern/relative_container/relative_container_model_ng.cpp`、`relative_container_layout_property.h`、`relative_container_pattern.h` | 已核对 |
| Layout algorithm | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp` | 已核对 |

> 依赖循环与 bias 归 Feat-02，guideline/barrier 归 Feat-03，chain 归 Feat-04。

## 用户故事

### US-1: 创建多子项相对容器

**作为** ArkUI 页面开发者  
**我想要** 创建可容纳多个子组件的 RelativeContainer  
**以便** 用锚点关系描述复杂布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `RelativeContainer()` THEN 创建 RELATIVE_CONTAINER FrameNode、RelativeContainerPattern、RelativeContainerLayoutProperty 和专用 LayoutAlgorithm | 正常 |
| AC-1.2 | WHEN 未显式设置 width/height THEN 容器在两个轴使用父约束允许的 100% 尺寸，而不是默认包裹子项 | 正常 |
| AC-1.3 | WHEN 容器没有子项 THEN 按解析后的自身理想尺寸结束测量，不进入依赖图或子项测量 | 边界 |
| AC-1.4 | WHEN 容器包含多个子项 THEN 为无 inspector id 的子项生成本次布局可用的合成 ID，参与独立测量和定位 | 边界 |

### US-2: 用 alignRules 锚定容器或兄弟

**作为** 相对布局开发者  
**我想要** 把子项不同边或中心对齐到合法锚点  
**以便** 不依赖声明顺序地建立位置关系

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 子项设置 left/right/middle 水平规则 THEN 按 anchor 的 HorizontalAlign 计算 x；WHEN 设置 top/bottom/center THEN 按 VerticalAlign 计算 y | 正常 |
| AC-2.2 | WHEN anchor 是特殊容器锚点 THEN 使用 RelativeContainer 去除 padding/border 后的内容区作为 anchor rect | 正常 |
| AC-2.3 | WHEN anchor 是已测量兄弟 THEN 使用兄弟的 frame size 和已记录 offset；API 11+ 另计相关 margin 距离 | 正常 |
| AC-2.4 | WHEN 同一轴只配置一个合法规则 THEN 该规则决定位置而不强制改变子项自身尺寸 | 边界 |
| AC-2.5 | WHEN 同一轴两侧均配置且子项没有显式理想尺寸 THEN 算法可由两锚点间距推导该轴理想尺寸 | 正常 |

### US-3: 按内容自适应容器尺寸

**作为** 组件开发者  
**我想要** RelativeContainer 在 auto/wrapContent 场景按有效子项自适应  
**以便** 构建可复用的包裹内容组件

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API>=11 且 width/height 为 auto、该轴没有子项直接或间接依赖容器 THEN 以有效子项边界扩展该轴尺寸并服从约束 | 正常 |
| AC-3.2 | WHEN 某轴存在子项直接或间接以容器为 anchor THEN 该轴 auto 不由这些依赖项推动，效果等同该轴未设置 auto | 边界 |
| AC-3.3 | WHEN API>=20 使用 LayoutPolicy.wrapContent THEN 按内容理想尺寸自适应但受祖先约束；WHEN 使用 fixAtIdealSize THEN 按理想内容尺寸且不受祖先尺寸限制 | 正常 |
| AC-3.4 | WHEN API>=20 的 wrap/fix 轴存在对容器的直接或间接锚定 THEN 该轴不按该依赖子项自适应 | 边界 |
| AC-3.5 | WHEN 容器为空且自身尺寸为 auto/wrap 类策略 THEN 返回由约束解析的空内容尺寸，不访问不存在子项 | 边界 |

### US-4: 解释 margin 与 position

**作为** 相对布局开发者  
**我想要** 明确 margin 和显式 position 与 alignRules 的优先级  
**以便** 避免重复定位产生歧义

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API>=11 且某方向存在 anchor THEN 该方向 margin 表示与锚点之间的距离并进入 offset 计算 | 正常 |
| AC-4.2 | WHEN 某方向没有 anchor THEN 该方向 margin 不产生相对锚点位移 | 边界 |
| AC-4.3 | WHEN 子项具有有效 alignRules THEN 布局属性关闭显式 position 的使用，由相对锚定结果决定位置 | 边界 |
| AC-4.4 | WHEN RTL 布局读取兄弟水平 margin THEN 使用与文本方向相符的 origin margin 侧 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | NG Create/empty/multi-child UT | `frameworks/core/components_ng/pattern/relative_container/relative_container_model_ng.cpp:23-32`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:29-47,173-195` |
| AC-2.1~AC-2.5 | R-5~R-8 | 已有实现 | anchor matrix Layout UT | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5458-5565`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1750-1787,2031-2232` |
| AC-3.1~AC-3.5 | R-9~R-12 | 已有实现 | API 10/11/20 auto/LayoutPolicy UT | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:431-447`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:912-1031,1257-1313` |
| AC-4.1~AC-4.4 | R-13~R-15 | 已有实现 | margin/position/RTL UT | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:449-452`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:962-1074,2061-2232` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 |调用 RelativeContainer 创建入口 |创建容器节点及专用 Pattern/Property/Algorithm | `frameworks/core/components_ng/pattern/relative_container/relative_container_model_ng.cpp:23-32`；`frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:29-62` | AC-1.1 |
| R-2 | 行为 |宽高均未设置 |使用父约束下 100% 默认尺寸 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:431-433` | AC-1.2 |
| R-3 | 边界 |子列表为空 |UpdateSizeWhenChildrenEmpty 写自身尺寸并返回 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:173-195,892-897` | AC-1.3 |
| R-4 | 边界 |子项没有 inspector id |Initialize 为该节点生成合成 ID 并加入 idNodeMap | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:29-47,100-147` | AC-1.4 |
| R-5 | 行为 |配置水平/垂直 AlignRuleOption |分别用 anchor rect、align enum 和子项尺寸计算 x/y | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5458-5565`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:2031-2232` | AC-2.1 |
| R-6 | 行为 |anchor 为容器 |anchor size 使用容器内容宽高，offset 原点为内容区 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:2056-2122,2183-2205` | AC-2.2 |
| R-7 | 行为 |anchor 为合法兄弟 |使用兄弟已记录 offset 和 frame size；API 11+ 计入 margin | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:2068-2122,2183-2232` | AC-2.3 |
| R-8 | 边界 |同轴一个/两个合法锚点 |单锚点只定位；双锚点可在无理想尺寸时推导尺寸 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1033-1074,1750-1787` | AC-2.4, AC-2.5 |
| R-9 | 行为 |API>=11 且 auto 轴无容器依赖 |根据子项边界更新容器该轴尺寸并施加约束 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:912-1031,1257-1313` | AC-3.1 |
| R-10 | 边界 |auto 轴存在直接/间接容器依赖 |标记该轴 relyOnContainer，不由依赖项推动自适应 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:434-437`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1257-1313` | AC-3.2 |
| R-11 | 行为 |API>=20 且使用 wrapContent/fixAtIdealSize |分别使用受祖先约束/不受祖先约束的理想内容尺寸路径 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:439-447`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:912-1031` | AC-3.3, AC-3.4 |
| R-12 | 边界 |空容器处于自适应策略 |按空内容和自身约束安全返回 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:173-195` | AC-3.5 |
| R-13 | 行为 |API>=11 且对应方向有兄弟 anchor |margin 加入 anchor offset；RTL 选择相应 origin margin | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:2061-2105,2206-2232` | AC-4.1, AC-4.4 |
| R-14 | 边界 |对应方向无 anchor |margin 不作为该方向相对锚点距离 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:449-452` | AC-4.2 |
| R-15 | 边界 |子项有 alignRules |SetUsingPosition(false)，相对规则优先于显式 position | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:962-987,1033-1074` | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | NG Create/Measure UT |默认 100%、空容器、多子项、合成 ID |
| VM-2 | R-5~R-8, AC-2.1~AC-2.5 | anchor 组合 UT |六方向、容器/兄弟、单/双锚点、理想尺寸 |
| VM-3 | R-9~R-12, AC-3.1~AC-3.5 | API 10/11/19/20 Layout UT |auto、容器依赖、wrapContent、fixAtIdealSize |
| VM-4 | R-13~R-15, AC-4.1~AC-4.4 | margin/position/RTL UT |有/无 anchor、LTR/RTL、position 被关闭 |

## API 变更分析

> 本次只补录已有 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `RelativeContainer()` | Public |无 | RelativeContainerAttribute | N/A | API 9 创建多子项相对容器 | AC-1.1~AC-1.4 |
| `alignRules(value: AlignRuleOption)` | Public |六方向 anchor/align、bias |当前组件类型 | N/A | API 9 设置子项相对规则 | AC-2.1~AC-4.4 |
| localized `alignRules` overload | Public |start/end/middle/top/bottom/center |当前组件类型 | N/A | API 12 支持 RTL 逻辑方向 | AC-4.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| RelativeContainer auto sizing | 变更 |API 11+ 设置 width/height=auto |按是否锚定容器判断能否自适应 | AC-3.1, AC-3.2 |
| RelativeContainer LayoutPolicy sizing | 变更 |API 20+ 使用 wrapContent/fixAtIdealSize |按祖先约束需求选择 policy | AC-3.3, AC-3.4 |

## 接口规格

### 接口定义

**RelativeContainer()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RelativeContainer(): RelativeContainerAttribute` |
| 返回值 | RelativeContainerAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| 无 | N/A | N/A |宽高 100% |支持多个子组件 |

**alignRules(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `alignRules(value: AlignRuleOption \| LocalizedAlignRuleOptions): T` |
| 返回值 |当前组件类型 T |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| anchor | string |每条规则必填 |无 |容器、合法兄弟、guideline 或 barrier ID |
| align | HorizontalAlign/VerticalAlign |每条规则必填 |无 |须与规则方向匹配 |
| bias | Bias |否 |horizontal/vertical 均 0.5 |详细偏置归 Feat-02 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 |容器/兄弟单边或双边锚定 |计算位置，必要时推导尺寸 | AC-2.1~AC-2.5 |
| 2 |auto/LayoutPolicy 与容器依赖组合 |自适应或抑制该轴自适应 | AC-3.1~AC-3.5 |
| 3 |alignRules 与 margin/position 组合 |margin 作为锚距，position 不生效 | AC-4.1~AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 11 增加 auto 自适应与 margin 锚距，API 20 增加 LayoutPolicy 行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** RelativeContainer/alignRules 为 API 9。
- **API 版本号策略:** API 9 基础、API 11 bias/自适应运行行为、API 12 localized overload、API 20 LayoutPolicy。

| 版本 | 行为 | 证据 |
|------|------|------|
| API 9 |RelativeContainer 和 AlignRuleOption | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:21-43`；`interface/sdk-js/api/@internal/component/ets/common.d.ts:5458-5565` |
| API 11 |auto 自适应、margin 锚距、bias 字段 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:434-452`；`interface/sdk-js/api/@internal/component/ets/common.d.ts:5556-5565` |
| API 12 |localized alignRules | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5567-5723,23143-23160` |
| API 20 |LayoutPolicy 自适应 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:439-447` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
|属性所有权 |alignRules 在子项 FlexItemProperty，容器算法统一消费 | AC-2.1~AC-2.5 |
|内容区锚点 |容器锚点使用去除 padding/border 的内容区 | AC-2.2 |
|依赖感知自适应 |auto/LayoutPolicy 不能由该轴依赖容器的子项推动 | AC-3.2, AC-3.4 |
|定位优先级 |alignRules 优先于显式 position | AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |不新增指标；普通锚定按拓扑顺序一次测量 |Trace/现有 benchmark | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:882-910` |
| 功耗 |无后台任务或定时器 |代码审查 | VM-1~VM-4 |
| 内存 |每个子项保存有限 align rules；布局图为临时状态 |内存基线 | `frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:172-178` |
| 安全 |无权限或敏感数据 |API 审查 | VM-1 |
| 可靠性 |空容器、无 inspector id、缺尺寸均安全处理 |边界 UT/fuzz | AC-1.3, AC-1.4, AC-3.5 |
| 可测试性 |固定 anchor rect/child size 可精确断言 offset |Layout UT | VM-2~VM-4 |
| 自动化维测 |Pattern Dump 输出拓扑和循环信息 |Dump | `frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:95-132` |
| 定界定位 |区分 container Property、child FlexItem、algorithm |设计审查 | `05-ui-components/01-layout-components/08-relative-container/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 |无专有算法差异 |较窄父约束影响默认 100% 和 wrapContent 上限 |手机约束 UT | AC-1.2, AC-3.3 |
| 平板 |无专有算法差异 |较宽内容区改变容器锚点 rect |平板约束 UT | AC-2.2 |
| 折叠屏 |父约束可动态变化 |重新 Measure 后重算自适应尺寸和锚点 |折叠/展开集成测试 | AC-3.1~AC-3.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 |视觉锚定不重排声明树；需回归焦点顺序 | AC-2.1 |
| 大字体 | 是 |内容理想尺寸变化可推动 auto/wrapContent | AC-3.1, AC-3.3 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |父约束改变默认/自适应尺寸并重算 anchor | AC-1.2, AC-3.1 |
| 多用户 | 否 |无用户状态 |
| 版本升级 | 是 |API 11/20 自适应语义需回归 | AC-3.1~AC-3.4 |
| 生态兼容 | 是 |margin/position 优先级和默认 100% 必须保留 | AC-1.2, AC-4.1~AC-4.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RelativeContainer 锚定与自适应尺寸
  Scenario: auto 轴没有容器依赖
    Given API 11+ RelativeContainer width 为 auto
    And 子项只锚定另一个固定尺寸兄弟
    When 完成测量
    Then容器宽度包围有效子项
    And结果服从父 min/max 约束

  Scenario: auto 轴依赖容器
    Given API 11+ RelativeContainer width 为 auto
    And 子项 right 锚定 RelativeContainer 右边
    When 完成依赖分析
    Then该子项不推动容器宽度自适应
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x]锚定/自适应与依赖循环/扩展锚点/链职责分离
- [x] API 9/11/12/20 版本边界明确
- [x]每个 AC 与规则、VM 双向追溯
- [x]包含空容器、容器依赖、margin 和 position 边界

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RelativeContainer alignRules auto size LayoutPolicy margin SetUsingPosition"
  - repo: "openharmony/interface_sdk-js"
    query: "RelativeContainer AlignRuleOption LocalizedAlignRuleOptions API 9 11 12 20"
```

**关键文档：**

- Relative SDK：`interface/sdk-js/api/@internal/component/ets/relative_container.d.ts`
- Common SDK：`interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 共享设计：`05-ui-components/01-layout-components/08-relative-container/design.md`
