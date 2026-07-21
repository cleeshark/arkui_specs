# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | promptAction 全量规格（showToast / openToast / closeToast + ShowToastOptions） |
| 特性编号 | Func-05-06-10-Feat-01 |
| FuncID | 05-06-10 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 9 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 9 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | promptAction.showToast(options) | @since 9，命令式 Toast 显示 API |
| ADDED | ShowToastOptions.message / duration / bottom | @since 9，基础属性 |
| ADDED | UIContext.getPromptAction().showToast() | @since 10，实例化 API |
| ADDED | ShowToastOptions.showMode（DEFAULT / TOP_MOST / SYSTEM_TOP_MOST） | @since 11 |
| ADDED | ShowToastOptions.alignment / offset / backgroundColor / textColor / backgroundBlurStyle / shadow | @since 12 |
| ADDED | ShowToastOptions.enableHoverMode / hoverModeArea | @since 14 |
| MODIFIED | promptAction.showToast(options) | @since 18 标记废弃，建议使用 UIContext.getPromptAction().showToast |
| ADDED | promptAction.openToast(options): Promise\<number\> | @since 18，返回 toastId |
| ADDED | promptAction.closeToast(toastId, showMode?) | @since 18，精确关闭 |
| ADDED | ShowToastOptions.systemMaterial | @since 26 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/10-prompt-action/design.md`
- **KB 路由**: `docs/kb/components/overlay/toast.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@ohos.promptAction.d.ts`
  - Dynamic (UIContext): `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础 Toast 显示

**角色**: 应用开发者
**期望**: 我想要通过命令式 API 显示一条简短消息提示
**价值**: 以便在不阻塞用户操作的情况下反馈操作结果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `promptAction.showToast({ message: 'Hello' })` THEN 创建 Toast FrameNode 并挂载到 overlay 层，Toast 显示指定消息（`overlay_manager.cpp:579-610`） | 正常 |
| AC-1.2 | WHEN showToast 未设置 duration THEN 使用默认值 1500ms（`toast_layout_property.h:32`） | 正常 |
| AC-1.3 | WHEN showToast 未设置 bottom THEN 使用默认值 80vp（`toast_layout_property.h:33`） | 正常 |
| AC-1.4 | WHEN showToast 调用时 toastMap_ 中已有 Toast THEN 先清除所有已有 Toast 再显示新 Toast（`overlay_manager.cpp:589-593`） | 正常 |

### US-2: Toast 动画

**角色**: 终端用户
**期望**: 我想要 Toast 显示时有平滑的淡入淡出动画
**价值**: 以便获得自然的视觉过渡体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Toast 开始显示 THEN 使用 CubicCurve(0.2, 0, 0.1, 1.0) 执行 opacity 0→1 + translate Y 动画（`overlay_manager.cpp:666, 660-690`） | 正常 |
| AC-2.2 | WHEN Toast duration 到期 THEN 触发 PopToast 执行退出动画（opacity 1→0）（`overlay_manager.cpp:712-718`） | 正常 |
| AC-2.3 | WHEN PopToast 退出动画完成 THEN 从 toastMap_ 中 erase 对应 toastId（`overlay_manager.cpp:739`） | 正常 |

### US-3: openToast / closeToast 精确管理

