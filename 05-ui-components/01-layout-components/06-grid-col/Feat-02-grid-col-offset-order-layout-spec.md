# 特性规格

> Func-05-01-06-Feat-02 GridCol 偏移、排序与协同布局：补录 offset/order 六档属性及 GridRow 对排序、换行、列宽和非 GridCol 子项的处理。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GridCol 偏移、排序与协同布局 |
| 特性编号 | Func-05-01-06-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

GridCol 的 `offset` 表示相对原始栅格位置前移的空列数，`order` 表示当前断点的展示排序值。二者只保存配置，最终顺序、换行数和 x/y 偏移由 GridRowLayoutAlgorithm 计算。公开定义见 `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:149-186,242-271`，算法边界见 `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:44-80,120-189,587-599`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | offset 响应式规格 | 覆盖标量、六档对象、默认值、非法值和前向继承 |
| ADDED | order 排序规格 | 覆盖默认 0、升序、同值稳定顺序和未设置项 |
| ADDED | GridRow 协同布局规格 | 覆盖 span 限制、offset 换行、跨多行和子项宽度 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/06-grid-col/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts` | 已核对 |
| GridCol Property | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_property.h` | 已核对 |
| GridCol Bridge/Modifier | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp`、`grid_col_dynamic_modifier.cpp` | 已核对 |
| GridRow Algorithm | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp` | 已核对 |

> GridRow 的 columns、gutter、breakpoint、alignItems 和 RTL 完整契约归 05-01-07；本文只定义 GridCol 输入如何被父容器消费。

## 用户故事

### US-1: 设置栅格偏移

**作为** 响应式页面开发者  
**我想要** 为 GridCol 设置当前断点的 offset  
**以便** 在栅格中形成留白并在空间不足时得到确定的换行

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN offset 为非负整数 n THEN 六档均为 n；WHEN 为对象 THEN xs 缺失使用 0、其余缺失档继承前一档 | 正常 |
| AC-1.2 | WHEN offset 缺失、为负数或不是支持的标量/对象 THEN Dynamic 路径使用 0 且不抛业务错误码 | 异常 |
| AC-1.3 | WHEN 当前剩余列数不小于 `offset + span` THEN GridCol 留在当前行，行内起始列在当前已占列之后增加 offset | 正常 |
| AC-1.4 | WHEN 当前剩余列可容纳 offset 但不能容纳 `offset + span` THEN GridCol 换到下一行且新行 offset 为 0 | 边界 |
| AC-1.5 | WHEN offset 大于当前剩余列 THEN 算法按总列数计算跨越行数和余数；若余数加 span 再次越界，则再增加一行并以 0 offset 放置 | 边界 |

### US-2: 按 order 稳定排序

**作为** 页面开发者  
**我想要** 不改变声明树的情况下调整 GridCol 展示顺序  
**以便** 在不同断点呈现不同的信息优先级

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN order 为非负整数 n THEN 六档均为 n；WHEN 为对象 THEN xs 缺失使用 0、其余缺失档继承前一档 | 正常 |
| AC-2.2 | WHEN order 缺失或非法 THEN 使用默认 0 | 异常 |
| AC-2.3 | WHEN 同一 GridRow 的 GridCol 具有不同 order THEN GridRow 在测量前按当前断点 order 升序排列 | 正常 |
| AC-2.4 | WHEN 多个 GridCol 的 order 相同 THEN 保持其原始代码顺序；未设置 order 的 0 值项位于正 order 项之前 | 边界 |
| AC-2.5 | WHEN GridRow 的 sizeType 改变 THEN 排序使用新断点对应的 order，并重新执行 Measure | 正常 |

### US-3: 由父容器完成宽度和行高计算

