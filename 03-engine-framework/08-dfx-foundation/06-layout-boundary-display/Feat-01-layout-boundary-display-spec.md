# 特性规格

## 概述

| 属性 | 值 |
|------|------|
| 特性名称 | 布局边界显示调试能力 |
| 特性编号 | Func-03-08-06-Feat-01 |
| 所属 Epic | DFX 调试工具 |
| 优先级 | P1 |
| 目标版本 | API 10+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 已有实现补录（lineage: new-on-legacy），无代码变更。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 布局边界显示调试能力规格文档 | 补录已有框架内部 DFX 能力的规格文档 |

## 输入文档

| 文档类型 | 路径 |
|---------|------|
| 设计文档 | `specs/03-engine-framework/08-dfx-foundation/06-layout-boundary-display/design.md` |
| 源码定位 | `adapter/ohos/osal/system_properties.cpp`, `frameworks/core/components_ng/render/debug_boundary_painter.cpp`, `frameworks/core/common/render_boundary_manager.cpp` |

## 用户故事

### US-1: 开发者开启布局边界调试显示

**As a** 应用开发者
**I want** 通过系统参数开启布局边界显示，以便在调试 UI 布局问题时可视化每个组件的 margin/border/padding 区域
**So that** 快速定位布局溢出、margin 重叠、尺寸异常等问题

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-1.1 | **WHEN** 系统处于开发者模式且设置 `persist.ace.debug.boundary.enabled` 为 `"true"` **THEN** 所有 FrameNode 的 marginFrameSize 区域显示红色（`0xFFFA2A2D`）矩形边界框，线宽 1.0px | 正常 |
| AC-1.2 | **WHEN** 布局边界显示已开启 **THEN** 每个 FrameNode 的四角显示蓝色（`0xFF007DFF`）L 型角标，每条边长度 8.0px | 正常 |
| AC-1.3 | **WHEN** 布局边界显示已开启 **THEN** 每个 FrameNode 的 margin 区域以品红色半透明（`0x3FFF00AA`，alpha=0x3F）填充 | 正常 |
| AC-1.4 | **WHEN** 系统未处于开发者模式（`developerModeOn_ == false`）**THEN** 即使设置 `persist.ace.debug.boundary.enabled` 为 `"true"`，布局边界也不显示 | 边界 |
| AC-1.5 | **WHEN** 在 500ms 内连续 toggle `persist.ace.debug.boundary.enabled` 参数 3 次以上（true→false→true）**THEN** 最终显示状态与最后一次参数值一致，且中间态的全树重绘次数被任务队列去重机制最小化 | 边界 |
| AC-1.6 | **WHEN** 页面包含 LazyForEach/Repeat 虚拟滚动列表且布局边界已开启 **THEN** 当前屏幕可见的缓存项显示布局边界，未加载的回收项不显示 | 正常 |
| AC-1.7 | **WHEN** 同一页面在 NG 管线和 Legacy 管线下分别渲染且布局边界已开启 **THEN** 两种管线下边界颜色（RED `0xFFFA2A2D`/BLUE `0xFF007DFF`/MAGENTA `0x3FFF00AA`）和线宽（1.0px）一致 | 正常 |
| AC-1.8 | **WHEN** 布局边界显示已开启且对页面进行 UI 截图 **THEN** 截图结果中不包含调试边界（因 `SetNoNeedUICaptured(true)`） | 正常 |
| AC-1.9 | **WHEN** 设置 `persist.ace.debug.boundary.enabled` 为 `"false"` **THEN** 所有节点的布局边界立即消失（通过 `WatchParameter` 运行时生效，无需重启） | 正常 |

### US-2: 开发者开启手势边界调试显示

