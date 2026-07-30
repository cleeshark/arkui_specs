# 特性规格

> Func-05-01-10-Feat-02 RowSplit 可拖拽调整与边界约束存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RowSplit 可拖拽调整与边界约束 |
| 特性编号 | Func-05-01-10-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性规定 RowSplit `resizeable`、垂直分隔线命中、水平拖拽、API 10 前后的两套位移模型、最小宽度边界、鼠标 hover/cursor 与状态生命周期。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | resizeable 行为 | 默认 false、设置与 reset |
| ADDED | 水平拖拽交互 | 触摸/鼠标命中、位移和结束 |
| ADDED | 宽度边界 | 最小宽度、padding/border 和 FRC 场景 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/10-row-split/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/row_split.d.ts` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/linear_split/linear_split_pattern.cpp` | 已核对 |
| Layout | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp` | 已核对 |

## 用户故事

### US-1: 拖动垂直分隔线

**作为** 应用用户  
**我想要** 水平拖动 RowSplit 分隔线  
**以便** 调整左右分区宽度

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN resizeable 未设置、false、undefined 或非法 THEN 分隔线不响应宽度拖拽 | 边界 |
| AC-1.2 | WHEN resizeable=true 且指针命中垂直分隔线热区 THEN 记录索引并开始水平拖拽 | 正常 |
| AC-1.3 | WHEN NG 路径 API>=10 且 dx 在合法区间 THEN childrenDragPos 边界移动，左右子项宽度反向变化且总主轴长度保持 | 正常 |
| AC-1.4 | WHEN 指针未命中 divider THEN 不改变拖拽数组或子项几何 | 异常 |
| AC-1.5 | WHEN NG 路径 API<10 或 legacy renderer 处理拖拽 THEN 仅累计非负 dragSplitOffset，在 divider 后增加间距并平移后续子项，不改变相邻子项宽度 | 边界 |

### US-2: 限制边界并提供鼠标反馈

**作为** 应用开发者  
**我想要** 拖拽遵守宽度限制  
**以便** 子项保持可用

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN NG 路径 API>=10 的拖拽导致任一相邻子项低于显式或主题最小宽度 THEN dx 被钳制到最后合法值；API<10 gap-only 路径不应用该最小尺寸钳制 | 边界 |
| AC-2.2 | WHEN padding/border 占用宽度 THEN 可拖区间按内容宽度计算 | 正常 |
| AC-2.3 | WHEN NG 鼠标 hover 命中可拖 divider THEN cursor 按两侧可移动边界返回 DEFAULT、单向或双向横向 resize；legacy renderer 命中时使用双向横向 resize，离开后恢复 | 边界 |
| AC-2.4 | WHEN PanEnd/鼠标释放 THEN 仅清除 isDraged 与当前索引并保留 childrenDragPos；WHEN resizeable 属性 flag 变化触发 OnModifyDone THEN 清空 childrenDragPos 但不清除旧版 dragSplitOffset | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-4, R-9 | 已有实现 | API 9/10 Touch/Mouse UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_pattern.cpp:113-165,238-344`; `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:521-636` |
| AC-2.1~AC-2.2 | R-5~R-6 | 已有实现 | API 9/10 minSize UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:496-506,521-657` |
| AC-2.3~AC-2.4 | R-7~R-8 | 已有实现 | Cursor/状态生命周期 UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_pattern.cpp:346-369,371-518,533-581` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 边界 | resizeable 非 true | 禁止调整 | 默认 false | AC-1.1 |
| R-2 | 行为 | 命中垂直热区 | 选择 divider 并开始拖拽 | 单索引 | AC-1.2 |
| R-3 | 行为 | API>=10 合法 dx | 左右宽度反向变化 | 总宽度不变 | AC-1.3 |
| R-4 | 异常 | 未命中 | 忽略更新 | 不污染几何 | AC-1.4 |
| R-5 | 边界 | API>=10 达到 minWidth | 钳制位移 | 显式/主题最小值；API<10 不适用 | AC-2.1 |
| R-6 | 行为 | padding/border 非零 | 扣除后计算可用宽度 | 非负 | AC-2.2 |
| R-7 | 边界 | hover 命中/离开 | NG 按边界选择 DEFAULT/单向/双向横向 cursor；legacy 命中为双向 | resizeable=true | AC-2.3 |
| R-8 | 边界 | PanEnd/释放或属性 flag 变化 | 前者清 isDraged/index 并保留位置；后者清 childrenDragPos 且保留 dragSplitOffset | 不存在统一“全状态清空” | AC-2.4 |
| R-9 | 边界 | API<10/legacy 合法拖拽 | 累计非负 dragSplitOffset，增加 divider 后间距并平移后续项 | 不调整相邻尺寸、不应用 minWidth 钳制 | AC-1.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.5 | API 9/10 与 legacy Touch/Mouse UT | 命中、API>=10 相邻尺寸及 API<10 gap-only 位移 |
| VM-2 | AC-2.1~AC-2.2 | API 9/10 最小宽度矩阵 | 钳制仅适用于 API>=10，内容宽度 |
| VM-3 | AC-2.3~AC-2.4 | Hover/PanEnd/OnModifyDone UT | cursor 状态矩阵与字段级清理 |

