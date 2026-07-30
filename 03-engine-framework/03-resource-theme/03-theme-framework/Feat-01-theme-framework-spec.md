# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Theme 框架全量规格（注册/缓存/Token/颜色模式/通知） |
| 特性编号 | Func-03-03-03-Feat-01 |
| FuncID | 03-03-03 |
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
| ADDED | ThemeManager 抽象基类 + ThemeManagerImpl 实现 | API 7，基础主题管理框架 |
| ADDED | THEME_BUILDERS 静态注册表 | API 7，编译时主题注册 |
| ADDED | ThemeConstants 资源常量管理 | API 7，LoadTheme/ParseTheme/UpdateConfig |
| ADDED | RegisterThemeKit / THEME_BUILDERS_KIT 动态注册 | API 12，组件化 Kit 延迟注册 |
| ADDED | TokenTheme / TokenThemeStorage | API 12，运行时颜色 Token 容器和全局存储 |
| ADDED | TOKEN_THEME_WRAPPER_BUILDERS / _KIT 双轨注册 | API 12，Wrapper 注册机制 |
| ADDED | ThemeFactory 静态工厂 | API 12，统一 Kit 入口 GetTheme/GetTheme(scopeId) |
| ADDED | 颜色模式临时切换机制 | API 12，WithTheme 局部颜色模式支持 |
| MODIFIED | LoadResourceThemes 增加 TokenThemeStorage::CacheClear | API 12，Token 主题缓存同步清理 |
| ADDED | GetThemeMultiThread 多线程安全路径 | API 12+，MultiThreadBuildManager 分流 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/03-resource-theme/03-theme-framework/design.md`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 主题注册与查询

**角色**: 组件化 Kit 开发者
**期望**: 我想要通过 Kit 注册自定义主题并查询已注册的主题
**价值**: 以便组件化 Kit 能延迟注册主题而无需修改 ace_engine 核心代码

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `RegisterThemeKit(type, func)` 注册主题 THEN 主题被存入 `THEME_BUILDERS_KIT` map，后续 `GetTheme(type)` 优先从 Kit 注册表查询（`theme_manager_impl.cpp:275-282, 317-348`） | 正常 |
| AC-1.2 | WHEN 调用 `RegisterCustomThemeKit(type, func)` 注册 Wrapper THEN Wrapper 被存入 `TOKEN_THEME_WRAPPER_BUILDERS_KIT`，后续 `GetTheme(type, scopeId)` 优先从 Kit Wrapper 注册表查询（`theme_manager_impl.cpp:351-358, 421-463`） | 正常 |
| AC-1.3 | WHEN 重复调用 `RegisterThemeKit(type, func)` 注册同一 ThemeType THEN 第二次注册被忽略，`themes_` 中已有该类型时也直接返回不注册（`theme_manager_impl.cpp:277-280`） | 边界 |
| AC-1.4 | WHEN 查询未注册的 ThemeType THEN `GetThemeKit` 返回 nullptr，回退到 `GetThemeOrigin` 查 `THEME_BUILDERS` 静态表（`theme_manager_impl.cpp:300-302`） | 异常 |
| AC-1.5 | WHEN Kit 和静态表都未注册 THEN `GetThemeOrigin` 返回 nullptr（`theme_manager_impl.cpp:308-310`） | 异常 |

### US-2: 主题缓存管理

**角色**: 框架开发者
**期望**: 我想要缓存已构建的主题实例以避免重复构建
**价值**: 以便提高主题查询性能，减少资源解析开销

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `GetTheme(type)` 首次查询某类型 THEN 构建后存入 `themes_` map，后续查询直接从缓存返回（`theme_manager_impl.cpp:295-298, 313-314`） | 正常 |
| AC-2.2 | WHEN 调用 `LoadResourceThemes()` THEN `themes_`、`themeWrappersLight_`、`themeWrappersDark_` 三个 map 全部清空，并重新 `LoadTheme(currentThemeId_)`（`theme_manager_impl.cpp:493-499`） | 正常 |
| AC-2.3 | WHEN `GetThemeKit(type)` 构建主题成功 THEN 主题被 emplace 到 `themes_` map（`theme_manager_impl.cpp:341, 346`） | 正常 |
| AC-2.4 | WHEN `GetThemeKit(type, scopeId)` 构建 Wrapper 成 THEN Wrapper 被 emplace 到对应颜色模式的 `themeWrappersLight_` 或 `themeWrappersDark_` map（`theme_manager_impl.cpp:417, 462`） | 正常 |

### US-3: Token 主题存储

**角色**: 应用开发者
**期望**: 我想要通过 Token 主题作用域 ID 获取对应的 Token 主题实例
**价值**: 以便 WithTheme 场景下组件使用局部主题颜色

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `GetTheme(scopeId)` 查询 scopeId=0 THEN 返回 `GetDefaultTheme()`，即系统默认主题（`token_theme_storage.cpp:63-64`） | 正常 |
| AC-3.2 | WHEN `GetTheme(scopeId)` 查询已注册的 scopeId THEN 从 `themeScopeMap_` 查到 themeId，再从 `themeCache_` 查到 TokenTheme 实例（`token_theme_storage.cpp:66-70`） | 正常 |
| AC-3.3 | WHEN `GetTheme(scopeId)` 查询未注册的 scopeId THEN 返回空引用（`token_theme_storage.cpp:67-69`） | 异常 |
| AC-3.4 | WHEN `CacheClear()` 被调用 THEN `themeCache_` map 被清空，加锁保护 `themeCacheMutex_`（`token_theme_storage.cpp:121-125`） | 正常 |
| AC-3.5 | WHEN 系统主题 ID 为 -1 THEN 对应 `SYSTEM_THEME_LIGHT_ID`，为 -2 THEN 对应 `SYSTEM_THEME_DARK_ID`（`token_theme_storage.h:61-62`） | 边界 |
| AC-3.6 | WHEN scopeId 等于 `INVALID_THEME_SCOPE_ID = -3` THEN 查询 `themeScopeMap_` 未命中，返回空引用（`token_theme_storage.h:31, :67-69`） | 边界 |

### US-4: 颜色模式分桶缓存

**角色**: 框架开发者
**期望**: 我想要按颜色模式分别缓存 Theme Wrapper
**价值**: 以便深浅色模式下各自有独立的 Wrapper 实例，切换时无需重建

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `GetThemeWrappers(ColorMode::DARK)` 被调用 THEN 返回 `themeWrappersDark_` 引用（`theme_manager_impl.cpp:501-504`） | 正常 |
| AC-4.2 | WHEN `GetThemeWrappers(ColorMode::LIGHT)` 被调用 THEN 返回 `themeWrappersLight_` 引用（`theme_manager_impl.cpp:501-504`） | 正常 |
| AC-4.3 | WHEN Wrapper 构建时 `themeMode == COLOR_MODE_UNDEFINED` THEN 使用 `currentMode` 选择分桶（`theme_manager_impl.cpp:387, 432`） | 正常 |

### US-5: 颜色模式临时切换

**角色**: 应用开发者
**期望**: 我想要在 WithTheme 设置局部颜色模式时，主题构建使用正确的颜色模式
**价值**: 以便 WithTheme(dark) 在系统浅色模式下也能正确构建深色主题

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `GetThemeKit(type)` 发现 `localMode != UNDEFINED && localMode != systemMode` THEN 临时切换 ResourceManager 到 systemMode 构建，完成后恢复到 localMode（`theme_manager_impl.cpp:328-340`） | 正常 |
| AC-5.2 | WHEN `GetThemeOrigin(type, scopeId)` 发现 `themeMode != UNDEFINED && themeMode != currentMode` THEN 临时切换 ResourceManager 到 themeMode 构建，完成后恢复到 currentMode（`theme_manager_impl.cpp:400-415`） | 正常 |
| AC-5.3 | WHEN `GetCurrentColorMode()` 被调用 THEN 优先返回 `pipeline->GetLocalColorMode()`，若为 UNDEFINED 则返回 `Container::CurrentColorMode()`（`theme_manager_impl.cpp:506-513`） | 正常 |

### US-6: 主题变更通知

**角色**: 终端用户
**期望**: 我想要在系统主题切换后，应用 UI 自动更新为新主题颜色
**价值**: 以便无需重启应用即可看到主题变更效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN AceContainer::UpdateConfiguration 被调用 THEN 依次执行 `themeManager->UpdateConfig` → `ResourceManager::UpdateResourceConfig` → `themeManager->LoadResourceThemes`（`ace_container.cpp:3784-3788`） | 正常 |
| AC-6.2 | WHEN `LoadResourceThemes()` 执行 THEN `themes_`/`themeWrappersLight_`/`themeWrappersDark_` 被清空，`TokenThemeStorage::CacheClear()` 被调用（`theme_manager_impl.cpp:493-499`, `ace_container.cpp:3675`） | 正常 |
| AC-6.3 | WHEN 颜色模式仅变更（OnlyColorModeChange）THEN 走快速路径：`ReloadThemeCache()` → `OnFrontUpdated()` → `UpdateColorMode()` → `NotifyColorModeChange()`，跳过完整 FlushReload（`ace_container.cpp:3789-3793`） | 正常 |
| AC-6.4 | WHEN `NotifyColorModeChange(colorMode)` 执行 THEN 使用 400ms FRICTION 动画曲线包裹 `rootNode->NotifyColorModeChange(colorMode)` 遍历（`pipeline_context.cpp:7621-7650`） | 正常 |

### US-7: 多线程主题构建

**角色**: 框架开发者
**期望**: 我想要在多线程场景下安全地构建主题
**价值**: 以便组件化 Kit 在后台线程构建主题时不会出现数据竞争

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `MultiThreadBuildManager::IsThreadSafeNodeScope()` 返回 true THEN `GetTheme` 走 `GetThemeMultiThread` 路径（`theme_manager_impl.cpp:286-288`） | 正常 |
| AC-7.2 | WHEN 非 ThreadSafeNodeScope 场景 THEN `GetTheme` 使用 `std::recursive_mutex` 保护，走 `GetThemeNormal` 路径（`theme_manager_impl.cpp:289-291`） | 正常 |
| AC-7.3 | WHEN `LoadResourceThemes()` 在 ThreadSafeNodeScope 场景 THEN 走 `LoadResourceThemesMultiThread()` 路径（`theme_manager_impl.cpp:485-488`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2, R-3 | TASK-THEME-01 | UT | `test/unittest/core/theme/` |
| AC-2.1 ~ AC-2.4 | R-4, R-5 | TASK-THEME-01 | UT | theme_manager_impl 单测 |
| AC-3.1 ~ AC-3.6 | R-6, R-7, R-8 | TASK-THEME-01 | UT | token_theme_storage 单测 |
| AC-4.1 ~ AC-4.3 | R-9 | TASK-THEME-01 | UT | GetThemeWrappers 分桶测试 |
| AC-5.1 ~ AC-5.3 | R-10, R-11 | TASK-THEME-01 | UT | 颜色模式临时切换测试 |
| AC-6.1 ~ AC-6.4 | R-12, R-13, R-14 | TASK-THEME-01 | UT + 集成测试 | UpdateConfiguration 端到端测试 |
| AC-7.1 ~ AC-7.3 | R-15 | TASK-THEME-01 | UT | 多线程构建测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 RegisterThemeKit(type, func) | 主题存入 THEME_BUILDERS_KIT，GetThemeKit 优先查询 | themes_ 中已有同类型时不注册 | AC-1.1, AC-1.3 |
| R-2 | 行为 | 调用 RegisterCustomThemeKit(type, func) | Wrapper 存入 TOKEN_THEME_WRAPPER_BUILDERS_KIT | 已有同类型时不注册 | AC-1.2 |
| R-3 | 行为 | GetTheme(type) 查询 | themes_ → Kit → Origin 三级分发 | 全部 miss 返回 nullptr | AC-1.4, AC-1.5 |
| R-4 | 行为 | GetTheme(type) 首次构建 | 存入 themes_ map，后续直接缓存返回 | — | AC-2.1, AC-2.3 |
| R-5 | 行为 | LoadResourceThemes() 调用 | themes_/themeWrappersLight_/themeWrappersDark_ 全部 clear + LoadTheme 重建 | — | AC-2.2 |
| R-6 | 行为 | TokenThemeStorage::GetTheme(scopeId=0) | 返回 GetDefaultTheme() | scopeId=0 为系统默认 | AC-3.1 |
| R-7 | 行为 | TokenThemeStorage::GetTheme(scopeId) 已注册 | themeScopeMap_ 查 themeId → themeCache_ 查实例 | 未注册返回空引用 | AC-3.2, AC-3.3 |
| R-8 | 边界 | scopeId == INVALID_THEME_SCOPE_ID(-3) | themeScopeMap_ 未命中，返回空引用 | — | AC-3.6 |
| R-9 | 行为 | GetThemeWrappers(mode) | DARK → themeWrappersDark_，LIGHT → themeWrappersLight_ | UNDEFINED 归到 LIGHT 分桶 | AC-4.1 ~ AC-4.3 |
| R-10 | 行为 | GetThemeKit 中 localMode != systemMode | 临时切换 ResourceManager 到 systemMode，Build 后恢复 localMode | 仅普通主题（非 Wrapper） | AC-5.1 |
| R-11 | 行为 | GetThemeOrigin(type, scopeId) 中 themeMode != currentMode | 临时切换 ResourceManager 到 themeMode，Build 后恢复 currentMode | 仅 Wrapper 主题 | AC-5.2 |
| R-12 | 行为 | AceContainer::UpdateConfiguration | themeManager->UpdateConfig → LoadResourceThemes → NotifyColorModeChange | — | AC-6.1 |
| R-13 | 行为 | OnlyColorModeChange() 为 true | 走快速路径：ReloadThemeCache + UpdateColorMode，跳过完整 FlushReload | — | AC-6.3 |
| R-14 | 行为 | NotifyColorModeChange(colorMode) | 400ms FRICTION 动画包裹 rootNode->NotifyColorModeChange | onShow_ 为 false 时同步执行 | AC-6.4 |
| R-15 | 行为 | MultiThreadBuildManager::IsThreadSafeNodeScope() | GetTheme 走 GetThemeMultiThread，否则 recursive_mutex 保护 | — | AC-7.1 ~ AC-7.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | 双轨注册表查询和回退逻辑 |
| VM-2 | AC-2.1 ~ AC-2.4 | UT | themes_/themeWrappers 缓存生命周期 |
| VM-3 | AC-3.1 ~ AC-3.6 | UT | TokenThemeStorage scope 查询和缓存 |
| VM-4 | AC-4.1 ~ AC-4.3 | UT | 颜色模式分桶缓存选择 |
| VM-5 | AC-5.1 ~ AC-5.3 | UT | 颜色模式临时切换与恢复 |
| VM-6 | AC-6.1 ~ AC-6.4 | UT + 集成测试 | 主题变更通知端到端 |
| VM-7 | AC-7.1 ~ AC-7.3 | UT | 多线程主题构建安全 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| ThemeFactory::GetTheme(type) | InnerApi | ThemeType type | RefPtr<Theme> | N/A | 查询全局主题 | AC-1.1, AC-1.4 |
| ThemeFactory::GetTheme(type, scopeId) | InnerApi | ThemeType type, int32_t scopeId | RefPtr<Theme> | N/A | 查询带作用域的主题 | AC-1.2, AC-3.2 |
| ThemeFactory::CreateTheme(type, func) | InnerApi | ThemeType type, BuildFunc func | bool | N/A | 注册主题构建器 | AC-1.1 |
| ThemeFactory::CreateCustomTheme(type, func) | InnerApi | ThemeType type, BuildThemeWrapperFunc func | bool | N/A | 注册 Wrapper 构建器 | AC-1.2 |
| ThemeFactory::GetThemeScopeId(node) | InnerApi | RefPtr<FrameNode>& node | int32_t | N/A | 获取节点主题作用域 ID | AC-3.2 |
| ThemeManager::RegisterThemeKit(type, func) | InnerApi | ThemeType type, BuildFunc func | void | N/A | 注册 Kit 主题构建器 | AC-1.1 |
| ThemeManager::RegisterCustomThemeKit(type, func) | InnerApi | ThemeType type, BuildThemeWrapperFunc func | void | N/A | 注册 Kit Wrapper 构建器 | AC-1.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| ThemeManager::LoadResourceThemes | MODIFIED | API 12+ 新增 TokenThemeStorage::CacheClear 调用 | 无需迁移，行为增强 | AC-2.2, AC-6.2 |

## 接口规格

### 接口定义

**ThemeManagerImpl::GetTheme**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<Theme> ThemeManagerImpl::GetTheme(ThemeType type)` |
| 返回值 | `RefPtr<Theme>` — 主题实例，全部 miss 时为 nullptr |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | ThemeType (AceType::IdType) | 是 | 无 | 必须为已注册的 Theme::TypeId() |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | themes_ 已缓存该类型 | 直接返回缓存实例 | AC-2.1 |
| 2 | themes_ 未缓存，THEME_BUILDERS_KIT 有注册 | 调用 BuildFunc 构建，存入 themes_ | AC-1.1 |
| 3 | Kit 未注册，THEME_BUILDERS 有注册 | 调用静态 BuildFunc 构建，存入 themes_ | AC-1.4 |
| 4 | 两套注册表都未注册 | GetThemeOrigin 返回 nullptr | AC-1.5 |

