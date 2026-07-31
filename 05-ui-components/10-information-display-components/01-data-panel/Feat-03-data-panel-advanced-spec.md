# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DataPanel 高级能力 |
| 特性编号 | Func-05-10-01-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | DataPanel 高级能力规格补录 | trackShadow、ContentModifier、C-API 全量规格 |

## 输入文档

- 设计文档: `05-ui-components/10-information-display-components/01-data-panel/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/data_panel/`, `frameworks/core/interfaces/native/`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。

## 用户故事

### US-1: 开发者为 DataPanel 添加阴影效果

**As a** 应用开发者  
**I want to** 通过 trackShadow 为环形进度条添加阴影  
**So that** 能够增强视觉层次感

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 trackShadow({ radius: 10 }) THEN 显示模糊半径为 10 的阴影 | 正常 |
| AC-1.2 | WHEN 设置 trackShadow({ offsetX: 5, offsetY: 5 }) THEN 阴影偏移 5x5 | 正常 |
| AC-1.3 | WHEN trackShadow.colors 未指定 THEN 使用 valueColors 作为阴影颜色 | 边界 |
| AC-1.4 | WHEN trackShadow.colors 为空数组 THEN 使用 valueColors 作为阴影颜色 | 边界 |

### US-2: 开发者使用 ContentModifier 自定义渲染

**As a** 应用开发者  
**I want to** 通过 ContentModifier 完全自定义 DataPanel 渲染  
**So that** 能够实现特殊的视觉效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 contentModifier THEN 默认渲染被跳过 | 正常 |
| AC-2.2 | WHEN ContentModifier 回调执行 THEN 接收 DataPanelConfiguration（values/maxValue/enabled） | 正常 |
| AC-2.3 | WHEN contentModifier 返回自定义节点 THEN 自定义内容被渲染 | 正常 |

### US-3: Native 开发者通过 C-API 使用 DataPanel

**As a** Native 开发者  
**I want to** 通过 C-API 创建和控制 DataPanel  
**So that** 能够在 Native 层使用数据面板组件

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 construct() THEN 返回有效的 Ark_NativePointer | 正常 |
| AC-3.2 | WHEN 调用 setDataPanelOptions() THEN values/max/type 被设置 | 正常 |
| AC-3.3 | WHEN 调用 setCloseEffect() THEN 效果状态被更新 | 正常 |
| AC-3.4 | WHEN 调用 setValueColors() THEN 颜色数组被应用 | 正常 |
| AC-3.5 | WHEN 调用 setTrackBackgroundColor() THEN 轨道背景被更新 | 正常 |
| AC-3.6 | WHEN 调用 setStrokeWidth() THEN 环形宽度被更新 | 正常 |
| AC-3.7 | WHEN 调用 setTrackShadow (ExtenderAccessor) THEN 阴影效果被应用 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-3 | C-API 单元测试 | test_trackShadow_radius |
| AC-1.2 | R-2 | TASK-3 | C-API 单元测试 | test_trackShadow_offset |
| AC-1.3 | R-3 | TASK-3 | C-API 单元测试 | test_trackShadow_colors_fallback |
| AC-1.4 | R-4 | TASK-3 | C-API 单元测试 | test_trackShadow_colors_empty |
| AC-2.1 | R-5 | TASK-3 | 单元测试 | test_contentModifier_bypass |
| AC-2.2 | R-6 | TASK-3 | 单元测试 | test_contentModifier_config |
| AC-2.3 | R-7 | TASK-3 | 单元测试 | test_contentModifier_render |
| AC-3.1 | R-8 | TASK-3 | C-API 单元测试 | test_capi_construct |
| AC-3.2 | R-9 | TASK-3 | C-API 单元测试 | test_capi_setDataPanelOptions |
| AC-3.3 | R-10 | TASK-3 | C-API 单元测试 | test_capi_setCloseEffect |
| AC-3.4 | R-11 | TASK-3 | C-API 单元测试 | test_capi_setValueColors |
| AC-3.5 | R-12 | TASK-3 | C-API 单元测试 | test_capi_setTrackBackgroundColor |
| AC-3.6 | R-13 | TASK-3 | C-API 单元测试 | test_capi_setStrokeWidth |
| AC-3.7 | R-14 | TASK-3 | C-API 单元测试 | test_capi_setTrackShadow |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | trackShadow.radius = 10 | 模糊半径为 10 | 无 | AC-1.1 |
| R-2 | 行为 | trackShadow.offsetX/Y = 5 | 阴影偏移 5x5 | 无 | AC-1.2 |
| R-3 | 边界 | trackShadow.colors 未指定 | 使用 valueColors | 无 | AC-1.3 |
| R-4 | 边界 | trackShadow.colors = [] | 使用 valueColors | 无 | AC-1.4 |
| R-5 | 行为 | 设置 contentModifier | onDraw 直接返回，跳过默认渲染 | useContentModifier_ = true | AC-2.1 |
| R-6 | 行为 | ContentModifier 回调执行 | 接收 DataPanelConfiguration | 含 values/maxValue/enabled | AC-2.2 |
| R-7 | 行为 | contentModifier 返回节点 | 渲染自定义内容 | 无 | AC-2.3 |
| R-8 | 行为 | C-API construct() | 返回有效 Ark_NativePointer | 无 | AC-3.1 |
| R-9 | 行为 | C-API setDataPanelOptions() | 设置 values/max/type | 无 | AC-3.2 |
| R-10 | 行为 | C-API setCloseEffect() | 更新效果状态 | 无 | AC-3.3 |
| R-11 | 行为 | C-API setValueColors() | 应用颜色数组 | 无 | AC-3.4 |
| R-12 | 行为 | C-API setTrackBackgroundColor() | 更新轨道背景 | 无 | AC-3.5 |
| R-13 | 行为 | C-API setStrokeWidth() | 更新环形宽度 | 无 | AC-3.6 |
| R-14 | 行为 | C-API setTrackShadow() | 应用阴影效果 | 通过 ExtenderAccessor | AC-3.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | trackShadow 颜色回退 | C-API 单元测试 | 验证 fallback 逻辑 |
| VM-2 | ContentModifier 跳过默认渲染 | 单元测试 | 验证 useContentModifier_ 标志 |
| VM-3 | C-API 构造和属性设置 | C-API 单元测试 | 验证完整 C-API 接口 |
| VM-4 | C-API ExtenderAccessor | C-API 单元测试 | 验证 setTrackShadow 接口 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| trackShadow(value: DataPanelShadowOptions) | Public | value: 阴影配置 | void | 无 | 设置阴影效果 | AC-1.1 ~ AC-1.4 |
| contentModifier\<DataPanelConfiguration\>(value: ContentModifier) | Public | value: 内容修改器 | void | 无 | 自定义渲染 | AC-2.1 ~ AC-2.3 |

