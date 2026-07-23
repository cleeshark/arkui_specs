# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Inspector树形诊断系统 |
| 特性编号 | Func-03-08-04-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 ArkUI ace_engine 的 Inspector 树形诊断子系统：Inspector 类的完整树形序列化（GetInspector / GetInspectorByKey BFS / GetInspectorOfNode / GetSubWindowInspector）、InspectorFilter 属性过滤（FixedAttrBit 位掩码 / CheckExtAttr / IsFastFilter / 深度过滤）、UINode::DumpTree 文本与 JSON 双模式树形 dump、FrameNode 多层 dump（DumpCommonInfo / DumpAdvanceInfo / JSON dump）、Pattern 虚函数 dump 覆盖（DumpInfo / DumpAdvanceInfo / DumpViewDataPageNode 等 8 个虚函数、25+ 子类覆盖）、InspectorOffscreenNodesMgr 离屏节点管理、LayoutInspector IDE 集成（SupportInspector / GetInspectorTreeJsonStr / GetSnapshotJson / ProcessMessages / StateProfiler / RSProfiler / NodeTrace / 3D 布局）。不涉及具体日志输出格式（Feat-01）、性能 Trace 打点（03-trace 域）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Inspector 类完整树形序列化规格 | inspector.h:56-87 声明 Inspector 静态工具类，包含 GetInspector / GetInspectorByKey / GetInspectorNodeByKey / GetFrameNodeByKey / GetInspectorOfNode / GetSubWindowInspector / GetInspectorTree / GetFreeNodesInspector 等方法 |
| ADDED | GetInspector 主流程规格 | inspector.cpp:787-832 实现 GetInspector(isLayoutInspector, filter, needThrow)：创建 JSON root → GetContextInfo 写入 Width/Height/Resolution → 获取 StageManager 最后一页 → GetFrameNodeChildren 收集子节点 → GetInspectorInfo 递归构建 JSON 树 |
| ADDED | GetInspectorByKey BFS 搜索规格 | inspector.cpp:857-891 实现 GetInspectorByKey(root, key, notDetach)：使用广度优先搜索，两层 vector 轮换，匹配 GetInspectorId() 返回的目标 UINode |
| ADDED | GetContextInfo 上下文信息规格 | inspector.cpp:537-546 实现 GetContextInfo：Width = rootWidth * viewScale，Height = rootHeight * viewScale，Resolution = PipelineBase::GetCurrentDensity()，同时设置全局 deviceRect 用于 rect 约束 |
| ADDED | PutNodeInfoToJsonNode 节点信息写入规格 | inspector.cpp:329-341 实现 PutNodeInfoToJsonNode：INSPECTOR_RECT（相对窗口的 bounds，格式 "left,top,width,height"）、INSPECTOR_DEBUGLINE（源码行号），isActive 为 false 时 rect 为空 |
| ADDED | InspectorFilter 属性过滤规格 | inspector_filter.h:38-71 定义 FixedAttrBit 枚举（8 个位：ID/CONTENT/SRC/EDITABLE/SCROLLABLE/SELECTABLE/FOCUSABLE/FOCUSED）和 InspectorFilter 类（filterFixed 位掩码 / filterExt 向量 / filterId / filterDepth / isFreeNodesEnable） |
| ADDED | GetInspectorChildren 递归树构建规格 | inspector.cpp:391-479 实现 GetInspectorChildren：SpanNode 特殊处理 / CustomNode 在非 LayoutInspector 时跳过 / 内部节点过滤 / NavDestination 自定义节点处理 / 深度递减控制 / JSON 非法字符串过滤 |
| ADDED | UINode::DumpTree 双模式树形 dump 规格 | ui_node.cpp:1385-1435 实现 DumpTree(depth, hasJson, desc)：JSON 模式输出 childSize/ID/Depth/InstanceId/AccessibilityId/IsDisappearing；文本模式输出 DumpBasicInfo + DumpInfo；不可见/非活跃节点跳过（除非 IsDumpAllNodes）；LazyForEach/Repeat 经 GetChildrenForInspector 处理；递归 children/disappearingChildren/overlay/cornerMark |
| ADDED | FrameNode 多层 dump 规格 | frame_node.cpp:1579-1610 DumpInfo()（LastParent + CommonInfo + OnSizeChange + KeyboardShortcut + Pattern + RenderContext）、frame_node.cpp:8320-8330 DumpInfo(json)、frame_node.cpp:1186-1238 DumpCommonInfo()（FrameRect/PaintRect/BackgroundColor/ParentLayoutConstraint/Active/Freeze/Visible）、frame_node.cpp:8289-8318 DumpCommonInfo(json) |
| ADDED | Pattern 虚函数 dump 覆盖规格 | pattern.h:335-345 声明 8 个 dump 虚函数（DumpInfo/DumpInfo(json)/DumpSimplifyInfo/DumpAdvanceInfo/DumpAdvanceInfo(json)/DumpViewDataPageNode/DumpSimplifyInfo(shared_ptr)/DumpSimplifyInfoOnlyForParamConfig），25+ Pattern 子类覆盖 |
| ADDED | InspectorOffscreenNodesMgr 离屏节点管理规格 | inspector.h:44-54 定义 InspectorOffscreenNodesMgr：std::set<RefPtr<FrameNode>> 存储，AddOffscreenNode/RemoveOffscreenNode/GetOffscreenNodesSize/GetOffscreenNodes/ClearOffscreenNodes |
| ADDED | LayoutInspector IDE 集成规格 | layout_inspector.h:39-104 定义 LayoutInspector：SupportInspector / GetInspectorTreeJsonStr / CreateLayoutInfo / GetSnapshotJson / ProcessMessages / RegisterConnectCallback / StateProfiler / RSProfiler / NodeTrace / 3D 布局 |

## 输入文档

