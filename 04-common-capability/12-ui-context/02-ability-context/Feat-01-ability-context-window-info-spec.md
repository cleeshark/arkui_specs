# 特性规格：Ability上下文与窗口信息

## 概述

| 属性 | 值 |
|------|------|
| 特性名称 | Ability上下文与窗口信息 |
| 特性编号 | Func-04-12-02-Feat-01 |
| 所属 Epic | UI 上下文 (04-12) |
| 优先级 | P1 |
| 目标版本 | API 10+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

本特性规格覆盖 `UIContext` 中与 Ability 上下文获取、窗口信息查询、断点计算及交互控制相关的 API 集合。这些 API 使应用在组件化场景下能从 `UIContext` 实例获取宿主 Ability 上下文、共享 LocalStorage、原子化服务状态栏控制器、窗口断点（宽度/高度）以及交互手势开关等信息，实现 UI 层与 Ability/窗口层的解耦信息桥接。

**关键架构约束（须重点关注）**：

1. **HeightBreakpoint = 宽高比计算，非绝对 VP 阈值**：`HeightBreakpoint` 基于窗口高度与宽度的宽高比 (H/W) 计算，阈值分别为 0.8 和 1.2，与 `WidthBreakpoint` 的绝对 VP 阈值计算方式完全不同。源码：`view_abstract.cpp:12245-12258`

2. **AtomicServiceBar 门控检查**：`getAtomicServiceBar` 在非原子化服务应用（`bundleType != 1`）中返回 `undefined`，仅当 `appInfo.bundleType == 1` 时才创建并返回 `AtomicServiceBar` 实例。源码：`jsUIContext.js:765-777`

## 本次变更范围（Delta）

本规格为既有 API 的 **补录规格（backfill）**，不引入新增/变更/废弃 API。所有接口均已存在于 ace_engine 实现中，本规格仅对实现行为进行规格化描述。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | getHostContext/getSharedLocalStorage 规格 | 已有实现补录（@since 10） |
| ADDED | getAtomicServiceBar 与 bundleType 门控规格 | 已有实现补录（@since 11） |
| ADDED | WidthBreakpoint/HeightBreakpoint 断点计算规格 | 已有实现补录（@since 11） |
| ADDED | enableSwipeBack 规格 | 已有实现补录（@since 11） |
| ADDED | getWindowName/getWindowId/isEasySplit 规格 | 已有实现补录（@since 12） |

涉及枚举类型：

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | WidthBreakpoint (XS/SM/MD/LG/XL) 枚举规格 | 已有实现补录（@since 11） |
| ADDED | HeightBreakpoint (SM/MD/LG) 枚举规格 | 已有实现补录（@since 11），使用宽高比而非绝对 VP |

## 输入文档

| 文档类型 | 文档名称 | 版本/日期 | 备注 |
|----------|----------|-----------|------|
| SDK 类型定义 | `@ohos.arkui.UIContext.d.ts` | API 10-12 | 公共 API 签名 |
| 动态前端 | `jsUIContext.js` | 当前 | 动态版本实现 |
| 静态前端 | `@ohos.arkui.UIContext.ts` | 当前 | 静态版本实现 |
| C++ 核心 | `view_abstract.cpp` | 当前 | Breakpoint 计算逻辑 |
| ANI 桥接 | `common_ani_modifier.cpp` | 当前 | 静态版本 C 桥接 |
| 管道层 | `pipeline_context.cpp` | 当前 | enableSwipeBack / isEasySplit / getWindowName |
| NAPI 桥接 | `js_view_context.cpp` | 当前 | isEasySplit 动态版注册 |

## 用户故事

### US-01: 获取宿主 Ability 上下文

**作为** 组件化 UI 开发者，**我想要** 通过 `UIContext.getHostContext()` 获取当前页面的宿主 Ability 上下文，**以便** 在不依赖全局 `getContext()` 的条件下获取 Ability 级资源与能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 在 UIAbility 场景调用 getHostContext() THEN 返回 UIAbilityContext 实例 | 正常 |
| AC-1.2 | WHEN 在 Extension 场景调用 getHostContext() THEN 返回 ExtensionContext 实例 | 正常 |
| AC-1.3 | WHEN 上下文不可获取（Frontend::GetHostContext() 返回空）THEN 返回 undefined | 异常 |
| AC-1.4 | WHEN 动态前端调用 getHostContext() THEN 通过全局 getContext() 获取 | 正常 |
| AC-1.5 | WHEN 静态前端调用 getHostContext() THEN 通过 ArkUIAniModule._Common_GetHostContext(instanceId) 获取 | 正常 |

### US-02: 获取共享 LocalStorage

**作为** 组件化 UI 开发者，**我想要** 通过 `UIContext.getSharedLocalStorage()` 获取跨 Ability 实例共享的 `LocalStorage`，**以便** 在多窗口/多实例场景下共享 UI 状态数据。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 getSharedLocalStorage() THEN 返回与当前 UI 实例绑定的共享 LocalStorage 实例 | 正常 |
| AC-2.2 | WHEN 共享 LocalStorage 不存在 THEN 返回 undefined（静态前端）或 null（C++ 层） | 异常 |
| AC-2.3 | WHEN 多实例场景下不同 instanceId 调用 THEN 返回对应实例的 LocalStorage（实例隔离） | 边界 |

### US-03: 原子化服务状态栏控制

**作为** 原子化服务开发者，**我想要** 通过 `UIContext.getAtomicServiceBar()` 获取状态栏控制器，**以便** 定制原子化服务的顶部状态栏。非原子化服务应用调用应返回 `undefined`。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 应用 bundleType == 1 调用 getAtomicServiceBar() THEN 返回 AtomicServiceBarController 实例 | 正常 |
| AC-3.2 | WHEN 应用 bundleType != 1 调用 getAtomicServiceBar() THEN 返回 undefined | 边界 |
| AC-3.3 | WHEN bundleMgr 模块不可获取（requireNapi 失败）THEN 返回 undefined | 异常 |
| AC-3.4 | WHEN AtomicServiceBarController 创建后 THEN 支持 setVisible/setBackgroundColor/setTitleContent/setTitleFontStyle/setIconColor/getBarRect/onBarRectChange 方法 | 正常 |
| AC-3.5 | WHEN 动态前端执行门控检查 THEN 每次调用时延迟检查 bundleType | 正常 |
| AC-3.6 | WHEN 静态前端执行门控检查 THEN AtomicServiceBarInternal 在 UIContext 构造时即创建，门控在更早阶段完成 | 边界 |

### US-04: 窗口断点响应式布局

