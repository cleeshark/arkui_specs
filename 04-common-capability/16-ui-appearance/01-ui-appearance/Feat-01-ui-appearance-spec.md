# 特性规格

> Func-04-16-01-Feat-01 UI 外观（色彩模式）：固化深色/浅色模式检测、系统配置更新传播、Pipeline NotifyColorModeChange、FrameNode 递归传播、Force Dark、WithTheme 本地色模式覆盖、暗色亮度调整与 C-API 事件注册的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UI 外观（色彩模式）(UIAppearance - Color Mode) |
| 特性编号 | Func-04-16-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持 Configuration.colorMode，API 10 ThemeColorMode，API 12 C-API，API 20 Force Dark，API 26 AnchoredColorMode |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/16-ui-appearance/01-ui-appearance/design.md` | Baselined |
| SDK API | `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | — |
| SDK 组件 | `docs/sdk/Component_API_Knowledge_Base_CN.md` | — |

---

## 用户故事

### US-1: 色彩模式检测

**作为** 应用开发者,
**我想要** 通过 Configuration 接口读取系统当前色彩模式,
**以便** 应用能感知深色/浅色模式状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 读取 `common.d.ts:2357-2396` Configuration.colorMode THEN 返回 ConfigurationConstant.ColorMode（DARK/LIGHT/NOT_SET） | 正常 |
| AC-1.2 | WHEN C++ ColorMode 枚举定义于 `ace_type.h:43-47` THEN 包含 LIGHT=0/DARK/COLOR_MODE_UNDEFINED | 边界 |
| AC-1.3 | WHEN ThemeColorMode 枚举定义于 `common.d.ts:8020-8052` THEN 包含 SYSTEM=0/LIGHT=1/DARK=2，@since 10 | 边界 |

### US-2: 系统配置更新传播

**作为** 应用开发者,
**我想要** 系统色彩模式变更自动传播到 ArkUI 组件树,
**以便** 组件无需手动监听即可响应色模式切换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Ability OnConfigurationUpdated 接收系统配置 THEN `ace_ability.cpp:617-641` 触发 Container UpdateConfiguration | 正常 |
| AC-2.2 | WHEN BuildParsedConfig 读取 SYSTEM_COLORMODE THEN `ui_content_impl.cpp:3505-3533` 将 colorMode 存入 ParsedConfig | 正常 |
| AC-2.3 | WHEN ProcessColorModeUpdate 执行 THEN `ace_container.cpp:3653-3670` 调用 SetColorMode + SetColorScheme + NotifyColorModeChange | 正常 |

### US-3: Pipeline NotifyColorModeChange

**作为** 应用开发者,
**我想要** Pipeline 统一调度色彩模式变更通知,
**以便** 整个组件树以动画方式平滑切换色模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN NotifyColorModeChange 执行 THEN `pipeline_context.cpp:7678-7714` 使用 400ms FRICTION 曲线动画过渡 | 正常 |
| AC-3.2 | WHEN 动画闭包执行 THEN SetNeedReload(true) + SetIsReloading(true) + rootNode->SetDarkMode + rootNode->NotifyColorModeChange + FlushUITasks | 正常 |
| AC-3.3 | WHEN FrameNode NotifyColorModeChange 执行 THEN `frame_node.cpp:1949-1991` 检查 GetLocalColorMode 后递归子节点，调用 pattern_->OnColorConfigurationUpdate | 正常 |

### US-4: Force Dark

**作为** 应用开发者,
**我想要** 通过 C-API 设置强制深色配置,
**以便** 控制组件是否允许强制深色模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN UINode 定义 Force Dark 标记 THEN `ui_node.h:1039-1086` forceDarkAllowed_ 默认 true，forceDarkAllowedbyUser_ 默认 false | 边界 |
| AC-4.2 | WHEN 调用 OH_ArkUI_SetForceDarkConfig THEN `native_node.h:14314` 设置 forceDarkAllowedbyUser_，@since 20 | 正常 |
| AC-4.3 | WHEN ForceDarkConfig 无效 THEN 返回 ARKUI_ERROR_CODE_FORCE_DARK_CONFIG_INVALID | 异常 |

