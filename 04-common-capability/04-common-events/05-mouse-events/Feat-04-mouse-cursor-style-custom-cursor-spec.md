# 特性规格

> Func-04-04-05-Feat-04 鼠标光标样式与自定义光标：固化 ArkUI 光标控制从 Dynamic/Static API、窗口级状态仲裁、VSync 提交到 OHOS MMI 平台适配的现有行为。

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 鼠标光标样式与自定义光标 |
| 特性编号 | Func-04-04-05-Feat-04 |
| 所属 Epic | 通用能力层 / 通用事件 / 鼠标事件 |
| 优先级 | P1 |
| 目标版本 | API 26 存量能力补录 |
| SIG 归属 | SIG_ApplicationFramework / ArkUI |
| 状态 | Baselined |
| 复杂度 | L2（复杂） |

本特性覆盖全局 `cursorControl`、绑定 UIContext 的 `CursorController`、`PointerStyle` 版本和值域、API 26 自定义 PixelMap 光标、用户与组件内部光标优先级、hold-node、VSync 仲裁、失焦与销毁恢复、普通窗口/UIExtension/Previewer 平台差异，以及与 InputKit、Hover、Web、Drag 和 Node C-API 的责任边界。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Feat-04 存量规格 | 补录鼠标系统样式、自定义光标和窗口级状态机 |
| ADDED | API 11/12/23/26 版本矩阵 | 分别描述 Dynamic 全局、Dynamic UIContext、Static 和自定义光标 |
| ADDED | 平台兼容与实现偏差 | 记录 UIExtension token、Previewer、Static no-op 和热点边界差异 |
| MODIFIED | 共享鼠标事件设计 | 将光标样式内容增量合入现有 `design.md`，不新建 Feat 顶级章节 |
| REMOVED | 无 | 不删除或修改产品 API、ABI、错误码和实现 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| 共享设计 | `specs/04-common-capability/04-common-events/05-mouse-events/design.md` | 存量增量合并 |
| Dynamic 全局 SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:7444-7493` | 已核对 |
| Dynamic UIContext SDK | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts:3836-3908,5720-5730` | 已核对 |
| Static 全局 SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:3239-3274` | 已核对 |
| Static UIContext SDK | `interface/sdk-js/api/@ohos.arkui.UIContext.static.d.ets:2903-2953,4152-4160` | 已核对 |
| PointerStyle/InputKit SDK | `interface/sdk-js/api/@ohos.multimodalInput.pointer.d.ts:25-537,770-904,1824-1892` | 已核对 |
| 核心状态模型 | `frameworks/base/mousestyle/mouse_style.h:27-209`、`mouse_style.cpp:26-140` | 已核对 |
| Pipeline 与生命周期 | `frameworks/core/pipeline_ng/pipeline_context.cpp:5408-5419,5788-5795,6816-6844` | 已核对 |
| OHOS 平台适配 | `adapter/ohos/osal/mouse_style_ohos.cpp:31-150,198-233` | 已核对 |

## 用户故事

### US-1: 按 API 版本选择光标控制入口

**作为** ArkUI 应用开发者，**我想要** 使用目标 API 版本支持的全局或 UIContext 光标接口，**以便** 在正确实例和窗口中设置光标。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Dynamic 应用目标 API >= 11 调用 `cursorControl.setCursor/restoreDefault` THEN 全局入口可用；目标 API < 11 时不属于公开契约 | 边界 |
| AC-1.2 | WHEN Dynamic 应用目标 API >= 12 调用 `UIContext.getCursorController()` THEN 返回绑定该 instance ID 的缓存控制器，可调用 set/restore；目标 API < 12 时不属于公开契约 | 边界 |
| AC-1.3 | WHEN Static 应用目标 API >= 23 使用全局 `cursorControl` 或 `CursorController` THEN SDK 声明相应 set/restore 接口 | 正常 |
| AC-1.4 | WHEN Dynamic 或 Static 应用目标 API >= 26 调用 `CursorController.setCustomCursor` THEN 可提供 PixelMap 与可选热点；API < 26 时 ArkUI UIContext 不公开该接口 | 边界 |
| AC-1.5 | WHEN `setCursor` 接收 `PointerStyle` THEN 公开内建值域按 API 9/10/18/20/22 演进解释；`DEVELOPER_DEFINED_ICON=-100` 和空鼠专用样式不得被假定为普通可设置样式 | 边界 |

### US-2: 在渲染帧中确定最终光标样式

**作为** ArkUI 框架维护者，**我想要** 在 VSync 中统一仲裁光标请求，**以便** 同帧多个来源得到确定结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 有效系统样式或自定义光标请求进入 Pipeline THEN 请求入队并触发 RequestFrame，平台样式在下一次光标请求 flush 中应用，而非在公开 API 返回前立即应用 | 正常 |
| AC-2.2 | WHEN 同一帧存在不同原因的请求 THEN 按 `INNER < USER < CONTAINER_DESTROY < WINDOW_LOST_FOCUS < WINDOW_SCENE_LOST_FOCUS` 选择最高优先级请求 | 正常 |
| AC-2.3 | WHEN 同一帧存在多个相同原因请求 THEN 后加入的请求覆盖先加入请求 | 边界 |
| AC-2.4 | WHEN 仲裁后的系统样式或自定义 PixelMap 指针及热点与上一已应用值相同 THEN 不重复调用平台设置接口 | 正常 |
| AC-2.5 | WHEN Manager 接受请求但平台 container、InputManager、token、PixelMap 缺失或 MMI 返回失败 THEN ArkUI `void` API不返回错误，平台失败仅通过日志可见 | 异常 |

### US-3: 协调用户设置与组件内部样式

**作为** 组件和应用开发者，**我想要** 用户显式设置优先于组件自动光标，**以便** 光标不会被内部 Hover 行为意外覆盖。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `userSetCursor_` 为 true 且组件提交 `INNER_SET_MOUSESTYLE` THEN Manager 拒绝该内部请求 | 正常 |
| AC-3.2 | WHEN 组件提交内部请求 THEN 仅在 node ID 等于当前唯一 hold-node 时接受；未持有或 ID 不匹配时拒绝 | 边界 |
| AC-3.3 | WHEN 一个节点已占用 hold-node THEN 另一节点申请失败；仅相同 ID 或无参释放成功后才可重新占用 | 边界 |
| AC-3.4 | WHEN 用户调用 `restoreDefault()` THEN DEFAULT 请求按用户原因入队并清除用户覆盖标志，使后续合法内部请求可再次参与仲裁 | 恢复 |
| AC-3.5 | WHEN 内部调用以 `isByPass=true` 提交光标请求 THEN Manager 直接拒绝且不改变待处理样式 | 异常 |

### US-4: 设置 PixelMap 自定义光标

**作为** ArkUI 应用开发者，**我想要** 使用 PixelMap 和热点设置自定义光标，**以便** 点击位置与自定义图形对齐。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN `focusX/focusY` 省略或不是可转换数字 THEN 当前入口分别使用 0 作为默认热点坐标 | 正常 |
| AC-4.2 | WHEN 热点为负数 THEN Dynamic/Static 均将对应坐标回退为 0；WHEN 热点等于 PixelMap 宽/高 THEN Dynamic 当前保留该值而 Static 回退为 0 | 边界 |
| AC-4.3 | WHEN PixelMap 转换失败、为空或 Pipeline 收到空 PixelMap THEN 记录日志或直接返回，不入队自定义光标且不抛出 ArkUI BusinessError | 异常 |
| AC-4.4 | WHEN 连续自定义请求持有相同 PixelMap 像素指针且热点相同 THEN Manager 视为未变化；PixelMap 内容相同但像素指针不同不满足该相等条件 | 边界 |
| AC-4.5 | WHEN OHOS MMI 成功应用自定义光标 THEN 平台调用 `SetPointerVisible(true)`；MMI 失败时不执行该可见性设置 | 正常 |

### US-5: 在窗口和容器生命周期中恢复光标

**作为** 多窗口或 UIExtension 应用开发者，**我想要** 光标在失焦和销毁时恢复并使用正确窗口身份，**以便** 不把一个窗口的光标状态泄漏到其他窗口。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN Pipeline 窗口失焦 THEN 以 `WINDOW_LOST_FOCUS_RESET_MOUSESTYLE` 提交 DEFAULT 请求，该请求优先级高于用户设置 | 恢复 |
| AC-5.2 | WHEN WindowScene 失焦 THEN 以 session persistent ID 和最高原因优先级提交 DEFAULT 请求 | 恢复 |
| AC-5.3 | WHEN容器销毁且当前已应用样式不是 DEFAULT THEN 提交容器销毁恢复请求并在 `ClearResults` 中立即 flush；当前样式为 DEFAULT 时不提交该恢复请求 | 恢复 |
| AC-5.4 | WHEN OHOS 普通窗口应用系统/自定义光标 THEN 调用无 token 的 MMI 重载；WHEN UIExtension 应用光标 THEN 获取窗口 token 并调用带 token 重载 | 正常 |
| AC-5.5 | WHEN UIExtension token 为空或 MMI 调用失败 THEN 不继续应用光标，ArkUI 调用方不接收错误回调 | 异常 |
| AC-5.6 | WHEN Previewer 调用系统光标接口 THEN 当前适配层记录“不支持”并表面返回成功；自定义光标继承空实现，不产生可见效果 | 边界 |

### US-6: 明确跨模块和其他光标链路边界

**作为** 规格和平台维护者，**我想要** 区分 ArkUI 光标状态与 InputKit、Hover、Web、Drag、Native 接口，**以便** 避免错误归属和跨通道假设。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN 文档引用 InputKit `set/getPointerStyle` 或自定义光标接口 THEN 仅把它作为 `PointerStyle` 来源和平台责任边界，不把其 Promise、回调、401/202/26500001 错误码写成 ArkUI `void` API 行为 | 边界 |
| AC-6.2 | WHEN 检查 Node C-API/NDK 光标样式能力 THEN 明确记录“Node C-API/NDK 鼠标光标样式接口在 ace_engine 中未实现” | 边界 |
| AC-6.3 | WHEN Web 或 Drag 修改光标 THEN 分别沿 Web 平台直通链和 DragCursorStyleCore 链处理，不要求进入本 Feat 的普通 MouseStyleManager 用户/hold 仲裁 | 边界 |
| AC-6.4 | WHEN Static `CursorController.setCursor` 按当前 checked-in 源码执行 THEN 只同步并恢复 instance ID，未调用实际 setter；该 SDK/源码偏差作为风险保留 | 异常 |
| AC-6.5 | WHEN 开发者在 `onHover` 中调用光标 API THEN Hover 仅作为触发来源；Hover 命中、传播和视觉动画仍归 Feat-03 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | TASK-F4-1 | SDK 静态检查 | `common.d.ts:7444-7493`、`UIContext.d.ts:3836-3908`、Static 对应声明 |
| AC-1.5 | R-5 | TASK-F4-1 | SDK 枚举矩阵 + Pipeline UT | `pointer.d.ts:25-537`、`pipeline_context.cpp:6816-6835` |
| AC-2.1~AC-2.5 | R-6~R-10 | TASK-F4-1 | Manager/Pipeline Host UT | `mouse_style.cpp:62-140`、`pipeline_context.cpp:5408-5419` |
| AC-3.1~AC-3.5 | R-11~R-15 | TASK-F4-1 | MouseStyleManager UT | `mouse_style_manager_test_ng.cpp:45-461,578-652` |
| AC-4.1~AC-4.5 | R-16~R-20 | TASK-F4-1 | Dynamic/Static bridge + OHOS adapter UT | `jsi_view_register.cpp:1889-1937`、`iui_context_accessor.cpp:776-802` |
| AC-5.1~AC-5.6 | R-21~R-26 | TASK-F4-1 | 生命周期/Pipeline/平台集成测试 | `pipeline_context.cpp:5788-5795`、`pipeline_base.cpp:1136-1147`、`mouse_style_ohos.cpp:104-150,198-233` |
| AC-6.1~AC-6.5 | R-27~R-31 | TASK-F4-1 | 边界审查 + 源码追溯 | InputKit SDK、Static 实现、Web/Drag 源码 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 边界 | Dynamic 全局入口目标 API >= 11 | `cursorControl` set/restore 可用 | API < 11 不在契约内 | AC-1.1 |
| R-2 | 行为 | Dynamic UIContext 目标 API >= 12 | 缓存并返回绑定 instance ID 的 CursorController | 同一 UIContext 重复获取复用控制器 | AC-1.2 |
| R-3 | 边界 | Static 目标 API >= 23 | SDK 声明全局与实例 set/restore | 实现偏差由 R-30 单列 | AC-1.3 |
| R-4 | 边界 | Dynamic/Static 目标 API >= 26 | UIContext 公开 PixelMap 自定义光标 | API < 26 不开放 ArkUI 实例接口 | AC-1.4 |
| R-5 | 边界 | `setCursor` 输入整数样式 | Pipeline 仅接受 0..51 | -100、<0、>51 和内部 1001..1004 不入队 | AC-1.5 |
| R-6 | 行为 | 合法请求进入 Pipeline | 加入 Manager 请求队列并 RequestFrame | 公开 API返回不表示平台已应用 | AC-2.1 |
| R-7 | 行为 | 同帧不同 reason | 选择数值最高的 reason | 优先级 0..4 依次递增 | AC-2.2 |
| R-8 | 边界 | 同帧相同 reason 多请求 | 后到请求胜出 | 使用 `>=` 仲裁 | AC-2.3 |
| R-9 | 行为 | 最终样式等于上一应用值 | 清队列且不调用平台 setter | 自定义相等按指针和热点 | AC-2.4 |
| R-10 | 异常 | 平台前置对象缺失或 MMI 失败 | 记录日志并返回，不向 ArkUI void API传递错误 | 不套用 InputKit 错误码 | AC-2.5 |
| R-11 | 行为 | userSetCursor=true 且 reason=INNER | 拒绝请求 | 不影响 USER 或恢复 reason | AC-3.1 |
| R-12 | 边界 | 内部请求 nodeId 与 hold-node 比较 | 仅精确相等时接受 | hold 缺失或不匹配均拒绝 | AC-3.2 |
| R-13 | 边界 | hold-node 已占用 | 第二次申请失败 | 同 ID 释放或无参释放后可重占 | AC-3.3 |
| R-14 | 恢复 | 用户 restoreDefault | DEFAULT 入队并将 userSetCursor 设为 false | 仍按 VSync 生效 | AC-3.4 |
| R-15 | 异常 | isByPass=true | 立即拒绝 | 不写入请求队列 | AC-3.5 |
| R-16 | 行为 | 热点省略或不可转为数值 | focusX/focusY 使用 0 | 单位 px | AC-4.1 |
| R-17 | 边界 | 热点为 -1、0、size-1、size、size+1 | 负数回退 0；Dynamic 在 =size 时保留，Static 在 =size 时回退 0 | 分别按宽/高判断 | AC-4.2 |
| R-18 | 异常 | PixelMap 转换失败或为空 | 不提交自定义光标 | 日志/静默返回，无 ArkUI 异常 | AC-4.3 |
| R-19 | 边界 | 判断自定义光标是否变化 | 比较像素指针、focusX、focusY | 不比较整幅像素内容 | AC-4.4 |
| R-20 | 行为 | MMI SetCustomCursor 返回 0 | 设置 pointer visible=true | 非 0 时不设置可见性 | AC-4.5 |
| R-21 | 恢复 | Pipeline 窗口失焦 | 提交 DEFAULT，reason=3 | 优先于 INNER/USER/DESTROY | AC-5.1 |
| R-22 | 恢复 | WindowScene 失焦 | 使用 persistent ID 提交 DEFAULT，reason=4 | 当前最高优先级 | AC-5.2 |
| R-23 | 恢复 | 容器销毁且当前样式非 DEFAULT | reason=2 恢复并在 ClearResults flush | 当前样式为 DEFAULT 时跳过 | AC-5.3 |
| R-24 | 行为 | OHOS 平台判断 UIExtension | UIExtension 使用 token 重载，普通窗口使用无 token 重载 | 系统样式和 UEA custom 均分流 | AC-5.4 |
| R-25 | 异常 | UIExtension token=null 或 MMI 失败 | 停止应用并记录日志 | ArkUI 无回调/Promise | AC-5.5 |
| R-26 | 边界 | Previewer 设置系统或自定义光标 | 系统接口表面成功、自定义接口 no-op | 无可见平台效果 | AC-5.6 |
| R-27 | 边界 | 引用 InputKit 接口 | 仅记录类型来源和系统边界 | InputKit 的错误码不继承到 ArkUI | AC-6.1 |
| R-28 | 边界 | 查询 Node C-API/NDK | 标记未实现 | 不将 CJ FFI 当作 Node C-API | AC-6.2 |
| R-29 | 边界 | Web/Drag 修改光标 | 使用各自直通/拖拽状态链 | 不受普通 Manager 的 user/hold 规则约束 | AC-6.3 |
| R-30 | 异常 | Static 实例 CursorController.setCursor | 当前只切换 instance ID，未设置光标 | SDK 声明仍保留，列为实现风险 | AC-6.4 |
| R-31 | 边界 | Hover 回调调用光标 API | 触发 Feat-04 窗口级状态请求 | Hover 本身归 Feat-03 | AC-6.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4, R-1~R-4 | Dynamic/Static SDK 静态检查 | API 11/12/23/26 与签名 |
| VM-2 | AC-1.5, R-5 | PointerStyle 参数化 UT | 0、44、51、-100、52、1001 |
| VM-3 | AC-2.1~AC-2.4, R-6~R-9 | MouseStyleManager Host UT | 下一帧、reason 顺序、同级后到、去重 |
| VM-4 | AC-2.5, R-10 | OHOS adapter 故障注入 UT | null container/InputManager/token、MMI 失败 |
| VM-5 | AC-3.1~AC-3.5, R-11~R-15 | Manager/Pipeline Host UT | user/inner、hold 单槽、释放、bypass |
| VM-6 | AC-4.1~AC-4.3, R-16~R-18 | Dynamic/Static bridge 参数化 UT | 热点 -1/0/size-1/size/size+1、空 PixelMap |
| VM-7 | AC-4.4~AC-4.5, R-19~R-20 | Manager + MMI mock UT | PixelMap 指针相等、visible 调用条件 |
| VM-8 | AC-5.1~AC-5.3, R-21~R-23 | Pipeline 生命周期 UT | 窗口/Scene 失焦、销毁时即时 flush |
| VM-9 | AC-5.4~AC-5.5, R-24~R-25 | OHOS 普通窗口/UIExtension 集成测试 | windowId、token overload、失败日志 |
| VM-10 | AC-5.6, R-26 | Previewer 验证 | 返回值与无可见效果差异 |
| VM-11 | AC-6.1~AC-6.3, R-27~R-29 | API/架构边界审查 | InputKit、Node C、Web、Drag 不混用 |
| VM-12 | AC-6.4~AC-6.5, R-30~R-31 | Static 实现追溯 + 组件测试 | no-op 风险与 Hover 触发边界 |

## API 变更分析

> 本次为存量能力补录，不新增产品 API。下表记录纳入规格的现有公开契约。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `cursorControl.setCursor` | Public | `PointerStyle` | `void` | N/A | Dynamic API 11、Static API 23 设置系统光标 | AC-1.1, AC-1.3, AC-2.1 |
| `cursorControl.restoreDefault` | Public | 无 | `void` | N/A | Dynamic API 11、Static API 23 恢复默认箭头 | AC-1.1, AC-1.3, AC-3.4 |
| `UIContext.getCursorController` | Public | 无 | `CursorController` | N/A | Dynamic API 12、Static API 23 获取绑定实例的控制器 | AC-1.2, AC-1.3 |
| `CursorController.setCursor` | Public | `PointerStyle` | `void` | N/A | 设置 UIContext 对应窗口光标，Dynamic 声明下一帧生效 | AC-1.2, AC-1.3, AC-2.1, AC-6.4 |
| `CursorController.restoreDefault` | Public | 无 | `void` | N/A | 恢复 UIContext 对应窗口默认光标 | AC-3.4 |
| `CursorController.setCustomCursor` | Public | PixelMap、可选 focusX/focusY | `void` | N/A | API 26 设置自定义光标及热点 | AC-1.4, AC-4.1~AC-4.5 |
| `pointer.PointerStyle` | Public/InputKit | 枚举 0..51、-100 | 枚举 | N/A | ArkUI setCursor 的类型来源；部分值不可直接设置 | AC-1.5, AC-6.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 文档补录不改变 API | 无迁移要求 | N/A |

## 接口规格

### 接口定义

**cursorControl.setCursor / CursorController.setCursor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setCursor(value: PointerStyle): void` |
| 返回值 | `void` — 请求提交无同步成功状态 |
| 开放范围 | Public |
| 错误码 | N/A；不得套用 InputKit BusinessError |
| 关联 AC | AC-1.1~AC-3.5, AC-5.4~AC-5.6, AC-6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `PointerStyle` | 是 | 无 | Pipeline 当前仅接受 0..51；-100、负数、>51 和内部 1001..1004 不入队 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法系统样式 | 在下一次 VSync 仲裁并应用 | AC-2.1~AC-2.4 |
| 2 | 用户设置后组件内部请求 | 内部请求被用户覆盖标志拒绝 | AC-3.1 |
| 3 | 非法样式值 | 静默不改变当前样式 | AC-1.5 |
| 4 | Static 实例入口 | 按当前源码不执行底层 setter，作为风险记录 | AC-6.4 |