**作为** 响应式布局开发者，**我想要** 通过断点 API 获取当前窗口的宽度和高度断点等级，**以便** 根据窗口尺寸变化调整布局策略。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 窗口宽度 < 320vp THEN getWindowWidthBreakpoint() 返回 WIDTH_XS | 正常 |
| AC-4.2 | WHEN 窗口宽度在 320vp-600vp THEN getWindowWidthBreakpoint() 返回 WIDTH_SM | 正常 |
| AC-4.3 | WHEN 窗口宽度在 600vp-840vp THEN getWindowWidthBreakpoint() 返回 WIDTH_MD | 正常 |
| AC-4.4 | WHEN 窗口宽度在 840vp-1440vp THEN getWindowWidthBreakpoint() 返回 WIDTH_LG | 正常 |
| AC-4.5 | WHEN 窗口宽度 ≥ 1440vp THEN getWindowWidthBreakpoint() 返回 WIDTH_XL | 正常 |
| AC-4.6 | WHEN aspectRatio (H/W) < 0.8 THEN getWindowHeightBreakpoint() 返回 HEIGHT_SM | 正常 |
| AC-4.7 | WHEN aspectRatio 在 0.8-1.2 THEN getWindowHeightBreakpoint() 返回 HEIGHT_MD | 正常 |
| AC-4.8 | WHEN aspectRatio ≥ 1.2 THEN getWindowHeightBreakpoint() 返回 HEIGHT_LG | 正常 |
| AC-4.9 | WHEN 窗口宽度为 0 THEN aspectRatio 取 0，getWindowHeightBreakpoint() 返回 HEIGHT_SM | 边界 |
| AC-4.10 | WHEN 容器为 null THEN C++ 层返回 -2，静态前端映射为 WIDTH_XS / HEIGHT_SM | 异常 |
| AC-4.11 | WHEN 窗口为 null THEN C++ 层返回 -3，静态前端映射为 WIDTH_XS / HEIGHT_SM | 异常 |

### US-05: 滑动返回手势控制

**作为** 应用开发者，**我想要** 通过 `UIContext.enableSwipeBack()` 控制滑动返回手势，**以便** 在特定页面场景下关闭系统级滑动返回避免手势冲突。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 调用 enableSwipeBack(true) THEN 启用滑动返回手势 | 正常 |
| AC-5.2 | WHEN 调用 enableSwipeBack(false) THEN 禁用滑动返回手势 | 正常 |
| AC-5.3 | WHEN 调用 enableSwipeBack(undefined) THEN 等同于启用（默认行为） | 边界 |
| AC-5.4 | WHEN 设置完成 THEN RootPattern.enableSwipeBack 被更新 | 正常 |

### US-06: 窗口标识查询

**作为** 应用开发者，**我想要** 通过窗口标识 API 查询当前窗口名称和 ID，**以便** 在多窗口管理或调试场景下识别特定窗口。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 窗口存在 THEN getWindowName() 返回窗口名称字符串 | 正常 |
| AC-6.2 | WHEN 窗口不存在 THEN getWindowName() 返回空字符串（C++层）或 undefined（静态前端） | 异常 |
| AC-6.3 | WHEN 窗口存在 THEN getWindowId() 返回窗口 ID (int32) | 正常 |
| AC-6.4 | WHEN 容器不存在 THEN getWindowId() 返回 -1（动态前端）或 undefined（静态前端将 -1 映射为 undefined） | 异常 |

### US-07: 强制分屏模式判定

