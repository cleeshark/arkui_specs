# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Grid 编辑模式与拖拽 |
| 特性编号 | Func-05-03-04-Feat-04 |
| 所属 Epic | Grid/GridItem 组件规格补录 |
| 优先级 | P0 |
| 目标版本 | API 8–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 存量特性补录（lineage: new-on-legacy），本规格补录已有实现的行为。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | editMode 属性 | 控制是否进入编辑模式，启用拖拽能力 |
| ADDED | enableEditMode 双向绑定 | @since 26，支持双向绑定控制编辑模式开关 |
| ADDED | multiSelectable 属性 | 启用鼠标拖拽多选 |
| ADDED | supportAnimation 属性 | 启用拖拽动画效果 |
| ADDED | focusWrapMode 属性 | @since 20，控制焦点遍历是否环绕 |
| ADDED | editModeOptions 属性 | @since 23，编辑模式选项（聚合动画、预览徽章、默认多选样式） |
| ADDED | onItemDragStart 事件 | 拖拽开始回调，返回自定义拖拽预览 |
| ADDED | onItemDragEnter 事件 | 拖拽进入目标区域回调 |
| ADDED | onItemDragMove 事件 | 拖拽移动回调，含目标位置索引 |
| ADDED | onItemDragLeave 事件 | 拖拽离开目标区域回调 |
| ADDED | onItemDrop 事件 | 拖拽释放回调 |
| ADDED | GridItemDragManager 状态机 | IDLE→LONG_PRESS→DRAGGING 三态拖拽管理 |
| ADDED | 拖拽视觉效果 | 长按缩放1.05x、弹簧动画、z-index=100、邻近项缩放 |
| ADDED | 交换动画 | InterpolatingSpring(0,1,400,38) 弹簧插值 |
| ADDED | 自动滚动热区 | 垂直59vp / 水平26vp 边缘自动滚动 |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/03-scroll-container-components/04-grid-grid-item/design.md`
- 源码定位：`frameworks/core/components_ng/pattern/grid/`

## 用户故事

### US-1: 开发者启用编辑模式以允许拖拽排序

作为 ArkUI 开发者，我想要设置 editMode=true 使 Grid 进入编辑模式，以便用户可以长按拖拽子项重新排序。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN editMode=true THEN Grid 进入编辑模式，子项可被长按触发拖拽 | 正常 |
| AC-1.2 | WHEN editMode=false THEN Grid 处于普通模式，子项不可拖拽 | 正常 |
| AC-1.3 | WHEN enableEditMode 通过双向绑定设置 THEN 绑定变量与编辑模式状态双向同步 | 正常 |
| AC-1.4 | WHEN editMode=false 且触发 onItemDragStart THEN 拖拽不启动（旧系统 GetEditable() 守卫生效） | 边界 |

### US-2: 开发者配置拖拽预览与事件

作为 ArkUI 开发者，我想要通过 onItemDragStart 返回自定义拖拽预览组件，并通过拖拽事件回调追踪拖拽过程。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 长按子项触发 onItemDragStart THEN 回调执行，返回的 CustomBuilder 作为拖拽预览显示 | 正常 |
| AC-2.2 | WHEN 拖拽预览进入另一子项区域 THEN onItemDragEnter 回调触发，参数含 ItemDragInfo | 正常 |
| AC-2.3 | WHEN 拖拽预览在子项间移动 THEN onItemDragMove 回调触发，参数含 ItemDragInfo、itemIndex、insertIndex | 正常 |
| AC-2.4 | WHEN 拖拽预览离开子项区域 THEN onItemDragLeave 回调触发，参数含 ItemDragInfo、itemIndex | 正常 |
| AC-2.5 | WHEN 释放拖拽 THEN onItemDrop 回调触发，参数含 ItemDragInfo、itemIndex、insertIndex、isSuccess | 正常 |
| AC-2.6 | WHEN onItemDragStart 返回 null/undefined THEN 使用默认拖拽预览（子项快照） | 边界 |

### US-3: 开发者启用拖拽动画效果

作为 ArkUI 开发者，我想要设置 supportAnimation=true 启用拖拽过程中的动画效果，以便拖拽体验更流畅自然。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN supportAnimation=true 且 editMode=true THEN 拖拽过程中子项交换使用 InterpolatingSpring(0,1,400,38) 弹簧动画 | 正常 |
| AC-3.2 | WHEN supportAnimation=false THEN 子项交换无动画，直接跳到目标位置 | 正常 |
| AC-3.3 | WHEN 长按触发拖拽 THEN 被拖拽子项缩放至1.05x，使用 spring 动画，z-index=100 | 正常 |
| AC-3.4 | WHEN 拖拽过程中邻近子项 THEN 邻近子项按 (1 - sharped * 0.05) 缩放 | 正常 |

### US-4: 开发者启用鼠标拖拽多选

作为 ArkUI 开发者，我想要设置 multiSelectable=true 启用鼠标框选多选功能，以便用户可以通过鼠标拖拽框选多个子项。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN multiSelectable=true THEN 用户可通过鼠标拖拽框选多个子项 | 正常 |
| AC-4.2 | WHEN multiSelectable=false THEN 鼠标拖拽不触发多选 | 正常 |
| AC-4.3 | WHEN editModeOptions.useDefaultMultiSelectStyle=true THEN 默认多选样式应用于选中项 | 正常 |
| AC-4.4 | WHEN editModeOptions.useDefaultMultiSelectStyle=false THEN 不应用默认多选样式，由开发者自定义 | 边界 |

### US-5: 开发者配置编辑模式选项

作为 ArkUI 开发者，我想要通过 editModeOptions 配置编辑模式的高级选项，包括聚合动画、预览徽章和多选样式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN editModeOptions.enableGatherSelectedItemsAnimation=true THEN 多选聚合动画启用 | 正常 |
| AC-5.2 | WHEN editModeOptions.onGetPreviewBadge 设置 THEN 拖拽预览上显示徽章 | 正常 |
| AC-5.3 | WHEN editModeOptions 未设置 THEN enableGatherSelectedItemsAnimation 默认 false，onGetPreviewBadge 默认 null | 边界 |

### US-6: 开发者控制焦点遍历环绕

作为 ArkUI 开发者，我想要设置 focusWrapMode 控制焦点遍历到边界时是否环绕，以便适配不同的交互需求。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN focusWrapMode=Wrap THEN 焦点遍历到末尾项后环绕到首项 | 正常 |
| AC-6.2 | WHEN focusWrapMode=NoWrap THEN 焦点遍历到末尾项后停止，不环绕 | 正常 |

### US-7: 拖拽过程自动滚动

作为 ArkUI 开发者，我想要在拖拽过程中将拖拽预览移到 Grid 边缘时自动滚动，以便将子项拖到可视区域外的位置。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN 拖拽预览位于垂直方向距边缘59vp以内 THEN Grid 自动垂直滚动 | 正常 |
| AC-7.2 | WHEN 拖拽预览位于水平方向距边缘26vp以内 THEN Grid 自动水平滚动 | 正常 |
| AC-7.3 | WHEN 拖拽预览离开边缘热区 THEN 自动滚动停止 | 边界 |

### US-8: 拖拽状态机管理

作为 ArkUI 开发者，我想要拖拽行为通过状态机管理，以确保拖拽过程的状态转换一致且可预测。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-8.1 | WHEN 无拖拽操作 THEN GridItemDragManager 状态为 IDLE | 正常 |
| AC-8.2 | WHEN 长按子项触发 THEN 状态从 IDLE 转为 LONG_PRESS | 正常 |
| AC-8.3 | WHEN 长按后开始移动 THEN 状态从 LONG_PRESS 转为 DRAGGING | 正常 |
| AC-8.4 | WHEN 释放拖拽或取消 THEN 状态从 DRAGGING 转回 IDLE | 正常 |
| AC-8.5 | WHEN onItemDragStart 回调执行 THEN GetIsAllowMouse() 返回 false，禁用鼠标滚动 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-GRID-04 | UT: editMode=true 拖拽可触发 | grid_event_hub.cpp |
| AC-1.2 | R-2 | TASK-GRID-04 | UT: editMode=false 拖拽不可触发 | grid_event_hub.cpp |
| AC-1.3 | R-3 | TASK-GRID-04 | UT: enableEditMode 双向绑定同步 | grid_model_ng.cpp |
| AC-1.4 | R-4 | TASK-GRID-04 | UT: GetEditable() 守卫拦截 | grid_event_hub.cpp |
| AC-2.1 | R-5 | TASK-GRID-04 | UT: onItemDragStart 返回 CustomBuilder | grid_item_drag_manager.cpp |
| AC-2.2 | R-6 | TASK-GRID-04 | UT: onItemDragEnter 触发 | grid_event_hub.cpp |
| AC-2.3 | R-7 | TASK-GRID-04 | UT: onItemDragMove 含 insertIndex | grid_event_hub.cpp |
| AC-2.4 | R-8 | TASK-GRID-04 | UT: onItemDragLeave 触发 | grid_event_hub.cpp |
| AC-2.5 | R-9 | TASK-GRID-04 | UT: onItemDrop 含 isSuccess | grid_event_hub.cpp |
| AC-2.6 | R-10 | TASK-GRID-04 | UT: null 返回值使用默认预览 | grid_item_drag_manager.cpp |
| AC-3.1 | R-11 | TASK-GRID-04 | UT: supportAnimation=true 弹簧动画 | grid_item_drag_manager.cpp |
| AC-3.2 | R-12 | TASK-GRID-04 | UT: supportAnimation=false 无动画 | grid_item_drag_manager.cpp |
| AC-3.3 | R-13 | TASK-GRID-04 | UT: 长按缩放1.05x+z-index | grid_item_drag_manager.cpp |
| AC-3.4 | R-14 | TASK-GRID-04 | UT: 邻近项缩放公式 | grid_item_drag_manager.cpp |
| AC-4.1 | R-15 | TASK-GRID-04 | UT: multiSelectable=true 鼠标框选 | grid_pattern.cpp |
| AC-4.2 | R-16 | TASK-GRID-04 | UT: multiSelectable=false 不可框选 | grid_pattern.cpp |
| AC-4.3 | R-17 | TASK-GRID-04 | UT: useDefaultMultiSelectStyle=true 默认样式 | grid_pattern.cpp |
| AC-4.4 | R-18 | TASK-GRID-04 | UT: useDefaultMultiSelectStyle=false 无默认样式 | grid_pattern.cpp |
| AC-5.1 | R-19 | TASK-GRID-04 | UT: enableGatherSelectedItemsAnimation | grid_pattern.cpp |
| AC-5.2 | R-20 | TASK-GRID-04 | UT: onGetPreviewBadge 回调 | grid_pattern.cpp |
| AC-5.3 | R-21 | TASK-GRID-04 | UT: editModeOptions 默认值 | grid_model_ng.cpp |
| AC-6.1 | R-22 | TASK-GRID-04 | UT: focusWrapMode=Wrap 环绕 | grid_pattern.cpp |
| AC-6.2 | R-23 | TASK-GRID-04 | UT: focusWrapMode=NoWrap 不环绕 | grid_pattern.cpp |
| AC-7.1 | R-24 | TASK-GRID-04 | UT: 垂直热区59vp自动滚动 | grid_item_drag_manager.cpp |
| AC-7.2 | R-25 | TASK-GRID-04 | UT: 水平热区26vp自动滚动 | grid_item_drag_manager.cpp |
| AC-7.3 | R-26 | TASK-GRID-04 | UT: 离开热区停止滚动 | grid_item_drag_manager.cpp |
| AC-8.1 | R-27 | TASK-GRID-04 | UT: IDLE 初始状态 | grid_item_drag_manager.cpp |
| AC-8.2 | R-28 | TASK-GRID-04 | UT: IDLE→LONG_PRESS 转换 | grid_item_drag_manager.cpp |
| AC-8.3 | R-29 | TASK-GRID-04 | UT: LONG_PRESS→DRAGGING 转换 | grid_item_drag_manager.cpp |
| AC-8.4 | R-30 | TASK-GRID-04 | UT: DRAGGING→IDLE 转换 | grid_item_drag_manager.cpp |
| AC-8.5 | R-31 | TASK-GRID-04 | UT: GetIsAllowMouse() 返回 false | grid_event_hub.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | editMode=true | Grid 进入编辑模式，子项可被长按拖拽 | 需同时设置 onItemDragStart 才能触发新系统拖拽 | AC-1.1 |
| R-2 | 行为 | editMode=false | Grid 不进入编辑模式，拖拽不可触发 | 旧系统通过 GetEditable() 守卫拦截 | AC-1.2 |
| R-3 | 行为 | enableEditMode 双向绑定 | 绑定变量与内部 editMode 状态双向同步 | @since 26；类型为 boolean \| undefined | AC-1.3 |
| R-4 | 边界 | editMode=false 且触发拖拽事件 | 旧系统(GridEventHub)检查 GetEditable()=false，拒绝拖拽 | 旧系统与新系统并存，editMode 控制旧系统守卫 | AC-1.4 |
| R-5 | 行为 | onItemDragStart 回调执行 | 返回 CustomBuilder 作为拖拽预览组件 | 新系统(GridItemDragManager)在 editMode=true 时工作 | AC-2.1 |
| R-6 | 行为 | 拖拽预览进入子项区域 | onItemDragEnter 触发，参数含 ItemDragInfo(x,y) | ItemDragInfo 包含拖拽点坐标 | AC-2.2 |
| R-7 | 行为 | 拖拽预览在子项间移动 | onItemDragMove 触发，参数含 ItemDragInfo、itemIndex、insertIndex | insertIndex 为预计插入位置 | AC-2.3 |
| R-8 | 行为 | 拖拽预览离开子项区域 | onItemDragLeave 触发，参数含 ItemDragInfo、itemIndex | — | AC-2.4 |
| R-9 | 行为 | 释放拖拽 | onItemDrop 触发，参数含 ItemDragInfo、itemIndex、insertIndex、isSuccess | isSuccess=false 表示拖拽未成功完成 | AC-2.5 |
| R-10 | 边界 | onItemDragStart 返回 null/undefined | 使用默认拖拽预览（子项快照截图） | — | AC-2.6 |
| R-11 | 行为 | supportAnimation=true 且子项交换 | 交换动画使用 InterpolatingSpring(0,1,400,38) | mass=0, stiffness=1, damping=400, velocity=38 | AC-3.1 |
| R-12 | 行为 | supportAnimation=false | 子项交换无动画，直接跳到目标位置 | — | AC-3.2 |
| R-13 | 行为 | 长按触发拖拽 | 被拖拽子项缩放至1.05x，spring动画过渡，z-index=100 | 缩放和z-index在LONG_PRESS→DRAGGING转换时设置 | AC-3.3 |
| R-14 | 行为 | 拖拽过程中邻近子项 | 邻近子项按 (1 - sharped * 0.05) 缩放 | sharped 值随距离递减 | AC-3.4 |
| R-15 | 行为 | multiSelectable=true | 鼠标拖拽可框选多个子项 | 仅鼠标输入有效 | AC-4.1 |
| R-16 | 行为 | multiSelectable=false | 鼠标拖拽不触发多选 | — | AC-4.2 |
| R-17 | 行为 | editModeOptions.useDefaultMultiSelectStyle=true | 默认多选样式应用于选中项 | @since 26 | AC-4.3 |
| R-18 | 边界 | editModeOptions.useDefaultMultiSelectStyle=false | 不应用默认多选样式，开发者自定义 | — | AC-4.4 |
| R-19 | 行为 | editModeOptions.enableGatherSelectedItemsAnimation=true | 多选聚合动画启用 | — | AC-5.1 |
| R-20 | 行为 | editModeOptions.onGetPreviewBadge 设置 | 拖拽预览上显示徽章 | 回调返回徽章组件 | AC-5.2 |
| R-21 | 边界 | editModeOptions 未设置 | enableGatherSelectedItemsAnimation=false, onGetPreviewBadge=null | — | AC-5.3 |
| R-22 | 行为 | focusWrapMode=Wrap | 焦点遍历到末尾项后环绕到首项 | @since 20 | AC-6.1 |
| R-23 | 行为 | focusWrapMode=NoWrap | 焦点遍历到末尾项后停止 | — | AC-6.2 |
| R-24 | 行为 | 拖拽预览位于垂直方向距边缘59vp以内 | Grid 自动垂直滚动 | 热区阈值=59vp | AC-7.1 |
| R-25 | 行为 | 拖拽预览位于水平方向距边缘26vp以内 | Grid 自动水平滚动 | 热区阈值=26vp | AC-7.2 |
| R-26 | 边界 | 拖拽预览离开边缘热区 | 自动滚动停止 | — | AC-7.3 |
| R-27 | 行为 | 无拖拽操作 | GridItemDragManager 状态为 IDLE | 初始状态 | AC-8.1 |
| R-28 | 行为 | 长按子项触发 | 状态从 IDLE 转为 LONG_PRESS | — | AC-8.2 |
| R-29 | 行为 | 长按后开始移动 | 状态从 LONG_PRESS 转为 DRAGGING | — | AC-8.3 |
| R-30 | 行为 | 释放拖拽或取消 | 状态从 DRAGGING 转回 IDLE | — | AC-8.4 |
| R-31 | 边界 | onItemDragStart 回调执行 | GetIsAllowMouse() 返回 false，禁用鼠标滚动 | 拖拽期间禁用滚动以避免冲突 | AC-8.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | editMode 启用/禁用 | UT: GridEventHub::GetEditable() | editMode 守卫生效 |
| VM-2 | enableEditMode 双向绑定 | UT: GridModelNG::SetEnableEditMode | 绑定同步 |
| VM-3 | onItemDragStart 返回预览 | UT: GridItemDragManager::OnItemDragStart | CustomBuilder 渲染 |
| VM-4 | 拖拽事件回调 | UT: GridEventHub 拖拽事件分发 | Enter/Move/Leave/Drop 参数正确 |
| VM-5 | supportAnimation 弹簧动画 | UT: GridItemDragManager::HandleDragMove | InterpolatingSpring 参数 |
| VM-6 | 长按缩放与z-index | UT: GridItemDragManager::HandleLongPress | scale=1.05, z-index=100 |
| VM-7 | 邻近项缩放 | UT: GridItemDragManager::UpdateNearbyItemsScale | (1-sharped*0.05) 公式 |
| VM-8 | multiSelectable 多选 | UT: GridPattern::HandleMouseSelect | 鼠标框选行为 |
| VM-9 | useDefaultMultiSelectStyle | UT: GridPattern::ApplyMultiSelectStyle | 默认样式应用 |
| VM-10 | editModeOptions 选项 | UT: GridModelNG::SetEditModeOptions | 各子选项生效 |
| VM-11 | focusWrapMode | UT: GridPattern::HandleFocusWrap | Wrap/NoWrap 环绕行为 |
| VM-12 | 自动滚动热区 | UT: GridItemDragManager::CheckAutoScroll | 59vp/26vp 阈值 |
| VM-13 | 拖拽状态机 | UT: GridItemDragManager 状态转换 | IDLE/LONG_PRESS/DRAGGING |
| VM-14 | 拖拽期间鼠标滚动禁用 | UT: GetIsAllowMouse() | 拖拽时返回 false |

## API 变更分析

### 新增 API

> 本规格为存量补录，以下 API 已在 SDK 中存在。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| editMode(boolean) | Public | boolean | GridAttribute | 无 | 控制编辑模式开关 (@since 8) | AC-1.1 |
| enableEditMode(boolean \| undefined) | Public | boolean \| undefined | GridAttribute | 无 | 编辑模式双向绑定 (@since 26) | AC-1.3 |
| multiSelectable(boolean) | Public | boolean | GridAttribute | 无 | 启用鼠标多选 (@since 8) | AC-4.1 |
| supportAnimation(boolean) | Public | boolean | GridAttribute | 无 | 启用拖拽动画 (@since 8) | AC-3.1 |
| focusWrapMode(FocusWrapMode) | Public | FocusWrapMode | GridAttribute | 无 | 焦点环绕模式 (@since 20) | AC-6.1 |
| editModeOptions(EditModeOptions) | Public | EditModeOptions | GridAttribute | 无 | 编辑模式选项 (@since 23) | AC-5.1 |
| onItemDragStart(callback) | Public | OnItemDragStartCallback | GridAttribute | 无 | 拖拽开始回调 (@since 8) | AC-2.1 |
| onItemDragEnter(callback) | Public | (ItemDragInfo) => void | GridAttribute | 无 | 拖拽进入回调 (@since 8) | AC-2.2 |
| onItemDragMove(callback) | Public | (ItemDragInfo, number, number) => void | GridAttribute | 无 | 拖拽移动回调 (@since 8) | AC-2.3 |
| onItemDragLeave(callback) | Public | (ItemDragInfo, number) => void | GridAttribute | 无 | 拖拽离开回调 (@since 8) | AC-2.4 |
| onItemDrop(callback) | Public | (ItemDragInfo, number, number, boolean) => void | GridAttribute | 无 | 拖拽释放回调 (@since 8) | AC-2.5 |

### 变更/废弃 API

无新增变更或废弃。enableEditMode 是 @since 26 新增属性，不影响原有 editMode。

## 接口规格

### 接口定义

**editMode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `editMode(enabled: boolean): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enabled | boolean | 是 | false | true=编辑模式，false=普通模式 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enabled=true | Grid 进入编辑模式，子项可被长按拖拽 | AC-1.1 |
| 2 | enabled=false | Grid 不进入编辑模式，拖拽不可触发 | AC-1.2 |

