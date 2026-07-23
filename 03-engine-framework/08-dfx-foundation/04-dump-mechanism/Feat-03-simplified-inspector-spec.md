# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SimplifiedInspector与简化树 |
| 特性编号 | Func-03-08-04-Feat-03 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 ArkUI ace_engine 的简化树采集子系统：SimplifiedInspector 三构造模式（TreeParams 全树 / UICommandParams 命令执行 / ComponentParams 单组件截图）、同步 GetInspector 与异步 GetInspectorAsync / GetInspectorBackgroundAsync 采集管线、ExecuteUICommand 节点/Web 滚动命令、GetComponentImageInfo 组件截图（PixelMap / Snapshot）、UINode 简化树基础信息与递归遍历（DumpSimplifyTreeBase / DumpSimplifyTreeNode / DumpSimplifyTree）、ParamConfig 驱动的矩形剔除与不透明度剔除（DumpSimplifyTreeWithParamConfig 系列）、FrameNode 简化公共信息与安全区域信息输出、InspectorTreeCollector 异步任务计数与结果回调、AceContainer::DumpSimplifyTreeWithParamConfig 入口委托。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | SimplifiedInspector 三构造模式规格 | simplified_inspector.h:30-32 构造函数声明，simplified_inspector.cpp:250-261 三构造模式实现（TreeParams / UICommandParams / ComponentParams） |
| ADDED | SimplifiedInspector GetInspector 同步采集规格 | simplified_inspector.cpp:277-294 同步 JSON 树采集，Step1 + Step2 两阶段 |
| ADDED | SimplifiedInspector 异步与后台采集规格 | simplified_inspector.cpp:526-601 GetInspectorAsync / GetInspectorBackgroundAsync，后台线程 + 节点缓存 |
| ADDED | ExecuteUICommand UI 命令执行规格 | simplified_inspector.cpp:700-758 命令解析 + NODE 滚动 / Web JS 执行，3 种错误码 |
| ADDED | GetComponentImageInfo 组件截图规格 | simplified_inspector.cpp:760-824 三种截图模式（PixelMap=1 / Snapshot=2 / ImageSnapshot=3） |
| ADDED | UINode 简化树基础信息与递归遍历规格 | ui_node.cpp:1495-1517,1742-1769 DumpSimplifyTreeBase / DumpSimplifyTreeNode / DumpSimplifyTree |
| ADDED | UINode ParamConfig 矩形剔除与不透明度剔除规格 | ui_node.cpp:1519-1608 RectCullingState / CreateRectCullingState / IsCulledByRect，ui_node.cpp:1610-1740 DumpSimplifyTreeWithParamConfig 系列 |
| ADDED | FrameNode 简化公共信息与安全区域信息规格 | frame_node.cpp:1396-1500 DumpSimplifyCommonInfo / DumpSimplifyCommonInfoOnlyForParamConfig / DumpSimplifySafeAreaInfo |
| ADDED | InspectorTreeCollector 异步任务计数与回调规格 | inspector_tree_collector.h:28-50, inspector_tree_collector.cpp:20-89 任务计数 / 结果回调 / 节点缓存 |
| ADDED | AceContainer::DumpSimplifyTreeWithParamConfig 入口委托规格 | ace_container.cpp:2593-2600 委托 pipelineContext->GetComponentOverlayInspector |

## 输入文档

- 关联设计：`specs/03-engine-framework/08-dfx-foundation/04-dump-mechanism/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/core/components_ng/base/simplified_inspector.h`（81 行）—— SimplifiedInspector 类声明、三构造模式、SimplifiedInspectorTree 内部结构
  - `frameworks/core/components_ng/base/simplified_inspector.cpp`（825 行）—— 同步/异步/后台采集、命令执行、组件截图实现
  - `frameworks/core/components_ng/base/ui_node.h:354-360,1235-1237,1309-1317` —— UINode 简化树方法声明、RectCullingState 前向声明
  - `frameworks/core/components_ng/base/ui_node.cpp:46-50,1495-1769` —— DumpSimplifyTreeBase / Node / Tree / WithParamConfig 系列实现 + RectCullingState 定义
  - `frameworks/core/components_ng/base/frame_node.h:1698-1701` —— FrameNode 简化信息方法声明
  - `frameworks/core/components_ng/base/frame_node.cpp:1396-1500` —— DumpSimplifyCommonInfo / OnlyForParamConfig / SafeAreaInfo 实现
  - `adapter/ohos/entrance/ace_container.cpp:2593-2600` —— DumpSimplifyTreeWithParamConfig 入口
  - `frameworks/core/common/recorder/inspector_tree_collector.h`（52 行）—— InspectorTreeCollector 声明
  - `frameworks/core/common/recorder/inspector_tree_collector.cpp`（89 行）—— 任务计数 / 结果回调 / 节点缓存实现
  - `interfaces/inner_api/ace/ui_event_observer.h:47-76` —— TreeParams / UICommandParams / ComponentParams / ComponentResult 结构定义
  - `interfaces/inner_api/ui_session/param_config.h:23-31` —— ParamConfig 结构定义
  - `interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h:73-76` —— InspectorConfig 结构定义