**作为** 应用开发者，**我想要** 通过 `UIContext.isEasySplit()` 判断当前是否处于强制分屏模式，**以便** 在分屏模式下调整 UI 布局。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-7.1 | WHEN 处于强制分屏模式 THEN isEasySplit() 返回 true | 正常 |
| AC-7.2 | WHEN 不处于强制分屏模式 THEN isEasySplit() 返回 false | 正常 |
| AC-7.3 | WHEN PipelineContext 不可获取 THEN isEasySplit() 返回 false（安全降级） | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-01 | TASK-1 | 单测 | common_ani_modifier.cpp:130-143, jsUIContext.js:808-811 |
| AC-1.2 | R-01 | TASK-1 | 单测 | common_ani_modifier.cpp:130-143 |
| AC-1.3 | R-01 | TASK-1 | 单测 | jsUIContext.js:808-811 |
| AC-1.4 | R-01 | TASK-1 | 单测 | jsUIContext.js:808-811 (getContext) |
| AC-1.5 | R-01 | TASK-1 | 单测 | @ohos.arkui.UIContext.ts:975-977 (ANI bridge) |
| AC-2.1 | R-02 | TASK-1 | 单测 | common_ani_modifier.cpp:292-309, jsUIContext.js:814-817 |
| AC-2.2 | R-02 | TASK-1 | 单测 | common_ani_modifier.cpp:292-309 |
| AC-2.3 | R-02, R-11 | TASK-1 | 单测 | Container::CurrentIdSafely() 隔离 |
| AC-3.1 | R-03 | TASK-1 | 单测 | jsUIContext.js:765-777 |
| AC-3.2 | R-03 | TASK-1 | 单测 | jsUIContext.js:765-777 |
| AC-3.3 | R-03 | TASK-1 | 单测 | jsUIContext.js:765-777 (bundleMgr null) |
| AC-3.4 | R-03 | TASK-1 | 单测 | jsUIContext.js:1847-1887 |
| AC-3.5 | R-03 | TASK-1 | 单测 | jsUIContext.js:765-777 (lazy gate) |
| AC-3.6 | R-03 | TASK-1 | 单测 | @ohos.arkui.UIContext.ts:771,788 (eager create) |
| AC-4.1 | R-04 | TASK-1 | 单测 | view_abstract.cpp:12209-12234 |
| AC-4.2 | R-04 | TASK-1 | 单测 | view_abstract.cpp:12209-12234 |
| AC-4.3 | R-04 | TASK-1 | 单测 | view_abstract.cpp:12209-12234 |
| AC-4.4 | R-04 | TASK-1 | 单测 | view_abstract.cpp:12209-12234 |
| AC-4.5 | R-04 | TASK-1 | 单测 | view_abstract.cpp:12209-12234 |
| AC-4.6 | R-05 | TASK-1 | 单测 | view_abstract.cpp:12237-12260 |
| AC-4.7 | R-05 | TASK-1 | 单测 | view_abstract.cpp:12237-12260 |
| AC-4.8 | R-05 | TASK-1 | 单测 | view_abstract.cpp:12237-12260 |
| AC-4.9 | R-05 | TASK-1 | 单测 | view_abstract.cpp:12245-12258 (width=0) |
| AC-4.10 | R-10 | TASK-1 | 单测 | view_abstract.cpp:12212 (-2 error) |
| AC-4.11 | R-10 | TASK-1 | 单测 | view_abstract.cpp:12240-12242 (-3 error) |
| AC-5.1 | R-06 | TASK-1 | 单测 | ui_context_get_info_accessor.cpp:52-62 |
| AC-5.2 | R-06 | TASK-1 | 单测 | ui_context_get_info_accessor.cpp:52-62 |
| AC-5.3 | R-06 | TASK-1 | 单测 | ui_context_get_info_accessor.cpp:52-62 (undefined→true) |
| AC-5.4 | R-06 | TASK-1 | 单测 | pipeline_context.cpp:7907-7913 |
| AC-6.1 | R-07 | TASK-1 | 单测 | common_ani_modifier.cpp:692-702 |
| AC-6.2 | R-07 | TASK-1 | 单测 | common_ani_modifier.cpp:692-702 |
| AC-6.3 | R-08 | TASK-1 | 单测 | common_ani_modifier.cpp:704-712 |
| AC-6.4 | R-08 | TASK-1 | 单测 | @ohos.arkui.UIContext.ts:1205-1211 (-1→undefined) |
| AC-7.1 | R-09 | TASK-1 | 单测 | common_ani_modifier.cpp:120-128 |
| AC-7.2 | R-09 | TASK-1 | 单测 | pipeline_context.cpp:8384-8391 |
| AC-7.3 | R-09 | TASK-1 | 单测 | pipeline_context.cpp (null context → false) |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-01 | 行为 | 调用 `getHostContext()` | 返回 `UIAbilityContext \| ExtensionContext \| undefined`；动态前端通过全局 `getContext()` 获取，静态前端通过 `ArkUIAniModule._Common_GetHostContext(instanceId_)` 获取，C++ 通过 `Frontend::GetHostContext()` 获取 | `Frontend::GetHostContext()` 返回空时返回 `undefined`；源码：jsUIContext.js:808-811, @ohos.arkui.UIContext.ts:975-977, common_ani_modifier.cpp:130-143 | AC-1.1~1.5 |
| R-02 | 行为 | 调用 `getSharedLocalStorage()` | 返回与当前 UI 实例绑定的共享 `LocalStorage`；动态前端通过 `NativeLocalStorage.GetShared()`，静态前端通过 `ArkUIAniModule._Common_GetSharedLocalStorage()`，C++ 通过 `frontend->GetSharedStorage(currentInstance)` | 实例 ID 由 `Container::CurrentIdSafely()` 确定；不存在时返回 `undefined`(静态前端)/`null`(C++层)；源码：jsUIContext.js:814-817, @ohos.arkui.UIContext.ts:924-926, common_ani_modifier.cpp:292-309 | AC-2.1~2.3 |
| R-03 | 边界 | 调用 `getAtomicServiceBar()`，检查 `appInfo.bundleType` | `bundleType==1` 时返回 `AtomicServiceBarController` 实例（创建并缓存）；`!=1` 时返回 `undefined`；`bundleMgr` 不可获取时返回 `undefined` | **关键约束**：动态前端延迟门控（每次调用检查 bundleType via `bundleMgr.getBundleInfoForSelfSync`）；静态前端构造时预创建 `AtomicServiceBarInternal`（@ohos.arkui.UIContext.ts:771,788），门控在 ANI 层完成；开发者须预期非原子化服务返回 `undefined`；源码：jsUIContext.js:765-777, jsUIContext.js:1847-1887 | AC-3.1~3.6 |
| R-04 | 行为 | 调用 `getWindowWidthBreakpoint()`，窗口宽度 VP 值落入对应区间 | 按 VP 阈值返回 XS(<320)/SM(320~600)/MD(600~840)/LG(840~1440)/XL(≥1440) | 窗口宽度 = 像素宽度/density（density=0 时用原始像素值）；阈值常量 view_abstract.cpp:92-95；源码：view_abstract.cpp:12209-12234 | AC-4.1~4.5 |
| R-05 | 边界 | 调用 `getWindowHeightBreakpoint()`，计算 aspectRatio = height/width | 按宽高比返回 SM(<0.8)/MD(0.8~1.2)/LG(≥1.2)；计算公式 `aspectRatio = height / width` | **关键约束**：不做 density 转换，使用窗口原始像素值；与 WidthBreakpoint 绝对 VP 阈值计算方式完全不同；width=0 时 aspectRatio=0 → HEIGHT_SM；阈值 0.8/1.2 硬编码不可变更（view_abstract.cpp:96-97）；同高度不同宽度产生不同断点；源码：view_abstract.cpp:12237-12260 | AC-4.6~4.9 |
| R-06 | 行为 | 调用 `enableSwipeBack(enabled)` | `true` 启用、`false` 禁用滑动返回手势；通过 `PipelineContext::SetEnableSwipeBack(isEnable)` 设置到 `RootPattern` | `undefined`/未提供等同于 `true`（默认启用）；源码：jsUIContext.js:1032-1035, @ohos.arkui.UIContext.ts:1196-1199, ui_context_get_info_accessor.cpp:52-62, pipeline_context.cpp:7907-7913 | AC-5.1~5.4 |
| R-07 | 行为 | 调用 `getWindowName()` | 返回窗口名称字符串；窗口不存在时返回空字符串 `""` | 静态前端窗口不存在时返回 `undefined`；源码：jsUIContext.js:938-941, @ohos.arkui.UIContext.ts:1202-1203, common_ani_modifier.cpp:692-702, pipeline_context.cpp:7901-7904 | AC-6.1~6.2 |
| R-08 | 边界 | 调用 `getWindowId()` | 返回窗口 ID (int32)；容器不存在时 C++ 层返回 -1 | 静态前端将 -1 映射为 `undefined`（@ohos.arkui.UIContext.ts:1205-1211：`ret === -1 → undefined`）；源码：jsUIContext.js:944-947, common_ani_modifier.cpp:704-712 | AC-6.3~6.4 |
| R-09 | 行为 | 调用 `isEasySplit()` | 返回 true(强制分屏)/false(非分屏)；PipelineContext 不可获取时返回 false（安全降级） | 实现为 `PipelineContext::IsDisplayInForceSplitMode()`，综合判断 `forceSplitMgr_` 和 `stageManager_`；源码：jsUIContext.js:1119-1122, common_ani_modifier.cpp:120-128, pipeline_context.cpp:8384-8391 | AC-7.1~7.3 |
| R-10 | 异常 | `getWindowWidthBreakpoint()`/`getWindowHeightBreakpoint()` 获取容器或窗口失败 | C++ 层返回负值错误码：-2(容器null)/-3(窗口null)/-1(ANI初始化失败)；静态前端映射为默认值 WIDTH_XS/HEIGHT_SM 并打印错误日志 | 静态前端使用 `handleBreakpointError` 处理（@ohos.arkui.UIContext.ts:1213-1222, 1227-1230, 1238-1241）；动态前端依赖 C++ 层返回值不做额外映射；源码：view_abstract.cpp:12212, view_abstract.cpp:12240-12242 | AC-4.10~4.11 |
| R-11 | 边界 | 多实例场景下调用任何涉及 UI 实例的方法 | 在正确 `instanceId` 上下文中执行，确保实例数据隔离 | 动态前端 `withInstanceId(instanceId, callback)` (jsUIContext.js)；静态前端 `Sync_InstanceId/Restore_InstanceId` (@ohos.arkui.UIContext.ts)；C++ `ContainerScope scope(instanceId)`/`Container::CurrentIdSafely()`；错误 instanceId 导致返回错误实例数据或 undefined/默认值 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-01 | AC-1.1~1.5: getHostContext | 单元测试 | UIAbility/Extension/undefined 场景及前端路径差异 |
| VM-02 | AC-2.1~2.3: getSharedLocalStorage | 单元测试 | 多实例隔离、undefined/null 返回值 |
| VM-03 | AC-3.1~3.6: getAtomicServiceBar | 单元测试 | bundleType 门控、方法清单、前端门控时机差异 |
| VM-04 | AC-4.1~4.5: WidthBreakpoint | 单元测试 | 320/600/840/1440 VP 边界值枚举映射 |
| VM-05 | AC-4.6~4.11: HeightBreakpoint | 单元测试 | aspectRatio 0.8/1.2 边界、width=0、错误码 -2/-3 |
| VM-06 | AC-5.1~5.4: enableSwipeBack | 单元测试 | true/false/undefined 行为差异 |
| VM-07 | AC-6.1~6.4: getWindowName/getWindowId | 单元测试 | 正常/窗口不存在、-1→undefined 映射 |
| VM-08 | AC-7.1~7.3: isEasySplit | 单元测试 | 分屏/非分屏/null context 场景 |

