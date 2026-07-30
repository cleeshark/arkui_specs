# 特性规格

> Func-05-01-10-Feat-01 RowSplit 水平分割布局与分隔线绘制存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RowSplit 水平分割布局与分隔线绘制 |
| 特性编号 | Func-05-01-10-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

RowSplit 沿水平方向排列子节点并绘制垂直分隔线；API>=10 的 NG 路径按可见子节点统计，API<10 的旧路径遍历全部构建子节点。它与 ColumnSplit 共享 LinearSplit 算法，但主轴、最小尺寸和安全区修正按 RowSplit 语义处理。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 水平分割布局规格 | 补录尺寸、可见子项、垂直 divider 与顺序 |
| ADDED | API 版本分支 | 补录 API 10 前后算法 |
| ADDED | 安全区与 layout policy | 补录位置修正和延迟测量 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/10-row-split/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/row_split.d.ts` | 已核对 |
| Layout | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp` | 已核对 |
| Paint | `frameworks/core/components_ng/pattern/linear_split/linear_split_paint_method.cpp` | 已核对 |

## 用户故事

### US-1: 形成稳定的水平分区

**作为** 应用开发者  
**我想要** RowSplit 按子项约束水平排布  
**以便** 构建左右可分割界面

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN NG 路径 API>=10 且 RowSplit 包含多个可见子项 THEN 子项沿 X 轴依次布局并在相邻子项间绘制垂直分隔线 | 正常 |
| AC-1.2 | WHEN NG 路径 API>=10 且子节点 Visibility=GONE THEN Measure/Layout 跳过该节点，visibleChildCount 与 divider 数按非 GONE 项计算 | 边界 |
| AC-1.3 | WHEN 父约束含合法理想尺寸 THEN 容器优先采用理想尺寸；否则按约束与子项测量结果确定 | 正常 |
| AC-1.4 | WHEN padding/border 非零 THEN 子项位于扣除边界后的内容区域 | 正常 |

### US-2: 保持旧版本和安全区行为

