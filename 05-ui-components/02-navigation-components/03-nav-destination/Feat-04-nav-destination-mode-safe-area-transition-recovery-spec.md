# Feat-04: NavDestination 模式/安全区/转场动画/状态恢复

| 字段 | 值 |
|------|------|
| 功能编号 | Func-05-02-01-Feat-11 |
| 所属功能域 | 05-ui-components / 02-navigation-components / 03-nav-destination |
| Spec ID | Feat-04 |
| 版本 | 1.0 |
| 状态 | Defined |
| 覆盖 API 版本 | @since 12 (systemBarStyle, NavDestinationModifier), @since 14 (recoverable, systemTransition), @since 15 (customTransition, EXPLODE/SLIDE_RIGHT/SLIDE_BOTTOM), @since 23 (NavDestinationModifier.static) |

---

## 1 概述

本 Feat 覆盖 NavDestination 的四类非视觉内容属性能力：

1. **系统栏样式 (systemBarStyle)** — NavDestination 级别 SystemBarStyle 覆盖 Navigation 级别，含 backup/restore 机制
2. **状态恢复 (recoverable)** — 标记 NavDestination 可在 App 终止后恢复，仅 HOME/RELATED 类型目的地参与恢复
3. **转场动画 (systemTransition / customTransition)** — 预定义系统转场类型和开发者自定义转场委托
4. **C API Modifier 桥接 (NavDestinationModifier dynamic + static)** — C API 属性桥接到 ModelNG / ModelStatic
5. **全屏覆盖 (fullScreenOverlay)** — SPLIT 模式下 NavDestination 使用 overlay 容器替代 content 容器

---

## 2 用户故事

### US-1: NavDestination 系统栏样式配置

**角色**: 应用开发者  
**意图**: 在 NavDestination 上设置 SystemBarStyle，使其在目的地激活时覆盖 Navigation 级别样式，退出时自动恢复  
**验收标准**:

- AC-1: `systemBarStyle(Optional<SystemBarStyle>)` 设置后，NavDestination 激活时生效
  - 实现: `NavDestinationModelNG::SetSystemBarStyle` 将 style 传递给 pattern (`navdestination_model_ng.cpp:1433-1441`)
  - pattern `SetSystemBarStyle` 首次调用时从 `windowManager->GetSystemBarStyle()` 保存 `backupStyle_` (`navdestination_pattern.cpp:530`)
  - 当前 style 记入 `currStyle_` (`navdestination_pattern.cpp:533`)
- AC-2: NavDestination 被弹出后自动恢复前一个 SystemBarStyle
  - `OnDetachFromMainTree` 重置 `backupStyle_` 和 `currStyle_` (`navdestination_pattern.cpp:579-580`)
  - fullPageNavigation + topNavDestination 条件下，`currStyle_ != nullptr` 时调用 `windowManager->SetSystemBarStyle(currStyle_)` (`navdestination_pattern.cpp:538-539`)
  - 否则调用 `navigationPattern->TryRestoreSystemBarStyle(windowManager)` 恢复 Navigation 级别样式 (`navdestination_pattern.cpp:541`)
- AC-3: DIALOG 模式 NavDestination 不支持 systemBarStyle（仅支持 STANDARD 模式）
- AC-4: C API dynamic 桥接: `SetNavDestinationSystemBarStyle(ArkUINodeHandle, ArkUI_Uint32)` 通过 `SystemBarStyle::CreateStyleFromColor(value)` 转换 (`nav_destination_modifier.cpp:605-611`)
  - Reset: `SetSystemBarStyle(frameNode, nullptr)` (`nav_destination_modifier.cpp:617`)
- AC-5: C API static 桥接: `SetSystemBarStyleImpl` 从 `optValue->statusBarContentColor` 提取 Color (`nav_destination_modifier.cpp(impl):311-323`)
  - 转换后调用 `NavDestinationModelStatic::SetSystemBarStyle(frameNode, contentColor)` (`navdestination_model_static.h:77`, `navdestination_model_static.cpp:714-722`)
  - `SystemBarStyle::CreateStyleFromColor(contentColor.GetValue())` 创建 style 对象 (`navdestination_model_static.cpp:721`)

### US-2: NavDestination 状态恢复

**角色**: 应用开发者  
**意图**: 标记 NavDestination 为可恢复，确保 App 终止后仅 HOME/RELATED 类型目的地参与恢复流程  
**验收标准**:

- AC-1: `recoverable(Optional<boolean>)` 设置后，NavDestinationGroupNode 记录 `recoverable_` 标志
  - `NavDestinationGroupNode::SetRecoverable(bool)` (`navdestination_group_node.h:194-197`)
  - `NavDestinationGroupNode::CanRecovery()` 返回 `recoverable_ && !fromNavrouterAndNoRouteInfo_` (`navdestination_group_node.h:204-207`)
