# 特性规格

> Func-05-01-06-Feat-01 GridCol 创建与响应式占列：补录 GridCol 容器身份、父子约束、span 默认值及 API 20 前后的断点继承。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GridCol 创建与响应式占列 |
| 特性编号 | Func-05-01-06-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

GridCol 是 GridRow 的栅格子项。它把 xs、sm、md、lg、xl、xxl 六档 span 保存到 `GridColLayoutProperty`；GridRow 在测量时选择当前断点、限制占列数并决定子项宽度。公开父子约束见 `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:274-287`，节点和属性实现见 `frameworks/core/components_ng/pattern/grid_col/grid_col_model_ng.cpp:24-58`、`frameworks/core/components_ng/pattern/grid_col/grid_col_layout_property.h:29-75`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | GridCol 创建与节点身份规格 | 覆盖 FrameNode、Pattern、Property、Algorithm 和焦点范围 |
| ADDED | GridRow 子项约束规格 | 覆盖只能放入 GridRow、单子组件及非 GridCol 子项边界 |
| ADDED | span 响应式规格 | 覆盖标量、六档对象、0、非法值、默认值和 API 20 继承 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/06-grid-col/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/gridCol.static.d.ets` | 已核对 |
| NG Model/Property | `frameworks/core/components_ng/pattern/grid_col/grid_col_model_ng.cpp`、`grid_col_layout_property.h` | 已核对 |
| Parent algorithm | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp` | 已核对 |

> 本文档仅补录存量实现，不新增产品能力；SDK 与实现不一致之处只进入风险项。

## 用户故事

### US-1: 创建栅格子项

**作为** ArkUI 应用开发者  
**我想要** 在 GridRow 中创建 GridCol 并承载一个内容子节点  
**以便** 让内容参与响应式栅格布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `GridCol()` THEN 创建 tag 为 GRID_COL 的非原子 FrameNode，并绑定 GridColLayoutPattern 与 GridColLayoutProperty | 正常 |
| AC-1.2 | WHEN Pattern 创建布局算法 THEN 返回纵向 LinearLayoutAlgorithm，并作为可聚焦 Scope 承载内容 | 正常 |
| AC-1.3 | WHEN 应用按公开契约组合组件 THEN GridCol 是 GridRow 的直接子组件且只包含一个内容子组件 | 边界 |
| AC-1.4 | WHEN GridRow 的子列表包含非 GRID_COL 节点 THEN GridRow 测量跳过该节点，不把它计入栅格行 | 异常 |

### US-2: 设置当前断点的占列数

**作为** 响应式页面开发者  
**我想要** 用标量或 xs–xxl 对象设置 span  
**以便** 在不同窗口宽度下控制 GridCol 宽度和可见性

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN span 是非负整数 n THEN 六个断点均使用 n；GridRow 以 `min(n, 当前总列数)` 作为有效占列数 | 正常 |
| AC-2.2 | WHEN span 为 0 THEN GridCol 不参与有效栅格布局，公开契约表现为不渲染 | 边界 |
| AC-2.3 | WHEN span 缺失或 Dynamic 输入为负数/非支持类型 THEN 使用默认占列数 1，且不抛出业务错误码 | 异常 |
| AC-2.4 | WHEN span 大于 GridRow 当前总列数 THEN 有效 span 被限制为总列数，子项宽度不超过整行栅格宽度 | 边界 |

### US-3: 跨 API 版本继承响应式 span

