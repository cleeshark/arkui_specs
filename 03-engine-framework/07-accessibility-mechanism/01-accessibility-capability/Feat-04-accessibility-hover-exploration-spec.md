# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍悬停探测 |
| 特性编号 | Func-03-07-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 13 起 |
| SIG 归属 | SIG_ApplicationFramework |
| 状态 | Draft |
| 复杂度 | 复杂 |

> 框架内部能力补录：当前实现即契约。本 Feat 覆盖**辅助技术（读屏）的悬停探测（触控浏览）命中算法与状态机**；元素信息查询响应在 Feat-01。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无障碍悬停探测规格化 | 固化 HoverTest 命中链路、HoverTestRecursive 过滤、GetSearchStrategy level 四态、HoverStateManager 状态机、应用自绘组件悬停、坐标反变换、节流/源切换常量 |

## 输入文档

- 设计文档：`03-engine-framework/07-accessibility-mechanism/01-accessibility-capability/design.md`
- 源码定位：`frameworks/core/accessibility/accessibility_manager_ng.cpp`、`frameworks/core/components_ng/property/accessibility_property.cpp`、`adapter/ohos/osal/js_third_accessibility_hover_ng.cpp`、`frameworks/core/accessibility/accessibility_constants.h`

## 用户故事

### US-1: 触控浏览的命中探测

**作为** 读屏用户,
**我想要** 用手指拖动探测屏幕元素,
**以便** 在触摸时听到对应内容

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN Touch HOVER_ENTER/MOVE/EXIT/CANCEL 事件到达 THEN `HandleAccessibilityHoverEvent`(Touch 重载) 经 `HoverTestRecursive` 自顶向下命中 | 正常 |
| AC-1.2 | WHEN 命中节点 shouldSearchSelf 且命中矩形 `IsInnerRegion` 且通过消费检查 THEN 节点加入命中 path | 正常 |
| AC-1.3 | WHEN 节点 `!IsActive()`/`IsInternal()`/`!IsVisible()` THEN 不参与命中（return false） | 边界 |
| AC-1.4 | WHEN 节点 hasClip 且未命中自身 THEN 子树被裁掉（return false） | 边界 |
| AC-1.5 | WHEN 命中节点且 shouldSearchChildren THEN 以 `noOffsetPoint` 递归子节点（rbegin/rend 逆序） | 正常 |

### US-2: accessibilityLevel 与节点状态对搜索策略的影响

**作为** 框架,
**我想要**  level 与 disabled/HitTestMode 共同决定命中搜索策略,
**以便** 正确表达"读屏把一组读成一个"等语义

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN level=YES THEN shouldSearchSelf=true 定案（跳过 NodeState） | 正常 |
| AC-2.2 | WHEN level=NO_HIDE_DESCENDANTS THEN shouldSearchSelf=false、shouldSearchChildren=false | 正常 |
| AC-2.3 | WHEN level=NO THEN shouldSearchSelf=false，子树按 NodeState 继续 | 正常 |
| AC-2.4 | WHEN 节点 disabled THEN shouldSearchChildren=false（YES/NO_HIDE/有文本的 AUTO 不受影响） | 边界 |
| AC-2.5 | WHEN HitTestMode=BLOCK THEN shouldSearchChildren=false；=NONE THEN shouldSearchSelf=false | 边界 |
| AC-2.6 | WHEN 父为 group（ancestorGroupFlag）且本节点 level≠YES THEN shouldSearchSelf=false，组语义向子树传播 | 正常 |

### US-3: 悬停状态机与节流

**作为** 框架,
**我想要** 维护悬停状态机的 ENTER/MOVE/EXIT/CANCEL 流转并节流,
**以便** 避免重复播报与抖动

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN last 命中节点≠current THEN 对 last 发 HOVER_EXIT、对 current 发 HOVER_ENTER（受 IgnoreCurrentHoveringNode 门控） | 正常 |
| AC-3.2 | WHEN eventType=CANCEL THEN 跳过命中测试，对 nodeTransparent 发 transparent exit 并 Reset 状态 | 边界 |
| AC-3.3 | WHEN 非直接处理转换且事件间隔 < 10ms（THROTTLE_INTERVAL_HOVER_EVENT）THEN return IN_TIME_LIMIT 节流丢弃 | 边界 |
| AC-3.4 | WHEN sourceType 在 TOUCH/MOUSE 间切换且间隔 < 1000ms（MIN_SOURCE_CHANGE_GAP_MS）THEN return IN_TIME_LIMIT | 边界 |
| AC-3.5 | WHEN 多指 Touch（pointers>1 且当前 source==TOUCH）THEN Reset 并 return | 边界 |

### US-4: 应用自绘组件悬停与跨进程转发

