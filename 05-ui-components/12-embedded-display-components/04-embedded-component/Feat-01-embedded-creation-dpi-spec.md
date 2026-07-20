# 特性规格

> Func-05-12-04-Feat-01 EmbeddedComponent创建/选项/DPI策略：固化 EmbeddedComponent 创建流程、Want/EmbeddedType 传递、EmbeddedUIExtensionConfig 构建、DPI跟随策略（densityDpi）、窗口模式跟随策略（isWindowModeFollowHost）、Placeholder 机制、最小尺寸约束（10vp×10vp）以及 C-API NDK 创建与选项的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | EmbeddedComponent创建/选项/DPI策略 |
| 特性编号 | Func-05-12-04-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 12+（@atomicservice @stagemodelonly）；选项增强 API 26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | EmbeddedComponent 创建与 Want 规格 | 补录 EmbeddedComponent(want, type) 和 EmbeddedComponent(want, type, options) 创建流程、EmbeddedUIExtensionConfig 构建、UIExtensionNode（tag=EMBEDDED_COMPONENT_ETS_TAG）创建规格 |
| ADDED | DPI 与窗口模式策略规格 | 补录 dpiFollowStrategy → densityDpi(bool) 映射、windowModeFollowStrategy → isWindowModeFollowHost(bool) 映射规格 |
| ADDED | Placeholder 机制规格 | 补录 placeholder(INITIAL) 和 areaChangePlaceholder(UNDEFINED/ROTATION/FOLD_TO_EXPAND) 到 placeholderMap 的解析与挂载规格 |
| ADDED | 最小尺寸约束规格 | 补录 10vp × 10vp 最小尺寸设置规格 |
| ADDED | C-API NDK 创建与选项规格 | 补录 ARKUI_NODE_EMBEDDED_COMPONENT、NODE_EMBEDDED_COMPONENT_WANT/OPTION、ArkUIEmbeddedComponentModifier（Dynamic）、GENERATED_ArkUIEmbeddedComponentModifier（Static stub）规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/04-embedded-component/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 EmbeddedComponent 并传入 Want 与类型

**作为** 三方应用开发者,
**我想要** 通过 EmbeddedComponent(loader: Want, type: EmbeddedType) 创建组件并传入 Want 和 EmbeddedType,
**以便** 在宿主页面中嵌入 UIExtensionAbility 的 UI 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `EmbeddedComponent({ bundleName: 'com.example', abilityName: 'ExampleAbility' }, EmbeddedType)` THEN JSEmbeddedComponent::Create 解析 Want → WantWrap → 构建 EmbeddedUIExtensionConfig → UIExtensionModelNG::Create 创建 UIExtensionNode（tag=EMBEDDED_COMPONENT_ETS_TAG, sessionType=EMBEDDED_UI_EXTENSION, usage=EMBEDDED） → Push ViewStackProcessor | 正常 |
| AC-1.2 | WHEN Want 为空或无效 THEN 不创建 UIExtensionNode；SessionWrapperImpl 不创建 Session | 异常 |
| AC-1.3 | WHEN EmbeddedComponent 创建成功 THEN 设置默认尺寸 width=10vp, height=10vp, minWidth=10vp, minHeight=10vp | 正常 |
| AC-1.4 | WHEN 开发者通过 width/height 设置更大尺寸 THEN 覆盖默认尺寸，但不低于 10vp × 10vp 最小约束 | 正常 |

### US-2: DPI 与窗口模式策略配置

**作为** 三方应用开发者,
**我想要** 通过 EmbeddedOptions 的 dpiFollowStrategy 和 windowModeFollowStrategy 控制 DPI 和窗口模式跟随行为,
**以便** 根据业务需求决定嵌入式组件是否跟随宿主的 DPI 和窗口模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `EmbeddedComponent(want, type, { dpiFollowStrategy: EmbeddedDpiFollowStrategy.FOLLOW_HOST_DPI })` THEN JSEmbeddedComponent::Create 将 dpiFollowStrategy=0 映射为 densityDpi=true → UIExtensionPattern::SetDensityDpi(true) → SessionViewportConfig.isDensityFollowHost_=true | 正常 |
| AC-2.2 | WHEN 调用 `EmbeddedComponent(want, type, { dpiFollowStrategy: EmbeddedDpiFollowStrategy.FOLLOW_UI_EXTENSION_ABILITY_DPI })` THEN dpiFollowStrategy=1 映射为 densityDpi=false → UIExtensionPattern::SetDensityDpi(false) → SessionViewportConfig.isDensityFollowHost_=false | 正常 |
| AC-2.3 | WHEN 调用 `EmbeddedComponent(want, type, { windowModeFollowStrategy: EmbeddedWindowModeFollowStrategy.FOLLOW_HOST_WINDOW_MODE })` THEN windowModeFollowStrategy=0 映射为 isWindowModeFollowHost=true → UIExtensionPattern::SetIsWindowModeFollowHost(true) → NotifyHostWindowMode | 正常 |
| AC-2.4 | WHEN 调用 `EmbeddedComponent(want, type, { windowModeFollowStrategy: EmbeddedWindowModeFollowStrategy.FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE })` THEN windowModeFollowStrategy=1 映射为 isWindowModeFollowHost=false → UIExtensionPattern::SetIsWindowModeFollowHost(false) | 正常 |
| AC-2.5 | WHEN 未传入 EmbeddedOptions（constructor overload 1, @since 12）THEN densityDpi=false, isWindowModeFollowHost=false（默认不跟随宿主） | 正常 |