- AC-2: 默认值为 true — 未设置 recoverable 时目的地默认可恢复
  - static 桥接: `SetRecoverable` 默认值 `recoverable.value_or(true)` (`navdestination_model_static.cpp:474`)
  - dynamic C API Reset: `SetRecoverable(frameNode, true)` (`nav_destination_modifier.cpp:479`)
- AC-3: 仅 HOME 和 RELATED 类型 NavDestination 参与 `OnDetachFromMainTree` 的恢复通知
  - `OnDetachFromMainTree` 检查 `hostNode->IsHomeDestination() || hostNode->GetNavDestinationType() == NavDestinationType::RELATED` (`navdestination_pattern.cpp:581`)
  - NavDestinationType 枚举: DETAIL=0, HOME=1, PROXY=2, RELATED=3 (`navigation_declaration.h:304-308`)
- AC-4: dynamic 桥接: `NavDestinationModelNG::SetRecoverable(FrameNode*, bool)` 调用 `navDestination->SetRecoverable(recoverable)` (`navdestination_model_ng.cpp:1124-1128`)
  - 非静态版: `navDestination->SetRecoverable(recoverable)` (`navdestination_model_ng.cpp:1136`)
- AC-5: static 桥接: `SetRecoverableImpl` 调用 `NavDestinationModelStatic::SetRecoverable(frameNode, convValue)` (`nav_destination_modifier.cpp(impl):324-331`)
  - `convValue` 为 `std::optional<bool>` (`nav_destination_modifier.cpp(impl):329-330`)
- AC-6: `SetPendingToClean` 在 pendingToClean_ 变为 false 时调用 `navigationStack->MarkAutoCleanedFlag`，使用 `hostNode->CanRecovery()` 判断是否可恢复 (`navdestination_pattern.cpp:1148`)

### US-3: NavDestination 转场动画

**角色**: 应用开发者  
**意图**: 为 NavDestination 配置预定义系统转场类型或自定义转场委托，实现 PUSH/POP 方向和进入/退出的差异化动画  
**验收标准**:

- AC-1: `systemTransition(NavigationSystemTransitionType)` 设置预定义转场类型
  - 枚举定义: `NavigationSystemTransitionType` (`navigation_declaration.h:293-302`)
    - NONE=0, TITLE=1, CONTENT=2 (1<<1), DEFAULT=3 (1|1<<1), FADE=4 (1<<2), EXPLODE=5 (1<<3), SLIDE_RIGHT=6 (1<<4), SLIDE_BOTTOM=7 (1<<5)
  - `NavDestinationModelNG::SetSystemTransitionType(FrameNode*, type)` 调用 `navDestination->SetSystemTransitionType(type)` (`navdestination_model_ng.cpp:1820-1824`)
  - dynamic C API: `SetNavDestinationSystemTransition(node, int32_t value)` 转为 `NG::NavigationSystemTransitionType` (`nav_destination_modifier.cpp:133-137`)
  - Reset: `SetSystemTransitionType(frameNode, NavigationSystemTransitionType::DEFAULT)` (`nav_destination_modifier.cpp:144`)
- AC-2: static C API 桥接: `SetSystemTransitionImpl` 将 JS enum 值映射为内部 enum
  - 映射: NONE=1→NONE, TITLE=2→TITLE, CONTENT=3→CONTENT, FADE=4→FADE, EXPLODE=5→EXPLODE, SLIDE_RIGHT=6→SLIDE_RIGHT, SLIDE_BOTTOM=7→SLIDE_BOTTOM (`nav_destination_modifier.cpp(impl):343-378`)
  - 调用 `NavDestinationModelStatic::SetSystemTransitionType(frameNode, res)` (`navdestination_model_static.h:46`, `nav_destination_modifier.cpp(impl):380`)
- AC-3: `customTransition(NavDestinationTransitionDelegate)` 设置自定义转场委托
  - 委托类型: `NavDestinationTransitionDelegate = std::function<std::optional<std::vector<NavDestinationTransition>>(NavigationOperation, bool)>` (`navigation_declaration.h:344-345`)
  - `NavDestinationTransition` 结构: delay, duration, curve, event, onTransitionEnd (`navigation_declaration.h:320-326`)
  - dynamic: `NavDestinationModelNG::SetCustomTransition` → `node->SetNavDestinationTransitionDelegate(std::move(transitionDelegate))` (`navdestination_model_ng.cpp:2044-2051`)
  - `NavDestinationGroupNode::SetNavDestinationTransitionDelegate` 存储委托 (`navdestination_group_node.h:239`)
  - 成员: `navDestinationTransitionDelegate_` (`navdestination_group_node.h:352`)
