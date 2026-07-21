# 特性规格

> Func-05-01-07-Feat-03 GridRow 排列、换行、对齐与 RTL：补录 order 稳定排序、span/offset 分行、Row/RowReverse、alignItems/alignSelf 和布局方向组合。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GridRow 排列、换行、对齐与 RTL |
| 特性编号 | Func-05-01-07-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

GridRow 在当前断点先按 GridCol order 稳定排序，再根据 span/offset 把子项分组为行，按每行最大高度执行 Start/Center/End/Stretch 交叉轴对齐，最后把 GridRowDirection 与 RTL 组合成是否反向定位。公开方向和换行规则见 `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:270-320`，对齐契约见 `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:509-526`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 子项排序和分行规格 | 覆盖 order、span 上限、offset、跨行、非 GridCol 跳过 |
| ADDED | 行高与交叉轴对齐规格 | 覆盖 Start/Center/End/Stretch 与 alignSelf 优先级 |
| ADDED | direction 与 RTL 规格 | 覆盖 Row/RowReverse、LTR/RTL 异或和最终镜像 |
| ADDED | 特殊测量边界 | 覆盖 match-parent 子项和 LayoutPolicy 既有路径 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/07-grid-row/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts` | 已核对 |
| GridRow algorithm | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp` | 已核对 |
| GridRow property/model | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_property.h`、`grid_row_model_ng.cpp` | 已核对 |
| GridCol property | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_property.h` | 已核对 |
| Bridge | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp` | 已核对 |

> GridCol span/offset/order 的输入和继承归 05-01-06；本文定义 GridRow 如何消费当前断点值。

## 用户故事

### US-1: 排序并把 GridCol 分配到栅格行

**作为** 响应式页面开发者  
**我想要** GridRow 按 order、span 和 offset 排列子项  
**以便** 获得稳定且可预测的自动换行

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN GridRow 开始测量 THEN 先按当前 sizeType 的 order 升序稳定排序，同 order 保持代码顺序 | 正常 |
| AC-1.2 | WHEN 子项不是 GRID_COL 或没有 GridColLayoutProperty THEN 跳过该子项，不占列也不形成行高 | 异常 |
| AC-1.3 | WHEN 单个 GridCol span 大于当前 columns THEN 有效 span 限制为 columns | 边界 |
| AC-1.4 | WHEN 当前行剩余列不足以容纳 offset+span THEN 子项进入后续行；大 offset 可跨越多行 | 边界 |
| AC-1.5 | WHEN 一行结束 THEN 该行高度取所有有效 GridCol margin frame height 的最大值，下一行在其后增加 gutterY | 正常 |

### US-2: 对齐同一栅格行内的 GridCol

**作为** 页面设计者  
**我想要** 在不同高度的 GridCol 之间设置垂直对齐  
**以便** 保持行内内容的视觉秩序

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN alignItems 未设置或非法且运行版本>=API 10 THEN 使用 ItemAlign.Start | 异常 |
| AC-2.2 | WHEN alignItems 为 Start/Center/End THEN GridCol 在本行最大高度内分别位于顶部/居中/底部 | 正常 |
| AC-2.3 | WHEN alignItems=Stretch 且 GridCol 没有覆盖条件 THEN 按本行最大高度重新测量/铺满交叉轴 | 正常 |
| AC-2.4 | WHEN GridCol 同时设置 alignSelf THEN alignSelf 优先于 GridRow alignItems | 边界 |
| AC-2.5 | WHEN 一行只有一个 GridCol THEN Start/Center/End 不改变其行高，Stretch 仍服从显式尺寸约束 | 边界 |

### US-3: 组合 RowDirection 与 RTL

**作为** 国际化页面开发者  
**我想要** GridRow 在 LTR/RTL 下正确解释 Row 与 RowReverse  
**以便** 同一界面在双向语言中保持逻辑反向关系

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN direction 缺失 THEN 使用 GridRowDirection.Row；公开值只支持 Row 和 RowReverse | 正常 |
| AC-3.2 | WHEN direction=Row 且布局方向=LTR THEN 不反向；WHEN direction=RowReverse 且 LTR THEN 反向 | 正常 |
| AC-3.3 | WHEN direction=Row 且布局方向=RTL THEN 反向；WHEN direction=RowReverse 且 RTL THEN 不反向 | 正常 |
| AC-3.4 | WHEN 执行反向定位 THEN 保持 Measure 得到的行分组、span 和 order，只镜像每行的最终水平位置 | 边界 |

### US-4: 处理特殊布局策略子项

**作为** 布局引擎维护者  
**我想要** GridRow 对 match-parent/LayoutPolicy 子项使用专用测量路径  
**以便** 避免父子尺寸互相依赖导致错误结果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 子列表存在高度 match-parent GridCol THEN 先走非 match-parent 子项测量路径以确定可用父高度，再重测依赖子项 | 边界 |
| AC-4.2 | WHEN GridRow 自身使用非 NO_MATCH LayoutPolicy THEN 在普通测量结果上按策略更新最终自身尺寸 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | order/span/offset Layout UT | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:44-80,120-189,587-599` |
| AC-2.1~AC-2.5 | R-6~R-9 | 已有实现 |行高/对齐参数 UT | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:192-251`；`frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:419-455` |
| AC-3.1~AC-3.4 | R-10~R-12 | 已有实现 | direction × RTL 矩阵 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:344-394,442-490` |
| AC-4.1~AC-4.2 | R-13~R-14 | 已有实现 | LayoutPolicy/match-parent UT | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:129-134,523-585,602-703` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Measure 获取子列表 |按当前 sizeType order stable sort | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:120-126,587-599` | AC-1.1 |
| R-2 | 异常 |子项 tag/Property 不是 GridCol |continue 跳过，不参与栅格行 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:135-143` | AC-1.2 |
| R-3 | 边界 | GridCol span>columns |effective span 为 min(span, columns) | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:146-159` | AC-1.3 |
| R-4 | 边界 |剩余列小于 offset+span |按 offset 与总列数计算至少一次换行；大 offset 可增加多行 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:44-80` | AC-1.4 |
| R-5 | 行为 |完成一行子项测量 |currentRowHeight 取最大子项高度；换行累计高度和 gutterY | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:153-189` | AC-1.5 |
| R-6 | 异常 | alignItems 输入不是 Start/Center/End/Stretch |API 10+ Dynamic Bridge 写 Start；非数字 reset | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:419-455` | AC-2.1 |
| R-7 | 行为 |行内 alignment 为 Start/Center/End |依据行高与子项高度计算 0、差值/2 或差值的纵向偏移 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:192-251` | AC-2.2, AC-2.5 |
| R-8 | 行为 |行内 alignment 为 Stretch |对可拉伸子项按行高更新约束并重新 Measure | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:192-251` | AC-2.3 |
| R-9 | 边界 | GridCol alignSelf 有值 |使用子项值覆盖 GridRow alignItems | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:509-526`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:192-208` | AC-2.4 |
| R-10 | 行为 | direction 缺失 |使用 Row；公开枚举只含 Row/RowReverse | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:270-320,437-450` | AC-3.1 |
| R-11 | 行为 |组合 direction 与 layoutDirection |effective reverse 为 `(RowReverse && LTR) || (Row && RTL)` | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:344-355` | AC-3.2, AC-3.3 |
| R-12 | 边界 | effective reverse 为真 |布局阶段镜像每行水平起点和子项推进方向，不重建 Measure 行分组 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:357-394,442-490` | AC-3.4 |
| R-13 | 边界 |存在高度 MATCH_PARENT 子项 |进入 MeasureNonMatchParentChildren 专用路径后处理依赖尺寸 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:129-134,602-703` | AC-4.1 |
| R-14 | 行为 | GridRow 自身 LayoutPolicy 非 NO_MATCH |调用 MeasureSelfByLayoutPolicy 更新理想尺寸 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:84-117,523-585` | AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | Layout UT |stable order、非 GridCol、span clamp、offset 跨行、最大行高 |
| VM-2 | R-6~R-9, AC-2.1~AC-2.5 | align 参数化 UT |四种支持值、非法值、alignSelf、显式高度 |
| VM-3 | R-10~R-12, AC-3.1~AC-3.4 | 2×2 direction/RTL UT |Row/RowReverse × LTR/RTL 最终 offset |
| VM-4 | R-13~R-14, AC-4.1~AC-4.2 | LayoutPolicy UT |高度 match-parent、父 wrap/fix/match 策略 |