### US-3: Placeholder 机制配置

**作为** 三方应用开发者,
**我想要** 通过 EmbeddedOptions 的 placeholder 和 areaChangePlaceholder 配置不同场景下的占位内容,
**以便** 在 Extension 内容加载前或状态变化时显示占位 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 传入 `options: { placeholder: ComponentContent }` THEN JSEmbeddedComponent::InsertPlaceholderObj 将 placeholder 映射为 PlaceholderType::INITIAL → 加入 placeholderMap → UIExtensionPattern::SetPlaceholderMap | 正常 |
| AC-3.2 | WHEN 传入 `options: { areaChangePlaceholder: { UNDEFINED: ComponentContent, ROTATION: ComponentContent, FOLD_TO_EXPAND: ComponentContent } }` THEN ResolveAreaPlaceholderParams 将字符串键映射为对应 PlaceholderType → 加入 placeholderMap | 正常 |
| AC-3.3 | WHEN UIExtensionPattern 收到 placeholderMap THEN 在 curPlaceholderType_=NONE 时挂载 INITIAL placeholder；Extension 内容就绪后 ReplacePlaceholderByContent 替换 placeholder | 正常 |
| AC-3.4 | WHEN 旋转/折叠状态变化 THEN UIExtensionPattern 判断 IsCanMountPlaceholder(type > curPlaceholderType_) → MountPlaceholderNode 挂载对应类型 placeholder | 正常 |
| AC-3.5 | WHEN placeholder 或 areaChangePlaceholder 中的 ComponentContent 的 builderNode_ 为空或无效 THEN 跳过该 placeholder 映射，不加入 placeholderMap | 异常 |

### US-4: C-API NDK 创建与选项配置