- AC-4: static 桥接: `SetCustomTransitionImpl` 通过 `CallbackHelper` 封装 Ark 回调 (`nav_destination_modifier.cpp(impl):438-458`)
  - 转换 `NavigationOperation → Ark_NavigationOperation`, `isEnter → Ark_Boolean` (`nav_destination_modifier.cpp(impl):451-452`)
  - 返回 `std::optional<std::vector<NavDestinationTransition>>` 通过 `InvokeWithOptConvertResult` (`nav_destination_modifier.cpp(impl):453-456`)
  - undefined tag 时调用 `SetCustomTransition(frameNode, nullptr)` (`nav_destination_modifier.cpp(impl):445`)
  - 调用 `NavDestinationModelStatic::SetCustomTransition(frameNode, onNavigationAnimation)` (`navdestination_model_static.cpp:182-189`)
- AC-5: NONE 类型意味着无转场动画
- AC-6: TITLE 类型仅标题栏参与动画
- AC-7: CONTENT 类型内容区域滑动
- AC-8: FADE 类型淡入淡出
- AC-9: EXPLODE/SLIDE_RIGHT/SLIDE_BOTTOM 类型自 API 15 开始支持

### US-4: NavDestination C API Modifier (dynamic + static)

**角色**: NDK/C API 应用开发者  
**意图**: 通过 C API Modifier 设置 NavDestination 属性（systemBarStyle, recoverable, systemTransition, customTransition, fullScreenOverlay, ignoreLayoutSafeArea 等）  
**验收标准**:

- AC-1: dynamic modifier 注册所有属性 setter/resetter
  - `GetNavDestinationModifier()` 返回 `ArkUINavDestinationModifier` 结构体 (`nav_destination_modifier.cpp:1067-1157`)
  - 注册条目:
    - `.setRecoverable = SetNavDestinationRecoverable` (`nav_destination_modifier.cpp:1090`)
    - `.resetRecoverable = ResetNavDestinationRecoverable` (`nav_destination_modifier.cpp:1091`)
    - `.setFullScreenOverlay = SetFullScreenOverlay` (`nav_destination_modifier.cpp:1092`)
    - `.resetFullScreenOverlay = ResetFullScreenOverlay` (`nav_destination_modifier.cpp:1093`)
    - `.setNavDestinationSystemTransition = SetNavDestinationSystemTransition` (`nav_destination_modifier.cpp:1094`)
    - `.resetNavDestinationSystemTransition = ResetNavDestinationSystemTransition` (`nav_destination_modifier.cpp:1095`)
    - `.setNavDestinationSystemBarStyle = SetNavDestinationSystemBarStyle` (`nav_destination_modifier.cpp:1106`)
    - `.resetNavDestinationSystemBarStyle = ResetNavDestinationSystemBarStyle` (`nav_destination_modifier.cpp:1107`)
    - `.setIgnoreLayoutSafeArea = SetIgnoreLayoutSafeArea` (`nav_destination_modifier.cpp:1079`)
    - `.resetIgnoreLayoutSafeArea = ResetIgnoreLayoutSafeArea` (`nav_destination_modifier.cpp:1080`)
- AC-2: dynamic `SetFullScreenOverlay` 将 `ArkUIOptionalBool` 转为 `std::optional<bool>` (`nav_destination_modifier.cpp:691-699`)
  - 调用 `NavDestinationModelNG::SetFullScreenOverlay(frameNode, overlay)` (`nav_destination_modifier.cpp:699`)
  - Reset: `SetFullScreenOverlay(frameNode, std::nullopt)` (`nav_destination_modifier.cpp:706`)
- AC-3: dynamic `SetIgnoreLayoutSafeArea` 解析 type/edge 字符串为位掩码 (`nav_destination_modifier.cpp:147-185`)
  - 使用 `IgnoreLayoutSafeAreaOpts::TypeToMask` / `EdgeToMask` (`nav_destination_modifier.cpp:167,180`)
  - 调用 `NavDestinationModelNG::SetIgnoreLayoutSafeArea(frameNode, opts)` (`nav_destination_modifier.cpp:184`)
  - Reset 默认: type=SYSTEM(0b1), edges=ALL(0b1111) (`nav_destination_modifier.cpp:22-23,192-194`)
- AC-4: static modifier 通过 `ConstructImpl` 创建 FrameNode (`nav_destination_modifier.cpp(impl):130-144`)
  - `NavDestinationModelStatic::CreateFrameNode(id, navPathInfo, std::move(contentCreator))` (`nav_destination_modifier.cpp(impl):138`)
  - `ShallowBuilder` 包装 `contentCreator` (`navdestination_model_static.cpp:358`)
  - `NavDestinationPattern` 设置 `isStatic = true` (`navdestination_model_static.cpp:361`)
- AC-5: static `GetNavDestinationModifier()` 返回 `GENERATED_ArkUINavDestinationModifier` (`nav_destination_modifier.cpp(impl):856-896`)
  - 注册: `SetSystemBarStyleImpl`, `SetRecoverableImpl`, `SetSystemTransitionImpl`, `SetCustomTransitionImpl`, `SetFullScreenOverlayImpl`, `SetIgnoreLayoutSafeAreaImpl` (`nav_destination_modifier.cpp(impl):873-895`)
