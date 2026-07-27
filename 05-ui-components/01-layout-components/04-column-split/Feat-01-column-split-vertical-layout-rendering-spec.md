# 特性规格

> Func-05-01-04-Feat-01 ColumnSplit 垂直分割布局与分隔线绘制存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ColumnSplit 垂直分割布局与分隔线绘制 |
| 特性编号 | Func-05-01-04-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

ColumnSplit 沿纵向排列子节点并在相邻项之间绘制水平分隔线；API>=10 的 NG 路径按可见子节点统计，API<10 的旧路径遍历全部构建子节点，并按版本选择布局策略与安全区处理。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 垂直分割布局规格 | 补录容器尺寸、子项测量、分隔线位置和可见性规则 |
| ADDED | API 版本分支规格 | 补录 API 10 前后两套既有算法 |
| ADDED | 安全区集成规格 | 补录 ignoreLayoutSafeArea 的位置修正与延迟测量 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/04-column-split/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/column_split.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/columnSplit.static.d.ets` | 已核对 |
| Layout | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp` | 已核对 |
| Paint | `frameworks/core/components_ng/pattern/linear_split/linear_split_paint_method.cpp` | 已核对 |

## 用户故事

### US-1: 形成稳定的纵向分区

**作为** 应用开发者  
**我想要** ColumnSplit 按子项约束纵向排布并显示分隔线  
**以便** 构建可调整的上下分区界面

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN NG 路径 API>=10 且包含多个可见子节点 THEN 子节点沿 Y 轴依次布局，相邻可见子节点之间形成水平分隔线 | 正常 |
| AC-1.2 | WHEN NG 路径 API>=10 且子节点 Visibility=GONE THEN Measure/Layout 跳过该节点，visibleChildCount 与 divider 数按非 GONE 项计算 | 边界 |
| AC-1.3 | WHEN 父约束含合法 selfIdealSize THEN 容器优先采用该理想尺寸；否则按约束和子项测量结果确定尺寸 | 正常 |
| AC-1.4 | WHEN padding 或 border 非零 THEN 子项与分隔线在扣除内边距后的内容区域内布局 | 正常 |

### US-2: 保持版本和安全区兼容

