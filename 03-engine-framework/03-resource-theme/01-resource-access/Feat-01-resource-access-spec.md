# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 资源访问内部机制（ResourceManager / ResourceAdapter / ResourceObject / V1V2 适配器） |
| 特性编号 | Func-03-03-01-Feat-01 |
| FuncID | 03-03-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 6 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 6 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ResourceManager 单例 + GetOrCreateResourceAdapter | @since 6，per-instanceId 隔离的资源适配器管理 |
| ADDED | ResourceAdapter 抽象基类 + Create 工厂 | @since 6，GetColor/GetDimension/GetString/GetMedia/GetRawfile |
| ADDED | ResourceAdapterImpl V1 实现 | @since 6，封装 Global::Resource::ResourceManager |
| ADDED | ResourceAdapterImplV2 V2 实现 | 暗色资源检测、override 适配器、pattern 主题样式 |
| ADDED | ResourceAdapter::CreateV2 工厂 | V2 适配器创建入口 |
| ADDED | ResourceAdapter::CreateNewResourceAdapter 工厂 | 带实际 instanceId 的 V2 适配器创建 |
| ADDED | ResourceObject InnerAPI | id/type/instanceId/params/bundleName/moduleName/colorMode/hasDarkRes |
| ADDED | CountLimitLRU 缓存 | ResourceManager 内置 LRU，默认容量 3 |
| ADDED | ResourceManager::SetResourceCacheSize | 动态调整 LRU 容量 |
| ADDED | ResourceManager::AddResourceLoadError/DumpResLoadError | 资源加载错误追踪，最多 100 条 |
| MODIFIED | ResourceAdapter ExistDarkResById/ExistDarkResByName | V2 新增暗色资源检测能力 |
| MODIFIED | ResourceAdapter GetOverrideResourceAdapter | V2 新增 override 适配器创建能力 |
| MODIFIED | ResourceAdapter UpdateColorMode/GetResourceColorMode | V2 新增运行时色彩模式切换能力 |
| MODIFIED | ResourceAdapter GetPatternByName | V2 新增 pattern 主题样式获取能力 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/03-resource-theme/01-resource-access/design.md`
- **SDK 类型定义**:
  - `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/units.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 资源适配器获取与隔离

**角色**: 框架开发者
**期望**: 我想要通过 ArkUI 实例独立的 ResourceAdapter 访问 HAP 包资源
**价值**: 以便多实例场景下各实例资源访问互不干扰

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `ResourceManager::GetInstance().GetOrCreateResourceAdapter(resourceObject)` THEN 返回与 resourceObject.GetInstanceId() 绑定的 ResourceAdapter 实例 | 正常 |
| AC-1.2 | WHEN 同一 instanceId + bundleName + moduleName 第二次调用 GetOrCreateResourceAdapter THEN 返回缓存的同一 ResourceAdapter 实例（LRU 命中） | 正常 |
| AC-1.3 | WHEN 不同 instanceId 的 ResourceObject 调用 GetOrCreateResourceAdapter THEN 返回各自独立的 ResourceAdapter 实例 | 正常 |
| AC-1.4 | WHEN resourceObject 为 nullptr 传入 GetOrCreateResourceAdapter THEN 返回 nullptr（`resource_manager.cpp:56` CHECK_NULL_RETURN） | 异常 |

### US-2: LRU 缓存管理

**角色**: 框架开发者
**期望**: 我想要 ResourceManager 通过 LRU 缓存管理 ResourceAdapter 实例，控制内存占用
**价值**: 以便在多 HAP 包场景下自动淘汰不活跃的适配器

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 首次为某 bundleName.moduleName.instanceId 创建适配器 THEN 通过 `AddResourceAdapter` 存入 `cache_` 和 `cacheList_`（`resource_manager.cpp:88-101`） | 正常 |
| AC-2.2 | WHEN 缓存数量超过 `capacity_`（默认 3） THEN LRU 从 `cacheList_` 尾部淘汰最久未使用的适配器（`resource_manager.cpp:262`） | 边界 |
| AC-2.3 | WHEN 调用 `SetResourceCacheSize(size_t cacheSize)` THEN `capacity_` 更新为新值，超出时立即淘汰（`resource_manager.cpp:261-262`） | 正常 |
| AC-2.4 | WHEN `bundleName` 和 `moduleName` 均为空 THEN `MakeCacheKey` 返回 `to_string(instanceId)` 作为缓存键（`resource_manager.cpp:82-83`） | 边界 |