- AC-6: static `SetIgnoreLayoutSafeAreaImpl` 解析 type/edge 数组为位掩码 (`nav_destination_modifier.cpp(impl):794-834`)
  - 使用 `Converter::Convert<std::vector<uint32_t>>` 解析数组 (`nav_destination_modifier.cpp(impl):809,821`)
  - 调用 `NavDestinationModelStatic::SetIgnoreLayoutSafeArea(frameNode, opts)` (`nav_destination_modifier.cpp(impl):834`)
- AC-7: static `SetFullScreenOverlayImpl` 调用 `NavDestinationModelNG::SetFullScreenOverlay(frameNode, enabled)` (`nav_destination_modifier.cpp(impl):497-503`)
  - 注意: static 桥接中 fullScreenOverlay 调用的是 `NavDestinationModelNG`（非 ModelStatic）

### US-5: NavDestination 全屏覆盖 (fullScreenOverlay in SPLIT mode)

**角色**: 应用开发者  
**意图**: 在 SPLIT 模式下将 NavDestination 从 content 容器移至 overlay 容器，使其覆盖整个 Navigation 区域  
**验收标准**:

- AC-1: `fullScreenOverlay(Optional<boolean>)` 存储于 `NavDestinationLayoutPropertyBase::FullScreenOverlay` (`navdestination_layout_property_base.h:105`)
  - `ACE_DEFINE_PROPERTY_ITEM_WITHOUT_GROUP(FullScreenOverlay, bool, PROPERTY_UPDATE_MEASURE)` (`navdestination_layout_property_base.h:105`)
- AC-2: `SetFullScreenOverlay(FrameNode*, optional<bool>)` 先获取 previousRequest (`navdestination_model_ng.cpp:1644`)
  - 有值时 `UpdateFullScreenOverlay(value)` (`navdestination_model_ng.cpp:1646`)
  - 无值时 `ResetFullScreenOverlay()` (`navdestination_model_ng.cpp:1648`)
  - 调用 `navDestinationPattern->NotifyFullScreenOverlayRequestChange(previousRequest, fullScreenOverlay)` (`navdestination_model_ng.cpp:1652`)
- AC-3: `NotifyFullScreenOverlayRequestChange` 触发 Navigation 级别重算
  - `navigationNode->UpdateNavDestinationNodeWithoutMarkDirty(nullptr)` (`navdestination_pattern.cpp:209`)
  - `navigationNode->MarkDirtyNode(PROPERTY_UPDATE_MEASURE_SELF_AND_CHILD)` (`navdestination_pattern.cpp:212`)
  - overlay 节点和 content 节点分别 `RebuildRenderContextTree` (`navdestination_pattern.cpp:216,225`)
  - 根据 `isCurFullscreenOverlay` 条件切换容器可见性 (`navdestination_pattern.cpp:218-229`)
- AC-4: `NavDestinationGroupNode::IsFullScreenOverlay()` 返回 `isFullScreenOverlay_` (`navdestination_group_node.h:86-89`)
- AC-5: `GetUserSetFullScreenOverlay()` 获取用户设置的原始 overlay 值 (`navdestination_group_node.h:79`)

---

## 3 API 清单

### 3.1 ArkTS 属性 API

| API | 类型 | @since | 说明 |
|------|------|--------|------|
| `systemBarStyle(Optional<SystemBarStyle>)` | 属性设置 | 12 | NavDestination 级别系统栏样式 |
| `recoverable(Optional<boolean>)` | 属性设置 | 14 | 标记目的地可恢复 |
| `systemTransition(NavigationSystemTransitionType)` | 属性设置 | 14 | 预定义系统转场类型 |
| `customTransition(NavDestinationTransitionDelegate)` | 属性设置 | 15 | 自定义转场委托 |

### 3.2 C API (dynamic NavDestinationModifier)

| C API 函数 | @since | 对应 ModelNG 方法 |
|------|--------|------|
| `setNavDestinationSystemBarStyle(ArkUINodeHandle, ArkUI_Uint32)` | 12 | `NavDestinationModelNG::SetSystemBarStyle` |
| `resetNavDestinationSystemBarStyle(ArkUINodeHandle)` | 12 | `NavDestinationModelNG::SetSystemBarStyle(nullptr)` |
| `setRecoverable(ArkUINodeHandle, ArkUI_Bool)` | 14 | `NavDestinationModelNG::SetRecoverable` |
| `resetRecoverable(ArkUINodeHandle)` | 14 | `NavDestinationModelNG::SetRecoverable(true)` |
| `setNavDestinationSystemTransition(ArkUINodeHandle, int32_t)` | 14 | `NavDestinationModelNG::SetSystemTransitionType` |
| `resetNavDestinationSystemTransition(ArkUINodeHandle)` | 14 | `NavDestinationModelNG::SetSystemTransitionType(DEFAULT)` |
| `setFullScreenOverlay(ArkUINodeHandle, ArkUIOptionalBool)` | 14 | `NavDestinationModelNG::SetFullScreenOverlay` |
| `resetFullScreenOverlay(ArkUINodeHandle)` | 14 | `NavDestinationModelNG::SetFullScreenOverlay(nullopt)` |
| `setIgnoreLayoutSafeArea(ArkUINodeHandle, const char*, const char*)` | 12 | `NavDestinationModelNG::SetIgnoreLayoutSafeArea` |
| `resetIgnoreLayoutSafeArea(ArkUINodeHandle)` | 12 | `NavDestinationModelNG::SetIgnoreLayoutSafeArea(defaults)` |