## 用户故事

### US-1: SimplifiedInspector 同步简化树采集

- As a 自动化测试工具开发者
- I want SimplifiedInspector::GetInspector 同步返回当前页面的简化 JSON 组件树
- So that 在 UI 线程上即时获取组件树快照用于测试断言

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN SimplifiedInspector 以 TreeParams 构造且 params_.infoType == InspectorInfoType::WEB_LANG THEN GetInspector 调用 GetCurrentWebLang 获取活跃 Web 节点语言并直接返回字符串，不执行树采集。来源：`simplified_inspector.cpp:281-285` | 正常 |
| AC-1.2 | WHEN GetInspector 正常执行 THEN 先调用 GetInspectorStep1 填充 root 元信息（$type="root"、width、height、$resolution、navDstName），若 StageManager 或 pageRootNode 为空则返回当前 jsonRoot->ToString()；Step1 成功后调用 GetInspectorStep2 填充 bundleName、ability、pageUrl 并递归采集子节点。来源：`simplified_inspector.cpp:277-294,296-345` | 正常 |
| AC-1.3 | WHEN GetInspectorStep2 执行 THEN 遍历 pageRootNode 子节点调用 GetFrameNodeChildren 收集顶层 FrameNode/SpanNode/CustomNode，并追加 overlay 节点子树；最终在 jsonRoot 写入 $children 数组和 $childrenCount（= size_）。来源：`simplified_inspector.cpp:315-345` | 正常 |
| AC-1.4 | WHEN GetInspectorChildren 遍历节点 THEN 对非 enableAllNodes 模式跳过 inactive 节点和 visibility != VISIBLE 的节点；CheckNodeRect 在 isVisibleOnly 模式下跳过与 deviceRect_ 不相交的节点。来源：`simplified_inspector.cpp:373-417,468-481` | 边界 |

### US-2: SimplifiedInspector 异步与后台采集

- As a UI 事件录制工具开发者
- I want SimplifiedInspector 提供异步和后台线程采集模式，通过 InspectorTreeCollector 回调结果
- So that 采集大量节点时不阻塞 UI 线程

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN GetInspectorAsync(collector) 被调用 THEN 受 `#if !defined(PREVIEW) && !defined(ACE_UNITTEST)` 编译条件保护；设置 isAsync_=true，IncreaseTaskNum 后复用 Step1/Step2 采集逻辑，完成后 DecreaseTaskNum。来源：`simplified_inspector.cpp:526-546` | 正常 |
| AC-2.2 | WHEN GetInspectorBackgroundAsync(collector) 被调用 THEN 先在调用线程构建 SimplifiedInspectorTree（GetInspectorTreeNode 缓存 WeakPtr 节点引用），然后 PostTask 到 TaskExecutor::BACKGROUND 线程执行 JSON 序列化，序列化完成后 DecreaseTaskNum 触发回调。来源：`simplified_inspector.cpp:548-601` | 正常 |
| AC-2.3 | WHEN 后台采集模式下 GetFrameNodeChildren 被调用 THEN 通过 collector_->RetainNode(uiNode) 将节点 RefPtr 缓存到 InspectorTreeCollector::cacheNodes_，防止后台序列化期间节点被释放。来源：`simplified_inspector.cpp:347-352, inspector_tree_collector.cpp:80-83` | 恢复 |

### US-3: ExecuteUICommand UI 命令执行

- As a 自动化驱动工具开发者
- I want SimplifiedInspector::ExecuteUICommand 解析命令 JSON 并执行滚动定位操作
- So that 自动化测试能通过命令驱动节点滚动到可视区域

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN ExecuteUICommand 被调用且 ParseCommandParam 解析失败（action != "scroll" 或 JSON 无效）THEN 在 collector JSON 中写入 code=ERR_INVALID_PARAM(101) 并 DecreaseTaskNum 返回。来源：`simplified_inspector.cpp:707-712,68-71,92-101` | 异常 |
| AC-3.2 | WHEN command.type == TargetType::NODE THEN 通过 GetNodeById BFS 查找目标节点，FindParentScrollable 向上查找最近的 List/Scroll/WaterFlow/Grid 可滚动父节点，调用 ScrollablePattern::ScrollToTarget 执行滚动；成功返回 code=ERR_OK(0)，节点未找到返回 ERR_NOT_FOUND_TARGET_NODE(102)，无可滚动父节点返回 ERR_NOT_FOUND_SCROLLABLE_NODE(103)。来源：`simplified_inspector.cpp:164-175,718-722` | 正常 |
| AC-3.3 | WHEN command.type == TargetType::WEB THEN 调用 ExecuteWebScrollCommand 在 WEB_SUPPORTED 条件下查找 nodeId 对应的 Web 节点，通过 WebPattern::RunJavascriptAsync 异步执行 jsCode，回调中写入 code=ERR_OK 和 ret；jsCode 为空返回 ERR_INVALID_PARAM。来源：`simplified_inspector.cpp:733-758` | 正常 |

