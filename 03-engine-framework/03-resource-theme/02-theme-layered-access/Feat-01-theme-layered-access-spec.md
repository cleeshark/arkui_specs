# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 主题分层访问全量规格（ThemeManager 四层解析 / TokenTheme / ThemeConstants / 色彩模式切换） |
| 特性编号 | Func-03-03-02-Feat-01 |
| FuncID | 03-03-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ThemeManager 抽象基类 + GetTheme/GetThemeConstants/LoadResourceThemes | @since 7，主题管理抽象接口 |
| ADDED | ThemeManagerImpl 实现 + themes_ 缓存 + THEME_BUILDERS 静态注册 | @since 7，origin 主题构建 |
| ADDED | ThemeConstants 资源封装 + GetColor/GetDimension/GetString/LoadTheme/ParseTheme | @since 7，委托 ResourceAdapter |
| ADDED | ThemeManager::RegisterThemeKit(type, BuildFunc) | Kit 主题注册式扩展机制 |
| ADDED | ThemeManager::GetTheme(type, themeScopeId) 重载 | @since API 后期，scope 级别主题查询 |
| ADDED | TokenTheme InnerAPI + colors_/darkColors_ + colorMode_ + IsDark/Colors | 亮暗色分离的主题色彩载体 |
| ADDED | TokenThemeStorage 单例 + themeScopeMap_/themeCache_ + StoreThemeScope/GetTheme/SetDefaultTheme | 全局 TokenTheme 缓存与 scope 映射 |
| ADDED | TokenThemeWrapper + ApplyTokenTheme 纯虚 + TOKEN_THEME_WRAPPER_BUILDERS 注册 | 主题 Wrapper 扩展机制 |
| ADDED | ThemeManager::RegisterCustomThemeKit(type, BuildThemeWrapperFunc) | 自定义 Wrapper 注册 |
| ADDED | themeWrappersLight_/themeWrappersDark_ 双缓存分离 | 明暗模式 Wrapper 独立缓存 |
| ADDED | GetThemeOrigin(type, scopeId) / GetThemeKit(type, scopeId) 带 scope 的分层查询 | 四层解析完整化 |
| ADDED | MultiThreadBuildManager + themeMultiThreadMutex_ 多线程构建 | 主题多线程安全构建 |
| ADDED | 本地色彩模式临时切换与恢复机制 | GetThemeKit/GetThemeOrigin 中 UpdateColorMode + 恢复 |
| MODIFIED | ThemeManager::GetTheme(type) | 新增 GetThemeNormal/GetThemeKit/GetThemeOrigin 分层 |
| MODIFIED | ThemeConstants::GetColor(uint32_t) | 新增 GetColorByName(string) 按名称查询重载 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/03-resource-theme/02-theme-layered-access/design.md`
- **依赖规格**: `specs/03-engine-framework/03-resource-theme/01-resource-access/Feat-01-resource-access-spec.md`
- **SDK 类型定义**:
  - `<OH_ROOT>/interface/sdk-js/api/@ohos.resourceManager.d.ts`（ColorMode 间接访问）

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 四层主题解析

**角色**: 组件框架开发者
**期望**: 我想要通过 GetTheme(type, scopeId) 按四层优先级获取主题
**价值**: 以便 TokenTheme scope 优先于 Kit/Origin 主题，支持局部主题覆盖

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `GetTheme(type, scopeId)` 且 TokenThemeStorage 中 scopeId 对应 TokenTheme 存在 THEN 返回经 ApplyTokenTheme 应用的 TokenThemeWrapper（`theme_manager_impl.cpp:369-373`） | 正常 |
| AC-1.2 | WHEN scopeId 对应 TokenTheme 不存在但 Kit 主题已注册 THEN fallback 到 GetThemeKit(type) 返回 Kit 主题（`theme_manager_impl.cpp:421-425, 317-348`） | 正常 |
| AC-1.3 | WHEN Kit 主题未注册 THEN fallback 到 GetThemeOrigin(type) 通过 THEME_BUILDERS 构建 origin 主题（`theme_manager_impl.cpp:305-315`） | 正常 |
| AC-1.4 | WHEN 调用 GetTheme(type)（无 scopeId） THEN 查 themes_ 缓存，未命中走 GetThemeKit→GetThemeOrigin 分层（`theme_manager_impl.cpp:293-303`） | 正常 |

### US-2: TokenThemeStorage scope 映射与缓存

**角色**: 框架开发者
**期望**: 我想要通过 TokenThemeStorage 管理 scopeId → themeId → TokenTheme 的映射和缓存
**价值**: 以便支持局部主题覆盖和全局主题复用

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `StoreThemeScope(scopeId, themeId)` THEN themeScopeMap_ 中记录 scopeId → themeId 映射（`token_theme_storage.h:37`） | 正常 |
| AC-2.2 | WHEN 调用 `GetTheme(scopeId)` 且 scopeId 已注册 THEN 通过 themeScopeMap_ 查 themeId，再查 themeCache_ 返回 TokenTheme（`token_theme_storage.h:39`） | 正常 |
| AC-2.3 | WHEN 调用 `SetDefaultTheme(theme, colorMode)` THEN defaultLightTheme_ 或 defaultDarkTheme_ 被设置（`token_theme_storage.h:42,83-84`） | 正常 |
| AC-2.4 | WHEN 调用 `CacheClear()` THEN themeCache_ 清空（`token_theme_storage.h:47`） | 正常 |

### US-3: 本地色彩模式临时切换

**角色**: 框架开发者
**期望**: 我想要在 TokenTheme 的 colorMode 与系统 colorMode 不一致时临时切换并恢复
**价值**: 以便某个 scope 固定使用暗色主题，而系统全局保持亮色

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN GetThemeKit(type) 中 localMode != COLOR_MODE_UNDEFINED 且 localMode != systemMode THEN 临时切换 ResourceManager 到 systemMode 构建，构建后恢复 localMode（`theme_manager_impl.cpp:328-340`） | 正常 |
| AC-3.2 | WHEN GetThemeOrigin(type, scopeId) 中 tokenTheme->GetColorMode() != COLOR_MODE_UNDEFINED 且 != currentMode THEN 临时切换 ResourceManager 到 themeMode，构建后恢复 currentMode（`theme_manager_impl.cpp:400-415`） | 正常 |
| AC-3.3 | WHEN 本地色彩模式临时切换完成后 THEN pipeline->SetLocalColorMode 恢复原值，ResourceManager::UpdateColorMode 恢复原值（`theme_manager_impl.cpp:336-340, 410-415`） | 正常 |
| AC-3.4 | WHEN tokenTheme->GetColorMode() == COLOR_MODE_UNDEFINED THEN 使用 GetCurrentColorMode() 当前模式，不触发临时切换（`theme_manager_impl.cpp:387, 432`） | 边界 |

### US-4: Light/Dark Wrapper 双缓存分离

**角色**: 框架开发者
**期望**: 我想要明暗模式的 TokenThemeWrapper 分别缓存
**价值**: 以便切换色彩模式时无需重建 Wrapper

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN GetThemeOrigin(type, scopeId) 调用 GetThemeWrappers(mode) 且 mode == DARK THEN 返回 themeWrappersDark_ 引用（`theme_manager_impl.cpp:501-503`） | 正常 |
| AC-4.2 | WHEN GetThemeOrigin(type, scopeId) 调用 GetThemeWrappers(mode) 且 mode != DARK THEN 返回 themeWrappersLight_ 引用（`theme_manager_impl.cpp:501-503`） | 正常 |
| AC-4.3 | WHEN LoadResourceThemesInner() 完成后 THEN themeWrappersLight_ 和 themeWrappersDark_ 被清空（`theme_manager_impl.cpp:496-497`） | 正常 |

### US-5: 多线程主题构建

**角色**: 框架开发者
**期望**: 我想要大型主题构建支持多线程加速
**价值**: 以便减少首帧渲染延迟

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN MultiThreadBuildManager::IsThreadSafeNodeScope() 返回 true THEN GetTheme 走 GetThemeMultiThread 路径（`theme_manager_impl.cpp:286-288, 362-364`） | 正常 |
| AC-5.2 | WHEN MultiThreadBuildManager::IsThreadSafeNodeScope() 返回 false THEN GetTheme 走 GetThemeNormal 路径，持有 themeMultiThreadMutex_ 锁（`theme_manager_impl.cpp:289-290, 365-366`） | 正常 |
| AC-5.3 | WHEN 多线程同时调用 GetTheme(type) THEN themeMultiThreadMutex_ (recursive_mutex) 保证 themes_ 缓存安全（`theme_manager_impl.h:161`） | 正常 |

### US-6: TokenTheme 亮暗色分离

**角色**: 框架开发者
**期望**: 我想要 TokenTheme 持有 colors_ 和 darkColors_ 两套色彩集合
**价值**: 以便同一个 TokenTheme 实例支持亮暗模式切换

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `TokenTheme::Colors()` 且 IsDark() 返回 true THEN 返回 darkColors_ 引用（`token_theme.h:47-50`） | 正常 |
| AC-6.2 | WHEN 调用 `TokenTheme::Colors()` 且 IsDark() 返回 false THEN 返回 colors_ 引用（`token_theme.h:47-50`） | 正常 |
| AC-6.3 | WHEN TokenTheme colorMode_ == COLOR_MODE_UNDEFINED THEN IsDark() 使用 TokenTheme::IsDarkMode() 系统模式判断（`token_theme.h:104-110`） | 边界 |
| AC-6.4 | WHEN 调用 `TokenTheme::SetColorMode(mode)` THEN colorMode_ 更新，且当前活跃 colors 调用 SetColorMode（`token_theme.h:52-59`） | 正常 |

### US-7: ThemeConstants 资源查询

**角色**: 组件开发者
**期望**: 我想要通过 ThemeConstants 获取颜色、尺寸、字符串等主题资源值
**价值**: 以便组件主题构建时从统一的资源适配器获取值

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `ThemeConstants::GetColor(uint32_t key)` THEN 返回对应 key 的 Color 值，未找到返回 Color::BLACK（`theme_constants.h:60`） | 正常 |
| AC-7.2 | WHEN 调用 `ThemeConstants::GetDimension(uint32_t key)` THEN 返回对应 key 的 Dimension 值，未找到返回 0.0（`theme_constants.h:76`） | 正常 |
| AC-7.3 | WHEN 调用 `ThemeConstants::GetString(uint32_t key)` THEN 返回对应 key 的 string 值，未找到返回空字符串（`theme_constants.h:124`） | 正常 |
| AC-7.4 | WHEN 调用 `ThemeConstants::LoadTheme(themeId)` THEN 从系统资源加载主题到 currentThemeStyle_（`theme_constants.h:302`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:369-373` |
| AC-1.2 | R-2 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:421-425, 317-348` |
| AC-1.3 | R-3 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:305-315` |
| AC-1.4 | R-4 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:293-303` |
| AC-2.1 | R-5 | TASK-THEME-01 | UT | `token_theme_storage.h:37` |
| AC-2.2 | R-6 | TASK-THEME-01 | UT | `token_theme_storage.h:39` |
| AC-2.3 | R-7 | TASK-THEME-01 | UT | `token_theme_storage.h:42,83-84` |
| AC-2.4 | R-8 | TASK-THEME-01 | UT | `token_theme_storage.h:47` |
| AC-3.1 | R-9 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:328-340` |
| AC-3.2 | R-10 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:400-415` |
| AC-3.3 | R-9, R-10 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:336-340, 410-415` |
| AC-3.4 | R-11 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:387, 432` |
| AC-4.1 | R-12 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:501-503` |
| AC-4.2 | R-12 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:501-503` |
| AC-4.3 | R-13 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:496-497` |
| AC-5.1 | R-14 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:286-288, 362-364` |
| AC-5.2 | R-15 | TASK-THEME-01 | UT | `theme_manager_impl.cpp:289-290, 365-366` |
| AC-5.3 | R-16 | TASK-THEME-01 | UT | `theme_manager_impl.h:161` |
| AC-6.1 | R-17 | TASK-THEME-01 | UT | `token_theme.h:47-50, 104-110` |
| AC-6.2 | R-17 | TASK-THEME-01 | UT | `token_theme.h:47-50, 104-110` |
| AC-6.3 | R-18 | TASK-THEME-01 | UT | `token_theme.h:106-108` |
| AC-6.4 | R-19 | TASK-THEME-01 | UT | `token_theme.h:52-59` |
| AC-7.1 | R-20 | TASK-THEME-01 | UT | `theme_constants.h:60` |
| AC-7.2 | R-20 | TASK-THEME-01 | UT | `theme_constants.h:76` |
| AC-7.3 | R-20 | TASK-THEME-01 | UT | `theme_constants.h:124` |
| AC-7.4 | R-21 | TASK-THEME-01 | UT | `theme_constants.h:302` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetTheme(type, scopeId) 且 TokenThemeStorage::GetTheme(scopeId) 返回有效 TokenTheme | 走 GetThemeKit(type, scopeId) 路径，查询/创建 TokenThemeWrapper，ApplyTokenTheme 后返回 | TokenTheme 必须非空 | AC-1.1 |
| R-2 | 行为 | GetThemeKit(type, scopeId) 返回 nullptr（Kit 未注册或 TokenTheme 不存在） | Fallback 到 GetThemeOrigin(type, scopeId) | Kit 层必须返回 nullptr 而非异常 | AC-1.2 |
| R-3 | 行为 | GetThemeOrigin(type) 且 THEME_BUILDERS 中有 type 对应 builder | 调用 builder->second(themeConstants_) 构建，存入 themes_ 并返回 | THEME_BUILDERS 为静态注册表 | AC-1.3 |
| R-4 | 行为 | GetTheme(type)（无 scopeId） | 先查 themes_ 缓存，未命中走 GetThemeKit→GetThemeOrigin 分层 | 无 scopeId 时跳过 TokenTheme scope 层 | AC-1.4 |
| R-5 | 行为 | StoreThemeScope(scopeId, themeId) | themeScopeMap_ 记录 scopeId → themeId 映射 | scopeId >= 0 为用户 scope | AC-2.1 |
| R-6 | 行为 | GetTheme(scopeId) | 先查 themeScopeMap_ 获取 themeId，再查 themeCache_ 返回 TokenTheme | scopeId 未注册时返回空 | AC-2.2 |
| R-7 | 行为 | SetDefaultTheme(theme, colorMode) | 按 colorMode 设置 defaultLightTheme_ 或 defaultDarkTheme_ | colorMode 为 LIGHT 或 DARK | AC-2.3 |
| R-8 | 行为 | CacheClear() | 清空 themeCache_ 中的所有 TokenTheme 实例 | 不影响 themeScopeMap_ 和 defaultTheme | AC-2.4 |
| R-9 | 行为 | GetThemeKit(type) 中 localMode != UNDEFINED 且 localMode != systemMode | 临时切换 ResourceManager 到 systemMode，清除 localColorMode，构建后恢复 localMode 和 ResourceManager | 切换和恢复必须配对 | AC-3.1, AC-3.3 |
| R-10 | 行为 | GetThemeOrigin(type, scopeId) 中 themeMode != UNDEFINED 且 themeMode != currentMode | 临时切换 ResourceManager 到 themeMode，设置 localColorMode，构建后恢复 | 切换和恢复必须配对 | AC-3.2, AC-3.3 |
| R-11 | 边界 | tokenTheme->GetColorMode() == COLOR_MODE_UNDEFINED | 使用 GetCurrentColorMode() 当前模式，不触发临时切换 | 无 | AC-3.4 |
| R-12 | 行为 | GetThemeWrappers(mode) 调用 | mode == DARK 返回 themeWrappersDark_，否则返回 themeWrappersLight_ | 无 | AC-4.1, AC-4.2 |
| R-13 | 行为 | LoadResourceThemesInner() 完成 | themeWrappersLight_ 和 themeWrappersDark_ 被清空 | 无 | AC-4.3 |
| R-14 | 行为 | MultiThreadBuildManager::IsThreadSafeNodeScope() 返回 true | GetTheme 走 GetThemeMultiThread 路径 | 无锁路径 | AC-5.1 |
| R-15 | 行为 | MultiThreadBuildManager::IsThreadSafeNodeScope() 返回 false | GetTheme 走 GetThemeNormal 路径，持有 themeMultiThreadMutex_ | recursive_mutex | AC-5.2 |
| R-16 | 行为 | 多线程同时调用 GetTheme(type) | themeMultiThreadMutex_ 保证 themes_ 缓存安全 | recursive_mutex 可重入 | AC-5.3 |
| R-17 | 行为 | 调用 TokenTheme::Colors() | IsDark() 为 true 返回 darkColors_，false 返回 colors_ | colors_ 或 darkColors_ 可能为空 | AC-6.1, AC-6.2 |
| R-18 | 边界 | TokenTheme colorMode_ == COLOR_MODE_UNDEFINED | IsDark() 使用 TokenTheme::IsDarkMode() 系统模式判断 | 无 | AC-6.3 |
| R-19 | 行为 | 调用 TokenTheme::SetColorMode(mode) | colorMode_ 更新，当前活跃 colors 调用 SetColorMode(mode) | 无 | AC-6.4 |
| R-20 | 行为 | 调用 ThemeConstants::GetColor/GetDimension/GetString(key) | 委托 resAdapter_->GetColor/GetDimension/GetString(key) 查询，未找到返回默认值 | BLACK/0.0/空字符串 | AC-7.1 ~ AC-7.3 |
| R-21 | 行为 | 调用 ThemeConstants::LoadTheme(themeId) | 从系统资源加载主题到 currentThemeStyle_ | themeId 有效 | AC-7.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | 四层主题解析优先级：TokenTheme scope → Kit → Origin → Resource |
| VM-2 | AC-2.1 ~ AC-2.4 | UT | TokenThemeStorage scope 映射、缓存、默认主题、清空 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | 本地色彩模式临时切换与恢复（GetThemeKit 和 GetThemeOrigin 两条路径） |
| VM-4 | AC-4.1 ~ AC-4.3 | UT | Light/Dark Wrapper 双缓存分离 + GetThemeWrappers 路由 + LoadResourceThemesInner 清空 |
| VM-5 | AC-5.1 ~ AC-5.3 | UT | 多线程构建（IsThreadSafeNodeScope 判断 + recursive_mutex 保护） |
| VM-6 | AC-6.1 ~ AC-6.4 | UT | TokenTheme 亮暗色分离 + IsDark/Colors 切换 + SetColorMode |
| VM-7 | AC-7.1 ~ AC-7.4 | UT | ThemeConstants 资源查询（GetColor/GetDimension/GetString + LoadTheme） |

## API 变更分析

> 本特性为已有实现补录，以下列出已有的 InnerAPI 接口。无公开 SDK 主题命名空间。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| ThemeManager::GetTheme(type) | InnerApi | ThemeType | RefPtr<Theme> | 无 | 获取主题（四层解析） | AC-1.4 |
| ThemeManager::GetTheme(type, scopeId) | InnerApi | ThemeType, int32_t | RefPtr<Theme> | 无 | 获取带 scopeId 的主题 | AC-1.1 ~ AC-1.3 |
| ThemeManager::GetThemeConstants() | InnerApi | 无 | RefPtr<ThemeConstants> | 无 | 获取主题常量 | AC-7.1 ~ AC-7.4 |
| ThemeManager::LoadResourceThemes() | InnerApi | 无 | void | 无 | 加载资源主题 | AC-4.3 |
| ThemeManager::GetResourceLimitKeys() | InnerApi | 无 | uint32_t | 无 | 获取资源限制键 | 无 |
| ThemeManager::RegisterThemeKit(type, func) | InnerApi | ThemeType, BuildFunc | void | 无 | 注册 Kit 主题 builder | AC-1.2 |
| ThemeManager::RegisterCustomThemeKit(type, func) | InnerApi | ThemeType, BuildThemeWrapperFunc | void | 无 | 注册自定义 Wrapper builder | AC-1.1 |
| ThemeConstants::GetColor(key) | InnerApi | uint32_t | Color | 无 | 按资源 ID 获取颜色 | AC-7.1 |
| ThemeConstants::GetDimension(key) | InnerApi | uint32_t | Dimension | 无 | 按资源 ID 获取尺寸 | AC-7.2 |
| ThemeConstants::GetString(key) | InnerApi | uint32_t | string | 无 | 按资源 ID 获取字符串 | AC-7.3 |
| ThemeConstants::LoadTheme(themeId) | InnerApi | int32_t | void | 无 | 从系统资源加载主题 | AC-7.4 |
| ThemeConstants::ParseTheme() | InnerApi | 无 | void | 无 | 解析主题样式 | 无 |
| ThemeConstants::GetThemeStyle() | InnerApi | 无 | RefPtr<ThemeStyle> | 无 | 获取当前主题样式 | 无 |
| TokenThemeStorage::GetInstance() | InnerApi | 无 | TokenThemeStorage* | 无 | 获取单例 | AC-2.1 ~ AC-2.4 |
| TokenThemeStorage::StoreThemeScope(scopeId, themeId) | InnerApi | TokenThemeScopeId, int32_t | void | 无 | 注册 scope 映射 | AC-2.1 |
| TokenThemeStorage::GetTheme(scopeId) | InnerApi | TokenThemeScopeId | RefPtr<TokenTheme>& | 无 | 按 scopeId 获取 TokenTheme | AC-2.2 |
| TokenThemeStorage::SetDefaultTheme(theme, colorMode) | InnerApi | RefPtr<TokenTheme>, ColorMode | void | 无 | 设置默认主题 | AC-2.3 |
| TokenThemeStorage::CacheClear() | InnerApi | 无 | void | 无 | 清空缓存 | AC-2.4 |
| TokenTheme::Colors() | InnerApi | 无 | RefPtr<TokenColors>& | 无 | 获取当前模式色彩集 | AC-6.1, AC-6.2 |
| TokenTheme::IsDark() | InnerApi | 无 | bool | 无 | 判断是否暗色模式 | AC-6.3 |
| TokenTheme::SetColorMode(mode) | InnerApi | ColorMode | void | 无 | 设置色彩模式 | AC-6.4 |
| TokenThemeWrapper::ApplyTokenTheme(theme) | InnerApi | TokenTheme& | void | 无 | 应用 TokenTheme（纯虚） | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| ThemeManager::GetTheme(type) | MODIFIED | 新增 GetThemeNormal/GetThemeKit/GetThemeOrigin 分层内部实现 | 调用方无感知，外部接口不变 | AC-1.4 |
| ThemeConstants::GetColor(uint32_t) | MODIFIED | 新增 GetColorByName(string) 按名称查询重载 | 原 ID 查询保留，新增按名称查询 | AC-7.1 |

## 接口规格

### 接口定义

**ThemeManager::GetTheme(type, scopeId)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `virtual RefPtr<Theme> ThemeManager::GetTheme(ThemeType type, int32_t themeScopeId) = 0` |
| 返回值 | `RefPtr<Theme>` — 四层解析结果，nullptr 表示无可用主题 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | `ThemeType` | 是 | 无 | 有效的 ThemeType 枚举值 |
| themeScopeId | `int32_t` | 是 | 无 | >= -3（INVALID_THEME_SCOPE_ID）；-1=LIGHT, -2=DARK, -3=INVALID |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | TokenThemeStorage 有 scopeId 对应 TokenTheme | 走 GetThemeKit(type, scopeId) 创建/查询 Wrapper | AC-1.1 |
| 2 | Kit 未注册或 TokenTheme 不存在 | Fallback 到 GetThemeOrigin(type, scopeId) | AC-1.2 |
| 3 | Origin 也无 scopeId 的 TokenTheme | Fallback 到 GetTheme(type) 无 scope | AC-1.3 |
| 4 | 所有层均未命中 | 返回 nullptr | AC-1.3 |

---

**TokenThemeStorage::GetTheme(scopeId)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `const RefPtr<TokenTheme>& TokenThemeStorage::GetTheme(TokenThemeScopeId themeScopeId)` |
| 返回值 | `RefPtr<TokenTheme>&` — 对应 scopeId 的 TokenTheme，空表示未注册 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| themeScopeId | `TokenThemeScopeId (int32_t)` | 是 | 无 | >= -3；INVALID_THEME_SCOPE_ID = -3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | scopeId 已注册且 themeId 在 themeCache_ 中 | 返回缓存的 TokenTheme | AC-2.2 |
| 2 | scopeId 未注册 | 返回空 RefPtr | AC-2.2 |
| 3 | scopeId 已注册但 themeId 不在 themeCache_ 中 | 返回空 RefPtr | AC-2.2 |

---

**TokenTheme::Colors()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `const RefPtr<TokenColors>& TokenTheme::Colors() const` |
| 返回值 | `RefPtr<TokenColors>&` — 当前模式对应的色彩集合（colors_ 或 darkColors_） |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-6.1, AC-6.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无 | — | — | — | 无参数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | IsDark() 返回 true | 返回 darkColors_ | AC-6.1 |
| 2 | IsDark() 返回 false | 返回 colors_ | AC-6.2 |

---

**ThemeConstants::GetColor(key)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Color ThemeConstants::GetColor(uint32_t key) const` |
| 返回值 | `Color` — 资源 ID 对应的颜色，未找到返回 Color::BLACK |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-7.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| key | `uint32_t` | 是 | 无 | 有效的资源 ID |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效资源 ID | 返回对应颜色值 | AC-7.1 |
| 2 | 资源 ID 不存在 | 返回 Color::BLACK | AC-7.1 |