### US-3: V1 适配器资源访问

**角色**: 框架开发者
**期望**: 我想要通过 ResourceAdapter 获取颜色、尺寸、字符串、媒体等资源值
**价值**: 以便在 ArkUI 组件中使用 $r/$rawfile 引用的资源

> **V1 接入约束**: V1 适配器（ResourceAdapterImpl / `ResourceAdapter::Create()`）在任何情况下都不应主动接入；资源访问统一通过 V2（`ResourceAdapter::CreateV2()` / `CreateNewResourceAdapter()`）接入。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `ResourceAdapter::GetColor(uint32_t resId)` THEN 返回 `Color` 对应资源 ID 的颜色值（`resource_adapter.h:88` 纯虚，`resource_adapter_impl.h:41` V1 覆写） | 正常 |
| AC-3.2 | WHEN 调用 `ResourceAdapter::GetDimension(uint32_t resId)` THEN 返回 `Dimension` 对应资源 ID 的尺寸值（`resource_adapter.h:95` 纯虚） | 正常 |
| AC-3.3 | WHEN 调用 `ResourceAdapter::GetString(uint32_t resId)` THEN 返回 `string` 对应资源 ID 的字符串值（`resource_adapter.h:102` 纯虚） | 正常 |
| AC-3.4 | WHEN 调用 `ResourceAdapter::GetRawfile(string fileName)` THEN 返回 rawfile 的文件路径（`resource_adapter.h:160` 虚函数） | 正常 |
| AC-3.5 | WHEN 资源 ID 不存在 THEN GetColor 返回 Color::BLACK，GetDimension 返回 0.0，GetString 返回空字符串 | 异常 |

### US-4: V2 适配器暗色资源检测

**角色**: 框架开发者
**期望**: V2 适配器暗色资源检测由框架控制，应用开发者不感知
**价值**: 以便在深色模式切换时框架自动选择正确的资源

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN ResourceAdapterImplV2 初始化 THEN `appHasDarkRes_` 默认为 false；该标志由上游元能力直接写入底层 ResourceManager，ResourceAdapterImplV2 仅记录此值，其 `SetAppHasDarkRes` 接口不影响能否取到深色资源。置为 true 的条件（满足其一）：①应用 resource 目录配置了 dark 资源；②元能力调用 `setColorMode` 接口（`resource_adapter_impl_v2.h:91,113`） | 正常 |
| AC-4.2 | WHEN 调用 `ExistDarkResById(string resourceId)` THEN 返回该资源 ID 是否有暗色版本（`resource_adapter_impl_v2.h:94` 覆写） | 正常 |
| AC-4.3 | WHEN 调用 `ExistDarkResByName(string resourceName, string resourceType)` THEN 返回该资源名+类型是否有暗色版本（`resource_adapter_impl_v2.h:95` 覆写） | 正常 |
| AC-4.4 | WHEN 调用 `GetOverrideResourceAdapter(config, configurationChange)` THEN 返回 override 适配器实例，`isOverrideResourceAdapter_` 为 true（`resource_adapter_impl_v2.h:92-93,114`） | 正常 |

### US-5: ResourceObject InnerAPI 载体

