# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Dialog C API（ArkUI_NativeDialogAPI_1/2/3、OH_ArkUI_CustomDialog 函数族、枚举与状态查询） |
| 特性编号 | Func-05-06-04-Feat-03 |
| FuncID | 05-06-04 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 12 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 12 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArkUI_NativeDialogAPI_1（create/dispose/setContent/removeContent/setContentAlignment/resetContentAlignment/setModalMode/setAutoCancel/setMask/setBackgroundColor/setCornerRadius/setGridColumnCount/enableCustomStyle/enableCustomAnimation/registerOnWillDismiss/show/close/registerOnWillDismissWithUserData） | @since 12 |
| ADDED | ArkUI_DismissReason 枚举（BACK_PRESS=0/TOUCH_OUTSIDE/CLOSE_BUTTON） | @since 12 |
| ADDED | ArkUI_NativeDialogAPI_2（setKeyboardAvoidDistance/setLevelMode/setLevelUniqueId/setImmersiveMode） | @since 15 |
| ADDED | ArkUI_NativeDialogAPI_3（setLevelOrder/registerOnWillAppear/registerOnDidAppear/registerOnWillDisappear/registerOnDidDisappear） | @since 18 |
| ADDED | ArkUI_NativeDialogAPI_3 扩展（setBorderWidth/setBorderColor/setBorderStyle/setWidth/setHeight/setShadow/setCustomShadow/setBackgroundBlurStyle/setKeyboardAvoidMode/enableHoverMode/setHoverModeArea/setFocusable/setBackgroundBlurStyleOptions/setBackgroundEffect） | @since 19 |
| ADDED | OH_ArkUI_CustomDialog 函数族（OpenDialog/CloseDialog/CreateOptions/DisposeOptions/UpdateDialog 及全部属性设置函数族） | @since 19 |
| ADDED | OH_ArkUI_CustomDialog_GetState | @since 20 |
| ADDED | ArkUI_DialogState 枚举（UNINITIALIZED/APPEARING/APPEARED/DISAPPEARING/DISAPPEARED） | @since 20 |
| ADDED | OH_ArkUI_DialogDisplayModeInSubWindow 枚举（SCREEN_BASED=0/WINDOW_BASED） | @since 26.0.0 |
| ADDED | OH_ArkUI_NativeModule_CustomDialog_SetSystemMaterialInOptions/SetSystemMaterial（systemapi） | @since 26.0.0 |
| ADDED | OH_ArkUI_CustomDialog_OpenDialogWithCallback | @since 26.1.0 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/04-custom-dialog/design.md`
- **KB 路由**: `docs/kb/components/overlay/dialog.md`
- **SDK 类型定义**:
  - C API 头文件: `interface/sdk-js/api/arkui/native/native_dialog.h`
- **源码入口**:
  - C API 声明: `interfaces/native/native_dialog.h`
  - C API Model: `interfaces/native/node/dialog_model.cpp`
  - C API Option: `interfaces/native/node/dialog_option.cpp`
  - node_modifier 委托: `frameworks/core/interfaces/native/node/dialog_modifier.cpp`
  - NAPI (promptAction): `interfaces/napi/kits/promptaction/js_prompt_action.cpp`
  - NAPI (arkui.dialog): `interfaces/napi/kits/dialog/js_dialog.cpp`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: ArkUI_NativeDialogAPI_1 基础生命周期与内容管理

**角色**: NDK 开发者
**期望**: 我想要通过 C API 创建、设置内容、显示和关闭对话框
**价值**: 以便在 Native 层集成对话框功能

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `ArkUI_NativeDialogAPI_1.create()`（@since 12）THEN 创建 ArkUI_DialogHandle 句柄 | 正常 |
| AC-1.2 | WHEN 调用 `setContent(handle, contentNode)`（@since 12）THEN 将 contentNode 设置为对话框内容节点 | 正常 |
| AC-1.3 | WHEN 调用 `removeContent(handle)`（@since 12）THEN 移除对话框内容节点 | 正常 |
| AC-1.4 | WHEN 调用 `show(handle)`（@since 12）THEN 对话框显示 | 正常 |
| AC-1.5 | WHEN 调用 `close(handle)`（@since 12）THEN 对话框关闭 | 正常 |
| AC-1.6 | WHEN 调用 `dispose(handle)`（@since 12）THEN 释放对话框句柄资源 | 正常 |
| AC-1.7 | WHEN 对已 dispose 的 handle 调用 show/close THEN 无效果，不崩溃 | 异常 |

### US-2: ArkUI_NativeDialogAPI_1 样式与行为属性

**角色**: NDK 开发者
**期望**: 我想要通过 C API 设置对话框的对齐、遮罩、模态、背景色、圆角等样式
**价值**: 以便 Native 弹窗外观和行为与 ArkTS 弹窗一致

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `setContentAlignment(handle, alignment, dx, dy)`（@since 12）THEN 对话框按 alignment + offset 定位 | 正常 |
| AC-2.2 | WHEN 调用 `resetContentAlignment(handle)`（@since 12）THEN 对齐方式重置为默认值 | 正常 |
| AC-2.3 | WHEN 调用 `setModalMode(handle, isModal)`（@since 12）THEN 对话框模态/非模态行为生效 | 正常 |
| AC-2.4 | WHEN 调用 `setAutoCancel(handle, autoCancel)`（@since 12）THEN 点击遮罩关闭行为生效 | 正常 |
| AC-2.5 | WHEN 调用 `setMask(handle, maskColor, maskRect)`（@since 12）THEN 遮罩颜色和区域生效 | 正常 |
| AC-2.6 | WHEN 调用 `setBackgroundColor(handle, color)`（@since 12）THEN 对话框背景色生效 | 正常 |
| AC-2.7 | WHEN 调用 `setCornerRadius(handle, radius)`（@since 12）THEN 对话框圆角生效 | 正常 |
| AC-2.8 | WHEN 调用 `setGridColumnCount(handle, count)`（@since 12）THEN 对话框栅格列数生效 | 正常 |
| AC-2.9 | WHEN 调用 `enableCustomStyle(handle, enableCustomStyle)`（@since 12）THEN 对话框启用/禁用自定义样式 | 正常 |
| AC-2.10 | WHEN 调用 `enableCustomAnimation(handle, enableCustomAnimation)`（@since 12）THEN 对话框启用/禁用自定义动画 | 正常 |
| AC-2.11 | WHEN 调用 `registerOnWillDismiss(handle, callback)`（@since 12）THEN 关闭请求时触发回调，开发者可通过 ArkUI_DismissReason 决定是否关闭 | 正常 |
| AC-2.12 | WHEN 调用 `registerOnWillDismissWithUserData(handle, callback, userData)`（@since 12）THEN 回调携带 userData 上下文 | 正常 |

### US-3: ArkUI_NativeDialogAPI_2/_3 扩展属性

**角色**: NDK 开发者
**期望**: 我想要通过 C API 设置键盘避让、多层级、边框、尺寸、阴影、模糊、悬浮、焦点等扩展属性
**价值**: 以便 Native 弹窗具备与 ArkTS 等价的全部布局和样式能力

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `setKeyboardAvoidDistance(handle, distance)`（@since 15，API_2）THEN 对话框与软键盘距离生效 | 正常 |
| AC-3.2 | WHEN 调用 `setLevelMode(handle, levelMode)`（@since 15，API_2）THEN 层级模式（OVERLAY/EMBEDDED）生效 | 正常 |
| AC-3.3 | WHEN 调用 `setLevelUniqueId(handle, uniqueId)`（@since 15，API_2）THEN 层级唯一标识生效 | 正常 |
| AC-3.4 | WHEN 调用 `setImmersiveMode(handle, immersiveMode)`（@since 15，API_2）THEN 沉浸式模式生效 | 正常 |
| AC-3.5 | WHEN 调用 `setLevelOrder(handle, levelOrder)`（@since 18，API_3）THEN 同层级 Z 序生效 | 正常 |
| AC-3.6 | WHEN 调用 `setBorderWidth(handle, value)`/`setBorderColor`/`setBorderStyle`（@since 19，API_3）THEN 对话框边框属性生效 | 正常 |
| AC-3.7 | WHEN 调用 `setWidth(handle, width)`/`setHeight(handle, height)`（@since 19，API_3）THEN 对话框显式尺寸生效 | 正常 |
| AC-3.8 | WHEN 调用 `setShadow(handle, shadow)`/`setCustomShadow(handle, customShadow)`（@since 19，API_3）THEN 对话框阴影生效 | 正常 |
| AC-3.9 | WHEN 调用 `setBackgroundBlurStyle(handle, blurStyle)`（@since 19，API_3）THEN 对话框背景模糊生效 | 正常 |
| AC-3.10 | WHEN 调用 `setKeyboardAvoidMode(handle, mode)`（@since 19，API_3）THEN 键盘避让模式（NONE/TRANSLATE/RESIZE）生效 | 正常 |
| AC-3.11 | WHEN 调用 `enableHoverMode(handle, enable)`/`setHoverModeArea(handle, area)`（@since 19，API_3）THEN 折叠屏悬浮态行为生效 | 正常 |
| AC-3.12 | WHEN 调用 `setFocusable(handle, focusable)`（@since 19，API_3）THEN 对话框可聚焦性生效 | 正常 |
| AC-3.13 | WHEN 调用 `setBackgroundBlurStyleOptions(handle, options)`/`setBackgroundEffect(handle, effect)`（@since 19，API_3）THEN 背景模糊扩展选项和背景效果生效 | 正常 |

### US-4: ArkUI_NativeDialogAPI_3 生命周期回调注册

**角色**: NDK 开发者
**期望**: 我想要通过 C API 注册对话框出现/消失各阶段的回调
**价值**: 以便在 Native 层执行生命周期关键节点的业务逻辑

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `registerOnWillAppear(handle, callback)`（@since 18，API_3）THEN 对话框进入 APPEARING 时触发回调 | 正常 |
| AC-4.2 | WHEN 调用 `registerOnDidAppear(handle, callback)`（@since 18，API_3）THEN 对话框进入 APPEARED 时触发回调 | 正常 |
| AC-4.3 | WHEN 调用 `registerOnWillDisappear(handle, callback)`（@since 18，API_3）THEN 对话框进入 DISAPPEARING 时触发回调 | 正常 |
| AC-4.4 | WHEN 调用 `registerOnDidDisappear(handle, callback)`（@since 18，API_3）THEN 对话框进入 DISAPPEARED 时触发回调 | 正常 |

### US-5: OH_ArkUI_CustomDialog 函数族

**角色**: NDK 开发者
**期望**: 我想要通过 OH_ArkUI_CustomDialog 函数族创建、显示、关闭、释放和更新 Native 自定义对话框
**价值**: 以便使用统一的 Options 模式管理 Native 弹窗全生命周期

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `OH_ArkUI_CustomDialog_CreateOptions(&options)`（@since 19）THEN 创建 OH_ArkUI_CustomDialogOptions 选项对象 | 正常 |
| AC-5.2 | WHEN 调用 `OH_ArkUI_CustomDialog_OpenDialog(options, callback, userData)`（@since 19）THEN 打开对话框，通过回调返回 dialog 实例 | 正常 |
| AC-5.3 | WHEN 调用 `OH_ArkUI_CustomDialog_CloseDialog(dialog)`（@since 19）THEN 关闭指定对话框 | 正常 |
| AC-5.4 | WHEN 调用 `OH_ArkUI_CustomDialog_DisposeOptions(options)`（@since 19）THEN 释放选项对象资源 | 正常 |
| AC-5.5 | WHEN 调用 `OH_ArkUI_CustomDialog_UpdateDialog(dialog, options)`（@since 19）THEN 更新已显示对话框的属性 | 正常 |
| AC-5.6 | WHEN 调用 `OH_ArkUI_CustomDialog_OpenDialogWithCallback(options, callback, userData)`（@since 26.1.0）THEN 打开对话框并通过 callback 返回 DialogBaseController | 正常 |

### US-6: OH_ArkUI_CustomDialog 属性设置函数族

**角色**: NDK 开发者
**期望**: 我想要通过 OH_ArkUI_CustomDialog_Set* 函数族设置对话框全部属性
**价值**: 以便在 Options 对象上统一配置所有样式和行为属性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `SetLevelMode(options, levelMode)`/`SetAlignment(options, alignment, dx, dy)`/`SetModalMode(options, isModal)`/`SetAutoCancel(options, autoCancel)`（@since 19）THEN 对应属性写入 options | 正常 |
| AC-6.2 | WHEN 调用 `SetSubwindowMode(options, isSubwindow)`/`SetDisplayModeInSubWindow(options, mode)`（@since 19/26.0.0）THEN 子窗口模式和显示模式生效 | 正常 |
| AC-6.3 | WHEN 调用 `SetMask(options, maskColor, maskRect)`（@since 19）THEN 遮罩颜色和区域写入 options | 正常 |
| AC-6.4 | WHEN 调用 `SetBackgroundColor(options, color)`/`SetCornerRadius(options, radius)`（@since 19）THEN 背景色和圆角写入 options | 正常 |
| AC-6.5 | WHEN 调用 `SetBorderWidth(options, value)`/`SetBorderColor(options, color)`/`SetBorderStyle(options, style)`（@since 19）THEN 边框属性写入 options | 正常 |
| AC-6.6 | WHEN 调用 `SetWidth(options, width)`/`SetHeight(options, height)`（@since 19）THEN 显式尺寸写入 options | 正常 |
| AC-6.7 | WHEN 调用 `SetShadow(options, shadow)`/`SetCustomShadow(options, customShadow)`（@since 19）THEN 阴影属性写入 options | 正常 |
| AC-6.8 | WHEN 调用 `SetBackgroundBlurStyle(options, blurStyle)`/`SetBackgroundBlurStyleOptions(options, options_)`/`SetBackgroundEffect(options, effect)`（@since 19）THEN 背景模糊和效果写入 options | 正常 |
| AC-6.9 | WHEN 调用 `SetKeyboardAvoidMode(options, mode)`（@since 19）THEN 键盘避让模式写入 options | 正常 |
| AC-6.10 | WHEN 调用 `SetHoverModeEnabled(options, enable)`/`SetHoverModeArea(options, area)`（@since 19）THEN 悬浮态属性写入 options | 正常 |
| AC-6.11 | WHEN 调用 `RegisterOnWillDismissCallback(options, callback)`/`RegisterOnWillAppearCallback(options, callback)`/`RegisterOnDidAppearCallback(options, callback)`/`RegisterOnWillDisappearCallback(options, callback)`/`RegisterOnDidDisappearCallback(options, callback)`（@since 19）THEN 生命周期回调注册到 options | 正常 |

### US-7: 枚举与状态查询

**角色**: NDK 开发者
**期望**: 我想要使用 ArkUI_DismissReason、ArkUI_DialogState、OH_ArkUI_DialogDisplayModeInSubWindow 枚举并查询对话框状态
**价值**: 以便在回调中判断关闭原因、查询弹窗状态、控制子窗口显示基准

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN onWillDismiss 回调接收 ArkUI_DismissReason（@since 12）THEN reason 为 BACK_PRESS=0/TOUCH_OUTSIDE=1/CLOSE_BUTTON=2 之一 | 正常 |
| AC-7.2 | WHEN 调用 `OH_ArkUI_CustomDialog_GetState(dialog)`（@since 20）THEN 返回 ArkUI_DialogState 枚举值（UNINITIALIZED/APPEARING/APPEARED/DISAPPEARING/DISAPPEARED） | 正常 |
| AC-7.3 | WHEN 设置 `OH_ArkUI_DialogDisplayModeInSubWindow` 为 SCREEN_BASED=0（@since 26.0.0）THEN 子窗口弹窗以屏幕为基准显示 | 正常 |
| AC-7.4 | WHEN 设置 `OH_ArkUI_DialogDisplayModeInSubWindow` 为 WINDOW_BASED（@since 26.0.0）THEN 子窗口弹窗以窗口为基准显示 | 正常 |

### US-8: systemapi 扩展接口

**角色**: 系统应用开发者
**期望**: 我想要通过 systemapi 接口设置系统 Material 效果
**价值**: 以便系统应用对话框使用统一的系统 Material 视觉

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `OH_ArkUI_NativeModule_CustomDialog_SetSystemMaterialInOptions(options, enable)`（@since 26.0.0，systemapi）THEN options 中系统 Material 标志生效 | 正常 |
| AC-8.2 | WHEN 调用 `OH_ArkUI_NativeModule_CustomDialog_SetSystemMaterial(dialog, enable)`（@since 26.0.0，systemapi）THEN 已显示对话框的系统 Material 效果更新 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.7 | R-1, R-2 | TASK-DIALOG-01 | C API UT | `test/unittest/capi/accessors/dialog_extender_accessor_test.cpp` |
| AC-2.1 ~ AC-2.12 | R-3 | TASK-DIALOG-01 | C API UT | `test/unittest/capi/accessors/dialog_extender_accessor_test.cpp` |
| AC-3.1 ~ AC-3.13 | R-4, R-5 | TASK-DIALOG-01 | C API UT | `test/unittest/capi/accessors/dialog_extender_accessor_test.cpp` |
| AC-4.1 ~ AC-4.4 | R-6 | TASK-DIALOG-01 | C API UT | `test/unittest/capi/accessors/dialog_extender_accessor_test.cpp` |
| AC-5.1 ~ AC-5.6 | R-7, R-8 | TASK-DIALOG-01 | C API UT | `test/unittest/capi/accessors/custom_dialog_controller_accessor_test.cpp` |
| AC-6.1 ~ AC-6.11 | R-9 | TASK-DIALOG-01 | C API UT | `test/unittest/capi/accessors/custom_dialog_controller_accessor_test.cpp` |
| AC-7.1 ~ AC-7.4 | R-10, R-11, R-12 | TASK-DIALOG-01 | C API UT | `test/unittest/capi/accessors/custom_dialog_controller_accessor_test.cpp` |
| AC-8.1 ~ AC-8.2 | R-13 | TASK-DIALOG-01 | C API UT | `test/unittest/capi/accessors/custom_dialog_controller_accessor_test.cpp` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `dialog_model.cpp` create/setContent/show/close | create 返回 handle；setContent 设置内容节点；show 显示；close 关闭 | @since 12，API_1 | AC-1.1 ~ AC-1.5 |
| R-2 | 异常 | `dialog_model.cpp` 对已 dispose 的 handle 操作 | show/close 无效果，不崩溃 | handle 为 NULL 或已释放 | AC-1.7 |
| R-3 | 行为 | `dialog_model.cpp` 样式/行为属性 | setContentAlignment/resetContentAlignment/setModalMode/setAutoCancel/setMask/setBackgroundColor/setCornerRadius/setGridColumnCount/enableCustomStyle/enableCustomAnimation/registerOnWillDismiss/registerOnWillDismissWithUserData | @since 12，API_1 | AC-2.1 ~ AC-2.12 |
| R-4 | 行为 | `dialog_model.cpp` API_2 扩展 | setKeyboardAvoidDistance/setLevelMode/setLevelUniqueId/setImmersiveMode | @since 15，API_2 | AC-3.1 ~ AC-3.4 |
| R-5 | 行为 | `dialog_model.cpp` API_3 扩展 | setLevelOrder + @since 19 扩展（setBorderWidth/setBorderColor/setBorderStyle/setWidth/setHeight/setShadow/setCustomShadow/setBackgroundBlurStyle/setKeyboardAvoidMode/enableHoverMode/setHoverModeArea/setFocusable/setBackgroundBlurStyleOptions/setBackgroundEffect） | setLevelOrder @since 18，其余 @since 19，API_3 | AC-3.5 ~ AC-3.13 |
| R-6 | 行为 | `dialog_model.cpp` API_3 生命周期回调 | registerOnWillAppear/registerOnDidAppear/registerOnWillDisappear/registerOnDidDisappear | @since 18，API_3 | AC-4.1 ~ AC-4.4 |
| R-7 | 行为 | `dialog_option.cpp` OH_ArkUI_CustomDialog 创建/显示/关闭/释放/更新 | CreateOptions 创建选项；OpenDialog 打开；CloseDialog 关闭；DisposeOptions 释放；UpdateDialog 更新 | @since 19 | AC-5.1 ~ AC-5.5 |
| R-8 | 行为 | `dialog_option.cpp` OpenDialogWithCallback | 打开对话框并通过 callback 返回 DialogBaseController | @since 26.1.0 | AC-5.6 |
| R-9 | 行为 | `dialog_option.cpp` OH_ArkUI_CustomDialog_Set* 函数族 | SetLevelMode/SetAlignment/SetModalMode/SetAutoCancel/SetSubwindowMode/SetDisplayModeInSubWindow/SetMask/SetBackgroundColor/SetCornerRadius/SetBorderWidth/SetBorderColor/SetBorderStyle/SetWidth/SetHeight/SetShadow/SetCustomShadow/SetBackgroundBlurStyle/SetBackgroundBlurStyleOptions/SetBackgroundEffect/SetKeyboardAvoidMode/SetHoverModeEnabled/SetHoverModeArea/RegisterOn*Callback | @since 19，SetDisplayModeInSubWindow @since 26.0.0 | AC-6.1 ~ AC-6.11 |
| R-10 | 行为 | `native_dialog.h` ArkUI_DismissReason | 枚举值 BACK_PRESS=0/TOUCH_OUTSIDE=1/CLOSE_BUTTON=2 | @since 12 | AC-7.1 |
| R-11 | 行为 | `dialog_option.cpp` OH_ArkUI_CustomDialog_GetState | 返回 ArkUI_DialogState 枚举（UNINITIALIZED/APPEARING/APPEARED/DISAPPEARING/DISAPPEARED） | @since 20 | AC-7.2 |
| R-12 | 行为 | `native_dialog.h` OH_ArkUI_DialogDisplayModeInSubWindow | 枚举值 SCREEN_BASED=0/WINDOW_BASED | @since 26.0.0 | AC-7.3, AC-7.4 |
| R-13 | 行为 | `dialog_option.cpp` SetSystemMaterialInOptions/SetSystemMaterial | 设置系统 Material 效果（systemapi） | @since 26.0.0，systemapi | AC-8.1, AC-8.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.7 | C API UT | ArkUI_NativeDialogAPI_1 基础生命周期 |
| VM-2 | AC-2.1 ~ AC-2.12 | C API UT | ArkUI_NativeDialogAPI_1 样式与行为属性 |
| VM-3 | AC-3.1 ~ AC-3.13 | C API UT | ArkUI_NativeDialogAPI_2/_3 扩展属性 |
| VM-4 | AC-4.1 ~ AC-4.4 | C API UT | ArkUI_NativeDialogAPI_3 生命周期回调 |
| VM-5 | AC-5.1 ~ AC-5.6 | C API UT | OH_ArkUI_CustomDialog 创建/显示/关闭/释放/更新 |
| VM-6 | AC-6.1 ~ AC-6.11 | C API UT | OH_ArkUI_CustomDialog_Set* 属性函数族 |
| VM-7 | AC-7.1 ~ AC-7.4 | C API UT | 枚举与状态查询 |
| VM-8 | AC-8.1 ~ AC-8.2 | C API UT | systemapi 扩展接口 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC | @since |
|----------|----------|----------|--------|-----------|----------|---------|--------|
| ArkUI_NativeDialogAPI_1.create | NDK/Public | — | ArkUI_DialogHandle | 无 | 创建对话框句柄 | AC-1.1 | 12 |
| ArkUI_NativeDialogAPI_1.setContent | NDK/Public | handle, contentNode | void | 无 | 设置内容节点 | AC-1.2 | 12 |
| ArkUI_NativeDialogAPI_1.removeContent | NDK/Public | handle | void | 无 | 移除内容节点 | AC-1.3 | 12 |
| ArkUI_NativeDialogAPI_1.show | NDK/Public | handle | int32_t | 无 | 显示对话框 | AC-1.4 | 12 |
| ArkUI_NativeDialogAPI_1.close | NDK/Public | handle | int32_t | 无 | 关闭对话框 | AC-1.5 | 12 |
| ArkUI_NativeDialogAPI_1.dispose | NDK/Public | handle | void | 无 | 释放句柄 | AC-1.6 | 12 |
| ArkUI_NativeDialogAPI_1.setContentAlignment | NDK/Public | handle, alignment, dx, dy | void | 无 | 设置对齐 | AC-2.1 | 12 |
| ArkUI_NativeDialogAPI_1.resetContentAlignment | NDK/Public | handle | void | 无 | 重置对齐 | AC-2.2 | 12 |
| ArkUI_NativeDialogAPI_1.setModalMode | NDK/Public | handle, isModal | void | 无 | 设置模态 | AC-2.3 | 12 |
| ArkUI_NativeDialogAPI_1.setAutoCancel | NDK/Public | handle, autoCancel | void | 无 | 设置遮罩关闭 | AC-2.4 | 12 |
| ArkUI_NativeDialogAPI_1.setMask | NDK/Public | handle, maskColor, maskRect | void | 无 | 设置遮罩 | AC-2.5 | 12 |
| ArkUI_NativeDialogAPI_1.setBackgroundColor | NDK/Public | handle, color | void | 无 | 设置背景色 | AC-2.6 | 12 |
| ArkUI_NativeDialogAPI_1.setCornerRadius | NDK/Public | handle, radius | void | 无 | 设置圆角 | AC-2.7 | 12 |
| ArkUI_NativeDialogAPI_1.setGridColumnCount | NDK/Public | handle, count | void | 无 | 设置栅格列数 | AC-2.8 | 12 |
| ArkUI_NativeDialogAPI_1.enableCustomStyle | NDK/Public | handle, enable | void | 无 | 启用自定义样式 | AC-2.9 | 12 |
| ArkUI_NativeDialogAPI_1.enableCustomAnimation | NDK/Public | handle, enable | void | 无 | 启用自定义动画 | AC-2.10 | 12 |
| ArkUI_NativeDialogAPI_1.registerOnWillDismiss | NDK/Public | handle, callback | void | 无 | 注册关闭请求回调 | AC-2.11 | 12 |
| ArkUI_NativeDialogAPI_1.registerOnWillDismissWithUserData | NDK/Public | handle, callback, userData | void | 无 | 注册带 userData 的关闭请求回调 | AC-2.12 | 12 |
| ArkUI_DismissReason | NDK/Public | — | enum | 无 | 关闭原因枚举 | AC-7.1 | 12 |
| ArkUI_NativeDialogAPI_2.setKeyboardAvoidDistance | NDK/Public | handle, distance | void | 无 | 键盘避让距离 | AC-3.1 | 15 |
| ArkUI_NativeDialogAPI_2.setLevelMode | NDK/Public | handle, levelMode | void | 无 | 层级模式 | AC-3.2 | 15 |
| ArkUI_NativeDialogAPI_2.setLevelUniqueId | NDK/Public | handle, uniqueId | void | 无 | 层级唯一标识 | AC-3.3 | 15 |
| ArkUI_NativeDialogAPI_2.setImmersiveMode | NDK/Public | handle, immersiveMode | void | 无 | 沉浸式模式 | AC-3.4 | 15 |
| ArkUI_NativeDialogAPI_3.setLevelOrder | NDK/Public | handle, levelOrder | void | 无 | Z 序 | AC-3.5 | 18 |
| ArkUI_NativeDialogAPI_3.registerOnWillAppear | NDK/Public | handle, callback | void | 无 | 注册 WillAppear 回调 | AC-4.1 | 18 |
| ArkUI_NativeDialogAPI_3.registerOnDidAppear | NDK/Public | handle, callback | void | 无 | 注册 DidAppear 回调 | AC-4.2 | 18 |
| ArkUI_NativeDialogAPI_3.registerOnWillDisappear | NDK/Public | handle, callback | void | 无 | 注册 WillDisappear 回调 | AC-4.3 | 18 |
| ArkUI_NativeDialogAPI_3.registerOnDidDisappear | NDK/Public | handle, callback | void | 无 | 注册 DidDisappear 回调 | AC-4.4 | 18 |
| ArkUI_NativeDialogAPI_3.setBorderWidth/setBorderColor/setBorderStyle | NDK/Public | handle, value | void | 无 | 边框属性 | AC-3.6 | 19 |
| ArkUI_NativeDialogAPI_3.setWidth/setHeight | NDK/Public | handle, dimension | void | 无 | 显式尺寸 | AC-3.7 | 19 |
| ArkUI_NativeDialogAPI_3.setShadow/setCustomShadow | NDK/Public | handle, shadow | void | 无 | 阴影 | AC-3.8 | 19 |
| ArkUI_NativeDialogAPI_3.setBackgroundBlurStyle | NDK/Public | handle, blurStyle | void | 无 | 背景模糊 | AC-3.9 | 19 |
| ArkUI_NativeDialogAPI_3.setKeyboardAvoidMode | NDK/Public | handle, mode | void | 无 | 键盘避让模式 | AC-3.10 | 19 |
| ArkUI_NativeDialogAPI_3.enableHoverMode/setHoverModeArea | NDK/Public | handle, enable/area | void | 无 | 悬浮态 | AC-3.11 | 19 |
| ArkUI_NativeDialogAPI_3.setFocusable | NDK/Public | handle, focusable | void | 无 | 可聚焦性 | AC-3.12 | 19 |
| ArkUI_NativeDialogAPI_3.setBackgroundBlurStyleOptions/setBackgroundEffect | NDK/Public | handle, options/effect | void | 无 | 背景模糊扩展/背景效果 | AC-3.13 | 19 |
| OH_ArkUI_CustomDialog_CreateOptions | NDK/Public | options* | int32_t | 无 | 创建选项对象 | AC-5.1 | 19 |
| OH_ArkUI_CustomDialog_OpenDialog | NDK/Public | options, callback, userData | int32_t | 无 | 打开对话框 | AC-5.2 | 19 |
| OH_ArkUI_CustomDialog_CloseDialog | NDK/Public | dialog | int32_t | 无 | 关闭对话框 | AC-5.3 | 19 |
| OH_ArkUI_CustomDialog_DisposeOptions | NDK/Public | options | void | 无 | 释放选项对象 | AC-5.4 | 19 |
| OH_ArkUI_CustomDialog_UpdateDialog | NDK/Public | dialog, options | int32_t | 无 | 更新对话框属性 | AC-5.5 | 19 |
| OH_ArkUI_CustomDialog_Set* 函数族 | NDK/Public | options, value | void | 无 | 属性设置函数族（SetLevelMode/SetAlignment/SetModalMode/SetAutoCancel/SetSubwindowMode/SetMask/SetBackgroundColor/SetCornerRadius/SetBorderWidth/SetBorderColor/SetBorderStyle/SetWidth/SetHeight/SetShadow/SetCustomShadow/SetBackgroundBlurStyle/SetKeyboardAvoidMode/SetHoverModeEnabled/SetHoverModeArea/RegisterOn*Callback 等） | AC-6.1 ~ AC-6.11 | 19 |
| OH_ArkUI_CustomDialog_SetBackgroundBlurStyleOptions/SetBackgroundEffect | NDK/Public | options, value | void | 无 | 背景模糊扩展/背景效果 | AC-6.8 | 19 |
| OH_ArkUI_CustomDialog_SetDisplayModeInSubWindow | NDK/Public | options, mode | void | 无 | 子窗口显示模式 | AC-6.2 | 26.0.0 |
| OH_ArkUI_CustomDialog_GetState | NDK/Public | dialog | ArkUI_DialogState | 无 | 查询弹窗状态 | AC-7.2 | 20 |
| ArkUI_DialogState | NDK/Public | — | enum | 无 | 弹窗状态枚举 | AC-7.2 | 20 |
| OH_ArkUI_DialogDisplayModeInSubWindow | NDK/Public | — | enum | 无 | 子窗口显示模式枚举 | AC-7.3, AC-7.4 | 26.0.0 |
| OH_ArkUI_NativeModule_CustomDialog_SetSystemMaterialInOptions | NDK/System | options, enable | void | 无 | 设置系统 Material（systemapi） | AC-8.1 | 26.0.0 |
| OH_ArkUI_NativeModule_CustomDialog_SetSystemMaterial | NDK/System | dialog, enable | void | 无 | 更新系统 Material（systemapi） | AC-8.2 | 26.0.0 |
| OH_ArkUI_CustomDialog_OpenDialogWithCallback | NDK/Public | options, callback, userData | int32_t | 无 | 打开对话框并返回 DialogBaseController | AC-5.6 | 26.1.0 |

### 变更/废弃 API

无变更/废弃 API。

## 接口规格

### 接口定义

**ArkUI_NativeDialogAPI_1.create**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_DialogHandle ArkUI_NativeDialogAPI_1::create()` |
| 返回值 | `ArkUI_DialogHandle` — 对话框句柄 |
| 开放范围 | NDK/Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | 无参数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 返回有效的 ArkUI_DialogHandle | AC-1.1 |
| 2 | 内存不足 | 返回 NULL | AC-1.1 |