**作为** NDK 开发者,
**我想要** 通过 ARKUI_NODE_EMBEDDED_COMPONENT 创建 EmbeddedComponent 节点，并通过 NODE_EMBEDDED_COMPONENT_WANT 和 NODE_EMBEDDED_COMPONENT_OPTION 设置 Want 和回调选项,
**以便** 在 NDK 场景中使用 EmbeddedComponent。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 通过 ArkUI_NodeAdapter 创建 ARKUI_NODE_EMBEDDED_COMPONENT 节点 THEN ArkUIEmbeddedComponentModifier 创建 UIExtensionNode（UIExtensionPattern, sessionType=EMBEDDED_UI_EXTENSION） | 正常 |
| AC-4.2 | WHEN 设置 NODE_EMBEDDED_COMPONENT_WANT 属性（AbilityBase_Want） THEN ArkUIEmbeddedComponentModifier::setEmbeddedComponentWant 将 CWant 转换为 AAFwk::Want → UIExtensionAdapter::SetEmbeddedComponentWant → UIExtensionPattern::UpdateWant | 正常 |
| AC-4.3 | WHEN 设置 NODE_EMBEDDED_COMPONENT_OPTION 属性（ArkUI_EmbeddedComponentOption） THEN ArkUIEmbeddedComponentModifier::setEmbeddedComponentOption 从 option 提取 onError/onTerminated → UIExtensionAdapter::SetEmbeddedComponentOnError/SetEmbeddedComponentOnTerminated | 正常 |
| AC-4.4 | WHEN CWant 转换失败（CWantManager::TransformToWant 返回错误码） THEN SetEmbeddedComponentWant 记录错误日志，不更新 Want | 异常 |
| AC-4.5 | WHEN 通过 GENERATED_ArkUIEmbeddedComponentModifier::ConstructImpl(id, flags) THEN 创建 UIExtensionNode + UIExtensionPattern(sessionType=EMBEDDED_UI_EXTENSION) + 设置 minWidth/minHeight=10vp | 正常 |
| AC-4.6 | WHEN 通过 GENERATED_ArkUIEmbeddedComponentModifier 调用 SetEmbeddedComponentOptions0Impl/SetEmbeddedComponentOptions1Impl THEN 输出 LOGE "not supported"，无实际效果 | 边界 |
| AC-4.7 | WHEN 通过 OH_ArkUI_EmbeddedComponentOption_Create() THEN 创建 ArkUI_EmbeddedComponentOption 结构体 { onError=nullptr, onTerminated=nullptr } | 正常 |
| AC-4.8 | WHEN 通过 OH_ArkUI_EmbeddedComponentOption_SetOnError(option, callback) THEN 设置 option->onError 为回调函数指针 | 正常 |
| AC-4.9 | WHEN 通过 OH_ArkUI_EmbeddedComponentOption_SetOnTerminated(option, callback) THEN 设置 option->onTerminated 为回调函数指针 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1, R-2, R-3, R-4, R-5, R-6 | 已有实现 | 代码评审 | `js_embedded_component.cpp`, `ui_extension_model_ng.cpp` |
| AC-2.1~2.5 | R-7, R-8, R-9, R-10 | 已有实现 | 代码评审 | `js_embedded_component.cpp:164-170` |
| AC-3.1~3.5 | R-11, R-12, R-13, R-14, R-15 | 已有实现 | 代码评审 | `js_embedded_component.cpp:68-144` |
| AC-4.1~4.9 | R-16, R-17, R-18, R-19, R-20, R-21, R-22, R-23, R-24 | 已有实现 | C-API 单测 | `embeddedComponent_modifier.cpp`, `embedded_component_modifier.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `EmbeddedComponent(want, type)` 被调用 | JSEmbeddedComponent::Create 解析 Want → WantWrap → 构建 EmbeddedUIExtensionConfig → UIExtensionModelNG::Create 创建 UIExtensionNode（tag=EMBEDDED_COMPONENT_ETS_TAG, sessionType=EMBEDDED_UI_EXTENSION） | — | AC-1.1 |
| R-2 | 行为 | UIExtensionModelNG::Create(EmbeddedUIExtensionConfig) | 创建 UIExtensionNode + UIExtensionPattern（transferringCaller=false, isModal=false, sessionType=EMBEDDED_UI_EXTENSION） → SetWantWrap/SetPlaceholderMap/SetDensityDpi/SetIsWindowModeFollowHost → Push ViewStackProcessor | — | AC-1.1 |
| R-3 | 行为 | EmbeddedComponent 创建成功 | SetWidth/SetHeight/SetMinWidth/SetMinHeight = EMBEDDED_COMPONENT_MIN_WIDTH/HEIGHT (10vp) | 10vp 为强制最小尺寸 | AC-1.3 |
| R-4 | 行为 | 开发者通过 width/height 设置更大尺寸 | 覆盖默认尺寸，minWidth/minHeight 保证不低于 10vp | — | AC-1.4 |
| R-5 | 异常 | Want 为空或无效 | 不创建 UIExtensionNode；SessionWrapperImpl 不创建 Session | — | AC-1.2 |
| R-6 | 边界 | UIExtensionPattern::OnAttachToFrameNode | 注册回调、初始化 Placeholder、设置 DrawDelegate；SetNeedCheckWindowSceneId(true) | EMBEDDED 用法需要检查 WindowSceneId | AC-1.1 |
| R-7 | 行为 | dpiFollowStrategy=FOLLOW_HOST_DPI(0) | JSEmbeddedComponent::Create 映射为 densityDpi=true → Pattern::SetDensityDpi(true) → SessionViewportConfig.isDensityFollowHost_=true | 枚举→bool 映射为设计决策 | AC-2.1 |
| R-8 | 行为 | dpiFollowStrategy=FOLLOW_UI_EXTENSION_ABILITY_DPI(1) | 映射为 densityDpi=false → Pattern::SetDensityDpi(false) | — | AC-2.2 |
| R-9 | 行为 | windowModeFollowStrategy=FOLLOW_HOST_WINDOW_MODE(0) | 映射为 isWindowModeFollowHost=true → Pattern::SetIsWindowModeFollowHost(true) → NotifyHostWindowMode | — | AC-2.3 |
| R-10 | 行为 | windowModeFollowStrategy=FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE(1) | 映射为 isWindowModeFollowHost=false → Pattern::SetIsWindowModeFollowHost(false) | — | AC-2.4 |
| R-11 | 行为 | options.placeholder 传入 | InsertPlaceholderObj 将 ComponentContent.builderNode_.nodePtr_ 映射为 FrameNode → PlaceholderType::INITIAL → placeholderMap | — | AC-3.1 |
| R-12 | 行为 | options.areaChangePlaceholder 传入 | ResolveAreaPlaceholderParams 将字符串键(UNDEFINED/ROTATION/FOLD_TO_EXPAND)映射为 PlaceholderType → placeholderMap | — | AC-3.2 |
| R-13 | 行为 | UIExtensionPattern 收到 placeholderMap | curPlaceholderType_=NONE → MountPlaceholderNode(INITIAL)；Extension 内容就绪 → ReplacePlaceholderByContent | — | AC-3.3 |
| R-14 | 行为 | 旋转/折叠状态变化 | IsCanMountPlaceholder(type > curPlaceholderType_) → MountPlaceholderNode(对应类型) | PlaceholderType 按优先级挂载 | AC-3.4 |
| R-15 | 异常 | ComponentContent.builderNode_ 为空或无效 | 跳过该 placeholder 映射，不加入 placeholderMap | — | AC-3.5 |
| R-16 | 行为 | C-API 创建 ARKUI_NODE_EMBEDDED_COMPONENT | ArkUIEmbeddedComponentModifier 创建 UIExtensionNode + UIExtensionPattern(sessionType=EMBEDDED_UI_EXTENSION) | — | AC-4.1 |
| R-17 | 行为 | C-API NODE_EMBEDDED_COMPONENT_WANT | setEmbeddedComponentWant → CWant→AAFwk::Want → UIExtensionAdapter::SetEmbeddedComponentWant → Pattern::UpdateWant | CWant 转换依赖 AAFwk::CWantManager | AC-4.2 |
| R-18 | 行为 | C-API NODE_EMBEDDED_COMPONENT_OPTION | setEmbeddedComponentOption → 提取 onError/onTerminated → UIExtensionAdapter::SetEmbeddedComponentOnError/SetEmbeddedComponentOnTerminated → Pattern 回调注册 | — | AC-4.3 |
| R-19 | 异常 | CWant 转换失败 | SetEmbeddedComponentWant 记录 LOGE，不更新 Want | — | AC-4.4 |
| R-20 | 行为 | C-API Static ConstructImpl | UIExtensionStatic::CreateFrameNode(id, EMBEDDED_UI_EXTENSION) → 创建 UIExtensionNode + 10vp 最小尺寸 | 仅 EMBEDDED_UI_EXTENSION 分支走 CreateEmbeddedComponent | AC-4.5 |
| R-21 | 边界 | C-API Static SetEmbeddedComponentOptions | LOGE "not supported"，无实际效果 | Arkoala 尚未完整支持 | AC-4.6 |
| R-22 | 行为 | OH_ArkUI_EmbeddedComponentOption_Create | 创建 ArkUI_EmbeddedComponentOption { onError=nullptr, onTerminated=nullptr } | — | AC-4.7 |
| R-23 | 行为 | OH_ArkUI_EmbeddedComponentOption_SetOnError | 设置 option->onError 为回调函数指针 | — | AC-4.8 |
| R-24 | 行为 | OH_ArkUI_EmbeddedComponentOption_SetOnTerminated | 设置 option->onTerminated 为回调函数指针 | — | AC-4.9 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1, R-2, R-6 | 代码评审 | EmbeddedComponent 创建流程完整性（JSEmbedded→Model→Pattern→Node） |
| VM-2 | AC-1.3~1.4, R-3, R-4 | 代码评审 | 最小尺寸约束（10vp × 10vp）和开发者尺寸覆盖 |
| VM-3 | AC-1.2, R-5 | 代码评审 | 无效 Want 的错误处理 |
| VM-4 | AC-2.1~2.5, R-7~R-10 | 代码评审 | DPI 和窗口模式策略映射 |
| VM-5 | AC-3.1~3.5, R-11~R-15 | 代码评审 | Placeholder 机制解析和挂载 |
| VM-6 | AC-4.1~4.3, R-16~R-18 | C-API 单测 | Dynamic modifier Want 和 Option |
| VM-7 | AC-4.5, R-20 | C-API 单测 | Static modifier ConstructImpl |
| VM-8 | AC-4.6, R-21 | 代码评审 | Static modifier stub 行为 |
| VM-9 | AC-4.7~4.9, R-22~R-24 | C-API 单测 | Option 对象创建和回调设置 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `EmbeddedComponent(loader: Want, type: EmbeddedType)` | AtomicService | 创建嵌入式组件 | SDK repo | 12 | @atomicservice @stagemodelonly |
| `EmbeddedComponent(loader: Want, type: EmbeddedType, options: EmbeddedOptions)` | AtomicService | 创建嵌入式组件（含选项） | SDK repo | 26.0.0 | @atomicservice |
| `EmbeddedOptions { placeholder?, areaChangePlaceholder?, dpiFollowStrategy?, windowModeFollowStrategy? }` | AtomicService | 创建选项 | SDK repo | 26.0.0 | @atomicservice |
| `EmbeddedDpiFollowStrategy { FOLLOW_HOST_DPI = 0, FOLLOW_UI_EXTENSION_ABILITY_DPI = 1 }` | AtomicService | DPI 策略枚举 | SDK repo | 26.0.0 | @atomicservice |
| `EmbeddedWindowModeFollowStrategy { FOLLOW_HOST_WINDOW_MODE = 0, FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE = 1 }` | AtomicService | 窗口模式策略枚举 | SDK repo | 26.0.0 | @atomicservice |
| `TerminationInfo { code: number, want?: Want }` | AtomicService | 终止信息 | SDK repo | 12 | @atomicservice |

**C-API (NDK) 接口：**

| Modifier 类型 | 属性枚举/接口 | 功能 | @since |
|---------------|---------------|------|--------|
| NDK Node Type | `ARKUI_NODE_EMBEDDED_COMPONENT` | 节点类型枚举 | 20 |
| NDK Attribute | `NODE_EMBEDDED_COMPONENT_WANT` | Want 属性 | 20 |
| NDK Attribute | `NODE_EMBEDDED_COMPONENT_OPTION` | 选项属性（含回调） | 20 |
| Dynamic | `ArkUIEmbeddedComponentModifier::setEmbeddedComponentWant` | 设置 Want | 20 |
| Dynamic | `ArkUIEmbeddedComponentModifier::setEmbeddedComponentOption` | 设置选项（含回调） | 20 |
| Dynamic | `ArkUIEmbeddedComponentModifier::setOnTerminated/resetOnTerminated` | 设置/重置 onTerminated | 20 |
| Dynamic | `ArkUIEmbeddedComponentModifier::setOnError/resetOnError` | 设置/重置 onError | 20 |
| Static (Arkoala) | `GENERATED_ArkUIEmbeddedComponentModifier::ConstructImpl` | 创建 FrameNode（仅此方法有效） | — |
| Static (Arkoala) | `GENERATED_ArkUIEmbeddedComponentModifier::SetEmbeddedComponentOptions*` | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIEmbeddedComponentModifier::SetOnTerminatedImpl/SetOnErrorImpl/SetOnDrawReadyImpl` | stub（LOGE "not supported"） | — |
| C-API Option | `OH_ArkUI_EmbeddedComponentOption_Create` | 创建 Option | 20 |
| C-API Option | `OH_ArkUI_EmbeddedComponentOption_Dispose` | 销毁 Option | 20 |
| C-API Option | `OH_ArkUI_EmbeddedComponentOption_SetOnError` | 设置 onError | 20 |
| C-API Option | `OH_ArkUI_EmbeddedComponentOption_SetOnTerminated` | 设置 onTerminated | 20 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `EmbeddedType` | 枚举（推测在 SDK repo 定义，ace_engine 未包含） | SDK repo |
| `EmbeddedOptions` | `{ placeholder?, areaChangePlaceholder?, dpiFollowStrategy?, windowModeFollowStrategy? }` | SDK repo |
| `TerminationInfo` | `{ code: number; want?: Want }` | SDK repo |
| `EmbeddedUIExtensionConfig` | C++ 内部结构：wantWrap, sessionType=EMBEDDED_UI_EXTENSION, placeholderMap, densityDpi(bool), isWindowModeFollowHost(bool) | `ui_extension_model.h:44-50` |
| `PlaceholderType` | C++ 枚举：NONE=0, UNDEFINED=1, ROTATION=2, FOLD_TO_EXPAND=3, INITIAL=4 | `ui_extension_config.h:24-30` |
| `ArkUI_EmbeddedComponentOption` | C 结构：{ onError: void*, onTerminated: void* } | `embeddedComponent_option.h:25-28` |