**As a** 应用开发者
**I want** 通过系统参数开启手势响应区域边界显示，以便在调试手势冲突时可视化每个组件注册的手势响应区域
**So that** 快速定位手势抢占、响应区域重叠、手势未注册等问题

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-2.1 | **WHEN** 设置 `persist.ace.debug.gesture.boundary.enabled` 为 `"true"` 且编译宏 `GESTURE_DEBUG_BOUNDARY_SUPPORTED` 已定义 **THEN** 活跃手势节点的边界按手势类型着色显示，线宽 8.0px | 正常 |
| AC-2.2 | **WHEN** 手势边界显示已开启且节点同时注册了多种手势类型 **THEN** 该节点边界显示多种颜色的叠加（每种手势类型对应一种颜色） | 正常 |
| AC-2.3 | **WHEN** 手势边界颜色资源查找失败 **THEN** 回退使用红色（`Color::RED`）作为该手势类型的边界颜色 | 异常 |
| AC-2.4 | **WHEN** 手势边界参数在应用运行期间被修改 **THEN** 修改不即时生效，需重启应用后生效（无 `WatchParameter` 注册） | 边界 |
| AC-2.5 | **WHEN** FrameNode 的 marginFrameSize 的宽度或高度小于 32vp * density（像素值）**THEN** 该节点不显示手势边界 | 边界 |
| AC-2.6 | **WHEN** 编译宏 `GESTURE_DEBUG_BOUNDARY_SUPPORTED` 未定义 **THEN** `IsGestureDebugBoundaryEnabled()` 始终返回 `false`，手势边界功能不可用 | 边界 |

### US-3: 开发者模式安全门控