**ThemeManagerImpl::GetTheme(type, scopeId)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<Theme> ThemeManagerImpl::GetTheme(ThemeType type, int32_t themeScopeId)` |
| 返回值 | `RefPtr<Theme>` — 主题或 Wrapper 实例，TokenTheme 不存在时回退到 GetTheme(type) |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2, AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | ThemeType | 是 | 无 | 必须为已注册的 Theme::TypeId() |
| themeScopeId | int32_t (TokenThemeScopeId) | 是 | 无 | 0=系统默认，-3=INVALID，正数=已注册 scope |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | TokenThemeStorage::GetTheme(scopeId) 返回 nullptr | 回退到 GetTheme(type) | AC-3.3 |
| 2 | TokenTheme 存在，Wrapper 缓存命中 | ApplyTokenTheme 后返回 | AC-2.4 |
| 3 | TokenTheme 存在，Wrapper 缓存未命中 | 构建 Wrapper + 颜色模式临时切换 + ApplyTokenTheme | AC-5.2 |

**TokenThemeStorage::GetTheme**

| 属性 | 值 |
|------|-----|
| 函数签名 | `const RefPtr<TokenTheme>& TokenThemeStorage::GetTheme(TokenThemeScopeId themeScopeId)` |
| 返回值 | `const RefPtr<TokenTheme>&` — Token 主题实例，未找到时为空引用 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1 ~ AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| themeScopeId | TokenThemeScopeId (int32_t) | 是 | 无 | 0=系统默认，-1=LIGHT，-2=DARK，-3=INVALID |

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - `LoadResourceThemes` API 12+ 新增 `TokenThemeStorage::CacheClear()` 调用，主题变更时同步清理 Token 主题缓存（AC-2.2, AC-6.2）
  - `GetTheme(type, scopeId)` API 12+ 新增颜色模式临时切换逻辑（AC-5.2）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 基础 Theme API @since 7，TokenTheme/ThemeFactory/Wrapper @since 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双轨注册表 | THEME_BUILDERS + THEME_BUILDERS_KIT 并存，Kit 优先查询 | AC-1.1, AC-1.4 |
| 三级缓存一致性 | themes_ + themeWrappersLight_/Dark_ + TokenThemeStorage::themeCache_ 需同步清理 | AC-2.2, AC-6.2 |
| 颜色模式临时切换线程安全 | UpdateColorMode 为全局操作，仅在 UI 线程执行 | AC-5.1, AC-5.2 |
| 系统主题特殊 ID | -1=LIGHT, -2=DARK, -3=INVALID，0=默认 | AC-3.1, AC-3.5, AC-3.6 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 主题首次构建 < 50ms，缓存查询 < 1ms | UT + 性能测试 | theme_manager_impl 构建耗时 |
| 内存 | 单个 Theme 实例 < 10KB，全局缓存 < 2MB | 内存分析 | themes_ map 内存占用 |
| 可靠性 | LoadResourceThemes 后所有缓存一致，无悬空引用 | UT | 缓存清理后 GetTheme 重建测试 |
| 可测试性 | 双轨注册表可独立测试，Mock ThemeConstants | UT | RegisterThemeKit 单测 |
| 定界定位 | TAG_LOGI(ACE_THEME) 日志记录主题加载和颜色切换 | hilog | theme 相关日志 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | Theme 框架不直接提供无障碍能力 | — |
| 大字体 | 否 | 字体缩放由 AceContainer::SetFontScaleAndWeightScale 处理 | — |
| 深色模式 | 是 | 双颜色集合 colors_/darkColors_ + 分桶缓存 themeWrappersLight_/Dark_ | AC-4.1 ~ AC-4.3, AC-5.1 ~ AC-5.2 |
| 多窗口/分屏 | 否 | Theme 框架为全局单例，不区分窗口 | — |
| 多用户 | 否 | 主题为系统级配置 | — |
| 版本升级 | 是 | API 7 基础框架 → API 12 TokenTheme → API 26+ ThemeFactory | 兼容性声明 |
| 生态兼容 | 否 | 不涉及 | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Theme 框架主题注册与查询
  作为 组件化 Kit 开发者
  我想要 通过 Kit 注册自定义主题并查询
  以便 组件化 Kit 延迟注册主题而无需修改核心代码

  Scenario: Kit 注册主题并查询
    Given THEME_BUILDERS_KIT 为空
    When 调用 RegisterThemeKit(SwitchTheme::TypeId(), buildFunc)
    Then THEME_BUILDERS_KIT 包含 SwitchTheme::TypeId() 映射
    And GetTheme(SwitchTheme::TypeId()) 返回非空 Theme 实例

  Scenario: 重复注册被忽略
    Given themes_ 已有 SwitchTheme 缓存
    When 再次调用 RegisterThemeKit(SwitchTheme::TypeId(), newFunc)
    Then themes_ 中已有该类型，直接返回不注册

  Scenario: 未注册类型回退
    Given THEME_BUILDERS_KIT 和 THEME_BUILDERS 都未注册 UnknownTheme
    When 调用 GetTheme(UnknownTheme::TypeId())
    Then GetThemeKit 返回 nullptr
    And GetThemeOrigin 返回 nullptr
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "arkui/ace_engine"
    query: "ThemeManagerImpl 双轨注册表 THEME_BUILDERS 和 THEME_BUILDERS_KIT 的查询优先级"
  - repo: "arkui/ace_engine"
    query: "TokenThemeStorage 系统主题 ID -1/-2 和 INVALID_THEME_SCOPE_ID -3 的处理逻辑"
  - repo: "arkui/ace_engine"
    query: "GetTheme type scopeId 中颜色模式临时切换 ResourceManager::UpdateColorMode 的 needRestore 路径"
  - repo: "arkui/ace_engine"
    query: "LoadResourceThemes 清空 themes_ themeWrappersLight_ themeWrappersDark_ 三级缓存的时序"
```

**关键文档:** `frameworks/core/components/theme/theme_manager_impl.h/.cpp`, `interfaces/inner_api/ace_kit/include/ui/view/theme/theme_factory.h`, `frameworks/core/components_ng/token_theme/token_theme_storage.h/.cpp`
