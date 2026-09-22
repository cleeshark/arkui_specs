# 特性规格

> Func-07-04-23-Feat-01 响应式断点：固化 5 档断点枚举（`xs/sm/md/lg/xl`）、阈值（`[0,320)/[320,600)/[600,840)/[840,1440)/[1440,+∞)` vp）、双端解析（ArkTS `BreakpointUtils.resolveBreakpoint` + C++ `ResolveBreakpointFromWidth`/`ResolveBreakpointValue`）、断点驱动链路（`UIRendererComponentCore.onSizeChange`→`updateBreakpointByWidth`→NAPI→`SurfaceManager::UpdateBreakpoint` 双通道传播）、全局变量 `$__widthBreakpoint` 字符串值（`xs..xl`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 响应式断点 |
| 特性编号 | Func-07-04-23-Feat-01 |
| 优先级 | P0 |
| 目标版本 | OpenHarmony API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-23 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/23-multi-device-adaptation/design.md` | Baselined |
| 断点解析（ArkTS） | `genui/src/main/ets/core/common/BreakpointUtils.ets` | — |
| 断点枚举（ArkTS） | `genui/src/main/ets/interface/Types.ets` | — |
| 断点控制器（ArkTS） | `genui/src/main/ets/core/base/SurfaceControllerImpl.ets` | — |
| 断点承载（ArkTS） | `genui/src/main/ets/core/components/UIRendererComponentCore.ets` | — |
| 断点传播（C++） | `genui/src/main/cpp/SurfaceManager.cpp` | — |
| 断点枚举/阈值（C++） | `genui/src/main/cpp/theme/ThemeBase.h` | — |
| 断点入参转换（C++） | `genui/src/main/cpp/NativeEntry.cpp` | — |
| 全局变量解析（C++） | `genui/src/main/cpp/expression/EvaluationContext.cpp`、`expression/ThemeContextUtils.h` | — |
| 概念参考（Docs） | `concepts/multi-device-adaptation.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 断点枚举与阈值定义

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎提供稳定的断点档位与宽度阈值,
**以便** 同一 DSL 在不同屏幕宽度下呈现自适应布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 读取 `Breakpoint` 枚举 THEN 存在 XS=0/SM=1/MD=2/LG=3/XL=4 五档（`Types.ets:151-166`） | 正常 |
| AC-1.2 | WHEN C++ 侧 `Breakpoint` 枚举（`ThemeBase.h:36-42`）与 ArkTS 枚举 THEN 档位顺序一致（XS/SM/MD/LG/XL） | 正常 |
| AC-1.3 | WHEN 输入 widthVp<320 THEN `resolveBreakpoint` 返回 XS（`BreakpointUtils.ets:20-22`） | 边界 |
| AC-1.4 | WHEN 320≤widthVp<600 THEN 返回 SM（`BreakpointUtils.ets:23-25`） | 边界 |
| AC-1.5 | WHEN 600≤widthVp<840 THEN 返回 MD（`BreakpointUtils.ets:26-28`） | 边界 |
| AC-1.6 | WHEN 840≤widthVp<1440 THEN 返回 LG（`BreakpointUtils.ets:29-31`） | 边界 |
| AC-1.7 | WHEN widthVp≥1440 THEN 返回 XL（`BreakpointUtils.ets:32`） | 边界 |

### US-2: 断点驱动与去重

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎在容器尺寸变化时自动重算断点并避免重复下发,
**以便** 断点仅在档位变化时生效。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 控制器已销毁 THEN `updateBreakpoint` 被忽略并打 `updateBreakpoint ignored` 日志（`SurfaceControllerImpl.ets:1176-1179`） | 异常 |
| AC-2.2 | WHEN 新断点与 `currentBreakpoint` 相同 THEN `updateBreakpoint` 跳过并打 `updateBreakpoint skipped` 日志（`SurfaceControllerImpl.ets:1182-1185`） | 边界 |
| AC-2.3 | WHEN 新断点不同 THEN 更新 `currentBreakpoint` 并调 `NativeEngineBridge.updateBreakpoint`（`SurfaceControllerImpl.ets:1187-1189`） | 正常 |
| AC-2.4 | WHEN `updateBreakpointByWidth` 收到非有限或 ≤0 的 widthVp THEN 跳过并打 `updateBreakpointByWidth skipped` 日志（`SurfaceControllerImpl.ets:1193-1199`） | 异常 |
| AC-2.5 | WHEN `updateBreakpointByWidth` 收到合法 widthVp THEN 经 `resolveBreakpoint` 转档后调 `updateBreakpoint`（`SurfaceControllerImpl.ets:1200`） | 正常 |
| AC-2.6 | WHEN `getBreakpoint` 被调用 THEN 返回 `currentBreakpoint`（`SurfaceControllerImpl.ets:1207-1209`） | 正常 |
| AC-2.7 | WHEN 控制器初始化 THEN `currentBreakpoint` 默认值为 SM（`SurfaceControllerImpl.ets:124`） | 边界 |