**角色**: 框架开发者
**期望**: 我想要通过 ResourceObject 携带完整的资源上下文信息跨层传递
**价值**: 以便 ResourceManager 据此选择正确的适配器并支持暗色资源判断

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 构造 `ResourceObject(id, type, params, bundleName, moduleName, instanceId)` THEN 各字段可通过 getter 访问（`resource_object.h:40-43`） | 正常 |
| AC-5.2 | WHEN 调用 `ResourceObject::HasDarkResource()` THEN 返回 `hasDarkRes_` 字段值，默认为 false（`resource_object.h:129-132,145`） | 正常 |
| AC-5.3 | WHEN 调用 `ResourceObject::GetColorMode()` THEN 返回 `colorMode_` 字段值，默认为 `COLOR_MODE_UNDEFINED`（`resource_object.h:119-122,143`） | 正常 |
| AC-5.4 | WHEN 调用 `ResourceObject::SetInstanceId(int32_t)` THEN `instanceId_` 字段更新（`resource_object.h:64-67`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-RES-01 | UT | `resource_manager.cpp:54-77` |
| AC-1.2 | R-1 | TASK-RES-01 | UT | `resource_manager.cpp:150` |
| AC-1.3 | R-2 | TASK-RES-01 | UT | `resource_manager.cpp:79-86` |
| AC-1.4 | R-8 | TASK-RES-01 | UT | `resource_manager.cpp:56` |
| AC-2.1 | R-3 | TASK-RES-01 | UT | `resource_manager.cpp:88-101` |
| AC-2.2 | R-4 | TASK-RES-01 | UT | `resource_manager.cpp:262` |
| AC-2.3 | R-5 | TASK-RES-01 | UT | `resource_manager.cpp:261` |
| AC-2.4 | R-6 | TASK-RES-01 | UT | `resource_manager.cpp:82-83` |
| AC-3.1 | R-7 | TASK-RES-01 | UT | `resource_adapter.h:88`, `resource_adapter_impl.h:41` |
| AC-3.2 | R-7 | TASK-RES-01 | UT | `resource_adapter.h:95` |
| AC-3.3 | R-7 | TASK-RES-01 | UT | `resource_adapter.h:102` |
| AC-3.4 | R-7 | TASK-RES-01 | UT | `resource_adapter.h:160` |
| AC-3.5 | R-9 | TASK-RES-01 | UT | `resource_adapter.h` 默认返回值 |
| AC-4.1 | R-10 | TASK-RES-01 | UT | `resource_adapter_impl_v2.h:91,113` |
| AC-4.2 | R-10 | TASK-RES-01 | UT | `resource_adapter_impl_v2.h:94` |
| AC-4.3 | R-10 | TASK-RES-01 | UT | `resource_adapter_impl_v2.h:95` |
| AC-4.4 | R-11 | TASK-RES-01 | UT | `resource_adapter_impl_v2.h:92-93,114` |
| AC-5.1 | R-12 | TASK-RES-01 | UT | `resource_object.h:40-43` |
| AC-5.2 | R-13 | TASK-RES-01 | UT | `resource_object.h:129-132,145` |
| AC-5.3 | R-14 | TASK-RES-01 | UT | `resource_object.h:119-122,143` |
| AC-5.4 | R-15 | TASK-RES-01 | UT | `resource_object.h:64-67` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetOrCreateResourceAdapter 传入有效 ResourceObject | 按 instanceId+bundleName+moduleName 查找缓存，命中返回已有适配器，未命中创建新适配器并存入 LRU | LRU 默认容量 3 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 不同 instanceId 的 ResourceObject 调用 GetOrCreateResourceAdapter | 返回各自独立的 ResourceAdapter 实例 | instanceId 是缓存键的组成部分 | AC-1.3 |
| R-3 | 行为 | AddResourceAdapter 存入新适配器 | 通过 CountLimitLRU::CacheWithCountLimitLRU 存入 cacheList_ 和 cache_ | bundleName 和 moduleName 为空时直接存 resourceAdapters_ | AC-2.1 |
| R-4 | 边界 | cache_ 数量超过 capacity_ | 从 cacheList_ 尾部淘汰最久未使用的 ResourceAdapter | capacity_ 默认为 3，最小为 1 | AC-2.2 |
| R-5 | 行为 | 调用 SetResourceCacheSize(cacheSize) | capacity_ 更新为 cacheSize，超出时立即从尾部淘汰 | cacheSize >= 1 | AC-2.3 |
| R-6 | 边界 | bundleName 和 moduleName 均为空 | MakeCacheKey 返回 to_string(instanceId) | 空字符串判定 | AC-2.4 |
| R-7 | 行为 | 调用 ResourceAdapter GetColor/GetDimension/GetString/GetRawfile 等纯虚或虚函数 | 委托给 Global::Resource::ResourceManager 查询资源值，返回 Color/Dimension/string/string | 资源不存在时返回默认值（BLACK/0.0/空字符串） | AC-3.1 ~ AC-3.4 |
| R-8 | 异常 | GetOrCreateResourceAdapter 传入 nullptr ResourceObject | CHECK_NULL_RETURN 返回 nullptr | 无 | AC-1.4 |
| R-9 | 异常 | 资源 ID 不存在时调用 GetColor/GetDimension/GetString | GetColor 返回 Color::BLACK，GetDimension 返回 0.0，GetString 返回空字符串 | 无 | AC-3.5 |
| R-10 | 行为 | ResourceAdapterImplV2 初始化或调用 ExistDarkRes* | appHasDarkRes_ 默认 false，由上游元能力直接写入底层 ResourceManager，适配器仅记录此值（`SetAppHasDarkRes` 不影响深色资源可获取性；置 true 条件：应用 resource 目录含 dark 资源，或元能力调用 `setColorMode`）；ExistDarkResById/Name 查询底层资源管理器返回暗色资源是否存在 | 默认 false | AC-4.1 ~ AC-4.3 |
| R-11 | 行为 | 调用 GetOverrideResourceAdapter(config, configurationChange) | 返回新的 override ResourceAdapterImplV2 实例，isOverrideResourceAdapter_ = true | config 和 configurationChange 必须有效 | AC-4.4 |
| R-12 | 行为 | 构造 ResourceObject(id, type, params, bundleName, moduleName, instanceId) | 各字段可通过 getter 访问：GetId/GetType/GetInstanceId/GetParams/GetBundleName/GetModuleName | id 和 type 为 int32_t，instanceId 为 int32_t | AC-5.1 |
| R-13 | 行为 | 调用 ResourceObject::HasDarkResource() | 返回 hasDarkRes_ 字段值 | 默认 false | AC-5.2 |
| R-14 | 行为 | 调用 ResourceObject::GetColorMode() | 返回 colorMode_ 字段值 | 默认 COLOR_MODE_UNDEFINED | AC-5.3 |
| R-15 | 行为 | 调用 ResourceObject::SetInstanceId(int32_t) | instanceId_ 字段更新为新值 | 无 | AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | ResourceManager 单例 + GetOrCreateResourceAdapter 缓存命中/未命中/隔离/空值 |
| VM-2 | AC-2.1 ~ AC-2.4 | UT | CountLimitLRU 缓存存入/淘汰/容量调整/空键处理 |
| VM-3 | AC-3.1 ~ AC-3.5 | UT | ResourceAdapter V1 GetColor/GetDimension/GetString/GetRawfile + 异常默认值 |
| VM-4 | AC-4.1 ~ AC-4.4 | UT | ResourceAdapterImplV2 暗色资源检测 + override 适配器创建 |
| VM-5 | AC-5.1 ~ AC-5.4 | UT | ResourceObject 全字段 getter/setter |

