# 特性规格

> Func-07-04-24-Feat-01 主题与色彩模式：固化主题模式双层枚举（ArkTS `ThemeMode{0/1}` ↔ C++ `ThemeMode{LIGHT/DARK}`）、`createSurface.theme` 品牌色解析（`primaryColor`/`darkPrimaryColor`/`iconUrl`/`agentDisplayName`）、品牌色三态派生（深色 darkPrimaryColor 优先，缺省取 primaryColor RGB 反色）、颜色格式解析（`#RRGGBB`/`#AARRGGBB`）、跟随系统 vs 手动切换状态机（`isFollowSystemColorMode`）、主题变更广播（组件 `OnConfigChange` + `__colorMode` 全局表达式变量）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 主题与色彩模式 |
| 特性编号 | Func-07-04-24-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9；宿主集成 API Version ≥ 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-24 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/24-theme-color-mode/design.md` | Baselined |
| 主题上下文/枚举（C++） | `genui/src/main/cpp/theme/ThemeBase.h` | — |
| 主题管理（C++） | `genui/src/main/cpp/theme/ThemeManager.cpp` | — |
| 主题工厂（C++） | `genui/src/main/cpp/theme/ThemeFactory.cpp` | — |
| 颜色工具（C++） | `genui/src/main/cpp/utils/ThemeColorUtils.cpp` | — |
| 模式/断点枚举（ArkTS） | `genui/src/main/ets/interface/Types.ets` | — |
| 控制器实现（ArkTS） | `genui/src/main/ets/core/base/SurfaceControllerImpl.ets` | — |
| 宿主集成（ArkTS） | `genui/src/main/ets/core/components/UIRendererComponentCore.ets` | — |
| 原生入口（C++） | `genui/src/main/cpp/NativeEntry.cpp` | — |
| 渲染管理（C++） | `genui/src/main/cpp/SurfaceManager.cpp` | — |
| 表达式求值（C++） | `genui/src/main/cpp/expression/EvaluationContext.cpp` | — |
| 主题概念参考（Docs） | `render_docs/concepts/theme-and-color-mode.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 主题模式枚举与双层映射

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎在 ArkTS 与 C++ 两层以一致的数值表示主题模式,
**以便** 跨语言传递时深浅色语义不丢失。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 引用 ArkTS `ThemeMode.LIGHT` THEN 值为 0（`Types.ets:142`） | 正常 |
| AC-1.2 | WHEN 引用 ArkTS `ThemeMode.DARK` THEN 值为 1（`Types.ets:145`） | 正常 |
| AC-1.3 | WHEN C++ 侧引用 `ThemeMode::LIGHT`/`ThemeMode::DARK` THEN 为 `enum class` 两态（`ThemeBase.h:27-30`） | 正常 |
| AC-1.4 | WHEN NAPI `UpdateThemeMode` 收到 `mode==1` THEN 映射为 `ThemeMode::DARK`，否则映射为 `ThemeMode::LIGHT`（`NativeEntry.cpp:2199`） | 正常 |
| AC-1.5 | WHEN `ThemeContext` 默认构造 THEN `colorMode == ThemeMode::LIGHT`（`ThemeBase.h:71`） | 边界 |

