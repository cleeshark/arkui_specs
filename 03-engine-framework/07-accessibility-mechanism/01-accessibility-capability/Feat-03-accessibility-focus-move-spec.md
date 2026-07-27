# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍焦点移动 |
| 特性编号 | Func-03-07-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 13 起 |
| SIG 归属 | SIG_ApplicationFramework |
| 状态 | Draft |
| 复杂度 | 复杂 |

> 框架内部能力补录：当前实现即契约。本 Feat 覆盖**无障碍焦点（读屏焦点）的方向性移动搜索算法**；元素信息查询响应在 Feat-01，悬停命中在 Feat-04。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无障碍焦点移动规格化 | 固化 FocusMoveSearchWithCondition 链路、AccessibilityFocusStrategy 先序/逆先序树搜索、FocusRulesCheckNode 判定、direction/condition 语义、可滚动祖先处理、NG/旧DOM/应用自绘组件三路差异 |

## 输入文档

- 设计文档：`03-engine-framework/07-accessibility-mechanism/01-accessibility-capability/design.md`
- 源码定位：`adapter/ohos/osal/accessibility/focus_move/accessibility_focus_strategy.cpp`、`accessibility_focus_move_osal*.cpp`、`accessibility_focus_frame_node_utils.cpp`、`adapter/ohos/osal/js_accessibility_manager.cpp`

## 用户故事

### US-1: 读屏焦点的方向性移动

作为读屏用户
我想要按 forward/backward/last 方向在可读节点间移动无障碍焦点
以便顺序朗读内容

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN SA 以 direction=FORWARD 发起 FocusMoveSearchWithCondition THEN `AccessibilityFocusStrategy::FindNextReadableNode` 以先序遍历搜索下一可读节点 | 正常 |
| AC-1.2 | WHEN direction=BACKWARD THEN `FindPrevReadableNode` 以逆先序（右→左→根）搜索 | 正常 |
| AC-1.3 | WHEN direction=FIND_LAST THEN `FindLastNodeWithoutCheck` 沿最右子孙下钻取最后节点 | 正常 |
| AC-1.4 | WHEN direction 为 UP/DOWN/LEFT/RIGHT 绝对方向 THEN 新 readable-rules 链路返回 NOT_SUPPORT（仅旧链路基于几何择优支持） | 边界 |
| AC-1.5 | WHEN 焦点移动到达根 ROOT_TYPE THEN 不回绕，返回 FIND_FAIL / FIND_FAIL_IN_ROOT_TYPE（回绕由 SA 二次发起） | 边界 |

### US-2: 滚动祖先与可读性判定

作为读屏用户
我想要焦点移动遇到可滚动边界时触发滚动祖先
以便到达当前视口外的内容

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN forward 搜索到可向前滚动祖先边界 THEN 返回 FIND_FAIL_IN_SCROLL 并把 targetNode=parent 返回，由 SA 决策滚动 | 正常 |
| AC-2.2 | WHEN direction=GET_FORWARD_SCROLL_ANCESTOR/GET_BACKWARD_SCROLL_ANCESTOR/GET_SCROLLABLE_ANCESTOR THEN `ProcessGetScrollAncestor` 返回对应可滚动祖先 | 正常 |
| AC-2.3 | WHEN 节点 `IsAccessibiltyVisible()` 为 false 或 level=NO_HIDE_DESCENDANTS THEN 其子树不参与焦点搜索（NoNeedSearchChild） | 边界 |
| AC-2.4 | WHEN 节点经 `CanAccessibilityFocus`（可见 + focusType 匹配 + SA CheckNodeIsReadable）失败 THEN 不作为可读候选 | 边界 |

### US-3: 子树容器、嵌入目标与虚拟节点

作为框架
我想要焦点移动正确处理子树容器、嵌入目标与虚拟节点
以便跨树/跨进程焦点移动

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 节点为子树容器（IsChildTreeContainer，childTreeId>0）且未 bypassDescendants THEN 返回 FIND_CHILDTREE，由 SA 下钻子树 | 正常 |
| AC-3.2 | WHEN 节点为嵌入目标（IsEmbededTarget）THEN 返回 FIND_EMBED_TARGET | 正常 |
| AC-3.3 | WHEN 宿主 HasVirtualNodeTreeRoot THEN 其子节点列表被替换为虚拟节点树根作为焦点候选 | 边界 |
| AC-3.4 | WHEN FIND_FAIL_IN_CHILDTREE 且非 FIND_LAST THEN 返回 SEARCH_FAIL_IN_CHILDTREE 并 ChangeToRoot 跨树回退 | 边界 |