**作为** 框架维护者  
**我想要** API target 与安全区状态选择既有路径  
**以便** 升级不改变存量布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN NG 路径 API<10 THEN MeasureChildrenBeforeAPI10/LayoutBeforeAPI10 遍历全部构建子节点（包括 GONE），drag/divider 数按 totalChildCount 计算 | 边界 |
| AC-2.2 | WHEN API>=10 THEN 使用可见子项、最小宽度和 layout policy 的新算法 | 正常 |
| AC-2.3 | WHEN NG 路径 API>=10 且子项 ignoreLayoutSafeArea 有效 THEN 位置扣除累计安全区 left/top 偏移 | 正常 |
| AC-2.4 | WHEN NG 路径 API>=10 且 match-parent 子项需扩展约束 THEN 延迟测量并登记 Pipeline bundle | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Layout/Paint UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:83-103,347-400`; `frameworks/core/components_ng/pattern/linear_split/linear_split_paint_method.cpp:41-64` |
| AC-2.1~AC-2.2 | R-5~R-6 | 已有实现 | API target UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:51-55,521-636` |
| AC-2.3~AC-2.4 | R-7~R-8 | 已有实现 | SafeArea/LayoutPolicy UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:327-345,691-721` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | API>=10 且 N>=2 可见子项 | 沿 X 轴放置并生成 N-1 条垂直线 | N 为非 GONE 项数 | AC-1.1 |
| R-2 | 边界 | API>=10 且 GONE 子项 | 跳过测量占位与分隔线 | API<10 不过滤；INVISIBLE 始终占位 | AC-1.2 |
| R-3 | 行为 | ideal size 有效 | 优先采用理想尺寸 | 受 min/max 约束 | AC-1.3 |
| R-4 | 行为 | padding/border 非零 | 在内容区布局 | 尺寸非负 | AC-1.4 |
| R-5 | 边界 | API<10 | 使用旧算法并遍历全部构建项 | GONE 不过滤，保留旧 offset | AC-2.1 |
| R-6 | 行为 | API>=10 | 使用新算法 | 按可见项统计 | AC-2.2 |
| R-7 | 行为 | API>=10 且 ignore opts 有效 | 修正子项 offset | API<10 旧分支不执行 | AC-2.3 |
| R-8 | 边界 | API>=10 且延迟约束需要 | 登记 bundle 后由 Pipeline 补测 | API<10 旧分支不执行 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | LinearSplit Layout/Paint UT | API>=10 X 轴、GONE、padding |
| VM-2 | AC-2.1~AC-2.2 | API 9/10 UT | API 9 全构建项与 API 10 可见项统计 |
| VM-3 | AC-2.3~AC-2.4 | API 9/10 SafeArea/LayoutPolicy UT | 安全区/延迟 bundle 仅在 API>=10 NG 路径生效 |

## API 变更分析

### 新增 API

N/A，本次不新增 `RowSplit()` API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**RowSplit()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RowSplit(): RowSplitAttribute` |
| 返回值 | RowSplitAttribute — 水平分割容器属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| content | 子组件序列 | 否 | 空 | GONE 子项按版本路径处理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多个可见子项 | 水平布局并绘制垂直线 | AC-1.1 |
| 2 | API 9/10 | 旧/新算法 | AC-2.1, AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 10 为算法分界。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** Dynamic API 7，cross-platform API 10，Static API 23，Builder API 26。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 共享 LinearSplit | SplitType=ROW_SPLIT 固定水平主轴 | AC-1.1 |
| Paint 方向 | RowSplit 绘制垂直 divider | AC-1.1 |
| Pipeline 延迟 | Ignore-safe-area 未决约束由 scheduler 处理 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次布局按子项数线性遍历 | Trace | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:276-345` |
| 功耗 | 无后台任务 | 审查 | VM-1 |
| 内存 | API>=10 几何数组按可见项增长；API<10 旧状态按全部构建项增长 | API 9/10 UT | AC-1.2, AC-2.1 |
| 安全 | 无权限和敏感数据 | 审查 | VM-1 |
| 可靠性 | 空项安全处理；GONE 与延迟安全区行为严格遵守 API 9/10 分支 | 边界 UT | VM-1~VM-3 |
| 可测试性 | 位置和尺寸可直接断言 | UT | VM-1~VM-3 |
| 自动化维测 | Geometry/LayoutProperty 可 Dump | Inspector | AC-1.3 |
| 定界定位 | SDK/Layout/Paint/SafeArea 分层 | 代码审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 横向空间较小 | 最小宽度优先 | 尺寸矩阵 | AC-2.2 |
| 平板 | 适合多栏 | N 个可见项规则不变 | 多子项 UT | AC-1.1 |
| 折叠屏 | 展开后宽度变化 | 重新测量与安全区修正 | 集成测试 | AC-2.3 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 保持子节点语义顺序 | AC-1.1 |
| 大字体 | 是 | 内容最小宽度可能变化 | AC-2.2 |
| 深色模式 | 否 | 不涉及颜色配置 | VM-1 |
| 多窗口/分屏 | 是 | 宽度变化重测 | AC-1.3 |
| 多用户 | 否 | 无用户状态 | VM-1 |
| 版本升级 | 是 | API 10 分支回归 | AC-2.1 |
| 生态兼容 | 是 | 旧算法保留 | AC-2.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RowSplit 水平分割布局
  Scenario: 忽略 GONE 子项
    Given RowSplit 有三个子项且中间项为 GONE
    When API 10+ 执行测量布局
    Then 仅两个可见项占用宽度并生成一条垂直分隔线
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] API、GONE、安全区与 layout policy 边界明确
- [x] AC、规则、VM 一致
- [x] 未修改产品实现

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RowSplit horizontal LinearSplit API10 safe area"
  - repo: "openharmony/interface_sdk-js"
    query: "RowSplit API 7 static 23"
```

**关键文档：** `05-ui-components/01-layout-components/10-row-split/design.md`