- 关联设计：`specs/03-engine-framework/08-dfx-foundation/04-dump-mechanism/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/core/components_ng/base/inspector.h`（90 行）—— Inspector 类与 InspectorOffscreenNodesMgr 声明
  - `frameworks/core/components_ng/base/inspector.cpp`（1239 行）—— Inspector 完整实现
  - `interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h`（79 行）—— InspectorFilter 与 FixedAttrBit 定义
  - `frameworks/core/components_ng/base/ui_node.h`（1440 行）—— UINode dump 虚函数声明（DumpInfo/DumpAdvanceInfo 等）
  - `frameworks/core/components_ng/base/ui_node.cpp`（3337 行）—— DumpTree 实现
  - `frameworks/core/components_ng/base/frame_node.h`（2162 行）—— FrameNode dump 方法声明
  - `frameworks/core/components_ng/base/frame_node.cpp`（9182 行）—— FrameNode dump 实现
  - `frameworks/core/components_ng/pattern/pattern.h`（748 行）—— Pattern dump 虚函数声明
  - `frameworks/core/common/layout_inspector.h`（106 行）—— LayoutInspector IDE 集成

## 用户故事

### US-1: GetInspector 完整树形序列化

- As a IDE 可视化调试工具开发者
- I want 调用 Inspector::GetInspector 获取当前页面的完整组件树 JSON
- So that IDE 能渲染组件树结构并显示每个节点的位置和属性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN Inspector::GetInspector(isLayoutInspector) 被调用 THEN 创建 JSON root 并设置 "$type"="root"，通过 PipelineContext::GetCurrentContext() 获取上下文，context 为空时设 needThrow=true 并返回仅含 root 的 JSON。来源：`inspector.cpp:789-796` | 正常 |
| AC-1.2 | WHEN GetContextInfo(context, jsonRoot) 执行 THEN 写入 width=rootWidth*scale、height=rootHeight*scale、$resolution=PipelineBase::GetCurrentDensity()，同时设置全局 deviceRect=(0,0,rootWidth*scale,rootHeight*scale)。来源：`inspector.cpp:537-546` | 正常 |
| AC-1.3 | WHEN filter.GetFilterID() 返回空 THEN 通过 StageManager::GetLastPage() 获取最后一页作为根节点，pageId 从该页获取；filter.GetFilterID() 非空时经 GetInspectorByKey(rootNode, key) 定位子树根。来源：`inspector.cpp:800-814` | 正常 |
| AC-1.4 | WHEN key 为空且收集子节点 THEN 遍历 pageRootNode 子节点调用 GetFrameNodeChildren 过滤，当 filter.IsFreeNodesEnabled() 时调用 GetAllPageNodes 追加其他页面节点，获取 GetOverlayNode 追加 overlay 节点。来源：`inspector.cpp:816-830` | 正常 |
| AC-1.5 | WHEN isLayoutInspector 为 true THEN GetInspectorInfo 返回外层包装 {"type":"root","content":jsonRoot,"VsyncID":frameCount,"ProcessID":pid,"WindowID":windowId}，若 filter.IsFreeNodesEnabled() 追加 "other_contents" 字段。来源：`inspector.cpp:616-630` | 正常 |
| AC-1.6 | WHEN pageRootNode 为空或 context 为空 THEN needThrow 设为 true，返回仅含 $type="root" 的最小 JSON。来源：`inspector.cpp:793-795,811-814` | 边界 |

### US-2: GetInspectorByKey BFS 查找与单节点诊断

- As a 自动化测试工程师
- I want 通过组件 key 快速定位到目标 FrameNode 节点并获取其 Inspector 信息
- So that 能对特定组件进行精准的诊断和事件注入

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN GetInspectorByKey(root, key, notDetach) 被调用 THEN 先检查 root 自身的 InspectorId 是否匹配 key，匹配则直接返回 root。来源：`inspector.cpp:858-863` | 正常 |
| AC-2.2 | WHEN BFS 遍历执行 THEN 使用 elements 和 elementsNext 两个 vector 轮换，每层遍历检查 InspectorId 匹配，未匹配则展开子节点到 elementsNext（reserve 为 elements.size()*2），交换后继续。来源：`inspector.cpp:865-889` | 正常 |
| AC-2.3 | WHEN 所有层遍历完毕未匹配 THEN 返回 nullptr。来源：`inspector.cpp:890` | 边界 |
| AC-2.4 | WHEN GetFrameNodeByKey(key, notDetach, skipoffscreenNodes) 被调用 THEN 先检查 offscreenNodesMgr（skipoffscreenNodes=false 时），遍历离屏节点调用 GetInspectorByKey 查找，未命中再从 rootElement 搜索。来源：`inspector.cpp:636-660` | 正常 |
| AC-2.5 | WHEN GetInspectorNodeByKey(key, filter) 被调用 THEN 返回包含 $type、$ID、$rect（相对窗口 transform rect）、$debugLine、$attrs（ToJsonValue 序列化）的单节点 JSON 字符串。来源：`inspector.cpp:663-688` | 正常 |

### US-3: InspectorFilter 属性过滤

- As a 性能优化工程师
- I want InspectorFilter 通过位掩码和扩展属性列表精确控制哪些属性被序列化
- So that 大型组件树 dump 时可以只输出必要属性，减少序列化开销

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN FixedAttrBit 枚举被使用 THEN 定义 8 个位：FIXED_ATTR_ID=0、FIXED_ATTR_CONTENT=1、FIXED_ATTR_SRC=2、FIXED_ATTR_EDITABLE=3、FIXED_ATTR_SCROLLABLE=4、FIXED_ATTR_SELECTABLE=5、FIXED_ATTR_FOCUSABLE=6、FIXED_ATTR_FOCUSED=7。来源：`inspector_filter.h:38-47` | 正常 |
| AC-3.2 | WHEN InspectorFilter 默认构造 THEN filterFixed=0、filterDepth=0、isFreeNodesEnable=false，无任何过滤属性设置。来源：`inspector_filter.h:51,67-70` | 正常 |
| AC-3.3 | WHEN SetFilterDepth(depth) 被调用 THEN GetInspectorInfo 中使用 depth 作为递归深度限制，depth-1 传递给 GetInspectorChildren。来源：`inspector_filter.h:59`, `inspector.cpp:605,610` | 正常 |
| AC-3.4 | WHEN EnableFreeNodes() 被调用 THEN IsFreeNodesEnabled() 返回 true，GetInspector 主流程在收集子节点时调用 GetAllPageNodes 追加非当前页节点，GetInspectorInfo 中追加 "other_contents" 字段。来源：`inspector_filter.h:61`, `inspector.cpp:625-627,821-823` | 正常 |
| AC-3.5 | WHEN IsFastFilter() 返回 true THEN FrameNode::MouseToJsonValue 等扩展属性序列化路径直接 return，跳过非固定属性序列化。来源：`inspector_filter.h:55`, `frame_node.cpp:1631-1633` | 正常 |

