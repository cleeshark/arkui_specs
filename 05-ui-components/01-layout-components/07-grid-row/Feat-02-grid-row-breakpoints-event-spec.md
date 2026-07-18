# 特性规格

> Func-05-01-07-Feat-02 GridRow 响应式断点与变更事件：补录默认/自定义断点、WindowSize/ComponentSize 参照、sizeType 选择、尺寸监听和回调。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GridRow 响应式断点与变更事件 |
| 特性编号 | Func-05-01-07-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

GridRow 把参照宽度映射为 xs、sm、md、lg、xl、xxl 六种 sizeType。默认断点数组为 320vp、600vp、840vp，默认参照为 WindowSize；ComponentSize 使用 GridRow 自身内容宽度。公开契约见 `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:237-268,322-366,413-435,488-507`，选择实现见 `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:62-128`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | BreakPoints 配置规格 | 覆盖默认值、严格递增、1–5 个阈值、reference 和非法值 |
| ADDED | 断点选择规格 | 覆盖 WindowSize、ComponentSize、用户/系统/默认优先级 |
| ADDED | 尺寸变化与重测规格 | 覆盖 Pattern surface callback 和当前 sizeType 更新 |
| ADDED | onBreakpointChange 规格 | 覆盖回调值、触发时机、reset 和 ComponentSize 重入限制 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/07-grid-row/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts` | 已核对 |
| Shared utility | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp` | 已核对 |
| Pattern/EventHub | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_pattern.cpp`、`grid_row_event_hub.h` | 已核对 |
| Layout algorithm | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp` | 已核对 |
| ArkTS Bridge | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp` | 已核对 |

> columns/gutter 六档内容归 Feat-01；本文定义选择哪一档以及何时通知应用。

## 用户故事

### US-1: 配置响应式断点

**作为** 响应式页面开发者  
**我想要** 使用默认断点或提供严格递增的自定义断点  
**以便** 控制 GridRow 何时切换栅格配置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN breakpoints 缺失或执行 reset THEN value 使用 320vp/600vp/840vp，reference 使用 WindowSize | 正常 |
| AC-1.2 | WHEN value 是 1–5 个可解析且严格递增的 vp 阈值 THEN 依次划分 xs 到最多 xxl 的 sizeType | 正常 |
| AC-1.3 | WHEN value 为空、超过 5 项、包含不可解析值或非递增 THEN canonical 行为回退默认断点 | 异常 |
| AC-1.4 | WHEN reference 缺失或非法 THEN 使用 WindowSize；WHEN 为 ComponentSize THEN 使用组件宽度 | 边界 |

### US-2: 按正确参照选择 sizeType

**作为** 在窗口和嵌套容器中复用组件的开发者  
**我想要** 选择窗口宽度或组件宽度作为断点参照  
**以便** 同一 GridRow 在不同承载环境中得到合适列配置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN reference=WindowSize THEN 断点比较使用当前页面/显示窗口宽度，而不是 GridRow 局部内容宽度 | 正常 |
| AC-2.2 | WHEN reference=ComponentSize THEN 断点比较使用 GridRow 内容区宽度，并扣除布局中相关 padding/border 影响 | 正常 |
| AC-2.3 | WHEN 存在合法用户自定义断点 THEN 优先使用用户值；否则按系统栅格配置、默认 320/600/840 的顺序降级 | 边界 |
| AC-2.4 | WHEN 参照宽度依次跨过 n 个阈值 THEN 当前 sizeType 为对应的第 n+1 档，低于第一个阈值时为 xs | 正常 |

### US-3: 响应尺寸变化并通知断点

**作为** ArkUI 应用开发者  
**我想要** 在语义断点真正变化时收到一次回调  
**以便** 更新与断点相关但不参与 GridRow 布局的业务状态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 窗口或组件尺寸变化可能改变参照宽度 THEN GridRow Pattern 标记节点需要重新 Measure | 正常 |
| AC-3.2 | WHEN Measure/Layout 得到的新 sizeType 与旧值不同 THEN 更新 LayoutProperty 并回调对应字符串 xs/sm/md/lg/xl/xxl | 正常 |
| AC-3.3 | WHEN 尺寸变化但仍处于同一 sizeType THEN 不重复触发 onBreakpointChange | 边界 |
| AC-3.4 | WHEN callback 为 undefined/null/非函数或执行 reset THEN 非 JSView modifier 路径移除既有 callback，之后不通知 | 边界 |
| AC-3.5 | WHEN reference=ComponentSize 且 callback 内动态修改 GridRow 自身 padding/margin THEN 该用法不受推荐，应用不得依赖单次稳定回调次数 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | BreakPoints 参数矩阵 | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:322-366`；`frameworks/core/components_v2/grid_layout/grid_container_util_class.h:195-219` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Window/Component/System mock UT | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:62-128`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:279-341` |
| AC-3.1~AC-3.3 | R-9~R-10 | 已有实现 | resize/layout/event UT | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_pattern.cpp:22-70`；`frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:254-277` |
| AC-3.4~AC-3.5 | R-11~R-12 | 已有实现 | callback reset/reentrancy UT | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:488-507`；`frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:625-680` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | breakpoints 缺失或 reset | value 为 320/600/840vp，reference 为 WindowSize | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:334-366`；`frameworks/core/components_v2/grid_layout/grid_container_util_class.h:195-219` | AC-1.1 |
| R-2 | 行为 | value 含 1–5 个严格递增合法阈值 |按数组顺序保存用户断点并标记 userDefine | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:295-331` | AC-1.2 |
| R-3 | 异常 | value 为空、长度>5、解析失败或非递增 | canonical 使用默认断点；modifier 截断差异仅列风险 | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:334-350`；`frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:488-532` | AC-1.3 |
| R-4 | 边界 | reference 缺失/非法或显式 ComponentSize |前者 WindowSize，后者 ComponentSize | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:237-268,352-365` | AC-1.4 |
| R-5 | 行为 | reference=WindowSize |读取页面/显示窗口可用宽度，浮窗版本细节沿用实现 | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:62-93` | AC-2.1 |
| R-6 | 行为 | reference=ComponentSize |使用 GridRow 可用组件宽度决定断点 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:279-320` | AC-2.2 |
| R-7 | 边界 |断点来源存在用户、系统或默认候选 |选择优先级为用户 > 系统 > 默认 | `frameworks/core/components_ng/pattern/gridlayout/grid_container_utils.cpp:115-128` | AC-2.3 |
| R-8 | 行为 |宽度跨越 n 个有序阈值 |sizeType 选择第 n+1 档，未跨阈值为 xs | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:279-341` | AC-2.4 |
| R-9 | 行为 |surface size change callback 触发 |Pattern 标记 Measure dirty，后续重新解析 sizeType | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_pattern.cpp:22-70` | AC-3.1 |
| R-10 | 行为 |Layout 比较新旧 sizeType |仅变化时更新属性并通过 EventHub 回调字符串 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_algorithm.cpp:254-277`；`frameworks/core/components_ng/pattern/grid_row/grid_row_event_hub.h:24-44` | AC-3.2, AC-3.3 |
| R-11 | 恢复 |callback 无效或 reset |非 JSView modifier 清除 EventHub callback；显式 reset 也清除 | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:625-680` | AC-3.4 |
| R-12 | 边界 |ComponentSize callback 内修改自身 padding/margin |SDK 标注为不推荐；回调可能重新改变参照宽度 | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:488-507` | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | BreakPoints 参数 UT |默认、1/3/5 项、0/6 项、非递增、reference |
| VM-2 | R-5~R-8, AC-2.1~AC-2.4 | Pipeline/Component mock UT |两种参照、来源优先级、阈值等于边界 |
| VM-3 | R-9~R-10, AC-3.1~AC-3.3 | resize + event UT |同档不回调、跨档只回调一次、六档字符串 |
| VM-4 | R-11~R-12, AC-3.4~AC-3.5 | callback reset/reentrancy UT |非函数、undefined、ComponentSize 自身尺寸反馈 |

## API 变更分析

> 本次只补录已有 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `BreakpointsReference` | Public | WindowSize/ComponentSize | N/A | N/A | API 9 指定断点参照 | AC-1.4, AC-2.1, AC-2.2 |
| `BreakPoints` | Public | value 字符串数组、reference | N/A | N/A | API 9 定义响应式断点 | AC-1.1~AC-2.4 |
| `onBreakpointChange(callback)` | Public | 接收断点字符串的函数 | GridRowAttribute | N/A | API 9 监听 sizeType 变化 | AC-3.2~AC-3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 |默认断点和两种 reference 自 API 9 保持 |无需迁移；避免 ComponentSize 回调修改自身 padding/margin | AC-1.1, AC-3.5 |

## 接口规格

### 接口定义

**GridRowOptions.breakpoints**

| 属性 | 值 |
|------|-----|
| 函数签名 | `breakpoints?: BreakPoints` |
| 返回值 | N/A — GridRow 构造 options 字段 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | Array<string> | 否 | ["320vp","600vp","840vp"] | 1–5 项、可解析、严格递增 |
| reference | BreakpointsReference | 否 | WindowSize | WindowSize 或 ComponentSize |

**onBreakpointChange(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onBreakpointChange(callback: (breakpoints: string) => void): GridRowAttribute` |
| 返回值 | GridRowAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.2~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | (breakpoints:string)=>void | 是 | 无 callback |参数值只为 xs/sm/md/lg/xl/xxl |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 |合法/非法断点 |保存用户值或回退默认 | AC-1.1~AC-1.3 |
| 2 |WindowSize/ComponentSize |按对应参照选择 sizeType | AC-2.1~AC-2.4 |
| 3 |跨档/同档尺寸变化 |分别回调一次或不回调 | AC-3.1~AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；本 Feat 不涉及 API 20 columns 语义。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 9。
- **API 版本号策略:** BreakPoints、reference 和回调均 `@since 9 dynamic`；cross-platform 自 API 10，atomic service 自 API 11。