**作为** 应用自绘组件/跨进程组件,
**我想要** 悬停事件转发到子树,
**以便** 自绘/跨进程内容参与触控浏览

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 命中节点经 SessionAdapter（Form/UIExtension/Isolated/XComponent/Web/Custom）THEN `NotifyHoverEventToNodeSession`→`TransferHoverEvent` 转发，标记 transformHover | 正常 |
| AC-4.2 | WHEN 宿主 HasVirtualNodeTreeRoot THEN `NotifyHoverEventToVirtualNode`→`virtualRoot->OnAccessibilityHover` 转发 | 正常 |
| AC-4.3 | WHEN 应用自绘组件 Provider 悬停 THEN `HandleAccessibilityHoverForThird`（BACKGROUND 线程）基于 AccessibilityElementInfo 的 RectInScreen 命中，last≠current 发 hover exit/enter | 正常 |

### US-5: 悬停命中几何与坐标反变换

**作为** 框架,
**我想要** 命中判定基于反变换坐标 + 未变换矩形,
**以便** 支持旋转/缩放/变换下的正确命中

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 命中判定 THEN 使用 `GetPaintRectWithoutTransform()` 矩形 + `GetPointWithRevert` 点反变换（含 rotate/scale/skew/translate/perspective 逆矩阵） | 正常 |
| AC-5.2 | WHEN 节点为 DISPLAY_NODE 且旋转 degree≠0 THEN 其旋转不参与悬停命中反变换（返回单位矩阵） | 边界 |
| AC-5.3 | WHEN Modal Dialog 节点（TAGS_MODAL_DIALOG_COMPONENT）THEN 即使非 focusable 也视为可消费；非真正模态（IsAccessibilityModal=false）的 wrapper 允许穿透 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-4 | 单测 | accessibility_manager_ng.cpp:403 |
| AC-1.2 | R-1, R-2 | TASK-4 | 单测 | accessibility_property.cpp:756 |
| AC-1.3 | R-2 | TASK-4 | 单测 | accessibility_property.cpp:732 |
| AC-1.4 | R-2 | TASK-4 | 单测 | accessibility_property.cpp:766 |
| AC-1.5 | R-1 | TASK-4 | 单测 | accessibility_property.cpp:771 |
| AC-2.1 | R-3 | TASK-4 | 单测 | accessibility_property.cpp:916 |
| AC-2.2 | R-3 | TASK-4 | 单测 | accessibility_property.cpp:918 |
| AC-2.3 | R-3 | TASK-4 | 单测 | accessibility_property.cpp:922 |
| AC-2.4 | R-4 | TASK-4 | 单测 | accessibility_property.cpp:937 |
| AC-2.5 | R-4 | TASK-4 | 单测 | accessibility_property.cpp:782 |
| AC-2.6 | R-5 | TASK-4 | 单测 | accessibility_property.cpp:966 |
| AC-3.1 | R-6 | TASK-4 | 单测 | accessibility_manager_ng.cpp:481 |
| AC-3.2 | R-6 | TASK-4 | 单测 | accessibility_manager_ng.cpp:417 |
| AC-3.3 | R-7 | TASK-4 | 单测 | accessibility_manager_ng.cpp:413 |
| AC-3.4 | R-7 | TASK-4 | 单测 | accessibility_manager_ng.cpp:434 |
| AC-3.5 | R-7 | TASK-4 | 单测 | accessibility_manager_ng.cpp:268 |
| AC-4.1 | R-8 | TASK-4 | 单测 | accessibility_manager_ng.cpp:546 |
| AC-4.2 | R-8 | TASK-4 | 单测 | accessibility_manager_ng.cpp:570 |
| AC-4.3 | R-9 | TASK-4 | 单测 | js_third_accessibility_hover_ng.cpp:217 |
| AC-5.1 | R-10 | TASK-4 | 单测 | accessibility_property.cpp:752 |
| AC-5.2 | R-10 | TASK-4 | 单测 | rosen_render_context.cpp:2958 |
| AC-5.3 | R-11 | TASK-4 | 单测 | accessibility_property.cpp:858 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 悬停事件（Mouse/Touch/坐标）到达且 `IsTouchExplorationEnabled` | `HandleAccessibilityHoverEventInner`→`HoverTest`→`HoverTestRecursive` 自顶向下命中，构建命中 path | Mouse/Touch action 分别映射 ENTER/MOVE/EXIT/CANCEL | AC-1.1, AC-1.5 |
| R-2 | 边界 | `!IsActive()`/`IsInternal()`(虚拟节点豁免)/`!IsVisible()`/hasClip 且未命中自身 | 节点或子树不参与命中 | 虚拟节点不检查 IsActive/IsInternal | AC-1.2, AC-1.3, AC-1.4 |
| R-3 | 行为 | level 四态（ResolveStrategyByLevel） | YES→搜自身定案；NO_HIDE_DESCENDANTS→不搜自身不搜子；NO→不搜自身；AUTO 有文本→搜自身 | YES/NO_HIDE/有文本 AUTO 跳过 NodeState | AC-2.1, AC-2.2, AC-2.3 |
| R-4 | 边界 | disabled / HitTestMode（UpdateStrategyByNodeState） | disabled→shouldSearchChildren=false；BLOCK→children=false；NONE→self=false；virtualNode 且非 hideDescendants→children=true | 仅在 ResolveStrategyByLevel 未定案时生效 | AC-2.4, AC-2.5 |
| R-5 | 行为 | 父为 group（ancestorGroupFlag） | 本节点 level≠YES 时 shouldSearchSelf=false，currentGroupFlag 传播 | 子树组件强制 shouldSearchSelf=true 优先 | AC-2.6 |
| R-6 | 行为 | 命中变化 / CANCEL | last≠current 对 last 发 EXIT、current 发 ENTER；CANCEL 跳过命中测试发 transparent exit 并 Reset | 受 IgnoreCurrentHoveringNode 门控 | AC-3.1, AC-3.2 |
| R-7 | 边界 | 节流（<10ms）/ 源切换（<1000ms）/ 多指 Touch | return IN_TIME_LIMIT 或 Reset | 直接处理转换（MOVE→EXIT、ENTER→EXIT）不受节流 | AC-3.3, AC-3.4, AC-3.5 |
| R-8 | 行为 | 命中节点为跨进程/虚拟节点宿主 | 优先 `NotifyHoverEventToVirtualNode`（virtualRoot），其次 `NotifyHoverEventToNodeSession`（SessionAdapter.TransferHoverEvent），标记 transformHover | MOUSE 时 virtualNode 不转发；disabled 不转发 session | AC-4.1, AC-4.2 |
| R-9 | 行为 | 应用自绘组件 Provider 悬停 | `HandleAccessibilityHoverForThird`（BACKGROUND）基于 ElementInfo RectInScreen 命中，last≠current 发 hover exit/enter | ENTER 先 Reset，EXIT 跳过命中；IsAccessibilityFocusable 影响 shouldSearchSelf | AC-4.3 |
| R-10 | 行为 | 命中几何 | `GetPaintRectWithoutTransform()` + `GetPointWithRevert`（含 rotate/scale/skew/translate/perspective 逆矩阵） | DISPLAY_NODE 且 degree≠0 返回单位矩阵（旋转豁免） | AC-5.1, AC-5.2 |
| R-11 | 边界 | Modal Dialog 节点（TAGS_MODAL_DIALOG_COMPONENT） | 即使非 focusable 也视为可消费；wrapper 非 IsAccessibilityModal 时允许穿透 | Header/Footer 自动获得 hover priority | AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.x（命中链路） | 单测：`accessibility_manager_ng_test_ng.cpp` | HoverTest 命中 path、过滤、clip |
| VM-2 | AC-2.x（搜索策略） | 单测：level/HitTestMode/group 策略 | 四态、disabled、BLOCK/NONE |
| VM-3 | AC-3.x（状态机） | 单测 | ENTER/MOVE/EXIT/CANCEL、节流、源切换 |
| VM-4 | AC-4.x（应用自绘组件/转发） | 单测：`js_third_accessibility_hover_ng_test.cpp` + SessionAdapter | virtualNode/session 转发、应用自绘组件命中 |
| VM-5 | AC-5.x（命中几何） | 单测 + HoverTestDebug | 反变换坐标、DisplayNode 豁免、modal |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| 无新增对外 API | — | — | — | — | 悬停命中为引擎内部机制，无 Public 入口 | — |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