### 3.3 C API (static NavDestinationModifier.static)

| C API 函数 | @since | 对应 ModelStatic 方法 |
|------|--------|------|
| `SetSystemBarStyleImpl(Ark_NativePointer, Opt_window_SystemBarStyle*)` | 23 | `NavDestinationModelStatic::SetSystemBarStyle(Color)` |
| `SetRecoverableImpl(Ark_NativePointer, Opt_Boolean*)` | 23 | `NavDestinationModelStatic::SetRecoverable(optional<bool>)` |
| `SetSystemTransitionImpl(Ark_NativePointer, Opt_NavigationSystemTransitionType*)` | 23 | `NavDestinationModelStatic::SetSystemTransitionType` |
| `SetCustomTransitionImpl(Ark_NativePointer, Opt_NavDestinationTransitionDelegate*)` | 23 | `NavDestinationModelStatic::SetCustomTransition` |
| `SetFullScreenOverlayImpl(Ark_NativePointer, Opt_Boolean*)` | 23 | `NavDestinationModelNG::SetFullScreenOverlay` |
| `SetIgnoreLayoutSafeAreaImpl(Ark_NativePointer, Opt_Array*, Opt_Array*)` | 23 | `NavDestinationModelStatic::SetIgnoreLayoutSafeArea` |
| `ConstructImpl(Ark_Int32 id, Ark_Int32 flags)` | 23 | `NavDestinationModelStatic::CreateFrameNode` |

### 3.4 Context API

| API | 类型 | @since | 说明 |
|------|------|--------|------|
| `NavDestinationContext.getConfigInRouteMap()` | 方法 | 12 | 获取路由配置信息 |
| `NavDestinationModifier` (class) | Modifier | 12 | dynamic 属性修改器 (`NavDestinationModifier.d.ts:43`) |
| `NavDestinationModifier.static` | Modifier | 23 | static 属性修改器 |

### 3.5 枚举与结构体

| 名称 | 类型 | 定义位置 |
|------|------|------|
| `NavigationSystemTransitionType` | enum class | `navigation_declaration.h:293-302` |
| `NavDestinationType` | enum class | `navigation_declaration.h:304-308` |
| `NavDestinationTransition` | struct | `navigation_declaration.h:320-326` |
| `NavDestinationTransitionDelegate` | type alias | `navigation_declaration.h:344-345` |
| `IgnoreLayoutSafeAreaOpts` | struct | `safe_area_insets.h:226` |
| `BarTranslateState` | enum class | `navdestination_layout_property_base.h:56-60` |

---

## 4 详细设计

### 4.1 systemBarStyle 设置与恢复机制

**数据流**:
1. ArkTS → `NavDestinationModel::SetSystemBarStyle(style)` (`navdestination_model.h:114`)
2. Dynamic → `NavDestinationModelNG::SetSystemBarStyle(FrameNode*, style)` (`navdestination_model_ng.cpp:1989-1996`)
3. Pattern → `NavDestinationPattern::SetSystemBarStyle(style)` (`navdestination_pattern.cpp:521-544`)
4. Static → `NavDestinationModelStatic::SetSystemBarStyle(FrameNode*, Color)` (`navdestination_model_static.cpp:714-722`)

**核心逻辑** (`navdestination_pattern.cpp:521-544`):
- 第一次调用: `backupStyle_ = windowManager->GetSystemBarStyle()` (`navdestination_pattern.cpp:531`)
- 设置当前: `currStyle_ = style` (`navdestination_pattern.cpp:533`)
- 激活应用: fullPageNavigation + topNavDestination 条件下 (`navdestination_pattern.cpp:537`)
  - `currStyle_ != nullptr` → `windowManager->SetSystemBarStyle(currStyle_)` (`navdestination_pattern.cpp:539`)
  - `currStyle_ == nullptr` → `navigationPattern->TryRestoreSystemBarStyle(windowManager)` (`navdestination_pattern.cpp:541`)
- 退出清理: `OnDetachFromMainTree` → `backupStyle_.reset()`, `currStyle_.reset()` (`navdestination_pattern.cpp:579-580`)

**存储位置**: `NavDestinationPattern::backupStyle_` 和 `currStyle_` (`navdestination_pattern.h:398-399`)

### 4.2 recoverable 标记与恢复逻辑