### C-API 新增接口

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| construct(id, flags) | System | id, flags | Ark_NativePointer | 无 | 构造 DataPanel | AC-3.1 |
| setDataPanelOptions(node, options) | System | node, Ark_DataPanelOptions | void | 无 | 设置构造参数 | AC-3.2 |
| setCloseEffect(node, value) | System | node, Opt_Boolean | void | 无 | 设置效果开关 | AC-3.3 |
| setValueColors(node, value) | System | node, Opt_Array | void | 无 | 设置颜色数组 | AC-3.4 |
| setTrackBackgroundColor(node, value) | System | node, Opt_ResourceColor | void | 无 | 设置轨道背景 | AC-3.5 |
| setStrokeWidth(node, value) | System | node, Opt_Length | void | 无 | 设置环形宽度 | AC-3.6 |
| setTrackShadow(node, options) | System | node, Opt_DataPanelShadowOptions | void | 无 | 设置阴影（ExtenderAccessor） | AC-3.7 |

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**trackShadow**

| 属性 | 值 |
|------|-----|
| 函数签名 | `trackShadow(value: DataPanelShadowOptions): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1 ~ AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.radius | `number \| Resource` | 否 | 5.0 | 模糊半径 |
| value.offsetX | `number \| Resource` | 否 | 5.0 | 水平偏移 |
| value.offsetY | `number \| Resource` | 否 | 5.0 | 垂直偏移 |
| value.colors | `Array<ResourceColor \| LinearGradient>` | 否 | valueColors | 阴影颜色 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | trackShadow({ radius: 10 }) | 模糊半径为 10 | AC-1.1 |
| 2 | trackShadow({ offsetX: 5, offsetY: 5 }) | 阴影偏移 5x5 | AC-1.2 |
| 3 | trackShadow({}) 未指定 colors | 使用 valueColors | AC-1.3 |
| 4 | trackShadow({ colors: [] }) | 使用 valueColors | AC-1.4 |

---

**contentModifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `contentModifier<DataPanelConfiguration>(value: ContentModifier): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-2.1 ~ AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `ContentModifier<DataPanelConfiguration>` | 是 | - | 回调返回自定义节点 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | contentModifier 设置 | 跳过默认渲染 | AC-2.1 |
| 2 | 回调执行 | 接收 values/maxValue/enabled | AC-2.2 |
| 3 | 回调返回自定义节点 | 渲染自定义内容 | AC-2.3 |