### US-4: UINode::DumpTree 双模式树形 dump

- As a DFX 诊断工程师
- I want DumpTree 支持文本模式和 JSON 模式两种输出格式
- So that 既能通过命令行工具查看树形文本结构，又能通过 IDE 解析 JSON 结构化数据

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN DumpTree(depth, hasJson=true) 执行 THEN 创建 JSON 对象写入 childSize=GetChildren().size()、ID=nodeId_、Depth=depth_、InstanceId=instanceId_、AccessibilityId=accessibilityId_，若 IsDisappearing() 则写入 IsDisappearing=true，随后调用 DumpInfo(json)。来源：`ui_node.cpp:1387-1403` | 正常 |
| AC-4.2 | WHEN DumpTree(depth, hasJson=false) 执行 THEN 调用 DumpBasicInfo(depth, hasJson, desc) 和 DumpInfo()，使用 DumpLog::Append(depth, name, childSize) 输出树形文本，name 为 ToString()（DumpAllNodes）或 GetTag()。来源：`ui_node.cpp:1404-1410` | 正常 |
| AC-4.3 | WHEN 节点不满足 IsVisibleAndActive() 且 IsDumpAllNodes() 为 false THEN 直接 return 不递归子节点。来源：`ui_node.cpp:1412-1414` | 边界 |
| AC-4.4 | WHEN 节点 tag 为 LazyForEach 或 Repeat THEN 子节点经 GetChildrenForInspector(true) 获取，递归 DumpTree 时 desc="ChildrenForInspector"。来源：`ui_node.cpp:1418-1423` | 正常 |
| AC-4.5 | WHEN DumpTree 递归处理子节点 THEN 遍历 GetChildren()，若子节点 parent 不是当前节点则 desc="BrokenChildren"，否则 desc="Children"；同时递归 disappearingChildren_（desc="DisappearingChildren"）、FrameNode overlay（desc="OverlayNode"）、CornerMarkNode（DumpCornerMarkNode）。来源：`ui_node.cpp:1424-1434` | 正常 |

### US-5: FrameNode 多层 dump 信息

- As a 组件调试开发者
- I want FrameNode 的 dump 输出包含布局信息、Pattern 特有信息和 RenderContext 信息
- So that 能完整诊断组件的布局状态、业务状态和渲染属性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN FrameNode::DumpInfo()（文本模式）执行 THEN 输出 LastParentTag/LastParentId（若 LastParent 有效）、DumpCommonInfo()（FrameRect/PaintRect/BackgroundColor/ParentLayoutConstraint/Active/Freeze/Visible 等）、DumpOnSizeChangeInfo()、DumpKeyboardShortcutInfo()、pattern_->DumpInfo()、renderContext_->DumpInfo()。来源：`frame_node.cpp:1579-1595` | 正常 |
| AC-5.2 | WHEN FrameNode::DumpInfo(json)（JSON 模式）执行 THEN 调用 DumpCommonInfo(json)、DumpOnSizeChangeInfo(json)、pattern_->DumpInfo(json)、renderContext_->DumpInfo(json)。来源：`frame_node.cpp:8320-8330` | 正常 |
| AC-5.3 | WHEN FrameNode::DumpCommonInfo()（文本模式）执行 THEN 输出 FrameRect（geometryNode_->GetFrameRect()）、PaintRect without transform、BackgroundColor（非 #00000000 时）、ParentLayoutConstraint（可选）、IsActive（非 1 时）、Freeze/UserFreeze（IsFreeze 时）、Visible（非 0 时）、Padding/SafeArea/Border 等。来源：`frame_node.cpp:1186-1238` | 正常 |
| AC-5.4 | WHEN FrameNode::DumpCommonInfo(json) 执行 THEN 写入 FrameRect、PaintRect without transform、BackgroundColor、BuildLayoutInfo(json)、DumpSafeAreaInfo(json)、DumpVisibleAreaInfo(json)、compid（propInspectorId 非空时）、ContentConstraint、DumpAlignRulesInfo(json)、DumpDragInfo(json)、DumpOverlayInfo(json)。来源：`frame_node.cpp:8289-8318` | 正常 |
| AC-5.5 | WHEN FrameNode::DumpAdvanceInfo()（文本模式）执行 THEN 在 DumpInfo 基础上追加 pattern_->DumpAdvanceInfo() 和 renderContext_->DumpAdvanceInfo()，输出 Pattern 高级信息和 RenderContext 高级信息。来源：`frame_node.cpp:1597-1610` | 正常 |
| AC-5.6 | WHEN IsDumpAllNodes() 为 true THEN DumpCommonInfo() 额外输出 IsFrameDisappear、IsActive、AccessibilityVisible、HasAccessibilityVirtualNode。来源：`frame_node.cpp:1188-1193` | 边界 |

### US-6: Pattern 虚函数 dump 覆盖

- As a 组件开发者
- I want Pattern 子类通过覆盖 dump 虚函数输出组件特有诊断信息
- So that 不同组件类型的诊断信息能自动集成到 Inspector 树和 DumpTree 中

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN Pattern 基类声明 dump 虚函数 THEN 定义 8 个虚函数：DumpInfo()、DumpInfo(json)、DumpSimplifyInfo(json)、DumpAdvanceInfo()、DumpAdvanceInfo(json)、DumpViewDataPageNode(viewDataWrap, needsRecordData)、DumpSimplifyInfo(shared_ptr json)、DumpSimplifyInfoOnlyForParamConfig(shared_ptr json, config)，全部默认空实现。来源：`pattern.h:335-344` | 正常 |
| AC-6.2 | WHEN FrameNode::DumpInfo(json) 执行且 pattern_ 非空 THEN 调用 pattern_->DumpInfo(json)，由具体 Pattern 子类覆盖实现写入组件特有 JSON 属性。来源：`frame_node.cpp:8324-8326`, `pattern.h:336` | 正常 |
| AC-6.3 | WHEN FrameNode::DumpAdvanceInfo(json) 执行且 pattern_ 非空 THEN 在 DumpInfo(json) 基础上额外调用 pattern_->DumpAdvanceInfo(json)，输出组件高级诊断信息。来源：`frame_node.cpp:8336-8338`, `pattern.h:339` | 正常 |
| AC-6.4 | WHEN FrameNode::DumpViewDataPageNode(viewDataWrap, needsRecordData) 被调用 THEN 委托给 pattern_->DumpViewDataPageNode(viewDataWrap, needsRecordData)，由组件 Pattern 实现 ViewData 序列化。来源：`frame_node.cpp:1612-1617`, `pattern.h:340` | 正常 |