### US-5: WithTheme 本地色模式覆盖

**作为** 应用开发者,
**我想要** 通过 WithTheme 在子树级别覆盖全局色模式,
**以便** 局部区域使用与系统不同的色模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN Pipeline 维护 localColorMode_ THEN `pipeline_context.h:924-930` SetLocalColorMode/GetLocalColorMode，默认 COLOR_MODE_UNDEFINED | 边界 |
| AC-5.2 | WHEN resource_adapter_impl_v2 检查色模式 THEN `resource_adapter_impl_v2.cpp:133-176` 优先检查 localColorMode_，UNDEFINED 时回退全局 colorMode_ | 正常 |

### US-6: 暗色亮度调整

**作为** 应用开发者,
**我想要** 暗色模式下自动调整亮度,
**以便** 降低屏幕亮度保护用户视力。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN colorMode == DARK THEN `pipeline_context.cpp:7163-7184` ChangeDarkModeBrightness 叠加黑色背景 #FF000000 | 正常 |
| AC-6.2 | WHEN 亮度百分比读取 THEN SystemProperties::GetDarkModeBrightnessPercent 默认 "0.10,0.05" | 边界 |

### US-7: C-API 色彩模式事件注册

**作为** NDK 开发者,
**我想要** 通过 C-API 注册系统色彩模式变更事件,
**以便** 在 C 代码中感知色模式切换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 OH_ArkUI_RegisterSystemColorModeChangeEvent THEN `native_node.h:13984` 注册回调，@since 12 | 正常 |
| AC-7.2 | WHEN 调用 OH_ArkUI_UnregisterSystemColorModeChangeEvent THEN `native_node.h:13993` 注销回调 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 common.d.ts:2357-2396 |
| AC-1.2 | US-1 | R-2 | 代码审查 ace_type.h:43-47 |
| AC-1.3 | US-1 | R-3 | 代码审查 common.d.ts:8020-8052 |
| AC-2.1 | US-2 | R-4 | 代码审查 ace_ability.cpp:617-641 |
| AC-2.2 | US-2 | R-5 | 代码审查 ui_content_impl.cpp:3505-3533 |
| AC-2.3 | US-2 | R-6 | 代码审查 ace_container.cpp:3653-3670 |
| AC-3.1 | US-3 | R-7 | 单元测试 withtheme_test_ng.cpp |
| AC-3.2 | US-3 | R-8 | 代码审查 pipeline_context.cpp:7678-7714 |
| AC-3.3 | US-3 | R-9 | 代码审查 frame_node.cpp:1949-1991 |
| AC-4.1 | US-4 | R-10 | 代码审查 ui_node.h:1039-1086 |
| AC-4.2 | US-4 | R-11 | 代码审查 native_node.h:14314 |
| AC-4.3 | US-4 | R-12 | 代码审查 native_node.h:14314 |
| AC-5.1 | US-5 | R-13 | 代码审查 pipeline_context.h:924-930 |
| AC-5.2 | US-5 | R-14 | 代码审查 resource_adapter_impl_v2.cpp:133-176 |
| AC-6.1 | US-6 | R-15 | 代码审查 pipeline_context.cpp:7163-7184 |
| AC-6.2 | US-6 | R-16 | 代码审查 pipeline_context.cpp:7163-7184 |
| AC-7.1 | US-7 | R-17 | 代码审查 native_node.h:13984 |
| AC-7.2 | US-7 | R-18 | 代码审查 native_node.h:13993 |

## 规则定义