---

**enableEditMode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableEditMode(enabled: boolean \| undefined): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 26) |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enabled | boolean \| undefined | 是 | undefined | 支持双向绑定；undefined 时不改变编辑模式 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enabled=true | 编辑模式开启，绑定变量同步为 true | AC-1.3 |
| 2 | 外部修改绑定变量为 false | 编辑模式关闭 | AC-1.3 |
| 3 | enabled=undefined | 不改变当前编辑模式状态 | AC-1.3 |

---

**multiSelectable**

| 属性 | 值 |
|------|-----|
| 函数签名 | `multiSelectable(enabled: boolean): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enabled | boolean | 是 | false | true=启用鼠标多选，false=禁用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enabled=true | 鼠标拖拽可框选多个子项 | AC-4.1 |
| 2 | enabled=false | 鼠标拖拽不触发多选 | AC-4.2 |

---

**supportAnimation**

| 属性 | 值 |
|------|-----|
| 函数签名 | `supportAnimation(enabled: boolean): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enabled | boolean | 是 | false | true=启用拖拽动画，false=禁用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enabled=true 且拖拽交换 | 使用 InterpolatingSpring(0,1,400,38) 弹簧动画 | AC-3.1 |
| 2 | enabled=false | 子项交换无动画，直接跳到目标位置 | AC-3.2 |