**数据流**:
1. ArkTS → `NavDestinationModel::SetRecoverable(bool)` (`navdestination_model.h:96`)
2. Dynamic → `NavDestinationModelNG::SetRecoverable(FrameNode*, bool)` (`navdestination_model_ng.cpp:1124-1128`)
3. Node → `NavDestinationGroupNode::SetRecoverable(bool)` → `recoverable_ = recoverable` (`navdestination_group_node.h:194-197`)
4. Static → `NavDestinationModelStatic::SetRecoverable(FrameNode*, optional<bool>)` → `recoverable.value_or(true)` (`navdestination_model_static.cpp:470-474`)
5. C API Reset → `SetRecoverable(frameNode, true)` (默认可恢复) (`nav_destination_modifier.cpp:479`)

**恢复判定**:
- `CanRecovery()` = `recoverable_ && !fromNavrouterAndNoRouteInfo_` (`navdestination_group_node.h:204-207`)
- `OnDetachFromMainTree` 仅对 HOME/RELATED 类型触发恢复通知 (`navdestination_pattern.cpp:581`)
- `SetPendingToClean(false)` 时调用 `navigationStack->MarkAutoCleanedFlag(id, hostNode->CanRecovery())` (`navdestination_pattern.cpp:1148`)

### 4.3 systemTransition 预定义转场类型

**枚举值映射** (`navigation_declaration.h:293-302`):

| 内部值 | 枚举名 | JS 枚举值 | 说明 |
|--------|--------|-----------|------|
| 0 | NONE | 1 | 无动画 |
| 1 | TITLE | 2 | 标题栏动画 |
| 2 (1<<1) | CONTENT | 3 | 内容滑动 |
| 3 (1|1<<1) | DEFAULT | 0 | 默认(=TITLE|CONTENT) |
| 4 (1<<2) | FADE | 4 | 淡入淡出 |
| 5 (1<<3) | EXPLODE | 5 | 爆炸效果 @since 15 |
| 6 (1<<4) | SLIDE_RIGHT | 6 | 右滑 @since 15 |
| 7 (1<<5) | SLIDE_BOTTOM | 7 | 底部滑入 @since 15 |

**数据流**:
- Dynamic: `NavDestinationModelNG::SetSystemTransitionType(FrameNode*, type)` → `navDestination->SetSystemTransitionType(type)` (`navdestination_model_ng.cpp:1820-1824`)
- Static C API: JS enum 值经 switch-case 映射后调用 `NavDestinationModelStatic::SetSystemTransitionType(frameNode, res)` (`nav_destination_modifier.cpp(impl):332-381`)
- C API dynamic: `SetNavDestinationSystemTransition(node, int32_t)` → `static_cast<NG::NavigationSystemTransitionType>(value)` (`nav_destination_modifier.cpp:133-137`)
- Reset: DEFAULT (`nav_destination_modifier.cpp:144`)

### 4.4 customTransition 自定义转场委托

**委托签名**: `std::function<std::optional<std::vector<NavDestinationTransition>>(NavigationOperation, bool isEnter)>` (`navigation_declaration.h:344-345`)

**NavDestinationTransition 结构** (`navigation_declaration.h:320-326`):
- `int32_t delay` — 动画延迟
- `int32_t duration` — 动画持续时间
- `RefPtr<Curve> curve` — 动画曲线
- `std::function<void()> event` — 动画触发回调
- `std::function<void()> onTransitionEnd` — 动画结束回调

**数据流**:
- Dynamic: `NavDestinationModelNG::SetCustomTransition(delegate)` → `node->SetNavDestinationTransitionDelegate(std::move(delegate))` (`navdestination_model_ng.cpp:2044-2051`)
  - 存储于 `NavDestinationGroupNode::navDestinationTransitionDelegate_` (`navdestination_group_node.h:352`)
- Static: `NavDestinationModelStatic::SetCustomTransition(FrameNode*, delegate)` → `node->SetNavDestinationTransitionDelegate(std::move(transitionDelegate))` (`navdestination_model_static.cpp:182-189`)
- C API static: `SetCustomTransitionImpl` 通过 `CallbackHelper` 封装 Ark 回调 (`nav_destination_modifier.cpp(impl):438-458`)
  - 转换 `NavigationOperation → Ark_NavigationOperation` (`nav_destination_modifier.cpp(impl):451`)
  - 转换 `bool isEnter → Ark_Boolean` (`nav_destination_modifier.cpp(impl):452`)
  - `InvokeWithOptConvertResult` 获取返回值 (`nav_destination_modifier.cpp(impl):453-456`)
  - undefined tag → `SetCustomTransition(frameNode, nullptr)` (`nav_destination_modifier.cpp(impl):445`)

### 4.5 fullScreenOverlay (SPLIT 模式)

**属性存储**: `NavDestinationLayoutPropertyBase::FullScreenOverlay` (`navdestination_layout_property_base.h:105`)
- `ACE_DEFINE_PROPERTY_ITEM_WITHOUT_GROUP(FullScreenOverlay, bool, PROPERTY_UPDATE_MEASURE)` (`navdestination_layout_property_base.h:105`)