> **统一规则表。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `common.d.ts:2357-2396` | Configuration.colorMode 返回 ConfigurationConstant.ColorMode | @since 7/11 | AC-1.1 |
| R-2 | 边界 | `ace_type.h:43-47` | ColorMode 枚举包含 LIGHT=0/DARK/COLOR_MODE_UNDEFINED | — | AC-1.2 |
| R-3 | 边界 | `common.d.ts:8020-8052` | ThemeColorMode 枚举包含 SYSTEM=0/LIGHT=1/DARK=2 | @since 10 | AC-1.3 |
| R-4 | 行为 | `ace_ability.cpp:617-641` | Ability OnConfigurationUpdated 接收系统配置变更并触发 Container UpdateConfiguration | — | AC-2.1 |
| R-5 | 行为 | `ui_content_impl.cpp:3505-3533` | BuildParsedConfig 读取 SYSTEM_COLORMODE 存入 ParsedConfig.colorMode | colorModeIsSetByApp (ace_container.h:94) | AC-2.2 |
| R-6 | 行为 | `ace_container.cpp:3653-3670` | ProcessColorModeUpdate 调用 SetColorMode + SetColorScheme + NotifyColorModeChange | — | AC-2.3 |
| R-7 | 行为 | `pipeline_context.cpp:7678-7714` | NotifyColorModeChange 使用 400ms FRICTION 曲线动画 | duration=400ms | AC-3.1 |
| R-8 | 行为 | `pipeline_context.cpp:7693-7699` | 动画闭包执行 SetNeedReload(true)+SetIsReloaling(true)+SetDarkMode+NotifyColorModeChange+FlushUITasks | SetIsReloading 阻止中间态 | AC-3.2 |
| R-9 | 行为 | `frame_node.cpp:1949-1991` | FrameNode NotifyColorModeChange 检查 GetLocalColorMode 后递归子节点调用 OnColorConfigurationUpdate | colorModeUpdateCallback_ (h:1839) | AC-3.3 |
| R-10 | 边界 | `ui_node.h:1039-1086, 1421-1422` | forceDarkAllowed_ 默认 true，forceDarkAllowedbyUser_ 默认 false | 双标记区分系统/用户 | AC-4.1 |
| R-11 | 行为 | `native_node.h:14314` | OH_ArkUI_SetForceDarkConfig 设置 forceDarkAllowedbyUser_ | @since 20 | AC-4.2 |
| R-12 | 异常 | `native_node.h:14314` | ForceDarkConfig 无效时返回 ARKUI_ERROR_CODE_FORCE_DARK_CONFIG_INVALID | — | AC-4.3 |
| R-13 | 边界 | `pipeline_context.h:924-930, 1631-1632` | localColorMode_ 为 std::atomic\<ColorMode\>，默认 COLOR_MODE_UNDEFINED | colorMode_ 默认 LIGHT | AC-5.1 |
| R-14 | 行为 | `resource_adapter_impl_v2.cpp:133-176` | 优先检查 localColorMode_，UNDEFINED 时回退全局 colorMode_ | DumpColorMode (L445-462) | AC-5.2 |
| R-15 | 行为 | `pipeline_context.cpp:7163-7184` | DARK 模式时 ChangeDarkModeBrightness 叠加 #FF000000 | 仅 DARK 模式 | AC-6.1 |
| R-16 | 边界 | `pipeline_context.cpp:7163-7184` | SystemProperties::GetDarkModeBrightnessPercent 默认 "0.10,0.05" | — | AC-6.2 |
| R-17 | 行为 | `native_node.h:13984` | OH_ArkUI_RegisterSystemColorModeChangeEvent 注册回调 | @since 12 | AC-7.1 |
| R-18 | 行为 | `native_node.h:13993` | OH_ArkUI_UnregisterSystemColorModeChangeEvent 注销回调 | @since 12 | AC-7.2 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 色彩模式检测 (AC-1.1~1.3) | 代码审查 | Configuration.colorMode；ColorMode 枚举；ThemeColorMode 枚举 |
| VM-2 | US-2 系统配置传播 (AC-2.1~2.3) | 代码审查 | OnConfigurationUpdated；BuildParsedConfig；ProcessColorModeUpdate |
| VM-3 | US-3 Pipeline 通知 (AC-3.1~3.3) | 单元测试 + 代码审查 | 400ms 动画；SetNeedReload；FrameNode 递归 |
| VM-4 | US-4 Force Dark (AC-4.1~4.3) | 代码审查 | 双标记；C-API；错误码 |
| VM-5 | US-5 WithTheme (AC-5.1~5.2) | 代码审查 | localColorMode_ 原子变量；resource_adapter 优先级 |
| VM-6 | US-6 暗色亮度 (AC-6.1~6.2) | 代码审查 | #FF000000 叠加；亮度百分比 |
| VM-7 | US-7 C-API 事件注册 (AC-7.1~7.2) | 代码审查 | Register/Unregister 回调 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:2357-2396` |
| AC-1.2 | 代码审查 | `interfaces/inner_api/ace_kit/include/ui/base/ace_type.h:43-47` |
| AC-1.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:8020-8052` |
| AC-2.1 | 代码审查 | `frameworks/core/ability/ace_ability.cpp:617-641` |
| AC-2.2 | 代码审查 | `adapter/ohos/entrance/ui_content_impl.cpp:3505-3533` |
| AC-2.3 | 代码审查 | `adapter/ohos/entrance/ace_container.cpp:3653-3670` |
| AC-3.1 | 单元测试 | `test/unittest/core/pattern/withtheme/withtheme_test_ng.cpp` |
| AC-3.2 | 代码审查 | `frameworks/core/pipeline_ng/pipeline_context.cpp:7678-7714` |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/base/frame_node.cpp:1949-1991` |
| AC-4.1 | 代码审查 | `frameworks/core/components_ng/base/ui_node.h:1039-1086, 1421-1422` |
| AC-4.2 | 代码审查 | `interfaces/native/native_node.h:14314` |
| AC-4.3 | 代码审查 | `interfaces/native/native_node.h:14314` |
| AC-5.1 | 代码审查 | `frameworks/core/pipeline_ng/pipeline_context.h:924-930, 1631-1632` |
| AC-5.2 | 代码审查 | `frameworks/core/common/resource_manager/resource_adapter_impl_v2.cpp:133-176` |
| AC-6.1 | 代码审查 | `frameworks/core/pipeline_ng/pipeline_context.cpp:7163-7184` |
| AC-6.2 | 代码审查 | `frameworks/core/pipeline_ng/pipeline_context.cpp:7163-7184` |
| AC-7.1 | 代码审查 | `interfaces/native/native_node.h:13984` |
| AC-7.2 | 代码审查 | `interfaces/native/native_node.h:13993` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/common.d.ts` 及 `interfaces/native/native_node.h`