**角色**: 应用开发者
**期望**: 我想要通过 openToast 获取 toastId 并精确关闭指定 Toast
**价值**: 以便在多 Toast 场景下精确控制每条 Toast 的生命周期

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `promptAction.openToast({ message: 'Hello' })` THEN 返回 Promise\<number\>，resolve 为编码后的 toastId（`prompt_action.cpp:568, 602`） | 正常 |
| AC-3.2 | WHEN 调用 `promptAction.closeToast(toastId)` THEN 查找 toastMap_ 并执行 PopToast 关闭指定 Toast（`overlay_manager.cpp:620, 633-655`） | 正常 |
| AC-3.3 | WHEN openToast 时 toastMap_ 中已有 Toast THEN 不清除已有 Toast，支持多 Toast 共存（API 18+ 行为） | 正常 |
| AC-3.4 | WHEN closeToast 的 toastId 经解码为 `(toastId << 3) \| (showMode & 0b111)` THEN 高 29 位为 FrameNode ID，低 3 位为 showMode（`overlay_manager.cpp:606-607`） | 正常 |
| AC-3.5 | WHEN closeToast 传入不存在的 toastId THEN toastMap_.find 返回 end，不执行任何操作（`overlay_manager.cpp:633-634`） | 异常 |
| AC-3.6 | WHEN closeToast 传入 toastId < 0 THEN 返回参数错误，不执行关闭（`prompt_action.cpp:669`） | 异常 |

### US-4: ShowToastOptions 全属性

**角色**: 应用开发者
**期望**: 我想要自定义 Toast 的位置、颜色、背景模糊和阴影
**价值**: 以便匹配应用的设计语言和布局需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `alignment: Alignment.CENTER` THEN Toast 按指定对齐方式定位（`toast_view.cpp:64`） | 正常 |
| AC-4.2 | WHEN 设置 `offset: { dx: 10, dy: 20 }` THEN Toast 在 alignment 基础上叠加偏移（`toast_view.cpp:70-71`） | 正常 |
| AC-4.3 | WHEN 设置 `backgroundColor: Color.Red` THEN Toast 背景色为红色，覆盖默认主题色（`toast_view.cpp:342`） | 正常 |
| AC-4.4 | WHEN 设置 `textColor: Color.White` THEN Toast 文字颜色为白色（`toast_view.cpp:116`） | 正常 |
| AC-4.5 | WHEN 设置 `backgroundBlurStyle: BlurStyle.COMPONENT_ULTRA_THICK` THEN 应用对应模糊效果，默认为 COMPONENT_ULTRA_THICK（`toast_layout_property.h:40`） | 正常 |
| AC-4.6 | WHEN 设置 `shadow: ShadowType.OUTER_DEFAULT_MD` THEN 应用默认阴影，未设置时使用 OUTER_DEFAULT_MD（`toast_layout_property.h:41`） | 正常 |
| AC-4.7 | WHEN 未设置 backgroundColor/textColor/backgroundBlurStyle/shadow THEN 使用 ToastTheme 默认值（`toast_view.cpp:241-243`） | 正常 |

### US-5: showMode 窗口层级

**角色**: 应用开发者
**期望**: 我想要控制 Toast 在不同窗口层级显示
**价值**: 以便在跨窗口或系统级场景下确保 Toast 可见

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN showMode = DEFAULT THEN Toast 挂载到当前页面的 overlay 节点（`overlay_manager.cpp:611`） | 正常 |
| AC-5.2 | WHEN showMode = TOP_MOST THEN Toast 挂载到顶层窗口的 overlay 节点（`overlay_manager.cpp:613`） | 正常 |
| AC-5.3 | WHEN showMode = SYSTEM_TOP_MOST THEN Toast 挂载到系统顶层窗口的 overlay 节点（`overlay_manager.cpp:615`） | 正常 |
| AC-5.4 | WHEN showMode 值不在 [0, 2] 范围 THEN 取 DEFAULT（`prompt_action.cpp:176-177`） | 边界 |

### US-6: duration 边界

**角色**: 应用开发者
**期望**: 我想要了解 Toast 显示时长的有效范围
**价值**: 以便设置合理的显示时间

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN duration = 1500 THEN Toast 显示 1500ms 后自动关闭 | 边界 |
| AC-6.2 | WHEN duration = 10000 THEN Toast 显示 10000ms 后自动关闭 | 边界 |
| AC-6.3 | WHEN duration < 1500 THEN 取 1500ms | 边界 |
| AC-6.4 | WHEN duration > 10000 THEN 取 10000ms | 边界 |
| AC-6.5 | WHEN duration 未设置 THEN 使用默认值 1500ms（`toast_layout_property.h:32`） | 正常 |