### US-7: InspectorOffscreenNodesMgr 与 LayoutInspector IDE 集成

- As a IDE DevTools 集成工程师
- I want LayoutInspector 通过 Inspector 收集组件树快照并通过 connect server 通信
- So that IDE 能实时展示组件树布局信息、截图、3D 布局和状态 profiling

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN InspectorOffscreenNodesMgr::AddOffscreenNode(node) 被调用 THEN 将 node 插入 std::set<RefPtr<FrameNode>> offscreenNodes_（按 RefPtr 排序去重）；RemoveOffscreenNode 执行 erase 删除。来源：`inspector.cpp:1213-1223` | 正常 |
| AC-7.2 | WHEN Inspector::GetOffScreenTreeNodes(nodes) 被调用 THEN 从 offscreenNodesMgr 获取离屏节点集合，对每个节点调用 AddInspectorTreeNode 构建 RecNode 树。来源：`inspector.cpp:1154-1170` | 正常 |
| AC-7.3 | WHEN LayoutInspector::GetInspectorTreeJsonStr(treeJsonStr, containerId, isNeedFreeNodes) 被调用 THEN 按 containerId 定位容器，isNeedFreeNodes 为 true 时调用 GetFreeNodesInspector（filter.EnableFreeNodes()），生成组件树 JSON 字符串。来源：`layout_inspector.h:43`, `inspector.cpp:773-778` | 正常 |
| AC-7.4 | WHEN Inspector::ParseWindowIdFromMsg(message) 被调用 THEN 解析 JSON 的 "method" 字段，校验是否在 SUPPORT_METHOD（"ArkUI.tree"/"ArkUI.tree.3D"/"ArkUI.queryAbilities"）中，提取 "params.windowId"，返回 {windowId, methodIndex}。来源：`inspector.cpp:54,1172-1196` | 正常 |
| AC-7.5 | WHEN LayoutInspector::ProcessMessages(message) 被调用 THEN 返回 {windowId, pageId} 对，用于定位目标窗口和页面。来源：`layout_inspector.h:51` | 正常 |
| AC-7.6 | WHEN LayoutInspector::GetSnapshotJson(containerId, message) 被调用 THEN 生成包含 PixelMap 截图的 JSON 快照信息，用于 IDE 可视化展示。来源：`layout_inspector.h:49` | 正常 |
| AC-7.7 | WHEN LayoutInspector 提供 StateProfiler / RSProfiler / NodeTrace 能力 THEN 通过 GetStateProfilerStatus/SetStateProfilerStatus（:58-60）、GetRsProfilerNodeMountCallback/HandleStartRecord/HandleStopRecord（:67-72）、GetEnableNodeTrace/SetEnableNodeTrace（:76-77）分别管理三种 profiling 状态。来源：`layout_inspector.h:57-81` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|---------|------|
| AC-1.1 | R-1 | TASK-02 | 代码评审 | 代码审查 |
| AC-1.2 | R-2 | TASK-02 | 代码评审 | 代码审查 |
| AC-1.3 | R-3 | TASK-02 | 单元测试 | 代码审查 |
| AC-1.4 | R-4 | TASK-02 | 代码评审 | 代码审查 |
| AC-1.5 | R-5 | TASK-02 | 代码评审 | 代码审查 |
| AC-1.6 | R-6 | TASK-02 | 单元测试 | 代码审查 |
| AC-2.1 | R-7 | TASK-02 | 单元测试 | 代码审查 |
| AC-2.2 | R-7 | TASK-02 | 单元测试 | 代码审查 |
| AC-2.3 | R-8 | TASK-02 | 单元测试 | 代码审查 |
| AC-2.4 | R-9 | TASK-02 | 代码评审 | 代码审查 |
| AC-2.5 | R-10 | TASK-02 | 单元测试 | 代码审查 |
| AC-3.1 | R-11 | TASK-02 | 代码评审 | 代码审查 |
| AC-3.2 | R-12 | TASK-02 | 代码评审 | 代码审查 |
| AC-3.3 | R-13 | TASK-02 | 代码评审 | 代码审查 |
| AC-3.4 | R-14 | TASK-02 | 代码评审 | 代码审查 |
| AC-3.5 | R-15 | TASK-02 | 代码评审 | 代码审查 |
| AC-4.1 | R-16 | TASK-02 | 单元测试 | 代码审查 |
| AC-4.2 | R-17 | TASK-02 | 单元测试 | 代码审查 |
| AC-4.3 | R-18 | TASK-02 | 单元测试 | 代码审查 |
| AC-4.4 | R-19 | TASK-02 | 代码评审 | 代码审查 |
| AC-4.5 | R-20 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.1 | R-21 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.2 | R-22 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.3 | R-23 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.4 | R-24 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.5 | R-25 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.6 | R-26 | TASK-02 | 代码评审 | 代码审查 |
| AC-6.1 | R-27 | TASK-02 | 代码评审 | 代码审查 |
| AC-6.2 | R-28 | TASK-02 | 代码评审 | 代码审查 |
| AC-6.3 | R-29 | TASK-02 | 代码评审 | 代码审查 |
| AC-6.4 | R-30 | TASK-02 | 代码评审 | 代码审查 |
| AC-7.1 | R-31 | TASK-02 | 单元测试 | 代码审查 |
| AC-7.2 | R-32 | TASK-02 | 代码评审 | 代码审查 |
| AC-7.3 | R-33 | TASK-02 | 代码评审 | 代码审查 |
| AC-7.4 | R-34 | TASK-02 | 单元测试 | 代码审查 |
| AC-7.5 | R-35 | TASK-02 | 代码评审 | 代码审查 |
| AC-7.6 | R-36 | TASK-02 | 代码评审 | 代码审查 |
| AC-7.7 | R-37 | TASK-02 | 代码评审 | 代码审查 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetInspector 主入口 | 创建 "$type"="root" 的 JSON root，获取 PipelineContext，context 为空时 needThrow=true。 | needThrow 通过引用返回给调用方。 | AC-1.1 |
| R-2 | 行为 | GetContextInfo | Width/Height = rootWidth/rootHeight * viewScale，$resolution = GetCurrentDensity()，设置全局 deviceRect。 | deviceRect 为匿名命名空间全局变量，用于 PutNodeInfoToJsonNode 中的 rect 约束。 | AC-1.2 |
| R-3 | 行为 | GetInspector 页面定位 | filter.GetFilterID() 为空时用 StageManager::GetLastPage()，非空时经 GetInspectorByKey 定位。 | GetLastPage 返回空时 needThrow=true。 | AC-1.3 |
| R-4 | 行为 | GetInspector 子节点收集 | 遍历页面子节点经 GetFrameNodeChildren 过滤，FreeNodes 模式追加其他页面节点，追加 overlay 节点。 | key 非空时直接将 pageRootNode 作为唯一 child。 | AC-1.4 |
| R-5 | 行为 | LayoutInspector JSON 包装 | isLayoutInspector=true 时外层包装含 type/content/VsyncID/ProcessID/WindowID，FreeNodes 追加 other_contents。 | VsyncID 为 PipelineContext::GetFrameCount()。 | AC-1.5 |
| R-6 | 边界 | GetInspector 空上下文/空页面 | context 或 pageRootNode 为空时 needThrow=true，返回最小 root JSON。 | 调用方通过 needThrow 判断是否抛出异常。 | AC-1.6 |
| R-7 | 行为 | GetInspectorByKey BFS 搜索 | 先检查根节点 InspectorId，再双层 vector BFS 逐层展开，elementsNext reserve 为 elements.size()*2。 | InspectorId 为 optional，空时按 keyIsNull 匹配。 | AC-2.1 / AC-2.2 |
| R-8 | 边界 | BFS 未找到目标 | 所有层遍历完毕后返回 nullptr。 | 调用方需 CHECK_NULL 判空。 | AC-2.3 |
| R-9 | 行为 | GetFrameNodeByKey 离屏优先 | skipoffscreenNodes=false 时先搜索 offscreenNodes，再搜索 rootElement。 | offscreenNodes 过多时 skipoffscreenNodes=true 可跳过。 | AC-2.4 |
| R-10 | 行为 | GetInspectorNodeByKey 单节点序列化 | 输出 $type/$ID/$rect（transform rect relative to window）/ $debugLine / $attrs（ToJsonValue）。 | 节点为 FrameNode 时才有 $rect。 | AC-2.5 |
| R-11 | 行为 | FixedAttrBit 位掩码 | 8 个枚举值对应 8 个位（0-7），CheckFixedAttr 通过 (filterFixed >> bit) & 1 检查。 | FixedAttrBit 底层类型 uint64_t。 | AC-3.1 |
| R-12 | 行为 | InspectorFilter 默认状态 | 默认无过滤，filterFixed=0/filterDepth=0/isFreeNodesEnable=false，所有属性均被序列化。 | 默认构造的 InspectorFilter 等价于全量 dump。 | AC-3.2 |
| R-13 | 行为 | SetFilterDepth 深度限制 | filterDepth 从 GetInspectorInfo 传入 GetInspectorChildren，每次递归 depth-1，depth=0 时停止递归。 | filterDepth=0 时使用默认 UINT32_MAX。 | AC-3.3 |
| R-14 | 行为 | EnableFreeNodes 自由节点 | isFreeNodesEnable=true 时追加其他页面节点和 other_contents 字段。 | GetFreeNodesInspector 内部创建 filter 并 EnableFreeNodes。 | AC-3.4 |
| R-15 | 行为 | IsFastFilter 快速过滤 | IsFastFilter()=true 时跳过非固定属性序列化，减少 JSON 输出量。 | FrameNode::MouseToJsonValue 等方法首行检查 IsFastFilter。 | AC-3.5 |
| R-16 | 行为 | DumpTree JSON 模式 | 输出 childSize/ID/Depth/InstanceId/AccessibilityId/IsDisappearing，key 为 tag_ 或 tag_id。 | IsDisappearing 仅在为 true 时输出。 | AC-4.1 |
| R-17 | 行为 | DumpTree 文本模式 | 输出 DumpBasicInfo + DumpInfo + Append(depth, name, childSize)。 | name 取决于 IsDumpAllNodes。 | AC-4.2 |
| R-18 | 边界 | DumpTree 不可见节点跳过 | !IsVisibleAndActive() 且 !IsDumpAllNodes() 时直接 return。 | IsDumpAllNodes 由 DumpLog 控制。 | AC-4.3 |
| R-19 | 行为 | DumpTree LazyForEach/Repeat 处理 | tag 为 LazyForEach/Repeat 时经 GetChildrenForInspector(true) 获取实际子节点。 | 解决懒加载场景下 children 不完整问题。 | AC-4.4 |
| R-20 | 行为 | DumpTree 全类型递归 | 递归 children/disappearingChildren/overlay/cornerMark，BrokenChildren 标记脱离父节点的子节点。 | desc 参数标识来源类型。 | AC-4.5 |
| R-21 | 行为 | FrameNode::DumpInfo() 文本 | LastParent + DumpCommonInfo + DumpOnSizeChangeInfo + KeyboardShortcut + pattern_->DumpInfo + renderContext_->DumpInfo。 | LastParent 仅在 Upgrade 有效时输出。 | AC-5.1 |
| R-22 | 行为 | FrameNode::DumpInfo(json) | DumpCommonInfo(json) + DumpOnSizeChangeInfo(json) + pattern_->DumpInfo(json) + renderContext_->DumpInfo(json)。 | 不输出 LastParent（JSON 模式简化）。 | AC-5.2 |
| R-23 | 行为 | FrameNode::DumpCommonInfo() 文本 | FrameRect/PaintRect/BackgroundColor/ParentLayoutConstraint/Active/Freeze/Visible/Padding/Border 等。 | BackgroundColor 仅在非 #00000000 时输出。 | AC-5.3 |
| R-24 | 行为 | FrameNode::DumpCommonInfo(json) | FrameRect/PaintRect/BackgroundColor/BuildLayoutInfo/SafeArea/VisibleArea/compid/ContentConstraint/AlignRules/DragInfo/OverlayInfo。 | compid 来自 propInspectorId_。 | AC-5.4 |
| R-25 | 行为 | FrameNode::DumpAdvanceInfo() 文本 | DumpCommonInfo + DumpOnSizeChangeInfo + KeyboardShortcut + pattern_->DumpInfo + pattern_->DumpAdvanceInfo + renderContext_->DumpInfo + renderContext_->DumpAdvanceInfo。 | 比 DumpInfo 多 Pattern/RenderContext 高级信息。 | AC-5.5 |
| R-26 | 边界 | IsDumpAllNodes 扩展输出 | IsDumpAllNodes()=true 时 DumpCommonInfo 额外输出 IsFrameDisappear/IsActive/AccessibilityVisible/HasAccessibilityVirtualNode。 | 用于全量诊断场景。 | AC-5.6 |
| R-27 | 行为 | Pattern dump 虚函数基类 | 8 个虚函数全部默认空实现，子类按需覆盖。 | DumpViewDataPageNode 有两个参数，默认 needsRecordData=false。 | AC-6.1 |
| R-28 | 行为 | Pattern dump JSON 集成 | FrameNode::DumpInfo(json) 调用 pattern_->DumpInfo(json)，由具体 Pattern 写入组件特有属性。 | pattern_ 为空时跳过。 | AC-6.2 |
| R-29 | 行为 | Pattern dump 高级信息 | FrameNode::DumpAdvanceInfo(json) 额外调用 pattern_->DumpAdvanceInfo(json)。 | 高级 dump 比 dump 多输出深层属性。 | AC-6.3 |
| R-30 | 行为 | Pattern ViewData 序列化 | FrameNode::DumpViewDataPageNode 委托 pattern_->DumpViewDataPageNode，用于自动填充/状态保存。 | needsRecordData 控制是否记录数据。 | AC-6.4 |
| R-31 | 行为 | InspectorOffscreenNodesMgr CRUD | AddOffscreenNode 执行 set::insert，RemoveOffscreenNode 执行 set::erase，GetOffscreenNodesSize 返回 size。 | std::set 按 RefPtr 排序，自动去重。 | AC-7.1 |
| R-32 | 行为 | GetOffScreenTreeNodes | 从 offscreenNodesMgr 获取离屏节点，逐个调用 AddInspectorTreeNode 构建扁平 RecNode 树。 | offscreenNodesMgr 为空时记录 WARNING 日志并 return。 | AC-7.2 |
| R-33 | 行为 | LayoutInspector::GetInspectorTreeJsonStr | 按 containerId 定位容器生成树 JSON，isNeedFreeNodes 控制是否包含自由节点。 | isNeedFreeNodes 默认 false。 | AC-7.3 |
| R-34 | 行为 | ParseWindowIdFromMsg 消息解析 | 解析 JSON method 字段校验 SUPPORT_METHOD（3 个方法），提取 params.windowId。 | method 不在 SUPPORT_METHOD 时返回 {INVALID_WINDOW_ID=0, INVALID_METHOD_ID=-1}。 | AC-7.4 |
| R-35 | 行为 | LayoutInspector::ProcessMessages | 返回 {windowId, pageId} 对用于定位目标窗口和页面。 | 与 ParseWindowIdFromMsg 配合使用。 | AC-7.5 |
| R-36 | 行为 | LayoutInspector::GetSnapshotJson | 生成含 PixelMap 截图的 JSON 快照。 | 使用 PixelMapPair = pair<uint64_t, shared_ptr<PixelMap>>。 | AC-7.6 |
| R-37 | 行为 | LayoutInspector Profiling 三态 | StateProfiler（jsStateProfilerStatusCallback_）/RSProfiler（rsProfilerNodeMountCallback_）/NodeTrace（enableNodeTrace_）三种独立 profiling。 | NodeTrace 使用 shared_mutex 保护。 | AC-7.7 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.6 / R-1..R-6 | 代码评审 + 单元测试 | inspector.cpp:787-832,537-546,601-633 |
| VM-2 | AC-2.1..2.5 / R-7..R-10 | 代码评审 + 单元测试 | inspector.cpp:857-891,636-688 |
| VM-3 | AC-3.1..3.5 / R-11..R-15 | 代码评审 | inspector_filter.h:38-71, frame_node.cpp:1631-1633 |
| VM-4 | AC-4.1..4.5 / R-16..R-20 | 代码评审 + 单元测试 | ui_node.cpp:1385-1435 |
| VM-5 | AC-5.1..5.6 / R-21..R-26 | 代码评审 | frame_node.cpp:1186-1238,1579-1610,8289-8344 |
| VM-6 | AC-6.1..6.4 / R-27..R-30 | 代码评审 | pattern.h:335-344, frame_node.cpp:1579-1617,8320-8344 |
| VM-7 | AC-7.1..7.7 / R-31..R-37 | 代码评审 + 单元测试 | inspector.h:44-54, inspector.cpp:773-778,1154-1238,1172-1196, layout_inspector.h:39-104 |