### US-3: 断点驱动链路

**作为** 生成式 UI 宿主开发者,
**我想要** 承载组件自动采集容器宽度并同步断点,
**以便** 无需宿主手动调用断点 API。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 容器 `onSizeChange` 触发 THEN `handleContainerAreaChange` 解析新宽度并 `syncBreakpointFromContainer`（`UIRendererComponentCore.ets:279-282`） | 正常 |
| AC-3.2 | WHEN `aboutToAppear`/`onAppear` 触发 THEN 调用 `syncBreakpointFromContainer`（`UIRendererComponentCore.ets:206,385`） | 正常 |
| AC-3.3 | WHEN `containerWidthVp` 为 undefined/非有限/≤0 THEN `syncBreakpointFromContainer` 直接返回（`UIRendererComponentCore.ets:263-267`） | 边界 |
| AC-3.4 | WHEN 宽度为 number 且有限且 >0 THEN `resolveAreaLengthVpForBreakpoint` 返回该值（`UIRendererComponentCore.ets:41-46`） | 正常 |
| AC-3.5 | WHEN 宽度为 `Nvp` 字符串（如 `"600vp"`） THEN 返回数值 600（`UIRendererComponentCore.ets:54-62`） | 正常 |
| AC-3.6 | WHEN 宽度为非法字符串/非 vp 单位/≤0 THEN `resolveAreaLengthVpForBreakpoint` 返回 undefined（`UIRendererComponentCore.ets:47-62`） | 异常 |

### US-4: native 断点入参与传播

**作为** 渲染引擎开发者,
**我想要** native 侧校验断点入参并传播到所有 surface,
**以便** 断点变化正确驱动主题与表达式重求值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN NAPI `UpdateBreakpoint` 收到非法断点值（非 0-4） THEN `ResolveBreakpointValue` 回落 SM 并打 warn（`NativeEntry.cpp:2219-2221`） | 异常 |
| AC-4.2 | WHEN NAPI `UpdateBreakpoint` 收到 0-4 THEN `ResolveBreakpointValue` 映射为 XS/SM/MD/LG/XL（`NativeEntry.cpp:2208-2218`） | 正常 |
| AC-4.3 | WHEN `UpdateBreakpoint` 找不到 renderSlot 或 surfaceManager THEN 打 warn 并返回（`NativeEntry.cpp:2251-2260`） | 异常 |
| AC-4.4 | WHEN `SurfaceManager::UpdateBreakpoint` 执行 THEN 更新 `themeContext_.breakpoint`（`SurfaceManager.cpp:308`） | 正常 |
| AC-4.5 | WHEN 断点传播 THEN 逆序遍历 surface，逐个 `UpdateBreakpoint`+`NotifyThemeChange`+`NotifyGlobalExpressionVariableChanged("__widthBreakpoint")`（`SurfaceManager.cpp:310-324`） | 正常 |
| AC-4.6 | WHEN `ThemeManager::UpdateBreakpoint` 执行 THEN 更新 `context_.breakpoint`（`ThemeManager.cpp:35-38`） | 正常 |

### US-5: `__widthBreakpoint` 全局变量

