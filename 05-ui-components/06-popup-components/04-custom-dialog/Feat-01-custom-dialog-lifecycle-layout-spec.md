# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | CustomDialogController 生命周期与布局属性及命令式弹窗 API（状态机、布局定位、多层级、悬浮态、样式定制、模态焦点、动画、无障碍、promptAction/UIContext/arkui.dialog 命令式 API） |
| 特性编号 | Func-05-06-04-Feat-01 |
| FuncID | 05-06-04 |
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
| ADDED | CustomDialogController（open/close） | @since 7 |
| ADDED | CustomDialogControllerOptions: builder/cancel/autoCancel/alignment/offset/customStyle | @since 7 |
| ADDED | gridCount 属性 | @since 8 |
| ADDED | maskColor, maskRect, openAnimation, closeAnimation, showInSubWindow, backgroundColor, cornerRadius 属性 | @since 10 |
| ADDED | isModal 属性 | @since 11 |
| ADDED | promptAction.openCustomDialog（Promise\<number\>）/closeCustomDialog | @since 11，@since 18 标记废弃 |
| ADDED | onWillDismiss, width, height, borderWidth, borderColor, borderStyle, shadow, backgroundBlurStyle, keyboardAvoidMode, transition 属性 | @since 12 |
| ADDED | promptAction.updateCustomDialog | @since 12 |
| ADDED | UIContext.getPromptAction().openCustomDialog/closeCustomDialog/updateCustomDialog | @since 12 |
| ADDED | enableHoverMode, hoverModeArea 属性 | @since 14 |
| ADDED | keyboardAvoidDistance, levelMode, levelUniqueId, immersiveMode 属性 | @since 15 |
| ADDED | levelOrder 属性 | @since 18 |
| ADDED | promptAction.openCustomDialogWithController/presentCustomDialog | @since 18 |
| ADDED | UIContext.getPromptAction().openCustomDialogWithController/presentCustomDialog | @since 18 |
| ADDED | focusable 属性 | @since 19 |
| ADDED | onDidAppear, onDidDisappear, onWillAppear, onWillDisappear 回调 | @since 19 |
| ADDED | backgroundBlurStyleOptions, backgroundEffect 属性 | @since 19 |
| ADDED | dialogTransition, maskTransition 属性 | @since 19 |
| ADDED | getState() 方法 | @since 20 |
| ADDED | systemMaterial 属性 | @since 26 |
| ADDED | displayModeInSubWindow 属性 | @since 26.0.0 |
| ADDED | distortionMode, edgeLightMode 属性（systemapi） | @since 26 |
| ADDED | arkui.dialog 统一命名空间（presentDialog/presentCustomDialog/updateCustomDialog/dismissDialog） | @since 26.1.0 |
| ADDED | DialogBaseController 类（close/getState） | @since 26.1.0 |
| ADDED | DialogStyleOptions/DialogCustomOptions 接口 | @since 26.1.0 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/04-custom-dialog/design.md`
- **KB 路由**: `docs/kb/components/overlay/dialog.md`
- **SDK 类型定义**:
  - Dynamic API (CustomDialog): `interface/sdk-js/api/@internal/component/ets/custom_dialog.d.ts`
  - Dynamic API (AlertDialog): `interface/sdk-js/api/@internal/component/ets/alert_dialog.d.ts`
  - Dynamic API (ActionSheet): `interface/sdk-js/api/@internal/component/ets/action_sheet.d.ts`
  - Dynamic API (promptAction): `interface/sdk-js/api/@ohos.promptAction.d.ts`
  - Dynamic API (arkui.dialog): `interface/sdk-js/api/@ohos.arkui.dialog.d.ts`
- **NAPI 实现入口**:
  - promptAction: `interfaces/napi/kits/promptaction/js_prompt_action.cpp`
  - arkui.dialog: `interfaces/napi/kits/dialog/js_dialog.cpp`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: CustomDialog 基础生命周期

**角色**: 应用开发者
**期望**: 我想要使用 CustomDialogController 控制自定义对话框的打开和关闭
**价值**: 以便在应用中显示自定义内容的模态对话框

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `new CustomDialogController({ builder: this.CustomContent })` THEN 控制器持有对话框引用，不立即显示 | 正常 |
| AC-1.2 | WHEN 调用 `controller.open()` THEN DialogView::CreateDialogNode 创建对话框节点，DialogPattern 状态机进入 APPEARING 状态 | 正常 |
| AC-1.3 | WHEN 调用 `controller.close()` THEN DialogPattern 状态机进入 DISAPPEARING 状态，动画完成后卸载 overlay 节点 | 正常 |
| AC-1.4 | WHEN 已 open 的对话框重复调用 `controller.open()` THEN 无效果（状态不变） | 异常 |
| AC-1.5 | WHEN 已 close 的对话框重复调用 `controller.close()` THEN 无效果（状态不变） | 异常 |
| AC-1.6 | WHEN 调用 `controller.getState()`（@since 20）THEN 返回当前状态（CLOSED/OPENING/OPEN/CLOSING） | 正常 |

### US-2: 状态机与生命周期回调

**角色**: 应用开发者
**期望**: 我想要在对话框出现/消失的各阶段执行回调
**价值**: 以便在对话框生命周期的关键节点执行业务逻辑

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN DialogPattern 进入 APPEARING 状态 THEN 触发 onWillAppear 回调（@since 19） | 正常 |
| AC-2.2 | WHEN DialogPattern 进入 APPEARED 状态 THEN 触发 onDidAppear 回调（@since 19） | 正常 |
| AC-2.3 | WHEN DialogPattern 进入 DISAPPEARING 状态 THEN 触发 onWillDisappear 回调（@since 19） | 正常 |
| AC-2.4 | WHEN DialogPattern 进入 DISAPPEARED 状态 THEN 触发 onDidDisappear 回调（@since 19） | 正常 |
| AC-2.5 | WHEN 用户点击遮罩区域且 autoCancel=true THEN 触发 onWillDismiss 回调（@since 12），开发者可通过 DismissDialogAction 决定是否关闭 | 正常 |
| AC-2.6 | WHEN onWillDismiss 回调中调用 DismissDialogAction.dismiss() THEN 对话框继续关闭 | 正常 |
| AC-2.7 | WHEN onWillDismiss 回调中不调用 dismiss() THEN 对话框保持打开 | 正常 |
| AC-2.8 | WHEN 对话框从 APPEARING 直接调用 close() THEN 状态跳转到 DISAPPEARING，跳过 APPEARED | 异常 |

### US-3: 对话框布局与定位

**角色**: 应用开发者
**期望**: 我想要控制对话框的位置、尺寸和栅格宽度
**价值**: 以便对话框在不同场景下正确布局

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `alignment: DialogAlignment.Center` THEN 对话框居中显示 | 正常 |
| AC-3.2 | WHEN 设置 `alignment: DialogAlignment.Bottom` THEN 对话框底部显示 | 正常 |
| AC-3.3 | WHEN 设置 `offset: { dx: 10, dy: 20 }` THEN 对话框在 alignment 基础上偏移 dx=10vp, dy=20vp | 正常 |
| AC-3.4 | WHEN 设置 `gridCount: 4`（@since 8）THEN 对话框宽度按 4 栅格列计算 | 正常 |
| AC-3.5 | WHEN 设置 `width: 300, height: 400`（@since 12）THEN 对话框尺寸为 300vp × 400vp | 正常 |
| AC-3.6 | WHEN 设置 `keyboardAvoidMode: KeyboardAvoidMode.TRANSLATE`（@since 12）THEN 软键盘弹出时对话框上移避让 | 正常 |
| AC-3.7 | WHEN 设置 `keyboardAvoidMode: KeyboardAvoidMode.RESIZE`（@since 12）THEN 软键盘弹出时对话框缩小避让 | 正常 |
| AC-3.8 | WHEN 设置 `keyboardAvoidDistance: 20`（@since 15）THEN 对话框与软键盘保持 20vp 距离 | 正常 |

### US-4: 多层级对话框

**角色**: 应用开发者
**期望**: 我想要控制对话框的层级模式、唯一标识和 Z 序
**价值**: 以便管理多个嵌套对话框的显示层次

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `levelMode: LevelMode.OVERLAY`（@since 15）THEN 对话框通过 OverlayManager 挂载（默认行为） | 正常 |
| AC-4.2 | WHEN 设置 `levelMode: LevelMode.EMBEDDED` 和 `levelUniqueId: 123`（@since 15）THEN 对话框嵌入到指定父节点（levelUniqueId=123）下 | 正常 |
| AC-4.3 | WHEN 设置 `levelOrder: 5`（@since 18）THEN 同层级对话框中 Z 序为 5 | 正常 |
| AC-4.4 | WHEN 设置 `immersiveMode: ImmersiveMode.ENABLE`（@since 15）THEN 对话框启用沉浸式模式 | 正常 |
| AC-4.5 | WHEN 设置 `immersiveMode: ImmersiveMode.DISABLE`（@since 15）THEN 对话框禁用沉浸式模式（默认） | 正常 |

### US-5: 悬浮态支持

**角色**: 应用开发者
**期望**: 我想要对话框在折叠屏悬浮态正确显示
**价值**: 以便折叠屏用户获得一致的对话框体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 `enableHoverMode: true`（@since 14）THEN 折叠屏悬浮态时对话框正确显示 | 正常 |
| AC-5.2 | WHEN 设置 `hoverModeArea: HoverModeAreaType.HALF_SCREEN`（@since 14）THEN 对话框在半屏区域显示 | 正常 |
| AC-5.3 | WHEN 未设置 enableHoverMode THEN 折叠屏悬浮态使用默认行为 | 正常 |

### US-6: 样式定制

**角色**: 应用开发者
**期望**: 我想要自定义对话框的背景色、圆角、边框、阴影和模糊效果
**价值**: 以便对话框外观与应用设计语言一致

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 `backgroundColor: Color.White`（@since 10）THEN 对话框背景色为白色 | 正常 |
| AC-6.2 | WHEN 设置 `cornerRadius: 20`（@since 10）THEN 对话框圆角为 20vp | 正常 |
| AC-6.3 | WHEN 设置 `borderWidth: { width: 1 }, borderColor: Color.Gray, borderStyle: BorderStyle.Solid`（@since 12）THEN 对话框显示 1vp 灰色实线边框 | 正常 |
| AC-6.4 | WHEN 设置 `shadow: { radius: 10, color: Color.Black }`（@since 12）THEN 对话框显示阴影 | 正常 |
| AC-6.5 | WHEN 设置 `backgroundBlurStyle: BlurStyle.Regular`（@since 12）THEN 对话框背景应用 Regular 模糊效果 | 正常 |
| AC-6.6 | WHEN 设置 `maskColor: Color.Black`（@since 10）THEN 遮罩颜色为黑色 | 正常 |
| AC-6.7 | WHEN 设置 `maskRect: { x: 0, y: 0, width: '100%', height: '100%' }`（@since 10）THEN 遮罩区域为全屏 | 正常 |
| AC-6.8 | WHEN 设置 `customStyle: true` THEN 对话框使用自定义样式，不应用默认主题样式 | 正常 |
| AC-6.9 | WHEN 设置 `systemMaterial: true`（@since 26）THEN 对话框使用系统 Material 效果 | 正常 |

### US-7: 模态与焦点

**角色**: 应用开发者
**期望**: 我想要控制对话框的模态行为和可聚焦性
**价值**: 以便管理对话框与底层内容的交互

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 `isModal: true`（@since 11）THEN 对话框为模态，遮罩拦截底层事件 | 正常 |
| AC-7.2 | WHEN 设置 `isModal: false`（@since 11）THEN 对话框为非模态，底层可交互 | 正常 |
| AC-7.3 | WHEN 设置 `focusable: true`（@since 19）THEN 对话框可获取焦点 | 正常 |
| AC-7.4 | WHEN 设置 `focusable: false`（@since 19）THEN 对话框不可获取焦点 | 正常 |
| AC-7.5 | WHEN 设置 `autoCancel: true` THEN 点击遮罩区域关闭对话框 | 正常 |
| AC-7.6 | WHEN 设置 `autoCancel: false` THEN 点击遮罩区域不关闭对话框 | 正常 |

### US-8: 动画定制

**角色**: 应用开发者
**期望**: 我想要自定义对话框的打开和关闭动画
**价值**: 以便对话框动画与应用过渡风格一致

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 设置 `openAnimation: { ... }`（@since 10）THEN 对话框打开时使用自定义动画 | 正常 |
| AC-8.2 | WHEN 设置 `closeAnimation: { ... }`（@since 10）THEN 对话框关闭时使用自定义动画 | 正常 |
| AC-8.3 | WHEN 未设置 openAnimation/closeAnimation THEN 使用默认出现/消失动画 | 正常 |
| AC-8.4 | WHEN 设置 `showInSubWindow: true`（@since 10）THEN 对话框在独立子窗口显示 | 正常 |

### US-9: 无障碍与 API 版本兼容

**角色**: 辅助功能用户 / 应用开发者
**期望**: 我想要通过无障碍服务操作对话框，并了解不同 API 版本的行为差异
**价值**: 以便辅助功能用户完成对话框交互，开发者适配不同版本

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 无障碍服务查询对话框 THEN 报告角色为 Dialog | 正常 |
| AC-9.2 | WHEN 无障碍服务执行 ActionDismiss THEN 对话框关闭 | 正常 |
| AC-9.3 | WHEN API < 10 THEN maskColor/maskRect/openAnimation/closeAnimation/showInSubWindow/backgroundColor/cornerRadius 属性不可用 | 边界 |
| AC-9.4 | WHEN API < 12 THEN onWillDismiss/width/height/borderWidth/shadow/backgroundBlurStyle/keyboardAvoidMode/transition 属性不可用 | 边界 |

### US-10: promptAction 命令式自定义弹窗

**角色**: 应用开发者
**期望**: 我想要通过 promptAction 命令式 API 打开、更新和关闭自定义弹窗
**价值**: 以便在不使用 @CustomDialog 装饰器的场景下命令式地控制弹窗

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 `promptAction.openCustomDialog({ builder: this.CustomContent })`（@since 11）THEN 返回 Promise\<number\>，resolve 为 dialogId，对话框显示 | 正常 |
| AC-10.2 | WHEN 调用 `promptAction.openCustomDialog({ componentContent: content })`（@since 11）THEN 使用 ComponentContent 作为弹窗内容，返回 dialogId | 正常 |
| AC-10.3 | WHEN 调用 `promptAction.closeCustomDialog(dialogId)`（@since 11）THEN 根据 dialogId 关闭对应对话框 | 正常 |
| AC-10.4 | WHEN API >= 18 调用 `promptAction.openCustomDialog` THEN 标记为 @deprecated，推荐使用 openCustomDialogWithController | 边界 |
| AC-10.5 | WHEN 调用 `promptAction.openCustomDialogWithController({ nodePtr, controller })`（@since 18）THEN 基于 FrameNode 和 PromptDialogController 显示对话框 | 正常 |
| AC-10.6 | WHEN 调用 `promptAction.presentCustomDialog({ builder, controller, options })`（@since 18）THEN 使用 DialogStyleOptions 样式选项显示对话框 | 正常 |
| AC-10.7 | WHEN 调用 `promptAction.updateCustomDialog({ dialogId, alignment, offset, autoCancel, maskColor })`（@since 12）THEN 已显示对话框的 alignment/offset/autoCancel/maskColor 属性被更新 | 正常 |
| AC-10.8 | WHEN 调用 `promptAction.updateCustomDialog` 传入不存在的 dialogId THEN 无效果，不崩溃 | 异常 |

### US-11: UIContext 命令式自定义弹窗

**角色**: 应用开发者
**期望**: 我想要通过 UIContext.getPromptAction() 命令式 API 在指定 UI 上下文中管理弹窗
**价值**: 以便多窗口/多实例场景下精确绑定弹窗到对应 UIContext

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-11.1 | WHEN 调用 `uiContext.getPromptAction().openCustomDialog(options)`（@since 12）THEN 在该 UIContext 对应的窗口中显示对话框，返回 dialogId | 正常 |
| AC-11.2 | WHEN 调用 `uiContext.getPromptAction().openCustomDialogWithController(options)`（@since 18）THEN 在该 UIContext 中基于 FrameNode+Controller 显示对话框 | 正常 |
| AC-11.3 | WHEN 调用 `uiContext.getPromptAction().presentCustomDialog(options)`（@since 18）THEN 在该 UIContext 中使用样式选项显示对话框 | 正常 |
| AC-11.4 | WHEN 调用 `uiContext.getPromptAction().updateCustomDialog(options)`（@since 12）THEN 在该 UIContext 中更新已显示对话框属性 | 正常 |
| AC-11.5 | WHEN 调用 `uiContext.getPromptAction().closeCustomDialog(dialogId)`（@since 12）THEN 在该 UIContext 中根据 dialogId 关闭对话框 | 正常 |

### US-12: arkui.dialog 统一弹窗命名空间

**角色**: 应用开发者
**期望**: 我想要通过 arkui.dialog 统一命名空间命令式地管理弹窗
**价值**: 以便使用最新统一 API 简化弹窗调用并支持属性弹窗和遮罩弹窗

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-12.1 | WHEN 调用 `arkui.dialog.presentDialog(params)`（@since 26.1.0）THEN 解析 DialogParams，通过 OverlayManager 或 SubwindowManager 显示对话框 | 正常 |
| AC-12.2 | WHEN 调用 `arkui.dialog.presentCustomDialog(params)`（@since 26.1.0）THEN 解析 builder + DialogOptions，显示命令式自定义弹窗 | 正常 |
| AC-12.3 | WHEN 调用 `arkui.dialog.updateCustomDialog(options)`（@since 26.1.0）THEN 通过 OverlayManager::UpdateCustomDialog 更新已显示弹窗属性 | 正常 |
| AC-12.4 | WHEN 调用 `arkui.dialog.dismissDialog({ dialogId })`（@since 26.1.0）THEN 根据 DialogId 关闭对话框 | 正常 |
| AC-12.5 | WHEN 调用 `arkui.dialog.dismissDialog({ frameNode })`（@since 26.1.0）THEN 根据 FrameNode 关闭关联对话框 | 正常 |

### US-13: DialogBaseController 统一控制器

**角色**: 应用开发者
**期望**: 我想要通过 DialogBaseController 统一控制器关闭弹窗并查询状态
**价值**: 以便使用统一控制器接口管理不同来源的弹窗实例

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-13.1 | WHEN 获取 DialogBaseController 实例后调用 `controller.close()`（@since 26.1.0）THEN 对话框关闭 | 正常 |
| AC-13.2 | WHEN 调用 `controller.getState()`（@since 26.1.0）THEN 返回 ArkUI_DialogState 枚举值（UNINITIALIZED/APPEARING/APPEARED/DISAPPEARING/DISAPPEARED） | 正常 |
| AC-13.3 | WHEN 使用 DialogStyleOptions 接口（@since 26.1.0）配置样式 THEN presentDialog/presentCustomDialog 按 DialogStyleOptions 渲染弹窗样式 | 正常 |
| AC-13.4 | WHEN 使用 DialogCustomOptions 接口（@since 26.1.0）配置自定义内容 THEN presentCustomDialog 按 DialogCustomOptions 构建 builder 和 controller | 正常 |

### US-14: 扩展样式与过渡属性

**角色**: 应用开发者
**期望**: 我想要使用 transition、backgroundBlurStyleOptions、backgroundEffect 等扩展属性控制弹窗过渡和视觉效果
**价值**: 以便弹窗视觉表现更丰富、过渡动画更灵活

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-14.1 | WHEN 设置 `transition: TransitionEffect.OPACITY`（@since 12）THEN 对话框使用 TransitionEffect 定义的出现/消失过渡 | 正常 |
| AC-14.2 | WHEN 设置 `backgroundBlurStyleOptions: { adaptiveColor, scale, policy, inactiveMode, ... }`（@since 19）THEN 对话框背景模糊使用扩展选项 | 正常 |
| AC-14.3 | WHEN 设置 `backgroundEffect: { radius, saturation, brightness, ... }`（@since 19）THEN 对话框应用背景效果（半径/饱和度/亮度） | 正常 |
| AC-14.4 | WHEN 设置 `dialogTransition` 和 `maskTransition`（@since 19）THEN 对话框内容和遮罩分别使用独立过渡动画 | 正常 |
| AC-14.5 | WHEN 设置 `displayModeInSubWindow: DialogDisplayModeInSubWindow.SCREEN_BASED`（@since 26.0.0）THEN 子窗口弹窗以屏幕为基准显示 | 正常 |
| AC-14.6 | WHEN 设置 `displayModeInSubWindow: DialogDisplayModeInSubWindow.WINDOW_BASED`（@since 26.0.0）THEN 子窗口弹窗以窗口为基准显示 | 正常 |
| AC-14.7 | WHEN 设置 `distortionMode`（@since 26，systemapi）THEN 对话框应用指定形变模式 | 正常 |
| AC-14.8 | WHEN 设置 `edgeLightMode`（@since 26，systemapi）THEN 对话框边缘光效模式生效 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.6 | R-1, R-2, R-3, R-4, R-24 | TASK-DIALOG-01 | UT | `test/unittest/core/pattern/dialog/` |
| AC-2.1 ~ AC-2.8 | R-5, R-6, R-7, R-8, R-23, R-25 | TASK-DIALOG-01 | UT | dialog_pattern_test |
| AC-3.1 ~ AC-3.8 | R-9, R-10, R-11 | TASK-DIALOG-01 | UT | dialog_layout_test |
| AC-4.1 ~ AC-4.5 | R-12, R-13 | TASK-DIALOG-01 | UT + 手工 | 多层级对话框测试 |
| AC-5.1 ~ AC-5.3 | R-14 | TASK-DIALOG-01 | 手工 | 悬浮态测试 |
| AC-6.1 ~ AC-6.9 | R-15, R-16 | TASK-DIALOG-01 | UT | 样式属性测试 |
| AC-7.1 ~ AC-7.6 | R-17, R-18, R-26 | TASK-DIALOG-01 | UT | 模态/焦点测试 |
| AC-8.1 ~ AC-8.4 | R-19, R-20 | TASK-DIALOG-01 | UT + 手工 | 动画测试 |
| AC-9.1 ~ AC-9.4 | R-21, R-22 | TASK-DIALOG-01 | UT | 无障碍/版本兼容测试 |
| AC-10.1 ~ AC-10.8 | R-27, R-28, R-29 | TASK-DIALOG-01 | UT | js_prompt_action 单测 |
| AC-11.1 ~ AC-11.5 | R-30 | TASK-DIALOG-01 | UT | UIContext promptAction 单测 |
| AC-12.1 ~ AC-12.5 | R-31 | TASK-DIALOG-01 | UT | js_dialog 单测 |
| AC-13.1 ~ AC-13.4 | R-32 | TASK-DIALOG-01 | UT | DialogBaseController 单测 |
| AC-14.1 ~ AC-14.8 | R-33, R-34, R-35, R-36, R-37 | TASK-DIALOG-01 | UT | 扩展样式属性测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `custom_dialog_controller_model_ng.cpp` open() | 调用 DialogView::CreateDialogNode 创建节点，DialogPattern 状态机进入 APPEARING | — | AC-1.2 |
| R-2 | 行为 | `dialog_pattern.cpp` close() | DialogPattern 状态机进入 DISAPPEARING，动画完成后卸载 overlay 节点 | — | AC-1.3 |
| R-3 | 异常 | `custom_dialog_controller_model_ng.cpp` 重复 open | 已 open 的对话框重复调用 open() 无效 | 状态不变 | AC-1.4 |
| R-4 | 异常 | `custom_dialog_controller_model_ng.cpp` 重复 close | 已 close 的对话框重复调用 close() 无效 | 状态不变 | AC-1.5 |
| R-5 | 行为 | `dialog_pattern.cpp` 状态机 APPEARING | 进入 APPEARING 时触发 onWillAppear 回调 | @since 19 | AC-2.1 |
| R-6 | 行为 | `dialog_pattern.cpp` 状态机 APPEARED | 进入 APPEARED 时触发 onDidAppear 回调 | @since 19 | AC-2.2 |
| R-7 | 行为 | `dialog_pattern.cpp` 状态机 DISAPPEARING | 进入 DISAPPEARING 时触发 onWillDisappear 回调 | @since 19 | AC-2.3 |
| R-8 | 行为 | `dialog_pattern.cpp` 状态机 DISAPPEARED | 进入 DISAPPEARED 时触发 onDidDisappear 回调 | @since 19 | AC-2.4 |
| R-9 | 行为 | `dialog_layout_algorithm.cpp` 布局 | alignment 控制对齐；offset 控制偏移；gridCount 控制栅格宽度；width/height 控制显式尺寸 | gridCount @since 8, width/height @since 12 | AC-3.1 ~ AC-3.5 |
| R-10 | 行为 | `dialog_layout_algorithm.cpp` 键盘避让 | keyboardAvoidMode 控制避让模式（NONE/TRANSLATE/RESIZE） | @since 12 | AC-3.6, AC-3.7 |
| R-11 | 行为 | `dialog_layout_algorithm.cpp` 避让距离 | keyboardAvoidDistance 控制对话框与软键盘的距离 | @since 15 | AC-3.8 |
| R-12 | 行为 | `dialog_pattern.cpp` levelMode | OVERLAY 通过 OverlayManager 挂载；EMBEDDED 挂载到指定父节点（levelUniqueId） | @since 15 | AC-4.1, AC-4.2 |
| R-13 | 行为 | `dialog_pattern.cpp` levelOrder/immersiveMode | levelOrder 控制同层级 Z 序；immersiveMode 控制沉浸式模式 | levelOrder @since 18, immersiveMode @since 15 | AC-4.3 ~ AC-4.5 |
| R-14 | 行为 | `dialog_pattern.cpp` enableHoverMode/hoverModeArea | 折叠屏悬浮态对话框正确显示 | @since 14 | AC-5.1 ~ AC-5.3 |
| R-15 | 行为 | `dialog_layout_property.h` 样式属性 | backgroundColor/cornerRadius/borderWidth/borderColor/borderStyle/shadow/backgroundBlurStyle/maskColor/maskRect/customStyle | 样式属性 @since 10/12 | AC-6.1 ~ AC-6.8 |
| R-16 | 行为 | `dialog_layout_property.h` systemMaterial | 对话框使用系统 Material 效果 | @since 26 | AC-6.9 |
| R-17 | 行为 | `dialog_pattern.cpp` isModal | true 模态（遮罩拦截）；false 非模态（底层可交互） | @since 11 | AC-7.1, AC-7.2 |
| R-18 | 行为 | `dialog_pattern.cpp` focusable | 控制对话框是否可获取焦点 | @since 19 | AC-7.3, AC-7.4 |
| R-19 | 行为 | `dialog_pattern.cpp` openAnimation/closeAnimation | 自定义打开/关闭动画 | @since 10 | AC-8.1 ~ AC-8.3 |
| R-20 | 行为 | `dialog_pattern.cpp` showInSubWindow | 对话框在独立子窗口显示 | @since 10 | AC-8.4 |
| R-21 | 行为 | `dialog_accessibility_property.cpp` | 报告角色 Dialog，支持 ActionDismiss | — | AC-9.1, AC-9.2 |
| R-22 | 边界 | API 版本兼容 | @since 10/11/12/14/15/18/19/20/26 各版本新增属性在旧版本不可用 | — | AC-9.3, AC-9.4 |
| R-23 | 行为 | `dialog_pattern.cpp` onWillDismiss | 关闭请求时触发，开发者通过 DismissDialogAction 决定是否关闭 | @since 12 | AC-2.5 ~ AC-2.7 |
| R-24 | 行为 | `dialog_event_hub.cpp` getState | 返回当前状态 CLOSED/OPENING/OPEN/CLOSING | @since 20 | AC-1.6 |
| R-25 | 异常 | `dialog_pattern.cpp` 状态跳跃 | 从 APPEARING 直接 close() 时跳转到 DISAPPEARING，跳过 APPEARED | — | AC-2.8 |
| R-26 | 恢复 | `dialog_pattern.cpp` autoCancel | autoCancel=true 时点击遮罩关闭；false 时不关闭 | 默认 true | AC-7.5, AC-7.6 |
| R-27 | 行为 | `js_prompt_action.cpp` openCustomDialog/closeCustomDialog | NAPI 命令式 API，openCustomDialog 返回 Promise\<dialogId\>，closeCustomDialog 按 dialogId 关闭 | @since 11，@since 18 标记废弃 | AC-10.1 ~ AC-10.4 |
| R-28 | 行为 | `js_prompt_action.cpp` openCustomDialogWithController/presentCustomDialog | 基于 FrameNode+Controller 和 DialogStyleOptions 的命令式弹窗 | @since 18 | AC-10.5, AC-10.6 |
| R-29 | 行为 | `js_prompt_action.cpp` updateCustomDialog | 更新已显示对话框的 alignment/offset/autoCancel/maskColor | @since 12 | AC-10.7, AC-10.8 |
| R-30 | 行为 | `js_prompt_action.cpp` UIContext.getPromptAction() 命令式 API | openCustomDialog/openCustomDialogWithController/presentCustomDialog/updateCustomDialog/closeCustomDialog 绑定到指定 UIContext | @since 12/18 | AC-11.1 ~ AC-11.5 |
| R-31 | 行为 | `js_dialog.cpp` arkui.dialog 命名空间 | presentDialog/presentCustomDialog/updateCustomDialog/dismissDialog 统一命令式 API，直接操作 OverlayManager/DialogManager | @since 26.1.0 | AC-12.1 ~ AC-12.5 |
| R-32 | 行为 | `js_dialog.cpp` DialogBaseController | close() 关闭弹窗；getState() 返回 ArkUI_DialogState；DialogStyleOptions/DialogCustomOptions 配置样式和内容 | @since 26.1.0 | AC-13.1 ~ AC-13.4 |
| R-33 | 行为 | `dialog_layout_property.h` transition | 使用 TransitionEffect 定义出现/消失过渡 | @since 12 | AC-14.1 |
| R-34 | 行为 | `dialog_layout_property.h` backgroundBlurStyleOptions/backgroundEffect | 扩展背景模糊选项和背景效果（半径/饱和度/亮度） | @since 19 | AC-14.2, AC-14.3 |
| R-35 | 行为 | `dialog_layout_property.h` dialogTransition/maskTransition | 对话框内容和遮罩分别使用独立过渡动画 | @since 19 | AC-14.4 |
| R-36 | 行为 | `dialog_layout_property.h` displayModeInSubWindow | SCREEN_BASED 以屏幕为基准；WINDOW_BASED 以窗口为基准 | @since 26.0.0 | AC-14.5, AC-14.6 |
| R-37 | 行为 | `dialog_layout_property.h` distortionMode/edgeLightMode | 形变模式和边缘光效模式（systemapi） | @since 26，systemapi | AC-14.7, AC-14.8 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.6 | UT | CustomDialogController 生命周期和状态查询 |
| VM-2 | AC-2.1 ~ AC-2.8 | UT | 状态机四态转换和生命周期回调 |
| VM-3 | AC-3.1 ~ AC-3.8 | UT | 对话框布局与键盘避让 |
| VM-4 | AC-4.1 ~ AC-4.5 | UT + 手工 | 多层级对话框 |
| VM-5 | AC-5.1 ~ AC-5.3 | 手工 | 悬浮态支持 |
| VM-6 | AC-6.1 ~ AC-6.9 | UT | 样式定制 |
| VM-7 | AC-7.1 ~ AC-7.6 | UT | 模态与焦点 |
| VM-8 | AC-8.1 ~ AC-8.4 | UT + 手工 | 动画定制 |
| VM-9 | AC-9.1 ~ AC-9.4 | UT | 无障碍与版本兼容 |
| VM-10 | AC-10.1 ~ AC-10.8 | UT | promptAction 命令式自定义弹窗 API |
| VM-11 | AC-11.1 ~ AC-11.5 | UT | UIContext 命令式自定义弹窗 API |
| VM-12 | AC-12.1 ~ AC-12.5 | UT | arkui.dialog 统一弹窗命名空间 |
| VM-13 | AC-13.1 ~ AC-13.4 | UT | DialogBaseController 统一控制器 |
| VM-14 | AC-14.1 ~ AC-14.8 | UT | 扩展样式与过渡属性 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC | @since |
|----------|----------|----------|--------|-----------|----------|---------|--------|
| CustomDialogController(options) | Public | CustomDialogControllerOptions | CustomDialogController | 无 | 创建对话框控制器 | AC-1.1 | 7 |
| .open() | Public | — | void | 无 | 打开对话框 | AC-1.2 | 7 |
| .close() | Public | — | void | 无 | 关闭对话框 | AC-1.3 | 7 |
| .getState() | Public | — | DTState | 无 | 查询状态 | AC-1.6 | 20 |
| CustomDialogControllerOptions.gridCount | Public | number | — | 无 | 栅格宽度 | AC-3.4 | 8 |
| CustomDialogControllerOptions.maskColor | Public | ResourceColor | — | 无 | 遮罩颜色 | AC-6.6 | 10 |
| CustomDialogControllerOptions.maskRect | Public | DimensionRect | — | 无 | 遮罩区域 | AC-6.7 | 10 |
| CustomDialogControllerOptions.openAnimation | Public | TranslateOptions | — | 无 | 打开动画 | AC-8.1 | 10 |
| CustomDialogControllerOptions.closeAnimation | Public | TranslateOptions | — | 无 | 关闭动画 | AC-8.2 | 10 |
| CustomDialogControllerOptions.showInSubWindow | Public | boolean | — | 无 | 子窗口显示 | AC-8.4 | 10 |
| CustomDialogControllerOptions.backgroundColor | Public | ResourceColor | — | 无 | 背景色 | AC-6.1 | 10 |
| CustomDialogControllerOptions.cornerRadius | Public | Dimension | — | 无 | 圆角 | AC-6.2 | 10 |
| CustomDialogControllerOptions.isModal | Public | boolean | — | 无 | 模态/非模态 | AC-7.1 | 11 |
| promptAction.openCustomDialog | Public | CustomDialogOptions | Promise\<number\> | 无 | NAPI 命令式自定义弹窗，接受 builder 或 ComponentContent | AC-10.1, AC-10.2 | 11 |
| promptAction.closeCustomDialog | Public | number (dialogId) | void | 无 | 按 dialogId 关闭对话框 | AC-10.3 | 11 |
| CustomDialogControllerOptions.onWillDismiss | Public | (DismissDialogAction) => void | — | 无 | 关闭请求回调 | AC-2.5 | 12 |
| CustomDialogControllerOptions.width | Public | Dimension | — | 无 | 宽度 | AC-3.5 | 12 |
| CustomDialogControllerOptions.height | Public | Dimension | — | 无 | 高度 | AC-3.5 | 12 |
| CustomDialogControllerOptions.borderWidth | Public | Widths | — | 无 | 边框宽度 | AC-6.3 | 12 |
| CustomDialogControllerOptions.borderColor | Public | Colors | — | 无 | 边框颜色 | AC-6.3 | 12 |
| CustomDialogControllerOptions.borderStyle | Public | BorderStyles | — | 无 | 边框样式 | AC-6.3 | 12 |
| CustomDialogControllerOptions.shadow | Public | ShadowOptions | — | 无 | 阴影 | AC-6.4 | 12 |
| CustomDialogControllerOptions.backgroundBlurStyle | Public | BlurStyle | — | 无 | 背景模糊 | AC-6.5 | 12 |
| CustomDialogControllerOptions.keyboardAvoidMode | Public | KeyboardAvoidMode | — | 无 | 键盘避让模式 | AC-3.6 | 12 |
| CustomDialogControllerOptions.transition | Public | TransitionEffect | — | 无 | 出现/消失过渡效果 | AC-14.1 | 12 |
| promptAction.updateCustomDialog | Public | CustomDialogUpdateOptions | void | 无 | 更新已显示对话框的 alignment/offset/autoCancel/maskColor | AC-10.7 | 12 |
| UIContext.getPromptAction().openCustomDialog | Public | CustomDialogOptions | Promise\<number\> | 无 | UIContext 绑定的命令式自定义弹窗 | AC-11.1 | 12 |
| UIContext.getPromptAction().updateCustomDialog | Public | CustomDialogUpdateOptions | void | 无 | UIContext 绑定的弹窗属性更新 | AC-11.4 | 12 |
| UIContext.getPromptAction().closeCustomDialog | Public | number (dialogId) | void | 无 | UIContext 绑定的按 dialogId 关闭 | AC-11.5 | 12 |
| CustomDialogControllerOptions.enableHoverMode | Public | boolean | — | 无 | 悬浮态 | AC-5.1 | 14 |
| CustomDialogControllerOptions.hoverModeArea | Public | HoverModeAreaType | — | 无 | 悬浮态区域 | AC-5.2 | 14 |
| CustomDialogControllerOptions.keyboardAvoidDistance | Public | Dimension | — | 无 | 键盘避让距离 | AC-3.8 | 15 |
| CustomDialogControllerOptions.levelMode | Public | LevelMode | — | 无 | 层级模式 | AC-4.1 | 15 |
| CustomDialogControllerOptions.levelUniqueId | Public | number | — | 无 | 层级唯一标识 | AC-4.2 | 15 |
| CustomDialogControllerOptions.immersiveMode | Public | ImmersiveMode | — | 无 | 沉浸式模式 | AC-4.4 | 15 |
| CustomDialogControllerOptions.levelOrder | Public | number | — | 无 | Z 序 | AC-4.3 | 18 |
| promptAction.openCustomDialogWithController | Public | CustomDialogControllerOptions | void | 无 | 基于 FrameNode+Controller 的命令式弹窗 | AC-10.5 | 18 |
| promptAction.presentCustomDialog | Public | CustomDialogOptions + DialogStyleOptions | void | 无 | 带样式选项的命令式弹窗 | AC-10.6 | 18 |
| UIContext.getPromptAction().openCustomDialogWithController | Public | CustomDialogControllerOptions | void | 无 | UIContext 绑定的 FrameNode+Controller 弹窗 | AC-11.2 | 18 |
| UIContext.getPromptAction().presentCustomDialog | Public | CustomDialogOptions + DialogStyleOptions | void | 无 | UIContext 绑定的带样式弹窗 | AC-11.3 | 18 |
| CustomDialogControllerOptions.focusable | Public | boolean | — | 无 | 可聚焦 | AC-7.3 | 19 |
| onWillAppear/onDidAppear/onWillDisappear/onDidDisappear | Public | callback | — | 无 | 生命周期回调 | AC-2.1 ~ AC-2.4 | 19 |
| CustomDialogControllerOptions.backgroundBlurStyleOptions | Public | BackgroundBlurStyleOptions | — | 无 | 背景模糊扩展选项 | AC-14.2 | 19 |
| CustomDialogControllerOptions.backgroundEffect | Public | BackgroundEffectOptions | — | 无 | 背景效果 | AC-14.3 | 19 |
| CustomDialogControllerOptions.dialogTransition | Public | TransitionEffect | — | 无 | 对话框内容过渡 | AC-14.4 | 19 |
| CustomDialogControllerOptions.maskTransition | Public | TransitionEffect | — | 无 | 遮罩过渡 | AC-14.4 | 19 |
| CustomDialogControllerOptions.systemMaterial | Public | boolean | — | 无 | 系统 Material | AC-6.9 | 26 |
| CustomDialogControllerOptions.displayModeInSubWindow | Public | DialogDisplayModeInSubWindow | — | 无 | 子窗口显示模式（SCREEN_BASED/WINDOW_BASED） | AC-14.5, AC-14.6 | 26.0.0 |
| CustomDialogControllerOptions.distortionMode | System | DistortionMode | — | 无 | 形变模式（systemapi） | AC-14.7 | 26 |
| CustomDialogControllerOptions.edgeLightMode | System | EdgeLightMode | — | 无 | 边缘光效模式（systemapi） | AC-14.8 | 26 |
| arkui.dialog.presentDialog | Public | DialogParams | void | 无 | 统一命令式弹窗显示 | AC-12.1 | 26.1.0 |
| arkui.dialog.presentCustomDialog | Public | DialogCustomOptions | void | 无 | 统一命令式自定义弹窗显示 | AC-12.2 | 26.1.0 |
| arkui.dialog.updateCustomDialog | Public | CustomDialogUpdateOptions | void | 无 | 统一命令式弹窗属性更新 | AC-12.3 | 26.1.0 |
| arkui.dialog.dismissDialog | Public | DialogId / FrameNode | void | 无 | 统一命令式弹窗关闭 | AC-12.4, AC-12.5 | 26.1.0 |
| DialogBaseController | Public | — | DialogBaseController | 无 | 统一弹窗控制器类 | AC-13.1, AC-13.2 | 26.1.0 |
| DialogBaseController.close() | Public | — | void | 无 | 关闭弹窗 | AC-13.1 | 26.1.0 |
| DialogBaseController.getState() | Public | — | ArkUI_DialogState | 无 | 查询弹窗状态 | AC-13.2 | 26.1.0 |
| DialogStyleOptions | Public | — | — | 无 | 样式选项接口 | AC-13.3 | 26.1.0 |
| DialogCustomOptions | Public | — | — | 无 | 自定义内容选项接口 | AC-13.4 | 26.1.0 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| promptAction.openCustomDialog | 废弃（@since 18） | 命令式自定义弹窗 | 使用 promptAction.openCustomDialogWithController 或 UIContext.getPromptAction().openCustomDialog 替代 | AC-10.4 |
| promptAction.closeCustomDialog | 废弃（@since 18） | 按 dialogId 关闭弹窗 | 使用 UIContext.getPromptAction().closeCustomDialog 或 arkui.dialog.dismissDialog 替代 | AC-10.4 |

## 接口规格

### 接口定义

**CustomDialogController.open**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void CustomDialogController::open()` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | 无参数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 状态为 CLOSED 时调用 | DialogView::CreateDialogNode 创建节点，状态 → APPEARING | AC-1.2 |
| 2 | 状态为 OPEN/OPENING 时调用 | 无效果 | AC-1.4 |

