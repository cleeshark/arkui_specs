# 特性规格

> Func-05-12-01-Feat-01 PluginComponent创建/模板/数据与事件回调：固化 PluginComponent 创建流程、template/data 传递机制、PluginSubContainer 独立管线加载、以及 onComplete/onError 事件回调的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | PluginComponent创建/模板/数据与事件回调 |
| 特性编号 | Func-05-12-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 9+（@systemapi） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | PluginComponent 创建与模板规格 | 补录 PluginComponent(options) 创建流程、PluginComponentTemplate { source, bundleName } 解析、PluginSubContainer 独立管线加载规格 |
| ADDED | 事件回调规格 | 补录 onComplete/onError 事件回调触发条件与数据格式规格 |
| ADDED | C-API 双通道规格 | 补录 Dynamic modifier (width/height/size) 和 Static modifier (Arkoala: setPluginComponentOptions/onComplete/onError) 覆盖范围规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/01-plugin-component/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 PluginComponent 并加载 Plugin 内容

**作为** 系统应用开发者,
**我想要** 通过 PluginComponent(options) 创建组件并传入 template 和 data,
**以便** 在宿主页面中嵌入外部 Plugin 的 UI 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `PluginComponent({ template: { source: 'plugin_source', bundleName: 'com.example.plugin' }, data: pluginData })` THEN 创建 PluginPattern → 创建 PluginSubContainer（独立 PipelineContext + PluginFrontend）加载 Plugin HAP 内容 | 正常 |
| AC-1.2 | WHEN template.source 为空字符串 THEN 不创建 PluginSubContainer；FireOnError 回调传递 PluginErrorData { errcode, msg } | 异常 |
| AC-1.3 | WHEN template.bundleName 为空字符串 THEN 不创建 PluginSubContainer；FireOnError 回调传递 PluginErrorData { errcode, msg } | 异常 |
| AC-1.4 | WHEN PluginSubContainer 创建失败（HAP 路径解析错误、BMS 查询失败）THEN FireOnError 回调传递 PluginErrorData | 异常 |

### US-2: 监听 Plugin 加载完成/失败事件

**作为** 系统应用开发者,
**我想要** 通过 onComplete 和 onError 回调监听 Plugin 加载状态,
**以便** 在 Plugin 加载成功或失败时执行相应处理逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Plugin 加载成功 THEN PluginManagerDelegate 触发 OnComplete 回调 → PluginEventHub 触发 onComplete 事件 → ArkTS 层回调被调用 | 正常 |
| AC-2.2 | WHEN Plugin 加载失败 THEN PluginManagerDelegate 触发 OnError 回调 → PluginEventHub 触发 onError 事件 → ArkTS 层回调收到 PluginErrorData { errcode: number, msg: string } | 正常 |
| AC-2.3 | WHEN template 变化导致重新加载 THEN 销毁旧 PluginSubContainer，创建新 PluginSubContainer，重新触发 onComplete 或 onError | 正常 |

### US-3: 通过 C-API Dynamic Modifier 更新 Plugin 尺寸

**作为** NDK 开发者,
**我想要** 通过 ArkUIPluginModifier 的 SetPluginWidth/SetPluginHeight/SetPluginSize 在运行时更新 Plugin 尺寸,
**以便** 动态调整 Plugin 显示区域大小。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 SetPluginWidth(nodeHandle, width) THEN PluginPattern 更新 RequestPluginInfo 中的 width 字段并触发重新布局 | 正常 |
| AC-3.2 | WHEN 调用 SetPluginHeight(nodeHandle, height) THEN PluginPattern 更新 RequestPluginInfo 中的 height 字段并触发重新布局 | 正常 |
| AC-3.3 | WHEN 调用 SetPluginSize(nodeHandle, width, height) THEN 同时更新 width 和 height 并触发重新布局 | 正常 |

### US-4: 通过 C-API Static Modifier 创建 PluginComponent

