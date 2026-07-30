# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | @ohos.arkui.theme 公开主题 API（Colors / CustomTheme / WithTheme / ThemeColorMode） |
| 特性编号 | Func-03-03-03-Feat-02 |
| FuncID | 03-03-03 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 12 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 12 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `@ohos.arkui.theme` 公开 SDK 模块 | @since 12，Colors/Theme/CustomTheme/WithTheme/ThemeControl |
| ADDED | `Colors` 接口（54 颜色 Token） | @since 12，brand/warning/alert/confirm/font*/icon*/background*/comp*/interactive* |
| ADDED | `CustomTheme` / `CustomColors` | @since 12，应用自定义颜色覆盖 |
| ADDED | `CustomDarkColors` | @since 20，深色模式自定义颜色 |
| ADDED | `WithTheme` 声明式容器 | @since 12，局部主题与色彩模式作用域 |
| ADDED | `ThemeControl.setDefaultTheme` | @since 12，设置全局默认主题 |
| ADDED | `ThemeColorMode` 枚举 | SYSTEM=0/LIGHT=1/DARK=2 |
| ADDED | native theme 模块注册 | createAndBindTheme/pop/setDefaultTheme/removeFromCache |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/03-resource-theme/03-theme-framework/design.md`
- **SDK 类型定义**:
  - `<OH_ROOT>/interface_sdk-js/api/@ohos.arkui.theme.d.ts`（本地镜像 `frameworks/bridge/declarative_frontend/ark_theme/theme_manager/types/theme.d.ts`）

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 应用自定义颜色主题

**角色**: 应用开发者
**期望**: 我想要通过 `CustomTheme` 自定义品牌色等颜色 Token
**价值**: 以便应用在系统主题基础上覆盖关键颜色

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 应用声明 `CustomTheme` 含 `colors: CustomColors` THEN `CustomColors` 为 `Partial<Colors>`，仅覆盖指定 Token（`theme.d.ts` CustomTheme/CustomColors，@since 12） | 正常 |
| AC-1.2 | WHEN 应用声明 `darkColors: CustomDarkColors` THEN 深色模式按 `Partial<Colors>` 覆盖（@since 20） | 正常 |
| AC-1.3 | WHEN `CustomTheme` 未指定某 Token THEN 回退到系统主题对应 Token 值 | 正常 |
| AC-1.4 | WHEN `ThemeControl.setDefaultTheme(customTheme)` 调用 THEN 经 `ArkThemeControl.ts` 设置全局默认主题，并下发 native `theme.setDefaultTheme` 写入 `TokenThemeStorage` 默认主题（`theme.d.ts` ThemeControl，`arkts_native_api_impl_bridge.cpp:862`） | 正常 |
| AC-1.5 | WHEN `ThemeControl.setDefaultTheme(undefined)` 调用 THEN 清除全局默认主题，回退系统主题（`ObtainSystemTheme`） | 正常 |
| AC-1.6 | WHEN 全局默认主题变更 THEN `ArkThemeScopeManager.getFinalTheme` 合并默认主题与各作用域局部主题，传播到全部已建作用域（`ArkThemeScopeManager.ts`） | 正常 |
| AC-1.7 | WHEN 应用未设默认主题且作用域未覆盖某 Token THEN `getFinalTheme` 回退链：作用域主题 → 默认主题 → `ObtainSystemTheme` 系统主题（`token_theme_storage.cpp`） | 正常 |

### US-2: 局部主题与色彩模式作用域

**角色**: 应用开发者
**期望**: 我想要通过 `WithTheme` 为子树设置局部主题与色彩模式
**价值**: 以便局部区域使用独立主题/深浅色而不影响全局

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 应用使用 `WithTheme(theme: CustomTheme){...}` THEN 进入作用域时 `sendThemeToNative` 将主题下发 native 并经 `setThemeScopeId` 分配 scopeId（`js_with_theme.cpp`，`ArkThemeNativeHelper.ts`） | 正常 |
| AC-2.2 | WHEN `WithThemeOptions.colorMode` 指定 `ThemeColorMode.DARK` THEN 子树使用 DARK 局部色彩模式（`ark_component/types/index.d.ts:622`） | 正常 |
| AC-2.3 | WHEN `WithTheme` 作用域退出 THEN `removeThemeInNative` 清理 scopeId 对应主题，native `theme.pop` 移除绑定（`js_with_theme.cpp`） | 正常 |
| AC-2.4 | WHEN native theme 模块 `createAndBindTheme` 执行 THEN 创建并绑定 TokenTheme 到节点，`TokenThemeStorage.StoreThemeScope(scopeId)` 存储作用域主题（`arkts_native_api_impl_bridge.cpp:862` RegisterThemeAttributes，`token_theme_storage.cpp`） | 正常 |
| AC-2.5 | WHEN `WithTheme` 嵌套 THEN 内层作用域经 `ArkThemeScopeManager.onComponentCreateEnter` 压栈分配新 scopeId，内层 Token 覆盖外层，退出时 `onComponentCreateExit` 出栈恢复外层（`ArkThemeScopeManager.ts`） | 正常 |
| AC-2.6 | WHEN 组件创建进入 WithTheme 作用域 THEN `onComponentCreateEnter` 维护作用域栈；组件销毁时 `onComponentCreateExit` 清理（`ArkThemeScopeManager.ts`） | 正常 |
| AC-2.7 | WHEN IfElse 分支切换 THEN `onIfElseBranchUpdateEnter`/`onIfElseBranchUpdateExit` 更新作用域主题，未命中分支作用域主题不生效（`ArkThemeScopeManager.ts`） | 边界 |
| AC-2.8 | WHEN 作用域内组件取色 THEN 经 `TokenThemeStorage.GetTheme(scopeId)` 取作用域 TokenTheme，`TokenThemeWrapper.ApplyTokenTheme` 应用 54 Token 到节点（`token_theme_storage.cpp`，`token_theme_wrapper.h`） | 正常 |
| AC-2.9 | WHEN PU 视图创建/销毁 THEN `onViewPUCreate`/`onViewPUDelete` 同步作用域生命周期（`ArkThemeScopeManager.ts`） | 正常 |

### US-3: ThemeColorMode 色彩模式控制

**角色**: 应用开发者
**期望**: 我想要通过 `ThemeColorMode` 指定 SYSTEM/LIGHT/DARK
**价值**: 以便局部或全局控制系统/亮/暗色彩模式

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `ThemeColorMode.SYSTEM` THEN 跟随系统色彩模式（`ark_component/types/index.d.ts:622`，SYSTEM=0） | 正常 |
| AC-3.2 | WHEN `ThemeColorMode.LIGHT` THEN 强制浅色模式（LIGHT=1） | 正常 |
| AC-3.3 | WHEN `ThemeColorMode.DARK` THEN 强制深色模式（DARK=2） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-THEME-02 | XTS | `theme.d.ts` CustomColors |
| AC-1.2 | R-1 | TASK-THEME-02 | XTS | `theme.d.ts` CustomDarkColors @since 20 |
| AC-1.3 | R-2 | TASK-THEME-02 | XTS | `theme.d.ts` CustomTheme |
| AC-1.4 | R-3 | TASK-THEME-02 | XTS | `ArkThemeControl.ts`，`arkts_native_api_impl_bridge.cpp:862` |
| AC-1.5 | R-3 | TASK-THEME-02 | XTS | `ArkThemeControl.ts` setDefaultTheme(undefined) |
| AC-1.6 | R-7 | TASK-THEME-02 | UT | `ArkThemeScopeManager.ts` getFinalTheme |
| AC-1.7 | R-8 | TASK-THEME-02 | UT | `token_theme_storage.cpp` ObtainSystemTheme |
| AC-2.1 | R-4 | TASK-THEME-02 | UT | `js_with_theme.cpp` |
| AC-2.2 | R-5 | TASK-THEME-02 | UT | `ark_component/types/index.d.ts:622` |
| AC-2.3 | R-4 | TASK-THEME-02 | UT | `js_with_theme.cpp` |
| AC-2.4 | R-6 | TASK-THEME-02 | UT | `arkts_native_api_impl_bridge.cpp:862`，`token_theme_storage.cpp` |
| AC-2.5 | R-9 | TASK-THEME-02 | UT | `ArkThemeScopeManager.ts` onComponentCreateEnter/Exit |
| AC-2.6 | R-9 | TASK-THEME-02 | UT | `ArkThemeScopeManager.ts` |
| AC-2.7 | R-9 | TASK-THEME-02 | UT | `ArkThemeScopeManager.ts` onIfElseBranchUpdate* |
| AC-2.8 | R-10 | TASK-THEME-02 | UT | `token_theme_storage.cpp`，`token_theme_wrapper.h` |
| AC-2.9 | R-9 | TASK-THEME-02 | UT | `ArkThemeScopeManager.ts` onViewPUCreate/Delete |
| AC-3.1 | R-5 | TASK-THEME-02 | XTS | `ark_component/types/index.d.ts:622` |
| AC-3.2 | R-5 | TASK-THEME-02 | XTS | `ark_component/types/index.d.ts:622` |
| AC-3.3 | R-5 | TASK-THEME-02 | XTS | `ark_component/types/index.d.ts:622` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 声明 CustomTheme.colors/darkColors | 按 Partial<Colors> 覆盖指定 Token | 未指定 Token 回退系统主题 | AC-1.1, AC-1.2 |
| R-2 | 行为 | CustomTheme 未指定 Token | 回退系统主题对应值 | 无 | AC-1.3 |
| R-3 | 行为 | ThemeControl.setDefaultTheme(customTheme \| undefined) | 设置/清除全局默认主题，下发 native theme.setDefaultTheme 写入 TokenThemeStorage | undefined 清除回退系统 | AC-1.4, AC-1.5 |
| R-4 | 行为 | WithTheme 进入/退出作用域 | 进入 sendThemeToNative + setThemeScopeId 分配 scopeId；退出 removeThemeInNative + theme.pop | scopeId 唯一 | AC-2.1, AC-2.3 |
| R-5 | 行为 | WithThemeOptions.colorMode 指定 | SYSTEM=0/LIGHT=1/DARK=2 对应色彩模式 | 无 | AC-2.2, AC-3.1~AC-3.3 |
| R-6 | 行为 | native createAndBindTheme | 创建并绑定 TokenTheme 到节点，TokenThemeStorage.StoreThemeScope 存作用域主题 | 经 RegisterThemeAttributes 注册 | AC-2.4 |
| R-7 | 行为 | 全局默认主题变更 | ArkThemeScopeManager.getFinalTheme 合并默认+作用域主题传播到全部作用域 | 无 | AC-1.6 |
| R-8 | 行为 | 作用域/默认未覆盖 Token | getFinalTheme 回退链：作用域 → 默认 → ObtainSystemTheme | 无 | AC-1.7 |
| R-9 | 行为 | 组件/分支/PU 生命周期进作用域 | onComponentCreateEnter/Exit、onIfElseBranchUpdate*、onViewPUCreate/Delete 维护作用域栈 | 嵌套内层覆盖外层 | AC-2.5~AC-2.7, AC-2.9 |
| R-10 | 行为 | 作用域内取色 | TokenThemeStorage.GetTheme(scopeId) + TokenThemeWrapper.ApplyTokenTheme 应用 54 Token | 无 | AC-2.8 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.7 | XTS + UT | CustomTheme/CustomColors/CustomDarkColors 覆盖与回退、setDefaultTheme 设置/清除、getFinalTheme 传播与回退链 |
| VM-2 | AC-2.1 ~ AC-2.9 | UT | WithTheme 作用域下发/清理、native 绑定、嵌套压栈、生命周期、IfElse 分支、ApplyTokenTheme 取色 |
| VM-3 | AC-3.1 ~ AC-3.3 | XTS | ThemeColorMode SYSTEM/LIGHT/DARK |

## API 变更分析

> 本特性为已有实现补录，以下列出已有的公开和 InnerAPI 接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `Colors`（interface） | Public | 54 颜色 Token 字段 | Colors | 无 | 系统颜色 Token 集合 | AC-1.1 |
| `CustomColors` | Public | Partial<Colors> | CustomColors | 无 | 应用自定义颜色覆盖 | AC-1.1 |
| `CustomDarkColors` | Public | Partial<Colors> | CustomDarkColors | 无 | 深色模式自定义颜色覆盖 | AC-1.2 |
| `CustomTheme` | Public | { colors?: CustomColors, darkColors?: CustomDarkColors } | CustomTheme | 无 | 应用自定义主题 | AC-1.1~AC-1.3 |
| `WithThemeOptions` | Public | { theme?: CustomTheme, colorMode?: ThemeColorMode } | WithThemeOptions | 无 | WithTheme 配置 | AC-2.2 |
| `WithTheme(theme: CustomTheme)` | Public | CustomTheme | void | 无 | 局部主题作用域容器 | AC-2.1 |
| `ThemeControl.setDefaultTheme(customTheme)` | Public | CustomTheme \| undefined | void | 无 | 设置全局默认主题 | AC-1.4 |
| `ThemeColorMode`（enum） | Public | 无 | SYSTEM=0/LIGHT=1/DARK=2 | 无 | 色彩模式枚举 | AC-3.1~AC-3.3 |
| native theme.createAndBindTheme | InnerApi | scopeId, CustomTheme | void | 无 | 创建并绑定 TokenTheme 到节点 | AC-2.4 |
| native theme.pop | InnerApi | scopeId | void | 无 | 退出作用域清理 | AC-2.3 |
| native theme.setDefaultTheme | InnerApi | CustomTheme | void | 无 | native 侧设置默认主题 | AC-1.4 |
| native theme.removeFromCache | InnerApi | scopeId | void | 无 | 从缓存移除主题 | AC-2.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `CustomTheme.darkColors` | ADDED | @since 20 新增深色自定义颜色 | 低版本仅用 colors | AC-1.2 |

## 接口规格

### 接口定义

**[WithTheme]**

| 属性 | 值 |
|------|-----|
| 函数签名 | `WithTheme(theme: CustomTheme, options?: WithThemeOptions): void`（声明式容器，create/pop 模式） |
| 开放范围 | Public（@since 12） |
| 关联 AC | AC-2.1 ~ AC-2.9 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 进入 WithTheme 作用域 | ArkThemeNativeHelper.sendThemeToNative 下发主题；setThemeScopeId 分配 scopeId；native createAndBindTheme 绑定 TokenTheme 到当前构建节点 | AC-2.1, AC-2.4 |
| 2 | 嵌套 WithTheme | onComponentCreateEnter 压栈分配新 scopeId，内层 Token 覆盖外层 | AC-2.5 |
| 3 | 组件创建/销毁 | onComponentCreateEnter/Exit 维护作用域栈；onViewPUCreate/Delete 同步 PU 视图 | AC-2.6, AC-2.9 |
| 4 | IfElse 分支切换 | onIfElseBranchUpdateEnter/Exit 更新作用域主题，未命中分支不生效 | AC-2.7 |
| 5 | 作用域内取色 | TokenThemeStorage.GetTheme(scopeId) + TokenThemeWrapper.ApplyTokenTheme 应用 54 Token | AC-2.8 |
| 6 | 退出 WithTheme 作用域 | removeThemeInNative 清理 scopeId；native theme.pop 移除绑定 | AC-2.3 |

**[ThemeControl.setDefaultTheme]**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ThemeControl.setDefaultTheme(customTheme: CustomTheme \| undefined): void` |
| 开放范围 | Public（@since 12） |
| 关联 AC | AC-1.4, AC-1.5, AC-1.6, AC-1.7 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 CustomTheme | ArkThemeControl.ts 设置全局默认主题，下发 native theme.setDefaultTheme 写入 TokenThemeStorage 默认主题并 CacheSet 缓存 | AC-1.4 |
| 2 | 传入 undefined | 清除全局默认主题，回退 ObtainSystemTheme 系统主题 | AC-1.5 |
| 3 | 默认主题变更 | ArkThemeScopeManager.getFinalTheme 合并默认+作用域主题传播到全部已建作用域 | AC-1.6 |
| 4 | 作用域/默认均未覆盖某 Token | getFinalTheme 回退链：作用域主题 → 默认主题 → 系统主题 | AC-1.7 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12（CustomTheme/WithTheme/ThemeColorMode），API 20（CustomDarkColors）
- **API 版本号策略:** @since 12（Colors/CustomTheme/WithTheme/ThemeControl/ThemeColorMode），@since 20（CustomDarkColors）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Token 主题模型 | @ohos.arkui.theme 经 TokenTheme/TokenColors/TokenThemeStorage 落地，与 legacy GetPatternByName 资源主题并行 | AC-2.4 |
| SysCap | CustomTheme 为 SystemCapability.ArkUI.ArkUI.Full，@crossplatform、@atomicservice | AC-1.1 |
| 局部作用域隔离 | WithTheme 分配 scopeId，子树局部主题/色彩模式不影响全局 | AC-2.1~AC-2.3 |
| 双轨注册 | 内部 ThemeManager 经 THEME_BUILDERS + THEME_BUILDERS_KIT 双轨注册，token 主题经 TokenThemeStorage | AC-2.4 |

## context-references

```yaml
context-queries:
  - repo: "openharmony/interface_sdk-js"
    query: "@ohos.arkui.theme.d.ts Colors CustomTheme WithTheme ThemeControl declarations"
  - repo: "openharmony/arkui_ace_engine"
    query: "JSWithTheme sendThemeToNative removeThemeInNative WithTheme binding"
  - repo: "openharmony/arkui_ace_engine"
    query: "RegisterThemeAttributes createAndBindTheme setDefaultTheme native theme module"
  - repo: "openharmony/arkui_ace_engine"
    query: "TokenTheme TokenColors TokenThemeStorage ThemeColorMode"
```

**关键文档:** design.md (`specs/03-engine-framework/03-resource-theme/03-theme-framework/design.md`)