**数据流**:
1. `NavDestinationModelNG::SetFullScreenOverlay(FrameNode*, optional<bool>)` (`navdestination_model_ng.cpp:1635-1653`)
   - 获取 previousRequest (`navdestination_model_ng.cpp:1644`)
   - Update/Reset property (`navdestination_model_ng.cpp:1646-1648`)
   - 通知 pattern: `navDestinationPattern->NotifyFullScreenOverlayRequestChange(previousRequest, fullScreenOverlay)` (`navdestination_model_ng.cpp:1652`)
2. `NotifyFullScreenOverlayRequestChange(previousRequest, currentRequest)` (`navdestination_pattern.cpp:196-231`)
   - 无变化则 return (`navdestination_pattern.cpp:199-201`)
   - 触发 Navigation 级重算: `navigationNode->UpdateNavDestinationNodeWithoutMarkDirty(nullptr)` (`navdestination_pattern.cpp:209`)
   - 标记 dirty: `navigationNode->MarkDirtyNode(PROPERTY_UPDATE_MEASURE_SELF_AND_CHILD)` (`navdestination_pattern.cpp:212`)
   - overlay/content 容器 rebuild (`navdestination_pattern.cpp:215-229`)
   - 根据 `isCurFullscreenOverlay` 切换容器可见性 (`navdestination_pattern.cpp:218,227`)
3. Node 状态: `NavDestinationGroupNode::IsFullScreenOverlay()` (`navdestination_group_node.h:86-89`)
4. `GetUserSetFullScreenOverlay()` (`navdestination_group_node.h:79`)

**static C API 桥接**: `SetFullScreenOverlayImpl` 调用 `NavDestinationModelNG::SetFullScreenOverlay` (`nav_destination_modifier.cpp(impl):497-503`)
- 注意: 此处使用 ModelNG 而非 ModelStatic，因为 fullScreenOverlay 需触发 Navigation 级重算

### 4.6 ignoreLayoutSafeArea

**Dynamic C API** (`nav_destination_modifier.cpp:147-195`):
- 解析 typeStr/edgesStr 为位掩码
- `IgnoreLayoutSafeAreaOpts::TypeToMask` / `EdgeToMask` (`nav_destination_modifier.cpp:167,180`)
- Reset 默认: type=SYSTEM(0b1), edges=ALL(0b1111) (`nav_destination_modifier.cpp:22-23`)
- 存储于 `NavDestinationLayoutPropertyBase::IgnoreLayoutSafeArea` (`navdestination_layout_property_base.h:100`)

**Static C API** (`nav_destination_modifier.cpp(impl):794-834`):
- 解析 `Opt_Array_LayoutSafeAreaType` / `Opt_Array_LayoutSafeAreaEdge` 为位掩码
- 调用 `NavDestinationModelStatic::SetIgnoreLayoutSafeArea(frameNode, opts)` (`nav_destination_modifier.cpp(impl):834`)

**ModelNG 方法** (`navdestination_model_ng.h:103-104`):
- `SetIgnoreLayoutSafeArea(IgnoreLayoutSafeAreaOpts)` (实例版)
- `static void SetIgnoreLayoutSafeArea(FrameNode*, IgnoreLayoutSafeAreaOpts)` (静态版)

### 4.7 freeze 属性

**数据流** (`navdestination_model_ng.cpp:2165-2181`):
- `NavDestinationModelNG::SetFreeze(bool freeze, bool isValid)` → `SetFreeze(frameNode, freeze, isValid)` (`navdestination_model_ng.cpp:2168`)
- isValid=false 时: `ViewAbstract::SetFreeze(false)`, `navDestinationNode->SetIsUserSetFreeze(false)` (`navdestination_model_ng.cpp:2176-2177`)
- isValid=true 时: `ViewAbstract::SetFreeze(freeze)`, `navDestinationNode->SetIsUserSetFreeze(true)` (`navdestination_model_ng.cpp:2180-2181`)
- `static void SetFreeze(FrameNode*, bool, bool)` (`navdestination_model_ng.h:176`)

### 4.8 NavDestinationContext.getConfigInRouteMap()

**JS 注册**: `JSClass<JSNavDestinationContext>::CustomMethod("getConfigInRouteMap", &JSNavDestinationContext::GetRouteInfo)` (`js_navdestination_context.cpp:164`)

---

## 5 关键类/文件映射

