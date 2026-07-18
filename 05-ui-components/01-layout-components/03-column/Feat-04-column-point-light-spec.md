# 特性规格

> Func-05-01-03-Feat-04 Column PointLight 系统光效：固化光效参数从 ArkTS 到主题、`RenderContext` 和 Rosen 的存量行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Column PointLight 系统光效 |
| 特性编号 | Func-05-01-03-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 11–26；Static API 23–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

`pointLight` 是 Stage 模型 System API。状态写入通用 `RenderContext`，不参与 Column 布局；效果受编译开关、主题和渲染后端约束。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | PointLightStyle 规格 | 覆盖 LightSource、illuminated、bloom 及默认语义 |
| ADDED | 多入口与渲染规格 | 覆盖 Dynamic、Modifier、Static、reset、主题和 Rosen |
| ADDED | 已知偏差 | 记录 Static z 转换和测试覆盖缺口，不修改实现 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/03-column/design.md` | 已核对 |
| SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts`、`interface/sdk-js/api/arkui/component/column.static.d.ets` | 已核对 |
| ArkTS bridge | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | 已核对 |
| Render backend | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp` | 已核对 |

> 本文档是已有能力补录；实现与 SDK 不一致处按当前行为记录为风险。

## 用户故事

### US-1: 设置系统光效

**作为** 系统应用开发者，**我想要** 设置光源、受光区域和 bloom，**以便** 获得主题一致的效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN宏开启且参数、主题有效 THEN五项光效状态写入 `RenderContext`，Column 布局不变 | 正常 |
| AC-1.2 | WHEN LightSource 提供 x/y/z/intensity 而 color 缺省 THEN color 默认为 White；illuminated、bloom 缺省语义分别为 NONE、0 | 正常 |
| AC-1.3 | WHEN Dynamic 直调收到非 object THEN 不修改状态且不抛异常 | 异常 |
| AC-1.4 | WHEN关闭 `POINT_LIGHT_ENABLE` THEN三个入口均不写状态并正常返回 | 边界 |

### US-2: 跨入口更新与重置

**作为** 框架接入者，**我想要** 区分各入口语义，**以便** 避免状态残留或误清空。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Dynamic 直调只含部分字段 THEN 仅解析成功的字段更新，缺失或解析失败字段可保留旧值 | 边界 |
| AC-2.2 | WHEN Modifier 提交部分 style THEN 缺失/非法字段分别 reset；WHEN modifier 移除 THEN全部 PointLight 字段 reset | 恢复 |
| AC-2.3 | WHEN classic Dynamic 解析 lightSource 后缺 `ResourceAdapter` THEN可部分应用；WHEN Modifier 缺该对象 THEN当前条件分支存在空指针解引用风险；WHEN Static 缺 `ThemeConstants` THEN设置/reset 均 no-op | 异常 |
| AC-2.4 | WHEN Static intensity/bloom 超出 `[0,1]` THEN optional 被清除并 reset；Dynamic 直调当前只校验 number，不按该范围钳制 | 边界 |

### US-3: 提交 Rosen 光效

**作为** 渲染维护者，**我想要** 明确换算和 reset 规则，**以便** 验证可见结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN x/y 为百分比且 paint rect 非空 THEN按宽/高换算；空 rect 时位置不提交；z 不支持百分比语义，只做普通 px 转换 | 边界 |
| AC-3.2 | WHEN Rosen RSNode 可用且光效属性更新 THEN对应值提交并请求下一帧 | 正常 |
| AC-3.3 | WHEN Modifier reset THEN写具体默认值；WHEN Static reset THEN清 optional，但仍按主题写 borderWidth 和 bloom 阴影 | 恢复 |
| AC-3.4 | WHEN 正常 Static 构建转换 SDK LightSource THEN当前 converter 不转换 z，三轴不完整导致位置 reset；不得宣称该路径已正确支持三维位置 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-3 | 已有实现 | build matrix + 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10160-10203` |
| AC-2.1~AC-2.4 | R-4~R-7 | 已有实现 | 三入口对照测试 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp:7796-7925` |
| AC-3.1~AC-3.4 | R-8~R-10 | 已有实现/缺口 | Rosen + Static 回归测试 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 有效 style | 写通用 RenderContext，不写 Column LayoutProperty | `frameworks/core/components_ng/render/render_property.h:191-199` | AC-1.1 |
| R-2 | 边界 | 字段缺省 | lightSource undefined、illuminated NONE、bloom 0、color White | `interface/sdk-js/api/@internal/component/ets/common.d.ts:29678-29792`; `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10045-10158` | AC-1.2 |
| R-3 | 边界 | 编译 PointLight | 逻辑仅在 `POINT_LIGHT_ENABLE` 下执行 | `ace_config.gni:51-55`; `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10160-10203` | AC-1.3, AC-1.4 |
| R-4 | 行为 | Dynamic 直调 | 只更新存在且解析成功字段；主题查询发生在 lightSource 解析后 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10045-10200` | AC-2.1, AC-2.3 |
| R-5 | 恢复 | Modifier 设置/移除 | 逐项 set/reset；移除时统一 reset；空 ResourceAdapter 分支存在解引用风险 | `frameworks/bridge/declarative_frontend/ark_component/src/ArkColumn.ts:67-105`; `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp:7838-7925` | AC-2.2, AC-2.3 |
| R-6 | 异常 | Static 缺 ThemeConstants | 任一字段写入前返回，包括 undefined reset | `frameworks/core/interfaces/native/implementation/column_modifier.cpp:143-177` | AC-2.3 |
| R-7 | 边界 | Static 转换数值 | intensity/bloom 仅保留 `[0,1]`；Dynamic 无同等硬校验 | `frameworks/core/interfaces/native/utility/validators.cpp:23-31,100-105,162-169` | AC-2.4 |
| R-8 | 行为 | Rosen 更新位置/属性 | x/y 百分比参照 paint rect，z 普通转 px；提交后请求下一帧 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603` | AC-3.1, AC-3.2 |
| R-9 | 恢复 | Modifier/Static reset | 前者写具体默认值；后者清 optional 并保留主题派生边框/阴影 | `frameworks/core/interfaces/native/node/node_common_modifier.cpp:6113-6247`; `frameworks/core/components_ng/base/view_abstract_model_static.cpp:1128-1205` | AC-3.3 |
| R-10 | 异常 | Static 转换位置 | z 仅在 `WRONG_SDK` 分支转换；正常构建三轴检查失败并 reset | `frameworks/core/interfaces/native/utility/converter.cpp:3654-3665`; `frameworks/core/components_ng/base/view_abstract_model_static.cpp:1176-1185` | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~AC-1.4 | 开/关宏构建测试 | API、布局隔离、关闭时 no-op |
| VM-2 | R-4~R-6, AC-2.1~AC-2.3 | 三入口异常注入 | 缺字段、主题对象缺失、Modifier 空指针风险 |
| VM-3 | R-5, R-9, AC-2.2, AC-3.3 | Modifier UT | 部分 style 与 reset |
| VM-4 | R-7, AC-2.4 | Static UT | intensity/bloom 边界与越界 reset |
| VM-5 | R-8, R-10, AC-3.1~AC-3.4 | Rosen/Static 回归测试 | x/y/z 与 Static z 缺口；setter 用例受 `test/unittest/capi/modifiers/column_modifier_test.cpp:201-676` 屏蔽 |

## API 变更分析

> 本次不产生 API 增量，下表仅固定既有版本边界。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic `pointLight(value: PointLightStyle)` | System/Stage | lightSource/illuminated/bloom | `ColumnAttribute` | N/A | API 11+ 设置光效 | AC-1.1~AC-3.3 |
| Static `pointLight(value: PointLightStyle \| undefined)` | System/Stage | style 或 undefined | `ColumnAttribute` | N/A | API 23+ 设置/reset | AC-2.3, AC-2.4, AC-3.3, AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 存量规格补录 | 无需迁移 | AC-1.1~AC-3.4 |

## 接口规格

### 接口定义

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic `pointLight(value: PointLightStyle)`；Static `pointLight(value: PointLightStyle \| undefined)` |
| 返回值 | `ColumnAttribute`，链式调用 |
| 开放范围 | System、Stage；Dynamic API 11+，Static API 23+ |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.4 |

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|------|------|--------|------|
| lightSource | `LightSource` | 否 | undefined | 提供时 SDK 要求 x/y/z/intensity |
| x/y/z | `Dimension` | 是* | 无 | x/y 可按百分比换算，z 不支持百分比语义 |
| intensity | `number` | 是* | 无 | SDK 推荐 `[0,1]`，Static 实际校验 |
| color | `ResourceColor` | 否 | White | 可走资源更新 |
| illuminated | `IlluminatedType` | 否 | NONE | 取值 0–5 |
| bloom | `number` | 否 | 0 | SDK 推荐 `[0,1]`，Static 实际校验 |

`*`：仅在提供 LightSource 时必填。

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 构建开关、参数和主题完整 | 更新 RenderContext 并由 Rosen 请求下一帧 | AC-1.1, AC-3.2 |
| 2 | 宏关闭或主题对象缺失 | 按入口无操作、部分应用或保留风险边界 | AC-1.4, AC-2.3 |
| 3 | reset 或 Static 三轴转换不完整 | 按通道恢复默认，Static 位置执行现有 reset | AC-3.3, AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录 Dynamic、Modifier、Static 的既有差异。
- **配置文件格式变更:** 否；沿用 `ace_engine_feature_enable_point_light` 与 `POINT_LIGHT_ENABLE`。
- **数据存储格式变更:** 否；状态仅存在于节点 `RenderContext`，无持久化或迁移。
- **最低支持版本:** Dynamic API 11，Static API 23。
- **API 版本号策略:** 以 canonical SDK 的 System/Stage 与 `@since` 标注为准，不扩展 Native Column 布局属性。

| 风险 | 当前实现 | 契约影响 | 证据 |
|------|----------|----------|------|
| Dynamic 部分应用 | lightSource 在 ResourceAdapter 查询前解析 | Adapter 缺失时可能只更新部分字段 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10160-10182` |
| Modifier 空对象 | 空 ResourceAdapter 分支存在解引用风险 | 异常环境下不保证安全 reset | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp:7838-7925` |
| Static z 缺失 | 正常 converter 未形成完整三轴 | Static 光源位置可能 reset | `frameworks/core/interfaces/native/utility/converter.cpp:3654-3665` |
| reset 差异 | Modifier 写具体默认值，Static 清 optional 并派生主题效果 | 跨通道状态快照不完全相同 | `frameworks/core/interfaces/native/node/node_common_modifier.cpp:6113-6247`; `frameworks/core/components_ng/base/view_abstract_model_static.cpp:1128-1205` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 渲染分层 | 复用通用 `ViewAbstract`/`RenderContext`，不得写入 Column LayoutProperty | AC-1.1 |
| 环境门控 | Dynamic 使用 ResourceAdapter，Static 使用 ThemeConstants，且均受编译宏控制 | AC-1.4, AC-2.3 |
| 后端边界 | Rosen 负责维度换算和 RSNode 提交；通用 RenderContext 默认 hook 为空 | AC-3.1, AC-3.2 |
| SDK 权威 | System/Stage 签名以 canonical SDK 为准，Static z 偏差只列风险 | AC-2.4, AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 光效更新不触发 Column Measure，沿用 RenderContext 下一帧机制 | trace + 集成测试 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603` |
| 功耗 | 不新增定时器或后台任务，只在属性更新时请求帧 | 代码审查 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6561-6602` |
| 内存 | 不新增持久缓存，状态随 RenderContext 生命周期存在 | 生命周期 UT | `frameworks/core/components_ng/render/render_property.h:191-199` |
| 安全 | System API 不处理敏感数据或新增权限 | SDK/代码审查 | `interface/sdk-js/api/@internal/component/ets/column.d.ts:201-211` |
| 可靠性 | 覆盖宏关闭、主题缺失、空 paint rect 和空 RSNode | build matrix + 异常注入 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10160-10203`; `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603` |
| 可测试性 | 三入口及 x/y/z/reset 均有独立验证映射 | 追溯审查 | VM-1~VM-5 |
| 自动化维测 | RenderContext 属性更新可通过 Rosen Mock/RSNode 状态观测 | Render UT | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603` |
| 定界定位 | 按 SDK、Bridge、Theme、RenderContext、Rosen 五层定位 | 日志/源码审查 | `05-ui-components/01-layout-components/03-column/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无固定差异 | 依赖产品开关、主题和 Rosen 后端 | 构建矩阵 + Render UT | AC-1.4, AC-3.2 |
| 平板 | 无固定差异 | x/y 百分比按实际 paint rect 换算 | 多窗口渲染测试 | AC-3.1 |
| 折叠屏 | 无固定差异 | 尺寸/配置变化后使用最新 paint rect 与主题结果 | 折叠态渲染测试 | AC-2.1, AC-3.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不新增语义或改变子项顺序 | N/A |
| 大字体 | 否 | 不读取字体缩放 | N/A |
| 深色模式 | 是 | color、borderWidth、bloom radius 与 shadow color 由主题/资源决定 | AC-1.1, AC-2.1 |
| 多窗口/分屏 | 是 | paint rect 改变 x/y 百分比位置，不改变布局尺寸 | AC-3.1 |
| 多用户 | 否 | 无用户级持久状态 | N/A |
| 版本升级 | 是 | Dynamic API 11 与 Static API 23 边界必须保留 | AC-1.1, AC-2.3 |
| 生态兼容 | 是 | 保持 System API；非 Rosen 后端不承诺同等可见效果 | AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Column PointLight 系统光效

  Scenario: 编译开关关闭
    Given POINT_LIGHT_ENABLE 未定义
    When Dynamic、Modifier 或 Static 设置 PointLightStyle
    Then 不写入 PointLight 状态
    And 调用正常返回

  Scenario: Dynamic 在主题适配器缺失时部分应用
    Given POINT_LIGHT_ENABLE 已开启
    And Dynamic 输入包含合法 lightSource
    But ResourceAdapter 创建失败
    When pointLight 执行
    Then 已解析的 lightSource 可以保留
    And illuminated 与 bloom 不继续更新

  Scenario: Rosen 百分比位置换算
    Given paint rect 非空且 x/y 为百分比
    When RenderContext 提交光源位置
    Then x/y 分别按 paint rect 宽高换算
    And z 仅按普通维度转 px
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖 PointLight，不扩展 Column 布局或 Native layout attribute
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则使用行为/边界/异常/恢复类型并通过五项质量检查
- [x] 已覆盖 Dynamic/Modifier/Static、主题、宏、RenderContext、Rosen 与 Static z 风险

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Column PointLight Dynamic Static Modifier Theme RenderContext Rosen reset"
  - repo: "openharmony/interface_sdk-js"
    query: "Column pointLight PointLightStyle LightSource API 11 API 23 System Stage"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/column.d.ts:201-211`、`interface/sdk-js/api/arkui/component/column.static.d.ets:103-112`、`05-ui-components/01-layout-components/03-column/design.md`。