### US-4: GetComponentImageInfo 组件截图

- As a UI 截图工具开发者
- I want SimplifiedInspector::GetComponentImageInfo 根据 mode 返回组件像素图或快照
- So that 获取组件渲染结果用于视觉对比

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN componentParams_.mode == MODE_IMAGE_PIXELMAP(1) THEN 通过 GetNodeById 查找 aceId 节点，仅对 Image_ETS_TAG 节点从 ImagePattern::GetCanvasImage → GetPixelMap 提取 PixelMap，通过 result->callback 回传 {nodeId, pixelMap} 并设置 result->isOk=true。来源：`simplified_inspector.cpp:771-777,785-799,73-74` | 正常 |
| AC-4.2 | WHEN componentParams_.mode == MODE_COMPONENT_SNAPSHOT(2) THEN 对目标 FrameNode 调用 ComponentSnapshot::GetNormalCapture 异步截图；mode == MODE_IMAGE_SNAPSHOT(3) THEN 先通过 Recorder::GetFirstImageNodeChild 找到子 Image 节点再截图。回调通过 result->callback 回传 {aceId, pixelMap} 并设置 result->isOk=true。来源：`simplified_inspector.cpp:778-824` | 正常 |

### US-5: UINode 简化树基础信息与递归遍历

- As a 框架调试开发者
- I want UINode 提供 DumpSimplifyTreeBase / DumpSimplifyTreeNode / DumpSimplifyTree 三层简化信息输出
- So that 简化树以轻量 JSON 格式输出节点标识与关键属性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN DumpSimplifyTreeBase(json) 被调用 THEN 写入 $type=tag_、$ID=nodeId_，并对 CustomNode 子类写入 type="custom"，其他写入 type="build-in"。来源：`ui_node.cpp:1495-1504` | 正常 |
| AC-5.2 | WHEN DumpSimplifyTreeNode(json, config) 被调用 THEN 依次调用 DumpSimplifyTreeBase + DumpSimplifyInfo + DumpSimplifyInfoOnlyForParamConfig(json, config)，组合基础标识、子类扩展信息与 config 控制的交互/无障碍信息。来源：`ui_node.cpp:1506-1511` | 正常 |
| AC-5.3 | WHEN DumpSimplifyTree(depth, json) 被调用 THEN 先写 Base + Info，若节点不可见或 inactive 则不递归子节点；否则遍历 GetChildren() 和 disappearingChildren_，对每个子节点递归 DumpSimplifyTree(depth+1, child)，结果写入 $children 数组。来源：`ui_node.cpp:1742-1769` | 正常 |

### US-6: UINode ParamConfig 矩形剔除与不透明度剔除

- As a 性能优化工程师
- I want DumpSimplifyTreeWithParamConfig 支持 rectCulling 和 minOpacity 剔除离屏和近乎透明的节点
- So that 长列表等大型树的 dump 输出量大幅减少

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN DumpSimplifyTreeWithParamConfig 被调用且 onlyNeedVisible=true THEN 调用 CreateRectCullingState 从当前节点沿父链计算 viewportRect 和 clipRect（clipRect 仅在父节点 GetClipEdge()==true 时更新并通过 Constrain 取交集）；onlyNeedVisible=false 时设置 config.minOpacity=0.0f 且 config.rectCulling=false。来源：`ui_node.cpp:1519-1548,1725-1740` | 正常 |
| AC-6.2 | WHEN DumpSimplifyTreeWithParamConfigInner 遍历子节点 THEN 在 config.minOpacity > 0 时累计 currentFinalOpacity（= parentFinalOpacity * GetNodeOpacityValue），若 currentFinalOpacity < config.minOpacity 则跳过该子节点；cacheChildren 仅对 JS_LAZY_FOR_EACH / JS_REPEAT 节点通过 GetChildrenForInspector(true) 获取。来源：`ui_node.cpp:1610-1639,1649-1692` | 正常 |
| AC-6.3 | WHEN IsCulledByRect(rectCullingState, hasInspectableChildren) 被调用 THEN 节点 rect 与 clipRect 不相交时返回 !hasInspectableChildren（有可检查子节点时不剔除），与 viewportRect 不相交时同样返回 !hasInspectableChildren。来源：`ui_node.cpp:1587-1608` | 边界 |

### US-7: FrameNode 简化公共信息与安全区域信息

- As a 框架调试开发者
- I want FrameNode 输出简化公共信息（rect/compid/active/visible/opacity/backgroundColor）和安全区域信息
- So that 简化树包含足够的视觉与布局状态用于调试

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN DumpSimplifyCommonInfo(json) 被调用 THEN 写入 $rect（GetTransformRectRelativeToWindow().ToBounds()）、compid（非空时）、active="false"（非活跃时）、visible="false"（非可见时）、opacity（非 1.0 时）、backgroundColor（有值时）。来源：`frame_node.cpp:1396-1417` | 正常 |
| AC-7.2 | WHEN DumpSimplifyCommonInfoOnlyForParamConfig(json, config) 被调用且 config.interactionInfo=true THEN 输出 clickable、longClickable、focusable、scrollable、editable；config.accessibilityInfo=true 时输出 accessibilityContent。来源：`frame_node.cpp:1419-1440` | 正常 |
| AC-7.3 | WHEN DumpSimplifySafeAreaInfo(json) 被调用 THEN 输出 SafeAreaExpandOpts（type/edges 非 NONE 时）、SafeAreaInsets（有值时）、SelfAdjust/ParentSelfAdjust（SelfOrParentExpansive 且非默认零矩形时）；仅 PAGE_ETS_TAG 节点额外输出 KeyboardInset、IgnoreSafeArea、IsNeedAvoidWindow、IsFullScreen、IsKeyboardAvoidMode、IsUseCutout。来源：`frame_node.cpp:1467-1500` | 正常 |

