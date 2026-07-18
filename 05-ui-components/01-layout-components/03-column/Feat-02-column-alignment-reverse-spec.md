# 特性规格

> Func-05-01-03-Feat-02 Column 对齐与反向排列：固化交叉轴对齐、主轴空间分布及 reverse 的存量布局行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Column 对齐与反向排列 |
| 特性编号 | Func-05-01-03-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Column 通过 LinearLayoutAlgorithm 复用 FlexLayoutAlgorithm，固定主轴为 COLUMN；主轴默认 Start、交叉轴默认 Center，Layout 阶段再应用空间分布、RTL 与 reverse。证据：frameworks/core/components_ng/pattern/linear_layout/linear_layout_algorithm.h:28-36；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:230-263,1567-1604。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 交叉轴对齐 | alignItems、RTL 与 alignSelf 覆盖 |
| ADDED | 主轴空间分布 | justifyContent 与显式 space/Space* 组合 |
| ADDED | 反向排列 | reverse 的 Measure/Layout 分工及 legacy 语义 |

本 Feat 仅接收“已解析的非负 space”；解析与 Resource 生命周期归 Feat-01。各入口的 undefined/reset/get/error 归 Feat-03，本文件不展开 Native 全量契约；PointLight 归 Feat-04。拆分依据见 `05-ui-components/01-layout-components/03-column/design.md` 的“设计骨架”和“后续 Task 拆分”。

## 输入文档

| 文档 | 路径及核对位置 |
|------|----------------|
| Design | 05-ui-components/01-layout-components/03-column/design.md |
| Dynamic SDK | interface/sdk-js/api/@internal/component/ets/column.d.ts:54-71,173-226 |
| NG 属性入口 | frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:150-207；frameworks/core/components_ng/pattern/flex/flex_layout_property.h:63-68 |
| NG 布局算法 | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1531-1739,1826-1836 |

## 用户故事

### US-1: 控制交叉轴对齐

**作为** ArkUI 开发者，**我想要** 控制子项横向位置并适配 RTL，**以便** 获得稳定的跨语言布局。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 未设置 alignItems THEN 有效子项按 Center 计算横向偏移 | 正常 |
| AC-1.2 | WHEN alignItems 为 Start/Center/End 且方向为 LTR THEN 子项靠左/居中/靠右 | 正常 |
| AC-1.3 | WHEN 方向为 RTL 或 AUTO 解析到 RTL THEN Start/End 横向互换、Center 不变且纵向主轴不翻转 | 边界 |
| AC-1.4 | WHEN 子项 alignSelf 非 AUTO THEN 覆盖容器值；WHEN 缺省/AUTO THEN 回退，Stretch 触发交叉轴二次测量 | 边界 |

### US-2: 分配主轴剩余空间

**作为** ArkUI 布局开发者，**我想要** 组合 justifyContent 与 space，**以便** 精确控制纵向留白。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN justifyContent 为 Start/Center/End THEN front 为 0/remain÷2/remain且相邻项使用显式 space | 正常 |
| AC-2.2 | WHEN justifyContent 为 Between/Around/Evenly THEN 忽略显式 space，between 为 remain/(N-1)、remain/N、remain/(N+1)，front 为 0、between/2、between | 正常 |
| AC-2.3 | WHEN 仅有一个有效子项 THEN Between 置于起点，Around/Evenly 均居中 | 边界 |
| AC-2.4 | WHEN 子项总高溢出或子项 GONE/离流 THEN remain 最小为 0且 GONE/离流不计入占用尺寸和位置序列 | 边界 |

### US-3: 反向排列子项

