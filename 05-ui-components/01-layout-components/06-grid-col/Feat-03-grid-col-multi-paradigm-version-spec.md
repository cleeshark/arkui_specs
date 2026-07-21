# 特性规格

> Func-05-01-06-Feat-03 GridCol 多范式接口与版本兼容：补录 Dynamic、AttributeModifier、Static、builder/options 及内部 modifier ABI 的版本和 reset 边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GridCol 多范式接口与版本兼容 |
| 特性编号 | Func-05-01-06-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

GridCol 的 Dynamic 组件和属性自 API 9 可用，Dynamic AttributeModifier 类型自 API 12 可用，Static 组件自 API 23 可用，`setGridColOptions` 和 builder overload 自 API 26 可用。各入口最终写入相同的 GridColLayoutProperty，但参数表示、undefined/reset 和非负校验路径不同。canonical 声明见 `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:189-287`、`interface/sdk-js/api/arkui/GridColModifier.d.ts:24-57` 和 `interface/sdk-js/api/arkui/component/gridCol.static.d.ets:123-219`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Dynamic 与 modifier 规格 | 覆盖 API 9/12、create、set/reset 和 API target 20 分支 |
| ADDED | Static 规格 | 覆盖 API 23 属性/构造、undefined 与 API 26 options/builder |
| ADDED | 内部 ABI 与公开边界 | 覆盖 ArkUI/CJ modifier，并声明不存在公开 Native GridCol node type |
| ADDED | 通道风险矩阵 | 只记录实现差异，不把偏差写成 canonical API 承诺 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/06-grid-col/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts` | 已核对 |
| Modifier SDK | `interface/sdk-js/api/arkui/GridColModifier.d.ts`、`GridColModifier.static.d.ets` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/gridCol.static.d.ets` | 已核对 |
| Dynamic/Static modifier | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp`、`grid_col_static_modifier.cpp` | 已核对 |
| Internal ABI | `frameworks/core/interfaces/arkoala/arkoala_api.h` | 已核对 |

## 用户故事

### US-1: 使用 Dynamic 与 AttributeModifier

**作为** ArkTS Dynamic 范式开发者  
**我想要** 在正确 API level 使用 GridCol 及增量属性修改  
**以便** 获得与构造 options 一致的响应式属性

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN API level 大于等于 9 THEN Dynamic `GridCol(option?)`、`span`、`gridColOffset`、`order` 可见并返回 GridColAttribute | 正常 |
| AC-1.2 | WHEN API level 大于等于 12 THEN `GridColModifier` 可构造并通过 `applyNormalAttribute` 应用 GridColAttribute 修改 | 正常 |
| AC-1.3 | WHEN Dynamic modifier reset span/offset/order THEN 分别恢复六档 1/0/0，并触发后续测量 | 边界 |
| AC-1.4 | WHEN target 在 API 20 前后设置缺低断点 span THEN modifier 与 Dynamic Bridge 分别使用对应版本的继承分支 | 边界 |

### US-2: 使用 Static GridCol

**作为** ArkTS Static 范式开发者  
**我想要** 通过组件构造、属性或 options 更新 GridCol  
**以便** 在 Static 编译模型中使用相同布局能力

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN API level 大于等于 23 THEN Static `GridCol(option?, content_?)` 和 span/offset/order/attributeModifier 可见 | 正常 |
| AC-2.2 | WHEN Static 属性收到有效非负标量或对象 THEN 转换为 GridContainerSize 并写入对应 optional 属性 | 正常 |
| AC-2.3 | WHEN Static 属性任一断点为负数 THEN 非负校验清空该属性 optional，不保留部分合法断点 | 异常 |
| AC-2.4 | WHEN API level 大于等于 26 THEN `setGridColOptions(options?)` 和 style builder overload 可见；options 缺失时清空三个 Static optional | 边界 |

### US-3: 区分内部 ABI 与公开 Native API

**作为** 接口维护者  
**我想要** 准确区分可发布 API 和内部节点 modifier  
**以便** 不对应用开发者承诺不存在的 Native GridCol 接口

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN ace_engine 注册 GridCol dynamic modifier THEN 表中包含 create、span、offset、order 及 reset，并依据当前管线选择 NG/legacy 实现 | 正常 |
| AC-3.2 | WHEN CJUI 请求 GridCol modifier THEN 仅暴露 set/reset span、offset、order，不把内部结构提升为 SDK Public API | 正常 |
| AC-3.3 | WHEN 检查公开 ArkUI Native node type THEN 列表没有 GridRow/GridCol，因此本 Feat 不声明 Native 创建或节点属性接口 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | SDK level compile + Dynamic modifier UT | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:189-287`；`interface/sdk-js/api/arkui/GridColModifier.d.ts:24-57` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Static compile + generated modifier UT | `interface/sdk-js/api/arkui/component/gridCol.static.d.ets:123-219`；`frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_static_modifier.cpp:35-45,111-181` |
| AC-3.1~AC-3.3 | R-9~R-11 | 已有实现 | ABI 表审查 + Native SDK 负向检查 | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:252-300`；`interfaces/native/native_node.h:124-141` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | API level >= 9 编译 Dynamic 调用 | GridCol 构造和三个专有属性可见 | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:189-287` | AC-1.1 |
| R-2 | 行为 | API level >= 12 使用 GridColModifier | modifier 创建后由 applyNormalAttribute 写属性 | `interface/sdk-js/api/arkui/GridColModifier.d.ts:24-57` | AC-1.2 |
| R-3 | 恢复 | Dynamic modifier 执行 resetSpan/resetOffset/resetOrder | 写回 GridContainerSize 1/0/0 | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:197-240` | AC-1.3 |
| R-4 | 边界 | Dynamic modifier 设置 span 且 target 跨 API 20 | target <20 使用默认 1+前档继承；target >=20 首个有效值回填低档 | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:86-104,139-180` | AC-1.4 |
| R-5 | 行为 | API level >=23 编译 Static GridCol | Static 类型、属性、构造和 attributeModifier 可见 | `interface/sdk-js/api/arkui/component/gridCol.static.d.ets:21-202` | AC-2.1 |
| R-6 | 行为 | Static 参数全部非负 | 转换为六档值并写对应 optional LayoutProperty | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_static_modifier.cpp:50-96,111-170` | AC-2.2 |
| R-7 | 异常 | Static 六档值任一小于 0 | `ValidateGridContainerSizeNonNegative` 清空整个 optional | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_static_modifier.cpp:35-45` | AC-2.3 |
| R-8 | 边界 | API level >=26 调用 setGridColOptions 或 builder overload | options 存在时写三个属性；不存在时三个 optional 均清空 | `interface/sdk-js/api/arkui/component/gridCol.static.d.ets:164-219`；`frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_static_modifier.cpp:111-136` | AC-2.4 |
| R-9 | 行为 | 请求 GridCol dynamic modifier | 当前管线选择 legacy 或 NG 表，均保持相同函数槽位 | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:252-285` | AC-3.1 |
| R-10 | 行为 | 请求 CJUI GridCol modifier | 返回六个属性 set/reset 槽位，不含 create | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:287-300` | AC-3.2 |
| R-11 | 边界 | 检索公开 Native NodeType | RelativeContainer 存在而 GridRow/GridCol 不存在；内部 `ArkUIGridColModifier` 不视为 Public | `interfaces/native/native_node.h:124-141`；`frameworks/core/interfaces/arkoala/arkoala_api.h:8898-8910` | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | Dynamic SDK 编译 + modifier UT | API 9/12 可见性、reset、API 20 span |
| VM-2 | R-5~R-8, AC-2.1~AC-2.4 | Static SDK 编译 + generated UT | API 23/26、undefined、任一负断点 |
| VM-3 | R-9~R-10, AC-3.1~AC-3.2 | ABI 结构检查 | NG/legacy/CJ 函数槽位 |
| VM-4 | R-11, AC-3.3 | Native SDK 负向检查 | 不生成 GridCol Public Native 用例 |