**cursorControl.restoreDefault / CursorController.restoreDefault**

| 属性 | 值 |
|------|-----|
| 函数签名 | `restoreDefault(): void` |
| 返回值 | `void` — DEFAULT 请求无同步成功状态 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.3, AC-3.4, AC-5.1~AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无 | N/A | N/A | N/A | 使用当前 focus window ID；生命周期恢复可传入明确窗口 ID |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 用户主动恢复 | DEFAULT 以 USER reason 入队并清除 user flag | AC-3.4 |
| 2 | 窗口/Scene 失焦 | 更高优先级 DEFAULT 覆盖同帧用户请求 | AC-5.1, AC-5.2 |
| 3 | 容器销毁 | 当前非 DEFAULT 时恢复并立即 flush | AC-5.3 |

**CursorController.setCustomCursor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setCustomCursor(value: image.PixelMap, focusX?: int, focusY?: int): void` |
| 返回值 | `void` — 请求提交无同步成功状态 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.4, AC-2.1~AC-2.5, AC-4.1~AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `image.PixelMap` | 是 | 无 | 转换后必须非空；ArkUI 当前不声明 256×256 上限错误 |
| focusX | `int` | 否 | 0 | 单位 px；负值回退 0；Dynamic/Static 对 =width 的处理不同 |
| focusY | `int` | 否 | 0 | 单位 px；负值回退 0；Dynamic/Static 对 =height 的处理不同 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 PixelMap 和热点 | 下一帧应用自定义光标 | AC-2.1, AC-4.1 |
| 2 | 热点越界 | 按 Dynamic/Static 现有边界回退 | AC-4.2 |
| 3 | 空或不可转换 PixelMap | 静默不设置 | AC-4.3 |
| 4 | UIExtension | 使用 host window ID 与 token 重载 | AC-5.4, AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 否。本规格记录现有行为；Dynamic/Static 自定义热点上界不一致和 Static 实例 setCursor no-op 作为实现偏差保留。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；光标状态仅驻留于当前 Pipeline/Manager 和平台窗口。
- **最低支持版本:** Dynamic 全局 API 11；Dynamic UIContext API 12；Static API 23；ArkUI 自定义光标 API 26。
- **API 版本号策略:** 以 canonical SDK `@since` 为准；PointerStyle Dynamic 项按 API 9/10/18/20/22 分组，Static 统一 API 23。
- **生效时序:** Dynamic SDK明确下一渲染帧生效；Static SDK未重复说明，但当前实现共享 Pipeline VSync 队列。
- **异常模型:** ArkUI 接口返回 `void` 且不声明 BusinessError；InputKit 的 401/202/26500001 不属于 ArkUI 接口契约。
- **前端差异:** Dynamic 在热点等于宽/高时保留，Static 回退为 0；Static `CursorController.setCursor` 当前未转发。
- **平台差异:** OHOS 真机调用 MMI；Previewer 当前无可见效果；UIExtension 需要有效窗口 token。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 窗口级状态 | 普通光标属于 Pipeline/EventManager/MouseStyleManager，不存入 FrameNode 属性 | AC-2.1~AC-5.6 |
| 帧同步 | 公开调用只排队，平台应用必须由 VSync/FlushCursorStyleRequests 完成 | AC-2.1~AC-2.4 |
| 原因优先级 | 恢复原因高于用户原因，用户原因高于内部组件原因 | AC-2.2, AC-5.1~AC-5.3 |
| 内部节点门禁 | 内部样式必须取得唯一 hold-node 且 node ID 匹配 | AC-3.1~AC-3.5 |
| 平台隔离 | MMI 调用仅位于 adapter；UIExtension token 从 Container 获取 | AC-5.4, AC-5.5 |
| 契约优先级 | 公开 API以 SDK 为准，源码偏差进入风险，不静默改写契约 | AC-4.2, AC-6.4 |
| Feat 边界 | Hover 归 Feat-03；Web 和 Drag 光标使用独立链；InputKit 不归 ace_engine 实现 | AC-6.1~AC-6.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 同一帧所有普通光标请求只应用一个最终样式；与上一帧相同则不调用平台接口 | Manager UT | `mouse_style.cpp:62-89,104-140` |
| 功耗 | 不新增定时器，复用 Pipeline 渲染帧请求 | 代码审查 | `pipeline_context.cpp:5408-5419` |
| 内存 | 自定义光标以 RefPtr 持有 PixelMap，队列清空后释放请求记录 | 生命周期 UT/泄漏检测 | `mouse_style.h:103-119,202-208` |
| 安全 | UIExtension 必须取得有效 token 后才能调用 token MMI 重载 | 平台故障注入 | `mouse_style_ohos.cpp:104-122,217-226` |
| 可靠性 | 失焦恢复原因必须覆盖同帧用户和内部请求 | Manager/Pipeline UT | `mouse_style.h:121-127` |
| 可测试性 | 对 0、51、-100、52 和热点五边界值提供参数化用例 | UT | VM-2、VM-6 |
| 自动化维测 | 保留最近 10 条实际光标变化日志 | Dump/日志 UT | `mouse_style.cpp:24,135-150` |
| 定界定位 | 平台失败、token 缺失、空 PixelMap 通过 ACE_MOUSE 日志暴露 | 日志检查 | `mouse_style_ohos.cpp:31-41,110-120,198-230` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无鼠标时无可见效果；连接鼠标后走窗口级 MMI 光标 | 不保证设备始终显示 pointer | 外接鼠标真机测试 | `mouse_style_ohos.cpp:31-122` |
| 平板 | 常见外接鼠标/触控板，字段与手机一致 | 触控板 pointer 同样使用窗口样式 | 真机测试 | OHOS MMI 适配链 |
| 折叠屏 | 窗口/Scene 焦点变化可能触发默认恢复 | 展开、分屏和窗口切换后按失焦规则恢复 | 多窗口集成测试 | `pipeline_context.cpp:5788-5795` |
| UIExtension | 使用 host/focus window ID 和 token MMI 重载 | token 缺失时不应用 | UIExtension 集成测试 | `mouse_style_ohos.cpp:104-150,217-226` |
| Previewer | 普通接口表面成功但不设置平台光标，自定义接口 no-op | 不以 Previewer 结果证明真机光标生效 | Previewer 对照测试 | `adapter/preview/osal/mouse_style_ohos.cpp:27-37` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 光标图形可辅助指示交互语义，但不替代无障碍焦点或朗读 | PointerStyle 选择 |
| 大字体 | 否 | 不参与文本布局和字号缩放 | N/A |
| 深色模式 | 是 | 系统 PointerStyle 的主题适配由 MMI/系统负责；自定义 PixelMap 需应用自行提供适配资源 | 系统/自定义光标 |
| 多窗口/分屏 | 是 | 状态按 focus/host window ID 应用，失焦恢复默认 | AC-5.1~AC-5.5 |
| 多用户 | 否 | 不持久化用户数据 | N/A |
| 版本升级 | 是 | API 11/12/23/26 与 PointerStyle 分组需按目标版本验证 | AC-1.1~AC-1.5 |
| 生态兼容 | 是 | Dynamic/Static 热点和 Static no-op 偏差、Previewer 差异需要显式测试 | AC-4.2, AC-5.6, AC-6.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 鼠标光标样式与自定义光标
  作为 ArkUI 应用或组件开发者
  我想要在正确窗口中设置并恢复系统或自定义光标
  以便光标样式在多来源竞争和生命周期变化时保持确定

  Scenario Outline: PointerStyle 合法值域
    Given 当前窗口光标为 DEFAULT
    When 用户调用 setCursor 传入 <value>
    Then 请求处理结果为 <result>

    Examples:
      | value | result |
      | 0 | 下一帧应用或因相同值去重 |
      | 51 | 下一帧进入平台适配 |
      | -100 | 静默忽略 |
      | 52 | 静默忽略 |
      | 1001 | 静默忽略 |

  Scenario: 同帧原因优先级
    Given 同一帧先后收到内部 HAND_POINTING、用户 TEXT_CURSOR 和窗口失焦 DEFAULT 请求
    When Pipeline flush 光标请求
    Then 最终应用 DEFAULT
    And 仅最高优先级请求进入平台 setter

  Scenario: 用户设置压制组件内部设置
    Given 用户已成功提交 TEXT_CURSOR 且 userSetCursor 为 true
    And 组件持有合法 hold-node
    When 组件提交内部 HAND_POINTING 请求
    Then Manager 拒绝该内部请求
    When 用户调用 restoreDefault 并完成仲裁
    Then 后续匹配 hold-node 的内部请求可再次被接受

  Scenario Outline: 自定义热点前端差异
    Given PixelMap 的宽度为 32
    When <frontend> 调用 setCustomCursor 且 focusX 为 <focusX>
    Then 提交到 Pipeline 的 focusX 为 <expected>

    Examples:
      | frontend | focusX | expected |
      | Dynamic | -1 | 0 |
      | Static | -1 | 0 |
      | Dynamic | 31 | 31 |
      | Static | 31 | 31 |
      | Dynamic | 32 | 32 |
      | Static | 32 | 0 |
      | Dynamic | 33 | 0 |
      | Static | 33 | 0 |

  Scenario: UIExtension token 缺失
    Given 当前容器是 UIExtension 且窗口 token 为空
    When VSync 尝试应用系统或自定义光标
    Then 平台适配记录错误日志并停止
    And ArkUI void 调用方不收到 BusinessError

  Scenario: Previewer 降级
    Given 应用运行在 Previewer
    When 调用 setCursor 或 setCustomCursor
    Then 不产生可见平台光标变化
    And 普通 setCursor 的适配层仍表面返回成功

  Scenario: Static 实例入口偏差
    Given 应用通过 Static UIContext 获取 CursorController
    When 调用 CursorController.setCursor(TEXT_CURSOR)
    Then 当前 checked-in 实现仅同步并恢复 instance ID
    And 不假定底层 Pipeline 已接收该样式
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（ArkUI、InputKit、Hover、Web、Drag、Node C-API 清晰分离）
- [x] 无语义模糊表述（数值、版本、优先级、热点边界均明确）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "cursorControl CursorController MouseStyleManager VsyncMouseFormat hold node restore default"
  - repo: "openharmony/arkui_ace_engine"
    query: "setCustomCursor PixelMap focusX focusY UIExtension token Previewer"
  - repo: "openharmony/interface_sdk-js"
    query: "PointerStyle cursorControl CursorController API since custom cursor"
```

**关键文档：** `specs/04-common-capability/04-common-events/05-mouse-events/design.md`、`interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`、`interface/sdk-js/api/@ohos.multimodalInput.pointer.d.ts`、`frameworks/base/mousestyle/mouse_style.h`