**作为** Arkoala 静态范式开发者,
**我想要** 通过 ArkUIPluginComponentModifier 的 ConstructImpl 创建 PluginComponent FrameNode 并设置 options 和事件回调,
**以便** 在静态范式中使用 PluginComponent。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 ConstructImpl(id, persistentId) THEN 创建 PluginNode（PluginPattern + PluginLayoutProperty + PluginEventHub） | 正常 |
| AC-4.2 | WHEN 调用 SetPluginComponentOptionsImpl(nodeHandle, options) THEN 设置 RequestPluginInfo 和 data 到 PluginLayoutProperty | 正常 |
| AC-4.3 | WHEN 调用 SetOnCompleteImpl(nodeHandle, callback) THEN 注册 onComplete 回调到 PluginEventHub | 正常 |
| AC-4.4 | WHEN 调用 SetOnErrorImpl(nodeHandle, callback) THEN 注册 onError 回调到 PluginEventHub | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1, R-2, R-3, R-5, R-6 | 已有实现 | 代码评审 | `plugin_pattern.cpp`, `plugin_sub_container.cpp` |
| AC-2.1~2.3 | R-4, R-7, R-8 | 已有实现 | 代码评审 | `plugin_pattern.cpp`, `plugin_manager_delegate.h` |
| AC-3.1~3.3 | R-9, R-10 | 已有实现 | C-API 单测 | `plugin_modifier.cpp` |
| AC-4.1~4.4 | R-11, R-12, R-13, R-14 | 已有实现 | C-API 单测 | `plugin_component_modifier.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `PluginComponent(options)` 被调用 | JSPlugin::Create 解析 template/data → PluginModel::GetInstance() 根据 IsCurrentUseNewPipeline() 返回 PluginModelNG 或 PluginModelImpl → NG 路径创建 PluginPattern | Model Dispatch 保留 legacy 路径 | AC-1.1 |
| R-2 | 行为 | PluginPattern::OnAttachToFrameNode | 注册 OnComplete/OnError 回调到 PluginEventHub；初始化 PluginManagerDelegate（注册 complete/update/error 回调）；设置 DrawDelegate 用于 PluginSubContainer 渲染结果挂载 | — | AC-1.1, AC-2.1 |
| R-3 | 行为 | PluginSubContainer 创建 | 创建独立 PipelineContext（独立 TaskExecutor + ThreadModel）+ PluginFrontend → 初始化 AssetProvider → RunPlugin 加载 JS bundle | 独立管线与宿主页面渲染隔离 | AC-1.1 |
| R-4 | 行为 | Plugin 加载成功 | PluginManagerDelegate::OnComplete → PluginPattern::FireOnCompleteEvent → PluginEventHub::FireOnComplete → ArkTS onComplete 回调 | 回调链为 ManagerDelegate→Pattern→EventHub→ArkTS | AC-2.1 |
| R-5 | 异常 | template.source 为空 | PluginPattern 不创建 PluginSubContainer；FireOnError 回调传递 PluginErrorData | source 为定位 Plugin 的必要字段 | AC-1.2 |
| R-6 | 异常 | PluginSubContainer 创建失败 | PluginManagerDelegate 进入 CREATEFAILED 状态 → PluginPattern::FireOnErrorEvent → ArkTS onError 回调 | — | AC-1.4 |
| R-7 | 行为 | Plugin 加载失败 | PluginManagerDelegate::OnError → PluginPattern::FireOnErrorEvent → PluginEventHub::FireOnError → ArkTS onError 回调收到 PluginErrorData { errcode, msg } | — | AC-2.2 |
| R-8 | 行为 | template 变化导致重新加载 | PluginPattern::OnDirtyLayoutWrapperSwap 比较新旧 RequestPluginInfo → 若 bundleName/abilityName/source 不同 → DestroyPluginSubContainer → CreateNewPluginSubContainer → 重新触发 onComplete 或 onError | 仅 template 核心字段变化触发重建 | AC-2.3 |
| R-9 | 行为 | C-API Dynamic modifier SetPluginWidth | 获取 PluginPattern → 更新 RequestPluginInfo.width → 触发 PROPERTY_UPDATE_MEASURE | 仅运行时尺寸更新 | AC-3.1 |
| R-10 | 行为 | C-API Dynamic modifier SetPluginSize | 同时更新 width 和 height → 触发 PROPERTY_UPDATE_MEASURE | — | AC-3.3 |
| R-11 | 行为 | C-API Static modifier ConstructImpl | PluginModelStatic::CreateFrameNode(id, persistentId) → 创建 PluginNode + PluginLayoutProperty + PluginEventHub | Static modifier 仅覆盖创建时配置 | AC-4.1 |
| R-12 | 行为 | C-API Static modifier SetPluginComponentOptionsImpl | 解析 options 为 RequestPluginInfo → 设置到 PluginLayoutProperty 的 REQUEST_PLUGIN_INFO 和 DATA 属性 | — | AC-4.2 |
| R-13 | 行为 | C-API Static modifier SetOnCompleteImpl | 注册 onComplete 回调到 PluginEventHub 的 OnComplete_ | — | AC-4.3 |
| R-14 | 行为 | C-API Static modifier SetOnErrorImpl | 注册 onError 回调到 PluginEventHub 的 onError_ | — | AC-4.4 |
| R-15 | 边界 | PluginManagerDelegate 生命周期状态机 | WAITINGFORSIZE → CREATING → CREATED / CREATEFAILED → RELEASED | 状态转换由平台侧资源就绪驱动 | AC-1.1 |
| R-16 | 边界 | PLUGIN_COMPONENT_SUPPORTED 编译开关 | 不支持时编译为空壳（PluginModelNG 方法为空实现） | — | AC-1.1 |
| R-17 | 异常 | template.bundleName 为空 | 不创建 PluginSubContainer；FireOnError 回调 | bundleName 为 BMS 查询必要字段 | AC-1.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1, R-2, R-3 | 代码评审 | Plugin 创建流程完整性（JSPlugin→Model→Pattern→SubContainer） |
| VM-2 | AC-1.2, R-5 | 代码评审 | 空 source 的错误处理 |
| VM-3 | AC-1.3, R-17 | 代码评审 | 空 bundleName 的错误处理 |
| VM-4 | AC-2.1, R-4 | 代码评审 | onComplete 回调链完整性 |
| VM-5 | AC-2.2, R-7 | 代码评审 | onError 回调链完整性 |
| VM-6 | AC-2.3, R-8 | 代码评审 | template 变化时 SubContainer 重建逻辑 |
| VM-7 | AC-3.1~3.3, R-9, R-10 | C-API 单测 | Dynamic modifier 尺寸更新 |
| VM-8 | AC-4.1~4.4, R-11~R-14 | C-API 单测 | Static modifier 创建与事件注册 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `PluginComponent(options: PluginComponentOptions)` | System | 创建插件组件 | `@internal/component/ets/plugin_component.d.ts` | 9 | @systemapi |
| `onComplete(callback: VoidCallback)` | System | 加载完成回调 | `@internal/component/ets/plugin_component.d.ts` | 9 | @systemapi |
| `onError(callback: PluginErrorCallback)` | System | 加载失败回调 | `@internal/component/ets/plugin_component.d.ts` | 9/18 | @systemapi |
| `PluginComponentTemplate { source, bundleName }` | System | 模板定义 | `@internal/component/ets/plugin_component.d.ts` | 9 | @systemapi |
| `PluginComponentOptions { template, data }` | System | 创建选项 | `@internal/component/ets/plugin_component.d.ts` | 9/18 | @systemapi |
| `PluginErrorData { errcode, msg }` | System | 错误数据 | `@internal/component/ets/plugin_component.d.ts` | 9/18 | @systemapi |

**C-API (NDK) 接口：**

| Modifier 类型 | 属性枚举 | 功能 | @since |
|---------------|----------|------|--------|
| Dynamic | `ArkUIPluginModifier::SetPluginWidth` | 设置宽度 | 10 |
| Dynamic | `ArkUIPluginModifier::SetPluginHeight` | 设置高度 | 10 |
| Dynamic | `ArkUIPluginModifier::SetPluginSize` | 同时设置宽高 | 10 |
| Static (Arkoala) | `ArkUIPluginComponentModifier::ConstructImpl` | 创建 FrameNode | — |
| Static (Arkoala) | `ArkUIPluginComponentModifier::SetPluginComponentOptionsImpl` | 设置创建选项 | — |
| Static (Arkoala) | `ArkUIPluginComponentModifier::SetOnCompleteImpl` | 注册完成回调 | — |
| Static (Arkoala) | `ArkUIPluginComponentModifier::SetOnErrorImpl` | 注册错误回调 | — |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `PluginComponentTemplate` | `{ source: string; bundleName: string }` | `plugin_component.d.ts` |
| `PluginComponentOptions` | `{ template: PluginComponentTemplate; data: any }` | `plugin_component.d.ts` |
| `PluginErrorData` | `{ errcode: number; msg: string }` | `plugin_component.d.ts` |
| `RequestPluginInfo` | C++ 内部结构：id, pluginName, bundleName, abilityName, moduleName, source, moduleResPath, dimension, allowUpdate, width, height, index | `plugin_request_data.h` |

### 变更/废弃 API

无变更/废弃 API。

---

## 接口规格

### 接口定义 — PluginComponent(options: PluginComponentOptions)

| 属性 | 值 |
|------|-----|
| 函数签名 | `PluginComponentAttribute PluginComponent(PluginComponentOptions options)` |
| 返回值 | `PluginComponentAttribute` — 组件属性对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | PluginComponentOptions | 是 | — | template.source 和 template.bundleName 非空时才创建 PluginSubContainer |
| options.template | PluginComponentTemplate | 是 | — | source/bundleName 必填 |
| options.data | any | 否 | null | 无约束 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | template.source 非空，bundleName 非空 | 创建 PluginSubContainer 加载 Plugin HAP 内容 | AC-1.1 |
| 2 | template.source 为空字符串 | FireOnError → PluginErrorData | AC-1.2 |
| 3 | template.bundleName 为空字符串 | FireOnError → PluginErrorData | AC-1.3 |

### 接口定义 — onComplete(callback: VoidCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `PluginComponentAttribute onComplete(VoidCallback callback)` |
| 返回值 | `PluginComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | VoidCallback () => void | 是 | — | 无约束 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Plugin 加载成功 | 回调 callback | AC-2.1 |
| 2 | template 变化重新加载成功 | 再次触发 callback | AC-2.3 |