### US-7: 折叠屏适配

**角色**: 应用开发者
**期望**: 我想要在折叠屏设备上适配 Toast 显示位置
**价值**: 以便 Toast 在折叠屏展开/折叠时显示在合适的区域

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 `enableHoverMode: true` THEN Toast 启用折叠屏悬停模式适配（`toast_layout_property.h:42`） | 正常 |
| AC-7.2 | WHEN 设置 `enableHoverMode: true` 且未设置 hoverModeArea THEN 使用默认值 BOTTOM_SCREEN（`toast_layout_property.h:43`） | 正常 |
| AC-7.3 | WHEN 设置 `hoverModeArea: HoverModeAreaType.TOP_SCREEN` THEN Toast 在折叠屏上半屏区域显示 | 正常 |
| AC-7.4 | WHEN enableHoverMode = false THEN Toast 不进行折叠屏适配，按常规布局显示 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3 | TASK-PROMPT-ACTION-01 | UT | `test/unittest/core/pattern/overlay/overlay_manager_toast_test_ng.cpp` |
| AC-2.1 ~ AC-2.3 | R-4, R-5 | TASK-PROMPT-ACTION-01 | UT + 手工 | Toast 动画测试 |
| AC-3.1 ~ AC-3.6 | R-6, R-7, R-8 | TASK-PROMPT-ACTION-01 | UT | openToast/closeToast 测试 |
| AC-4.1 ~ AC-4.7 | R-9, R-10 | TASK-PROMPT-ACTION-01 | UT | ShowToastOptions 属性测试 |
| AC-5.1 ~ AC-5.4 | R-11 | TASK-PROMPT-ACTION-01 | UT | showMode 分发测试 |
| AC-6.1 ~ AC-6.5 | R-12 | TASK-PROMPT-ACTION-01 | UT | duration 边界测试 |
| AC-7.1 ~ AC-7.4 | R-13 | TASK-PROMPT-ACTION-01 | 手工 | 折叠屏适配验证 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `overlay_manager.cpp:579-610` | ShowToast 创建 Toast FrameNode，挂载到 overlay 层，注册到 toastMap_ | — | AC-1.1 |
| R-2 | 行为 | `toast_layout_property.h:32` | duration 默认值 1500ms | 范围 [1500, 10000] | AC-1.2 |
| R-3 | 行为 | `overlay_manager.cpp:589-593` | ShowToast 先清除 toastMap_ 中所有已有 Toast 再显示新 Toast（API 9~17 单 Toast 策略） | — | AC-1.4 |
| R-4 | 行为 | `overlay_manager.cpp:660-690` | OpenToastAnimation 使用 CubicCurve(0.2, 0, 0.1, 1.0)，opacity 0→1 + translate Y | — | AC-2.1 |
| R-5 | 行为 | `overlay_manager.cpp:712-739` | PopToast 执行退出动画，完成后 toastMap_.erase(toastId) | — | AC-2.2, AC-2.3 |
| R-6 | 行为 | `prompt_action.cpp:568, 602` | openToast 返回 Promise\<number\>，resolve 为编码 toastId = (toastId << 3) \| (showMode & 0b111) | — | AC-3.1 |
| R-7 | 行为 | `overlay_manager.cpp:620, 633-655` | closeToast 查找 toastMap_ 并执行 PopToast 关闭指定 Toast | — | AC-3.2 |
| R-8 | 行为 | `overlay_manager.cpp:606-607` | toastId 编码：高 29 位为 FrameNode ID，低 3 位为 showMode | showMode 范围 0~2 | AC-3.4 |
| R-9 | 行为 | `toast_view.cpp:64, 70-71, 116, 342` | ShowToastOptions 的 alignment/offset/textColor/backgroundColor 解析并更新到 ToastLayoutProperty 和 RenderContext | — | AC-4.1 ~ AC-4.4 |
| R-10 | 行为 | `toast_view.cpp:241-243, toast_layout_property.h:40-41` | backgroundBlurStyle 默认 COMPONENT_ULTRA_THICK，shadow 默认 OUTER_DEFAULT_MD，未设置时使用 ToastTheme 默认值 | — | AC-4.5 ~ AC-4.7 |
| R-11 | 行为 | `overlay_manager.cpp:611-615` | showMode 分发：DEFAULT→当前页面 overlay，TOP_MOST→顶层窗口 overlay，SYSTEM_TOP_MOST→系统顶层窗口 overlay | showMode ∈ {0,1,2} | AC-5.1 ~ AC-5.4 |
| R-12 | 边界 | `prompt_action.cpp` | duration 范围 [1500, 10000]ms，超出范围截断到边界值 | =1500 最小，=10000 最大 | AC-6.1 ~ AC-6.5 |
| R-13 | 行为 | `toast_layout_property.h:42-43` | enableHoverMode 启用折叠屏适配，hoverModeArea 默认 BOTTOM_SCREEN | — | AC-7.1 ~ AC-7.4 |
| R-14 | 异常 | `overlay_manager.cpp:633-634` | closeToast 传入不存在的 toastId，toastMap_.find 返回 end，不执行操作 | — | AC-3.5 |
| R-15 | 异常 | `prompt_action.cpp:669` | closeToast 传入 toastId < 0 或 showMode 越界，返回参数错误 | toastId ≥ 0, showMode ∈ [0,2] | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | showToast 基础流程和单 Toast 策略 |
| VM-2 | AC-2.1 ~ AC-2.3 | UT + 手工 | 进入/退出动画曲线和 toastMap_ 清理 |
| VM-3 | AC-3.1 ~ AC-3.6 | UT | openToast 返回 toastId、closeToast 精确关闭、异常参数处理 |
| VM-4 | AC-4.1 ~ AC-4.7 | UT | ShowToastOptions 全属性解析和默认值 |
| VM-5 | AC-5.1 ~ AC-5.4 | UT | showMode 分发和越界处理 |
| VM-6 | AC-6.1 ~ AC-6.5 | UT | duration 边界截断 |
| VM-7 | AC-7.1 ~ AC-7.4 | 手工 | 折叠屏 enableHoverMode 适配 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `promptAction.showToast(options: ShowToastOptions)` | Public | ShowToastOptions | void | N/A | 显示 Toast 消息提示 | AC-1.1 ~ AC-1.4 | @since 9, @deprecated 18 |
| `promptAction.openToast(options: ShowToastOptions)` | Public | ShowToastOptions | Promise\<number\> | N/A | 显示 Toast 并返回 toastId | AC-3.1, AC-3.3 | @since 18 |
| `promptAction.closeToast(toastId: number, showMode?: ToastShowMode)` | Public | toastId, showMode | void | N/A | 关闭指定 toastId 的 Toast | AC-3.2, AC-3.5, AC-3.6 | @since 18 |
| `UIContext.getPromptAction().showToast(options)` | Public | ShowToastOptions | void | N/A | UIContext 实例化 showToast | AC-1.1 | @since 10 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `promptAction.showToast(options)` | 废弃 | @since 18 废弃 | 使用 `promptAction.openToast(options)` 替代，openToast 返回 toastId 可精确关闭 | AC-1.1 |