## 接口规格

> L0/L1：悬停探测为引擎内部能力，无新增 Public 接口规格；命中行为同规则定义。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 13
- **API 版本号策略:** 保留既有标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 命中几何基于反变换 | `GetPaintRectWithoutTransform` + `GetPointWithRevert`，非变换后 paintRect | AC-5.x |
| 转发优先级 | virtualNode > session；转发标记 transformHover 导致返回 HOVER_FAIL | AC-4.x |
| 读屏规则改写 | 读屏规则开启时实际 enter 节点可能与几何命中节点不同（NeedChangeToReadableNode） | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 悬停命中在 UI 线程一帧内完成 | trace + HoverTestDebug | accessibility_manager_ng.cpp:602 |
| 可靠性 | 10ms 节流避免抖动重复播报 | 单测 | accessibility_manager_ng.cpp:413 |
| 自动化维测 | `hidumper --hover-test x y` 输出命中链与搜索明细 | hidumper | accessibility_manager_ng.cpp:602 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本特性即悬停探测 | 全部 |
| 多窗口/分屏 | 是 | 跨进程 session 转发、BySurfaceId embed 路径 | AC-4.x |
| 版本升级 | 是 | — | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（悬停命中；不含元素查询响应 Feat-01）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityManagerNG HandleAccessibilityHoverEvent 悬停命中与状态机"
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityProperty HoverTestRecursive / GetSearchStrategy level 四态"
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityHoverManagerForThirdNG 应用自绘组件悬停命中"
```

**关键文档：** design.md（同目录）、`frameworks/core/accessibility/accessibility_manager_ng.h`