---

**C-API: GENERATED_ArkUIDataPanelModifier**

| 属性 | 值 |
|------|-----|
| 结构体 | `GENERATED_ArkUIDataPanelModifier` |
| 开放范围 | System |
| 错误码 | 无 |
| 关联 AC | AC-3.1 ~ AC-3.7 |

**成员函数**

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| construct | id: Ark_Int32, flags: Ark_Int32 | Ark_NativePointer | 构造节点 |
| setDataPanelOptions | node, options* | void | 设置构造参数 |
| setCloseEffect | node, value* | void | 设置效果开关 |
| setValueColors | node, value* | void | 设置颜色数组 |
| setTrackBackgroundColor | node, value* | void | 设置轨道背景 |
| setStrokeWidth | node, value* | void | 设置环形宽度 |

---

**C-API: GENERATED_ArkUIDataPanelExtenderAccessor**

| 属性 | 值 |
|------|-----|
| 结构体 | `GENERATED_ArkUIDataPanelExtenderAccessor` |
| 开放范围 | System |
| 错误码 | 无 |
| 关联 AC | AC-3.7 |

**成员函数**

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| setTrackShadow | node, options* | void | 设置阴影效果 |
| nullTrackShadow | node | void | 清除阴影效果 |

## 兼容性声明

- **已有 API 行为变更:** 否，纯补录规格
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 无特殊版本约束

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| trackShadow 颜色回退 | 未指定时使用 valueColors | AC-1.3, AC-1.4 |
| ContentModifier 跳过默认渲染 | useContentModifier_ 标志控制 | AC-2.1 |
| C-API 双范式支持 | Dynamic + Static modifier | AC-3.1 ~ AC-3.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 无特殊要求 | N/A | N/A |
| 功耗 | 无特殊要求 | N/A | N/A |
| 内存 | 无特殊要求 | N/A | N/A |
| 安全 | 无权限校验 | 代码评审 | 无敏感数据 |
| 可靠性 | 颜色回退保证渲染正常 | 单元测试 | test_trackShadow_colors_fallback |
| 可测试性 | 支持 C-API 单元测试 | C-API 单元测试 | 100% AC 覆盖 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | N/A | N/A | N/A |
| 平板 | 无差异 | N/A | N/A | N/A |
| 折叠屏 | 无差异 | N/A | N/A | N/A |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | ContentModifier 支持自定义无障碍 | 无障碍定制 |
| 大字体 | 否 | 不涉及 | N/A |
| 深色模式 | 是 | trackShadow.colors 支持主题色 | 深色模式适配 |
| 多窗口/分屏 | 否 | 不涉及 | N/A |
| 多用户 | 否 | 不涉及 | N/A |
| 版本升级 | 否 | 不涉及 | N/A |
| 生态兼容 | 是 | C-API 支持 Native 场景 | NDK 生态 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DataPanel 高级能力
  作为 应用开发者
  我想要 使用 trackShadow、ContentModifier、C-API 高级能力
  以便 能够实现更丰富的视觉效果和跨语言集成

  Scenario: 阴影颜色回退
    Given valueColors = [Color.Red, Color.Blue]
    When trackShadow({ radius: 10 })
    Then 阴影颜色使用 [Color.Red, Color.Blue]

  Scenario: ContentModifier 跳过默认渲染
    Given 设置 contentModifier
    When onDraw 执行
    Then 直接返回，不渲染默认进度条

  Scenario: C-API 构造和设置属性
    Given 调用 construct() 获得节点指针
    When 调用 setDataPanelOptions(values=[10,20], max=100, type=CIRCLE)
    And 调用 setValueColors([Color.Red, Color.Blue])
    And 调用 setStrokeWidth(24)
    Then C-API 节点属性与 ArkTS 组件一致
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel trackShadow 颜色回退到 valueColors 的实现逻辑"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel ContentModifier 跳过默认渲染的 useContentModifier_ 标志"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel C-API GENERATED_ArkUIDataPanelModifier 接口定义"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel C-API ExtenderAccessor setTrackShadow 实现"
```

**关键文档：** design.md, arkoala_api_generated.h