**作为** ArkUI 开发者，**我想要** 不改声明顺序而反向展示子项，**以便** 复用同一组件树。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 从未调用 reverse THEN IsReverse 缺省 false且从顶部向下放置 | 正常 |
| AC-3.2 | WHEN 显式 reverse(true) THEN 属性标脏 Measure，Measure 仍按 COLUMN 定尺寸，Layout 翻为 COLUMN_REVERSE 并从底向上放置 | 正常 |
| AC-3.3 | WHEN 显式 reverse(false) THEN Layout 不翻转且恢复从顶部向下放置 | 正常 |
| AC-3.4 | WHEN reverse 与 justifyContent、RTL 共存或运行 legacy pipeline THEN reverse 只翻纵向起点、RTL 只镜像横向，NG 按原序列写反向 offset且 legacy reverse 无效果 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1～AC-1.4 | R-1～R-2 | 已有实现 | NG Layout UT：默认/RTL/alignSelf | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1567-1689,1826-1836 |
| AC-2.1～AC-2.4 | R-3～R-5 | 已有实现 | 参数化 UT：N、space、溢出 | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1531-1657 |
| AC-3.1～AC-3.4 | R-6～R-9 | 已有实现 | 属性、方向、offset 与 legacy 回归 | test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp:785-801；test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp:426-474 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 未写 alignItems，或在 LTR/RTL 间切换 | cross 默认 Center；Start/End 随 RTL 镜像 | Center 不受 RTL 影响；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:247-253,1660-1678 | AC-1.1～AC-1.3 |
| R-2 | 边界 | 子项 alignSelf 为 AUTO、缺省、Stretch 或其他显式值 | AUTO/缺省回退容器，显式值覆盖；Stretch 重测 | 覆盖仅作用当前子项；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:973-975,1826-1836 | AC-1.4 |
| R-3 | 行为 | justify 为 Start/Center/End 且 space=S≥0 | front=0/remain÷2/remain，between=S | remain≥0；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1600-1604,1628-1642 | AC-2.1 |
| R-4 | 行为 | justify 为三种 Space* 且有效项数 N≥1 | 忽略 S，按 N 计算 front/between | N=1 使用专门分支；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1538-1554,1643-1654 | AC-2.2, AC-2.3 |
| R-5 | 边界 | allocatedSize>mainAxisSize，或子项 GONE/离流 | remain=0；GONE/离流不进入正常位置序列 | 不产生负 remain；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1545-1553,1600-1604,1697-1707 | AC-2.4 |
| R-6 | 行为 | IsReverse 缺省或写入 true/false | 缺省 false；写入触发 Measure 脏标记 | 属性类型为 bool；frameworks/core/components_ng/pattern/flex/flex_layout_property.h:63-68；frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:202-207 | AC-3.1～AC-3.3 |
| R-7 | 行为 | reverse=true 进入 Measure 与 Layout | Measure 固定 COLUMN；Layout 翻为 COLUMN_REVERSE | 仅 Layout 读取并翻转；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:230-263,1578-1583 | AC-3.2 |
| R-8 | 行为 | direction=COLUMN_REVERSE 放置有效子项 | 按原序列迭代，坐标从 mainAxisSize-front 起递减 | RTL 不改变纵向递减方向；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1691-1734 | AC-3.2～AC-3.4 |
| R-9 | 边界 | legacy pipeline 调用 reverse | SetIsReverse 空实现，不产生 NG 反向效果 | 仅限 legacy；frameworks/bridge/declarative_frontend/jsview/models/column_model_impl.h:24-30 | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1～R-2；AC-1.1～AC-1.4 | NG Layout UT | 断言 Center、两端、RTL、alignSelf offset；test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp:36-83 |
| VM-2 | R-3～R-5；AC-2.1～AC-2.4 | 参数化 Layout UT | N=0/1/2、space、溢出、GONE/离流；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1531-1657 |
| VM-3 | R-6～R-7；AC-3.1～AC-3.3 | Property/Algorithm UT | 初始 false 与 COLUMN→COLUMN_REVERSE；test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp:785-801；test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp:426-474 |
| VM-4 | R-8～R-9；AC-3.2～AC-3.4 | NG/legacy 兼容测试 | 反向 offset/序列与 legacy 无效果；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1691-1734；frameworks/bridge/declarative_frontend/jsview/models/column_model_impl.h:24-30 |

## API 变更分析

本次仅回填既有 API；声明见 interface/sdk-js/api/@internal/component/ets/column.d.ts:173-226。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| 无 | N/A | N/A | N/A | N/A | 存量补录，无新增 API | AC-1.1～AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 现有行为不变 | 无需迁移 | AC-1.1～AC-3.4 |

## 接口规格

### 接口定义

**alignItems**