## API 变更分析

> 本特性为已有实现补录，以下列出已有的公开和 InnerAPI 接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| ResourceManager::GetInstance() | InnerApi | 无 | ResourceManager& | 无 | 获取 ResourceManager 单例引用 | AC-1.1 |
| ResourceManager::GetOrCreateResourceAdapter(resourceObject) | InnerApi | RefPtr<ResourceObject> | RefPtr<ResourceAdapter> | 无 | 按 ResourceObject 获取或创建适配器 | AC-1.1 ~ AC-1.4 |
| ResourceManager::AddResourceAdapter(bundleName, moduleName, instanceId, adapter, replace) | InnerApi | string, string, int32_t, RefPtr&, bool | void | 无 | 注册新适配器到缓存 | AC-2.1 |
| ResourceManager::SetResourceCacheSize(cacheSize) | InnerApi | size_t | void | 无 | 调整 LRU 缓存容量 | AC-2.3 |
| ResourceAdapter::Create() | InnerApi | 无 | RefPtr<ResourceAdapter> | 无 | V1 适配器工厂 | AC-3.1 |
| ResourceAdapter::CreateV2() | InnerApi | 无 | RefPtr<ResourceAdapter> | 无 | V2 适配器工厂 | AC-4.1 |
| ResourceAdapter::CreateNewResourceAdapter(bundleName, moduleName, actualInstanceId) | InnerApi | string, string, int32_t& | RefPtr<ResourceAdapter> | 无 | 带实例 ID 的 V2 适配器工厂 | AC-1.1 |
| ResourceAdapter::GetColor(resId) | InnerApi | uint32_t | Color | 无 | 按资源 ID 获取颜色 | AC-3.1 |
| ResourceAdapter::GetDimension(resId) | InnerApi | uint32_t | Dimension | 无 | 按资源 ID 获取尺寸 | AC-3.2 |
| ResourceAdapter::GetString(resId) | InnerApi | uint32_t | string | 无 | 按资源 ID 获取字符串 | AC-3.3 |
| ResourceAdapter::GetRawfile(fileName) | InnerApi | string | string | 无 | 获取 rawfile 路径 | AC-3.4 |
| ResourceAdapterImplV2::ExistDarkResById(resourceId) | InnerApi | string | bool | 无 | 检测暗色资源是否存在 | AC-4.2 |
| ResourceAdapterImplV2::ExistDarkResByName(resourceName, resourceType) | InnerApi | string, string | bool | 无 | 按名称检测暗色资源 | AC-4.3 |
| ResourceAdapterImplV2::GetOverrideResourceAdapter(config, change) | InnerApi | ResourceConfiguration&, ConfigurationChange& | RefPtr<ResourceAdapter> | 无 | 创建 override 适配器 | AC-4.4 |
| ResourceAdapterImplV2::SetAppHasDarkRes(hasDarkRes) | InnerApi | bool | void | 无 | 记录上游元能力写入的暗色资源标志（不影响深色资源可获取性） | AC-4.1 |
| ResourceObject(id, type, params, bundleName, moduleName, instanceId) | InnerApi | int32_t, int32_t, vector<Params>&, string, string, int32_t | ResourceObject | 无 | 构造资源对象 | AC-5.1 |
| ResourceObject::HasDarkResource() | InnerApi | 无 | bool | 无 | 查询是否有暗色资源 | AC-5.2 |
| ResourceObject::GetColorMode() | InnerApi | 无 | ColorMode& | 无 | 查询色彩模式 | AC-5.3 |
| ResourceObject::SetInstanceId(instanceId) | InnerApi | int32_t | void | 无 | 设置实例 ID | AC-5.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| ResourceAdapter::Create() | MODIFIED | V1 工厂仍可用，但新增代码应优先使用 CreateV2() | 新增代码使用 CreateV2() 替代 Create() | AC-3.1, AC-4.1 |
| ResourceAdapter::GetColor(resId) | MODIFIED | V2 新增 ExistDarkResById 配套暗色资源检测 | V1 调用方无需变更 | AC-3.1, AC-4.2 |