### 变更/废弃 API

无变更/废弃 API。

---

## 接口规格

### 接口定义 — EmbeddedComponent(loader: Want, type: EmbeddedType)

| 属性 | 值 |
|------|-----|
| 函数签名 | `EmbeddedComponentAttribute EmbeddedComponent(Want loader, EmbeddedType type)` |
| 返回值 | `EmbeddedComponentAttribute` — 组件属性对象 |
| 开放范围 | AtomicService (@atomicservice @stagemodelonly) |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| loader | Want | 是 | — | Want.bundleName 和 Want.abilityName 非空时才创建 Session |
| type | EmbeddedType | 是 | — | 枚举值在 SDK repo 定义，映射到 SessionType::EMBEDDED_UI_EXTENSION |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Want.bundleName 和 abilityName 非空，type 为合法 EmbeddedType | 创建 UIExtensionNode + UIExtensionPattern(sessionType=EMBEDDED_UI_EXTENSION) → 设置最小尺寸 10vp × 10vp | AC-1.1, AC-1.3 |
| 2 | Want 为空或无效 | 不创建 UIExtensionNode | AC-1.2 |

### 接口定义 — EmbeddedComponent(loader: Want, type: EmbeddedType, options: EmbeddedOptions)

| 属性 | 值 |
|------|-----|
| 函数签名 | `EmbeddedComponentAttribute EmbeddedComponent(Want loader, EmbeddedType type, EmbeddedOptions options)` |
| 返回值 | `EmbeddedComponentAttribute` — 组件属性对象 |
| 开放范围 | AtomicService (@atomicservice @since 26.0.0) |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2, AC-3.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| loader | Want | 是 | — | 同 overload 1 |
| type | EmbeddedType | 是 | — | 同 overload 1 |
| options | EmbeddedOptions | 否 | — | 含 placeholder/areaChangePlaceholder/dpiFollowStrategy/windowModeFollowStrategy |
| options.placeholder | ComponentContent | 否 | null | builderNode_ 须有效 |
| options.areaChangePlaceholder | object | 否 | null | 键为 UNDEFINED/ROTATION/FOLD_TO_EXPAND |
| options.dpiFollowStrategy | EmbeddedDpiFollowStrategy | 否 | FOLLOW_UI_EXTENSION_ABILITY_DPI(1) → densityDpi=false | 0 或 1 |
| options.windowModeFollowStrategy | EmbeddedWindowModeFollowStrategy | 否 | FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE(1) → isWindowModeFollowHost=false | 0 或 1 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | dpiFollowStrategy=FOLLOW_HOST_DPI(0) | densityDpi=true, DPI 跟随宿主 | AC-2.1 |
| 2 | dpiFollowStrategy=FOLLOW_UI_EXTENSION_ABILITY_DPI(1) | densityDpi=false, DPI 跟随 Extension | AC-2.2 |
| 3 | windowModeFollowStrategy=FOLLOW_HOST_WINDOW_MODE(0) | isWindowModeFollowHost=true | AC-2.3 |
| 4 | windowModeFollowStrategy=FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE(1) | isWindowModeFollowHost=false | AC-2.4 |
| 5 | options 未传入 | densityDpi=false, isWindowModeFollowHost=false | AC-2.5 |
| 6 | options.placeholder 有效 ComponentContent | 映射为 PlaceholderType::INITIAL | AC-3.1 |
| 7 | options.areaChangePlaceholder 有效 | 映射为对应 PlaceholderType | AC-3.2 |
| 8 | ComponentContent.builderNode_ 无效 | 跳过映射 | AC-3.5 |