| 属性 | 值 |
|------|-----|
| 函数签名 | ColumnAttribute.alignItems(value: HorizontalAlign): ColumnAttribute |
| 返回值 | ColumnAttribute — 链式配置当前 Column |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1～AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | HorizontalAlign | 是 | N/A（未调用时 Center） | Start/Center/End；undefined/reset 归 Feat-03 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Gherkin“RTL 镜像 Start” | Start/End 随 RTL 镜像 | AC-1.1～AC-1.3 |
| 2 | 规则 R-2：子项设置 alignSelf | 显式子项值覆盖容器值 | AC-1.4 |

证据：interface/sdk-js/api/@internal/component/ets/column.d.ts:173-186；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1660-1678,1826-1836。

**justifyContent**

| 属性 | 值 |
|------|-----|
| 函数签名 | ColumnAttribute.justifyContent(value: FlexAlign): ColumnAttribute |
| 返回值 | ColumnAttribute — 链式配置当前 Column |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1～AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | FlexAlign | 是 | N/A（未调用时 Start） | Start/Center/End/SpaceBetween/SpaceAround/SpaceEvenly |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Gherkin“Space* 分布矩阵” | 三种 Space* 忽略显式 space并按 N 分配 | AC-2.2, AC-2.3 |
| 2 | 规则 R-3/R-5 | 普通对齐保留 space；溢出时 remain=0 | AC-2.1, AC-2.4 |

证据：interface/sdk-js/api/@internal/component/ets/column.d.ts:54-71,188-200；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1531-1657。

**reverse**

| 属性 | 值 |
|------|-----|
| 函数签名 | ColumnAttribute.reverse(isReversed: Optional<boolean>): ColumnAttribute |
| 返回值 | ColumnAttribute — 链式配置当前 Column |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1～AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| isReversed | Optional<boolean> | 是 | N/A（未调用时属性 false） | 本 Feat 仅验收显式 true/false；undefined/reset 归 Feat-03 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Gherkin“reverse 反转纵向放置” | Measure 尺寸不变，Layout 从底向上写 offset | AC-3.1～AC-3.3 |
| 2 | 规则 R-9：legacy 调用 | 保持 legacy 无效果 | AC-3.4 |

证据：interface/sdk-js/api/@internal/component/ets/column.d.ts:212-226；frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:160-167,202-207；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:230-263,1578-1734。

Static 的 undefined 签名仅作为 Feat-03 边界，见 interface/sdk-js/api/arkui/component/column.static.d.ets:81-122。

## 兼容性声明