### US-8: InspectorTreeCollector 异步任务计数与结果回调

- As a 异步采集调度开发者
- I want InspectorTreeCollector 维护任务计数，在所有异步子任务完成后触发结果回调
- So that 包含 Web 异步节点的完整树在所有结果就绪后才回调

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN InspectorTreeCollector::UpdateTaskNum 将 taskNum_ 递减至 0 THEN 调用 onResultFunc_(root_->ToString()) 回调完整结果，随后重置 root_ 为新 JSON；若 isBackground_ 则 PostTask 到 UI 线程清空 cacheNodes_。来源：`inspector_tree_collector.cpp:47-68` | 正常 |
| AC-8.2 | WHEN isBackground_ == true THEN IncreaseTaskNum/DecreaseTaskNum 使用 std::unique_lock<std::mutex> 保护 taskNum_ 操作；isBackground_ == false 时无锁直接操作。来源：`inspector_tree_collector.cpp:27-45` | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|---------|------|
| AC-1.1 | R-1 | TASK-03 | 代码评审 | 代码审查 |
| AC-1.2 | R-2 / R-3 | TASK-03 | 代码评审 | 代码审查 |
| AC-1.3 | R-3 | TASK-03 | 代码评审 | 代码审查 |
| AC-1.4 | R-4 / R-5 | TASK-03 | 代码评审 | 代码审查 |
| AC-2.1 | R-6 | TASK-03 | 代码评审 | 代码审查 |
| AC-2.2 | R-7 / R-8 | TASK-03 | 代码评审 | 代码审查 |
| AC-2.3 | R-9 | TASK-03 | 代码评审 | 代码审查 |
| AC-3.1 | R-10 | TASK-03 | 代码评审 | 代码审查 |
| AC-3.2 | R-11 / R-12 | TASK-03 | 代码评审 | 代码审查 |
| AC-3.3 | R-13 | TASK-03 | 代码评审 | 代码审查 |
| AC-4.1 | R-14 | TASK-03 | 代码评审 | 代码审查 |
| AC-4.2 | R-15 | TASK-03 | 代码评审 | 代码审查 |
| AC-5.1 | R-16 | TASK-03 | 代码评审 | 代码审查 |
| AC-5.2 | R-17 | TASK-03 | 代码评审 | 代码审查 |
| AC-5.3 | R-18 | TASK-03 | 代码评审 | 代码审查 |
| AC-6.1 | R-19 / R-20 | TASK-03 | 代码评审 | 代码审查 |
| AC-6.2 | R-21 / R-22 | TASK-03 | 代码评审 | 代码审查 |
| AC-6.3 | R-23 | TASK-03 | 代码评审 | 代码审查 |
| AC-7.1 | R-24 | TASK-03 | 代码评审 | 代码审查 |
| AC-7.2 | R-25 | TASK-03 | 代码评审 | 代码审查 |
| AC-7.3 | R-26 | TASK-03 | 代码评审 | 代码审查 |
| AC-8.1 | R-27 / R-28 | TASK-03 | 代码评审 | 代码审查 |
| AC-8.2 | R-28 | TASK-03 | 代码评审 | 代码审查 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetInspector 且 infoType==WEB_LANG | 调用 GetCurrentWebLang 查找活跃 Web 节点语言并直接返回 | 仅返回语言字符串，不构建树 | AC-1.1 |
| R-2 | 行为 | GetInspectorStep1 执行 | 填充 $type="root"、width、height、$resolution、navDstName；StageManager/pageRootNode 为空时返回 false | deviceRect_ 设为 (0,0,rootWidth*scale,rootHeight*scale) | AC-1.2 |
| R-3 | 行为 | GetInspectorStep2 执行 | 填充 bundleName、ability、pageUrl，递归 GetFrameNodeChildren 收集子节点，输出 $children 和 $childrenCount | 跳过 tag=="page" 且 pageId 不匹配的节点，跳过 IsInternal 的 FrameNode | AC-1.2 / AC-1.3 |
| R-4 | 边界 | GetInspectorChildren 节点过滤 | 非(enableAllNodes)模式下跳过 inactive 和 visibility!=VISIBLE 的节点 | SpanNode 走 GetSpanInspector 特殊路径，使用父 Text 节点 rect | AC-1.4 |
| R-5 | 边界 | CheckNodeRect 节点矩形检查 | paintRect 为空时返回 false；isVisibleOnly 模式下 rect 与 deviceRect_ 不相交时返回 false | rect 取 GetTransformRectRelativeToWindow | AC-1.4 |
| R-6 | 边界 | GetInspectorAsync 编译条件 | 受 `!defined(PREVIEW) && !defined(ACE_UNITTEST)` 保护 | PREVIEW 或 ACE_UNITTEST 构建下函数体为空 | AC-2.1 |
| R-7 | 行为 | GetInspectorBackgroundAsync 执行 | 先在调用线程构建 SimplifiedInspectorTree 缓存 WeakPtr 节点，PostTask 到 BACKGROUND 线序列化 JSON | 序列化完成后 DecreaseTaskNum 触发回调 | AC-2.2 |
| R-8 | 行为 | 后台采集 JSON 构建 | BACKGROUND 线程填充 root 元信息（width/height/resolution/ability/bundle/pageUrl/navDstName），遍历 treeNode->children 调用 GetInspectorChildrenBackground | size_ 初始值为 1 | AC-2.2 |
| R-9 | 恢复 | 后台采集节点缓存 | isBackground_ 模式下 GetFrameNodeChildren 调用 collector_->RetainNode 缓存 RefPtr | 回调触发后在 UI 线程清空 cacheNodes_ | AC-2.3 |
| R-10 | 异常 | ExecuteUICommand 参数解析失败 | ParseCommandParam 返回 false 时写入 code=ERR_INVALID_PARAM(101) | action 必须为 "scroll" | AC-3.1 |
| R-11 | 行为 | NODE 类型滚动命令 | GetNodeById BFS 查找节点，FindParentScrollable 查找可滚动父节点，ScrollablePattern::ScrollToTarget 执行 | 可滚动节点 tag：LIST_ETS_TAG / SCROLL_ETS_TAG / WATERFLOW_ETS_TAG / GRID_ETS_TAG | AC-3.2 |
| R-12 | 异常 | NODE 滚动错误码 | 目标节点未找到返回 ERR_NOT_FOUND_TARGET_NODE(102)，可滚动父节点未找到返回 ERR_NOT_FOUND_SCROLLABLE_NODE(103)，成功返回 ERR_OK(0) | ScrollablePattern::IsScrollable 返回 false 的节点跳过 | AC-3.2 |
| R-13 | 行为 | WEB 类型滚动命令 | WEB_SUPPORTED 下通过 WebPattern::RunJavascriptAsync 异步执行 jsCode，回调写入 code+ret | jsCode 为空返回 ERR_INVALID_PARAM；非 WEB_SUPPORTED 返回 ERR_NOT_FOUND_TARGET_NODE | AC-3.3 |
| R-14 | 行为 | MODE_IMAGE_PIXELMAP 截图 | 仅对 Image_ETS_TAG 节点，从 ImagePattern::GetCanvasImage→GetPixelMap 提取，回调 {nodeId, pixelMap} | 非 Image 节点返回 nullptr | AC-4.1 |
| R-15 | 行为 | MODE_COMPONENT_SNAPSHOT / MODE_IMAGE_SNAPSHOT | ComponentSnapshot::GetNormalCapture 异步截图；IMAGE_SNAPSHOT 先找子 Image 节点 | 回调 {aceId, pixelMap}，result->isOk=true | AC-4.2 |
| R-16 | 行为 | DumpSimplifyTreeBase | 写入 $type=tag_、$ID=nodeId_、type="custom"/"build-in" | CustomNode 子类判定使用 InstanceOf<CustomNode> | AC-5.1 |
| R-17 | 行为 | DumpSimplifyTreeNode | 组合 Base + DumpSimplifyInfo(虚函数) + DumpSimplifyInfoOnlyForParamConfig(json, config) | DumpSimplifyInfo 默认空实现，由子类覆写 | AC-5.2 |
| R-18 | 行为 | DumpSimplifyTree 递归遍历 | Base + Info 后，IsVisibleAndActive 为 true 时递归子节点 + disappearingChildren_ | depth+1 传递给子节点 | AC-5.3 |
| R-19 | 行为 | DumpSimplifyTreeWithParamConfig 入口 | onlyNeedVisible=false 时设置 minOpacity=0.0f、rectCulling=false；dumpChecker 为空时设为全通过 | 父默认不透明度 DEFAULT_NODE_OPACITY | AC-6.1 |
| R-20 | 行为 | CreateRectCullingState | onlyNeedVisible && config.rectCulling 时从当前节点沿父链计算 viewportRect（= 当前节点 rect）和 clipRect（= 父节点 clip 且 GetClipEdge()==true 时 Constrain 交集） | enabled = viewportRect.has_value() | AC-6.1 |
| R-21 | 行为 | DumpSimplifyTreeWithParamConfigInner 不透明度累积 | config.minOpacity > 0 时 currentFinalOpacity *= GetNodeOpacityValue，低于阈值则跳过 | NearZero(config.minOpacity) 时不启用不透明度剔除 | AC-6.2 |
| R-22 | 行为 | cacheChildren 获取 | JS_LAZY_FOR_EACH / JS_REPEAT 节点通过 GetChildrenForInspector(true) 获取缓存子节点 | config.cacheNodes 为 false 时不使用 cacheChildren | AC-6.2 |
| R-23 | 边界 | IsCulledByRect | 节点 rect 与 clipRect/viewportRect 不相交时返回 !hasInspectableChildren | hasInspectableChildren 考虑 disappearingChildren_ 和 cacheChildren | AC-6.3 |
| R-24 | 行为 | DumpSimplifyCommonInfo | $rect 必写；compid/active/visible/opacity/backgroundColor 仅在非默认值时写入 | opacity 仅在 !NearEqual(opacity, 1.0f) 时写入 | AC-7.1 |
| R-25 | 行为 | DumpSimplifyCommonInfoOnlyForParamConfig | config.interactionInfo 控制 clickable/longClickable/focusable/scrollable/editable；config.accessibilityInfo 控制 accessibilityContent | gestureEventHub / focusHub / accessibilityProperty_ 为空时跳过对应字段 | AC-7.2 |
| R-26 | 行为 | DumpSimplifySafeAreaInfo | 输出 SafeAreaExpandOpts/SafeAreaInsets/SelfAdjust/ParentSelfAdjust；PAGE_ETS_TAG 额外输出 KeyboardInset/IgnoreSafeArea 等 6 项 | SelfAdjust/ParentSelfAdjust 仅在 SelfOrParentExpansive 且非默认零矩形时输出 | AC-7.3 |
| R-27 | 行为 | InspectorTreeCollector 任务归零回调 | taskNum_ 减至 0 时调用 onResultFunc_(root_->ToString())，重置 root_ | root_ 为空或 onResultFunc_ 为空时不回调 | AC-8.1 |
| R-28 | 边界 | InspectorTreeCollector 并发保护 | isBackground_ 时 mutex_ 保护 taskNum_ 操作；回调后在 UI 线程清空 cacheNodes_ | isBackground_==false 时无锁 | AC-8.1 / AC-8.2 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.4 / R-1..R-5 | 代码评审 | simplified_inspector.cpp:277-481（GetInspector / Step1 / Step2 / GetInspectorChildren / CheckNodeRect） |
| VM-2 | AC-2.1..2.3 / R-6..R-9 | 代码评审 | simplified_inspector.cpp:526-698（GetInspectorAsync / GetInspectorBackgroundAsync / GetInspectorTreeNode），inspector_tree_collector.cpp:80-83（RetainNode） |
| VM-3 | AC-3.1..3.3 / R-10..R-13 | 代码评审 | simplified_inspector.cpp:92-175,700-758（ParseCommandParam / ScrollToTarget / ExecuteUICommand / ExecuteWebScrollCommand） |
| VM-4 | AC-4.1..4.2 / R-14..R-15 | 代码评审 | simplified_inspector.cpp:760-824（GetComponentImageInfo / GetImagePixelMap / GetComponentSnapshot） |
| VM-5 | AC-5.1..5.3 / R-16..R-18 | 代码评审 | ui_node.cpp:1495-1517,1742-1769（DumpSimplifyTreeBase / Node / Tree） |
| VM-6 | AC-6.1..6.3 / R-19..R-23 | 代码评审 | ui_node.cpp:1519-1608,1610-1740（RectCullingState / CreateRectCullingState / IsCulledByRect / DumpSimplifyTreeWithParamConfig 系列） |
| VM-7 | AC-7.1..7.3 / R-24..R-26 | 代码评审 | frame_node.cpp:1396-1500（DumpSimplifyCommonInfo / OnlyForParamConfig / SafeAreaInfo） |
| VM-8 | AC-8.1..8.2 / R-27..R-28 | 代码评审 | inspector_tree_collector.cpp:27-68,80-89（IncreaseTaskNum / DecreaseTaskNum / UpdateTaskNum / RetainNode） |

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
| SimplifiedInspector 生命周期 | 继承 enable_shared_from_this，支持异步任务捕获自身引用，生命周期由 shared_ptr 管理 | AC-2.1 / AC-2.2 |
| 三构造模式互斥 | TreeParams 全树 / UICommandParams 命令执行 / ComponentParams 单组件截图，inspectorCfg_ 仅 TreeParams 构造初始化 | AC-1.1 / AC-3.1 / AC-4.1 |
| InspectorTreeCollector 任务计数同步 | 主采集 IncreaseTaskNum，Web 异步子任务额外 IncreaseTaskNum，归零时触发统一回调 | AC-8.1 |
| 后台采集节点缓存 | BACKGROUND 线程构建 SimplifiedInspectorTree 持有 WeakPtr，InspectorTreeCollector::cacheNodes_ RetainNode 保留 RefPtr | AC-2.3 |
| ParamConfig 驱动核心入口 | onlyNeedVisible 控制矩形/不透明度剔除，dumpChecker 回调控制节点过滤策略 | AC-6.1 |
| FrameNode 简化信息三层分发 | DumpSimplifyCommonInfo（无条件）/ DumpSimplifyCommonInfoOnlyForParamConfig（config 门控）/ DumpSimplifySafeAreaInfo（安全区域） | AC-7.1 / AC-7.2 / AC-7.3 |
| AceContainer 入口委托 | DumpSimplifyTreeWithParamConfig 委托 PipelineContext::GetComponentOverlayInspector，支持 isInSubWindow | AC-7.1 |