**作为** 生成式 UI 宿主开发者,
**我想要** 在表达式里引用 `$__widthBreakpoint` 得到字符串档位,
**以便** 编写响应式 DSL。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `__widthBreakpoint` 解析且 themeContext 有效 THEN 返回 `BreakpointToString(breakpoint)`（`EvaluationContext.cpp:28-33`） | 正常 |
| AC-5.2 | WHEN `BreakpointToString` 收到 XS/SM/MD/LG/XL THEN 返回 `"xs"/"sm"/"md"/"lg"/"xl"`（`ThemeContextUtils.h:25-41`） | 正常 |
| AC-5.3 | WHEN `__widthBreakpoint` 解析且 themeContext 为 null THEN 回落 `"sm"`（`EvaluationContext.cpp:32`） | 边界 |
| AC-5.4 | WHEN `BreakpointToString` 收到非法值 THEN 回落 `"sm"`（`ThemeContextUtils.h:38-39`） | 边界 |
| AC-5.5 | WHEN 表达式引用 `$__widthBreakpoint` 且依赖断点变化 THEN 经 `NotifyGlobalVariableChanged("__widthBreakpoint")` 触发依赖组件重求值（`BindingEngine.cpp:445-482`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7 | R-1,R-2 | T-1 | ArkTS/C++ 单测：阈值边界判定 | `BreakpointUtils.ets:19-33`、`ThemeBase.h:44-59` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-2.7 | R-3,R-4,R-5 | T-1 | ArkTS 单测：updateBreakpoint 状态机 | `SurfaceControllerImpl.ets:1175-1209` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-6,R-7 | T-1 | ArkTS 单测：容器尺寸解析与同步 | `UIRendererComponentCore.ets:40-63,262-282` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 | R-8,R-9 | T-1 | C++ UT：NAPI 入参 + 传播 | `NativeEntry.cpp:2206-2266`、`SurfaceManager.cpp:303-325` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-10,R-11 | T-1 | C++ UT：全局变量解析 | `EvaluationContext.cpp:26-48`、`ThemeContextUtils.h:25-41` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 读取 Breakpoint 枚举 | 五档 XS=0/SM=1/MD=2/LG=3/XL=4 | ArkTS/C++ 双端一致 | AC-1.1,AC-1.2 |
| R-2 | 边界 | widthVp 落入阈值区间 | 返回对应档位 | 320/600/840/1440 为闭区间下界（=320→SM、=600→MD、=840→LG、=1440→XL） | AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7 |
| R-3 | 异常 | updateBreakpoint 时已 destroyed | 忽略 | 幂等 | AC-2.1 |
| R-4 | 边界 | updateBreakpoint 与当前档相同 | 跳过下发 | 无变化短路 | AC-2.2 |
| R-5 | 行为 | updateBreakpoint 档位变化 | 更新 currentBreakpoint 并 NAPI 下发 | — | AC-2.3,AC-2.6 |
| R-6 | 异常 | updateBreakpointByWidth 非有限或 ≤0 | 跳过 | NaN/Infinity/0/负数拒绝 | AC-2.4 |
| R-7 | 边界 | 容器宽度非法或缺失 | syncBreakpoint 直接返回 | undefined/非有限/≤0 | AC-3.3,AC-3.6 |
| R-8 | 异常 | NAPI 断点入参非 0-4 | 回落 SM | 默认档 SM | AC-4.1 |
| R-9 | 行为 | SurfaceManager.UpdateBreakpoint | 逆序传播到所有 surface | 主题 + 全局变量双通道 | AC-4.4,AC-4.5,AC-4.6 |
| R-10 | 行为 | 解析 `__widthBreakpoint` | 返回 xs/sm/md/lg/xl | themeContext 缺省回落 sm | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-11 | 行为 | 断点变化触发全局变量通知 | 依赖组件重求值 | 仅 EXPRESSION/FUNCTION_CALL 绑定 | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7 断点枚举与阈值 | ArkTS/C++ 单测 | 五档 + 阈值边界 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-2.7 断点驱动与去重 | ArkTS 单测 | destroyed/无变化/非法宽度短路 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 承载链路 | ArkTS 单测 | onSizeChange 尺寸解析 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 native 传播 | C++ UT | ResolveBreakpointValue + 逆序传播 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 全局变量 | C++ UT | BreakpointToString + 回落 |

## API 变更分析

