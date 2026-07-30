# 特性规格

> Func-04-06-02-Feat-02 FrameNode 树结构与挂载管理：固化 appendChild/insertChildAfter/removeChild/clearChildren/getChild(+ExpandMode)/getFirstChild/getNextSibling/getPreviousSibling/getParent/getChildrenCount(+ChildrenCountMode)/moveTo/adoptChild/removeAdoptedChild/addComponentContent 共 16 个公开 API 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameNode 树结构与挂载管理 |
| 特性编号 | Func-04-06-02-Feat-02 |
| 所属 Epic | 自定义节点能力 / FrameNode |
| 优先级 | P1 |
| 目标版本 | API 12（dynamic 起始）— API 26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂（L2） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | appendChild/insertChildAfter/removeChild/clearChildren/getChild/getFirstChild/getNextSibling/getPreviousSibling/getParent/getChildrenCount/moveTo/addComponentContent | API 12 起始 |
| ADDED | adoptChild/removeAdoptedChild | API 22（@FaAndStageModel） |
| ADDED | getChild(+ExpandMode)/getFirstChildIndexWithoutExpand/getLastChildIndexWithoutExpand | API 15 |
| ADDED | getChildrenCount(+ChildrenCountMode) | API 26.0.0 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/02-frame-node/design.md` | Baselined |
| 功能域注册 | `specs/registry/functions.yaml` (id: 04-06-02) | — |
| 特性注册 | `specs/registry/features.yaml` (func_id: 04-06-02, Feat-02) | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `FrameNode.static.d.ets` | — |

## 用户故事

### US-1: 增删子节点
**作为** 应用开发者，**我想要** 增删子节点，**以便** 动态构建节点树。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 `appendChild(node)` 且 node 有效、双方可改 THEN 将 node 追加至子列表末尾，更新 _childList | 正常 |
| AC-1.2 | WHEN node 为 null/undefined THEN 静默返回（不抛异常） | 边界 |
| AC-1.3 | WHEN node 已被 adopt（IsAdopted）THEN 抛 BusinessError(100025, "the node has already been adopted") | 异常 |
| AC-1.4 | WHEN node 已有其他父节点 THEN 抛 100021 | 异常 |
| AC-1.5 | WHEN 本节点不可改（ProxyFrameNode 且未开启 treeOperating）THEN 抛 100021 | 异常 |
| AC-1.6 | WHEN 重复 appendChild 同一已存在子节点 THEN 幂等（不重复插入） | 边界 |

### US-2: 按位置插入子节点
**作为** 应用开发者，**我想要** 在指定兄弟节点后插入子节点，
**以便** 调整节点树或事件流。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `insertChildAfter(child, sibling)` 且 sibling 有效 THEN 在 sibling 之后插入 child | 正常 |
| AC-2.2 | WHEN sibling 为 null/undefined THEN native 层插入至首位（index+1=0），但 bridge 返回 Undefined 导致 ArkTS 抛 100021 | 异常 |
| AC-2.3 | WHEN child 已 adopt THEN 抛 100025 | 异常 |

### US-3: 移除与清空子节点
**作为** 应用开发者，**我想要** 移除子节点或清空全部子节点，
**以便** 释放或撤销状态。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `removeChild(node)` 且 node 在子列表 THEN 移除并触发 OnRemoveFromParent；从 _childList 删除 | 正常 |
| AC-3.2 | WHEN node 不在子列表 THEN 静默返回（no-op） | 边界 |
| AC-3.3 | WHEN `clearChildren()` THEN 清空所有子节点（transition 子节点移至 disappearingChildren） | 正常 |

### US-4: 遍历子节点与兄弟节点
**作为** 应用开发者，**我想要** 获取首子/兄弟/父节点及子节点数量，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN `getChild(index, expandMode?)` 默认 expandMode=EXPAND(1) THEN 触发 build 后返回第 index 个 FrameNode；越界返回 null | 正常 |
| AC-4.2 | WHEN expandMode=NOT_EXPAND(0) THEN 不触发 build 返回 | 边界 |
| AC-4.3 | WHEN expandMode=LAZY_EXPAND(2) THEN 先不 build 查找，未命中再 EXPAND | 边界 |
| AC-4.4 | WHEN `getFirstChild()` 默认 isExpanded=true THEN 返回首子；无子返回 null | 正常 |
| AC-4.5 | WHEN `getNextSibling()`/`getPreviousSibling()` THEN 返回同级下一/上一兄弟；index 为首/末或未找到返回 null | 正常 |
| AC-4.6 | WHEN `getParent()` THEN 返回最近 FrameNode 祖先（跳过非 FrameNode）；Page/Stage 返回 null | 正常 |

### US-5: 获取子节点数量
**作为** 应用开发者，**我想要** 按不同模式统计子节点数，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN `getChildrenCount(ChildrenCountMode.ALL_EXPAND)` THEN 触发 build 后统计全部（含展开） | 正常 |
| AC-5.2 | WHEN `ONLY_EXPANDED` THEN 仅统计已展开数（CurrentFrameCount） | 边界 |
| AC-5.3 | WHEN `ALL_NOT_EXPAND` THEN 统计递归全部 TotalChildCount | 边界 |
| AC-5.4 | WHEN 传 boolean 兼容形式 true/false THEN 分别映射 ALL_EXPAND/ONLY_EXPANDED | 边界 |

### US-6: 跨父移动节点
**作为** 应用开发者，**我想要** 将节点移动到另一父节点下，
**以便** 调整节点树或事件流。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN `moveTo(targetParent, index?)` 且双方可改、源类型支持 THEN 从旧父移除并插入新父指定位置 | 正常 |
| AC-6.2 | WHEN index<0 或 >=childCount THEN 追加至末尾 | 边界 |
| AC-6.3 | WHEN 当前节点已 adopt THEN 抛 100027 ("The current node has already been adopted.") | 异常 |
| AC-6.4 | WHEN 源类型不在 allowlist（Stack/XComponent/EmbeddedComponent）THEN native 返回错误但 bridge 丢弃返回码→JS 侧静默 no-op | 边界 |

### US-7: 跨树 adopt 子节点
**作为** 应用开发者，**我想要** 将节点 adopt 至本节点（混合挂载），
**以便** 调整节点树或事件流。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-7.1 | WHEN `adoptChild(child)` 且双方满足条件 THEN 将 child 加入 adoptedChildren_（独立于 children_），SetIsAdopted(true) | 正常 |
| AC-7.2 | WHEN 本节点 disposed THEN 抛 100026 | 异常 |
| AC-7.3 | WHEN 本节点不可改 THEN 抛 100021 | 异常 |
| AC-7.4 | WHEN child 已有父节点 THEN native 返回 106207→抛 100025 | 异常 |
| AC-7.5 | WHEN 父/子类型不支持 adopt（非 CNode/ArkTsFrameNode/RootBuilderNode）THEN 返回 106208/106209→抛 100025 | 异常 |

### US-8: 移除 adopted 子节点
**作为** 应用开发者，**我想要** 移除已 adopt 的子节点，
**以便** 释放或撤销状态。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-8.1 | WHEN `removeAdoptedChild(child)` 且 child 确为本节点 adopted 子 THEN 从 adoptedChildren_ 移除，SetIsAdopted(false)，DetachRsNode | 正常 |
| AC-8.2 | WHEN child 非 adopted/非本节点 adopted THEN 返回 106210→抛 100025 | 异常 |

### US-9: 挂载 ComponentContent
**作为** 应用开发者，**我想要** 将 ComponentContent 挂载到本节点，
**以便** 调整节点树或事件流。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-9.1 | WHEN `addComponentContent(content)` THEN 复用 appendChild 路径挂载解包后的节点，并 setAttachedParent(WeakRef(this)) | 正常 |
| AC-9.2 | WHEN 本节点不可改 THEN 抛 100021 | 异常 |
| AC-9.3 | WHEN content 为 null THEN 静默返回 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.6 | R-1,R-8,R-9,R-10 | 单测 frame_node_test_ng | ui_node.cpp:229 AddChild; frame_node_modifier.cpp:140 |
| AC-2.1..2.3 | R-2,R-9,R-11 | 单测 | frame_node_modifier.cpp:155; bridge:887 |
| AC-3.1..3.3 | R-3,R-4 | 单测 | ui_node.cpp:373 RemoveChild; :495 Clean |
| AC-4.1..4.6 | R-5,R-6,R-12 | 单测 | frame_node_modifier.cpp:299,327,378,390,408,426 |
| AC-5.1..5.4 | R-7,R-13 | 单测 | frame_node_modifier.cpp:282 |
| AC-6.1..6.4 | R-14,R-15,R-16 | 单测 | frame_node_modifier.cpp:1156; bridge:1044 |
| AC-7.1..7.5 | R-17,R-18,R-19,R-20 | 单测 | node_render_node_modifier.cpp:2269; ui_node.cpp:742 |
| AC-8.1..8.2 | R-21,R-22 | 单测 | node_render_node_modifier.cpp:2428 |
| AC-9.1..9.3 | R-23,R-9 | 单测 | frame_node.ts:420; component_content.ts:91 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | appendChild 有效 child、双方可改 | 将 child 追加至子列表末尾 | 已存在同子节点幂等 | AC-1.1,1.6 |
| R-2 | 行为 | insertChildAfter(child, sibling) sibling 有效 | 在 sibling 之后插入 child | null sibling 路径异常 | AC-2.1 |
| R-3 | 行为 | removeChild(child) 在列表 | 从子列表移除 child（有过渡动画则延迟移除） | 不在列表 no-op | AC-3.1 |
| R-4 | 行为 | clearChildren() | 清空全部子节点（有过渡动画则延迟移除） | 不解绑 ComponentContent 挂载父引用 | AC-3.3 |
| R-5 | 行为 | getChild(index, expandMode=EXPAND) | 按 expandMode 返回第 index 个子节点（EXPAND 触发展开构建） | 越界返回 null；默认 EXPAND(1) | AC-4.1,4.2 |
| R-6 | 行为 | LAZY_EXPAND/NOT_EXPAND 模式 | LAZY 先不展开，未命中再 EXPAND；NOT_EXPAND 不展开 | LAZY_NOT_EXPAND 类似 | AC-4.2,4.3 |
| R-7 | 行为 | getChildrenCount(mode) | ALL_EXPAND→全部（含展开）；ONLY_EXPANDED→仅已展开；ALL_NOT_EXPAND→递归全部 | 默认 ALL_EXPAND | AC-5.1..5.3 |
| R-8 | 异常 | appendChild node 已 adopt | 抛 100025 "the node has already been adopted" | native 错误码映射 | AC-1.3 |
| R-9 | 异常 | node 已有其他父 / 本节点不可改 / ProxyFrameNode 未开 treeOperating | 抛 100021 | checkType 守卫 | AC-1.4,1.5,2.3,9.2 |
| R-10 | 边界 | appendChild null/undefined | 静默返回 | — | AC-1.2 |
| R-11 | 异常 | insertChildAfter sibling 为 null/undefined | 已知 quirk：底层已插首位但 ArkTS 抛 100021 | native 返 Undefined 致 ArkTS 守卫触发 | AC-2.2 |
| R-12 | 边界 | getFirstChild/NextSibling/PreviousSibling 无对应 | 返回 null | getParent 对 Page/Stage 返 null | AC-4.4,4.5,4.6 |
| R-13 | 边界 | getChildrenCount boolean 兼容 | true→ALL_EXPAND; false→ONLY_EXPANDED | — | AC-5.4 |
| R-14 | 行为 | moveTo(target, index) 双方可改、源类型支持 | 节点从旧父移除并插入新父指定位置 | index<0/>=count 追加末尾 | AC-6.1,6.2 |
| R-15 | 异常 | moveTo 当前节点已 adopt | 抛 100027 "The current node has already been adopted." | moveTo 独有 | AC-6.3 |
| R-16 | 边界 | moveTo 源类型不在 allowlist | 底层返错但 ArkTS 静默 no-op（返回码被丢弃） | 风险项 | AC-6.4 |
| R-17 | 行为 | adoptChild(child) 满足条件 | 将 child 跨树 adopt 至本节点（独立于常规子列表）；child 此后被标记为已 adopt | — | AC-7.1 |
| R-18 | 异常 | adoptChild 本节点 disposed/不可改 | 抛 100026/100021 | — | AC-7.2,7.3 |
| R-19 | 异常 | adoptChild child 已有父 | 抛 100025 | child 已有父 | AC-7.4 |
| R-20 | 异常 | adoptChild 类型不支持 | 抛 100025（child 不可 adopt 或父不可 adopt-to） | — | AC-7.5 |
| R-21 | 行为 | removeAdoptedChild(child) 命中 | 移除已 adopt 的 child；child 此后不再被标记为已 adopt | — | AC-8.1 |
| R-22 | 异常 | removeAdoptedChild child 非 adopted/非本节点 adopted | 抛 100025 | — | AC-8.2 |
| R-23 | 行为 | addComponentContent(content) | 将 content 解包后挂载为本节点子节点；content 记录其挂载父节点 | content null 静默返回 | AC-9.1,9.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1,R-8,R-9,R-10 增删 | 单测 | 幂等、100025/100021、null 静默 |
| VM-2 | R-2,R-11 插入 | 单测 | sibling null quirk |
| VM-3 | R-3,R-4 移除清空 | 单测 | disappearing、no-op |
| VM-4 | R-5,R-6,R-12 遍历 | 单测 | ExpandMode 默认/各模式、null |
| VM-5 | R-7,R-13 计数 | 单测 | 三模式、boolean 兼容 |
| VM-6 | R-14,R-15,R-16 moveTo | 单测 | 100027、源类型静默 no-op 风险 |
| VM-7 | R-17..R-22 adopt | 单测 | adoptedChildren_ 独立、106207-210→100025 |
| VM-8 | R-23 addComponentContent | 单测 | 解包、attachedParent |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| appendChild(node) | Public | node: FrameNode | void | 100021,100025 | 追加子节点 | AC-1 |
| insertChildAfter(child, sibling) | Public | child, sibling?: FrameNode\|null | void | 100021,100025 | sibling 后插入 | AC-2 |
| removeChild(node) | Public | node: FrameNode | void | — | 移除子节点 | AC-3 |
| clearChildren() | Public | — | void | — | 清空子节点 | AC-3 |
| getChild(index, expandMode?) | Public | index: number; expandMode?: ExpandMode | FrameNode\|null | — | 取子节点 | AC-4 |
| getFirstChildIndexWithoutExpand() | Public | — | number | — | 首子索引(不展开) | AC-4 |
| getLastChildIndexWithoutExpand() | Public | — | number | — | 末子索引 | AC-4 |
| getFirstChild(isExpanded?) | Public | — | FrameNode\|null | — | 首子 | AC-4 |
| getNextSibling(isExpanded?) | Public | — | FrameNode\|null | — | 下一兄弟 | AC-4 |
| getPreviousSibling(isExpanded?) | Public | — | FrameNode\|null | — | 上一兄弟 | AC-4 |
| getParent() | Public | — | FrameNode\|null | — | 父节点 | AC-4 |
| getChildrenCount(countMode?) | Public | countMode?: ChildrenCountMode\|boolean | number\|int | — | 子节点数 | AC-5 |
| moveTo(targetParent, index?) | Public | targetParent: FrameNode; index?: number\|int | void | 100021,100027 | 跨父移动 | AC-6 |
| adoptChild(child) | Public | child: FrameNode | void | 100021,100025,100026 | 跨树 adopt | AC-7 |
| removeAdoptedChild(child) | Public | child: FrameNode | void | 100021,100025,100026 | 移除 adopted | AC-8 |
| addComponentContent(content) | Public | content: ComponentContent | void | 100021 | 挂载 ComponentContent | AC-9 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**appendChild / insertChildAfter / removeChild / clearChildren**

| 属性 | 值 |
|------|-----|
| 函数签名 | `appendChild(node): void`; `insertChildAfter(child, sibling?): void`; `removeChild(node): void`; `clearChildren(): void` (dyn @since 12; static @since 23) |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | 100021(不可改/已有父), 100025(已adopt) |
| 关联 AC | AC-1,2,3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| node/child | FrameNode | 否 | — | null 静默返回(append/remove)；insertAfter null sibling→100021 quirk |
| sibling | FrameNode\|null | 否 | null | null 触发首位插入+100021 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 双方可改、child 有效 | AddChild 追加/插入/移除 | AC-1.1,2.1,3.1 |
| 2 | child 已 adopt | 抛 100025 | AC-1.3 |
| 3 | child 已有父/不可改 | 抛 100021 | AC-1.4,1.5 |
| 4 | null 参数 | append/remove 静默；insertAfter null sibling→100021 | AC-1.2,2.2,3.2 |

**getChild / getFirstChild / getNextSibling / getPreviousSibling / getParent / getChildrenCount**

| 属性 | 值 |
|------|-----|
| 函数签名 | 见 API 变更分析；expandMode/countMode 可选 (dyn @since 12/15/26; static @since 23/26) |
| 返回值 | FrameNode\|null / number |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-4,5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 默认 expandMode=EXPAND | 触发 build 后返回 | AC-4.1,4.4 |
| 2 | NOT_EXPAND/LAZY_EXPAND | 不 build / lazy 回退 | AC-4.2,4.3 |
| 3 | 无对应/越界 | 返回 null | AC-4.5,4.6 |
| 4 | getChildrenCount 三模式 | ALL_EXPAND/ONLY_EXPANDED/ALL_NOT_EXPAND 分别统计 | AC-5.1..5.3 |

**moveTo / adoptChild / removeAdoptedChild / addComponentContent**

| 属性 | 值 |
|------|-----|
| 函数签名 | moveTo(targetParent, index?): void(@since 18 dyn; 100027); adoptChild(child): void(@since 22); removeAdoptedChild(child): void(@since 22); addComponentContent(content): void(@since 12) |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | 100021,100025,100026,100027 |
| 关联 AC | AC-6,7,8,9 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | moveTo 双方可改 | 旧父移除+新父插入 | AC-6.1 |
| 2 | moveTo 已 adopt | 抛 100027 | AC-6.3 |
| 3 | moveTo 源类型不支持 | native 返错 bridge 丢弃→JS 静默 no-op | AC-6.4 |
| 4 | adoptChild 满足条件 | 加入 adoptedChildren_ | AC-7.1 |
| 5 | adopt 各失败条件 | 100026/100021/100025 | AC-7.2..7.5 |
| 6 | addComponentContent | 复用 appendChild 挂载 | AC-9.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 12（dynamic 树操作起）；adopt API 22；getChildrenCount(countMode) API 26.0.0；静态 @since 23。
- **API 版本号策略:** 逐 API 标注 @since；ExpandMode NOT_EXPAND/EXPAND/LAZY_EXPAND @since 15、LAZY_NOT_EXPAND @since 26.0.0；ChildrenCountMode @since 26.0.0；moveTo @since 18、100027 @since 22；adoptChild/removeAdoptedChild @since 22。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| insertChildAfter null sibling 触发 100021 但 native 已插首位 | 已知 quirk：bridge 返 Undefined 致 ArkTS 抛 100021，但 native GetChildIndex(nullptr)=-1 已 AddChild(index+1=0) | frame_node_modifier.cpp:155; bridge:887 |
| moveTo 源类型不支持时 JS 静默 no-op | native 限制源类型为 Stack/XComponent/EmbeddedComponent，返错但 bridge 丢弃返回码 | frame_node_modifier.cpp:1156; bridge:1044 |
| getFirstChildIndexWithoutExpand 失败返回不一致哨兵 | 无子节点时 modifier 不写 *index，bridge 返 4294967295(uint32 -1)；node null 返 -1 | bridge:976; modifier:327 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 可改性守卫 | 树操作前 checkType→isModifiable；ProxyFrameNode 须开 treeOperating | AC-1.5,9.2 |
| adopted 独立链表 | adoptedChildren_ 与 children_ 分离；已 adopt 节点拒绝常规树操作 | AC-1.3,7.1 |
| 源类型 allowlist | moveTo 仅 Stack/XComponent/EmbeddedComponent 支持 | AC-6.4 |
| ExpandMode 默认 EXPAND | getChild/getFirstChild 默认展开 build | AC-4.1,4.4 |
| transition 延迟移除 | removeChild 带 transition 时入 disappearingChildren | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | GetAllChildrenWithBuild 触发 build，大列表有开销 | 单测/性能 | frame_node_modifier.cpp:299 |
| 可靠性 | null 参数静默、移除不在列表 no-op | 单测 | ui_node.cpp:373,229 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口/分屏 | 否 | uiContext 已隔离 | — |
| 版本升级 | 是 | ExpandMode/ChildrenCountMode/adopt/moveTo 版本演进 | AC-4,5,6,7 |

## 行为场景

```gherkin
Feature: FrameNode 树结构与挂载管理
  Scenario: appendChild 已 adopt 子节点
    Given 子节点 N 已被另一节点 adopt
    When 调用 parentNode.appendChild(N)
    Then 抛出 BusinessError(100025)

  Scenario Outline: getChild expandMode 模式
    Given 节点 P 有未 build 的子树
    When 调用 P.getChild(0, <mode>)
    Then <期望>

    Examples:
      | mode | 期望 |
      | EXPAND | 触发 build 返回首子 |
      | NOT_EXPAND | 不 build 返回 |
      | LAZY_EXPAND | 先不 build，未命中再 EXPAND |

  Scenario: moveTo 已 adopt 节点
    Given 节点 N 已 adopt
    When 调用 N.moveTo(target)
    Then 抛出 BusinessError(100027)

  Scenario: adoptChild child 已有父
    Given child C 已有父节点
    When 调用 parent.adoptChild(C)
    Then 抛出 BusinessError(100025)
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（树结构与挂载；不含布局度量 Feat-03）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "UINode::AddChild/AddChildAfter/RemoveChild/Clean 树原语与 adoptedChildren_ 独立链表"
  - repo: "openharmony/arkui_ace_engine"
    query: "frame_node_modifier.cpp getChild ExpandMode 过滤与 GetAllChildrenWithBuild"
  - repo: "openharmony/arkui_ace_engine"
    query: "node_render_node_modifier.cpp AdoptChild/RemoveAdoptedChild 106206-210 错误码"
```
