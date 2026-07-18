# 特性规格

> Func-05-01-05-Feat-04 Flex 多范式接口与版本兼容：固化 Dynamic、Static、AttributeModifier、Native C API、legacy/NG 分派及 API 7–26 版本边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Flex 多范式接口与版本兼容 |
| 特性编号 | Func-05-01-05-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Flex 通过四组公开/框架入口汇入同一布局属性：Classic Dynamic 在 `js_flex_impl.cpp` 解析构造 options；AttributeModifier 经 ArkFlex 和 ArkTS Native Bridge 增量 set/reset；Static/generated modifier 在 API 23+ 转换 union/options；Native C API 在 API 12+ 提供 `NODE_FLEX_OPTION` 与 `NODE_FLEX_SPACE`。本文按通道固化已存在行为，不以某一通道推断其他通道。关键证据见 `frameworks/bridge/declarative_frontend/jsview/js_flex_impl.cpp:28-174,225-251`、`frameworks/bridge/declarative_frontend/ark_component/src/ArkFlex.ts:16-105`、`frameworks/core/interfaces/native/implementation/flex_modifier.cpp:31-166` 和 `interfaces/native/node/style_modifier.cpp:12697-12754,20575-20608,23080-23108`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Dynamic 与 legacy/NG 分派规格 | 覆盖 NoWrap/Wrap 解析、API 10 校验和旧 pipeline |
| ADDED | AttributeModifier 与 Static 规格 | 覆盖增量 diff、set/reset、component/style builder 和版本 |
| ADDED | Native C API 与版本矩阵 | 覆盖参数校验、set/reset/get、公开属性 ID 和 API 7/12/23/26 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/05-flex/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/flex.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/flex.static.d.ets` | 已核对 |
| Dynamic bridge | `frameworks/bridge/declarative_frontend/jsview/js_flex_impl.cpp`; `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_flex_bridge.cpp` | 已核对 |
| Native API | `interfaces/native/native_node.h`; `interfaces/native/node/style_modifier.cpp` | 已核对 |

## 用户故事

### US-1: 使用 Dynamic 与 AttributeModifier 配置 Flex

**作为** ArkTS Dynamic 开发者  
**我想要** 构造和增量更新 Flex options  
**以便** 在已有应用范式中获得稳定布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Classic Dynamic 调用 `Flex(options)` THEN 根据 wrap 选择 NoWrap/Wrap 解析路径，解析 direction、justifyContent、alignItems、alignContent 和可用 space 后调用当前 pipeline Model | 正常 |
| AC-1.2 | WHEN 当前容器使用 NG pipeline THEN 模型创建/更新 FLEX FrameNode；WHEN 使用 legacy pipeline THEN 继续创建既有 Flex/Wrap 组件并保留其尺寸策略 | 正常 |
| AC-1.3 | WHEN API 10+ Dynamic 枚举越界或字段类型无效 THEN 按字段默认值/忽略路径处理且不向应用抛 C++ 异常 | 异常 |
| AC-1.4 | WHEN AttributeModifier 首次设置或值发生 diff THEN ArkFlex 生成 options modifier 并调用 node modifier set；WHEN 对应 modifier 被移除 THEN 调用 reset 路径 | 正常 |
| AC-1.5 | WHEN 同一 FrameNode 在 NoWrap 与 Wrap options 间切换 THEN FlexModelNG 更新模式，后续 Pattern 创建与新 wrap 状态对应的算法 | 正常 |

### US-2: 使用 Static Flex 和构建器扩展

**作为** Static ArkTS 开发者  
**我想要** 通过强类型 Static API 创建和更新 Flex  
**以便** 使用编译期类型安全的组件范式

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN API 23+ 调用 Static `Flex(options, content_)` THEN 创建 Flex 并将 direction/wrap/align/space 转换到现有 Model，执行 content builder 构建子项 | 正常 |
| AC-2.2 | WHEN Static options 为未设置/Optional 空值 THEN 按 generated converter 的当前默认或 reset 语义处理，不读取无效 union | 边界 |
| AC-2.3 | WHEN API 23+ 使用 component builder 或 attributeModifier THEN 返回/应用 Static Flex 对应 builder/modifier 类型，不混用 Dynamic 类型声明 | 正常 |
| AC-2.4 | WHEN API 26+ 使用 style builder 或 `setFlexOptions` THEN 只在该目标 API 可见，并通过既有 Static options 更新链进入 Model | 正常 |
| AC-2.5 | WHEN 目标 API 低于 Static 声明的 `@since` THEN 编译期不可依赖相应 Static/builder 能力 | 边界 |

### US-3: 通过 Native C API 设置和读取属性

**作为** Native UI 开发者  
**我想要** 用公开属性 ID 设置、重置和读取 Flex  
**以便** 在 C/C++ 应用中复现 ArkTS 布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API 12+ 对 `NODE_FLEX_OPTION` 传入规定数量、范围内的 direction/wrap/align 原始值 THEN style_modifier 分派到 node modifier 并更新 Flex options | 正常 |
| AC-3.2 | WHEN 对 `NODE_FLEX_SPACE` 传入 main/cross 数值及合法单位 THEN 分派并更新双轴间距；get 返回当前节点对应属性值和单位 | 正常 |
| AC-3.3 | WHEN Native 参数数量不足、指针为空或枚举超出接口校验范围 THEN 返回 `PARAM_INVALID` 且不执行正常属性写入 | 异常 |
| AC-3.4 | WHEN Native reset Flex option/space THEN 使用该属性 ID 对应的 resetter；后续 getter 反映 reset 后当前默认状态 | 边界 |
| AC-3.5 | WHEN Native 操作的节点不是预期类型或已失效 THEN 依公共 Node API 的类型/生命周期保护返回，不解引用无效业务节点 | 异常 |

### US-4: 按 API 版本使用能力

**作为** 跨版本应用维护者  
**我想要** 明确 Flex 各范式的开放版本  
**以便** 正确设置 minAPIVersion 与迁移策略

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 目标 API 为 7+ THEN Dynamic Flex 基础 options 可用；API<12 不依赖 `space` | 正常 |
| AC-4.2 | WHEN 目标 API 为 12+ THEN Dynamic space 与 Public Native Flex 节点/属性能力按 canonical SDK/Native 头文件开放 | 正常 |
| AC-4.3 | WHEN 目标 API 为 23+ THEN Static Flex、Static FlexModifier 和 component builder 可用 | 正常 |
| AC-4.4 | WHEN 目标 API 为 26+ THEN Static style builder 与 `setFlexOptions` 可用 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | Dynamic/Modifier/模式切换 UT | `frameworks/bridge/declarative_frontend/jsview/js_flex_impl.cpp:28-174`; `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:22-90` |
| AC-2.1~AC-2.5 | R-6~R-9 | 已有实现 | Static SDK 编译 + generated modifier UT | `interface/sdk-js/api/arkui/component/flex.static.d.ets:31-200`; `frameworks/core/interfaces/native/implementation/flex_modifier.cpp:31-166` |
| AC-3.1~AC-3.5 | R-10~R-14 | 已有实现 | C API set/reset/get UT + fuzz | `interfaces/native/node/style_modifier.cpp:12697-12754,20575-20608,23080-23108`; `test/unittest/capi/modifiers/flex_modifier_test.cpp:69-206` |
| AC-4.1~AC-4.4 | R-15~R-18 | 已有实现 | API level 编译矩阵 | Dynamic/Static SDK 与 `interfaces/native/native_node.h:48-53,124-129,8467-8504` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Classic Dynamic 构造 | 按 wrap 分派并解析 options | `frameworks/bridge/declarative_frontend/jsview/js_flex_impl.cpp:28-174` | AC-1.1 |
| R-2 | 行为 | 选择 pipeline | NG 使用 FlexModelNG，legacy 使用 FlexModelImpl | `frameworks/bridge/declarative_frontend/jsview/js_flex.cpp:27-40`; `frameworks/bridge/declarative_frontend/jsview/models/flex_model_impl.cpp:26-184` | AC-1.2 |
| R-3 | 异常 | API 10+ options 非法 | 使用校验后的默认/忽略路径 | `frameworks/bridge/declarative_frontend/jsview/js_flex.cpp:55-92` | AC-1.3 |
| R-4 | 行为 | AttributeModifier diff/remove | 分别调用 options set/reset | `frameworks/bridge/declarative_frontend/ark_component/src/ArkFlex.ts:16-105` | AC-1.4 |
| R-5 | 行为 | wrap 模式变化 | Model 更新模式，Pattern 后续按状态选算法 | `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:22-90`; `frameworks/core/components_ng/pattern/flex/flex_layout_pattern.h:31-50` | AC-1.5 |
| R-6 | 行为 | Static Flex 创建 | converter 转 options 后调用现有创建/设置路径 | `frameworks/core/interfaces/native/implementation/flex_modifier.cpp:31-111` | AC-2.1 |
| R-7 | 边界 | Static Optional/union 空值 | 按 generated converter 默认/reset 处理 | 同上 | AC-2.2 |
| R-8 | 行为 | component/attribute builder | 使用 Static Flex 类型和 modifier | `interface/sdk-js/api/arkui/component/flex.static.d.ets:123-165` | AC-2.3 |
| R-9 | 边界 | style builder/setFlexOptions | 仅 API 26+ 可见 | `interface/sdk-js/api/arkui/component/flex.static.d.ets:145-200` | AC-2.4, AC-2.5 |
| R-10 | 行为 | 合法 NODE_FLEX_OPTION | 校验后分派 node modifier 更新 options | `interfaces/native/node/style_modifier.cpp:12697-12754,23080-23108` | AC-3.1 |
| R-11 | 行为 | 合法 NODE_FLEX_SPACE | 转换双轴 Dimension，支持 set/get | `interfaces/native/node/style_modifier.cpp:20575-20608` | AC-3.2 |
| R-12 | 异常 | Native 参数/范围非法 | 返回 PARAM_INVALID，不正常写入 | `interfaces/native/node/style_modifier.cpp:12697-12754` | AC-3.3 |
| R-13 | 恢复 | Native reset | 调用对应 resetter 并由 getter反映当前值 | `frameworks/core/interfaces/native/node/flex_modifier.cpp:113-169` | AC-3.4 |
| R-14 | 异常 | 节点类型/生命周期非法 | 使用公共 Node API 保护路径 | Native Node 分派公共前置检查 | AC-3.5 |
| R-15 | 边界 | API 7+ | Dynamic FlexOptions 可见 | `interface/sdk-js/api/@internal/component/ets/flex.d.ts:30-95,150-172` | AC-4.1 |
| R-16 | 边界 | API 12+ | space 与 Public Native 节点能力可见 | `interface/sdk-js/api/@internal/component/ets/flex.d.ts:97-147`; `interfaces/native/native_node.h:48-53,124-129` | AC-4.2 |
| R-17 | 边界 | API 23+ | Static Flex/Modifier/component builder 可见 | `interface/sdk-js/api/arkui/component/flex.static.d.ets:31-165`; `interface/sdk-js/api/arkui/FlexModifier.static.d.ets:24-32` | AC-4.3 |
| R-18 | 边界 | API 26+ | Static style builder/setFlexOptions 可见 | `interface/sdk-js/api/arkui/component/flex.static.d.ets:145-200` | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | Dynamic/Modifier NG UT | NoWrap/Wrap 分派、API 10 回退、diff/reset、模式切换 |
| VM-2 | R-6~R-9, AC-2.1~AC-2.5 | Static SDK 编译 + UT | Optional、builder、API 23/26 可见性 |
| VM-3 | R-10~R-14, AC-3.1~AC-3.5 | Native C API UT/fuzz | set/reset/get、数量/范围、节点保护 |
| VM-4 | R-15~R-18, AC-4.1~AC-4.4 | API level 编译矩阵 | 7/12/23/26 边界 |

## API 变更分析

> 所列均为已有接口；“新增”表示在历史 API 版本中加入，不表示本次文档任务新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic `Flex(value?: FlexOptions)` | Public | FlexOptions | FlexAttribute | N/A | API 7 动态组件入口 | AC-1.1~AC-1.3, AC-4.1 |
| Static `Flex(options, content_)` | Public | Static options + builder | FlexComponent | N/A | API 23 静态组件入口 | AC-2.1~AC-2.3, AC-4.3 |
| `setFlexOptions(options?)` | Public | Static FlexOptions | `this` | N/A | API 26 Static options 更新 | AC-2.4, AC-4.4 |
| `NODE_FLEX_OPTION` / `NODE_FLEX_SPACE` | Public C API | ArkUI_AttributeItem | ArkUI_ErrorCode/AttributeItem | NO_ERROR/PARAM_INVALID | Native set/reset/get | AC-3.1~AC-3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次无签名变更或废弃 | 按目标 API 选择 Dynamic/Static 能力 | AC-4.1~AC-4.4 |

## 接口规格

### 接口定义

| 通道 | 接口签名/属性 | set | reset | get | 目标版本 |
|------|---------------|-----|-------|-----|----------|
| Dynamic | `Flex(value?: FlexOptions)` | 构造/重建时解析 options | 空/移除按 Dynamic 路径 | 无组件专有 getter | API 7+ |
| AttributeModifier | Flex options modifier | ArkTS Native Bridge → node modifier | modifier remove → reset options | 内部 diff 使用阶段值 | 依 Dynamic modifier 框架 |
| Static | `Flex(options, content_)` | generated converter → Model | Optional 空值按生成路径 | Static 属性链 | API 23+ |
| Static update | `setFlexOptions(options?)` | 更新 options | 空 Optional 按定义处理 | 返回 this | API 26+ |
| Native | NODE_FLEX_OPTION/SPACE | AttributeItem set | 属性 reset | AttributeItem get | API 12+ Native Node |

**Native 参数约束摘要**

| 属性 | 输入 | 校验/默认 | 关联 AC |
|------|------|-----------|---------|
| NODE_FLEX_OPTION | direction/wrap/justify/alignItems/alignContent 原始枚举 | 参数数量与范围由 style_modifier 校验 | AC-3.1, AC-3.3 |
| NODE_FLEX_SPACE | main/cross 数值及单位 | 单位与数值经 Dimension 转换 | AC-3.2~AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；各通道保留当前事实。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 7；space/Public Native API 12；Static API 23；部分 Static builder API 26。
- **API 版本号策略:** canonical SDK 与 public native header 为权威；中间实现注记冲突只列风险。

| 风险 | 当前证据 | 兼容处理 |
|------|----------|----------|
| ArkTS Native Bridge 解析 main space 时读取 cross 参数 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_flex_bridge.cpp:53-67` | 记录为实现风险；以非对称值回归，不定义为公开语义 |
| options reset 未同步调用独立 space reset | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_flex_bridge.cpp:72-79`; `frameworks/core/interfaces/native/node/flex_modifier.cpp:113-160` | 删除/替换 modifier 时检查旧 space 残留；本次不修改实现 |
| Dynamic、Static、Native 的非法值/default/reset 不完全相同 | 各桥接与 style_modifier 路径 | 按通道验收，不做跨通道隐式归一 |
| canonical Dynamic `FlexModifier.d.ts` 当前未提供，而 Static modifier 已登记 | `interface/sdk-js/api/arkui/FlexModifier.static.d.ets:24-32` | 不臆造缺失签名；只登记真实 canonical 文件 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 多入口同模型 | 各通道最终更新 FlexModelNG/LayoutProperty，但自行负责解析与 reset | AC-1.1~AC-3.4 |
| SDK 权威 | 对外可见性以 canonical SDK/native header 为准 | AC-2.5, AC-4.1~AC-4.4 |
| 模式切换 | NoWrap/Wrap 更新必须使 Pattern 后续选择对应算法 | AC-1.5 |
| 错误隔离 | Native 参数错误不得进入正常 Model 写入 | AC-3.3~AC-3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | options 更新不新增额外布局遍历，继续以 Measure dirty 驱动 | Trace | Model/Property 路径 |
| 功耗 | 不新增后台任务或定时器 | 代码审查 | VM-1~VM-4 |
| 内存 | modifier 状态随 FrameNode/组件生命周期释放 | 生命周期 UT | ArkFlex/node modifier |
| 安全 | Native 输入在解引用/转换前完成数量和范围校验 | fuzz/代码审查 | AC-3.3~AC-3.5 |
| 可靠性 | 非法 options、空 Optional、reset 和节点失效不得崩溃 | 异常 UT | VM-1~VM-3 |
| 可测试性 | 每通道独立验证 set/reset/get 与最终 LayoutProperty | 追溯审查 | VM-1~VM-4 |
| 自动化维测 | 复用 Native 错误码与组件属性 dump | Native/Inspector UT | style_modifier/Property |
| 定界定位 | 能按 SDK→Bridge→Modifier→Model→Algorithm 分层定位 | 源码审查 | `05-ui-components/01-layout-components/05-flex/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无接口专有差异 | 相同 options 应进入同一模型 | Dynamic/Static/Native 对照测试 | AC-1.1, AC-2.1, AC-3.1 |
| 平板 | 无接口专有差异 | 窗口约束不同不改变版本可见性 | 可变窗口 + 通道对照 | AC-4.1~AC-4.4 |
| 折叠屏 | 无接口专有差异 | 状态切换后现有 options 重新布局 | 折叠态回归 | AC-1.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 间接 | 接口通道不应改变最终语义树 | AC-1.1~AC-3.2 |
| 大字体 | 间接 | 最终 Model 一致时由布局层响应子项尺寸 | AC-1.1, AC-2.1 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 间接 | 各通道配置由同一算法响应约束变化 | AC-1.5 |
| 多用户 | 否 | 无持久用户状态 | N/A |
| 版本升级 | 是 | API 7/12/23/26 是核心验收矩阵 | AC-4.1~AC-4.4 |
| 生态兼容 | 是 | 跨范式迁移需显式处理 default/reset 差异 | AC-1.3~AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Flex 多范式接口与版本兼容
  Scenario: 三通道设置相同合法 options
    Given Dynamic Static Native 分别创建 Flex
    When 三者设置相同 direction wrap justify align 和 space
    Then 各自最终 LayoutProperty 表达相同合法值
    And 使用相同算法模式

  Scenario: Native 参数数量非法
    Given 一个有效 Flex Native 节点
    When NODE_FLEX_OPTION 的 AttributeItem 参数数量不足
    Then 返回 PARAM_INVALID
    And 节点既有 options 不被正常写入路径覆盖

  Scenario: API 版本编译隔离
    Given 应用目标 API 为 23
    When 编译 Static Flex component builder
    Then 该能力可见
    And API 26 的 setFlexOptions 不可作为 API 23 契约依赖
```

## Spec 自审清单

- [x] 无占位文本
- [x] Dynamic、Modifier、Static、Native 和 legacy/NG 均有明确边界
- [x] API 7/12/23/26 可见性均映射到 canonical 文件
- [x] 实现偏差仅作为兼容风险，不提升为公共契约
- [x] AC、规则、VM 和接口矩阵闭环

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Flex Dynamic Static ArkFlex native modifier NODE_FLEX_OPTION NODE_FLEX_SPACE reset"
  - repo: "openharmony/interface_sdk-js"
    query: "Flex static setFlexOptions FlexModifier API 7 12 23 26"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/flex.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/flex.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/05-flex/design.md`