## 接口规格

### 接口定义

**ResourceManager::GetOrCreateResourceAdapter**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<ResourceAdapter> ResourceManager::GetOrCreateResourceAdapter(const RefPtr<ResourceObject>& resourceObject)` |
| 返回值 | `RefPtr<ResourceAdapter>` — 绑定到 instanceId 的资源适配器，nullptr 表示参数无效 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| resourceObject | `RefPtr<ResourceObject>` | 是 | 无 | nullptr 时返回 nullptr；instanceId >= 0 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 ResourceObject，缓存命中 | 返回缓存的 ResourceAdapter | AC-1.1, AC-1.2 |
| 2 | 有效 ResourceObject，缓存未命中 | 创建新 ResourceAdapter 并存入 LRU | AC-1.1 |
| 3 | 不同 instanceId | 返回各自独立的 ResourceAdapter | AC-1.3 |
| 4 | nullptr ResourceObject | 返回 nullptr | AC-1.4 |
| 5 | CreateNewResourceAdapter 失败 | 返回默认 bundle 的 ResourceAdapter | AC-1.1 |

---

**ResourceAdapter::GetColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `virtual Color ResourceAdapter::GetColor(uint32_t resId) = 0` |
| 返回值 | `Color` — 资源 ID 对应的颜色值，不存在时返回 Color::BLACK |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| resId | `uint32_t` | 是 | 无 | 有效的资源 ID |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效资源 ID | 返回对应颜色值 | AC-3.1 |
| 2 | 资源 ID 不存在 | 返回 Color::BLACK | AC-3.5 |

---

**ResourceAdapterImplV2::ExistDarkResById**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool ResourceAdapterImplV2::ExistDarkResById(const std::string& resourceId)` |
| 返回值 | `bool` — true 表示有暗色资源，false 表示无 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| resourceId | `string` | 是 | 无 | 非空字符串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 资源 ID 对应暗色版本存在 | 返回 true | AC-4.2 |
| 2 | 资源 ID 对应暗色版本不存在 | 返回 false | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 是，ResourceAdapter::Create() 仍可用但新增代码应优先使用 CreateV2()
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 6
- **API 版本号策略:** @since 6（ResourceManager / ResourceAdapter 基础接口）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Per-instanceId 隔离 | ResourceManager 以 instanceId 为键隔离 ResourceAdapter，不同 ArkUI 实例的资源访问互不干扰 | AC-1.1, AC-1.3 |
| LRU 缓存容量限制 | 默认容量 3，多 HAP 场景下可能淘汰不活跃适配器 | AC-2.2, AC-2.3 |
| V1/V2 共存 | V1 适配器不支持暗色检测和 override，V2 适配器支持；调用方按需选择工厂方法 | AC-3.1, AC-4.1 |
| 线程安全 | ResourceManager 通过 shared_mutex 保护 resourceAdapters_ 和 cache_；ResourceAdapterImpl 通过 shared_mutex 保护 resourceManager_ | AC-1.1, AC-2.1 |
| ResourceObject 不可变性 | ResourceObject 的 id/type/params/bundleName/moduleName 在构造时确定，instanceId/colorMode/hasDarkRes 可后续设置 | AC-5.1, AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | GetOrCreateResourceAdapter 缓存命中耗时 < 1ms | UT 计时 | `resource_manager.cpp:150` LRU 查找 |
| 内存 | LRU 缓存默认容量 3，单实例 ResourceAdapter 约占用 < 1MB | 内存分析 | `resource_manager.h:96` capacity_ = 3 |
| 可靠性 | resourceObject 为 nullptr 时返回 nullptr 而非崩溃 | UT | `resource_manager.cpp:56` CHECK_NULL_RETURN |
| 可测试性 | ResourceManager 单例可通过 Reset 清空状态 | UT | `resource_manager.h:75` Reset() |
| 自动化维测 | DumpResLoadError 输出最近 100 条资源加载错误 | hilog | `resource_manager.h:83` DumpResLoadError() |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | N/A | N/A | N/A |
| 平板 | 无差异 | N/A | N/A | N/A |
| 折叠屏 | 无差异 | N/A | N/A | N/A |