**作为** 维护跨版本应用的开发者  
**我想要** 明确未配置断点的继承规则  
**以便** 在 API target 升级时预测布局变化

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API target 小于 20 且 span 为 `{md:4, lg:8}` THEN xs、sm 使用默认 1，md 为 4，lg/xl/xxl 为 8 | 边界 |
| AC-3.2 | WHEN API target 大于等于 20 且 span 为 `{md:4, lg:8}` THEN xs、sm、md 为 4，lg/xl/xxl 为 8 | 边界 |
| AC-3.3 | WHEN API target 大于等于 20 且对象没有任一有效非负断点 THEN 保持 span 默认值 1 | 异常 |
| AC-3.4 | WHEN GridRow 选择新的 sizeType THEN GridCol 从已补齐的六档 span 中读取对应值并标记当前 SizeType | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.2 | R-1~R-2 | 已有实现 | GridCol NG UT + 代码审查 | `frameworks/core/components_ng/pattern/grid_col/grid_col_model_ng.cpp:24-58`；`frameworks/core/components_ng/pattern/grid_col/grid_col_layout_pattern.h:28-54` |
| AC-1.3~AC-1.4 | R-3~R-4 | 已有实现 | SDK 约束检查 + GridRow layout UT | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:274-287`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:135-143` |
| AC-2.1~AC-2.4 | R-5~R-7 | 已有实现 | 参数矩阵 + 布局 UT | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:133-147`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:146-166` |
| AC-3.1~AC-3.4 | R-8~R-10 | 已有实现 | API 19/20 target 矩阵 | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:88-190,212-237` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 GridCol 创建入口 | 创建 GRID_COL FrameNode 并写 span/offset/order 初值 | Model 创建链见 `frameworks/core/components_ng/pattern/grid_col/grid_col_model_ng.cpp:24-50` | AC-1.1 |
| R-2 | 行为 | Pattern 请求 Property、Algorithm 或 Focus | 返回 GridColLayoutProperty、LinearLayoutAlgorithm 和可聚焦 Scope | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_pattern.h:28-54` | AC-1.2 |
| R-3 | 边界 | 按公开组件树规则使用 GridCol | 只作为 GridRow 子项且只承载一个子组件 | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:274-287` | AC-1.3 |
| R-4 | 异常 | GridRow 遍历到 tag 不是 GRID_COL 的子项 | 跳过该子项，不测量为栅格列 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:135-143` | AC-1.4 |
| R-5 | 行为 | span 为非负数或六档对象 | 解析成 GridContainerSize 并写入 Span 属性，属性触发 Measure | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:111-190`；`frameworks/core/components_ng/pattern/grid_col/grid_col_layout_property.h:54-57` | AC-2.1 |
| R-6 | 边界 | 当前 span 为 0 或大于总列数 | 0 保留为合法公开值；正值在父算法中以总列数为上限 | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:133-147`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:146-159` | AC-2.2, AC-2.4 |
| R-7 | 异常 | Dynamic span 为负数、非对象或对象字段无效 | 用默认 1 替代无效输入，不抛错误码 | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:111-190` | AC-2.3 |
| R-8 | 边界 | target < 20 且低断点缺失 | xs 使用 1，其余缺失档继承前一档 | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:68-86,225-229` | AC-3.1 |
| R-9 | 边界 | target >= 20 且至少一个有效断点 | 首个有效值回填 xs，之后缺失档继承前一档 | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:88-109,152-190` | AC-3.2 |
| R-10 | 异常 | target >= 20 且对象没有有效断点 | ParseSpansNG 保持 GridContainerSize 默认 span 1 | `frameworks/core/components_ng/pattern/grid_col/bridge/arkts_native_grid_col_bridge.cpp:152-190` | AC-3.3, AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | NG 创建/父子组合 UT | tag、Pattern、Property、Algorithm、GridRow 子项过滤 |
| VM-2 | R-5~R-7, AC-2.1~AC-2.4 | span 参数化 Layout UT | 0、1、负数、超过 columns、对象字段 |
| VM-3 | R-8~R-10, AC-3.1~AC-3.4 | API target 19/20 对照测试 | `{md:4,lg:8}` 和全字段无效对象 |
| VM-4 | R-1~R-10, AC-1.1~AC-3.4 | SDK 编译 + 源码追溯 | Dynamic API 9 与六档类型可见性 |

## API 变更分析

> 本次只补录已有 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `GridCol(option?: GridColOptions)` | Public | 可选 span/offset/order | GridColAttribute | N/A | API 9 创建栅格子项 | AC-1.1~AC-1.3 |
| `span(value: number \| GridColColumnOption)` | Public | 非负整数或 xs–xxl 对象 | GridColAttribute | N/A | API 9 设置响应式占列 | AC-2.1~AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `GridColColumnOption` span 继承语义 | 变更 | API target 从 19 升级到 20 且未配置低断点 | 为所有需要稳定表现的断点显式配置 span | AC-3.1, AC-3.2 |

## 接口规格

### 接口定义

