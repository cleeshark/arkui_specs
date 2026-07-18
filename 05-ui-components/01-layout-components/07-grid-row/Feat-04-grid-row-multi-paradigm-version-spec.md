# 特性规格

> Func-05-01-07-Feat-04 GridRow 多范式接口与版本兼容：补录 Dynamic、AttributeModifier、Static、builder/options、内部 ArkUI/CJ ABI 及通道偏差风险。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GridRow 多范式接口与版本兼容 |
| 特性编号 | Func-05-01-07-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

GridRow Dynamic 构造、options 和断点事件自 API 9 可用，`alignItems` 自 API 10 可用，Dynamic Modifier 自 API 12 可用，Static 组件自 API 23 可用，Static options/builder 自 API 26 可用。公开签名以 `interface/sdk-js` 为准；ace_engine 中断点截断、raw direction、Static 扩展枚举和 legacy 空实现仅作为兼容风险。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Dynamic/AttributeModifier 规格 | 覆盖 API 9/10/12、create、set/reset、事件 |
| ADDED | Static 规格 | 覆盖 API 23 构造/属性和 API 26 options/builder |
| ADDED | 内部 ABI 与 legacy 边界 | 覆盖 ArkUI/CJ modifier、旧管线限制、无 Public Native node |
| ADDED | 通道偏差风险 | canonical 契约不被实现宽松/截断行为扩大 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/07-grid-row/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts` | 已核对 |
| Modifier SDK | `interface/sdk-js/api/arkui/GridRowModifier.d.ts`、`GridRowModifier.static.d.ets` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/gridRow.static.d.ets` | 已核对 |
| Dynamic modifier | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_dynamic_modifier.cpp` | 已核对 |
| Static modifier | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_static_modifier.cpp` | 已核对 |
| ArkTS Bridge/Internal ABI | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp`、`frameworks/core/interfaces/arkoala/arkoala_api.h` | 已核对 |

## 用户故事

### US-1: 按 API level 使用 Dynamic 表面

**作为** Dynamic ArkTS 应用开发者  
**我想要** 在支持版本使用 GridRow 构造、事件、对齐和 modifier  
**以便** 避免错误依赖高版本接口

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN API level>=9 THEN Dynamic `GridRow(option?)`、`onBreakpointChange` 和 GridRowOptions 全部字段可见 | 正常 |
| AC-1.2 | WHEN API level>=10 THEN `alignItems(ItemAlign)` 可见且只承诺 Start/Center/End/Stretch | 正常 |
| AC-1.3 | WHEN API level>=12 THEN `GridRowModifier` 可见并通过 `applyNormalAttribute` 应用 GridRowAttribute | 正常 |
| AC-1.4 | WHEN Dynamic modifier reset columns/gutter/breakpoints/direction/align/event THEN 恢复各自 canonical 默认或清除 callback | 边界 |
| AC-1.5 | WHEN target 在 API 20 前后创建或更新 columns THEN 选择对应默认值与继承路径 | 边界 |

### US-2: 使用 Static GridRow

**作为** Static ArkTS 应用开发者  
**我想要** 通过 Static 构造、属性和 builder 使用 GridRow  
**以便** 在 Static 编译模型中获得同一栅格能力

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN API level>=23 THEN Static types、`GridRow(option?, content_?)`、`onBreakpointChange`、`alignItems` 和 attributeModifier 可见 | 正常 |
| AC-2.2 | WHEN Static 属性传入 undefined THEN 对应 generated optional 被清空或执行该属性的 reset 语义 | 边界 |
| AC-2.3 | WHEN API level>=26 THEN `setGridRowOptions(options?)` 和 style builder overload 可见 | 正常 |
| AC-2.4 | WHEN API level<23/26 分别使用 Static 基础表面/扩展表面 THEN SDK 编译拒绝不可见接口 | 边界 |

### US-3: 保持内部 ABI 和旧管线边界

**作为** 框架接口维护者  
**我想要** 区分 NG、legacy、CJ 与 Public SDK  
**以便** 不把内部实现或无效旧管线路径写成公开承诺

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 当前使用 NG Pipeline THEN Dynamic modifier 的 create/set/reset 最终写 GridRowModelNG/Property/EventHub | 正常 |
| AC-3.2 | WHEN 当前使用 legacy Pipeline THEN 多个 dynamic modifier setter 为空实现，该限制只作为兼容风险而不描述为 NG 行为 | 边界 |
| AC-3.3 | WHEN CJUI 获取 GridRow modifier THEN 使用内部 set/reset 槽位；该结构不进入 Public SDK API 清单 | 正常 |
| AC-3.4 | WHEN 检查 Public Native NodeType THEN 不存在 GridRow/GridCol 类型，因此不声明 Native 创建或 GridRow 节点属性 | 边界 |

### US-4: 识别实现偏差而不扩大契约

**作为** 规格审阅者  
**我想要** 把实现宽松或不完整处单列为风险  
**以便** canonical SDK 与运行事实都可追溯

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN Dynamic modifier 收到非递增断点数组 THEN 记录实现可能截断的风险，Public 契约仍为非法值回退默认断点 | 异常 |
| AC-4.2 | WHEN Dynamic direction setter 收到 Row/RowReverse 之外的数字 THEN 记录 raw 转发风险，Public 契约仍为非法值回退 Row | 异常 |
| AC-4.3 | WHEN Static align 转换接受 Auto/Baseline THEN 仅验证 Static 当前通道，不扩大 Dynamic API 10 的四值集合 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | Dynamic SDK compile + modifier UT | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:368-526`；`interface/sdk-js/api/arkui/GridRowModifier.d.ts:24-57` |
| AC-2.1~AC-2.4 | R-6~R-9 | 已有实现 | Static SDK level compile + generated UT | `interface/sdk-js/api/arkui/component/gridRow.static.d.ets:306-392` |
| AC-3.1~AC-3.4 | R-10~R-13 | 已有实现 | Pipeline/ABI 审查 | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_dynamic_modifier.cpp:61-133,327-393`；`interfaces/native/native_node.h:124-141` |
| AC-4.1~AC-4.3 | R-14~R-16 | 已有实现 | 通道差异负向 UT | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:458-532`；`frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_static_modifier.cpp:221-244,368-399` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | API level>=9 编译 Dynamic GridRow |构造、options、breakpoint event 可见 | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:368-507` | AC-1.1 |
| R-2 | 行为 | API level>=10 编译 alignItems |接口可见，公开支持四个 ItemAlign | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:509-526` | AC-1.2 |
| R-3 | 行为 | API level>=12 使用 GridRowModifier |modifier 创建并应用 normal attribute | `interface/sdk-js/api/arkui/GridRowModifier.d.ts:24-57` | AC-1.3 |
| R-4 | 恢复 | Dynamic modifier reset 任一专有状态 |写 columns/gutter/breakpoints/direction/align 默认或清 callback | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_dynamic_modifier.cpp:135-293` | AC-1.4 |
| R-5 | 边界 | target 跨 API 20 设置 columns |Dynamic create/set 使用版本对应默认与继承 | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:212-293,386-415` | AC-1.5 |
| R-6 | 行为 | API level>=23 编译 Static GridRow |Static options/types/attributes/constructor/attributeModifier 可见 | `interface/sdk-js/api/arkui/component/gridRow.static.d.ets:23-375` | AC-2.1 |
| R-7 | 恢复 | Static 专有属性传入 undefined |generated converter 产生空 optional，并由 setter 清除或 reset | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_static_modifier.cpp:245-399` | AC-2.2 |
| R-8 | 行为 | API level>=26 编译 setGridRowOptions/builder |两个 Static 扩展入口可见 | `interface/sdk-js/api/arkui/component/gridRow.static.d.ets:316-357,377-392` | AC-2.3 |
| R-9 | 边界 |低于对应 API level 编译高版本 Static 表面 |SDK 不提供声明，编译期不可用 | `interface/sdk-js/api/arkui/component/gridRow.static.d.ets:306-392` | AC-2.4 |
| R-10 | 行为 | NG Pipeline 请求 dynamic modifier |使用 NG create/set/reset 表并写 FrameNode | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_dynamic_modifier.cpp:135-293,327-393` | AC-3.1 |
| R-11 | 边界 | legacy Pipeline 请求 setter |旧实现中多个 setter/resetter 为空操作 | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_dynamic_modifier.cpp:61-133` | AC-3.2 |
| R-12 | 行为 |请求 CJUI GridRow modifier |返回内部 GridRow set/reset 函数表 | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_dynamic_modifier.cpp:327-393` | AC-3.3 |
| R-13 | 边界 |检索 Public Native NodeType |列表无 GridRow/GridCol；内部 `ArkUIGridRowModifier` 不提升为 Public | `interfaces/native/native_node.h:124-141`；`frameworks/core/interfaces/arkoala/arkoala_api.h:8911-8926` | AC-3.4 |
| R-14 | 异常 |modifier breakpoints 含非递增/不可解析项 |实现可能把不可解析值变 0 并在非递增点截断；Public 仍按默认契约 | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:488-532` | AC-4.1 |
| R-15 | 异常 |Dynamic direction setter 收到任意 number |Bridge 直接把 int32 转交 modifier；该 raw 行为不扩大枚举 | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:458-473` | AC-4.2 |
| R-16 | 边界 |Static align converter 收到 Auto/Baseline |Static 实现可转换，Dynamic SDK 仍只承诺四值 | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_static_modifier.cpp:368-399` | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | API 9/10/12/20 compile + Dynamic UT |可见性、reset、columns 版本分支 |
| VM-2 | R-6~R-9, AC-2.1~AC-2.4 | API 22/23/25/26 Static compile |基础表面、undefined、options/builder |
| VM-3 | R-10~R-13, AC-3.1~AC-3.4 | NG/legacy/CJ/Native 负向检查 |函数槽、空实现、无 Public NodeType |
| VM-4 | R-14~R-16, AC-4.1~AC-4.3 | 通道差异 UT |非递增断点、raw direction、Static 扩展对齐 |

## API 变更分析

> 以下均为已有 API；内部 ABI 不进入 Public 表。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic GridRow/options/event | Public | GridRowOptions/callback | GridRowAttribute | N/A | API 9 Dynamic 表面 | AC-1.1 |
| `alignItems` | Public | ItemAlign 四值 | GridRowAttribute | N/A | API 10 Dynamic 对齐 | AC-1.2 |
| `GridRowModifier` | Public | applyNormalAttribute | void | N/A | API 12 Dynamic modifier | AC-1.3 |
| Static GridRow/attributes | Public | options/content/属性 | GridRowAttribute | N/A | API 23 Static 表面 | AC-2.1 |
| `setGridRowOptions`/builder | Public | options/style | this/GridRowAttribute | N/A | API 26 Static 扩展 | AC-2.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 |本次未新增、变更、废弃接口 |按 API level 与范式选择表面 | AC-1.1~AC-4.3 |

## 接口规格

### 接口定义

**Dynamic GridRow**

| 属性 | 值 |
|------|-----|
| 函数签名 | `GridRow(option?: GridRowOptions): GridRowAttribute` |
| 返回值 | GridRowAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| option | GridRowOptions | 否 |版本默认 options |API 9 Dynamic；columns 在 API 20 分支 |
| modifier | GridRowModifier | 否 |无 |API 12；reset 语义按专有属性 |

**Static GridRow**

| 属性 | 值 |
|------|-----|
| 函数签名 | `GridRow(option?: GridRowOptions, content_?: CustomBuilder): GridRowAttribute` |
| 返回值 | GridRowAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| option | GridRowOptions | 否 | undefined |API 23 Static |
| content_ | CustomBuilder | 否 |空内容 |只承载 GridCol 栅格子项 |
| style | CustomBuilderT<GridRowAttribute> | 是（builder overload） |无 |API 26 staticonly |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 |按 API 9/10/12 使用 Dynamic |相应接口可见并写共享属性模型 | AC-1.1~AC-1.4 |
| 2 |按 API 23/26 使用 Static |基础或扩展表面可见 | AC-2.1~AC-2.4 |
| 3 |legacy/internal/Public Native 检查 |保持实现边界，不扩大 Public 契约 | AC-3.1~AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；各通道差异为既有事实。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 9。
- **API 版本号策略:** Dynamic 9、align 10、modifier 12、columns 行为 20、Static 23、Static options/builder 26。

| API level | 能力 | 证据 |
|-----------|------|------|
| 9 |Dynamic GridRow/options/event | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:368-507` |
| 10 |alignItems | `interface/sdk-js/api/@internal/component/ets/grid_row.d.ts:509-526` |
| 12 |Dynamic GridRowModifier | `interface/sdk-js/api/arkui/GridRowModifier.d.ts:24-57` |
| 20 |columns 默认/继承分支 | `frameworks/core/components_ng/pattern/grid_row/bridge/arkts_native_grid_row_bridge.cpp:212-293,386-415` |
| 23 |Static GridRow | `interface/sdk-js/api/arkui/component/gridRow.static.d.ets:23-375` |
| 26 |Static options/builder | `interface/sdk-js/api/arkui/component/gridRow.static.d.ets:316-392` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| canonical SDK |开放范围和版本只取 interface/sdk-js | AC-1.1~AC-2.4 |
| 共享 NG 状态 |Dynamic/Static 正常路径写 GridRowLayoutProperty/EventHub | AC-1.3, AC-2.2 |
| 通道隔离 |legacy 空实现和 Static 宽松枚举不得改写 Dynamic 契约 | AC-3.2, AC-4.3 |
| ABI 分级 |ArkUI/CJ modifier 是 InnerApi，不是 Public Native | AC-3.3, AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |接口转换不新增布局复杂度 |Trace/代码审查 | VM-1~VM-2 |
| 功耗 |无后台任务、IPC 或定时器 |代码审查 | VM-3 |
| 内存 |modifier 表为静态对象；callback reset 后释放函数对象 |内存/生命周期 UT | `frameworks/core/components_ng/pattern/grid_row/bridge/grid_row_dynamic_modifier.cpp:327-393` |
| 安全 |Public API 无权限；内部指针不暴露 |API 审查 | AC-3.4 |
| 可靠性 |空节点/无效 callback 安全退出 |异常 UT/fuzz | AC-1.4 |
| 可测试性 |版本×范式×属性形成显式测试矩阵 |SDK compile/UT | VM-1~VM-4 |
| 自动化维测 |复用 GridRow Property/EventHub dump 与 callback 计数 |Inspector/Event | VM-1 |
| 定界定位 |SDK、Bridge、Dynamic/Static modifier、legacy 分层 |设计审查 | `05-ui-components/01-layout-components/07-grid-row/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 |无接口表面差异 |按 API level/target 执行同一版本矩阵 |SDK/运行测试 | AC-1.1~AC-2.4 |
| 平板 |无接口表面差异 |Static/Dynamic 写同一 NG 状态 |对照 Layout UT | AC-2.2 |
| 折叠屏 |无接口表面差异 |折叠影响断点，不改变 modifier ABI |折叠集成测试 | AC-1.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 |本 Feat 不改变语义树 |
| 大字体 | 否 |不改变字体属性 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |各范式在断点变化后共享重测链 | AC-1.4 |
| 多用户 | 否 |无用户状态 |
| 版本升级 | 是 |API 9/10/12/20/23/26 均需编译/运行回归 | AC-1.1~AC-2.4 |
| 生态兼容 | 是 |实现宽松处不得扩大公开枚举和 Native 表面 | AC-3.4, AC-4.1~AC-4.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: GridRow 多范式接口与版本兼容
  Scenario Outline: API level 控制表面可见性
    Given 工程 API level 为 <level>
    When 编译 <surface>
    Then 结果为 <result>

    Examples:
      | level | surface | result |
      | 9 | Dynamic GridRow | 可用 |
      | 9 | alignItems | 不可用 |
      | 10 | alignItems | 可用 |
      | 22 | Static GridRow | 不可用 |
      | 23 | Static GridRow | 可用 |
      | 26 | setGridRowOptions | 可用 |

  Scenario: 非递增 modifier 断点不扩大契约
    Given modifier 断点为 320vp、300vp
    When Dynamic modifier 解析该数组
    Then实现结果作为截断风险记录
    But Public 规格仍要求非法数组回退默认断点
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x] Dynamic/Static/legacy/internal ABI 边界清晰
- [x] 未创建或承诺 GridRow Public Native API
- [x] 每个 AC 与规则、VM 双向追溯
- [x] 实现偏差只列风险，不扩大 canonical SDK

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "GridRow dynamic modifier static modifier legacy CJUI Arkoala"
  - repo: "openharmony/interface_sdk-js"
    query: "GridRowModifier GridRow static setGridRowOptions API 12 23 26"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/grid_row.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/gridRow.static.d.ets`
- 共享设计：`05-ui-components/01-layout-components/07-grid-row/design.md`