### US-2: createSurface.theme 字段解析

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎从 createSurface 的 theme 字段解析品牌色与主题元数据,
**以便** 标准协议下配置品牌色与图标/显示名。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `createSurface` 消息体含 `theme` 对象 THEN `ParseCreateSurfaceComponentTheme` 解析并返回 true（`NativeEntry.cpp:371-379,408`） | 正常 |
| AC-2.2 | WHEN `createSurface` 无 `theme` 字段或 `theme` 非对象 THEN 返回 false（`NativeEntry.cpp:371-379`） | 异常 |
| AC-2.3 | WHEN `theme.primaryColor` 为合法 `#RRGGBB`/`#AARRGGBB` THEN `hasPrimaryColor=true` 且 `primaryColorArgb` 被写入（`NativeEntry.cpp:384-389`） | 正常 |
| AC-2.4 | WHEN `theme.primaryColor` 非法或空串 THEN 仅打 warn 日志，`hasPrimaryColor` 保持 false（`NativeEntry.cpp:386-394`） | 异常 |
| AC-2.5 | WHEN `theme.darkPrimaryColor` 合法 THEN `hasDarkPrimaryColor=true` 且 `darkPrimaryColorArgb` 被写入（`NativeEntry.cpp:396-401`） | 正常 |
| AC-2.6 | WHEN `theme.iconUrl`/`theme.agentDisplayName` 存在 THEN 对应字段被读取（`NativeEntry.cpp:381-382`） | 正常 |
| AC-2.7 | WHEN 解析成功 THEN 经 `ThemeManager::SetComponentTheme` 写入上下文（`NativeEntry.cpp:424` → `ThemeManager.cpp:52-62`） | 正常 |

### US-3: 品牌色派生

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎按当前深浅色模式派生有效品牌色,
**以便** 标准组件正确着色。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 深色模式且 `hasDarkPrimaryColor` THEN `brandColor == darkPrimaryColorArgb`（`ThemeManager.cpp:66-70`） | 正常 |
| AC-3.2 | WHEN 深色模式且仅 `hasPrimaryColor`（无 darkPrimaryColor） THEN `brandColor == InvertRgbKeepAlpha(primaryColorArgb)`（`ThemeManager.cpp:71-74`） | 正常 |
| AC-3.3 | WHEN 浅色模式且 `hasPrimaryColor` THEN `brandColor == primaryColorArgb`（`ThemeManager.cpp:75-78`） | 正常 |
| AC-3.4 | WHEN 无 effective 品牌色且 `forceClearWhenUnresolved` 或 `HasComponentThemeValue()` THEN `ClearBrandColor`（`ThemeManager.cpp:80-82`） | 边界 |
| AC-3.5 | WHEN `InvertRgbKeepAlpha` 处理任意 ARGB THEN alpha 通道保留、RGB 按位取反（`ThemeColorUtils.cpp:81-86`） | 正常 |
| AC-3.6 | WHEN `SetComponentTheme` 写入新主题字段 THEN 以 `forceClearWhenUnresolved=true` 重派生品牌色（`ThemeManager.cpp:61`） | 正常 |

### US-4: 颜色格式解析

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎支持标准颜色格式,
**以便** 品牌色以 `#RRGGBB`/`#AARRGGBB` 表达。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 输入 `#RRGGBB`（长度 7） THEN `TryParseArgb` 返回 true 且 alpha 补 `0xFF`（`ThemeColorUtils.cpp:51-54,58,76`） | 正常 |
| AC-4.2 | WHEN 输入 `#AARRGGBB`（长度 9） THEN 保留显式 alpha（`ThemeColorUtils.cpp:60-65`） | 正常 |
| AC-4.3 | WHEN 输入长度非 7/9 或非 `#` 前缀 THEN 返回 false（`ThemeColorUtils.cpp:51-55`） | 边界 |
| AC-4.4 | WHEN 输入含非十六进制字符 THEN `TryParseHexByte` 返回 false，整体返回 false（`ThemeColorUtils.cpp:29-45,70-74`） | 异常 |

