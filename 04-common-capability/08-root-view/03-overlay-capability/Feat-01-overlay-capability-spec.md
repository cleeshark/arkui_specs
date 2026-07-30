# 特性规格

> Func-04-08-03-Feat-01 浮层能力：固化 OverlayManager 的 addComponentContent/removeComponentContent/showComponentContent/hideComponentContent/showAllComponentContents/hideAllComponentContents/addComponentContentWithOrder/openOrderOverlay/setOverlayManagerOptions API 行为与层级约束规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 浮层能力 (Overlay Capability) |
| 特性编号 | Func-04-08-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 12 起 OverlayManager 类，API 15 起 Options，API 18 起 addComponentContentWithOrder，API 26 起 openOrderOverlay |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | OverlayManager 浮层管理 API 全量行为 | 补录 addComponentContent/remove/show/hide/addComponentContentWithOrder/openOrderOverlay/setOverlayManagerOptions 行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/08-root-view/03-overlay-capability/design.md` | Baselined |
| 开发指南 | `docs/zh-cn/application-dev/ui/arkts-create-overlaymanager.md` | — |
| SDK API | `docs/zh-cn/application-dev/reference/apis-arkui/arkts-apis-uicontext-overlaymanager.md` | — |

---

## 用户故事

### US-1: 添加浮层节点

**作为** 应用开发者,
**我想要** 通过 `addComponentContent(content, index?)` 将 ComponentContent 添加到 OverlayManager,
**以便** 在 Page 之上展示常驻悬浮内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `addComponentContent(content)` 不传 index THEN 节点默认添加至最高层（index 等效 < 0/null/undefined） | 正常 |
| AC-1.2 | WHEN 调用 `addComponentContent(content, index)` 传入 index ≥ 0 THEN index 值越大层级越高；相同 index 时后添加的层级更高 | 边界 |
| AC-1.3 | WHEN 同一 ComponentContent 被添加多次 THEN 只保留最后一次添加的节点 | 异常 |
| AC-1.4 | WHEN 添加节点 THEN 桥接层通过 `content.getFrameNode()` 提取 FrameNode 委托给 NAPI `addFrameNode`，CreateOverlayNode 确保 OVERLAY_ETS_TAG 容器存在 | 正常 |

### US-2: 删除浮层节点

**作为** 应用开发者,
**我想要** 通过 `removeComponentContent(content)` 从 OverlayManager 删除指定节点,
**以便** 移除不再需要的悬浮内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `removeComponentContent(content)` THEN 从 overlay 容器移除对应 FrameNode | 正常 |
| AC-2.2 | WHEN 同一 ComponentContent 已被重复添加（只保留最后）THEN removeComponentContent 只需调用一次即可移除 | 边界 |

### US-3: 显示/隐藏浮层节点

**作为** 应用开发者,
**我想要** 通过 show/hide 控制浮层节点可见性,
**以便** 在不删除节点的前提下临时切换显示状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `showComponentContent(content)` THEN 对应节点变为可见 | 正常 |
| AC-3.2 | WHEN 调用 `hideComponentContent(content)` THEN 对应节点变为不可见 | 正常 |
| AC-3.3 | WHEN 调用 `showAllComponentContents()` / `hideAllComponentContents()` THEN 批量设置所有浮层节点可见/不可见 | 正常 |

### US-4: 有序添加浮层（LevelOrder）

**作为** 应用开发者,
**我想要** 通过 `addComponentContentWithOrder(content, levelOrder?)` 指定精确 z-index,
**以便** 精确控制多个浮层节点的堆叠顺序。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `addComponentContentWithOrder(content, levelOrder)` THEN 通过 LevelOrder 指定精确浮点 z-index，levelOrder 越大层级越高 | 正常 |
| AC-4.2 | WHEN 不传 levelOrder THEN 默认 LevelOrder.clamp(0) | 边界 |
| AC-4.3 | WHEN 添加有序节点 THEN PutLevelOrder 注册到 nodeIdOrderMap_ + orderNodesMap_，GetNextNodeWithOrder 确定插入位置 | 正常 |

### US-5: openOrderOverlay（OrderOverlayOptions）

**作为** 应用开发者,
**我想要** 通过 `openOrderOverlay(content, options?)` 打开支持层级配置的浮层,
**以便** 在指定层级（OVERLAY/EMBEDDED）展示内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `openOrderOverlay(content, options)` THEN 返回 Promise，成功时 resolve，失败时 reject（错误码 103307） | 正常 |
| AC-5.2 | WHEN options.levelMode = LevelMode.OVERLAY（默认）THEN 浮层挂载到全局 OverlayManager | 正常 |
| AC-5.3 | WHEN options.levelMode = LevelMode.EMBEDDED 且设置 levelUniqueId THEN 通过 uniqueId 查找页面级 OverlayManager 挂载 | 边界 |

### US-6: OverlayManagerOptions

**作为** 应用开发者,
**我想要** 通过 `setOverlayManagerOptions(options)` 配置浮层行为,
**以便** 控制返回键响应与渲染选项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `setOverlayManagerOptions({ enableBackPressedEvent: true })` THEN OverlayManager 响应侧滑/返回手势 | 正常 |
| AC-6.2 | WHEN API < 19 THEN 不支持侧滑关闭，需在 onBackPress 中添加关闭逻辑 | 边界 |
| AC-6.3 | WHEN 调用 `getOverlayManagerOptions()` THEN 返回当前 OverlayManagerOptions（renderRootOverlay/enableBackPressedEvent/onBackPress） | 正常 |

### US-7: 层级约束与事件机制

**作为** 应用开发者,
**我想要** 了解浮层层级位置与事件传递规则,
**以便** 正确设计浮层交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 浮层节点显示 THEN 层级在 Page 之上、Dialog/Popup/Menu/BindSheet/BindContentCover/Toast 之下 | 边界 |
| AC-7.2 | WHEN 浮层节点 show/hide THEN 无默认动画 | 边界 |
| AC-7.3 | WHEN 浮层节点安全区域内外的绘制与键盘避让 THEN 与 Page 一致 | 边界 |
| AC-7.4 | WHEN 事件发生 THEN WrappedBuilder 装饰的组件优先接收；设置 hitTestBehavior=HitTestMode.Transparent 可将事件透传至底层 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 jsUIContext.js:1914-1922 |
| AC-1.2 | US-1 | R-2 | 代码审查 arkts-apis-uicontext-overlaymanager.md#addcomponentcontent12 |
| AC-1.3 | US-1 | R-3 | 代码审查 SDK 文档约束 |
| AC-1.4 | US-1 | R-4 | 代码审查 jsUIContext.js:1917 + overlay_manager.cpp:6016-6045 |
| AC-2.1 | US-2 | R-5 | 代码审查 jsUIContext.js:1934-1937 |
| AC-2.2 | US-2 | R-3 | 代码审查 SDK 文档约束 |
| AC-3.1 | US-3 | R-6 | 代码审查 jsUIContext.js:1940-1943 |
| AC-3.2 | US-3 | R-7 | 代码审查 jsUIContext.js:1946-1949 |
| AC-3.3 | US-3 | R-8 | 代码审查 jsUIContext.js:1952-1961 |
| AC-4.1 | US-4 | R-9 | 代码审查 jsUIContext.js:1924-1931 |
| AC-4.2 | US-4 | R-10 | 代码审查 arkts-apis-uicontext-overlaymanager.md#addcomponentcontentwithorder18 |
| AC-4.3 | US-4 | R-11 | 代码审查 overlay_manager.cpp:1980-1991 |
| AC-5.1 | US-5 | R-12 | 代码审查 jsUIContext.js:1964-1968 |
| AC-5.2 | US-5 | R-13 | 代码审查 overlay_options.h OrderOverlayOptions |
| AC-5.3 | US-5 | R-14 | 代码审查 level_mode.h LevelMode + levelUniqueId |
| AC-6.1 | US-6 | R-15 | 代码审查 jsUIContext.js:1900-1906 |
| AC-6.2 | US-6 | R-16 | 代码审查 arkts-create-overlaymanager.md 规格约束 |
| AC-6.3 | US-6 | R-17 | 代码审查 jsUIContext.js:1908-1912 |
| AC-7.1 | US-7 | R-18 | 代码审查 arkts-apis-uicontext-overlaymanager.md 说明 |
| AC-7.2 | US-7 | R-19 | 代码审查 arkts-create-overlaymanager.md 规格约束 |
| AC-7.3 | US-7 | R-20 | 代码审查 arkts-apis-uicontext-overlaymanager.md 说明 |
| AC-7.4 | US-7 | R-21 | 代码审查 arkts-create-overlaymanager.md 事件机制 |

## 规则定义

> **统一规则表。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | addComponentContent 不传 index | 节点添加至最高层 | `jsUIContext.js:1914-1922` | AC-1.1 |
| R-2 | 边界 | addComponentContent 传 index ≥ 0 | index 越大层级越高；相同 index 后添加更高 | `arkts-apis-uicontext-overlaymanager.md#addcomponentcontent12` | AC-1.2 |
| R-3 | 异常 | 同一 ComponentContent 添加多次 | 只保留最后一次 | `arkts-apis-uicontext-overlaymanager.md#addcomponentcontent12` | AC-1.3, AC-2.2 |
| R-4 | 行为 | addComponentContent 桥接 | content.getFrameNode() → NAPI addFrameNode → CreateOverlayNode + 挂载 | `jsUIContext.js:1917` + `overlay_manager.cpp:6016-6045` | AC-1.4 |
| R-5 | 行为 | removeComponentContent | 从 overlay 容器移除 FrameNode | `jsUIContext.js:1934-1937` | AC-2.1 |
| R-6 | 行为 | showComponentContent | 节点变为可见 | `jsUIContext.js:1940-1943` | AC-3.1 |
| R-7 | 行为 | hideComponentContent | 节点变为不可见 | `jsUIContext.js:1946-1949` | AC-3.2 |
| R-8 | 行为 | showAll/hideAllComponentContents | 批量设置所有节点可见/不可见 | `jsUIContext.js:1952-1961` | AC-3.3 |
| R-9 | 行为 | addComponentContentWithOrder(content, levelOrder) | LevelOrder 指定精确浮点 z-index | `jsUIContext.js:1924-1931` | AC-4.1 |
| R-10 | 边界 | 不传 levelOrder | 默认 LevelOrder.clamp(0) | `arkts-apis-uicontext-overlaymanager.md#addcomponentcontentwithorder18` | AC-4.2 |
| R-11 | 行为 | 有序添加内部 | PutLevelOrder 注册 nodeIdOrderMap_+orderNodesMap_，GetNextNodeWithOrder 确定插入位置 | `overlay_manager.cpp:1980-1991` | AC-4.3 |
| R-12 | 行为 | openOrderOverlay(content, options) | 返回 Promise，成功 resolve，失败 reject(103307) | `jsUIContext.js:1964-1968` | AC-5.1 |
| R-13 | 行为 | levelMode=OVERLAY（默认） | 挂载到全局 OverlayManager | `overlay_options.h` | AC-5.2 |
| R-14 | 边界 | levelMode=EMBEDDED + levelUniqueId | 通过 uniqueId 查找页面级 OverlayManager | `level_mode.h` | AC-5.3 |
| R-15 | 行为 | setOverlayManagerOptions({enableBackPressedEvent:true}) | 响应侧滑/返回手势 | `jsUIContext.js:1900-1906` | AC-6.1 |
| R-16 | 边界 | API < 19 | 不支持侧滑关闭，需 onBackPress 手动关闭 | `arkts-create-overlaymanager.md` | AC-6.2 |
| R-17 | 行为 | getOverlayManagerOptions() | 返回 renderRootOverlay/enableBackPressedEvent/onBackPress | `jsUIContext.js:1908-1912` | AC-6.3 |
| R-18 | 边界 | 浮层层级 | Page 之上、Dialog/Popup/Menu/BindSheet/BindContentCover/Toast 之下 | `arkts-apis-uicontext-overlaymanager.md` | AC-7.1 |
| R-19 | 边界 | show/hide 动画 | 无默认动画 | `arkts-create-overlaymanager.md` | AC-7.2 |
| R-20 | 边界 | 安全区域与键盘避让 | 与 Page 一致 | `arkts-apis-uicontext-overlaymanager.md` | AC-7.3 |
| R-21 | 行为 | 事件机制 | WrappedBuilder 优先接收；HitTestMode.Transparent 透传 | `arkts-create-overlaymanager.md` | AC-7.4 |
| R-22 | 恢复 | 推荐使用 AppStorage | 避免页面切换时属性值变化导致业务错误 | `arkts-create-overlaymanager.md` | — |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 添加节点 (AC-1.1~1.4) | 代码审查 + SDK 文档 | index 层级规则；重复添加；getFrameNode 桥接 |
| VM-2 | US-2 删除节点 (AC-2.1~2.2) | 代码审查 | removeComponentContent；重复添加只保留一次 |
| VM-3 | US-3 显示/隐藏 (AC-3.1~3.3) | 代码审查 | show/hide 单个与批量；无默认动画 |
| VM-4 | US-4 有序添加 (AC-4.1~4.3) | 代码审查 + SDK 文档 | LevelOrder 精确 z-index；默认 clamp(0)；双 map 注册 |
| VM-5 | US-5 openOrderOverlay (AC-5.1~5.3) | 代码审查 | Promise 返回；OVERLAY/EMBEDDED；levelUniqueId |
| VM-6 | US-6 OverlayManagerOptions (AC-6.1~6.3) | 代码审查 + SDK 文档 | enableBackPressedEvent；API 19 侧滑；getOverlayManagerOptions |
| VM-7 | US-7 层级约束与事件 (AC-7.1~7.4) | SDK 文档 | 层级位置；无动画；安全区域；事件透传 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1914-1922` |
| AC-1.2 | 代码审查 | `docs/zh-cn/application-dev/reference/apis-arkui/arkts-apis-uicontext-overlaymanager.md#addcomponentcontent12` |
| AC-1.3 | 代码审查 | 同上 SDK 文档约束 |
| AC-1.4 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1917` + `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:6016-6045` |
| AC-2.1 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1934-1937` |
| AC-2.2 | 代码审查 | SDK 文档约束 |
| AC-3.1 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1940-1943` |
| AC-3.2 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1946-1949` |
| AC-3.3 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1952-1961` |
| AC-4.1 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1924-1931` |
| AC-4.2 | 代码审查 | `docs/.../arkts-apis-uicontext-overlaymanager.md#addcomponentcontentwithorder18` |
| AC-4.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:1980-1991` |
| AC-5.1 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1964-1968` |
| AC-5.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_options.h` |
| AC-5.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/level_mode.h` |
| AC-6.1 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1900-1906` |
| AC-6.2 | 代码审查 | `docs/zh-cn/application-dev/ui/arkts-create-overlaymanager.md` 规格约束 |
| AC-6.3 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:1908-1912` |
| AC-7.1 | 代码审查 | `docs/.../arkts-apis-uicontext-overlaymanager.md` 说明 |
| AC-7.2 | 代码审查 | `docs/zh-cn/application-dev/ui/arkts-create-overlaymanager.md` 规格约束 |
| AC-7.3 | 代码审查 | 同上 |
| AC-7.4 | 代码审查 | 同上 事件机制 |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `docs/zh-cn/application-dev/reference/apis-arkui/arkts-apis-uicontext-overlaymanager.md`

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `addComponentContent(content, index?): void` | Public | content: ComponentContent; index?: number | void | N/A | 添加节点到 overlay，index 控制层级 | AC-1.1~1.4 |
| `addComponentContentWithOrder(content, levelOrder?): void` | Public | content; levelOrder?: LevelOrder | void | N/A | 有序添加（@since 18） | AC-4.1~4.3 |
| `removeComponentContent(content): void` | Public | content: ComponentContent | void | N/A | 删除节点 | AC-2.1~2.2 |
| `showComponentContent(content): void` | Public | content: ComponentContent | void | N/A | 显示节点 | AC-3.1 |
| `hideComponentContent(content): void` | Public | content: ComponentContent | void | N/A | 隐藏节点 | AC-3.2 |
| `showAllComponentContents(): void` | Public | — | void | N/A | 显示全部 | AC-3.3 |
| `hideAllComponentContents(): void` | Public | — | void | N/A | 隐藏全部 | AC-3.3 |
| `openOrderOverlay(content, options?): Promise<void>` | Public | content; options?: OrderOverlayOptions | Promise | 103307 | 打开有序浮层（@since 26） | AC-5.1~5.3 |
| `setOverlayManagerOptions(options): void` | Public | OverlayManagerOptions | void | N/A | 设置选项（@since 15） | AC-6.1 |
| `getOverlayManagerOptions(): OverlayManagerOptions` | Public | — | OverlayManagerOptions | N/A | 获取选项（@since 15） | AC-6.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无变更/废弃 API | — |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | OverlayManager 类首批接口（addComponentContent/remove/show/hide/showAll/hideAll） | 新增能力 | — |
| API 15 | OverlayManagerOptions（enableBackPressedEvent/onBackPress/renderRootOverlay） | 新增选项 | — |
| API 18 | addComponentContentWithOrder（LevelOrder 精确 z-index） | 新增方法 | 旧版用 index |
| API 19 | enableBackPressedEvent 支持侧滑关闭 | API < 19 不支持侧滑 | 需 onBackPress 手动关闭 |
| API 26 | openOrderOverlay（OrderOverlayOptions + LevelMode + levelUniqueId） | 新增方法 | 旧版用 addComponentContentWithOrder |

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 层级位置 | Page 之上、Dialog/Popup/Menu/BindSheet/BindContentCover/Toast 之下 | AC-7.1 |
| 无默认动画 | show/hide 无淡入淡出 | AC-7.2 |
| 安全区域与键盘避让 | 与 Page 一致 | AC-7.3 |
| 事件优先级 | WrappedBuilder 优先接收；HitTestMode.Transparent 透传 | AC-7.4 |
| index 层级规则 | ≥0 越大越高、相同后添加更高、<0/null/undefined 最高 | AC-1.2 |
| 重复添加 | 同一 ComponentContent 只保留最后 | AC-1.3 |
| AppStorage 推荐 | 避免页面切换属性变化 | — |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 添加/删除 O(1)；z-index 查找 O(log n) | 代码审查 | overlay_manager.cpp |
| 可靠性 | 重复添加只保留最后，避免重复节点 | 代码审查 | SDK 文档 |
| 可调试性 | getOverlayManagerOptions 可查询当前配置 | 代码审查 | jsUIContext.js:1908-1912 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 浮层内容由开发者负责无障碍 | — |
| 大字体 | 否 | 无差异，浮层内容由开发者控制 | — |
| 深色模式 | 否 | 无差异，浮层颜色由开发者控制 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 12/15/18/19/26 版本演进 | 兼容性声明 |
| 生态兼容 | 否 | 无差异 | — |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（不涉及 popup/modal/sheet/dialog 组件生命周期）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/pattern/overlay/overlay_manager.h` | OverlayManager 类（CreateOverlayNode/AddFrameNodeToOverlay/ShowNodeOnOverlay 等） |
| `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp` | OverlayManager 实现（CreateOverlayNode L6016-6045 / PutLevelOrder L1980-1991） |
| `frameworks/core/components_ng/pattern/overlay/overlay_options.h` | OrderOverlayOptions |
| `frameworks/core/components_ng/pattern/overlay/level_mode.h` | LevelMode 枚举（OVERLAY/EMBEDDED） |
| `frameworks/core/components_ng/pattern/overlay/level_order.h` | LevelOrder 类 |
| `frameworks/bridge/declarative_frontend/engine/jsUIContext.js` | OverlayManager 桥接层（addComponentContent L1914 / openOrderOverlay L1964） |
| `interfaces/napi/kits/overlay/js_overlay.cpp` | NAPI @ohos.overlayManager 导出（10 个函数 L401-411） |

### 开发文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/arkts-create-overlaymanager.md` | 浮层开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkts-apis-uicontext-overlaymanager.md` | OverlayManager SDK API 参考 |