---

**focusWrapMode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `focusWrapMode(mode: FocusWrapMode): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-6.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| mode | FocusWrapMode (Wrap / NoWrap) | 是 | NoWrap | Wrap=环绕，NoWrap=不环绕 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Wrap | 焦点遍历到末尾项后环绕到首项 | AC-6.1 |
| 2 | mode=NoWrap | 焦点遍历到末尾项后停止 | AC-6.2 |

---

**editModeOptions**

| 属性 | 值 |
|------|-----|
| 函数签名 | `editModeOptions(options: EditModeOptions): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 23) |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options | EditModeOptions | 是 | — | 包含 enableGatherSelectedItemsAnimation, onGetPreviewBadge, useDefaultMultiSelectStyle |

**EditModeOptions 结构**

| 字段 | 类型 | 必填 | 默认值 | 约束条件 | @since |
|------|------|------|--------|---------|--------|
| enableGatherSelectedItemsAnimation | boolean | 否 | false | 多选聚合动画开关 | 23 |
| onGetPreviewBadge | (index: number) => CustomBuilder | 否 | null | 拖拽预览徽章 | 23 |
| useDefaultMultiSelectStyle | boolean | 否 | true | 默认多选样式开关 | 26 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enableGatherSelectedItemsAnimation=true | 多选聚合动画启用 | AC-5.1 |
| 2 | onGetPreviewBadge 设置 | 拖拽预览上显示徽章 | AC-5.2 |
| 3 | useDefaultMultiSelectStyle=true | 默认多选样式应用于选中项 | AC-4.3 |
| 4 | useDefaultMultiSelectStyle=false | 不应用默认多选样式 | AC-4.4 |