### 接口定义 — NODE_EMBEDDED_COMPONENT_WANT (C-API)

| 属性 | 值 |
|------|-----|
| 属性枚举 | `NODE_EMBEDDED_COMPONENT_WANT` |
| 操作类型 | Set（ArkUI_AttributeItem.object = AbilityBase_Want*） |
| 开放范围 | NDK public |
| 错误码 | N/A |
| 关联 AC | AC-4.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 约束条件 |
|------|------|------|----------|
| .object | AbilityBase_Want* | 是 | CWant 转换依赖 AAFwk::CWantManager |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | AbilityBase_Want 有效 | CWant→AAFwk::Want → Pattern::UpdateWant | AC-4.2 |
| 2 | CWant 转换失败 | LOGE 记录错误，不更新 Want | AC-4.4 |

### 接口定义 — NODE_EMBEDDED_COMPONENT_OPTION (C-API)

| 属性 | 值 |
|------|-----|
| 属性枚举 | `NODE_EMBEDDED_COMPONENT_OPTION` |
| 操作类型 | Set（ArkUI_AttributeItem.object = ArkUI_EmbeddedComponentOption*） |
| 开放范围 | NDK public |
| 错误码 | N/A |
| 关联 AC | AC-4.3 |

**参数约束：**

| 参数 | 类型 | 必填 | 约束条件 |
|------|------|------|----------|
| .object | ArkUI_EmbeddedComponentOption* | 是 | 包含 onError 和 onTerminated 回调指针 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | option->onError 非空 | 设置 Pattern::SetOnErrorCallback | AC-4.3 |
| 2 | option->onTerminated 非空 | 设置 Pattern::SetOnTerminatedCallback | AC-4.3 |
| 3 | option 为 null | 不设置任何回调 | — |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12（@atomicservice @stagemodelonly），C-API @since 20
- **API 版本号策略:** overload 1 @since 12；overload 2（含 EmbeddedOptions）@since 26.0.0

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| EmbeddedComponent 为 @atomicservice（非 @systemapi） | 三方应用可直接使用，与 UIExtensionComponent 权限差异明确 | AC-1.1 |
| 与 UIExtensionComponent 共享 UIExtensionPattern | 通过 UIExtensionUsage::EMBEDDED 和 sessionType_ 区分行为 | AC-1.1 |
| EmbeddedType 枚举不在 ace_engine 中定义 | SDK repo 定义，ace_engine 接收 int32_t 映射到 SessionType | AC-1.1 |
| DPI/窗口模式策略 C++ 层使用 bool | SDK 层枚举→C++层 bool 映射（ADR-3） | AC-2.1~2.4 |
| 最小尺寸 10vp × 10vp | 强制约束，开发者设置的尺寸不低于此值 | AC-1.3 |
| C-API Static modifier 为 stub | 仅 ConstructImpl 有效，标注为已知限制 | AC-4.6 |
| SessionWrapperImpl 跨进程通信 | 依赖 Rosen::ExtensionSession 和 ability_runtime | AC-1.1 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Session 创建延迟由跨进程通信和 Ability 启动决定，不设量化指标 | 集成测试 | ui_extension_model_ng.cpp |
| 安全 | @atomicservice 面向三方应用开放，不限制为系统应用 | API 评审 | SDK repo d.ts |
| 可测试性 | DPI/窗口模式策略可通过 Mock SessionViewportConfig 验证 | 单测 | ui_extension_pattern.h |
| 可测试性 | Placeholder 机制可通过 Mock FrameNode 验证 | 单测 | js_embedded_component.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | DPI 策略影响密度显示 | dpiFollowStrategy 决定密度来源 | 集成测试 | ui_extension_model_ng.cpp |
| 折叠屏 | areaChangePlaceholder.FOLD_TO_EXPAND 触发 | PlaceholderType::FOLD_TO_EXPAND 挂载 | 集成测试 | js_embedded_component.cpp |
| 旋转屏 | areaChangePlaceholder.ROTATION 触发 | PlaceholderType::ROTATION 挂载 | 集成测试 | js_embedded_component.cpp |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Extension 内容通过 AccessibilityChildTreeCallback 进入宿主无障碍树 | AC-1.1 |
| 大字体 | 是 | dpiFollowStrategy=FOLLOW_HOST_DPI 时大字体跟随宿主 | AC-2.1 |
| 深色模式 | 否 | Extension 使用独立进程，深色模式由 Extension 自行处理 | — |
| 多窗口/分屏 | 是 | windowModeFollowStrategy 决定窗口模式跟随 | AC-2.3 |
| 多用户 | 否 | Extension 运行在独立进程 | — |
| 版本升级 | 否 | API 12 起行为不变，26.0.0 选项增强向后兼容 | — |
| 生态兼容 | 是 | @atomicservice 与 @systemapi（UIExtensionComponent）共存 | AC-1.1 |