### US-5: 跟随系统与手动切换

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎默认跟随系统深浅色并可手动覆盖,
**以便** 无需/需要时分别处理色彩模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 控制器构造 THEN `isFollowSystemColorMode=true` 且 `currentThemeMode=LIGHT`（`SurfaceControllerImpl.ets:108,123`） | 正常 |
| AC-5.2 | WHEN 调用 `updateThemeMode(mode)` THEN `isFollowSystemColorMode=false` 并更新模式（`SurfaceControllerImpl.ets:1158-1161`） | 正常 |
| AC-5.3 | WHEN `isFollowSystemColorMode=false` 且调用 `updateAndCheckThemeMode(mode)` THEN 直接返回不更新（`SurfaceControllerImpl.ets:1148-1153`） | 边界 |
| AC-5.4 | WHEN `updateThemeMode` 传入与 `currentThemeMode` 相同值 THEN 跳过更新（`SurfaceControllerImpl.ets:1140-1143`） | 边界 |
| AC-5.5 | WHEN 系统色彩模式变化触发 environment 回调 THEN 调 `updateAndCheckThemeMode(resolve(...))`（`UIRendererComponentCore.ets:118-128`） | 正常 |
| AC-5.6 | WHEN `resolveThemeModeFromSystemColorMode` 收到 `COLOR_MODE_DARK` THEN 返回 `ThemeMode.DARK`，否则返回 `ThemeMode.LIGHT`（`UIRendererComponentCore.ets:111-116`） | 正常 |
| AC-5.7 | WHEN 宿主主动调用 `updateThemeMode` 后系统再切换 THEN 系统切换被忽略（`updateAndCheckThemeMode` 早退） | 边界 |

### US-6: 主题变更广播

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎在主题变更时刷新组件并重求值表达式,
**以便** 全局深浅色语义即时生效。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `SurfaceManager::UpdateThemeMode` 被调用 THEN 逆序（latest→earliest）遍历所有 surface（`SurfaceManager.cpp:285-300`） | 正常 |
| AC-6.2 | WHEN 遍历每个 surface THEN 依次执行 `UpdateThemeMode`、`NotifyThemeChange`、`NotifyGlobalExpressionVariableChanged("__colorMode")`（`SurfaceManager.cpp:297-299`） | 正常 |
| AC-6.3 | WHEN `NotifyThemeChange` THEN 更新所有缓存主题 `UpdateContext` 并对所有组件调 `OnConfigChange`（`ThemeManager.cpp:108-129`） | 正常 |
| AC-6.4 | WHEN 表达式解析 `__colorMode` THEN 返回 `"light"`/`"dark"` 字符串（`EvaluationContext.cpp:34-39`、`ThemeContextUtils.h:43-53`） | 正常 |
| AC-6.5 | WHEN `UpdateBreakpoint` 被执行 THEN 通知 `__widthBreakpoint` 变量（`SurfaceManager.cpp:303-325`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-1 | 静态比对：ArkTS 枚举 vs C++ 枚举 vs NAPI 收敛 | `Types.ets:140-146`、`ThemeBase.h:27-30`、`NativeEntry.cpp:2199` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-2.7 | R-2,R-3 | T-1 | C++ UT：`ParseCreateSurfaceComponentTheme` 各字段 | `NativeEntry.cpp:369-425` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-4,R-5 | T-1 | C++ UT：`RefreshBrandColorFromContext` 组合 | `ThemeManager.cpp:64-83` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-6 | T-1 | C++ UT：`TryParseArgb`/`InvertRgbKeepAlpha` | `ThemeColorUtils.cpp:49-86` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 | R-7,R-8 | T-1 | ArkTS 单测：状态机 | `SurfaceControllerImpl.ets:108-1161`、`UIRendererComponentCore.ets:111-128` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 | R-9 | T-1 | C++ UT：广播遍历 | `SurfaceManager.cpp:277-325`、`ThemeManager.cpp:108-129` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | ThemeMode 双层枚举 | ArkTS 0/1 与 C++ LIGHT/DARK 对应；NAPI `mode==1?DARK:LIGHT` | 仅两态 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 异常 | createSurface.theme 非对象或缺失 | `ParseCreateSurfaceComponentTheme` 返回 false，不写入 | theme 缺失视为无主题 | AC-2.1,AC-2.2 |
| R-3 | 异常 | primaryColor/darkPrimaryColor 非法 | 仅告警，`hasPrimaryColor`/`hasDarkPrimaryColor` 保持 false | 非法值不阻断 createSurface | AC-2.3,AC-2.4,AC-2.5,AC-2.6 |
| R-4 | 行为 | 深色 + darkPrimaryColor | brandColor = darkPrimaryColorArgb | 优先于 primaryColor | AC-3.1 |
| R-5 | 行为 | 深色无 darkPrimaryColor 仅有 primaryColor | brandColor = primaryColor RGB 反色 | 反色保留 alpha | AC-3.2,AC-3.5 |
| R-6 | 边界 | 颜色串长度非 7/9 或非 `#` 前缀 | `TryParseArgb` 返回 false | `#RRGGBB` alpha 补 FF | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-7 | 行为 | 调用 updateThemeMode | 置 `isFollowSystemColorMode=false` 并更新 | 手动覆盖优先级 > 系统 | AC-5.2,AC-5.7 |
| R-8 | 边界 | currentThemeMode 与入参相同 | 跳过更新 | 同值去重 | AC-5.3,AC-5.4 |
| R-9 | 行为 | 主题/断点变更 | 广播组件 `OnConfigChange` + 通知 `__colorMode`/`__widthBreakpoint` | 逆序遍历 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 枚举双层映射 | 静态比对 | 数值一致与 NAPI 收敛 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-2.7 theme 解析 | C++ UT | 字段解析与非法降级 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 品牌色派生 | C++ UT | 三态优先级 + 反色 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 颜色格式 | C++ UT | RRGGBB/AARRGGBB/非法 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 跟随/手动 | ArkTS 单测 | 状态机与去重 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 变更广播 | C++ UT | 遍历顺序 + 表达式变量 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceController.updateThemeMode(mode: ThemeMode)` | 既有 | 手动切换深浅色 | 宿主按枚举传值 | AC-5.2 |
| `ThemeMode`（公开枚举） | 既有 | 主题模式取值 | 数值稳定（0/1） | AC-1.1,AC-1.2 |
| `Breakpoint`（公开枚举） | 既有 | 断点取值 | 数值稳定（0..4） | AC-6.5 |

> d.ts 位置：`genui/src/main/ets/interface/Types.ets`、`SurfaceController.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`SurfaceController.updateThemeMode(mode)`（公开，`SurfaceController.ets:128`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `updateThemeMode(mode: ThemeMode): void` |
| 返回值 | `void` — 无返回 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.2,AC-5.4,AC-5.7 |