### US-4: 用户自定义 nextFocus/prevFocus 关系

作为应用
我想要通过 nextFocusInspectorKey 自定义焦点移动顺序
以便控制读屏导航路径

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 设置 nextFocus 关系且 forward 搜索 THEN `TryJumpToNextFocusTarget` 沿用户关系跳转（要求 descendantMode 匹配） | 正常 |
| AC-4.2 | WHEN nextFocus/prevFocus 关系构成环 THEN 环检测命中即 skip 并记录 cycle | 异常 |
| AC-4.3 | WHEN 子节点列表 THEN 按 `GetAccessibilityZIndex` 升序排序决定焦点顺序 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:599 |
| AC-1.2 | R-1 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:797 |
| AC-1.3 | R-1 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:847 |
| AC-1.4 | R-2 | TASK-3 | 单测 | accessibility_focus_move_osal.cpp:137 |
| AC-1.5 | R-3 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:296 |
| AC-2.1 | R-4 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:589 |
| AC-2.2 | R-4 | TASK-3 | 单测 | accessibility_focus_move_osal.cpp:413 |
| AC-2.3 | R-5 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:113 |
| AC-2.4 | R-5 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:265 |
| AC-3.1 | R-6 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:464 |
| AC-3.2 | R-6 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:643 |
| AC-3.3 | R-7 | TASK-3 | 单测 | accessibility_focus_frame_node_utils.cpp:244 |
| AC-3.4 | R-6 | TASK-3 | 单测 | accessibility_focus_move_osal.cpp:70 |
| AC-4.1 | R-8 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:306 |
| AC-4.2 | R-8 | TASK-3 | 单测 | accessibility_focus_strategy.cpp:322 |
| AC-4.3 | R-9 | TASK-3 | 单测 | accessibility_focus_frame_node_utils.cpp:224 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | FORWARD/BACKWARD/FIND_LAST 方向请求 | 分别走 `FindNextReadableNode`（先序）/`FindPrevReadableNode`（逆先序）/`FindLastNodeWithoutCheck`（最右下钻） | 先序：自→子→右兄弟；逆先序：右→左→根 | AC-1.1, AC-1.2, AC-1.3 |
| R-2 | 边界 | direction 为 UP/DOWN/LEFT/RIGHT 绝对方向 | 新 readable-rules 链路返回 NOT_SUPPORT；仅旧 FocusMoveSearch 链路基于 `CheckBetterRect` 几何择优支持 | 旧链路仅 UIExtension 真正使用 | AC-1.4 |
| R-3 | 边界 | 搜索到达 ROOT_TYPE | 不回绕，返回 FIND_FAIL / FIND_FAIL_IN_ROOT_TYPE | 旧链路相对方向会回绕（新旧差异） | AC-1.5 |
| R-4 | 行为 | 焦点到可滚动祖先边界 / GET_*_SCROLL_ANCESTOR 方向 | 返回 FIND_FAIL_IN_SCROLL（target=parent）或对应可滚动祖先；FOCUS_BY_TITLE/LINK 命中 scroll 判 SEARCH_FAIL | header/footer 在 scroll 中按 CanScroll 跳过 | AC-2.1, AC-2.2 |
| R-5 | 边界 | 节点不可见 / level=NO_HIDE_DESCENDANTS / `CanAccessibilityFocus` 不通过 | 子树不搜索（NoNeedSearchChild）；节点不作可读候选 | CanAccessibilityFocus = 可见 ∧ focusType 匹配 ∧ SA CheckNodeIsReadable | AC-2.3, AC-2.4 |
| R-6 | 行为 | 子树容器（childTreeId>0）/ 嵌入目标 / 跨树回退 | IsChildTreeContainer→FIND_CHILDTREE；IsEmbededTarget→FIND_EMBED_TARGET；FIND_FAIL_IN_CHILDTREE→SEARCH_FAIL_IN_CHILDTREE+ChangeToRoot | 旧 DOM ChangeToRoot 返回 nullptr（不支持跨树回退） | AC-3.1, AC-3.2, AC-3.4 |
| R-7 | 边界 | 宿主 HasVirtualNodeTreeRoot | 子节点列表替换为虚拟节点树根；虚拟节点 ID 由 EncodeVirtualNodeAccessibilityId 编码 | 虚拟节点作为独立焦点候选 | AC-3.3 |
| R-8 | 行为 | 用户 nextFocus/prevFocus 关系 | `TryJumpToNextFocusTarget`/`TryFindByPrevFocus` 沿关系跳转，要求 descendantMode 匹配；带环检测（重复命中 skip） | 关系按 containerId 隔离存储于 NextFocusRelationController | AC-4.1, AC-4.2 |
| R-9 | 行为 | 子节点焦点顺序 | 按 `GetAccessibilityZIndex` 升序排序 | zIndex 小的先入焦点序 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.x（方向算法） | 单测：`accessibility_focus_strategy_*` | 先序/逆先序/FIND_LAST、不回绕 |
| VM-2 | AC-2.x（滚动祖先/可读性） | 单测 | FIND_FAIL_IN_SCROLL、CanAccessibilityFocus |
| VM-3 | AC-3.x（子树/嵌入/虚拟） | 单测 | FIND_CHILDTREE/EMBED_TARGET、虚拟节点替换 |
| VM-4 | AC-4.x（自定义关系） | 单测 | descendantMode 跳转、环检测、zIndex 排序 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `findNextFocusAccessibilityNode` (@since13) | Public(NDK) | elementId, direction, requestId, elementInfo* | int32_t | NOT_REGISTERED/COPY_FAILED | Provider 按方向查下一焦点 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