## API 变更分析

> 表中接口均为已有能力；开放范围严格以 canonical SDK 为准。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic `GridCol`/专有属性 | Public | options 或响应式值 | GridColAttribute | N/A | API 9 Dynamic 栅格子项 | AC-1.1 |
| `GridColModifier` | Public | 无构造参数；override applyNormalAttribute | void | N/A | API 12 Dynamic 属性 modifier | AC-1.2 |
| Static `GridCol(option?, content_?)` | Public | GridColOptions、CustomBuilder | GridColAttribute | N/A | API 23 Static 组件 | AC-2.1 |
| `setGridColOptions(options?)` / builder overload | Public | options 或 style builder | this/GridColAttribute | N/A | API 26 Static 更新和构建 | AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次未新增、变更或废弃接口 | 按 API level 选择 Dynamic/Static 表面 | AC-1.1~AC-3.3 |

## 接口规格

### 接口定义

**Dynamic GridCol 属性**

| 属性 | 值 |
|------|-----|
| 函数签名 | `span/gridColOffset/order(value: number \| GridColColumnOption): GridColAttribute` |
| 返回值 | GridColAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| span | number/GridColColumnOption | 是 | reset/非法为 1 | 非负；API 20 改变缺低档继承 |
| offset | number/GridColColumnOption | 是 | reset/非法为 0 | 非负；始终前档继承 |
| order | number/GridColColumnOption | 是 | reset/非法为 0 | 非负；始终前档继承 |

**Static GridCol**

| 属性 | 值 |
|------|-----|
| 函数签名 | `GridCol(option?: GridColOptions, content_?: CustomBuilder): GridColAttribute` |
| 返回值 | GridColAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| option | GridColOptions | 否 | undefined | Static API 23；属性允许 undefined |
| style | CustomBuilderT<GridColAttribute> | 是（builder overload） | 无 | API 26 staticonly |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Dynamic reset 或 target 跨 API 20 | 恢复默认或选择对应继承算法 | AC-1.3, AC-1.4 |
| 2 | Static 有效/负值/undefined | 写 optional、清空 optional 或清空 options | AC-2.2~AC-2.4 |
| 3 | Native 接口检索 | 不暴露 GridCol Public Native node | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；本 Feat 记录各版本既有表面和通道差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 9。
- **API 版本号策略:** Dynamic 9、cross-platform 10、atomic service 11、modifier 12、Static 23、Static options/builder 26。