## API 变更分析

### 新增 API

无。本规格为既有 API 补录。

### 变更/废弃 API

无。所有 API 签名与行为保持不变。

## 接口规格

### 接口定义

**getHostContext**

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIAbilityContext \| ExtensionContext \| undefined UIContext::getHostContext()` |
| 返回值 | `UIAbilityContext \| ExtensionContext \| undefined` — 当前 UI 实例的宿主 Ability 上下文；UIAbility 场景返回 UIAbilityContext，Extension 场景返回 ExtensionContext，不可获取时返回 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无参数) | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | UIAbility 场景调用 | 返回 UIAbilityContext 实例 | AC-1.1 |
| 2 | Extension 场景调用 | 返回 ExtensionContext 实例 | AC-1.2 |
| 3 | Frontend::GetHostContext() 返回空 | 返回 undefined | AC-1.3 |
| 4 | 动态前端调用 | 通过全局 getContext() 获取 | AC-1.4 |
| 5 | 静态前端调用 | 通过 ArkUIAniModule._Common_GetHostContext(instanceId) 获取 | AC-1.5 |

**getSharedLocalStorage**

| 属性 | 值 |
|------|-----|
| 函数签名 | `LocalStorage \| undefined UIContext::getSharedLocalStorage()` |
| 返回值 | `LocalStorage \| undefined` — 与当前 UI 实例绑定的共享 LocalStorage 实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无参数) | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 返回与当前 UI 实例绑定的共享 LocalStorage 实例 | AC-2.1 |
| 2 | 共享 LocalStorage 不存在 | 返回 undefined（静态前端）或 null（C++ 层） | AC-2.2 |
| 3 | 多实例场景不同 instanceId 调用 | 返回对应实例的 LocalStorage（实例隔离） | AC-2.3 |

**getAtomicServiceBar**

| 属性 | 值 |
|------|-----|
| 函数签名 | `AtomicServiceBarController \| undefined UIContext::getAtomicServiceBar()` |
| 返回值 | `AtomicServiceBarController \| undefined` — bundleType==1 时返回 AtomicServiceBarController 实例；否则返回 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无参数) | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 应用 bundleType == 1 调用 | 返回 AtomicServiceBarController 实例 | AC-3.1 |
| 2 | 应用 bundleType != 1 调用 | 返回 undefined | AC-3.2 |
| 3 | bundleMgr 模块不可获取（requireNapi 失败） | 返回 undefined | AC-3.3 |
| 4 | AtomicServiceBarController 创建后 | 支持 setVisible/setBackgroundColor/setTitleContent/setTitleFontStyle/setIconColor/getBarRect/onBarRectChange 方法 | AC-3.4 |
| 5 | 动态前端执行门控检查 | 每次调用时延迟检查 bundleType | AC-3.5 |
| 6 | 静态前端执行门控检查 | AtomicServiceBarInternal 在 UIContext 构造时即创建，门控在更早阶段完成 | AC-3.6 |

**getWindowWidthBreakpoint**

| 属性 | 值 |
|------|-----|
| 函数签名 | `WidthBreakpoint UIContext::getWindowWidthBreakpoint()` |
| 返回值 | `WidthBreakpoint` — 当前窗口宽度断点枚举值（XS/SM/MD/LG/XL） |
| 开放范围 | Public |
| 错误码 | -2（容器为 null）/ -3（窗口为 null）/ -1（ANI 环境初始化失败） |
| 关联 AC | AC-4.1~4.5, AC-4.10~4.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无参数) | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 窗口宽度 < 320vp | 返回 WIDTH_XS | AC-4.1 |
| 2 | 窗口宽度 320vp~600vp | 返回 WIDTH_SM | AC-4.2 |
| 3 | 窗口宽度 600vp~840vp | 返回 WIDTH_MD | AC-4.3 |
| 4 | 窗口宽度 840vp~1440vp | 返回 WIDTH_LG | AC-4.4 |
| 5 | 窗口宽度 ≥ 1440vp | 返回 WIDTH_XL | AC-4.5 |
| 6 | 容器为 null | C++ 层返回 -2，静态前端映射为 WIDTH_XS | AC-4.10 |
| 7 | 窗口为 null | C++ 层返回 -3，静态前端映射为 WIDTH_XS | AC-4.11 |

**getWindowHeightBreakpoint**

| 属性 | 值 |
|------|-----|
| 函数签名 | `HeightBreakpoint UIContext::getWindowHeightBreakpoint()` |
| 返回值 | `HeightBreakpoint` — 当前窗口高度断点枚举值（SM/MD/LG），基于宽高比计算 |
| 开放范围 | Public |
| 错误码 | -2（容器为 null）/ -3（窗口为 null）/ -1（ANI 环境初始化失败） |
| 关联 AC | AC-4.6~4.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无参数) | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | aspectRatio (H/W) < 0.8 | 返回 HEIGHT_SM | AC-4.6 |
| 2 | aspectRatio 在 0.8~1.2 | 返回 HEIGHT_MD | AC-4.7 |
| 3 | aspectRatio ≥ 1.2 | 返回 HEIGHT_LG | AC-4.8 |
| 4 | 窗口宽度为 0 | aspectRatio 取 0，返回 HEIGHT_SM | AC-4.9 |
| 5 | 容器为 null | C++ 层返回 -2，静态前端映射为 HEIGHT_SM | AC-4.10 |
| 6 | 窗口为 null | C++ 层返回 -3，静态前端映射为 HEIGHT_SM | AC-4.11 |

**enableSwipeBack**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void UIContext::enableSwipeBack(enabled: boolean)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1~5.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enabled | boolean | 否 | undefined（等同于 true） | true 启用/false 禁用滑动返回；undefined 或缺失等同于 true（默认启用） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 enableSwipeBack(true) | 启用滑动返回手势 | AC-5.1 |
| 2 | 调用 enableSwipeBack(false) | 禁用滑动返回手势 | AC-5.2 |
| 3 | 调用 enableSwipeBack(undefined) | 等同于启用（默认行为） | AC-5.3 |
| 4 | 设置完成 | RootPattern.enableSwipeBack 被更新 | AC-5.4 |

**getWindowName**

| 属性 | 值 |
|------|-----|
| 函数签名 | `string \| undefined UIContext::getWindowName()` |
| 返回值 | `string \| undefined` — 窗口名称字符串；窗口不存在时返回空字符串（C++ 层）或 undefined（静态前端） |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1~6.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无参数) | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 窗口存在 | 返回窗口名称字符串 | AC-6.1 |
| 2 | 窗口不存在 | 返回空字符串（C++ 层）或 undefined（静态前端） | AC-6.2 |

**getWindowId**

| 属性 | 值 |
|------|-----|
| 函数签名 | `number \| undefined UIContext::getWindowId()` |
| 返回值 | `number \| undefined` — 窗口 ID (int32)；容器不存在时 C++ 层返回 -1，静态前端映射为 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.3~6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无参数) | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 窗口存在 | 返回窗口 ID (int32) | AC-6.3 |
| 2 | 容器不存在 | 返回 -1（动态前端）或 undefined（静态前端将 -1 映射为 undefined） | AC-6.4 |

**isEasySplit**

| 属性 | 值 |
|------|-----|
| 函数签名 | `boolean UIContext::isEasySplit()` |
| 返回值 | `boolean` — 是否处于强制分屏显示模式；PipelineContext 不可获取时返回 false |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-7.1~7.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无参数) | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 处于强制分屏模式 | 返回 true | AC-7.1 |
| 2 | 不处于强制分屏模式 | 返回 false | AC-7.2 |
| 3 | PipelineContext 不可获取 | 返回 false（安全降级） | AC-7.3 |

## 兼容性声明

### 兼容性约束 1：HeightBreakpoint 宽高比语义

`HeightBreakpoint` 基于 `aspectRatio = height / width` 计算，而非绝对像素/VP 阈值。此行为自 API 11 引入以来始终一致。开发者须注意：

1. **同高度不同宽度**：一个 800px 高的窗口在 1000px 宽度下 `aspectRatio = 0.8`（HEIGHT_MD 边界），在 600px 宽度下 `aspectRatio = 1.33`（HEIGHT_LG），断点结果完全不同
2. **横竖屏切换**：旋转设备时 width/height 互换，aspectRatio 将从 `<1` 变为 `>1`（或反之），导致断点跳变
3. **多窗口/自由窗口场景**：用户调整窗口尺寸时，宽高比持续变化，断点可能频繁切换

此计算逻辑定义于 `view_abstract.cpp:96-97`（`HEIGHT_ASPECTRATIO_THRESHOLD1 = 0.8`, `HEIGHT_ASPECTRATIO_THRESHOLD2 = 1.2`），**不建议变更**，因为变更将破坏已有应用的响应式布局逻辑。

### 兼容性约束 2：AtomicServiceBar undefined 返回值

`getAtomicServiceBar()` 在 `bundleType != 1` 时返回 `undefined`。此门控逻辑定义于 `jsUIContext.js:765-777`：

```javascript
getAtomicServiceBar() {
    const bundleMgr = globalThis.requireNapi('bundle.bundleManager');
    if (!bundleMgr || !bundleMgr.BundleFlag) {
        return undefined;
    }
    let data = bundleMgr.getBundleInfoForSelfSync(bundleMgr.BundleFlag.GET_BUNDLE_INFO_WITH_APPLICATION);
    if (data.appInfo.bundleType == 1) {
        this.atomServiceBar = new AtomicServiceBar(this.instanceId_);
        return this.atomServiceBar;
    } else {
        return undefined;
    }
}
```

开发者须在调用前检查返回值是否为 `undefined`，不应假设其始终返回有效对象。此行为自 API 11 起一致，**不建议变更门控条件**。

### 兼容性约束 3：静态/动态前端返回值差异

| API | 动态前端返回 | 静态前端返回 | 差异说明 |
|------|-------------|-------------|----------|
| getWindowId (不可获取) | -1 (int) | undefined | 静态前端对 -1 做了 undefined 映射 |
| getAtomicServiceBar | 运行时门控检查 | 构造时预创建 + 返回 Nullable | 静态前端 AtomicServiceBarInternal 在构造时即创建 |
| getHostContext | `getContext()` 调用 | `ArkUIAniModule._Common_GetHostContext()` 调用 | 获取路径不同 |

### 兼容性约束 4：Breakpoint 错误码与默认值

当容器或窗口不可获取时，C++ 层返回负值错误码（-2, -3）。静态前端将这些错误码映射为默认枚举值（WIDTH_XS / HEIGHT_SM）并打印错误日志。动态前端依赖 C++ 层返回值，不做额外映射。此行为在 `@ohos.arkui.UIContext.ts:1213-1244` 中实现。

### 兼容性约束 5：enableSwipeBack(undefined) = enableSwipeBack(true)

`enableSwipeBack` 在 `enabled` 参数为 `undefined` 或缺失时等同于传入 `true`（启用）。此行为在 `ui_context_get_info_accessor.cpp:52-62` 中实现，**不建议变更默认值**。

## 架构约束

### AC-01：InstanceId 上下文隔离

所有 API 调用均须在正确的 `instanceId` 上下文中执行。多实例场景（多窗口/多 Ability）下，错误 instanceId 将导致返回错误实例的数据或 `undefined`/默认值。

- 动态前端使用 `withInstanceId(instanceId, callback)` 包装 — `jsUIContext.js` 各方法
- 静态前端使用 `ArkUIAniModule._Common_Sync_InstanceId(instanceId)` / `_Common_Restore_InstanceId()` — `@ohos.arkui.UIContext.ts` 各方法
- C++ 层使用 `ContainerScope scope(instanceId)` 切换 — `common_ani_modifier.cpp`

### AC-02：前端获取路径差异

| API | 动态前端路径 | 静态前端路径 | C++ 终端 |
|------|-------------|-------------|----------|
| getHostContext | `getContext()` (全局) | `ArkUIAniModule._Common_GetHostContext(instanceId)` | `Frontend::GetHostContext()` |
| getSharedLocalStorage | `NativeLocalStorage.GetShared()` | `ArkUIAniModule._Common_GetSharedLocalStorage()` | `Frontend::GetSharedStorage(instanceId)` |
| getAtomicServiceBar | 运行时 `bundleMgr` 门控 | `AtomicServiceBarInternal` 构造时 | NAPI `atomicservicebar` 模块 |
| enableSwipeBack | `Context.enableSwipeBack()` | `UIContextGetInfo.enableSwipeBack()` | `PipelineContext::SetEnableSwipeBack()` |
| getWindowWidthBreakpoint | `getUINativeModule().common.getWindowWidthBreakpoint()` | `ArkUIAniModule._Common_getWindowWidthBreakpoint()` | `ViewAbstract::GetWindowWidthBreakpoint()` |
| getWindowHeightBreakpoint | `getUINativeModule().common.getWindowHeightBreakpoint()` | `ArkUIAniModule._Common_getWindowHeightBreakpoint()` | `ViewAbstract::GetWindowHeightBreakpoint()` |
| getWindowName | `getUINativeModule().common.getWindowName()` | `ArkUIAniModule._Common_getWindowName(instanceId)` | `window->GetWindowName()` |
| getWindowId | `getUINativeModule().common.getWindowId()` | `ArkUIAniModule._Common_getWindowId(instanceId)` | `PipelineContext::GetFocusWindowId()` |
| isEasySplit | `Context.isEasySplit()` | `modifier->getCommonAniModifier()->isEasySplit(instanceId)` | `PipelineContext::IsDisplayInForceSplitMode()` |

### AC-03：HeightBreakpoint 宽高比计算（关键架构约束）

`HeightBreakpoint` 的宽高比计算方式是本特性中最重要的架构决策。该计算方式：

1. **不做 density 转换**：直接使用窗口像素尺寸计算 `height_px / width_px`
2. **与 WidthBreakpoint 不对称**：WidthBreakpoint 使用 VP 阈值，HeightBreakpoint 使用宽高比阈值
3. **边界条件**：width = 0 时 aspectRatio = 0，返回 HEIGHT_SM
4. **阈值不可变更**：0.8 和 1.2 是硬编码常量，变更将破坏兼容性

此设计选择可能的原因：高度断点更适合表达"纵横比"语义而非绝对高度语义，因为窗口高度在不同屏幕密度和尺寸组合下变化范围极大，使用宽高比能更好地表达"竖屏/方屏/横屏"等布局语义。

源码位置：`view_abstract.cpp:91` (enum), `view_abstract.cpp:96-97` (阈值), `view_abstract.cpp:12237-12260` (计算逻辑)

### AC-04：AtomicServiceBar 门控检查架构

`getAtomicServiceBar()` 的门控检查在动态前端 JS 层完成（`jsUIContext.js:765-777`），而非 C++ 层。这意味着：

1. 静态前端中 `AtomicServiceBarInternal` 在 UIContext 构造时即创建（`@ohos.arkui.UIContext.ts:771,788`），门控可能在更早阶段完成
2. 动态前端在每次调用时才执行门控检查（延迟检查）
3. 两者的门控时机不同，但最终效果一致：非原子化服务应用获取不到 `AtomicServiceBar`

## 非功能性需求

| 需求 ID | 类型 | 要求 | 验证方法 |
|----------|------|------|----------|
| NFR-01 | 性能 | Breakpoint 计算不应阻塞 UI 线程超过 1ms | 性能基准测试 |
| NFR-02 | 性能 | getHostContext/getSharedLocalStorage/getWindowName/getWindowId 应在 0.5ms 内完成 | 性能基准测试 |
| NFR-03 | 可靠性 | isEasySplit 在 PipelineContext 不可获取时安全返回 false | 异常场景单元测试 |
| NFR-04 | 可靠性 | getAtomicServiceBar 在 bundleMgr 不可获取时安全返回 undefined | 异常场景单元测试 |
| NFR-05 | 安全 | getHostContext 不应暴露跨实例的上下文数据 | InstanceId 隔离测试 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | WidthBreakpoint/HeightBreakpoint 正常工作；横竖屏切换导致断点变化 | 断点随横竖屏切换实时变化 | 多窗口断点单测 | `view_abstract.cpp:12209-12260` |
| 平板 | 大屏幕宽度可能映射到 WIDTH_LG/XL；宽高比变化范围更大 | WidthBreakpoint 阈值 840/1440 VP | 断点单测 | `view_abstract.cpp:12209-12234` |
| 折叠屏 | 折叠/展开状态切换导致宽高比变化，断点可能频繁跳变 | HeightBreakpoint 宽高比计算(0.8/1.2)；建议使用 UIObserver 监听断点变化 | 折叠屏场景测试 | `view_abstract.cpp:12237-12260` |
| 大屏/智慧屏 | WIDTH_XL 断点常见；aspectRatio 通常 < 0.8，映射到 HEIGHT_SM | 无特殊约束 | 断点单测 | — |
| 自由窗口 | 用户可调整窗口尺寸，断点实时响应变化 | 断点随窗口尺寸变化实时响应 | 多窗口断点单测 | `pipeline_context.cpp` |
| 可穿戴 | 小屏幕通常 WIDTH_XS；aspectRatio 依赖设备形状 | WIDTH_XS (< 320vp) | 断点单测 | — |

特别说明：`HeightBreakpoint` 的宽高比计算在折叠屏/自由窗口场景下可能导致断点频繁切换，建议开发者使用 `UIObserver` 监听断点变化而非仅在初始化时读取一次。

## 全局特性影响

本特性涉及的 API 均为 `UIContext` 实例方法，不影响全局组件框架或其他 UI 上下文子特性。主要交互关系：

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|----------|
| 无障碍 | 否 | 本特性 API 不涉及无障碍属性，不影响无障碍功能 | N/A |
| 大字体 | 否 | 断点计算基于 VP/宽高比而非字体大小，无大字体交互 | N/A |
| 深色模式 | 否 | 断点/窗口信息 API 不受深色模式影响 | N/A |
| 多窗口/分屏 | 是 | 断点随窗口尺寸变化实时响应；`enableSwipeBack` 影响分屏返回手势；`isEasySplit` 判定分屏状态 | 04-12-04 Router/Navigation（enableSwipeBack）；自由窗口断点变化 |
| 多用户 | 否 | 所有 API 基于 instanceId 隔离，无跨用户数据暴露 | AC-2.3 实例隔离 |
| 版本升级 | 是 | API 渐进开放(@since 10-12)，需注意版本差异 | getWindowName/getWindowId @since 12 |
| 生态兼容 | 是 | `AtomicServiceBar` 仅原子化服务(bundleType==1)可用，非原子化服务返回 `undefined` | 04-12-05 Overlay/Popup（AtomicServiceBar setVisible） |
| 04-12-01 UIContext 创建与获取 | 是 | 本特性 API 通过 `UIContext` 实例调用 | UIContext 实例获取 |
| 04-12-03 UIObserver | 是 | 断点变化可通过 UIObserver 监听，与本特性断点读取互补 | 断点变化监听 |
| 04-12-04 Router/Navigation | 是 | `enableSwipeBack` 影响 Navigation 的滑动返回行为 | 滑动返回手势控制 |
| 04-12-05 Overlay/Popup | 是 | AtomicServiceBar 的 `setVisible` 与 Overlay 层交互 | 状态栏可见性控制 |

## 行为场景

### 场景 1：HeightBreakpoint 宽高比计算

```gherkin
Feature: HeightBreakpoint 宽高比计算

  Scenario: 正常宽高比窗口 - 横屏设备
    Given 窗口宽度为 1920 像素
    And 窗口高度为 1080 像素
    When 调用 getWindowHeightBreakpoint()
    Then aspectRatio = 1080 / 1920 = 0.5625
    And 返回 HeightBreakpoint.HEIGHT_SM (0.5625 < 0.8)

  Scenario: 正常宽高比窗口 - 竖屏设备
    Given 窗口宽度为 1080 像素
    And 窗口高度为 1920 像素
    When 调用 getWindowHeightBreakpoint()
    Then aspectRatio = 1920 / 1080 = 1.778
    And 返回 HeightBreakpoint.HEIGHT_LG (1.778 ≥ 1.2)

  Scenario: 正常宽高比窗口 - 方形窗口
    Given 窗口宽度为 1000 像素
    And 窗口高度为 900 像素
    When 调用 getWindowHeightBreakpoint()
    Then aspectRatio = 900 / 1000 = 0.9
    And 返回 HeightBreakpoint.HEIGHT_MD (0.8 ≤ 0.9 < 1.2)

  Scenario: 窗口宽度为零
    Given 窗口宽度为 0 像素
    And 窗口高度为 800 像素
    When 调用 getWindowHeightBreakpoint()
    Then aspectRatio = 0 (width 为零时取 0)
    And 返回 HeightBreakpoint.HEIGHT_SM
