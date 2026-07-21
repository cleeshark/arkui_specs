# 特性规格

> Func-05-01-07-Feat-01 GridRow 列系统与间距：补录创建、columns/gutter 六档配置、API 20 默认值与继承、单位列宽和子项宽度。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GridRow 列系统与间距 |
| 特性编号 | Func-05-01-07-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

GridRow 是响应式栅格父容器。它保存 xs–xxl 六档 columns 与横纵 gutter，结合内容区宽度计算单位列宽，再按 GridCol 的 span/offset 完成测量。columns 的 canonical 默认值在 API 20 从六档 12 变为 2/4/8/12/12/12，见 `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:104-199,368-411`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | GridRow 创建与容器身份 | 覆盖 FrameNode、Pattern、Property、GridCol 子项约束 |
| ADDED | columns 六档规格 | 覆盖标量、对象、非法值、API 20 默认值和继承 |
| ADDED | gutter 六档规格 | 覆盖统一值、x/y 对象、默认值、前档继承和资源更新 |
| ADDED | 列宽与 GridCol 宽度公式 | 覆盖 padding/border、横向 gutter、span 上限和纵向 gutter |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/07-grid-row/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts` | 已核对 |
| GridRow Model/Property | `frameworks/core/components_ng/pattern/grid_row/grid_row_model_ng.cpp`、`grid_row_layout_property.h` | 已核对 |
| Shared utility | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp` | 已核对 |
| Layout algorithm | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp` | 已核对 |

> 断点选择和事件归 Feat-02；排列、换行、对齐及 RTL 归 Feat-03。本文只在列宽计算所需处引用 GridCol span。

## 用户故事

### US-1: 创建响应式栅格容器

**作为** ArkUI 页面开发者  
**我想要** 创建只以 GridCol 为有效栅格子项的 GridRow  
**以便** 用统一列系统组织响应式内容

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `GridRow()` THEN 创建 GRID_ROW FrameNode、GridRowLayoutPattern、GridRowLayoutProperty 和 GridRowEventHub | 正常 |
| AC-1.2 | WHEN GridRow 测量子列表 THEN 只把 GRID_COL 且具有 GridColLayoutProperty 的节点作为栅格子项 | 边界 |
| AC-1.3 | WHEN 创建时未提供 options THEN columns、gutter、breakpoints、direction 使用当前 API target 的既有默认值 | 正常 |

### US-2: 配置响应式总列数

**作为** 响应式布局开发者  
**我想要** 用标量或 xs–xxl 对象定义总列数  
**以便** 在不同宽度类型下改变栅格密度

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN columns 为整数 n 且 n>0 THEN 六个断点均使用 n | 正常 |
| AC-2.2 | WHEN target <20 且 columns 缺失或无效 THEN 六档默认均为 12；对象缺失档从较小断点向后继承，低档无配置时使用 12 | 边界 |
| AC-2.3 | WHEN target >=20 且 columns 缺失或无效 THEN 默认六档为 2/4/8/12/12/12 | 边界 |
| AC-2.4 | WHEN target >=20 且对象首个有效配置位于 md THEN xs/sm 使用 md 值，后续缺失档继承前一有效档 | 边界 |
| AC-2.5 | WHEN columns<=0 THEN 不以该值做除数，Dynamic 路径按当前 API target 恢复默认列配置 | 异常 |

### US-3: 配置横纵 gutter

**作为** 栅格布局开发者  
**我想要** 分别设置列间距和行间距  
**以便** 保持 GridCol 之间一致的视觉留白

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN gutter 是合法 Length g THEN x/y 六档均使用 g；WHEN 缺失 THEN 六档 x/y 均为 0 | 正常 |
| AC-3.2 | WHEN gutter 为 `{x, y}` 且任一方向是 GridRowSizeOption THEN 该方向 xs 缺失为 0，其余缺失档继承前一档 | 正常 |
| AC-3.3 | WHEN 某个 gutter 值无法解析或为无效负值 THEN 该位置使用 0 或既有解析回退，不产生业务错误码 | 异常 |
| AC-3.4 | WHEN gutter 使用 ResourceObject 且资源配置变化 THEN 重新解析对应档位并标记 GridRow 需要 Measure | 正常 |

### US-4: 计算列宽与子项尺寸

**作为** 布局引擎维护者  
**我想要** 按内容宽度、columns 和 gutter 计算栅格  
**以便** 每个 GridCol 得到可预测宽度和行距

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 当前列数 c>0 THEN 单位列宽为 `(contentWidth - gutterX*(c-1))/c`，contentWidth 排除 GridRow 横向 padding/border | 正常 |
| AC-4.2 | WHEN GridCol 有效 span 为 s THEN 理想宽度为 `columnUnitWidth*s + gutterX*(s-1)` | 正常 |
| AC-4.3 | WHEN GridCol span>columns THEN 有效 span 限制为 columns，不产生超出整行的栅格宽度 | 边界 |
| AC-4.4 | WHEN 产生新栅格行 THEN 总高度在上一行最大高度之外增加当前断点 gutterY | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.3 | R-1~R-3 | 已有实现 | GridRow NG 创建 UT | `frameworks/core/components_ng/pattern/grid_row/grid_row_model_ng.cpp:22-65`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:135-143` |
| AC-2.1~AC-2.5 | R-4~R-7 | 已有实现 | API target 19/20 columns 矩阵 | `frameworks/core/components_v2/grid_layout/grid_container_util_class.h:31-56`；`frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:179-221` |
| AC-3.1~AC-3.4 | R-8~R-10 | 已有实现 | gutter/Resource UT | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:21-102,201-235,377-393`；`frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:246-408` |
| AC-4.1~AC-4.4 | R-11~R-14 | 已有实现 | Measure/Layout 数值 UT | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:122-125`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:120-189` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 GridRow 创建入口 | 创建 GRID_ROW FrameNode，并初始化 Model/Property/Pattern/EventHub | `frameworks/core/components_ng/pattern/grid_row/grid_row_model_ng.cpp:22-65` | AC-1.1 |
| R-2 | 边界 | Measure 遍历子列表 | 非 GRID_COL 或无 GridColLayoutProperty 的子项被跳过 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:135-143` | AC-1.2 |
| R-3 | 行为 | 创建 options 缺失 | Model 写当前版本默认 columns、0 gutter、默认 breakpoint 和 Row | `frameworks/core/components_ng/pattern/grid_row/grid_row_model_ng.cpp:22-34` | AC-1.3 |
| R-4 | 行为 | columns 标量为整数且 >0 | 构造六档同值 GridContainerSize | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:395-411` | AC-2.1 |
| R-5 | 边界 | target <20 且 columns 缺失档 | xs 默认 12，sm..xxl 缺失时继承前档 | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:204-221` | AC-2.2 |
| R-6 | 边界 | target >=20 且未提供有效 columns |使用 2/4/8/12/12/12 默认配置 | `frameworks/core/components_v2/grid_layout/grid_container_util_class.h:31-56`；`interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:395-411` | AC-2.3 |
| R-7 | 边界 | target >=20 且首个有效配置不在 xs |首个有效值回填 xs，之后缺失档继承前一档；全无效时保留版本默认 | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:179-202` | AC-2.4, AC-2.5 |
| R-8 | 行为 | gutter 为统一 Length 或 x/y 六档对象 |分别构造横向/纵向 Gutter；xs 默认 0，其余缺失继承前档 | `frameworks/core/components_v2/grid_layout/grid_container_util_class.h:105-193`；`frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:374-408` | AC-3.1, AC-3.2 |
| R-9 | 异常 | gutter 单项解析失败或无有效值 |以 0vp 作为无效位置的安全回退，不抛业务错误码 | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:246-331` | AC-3.3 |
| R-10 | 恢复 | gutter ResourceObject 配置更新 |重新解析并通过属性更新触发 Measure | `frameworks/core/components_ng/pattern/grid_row/grid_row_model_ng.cpp:36-65`；`frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:246-408` | AC-3.4 |
| R-11 | 行为 | c>0 且得到 contentWidth/gutterX |单位列宽扣除 c-1 个横向 gutter 后除以 c | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:122-125`；`frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:130-177` | AC-4.1 |
| R-12 | 行为 | 测量 span=s 的 GridCol |理想宽度为 s 个单位列宽加 s-1 个 gutterX | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:146-166` | AC-4.2 |
| R-13 | 边界 | GridCol span>columns |effective span 使用两者较小值 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:146-159` | AC-4.3 |
| R-14 | 行为 | offset/span 使子项进入新行 |累计上一行最大高度和一个 gutterY | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:153-189` | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~AC-1.3 | NG Create UT |节点类型、默认 options、有效子项过滤 |
| VM-2 | R-4~R-7, AC-2.1~AC-2.5 | API 19/20 参数化 UT |标量、缺失、0/负数、首个 md |
| VM-3 | R-8~R-10, AC-3.1~AC-3.4 | Gutter/Resource UT |统一值、x/y、六档、配置更新 |
| VM-4 | R-11~R-14, AC-4.1~AC-4.4 |数值 Layout UT |padding、c-1 gutter、span clamp、行间距 |