**CustomDialogController.close**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void CustomDialogController::close()` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | 无参数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 状态为 OPEN 时调用 | 状态 → DISAPPEARING，动画完成后卸载 | AC-1.3 |
| 2 | 状态为 CLOSED/CLOSING 时调用 | 无效果 | AC-1.5 |
| 3 | 状态为 APPEARING 时调用 | 跳过 APPEARED，直接 → DISAPPEARING | AC-2.8 |

**CustomDialogController.getState**

| 属性 | 值 |
|------|-----|
| 函数签名 | `DTState CustomDialogController::getState()` |
| 返回值 | `DTState` — CLOSED/OPENING/OPEN/CLOSING |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.6 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 状态为 DISAPPEARED 时调用 | 返回 CLOSED | AC-1.6 |
| 2 | 状态为 APPEARING 时调用 | 返回 OPENING | AC-1.6 |
| 3 | 状态为 APPEARED 时调用 | 返回 OPEN | AC-1.6 |
| 4 | 状态为 DISAPPEARING 时调用 | 返回 CLOSING | AC-1.6 |

**promptAction.openCustomDialog**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Promise<number> promptAction.openCustomDialog(CustomDialogOptions options)` |
| 返回值 | `Promise<number>` — resolve 为 dialogId |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-10.1, AC-10.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| builder | () => void | 否 | — | builder 函数，与 componentContent 二选一 |
| componentContent | ComponentContent | 否 | — | ComponentContent 对象，与 builder 二选一 |
| alignment | DialogAlignment | 否 | Center | 对齐方式 |
| offset | { dx, dy } | 否 | {0,0} | 偏移量 |
| autoCancel | boolean | 否 | true | 点击遮罩是否关闭 |
| maskColor | ResourceColor | 否 | — | 遮罩颜色 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 builder 函数 | 显示 builder 内容的对话框，resolve 返回 dialogId | AC-10.1 |
| 2 | 传入 componentContent | 显示 ComponentContent 内容的对话框，resolve 返回 dialogId | AC-10.2 |
| 3 | API >= 18 调用 | 标记为 @deprecated，推荐使用 openCustomDialogWithController | AC-10.4 |