```

### 场景 2：AtomicServiceBar 门控检查

```gherkin
Feature: AtomicServiceBar 门控检查

  Scenario: 原子化服务应用获取 AtomicServiceBar
    Given 应用 bundleType 为 1 (原子化服务)
    And bundleMgr 模块可获取
    When 调用 getAtomicServiceBar()
    Then 返回 AtomicServiceBarController 实例
    And 实例支持 setVisible/setBackgroundColor/setTitleContent 等方法

  Scenario: 普通应用获取 AtomicServiceBar
    Given 应用 bundleType 不为 1 (非原子化服务)
    And bundleMgr 模块可获取
    When 调用 getAtomicServiceBar()
    Then 返回 undefined

  Scenario: bundleMgr 不可获取
    Given bundleMgr 模块不可获取 (requireNapi 失败)
    When 调用 getAtomicServiceBar()
    Then 返回 undefined
```

### 场景 3：WidthBreakpoint VP 阈值计算

```gherkin
Feature: WidthBreakpoint VP 阈值计算

  Scenario: 窗口宽度小于 320vp
    Given 窗口宽度为 280vp
    When 调用 getWindowWidthBreakpoint()
    Then 返回 WidthBreakpoint.WIDTH_XS

  Scenario: 窗口宽度在 320vp-600vp 之间
    Given 窗口宽度为 500vp
    When 调用 getWindowWidthBreakpoint()
    Then 返回 WidthBreakpoint.WIDTH_SM

  Scenario: 窗口宽度在 600vp-840vp 之间
    Given 窗口宽度为 720vp
    When 调用 getWindowWidthBreakpoint()
    Then 返回 WidthBreakpoint.WIDTH_MD

  Scenario: 窗口宽度在 840vp-1440vp 之间
    Given 窗口宽度为 1000vp
    When 调用 getWindowWidthBreakpoint()
    Then 返回 WidthBreakpoint.WIDTH_LG

  Scenario: 窗口宽度大于 1440vp
    Given 窗口宽度为 1600vp
    When 调用 getWindowWidthBreakpoint()
    Then 返回 WidthBreakpoint.WIDTH_XL