**GridCol(option?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `GridCol(option?: GridColOptions): GridColAttribute` |
| 返回值 | GridColAttribute — 创建栅格子项 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| option | GridColOptions | 否 | 空 options | GridCol 应位于 GridRow 下 |
| option.span | number/GridColColumnOption | 否 | 1 | 非负整数；0 合法；对象字段为 xs–xxl |

**span(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `span(value: number \| GridColColumnOption): GridColAttribute` |
| 返回值 | GridColAttribute — 返回当前属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | number/GridColColumnOption | 是 | 1（非法值回退） | 非负整数；0 表示不参与布局/渲染 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 标量 span | 六档取相同值，父容器限制到当前 columns | AC-2.1, AC-2.4 |
| 2 | span=0 或非法值 | 分别执行隐藏语义或回退 1 | AC-2.2, AC-2.3 |
| 3 | 缺低断点对象 | 按 API 20 前后规则补齐 | AC-3.1~AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 20 起只改变 span 的低断点继承方式。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；六档值随 LayoutProperty 存在。
- **最低支持版本:** API 9。
- **API 版本号策略:** Dynamic 以 `@since 9 dynamic` 为基线；cross-platform 自 API 10、atomic service 自 API 11。

| 版本 | 既有行为 | 证据 |
|------|----------|------|
| API 9 | GridCol、GridColOptions、span Dynamic 可用 | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:117-147,189-240` |
| API 10 | 标注 cross-platform | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:43-47` |
| API 11 | 标注 atomic service | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:43-47` |
| API 20 | span 首个有效高断点向低档继承 | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:24-41` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 父算法所有权 | 当前断点、总列数、列宽和最终位置由 GridRow 决定 | AC-2.1, AC-2.4, AC-3.4 |
| 属性分层 | GridCol 仅保存六档 span 与 sizeType，属性变化触发 Measure | AC-2.1, AC-3.4 |
| 组件树约束 | GridCol 必须作为 GridRow 子项并只含一个内容子项 | AC-1.3 |
| 版本分支 | Bridge 按 API target 20 选择 span 继承算法 | AC-3.1~AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增性能指标；span 查询为固定六档取值 | Trace/代码审查 | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_property.h:59-75` |
| 功耗 | 不新增后台任务或定时器 | 代码审查 | VM-1 |
| 内存 | 每个 GridCol 保存固定三个 GridContainerSize 与 sizeType | 内存基线 | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_property.h:54-57` |
| 安全 | 不读取敏感数据、不要求权限 | SDK/代码审查 | VM-4 |
| 可靠性 | 非法 Dynamic 输入回退且不崩溃 | 参数 fuzz | AC-2.3, AC-3.3 |
| 可测试性 | 每项规则可通过固定 columns/target 的布局 UT 观测 | 追溯审查 | VM-1~VM-4 |
| 自动化维测 | Property 可序列化输出 span/offset/order | Inspector/Dump | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_pattern.h:56-63` |
| 定界定位 | 区分 Bridge 解析、GridCol 属性与 GridRow 算法三层 | 源码定位 | `05-ui-components/01-layout-components/06-grid-col/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无组件专有差异 | 由 GridRow 当前 sizeType 选择 xs–xxl 值 | 窗口宽度矩阵 | AC-3.4 |
| 平板 | 无组件专有差异 | 大窗口通常命中较高断点，继承规则不变 | 可变窗口测试 | AC-3.1~AC-3.4 |
| 折叠屏 | 折叠态可触发 sizeType 改变 | 重新 Measure 后读取新档 span | 折叠/展开集成测试 | AC-3.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | GridCol 为 Focus Scope，但 span 不改变声明顺序 | AC-1.2 |
| 大字体 | 是 | 字体只改变内容测量高度，不改变 span 规则 | AC-2.1 |
| 深色模式 | 否 | 不涉及颜色或主题 |
| 多窗口/分屏 | 是 | 窗口变化可改变 GridRow 断点并重新选择 span | AC-3.4 |
| 多用户 | 否 | 无用户级状态 |
| 版本升级 | 是 | API 20 span 继承变化必须回归 | AC-3.1, AC-3.2 |
| 生态兼容 | 是 | 0、非法值和父子约束保持既有契约 | AC-1.3, AC-2.2, AC-2.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: GridCol 创建与响应式占列
  Scenario Outline: API target 决定缺失低断点的 span
    Given GridCol 位于总列数为 12 的 GridRow 中
    And span 配置为 {md:4, lg:8}
    When 应用以 API target <target> 运行在 xs 断点
    Then GridCol 的有效 span 为 <span>

    Examples:
      | target | span |
      | 19 | 1 |
      | 20 | 4 |

  Scenario: span 超过总列数
    Given GridRow 当前总列数为 8
    And GridCol span 为 12
    When GridRow 测量子项
    Then 有效 span 为 8
    And 子项宽度不超过整行栅格宽度
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x] 范围仅包含创建、父子约束、span 与版本继承
- [x] offset/order 详细行为路由到 Feat-02
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 规则均给出可复现输入、可观测结果和边界值

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "GridCol create span GridContainerSize API 20 inheritance GridRow MeasureChildren"
  - repo: "openharmony/interface_sdk-js"
    query: "GridColOptions GridColColumnOption span API 9 API 20"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/grid_col.d.ts`
- 共享设计：`05-ui-components/01-layout-components/06-grid-col/design.md`