> direction 枚举（FocusMoveDirection）、FocusMoveResult/DetailCondition 等定义在仓外 OHOS 无障碍 SDK 头文件，本仓仅引用；C API 对外 `ArkUI_AccessibilityFocusMoveDirection` 仅含 UP/DOWN/LEFT/RIGHT/FORWARD/BACKWARD（`native_interface_accessibility.h:300-315`）。

## 接口规格

> L1 标准：焦点移动算法行为同规则定义，无新增 Public 接口规格需展开（NDK `findNextFocusAccessibilityNode` 回调签名见 API 变更分析）。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 13
- **API 版本号策略:** 保留既有标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| NG 为标准路径 | 旧 DOM `FocusStrategyOsalNode` 不支持 ChangeToRoot/虚拟节点/zIndex 排序（全用基类默认 false） | AC-3.x, AC-4.3 |
| 默认不回绕 | 新链路到根即停，回绕由 SA 二次发起 | AC-1.5 |
| 可聚焦白名单驱动 | 默认可聚焦组件由 TAGS_FOCUSABLE 等白名单决定，非自动推导 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 焦点搜索在 UI 线程一帧内完成 | trace `ArkUIAccessibilityFocusMoveSearchWithCondition` | accessibility_focus_move_osal.cpp:337 |
| 可测试性 | 三路（NG/旧DOM/应用自绘组件）可独立单测 | 单测 | accessibility_focus_move_osal_{ng,node,third}.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本特性即焦点移动 | 全部 |
| 多窗口/分屏 | 是 | 子树容器/嵌入目标支持跨树焦点 | AC-3.x |
| 版本升级 | 是 | NDK @since13 | AC-1.x |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（焦点移动；不含元素查询响应 Feat-01、悬停 Feat-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityFocusStrategy FindNextReadableNode/FindPrevReadableNode 先序逆先序搜索"
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusRulesCheckNode IsChildTreeContainer/IsEmbededTarget/IsAccessibiltyVisible 判定"
  - repo: "openharmony/arkui_ace_engine"
    query: "NextFocusRelationController nextFocus/prevFocus 用户关系与环检测"
```

**关键文档：** design.md（同目录）、`adapter/ohos/osal/accessibility/focus_move/accessibility_focus_strategy.h`