#### ArkTS API

```typescript
// common.d.ts:2357-2396 (@since 7/11)
interface Configuration {
    readonly colorMode: ConfigurationConstant.ColorMode;
}

// common.d.ts:8020-8052 (@since 10)
enum ThemeColorMode {
    SYSTEM = 0,
    LIGHT = 1,
    DARK = 2
}

// common.d.ts:8063-8084 (@since 26)
enum AnchoredColorMode {
    FOLLOW_SYSTEM,
    FOLLOW_TARGET
}
```

#### C-API

| API 签名 | 返回类型 | native_node.h 行 | @since |
|----------|----------|-------------------|--------|
| `OH_ArkUI_RegisterSystemColorModeChangeEvent(callback)` | int32_t | 13984 | 12 |
| `OH_ArkUI_UnregisterSystemColorModeChangeEvent(callback)` | int32_t | 13993 | 12 |
| `OH_ArkUI_SetForceDarkConfig(config)` | int32_t | 14314 | 20 |

**关联类型定义：**

| 类型 | 定义 | 用途 |
|------|------|------|
| `ColorMode` | `ace_type.h:43-47` LIGHT=0/DARK/COLOR_MODE_UNDEFINED | C++ 内部色模式枚举 |
| `ColorScheme` | `constants.h:597-601` SCHEME_LIGHT=0/SCHEME_DARK=2 | 色方案枚举 |
| `ConfigurationChange` | `resource_configuration.h:20-56` colorModeUpdate 等位标记 | 配置变更标记 |
| `ArkUI_ColorMode` | `native_type.h:833-840` SYSTEM=0/LIGHT/DARK | C-API 色模式枚举 |
| `ArkUI_SystemColorMode` | `native_type.h:862-867` LIGHT=0/DARK | C-API 系统色模式枚举 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | Configuration.colorMode 首次引入（@since 7） | 新增能力 | — |
| API 9 | Ability Configuration.colorMode 和 ConfigurationConstant.ColorMode 引入 | 新增能力 | — |
| API 10 | ThemeColorMode 枚举引入（SYSTEM/LIGHT/DARK） | 新增能力 | — |
| API 12 | C-API ArkUI_ColorMode 和事件注册引入 | 新增能力 | — |
| API 20 | C-API OH_ArkUI_SetForceDarkConfig 引入，返回错误码 | 新增能力 | — |
| API 26 | AnchoredColorMode 枚举引入（FOLLOW_SYSTEM/FOLLOW_TARGET） | 新增能力 | — |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 三层传播 | Container→Pipeline→FrameNode 三层色模式传播架构 |
| 位标记变更 | ConfigurationChange 使用位标记，OnlyColorModeChange 快速判断 |
| 原子变量 | localColorMode_ 为 std::atomic\<ColorMode\> 保证线程安全 |
| 动画过渡 | NotifyColorModeChange 使用 400ms FRICTION 动画，SetIsReloading 阻止中间态 |
| 双标记 Force Dark | forceDarkAllowed_(系统) 和 forceDarkAllowedbyUser_(用户) 双标记区分 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | NotifyColorModeChange 使用 400ms 动画过渡，SetNeedReload 控制资源重载开销 |
| 线程安全 | localColorMode_ 使用 std::atomic 保证并发安全 |
| 可调试性 | DumpColorMode (resource_adapter_impl_v2.cpp:445-462) 诊断色模式状态 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 无障碍 | 是，深色模式影响无障碍对比度，组件 OnColorConfigurationUpdate 刷新主题 |
| 大字体 | 无差异 |
| 深色模式 | 是，本特性为深色模式核心实现 |
| 多窗口分屏 | 是，WithTheme 通过 localColorMode_ 实现窗口级色模式隔离 |
| 多用户 | 无差异 |
| 版本升级 | 是，API 7→9→10→12→20→26 版本演进 |
| 生态兼容 | 否 |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 业务规则/功能规则/异常规则/恢复契约编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（common.d.ts, native_node.h）
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/pipeline_ng/pipeline_context.cpp` | Pipeline 级 NotifyColorModeChange + ChangeDarkModeBrightness |
| `frameworks/core/pipeline_ng/pipeline_context.h` | colorMode_/localColorMode_ 字段定义 |
| `frameworks/core/components_ng/base/ui_node.h` | SetDarkMode/AllowForceDark/forceDarkAllowed_ |
| `frameworks/core/components_ng/base/frame_node.cpp` | NotifyColorModeChange 递归传播 |
| `frameworks/core/components_ng/base/frame_node.h` | colorModeUpdateCallback_ |
| `adapter/ohos/entrance/ace_container.cpp` | ParsedConfig + UpdateConfiguration + ProcessColorModeUpdate |
| `adapter/ohos/entrance/ace_container.h` | ParsedConfig colorMode/colorModeIsSetByApp |
| `adapter/ohos/entrance/ui_content_impl.cpp` | BuildParsedConfig 读取 SYSTEM_COLORMODE |
| `frameworks/core/ability/ace_ability.cpp` | OnConfigurationUpdated 接收系统配置 |
| `frameworks/core/common/resource_manager/resource_adapter_impl_v2.cpp` | localColorMode 优先检查 + DumpColorMode |
| `interfaces/inner_api/ace_kit/include/ui/base/ace_type.h` | ColorMode 枚举定义 |
| `interfaces/inner_api/ace_kit/include/ui/resource/resource_configuration.h` | ConfigurationChange 变更位定义 |
| `frameworks/core/components/common/layout/constants.h` | ColorScheme 枚举定义 |
| `interfaces/native/native_node.h` | C-API 色彩模式事件注册 + ForceDarkConfig |
| `interfaces/native/native_type.h` | ArkUI_ColorMode / ArkUI_SystemColorMode 枚举 |
| `interface/sdk-js/api/@internal/component/ets/common.d.ts` | Configuration/ThemeColorMode/AnchoredColorMode SDK 定义 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/withtheme/withtheme_test_ng.cpp` | WithTheme 色彩模式单元测试（ColorMode 设置/获取/缓存） |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | SDK API 知识库 |
| `docs/sdk/Component_API_Knowledge_Base_CN.md` | 组件 API 知识库 |