## API 变更分析

### 新增 API

N/A，无新增 Public/System/InnerApi。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

无新增接口规格。

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 无 @since 标注（框架内部能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| Inspector 纯静态工具类 | 不持有状态，通过 PipelineContext::GetCurrentContext() 获取上下文；InspectorOffscreenNodesMgr 挂载在 PipelineContext 上 | AC-1.1 / AC-7.1 |
| 树形序列化严格自上而下 | GetInspector→GetContextInfo+GetLastPage→GetFrameNodeChildren→GetInspectorInfo→GetInspectorChildren→PutNodeInfoToJsonNode+ToJsonValue，不允许子节点反向修改父节点 JSON | AC-1.1 / AC-1.4 |
| DumpTree 调用链 | UINode::DumpTree→DumpBasicInfo+DumpInfo→FrameNode::DumpInfo→DumpCommonInfo+pattern_->DumpInfo+renderContext_->DumpInfo | AC-4.1 / AC-5.1 |
| Pattern dump 虚函数开放扩展点 | 8 个虚函数由 25+ Pattern 子类覆盖，新增组件必须覆盖 DumpInfo/DumpInfo(json) | AC-6.1 / AC-6.2 |
| LayoutInspector IDE 通信唯一入口 | RegisterConnectCallback 注册回调，GetInspectorTreeJsonStr/GetSnapshotJson 由 connect server 消息驱动 | AC-7.3 / AC-7.5 |
| JSON 字段命名约定 | Inspector 树用 $ 前缀，DumpTree JSON 无 $ 前缀，两种格式不可混用 | AC-4.1 / AC-1.5 |
| deviceRect 全局变量 | 匿名命名空间，GetContextInfo 初始化后供 PutNodeInfoToJsonNode 使用，每次 GetInspector 重新初始化 | AC-1.2 |