| 类/文件 | 路径 | 责任 |
|------|------|------|
| NavDestinationPattern | `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.cpp/h` | systemBarStyle backup/restore, recoverable, fullScreenOverlay 通知, lifecycle |
| NavDestinationLayoutPropertyBase | `frameworks/core/components_ng/pattern/navigation/navdestination_layout_property_base.h` | FullScreenOverlay, IgnoreLayoutSafeArea, HideTitleBar/ToolBar 属性 |
| NavDestinationLayoutProperty | `frameworks/core/components_ng/pattern/navrouter/navdestination_layout_property.h` | 继承 Base，增加 NoPixMap/ImageSource/PixelMap |
| NavDestinationModelNG | `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.cpp/h` | Dynamic 属性设置桥接 |
| NavDestinationModelStatic | `frameworks/core/components_ng/pattern/navrouter/navdestination_model_static.cpp/h` | Static 属性设置桥接 |
| NavDestinationGroupNode | `frameworks/core/components_ng/pattern/navrouter/navdestination_group_node.h` | recoverable_, CanRecovery(), IsFullScreenOverlay(), transitionDelegate_ |
| NavigationDeclaration | `frameworks/core/components_ng/pattern/navigation/navigation_declaration.h` | NavigationSystemTransitionType, NavDestinationTransition, NavDestinationTransitionDelegate, NavDestinationType |
| nav_destination_modifier.cpp (dynamic) | `frameworks/core/interfaces/native/node/nav_destination_modifier.cpp` | C API dynamic modifier 函数集 |
| nav_destination_modifier.cpp (static) | `frameworks/core/interfaces/native/implementation/nav_destination_modifier.cpp` | C API static modifier 函数集 |
| NavDestinationModifier.d.ts | `interface/sdk-js/api/arkui/NavDestinationModifier.d.ts` | ArkTS Modifier 声明 |
| JSNavDestinationContext | `frameworks/bridge/declarative_frontend/jsview/js_navdestination_context.cpp` | getConfigInRouteMap JS 桥接 |

---

## 6 约束与边界

1. DIALOG 模式 NavDestination 不支持 systemBarStyle、orientation、statusBar、navigationIndicator 配置（`navdestination_pattern.cpp:994,1043,1087` 均对 DIALOG mode return）
2. `recoverable` 默认值为 true；HOME 和 RELATED 类型才参与恢复通知（`navdestination_pattern.cpp:581`）
3. `CanRecovery()` 需要 `recoverable_ && !fromNavrouterAndNoRouteInfo_` 两个条件（`navdestination_group_node.h:204-207`）
4. fullScreenOverlay 变化触发 Navigation 级 `PROPERTY_UPDATE_MEASURE_SELF_AND_CHILD` dirty（`navdestination_pattern.cpp:212`）
5. static C API `SetFullScreenOverlayImpl` 使用 `NavDestinationModelNG` 而非 `NavDestinationModelStatic`（`nav_destination_modifier.cpp(impl):503`）
6. customTransition 委托的 `NavigationOperation` 类型: PUSH=0, POP=1（来自 `NavigationOperation` 枚举）
7. NavigationSystemTransitionType 内部值为位掩码设计（NONE=0, TITLE=1, CONTENT=2, DEFAULT=3=TITLE|CONTENT, FADE=4, EXPLODE=5...），JS API 映射不同（NONE=1, TITLE=2, CONTENT=3, FADE=4, EXPLODE=5, SLIDE_RIGHT=6, SLIDE_BOTTOM=7）
8. `NavDestinationModifier` ArkTS class 声明为 `extends NavDestinationAttribute implements AttributeModifier<NavDestinationAttribute>` (`NavDestinationModifier.d.ts:43`)

---

## 7 测试要点

| 测试项 | 覆盖点 | 方法 |
|--------|--------|------|
| systemBarStyle backup/restore | backupStyle_ 保存, currStyle_ 应用, OnDetachFromMainTree 重置 | UT: 模拟 push→set→pop 流程验证 restore |
| recoverable 默认值 | 默认 true, 设置 false 后 CanRecovery=false | UT: 检查 SetRecoverable(false) → CanRecovery() |
| HOME/RELATED 通知 | OnDetachFromMainTree 仅对 HOME/RELATED 触发 | UT: 不同 NavDestinationType 的 detach 行为 |
| systemTransition enum | 内部值 vs JS 值映射 | UT: 验证 static C API JS→内部映射 |
| customTransition 回调 | NavigationOperation + isEnter 组合 | UT: PUSH+enter, POP+exit 回调触发 |
| fullScreenOverlay | Navigation dirty + 容器切换 | UT: SPLIT 模式 overlay/content 容器切换 |
| C API Modifier | dynamic + static setter/resetter | C API UT: linux_unittest_capi |
| getConfigInRouteMap | JS 桥接方法 | UT: JSNavDestinationContext.GetRouteInfo |

---

## 8 版本演进

| 版本 | 新增/变更 |
|------|-----------|
| @since 12 | systemBarStyle, NavDestinationModifier (dynamic), ignoreLayoutSafeArea, getConfigInRouteMap |
| @since 14 | recoverable, systemTransition, fullScreenOverlay |
| @since 15 | customTransition, EXPLODE, SLIDE_RIGHT, SLIDE_BOTTOM |
| @since 23 | NavDestinationModifier.static (static C API bridge) |
