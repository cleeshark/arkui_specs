# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 资源动态切换全量规格（ConfigurationChange/颜色模式/FlushReload/通知） |
| 特性编号 | Func-03-03-04-Feat-01 |
| FuncID | 03-03-04 |
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
| ADDED | ConfigurationChange 位域结构 | API 7，10 个 bool 标志 + IsNeedUpdate |
| ADDED | AceContainer::UpdateConfiguration 主入口 | API 7，配置变更统一处理 |
| ADDED | BuildResConfig 逐字段分发 | API 7，colorMode/language/direction/dpi 分发 |
| ADDED | PipelineContext::FlushReload | API 7，全量重建 + ReloadStage |
| ADDED | PipelineContext::NotifyColorModeChange | API 7，颜色模式树遍历通知 |
| ADDED | FrameNode::NotifyColorModeChange 树遍历 | API 7，递归调用 Pattern::OnColorModeChange |
| ADDED | Pattern::OnColorModeChange 虚函数 | API 7，默认 ReloadResources |
| ADDED | ProcessThemeUpdate 解析 themeTag JSON | API 7+，fontUpdate/iconUpdate/skinUpdate |
| MODIFIED | FlushReload 增加 400ms FRICTION 动画包裹 | API 12+，视觉过渡动画 |
| ADDED | OnlyColorModeChange 快速路径 | API 12+，ConfigChangePerform 启用 |
| ADDED | ConfigurationChange::MergeConfig 累积 | API 12+，位域 |= 累积 |
| ADDED | CheckForceVsync 后台 vsync 强制 | API 12+，白名单应用 |
| ADDED | SetFontScaleAndWeightScale | API 12+，字体缩放和字重缩放 |
| ADDED | SetColorModeUpdateCallback | API 12+，FrameNode 级颜色模式回调 |
| ADDED | HandleColorModeConfigurationUpdate | API 12+，colorModeUpdateCallback_ + FireColorNDKCallback |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/03-resource-theme/04-resource-dynamic-switching/design.md`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 配置变更位域分发

**角色**: 框架开发者
**期望**: 我想要通过位域标记区分不同类型的配置变更
**价值**: 以便针对不同变更类型执行差异化的更新策略

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `ConfigurationChange` 所有标志为 false THEN `IsNeedUpdate()` 返回 false（`resource_configuration.h:32-36`） | 边界 |
| AC-1.2 | WHEN 仅 `colorModeUpdate` 为 true THEN `OnlyColorModeChange()` 返回 true，其他标志任一为 true 时返回 false（`resource_configuration.h:38-42`） | 正常 |
| AC-1.3 | WHEN 调用 `MergeConfig(other)` THEN 所有标志使用 `\|=` 累积，`iconUpdate` 也被累积（`resource_configuration.h:44-55`） | 正常 |

### US-2: 颜色模式快速路径

**角色**: 终端用户
**期望**: 我想要在仅切换深浅色模式时获得快速响应
**价值**: 以便避免全量重建的开销，颜色切换更流畅

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `ConfigChangePerform()` 为 true 且 `OnlyColorModeChange()` 为 true THEN 走快速路径：`ReloadThemeCache()` → `OnFrontUpdated()` → `UpdateColorMode()`，跳过完整 FlushReload（`ace_container.cpp:3789-3793`） | 正常 |
| AC-2.2 | WHEN `OnlyColorModeChange()` 为 false THEN 走完整路径：`NotifyConfigurationChange()` → `NotifyConfigToSubContainers()` → `ClearImageCache()`（`ace_container.cpp:3795-3809`） | 正常 |
| AC-2.3 | WHEN `ConfigChangePerform()` 为 false 且 `OnlyColorModeChange()` 为 true THEN `TokenThemeStorage::CacheClear()` 被调用，不走快速路径（`ace_container.cpp:3673-3676`） | 边界 |

### US-3: FlushReload 全量重建

**角色**: 终端用户
**期望**: 我想要在语言/方向/DPI 等配置变更后看到 UI 完整更新
**价值**: 以便所有依赖配置的资源都正确刷新

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 应用在前台（onShow_=true）THEN `FlushReload` 使用 400ms FRICTION 动画曲线包裹 changeTask（`pipeline_context.cpp:5920-5923`） | 正常 |
| AC-3.2 | WHEN 应用在后台（!onShow_）THEN `FlushReload` 同步执行 changeTask，无动画包裹（`pipeline_context.cpp:5917-5918`） | 边界 |
| AC-3.3 | WHEN `FlushReload` 的 changeTask 执行 THEN `rootNode->UpdateConfigurationUpdate(configurationChange)` 被调用（`pipeline_context.cpp:5902-5903`） | 正常 |
| AC-3.4 | WHEN `fullUpdate` 为 true 且 `IsNeedUpdate()` 为 true THEN `stageManager->ReloadStage()` + `FlushUITasks()` 被执行（`pipeline_context.cpp:5909-5915`） | 正常 |

### US-4: 颜色模式变更树遍历

**角色**: 组件开发者
**期望**: 我想要在颜色模式变更时收到通知并更新组件颜色
**价值**: 以便组件能正确响应深浅色切换

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `NotifyColorModeChange(colorMode)` 执行 THEN 使用 400ms FRICTION 动画包裹 `rootNode->NotifyColorModeChange(colorMode)` 树遍历（`pipeline_context.cpp:7621-7650`） | 正常 |
| AC-4.2 | WHEN `FrameNode::NotifyColorModeChange` 执行 THEN 调用 `pattern_->OnColorModeChange(colorMode)` 和 `pattern_->OnColorConfigurationUpdate()`（`frame_node.cpp:1978-1981`） | 正常 |
| AC-4.3 | WHEN `FrameNode` 有 `colorModeUpdateCallback_` THEN 在 `HandleColorModeConfigurationUpdate` 中被调用（`frame_node.cpp:2053-2056`） | 正常 |
| AC-4.4 | WHEN `UINode::NotifyColorModeChange` 递归 THEN 子节点继承 `shouldClearCache`/`rerenderable`/`measureAnyway`/`forceDarkAllowed` 标志（`ui_node.cpp:2241-2244`） | 正常 |
| AC-4.5 | WHEN `Pattern::OnColorModeChange` 默认实现执行 THEN `resourceMgr_->ReloadResources()` 被调用（`pattern.cpp:62-67`） | 正常 |

### US-5: 后台 vsync 强制

**角色**: 框架开发者
**期望**: 我想要在后台时也能及时更新颜色模式
**价值**: 以便切回前台时不会看到旧颜色的闪烁

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 应用在后台（!GetOnShow()）且 `parsedConfig.colorMode` 非空且 `GetWhiteListStatus()` 为 true THEN `window->SetForceVsyncRequests(true)` 被调用（`ace_container.cpp:3719-3728`） | 正常 |
| AC-5.2 | WHEN 应用不在白名单 THEN 不强制 vsync，延迟到前台处理 | 边界 |

### US-6: 图片缓存清理

**角色**: 终端用户
**期望**: 我想要在颜色模式切换后看到正确的图片资源
**价值**: 以便深浅色模式使用不同的图片资源时不显示旧缓存

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `UpdateColorMode` 执行且 `ConfigChangePerform()` 为 true THEN `pipelineContext_->ClearImageCache()` 和 `ImageDecoder::ClearPixelMapCache()` 被调用（`ace_container.cpp:3693-3696`） | 正常 |
| AC-6.2 | WHEN 完整路径（非快速路径）THEN `pipelineContext_->ClearImageCache()` 和 `ImageDecoder::ClearPixelMapCache()` 在 `NotifyConfigToSubContainers` 后被调用（`ace_container.cpp:3805-3806`） | 正常 |

### US-7: 子容器配置传递

**角色**: 框架开发者
**期望**: 我想要子容器也收到配置变更通知
**价值**: 以便 UIExtension 和动态组件也响应配置变更

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `NotifyConfigToSubContainers` 被调用 THEN 遍历 `configurationChangedCallbacks_` map，每个回调被调用（`ace_container.cpp:3824-3831`） | 正常 |
| AC-7.2 | WHEN `UpdateSubContainerDensity` 被调用且 `instanceId_ >= MIN_SUBCONTAINER_ID` THEN 从父容器 PipelineContext 获取 density 设置到 resConfig（`ace_container.cpp:3742-3751`） | 正常 |

### US-8: 主题标签解析

**角色**: 应用开发者
**期望**: 我想要通过 themeTag 触发字体/图标/皮肤更新
**价值**: 以便主题变更时相关资源同步更新

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN `parsedConfig.themeTag` 非空 THEN 解析 JSON 获取 `fonts` 字段，设置 `configurationChange.fontUpdate`（`ace_container.cpp:3610-3613`） | 正常 |
| AC-8.2 | WHEN `parsedConfig.themeTag` 非空 THEN 解析 JSON 获取 `icons` 字段，设置 `configurationChange.iconUpdate`（`ace_container.cpp:3614-3615`） | 正常 |
| AC-8.3 | WHEN `parsedConfig.themeTag` 非空 THEN 解析 JSON 获取 `skin` 字段，设置 `configurationChange.skinUpdate`（`ace_container.cpp:3616-3622`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.3 | R-1, R-2, R-3 | TASK-RES-SWITCH-01 | UT | `test/unittest/core/resource/` |
| AC-2.1 ~ AC-2.3 | R-4, R-5, R-6 | TASK-RES-SWITCH-01 | UT | ace_container 单测 |
| AC-3.1 ~ AC-3.4 | R-7, R-8, R-9 | TASK-RES-SWITCH-01 | UT | pipeline_context 单测 |
| AC-4.1 ~ AC-4.5 | R-10, R-11, R-12 | TASK-RES-SWITCH-01 | UT | frame_node/ui_node/pattern 单测 |
| AC-5.1 ~ AC-5.2 | R-13 | TASK-RES-SWITCH-01 | UT | CheckForceVsync 单测 |
| AC-6.1 ~ AC-6.2 | R-14 | TASK-RES-SWITCH-01 | UT | ClearImageCache 单测 |
| AC-7.1 ~ AC-7.2 | R-15, R-16 | TASK-RES-SWITCH-01 | UT | 子容器配置传递测试 |
| AC-8.1 ~ AC-8.3 | R-17 | TASK-RES-SWITCH-01 | UT | ProcessThemeUpdate 单测 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ConfigurationChange 所有标志为 false | IsNeedUpdate() 返回 false | — | AC-1.1 |
| R-2 | 行为 | 仅 colorModeUpdate 为 true | OnlyColorModeChange() 返回 true | 其他标志任一为 true 时返回 false | AC-1.2 |
| R-3 | 行为 | 调用 MergeConfig(other) | 所有标志使用 |= 累积 | iconUpdate 也被累积 | AC-1.3 |
| R-4 | 行为 | ConfigChangePerform() && OnlyColorModeChange() | 走快速路径，跳过 FlushReload | — | AC-2.1 |
| R-5 | 行为 | !OnlyColorModeChange() | 走完整路径：NotifyConfigurationChange + ClearImageCache | — | AC-2.2 |
| R-6 | 边界 | !ConfigChangePerform() && OnlyColorModeChange() | TokenThemeStorage::CacheClear() 被调用，不走快速路径 | — | AC-2.3 |
| R-7 | 行为 | FlushReload 前台执行（onShow_=true）| 400ms FRICTION 动画包裹 changeTask | — | AC-3.1 |
| R-8 | 边界 | FlushReload 后台执行（!onShow_）| 同步执行 changeTask，无动画 | — | AC-3.2 |
| R-9 | 行为 | FlushReload changeTask 执行 | rootNode->UpdateConfigurationUpdate + stageManager->ReloadStage | fullUpdate && IsNeedUpdate | AC-3.3, AC-3.4 |
| R-10 | 行为 | NotifyColorModeChange(colorMode) | 400ms FRICTION 动画 + rootNode->NotifyColorModeChange | — | AC-4.1 |
| R-11 | 行为 | FrameNode::NotifyColorModeChange | pattern_->OnColorModeChange + OnColorConfigurationUpdate | — | AC-4.2 |
| R-12 | 行为 | colorModeUpdateCallback_ 存在 | HandleColorModeConfigurationUpdate 中被调用 | — | AC-4.3, AC-4.4 |
| R-13 | 行为 | 后台 && colorMode 非空 && 白名单 | window->SetForceVsyncRequests(true) | 非白名单不强制 | AC-5.1, AC-5.2 |
| R-14 | 行为 | UpdateColorMode 或完整路径 | ClearImageCache + ClearPixelMapCache | — | AC-6.1, AC-6.2 |
| R-15 | 行为 | NotifyConfigToSubContainers | 遍历 configurationChangedCallbacks_ | — | AC-7.1 |
| R-16 | 行为 | instanceId >= MIN_SUBCONTAINER_ID | 从父容器获取 density 设置到 resConfig | — | AC-7.2 |
| R-17 | 行为 | parsedConfig.themeTag 非空 | 解析 JSON 设置 fontUpdate/iconUpdate/skinUpdate | skin 回退检查 lastThemeHasSkin_ | AC-8.1 ~ AC-8.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.3 | UT | ConfigurationChange 位域逻辑 |
| VM-2 | AC-2.1 ~ AC-2.3 | UT | 颜色模式快速路径 vs 完整路径 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | FlushReload 动画和重建 |
| VM-4 | AC-4.1 ~ AC-4.5 | UT | 颜色模式树遍历通知 |
| VM-5 | AC-5.1 ~ AC-5.2 | UT | 后台 vsync 强制 |
| VM-6 | AC-6.1 ~ AC-6.2 | UT | 图片缓存清理 |
| VM-7 | AC-7.1 ~ AC-7.2 | UT | 子容器配置传递 |
| VM-8 | AC-8.1 ~ AC-8.3 | UT | themeTag JSON 解析 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| ConfigurationChange::IsNeedUpdate | InnerApi | 无 | bool | N/A | 判断是否有配置变更 | AC-1.1 |
| ConfigurationChange::OnlyColorModeChange | InnerApi | 无 | bool | N/A | 判断是否仅颜色模式变更 | AC-1.2 |
| ConfigurationChange::MergeConfig | InnerApi | const ConfigurationChange& | void | N/A | 累积配置变更标志 | AC-1.3 |
| AceContainer::UpdateConfiguration | InnerApi | ParsedConfig&, string&, bool | void | N/A | 配置变更主入口 | AC-2.1 ~ AC-2.2 |
| AceContainer::FlushReloadTask | InnerApi | bool, ConfigurationChange& | void | N/A | 重建任务 | AC-3.1 ~ AC-3.4 |
| PipelineContext::FlushReload | InnerApi | ConfigurationChange&, bool | void | N/A | Pipeline 全量重建 | AC-3.1 ~ AC-3.4 |
| PipelineContext::NotifyColorModeChange | InnerApi | uint32_t | void | N/A | 颜色模式变更通知 | AC-4.1 |
| FrameNode::SetColorModeUpdateCallback | InnerApi | function<void()>&& | void | N/A | 设置颜色模式回调 | AC-4.3 |
| Pattern::OnColorModeChange | InnerApi | uint32_t | void | N/A | Pattern 颜色模式处理 | AC-4.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| PipelineContext::FlushReload | MODIFIED | API 12+ 增加 400ms FRICTION 动画包裹 | 无需迁移，行为增强 | AC-3.1 |
| AceContainer::UpdateConfiguration | MODIFIED | API 12+ 增加 OnlyColorModeChange 快速路径 | 无需迁移，行为增强 | AC-2.1 |
| FrameNode::NotifyColorModeChange | MODIFIED | API 12+ 增加 colorModeUpdateCallback_ 和 ForceDark 逻辑 | 无需迁移，行为增强 | AC-4.3 |

## 接口规格

### 接口定义

**ConfigurationChange::OnlyColorModeChange**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool ConfigurationChange::OnlyColorModeChange() const` |
| 返回值 | `bool` — true 表示仅颜色模式变更 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | colorModeUpdate=true，其他全 false | 返回 true | AC-1.2 |
| 2 | colorModeUpdate=true，languageUpdate=true | 返回 false | AC-1.2 |
| 3 | colorModeUpdate=false | 返回 false | AC-1.2 |