| API level | 表面 | 证据 |
|-----------|------|------|
| 9 | Dynamic 构造与属性 | `interface/sdk-js/api/@internal/component/ets/grid_col.d.ts:189-287` |
| 12 | Dynamic GridColModifier | `interface/sdk-js/api/arkui/GridColModifier.d.ts:24-57` |
| 20 | Dynamic span 继承版本分支 | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:86-104` |
| 23 | Static 组件/属性/attributeModifier | `interface/sdk-js/api/arkui/component/gridCol.static.d.ets:123-202` |
| 26 | Static setGridColOptions/builder | `interface/sdk-js/api/arkui/component/gridCol.static.d.ets:164-219` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| canonical SDK | Public 签名和 `@since` 只取 interface/sdk-js | AC-1.1, AC-1.2, AC-2.1, AC-2.4 |
| 共享属性模型 | Dynamic/Static 最终写 GridColLayoutProperty | AC-1.3, AC-2.2 |
| 通道隔离 | 不把 Static optional 语义强加给 Dynamic reset | AC-1.3, AC-2.3 |
| ABI 分级 | Arkoala/CJ modifier 为内部实现，不进入 Public API 清单 | AC-3.1~AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 多范式转换不新增布局遍历；属性写入统一触发 Measure | Trace/代码审查 | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_property.h:54-57` |
| 功耗 | 无后台任务、IPC 或定时器 | 代码审查 | VM-1~VM-4 |
| 内存 | modifier 表为静态对象，节点属性随 FrameNode | 内存审查 | `frameworks/core/components_ng/pattern/grid_col/bridge/grid_col_dynamic_modifier.cpp:252-300` |
| 安全 | Public API 无权限；内部指针不暴露为 SDK API | API 审查 | AC-3.3 |
| 可靠性 | 空节点检查后退出，非法 Static 值清空 optional | UT/fuzz | AC-2.3 |
| 可测试性 | 每个 API level 和通道均有独立矩阵 | SDK/UT | VM-1~VM-4 |
| 自动化维测 | 复用 GridCol Property Dump | Inspector | `frameworks/core/components_ng/pattern/grid_col/grid_col_layout_pattern.h:56-63` |
| 定界定位 | SDK/Bridge/Modifier/Model 分层可追溯 | 设计审查 | `05-ui-components/01-layout-components/06-grid-col/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无接口表面差异 | 受同一 API level 和 target 规则约束 | SDK/运行测试 | AC-1.1~AC-2.4 |
| 平板 | 无接口表面差异 | Static/Dynamic 最终共享属性模型 | 布局对照 | AC-2.2 |
| 折叠屏 | 无接口表面差异 | 折叠仅影响父容器断点，不改变 modifier ABI | 折叠集成测试 | AC-1.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 本 Feat 只定义接口通道，不改变语义树 |
| 大字体 | 否 | 不改变字体或尺寸单位 |
| 深色模式 | 否 | 不涉及颜色 |
| 多窗口/分屏 | 是 | Dynamic/Static 属性在断点变化后由 GridRow 重测 | AC-1.4 |
| 多用户 | 否 | 无用户状态 |
| 版本升级 | 是 | API 9/12/20/23/26 可见性和行为需回归 | AC-1.1~AC-2.4 |
| 生态兼容 | 是 | 内部 ABI 不得被文档升级为 Public Native 契约 | AC-3.1~AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: GridCol 多范式接口与版本兼容
  Scenario Outline: API level 控制接口可见性
    Given 工程以 API level <level> 编译
    When 使用 <surface>
    Then 编译结果为 <result>

    Examples:
      | level | surface | result |
      | 9 | Dynamic GridCol | 可用 |
      | 22 | Static GridCol | 不可用 |
      | 23 | Static GridCol | 可用 |
      | 26 | setGridColOptions | 可用 |

  Scenario: Static 对象包含负断点
    Given Static span 对象的 md 为 -1
    When generated modifier 执行非负校验
    Then span optional 被清空
    And 不保留对象内其他断点值
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x] Dynamic、Modifier、Static 与内部 ABI 范围清晰
- [x] 未创建或承诺 GridCol Public Native API
- [x] 每个 AC 与规则、VM 双向可追溯
- [x] 实现差异只列风险，不替换 canonical SDK 契约

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "GridCol dynamic modifier static modifier CJUI Arkoala API target 20"
  - repo: "openharmony/interface_sdk-js"
    query: "GridColModifier GridCol static setGridColOptions API 12 23 26"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/grid_col.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/gridCol.static.d.ets`
- 共享设计：`05-ui-components/01-layout-components/06-grid-col/design.md`