> 存量补录，无新增/变更公开 API。断点接口为 framework-internal（`SurfaceControllerImpl` 内部），不暴露于公开 `SurfaceController` 契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Breakpoint`（公开枚举） | 既有 | 断点档位分类 | 数值稳定，宿主按枚举处理 | AC-1.1,AC-1.2 |
| `SurfaceControllerImpl.updateBreakpoint` / `updateBreakpointByWidth` / `getBreakpoint`（internal） | 既有 | 断点状态管理 | 不暴露给宿主，由承载组件驱动 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |

> d.ts 位置：`genui/src/main/ets/interface/Types.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`BreakpointUtils.resolveBreakpoint(widthVp)`（`BreakpointUtils.ets:19`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static resolveBreakpoint(widthVp: number): Breakpoint` |
| 返回值 | `Breakpoint` — 按阈值映射的档位 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7 |

**`SurfaceControllerImpl.updateBreakpointByWidth(widthVp)`（`SurfaceControllerImpl.ets:1192`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `updateBreakpointByWidth(widthVp: number): void` |
| 返回值 | `void` |
| 开放范围 | 内部 |
| 错误码 | N/A（非法输入静默跳过） |
| 关联 AC | AC-2.4,AC-2.5 |

**`SurfaceManager::UpdateBreakpoint(Breakpoint)`（`SurfaceManager.cpp:303`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void UpdateBreakpoint(Breakpoint breakpoint)` |
| 返回值 | `void` |
| 开放范围 | 内部（C++） |
| 错误码 | N/A |
| 关联 AC | AC-4.4,AC-4.5,AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| widthVp | number | 是 | — | 有限且 >0（否则跳过） |
| breakpoint | Breakpoint | 是 | SM（回落） | XS/SM/MD/LG/XL 之一 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | widthVp=320 | 返回 SM | AC-1.4 |
| 2 | widthVp=600 | 返回 MD | AC-1.5 |
| 3 | widthVp=840 | 返回 LG | AC-1.6 |
| 4 | widthVp=1440 | 返回 XL | AC-1.7 |
| 5 | widthVp=NaN/0/-1 | 跳过 | AC-2.4 |
| 6 | breakpoint 与当前相同 | 跳过下发 | AC-2.2 |
| 7 | breakpoint=5（非法） | 回落 SM | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** OpenHarmony API Version 20（多设备自适应为鸿蒙扩展协议新增能力）。
- **API 版本号策略:** 断点接口为 internal，不标注 `@since`；公开 `Breakpoint` 枚举随扩展协议引入。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 断点接口不对外 | 仅 `SurfaceControllerImpl` 内部 + 承载组件驱动，宿主不直接调用 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |
| 双端阈值一致 | ArkTS `BreakpointUtils` 与 C++ `ResolveBreakpointFromWidth` 阈值同步 | AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7 |
| 无变化短路 | `updateBreakpoint` 档位相同跳过，避免重复下发 | AC-2.2 |
| 非法回落 SM | native 非法断点与 themeContext 缺省均回落 SM | AC-4.1,AC-5.3,AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 width/breakpoint 不抛异常，统一跳过或回落 | ArkTS/C++ 单测 | `SurfaceControllerImpl.ets:1193-1199`、`NativeEntry.cpp:2219-2221` |
| 性能 | 断点无变化短路，避免重复 native 调用 | ArkTS 单测 | `SurfaceControllerImpl.ets:1182-1185` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 竖屏通常落入 sm/md | 阈值一致 | ohosTest | `BreakpointUtils.ets:19-33` |
| 平板 | 横竖屏落入 md/lg | 阈值一致 | ohosTest | 同上 |
| 折叠屏 | 展开/折叠动态切换断点 | onSizeChange 驱动 | ohosTest | `UIRendererComponentCore.ets:279-282` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 断点判定不涉及 | — |
| 大字体 | 否 | 字体缩放见 Feat-02 | — |
| 深色模式 | 是 | 与 `__colorMode` 同构传播（`SurfaceManager::UpdateThemeMode`） | 设计 ADR-3 |
| 多窗口/分屏 | 是 | 分屏尺寸变化触发断点重算 | AC-3.1 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 20 起扩展协议能力 | 兼容性「最低支持版本」 |
| 生态兼容 | 是 | 鸿蒙扩展协议 `ohos.a2ui.extended.catalog` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 响应式断点
  作为 生成式 UI 宿主开发者
  我想要 容器宽度变化自动重算断点档位
  以便 同一 DSL 自适应不同屏幕

  Scenario: 断点去重短路
    Given 控制器 currentBreakpoint=SM
    When 调用 updateBreakpoint(SM)
    Then 跳过下发并打 updateBreakpoint skipped 日志

  Scenario: 断点变化下发
    Given 控制器 currentBreakpoint=SM
    When 调用 updateBreakpointByWidth(900)
    Then 解析为 LG，更新 currentBreakpoint 并 NAPI 下发

  Scenario Outline: 阈值边界映射
    Given 调用 resolveBreakpoint(<width>)
    When 宽度落入对应区间
    Then 返回 <breakpoint>

    Examples:
      | width | breakpoint |
      | 319   | XS         |
      | 320   | SM         |
      | 600   | MD         |
      | 840   | LG         |
      | 1440  | XL         |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做断点枚举/阈值/驱动/传播；单位解析见 Feat-02，条件重渲染见 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "BreakpointUtils resolveBreakpoint 阈值 320 600 840 1440 Breakpoint 枚举"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceControllerImpl updateBreakpoint updateBreakpointByWidth currentBreakpoint 去重"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceManager UpdateBreakpoint NotifyGlobalExpressionVariableChanged __widthBreakpoint 双通道"
  - repo: "GenerativeUI/A2UIRender"
    query: "ResolveBreakpointValue NativeEntry UpdateBreakpoint 回落 SM"
  - repo: "GenerativeUI/A2UIRender"
    query: "EvaluationContext ResolveVariable __widthBreakpoint BreakpointToString xs sm md lg xl"
```

**关键文档：** `genui/src/main/ets/core/common/BreakpointUtils.ets`、`genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/cpp/SurfaceManager.cpp`、`genui/src/main/cpp/theme/ThemeBase.h`、`genui/src/main/cpp/NativeEntry.cpp`、`genui/src/main/cpp/expression/EvaluationContext.cpp`