## API 变更分析

> 本次只补录已有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `GridRow(option?: GridRowOptions)` | Public | gutter、columns、breakpoints、direction | GridRowAttribute | N/A | API 9 创建响应式栅格容器 | AC-1.1~AC-4.4 |
| `GridRowColumnOption` | Public | xs–xxl 可选正整数 | N/A | N/A | API 9 响应式总列数 | AC-2.1~AC-2.5 |
| `GutterOption`/`GridRowSizeOption` | Public | x/y Length 或六档 Length | N/A | N/A | API 9 响应式横纵间距 | AC-3.1~AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `GridRowOptions.columns` 默认/继承 | 变更 | API target 升级至 20 且 columns 缺失或低档未配置 |显式配置需要稳定的 xs–xxl 列数 | AC-2.2~AC-2.4 |

## 接口规格

### 接口定义

**GridRow(option?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `GridRow(option?: GridRowOptions): GridRowAttribute` |
| 返回值 | GridRowAttribute — 创建响应式栅格父容器 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| option | GridRowOptions | 否 | 空 options |有效栅格子项为 GridCol |
| option.columns | number/GridRowColumnOption | 否 | API<20 为 12；API>=20 为 2/4/8/12/12/12 |整数 >0 |
| option.gutter | Length/GutterOption | 否 | 0vp |合法 Length；x/y 可分别响应式 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | columns 标量/对象/非法值 |广播、继承或版本默认 | AC-2.1~AC-2.5 |
| 2 | gutter 标量/x-y 六档/Resource |写六档间距并在配置变化后重测 | AC-3.1~AC-3.4 |
| 3 |固定宽度、columns、gutter、span |按公式得到单位列宽和 GridCol 宽度 | AC-4.1~AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 20 起 columns 默认值和低断点继承改变。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 9。
- **API 版本号策略:** Dynamic API 9；cross-platform API 10；atomic service API 11；API 20 行为分支。

| 版本 | columns 默认 | 缺失低断点 | 证据 |
|------|--------------|------------|------|
| API 9–19 | 12/12/12/12/12/12 |使用 12，后续向前继承 | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:104-120,395-411` |
| API 20+ | 2/4/8/12/12/12 |首个有效高档回填低档 | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:179-202` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 父容器配置 | columns/gutter 只由 GridRow 持有 | AC-2.1, AC-3.1 |
| 子项职责 | GridCol 提供 span/offset/order，不能自行改变总列数 | AC-4.2, AC-4.3 |
| 版本选择 | Create 按 API target 20 选择 columns 解析 | AC-2.2~AC-2.5 |
| Measure 脏标记 | columns/gutter 及资源更新必须触发 Measure | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |不新增指标；六档继承为固定上限 6 次比较 | Trace/代码审查 | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:179-221` |
| 功耗 |无后台任务和轮询 |代码审查 | VM-1~VM-4 |
| 内存 |columns/gutter 使用固定六档结构；Resource 按档持有引用 |内存基线 | `frameworks/core/components_v2/grid_layout/grid_container_util_class.h:37-193` |
| 安全 |无权限或敏感数据 |API 审查 | VM-1 |
| 可靠性 |columns<=0 不进入除零路径，非法 gutter 安全回退 |边界 UT/fuzz | AC-2.5, AC-3.3 |
| 可测试性 |所有公式可用固定尺寸数值断言 |Layout UT | VM-2~VM-4 |
| 自动化维测 |LayoutProperty 可输出 columns/gutter/sizeType |Inspector/Dump | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_property.h:47-65` |
| 定界定位 |区分 SDK、解析、共享 utility 与父算法 |设计审查 | `05-ui-components/01-layout-components/07-grid-row/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | API 20 默认 xs/sm 列数较少 |按当前断点取 2 或 4 列 |窗口宽度矩阵 | AC-2.3 |
| 平板 |通常命中 md/lg |按当前断点取 8 或 12 列 |平板尺寸测试 | AC-2.3 |
| 折叠屏 |折叠/展开可切换断点 |重测后同时切换 columns 和 gutter |折叠态集成测试 | AC-2.4, AC-3.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 |只组织 GridCol 布局，不改变语义节点 | AC-1.2 |
| 大字体 | 是 |内容高度可改变行高，列宽公式不变 | AC-4.4 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |宽度变化后选择新档 columns/gutter | AC-2.4, AC-3.2 |
| 多用户 | 否 |无用户级状态 |
| 版本升级 | 是 |API 20 默认列数必须回归 | AC-2.2, AC-2.3 |
| 生态兼容 | 是 |列宽公式与非法值回退保持既有行为 | AC-2.5, AC-4.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: GridRow 列系统与间距
  Scenario Outline: API target 决定默认小屏列数
    Given GridRow 未配置 columns
    When 应用以 target <target> 在 xs 断点布局
    Then 当前总列数为 <columns>

    Examples:
      | target | columns |
      | 19 | 12 |
      | 20 | 2 |

  Scenario: 计算单位列宽
    Given GridRow 内容宽度为 800px
    And columns 为 12 且 gutterX 为 10px
    When GridRow 测量
    Then 单位列宽为 (800-10*11)/12
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 均使用 WHEN/THEN 并可独立验证
- [x] columns/gutter 与断点/排列职责边界明确
- [x] API 20 默认值和继承有版本矩阵
- [x] 每个 AC 与规则、VM 双向追溯
- [x] 包含 0、负数、span 超 columns 和资源更新边界

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "GridRow columns gutter GridContainerUtils columnUnitWidth API 20"
  - repo: "openharmony/interface_sdk-js"
    query: "GridRowOptions GridRowColumnOption GutterOption API 9 API 20"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/grid_row.d.ts`
- 共享设计：`05-ui-components/01-layout-components/07-grid-row/design.md`
