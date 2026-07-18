# 特性规格

> Func-05-01-08-Feat-02 RelativeContainer 依赖图、循环检测与偏置：补录合法锚点构图、拓扑缓存、缺失/GONE 锚点、循环失败行为和 bias。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RelativeContainer 依赖图、循环检测与偏置 |
| 特性编号 | Func-05-01-08-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

RelativeContainer 不能按声明顺序直接测量互相锚定的子项。算法收集容器、子项、guideline 和 barrier ID，建立 anchor→dependent 有向图，拓扑排序后按依赖顺序测量；检测到环时记录诊断、上报组件异常，并把全部子项停用后按 0x0 测量。bias 在同轴两个有效锚点之间调整显式尺寸子项的位置。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ID 与合法锚点规格 | 覆盖容器、子项、guideline、barrier、合成 ID 和缺失锚点 |
| ADDED | 依赖图与拓扑规格 | 覆盖边构建、barrier 依赖、排序和 Pattern 缓存 |
| ADDED | 循环与 GONE 锚点规格 | 覆盖循环诊断、0x0 恢复、API 12 前后的 GONE 边界 |
| ADDED | bias 规格 | 覆盖双锚点、显式尺寸、默认 0.5、0/1/负数和实现 >1 风险 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/08-relative-container/design.md` | 已补录 |
| Common SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h` | 已核对 |
| Layout algorithm | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp` | 已核对 |
| Relative layout tests | `test/unittest/core/pattern/relative_container/layout/relative_container_layout_test.cpp` | 已核对 |

> guideline/barrier 的坐标算法归 Feat-03；本 Feat 只覆盖其作为依赖图节点的作用。

## 用户故事

### US-1: 按合法锚点建立依赖图

**作为** 相对布局开发者  
**我想要** 子项按锚点依赖顺序测量  
**以便** 多级兄弟锚定得到与声明顺序无关的结果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN anchor 是容器特殊锚点或 guideline THEN 不增加普通节点入度，但对应轴可标记为依赖容器 | 正常 |
| AC-1.2 | WHEN anchor 是现存子项或 barrier THEN 为 anchor 到 dependent 建边，并增加 dependent 入度 | 正常 |
| AC-1.3 | WHEN anchor 字符串既不是容器/guideline/barrier 也不匹配子项 ID THEN 该规则不形成有效依赖边，也不访问不存在节点 | 异常 |
| AC-1.4 | WHEN 子项没有 inspector id THEN 算法生成布局期合成 ID，仍可进入图和 renderList | 边界 |
| AC-1.5 | WHEN barrier 引用多个子项或 barrier THEN 这些引用先成为 barrier 的依赖，再由 barrier 连接其 dependent | 正常 |

### US-2: 拓扑排序并复用稳定结果

**作为** 布局引擎维护者  
**我想要** 对无环依赖图生成稳定测量顺序并在规则不变时复用  
**以便** 正确处理多级锚定且避免无意义重复构图

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 节点入度为 0 THEN 进入初始队列；每输出一个节点后递减其 dependent 入度，降为 0 时入队 | 正常 |
| AC-2.2 | WHEN 所有有效节点都可输出 THEN renderList 包含完整拓扑顺序，Measure 按该顺序处理子项 | 正常 |
| AC-2.3 | WHEN 子项 alignRules 未变化且 Pattern 的拓扑缓存命中 THEN 复用缓存而不重建依赖顺序 | 正常 |
| AC-2.4 | WHEN 任一子项规则标记父容器需要重测 THEN Pattern 将 childAlignRulesChanged 置真并在本次测量重建/刷新缓存 | 边界 |

### US-3: 确定性处理循环和 GONE 锚点

**作为** 页面开发者  
**我想要** 在错误依赖关系下获得明确、可诊断的失败行为  
**以便** 定位循环而不是看到随机位置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 拓扑过程结束后仍有非零入度节点 THEN 判定存在循环，记录 loopDependentNodes 并上报 RelativeContainer loop exception | 异常 |
| AC-3.2 | WHEN 检测到循环 THEN 容器把全部子项设为 inactive，并用 selfIdealSize=0x0 执行测量，不选择任意断环 | 异常 |
| AC-3.3 | WHEN 系统 debug 开启 THEN Pattern Dump 输出 topologicalResult 和循环节点字符串 | 正常 |
| AC-3.4 | WHEN target<12 且子项锚定 GONE 兄弟 THEN dependent 被设为 inactive；target>=12 不执行该旧版本停用分支 | 边界 |
| AC-3.5 | WHEN 单个子项锚定自身 THEN 形成自环并进入与多节点循环相同的确定性失败路径 | 异常 |

### US-4: 在双锚点间应用 bias

**作为** 相对布局开发者  
**我想要** 调整显式尺寸子项在两个锚点之间的位置比例  
**以便** 形成靠前、居中或靠后的布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API>=11、同一轴找到两个有效对齐值且子项该轴有显式理想尺寸 THEN 偏移增量为 `(anchorDistance-childSize)*bias` | 正常 |
| AC-4.2 | WHEN bias 未设置 THEN horizontal/vertical 默认 0.5；0 表示靠首锚，1 表示靠尾锚 | 边界 |
| AC-4.3 | WHEN bias<0 THEN 实现使用默认 0.5；WHEN 该轴没有双锚点或没有显式理想尺寸 THEN 该轴 bias 不产生额外偏移 | 异常 |
| AC-4.4 | WHEN 子项处于对应方向 chain THEN 普通 bias offset 不重复应用，chain 自己消费 bias | 边界 |
| AC-4.5 | WHEN bias>1 THEN 当前实现仍按该值外推；该行为只登记风险，不扩大 canonical 比率语义 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | dependency graph UT | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1366-1510` |
| AC-2.1~AC-2.4 | R-6~R-9 | 已有实现 | topo/cache UT | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:149-171,1536-1621`；`frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:80-93,134-169` |
| AC-3.1~AC-3.5 | R-10~R-13 | 已有实现 | loop/GONE target UT + Dump | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:149-169,1422-1474,1536-1589` |
| AC-4.1~AC-4.5 | R-14~R-17 | 已有实现 | bias 参数化 UT | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5556-5565,5711-5722`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1789-1849` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 |anchor 为容器或 guideline |不计普通节点入度；按方向记录依赖容器状态 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1366-1374,1442-1450` | AC-1.1 |
| R-2 | 行为 |anchor 为现存 child/barrier |在 reliedOnMap 建 anchor→dependent 边 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1372-1384,1437-1474` | AC-1.2 |
| R-3 | 异常 |anchor 不属于任何合法类别 |不加入 anchorSet/普通依赖边，后续规则计算跳过 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1458-1461,1500-1508,2235-2242` | AC-1.3 |
| R-4 | 边界 |子项无 inspector id |GetOrCreateNodeInspectorId 生成合成 ID 并入 idNodeMap | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:29-47,1350-1363` | AC-1.4 |
| R-5 | 行为 |barrier 包含 referencedId |为每个引用向 barrier 建依赖，再计算 barrier 入度 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1377-1385,1512-1534` | AC-1.5 |
| R-6 | 行为 |构建无环图的初始队列 |无规则或入度 0 节点入队 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1541-1557,1591-1603` | AC-2.1 |
| R-7 | 行为 |队列输出节点 |递减 dependent 入度并将新 0 入度节点入队，输出到 renderList | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1562-1580,1604-1621` | AC-2.2 |
| R-8 | 行为 |Pattern 拓扑缓存命中且规则未变 |DetermineTopologicalOrder 直接复用已有顺序 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:149-154`；`frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:80-93` | AC-2.3 |
| R-9 | 恢复 |child FlexItem 标记 NeedMarkParentMeasure |BeforeCreateLayoutWrapper 设置 childAlignRulesChanged 并清标记 | `frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:134-169` | AC-2.4 |
| R-10 | 异常 |拓扑后 incomingDegreeMapCopy 非空 |返回循环失败、记录节点、发送 RELATIVE_CONTAINER_LOOP_ERR | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1536-1589,149-158` | AC-3.1 |
| R-11 | 恢复 |循环检测失败 |遍历全部 children，SetActive(false) 并以 0x0 约束 Measure | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:158-168` | AC-3.2, AC-3.5 |
| R-12 | 行为 |debug 开启或执行 Dump |保存/输出拓扑结果和循环节点 | `frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:95-132` | AC-3.3 |
| R-13 | 边界 |anchor child 为 GONE |target<12 停用 dependent；target>=12 跳过旧停用分支 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1458-1473` | AC-3.4 |
| R-14 | 行为 |API>=11 且双锚点+显式尺寸 |按剩余距离乘该轴 bias 形成额外 offset | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1794-1809,1812-1849` | AC-4.1 |
| R-15 | 边界 |bias 缺失、为 0 或 1 |缺失为 0.5；0/1 分别靠首/尾锚 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5556-5565,5711-5722` | AC-4.2 |
| R-16 | 异常 |bias<0、无双锚点、无显式尺寸或已在 chain |负数回退 0.5；其余条件不增加普通 bias offset | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1789-1849` | AC-4.3, AC-4.4 |
| R-17 | 异常 |bias>1 |当前 `IsValidBias` 仅检查>=0 并继续外推；只列实现风险 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1789-1809` | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | graph 构建 UT |容器、child、guide、barrier、缺失、合成 ID |
| VM-2 | R-6~R-9, AC-2.1~AC-2.4 | topo/cache UT |多级依赖、规则不变缓存、规则改变失效 |
| VM-3 | R-10~R-13, AC-3.1~AC-3.5 | loop/GONE target UT |自环/多环、inactive/0x0、Dump、API 11/12 |
| VM-4 | R-14~R-17, AC-4.1~AC-4.5 | bias 参数化 UT |无值、0、0.5、1、负数、>1、chain |

## API 变更分析

> 本次只补录 alignRules 中既有 bias 字段；依赖图和循环处理是实现行为。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `AlignRuleOption.bias` | Public | horizontal/vertical 比率 | N/A | N/A | API 11 调整双锚点间位置 | AC-4.1~AC-4.5 |
| `LocalizedAlignRuleOptions.bias` | Public | horizontal/vertical 比率 | N/A | N/A | API 12 localized 规则偏置 | AC-4.1~AC-4.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| GONE anchor target 行为 | 变更 |target 从 API 11 升至 12 |不要依赖旧版自动停用 dependent；显式控制 visibility/规则 | AC-3.4 |

## 接口规格

### 接口定义

**alignRules(...bias)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `alignRules(value: AlignRuleOption \| LocalizedAlignRuleOptions): T` |
| 返回值 |当前组件类型 T |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| anchor | string |每条规则必填 |无 |须解析为合法容器/child/guide/barrier 才生效 |
| bias.horizontal | number |否 |0.5 |双水平锚点且有显式宽度时生效 |
| bias.vertical | number |否 |0.5 |双垂直锚点且有显式高度时生效 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 |无环多级 anchor |拓扑顺序测量，结果与声明顺序无关 | AC-1.1~AC-2.2 |
| 2 |规则缓存命中/失效 |复用或重建 renderList | AC-2.3, AC-2.4 |
| 3 |自环/多节点环 |诊断、inactive、0x0 | AC-3.1~AC-3.5 |
| 4 |双锚点 bias |按比率偏移或按异常条件降级 | AC-4.1~AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 是；target API 12 改变 GONE anchor 的 dependent 停用分支。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 基础依赖图随 API 9；bias 自 API 11。
- **API 版本号策略:** bias 以 API 11/12 标注；循环为实现恢复契约，无独立 API。

| 版本 | 既有行为 | 证据 |
|------|----------|------|
| API 9 |基础 AlignRuleOption 与依赖求解 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5458-5565` |
| API 11 |bias 与 NG 新版 margin/依赖行为 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5556-5565` |
| API 12 |localized bias；不再走 target<12 的 GONE dependent 停用分支 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1458-1473` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
|图节点合法性 |只有存在的 child/barrier 形成普通入度，容器/guide 为根类锚点 | AC-1.1~AC-1.3 |
|拓扑前置 |任何子项测量不得绕过依赖顺序 | AC-2.1, AC-2.2 |
|确定性失败 |循环不得由实现任意断边 | AC-3.1, AC-3.2 |
|bias 条件 |必须有双锚点和显式理想尺寸，chain 自行消费 bias | AC-4.1, AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |构图/拓扑随节点和依赖边线性增长；规则不变复用缓存 |Trace/benchmark | `frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:80-93` |
| 功耗 |无后台任务；仅布局周期执行 |代码审查 | VM-1~VM-4 |
| 内存 |依赖 map/renderList 随单次算法；Pattern 只缓存一份列表/诊断 |内存基线 | `frameworks/core/components_ng/pattern/relative_container/relative_container_pattern.h:172-178` |
| 安全 |不涉及权限或敏感数据 |API 审查 | VM-1 |
| 可靠性 |循环、缺失 anchor、GONE 均有确定处理且不崩溃 |异常 UT/fuzz | AC-1.3, AC-3.1~AC-3.5 |
| 可测试性 |图结构、active、size、Dump 均可直接断言 |NG UT | VM-1~VM-4 |
| 自动化维测 |Dump 暴露 topologicalResult/loopDependentNodes |Dump 测试 | AC-3.3 |
| 定界定位 |区分构图、预检、排序、测量、bias 五段 |设计审查 | `05-ui-components/01-layout-components/08-relative-container/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 |无图算法差异 |anchor 距离较小但拓扑不变 |手机约束 UT | AC-2.2, AC-4.1 |
| 平板 |无图算法差异 |anchor 距离增大时 bias 位移相应增大 |平板约束 UT | AC-4.1 |
| 折叠屏 |尺寸变化不应改变无尺寸依赖的拓扑顺序 |重测可复用/刷新缓存，offset 重新计算 |折叠集成测试 | AC-2.3, AC-2.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 |inactive 循环子项不可形成有效布局，需验证语义树同步 | AC-3.2 |
| 大字体 | 是 |显式/内容尺寸变化会改变 bias 剩余距离，不改变图边 | AC-4.1 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |尺寸变化重算 offset，规则不变时可复用拓扑 | AC-2.3 |
| 多用户 | 否 |无用户状态 |
| 版本升级 | 是 |target 12 GONE anchor 分支需回归 | AC-3.4 |
| 生态兼容 | 是 |循环失败和缺失 anchor 处理必须确定 | AC-1.3, AC-3.1~AC-3.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RelativeContainer 依赖图、循环检测与偏置
  Scenario: 两节点互相锚定
    Given childA 锚定 childB
    And childB 锚定 childA
    When RelativeContainer 执行拓扑预检
    Then检测到循环并记录 childA、childB
    And两个子项均 inactive 且测量为 0x0

  Scenario Outline: bias 决定双锚点间位置
    Given两个水平锚点距离为 200vp
    And子项显式宽度为 40vp
    When horizontal bias 为 <bias>
    Then额外水平 offset 为 <offset>

    Examples:
      | bias | offset |
      | 0 | 0vp |
      | 0.5 | 80vp |
      | 1 | 160vp |
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x]依赖图与具体 anchor 坐标算法边界清晰
- [x]循环恢复、GONE 版本、bias 条件均明确
- [x]每个 AC 与规则、VM 双向追溯
- [x]bias >1 仅列风险，未扩大 canonical 语义

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RelativeContainer dependency topological loop cache GONE anchor bias"
  - repo: "openharmony/interface_sdk-js"
    query: "AlignRuleOption bias LocalizedAlignRuleOptions API 11 API 12"
```

**关键文档：**

- Common SDK：`interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 共享设计：`05-ui-components/01-layout-components/08-relative-container/design.md`