**`ParseCreateSurfaceComponentTheme(messageBody, themeContext)`（内部 C++，`NativeEntry.cpp:369`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool ParseCreateSurfaceComponentTheme(const JsonValue& messageBody, ThemeContext& themeContext)` |
| 返回值 | `bool` — 是否成功解析主题 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（非法颜色仅告警） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |

**`ThemeManager::RefreshBrandColorFromContext(forceClearWhenUnresolved)`（内部 C++，`ThemeManager.cpp:64`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void RefreshBrandColorFromContext(bool forceClearWhenUnresolved)` |
| 返回值 | `void` — 副作用更新 `context_.brandColor` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| mode | ThemeMode | 是 | — | 取值 0（LIGHT）/1（DARK）；其它值经 NAPI 收敛为 LIGHT |
| theme.primaryColor | string | 否 | 空串（不解析） | `#RRGGBB` 或 `#AARRGGBB` |
| theme.darkPrimaryColor | string | 否 | 空串（不解析） | 同上 |
| theme.iconUrl / theme.agentDisplayName | string | 否 | 空串 | 任意字符串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | createSurface 无 theme | 返回 false，无品牌色派生 | AC-2.2 |
| 2 | primaryColor 非法 | 告警，`hasPrimaryColor=false` | AC-2.4 |
| 3 | 深色 + darkPrimaryColor | brandColor = darkPrimaryColor | AC-3.1 |
| 4 | 深色仅 primaryColor | brandColor = 反色 | AC-3.2 |
| 5 | 浅色 + primaryColor | brandColor = primaryColor | AC-3.3 |
| 6 | 调用 updateThemeMode(DARK) | isFollow=false，经 NAPI 更新 | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 宿主集成 API Version ≥ 20（native 渲染启用门槛，`SurfaceControllerImpl.ets:139`）。
- **API 版本号策略:** 协议版本由 `CapabilitiesCore['v0.9']` 声明不受本域影响；`ThemeMode`/`Breakpoint` 枚举数值稳定。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 双层枚举 | ArkTS 与 C++ 枚举数值一致，NAPI 单点收敛 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| 品牌色三态 | 深色 darkPrimaryColor > primaryColor 反色；浅色 primaryColor | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 跟随系统默认 | `isFollowSystemColorMode` 默认 true，手动覆盖后不可恢复跟随 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 |
| 广播一致性 | 组件 `OnConfigChange` 与 `__colorMode` 变量通知同步触发 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法颜色不抛异常，仅告警并回落默认色 | C++ UT | `NativeEntry.cpp:390-394,402-405` |
| 性能 | 主题对象惰性缓存，避免重复创建 | C++ UT | `ThemeManager.cpp:85-100` |
| 可测试性 | 品牌色派生为纯函数（`RefreshBrandColorFromContext`/`InvertRgbKeepAlpha`） | C++ UT | `ThemeManager.cpp:64-83`、`ThemeColorUtils.cpp:81-86` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 主题/颜色与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 断点切换归 07-04-23 | ohosTest | `ThemeBase.h:36-59` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 颜色/模式无关 | — |
| 大字体 | 否 | 不涉及（字号缩放归另一接口） | — |
| 深色模式 | 是 | 本域核心能力 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7,AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |
| 多窗口/分屏 | 否 | 多 Surface 主题独立 | design.md ADR-5 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version ≥ 20 native 渲染门槛 | AC-5.1 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 `theme` 字段 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 主题与色彩模式
  作为 生成式 UI 宿主开发者
  我想要 配置品牌色并控制深浅色
  以便 标准组件正确着色且跟随/手动切换符合预期

  Scenario: 深色模式使用 darkPrimaryColor
    Given createSurface.theme 为 {"primaryColor":"#00BFFF","darkPrimaryColor":"#FF6A00"}
    And 当前 colorMode 为 DARK
    When 调用 RefreshBrandColorFromContext
    Then brandColor 等于 #FF6A00

  Scenario: 深色模式缺省 darkPrimaryColor 时取反色
    Given createSurface.theme 为 {"primaryColor":"#00BFFF"}
    And 当前 colorMode 为 DARK
    When 调用 RefreshBrandColorFromContext
    Then brandColor 等于 InvertRgbKeepAlpha(#00BFFF)

  Scenario: 手动切换后不跟随系统
    Given 控制器 isFollowSystemColorMode 为 true
    When 调用 updateThemeMode(ThemeMode.DARK)
    Then isFollowSystemColorMode 为 false
    And 后续 updateAndCheckThemeMode(LIGHT) 被忽略

  Scenario Outline: 非法颜色降级
    Given createSurface.theme.primaryColor 为 <value>
    When 调用 ParseCreateSurfaceComponentTheme
    Then hasPrimaryColor 为 false

    Examples:
      | value      |
      | ""         |
      | "#ZZZZZZ"  |
      | "#1234567" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做主题/品牌色/深浅色切换；扩展组件默认色见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ThemeManager RefreshBrandColorFromContext 品牌色派生 darkPrimaryColor 反色优先级"
  - repo: "GenerativeUI/A2UIRender"
    query: "ParseCreateSurfaceComponentTheme createSurface.theme primaryColor darkPrimaryColor iconUrl agentDisplayName"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceControllerImpl updateThemeMode updateAndCheckThemeMode isFollowSystemColorMode 状态机"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceManager UpdateThemeMode NotifyThemeChange __colorMode 全局表达式变量"
```

**关键文档：** `genui/src/main/cpp/theme/ThemeManager.cpp`、`genui/src/main/cpp/theme/ThemeBase.h`、`genui/src/main/cpp/NativeEntry.cpp`、`genui/src/main/cpp/SurfaceManager.cpp`、`genui/src/main/ets/interface/Types.ets`、`genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/ets/core/components/UIRendererComponentCore.ets`、`genui/src/main/cpp/utils/ThemeColorUtils.cpp`