## 非性能需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | rectCulling/minOpacity 剔除使输出为 O(visible_nodes) | 代码评审 | 代码审查 |
| 内存安全 | InspectorTreeCollector::cacheNodes_ 缓存 RefPtr 防释放，回调后 UI 线程清空 | 代码评审 | 代码审查 |
| 线程安全 | InspectorTreeCollector isBackground_ 下 mutex_ 保护 taskNum_/root_ | 代码评审 | 代码审查 |
| 可观测 | 简化树含 $rect/active/visible/opacity/backgroundColor/compid | 代码评审 | 代码审查 |
| 鲁棒性 | GetNodeById BFS 空 node 返回 nullptr；无效 JSON 返回 ERR_INVALID_PARAM | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | DumpSimplifyCommonInfoOnlyForParamConfig 输出 accessibilityContent | accessibilityInfo 门控 |
| 大字体 | 否 | 简化树输出不受字体缩放影响 | — |
| 深色模式 | 否 | 简化树输出不含颜色模式语义 | — |
| 多窗口 | 是 | AceContainer 支持 isInSubWindow 区分主窗口与子窗口 | GetInspectorBackgroundAsync |
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
- [x] 兼容性声明覆盖编译配置/数据结构/跨平台/输出格式四个维度
- [x] 无 TODO / TBD / 待定 占位符