## API 变更分析

> 本次只补录已有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `GridRowDirection` | Public | Row/RowReverse | N/A | N/A | API 9 控制水平排列方向 | AC-3.1~AC-3.4 |
| `GridRowOptions.direction` | Public | GridRowDirection | N/A | N/A |构造时设置 direction | AC-3.1~AC-3.4 |
| `alignItems(value: ItemAlign)` | Public | Start/Center/End/Stretch | GridRowAttribute | N/A | API 10 设置行内垂直对齐 | AC-2.1~AC-2.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 |方向和对齐沿用既有语义 |只使用公开支持的 Row/RowReverse 和四种 ItemAlign | AC-2.1, AC-3.1 |

## 接口规格

### 接口定义

**GridRowOptions.direction**

| 属性 | 值 |
|------|-----|
| 函数签名 | `direction?: GridRowDirection` |
| 返回值 | N/A — 构造 options 字段 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| direction | GridRowDirection | 否 | Row |仅 Row、RowReverse |

**alignItems(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `alignItems(value: ItemAlign): GridRowAttribute` |
| 返回值 | GridRowAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ItemAlign | 是 | Start |支持 Start/Center/End/Stretch；子项 alignSelf 优先 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 |order/span/offset 组合 |稳定排序并自动分行 | AC-1.1~AC-1.5 |
| 2 |父/子对齐组合 |alignSelf 覆盖父值，Stretch 必要时重测 | AC-2.1~AC-2.5 |
| 3 |direction × RTL |按异或关系决定最终镜像 | AC-3.1~AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；本 Feat 记录既有方向、换行和对齐。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** direction/换行为 API 9；alignItems 为 API 10。
- **API 版本号策略:** 以 canonical SDK `@since 9 dynamic` 和 `@since 10 dynamic` 为准。

| API | 默认/边界 | 证据 |
|-----|-----------|------|
| direction | Row；只支持 Row/RowReverse | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:270-320,437-450` |
| alignItems | Start；支持 Start/Center/End/Stretch | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:509-526` |
| span/offset 换行 |超过 columns 自动换行，单项 span 受上限 | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:278-290` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 当前断点一致 |order/span/offset 使用同一 sizeType | AC-1.1, AC-1.3 |
| Measure/Layout 分层 |Measure 建行，Layout 负责 direction/RTL 最终位置 | AC-3.4 |
| 对齐覆盖 |child alignSelf 优先于父 alignItems | AC-2.4 |
| 容器边界 |只有 GridCol 进入栅格算法 | AC-1.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |不新增指标；一次排序后线性测量/布局 |Trace/现有基准 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:120-189` |
| 功耗 |无异步任务或轮询 |代码审查 | VM-1~VM-4 |
| 内存 |行分组和偏移仅保留单次算法状态 |内存基线 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:168-188` |
| 安全 |无权限和敏感数据 |API 审查 | VM-3 |
| 可靠性 |非法对齐回退 Start；非 GridCol 安全跳过 |异常 UT/fuzz | AC-1.2, AC-2.1 |
| 可测试性 |direction/RTL 形成有限 4 组合矩阵 |参数化 UT | VM-3 |
| 自动化维测 |可检查每个 GridCol frame offset/size |Layout Inspector | VM-1~VM-4 |
| 定界定位 |排序/测量/对齐/镜像分别有源码区段 |设计审查 | `05-ui-components/01-layout-components/07-grid-row/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 |无算法差异 |较少 columns 可能产生更多换行 |手机宽度 Layout UT | AC-1.4 |
| 平板 |无算法差异 |较多 columns 可能减少换行 |平板宽度 Layout UT | AC-1.3~AC-1.5 |
| 折叠屏 |断点切换可重建行分组 |每次 Measure 使用新 sizeType 后再应用 RTL |折叠/展开 + RTL 测试 | AC-1.1, AC-3.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 |视觉 order/direction 不重建声明树，需回归焦点/阅读顺序 | AC-1.1, AC-3.4 |
| 大字体 | 是 |字体改变 GridCol 高度并影响行高/对齐 | AC-1.5, AC-2.2 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |断点变化后重新分行 | AC-1.1~AC-1.5 |
| 多用户 | 否 |无用户状态 |
| 版本升级 | 是 |API 10 起非法 alignItems 回退 Start | AC-2.1 |
| 生态兼容 | 是 |RTL 异或和 stable order 必须保持 | AC-1.1, AC-3.2, AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: GridRow 排列、换行、对齐与 RTL
  Scenario Outline: direction 与 RTL 组合
    Given GridRow direction 为 <direction>
    And layoutDirection 为 <layout>
    When GridRow 完成布局
    Then 行内视觉排列反向状态为 <reversed>

    Examples:
      | direction | layout | reversed |
      | Row | LTR | false |
      | RowReverse | LTR | true |
      | Row | RTL | true |
      | RowReverse | RTL | false |

  Scenario: alignSelf 覆盖 Stretch
    Given GridRow alignItems 为 Stretch
    And 某个 GridCol alignSelf 为 Center
    When 该行完成对齐
    Then该 GridCol 使用 Center
    And其他未覆盖子项继续使用 Stretch
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 均使用 WHEN/THEN，可独立测试
- [x] GridRow 消费规则与 GridCol 输入规格不重复
- [x] direction/RTL 四组合与对齐覆盖均明确
- [x] 每个 AC 与规则、VM 双向追溯
- [x] 包含非 GridCol、span 上限、大 offset 和 match-parent 边界

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "GridRow layout order span offset alignItems alignSelf RTL RowReverse"
  - repo: "openharmony/interface_sdk-js"
    query: "GridRowDirection GridRow alignItems ItemAlign API 9 API 10"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/grid_row.d.ts`
- 共享设计：`05-ui-components/01-layout-components/07-grid-row/design.md`