**promptAction.updateCustomDialog**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void promptAction.updateCustomDialog(CustomDialogUpdateOptions options)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-10.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| dialogId | number | 是 | — | openCustomDialog 返回的 dialogId |
| alignment | DialogAlignment | 否 | — | 更新对齐方式 |
| offset | { dx, dy } | 否 | — | 更新偏移量 |
| autoCancel | boolean | 否 | — | 更新遮罩关闭行为 |
| maskColor | ResourceColor | 否 | — | 更新遮罩颜色 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 dialogId 和属性 | 已显示对话框属性被更新 | AC-10.7 |
| 2 | 传入不存在的 dialogId | 无效果，不崩溃 | AC-10.8 |

**arkui.dialog.presentDialog**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void arkui.dialog.presentDialog(DialogParams params)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-12.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| builder | () => void | 否 | — | builder 函数（属性弹窗） |
| options | DialogStyleOptions | 否 | — | 样式选项（遮罩弹窗） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 builder | 通过 OverlayManager 或 SubwindowManager 显示属性弹窗 | AC-12.1 |
| 2 | 传入 options | 通过 OverlayManager 显示遮罩弹窗 | AC-12.1 |

**DialogBaseController.close / getState**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void DialogBaseController::close()` / `ArkUI_DialogState DialogBaseController::getState()` |
| 返回值 | `void` / `ArkUI_DialogState` — UNINITIALIZED/APPEARING/APPEARED/DISAPPEARING/DISAPPEARED |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-13.1, AC-13.2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 close() | 对话框关闭 | AC-13.1 |
| 2 | 调用 getState() | 返回当前 ArkUI_DialogState 枚举值 | AC-13.2 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - promptAction.openCustomDialog / closeCustomDialog 在 API 18 标记为 @deprecated，推荐使用 openCustomDialogWithController / UIContext.getPromptAction() 替代（AC-10.4）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** CustomDialogController（open/close）@since 7，gridCount @since 8，maskColor/maskRect/openAnimation/closeAnimation/showInSubWindow/backgroundColor/cornerRadius @since 10，isModal/promptAction.openCustomDialog/closeCustomDialog @since 11，onWillDismiss/width/height/borderWidth/borderColor/borderStyle/shadow/backgroundBlurStyle/keyboardAvoidMode/transition @since 12，promptAction.updateCustomDialog/UIContext.getPromptAction().openCustomDialog/closeCustomDialog/updateCustomDialog @since 12，enableHoverMode @since 14，keyboardAvoidDistance/levelMode/immersiveMode @since 15，levelOrder @since 18，promptAction.openCustomDialogWithController/presentCustomDialog/UIContext.getPromptAction().openCustomDialogWithController/presentCustomDialog @since 18，focusable/生命周期回调/backgroundBlurStyleOptions/backgroundEffect/dialogTransition/maskTransition @since 19，getState @since 20，systemMaterial @since 26，displayModeInSubWindow @since 26.0.0，distortionMode/edgeLightMode（systemapi）@since 26，arkui.dialog.presentDialog/presentCustomDialog/updateCustomDialog/dismissDialog/DialogBaseController/DialogStyleOptions/DialogCustomOptions @since 26.1.0

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 共享 Pattern | CustomDialog 共享 DialogPattern 底层实现 | AC-1.1 |
| Overlay 依赖 | 对话框通过 OverlayManager::ShowDialog/CloseDialog 挂载/卸载 | AC-1.2, AC-1.3 |
| 状态机四态 | DialogPattern 维护 APPEARING/APPEARED/DISAPPEARING/DISAPPEARED 四态 | AC-2.1 ~ AC-2.8 |
| 组件化不完全 | 基础 Pattern 已组件化（libarkui_dialog.z.so），但 CustomDialogController 仍有 JSView Bridge | AC-1.1 |
| NAPI 分发 | promptAction 命令式 API 通过 OpenCustomDialog() 公共分发函数，按环境选择 delegate 或 SubwindowManager 路径 | AC-10.1, AC-10.5 |
| arkui.dialog 直连 | js_dialog.cpp 直接操作 OverlayManager/DialogManager，不经过 delegate 中转 | AC-12.1 ~ AC-12.5 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 对话框打开/关闭动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | 对话框关闭后 overlay 节点和 builder 内容销毁 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | 状态机状态转换不出现非法跳转 | UT | dialog_pattern_test |
| 可靠性 | 重复 open/close 不崩溃 | UT | controller 单测 |
| 可靠性 | 命令式 API 传入无效 dialogId 不崩溃 | UT | js_prompt_action 单测 |
| 问题定位 | hilog 标签覆盖状态机转换和生命周期回调 | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | enableHoverMode（@since 14）支持悬浮态；hoverModeArea 控制悬浮态区域；displayModeInSubWindow（@since 26.0.0）控制子窗口显示基准 | 悬浮态对话框在折叠态正确显示 | 手工 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Dialog 实现 AccessibilityProperty，报告角色 Dialog，支持 ActionDismiss | AC-9.1, AC-9.2 |
| 大字体 | 是 | 对话框内容跟随系统字体缩放 | AC-1.1 |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随 | AC-6.1, AC-6.6 |
| 多窗口/分屏 | 是 | showInSubWindow 支持子窗口模式；displayModeInSubWindow 控制子窗口显示基准 | AC-8.4, AC-14.5, AC-14.6 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 10/11/12/14/15/18/19/20/26/26.1.0 各版本新增属性和 API 需兼容性处理 | AC-9.3, AC-9.4 |
| 生态兼容 | 否 | 无 C API 变更（C API 见 Feat-03） | — |

## 行为场景（Gherkin）

```gherkin
Feature: CustomDialogController 生命周期与布局
  作为应用开发者
  我想要使用 CustomDialogController 显示自定义对话框
  以便在应用中与用户进行模态交互

  Scenario: CustomDialog 打开和关闭
    Given CustomDialogController 已创建
    When 调用 controller.open()
    Then DialogPattern 状态 → APPEARING
    And 触发 onWillAppear 回调
    When 出现动画完成
    Then 状态 → APPEARED
    And 触发 onDidAppear 回调
    When 调用 controller.close()
    Then 状态 → DISAPPEARING
    And 触发 onWillDisappear 回调
    When 消失动画完成
    Then 状态 → DISAPPEARED
    And 触发 onDidDisappear 回调
    And overlay 节点卸载

  Scenario: 重复 open 无效
    Given CustomDialogController 状态为 OPEN
    When 调用 controller.open()
    Then 状态保持 OPEN
    And 无效果

  Scenario: 重复 close 无效
    Given CustomDialogController 状态为 CLOSED
    When 调用 controller.close()
    Then 状态保持 CLOSED
    And 无效果

  Scenario: 状态跳跃
    Given CustomDialogController 状态为 APPEARING
    When 调用 controller.close()
    Then 状态跳过 APPEARED 直接 → DISAPPEARING

  Scenario: onWillDismiss 控制
    Given 对话框已打开且设置了 onWillDismiss
    When 用户点击遮罩且 autoCancel=true
    Then 触发 onWillDismiss 回调
    When 回调中调用 DismissDialogAction.dismiss()
    Then 对话框继续关闭
    When 回调中不调用 dismiss()
    Then 对话框保持打开

  Scenario Outline: 对话框布局
    Given CustomDialogController 以 alignment=<alignment> 创建
    When 调用 open()
    Then 对话框<position>显示

    Examples:
      | alignment           | position |
      | DialogAlignment.Center | 居中     |
      | DialogAlignment.Bottom | 底部     |
      | DialogAlignment.Top    | 顶部     |

  Scenario: 多层级对话框
    Given CustomDialogController 以 levelMode=EMBEDDED, levelUniqueId=123, levelOrder=5 创建
    When 调用 open()
    Then 对话框嵌入到 levelUniqueId=123 的父节点下
    And Z 序为 5

  Scenario: 键盘避让
    Given CustomDialogController 以 keyboardAvoidMode=TRANSLATE 创建
    When 软键盘弹出
    Then 对话框上移避让

  Scenario Outline: API 版本兼容
    Given API <api_version> 环境
    When 设置 <property>
    Then 属性<available>

    Examples:
      | api_version | property          | available |
      | 9           | maskColor        | 不可用     |
      | 10          | maskColor         | 可用       |
      | 11          | isModal           | 不可用     |
      | 12          | isModal           | 可用       |
      | 11          | onWillDismiss     | 不可用     |
      | 12          | onWillDismiss      | 可用       |

  Scenario: promptAction 命令式弹窗
    Given 调用 promptAction.openCustomDialog({ builder })
    Then 返回 Promise<number> resolve 为 dialogId
    When 调用 promptAction.updateCustomDialog({ dialogId, alignment: Bottom })
    Then 对话框对齐方式更新为底部
    When 调用 promptAction.closeCustomDialog(dialogId)
    Then 对话框关闭

  Scenario: promptAction 废弃迁移
    Given API >= 18 环境
    When 调用 promptAction.openCustomDialog
    Then 标记为 @deprecated
    And 推荐使用 openCustomDialogWithController

  Scenario: arkui.dialog 统一命名空间
    Given 调用 arkui.dialog.presentDialog(params)
    Then 通过 OverlayManager 显示对话框
    When 调用 arkui.dialog.dismissDialog({ dialogId })
    Then 对话框关闭
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
    query: "DialogPattern 状态机四态转换和生命周期回调实现"
  - repo: "openharmony/ace_engine"
    query: "DialogLayoutAlgorithm 尺寸/定位/键盘避让/栅格宽度布局算法"
  - repo: "openharmony/ace_engine"
    query: "CustomDialogControllerModelNG open/close 生命周期和 getState 实现"
  - repo: "openharmony/ace_engine"
    query: "DialogView CreateDialogNode 和 OverlayManager ShowDialog/CloseDialog 交互"
  - repo: "openharmony/ace_engine"
    query: "promptAction NAPI openCustomDialog/closeCustomDialog/updateCustomDialog/openCustomDialogWithController/presentCustomDialog 实现"
  - repo: "openharmony/ace_engine"
    query: "arkui.dialog NAPI presentDialog/presentCustomDialog/updateCustomDialog/dismissDialog 实现"
  - repo: "openharmony/ace_engine"
    query: "DialogBaseController close/getState 和 DialogStyleOptions/DialogCustomOptions 接口实现"
```

**关键文档:**
- SDK 类型定义 (CustomDialog): `interface/sdk-js/api/@internal/component/ets/custom_dialog.d.ts`
- SDK 类型定义 (AlertDialog): `interface/sdk-js/api/@internal/component/ets/alert_dialog.d.ts`
- SDK 类型定义 (ActionSheet): `interface/sdk-js/api/@internal/component/ets/action_sheet.d.ts`
- SDK 类型定义 (promptAction): `interface/sdk-js/api/@ohos.promptAction.d.ts`
- SDK 类型定义 (arkui.dialog): `interface/sdk-js/api/@ohos.arkui.dialog.d.ts`
- KB 路由: `docs/kb/components/overlay/dialog.md`
- 源码入口: `frameworks/core/components_ng/pattern/dialog/dialog_pattern.cpp`
- NAPI (promptAction): `interfaces/napi/kits/promptaction/js_prompt_action.cpp`
- NAPI (arkui.dialog): `interfaces/napi/kits/dialog/js_dialog.cpp`