## API 变更分析

### 新增 API

N/A，`resizeable` 为 API 7 已有接口。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**resizeable(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `resizeable(value: boolean): RowSplitAttribute` |
| 返回值 | RowSplitAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4, AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | boolean | 是 | false | undefined/非法值按 reset/default 处理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | true、API>=10 且命中 divider | 在最小宽度边界内反向调整相邻子项 | AC-1.2, AC-1.3, AC-2.1 |
| 2 | false/未命中 | 不改变宽度 | AC-1.1, AC-1.4 |
| 3 | true、API<10 且命中 divider | 仅增加非负间距并平移后续项 | AC-1.5 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 10 将 gap-only 拖拽切换为相邻子项反向改尺寸并增加 minWidth 钳制，legacy renderer 保留旧模型。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** Dynamic API 7，Static API 23，Builder API 26。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| Pattern 状态 | 命中、hover、拖拽状态由 LinearSplitPattern 持有 | AC-1.2 |
| 最小宽度 | API>=10 由 LayoutAlgorithm 计算显式/主题/padding 边界；API<10 只应用非负 gap offset | AC-1.5, AC-2.1 |
| 轴向 | RowSplit 只消费 X 方向位移 | AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 指针移动仅更新相邻几何和脏标记 | Trace | `frameworks/core/components_ng/pattern/linear_split/linear_split_pattern.cpp:238-287` |
| 功耗 | 仅交互时处理事件 | 审查 | VM-1 |
| 内存 | 交互状态随节点释放 | 生命周期 UT | VM-3 |
| 安全 | 无权限和敏感数据 | 审查 | VM-1 |
| 可靠性 | 越界和未命中不破坏布局 | 边界 UT | VM-1, VM-2 |
| 可测试性 | dx、索引、cursor 可断言 | UT | VM-1~VM-3 |
| 自动化维测 | 事件 Trace 可定位交互阶段 | Trace | AC-2.4 |
| 定界定位 | Event/Pattern/Layout 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 触摸为主 | 命中区遵守边界 | Touch UT | AC-1.2 |
| 平板 | 鼠标场景常见 | 东西向 cursor | Mouse UT | AC-2.3 |
| 折叠屏 | 宽度突变 | 按版本模型重布局；普通重布局不等价于清空全部交互字段 | 集成测试 | AC-2.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 不改变语义顺序 | AC-1.3 |
| 大字体 | 是 | minWidth 可变化 | AC-2.1 |
| 深色模式 | 否 | 不涉及颜色 | VM-1 |
| 多窗口/分屏 | 是 | 宽度变化后重算边界 | AC-2.4 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | 多输入通道需回归 | 兼容性声明 |
| 生态兼容 | 是 | 默认 false 不变 | AC-1.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RowSplit 拖拽
  Scenario Outline: 版本化拖拽模型
    Given resizeable 为 true 且命中垂直分隔线
    When API 版本为 <version> 并向右拖动
    Then 产生 <result>

    Examples:
      | version | result |
      | 9 | 非负 gap 增长并平移后续子项 |
      | 10 | 相邻宽度反向变化并按 minWidth 钳制 |
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] API 9/10 拖拽、未命中、边界、cursor 与字段级状态生命周期明确
- [x] AC、规则、VM 一致
- [x] 未修改实现

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RowSplit resizeable horizontal drag cursor min width"
  - repo: "openharmony/interface_sdk-js"
    query: "RowSplit resizeable API 7"
```

**关键文档：** `05-ui-components/01-layout-components/10-row-split/design.md`