- **已有 API 行为变更:** 否；本次固化现有 SDK 与 NG 行为，证据见 interface/sdk-js/api/@internal/component/ets/column.d.ts:173-226 和 frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1531-1739。
- **配置文件格式变更:** 否；对齐与 reverse 写入既有 LayoutProperty，见 frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:150-177。
- **数据存储格式变更:** 否；属性随 FlexLayoutAttribute 运行时存在，见 frameworks/core/components_ng/pattern/flex/flex_layout_property.h:63-68。
- **最低支持版本:** API 7；justifyContent 自 API 8、reverse 自 API 12，见 interface/sdk-js/api/@internal/component/ets/column.d.ts:173-226。
- **API 版本号策略:** 保持 canonical SDK 的 @since 7/8/12，不新增版本标记，见 interface/sdk-js/api/@internal/component/ets/column.d.ts:173-226。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 生产链 | Pattern 创建 LinearLayoutAlgorithm 并继承 Flex；frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:47-55；frameworks/core/components_ng/pattern/linear_layout/linear_layout_algorithm.h:28-36 | AC-1.1～AC-3.4 |
| 阶段职责 | Measure 固定纵向，Layout 应用 align/RTL/reverse；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:230-263,1567-1739 | AC-1.1～AC-3.4 |
| 历史用例 | old_cases 仅作公式参考；当前 Column 不经过 LinearLayoutUtils，XComponent 仍独立调用；frameworks/core/components_ng/pattern/xcomponent/xcomponent_layout_algorithm.cpp:39-60 | AC-2.1～AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | reverse 沿原 children 序列单次放置 | Trace/代码审查 | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1697-1739 |
| 功耗 | 不新增定时器或后台任务，属性变化沿既有布局帧执行 | 代码审查 | frameworks/core/components_ng/pattern/flex/flex_layout_property.h:63-68 |
| 内存 | reverse 不排序、不复制 children | 内存回归/代码审查 | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1697-1739 |
| 安全 | 不处理敏感数据或新增权限 | SDK/代码审查 | interface/sdk-js/api/@internal/component/ets/column.d.ts:173-226 |
| 可靠性 | remain≥0，N=1 的 Space* 不除零 | 边界 UT | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1600-1604,1643-1654 |
| 可测试性 | 结果可由 GeometryNode frame offset 观测 | NG Layout UT | test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp:36-83 |
| 自动化维测 | Pattern dump 暴露 frontSpace/betweenSpace | Inspector/Dump | frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:94-120 |
| 定界定位 | 区分属性、Measure、Layout 与 legacy 四层 | 源码追溯 | 05-ui-components/01-layout-components/03-column/design.md |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 按内容区计算轴尺寸与 remain | 多尺寸 Layout UT | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1591-1604 |
| 平板 | 无差异 | 大窗口不改变分布公式 | 多尺寸 Layout UT | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1591-1657 |
| 折叠屏 | 无差异 | 折叠/展开后按新内容区重算 | 尺寸切换 Layout UT | frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1591-1604 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | reverse 只改 offset，Pattern 仍为纵向 Focus Scope；frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:57-65 | AC-3.4 |
| 大字体 | 是 | 子项尺寸变化后仍按同一 cross/remain 公式定位；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1531-1604 | AC-1.1～AC-2.4 |
| 深色模式 | 否 | 本 Feat 的 Layout 路径不读取颜色/主题；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1567-1739 | N/A |
| 多窗口/分屏 | 是 | 内容区变化后重算轴尺寸与 remain；frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1591-1604 | AC-2.1～AC-2.4 |
| 多用户 | 否 | 属性仅随 LayoutProperty 存在；frameworks/core/components_ng/pattern/flex/flex_layout_property.h:63-68 | N/A |
| 版本升级 | 是 | 保留 NG/legacy reverse 差异；frameworks/bridge/declarative_frontend/jsview/models/column_model_impl.h:24-30 | AC-3.4 |
| 生态兼容 | 是 | Space* 忽略 space 的 SDK/NG 契约一致；interface/sdk-js/api/@internal/component/ets/column.d.ts:54-71 | AC-2.2 |

## 行为场景（可选，Gherkin）

~~~gherkin
Feature: Column 对齐与反向排列

  # frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1660-1675
  Scenario: RTL 镜像 Start
    Given Column 宽 100vp且子项宽 20vp
    When alignItems 为 Start且方向从 LTR 切到 RTL
    Then 子项 x 从 0vp 变为 80vp

  # frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1538-1554,1643-1654
  Scenario Outline: Space* 分布矩阵
    Given remain 为 60vp且显式 space 为 10vp且有效子项数为 <N>
    When justifyContent 为 <align>
    Then front 为 <front> 且 between 为 <between>
    Examples:
      | N | align | front | between |
      | 2 | SpaceBetween | 0vp | 60vp |
      | 2 | SpaceAround | 15vp | 30vp |
      | 2 | SpaceEvenly | 20vp | 20vp |
      | 1 | SpaceBetween | 0vp | 0vp |
      | 1 | SpaceAround | 30vp | 60vp |
      | 1 | SpaceEvenly | 30vp | 30vp |

  # frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1578-1583,1691-1734
  Scenario: reverse 反转纵向放置
    Given Column 有两个声明顺序固定的子项
    When 显式 reverse true
    Then Layout 从底部向上写 offset
    And children 迭代序列不变
~~~

## Spec 自审清单

- [x] 12 条 AC 均含 WHEN/THEN、类型和源码证据
- [x] 9 条规则均有触发、可观测结果、证据与关联 AC
- [x] undefined/reset 只边界引用 Feat-03，未展开 Native
- [x] Resource/PointLight 已路由 Feat-01/Feat-04，old_cases 未误写为生产链

## context-references

~~~yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Column alignItems justifyContent RTL alignSelf FlexLayoutAlgorithm"
  - repo: "openharmony/interface_sdk-js"
    query: "Column space SpaceBetween SpaceAround SpaceEvenly reverse"
~~~