**作为** 布局维护者  
**我想要** 明确 GridCol 与 GridRow 的职责边界  
**以便** 避免在两个组件规格中重复或冲突地定义算法

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN GridRow 测量 GridCol THEN 有效 span 为 span 与总列数的较小值，宽度为 `columnUnitWidth * span + gutterX * (span - 1)` | 正常 |
| AC-3.2 | WHEN 一行内多个 GridCol 高度不同 THEN GridRow 使用该行最大子项高度推进下一行；GridCol 不自行维护行高 | 正常 |
| AC-3.3 | WHEN 子节点不是 GRID_COL 或没有 GridColLayoutProperty THEN GridRow 跳过该节点 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.2 | R-1~R-2 | 已有实现 | Bridge 参数矩阵 | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:68-86,111-150,230-231` |
| AC-1.3~AC-1.5 | R-3~R-5 | 已有实现 | GridRow offset Layout UT | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:44-80,146-183` |
| AC-2.1~AC-2.5 | R-6~R-8 | 已有实现 | order Property/Layout UT | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:164-186`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:587-599` |
| AC-3.1~AC-3.3 | R-9~R-11 | 已有实现 | GridRow 测量与混合子项 UT | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:120-189` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | offset 是标量或包含有效字段的六档对象 | 标量广播六档；对象 xs 缺失为 0、其余缺失档继承前一档 | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:68-86,111-150` | AC-1.1 |
| R-2 | 异常 | offset 标量小于 0、类型不支持或对象字段小于 0 | 无效位置使用默认 0，写入 Offset 并触发 Measure | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:111-150,230-231`；`frameworks/core/components_ng/pattern/grid_col/grid_col_layout_property.h:54-56` | AC-1.2 |
| R-3 | 行为 | `restColumns >= offset + span` | 不换行；本行 offset 增加属性值 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:61-80` | AC-1.3 |
| R-4 | 边界 | `restColumns < offset + span` 且 `restColumns >= offset` | 换一行并把新行 offset 置 0 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:66-73` | AC-1.4 |
| R-5 | 边界 | `offset > restColumns` | 以总列数计算跨行数量和余数，余数加 span 越界时再换一行 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:44-59,72-74` | AC-1.5 |
| R-6 | 行为 | order 是标量或六档对象 | 标量广播；对象按默认 0 和前档继承补齐 | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:122-150,223-239` | AC-2.1 |
| R-7 | 异常 | order 缺失或非法 | 使用 0；reset 恢复六档 0 | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:122-135,232-239` | AC-2.2 |
| R-8 | 行为 | GridRow 开始测量子列表 | 以当前 sizeType 的 order 升序 stable sort，同值保持源码顺序 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:120-126,587-599` | AC-2.3~AC-2.5 |
| R-9 | 行为 | 父容器测量合法 GridCol | span 限制到 columns，按列宽和 gutterX 计算理想宽度 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:135-166` | AC-3.1 |
| R-10 | 行为 | 一行包含不同高度 GridCol | currentRowHeight 保存最大 margin frame height，换行时累计总高度 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:153-189` | AC-3.2 |
| R-11 | 异常 | 子项 tag/Property 不是 GridCol | continue 跳过，不进入 span/offset/order 计算 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:135-143` | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-2, AC-1.1~AC-1.2 | Bridge/Property UT | offset 标量、对象、负数、缺字段、reset |
| VM-2 | R-3~R-5, AC-1.3~AC-1.5 | 参数化 Layout UT | 剩余列等于/小于 offset+span、大 offset 跨多行 |
| VM-3 | R-6~R-8, AC-2.1~AC-2.5 | order 排序 UT | 0、同值稳定性、不同断点 order |
| VM-4 | R-9~R-11, AC-3.1~AC-3.3 | GridRow 协同 UT | span clamp、gutter 公式、行高、混合子项 |

## API 变更分析

> 本次只补录已有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `gridColOffset(value)` | Public | 非负整数或 GridColColumnOption | GridColAttribute | N/A | API 9 设置响应式偏移 | AC-1.1~AC-1.5 |
| `order(value)` | Public | 非负整数或 GridColColumnOption | GridColAttribute | N/A | API 9 设置响应式展示顺序 | AC-2.1~AC-2.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | offset/order 沿用 API 9 前档继承语义 | 无需迁移 | AC-1.1, AC-2.1 |

## 接口规格

### 接口定义