**ArkUI_NativeDialogAPI_1.show / close / dispose**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t show(ArkUI_DialogHandle handle)` / `int32_t close(ArkUI_DialogHandle handle)` / `void dispose(ArkUI_DialogHandle handle)` |
| 返回值 | `int32_t` — 0 成功 / 非零失败 |
| 开放范围 | NDK/Public |
| 错误码 | N/A |
| 关联 AC | AC-1.4, AC-1.5, AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| handle | ArkUI_DialogHandle | 是 | — | create() 返回的句柄 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | handle 有效，调用 show | 对话框显示 | AC-1.4 |
| 2 | handle 有效，调用 close | 对话框关闭 | AC-1.5 |
| 3 | handle 有效，调用 dispose | 释放句柄资源 | AC-1.6 |
| 4 | handle 已 dispose，调用 show/close | 无效果，不崩溃 | AC-1.7 |

**OH_ArkUI_CustomDialog_OpenDialog**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_CustomDialog_OpenDialog(ArkUI_CustomDialogOptions* options, ArkUI_CustomDialogCallback callback, void* userData)` |
| 返回值 | `int32_t` — 0 成功 / 非零失败 |
| 开放范围 | NDK/Public |
| 错误码 | N/A |
| 关联 AC | AC-5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options | ArkUI_CustomDialogOptions* | 是 | — | CreateOptions 创建的选项对象 |
| callback | ArkUI_CustomDialogCallback | 是 | — | 打开结果回调，返回 dialog 实例 |
| userData | void* | 否 | NULL | 用户自定义上下文 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | options 有效 | 打开对话框，通过 callback 返回 dialog 实例 | AC-5.2 |
| 2 | options 为 NULL | 返回错误码，不崩溃 | AC-5.2 |