> SDK 声明见 `<OH_ROOT>/interface/sdk-js/api/@ohos.promptAction.d.ts` 和 `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`。

## 接口规格

### 接口定义

**promptAction.showToast**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static showToast(options: ShowToastOptions): void` |
| 返回值 | `void` — 无返回值 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| message | string | 是 | — | Toast 消息内容 |
| duration | number | 否 | 1500 | 范围 [1500, 10000] ms |
| bottom | string \| Resource | 否 | 80vp | Toast 底部偏移 |
| showMode | ToastShowMode | 否 | DEFAULT | 0=DEFAULT, 1=TOP_MOST, 2=SYSTEM_TOP_MOST |
| alignment | Alignment | 否 | BOTTOM_CENTER | Toast 对齐方式 |
| offset | Offset | 否 | {0, 0} | 在 alignment 基础上的偏移 |
| backgroundColor | ResourceColor | 否 | ToastTheme 默认 | Toast 背景色 |
| textColor | ResourceColor | 否 | ToastTheme 默认 | Toast 文字色 |
| backgroundBlurStyle | BlurStyle | 否 | COMPONENT_ULTRA_THICK | 背景模糊效果 |
| shadow | Shadow | 否 | OUTER_DEFAULT_MD | Toast 阴影 |
| enableHoverMode | boolean | 否 | false | 折叠屏悬停模式 |
| hoverModeArea | HoverModeAreaType | 否 | BOTTOM_SCREEN | 折叠屏区域 |
| systemMaterial | SystemUiMaterial | 否 | — | 系统材质 (@since 26) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 showToast({ message: 'Hello' }) | 创建 Toast 节点并显示，1500ms 后自动关闭 | AC-1.1, AC-1.2 |
| 2 | 调用时已有 Toast 显示 | 先清除已有 Toast 再显示新 Toast | AC-1.4 |
| 3 | duration = 500 | 截断为 1500ms | AC-6.3 |

---

**promptAction.openToast**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static openToast(options: ShowToastOptions): Promise<number>` |
| 返回值 | `Promise<number>` — resolve 为编码 toastId |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 openToast({ message: 'Hello' }) | 显示 Toast 并返回 toastId | AC-3.1 |
| 2 | 调用时已有 Toast 显示 | 不清除已有 Toast，支持多 Toast 共存 | AC-3.3 |

