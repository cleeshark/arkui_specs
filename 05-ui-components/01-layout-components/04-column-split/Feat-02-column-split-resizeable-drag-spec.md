# 特性规格

> Func-05-01-04-Feat-02 ColumnSplit 可拖拽调整与边界约束存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ColumnSplit 可拖拽调整与边界约束 |
| 特性编号 | Func-05-01-04-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性规定 ColumnSplit 的 `resizeable`、水平分隔线命中、纵向拖拽、API 10 前后的两套位移模型、最小高度边界、hover/cursor 和拖拽状态生命周期。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | resizeable 契约 | 补录默认、设置、重置与属性变化 |
| ADDED | 拖拽交互 | 补录触摸/鼠标命中、更新和结束 |
| ADDED | 尺寸边界 | 补录子项最小尺寸、padding/border 与 FRC 约束 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/04-column-split/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/column_split.d.ts` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/linear_split/linear_split_pattern.cpp` | 已核对 |
| Layout | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp` | 已核对 |

## 用户故事

### US-1: 拖动分隔线调整高度

**作为** 应用用户  
**我想要** 拖动 ColumnSplit 的水平分隔线  
**以便** 调整上下相邻分区的高度

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN resizeable 未设置、为 false、undefined 或非法值 THEN 分隔线不响应尺寸拖拽 | 边界 |
| AC-1.2 | WHEN resizeable=true 且指针命中分隔线热区 THEN Pattern 记录当前分隔线并开始纵向拖拽 | 正常 |
| AC-1.3 | WHEN NG 路径 API>=10 且拖拽增量位于允许区间 THEN childrenDragPos 边界移动，上下相邻子项按相反方向改变高度且总主轴长度保持 | 正常 |
| AC-1.4 | WHEN 指针未命中任何分隔线 THEN 不改变拖拽位置数组或子项几何 | 异常 |
| AC-1.5 | WHEN NG 路径 API<10 或 legacy renderer 处理拖拽 THEN 仅累计非负 dragSplitOffset，在 divider 后增加间距并平移后续子项，不改变相邻子项高度 | 边界 |

### US-2: 遵守最小尺寸和交互边界

**作为** 应用开发者  
**我想要** 框架限制非法拖拽并提供可感知的鼠标反馈  
**以便** 分区不会被拖成不可用尺寸

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN NG 路径 API>=10 的拖拽将任一相邻子项压缩到显式或主题最小高度以下 THEN 位移被钳制在最后合法边界；API<10 gap-only 路径不应用该最小尺寸钳制 | 边界 |
| AC-2.2 | WHEN padding/border 或 divider margin 占用主轴空间 THEN 可拖范围按扣除后的有效尺寸计算 | 正常 |
| AC-2.3 | WHEN NG 鼠标 hover 命中可拖水平分隔线 THEN cursor 按两侧可移动边界返回 DEFAULT、单向或双向纵向 resize；legacy renderer 命中时使用双向纵向 resize，离开后恢复 | 边界 |
| AC-2.4 | WHEN PanEnd/鼠标释放 THEN 仅清除 isDraged 与当前索引并保留 childrenDragPos；WHEN resizeable 属性 flag 变化触发 OnModifyDone THEN 清空 childrenDragPos 但不清除旧版 dragSplitOffset | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-4, R-9 | 已有实现 | API 9/10 Touch/Mouse UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_pattern.cpp:113-165,238-344`; `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:521-636` |
| AC-2.1~AC-2.2 | R-5~R-6 | 已有实现 | API 9/10 边界布局 UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:496-506,521-657` |
| AC-2.3~AC-2.4 | R-7~R-8 | 已有实现 | Cursor/状态生命周期 UT | `frameworks/core/components_ng/pattern/linear_split/linear_split_pattern.cpp:346-369,371-518,533-581` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 边界 | resizeable 非 true | 禁止拖拽调整 | 默认 false | AC-1.1 |
| R-2 | 行为 | 命中水平分隔线热区 | 选择索引并开始拖拽 | 只选一个分隔线 | AC-1.2 |
| R-3 | 行为 | API>=10 合法 dy | 相邻高度反向变化 | 总长度不变 | AC-1.3 |
| R-4 | 异常 | 未命中热区 | 忽略拖拽更新 | 不污染数组 | AC-1.4 |
| R-5 | 边界 | API>=10 达到 minSize | 将位移钳制为边界值 | minSize 含主题默认；API<10 不适用 | AC-2.1 |
| R-6 | 行为 | 存在边框/内边距/分隔线边距 | 从可用主轴长度扣除 | 结果不得为负 | AC-2.2 |
| R-7 | 边界 | hover 命中/离开 | NG 按边界选择 DEFAULT/单向/双向纵向 cursor；legacy 命中为双向 | resizeable=true | AC-2.3 |
| R-8 | 边界 | PanEnd/释放或属性 flag 变化 | 前者清 isDraged/index 并保留位置；后者清 childrenDragPos 且保留 dragSplitOffset | 不存在统一“全状态清空” | AC-2.4 |
| R-9 | 边界 | API<10/legacy 合法拖拽 | 累计非负 dragSplitOffset，增加 divider 后间距并平移后续项 | 不调整相邻尺寸、不应用 minSize 钳制 | AC-1.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.5 | API 9/10 与 legacy Touch/Mouse 单测 | 命中、API>=10 相邻尺寸及 API<10 gap-only 位移 |
| VM-2 | AC-2.1~AC-2.2 | API 9/10 最小尺寸矩阵 | 钳制仅适用于 API>=10，内容空间扣减 |
| VM-3 | AC-2.3~AC-2.4 | Hover/PanEnd/OnModifyDone UT | cursor 状态矩阵与字段级清理 |

## API 变更分析

### 新增 API

N/A，`resizeable` 为 API 7 起已有接口。

### 变更/废弃 API

N/A，无 API 变更或废弃。

## 接口规格

### 接口定义

**resizeable(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `resizeable(value: boolean): ColumnSplitAttribute` |
| 返回值 | ColumnSplitAttribute — 当前属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4, AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | boolean | 是 | false | undefined/非法值按 false/reset 路径处理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | true、API>=10 且命中 divider | 在最小高度边界内反向调整相邻子项 | AC-1.2, AC-1.3, AC-2.1 |
| 2 | false 或未命中 | 不调整子项 | AC-1.1, AC-1.4 |
| 3 | true、API<10 且命中 divider | 仅增加非负间距并平移后续项 | AC-1.5 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 10 将 gap-only 拖拽切换为相邻子项反向改尺寸并增加 minSize 钳制，legacy renderer 保留旧模型。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** Dynamic API 7，Static API 23，Builder API 26。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| Pattern 持有状态 | 命中索引、hover 与拖拽状态由 LinearSplitPattern 管理 | AC-1.2 |
| Layout 计算边界 | API>=10 由 LayoutAlgorithm 提供相邻尺寸/minSize 边界；API<10 只应用非负 gap offset | AC-1.5, AC-2.1 |
| 轴向固定 | ColumnSplit 只消费 Y 方向拖拽并使用南北 cursor | AC-1.3, AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次移动按相邻分隔线与边界常数计算 | Trace | `frameworks/core/components_ng/pattern/linear_split/linear_split_pattern.cpp:238-287` |
| 功耗 | 仅交互期间处理事件 | 代码审查 | VM-1 |
| 内存 | 状态随节点释放，无后台缓存 | 生命周期 UT | VM-3 |
| 安全 | 不涉及权限或敏感数据 | API 审查 | VM-1 |
| 可靠性 | 未命中和越界位移不破坏几何 | Fuzz/UT | VM-1, VM-2 |
| 可测试性 | 位置、索引和 cursor 可断言 | 单元测试 | VM-1~VM-3 |
| 自动化维测 | 交互状态可通过事件日志定位 | Trace | AC-2.4 |
| 定界定位 | 事件、Pattern、Layout 三层分离 | 代码审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 以触摸拖拽为主 | 热区仍受最小高度约束 | Touch UT | AC-1.2 |
| 平板 | 支持鼠标 hover/cursor | 南北 resize cursor | Mouse UT | AC-2.3 |
| 折叠屏 | 尺寸变化后重新布局 | 按版本模型重算；普通重布局不等价于清空全部交互字段 | 集成测试 | AC-2.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 拖拽不改变语义顺序 | AC-1.3 |
| 大字体 | 是 | 最小高度可能增大 | AC-2.1 |
| 深色模式 | 否 | 不改变交互几何 | VM-1 |
| 多窗口/分屏 | 是 | 边界随窗口尺寸重算 | AC-2.4 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | Static/Builder 入口需回归 | 兼容性声明 |
| 生态兼容 | 是 | 默认 false 不变 | AC-1.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ColumnSplit 拖拽
  Scenario Outline: 版本化拖拽模型
    Given resizeable 为 true 且命中水平分隔线
    When API 版本为 <version> 并向下拖动
    Then 产生 <result>

    Examples:
      | version | result |
      | 9 | 非负 gap 增长并平移后续子项 |
      | 10 | 相邻高度反向变化并按 minSize 钳制 |
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] API 9/10 拖拽、未命中、最小尺寸、cursor 和字段级状态生命周期明确
- [x] AC、规则、VM 一致
- [x] 未提出实现修改

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "LinearSplitPattern ColumnSplit drag resizeable cursor min size"
  - repo: "openharmony/interface_sdk-js"
    query: "ColumnSplit resizeable API 7"
```

**关键文档：** `05-ui-components/01-layout-components/04-column-split/design.md`