**OH_ArkUI_CustomDialog_GetState**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_DialogState OH_ArkUI_CustomDialog_GetState(ArkUI_CustomDialog dialog)` |
| 返回值 | `ArkUI_DialogState` — UNINITIALIZED/APPEARING/APPEARED/DISAPPEARING/DISAPPEARED |
| 开放范围 | NDK/Public |
| 错误码 | N/A |
| 关联 AC | AC-7.2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | dialog 处于未初始化状态 | 返回 UNINITIALIZED | AC-7.2 |
| 2 | dialog 处于 APPEARING 状态 | 返回 APPEARING | AC-7.2 |
| 3 | dialog 处于 APPEARED 状态 | 返回 APPEARED | AC-7.2 |
| 4 | dialog 处于 DISAPPEARING 状态 | 返回 DISAPPEARING | AC-7.2 |
| 5 | dialog 处于 DISAPPEARED 状态 | 返回 DISAPPEARED | AC-7.2 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** ArkUI_NativeDialogAPI_1 + ArkUI_DismissReason @since 12，ArkUI_NativeDialogAPI_2 @since 15，ArkUI_NativeDialogAPI_3（setLevelOrder/registerOn* 回调）@since 18，ArkUI_NativeDialogAPI_3 扩展（setBorderWidth 等）+ OH_ArkUI_CustomDialog 函数族 @since 19，OH_ArkUI_CustomDialog_GetState + ArkUI_DialogState @since 20，OH_ArkUI_DialogDisplayModeInSubWindow + OH_ArkUI_NativeModule_CustomDialog_SetSystemMaterialInOptions/SetSystemMaterial @since 26.0.0，OH_ArkUI_CustomDialog_OpenDialogWithCallback @since 26.1.0

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 共享 Pattern | C API 底层复用 DialogPattern 实现 | AC-1.1 |
| 版本分片 | ArkUI_NativeDialogAPI_1/_2/_3 分版本暴露，通过结构体版本号区分 | AC-1.1 ~ AC-4.4 |
| node_modifier 委托 | `dialog_modifier.cpp` 作为 C++ 属性委托层，桥接 C API 到 DialogLayoutProperty | AC-2.1 ~ AC-3.13 |
| Options 模式 | OH_ArkUI_CustomDialog 函数族使用 CreateOptions + Set* + OpenDialog 模式 | AC-5.1 ~ AC-6.11 |
| 不暴露为节点类型 | Dialog 不暴露为 ArkUI_NodeType，通过独立 C 接口族提供服务 | AC-1.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | C API 对话框打开/关闭动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | dispose/DisposeOptions 后句柄和选项资源释放 | C API UT + Dump | dialog_extender_accessor_test |
| 安全 | systemapi 接口（SetSystemMaterial*）仅系统应用可调用 | 权限审查 | — |
| 可靠性 | C API Create/Show/Close/Dispose 生命周期完整，无资源泄漏 | C API UT | capi accessor 单测 |
| 可靠性 | 对已释放 handle/options 操作不崩溃 | C API UT | dialog_extender_accessor_test |
| 问题定位 | hilog 标签覆盖 C API 创建/显示/关闭/回调 | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | enableHoverMode/setHoverModeArea（@since 19）支持悬浮态 | C API UT | capi accessor 单测 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | C API 弹窗无障碍共享 DialogPattern 实现（见 Feat-01） | — |
| 大字体 | 是 | C API 弹窗内容跟随系统字体缩放 | AC-1.1 |
| 深色模式 | 是 | C API 颜色属性支持主题跟随 | AC-2.6 |
| 多窗口/分屏 | 是 | SetSubwindowMode/SetDisplayModeInSubWindow 支持子窗口模式 | AC-6.2 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 12/15/18/19/20/26.0.0/26.1.0 各版本新增 C API 需兼容性处理 | AC-1.1, AC-3.5, AC-5.6 |
| 生态兼容 | 是 | C API 分版本暴露（_1/_2/_3 和 OH_ArkUI_CustomDialog_*），需在文档中明确各版本能力差异 | AC-1.1 ~ AC-8.2 |

## 行为场景（Gherkin）

```gherkin
Feature: Dialog C API
  作为 NDK 开发者
  我想要通过 C API 创建和控制对话框
  以便在 Native 层集成对话框功能

  Scenario: ArkUI_NativeDialogAPI_1 基础生命周期
    Given 调用 ArkUI_NativeDialogAPI_1.create()
    Then 返回 ArkUI_DialogHandle
    When 调用 setContent(handle, contentNode)
    Then 内容节点设置成功
    When 调用 show(handle)
    Then 对话框显示
    When 调用 close(handle)
    Then 对话框关闭
    When 调用 dispose(handle)
    Then 句柄资源释放

  Scenario: 已释放句柄操作安全
    Given handle 已 dispose
    When 调用 show(handle) 或 close(handle)
    Then 无效果，不崩溃

  Scenario: ArkUI_NativeDialogAPI 版本分片
    Given API 12 环境
    When 获取 ArkUI_NativeDialogAPI_1
    Then 可调用 create/show/close 等基础方法
    Given API 15 环境
    When 获取 ArkUI_NativeDialogAPI_2
    Then 可调用 setKeyboardAvoidDistance/setLevelMode 等扩展方法
    Given API 18 环境
    When 获取 ArkUI_NativeDialogAPI_3
    Then 可调用 setLevelOrder/registerOn* 回调

  Scenario: OH_ArkUI_CustomDialog 函数族
    Given 调用 OH_ArkUI_CustomDialog_CreateOptions(&options)
    Then 创建选项对象
    When 调用 Set* 函数族设置属性
    Then 属性写入 options
    When 调用 OH_ArkUI_CustomDialog_OpenDialog(options, callback, userData)
    Then 打开对话框并通过 callback 返回 dialog 实例
    When 调用 OH_ArkUI_CustomDialog_GetState(dialog)
    Then 返回 ArkUI_DialogState 枚举值
    When 调用 OH_ArkUI_CustomDialog_CloseDialog(dialog)
    Then 对话框关闭
    When 调用 OH_ArkUI_CustomDialog_DisposeOptions(options)
    Then 选项对象资源释放

  Scenario Outline: ArkUI_DismissReason 关闭原因
    Given 对话框已打开且注册了 onWillDismiss
    When 用户通过 <trigger> 触发关闭
    Then 回调接收 reason=<reason>

    Examples:
      | trigger        | reason        |
      | 返回键         | BACK_PRESS(0) |
      | 点击遮罩       | TOUCH_OUTSIDE(1) |
      | 关闭按钮       | CLOSE_BUTTON(2) |
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
    query: "ArkUI_NativeDialogAPI_1/2/3 C API create/dispose/show/close/setContent 和版本分片实现"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_CustomDialog 函数族 OpenDialog/CloseDialog/CreateOptions/DisposeOptions/UpdateDialog 实现"
  - repo: "openharmony/ace_engine"
    query: "dialog_model.cpp 和 dialog_option.cpp C API 属性委托实现"
  - repo: "openharmony/ace_engine"
    query: "dialog_modifier.cpp node_modifier 委托层和 GetCustomDialogControllerModel 实现"
  - repo: "openharmony/ace_engine"
    query: "ArkUI_DismissReason/ArkUI_DialogState/OH_ArkUI_DialogDisplayModeInSubWindow 枚举定义"
```

**关键文档:**
- C API 头文件: `interface/sdk-js/api/arkui/native/native_dialog.h`
- KB 路由: `docs/kb/components/overlay/dialog.md`
- 源码入口 (C API Model): `interfaces/native/node/dialog_model.cpp`
- 源码入口 (C API Option): `interfaces/native/node/dialog_option.cpp`
- 源码入口 (node_modifier): `frameworks/core/interfaces/native/node/dialog_modifier.cpp`
- NAPI (promptAction): `interfaces/napi/kits/promptaction/js_prompt_action.cpp`
- NAPI (arkui.dialog): `interfaces/napi/kits/dialog/js_dialog.cpp`
- 测试 (Dialog Extender): `test/unittest/capi/accessors/dialog_extender_accessor_test.cpp`
- 测试 (CustomDialog Controller): `test/unittest/capi/accessors/custom_dialog_controller_accessor_test.cpp`
- 测试 (AlertDialog): `test/unittest/capi/accessors/alert_dialog_accessor_test.cpp`