---

**promptAction.closeToast**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static closeToast(toastId: number, showMode?: ToastShowMode): void` |
| 返回值 | `void` — 无返回值 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.2, AC-3.5, AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| toastId | number | 是 | — | openToast 返回的 toastId，≥ 0 |
| showMode | ToastShowMode | 否 | DEFAULT | 需与 openToast 时的 showMode 一致 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 closeToast(validToastId) | 查找并关闭指定 Toast | AC-3.2 |
| 2 | toastId 不存在于 toastMap_ | 不执行任何操作 | AC-3.5 |
| 3 | toastId < 0 | 返回参数错误 | AC-3.6 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 18: `showToast` 废弃，引入 `openToast` / `closeToast` 支持多 Toast 和精确关闭
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 基础 API @since 9，UIContext 实例化 @since 10，showMode @since 11，alignment/offset/colors/blurStyle/shadow @since 12，enableHoverMode @since 14，openToast/closeToast @since 18，systemMaterial @since 26

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 命令式 API 路径 | Toast 无 JSView/Bridge 层，通过 NAPI → OverlayManager → ToastPattern 管理节点 | AC-1.1 |
| 单 Toast 策略（API 9~17） | ShowToast 先清除已有 Toast，同一时刻仅显示一个 Toast | AC-1.4 |
| toastId 编码 | (toastId << 3) \| (showMode & 0b111)，低 3 位存 showMode | AC-3.4 |
| 无组件化 | Toast 无独立 SO，随 ace_engine 主工程编译，无 C API | — |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Toast 显示动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | Toast 关闭后 toastMap_ 正确清理，无泄漏 | UT | toastMap_ size 验证 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | 多 Toast 场景下 toastId 精确管理，无误关闭 | UT | closeToast 测试 |
| 问题定位 | hilog 标签 ACE_OVERLAY / ACE_DIALOG 覆盖关键路径 | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | enableHoverMode = true 时适配折叠屏区域 | hoverModeArea 指定上/下半屏 | 手工 | AC-7.1 ~ AC-7.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | Toast 为瞬态提示，无无障碍属性 | — |
| 大字体 | 是 | Toast 文字大小跟随系统字体缩放 | AC-4.7 |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随 | AC-4.3, AC-4.4 |
| 多窗口/分屏 | 是 | showMode 支持跨窗口显示（TOP_MOST / SYSTEM_TOP_MOST） | AC-5.1 ~ AC-5.4 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 18 废弃 showToast，引入 openToast/closeToast | AC-3.1 ~ AC-3.6 |
| 生态兼容 | 否 | 无 C API | — |

## 行为场景（Gherkin）

```gherkin
Feature: promptAction Toast
  作为应用开发者
  我想要通过命令式 API 显示和管理 Toast 消息提示
  以便在不阻塞用户操作的情况下反馈操作结果

  Scenario: 基础 Toast 显示
    Given 应用调用 showToast({ message: 'Hello', duration: 2000 })
    When OverlayManager::ShowToast 执行
    Then 先清除 toastMap_ 中已有 Toast
    And 创建新 Toast FrameNode 并挂载到 overlay 层
    And 使用 CubicCurve(0.2, 0, 0.1, 1.0) 执行进入动画
    And 2000ms 后触发 PopToast 退出动画
    And 动画完成后 toastMap_.erase(toastId)

  Scenario: openToast 返回 toastId
    Given 应用调用 openToast({ message: 'Hello' })
    When Toast 节点创建完成
    Then Promise resolve 返回编码 toastId = (nodeId << 3) | (showMode & 0b111)
    And 不清除已有 Toast

  Scenario: closeToast 精确关闭
    Given 应用持有 openToast 返回的 toastId
    When 应用调用 closeToast(toastId)
    Then OverlayManager::CloseToast 查找 toastMap_
    And 找到对应节点后执行 PopToast
    And toastMap_.erase(toastId)

  Scenario: closeToast 不存在的 toastId
    Given 应用传入不存在的 toastId
    When OverlayManager::CloseToast 查找 toastMap_
    Then toastMap_.find 返回 end
    And 不执行任何操作

  Scenario Outline: duration 边界截断
    Given 应用调用 showToast({ message: 'test', duration: <input> })
    When duration 参数处理
    Then 实际显示时长为 <actual> ms

    Examples:
      | input | actual |
      | 500   | 1500   |
      | 1500  | 1500   |
      | 5000  | 5000   |
      | 10000 | 10000  |
      | 20000 | 10000  |

  Scenario: showMode 系统顶层窗口
    Given 应用调用 showToast({ message: 'Hello', showMode: SYSTEM_TOP_MOST })
    When ShowToast 执行
    Then Toast 挂载到系统顶层窗口的 overlay 节点

  Scenario Outline: showMode 越界处理
    Given 应用调用 showToast({ message: 'test', showMode: <mode> })
    When showMode 参数处理
    Then 使用 <actual> 模式

    Examples:
      | mode | actual   |
      | -1   | DEFAULT  |
      | 3    | DEFAULT  |
      | 0    | DEFAULT  |
      | 1    | TOP_MOST |
      | 2    | SYSTEM_TOP_MOST |

  Scenario: 折叠屏悬停模式
    Given 折叠屏设备，应用调用 showToast({ message: 'Hello', enableHoverMode: true, hoverModeArea: TOP_SCREEN })
    When Toast 布局计算
    Then Toast 显示在折叠屏上半屏区域
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
  - repo: "openharmony/ace_engine"
    query: "OverlayManager::ShowToast 单 Toast 策略和 toastMap_ 管理"
  - repo: "openharmony/ace_engine"
    query: "toastId 编码方案 (toastId << 3) | (showMode & 0b111)"
  - repo: "openharmony/ace_engine"
    query: "ToastView::CreateToastNode 节点创建和属性设置"
  - repo: "openharmony/ace_engine"
    query: "OverlayManager::OpenToastAnimation / PopToast 动画曲线"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.promptAction.d.ts`
- KB 路由: `docs/kb/components/overlay/toast.md`
- 源码入口: `interfaces/napi/kits/promptaction/prompt_action.cpp`, `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp`