**As a** 系统安全管理者
**I want** 布局边界显示功能仅在开发者模式下可用
**So that** 生产环境用户不会意外看到调试边界或泄露布局信息

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-3.1 | **WHEN** `developerModeOn_` 从 `true` 变为 `false`（开发者模式关闭）**THEN** `SetDebugBoundaryEnabled` 的结果被 AND 运算置为 `false`，布局边界立即消失 | 正常 |
| AC-3.2 | **WHEN** `developerModeOn_` 为 `false` 时 `SetDebugBoundaryEnabled(true)` 被调用 **THEN** `debugBoundaryEnabled_` 原子变量存储 `false`（`true && false`） | 边界 |
| AC-3.3 | **WHEN** 手势边界参数为 `"true"` 且开发者模式关闭 **THEN** 手势边界仍可显示（手势边界不受 `developerModeOn_` 门控） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1 | R-1, R-7 | TASK-1 | 手动验证 | `debug_boundary_painter.cpp:24,34-35` |
| AC-1.2 | R-1, R-8 | TASK-1 | 手动验证 | `debug_boundary_painter.cpp:23,25,82-83` |
| AC-1.3 | R-1, R-9 | TASK-1 | 手动验证 | `debug_boundary_painter.cpp:26,57` |
| AC-1.4 | R-2 | TASK-1 | 手动验证 | `system_properties.cpp:770,1330` |
| AC-1.5 | R-3, R-10 | TASK-1 | 单元测试 | `render_boundary_manager.cpp:26,53-73` |
| AC-1.6 | R-4 | TASK-1 | 手动验证 | `ui_node.cpp:2641-2646` |
| AC-1.7 | R-5 | TASK-1 | 手动验证 | `debug_boundary_painter.cpp:20-26` (NG), `components/common/painter/debug_boundary_painter.h:38-46` (Legacy) |
| AC-1.8 | R-6 | TASK-1 | 手动验证 | `rosen_render_context.cpp:1052` |
| AC-1.9 | R-1, R-11 | TASK-1 | 手动验证 | `ace_container.cpp:145-151,4668-4669` |
| AC-2.1 | R-7, R-12 | TASK-1 | 手动验证 | `gesture_debug_boundary_manager.h:60`, `system_properties.cpp:118-124` |
| AC-2.2 | R-12 | TASK-1 | 手动验证 | `gesture_debug_boundary_manager.cpp:130-135` |
| AC-2.3 | R-13 | TASK-1 | 手动验证 | `gesture_debug_boundary_manager.cpp:144` |
| AC-2.4 | R-14 | TASK-1 | 手动验证 | `system_properties.cpp:118-124`（无 WatchParameter） |
| AC-2.5 | R-15 | TASK-1 | 单元测试 | `gesture_debug_boundary_manager.h:59`, `gesture_debug_boundary_manager.cpp:121-124` |
| AC-2.6 | R-16 | TASK-1 | 手动验证 | `system_properties.cpp:122-124` |
| AC-3.1 | R-2 | TASK-1 | 手动验证 | `system_properties.cpp:1330` |
| AC-3.2 | R-2 | TASK-1 | 单元测试 | `system_properties.cpp:1330` |
| AC-3.3 | R-17 | TASK-1 | 手动验证 | `system_properties.cpp:771`（无 `&& developerModeOn_`） |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|---------|---------|-----------|---------|
| R-1 | 行为 | `GetDebugBoundaryEnabled() == true` 且 `NeedDebugBoundary() == true` | 在 `SyncGeometryProperties` 中调用 `PaintDebugBoundary(true)`，创建 `DebugBoundaryModifier` 并添加到 RS 节点 | 仅对 `RSCanvasNode` 类型创建修饰器（`rosen_render_context.cpp:1049`） | AC-1.1, AC-1.9 |
| R-2 | 边界 | `SetDebugBoundaryEnabled(value)` 被调用 | `debugBoundaryEnabled_` 存储 `value && developerModeOn_` | `developerModeOn_ == false` 时无论 value 为何，结果为 `false` | AC-1.4, AC-3.1, AC-3.2 |
| R-3 | 行为 | `PostTaskRenderBoundary` 被调用且任务队列非空 | 调用 `ResetTaskQueue` 检查队首任务目标值：相同则取消队尾冗余任务并返回 `false`（不新增）；不同则取消队首并返回 `true`（新增） | 快速 toggle 时保证最终状态与最后一次调用一致 | AC-1.5 |
| R-4 | 行为 | `PaintDebugBoundaryTreeAll(flag)` 在 LazyForEachNode/RepeatVirtualScroll2Node 等语法节点上调用 | 覆盖实现遍历内部缓存的活跃项，对每个缓存项调用 `PaintDebugBoundary` 和递归 | 不触发额外项的创建，保持惰性加载语义 | AC-1.6 |
| R-5 | 行为 | NG 管线和 Legacy 管线同时开启布局边界 | 颜色值相同：RED `0xFFFA2A2D`、BLUE `0xFF007DFF`、MAGENTA `0x3FFF00AA`；线宽相同：1.0px | NG 使用 `float` 类型尺寸（`SizeF`），Legacy 使用 `double`（`Size`） | AC-1.7 |
| R-6 | 行为 | `DebugBoundaryModifier` 被创建 | 调用 `SetNoNeedUICaptured(true)`，修饰器在 UI 截图中不可见 | 修饰器在 RenderService 线程执行绘制（非 UI 线程） | AC-1.8 |
| R-7 | 行为 | 布局边界绘制触发 | `DebugBoundaryPainter::DrawDebugBoundaries` 依次执行：`PaintDebugBoundary`（红色矩形框）→ `PaintDebugCorner`（蓝色角标）→ `PaintDebugMargin`（品红填充） | 红色框线宽 1.0px，角标边长 8.0px，margin alpha=0x3F | AC-1.1, AC-1.2, AC-1.3, AC-2.1 |
| R-8 | 行为 | `PaintDebugCorner` 执行 | 绘制 4 个角的 L 型蓝色角标，每角 2 条线（水平+垂直），每条长 8.0px | 右下角需减去 `HALF_STROKE_WIDTH_OFFSET`（0.5px）偏移 | AC-1.2 |
| R-9 | 行为 | `PaintDebugMargin` 执行 | 绘制 4 块品红色半透明矩形（上/下/左/右 margin 区域） | margin 尺寸从 `frameMarginSize_ - contentSize_` 计算 | AC-1.3 |
| R-10 | 行为 | `ResetTaskQueue(isDebugBoundary)` 被调用 | 如果队首 target == isDebugBoundary：取消队尾直到仅剩 1 个，返回 `false`；否则取消队首，返回 `true` | `Cancel()` 失败时中断取消操作 | AC-1.5 |
| R-11 | 行为 | `WatchParameter` 回调 `EnableSystemParameterDebugBoundaryCallback` 被触发 | 解析 value 为 bool，调用 `SetDebugBoundaryEnabled`，然后调用 `container->RenderLayoutBoundary(isDebugBoundary)` | value 必须精确匹配 `"true"` 字符串 | AC-1.9 |
| R-12 | 行为 | 手势被 accept 且 `gestureDebugBoundaryEnabled_ == true` | `GestureDebugBoundaryManager::HandleGestureAccept` 更新节点状态，构建渲染信息，通过 `NotifyNodeRefresh` 触发边界绘制 | 线宽 `DEFAULT_STROKE_WIDTH_PX = 8.0px` | AC-2.1, AC-2.2 |
| R-13 | 异常 | `ResolveGestureColor` 资源查找失败 | 返回 `Color::RED` 作为回退颜色 | `config` 为空或 `colorResName` 为空时触发 | AC-2.3 |
| R-14 | 边界 | 应用运行期间修改 `persist.ace.debug.gesture.boundary.enabled` | 参数变更不生效，`gestureDebugBoundaryEnabled_` 不更新（无 `WatchParameter` 注册） | 需重启应用才能生效 | AC-2.4 |
| R-15 | 边界 | FrameNode 的 `marginFrameSize` 宽度或高度 < `32.0f * density`（像素） | `BuildRenderInfo` 返回空的 `GestureDebugBoundaryInfo`（`gestureMask = 0`），该节点不绘制手势边界 | 32vp 是 OHOS 触控目标最小尺寸标准 | AC-2.5 |
| R-16 | 边界 | 编译时 `GESTURE_DEBUG_BOUNDARY_SUPPORTED` 未定义 | `IsGestureDebugBoundaryEnabled()` 编译期返回 `false`（`#else` 分支） | 功能在编译级别不可用 | AC-2.6 |
| R-17 | 边界 | 手势边界参数为 `"true"` 且 `developerModeOn_ == false` | `gestureDebugBoundaryEnabled_` 初始化为 `IsGestureDebugBoundaryEnabled()`，不与 `developerModeOn_` 做 AND 运算 | 与布局边界的门控策略不同（ADR-1） | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.3 | 手动验证 | 设置参数后肉眼检查红色边界框、蓝色角标、品红 margin 填充的颜色和位置 |
| VM-2 | AC-1.4, AC-3.1, AC-3.2 | 手动验证 + 单元测试 | 关闭开发者模式后验证边界消失；单测验证 `SetDebugBoundaryEnabled` AND 逻辑 |
| VM-3 | AC-1.5 | 单元测试 | 模拟快速 toggle，验证 `ResetTaskQueue` 去重逻辑 |
| VM-4 | AC-1.6 | 手动验证 | 包含 LazyForEach/Repeat 的页面验证缓存项边界显示 |
| VM-5 | AC-1.7 | 手动验证 | 对比 NG/Legacy 管线下边界视觉效果 |
| VM-6 | AC-1.8 | 手动验证 | 截图后验证不包含调试边界 |
| VM-7 | AC-1.9 | 手动验证 | 运行时切换参数后验证即时生效 |
| VM-8 | AC-2.1 ~ AC-2.3 | 手动验证 | 手势边界颜色、叠加、回退 |
| VM-9 | AC-2.4 | 手动验证 | 运行时修改参数后验证不生效 |
| VM-10 | AC-2.5 | 单元测试 | 构造小于 32vp 的节点验证不绘制 |
| VM-11 | AC-2.6 | 编译验证 | 不定义 `GESTURE_DEBUG_BOUNDARY_SUPPORTED` 编译后验证功能不可用 |
| VM-12 | AC-3.3 | 手动验证 | 关闭开发者模式后手势边界仍可用 |

