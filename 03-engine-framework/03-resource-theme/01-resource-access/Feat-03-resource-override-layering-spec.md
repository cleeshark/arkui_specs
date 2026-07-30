# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 资源分层与 Override 适配器（配置作用域资源视图 / ResourceConfiguration / 系统应用资源区分） |
| 特性编号 | Func-03-03-01-Feat-03 |
| FuncID | 03-03-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ResourceConfiguration | 设备类型/方向/密度/字体比/色彩模式/mcc/mnc/语言等资源配置载体 |
| ADDED | ConfigurationChange | 色彩/语言/方向/dpi/字体/图标/皮肤/字体比/字重/热重载变更位域 |
| ADDED | ResourceAdapter::GetOverrideResourceAdapter | 配置作用域资源视图，运行时探测暗色资源不切换全局配置 |
| ADDED | ResourceAdapterImplV2::CreateOverrideResourceAdapter | 动态 UI 内容容器初始化时创建 override 适配器 |
| ADDED | AceContainer::InitResourceAndThemeManager / BuildResConfig / UpdateConfiguration | 容器级资源初始化与配置变更编排 |
| ADDED | @sys/@app 资源 ID 空间分离 | SYSTEM_RES_ID_START=0x7000000 系统资源 ID 偏移 |
| ADDED | V1 逐 bundle ResourceManager 切换 | UpdateResourceManager 按 bundle/module 切换当前 ResourceManager |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/03-resource-theme/01-resource-access/design.md`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 子系统边界声明

> ace_engine 的 "Override" 适配器是**配置作用域的资源视图**（按 colorMode/direction/dpi 等参数化派生 ResourceManager），用于在不切换全局主 ResourceManager 配置的前提下探测特定配置下的资源（如暗色资源）。**系统资源覆盖应用资源的分层逻辑、以及产品级资源配置/overlay，由全球化资源管理子系统 `OHOS::Global::Resource::ResourceManager` 拥有**，ace_engine 仅经 `GetOverrideResourceManager`/`GetOverrideResConfig`/`UpdateOverrideResConfig` 调用，不在 ace_engine 内实现。ace_engine 不存在独立的"产品配置 overlay"实现。

## 用户故事

### US-1: 运行时探测特定配置下的资源

**角色**: 框架开发者
**期望**: 我想要在不切换全局色彩模式的前提下探测暗色资源是否存在
**价值**: 以便组件在深浅色切换前预取双形态资源值

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `ResourceAdapter::GetOverrideResourceAdapter(config, configurationChange)` THEN 经 `sysResourceManager_->GetOverrideResConfig` 拷贝当前 override 配置，按 configurationChange 设置 colorMode/direction/dpi，再 `GetOverrideResourceManager` 返回派生适配器（`resource_adapter_impl_v2.cpp:1241-1258`） | 正常 |
| AC-1.2 | WHEN 运行时探测暗色资源 THEN `ExistDarkResById`/`ExistDarkResByName` 通过 override 适配器查询，不影响全局主 ResourceManager 配置（`resource_adapter_impl_v2.cpp:1260,1298`） | 正常 |
| AC-1.3 | WHEN title_bar_pattern 需要双形态资源 THEN 同时缓存 light/dark 默认色（`title_bar_pattern.cpp:110-135`） | 正常 |
| AC-1.4 | WHEN image_loader 需要局部色彩模式 THEN 经 override 适配器解析资源数据（`image_loader.cpp:683-693`） | 正常 |

### US-2: 动态 UI 内容的隔离资源作用域

**角色**: 框架开发者
**期望**: 我想要为动态 UI 内容（DYNAMIC_COMPONENT）创建隔离的 override 适配器
**价值**: 以便动态组件的资源配置变更不影响宿主容器

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `AceContainer::InitResourceAndThemeManager` 且 `isDynamicUIContent` 为真 THEN 调用 `CreateOverrideResourceAdapter` 创建 override 适配器（`ace_container.cpp:308,338-342`） | 正常 |
| AC-2.2 | WHEN `CreateOverrideResourceAdapter` 执行 THEN 从主 ResourceManager 读取 ResConfig，设置 colorMode，`GetOverrideResourceManager` 返回派生管理器并包装为 `ResourceAdapterImplV2`（`resource_adapter_impl_v2.cpp:182-201`） | 正常 |
| AC-2.3 | WHEN override 适配器 `isOverrideResourceAdapter_=true` THEN `UpdateConfig` 额外调用 `UpdateOverrideResConfig` 同步 override 配置（`resource_adapter_impl_v2.cpp:264,270-272`） | 正常 |

### US-3: 资源配置与变更位域

**角色**: 框架开发者
**期望**: 我想要通过 ResourceConfiguration + ConfigurationChange 描述资源配置并驱动刷新
**价值**: 以便色彩/语言/方向/dpi 变更触发资源与主题刷新

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `AceContainer::BuildResConfig` 合并 ParsedConfig THEN 生成 ResourceConfiguration（colorMode/direction/density/language/mcc/mnc/colorModeIsSetByApp/deviceAccess/fontFamily）并设置 ConfigurationChange 标志（`ace_container.cpp:3613`） | 正常 |
| AC-3.2 | WHEN `AceContainer::UpdateConfiguration` 触发 THEN 调用 `ResourceManager::GetInstance().UpdateResourceConfig` 传播到同 instanceId 全部适配器（`ace_container.cpp:3744,3769`） | 正常 |
| AC-3.3 | WHEN `ConfigurationChange` 含 `colorModeUpdate` THEN `ResourceAdapterImplV2::UpdateColorMode` 取容器 ResourceConfiguration 设置 colorMode 并 UpdateConfig（`resource_adapter_impl_v2.cpp:1214`） | 正常 |
| AC-3.4 | WHEN `NeedUpdateResConfig` 判定 Locale/DeviceType/Direction/ScreenDensity/ColorMode/InputDevice 任一变更 THEN 返回 true 触发刷新（`resource_adapter_impl_v2.cpp:252`） | 正常 |

### US-4: 系统资源与应用资源区分

**角色**: 框架开发者
**期望**: 我想要区分 `@sys` 系统资源与 `@app` 应用资源
**价值**: 以便组件按来源选择系统内置资源或 HAP 包资源

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 资源 id 以 `@sys.` 开头 THEN 数值 id 加 `SYSTEM_RES_ID_START=0x7000000` 落入系统资源空间（`theme_utils.cpp:32,49`） | 正常 |
| AC-4.2 | WHEN 资源 id 以 `@app.` 开头 THEN 按 `^@app\.(\w+)\.(\w+)$` 经 `GetResourceIdByName` 解析应用资源（`theme_utils.cpp:38,44,49`） | 正常 |
| AC-4.3 | WHEN V1 适配器切换 bundle/module THEN `UpdateResourceManager` 按 `(bundleName,moduleName)` 从 `resourceManagers_` 取或创建对应 ResourceManager（`resource_adapter_impl.cpp:636,655`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-RES-03 | UT | `resource_adapter_impl_v2.cpp:1241` |
| AC-1.2 | R-1 | TASK-RES-03 | UT | `resource_adapter_impl_v2.cpp:1260,1298` |
| AC-1.3 | R-1 | TASK-RES-03 | UT | `title_bar_pattern.cpp:110-135` |
| AC-1.4 | R-1 | TASK-RES-03 | UT | `image_loader.cpp:683-693` |
| AC-2.1 | R-2 | TASK-RES-03 | UT | `ace_container.cpp:308,338` |
| AC-2.2 | R-2 | TASK-RES-03 | UT | `resource_adapter_impl_v2.cpp:182-201` |
| AC-2.3 | R-2 | TASK-RES-03 | UT | `resource_adapter_impl_v2.cpp:264,270` |
| AC-3.1 | R-3 | TASK-RES-03 | UT | `ace_container.cpp:3613` |
| AC-3.2 | R-3 | TASK-RES-03 | UT | `ace_container.cpp:3744,3769` |
| AC-3.3 | R-3 | TASK-RES-03 | UT | `resource_adapter_impl_v2.cpp:1214` |
| AC-3.4 | R-3 | TASK-RES-03 | UT | `resource_adapter_impl_v2.cpp:252` |
| AC-4.1 | R-4 | TASK-RES-03 | UT | `theme_utils.cpp:32,49` |
| AC-4.2 | R-4 | TASK-RES-03 | UT | `theme_utils.cpp:38,49` |
| AC-4.3 | R-5 | TASK-RES-03 | UT | `resource_adapter_impl.cpp:636,655` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 GetOverrideResourceAdapter(config, configurationChange) | 经平台 GetOverrideResConfig + GetOverrideResourceManager 返回配置作用域派生适配器 | 不修改全局主 ResourceManager 配置 | AC-1.1~AC-1.4 |
| R-2 | 行为 | 动态 UI 内容容器初始化 | CreateOverrideResourceAdapter 设置 isOverrideResourceAdapter_=true，UpdateConfig 同步 UpdateOverrideResConfig | 仅 DYNAMIC_COMPONENT 走此路径 | AC-2.1~AC-2.3 |
| R-3 | 行为 | 资源配置变更 | BuildResConfig 合并生成 ResourceConfiguration + ConfigurationChange，UpdateResourceConfig 传播同 instanceId 全部适配器 | NeedUpdateResConfig 判定任一维度变更 | AC-3.1~AC-3.4 |
| R-4 | 行为 | 资源 id 前缀 @sys/@app | @sys 加 SYSTEM_RES_ID_START=0x7000000；@app 按名 GetResourceIdByName | 系统/应用 ID 空间分离 | AC-4.1, AC-4.2 |
| R-5 | 行为 | V1 适配器切换 bundle/module | UpdateResourceManager 从 resourceManagers_ 取或创建对应 ResourceManager 并切换当前 | V1 路径，V2 走 override | AC-4.3 |
| R-6 | 边界 | 系统覆盖应用/产品 overlay | 由全球化 OHOS::Global::Resource::ResourceManager 拥有，ace_engine 不实现 | ace_engine 仅调用 GetOverrideResourceManager 等 | 无 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | override 适配器派生、暗色资源探测、双形态缓存、局部色彩模式 |
| VM-2 | AC-2.1 ~ AC-2.3 | UT | 动态 UI 内容 override 适配器创建与配置同步 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | ResourceConfiguration/ConfigurationChange 编排与传播 |
| VM-4 | AC-4.1 ~ AC-4.3 | UT | @sys/@app 区分与 V1 逐 bundle 切换 |

## API 变更分析

> 本特性为已有实现补录，以下列出已有的公开和 InnerAPI 接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `ResourceAdapter::GetOverrideResourceAdapter(config, change)` | InnerApi | ResourceConfiguration&, ConfigurationChange& | RefPtr<ResourceAdapter> | 无 | 创建配置作用域 override 适配器 | AC-1.1 |
| `ResourceAdapterImplV2::CreateOverrideResourceAdapter(...)` | InnerApi | shared_ptr<ResourceManager>, ResourceInfo& | RefPtr<ResourceAdapterImplV2> | 无 | 动态 UI 内容 override 适配器工厂 | AC-2.2 |
| `AceContainer::BuildResConfig` | InnerApi | ParsedConfig& | void | 无 | 合并生成 ResourceConfiguration | AC-3.1 |
| `AceContainer::UpdateConfiguration` | InnerApi | ParsedConfig& | void | 无 | 顶层配置变更编排 | AC-3.2 |
| `ResourceAdapterImplV2::NeedUpdateResConfig` | InnerApi | ResourceConfiguration& | bool | 无 | 判定资源配置是否需刷新 | AC-3.4 |
| `ResourceAdapterImpl::UpdateResourceManager` | InnerApi | string bundleName, string moduleName | void | 无 | V1 逐 bundle/module 切换 ResourceManager | AC-4.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ResourceAdapterImplV2::UpdateConfig` | MODIFIED | override 适配器额外同步 UpdateOverrideResConfig | 动态 UI 内容走 CreateOverrideResourceAdapter | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 是，V1 适配器长期维护，新增能力统一走 V2 override 路径
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** @since 7（ResourceConfiguration/ConfigurationChange），@since 12（TokenThemeStorage 缓存同步）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Override 不改全局配置 | override 适配器为配置作用域派生视图，不修改主 ResourceManager 全局配置 | AC-1.1, AC-1.2 |
| 系统/产品 overlay 边界 | 系统资源覆盖应用资源与产品级 overlay 由全球化 ResourceManager 拥有，ace_engine 不实现 | R-6 |
| 配置变更同 instanceId 传播 | UpdateResourceConfig 传播到同 instanceId 全部适配器 | AC-3.2 |
| @sys/@app ID 空间分离 | 系统资源 id 偏移 SYSTEM_RES_ID_START=0x7000000 | AC-4.1 |

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ResourceAdapterImplV2 GetOverrideResourceAdapter CreateOverrideResourceAdapter override resource manager"
  - repo: "openharmony/arkui_ace_engine"
    query: "AceContainer BuildResConfig UpdateConfiguration ResourceConfiguration ConfigurationChange"
  - repo: "openharmony/arkui_ace_engine"
    query: "ThemeUtils SYSTEM_RES_ID_START @sys @app ParseThemeIdReference"
  - repo: "openharmony/arkui_ace_engine"
    query: "ResourceAdapterImpl UpdateResourceManager per bundle module resource manager switching"
```

**关键文档:** design.md (`specs/03-engine-framework/03-resource-theme/01-resource-access/design.md`)