## 兼容性声明

- **已有 API 行为变更:** 是，GetTheme(type) 内部实现变更为四层解析，但外部接口不变；ThemeConstants::GetColor 新增按名称查询重载
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 主题无独立公开 SDK 命名空间，无 @since 标注；InnerAPI 通过 ace_kit 头文件暴露

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 四层解析优先级 | TokenTheme scope → Kit → Origin → Resource，上层命中则不继续下沉 | AC-1.1 ~ AC-1.4 |
| 本地色彩模式原子性 | UpdateColorMode + 构建 + 恢复必须配对，中间异常可能残留错误模式 | AC-3.1 ~ AC-3.3 |
| Light/Dark 双缓存 | themeWrappersLight_ 和 themeWrappersDark_ 分离缓存，切换时不重建 | AC-4.1 ~ AC-4.3 |
| 多线程安全 | themeMultiThreadMutex_ (recursive_mutex) 保护 themes_ 和 themeWrappers | AC-5.1 ~ AC-5.3 |
| TokenThemeStorage 全局单例 | 跨实例共享 themeCache_，通过 scopeId 区分 | AC-2.1 ~ AC-2.4 |
| 系统主题 ID 约定 | LIGHT=-1, DARK=-2, INVALID=-3，负数避免与用户 themeId 冲突 | AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | GetTheme 缓存命中耗时 < 2ms | UT 计时 | `theme_manager_impl.cpp:295-297` themes_ 查找 |
| 内存 | 每个 TokenThemeWrapper 实例约 < 10KB | 内存分析 | TokenThemeWrapper 为轻量色彩映射 |
| 可靠性 | 四层解析每层有 fallback，最终返回 nullptr 而非崩溃 | UT | `theme_manager_impl.cpp:301, 380` CHECK_NULL_RETURN |
| 可测试性 | TokenThemeStorage 可通过 CacheClear 清空状态 | UT | `token_theme_storage.h:47` |
| 安全 | TokenThemeStorage 操作受 themeCacheMutex_ 保护 | UT | `token_theme_storage.h:76` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | N/A | N/A | N/A |
| 平板 | 无差异 | N/A | N/A | N/A |
| 折叠屏 | 无差异 | N/A | N/A | N/A |