```

### 场景 4：enableSwipeBack 行为

```gherkin
Feature: enableSwipeBack 手势控制

  Scenario: 启用滑动返回
    When 调用 enableSwipeBack(true)
    Then RootPattern.enableSwipeBack 设为 true
    And 滑动返回手势可用

  Scenario: 禁用滑动返回
    When 调用 enableSwipeBack(false)
    Then RootPattern.enableSwipeBack 设为 false
    And 滑动返回手势不可用

  Scenario: 参数为 undefined 时默认启用
    When 调用 enableSwipeBack(undefined)
    Then RootPattern.enableSwipeBack 设为 true
    And 滑动返回手势可用
```

### 场景 5：isEasySplit 强制分屏判定

```gherkin
Feature: isEasySplit 强制分屏判定

  Scenario: 处于强制分屏模式
    Given forceSplitMgr_ 存在且 IsRouterForceSplit() 返回 true
    And stageManager_ 存在且 IsDisplaySplitMode() 返回 true
    When 调用 isEasySplit()
    Then 返回 true

  Scenario: 不处于强制分屏模式
    Given isCurrentInForceSplitMode_ 为 false
    And forceSplitMgr_ 存在但 IsRouterForceSplit() 返回 false
    When 调用 isEasySplit()
    Then 返回 false

  Scenario: PipelineContext 不可获取
    Given PipelineContext::GetCurrentContext() 返回 null
    When 调用 isEasySplit()
    Then 返回 false
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符 — 无推测内容，所有结论基于源码验证
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试 — 每个 AC 使用 WHEN/THEN 描述
- [x] 范围边界明确（做什么/不做什么清晰） — 本规格为既有 API 补录，不涉及 API 变更
- [x] 无语义模糊表述（"快速""稳定""尽可能"等） — 所有描述基于实际实现代码，无未验证假设
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC） — 验收追溯表中每项均有追溯源码
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突） — 所有规则标注源码位置、边界值和关联 AC
- [x] 所有声明引用了源码文件和行号 — 所有规则和验收项均标注源码位置
- [x] HeightBreakpoint 宽高比计算重点描述 — R-05/AC-03/兼容性约束 1/场景 1 均强调
- [x] AtomicServiceBar 门控检查重点描述 — R-03/AC-04/兼容性约束 2/场景 2 均强调
- [x] 兼容性声明覆盖前端差异 — 兼容性约束 3 覆盖静态/动态前端差异
- [x] 遵循 "Implementation IS the spec" 原则 — 所有描述基于实际实现代码
- [x] 多设备适配考虑断点差异 — 多设备适配声明覆盖

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "UIContext 动态前端(jsUIContext.js)与静态前端(@ohos.arkui.UIContext.ts)的双路径实现架构，包括 instanceId 上下文隔离机制(withInstanceId vs Sync_InstanceId/Restore_InstanceId)"
  - repo: "openharmony/ace_engine"
    query: "getAtomicServiceBar 门控检查机制：动态前端延迟门控(bundleMgr.getBundleInfoForSelfSync + bundleType==1) vs 静态前端构造时预创建(AtomicServiceBarInternal)"
  - repo: "openharmony/ace_engine"
    query: "WidthBreakpoint 与 HeightBreakpoint 的计算逻辑差异：WidthBreakpoint 基于 VP 阈值(320/600/840/1440) vs HeightBreakpoint 基于宽高比(aspectRatio 0.8/1.2)，以及错误码(-2/-3/-1)的静态前端 handleBreakpointError 处理"
  - repo: "openharmony/ace_engine"
    query: "ANI 桥接层(common_ani_modifier.cpp)中所有本特性 API 的注册与实现，包括 GetHostContext/GetSharedLocalStorage/GetWindowName/GetWindowId/IsEasySplit/GetWindowWidthBreakpoint/GetWindowHeightBreakpoint 及 InstanceId 切换(ContainerScope)"
  - repo: "openharmony/ace_engine"
    query: "PipelineContext 层 enableSwipeBack/SetEnableSwipeBack、getWindowName、IsDisplayInForceSplitMode 的实现，以及 ui_context_get_info_accessor.cpp 中 enableSwipeBack 的 undefined 默认启用行为"
  - repo: "openharmony/ace_engine"
    query: "静态前端 getWindowId 的 -1→undefined 映射逻辑(@ohos.arkui.UIContext.ts:1205-1211)及 getAtomicServiceBar 的 Nullable 返回值差异"
  - repo: "openharmony/ace_engine"
    query: "WidthBreakpoint/HeightBreakpoint 枚举定义(view_abstract.cpp:90-91)与阈值常量(92-97)，以及 ohos_mock.ts 中的枚举值定义"
  - repo: "openharmony/ace_engine"
    query: "AtomicServiceBar 类定义与方法清单(jsUIContext.js:1835-1887)，包括 setVisible/setBackgroundColor/setTitleContent/setTitleFontStyle/setIconColor/getBarRect/onBarRectChange"
  - repo: "openharmony/ace_engine"
    query: "JSIsEasySplit 动态前端注册(js_view_context.cpp:1512-1521)及 isEasySplit 的 PipelineContext::IsDisplayInForceSplitMode() 综合判断逻辑(forceSplitMgr_ + stageManager_)"