**gridColOffset(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `gridColOffset(value: number \| GridColColumnOption): GridColAttribute` |
| 返回值 | GridColAttribute — 返回当前属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | number/GridColColumnOption | 是 | 0（非法值回退） | 非负整数；允许超过当前行或总列数 |

**order(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `order(value: number \| GridColColumnOption): GridColAttribute` |
| 返回值 | GridColAttribute — 返回当前属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | number/GridColColumnOption | 是 | 0（非法值回退） | 非负整数；相同值按代码顺序 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | offset+span 小于等于剩余列 | 保持本行并增加 offset | AC-1.3 |
| 2 | offset 或 offset+span 超过剩余列 | 按边界换一行或跨多行 | AC-1.4, AC-1.5 |
| 3 | order 不同/相同/未设置 | 升序且相同值稳定 | AC-2.3, AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；offset/order 自 API 9 保持默认 0 与向前继承。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 9。
- **API 版本号策略:** 以 Dynamic `@since 9` 为基线；Static 与 modifier 版本归 Feat-03。

| 场景 | 兼容结论 | 证据 |
|------|----------|------|
| 缺失低断点 | offset/order 的 xs 为 0，不采用 API 20 span 的高档回填 | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:117-124` |
| order 未设置 | 默认 0，位于正值 order 项之前 | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:164-186` |
| offset 超行 | 保留跨行行为，不截断成总列数 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:44-80` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| GridCol 属性所有权 | offset/order 存在 GridColLayoutProperty | AC-1.1, AC-2.1 |
| GridRow 算法所有权 | 排序、换行、宽度、行高由父容器计算 | AC-1.3~AC-3.3 |
| 当前断点一致性 | span/offset/order 必须使用同一 sizeType | AC-2.5, AC-3.1 |
| 稳定顺序 | 同 order 不得引入节点 ID 等二次排序 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增性能指标；每次 Measure 对子列表排序并线性测量 | Trace/基准 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:120-189` |
| 功耗 | 不新增异步任务或轮询 | 代码审查 | VM-1~VM-4 |
| 内存 | 行数据仅在 LayoutAlgorithm 中保存当前测量结果 | 内存基线 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:168-188` |
| 安全 | 不涉及权限和敏感数据 | 代码审查 | VM-4 |
| 可靠性 | 极大 offset 通过整数行数计算，不越界访问子列表 | 边界 UT/fuzz | AC-1.5 |
| 可测试性 | 固定 columns/span/offset/order 即可复现全部规则 | 参数化 UT | VM-1~VM-4 |
| 自动化维测 | GridCol Dump 输出布局属性 | Inspector/Dump | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_pattern.h:56-63` |
| 定界定位 | 属性解析与父算法分别定位 | 源码追溯 | `05-ui-components/01-layout-components/06-grid-col/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无专有差异 | 当前 sizeType 选择对应 offset/order | 多窗口宽度矩阵 | AC-1.1, AC-2.5 |
| 平板 | 无专有差异 | 较大 columns 可能减少换行，但算法不变 | columns 参数化测试 | AC-1.3~AC-1.5 |
| 折叠屏 | sizeType 可随折叠态变化 | 重新排序并重新计算行 | 折叠/展开集成测试 | AC-2.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | order 改变视觉位置，不重写声明树；需回归焦点阅读顺序 | AC-2.3, AC-2.4 |
| 大字体 | 是 | 内容高度改变行高，offset/order 规则不变 | AC-3.2 |
| 深色模式 | 否 | 不涉及颜色 |
| 多窗口/分屏 | 是 | 断点变化后可使用不同 offset/order 并重新布局 | AC-2.5 |
| 多用户 | 否 | 无用户持久状态 |
| 版本升级 | 否 | 本 Feat 未引入 API 20 专有语义变化 |
| 生态兼容 | 是 | 同 order 稳定性和大 offset 行为必须保留 | AC-1.5, AC-2.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: GridCol 偏移、排序与协同布局
  Scenario: 当前行能容纳 offset 但不能容纳 span
    Given GridRow 总列数为 12 且当前行剩余 7 列
    And GridCol offset 为 5 且 span 为 4
    When GridRow 测量该 GridCol
    Then GridCol 换到下一行
    And 新行 offset 为 0

  Scenario: 同 order 保持代码顺序
    Given 三个 GridCol 的 order 依次为 0、2、2
    When GridRow 对子项排序
    Then order 为 0 的子项在前
    And 两个 order 为 2 的子项保持声明顺序
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x] GridCol 输入与 GridRow 算法职责边界明确
- [x] span 创建与版本继承路由到 Feat-01
- [x] 每个 AC 与规则、VM 双向可追溯
- [x] 数值边界包含 0、等于剩余列、越过一行和跨多行

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "GridCol offset order stable sort CalculateOffsetOfNewline GridRow"
  - repo: "openharmony/interface_sdk-js"
    query: "GridCol gridColOffset order GridColColumnOption API 9"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/grid_col.d.ts`
- 共享设计：`05-ui-components/01-layout-components/06-grid-col/design.md`