| 默认项 | 值 | 证据 |
|--------|----|------|
| value | 320vp/600vp/840vp | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:334-350` |
| reference | WindowSize | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:352-365` |
| callback value | xs/sm/md/lg/xl/xxl | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:488-507` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 单一 sizeType | GridRow columns/gutter 与所有 GridCol 属性必须共享当前 sizeType | AC-2.4, AC-3.2 |
| 参照一致性 |断点选择和事件回调必须使用同一个 reference width | AC-2.1, AC-2.2 |
| 事件后置 |回调只在布局得到新 sizeType 后触发 | AC-3.2, AC-3.3 |
| 生命周期 |EventHub 持有 callback，reset 后不得再次调用 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |最多比较 5 个断点；同档尺寸变化不触发业务回调 | Trace/事件计数 | AC-3.3 |
| 功耗 |无轮询；只响应 surface/layout 变化 |代码审查 | `frameworks/core/components_ng/pattern/grid_row/grid_row_layout_pattern.cpp:22-70` |
| 内存 |断点数组最大 5 项，EventHub 保存一个 callback |内存审查 | `frameworks/core/components_ng/pattern/grid_row/grid_row_event_hub.h:24-44` |
| 安全 |回调无权限和敏感数据 |API 审查 | VM-4 |
| 可靠性 |非法断点有默认降级，callback reset 后安全静默 |异常 UT | AC-1.3, AC-3.4 |
| 可测试性 |窗口/组件宽度和 callback 次数均可注入/计数 |Mock Pipeline UT | VM-1~VM-4 |
| 自动化维测 |sizeType 和断点属性可通过 Property/回调观察 |Inspector/Event | AC-3.2 |
| 定界定位 |区分尺寸监听、断点选择、布局更新和事件四层 |设计审查 | `05-ui-components/01-layout-components/07-grid-row/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 |通常处于 xs/sm |以真实参照宽度为准，不按设备标签硬编码 |窗口尺寸测试 | AC-2.4 |
| 平板 |通常处于 md/lg |可使用 WindowSize 或局部 ComponentSize |嵌套容器测试 | AC-2.1, AC-2.2 |
| 折叠屏 |折叠/展开可连续跨断点 |每次真正跨档触发对应 callback |状态切换集成测试 | AC-3.1~AC-3.3 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 |断点事件不改变语义节点 |
| 大字体 | 是 |字体可能改变组件内容但断点只比较宽度 | AC-2.2 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |主要触发源；WindowSize 跨档后重测并回调 | AC-2.1, AC-3.1 |
| 多用户 | 否 |无用户状态 |
| 版本升级 | 是 |浮窗/窗口获取实现有版本分支，公开断点契约不变 | AC-2.1 |
| 生态兼容 | 是 |callback 次数和默认断点不能被像素级变化放大 | AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: GridRow 响应式断点与变更事件
  Scenario: 默认断点从 xs 切换到 sm
    Given GridRow 使用默认 WindowSize 断点
    And 当前窗口宽度为 319vp 且 sizeType 为 xs
    When 窗口宽度变为 320vp 并完成布局
    Then sizeType 变为 sm
    And onBreakpointChange 收到 "sm" 一次

  Scenario: 同一断点内改变宽度
    Given 当前 sizeType 为 md
    When reference width 在 650vp 与 700vp 之间变化
    Then GridRow 可以重新测量
    But onBreakpointChange 不重复触发
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x] 断点选择与 columns/gutter 内容边界明确
- [x] callback 生命周期与 ComponentSize 重入限制明确
- [x] 每个 AC 与规则、VM 双向追溯
- [x] 实现截断差异仅列风险，不替换 canonical 默认行为

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "GridRow breakpoint WindowSize ComponentSize GridContainerUtils onBreakpointChange"
  - repo: "openharmony/interface_sdk-js"
    query: "BreakPoints BreakpointsReference GridRow onBreakpointChange API 9"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/grid_row.d.ts`
- 共享设计：`05-ui-components/01-layout-components/07-grid-row/design.md`