## context-references

```yaml
references:
  - path: frameworks/core/components_ng/base/simplified_inspector.h
    lines: 28-33
    description: SimplifiedInspector 类声明 + enable_shared_from_this + 三构造函数
  - path: frameworks/core/components_ng/base/simplified_inspector.h
    lines: 34-41
    description: GetInspector / GetInspectorAsync / GetInspectorBackgroundAsync / ExecuteUICommand / GetComponentImageInfo / TestScrollToTarget 公有接口
  - path: frameworks/core/components_ng/base/simplified_inspector.h
    lines: 44-47
    description: SimplifiedInspectorTree 内部结构：WeakPtr<UINode> + children 链表
  - path: frameworks/core/components_ng/base/simplified_inspector.h
    lines: 48-66
    description: 私有方法声明：GetInspectorStep1/Step2、GetFrameNodeChildren、GetInspectorChildren、GetSpanInspector、FillInspectorAttrs、CheckNodeRect、GetInspectorTreeNode/Children/Background、ExecuteWebScrollCommand、GetImagePixelMap、GetComponentSnapshot
  - path: frameworks/core/components_ng/base/simplified_inspector.h
    lines: 67-77
    description: 私有成员：deviceRect_、containerId_、pageId_、params_、commandParams_、componentParams_、inspectorCfg_、size_、isAsync_、isBackground_、collector_
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 44-66
    description: JSON 键常量：$type/$ID/$rect/$attrs/root/width/height/$resolution/$children/bundleName/ability/pageUrl/navDstName/id/label/content/enabled/opacity/zindex/visibility/$childrenCount
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 67-82
    description: KEY_CODE、ERR_OK=0/ERR_INVALID_PARAM=101/ERR_NOT_FOUND_TARGET_NODE=102/ERR_NOT_FOUND_SCROLLABLE_NODE=103、MODE_IMAGE_PIXELMAP=1/MODE_COMPONENT_SNAPSHOT=2/MODE_IMAGE_SNAPSHOT=3、TargetType 枚举
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 84-114
    description: ScrollCommand 结构 + ParseCommandParam JSON 解析
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 116-137
    description: GetNodeById BFS 遍历查找
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 139-175
    description: IsScrollable / FindParentScrollable / ScrollToTarget
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 177-232
    description: GetWebLangIfActive / GetActiveWebNodeLang / GetCurrentWebLang
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 250-261
    description: 三构造模式实现
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 263-275
    description: GetOverlayNode：获取 stage 兄弟 overlay 节点
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 277-294
    description: GetInspector 同步采集入口
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 296-345
    description: GetInspectorStep1 / GetInspectorStep2
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 347-371
    description: GetFrameNodeChildren：节点过滤 + RetainNode
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 373-466
    description: GetInspectorChildren / GetSpanInspector / FillInspectorAttrs
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 468-481
    description: CheckNodeRect：paintRect 空 + deviceRect_ 相交检查
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 483-524
    description: GetWebContentIfNeed：Web 无障碍 / JS 异步执行 + IncreaseTaskNum
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 526-546
    description: GetInspectorAsync：PREVIEW/ACE_UNITTEST 条件保护
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 548-601
    description: GetInspectorBackgroundAsync：BACKGROUND 线程序列化
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 603-698
    description: GetInspectorTreeNode / Children / GetInspectorChildrenBackground
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 700-758
    description: ExecuteUICommand / ExecuteWebScrollCommand
  - path: frameworks/core/components_ng/base/simplified_inspector.cpp
    lines: 760-824
    description: GetComponentImageInfo / GetImagePixelMap / GetComponentSnapshot
  - path: frameworks/core/components_ng/base/ui_node.h
    lines: 354-360
    description: DumpSimplifyTreeBase / DumpSimplifyTree / DumpSimplifyTreeNode / DumpSimplifyTreeWithParamConfig 声明
  - path: frameworks/core/components_ng/base/ui_node.h
    lines: 1235-1237
    description: DumpSimplifyInfo / DumpSimplifyInfoOnlyForParamConfig 虚函数声明
  - path: frameworks/core/components_ng/base/ui_node.h
    lines: 1309-1317
    description: RectCullingState 前向声明 + DumpSimplifyTreeWithParamConfigInner / CreateRectCullingState / CreateChildRectCullingState / IsCulledByRect / HasInspectableChildrenForRectCulling 私有声明
  - path: frameworks/core/components_ng/base/ui_node.cpp
    lines: 46-50
    description: RectCullingState 定义：enabled / viewportRect / clipRect
  - path: frameworks/core/components_ng/base/ui_node.cpp
    lines: 53-61
    description: GetNodeOpacityValue 工具函数
  - path: frameworks/core/components_ng/base/ui_node.cpp
    lines: 1495-1517
    description: DumpSimplifyTreeBase / DumpSimplifyTreeNode / DumpSimplifyInfoWithParamConfig
  - path: frameworks/core/components_ng/base/ui_node.cpp
    lines: 1519-1608
    description: CreateRectCullingState / CreateChildRectCullingState / HasInspectableChildrenForRectCulling / IsCulledByRect
  - path: frameworks/core/components_ng/base/ui_node.cpp
    lines: 1610-1740
    description: DumpSimplifyTreeWithParamConfigInner / DumpSimplifyTreeWithParamConfig
  - path: frameworks/core/components_ng/base/ui_node.cpp
    lines: 1742-1769
    description: DumpSimplifyTree 递归遍历
  - path: frameworks/core/components_ng/base/frame_node.h
    lines: 1698-1701
    description: DumpSimplifyCommonInfo / DumpSimplifyCommonInfoOnlyForParamConfig / DumpSimplifySafeAreaInfo / DumpSimplifyOverlayInfo 声明
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 1396-1417
    description: DumpSimplifyCommonInfo 实现
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 1419-1440
    description: DumpSimplifyCommonInfoOnlyForParamConfig 实现
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 1467-1500
    description: DumpSimplifySafeAreaInfo 实现
  - path: frameworks/core/components_ng/base/frame_node.cpp
    lines: 1502-1512
    description: DumpSimplifyOverlayInfo 实现
  - path: adapter/ohos/entrance/ace_container.cpp
    lines: 2593-2600
    description: DumpSimplifyTreeWithParamConfig 委托 GetComponentOverlayInspector
  - path: adapter/ohos/entrance/ace_container.h
    lines: 377-378
    description: DumpSimplifyTreeWithParamConfig override 声明
  - path: frameworks/core/pipeline_ng/pipeline_context.h
    lines: 1015-1016
    description: GetComponentOverlayInspector 声明
  - path: frameworks/core/common/recorder/inspector_tree_collector.h
    lines: 28-50
    description: InspectorTreeCollector 类声明
  - path: frameworks/core/common/recorder/inspector_tree_collector.cpp
    lines: 20-25
    description: 构造函数：callback + isBackground
  - path: frameworks/core/common/recorder/inspector_tree_collector.cpp
    lines: 27-68
    description: IncreaseTaskNum / DecreaseTaskNum / UpdateTaskNum：mutex 保护 + taskNum_==0 回调 + cacheNodes_ 清理
  - path: frameworks/core/common/recorder/inspector_tree_collector.cpp
    lines: 70-89
    description: CreateJson / GetJson / RetainNode / SetTaskExecutor
  - path: interfaces/inner_api/ace/ui_event_observer.h
    lines: 32-33
    description: OnInspectorTreeResult / UICommandResult 回调类型
  - path: interfaces/inner_api/ace/ui_event_observer.h
    lines: 35-46
    description: InspectorInfoType / InspectorPageType 枚举
  - path: interfaces/inner_api/ace/ui_event_observer.h
    lines: 47-49
    description: UICommandParams：params 字符串
  - path: interfaces/inner_api/ace/ui_event_observer.h
    lines: 51-66
    description: TreeParams：14 个布尔/枚举/整型/字符串字段
  - path: interfaces/inner_api/ace/ui_event_observer.h
    lines: 68-76
    description: ComponentParams：mode/aceId + ComponentResult：isOk/callback
  - path: interfaces/inner_api/ui_session/param_config.h
    lines: 23-31
    description: ParamConfig：interactionInfo/accessibilityInfo/cacheNodes/withWeb/withUIExtension/rectCulling/minOpacity
  - path: interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h
    lines: 73-76
    description: InspectorConfig：contentOnly/callingOnMain
```