### 接口定义 — onError(callback: PluginErrorCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `PluginComponentAttribute onError(PluginErrorCallback callback)` |
| 返回值 | `PluginComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-2.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | PluginErrorCallback (info: PluginErrorData) => void | 是 | — | info.errcode 为 number; info.msg 为 string |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Plugin 加载失败 | callback(info) | AC-2.2 |
| 2 | template.source/bundleName 为空 | callback 收到 PluginErrorData { errcode, msg } | AC-1.2, AC-1.3 |
| 3 | PluginSubContainer 创建失败 | callback 收到 PluginErrorData | AC-1.4 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** @since 9 为基础，@since 18 rectified 部分（data/errcode/msg）

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| Plugin 组件级 API 为 @systemapi | 仅系统应用可使用；EmbeddedComponent 为 @atomicservice 替代 | AC-1.1 |
| PluginSubContainer 使用独立 PipelineContext | Plugin 渲染与宿主页面渲染隔离 | AC-1.1 |
| PluginManagerDelegate 生命周期状态机 | WAITINGFORSIZE → CREATING → CREATED / CREATEFAILED → RELEASED | AC-1.4 |
| Model Dispatch 保留 legacy 路径 | FA 模型应用仍依赖 legacy PluginModelImpl | AC-1.1 |
| C-API Static modifier 仅覆盖创建时配置 | 不覆盖运行时 width/height/size 更新 | AC-4.2 |
| PLUGIN_COMPONENT_SUPPORTED 编译开关 | 控制完整编译/空壳编译 | 全 AC |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Plugin 加载延迟由 HAP 包大小和 BMS 查询决定，不设量化指标 | 集成测试 | plugin_pattern.cpp |
| 安全 | @systemapi 限制系统应用使用 | API 评审 | plugin_component.d.ts |
| 可测试性 | onComplete/onError 可通过 Mock PluginFrontend 验证 | 单测 | plugin_pattern.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | 无差异 | — | 集成测试 | — |
| 折叠屏 | PluginSubContainer 需响应折叠状态变化更新尺寸 | 需监听 display 变化 | 集成测试 | plugin_sub_container.cpp |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | Plugin 内容在独立管线中渲染，不进入宿主无障碍树 | — |
| 大字体 | 否 | Plugin 使用独立管线，大字体设置不影响宿主 | — |
| 深色模式 | 否 | Plugin 使用独立管线，深色模式不影响宿主 | — |
| 多窗口/分屏 | 是 | PluginSubContainer 需响应分屏尺寸变化 | AC-3.1~3.3 |
| 多用户 | 否 | Plugin 运行在独立进程 | — |
| 版本升级 | 否 | API 9 起行为不变 | — |
| 生态兼容 | 是 | 组件级 @systemapi 与 Manager 级 public 共存 | AC-1.1 |

---

## 行为场景

```gherkin
Feature: PluginComponent 创建与事件回调
  作为 系统应用开发者
  我想要 通过 PluginComponent 创建组件并监听 Plugin 加载状态
  以便 在宿主页面中嵌入外部 Plugin 的 UI 内容

  # ─── 创建与模板 ─────────────────────────

  Scenario: 正常创建 PluginComponent
    Given 一个宿主页面
    When 调用 PluginComponent({ template: { source: 'plugin_source', bundleName: 'com.example.plugin' }, data: { key: 'value' } })
    Then 创建 PluginPattern → PluginSubContainer（独立 PipelineContext + PluginFrontend）
    And PluginManagerDelegate 初始化并进入 WAITINGFORSIZE 状态
    And BMS 查询 Plugin HAP 包路径
    And PluginSubContainer 加载 Plugin JS bundle 并渲染

  Scenario: template.source 为空
    Given 一个宿主页面
    When 调用 PluginComponent({ template: { source: '', bundleName: 'com.example.plugin' }, data: {} })
    Then 不创建 PluginSubContainer
    And onError 回调被触发，PluginErrorData 包含错误信息

  Scenario: template.bundleName 为空
    Given 一个宿主页面
    When 调用 PluginComponent({ template: { source: 'plugin_source', bundleName: '' }, data: {} })
    Then 不创建 PluginSubContainer
    And onError 回调被触发，PluginErrorData 包含错误信息

  # ─── 事件回调 ───────────────────────────

  Scenario: Plugin 加载成功
    Given 一个 PluginComponent 已创建
    And PluginSubContainer 成功加载 Plugin HAP
    When PluginManagerDelegate 进入 CREATED 状态
    Then onComplete 回调被触发

  Scenario: Plugin 加载失败
    Given 一个 PluginComponent 已创建
    And PluginSubContainer 加载失败
    When PluginManagerDelegate 进入 CREATEFAILED 状态
    Then onError 回调被触发
    And 回调参数 PluginErrorData { errcode: number, msg: string }

  Scenario: template 变化导致重新加载
    Given 一个 PluginComponent 已创建且 Plugin 加载成功
    When 开发者更新 template.bundleName 为新的值
    Then 销毁旧 PluginSubContainer
    And 创建新 PluginSubContainer 加载新 Plugin
    And 重新触发 onComplete 或 onError

  # ─── C-API Dynamic Modifier ─────────────

  Scenario: Dynamic modifier 更新 Plugin 宽度
    Given 一个 PluginComponent FrameNode
    When 调用 ArkUIPluginModifier::SetPluginWidth(nodeHandle, 200)
    Then PluginPattern 更新 RequestPluginInfo.width = 200
    And 触发 PROPERTY_UPDATE_MEASURE 重新布局

  Scenario: Dynamic modifier 更新 Plugin 尺寸
    Given 一个 PluginComponent FrameNode
    When 调用 ArkUIPluginModifier::SetPluginSize(nodeHandle, 300, 200)
    Then PluginPattern 同时更新 width = 300, height = 200
    And 触发 PROPERTY_UPDATE_MEASURE 重新布局

  # ─── C-API Static Modifier ──────────────

  Scenario: Static modifier 创建 PluginComponent
    Given Arkoala 静态范式环境
    When 调用 ArkUIPluginComponentModifier::ConstructImpl(id, persistentId)
    Then 创建 PluginNode（PluginPattern + PluginLayoutProperty + PluginEventHub）

  Scenario: Static modifier 设置 PluginComponent 选项
    Given 一个已创建的 PluginComponent FrameNode
    When 调用 SetPluginComponentOptionsImpl(nodeHandle, { source, bundleName, data })
    Then PluginLayoutProperty 的 REQUEST_PLUGIN_INFO 和 DATA 属性被设置
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：创建/模板/数据/事件回调/C-API 双通道；不做什么：Manager push/request/on/off 机制）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "PluginPattern 如何检测 RequestPluginInfo 变化并决定是否重新创建 PluginSubContainer"
  - repo: "openharmony/ace_engine"
    query: "PluginSubContainer 创建独立 PipelineContext 的完整流程"
  - repo: "openharmony/ace_engine"
    query: "PluginManagerDelegate 生命周期状态机 WAITINGFORSIZE CREATING CREATED CREATEFAILED RELEASED"
  - repo: "openharmony/ace_engine"
    query: "C-API plugin_modifier 与 plugin_component_modifier 的覆盖范围差异"
```

**关键文档：**
- SDK API：`interface/sdk-js/api/@internal/component/ets/plugin_component.d.ts`
- Pattern 层：`frameworks/core/components_ng/pattern/plugin/plugin_pattern.h`
- Sub-Container 层：`frameworks/core/components/plugin/plugin_sub_container.h`
- Manager Delegate：`frameworks/core/components/plugin/plugin_manager_delegate.h`