```

**关键文档：**

- `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:765-777` — getAtomicServiceBar 门控检查（bundleType == 1）
- `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:808-811` — getHostContext 实现（调用 getContext()）
- `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:814-817` — getSharedLocalStorage 实现（调用 NativeLocalStorage.GetShared()）
- `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:938-947` — getWindowName/getWindowId 实现
- `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:950-960` — getWindowWidthBreakpoint/getWindowHeightBreakpoint 实现
- `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1032-1035` — enableSwipeBack 实现
- `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1119-1122` — isEasySplit 实现
- `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1835-1887` — AtomicServiceBar 类定义与方法
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts:924-926` — getSharedLocalStorage 静态实现
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts:975-977` — getHostContext 静态实现
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts:993-995` — getAtomicServiceBar 静态实现
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts:1196-1199` — enableSwipeBack 静态实现
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts:1202-1211` — getWindowName/getWindowId 静态实现
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts:1224-1244` — getWindowWidthBreakpoint/getWindowHeightBreakpoint 静态实现及错误处理
- `frameworks/core/components_ng/base/view_abstract.cpp:90-91` — WidthBreakpoint/HeightBreakpoint 枚举定义
- `frameworks/core/components_ng/base/view_abstract.cpp:92-97` — 断点阈值常量定义
- `frameworks/core/components_ng/base/view_abstract.cpp:12209-12234` — GetWindowWidthBreakpoint 计算逻辑
- `frameworks/core/components_ng/base/view_abstract.cpp:12237-12260` — GetWindowHeightBreakpoint 宽高比计算逻辑
- `frameworks/core/interfaces/native/ani/common_ani_modifier.cpp:120-128` — IsEasySplit ANI 桥接
- `frameworks/core/interfaces/native/ani/common_ani_modifier.cpp:130-143` — GetHostContext ANI 桥接
- `frameworks/core/interfaces/native/ani/common_ani_modifier.cpp:292-309` — GetSharedLocalStorage ANI 桥接
- `frameworks/core/interfaces/native/ani/common_ani_modifier.cpp:692-702` — GetWindowName ANI 桥接
- `frameworks/core/interfaces/native/ani/common_ani_modifier.cpp:704-712` — GetWindowId ANI 桥接
- `frameworks/core/interfaces/native/ani/common_ani_modifier.cpp:714-722` — GetWindowWidthBreakpoint/GetWindowHeightBreakpoint ANI 桥接
- `frameworks/core/interfaces/native/ani/common_ani_modifier.cpp:1250-1345` — ArkUIAniCommonModifier 注册表（含所有本特性 API）
- `frameworks/core/interfaces/native/implementation/ui_context_get_info_accessor.cpp:52-62` — EnableSwipeBack C API 桥接（undefined 默认启用）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:7901-7904` — GetWindowName 管道层实现
- `frameworks/core/pipeline_ng/pipeline_context.cpp:7907-7913` — SetEnableSwipeBack 管道层实现
- `frameworks/core/pipeline_ng/pipeline_context.cpp:8384-8391` — IsDisplayInForceSplitMode 管道层实现
- `frameworks/core/pipeline_ng/pipeline_context.h:1201-1202` — GetWindowWidthBreakpoint/GetWindowHeightBreakpoint 声明
- `frameworks/core/pipeline_ng/pipeline_context.h:1083` — GetWindowName 声明
- `frameworks/core/pipeline_ng/pipeline_context.h:1246` — IsDisplayInForceSplitMode 声明
- `frameworks/bridge/declarative_frontend/jsview/js_view_context.cpp:1512-1521` — JSIsEasySplit 动态前端注册
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/stateManagement/mock/ohos_mock.ts:43-55` — WidthBreakpoint/HeightBreakpoint 枚举值定义