## 非性能需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | GetInspector O(N) 序列化；GetInspectorByKey O(N) BFS；InspectorFilter CheckFixedAttr O(1) 位运算 | 代码评审 | 代码审查 |
| 性能 | DumpTree 不可见/非活跃节点提前剪枝 | 代码评审 | 代码审查 |
| 可观测 | Inspector JSON 含 $rect/$debugLine/$attrs；LayoutInspector 含 VsyncID/ProcessID/WindowID | 代码评审 | 代码审查 |
| 鲁棒性 | context/pageRootNode 为空时 needThrow=true；GetFrameNodeByKey 空时返回 nullptr | 代码评审 | 代码审查 |
| 鲁棒性 | GetInspectorChildren 对非法 JSON 执行 ConvertIllegalStr 过滤并 LOGW | 代码评审 | 代码审查 |
| 线程安全 | InspectorOffscreenNodesMgr std::set 非 thread-safe 约定 UI 线程调用；NodeTrace 用 shared_mutex | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Inspector 无障碍语义字段（clickable/scrollable 等）影响无障碍树构建 | DumpTreeNodeInfoNG |
| 大字体 | 否 | Inspector 输出不受字体缩放影响 | — |
| 深色模式 | 否 | Inspector 输出不含颜色模式语义 | — |
| 多窗口 | 是 | Inspector 按 containerId 区分窗口；GetSubWindowInspector 支持子窗口 | GetInspectorTreeJsonStr |
| 多用户 | 否 | 框架内部能力，不涉及多用户 | — |
| 版本升级 | 否 | 全部为已有实现补录 | — |
| 生态兼容 | 否 | 无 Public/System API 变更 | — |