> 主题分层访问为框架层能力，设备行为一致。设备差异由 HAP 包主题资源文件自身决定，不在本规格范围。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 主题色彩间接用于无障碍前景/背景色，无独立逻辑 | 无 |
| 大字体 | 否 | 字体大小由 ThemeConstants::GetDimension 返回，不改变解析机制 | 无 |
| 深色模式 | 是 | 主题系统通过 Light/Dark 双缓存和 TokenTheme colorMode 支持深色模式 | AC-3.1 ~ AC-3.4, AC-4.1 ~ AC-4.3, AC-6.1 ~ AC-6.4 |
| 多窗口/分屏 | 是 | 不同窗口可能对应不同 scopeId，通过 TokenThemeStorage scope 映射隔离 | AC-2.1, AC-2.2 |
| 多用户 | 否 | 多用户主题隔离由系统主题服务处理 | 无 |
| 版本升级兼容 | 是 | 四层解析为增量演进，新增层不影响旧层 fallback | AC-1.1 ~ AC-1.4 |
| 生态兼容 | 否 | N/A | 无 |

## 行为场景（可选，Gherkin）

> L2+（复杂）使用 Gherkin 场景。

```gherkin
Feature: 主题分层访问
  作为 组件框架开发者
  我想要 通过四层解析优先级获取主题
  以便 TokenTheme scope 优先于 Kit/Origin，支持局部主题覆盖

  Scenario: TokenTheme scope 命中
    Given TokenThemeStorage 中 scopeId=1 对应 TokenTheme 已注册
    And TOKEN_THEME_WRAPPER_BUILDERS_KIT 中已注册 Button 类型的 Wrapper builder
    When 调用 GetTheme(ThemeType::BUTTON, 1)
    Then 返回经 ApplyTokenTheme 应用的 TokenThemeWrapper
    And 不调用 GetThemeOrigin

  Scenario: TokenTheme scope 未命中，Kit 命中
    Given TokenThemeStorage 中 scopeId=2 无 TokenTheme
    And THEME_BUILDERS_KIT 中已注册 Button 类型的 Kit builder
    When 调用 GetTheme(ThemeType::BUTTON, 2)
    Then Fallback 到 GetThemeKit 返回 Kit 主题
    And 不调用 GetThemeOrigin

  Scenario: 四层全部未命中
    Given TokenThemeStorage 中 scopeId=3 无 TokenTheme
    And THEME_BUILDERS_KIT 中未注册该类型
    And THEME_BUILDERS 中未注册该类型
    When 调用 GetTheme(unknown_type, 3)
    Then 返回 nullptr

  Scenario Outline: 本地色彩模式临时切换
    Given localMode 为 <localMode>，systemMode 为 <systemMode>
    When 调用 GetThemeKit(type)
    Then 临时切换 ResourceManager 到 systemMode
    And 构建完成后恢复 localMode 和 ResourceManager

    Examples:
      | localMode | systemMode |
      | DARK | LIGHT |
      | LIGHT | DARK |

  Scenario: TokenTheme colorMode 为 UNDEFINED 时不切换
    Given TokenTheme 的 colorMode 为 COLOR_MODE_UNDEFINED
    When 调用 GetThemeOrigin(type, scopeId)
    Then 使用 GetCurrentColorMode 当前模式
    And 不调用 ResourceManager::UpdateColorMode
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
    query: "ThemeManagerImpl GetThemeNormal GetThemeKit GetThemeOrigin four-layer theme resolution"
  - repo: "openharmony/arkui_ace_engine"
    query: "TokenThemeStorage StoreThemeScope GetTheme themeScopeMap_ themeCache_ implementation"
  - repo: "openharmony/arkui_ace_engine"
    query: "TokenTheme IsDark Colors colorMode_ darkColors_ local color mode switching"
  - repo: "openharmony/arkui_ace_engine"
    query: "GetThemeOrigin local color mode temporary switch and restore ResourceManager UpdateColorMode"
  - repo: "openharmony/arkui_ace_engine"
    query: "themeWrappersLight_ themeWrappersDark_ GetThemeWrappers dual cache separation"
  - repo: "openharmony/arkui_ace_engine"
    query: "MultiThreadBuildManager IsThreadSafeNodeScope themeMultiThreadMutex multi-thread theme build"
```

**关键文档:** design.md (`specs/03-engine-framework/03-resource-theme/02-theme-layered-access/design.md`)