**AceContainer::UpdateConfiguration**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void AceContainer::UpdateConfiguration(const ParsedConfig& parsedConfig, const std::string& configuration, bool abilityLevel)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| parsedConfig | const ParsedConfig& | 是 | 无 | IsValid() 为 false 时直接返回 |
| configuration | const std::string& | 是 | 无 | 配置名称 |
| abilityLevel | bool | 否 | false | true 时跳过 themeManager->UpdateConfig |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | parsedConfig.IsValid() 为 false | 直接返回，LOGW 警告 | AC-2.2 |
| 2 | OnlyColorModeChange() 为 true | 走快速路径 | AC-2.1 |
| 3 | OnlyColorModeChange() 为 false | 走完整路径 | AC-2.2 |

**PipelineContext::NotifyColorModeChange**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void PipelineContext::NotifyColorModeChange(uint32_t colorMode)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| colorMode | uint32_t | 是 | 无 | 0=LIGHT, 1=DARK |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 400ms FRICTION 动画包裹 rootNode->NotifyColorModeChange | AC-4.1 |
| 2 | 动画完成 | OnFlushReloadFinish 回调执行 | AC-4.1 |

**Pattern::OnColorModeChange**

| 属性 | 值 |
|------|-----|
| 函数签名 | `virtual void Pattern::OnColorModeChange(uint32_t colorMode)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| colorMode | uint32_t | 是 | 无 | 颜色模式值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 默认实现 | resourceMgr_->ReloadResources() 调用 | AC-4.5 |
| 2 | 子类重写 | 各 Pattern 自行处理颜色模式变更 | AC-4.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - `FlushReload` API 12+ 增加 400ms FRICTION 动画包裹（AC-3.1）
  - `UpdateConfiguration` API 12+ 增加 OnlyColorModeChange 快速路径（AC-2.1）
  - `FrameNode::NotifyColorModeChange` API 12+ 增加 colorModeUpdateCallback_ 和 ForceDark 逻辑（AC-4.3）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 基础 ConfigurationChange/FlushReload/NotifyColorModeChange @since 7，OnlyColorModeChange/MergeConfig/SetColorModeUpdateCallback @since 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 位域分发 | ConfigurationChange 10 个 bool 标志，BuildResConfig 逐字段判断 | AC-1.1 ~ AC-1.3 |
| 快速路径条件 | ConfigChangePerform() && OnlyColorModeChange() 同时满足 | AC-2.1 |
| 400ms FRICTION 动画 | FlushReload 和 NotifyColorModeChange 均使用此曲线 | AC-3.1, AC-4.1 |
| 树遍历传播 | UINode 递归传播 shouldClearCache/rerenderable/measureAnyway/forceDarkAllowed | AC-4.4 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 颜色模式快速路径 < 100ms，完整路径 < 500ms | UT + 性能测试 | UpdateConfiguration 端到端耗时 |
| 功耗 | 后台 vsync 仅白名单应用 | 配置检查 | CheckForceVsync 白名单验证 |
| 内存 | 图片缓存清理后峰值内存下降 | 内存分析 | ClearImageCache 前后对比 |
| 可靠性 | 配置变更后 UI 一致，无残留旧颜色 | 集成测试 | 端到端颜色切换验证 |
| 可测试性 | ConfigurationChange 位域可独立测试 | UT | MergeConfig/IsNeedUpdate 单测 |
| 定界定位 | LOGI/LOGW 日志覆盖 UpdateConfiguration/FlushReload 关键节点 | hilog | 配置变更相关日志 |
| 自动化维测 | CheckForceVsync 白名单状态可查询 | hilog | GetWhiteListStatus 日志 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 配置变更不直接影响无障碍 | — |
| 大字体 | 是 | fontScale/fontWeightScale 变更通过 SetFontScaleAndWeightScale 处理 | AC-8.1 |
| 深色模式 | 是 | 颜色模式变更是核心场景，快速路径 + 树遍历通知 | AC-2.1, AC-4.1 ~ AC-4.5 |
| 多窗口/分屏 | 是 | 子容器通过 NotifyConfigToSubContainers 传递配置变更 | AC-7.1, AC-7.2 |
| 多用户 | 否 | 配置变更为系统级 | — |
| 版本升级 | 是 | API 7 基础框架 → API 12+ 快速路径和动画 | 兼容性声明 |
| 生态兼容 | 否 | 不涉及 | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 资源动态切换
  作为 终端用户
  我想要 在系统配置变更后 UI 自动更新
  以便 无需重启应用即可看到最新配置效果

  Scenario: 仅颜色模式变更走快速路径
    Given ConfigChangePerform 为 true
    And OnlyColorModeChange 为 true
    When UpdateConfiguration 被调用
    Then ReloadThemeCache 被调用
    And UpdateColorMode 被调用
    And 完整 FlushReload 被跳过

  Scenario: 多维度变更走完整路径
    Given colorModeUpdate 和 languageUpdate 均为 true
    When UpdateConfiguration 被调用
    Then NotifyConfigurationChange 被调用
    And FlushReload 被调用
    And ClearImageCache 被调用

  Scenario: 后台白名单应用强制 vsync
    Given 应用在后台
    And colorMode 配置非空
    And GetWhiteListStatus 为 true
    When CheckForceVsync 被调用
    Then window SetForceVsyncRequests true 被调用

  Scenario: 颜色模式变更树遍历
    Given NotifyColorModeChange 被调用
    Then rootNode NotifyColorModeChange 递归遍历
    And 每个 FrameNode 调用 Pattern OnColorModeChange
    And resourceMgr ReloadResources 被调用
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
    query: "ConfigurationChange 位域 OnlyColorModeChange 和 MergeConfig 的累积逻辑"
  - repo: "arkui/ace_engine"
    query: "AceContainer UpdateConfiguration 中快速路径和完整路径的分支条件"
  - repo: "arkui/ace_engine"
    query: "PipelineContext FlushReload 中 400ms FRICTION 动画包裹的 changeTask 内容"
  - repo: "arkui/ace_engine"
    query: "FrameNode NotifyColorModeChange 树遍历中 Pattern OnColorModeChange 的调用时序"
  - repo: "arkui/ace_engine"
    query: "CheckForceVsync 白名单应用后台 vsync 强制请求逻辑"
```

**关键文档:** `interfaces/inner_api/ace_kit/include/ui/resource/resource_configuration.h`, `adapter/ohos/entrance/ace_container.h/.cpp`, `frameworks/core/pipeline_ng/pipeline_context.h/.cpp`, `frameworks/core/components_ng/base/frame_node.h/.cpp`, `frameworks/core/components_ng/pattern/pattern.h/.cpp`