## Spec 自审清单

- [x] 所有 H2 章节按模板齐全
- [x] 每个 US 都有 AC，并使用 AC-X.Y 编号
- [x] 每个 AC 在「验收追溯」「验证映射」中可被引用
- [x] 规则定义使用 R-N 编号，类型标签齐全（行为/边界/异常/恢复）
- [x] 所有源码引用均给出 file:line
- [x] API 变更分析已说明本 Feat 为框架内部接口
- [x] 兼容性声明覆盖编译配置/跨版本/节点类型/线程安全四个维度
- [x] 无 TODO / TBD / 待定 占位符
- [x] 7 个 US 覆盖 Inspector 序列化 / BFS 搜索 / Filter 过滤 / DumpTree / FrameNode dump / Pattern 虚函数 / LayoutInspector IDE 集成

## context-references

```yaml
references:
  - path: frameworks/core/components_ng/base/inspector.h
    lines: 28-33
    description: Inspector 常量：KEY_METHOD/KEY_PARAMS/KEY_PARAM_NEED_FREE_NODES/INSPECTOR_INVALID_WINDOW_ID/INVALID_METHOD_ID
  - path: frameworks/core/components_ng/base/inspector.h
    lines: 35
    description: InspectorTreeMap = unordered_map<int32_t, RefPtr<RecNode>>
  - path: frameworks/core/components_ng/base/inspector.h
    lines: 37-42
    description: InspectorChildrenParameters 结构体：pageId/isActive/isLayoutInspector/needHandleInternal
  - path: frameworks/core/components_ng/base/inspector.h
    lines: 44-54
    description: InspectorOffscreenNodesMgr 类声明：AddOffscreenNode/RemoveOffscreenNode/GetOffscreenNodesSize/GetOffscreenNodes/ClearOffscreenNodes + offscreenNodes_ std::set
  - path: frameworks/core/components_ng/base/inspector.h
    lines: 56-87
    description: Inspector 类声明：16 个 public 静态方法 + 5 个 private 静态方法
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 35-52
    description: Inspector JSON 常量定义：$type/$ID/$rect/$attrs/$children/$debugLine/$resolution 及 PREVIEW 条件编译常量
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 54
    description: SUPPORT_METHOD = {"ArkUI.tree", "ArkUI.tree.3D", "ArkUI.queryAbilities"}
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 56
    description: LONG_PRESS_DELAY = 1000ms
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 329-341
    description: PutNodeInfoToJsonNode：INSPECTOR_RECT + INSPECTOR_DEBUGLINE，isActive 门控
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 391-479
    description: GetInspectorChildren 递归树构建：SpanNode/CustomNode/NavDestination 处理 + 深度递减 + JSON 非法过滤
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 537-546
    description: GetContextInfo：Width/Height = rootWidth/Height * viewScale，$resolution = GetCurrentDensity，deviceRect 初始化
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 601-633
    description: GetInspectorInfo：isLayoutInspector 外层包装 type/content/VsyncID/ProcessID/WindowID + FreeNodes other_contents
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 636-661
    description: GetFrameNodeByKey：离屏节点优先搜索 + rootElement 搜索
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 663-688
    description: GetInspectorNodeByKey：单节点 JSON 序列化
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 773-778
    description: GetFreeNodesInspector：filter.EnableFreeNodes + GetInspector(true, filter, needThrow)
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 787-832
    description: GetInspector 主流程：JSON root → GetContextInfo → GetLastPage → GetFrameNodeChildren → GetInspectorInfo
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 834-855
    description: GetInspectorOfNode：单节点 inspector，depth=0
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 857-891
    description: GetInspectorByKey BFS 搜索：双层 vector 轮换
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 893-908
    description: GetSubWindowInspector：OverlayManager 根节点
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 1010-1031
    description: GetInspectorTree：InspectorTreeMap 构建
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 1154-1170
    description: GetOffScreenTreeNodes：离屏节点树构建
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 1172-1196
    description: ParseWindowIdFromMsg：JSON method 校验 + windowId 提取
  - path: frameworks/core/components_ng/base/inspector.cpp
    lines: 1198-1211
    description: ParseNeedFreeNodes：isNeedFreeNodes 参数解析
  - path: interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h
    lines: 27-36
    description: TreeKey 命名空间常量：ID/CLICKABLE/LONG_CLICKABLE/SCROLLABLE/CONTENT/PLACEHOLDER/CHECKED/IS_EDITABLE
  - path: interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h
    lines: 38-47
    description: FixedAttrBit 枚举：8 个位 0-7
  - path: interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h
    lines: 49-71
    description: InspectorFilter 类：CheckFixedAttr/CheckExtAttr/IsFastFilter/AddFilterAttr/SetFilterID/SetFilterDepth/EnableFreeNodes + filterId/filterDepth/filterFixed/filterExt/isFreeNodesEnable 成员
  - path: interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h
    lines: 73-76
    description: InspectorConfig 结构体：contentOnly/callingOnMain
  - path: frameworks/core/components_ng/base/ui_node.h
    lines: 348-365
    description: UINode dump 方法声明：DumpViewDataPageNodes/DumpTree/DumpTreeJsonForDiff/DumpSimplifyTree 系列
  - path: frameworks/core/components_ng/base/ui_node.h
    lines: 1191-1240
    description: UINode dump 虚函数声明：DumpSimplifyInfoWithParamConfig + protected DumpInfo/DumpSimplifyInfo/DumpAdvanceInfo/DumpViewDataPageNode 等空实现
  - path: frameworks/core/components_ng/base/ui_node.cpp
    lines: 1385-1435
    description: DumpTree 实现：JSON/文本双模式 + 不可见剪枝 + LazyForEach/Repeat + children/disappearing/overlay/cornerMark 递归
  - path: frameworks/core/components_ng/base/frame_node.h
    lines: 1634-1640
    description: FrameNode dump 方法 override 声明：DumpInfo/DumpInfo(json)/DumpSimplifyInfo/DumpSimplifyInfoOnlyForParamConfig
  - path: frameworks/core/components_ng/base/frame_node.h
    lines: 1693-1724
    description: FrameNode private dump 方法声明：DumpDragInfo/DumpOverlayInfo/DumpCommonInfo 系列/DumpAdvanceInfo/DumpOnSizeChangeInfo/DumpKeyboardShortcutInfo
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 1186-1238
    description: DumpCommonInfo 文本模式：FrameRect/PaintRect/BackgroundColor/ParentLayoutConstraint/Active/Freeze/Visible/Padding/Border
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 1579-1595
    description: DumpInfo() 文本模式：LastParent + DumpCommonInfo + DumpOnSizeChangeInfo + KeyboardShortcut + Pattern + RenderContext
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 1597-1610
    description: DumpAdvanceInfo() 文本模式：追加 Pattern + RenderContext 高级信息
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 1612-1617
    description: DumpViewDataPageNode：委托 pattern_->DumpViewDataPageNode
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 8289-8318
    description: DumpCommonInfo(json)：FrameRect/PaintRect/BackgroundColor/BuildLayoutInfo/SafeArea/VisibleArea/compid/ContentConstraint/AlignRules/DragInfo/OverlayInfo
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 8320-8330
    description: DumpInfo(json)：DumpCommonInfo(json) + DumpOnSizeChangeInfo(json) + Pattern(json) + RenderContext(json)
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 8332-8344
    description: DumpAdvanceInfo(json)：追加 pattern_->DumpAdvanceInfo(json) + renderContext_->DumpAdvanceInfo(json)
  - path: frameworks/core/components_ng/pattern/pattern.h
    lines: 335-344
    description: Pattern dump 虚函数声明：8 个虚函数全部默认空实现
  - path: frameworks/core/common/layout_inspector.h
    lines: 27-33
    description: FrameNodeInfo 结构体：rsNodeId/frameNodeId/nodeType/debugline/parentNodeId
  - path: frameworks/core/common/layout_inspector.h
    lines: 35-37
    description: ProfilerStatusCallback / RsProfilerNodeMountCallback / PixelMapPair 类型别名
  - path: frameworks/core/common/layout_inspector.h
    lines: 39-55
    description: LayoutInspector public 方法：SupportInspector/SetlayoutInspectorStatus/GetInspectorTreeJsonStr/CreateLayoutInfo 系列/GetSnapshotJson/ProcessMessages/RegisterConnectCallback/3D 布局
  - path: frameworks/core/common/layout_inspector.h
    lines: 57-64
    description: StateProfiler 方法：GetStateProfilerStatus/SetStateProfilerStatus/TriggerJsStateProfilerStatusCallback/SendMessage/SetJsStateProfilerStatusCallback/HasJsStateProfilerStatusCallback/AppendJsStateProfilerStatusCallback
  - path: frameworks/core/common/layout_inspector.h
    lines: 66-72
    description: RSProfiler 方法：GetRsProfilerNodeMountCallback/SetRsProfilerNodeMountCallback/HandleStartRecord/HandleStopRecord/HandleInnerCallback/ConnectServerCallback
  - path: frameworks/core/common/layout_inspector.h
    lines: 76-81
    description: NodeTrace 方法 + ArkUI Interaction 方法
  - path: frameworks/core/common/layout_inspector.h
    lines: 83-103
    description: LayoutInspector private 成员：recNodeInfos_/recMutex_/stateProfilerStatus_/layoutInspectorStatus_/jsStateProfilerStatusCallback_/rsProfilerNodeMountCallback_/enableNodeTrace_/enableTraceMutex_ 等
```