> 资源访问为底层框架能力，设备行为一致。设备差异由 HAP 包资源文件自身的 limits 配置决定，不在本规格范围。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 资源访问不直接涉及无障碍 | 无 |
| 大字体 | 否 | 字体大小由 GetDimension 返回，不改变访问机制 | 无 |
| 深色模式 | 是 | V2 适配器支持暗色资源检测和 UpdateColorMode 切换 | AC-4.1 ~ AC-4.4 |
| 多窗口/分屏 | 是 | 不同窗口可能对应不同 instanceId，通过 per-instanceId 隔离 | AC-1.1, AC-1.3 |
| 多用户 | 否 | 多用户资源隔离由 HAP 包管理层处理 | 无 |
| 版本升级兼容 | 是 | V1/V2 共存，Create/CreateV2 工厂方法保持兼容 | AC-3.1, AC-4.1 |
| 生态兼容 | 否 | N/A | 无 |

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
    query: "ResourceManager GetOrCreateResourceAdapter LRU cache and per-instanceId isolation"
  - repo: "openharmony/arkui_ace_engine"
    query: "ResourceAdapterImplV2 ExistDarkResById and GetOverrideResourceAdapter implementation"
  - repo: "openharmony/arkui_ace_engine"
    query: "ResourceObject InnerAPI fields: id, type, instanceId, params, bundleName, colorMode, hasDarkRes"
```

**关键文档:** design.md (`specs/03-engine-framework/03-resource-theme/01-resource-access/design.md`)