---

## 行为场景

```gherkin
Feature: EmbeddedComponent 创建与选项配置
  作为 三方应用开发者
  我想要 通过 EmbeddedComponent 创建组件并配置 DPI/窗口模式策略/Placeholder
  以便 在宿主页面中嵌入 UIExtensionAbility 的 UI 内容

  # ─── 创建与 Want ─────────────────────────

  Scenario: 正常创建 EmbeddedComponent（overload 1）
    Given 一个宿主页面
    When 调用 EmbeddedComponent({ bundleName: 'com.example', abilityName: 'ExampleAbility' }, EmbeddedType)
    Then JSEmbeddedComponent::Create 解析 Want → WantWrap → EmbeddedUIExtensionConfig
    And UIExtensionModelNG::Create 创建 UIExtensionNode（tag=EMBEDDED_COMPONENT_ETS_TAG）
    And UIExtensionPattern sessionType_=EMBEDDED_UI_EXTENSION, usage_=EMBEDDED
    And 设置默认尺寸 width=10vp, height=10vp, minWidth=10vp, minHeight=10vp

  Scenario: 无效 Want
    Given 一个宿主页面
    When 传入 Want 为空
    Then 不创建 UIExtensionNode
    And SessionWrapperImpl 不创建 Session

  # ─── DPI 策略 ────────────────────────────

  Scenario: DPI 跟随宿主
    Given 一个宿主页面
    When 调用 EmbeddedComponent(want, type, { dpiFollowStrategy: FOLLOW_HOST_DPI })
    Then densityDpi=true
    And SessionViewportConfig.isDensityFollowHost_=true

  Scenario: DPI 跟随 Extension
    Given 一个宿主页面
    When 调用 EmbeddedComponent(want, type, { dpiFollowStrategy: FOLLOW_UI_EXTENSION_ABILITY_DPI })
    Then densityDpi=false
    And SessionViewportConfig.isDensityFollowHost_=false

  # ─── 窗口模式策略 ─────────────────────────

  Scenario: 窗口模式跟随宿主
    Given 一个宿主页面
    When 调用 EmbeddedComponent(want, type, { windowModeFollowStrategy: FOLLOW_HOST_WINDOW_MODE })
    Then isWindowModeFollowHost=true
    And NotifyHostWindowMode 分发宿主窗口模式

  Scenario: 窗口模式跟随 Extension
    Given 一个宿主页面
    When 调用 EmbeddedComponent(want, type, { windowModeFollowStrategy: FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE })
    Then isWindowModeFollowHost=false

  # ─── Placeholder ─────────────────────────

  Scenario: 设置默认 placeholder
    Given 一个宿主页面
    When 调用 EmbeddedComponent(want, type, { placeholder: ComponentContent })
    Then placeholder 映射为 PlaceholderType::INITIAL 加入 placeholderMap
    And UIExtensionPattern 挂载 INITIAL placeholder

  Scenario: 设置 areaChangePlaceholder
    Given 一个宿主页面
    When 调用 EmbeddedComponent(want, type, { areaChangePlaceholder: { UNDEFINED: content1, ROTATION: content2, FOLD_TO_EXPAND: content3 } })
    Then UNDEFINED→PlaceholderType::UNDEFINED, ROTATION→PlaceholderType::ROTATION, FOLD_TO_EXPAND→PlaceholderType::FOLD_TO_EXPAND
    And placeholderMap 包含三种 areaChange 类型

  Scenario: 无效 ComponentContent 跳过
    Given 一个宿主页面
    When 传入 placeholder 的 ComponentContent.builderNode_ 为空
    Then 跳过该 placeholder 映射

  # ─── C-API NDK ────────────────────────────

  Scenario: C-API 创建 EmbeddedComponent 节点
    Given NDK 开发环境
    When 通过 ArkUI_NodeAdapter 创建 ARKUI_NODE_EMBEDDED_COMPONENT
    Then 创建 UIExtensionNode + UIExtensionPattern(sessionType=EMBEDDED_UI_EXTENSION)

  Scenario: C-API 设置 Want
    Given 一个已创建的 EmbeddedComponent FrameNode
    When 设置 NODE_EMBEDDED_COMPONENT_WANT 属性（AbilityBase_Want*）
    Then CWant 转换为 AAFwk::Want → UIExtensionPattern::UpdateWant

  Scenario: C-API CWant 转换失败
    Given 一个已创建的 EmbeddedComponent FrameNode
    When AbilityBase_Want 转换失败
    Then LOGE 记录错误，不更新 Want

  Scenario: C-API 设置 Option（含回调）
    Given 一个已创建的 EmbeddedComponent FrameNode
    When 设置 NODE_EMBEDDED_COMPONENT_OPTION（ArkUI_EmbeddedComponentOption*）
    And option->onError 和 option->onTerminated 非空
    Then 设置 Pattern::SetOnErrorCallback 和 SetOnTerminatedCallback

  Scenario: C-API Option 创建与回调设置
    Given NDK 开发环境
    When 调用 OH_ArkUI_EmbeddedComponentOption_Create()
    Then 创建 ArkUI_EmbeddedComponentOption { onError=nullptr, onTerminated=nullptr }
    When 调用 OH_ArkUI_EmbeddedComponentOption_SetOnError(option, callback)
    Then option->onError = callback
    When 调用 OH_ArkUI_EmbeddedComponentOption_SetOnTerminated(option, callback)
    Then option->onTerminated = callback

  # ─── C-API Static Modifier ─────────────────

  Scenario: Static modifier 创建 EmbeddedComponent
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIEmbeddedComponentModifier::ConstructImpl(id, flags)
    Then 创建 UIExtensionNode + UIExtensionPattern(sessionType=EMBEDDED_UI_EXTENSION)
    And 设置 minWidth=10vp, minHeight=10vp

  Scenario: Static modifier SetEmbeddedComponentOptions（stub）
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIEmbeddedComponentModifier::SetEmbeddedComponentOptions0Impl
    Then 输出 LOGE "EmbeddedComponentModifier::SetEmbeddedComponentOptions0 - is not supported"
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：创建/Want/选项/DPI/窗口模式/Placeholder/最小尺寸/C-API NDK；不做什么：事件回调详细规格在 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "JSEmbeddedComponent::Create 如何解析 EmbeddedOptions 并构建 EmbeddedUIExtensionConfig"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionModelNG::Create(EmbeddedUIExtensionConfig) 如何创建 UIExtensionNode 并设置 Pattern 属性"
  - repo: "openharmony/ace_engine"
    query: "PlaceholderType 枚举值和 placeholderMap 在 UIExtensionPattern 中的挂载逻辑"
  - repo: "openharmony/ace_engine"
    query: "ArkUIEmbeddedComponentModifier setWant/setOption/setOnTerminated/setOnError 的实现"
  - repo: "openharmony/ace_engine"
    query: "GENERATED_ArkUIEmbeddedComponentModifier 为何全部为 stub（仅 ConstructImpl 有效）"
```

**关键文档：**
- JS Bridge 层：`frameworks/bridge/declarative_frontend/jsview/js_embedded_component.cpp`
- Model 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_model_ng.cpp`
- Pattern 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.h`
- Config 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_config.h`
- C-API Dynamic：`interfaces/native/node/embeddedComponent_modifier.cpp`
- C-API Static：`frameworks/core/interfaces/native/implementation/embedded_component_modifier.cpp`
- C-API Option 头：`interfaces/native/node_attributes/embedded_component.h`
- C-API Option 结构：`interfaces/native/node/embeddedComponent_option.h`
- Model 定义：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_model.h`
- Session Wrapper：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/session_wrapper_impl.h`