## API 变更分析

### 新增 API

N/A，无新增 Public/System/InnerApi。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

无新增接口规格。

## 兼容性声明

- **已有 API 行为变更:** 否。该功能不涉及任何 SDK API，仅通过系统参数 `persist.ace.debug.boundary.enabled` 和 `persist.ace.debug.gesture.boundary.enabled` 控制。
- **配置文件格式变更:** 否。系统参数为 key-value 字符串格式，无格式变更。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 10+（布局边界）；手势边界需 `GESTURE_DEBUG_BOUNDARY_SUPPORTED` 编译宏。
- **API 版本号策略:** N/A（无 SDK API）。

**兼容性风险：**

1. **门控策略不对称**（ADR-1）：布局边界受开发者模式门控，手势边界不受。开发者可能预期两者行为一致。
2. **运行时切换能力不对称**（ADR-2）：布局边界支持 `WatchParameter` 运行时切换，手势边界需重启。开发者可能预期两者切换行为一致。
3. **NG/Legacy 默认值差异**（ADR-5）：NG 管线 `needDebugBoundary_` 默认 `true`，Legacy 基类默认 `false`。跨管线迁移时可能出现边界显示行为差异。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|---------|
| RS 修饰器线程模型 | `DebugBoundaryModifier` 继承 `RSForegroundStyleModifier`，在 RenderService 线程执行 `Draw`，不可在 Draw 中访问 UI 线程对象 | AC-1.8 |
| 原子变量线程安全 | `debugBoundaryEnabled_` 为 `std::atomic<bool>`，支持跨线程读写 | AC-1.4, AC-3.1 |
| 任务队列互斥锁 | `renderLayoutBoundaryTaskMutex_` 保护 `renderLayoutBoundaryTaskQueue_`，系统参数线程入队与 UI 线程出队互斥 | AC-1.5 |
| RSCanvasNode 限制 | `DebugBoundaryModifier` 仅对 `RSCanvasNode` 类型创建，非该类型节点不显示边界 | AC-1.1 |
| 编译宏控制 | 手势边界功能受 `GESTURE_DEBUG_BOUNDARY_SUPPORTED` 编译宏控制 | AC-2.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 开启布局边界后帧率不低于 45 fps（500 节点树） | 性能测试 | 任务去重机制（`render_boundary_manager.cpp:26`）减少冗余重绘 |
| 内存 | DebugBoundaryModifier 仅在边界开启时创建，关闭时不持有 | 代码评审 | `rosen_render_context.cpp:1049-1061`（按需创建） |
| 安全 | 生产环境（非开发者模式）下布局边界不可用 | 手动验证 | `system_properties.cpp:770,1330`（AND 门控） |
| 可测试性 | 任务去重逻辑可独立单元测试 | 单元测试 | `render_boundary_manager.cpp:53-73` |
| 自动化维测 | 通过系统参数即可远程开启/关闭，无需代码修改 | 手动验证 | `hdc shell param set persist.ace.debug.boundary.enabled true` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|-----------|---------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | density 不同导致像素值不同，但 32vp 阈值语义不变 | 手动验证 | `gesture_debug_boundary_manager.cpp:121` |
| 折叠屏 | 无差异 | 折叠/展开时边界自动随重绘更新 | 手动验证 | `RequestFrame()` 触发重绘 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 否 | 调试边界不影响无障碍树 | — |
| 大字体 | 否 | 边界尺寸为固定像素值，不随字体缩放 | — |
| 深色模式 | 否 | 边界颜色为固定 ARGB 值，不随深色模式变化 | — |
| 多窗口/分屏 | 否 | 每个容器实例独立注册 `WatchParameter`，互不影响 | `ace_container.cpp:4653-4674` |
| 多用户 | 否 | 系统参数为全局参数，所有用户共享 | — |
| 版本升级 | 否 | 无持久化数据，无迁移需求 | — |
| 生态兼容 | 否 | 框架内部功能，不影响应用兼容性 | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 布局边界显示调试能力
  作为 应用开发者
  我想要 通过系统参数开启布局边界显示
  以便 可视化每个组件的 margin/border/padding 区域来调试布局问题

  Scenario: 开发者模式下开启布局边界
    Given 系统处于开发者模式
    And 布局边界当前未显示
    When 设置 persist.ace.debug.boundary.enabled 为 "true"
    Then 所有 FrameNode 显示红色矩形边界框（0xFFFA2A2D，线宽1.0px）
    And 每个 FrameNode 四角显示蓝色L型角标（0xFF007DFF，边长8.0px）
    And 每个 FrameNode 的 margin 区域显示品红色半透明填充（0x3FFF00AA）

  Scenario: 非开发者模式下布局边界不显示
    Given 系统未处于开发者模式
    When 设置 persist.ace.debug.boundary.enabled 为 "true"
    Then 布局边界不显示
    And debugBoundaryEnabled_ 原子变量存储 false

  Scenario: 运行时关闭布局边界
    Given 系统处于开发者模式
    And 布局边界当前已显示
    When 设置 persist.ace.debug.boundary.enabled 为 "false"
    Then WatchParameter 回调被触发
    And 所有节点的布局边界立即消失
    And 无需重启应用

  Scenario: 快速 toggle 参数时任务去重
    Given 布局边界当前已显示（队首任务 target=true）
    When 在 500ms 内连续设置参数为 false 然后 true
    Then ResetTaskQueue 取消中间的 false 任务
    And 最终全树重绘仅执行一次（target=true）
    And 显示状态与最后一次参数值一致

  Scenario Outline: 手势边界最小尺寸阈值
    Given 手势边界已开启
    And 节点 marginFrameSize 为 <width>vp x <height>vp
    When density = 3.0（阈值像素 = 96px）
    Then 手势边界显示状态为 <result>

    Examples:
      | width | height | result |
      | 40 | 40 | 显示 |
      | 32 | 40 | 显示 |
      | 31 | 40 | 不显示 |
      | 40 | 31 | 不显示 |
      | 32 | 32 | 显示 |

  Scenario: 手势边界运行时修改不生效
    Given 应用正在运行
    And 手势边界当前为关闭状态
    When 运行时设置 persist.ace.debug.gesture.boundary.enabled 为 "true"
    Then 手势边界不即时显示
    But 重启应用后手势边界显示

  Scenario: UI 截图排除调试边界
    Given 布局边界当前已显示
    When 对页面执行 UI 截图
    Then 截图结果中不包含红色/蓝色/品红色调试边界
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
  - repo: "openharmony/arkui_ace_engine"
    query: "DebugBoundaryPainter color constants and drawing implementation in NG pipeline"
  - repo: "openharmony/arkui_ace_engine"
    query: "RenderBoundaryManager task queue deduplication mechanism ResetTaskQueue"
  - repo: "openharmony/arkui_ace_engine"
    query: "SystemProperties debugBoundaryEnabled developer mode gating AND operation"
  - repo: "openharmony/arkui_ace_engine"
    query: "GestureDebugBoundaryManager MIN_SIZE_THRESHOLD_VP 32vp size filtering"
  - repo: "openharmony/arkui_ace_engine"
    query: "DebugBoundaryModifier RSForegroundStyleModifier SetNoNeedUICaptured thread model"
```

**关键文档：** `specs/03-engine-framework/08-dfx-foundation/06-layout-boundary-display/design.md`（DESIGN-Func-03-08-06）