**作为** 框架维护者  
**我想要** 不同 API target 与安全区状态走各自既有路径  
**以便** 存量应用升级后保持可观测行为

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN NG 路径 API<10 THEN MeasureChildrenBeforeAPI10/LayoutBeforeAPI10 遍历全部构建子节点（包括 GONE），drag/divider 数按 totalChildCount 计算 | 边界 |
| AC-2.2 | WHEN 平台 API 版本不低于 10 THEN 新算法按可见子项、layout policy 和最小尺寸完成测量布局 | 正常 |
| AC-2.3 | WHEN NG 路径 API>=10 且子节点启用 ignoreLayoutSafeArea THEN 布局位置扣除累计安全区扩展偏移 | 正常 |
| AC-2.4 | WHEN NG 路径 API>=10 且 match-parent 子节点需要扩展约束 THEN 子节点进入延迟测量 bundle，后续由 Pipeline 调度完成而不使用未决几何 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Layout/Paint UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:199-205,402-460`; `frameworks/core/components_ng/pattern/linear_split/linear_split_paint_method.cpp:41-64` |
| AC-2.1~AC-2.2 | R-5~R-6 | 已有实现 | API target UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:51-55,521-636` |
| AC-2.3~AC-2.4 | R-7~R-8 | 已有实现 | SafeArea/LayoutPolicy UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:327-345,691-721` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | API>=10 且至少两个可见子项 | 沿 Y 轴依次放置并生成 N-1 条水平分隔线 | N 为非 GONE 子项数 | AC-1.1 |
| R-2 | 边界 | API>=10 且 Visibility=GONE | 跳过该子项 | API<10 不过滤；INVISIBLE 始终参与布局 | AC-1.2 |
| R-3 | 行为 | selfIdealSize 有效 | 优先采用理想尺寸 | 仍受 min/max 约束 | AC-1.3 |
| R-4 | 行为 | padding/border 非零 | 扣除内容边界后布局 | 尺寸不得为负 | AC-1.4 |
| R-5 | 边界 | API<10 | 使用旧测量布局及 dragSplitOffset，并遍历全部构建项 | GONE 不过滤，按 totalChildCount 统计 | AC-2.1 |
| R-6 | 行为 | API>=10 | 使用新测量布局和 layout policy | 可见项独立统计 | AC-2.2 |
| R-7 | 行为 | API>=10 且 ignore opts 有效 | 减去累计 left/top 安全区偏移 | API<10 旧分支不执行 | AC-2.3 |
| R-8 | 边界 | API>=10 且子项需延迟扩展约束 | 登记 bundle 并推迟自身布局 | API<10 旧分支不执行 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | `linear_split_test_ng.cpp` 布局与绘制用例 | API>=10 顺序、尺寸、GONE、padding |
| VM-2 | AC-2.1~AC-2.2 | API target 参数化 UT | API 9 全构建项与 API 10 可见项统计 |
| VM-3 | AC-2.3~AC-2.4 | API 9/10 安全区与 layout policy UT | 安全区/延迟 bundle 仅在 API>=10 NG 路径生效 |

## API 变更分析

### 新增 API

N/A，本次仅补录已有 `ColumnSplit()` 行为，不新增 API。

### 变更/废弃 API

N/A，无 API 变更或废弃。

## 接口规格

### 接口定义

**ColumnSplit()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ColumnSplit(): ColumnSplitAttribute` |
| 返回值 | ColumnSplitAttribute — 垂直分割容器属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| content | 子组件序列 | 否 | 空 | 支持子组件；GONE 子项按版本路径处理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多个可见子项 | 纵向布局并绘制水平分隔线 | AC-1.1 |
| 2 | API 9/10 且含 GONE 项 | API 9 按全部构建项、API 10 按非 GONE 项布局 | AC-1.2, AC-2.1, AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 10 是测量布局算法分界，按当前实现分别记录。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** Dynamic API 7，cross-platform API 10，Static API 23，Builder API 26。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 共享算法 | ColumnSplit 与 RowSplit 共享 LinearSplitLayoutAlgorithm，以 SplitType 分派 | AC-1.1 |
| Paint 分离 | 分隔线由 LinearSplitPaintMethod 绘制 | AC-1.1 |
| 安全区调度 | 延迟测量必须通过 Pipeline bundle 完成 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次布局按子项数线性遍历，无后台循环 | Trace/UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:276-345` |
| 功耗 | 无定时器和后台任务 | 代码审查 | VM-1 |
| 内存 | API>=10 的位置数组按可见项增长；API<10 的旧状态按全部构建项增长 | API 9/10 UT | AC-1.2, AC-2.1 |
| 安全 | 不访问权限或敏感数据 | API 审查 | VM-1 |
| 可靠性 | 空项安全处理；GONE 与安全区行为严格遵守 API 9/10 分支 | 边界 UT | VM-1~VM-3 |
| 可测试性 | API 分支和几何结果可直接断言 | 单元测试 | VM-1~VM-3 |
| 自动化维测 | LayoutProperty/Geometry 可 Dump | Inspector | AC-1.3 |
| 定界定位 | 可按 SDK、Model、Layout、Paint 分层定位 | 代码审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 通常为窄宽纵向分区 | 仍按父约束布局 | 尺寸矩阵 | AC-1.3 |
| 平板 | 可容纳更多分区 | 子项数不改变规则 | 多子项 UT | AC-1.1 |
| 折叠屏 | 窗口尺寸变化触发重测 | 保留版本分支与安全区规则 | 折叠态集成测试 | AC-2.3 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 不改变子节点语义顺序 | AC-1.1 |
| 大字体 | 是 | 子项最小高度可影响分区 | AC-1.3 |
| 深色模式 | 否 | 分隔线当前绘制规则不引入主题 API | AC-1.1 |
| 多窗口/分屏 | 是 | 尺寸变化后重新测量 | AC-1.3 |
| 多用户 | 否 | 无用户级状态 | VM-1 |
| 版本升级 | 是 | API 10 分支需回归 | AC-2.1 |
| 生态兼容 | 是 | 保留旧算法行为 | AC-2.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ColumnSplit 垂直分割布局
  Scenario Outline: API 版本选择布局算法
    Given ColumnSplit 包含两个可见子项
    When 平台 API 版本为 <version>
    Then 使用 <algorithm> 完成纵向布局

    Examples:
      | version | algorithm |
      | 9 | 旧算法 |
      | 10 | 新算法 |
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 且可独立测试
- [x] API 10、GONE、安全区和 layout policy 边界明确
- [x] AC、规则和 VM 双向追溯
- [x] 未提出产品实现修改

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ColumnSplit LinearSplitLayoutAlgorithm API10 safe area"
  - repo: "openharmony/interface_sdk-js"
    query: "ColumnSplit API 7 static 23"
```

**关键文档：** `05-ui-components/01-layout-components/04-column-split/design.md`