---

**onItemDragStart**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onItemDragStart(callback: OnItemDragStartCallback): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (itemIndex: number) => CustomBuilder | ClassValue | 是 | — | 返回拖拽预览组件；返回 null/undefined 时使用默认预览 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 长按子项触发拖拽 | 回调执行，返回的 CustomBuilder 作为拖拽预览显示 | AC-2.1 |
| 2 | 回调返回 null/undefined | 使用默认拖拽预览（子项快照） | AC-2.6 |
| 3 | 回调执行 | GetIsAllowMouse() 返回 false，禁用鼠标滚动 | AC-8.5 |

---

**onItemDragEnter**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onItemDragEnter(callback: (event: ItemDragInfo) => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (event: ItemDragInfo) => void | 是 | — | ItemDragInfo 含拖拽点 x/y 坐标 |

---

**onItemDragMove**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onItemDragMove(callback: (event: ItemDragInfo, itemIndex: number, insertIndex: number) => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (event: ItemDragInfo, itemIndex: number, insertIndex: number) => void | 是 | — | itemIndex=拖拽源索引，insertIndex=预计插入索引 |

---

**onItemDragLeave**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onItemDragLeave(callback: (event: ItemDragInfo, itemIndex: number) => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (event: ItemDragInfo, itemIndex: number) => void | 是 | — | itemIndex=拖拽离开的子项索引 |

---

**onItemDrop**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onItemDrop(callback: (event: ItemDragInfo, itemIndex: number, insertIndex: number, isSuccess: boolean) => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (event: ItemDragInfo, itemIndex: number, insertIndex: number, isSuccess: boolean) => void | 是 | — | isSuccess=false 表示拖拽未成功完成 |

## 兼容性声明

- **已有 API 行为变更:** 否。enableEditMode 是 @since 26 新增属性，不影响原有 editMode。editModeOptions.useDefaultMultiSelectStyle 是 @since 26 新增字段，不影响 @since 23 的 editModeOptions。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 标注按各 API 最早引入版本；新增字段标注引入版本

- **SDK vs 源码偏差风险:**
  - 旧系统(GridEventHub)和新系统(GridItemDragManager)并存，editMode 控制旧系统 GetEditable() 守卫，新系统通过 per-item 拖拽管理器工作 — 两套系统行为可能存在细微差异
  - C-API 缺少 editModeOptions 相关接口，SDK 有此功能 — C-API 未实现

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双拖拽系统并存 | 旧系统(GridEventHub)通过 GetEditable() 守卫；新系统(GridItemDragManager)在 editMode=true 时工作 | AC-1.1, AC-1.4 |
| 状态机驱动 | GridItemDragManager 三态: IDLE→LONG_PRESS→DRAGGING | AC-8.1~AC-8.4 |
| 拖拽期间禁用滚动 | onItemDragStart 执行时 GetIsAllowMouse()=false | AC-8.5 |
| 弹簧动画参数固定 | InterpolatingSpring(0,1,400,38) 参数不可配置 | AC-3.1 |
| 自动滚动热区固定 | 垂直59vp / 水平26vp，不可配置 | AC-7.1, AC-7.2 |
| 长按缩放固定 | 1.05x 缩放和 z-index=100，不可配置 | AC-3.3 |
| 邻近项缩放公式固定 | (1 - sharped * 0.05)，不可配置 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 拖拽交换动画帧率 ≥55fps | Perf 组网测试 | Jank 检测 |
| 性能 | 长按响应延迟 <200ms | 触摸事件计时 | Trace 打点 |
| 性能 | 自动滚动启动延迟 <100ms | 热区检测计时 | Trace 打点 |
| 内存 | GridItemDragManager 状态管理无泄漏 | 内存 Dump | 拖拽前后内存对比 |
| 可测试性 | GridItemDragManager 状态转换可独立 UT | Mock 事件输入 | grid_item_drag_manager.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 触摸长按拖拽 | 长按时间阈值由系统默认 | 触摸交互测试 | — |
| 平板 | 鼠标/触摸/键盘多输入 | multiSelectable 鼠标框选；focusWrapMode 键盘焦点 | 多输入测试 | — |
| 折叠屏 | 折叠态变化时编辑模式状态保持 | 编辑模式不因折叠重置 | 折叠适配测试 | — |
| 穿戴 | 触摸拖拽 | 长按阈值可能不同 | 穿戴专项测试 | — |
| PC | 鼠标拖拽为主 | multiSelectable 鼠标框选；focusWrapMode Tab/方向键 | 桌面交互测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 编辑模式下拖拽操作需提供无障碍替代方案 | 辅助技术读取拖拽状态 |
| 大字体 | 否 | 编辑模式不涉及字体大小 | — |
| 深色模式 | 否 | 拖拽预览由 CustomBuilder 决定，深色模式由开发者控制 | — |
| 多窗口/分屏 | 是 | 拖拽预览在分屏边界内限制 | 分屏拖拽边界处理 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | enableEditMode @since 26，useDefaultMultiSelectStyle @since 26 | 低版本设备不支持 |
| 生态兼容 | 否 | — | — |

## 行为场景（Gherkin）

```gherkin
Feature: Grid 编辑模式与拖拽
  作为 ArkUI 开发者
  我想要启用编辑模式并配置拖拽行为
  以便用户可以长按拖拽子项重新排序

  Scenario: 启用编辑模式并拖拽
    Given editMode=true
    And supportAnimation=true
    And onItemDragStart 已设置
    When 用户长按子项 index=3
    Then GridItemDragManager 状态从 IDLE 转为 LONG_PRESS
    And 子项缩放至 1.05x
    And z-index=100
    When 用户开始移动
    Then 状态从 LONG_PRESS 转为 DRAGGING
    And onItemDragStart 回调触发
    And GetIsAllowMouse()=false
    And 拖拽预览显示

  Scenario: 拖拽过程交换动画
    Given editMode=true
    And supportAnimation=true
    And 拖拽预览移动到 index=5 位置
    When 触发子项交换
    Then 交换动画使用 InterpolatingSpring(0,1,400,38)
    And 邻近项按 (1 - sharped * 0.05) 缩放

  Scenario: 拖拽释放
    Given 拖拽预览在 index=5 位置
    When 用户释放拖拽
    Then onItemDrop 回调触发
    And 参数 itemIndex=3, insertIndex=5, isSuccess=true
    And GridItemDragManager 状态从 DRAGGING 转为 IDLE
    And 子项缩放恢复为 1.0
    And z-index 恢复

  Scenario: 拖拽边缘自动滚动
    Given editMode=true
    And 拖拽进行中
    When 拖拽预览位于垂直方向距边缘 30vp（<59vp）
    Then Grid 自动垂直滚动
    When 拖拽预览位于水平方向距边缘 20vp（<26vp）
    Then Grid 自动水平滚动
    When 拖拽预览移到距边缘 80vp（>59vp）
    Then 自动滚动停止

  Scenario: 鼠标多选
    Given editMode=true
    And multiSelectable=true
    When 用户鼠标拖拽框选多个子项
    Then 框选范围内子项被选中
    And useDefaultMultiSelectStyle=true 时默认多选样式应用

  Scenario: 焦点环绕
    Given focusWrapMode=Wrap
    And 焦点在最后一个子项
    When 用户按下方向键
    Then 焦点环绕到第一个子项

  Scenario: editMode=false 拖拽拒绝
    Given editMode=false
    When 用户长按子项
    Then GetEditable()=false
    And 拖拽不启动
```

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [ ] 范围边界明确（做什么/不做什么清晰）
- [ ] 无语义模糊表述（"快速""稳定""尽可能"等）
- [ ] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [ ] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Grid editMode 编辑模式与 GetEditable() 守卫 (grid_event_hub.cpp)"
  - repo: "openharmony/ace_engine"
    query: "GridItemDragManager 拖拽状态机 IDLE LONG_PRESS DRAGGING (grid_item_drag_manager.cpp)"
  - repo: "openharmony/ace_engine"
    query: "Grid 拖拽交换动画 InterpolatingSpring (grid_item_drag_manager.cpp)"
  - repo: "openharmony/ace_engine"
    query: "Grid 拖拽自动滚动热区 59vp 26vp (grid_item_drag_manager.cpp)"
  - repo: "openharmony/ace_engine"
    query: "Grid editModeOptions enableGatherSelectedItemsAnimation onGetPreviewBadge useDefaultMultiSelectStyle"
  - repo: "openharmony/ace_engine"
    query: "Grid onItemDragStart onItemDragEnter onItemDragMove onItemDragLeave onItemDrop (grid_event_hub.cpp)"
```

**关键文档：**
- SDK 动态 API: `interface/sdk-js/api/@internal/component/ets/grid.d.ts`
- SDK 静态 API: `interface/sdk-js/api/arkui/component/grid.static.d.ets`
- 源码入口: `frameworks/core/components_ng/pattern/grid/`
- 拖拽管理器: `frameworks/core/components_ng/pattern/grid/grid_item_drag_manager.cpp`
- 事件中心: `frameworks/core/components_ng/pattern/grid/grid_event_hub.cpp`
