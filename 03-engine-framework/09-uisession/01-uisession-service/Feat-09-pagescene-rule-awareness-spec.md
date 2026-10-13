# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | PageScene 规则感知与搜索功能识别 |
| 特性编号 | Func-03-09-01-Feat-09 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | OpenHarmony-7.1-Release |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |

PageScene 是 UISession 提供的页面场景感知能力。本规格定义文本编辑场景检测、搜索功能识别，以及规则注册、事件上报和生命周期管理。文本编辑场景通过 TEXT_EDITOR / COUNT_GTE 规则判断输入控件数量；搜索功能通过顶部页面关键区域内的关键词、Inspector ID 模糊匹配或五类控件特征识别。

搜索点击识别以开发者 onClick/onTouch 实际执行为前提，优先精确匹配响应控件自身的 Inspector ID，未命中时按局部区域或关键词回退。搜索存在性与点击共享页面稳定门控，同一 SA 最多注册两个独立规则集，命中结果按事件聚合上报。

搜索识别覆盖当前 UIContent 的主页面、类弹窗和 ArkUI 子窗，排除 Web、UIExtension 及其他 UIContent/独立窗口。文本编辑场景的子来源边界见 AC-6.x；IPC 鉴权沿用 Feat-01，页面稳定点与 Feat-06 共用。

## 本次变更范围（Delta）

> 本次在现有 Feat-09 中补充搜索识别，不新增 FuncID / FeatID。AC-1.x～AC-6.x 保留存量编号；搜索增量使用 AC-7.x～AC-18.x。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | TEXT_EDITOR 首批场景规则规格 | 当前页面或子内容源中存在 ≥2 文本输入类控件时上报命中事件 |
| ADDED | COUNT_GTE 规则运算符规格 | 规则条件操作符 COUNT Greater Than or Equal，命中节点数量 ≥ 阈值时匹配 |
| ADDED | ruleJson / webRules 预留规格 | ruleJson 由 SA 下发，webRules 为 Web 专用预留字段，宿主原样透传给 Web 控件 |
| ADDED | 上报结果结构规格 | currentPageName + source.type + nodes[].rect/focusable/text(includeText=true) |
| ADDED | TEXT_EDITOR_EXIT 退出上报规格 | 同一规则已上报过命中事件后不再满足规则时上报 TEXT_EDITOR_EXIT（matched=false） |
| ADDED | ContentChangeManager 收敛规格 | OnVsyncEnd FlushPageSceneNodeChanged 收敛检测，滚动/过渡/转场未稳定时延后 |
| ADDED | 与 ContentChange 共用稳定上报点规格 | 页面切换/滚动结束/Swiper切换/弹窗显示隐藏为共用稳定点 |
| MODIFIED | 纠正 PageScene 注册门控和接口签名 | 当前实现使用 pageSceneRuleRegistered_（atomic<bool>）；SA 接口接收 ruleJson/callback，注销接收 ruleSetId |
| ADDED | SavePageSceneDetectFunction 回调注册规格 | UIContentImpl 注册 PageScene 检测回调至 UiSessionManager |
| ADDED | 搜索存在性识别场景 | 按顶部页面关键区域内的关键词（子串、英文忽略大小写）或五类关键控件特征判断页面是否具备搜索功能；关键区域内节点 Inspector ID 按子串、英文忽略大小写模糊匹配参与关键词判定 |
| ADDED | 关键词与控件特征配置 | 每条 rule 必填关键区域（≥1，≤5）、关键词（≤5，单关键词 ≤20 UTF-8 字节）、Image/Swiper/Search/Button/TextInput 特征（`maxSize`/`maxRatio`/`autoPlay`） |
| ADDED | `inspectorIds` 精确匹配 | 每条 rule 可选字符串列表；存在性扫描按子串模糊匹配，点击仅对实际响应控件自身 Inspector ID 区分大小写完整精确匹配，命中时跳过区域/关键词 |
| ADDED | 页面/子窗范围 | Navigation 顶部 NavDestination、Router 顶部 pageUrl；主页面、类弹窗与当前 UIContent 的 ArkUI 子窗参与，子窗 Rect 映射主窗坐标，PageName=`<主窗口PageName>+Dialog` |
| ADDED | presence 状态机 | 首次具备搜索功能上报一次 true；特征消失/路由离开/后台上报一次 false；恢复后允许再次 true |
| MODIFIED | PageScene 事件载荷 | true/点击/false 三类事件字段；多规则/多 ruleSet 命中合并为一份 JSON、一次异步 IPC，report 端按 ruleSet 分别 callback |
| MODIFIED | 规则集生命周期 | 支持同一 SA 最多两个不同 `ruleSetId` 独立注册、独立 callback、幂等注销与 SA 死亡清理 |

## 输入文档

- 关联设计：[UISession 服务设计](design.md)。
- 用户提供的搜索识别提案：[pagesceneintake / proposal.md](https://gitcode.com/lushi871202/arkui_ace_engine/blob/pagesceneintake/.codespec/changes/ui-session-page-scene-awareness-search-function-detection/proposal.md)。
- 需求入口：[design-docs PR #807](https://gitcode.com/OpenHarmonyAI/design-docs/pull/807)。本次实际读取工作区 `design-docs` 归档 `codespec/changes/arkui_ace_engine/20260828398121/{proposal,spec,design,execution-plan}.md` 及 `metadata_tracking.yaml`，版本为 `cb29cc06bf1ac5739a280f4f017b3027311c6487`；未核验远端 PR head。
- 需求基线：2026-09-29 已批准 Define，需求 RR-30095586；归档明确映射 `03-09-01/Feat-09`。
- 实现对照：工作区 `arkui_ace_engine` 提交 `8742cdf09ee61f7f8acecd69e74974598b1eff09`（page session）。归档交付元数据另记录 CR 146045 / `45336e64214b953f62e153c2eded9c4614411a7e`，状态 review；二者分别记录，不假定为同一提交，也不据此声称已合入。
- 主要源码（路径相对 ace_engine，按上述本地提交核对）：
  - `interfaces/inner_api/ui_session/ui_content_service_interface.h`、`ui_content_errors.h`：SA 接口、callback 和错误码。
  - `interfaces/inner_api/ui_session/ui_session_manager.h`：PageScene 注册开关和检测回调。
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp`：规则校验、双规则集、定向上报与清理。
  - `frameworks/core/components_ng/manager/page_scene/page_scene_rule_manager.cpp`：规则解析、presence 状态与点击候选。
  - 同目录 `search_scene_context_collector.cpp`、`search_scene_snapshot.cpp`、`search_scene_matcher.cpp`、`search_scene_click_matcher.cpp`：页面/子窗、快照、匹配与点击回退。
  - `frameworks/core/components_ng/manager/content_change_manager/content_change_manager.cpp`：稳定点门控。
  - `adapter/ohos/entrance/ui_content_impl.cpp`、`ui_session/ui_report_stub.cpp`：UI 线程调度、事件 JSON 与 callback 路由。

## 用户故事

### US-1: TEXT_EDITOR 场景规则检测

**作为** SA 工具开发者
**我想要** SA 下发 TEXT_EDITOR 规则后，ArkUI 侧检测当前页面是否存在 ≥2 文本输入类控件，命中时上报 TEXT_EDITOR 事件
**以便** SA 工具可感知页面编辑场景，自动触发辅助能力（如翻译、输入增强）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN RegisterPageSceneRules 下发 TEXT_EDITOR 规则（ruleJson 包含 `condition.operator=COUNT_GTE`、`condition.threshold=2`、`selector.nodeTypes` 指定输入控件类型） THEN ArkUI 侧接受规则并在页面稳定点检测匹配。来源：KB 扩展指南设计边界 3 | 正常 |
| AC-1.2 | WHEN 当前页面存在 ≥2 文本输入类控件（TextInput / TextArea / Search / RichEditor） THEN 上报 TEXT_EDITOR 命中事件，包含 currentPageName、source.type=ARKUI、nodes[].rect 和 focusable。来源：KB 扩展指南设计边界 5 | 正常 |
| AC-1.3 | WHEN 当前页面仅存在 0 或 1 个文本输入类控件 THEN 不上报 TEXT_EDITOR 命中事件。来源：KB 扩展指南设计边界 3 | 边界 |
| AC-1.4 | WHEN `report.includeText=true` 在 TEXT_EDITOR 规则中指定 THEN nodes[] 分别携带 text 和 placeholder，text 为当前输入文本，placeholder 为控件占位提示；输入为空时 text 允许为空。来源：`PageSceneRuleManager::BuildSceneJson / FillInputInfo` | 正常 |

### US-2: TEXT_EDITOR_EXIT 退出上报

**作为** SA 工具开发者
**我想要** 同一 TEXT_EDITOR 规则已上报命中后，页面不再满足规则时上报 TEXT_EDITOR_EXIT 退出事件
**以便** SA 工具可正确维护场景状态，不再触发不需要的辅助能力

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 同一 TEXT_EDITOR 规则已上报过命中事件且后续页面稳定点检测发现不再满足规则 THEN 上报 TEXT_EDITOR_EXIT 事件，sceneType=TEXT_EDITOR、matched=false、matchedCount=当前参与统计的输入控件数量。来源：KB 扩展指南设计边界 8 | 正常 |
| AC-2.2 | WHEN 退出事件上报后 THEN 清理命中态，后续连续未命中不重复上报退出事件。来源：KB 扩展指南设计边界 8 | 恢复 |
| AC-2.3 | WHEN 主动 GetPageScene 未命中结果 THEN 使用 eventName=TEXT_EDITOR 而非 TEXT_EDITOR_EXIT。来源：KB 扩展指南设计边界 8 | 边界 |

### US-3: 页面场景规则化感知检测收敛至页面稳定点

**作为** 框架稳定性维护者
**我想要** 页面场景规则化感知检测统一收敛到页面稳定点（OnVsyncEnd FlushPageSceneNodeChanged），滚动/过渡/转场未稳定时延后检测
**以便** 页面场景规则化感知检测不影响帧率和渲染性能，且仅在页面内容真正稳定后触发

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN ArkUI 侧输入类节点上下树变化 THEN 先记为待检测规则，真正检测统一收敛到 ContentChangeManager::OnVsyncEnd 调用 FlushPageSceneNodeChanged。来源：KB 扩展指南设计边界 7 | 正常 |
| AC-3.2 | WHEN 滚动、Swiper 滚动或页面转场未稳定 THEN FlushPageSceneNodeChanged 延后执行，直到页面稳定点触发。来源：KB 扩展指南设计边界 7 | 正常 |
| AC-3.3 | WHEN Pipeline 只调用 ContentChangeManager::OnVsyncEnd THEN 不直接依赖页面场景规则化感知规则判断。来源：KB 扩展指南设计边界 7 | 正常 |

### US-4: 页面场景规则化感知与 ContentChange 共用稳定上报点

**作为** 框架设计维护者
**我想要** 页面场景规则化感知复用 ContentChange 的页面级稳定上报点：页面切换结束、滚动结束、Swiper/Tabs 切换结束、弹窗显示隐藏结束
**以便** 即使只注册页面场景规则化感知未注册 ContentChange，这些稳定点也会触发待检测规则

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 只注册页面场景规则化感知未注册 ContentChange THEN 页面切换/滚动结束/Swiper切换/弹窗显示隐藏等稳定点仍触发待检测规则。来源：KB 扩展指南设计边界 9 | 正常 |
| AC-4.2 | WHEN Text/Image 具体控件 ContentChange 事件 THEN 仅在 ContentChange 注册后生效，不作为页面场景规则化感知-only 的检测入口。来源：KB 扩展指南设计边界 9 | 边界 |

### US-5: RegisterPageSceneRules 门控与回调注册

**作为** SA 工具开发者
**我想要** RegisterPageSceneRules 维护按进程归属的规则和原子注册开关，SavePageSceneDetectFunction 注册 UI 线程回调
**以便** 多个 SA 进程可同时注册页面场景规则化感知规则，且检测回调在 UI 线程执行避免跨线程直接访问 Pipeline

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 合法规则注册成功 THEN 保存对应进程的规则并置 pageSceneRuleRegistered_=true；非法配置不得开启检测或覆盖已有规则。来源：`UiSessionManagerOhos::RegisterPageSceneRules / RegisterSearchPageSceneRules` | 正常 |
| AC-5.2 | WHEN 最后一个有效规则集注销完成 THEN 关闭 PageScene 检测；仍有其他有效规则集时继续检测，重复清理不得关闭其他有效订阅。来源：`UiSessionManagerOhos::UnregisterPageSceneRules / UnregisterSearchPageSceneRules` | 正常 |
| AC-5.3 | WHEN SavePageSceneDetectFunction 保存的检测回调被调用 THEN UIContentImpl 通过 TaskExecutor 将节点访问和匹配任务投递到 UI 线程。来源：`UIContentImpl::InitUISessionManagerCallbacks` | 正常 |

### US-6: ruleJson 规则下发与 Web/UIExtension 透传预留

**作为** SA 工具开发者
**我想要** 规则由 SA 通过 ruleJson 下发，ruleJson.webRules 为 Web 专用预留字段
**以便** SA 可灵活下发不同场景规则，Web 控件接收宿主透传的规则生命周期请求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN SA 下发 ruleJson THEN 首版条件操作符 COUNT_GTE 表示命中节点数量 ≥ 阈值。来源：KB 扩展指南设计边界 4 | 正常 |
| AC-6.2 | WHEN ruleJson 包含 webRules THEN 为 Web 专用预留字段，宿主原样透传给 Web 控件，具体规格不在当前特性中设计。来源：KB 扩展指南设计边界 4 | 边界 |
| AC-6.3 | WHEN UIExtension 接收宿主透传 THEN 仅作为子来源接收规则生命周期请求，不设计内部匹配、命中回传和 source.type=UI_EXTENSION 上报。来源：KB 扩展指南设计边界 6 | 边界 |

### US-7：配置页面、区域、关键词和控件特征识别搜索功能

**作为** UISession 系统 SA，
**我想要**配置 Navigation/Router 页面、关键区域、关键词和五类关键控件特征，
**以便**跨应用判断当前顶部页面是否具备搜索功能并维护其状态。

**关联 AC：** AC-7.1～AC-7.19、AC-8.1～AC-8.11、AC-9.1～AC-9.10、AC-10.1～AC-10.7、AC-15.1～AC-15.6、AC-18.1～AC-18.4

### US-8：用 Inspector ID 精确识别搜索入口并在未命中时回退

**作为** UISession 系统 SA，
**我想要**在实际 `onClick`/`onTouch` 响应后用响应控件自身 Inspector ID 精确识别搜索入口，未命中时再按区域或关键词回退，
**以便**列表关键入口滚动到任意位置仍能准确上报用户搜索操作。

**关联 AC：** AC-13.1～AC-13.13、AC-14.1～AC-14.7

### US-9：保证聚合、生命周期和性能受控

**作为** UISession 能力维护者，
**我想要**事件聚合、规则生命周期、清理和性能指标均有确定行为，
**以便**能力稳定交付且不给未配置应用带来可感知影响。

**关联 AC：** AC-11.1～AC-11.3、AC-12.1～AC-12.5、AC-14.1～AC-14.7、AC-15.1～AC-15.6、AC-16.1～AC-16.6、AC-17.1～AC-17.6、AC-18.1～AC-18.6

## 搜索功能识别验收标准（AC-7～AC-18）

以下每条 AC 是一个独立场景。注册用例除指定变项外满足规则定义中的约束；操作用例只统计本次操作对应的事件，排除注册、查询和场景退出事件。正向用例保持连接与 callback 有效，反向用例在操作处理完成并达到稳定点后核对事件数，不能只凭短时未收到就判断通过。

| AC 编号 | 验收标准（GIVEN / WHEN / THEN） | 可观察表面 | 类型 |
|---------|----------------------------------|------------|------|
| AC-7.1 | GIVEN SA 连接正常、无未完成注册请求，合法配置：1 条 rule，pageType=Navigation+Router 任一、1 区域、1 关键词、1 类控件特征，未配置 `inspectorIds`，ruleSetId 未注册；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `NO_ERROR(0)`，注册成功。 | InnerAPI | 正常 |
| AC-7.2 | GIVEN 除 `inspectorIds` 含空字符串元素外其余配置合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败，已有合法规则及其 callback 不被覆盖。 | InnerAPI | 异常 |
| AC-7.3 | GIVEN 当前 SA 尚有规则集名额，拟注册 ruleSet 含 11 条合法且 ruleId 不同的 rule，每条仅 1 个区域；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 边界 |
| AC-7.4 | GIVEN 当前 SA 已成功注册 ruleSet-A 和 callback-A，新配置复用同一 ruleSetId 并传入 callback-X；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败，已有合法规则及其 callback 不被覆盖。 | InnerAPI | 异常 |
| AC-7.5 | GIVEN 待注册 ruleSet 内两条 rule 使用相同 ruleId，其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 异常 |
| AC-7.6 | GIVEN 待注册 rule 的两个关键区域具有正面积交集，其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 边界 |
| AC-7.7 | GIVEN 当前 SA 尚有规则集名额，拟注册 ruleSet 仅含 1 条 rule，该 rule 含 6 个互不重叠的合法区域；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 边界 |
| AC-7.8 | GIVEN 待注册 rule 的关键词列表含 6 个互不相同的合法关键词（每个 ≤20 UTF-8 字节），其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 边界 |
| AC-7.9 | GIVEN 待注册 rule 含 1 个关键词，按 UTF-8 编码后长度为 21 字节（例如中文 7 个字符），其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败；不允许通过截断多字节序列把非法关键词转为合法值。 | InnerAPI | 国际化/边界 |
| AC-7.10 | GIVEN 除 `inspectorIds` 含数值元素 123 外其余配置合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 异常 |
| AC-7.11 | GIVEN 除 ruleSetId 为空字符串外其余配置合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 异常 |
| AC-7.12 | GIVEN 除一条 rule 的 ruleId 为空字符串外其余配置合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 异常 |
| AC-7.13 | GIVEN 同一 rule 为同一控件类型配置两份特征（例如两份 Image 特征），其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 异常 |
| AC-7.14 | GIVEN `maxSize` 或 `maxRatio` 为非正值、NaN、无穷值或类型错误（如字符串），其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败。 | InnerAPI | 异常 |
| AC-7.15 | GIVEN 同一 SA 已注册两个不同 ruleSet，拟注册第三个不同且其他字段合法的 ruleSet；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败，已有合法规则及其 callback 不被覆盖。 | InnerAPI | 边界 |
| AC-7.16 | GIVEN SA 已注册含 10 条 rule、每条含 5 个互不重叠区域/5 个合法关键词的 ruleSet-A，拟注册不同的 ruleSet-B 也含 10 条 rule、每条含 5 个区域/5 个关键词，其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN ruleSet-B 返回 `NO_ERROR(0)`，两个规则集注册成功，10/5/5 上限分别按每个 ruleSet/每条 rule 计算。 | InnerAPI | 边界 |
| AC-7.17 | GIVEN ruleSet-A 已注册 ruleId=R、区域 Ra，ruleSet-B 未注册且也含 ruleId=R、区域 Rb，Ra 与 Rb 重叠但各自 rule 内无重叠，其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN ruleSet-B 返回 `NO_ERROR(0)`，注册成功，跨 ruleSet 的相同 ruleId/重叠区域以 ruleSetId 组合区分。 | InnerAPI | 边界 |
| AC-7.18 | GIVEN `inspectorIds` 含重复项 `["payButton","payButton"]`，其他字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `NO_ERROR(0)`，注册成功，重复项在注册时归一化去重，后续不会因重复项产生重复事件。 | InnerAPI | 正常 |
| AC-7.19 | GIVEN 待注册 rule 未配置任何关键区域（regions 缺失或为空数组），其余字段合法；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，本次注册整体失败，关键区域为必填项。 | InnerAPI | 异常 |
| AC-8.1 | GIVEN SA 已成功注册含关键词 `搜索` 的 rule，页面匹配，Text 节点位于关键区域内且文本为 `打开搜索功能`；WHEN 页面达到 ContentChange 稳定点且该页面首次具备搜索功能；THEN SA 的 callback 收到且仅收到一条 true 事件，命中证据类型为关键词，携带命中关键词和该 Text 节点 ID/Type/Rect 及 PageName。 | InnerAPI | 正常 |
| AC-8.2 | GIVEN 关键词 `search`，Button 位于关键区域内且按钮文字为 `Search Now`；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中证据类型为关键词（按钮文字）。 | InnerAPI | 正常 |
| AC-8.3 | GIVEN 关键词 `搜索`，Search/TextInput 位于关键区域内且 value 或 placeholder 为 `搜索商品`；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中来源为 placeholder/value。 | InnerAPI | 正常 |
| AC-8.4 | GIVEN 关键词 `search`，关键区域内存在自定义控件，其 Name（JSViewName/CustomTag）为 `SearchBar`；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中来源为自定义控件 Name。 | InnerAPI | 正常 |
| AC-8.5 | GIVEN 关键词 `搜索`，关键区域内存在自定义控件，其自身 Name 不含关键词但子树文本为 `搜索入口`；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中来源为自定义控件子树文本。 | InnerAPI | 正常 |
| AC-8.6 | GIVEN 关键词 `搜索`，关键区域内存在节点，其无障碍描述为 `搜索按钮`；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中来源为无障碍描述。 | InnerAPI | 正常 |
| AC-8.7 | GIVEN 关键词为 `search`，关键区域内 Text 为 `SEARCH`；WHEN 页面稳定且首次命中；THEN 英文忽略大小写按子串匹配命中，收到一条 true 事件。 | InnerAPI | 国际化 |
| AC-8.8 | GIVEN 关键词 `搜索`，滚动容器中文本 `搜索推荐` 仍在树上但已被裁剪出可视区域，其最终可见矩形为空；WHEN 页面稳定；THEN 该文本不参与关键词匹配，不因该节点产生 true 事件。 | InnerAPI | 边界 |
| AC-8.9 | GIVEN 关键区域内存在多个含关键词的节点（Text、Button、Search 各一个），rule 含 1 个关键词；WHEN 页面稳定且首次命中；THEN 关键词查找在首个命中节点后立即停止本轮查找，不因后续节点重复构建证据。 | InnerAPI | 性能/正常 |
| AC-8.10 | GIVEN rule 关键词列表为 `["搜索","search"]`，关键区域内 Text 仅含 `search`；WHEN 页面稳定且首次命中；THEN 多关键词按 OR，任一命中即满足，收到一条 true 事件。 | InnerAPI | 正常 |
| AC-8.11 | GIVEN rule 配置关键区域仅覆盖页面顶部，关键词 `搜索` 只出现在关键区域之外；WHEN 页面稳定；THEN 区域外文本不参与匹配，不产生 true 事件。 | InnerAPI | 边界 |
| AC-9.1 | GIVEN rule 配置 Image 特征 `maxSize={width:40,height:40}`、`maxRatio=2.0`，关键区域内 Image 最终可见宽高为 30×20（中心点落区）；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中证据类型为关键控件，携带该 Image ID/Type/Rect。 | InnerAPI | 正常 |
| AC-9.2 | GIVEN rule 配置 Swiper 特征 `autoPlay=true`，关键区域内 Swiper 的 autoPlay 配置属性为 true 且尺寸/比例满足约束；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中证据为 Swiper 控件。 | InnerAPI | 正常 |
| AC-9.3 | GIVEN rule 配置 Search 特征，关键区域内存在 Search 控件且满足 `maxSize`/`maxRatio` 约束；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中证据为 Search 控件。 | InnerAPI | 正常 |
| AC-9.4 | GIVEN rule 配置 Button 特征，关键区域内存在 Button 控件且满足尺寸/比例约束；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中证据为 Button 控件。 | InnerAPI | 正常 |
| AC-9.5 | GIVEN rule 配置 TextInput 特征，关键区域内存在 TextInput 控件且满足尺寸/比例约束；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，命中证据为 TextInput 控件。 | InnerAPI | 正常 |
| AC-9.6 | GIVEN rule 同时配置 Image 与 Swiper 特征，关键区域内仅 Image 满足、Swiper 不满足；WHEN 页面稳定且首次命中；THEN 不同类型按 OR，Image 命中即满足，收到一条 true 事件。 | InnerAPI | 边界 |
| AC-9.7 | GIVEN rule 配置 Swiper 特征 `autoPlay=true`、`maxSize={width:60,height:60}`、`maxRatio=1.0`，关键区域内 Swiper 满足 autoPlay 但不满足 maxSize；WHEN 页面稳定；THEN 同类型约束按 AND，任一不满足则不命中，不产生 true 事件。 | InnerAPI | 边界 |
| AC-9.8 | GIVEN rule 配置 Button 特征且仅配置 `maxRatio`，关键区域内 Button 最终可见高度为 0；WHEN 页面稳定；THEN 该控件本次不命中，不产生 true 事件。 | InnerAPI | 边界 |
| AC-9.9 | GIVEN rule 配置 Image 特征 `maxRatio=2.0`，关键区域内 Image 最终可见宽高为 40×20（比例恰等于 2.0）；WHEN 页面稳定且首次命中；THEN `maxRatio` 边界包含等于，复用框架通用浮点比较，命中并收到一条 true 事件。 | InnerAPI | 边界 |
| AC-9.10 | GIVEN rule 关键区域为 `[100,100,60,60]`，Image 最终可见矩形为 `[80,80,40,40]`（中心点 (100,100) 恰在区域边界），其他特征满足；WHEN 页面稳定且首次命中；THEN 以最终可见矩形中心点落入区域判定，中心点位于区域内即命中。 | InnerAPI | 几何/边界 |
| AC-10.1 | GIVEN rule 配置 `pageType=Navigation`、`pageName=HomePage`，当前顶部页面为 Navigation 且顶部 NavDestination 名匹配；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，PageName 为该 NavDestination 名。 | InnerAPI | 正常 |
| AC-10.2 | GIVEN rule 配置 `pageType=Router`、`pageName=pages/Home`，当前顶部页面为 Router 且顶部 pageUrl 匹配；WHEN 页面稳定且首次命中；THEN 收到一条 true 事件，PageName 为该 pageUrl。 | InnerAPI | 正常 |
| AC-10.3 | GIVEN rule 命中证据位于类弹窗（实例组件树内部的 Dialog/overlay 分支），其最终可见矩形中心点在关键区域内；WHEN 页面稳定且首次命中；THEN 类弹窗参与识别，收到一条 true 事件。 | InnerAPI | 几何/边界 |
| AC-10.4 | GIVEN 当前 UIContent 存在 ArkUI 独立子窗，子窗内搜索控件在其子窗自身坐标系的 Rect 为 `[0,0,40,40]`，子窗相对主窗口偏移为 `[200,100]`，rule 关键区域在主窗坐标系 `[200,100,60,60]`；WHEN 页面稳定且首次命中；THEN 子窗 Rect 映射到主窗坐标后中心点落入关键区域，收到一条 true 事件。 | InnerAPI | 几何/边界 |
| AC-10.5 | GIVEN 顶部主窗口页面名为 `HomePage`，ArkUI 子窗内命中搜索证据；WHEN 页面稳定且首次命中；THEN 子窗事件 PageName 为 `HomePage+Dialog`。 | InnerAPI | 几何/边界 |
| AC-10.6 | GIVEN 页面无匹配的顶部 NavDestination/pageUrl；WHEN 页面稳定且存在关键词命中；THEN 该 rule 不参与该页面匹配，不产生 true 事件。 | InnerAPI | 边界 |
| AC-10.7 | GIVEN 控件矩形经自身及祖先变换后为 C，窗口有效可见边界为 W，沿祖先链实际生效裁剪矩形为 K1…Kn，按 `V=C∩W∩K1…∩Kn` 计算，V 为空或中心点不在区域内；WHEN 页面稳定；THEN 无参与区域匹配的可见矩形，不产生 true 事件。 | InnerAPI | 几何/边界 |
| AC-11.1 | GIVEN rule 已注册，页面首次具备搜索功能；WHEN 页面达到 ContentChange 稳定点；THEN 上报一次 `hasSearch=true` 事件；同页面后续稳定点证据仍命中时不重复上报。 | InnerAPI | 状态 |
| AC-11.2 | GIVEN 页面已上报 true，命中证据由 Text 切换为 Button（状态仍为具备搜索功能）；WHEN 后续稳定点检测；THEN 命中证据/规则/关键词变化但状态不变时不重复上报 true。 | InnerAPI | 状态 |
| AC-11.3 | GIVEN 页面处于转场、滚动或抛滑；WHEN 该时间段内触发 ContentChange；THEN 不在此时间段内完成搜索存在性扫描和最终上报。 | InnerAPI | 状态 |
| AC-12.1 | GIVEN 页面已上报 true，同一路由页面内搜索特征动态消失；WHEN 下一 ContentChange 稳定点；THEN 上报一次 `hasSearch=false` 退出事件，携带 PageName 及退出的 `ruleSetId/ruleId`；重复退出通知不产生第二条 false。 | InnerAPI | 生命周期 |
| AC-12.2 | GIVEN 页面已上报 true；WHEN 顶部页面路由离开；THEN 上报一次 `hasSearch=false` 退出事件，重复退出通知不产生第二条。 | InnerAPI | 生命周期 |
| AC-12.3 | GIVEN 页面已上报 true；WHEN 应用进入后台；THEN 上报一次 `hasSearch=false` 退出事件；WHEN 应用回到前台且规则仍注册、页面重新具备搜索功能；THEN 无需重新注册，允许再次上报一次 true。 | InnerAPI | 生命周期 |
| AC-12.4 | GIVEN 页面 A 已上报 true，进入具备搜索功能的页面 B；WHEN 路由切换稳定；THEN 先上报 A 的 `hasSearch=false`，再上报 B 的 `hasSearch=true`，顺序不颠倒。 | InnerAPI | 生命周期 |
| AC-12.5 | GIVEN 页面已上报 true 后注册仍有效；WHEN 特征消失、路由离开和后台三种退出入口在同一次离开中先后触发；THEN 该次离开只产生一条 `hasSearch=false` 事件。 | InnerAPI | 生命周期 |
| AC-13.1 | GIVEN SA 已成功注册规则，页面匹配，响应控件满足区域/关键词条件，控件绑定开发者 `onClick`；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN SA 收到且仅收到一条本次搜索点击事件，命中列表包含该 `ruleSetId`/`ruleId`。 | InnerAPI | 正常 |
| AC-13.2 | GIVEN SA 已成功注册规则，页面匹配，响应控件未绑定 onClick/onTouch；WHEN 输入到达控件并处理完成，页面稳定；THEN 未执行开发者回调时不产生候选，SA 不收到该 rule 对应的搜索点击事件。 | InnerAPI | 异常 |
| AC-13.3 | GIVEN 响应控件自身 Inspector ID 为 `paySearchBtn`，`inspectorIds=["paySearchBtn"]`，稳定后控件矩形位于全部关键区域之外且不含关键词；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN Inspector ID 区分大小写完整精确命中，直接上报该 rule 搜索点击事件，不受列表滚动位置影响，命中类型为 Inspector ID。 | InnerAPI | 正常 |
| AC-13.4 | GIVEN 未配置 `inspectorIds`（或响应控件自身 ID 为空），稳定后响应控件子树内候选控件中心点位于关键区域内或候选信息含关键词；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN 从响应控件向下最多 10 层按“区域 OR 关键词”回退，任一命中即上报，命中类型为区域或关键词。 | InnerAPI | 边界 |
| AC-13.5 | GIVEN 响应控件自身 Inspector ID 为 `paySearchBtn`，`inspectorIds=["PAYSEARCHBTN"]`，稳定后无区域/关键词回退命中；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN 大小写差异不命中，SA 不收到该 rule 对应的搜索点击事件。 | InnerAPI | 边界 |
| AC-13.6 | GIVEN 响应控件自身 Inspector ID 为 `paySearchBtn`，`inspectorIds=["pay"]`（仅前缀），稳定后无区域/关键词回退命中；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN 前缀不命中，SA 不收到该 rule 对应的搜索点击事件。 | InnerAPI | 边界 |
| AC-13.7 | GIVEN 响应控件自身 Inspector ID 为 `paySearchBtn`，`inspectorIds=["Search"]`（仅子串），稳定后无区域/关键词回退命中；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN 子串不命中，SA 不收到该 rule 对应的搜索点击事件。 | InnerAPI | 边界 |
| AC-13.8 | GIVEN 响应控件自身 Inspector ID 为 `childBtn`，父节点 ID 为 `paySearchBtn`，`inspectorIds=["paySearchBtn"]`，稳定后无区域/关键词回退命中；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN 祖先节点 ID 不参与匹配，SA 不收到该 rule 对应的搜索点击事件。 | InnerAPI | 边界 |
| AC-13.9 | GIVEN 响应控件自身 Inspector ID 为 `parentBtn`，子节点 ID 为 `paySearchBtn`，`inspectorIds=["paySearchBtn"]`，稳定后无区域/关键词回退命中；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN 后代节点 ID 不参与匹配，SA 不收到该 rule 对应的搜索点击事件。 | InnerAPI | 边界 |
| AC-13.10 | GIVEN 响应控件自身 Inspector ID 为空，内部数值 nodeId 为 12345，`inspectorIds=["12345"]`，稳定后无区域/关键词回退命中；WHEN 响应控件实际执行一次 `onClick`，操作结束且页面稳定；THEN 内部数值 nodeId 不参与 Inspector ID 匹配，SA 不收到该 rule 对应的搜索点击事件。 | InnerAPI | 边界 |
| AC-13.11 | GIVEN 响应控件实际执行 `onClick` 后页面发生滚动/转场（不稳定）；WHEN 滚动/转场进行中；THEN 候选被保留，不稳定期间不产生最终搜索点击事件；WHEN 页面达到稳定点；THEN 稳定后最多消费一次该候选并上报。 | InnerAPI | 状态 |
| AC-13.12 | GIVEN 响应控件同时绑定 onClick/onTouch；WHEN 先后执行两次独立点击，每次实际执行回调并分别结束、达到稳定点；THEN 分别收到两条搜索点击事件，每次各一条，不相互去重。 | InnerAPI | 正常 |
| AC-13.13 | GIVEN rule 配置 `inspectorIds=["paySearchBtn"]`，页面关键区域内存在 Inspector ID 为 `paySearchBtn` 的节点但未触发开发者回调，关键词/控件特征均不命中；WHEN 页面稳定；THEN `inspectorIds` 按子串、英文忽略大小写模糊匹配参与存在性扫描，命中产生一条 true 事件，命中证据类型为关键词（Inspector ID）。 | InnerAPI | 边界 |
| AC-14.1 | GIVEN 页面首次具备搜索功能；WHEN 组织 true 事件；THEN 事件至少携带 `hasSearch=true`、PageName、命中数组（含 `ruleSetId/ruleId`）、命中证据类型（关键词/关键控件）、命中关键词或命中控件 ID/Type/Rect；空字段省略。 | InnerAPI | 正常 |
| AC-14.2 | GIVEN 搜索点击命中；WHEN 组织点击事件；THEN 事件至少携带 `ruleSetId/ruleId`、命中条件类型（Inspector ID/区域/关键词）、命中关键词（仅关键词命中时）、实际响应控件 ID/Type/Rect 和 PageName。 | InnerAPI | 正常 |
| AC-14.3 | GIVEN 页面搜索功能退出；WHEN 组织 false 事件；THEN 事件至少携带 `hasSearch=false`、PageName 及退出的 `ruleSetId/ruleId` 数组，明确退出 rule。 | InnerAPI | 正常 |
| AC-14.4 | GIVEN 同一 ruleSet 中两条不同 rule 对同一页面均命中 true（或同一操作均命中点击）；WHEN 组织事件；THEN 一份 JSON 包含两条 rule 的完整命中信息，应用向 SA 发送一次异步事件 IPC。 | InnerAPI | IPC/并发 |
| AC-14.5 | GIVEN 同一 SA 的 ruleSet-A/B 对同一页面均命中；WHEN 组织事件；THEN 一份合并 JSON 包含两个 ruleSet 的命中信息，应用向 SA 发送一次异步事件 IPC，callback-A/B 各执行一次。 | InnerAPI | IPC/并发 |
| AC-14.6 | GIVEN 页面退出时 ruleSet-A/B 均在该页面命中过 true；WHEN 组织 false 事件；THEN 退出事件通过数组列出 A/B 及其退出的 ruleId，分别触发对应 callback。 | InnerAPI | IPC/并发 |
| AC-14.7 | GIVEN 命中证据为关键词；WHEN 组织事件；THEN 事件携带命中关键词但不携带页面其余文本正文；日志不输出规则 JSON、事件正文或文本/a11y 内容。 | InnerAPI | 数据最小化 |
| AC-15.1 | GIVEN 待注册 rule 的两个关键区域具有正面积交集；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，整体失败，不保留部分规则。 | InnerAPI | 异常 |
| AC-15.2 | GIVEN 待注册 ruleSet 与已注册 ruleSetId 重复（未注销）；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，整体失败，已有合法规则及其 callback 不被覆盖。 | InnerAPI | 异常 |
| AC-15.3 | GIVEN 待注册 rule 的 `maxSize`/`maxRatio` 非法（非正、NaN、无穷值）；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，整体失败。 | InnerAPI | 异常 |
| AC-15.4 | GIVEN 待注册 rule 任一字段类型错误（如 `inspectorIds` 含数值、`autoPlay` 为字符串）；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，整体失败。 | InnerAPI | 异常 |
| AC-15.5 | GIVEN 待注册配置任一容量超限（rule 数、区域数、关键词数、关键词字节长度、ruleSet 数、同类型特征重复）；WHEN 调用 `RegisterPageSceneRules(ruleJson, callback)`；THEN 返回 `PARAM_INVALID(4)`，整体失败。 | InnerAPI | 异常 |
| AC-15.6 | GIVEN 注册校验失败前 SA 已有合法 ruleSet-C；WHEN 发起包含非法项的注册请求；THEN 返回 `PARAM_INVALID(4)`，本次不保留任何部分规则，ruleSet-C 及其 callback 保持可用，可通过 ruleSet-C 独有命中验证原 callback 仍触发。 | InnerAPI | 异常 |
| AC-16.1 | GIVEN ruleSet-A 已注册且匹配中；WHEN 成功调用 `UnregisterPageSceneRules(ruleSetId=A)`；THEN 返回 `NO_ERROR(0)`，立即停止该 ruleSet 的匹配和后续事件；WHEN 注销后再执行合格点击/页面稳定；THEN callback-A 不再收到后续事件，注销本身不生成 false 退出事件。 | InnerAPI | 生命周期 |
| AC-16.2 | GIVEN ruleSet-A/B 均已注册且 SA 进程死亡；WHEN 应用继续执行合格点击和页面稳定；THEN 不向已死亡 SA 上报遗留事件，死亡清理只清理本地注册/pending，不生成场景退出报告，日志不含业务正文。 | InnerAPI | 生命周期 |
| AC-16.3 | GIVEN SA 连接断开后重连；WHEN 重连后执行合格点击；THEN 原注册不自动恢复，SA 需重新注册；重新注册前无该 ruleSet 事件。 | InnerAPI | 生命周期 |
| AC-16.4 | GIVEN 应用到 SA 的共享异步上报通道断开且存在待发送事件；WHEN 尝试发送该事件；THEN 该事件丢弃且不重试，记录不含业务正文的断链日志；清理后不再向该订阅发送事件。 | InnerAPI | 异常 |
| AC-16.5 | GIVEN 一次包含 ruleSet-A/B 的合并事件已送达 SA，共享通道正常；接收侧保留 A 的规则路由但将 callback-A 置空，callback-B 有效；WHEN 接收侧分发该次事件；THEN callback-B 执行一次并获得 B 的命中结果，callback-A 缺失不阻断 B，诊断日志不含业务正文。 | InnerAPI | 异常 |
| AC-16.6 | GIVEN 应用未注册搜索识别规则或 SA 已注销全部 ruleSet；WHEN 页面稳定、点击等事件到达；THEN 按搜索注册状态快速返回，不新增控件树扫描、不进行关键词/控件特征匹配。 | InnerAPI | 兼容 |
| AC-17.1 | GIVEN 应用未注册本特性规则；WHEN 执行正常点击、触摸和页面稳定；THEN 无本特性新增上报，应用原有回调次数和无障碍呈现保持不变。 | InnerAPI | 兼容 |
| AC-17.2 | GIVEN 目标设备已注册规则，典型规模约 500 个节点、最多 5 条规则、每规则最多 5 个区域；WHEN 测量页面稳定后单次搜索存在性扫描耗时并记录 P50/P95/P99；THEN 单次遍历匹配在 10 ms 内完成。 | InnerAPI | 性能 |
| AC-17.3 | GIVEN 目标设备已注册规则；WHEN 测量搜索点击链路相对未配置基准的新增耗时并记录 P50/P95/P99；THEN Inspector ID 命中路径与区域/关键词回退路径（从响应节点向下最多 10 层）的新增处理时延均小于 1 ms。 | InnerAPI | 性能 |
| AC-17.4 | GIVEN 目标设备连接正常；WHEN 测量同步配置 IPC 端到端耗时、异步事件上报端到端耗时并记录 P50/P95/P99；THEN 配置与上报 IPC 均不超过 5 ms。 | InnerAPI | 性能 |
| AC-17.5 | GIVEN 已注册 6～10 条合法规则；WHEN 测量页面扫描耗时；THEN 记录耗时退化曲线，不作为 10 ms 强制指标，但提供诊断统计（扫描节点数、命中早停位置）。 | InnerAPI | 性能/兼容 |
| AC-17.6 | GIVEN 目标设备已注册规则；WHEN 白盒评估 CPU、内存和功耗增量；THEN 无资源可感知增量。 | InnerAPI | 性能 |
| AC-18.1 | GIVEN 页面内容来自 Web 组件或 UIExtension；WHEN 页面稳定；THEN 不参与搜索功能识别，不产生 true 事件。 | InnerAPI | 范围 |
| AC-18.2 | GIVEN 应用处于多窗口或多实例场景；WHEN 页面稳定；THEN 搜索识别以当前 UIContent 主 Container 及其 ArkUI 子 Container 为边界，不使用无过滤的全进程容器遍历混入其他实例。 | InnerAPI | 范围 |
| AC-18.3 | GIVEN 命中证据位于当前应用实例组件树内部的类弹窗场景；WHEN 页面稳定；THEN 类弹窗参与识别，命中按最终可见矩形中心点判定。 | InnerAPI | 范围 |
| AC-18.4 | GIVEN 当前 UIContent 存在 ArkUI 内部框架创建的独立子窗；WHEN 页面稳定；THEN 子窗参与识别，Rect 映射到主窗口坐标后匹配，PageName 为 `<主窗口PageName>+Dialog`。 | InnerAPI | 范围 |
| AC-18.5 | GIVEN Demo 应用覆盖 Navigation/Router、全部关键词信息来源、英文忽略大小写、五类关键控件、`maxSize/maxRatio/autoPlay`、中心点区域命中、ContentChange 稳定门控、true/退出状态、列表滚动后 Inspector ID 精确命中、ID 未命中区域/关键词回退、类弹窗和 ArkUI 独立子窗；WHEN 执行 Demo 验证；THEN 各场景与规则定义一致。 | InnerAPI | 范围/验证 |
| AC-18.6 | GIVEN UT 覆盖 Inspector ID 大小写/前缀/子串/内部 nodeId/父子节点负例、空 ID 和未命中回退、Inspector ID 存在性模糊命中、不可见文本排除、多规则/多 ruleSet、非法配置（含关键区域缺失）、尺寸和比例边界、同操作去重、动态消失、后台切换、SA 死亡清理、事件字段完整性及排除范围；WHEN 执行 UT；THEN 用例全部通过。 | InnerAPI | 范围/验证 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-09 | 集成测试：下发 TEXT_EDITOR 规则 | 代码审查 |
| AC-1.2 | R-2 | TASK-09 | 集成测试：≥2 输入控件页面 | 代码审查 |
| AC-1.3 | R-2 | TASK-09 | 集成测试：0-1 输入控件页面 | 代码审查 |
| AC-1.4 | R-3 | TASK-09 | 集成测试：includeText=true | 代码审查 |
| AC-2.1 | R-4 | TASK-09 | 集成测试：命中→退出 | 代码审查 |
| AC-2.2 | R-4 | TASK-09 | 集成测试：退出后不重复上报 | 代码审查 |
| AC-2.3 | R-4 | TASK-09 | 集成测试：主动 GetPageScene | 代码审查 |
| AC-3.1 | R-5 | TASK-09 | 代码评审：OnVsyncEnd 收敛 | 代码审查 |
| AC-3.2 | R-5 | TASK-09 | 集成测试：滚动中延后 | 代码审查 |
| AC-3.3 | R-5 | TASK-09 | 代码评审 | 代码审查 |
| AC-4.1 | R-6 | TASK-09 | 集成测试：仅页面场景规则化感知注册 | 代码审查 |
| AC-4.2 | R-6 | TASK-09 | 代码评审 | 代码审查 |
| AC-5.1 | R-7 | TASK-09 | 单元测试：注册成功开启检测 | 代码审查 |
| AC-5.2 | R-7 | TASK-09 | 单元测试：最后一个规则集注销关闭检测 | 代码审查 |
| AC-5.3 | R-8 | TASK-09 | 代码评审 | 代码审查 |
| AC-6.1 | R-9 | TASK-09 | 集成测试 | 代码审查 |
| AC-6.2 | R-9 | TASK-09 | 代码评审（预留） | 代码审查 |
| AC-6.3 | R-10 | TASK-09 | 代码评审（预留） | 代码审查 |

### 搜索增量追溯

| AC | 关联规则 | 可观察表面 |
|----|----------|------------|
| AC-7.1、AC-7.16、AC-7.17、AC-7.18 | R-11 | InnerAPI |
| AC-7.2～AC-7.15、AC-7.19、AC-15.1～AC-15.6 | R-12、R-18 | InnerAPI |
| AC-8.1～AC-8.11 | R-13 | InnerAPI |
| AC-9.1～AC-9.10 | R-14 | InnerAPI |
| AC-10.1～AC-10.7 | R-15、R-16、R-17 | InnerAPI |
| AC-11.1～AC-11.3 | R-19 | InnerAPI |
| AC-12.1～AC-12.5 | R-20、R-21 | InnerAPI |
| AC-13.1、AC-13.2、AC-13.12 | R-22 | InnerAPI |
| AC-13.3 | R-23 | InnerAPI |
| AC-13.4～AC-13.11 | R-24 | InnerAPI |
| AC-13.13 | R-23、R-13 | InnerAPI |
| AC-14.1～AC-14.7 | R-25、R-26 | InnerAPI |
| AC-16.1 | R-27 | InnerAPI |
| AC-16.2、AC-16.3 | R-27、R-28 | InnerAPI |
| AC-16.4、AC-16.5 | R-29 | InnerAPI |
| AC-16.6、AC-17.1 | R-30 | InnerAPI |
| AC-17.2～AC-17.6 | R-31 | InnerAPI |
| AC-18.1～AC-18.6 | R-32 | InnerAPI |

### 与需求归档的编号对应

保留归档每条搜索验收项的次编号：归档 `AC-n.m` 对应本文 `AC-(n+6).m`（1≤n≤12）；归档 `R-n` 对应本文 `R-(n+10)`；归档 `VM-n` 对应本文 `VM-(n+6)`；归档 US-1～US-3 对应本文 US-7～US-9。存量 AC-1～AC-6、R-1～R-10、VM-1～VM-6 不重编号。AC-8.4 将原文“搜索 / SearchBar”的不匹配示例改为“search / SearchBar”，按英文忽略大小写子串匹配验收，不引入跨语言翻译。

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | RegisterPageSceneRules 下发 TEXT_EDITOR 规则 | ArkUI 侧接受 ruleJson 并在页面稳定点检测匹配。ruleJson 包含 `condition.operator=COUNT_GTE`、`condition.threshold=2`、`selector.nodeTypes` 指定输入控件类型。 | 仅首版 COUNT_GTE 操作符，后续版本可能扩展其他操作符 | AC-1.1 |
| R-2 | 行为 | TEXT_EDITOR 规则检测 | ≥2 文本输入类控件命中上报 TEXT_EDITOR 事件，0-1 个控件不上报。文本输入类控件包括 TextInput / TextArea / Search / RichEditor。 | 默认不包含输入文本正文，includeText=true 时携带 text | AC-1.2 / AC-1.3 |
| R-3 | 行为 | 上报结果结构 | currentPageName + source.type + nodes[].rect/focusable + (includeText=true: nodes[].text)。text 与 placeholder 分别上报当前输入和占位提示；输入为空时不以 placeholder 替换 text。 | 不设计完整控件树上报，不提供完整树上报开关 | AC-1.4 |
| R-4 | 行为 | TEXT_EDITOR_EXIT 退出上报 | 同一规则已上报命中后不再满足规则时上报 TEXT_EDITOR_EXIT（matched=false, matchedCount=当前输入控件数）。退出上报后清理命中态，连续未命中不重复上报。 | 主动 GetPageScene 未命中使用 eventName=TEXT_EDITOR 而非 TEXT_EDITOR_EXIT | AC-2.1 / AC-2.2 / AC-2.3 |
| R-5 | 行为 | 页面场景规则化感知检测收敛至页面稳定点 | 输入类节点上下树变化先记为待检测规则，真正检测统一收敛到 ContentChangeManager::OnVsyncEnd FlushPageSceneNodeChanged。滚动/过渡/转场未稳定时延后。 | Pipeline 只调用 OnVsyncEnd，不直接依赖页面场景规则化感知规则判断 | AC-3.1 / AC-3.2 / AC-3.3 |
| R-6 | 行为 | 页面场景规则化感知复用 ContentChange 稳定上报点 | 页面切换结束/滚动结束/Swiper切换结束/弹窗显示隐藏结束为共用稳定点。仅注册页面场景规则化感知未注册 ContentChange 时这些稳定点仍触发检测。 | Text/Image 具体控件 ContentChange 事件仅在 ContentChange 注册后生效 | AC-4.1 / AC-4.2 |
| R-7 | 行为 | PageScene 注册门控 | 按进程保存规则，pageSceneRuleRegistered_ 为 atomic<bool>；存在有效规则时开启检测，最后一个规则集清理后关闭。 | 规则生命周期按进程/规则集管理，不以 bool 替代规则表 | AC-5.1 / AC-5.2 |
| R-8 | 行为 | SavePageSceneDetectFunction UI 线程回调 | UIContentImpl 保存检测回调，调用时通过 TaskExecutor 将实际节点访问和匹配投递到 UI 线程。 | 与 InspectorTree/翻译回调的 UI 线程投递模式一致 | AC-5.3 |
| R-9 | 行为 | ruleJson 规则下发 | SA 通过 ruleJson 下发规则，首版操作符 COUNT_GTE。ruleJson.webRules 为 Web 专用预留字段，宿主原样透传给 Web 控件。 | Web 规则具体规格不在当前特性中设计 | AC-6.1 / AC-6.2 |
| R-10 | 边界 | UIExtension 规则透传 | UIExtension 仅作为子来源接收宿主透传的规则生命周期请求。不设计内部匹配、命中回传和 source.type=UI_EXTENSION 上报。 | 当前特性不验证 UIExtension 子来源 | AC-6.3 |

### 搜索识别规则

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-11 | 行为 | SA 注册合法搜索识别 ruleJson | 注册返回 `NO_ERROR` 并参与后续存在性/点击判定 | 同一 SA 最多两个 ruleSet；每 ruleSet ≤10 rule；每 rule 关键区域必填（≥1）且 ≤5 区域/5 关键词；关键词 ≤20 UTF-8 字节；`inspectorIds` 每项非空字符串且注册时去重 | AC-7.1、AC-7.16、AC-7.17、AC-7.18 |
| R-12 | 异常 | ruleJson 含空 ID、关键区域缺失/为空、非法字段/类型、容量超限、同 ruleSet 重复 ruleId、重复 ruleSetId、同 rule 区域重叠、同类型特征重复、非法 `maxSize`/`maxRatio` | 返回 `PARAM_INVALID`，配置整体不生效 | 不部分接受；多字节关键词按编码后字节数整体校验，不截断 | AC-7.2～AC-7.15、AC-7.19、AC-15.1～AC-15.6 |
| R-13 | 行为 | 关键区域内可见文本/按钮文字/placeholder/value/自定义控件 Name/子树文本/a11y/节点 Inspector ID 含任一关键词 | 页面具备搜索功能（关键词证据） | 子串匹配、英文忽略大小写；不可见/被裁剪出可视区文本不参与；Inspector ID 仅按子串模糊匹配参与存在性、不改变点击精确语义；命中即早停；多关键词 OR | AC-8.1～AC-8.11、AC-13.13 |
| R-14 | 行为 | Image/Swiper/Search/Button/TextInput 满足已配置特征且中心点落入关键区域 | 页面具备搜索功能（关键控件证据） | 不同类型 OR、同类型约束 AND；`maxRatio=width/height<=maxRatio` 含等于；最终可见高度 0 不命中；`maxSize`/`maxRatio` 为可选字段 | AC-9.1～AC-9.10 |
| R-15 | 行为 | `pageType=Navigation` | 按顶部 NavDestination 名匹配页面 | 不以拼接字符串直接匹配；无匹配则不参与 | AC-10.1、AC-10.6 |
| R-16 | 行为 | `pageType=Router` | 按顶部 pageUrl 匹配页面 | 无匹配则不参与 | AC-10.2、AC-10.6 |
| R-17 | 几何/范围 | 主页面、类弹窗与当前 UIContent 的 ArkUI 子窗稳定 | 子窗 Rect 映射主窗坐标后参与区域匹配；PageName=`<主窗口PageName>+Dialog` | 不使用无过滤全进程容器遍历 | AC-10.3～AC-10.7、AC-18.3、AC-18.4 |
| R-18 | 异常 | 任一非法配置项存在 | 整组 `PARAM_INVALID` 且不保留部分规则 | 已有合法规则与 callback 保持 | AC-7.2～AC-7.15、AC-15.1～AC-15.6 |
| R-19 | 状态 | 页面稳定且首次具备搜索功能 | 上报一次 true；证据变化状态不变不重复 | 转场/滚动/抛滑期间不扫描不上报 | AC-11.1～AC-11.3 |
| R-20 | 状态 | 特征消失、路由离开或后台 | 上报一次 false；恢复/重新出现允许再 true | 退出至多一次；A false 先于 B true | AC-12.1～AC-12.5 |
| R-21 | 生命周期 | 重复退出入口 | false 幂等去重 | 同一次离开只产出一条 false | AC-12.5 |
| R-22 | 行为 | 开发者 `onClick`/`onTouch` 实际执行 | 产生可去重的搜索点击候选 | 回调未执行不产生候选；同操作去重；两次独立点击分别上报 | AC-13.1、AC-13.2、AC-13.12 |
| R-23 | 行为 | 响应控件自身 Inspector ID 区分大小写完整精确匹配 `inspectorIds` | 该 rule 搜索点击直接命中并跳过区域/关键词 | 不匹配内部 nodeId、前缀、子串、祖先/后代；存在性扫描使用独立子串模糊匹配，不受点击精确语义约束；不旁路页面/回调/去重/稳定门控/合并 | AC-13.3、AC-13.13 |
| R-24 | 行为/边界 | ID 未配置、为空或未命中 | 从响应控件向下最多 10 层按“区域 OR 关键词”回退 | 命中立即返回；禁止全页面回退；不稳定时保留候选稳定后消费一次 | AC-13.4～AC-13.11 |
| R-25 | 行为 | true/点击/false 事件形成 | 字段符合契约，空字段省略 | 不携带回调类型、触摸阶段或原始事件参数 | AC-14.1～AC-14.3 |
| R-26 | IPC/并发 | 多规则/多 ruleSet 命中 | 一份 JSON、一次异步 IPC，按 ruleSet 分别 callback | 退出事件明确退出 rule | AC-14.4～AC-14.7 |
| R-27 | 生命周期 | 注销、SA 死亡、重连 | 停止匹配、幂等清理、按需重注册 | 注销/死亡不上报退出；清理后无遗留事件 | AC-16.1～AC-16.3 |
| R-28 | 生命周期 | SA 死亡 | 本地注册/pending 清理 | 不向已死亡 SA 上报 | AC-16.2、AC-16.3 |
| R-29 | 异常 | IPC 断开或 callback 失败 | 当前事件丢弃不重试；其他 callback 独立处理 | 日志不含业务正文 | AC-16.4、AC-16.5 |
| R-30 | 兼容 | 未注册搜索识别规则 | 按搜索注册状态快速返回，不新增扫描/匹配 | 原应用回调和无障碍呈现不变 | AC-16.6、AC-17.1 |
| R-31 | 性能 | 已注册正常负载 | 满足 10ms/1ms/5ms 及资源预算 | 目标设备 P50/P95/P99；6～10 规则记录退化曲线 | AC-17.2～AC-17.6 |
| R-32 | 范围 | 排除范围验证 | Web/UIExtension/多窗口/多实例不参与；类弹窗与当前 UIContent 的 ArkUI 子窗参与 | Demo/UT 基线覆盖 | AC-18.1～AC-18.6 |

## 搜索规则注册约束

`RegisterPageSceneRules(ruleJson, callback)` 由具备既有 UISession 调用条件的系统 SA 调用。一个 `ruleJson` 表示一个规则集；调用方须保持连接正常、无未完成的注册请求。成功直接以返回 `NO_ERROR(0)` 判定；字段或数量非法返回 `PARAM_INVALID(4)`，本次配置整体拒绝，既有合法规则和 callback 保留。

| 配置项 | 约束 | 非法输入示例 / 结果 |
|---|---|---|
| `ruleSetId` | 非空字符串；同一 SA 最多同时注册 2 个不同规则集；重复注册拒绝 | 第三个不同 ID、重复 ID、空字符串均返回 4 |
| `rules` | 规则数组，每个 ruleSet 最多 10 条；两个 ruleSet 独立计数 | 单集 11 条返回 4；两集各 10 条符合上限 |
| `rules[i].ruleId` | 非空字符串，同一 ruleSet 内唯一；不同 ruleSet 允许复用 | 同集重复返回 4；跨集以 `(ruleSetId, ruleId)` 组合区分 |
| `rules[i].pageType` | `Navigation` 或 `Router`；与 `pageName` 组合匹配顶部页面 | 非法取值返回 4 |
| `rules[i].pageName` | 非空字符串；Navigation 取顶部 NavDestination 名、Router 取顶部 pageUrl | 空字符串返回 4 |
| 关键区域列表 | 每条 rule 必填至少 1 个区域，最多 5 个区域；同一 rule 内区域不得有正面积重叠 | 空区域、单条 6 个区域或同 rule 重叠返回 4；跨 rule/跨 ruleSet 重叠允许 |
| 关键词列表 | 每条 rule 最多 5 个关键词；每个关键词按 UTF-8 编码 ≤20 字节；非空 | 单条 6 个关键词或单关键词超长/为空返回 4 |
| 控件特征 | 同一 rule 每类控件类型（Image/Swiper/Search/Button/TextInput）最多一份特征；`maxSize` 正数宽高、`maxRatio` 正数、`autoPlay` 布尔 | 同类型重复、非正/NaN/无穷值、类型错误返回 4 |
| `inspectorIds` | 每条 rule 可选的字符串列表；每个元素非空；重复项注册时归一化去重；存在性扫描按子串模糊匹配、点击按完整精确匹配 | `[""]`、`[123]` 返回 4 |
| 控件特征匹配关系 | 同类型 `maxSize`/`maxRatio`/`autoPlay` 按 AND；不同类型按 OR；与关键词条件按 OR | — |

## 搜索数据与事件契约

### 规则 JSON（注册输入，完整契约）

以下为需求归档的目标字段契约；实现差异见后文对照表。任一字段违反约束整体返回 `PARAM_INVALID(4)`，不保留部分规则。

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `ruleSetId` | string | 是 | 非空；同一 SA 最多 2 个不同值 |
| `rules` | array | 是 | 1～10 条 |
| `rules[i].ruleId` | string | 是 | 非空；同一 ruleSet 内唯一 |
| `rules[i].pageType` | string | 是 | `"Navigation"` 或 `"Router"` |
| `rules[i].pageName` | string | 是 | 非空；Navigation 取顶部 NavDestination 名、Router 取顶部 pageUrl |
| `rules[i].regions` | array | 是 | 1~5 个；每项 `{x,y,width,height}` 均为数值；同一 rule 内不得有正面积重叠 |
| `rules[i].keywords` | array | 否 | 0~5 个；每项非空字符串且按 UTF-8 编码 ≤20 字节 |
| `rules[i].components` | array | 否 | 每项 `type ∈ {Image,Swiper,Search,Button,TextInput}`；同 rule 内每类 type 最多 1 份；`maxSize.width/height`、`maxRatio` 为正数（NaN/无穷值非法）；`autoPlay` 为布尔（仅 Swiper） |
| `rules[i].inspectorIds` | array | 否 | 每项非空字符串；重复项注册时归一化去重；存在性按子串模糊匹配、点击按完整精确匹配 |

```json
{
  "ruleSetId": "search-set-1",
  "rules": [
    {
      "ruleId": "search-rule-1",
      "pageType": "Navigation",
      "pageName": "HomePage",
      "regions": [ { "x": 0, "y": 0, "width": 360, "height": 80 } ],
      "keywords": [ "search", "搜索" ],
      "components": [
        { "type": "Image", "maxSize": { "width": 48, "height": 48 }, "maxRatio": 2.0 },
        { "type": "Swiper", "autoPlay": true, "maxSize": { "width": 360, "height": 120 }, "maxRatio": 3.0 },
        { "type": "Search", "maxSize": { "width": 360, "height": 56 }, "maxRatio": 8.0 },
        { "type": "Button", "maxSize": { "width": 200, "height": 80 }, "maxRatio": 4.0 },
        { "type": "TextInput", "maxSize": { "width": 360, "height": 56 }, "maxRatio": 8.0 }
      ],
      "inspectorIds": [ "searchEntryBtn", "searchBox" ]
    }
  ]
}
```

### 事件 JSON（输出，完整契约）

三类事件由 `eventType` 区分；多规则/多 ruleSet 命中组织为一份 JSON、一次异步 IPC；report 端从命中数组提取 `ruleSetId` 建立 callback 快照后分别调用。`PageSceneEventCallback` 类型保持 `std::function<void(const std::string&)>`（`ui_content_service_interface.h:41`）。

**true 事件（eventType=`presence`，`hasSearch=true`）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `eventType` | string | `"presence"` |
| `hasSearch` | boolean | `true` |
| `pageName` | string | 主窗口顶部页面名；子窗为 `<主窗口PageName>+Dialog` |
| `hits` | array | 每条命中含 `ruleSetId/ruleId` |
| `hits[].evidenceType` | string | `"keyword"` 或 `"component"` |
| `hits[].source` | string | keyword 证据的命中来源：`text` / `buttonText` / `placeholderValue` / `customName` / `subtreeText` / `accessibility` / `inspectorId` |
| `hits[].matchedKeyword` | string | 仅 keyword 证据；inspectorId 来源时为命中的 Inspector ID |
| `hits[].nodeId/nodeType/rect` | int/string/object | 命中节点 ID/Type/窗口坐标 Rect |

```json
{
  "eventType": "presence",
  "hasSearch": true,
  "pageName": "HomePage",
  "hits": [
    {
      "ruleSetId": "search-set-1",
      "ruleId": "search-rule-1",
      "evidenceType": "keyword",
      "source": "text",
      "matchedKeyword": "搜索",
      "nodeId": 12345,
      "nodeType": "Text",
      "rect": { "x": 0, "y": 0, "width": 200, "height": 40 }
    }
  ]
}
```

**点击事件（eventType=`click`）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `eventType` | string | `"click"` |
| `pageName` | string | 同上 |
| `hits` | array | 每条含 `ruleSetId/ruleId` |
| `hits[].matchType` | string | `"inspectorId"` 或 `"region"` 或 `"keyword"` |
| `hits[].matchedKeyword` | string | 仅 keyword 命中时 |
| `hits[].responseNode` | object | 实际响应控件 `inspectorId/nodeId/type/rect` |

```json
{
  "eventType": "click",
  "pageName": "HomePage",
  "hits": [
    {
      "ruleSetId": "search-set-1",
      "ruleId": "search-rule-1",
      "matchType": "inspectorId",
      "responseNode": {
        "inspectorId": "paySearchBtn",
        "nodeId": 12346,
        "type": "Button",
        "rect": { "x": 100, "y": 200, "width": 80, "height": 40 }
      }
    }
  ]
}
```

**false 事件（eventType=`presence`，`hasSearch=false`）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `eventType` | string | `"presence"` |
| `hasSearch` | boolean | `false` |
| `pageName` | string | 同上 |
| `exits` | array | 退出的 `ruleSetId/ruleId` 数组，明确退出 rule |

```json
{
  "eventType": "presence",
  "hasSearch": false,
  "pageName": "HomePage",
  "exits": [
    { "ruleSetId": "search-set-1", "ruleId": "search-rule-1" }
  ]
}
```

空字段省略；不携带回调类型、触摸阶段或原始事件参数。多 ruleSet 命中时 callback 各自收到同一份合并 JSON 中本 ruleSet 的命中结果。

### 最终可见矩形

搜索配置的 regions、maxSize 与事件 rect 统一使用主窗口坐标系的 vp；此单位依据本地 `SearchSceneSnapshotBuilder::BuildNodeFeature` 的 px→vp 转换补充，验收需覆盖不同 density。子窗偏移先在 px 中映射，再统一转换为 vp，不与旧 TEXT_EDITOR 的 rect 单位混用。

搜索存在性与点击的几何量统一到窗口坐标系。记组件经自身及祖先变换后的矩形为 C，窗口内 root 的有效可见边界为 W，沿祖先链实际生效的裁剪矩形为 K1…Kn，则 `V = C ∩ W ∩ K1 ∩ … ∩ Kn` 为最终可见矩形。祖先没有启用裁剪时，不能仅因其 layout Rect 较小就与它求交；节点或其祖先不可见、未激活，或交集无面积时，没有可参与匹配的可见矩形。中心点取 V 的中心，落区判定包含等于。子窗节点矩形先映射到主窗口坐标再参与计算。现有 `GetTransformRectRelativeToWindowOnlyVisible`（`frame_node.cpp`）只提供可见性与变换累计事实，不进行逐级裁剪求交，实现不得以函数名含 OnlyVisible 省略裁剪。

### 命中语义要点

- 关键词条件与控件特征条件为 OR；命中证据类型区分 `keyword` 与 `component`。
- 搜索存在性扫描将关键区域内节点 Inspector ID 作为关键词来源之一，按子串、英文忽略大小写模糊匹配；`hasSearch=true/false` 由关键词（含 Inspector ID 模糊）或控件特征决定。
- 搜索点击：仅实际执行开发者 `onClick`/`onTouch` 的响应控件形成候选；先精确匹配响应控件自身 Inspector ID，命中即上报；未配置/为空/未命中时才从响应控件向下最多 10 层按“区域 OR 关键词”回退，命中立即返回。
- 每条 rule 必填至少 1 个关键区域；区域缺失或为空返回 `PARAM_INVALID`，存在性与控件特征判定均以关键区域为边界。
- Inspector ID 命中只旁路区域/关键词，不旁路 pageType/pageName、实际回调、同操作去重、稳定门控和事件合并。
- 日志不得输出规则 JSON、事件正文或文本/a11y 内容；只记录长度、节点数、错误类型等非内容诊断信息。

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1..1.4 / R-1 / R-2 / R-3 | 集成测试 | TEXT_EDITOR 规则下发、命中检测、上报结果结构 |
| VM-2 | AC-2.1..2.3 / R-4 | 集成测试 | TEXT_EDITOR_EXIT 退出上报、命中态清理 |
| VM-3 | AC-3.1..3.3 / R-5 | 代码评审 | OnVsyncEnd FlushPageSceneNodeChanged 收敛 |
| VM-4 | AC-4.1 / AC-4.2 / R-6 | 集成测试 | 仅页面场景规则化感知注册时稳定点仍触发 |
| VM-5 | AC-5.1..5.3 / R-7 / R-8 | 单元测试 + 代码评审 | 原子注册开关 + UI 线程调度 |
| VM-6 | AC-6.1..6.3 / R-9 / R-10 | 代码评审 | ruleJson 下发 + Web/UIExtension 预留 |

### 搜索增量验证映射（计划）

下列入口用于后续业务验收；本次仅核对源码和文档，未执行 ace_engine UT、SA 联调或设备性能测试。

| 编号 | 对应规格项 | 测试入口 | 验证方式 | 通过标准 |
| ------ | ------------ | ---------- | ---------- | ---------- |
| VM-7 | AC-7.1～AC-7.19、AC-15.1～AC-15.6 / R-11、R-12、R-18 | `test/unittest/core/manager/page_scene_rule_manager_test_ng.cpp`：搜索规则解析、容量、UTF-8、重叠、重复 ID、双 ruleSet 注册注销 | 单测 + Proxy/Stub 集成 | 合法配置成功；非法配置统一 `PARAM_INVALID`；容量与重叠边界符合规则 |
| VM-8 | AC-8.1～AC-8.11、AC-9.1～AC-9.10 / R-13、R-14 | 关键词来源、大小写、多字节、可见性 UT；五类控件及尺寸/比例/autoPlay 边界 UT | 单测 + 集成 | 任一来源/特征命中均产生正确 true 证据；边界符合规则 |
| VM-9 | AC-10.1～AC-10.7 / R-15、R-16、R-17 | Navigation/Router Demo；变换/裁剪、主窗偏移子窗和 Dialog Demo | 单测 + 集成 | 页面按 pageType 独立匹配；子窗映射后中心点判定正确；PageName 带 `+Dialog` |
| VM-10 | AC-11.1～AC-11.3、AC-12.1～AC-12.5 / R-19、R-20、R-21 | ContentChange 正负例、动态刷新、路由替换、前后台和顺序测试 | 集成 | true/false 去重正确；A false 先于 B true；退出至多一次 |
| VM-11 | AC-13.1～AC-13.13 / R-22、R-23、R-24 | 触屏/鼠标、onClick/onTouch、列表滚动、ID 正反例、区域/关键词回退、CANCEL/长按、稳定门控测试 | 单测 + 集成 | 仅实际回调形成候选；ID 精确命中越区域；未命中时 ≤10 层回退；负例全部不误匹配 |
| VM-12 | AC-14.1～AC-14.7 / R-25、R-26 | JSON schema 断言、双 ruleSet/多 rule 事件字段、一次 IPC 计数 | 集成 | 三类事件字段完整；一份 JSON/一次 IPC；按 ruleSet 分别 callback |
| VM-13 | AC-16.1～AC-16.6 / R-27、R-28、R-29 | 注销、死亡、重连、IPC 故障注入和日志扫描 | 集成 + 故障注入 | 注销/死亡幂等；重连需重注册；失败不重试；日志无正文 |
| VM-14 | AC-17.1～AC-17.6、AC-18.1～AC-18.6 / R-30、R-31、R-32 | 目标设备 P50/P95/P99 benchmark；未配置/配置对照；排除范围与 Demo/UT 清单 | 性能测试 + 集成 | 未配置无新增扫描；10ms/1ms/5ms 达标；排除范围与测试资产符合基线 |

## API 变更分析

### 新增 API

无新增 Public/System API、SDK d.ts 或 IPC 事务。

### 变更/废弃 API

现有 InnerAPI 签名保持不变：`RegisterPageSceneRules` 扩展搜索规则 JSON 和双规则集注册行为，`UnregisterPageSceneRules` 按规则集独立清理，`ReportPageSceneEvent` 扩展搜索事件载荷与聚合规则。无接口废弃；`GetPageScene` 的搜索查询支持情况见 GAP-9。

## 接口规格

### 接口定义

```cpp
using PageSceneEventCallback = std::function<void(const std::string&)>;
virtual int32_t RegisterPageSceneRules(
    const std::string& ruleJson, const PageSceneEventCallback& eventCallback);
virtual int32_t UnregisterPageSceneRules(const std::string& ruleSetId);
virtual int32_t GetPageScene(
    const std::string& ruleJsonOrRuleSetId, const PageSceneEventCallback& eventCallback);
virtual void ReportPageSceneEvent(const std::string& sceneJson, bool isGetResult = false);
```

以上是 `ui_content_service_interface.h` 的 SA 侧接口。服务端 manager 使用的 `processId` 是内部路由上下文，不是调用方传入的请求 id。`ReportPageSceneEvent` 属于反向 `ReportService`。

| 场景 | 返回或行为 | 关联 AC |
|------|------------|---------|
| 合法搜索配置且连接有效 | `NO_ERROR(0)`；同一 SA 最多两个不同 ruleSet，各自 callback | AC-7.1 / AC-7.16 |
| 搜索配置非法、同集重复 ruleId、重复 ruleSetId 或第三个 ruleSet | `PARAM_INVALID(4)`；整组拒绝且保留既有合法配置及 callback | AC-7.2～AC-7.19 / AC-15.1～AC-15.6 |
| 未连接 | `NOT_CONNECTED(1)` | 沿用 Feat-01 的连接契约 |
| IPC / 回复异常或前一同步请求未结束 | 沿用 `FAILED(2)`、`REPLY_ERROR(3)`、`LAST_UNFINISH(5)`；不新增错误码 | 沿用既有 Proxy/Stub 契约 |
| 按 ruleSetId 注销 | 成功停止该集后续匹配/回调，不主动生成 false，保留另一个集；清理应幂等 | AC-16.1 |
| TEXT_EDITOR 主动查询未命中 | 保留 `eventName=TEXT_EDITOR`；不伪造退出事件 | AC-2.3 |
| 搜索场景 GetPageScene | 归档提出载荷兼容扩展，但本地查询入口尚未接通搜索规则；不得宣称可用 | 见 GAP-9 |

## 兼容性声明

- 保留 TEXT_EDITOR / COUNT_GTE 及其命中、退出、主动查询契约；搜索存在性不使用“≥2 输入控件”判据，也不复用 TEXT_EDITOR_EXIT 事件名。
- 搜索规则使用前述 `ruleSetId/rules/pageType/regions` 结构。对照实现以根 `version` 缺失或 null 路由搜索规则，TEXT_EDITOR 使用 `version: 1`；搜索示例不添加旧版 `version`、`condition` 或 `sceneType` 字段。
- SA 按 `eventType` 与字段存在性解析搜索事件，按 `(ruleSetId, ruleId)` 区分命中。每次事件仅一次异步 IPC 是目标契约，代码差异见 GAP-3。
- 搜索增量目标为 OpenHarmony-7.1-Release；不据存量“API 13+”推断搜索识别已在 API 13 提供。InnerAPI 无新增 `@since`、无持久化格式变更。
- 未注册搜索规则时不得新增搜索扫描、关键词/特征匹配或上报；应用原有回调次数和无障碍呈现保持不变。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 页面场景规则化感知独立于 ContentChange/ComponentChange | 能力仅匹配时机上参考 ContentChange 模式，不设计/实现 ContentChange 内部检测入口作为页面场景规则化感知-only 入口（ADR-8） | AC-4.1 / AC-4.2 |
| 检测收敛到 OnVsyncEnd | 输入类节点上下树先记为待检测，OnVsyncEnd FlushPageSceneNodeChanged 统一执行 | AC-3.1 / AC-3.2 |
| 不设计完整控件树上报 | 上报结果仅包含命中节点摘要，不提供完整树上报开关 | AC-1.4 |
| 子来源边界 | TEXT_EDITOR 子来源保留既有边界；搜索识别排除 Web/UIExtension，只包含当前 UIContent 主页面与 ArkUI 子窗 | AC-6.2 / AC-6.3 / AC-18.1～AC-18.4 |

## 非功能性需求

| 指标 | 验收要求 | 验证方式 |
|------|----------|----------|
| 搜索存在性扫描 | 典型 500 节点、最多 5 条 rule、每条最多 5 区域，单次 ≤10 ms | 目标设备记录 P50/P95/P99 和原始样本；6～10 rule 另记退化曲线 |
| 搜索点击 | ID 精确与最多 10 层局部回退两条路径的新增时延均 <1 ms | 对比未配置基准，记录 P50/P95/P99 |
| IPC | 同步配置、异步事件端到端均 ≤5 ms | 模拟 SA / 真机采样 |
| 数据最小化 | 搜索事件仅含命中关键词与节点摘要，不携带页面其余正文；日志不输出规则 JSON、事件正文、文本或 a11y 内容 | JSON 断言、日志扫描；不改变 TEXT_EDITOR 显式 includeText 契约 |
| 资源 | CPU/内存/功耗增量按需求白盒评估 | 尚无本次实测结果；定量资源阈值由交付验收补齐 |

## 多设备适配声明

手机和平板使用相同的规则格式、匹配语义和事件契约，分别记录功能与性能验证结果。

| 适配维度 | 行为与约束 | 验证方式 |
|----------|------------|----------|
| 屏幕尺寸与像素密度 | 搜索规则区域、maxSize 与事件 rect 统一使用主窗口坐标系的 vp；布局变化后按最终可见矩形重新判断 | 在不同尺寸和 density 下核对变换、裁剪、区域中心点及尺寸/比例边界 |
| ArkUI 子窗 | 当前 UIContent 的子窗矩形先映射到主窗口坐标系，再参与区域匹配；子窗 PageName 使用主页面名加 `+Dialog` | 主窗偏移、Dialog 显示/隐藏及子窗退出用例，关联 AC-10.3～AC-10.7 |
| 输入设备 | 触屏与鼠标操作均以开发者 onClick/onTouch 实际执行为候选前提，保持同操作去重和稳定后消费语义 | VM-11 的触屏/鼠标、回调未执行及独立操作用例 |
| 设备性能 | 手机和平板分别验证扫描、点击和 IPC 指标 | VM-14；报告设备、版本、P50/P95/P99 与原始样本，未执行项保持未验证 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 适用 | 无障碍文本和描述可作为搜索关键词来源；不改变应用原有无障碍呈现 | AC-8.6 / AC-14.7 / AC-17.1 |
| 大字体与布局变化 | 适用 | 布局变化后依据最终可见矩形、区域和控件尺寸约束重新匹配 | AC-9.1～AC-9.10 / AC-10.7 |
| 深色模式 | 不适用 | 规则不使用颜色或图像像素判定；PageScene 不修改应用主题 | 搜索规则与快照匹配 |
| 多窗口与多实例 | 适用 | 搜索范围限定为当前 UIContent 主 Container 及所属 ArkUI 子 Container，其他独立窗口和实例不混入匹配 | AC-18.2～AC-18.4 |
| 国际化 | 适用 | 关键词按 UTF-8 字节长度校验，英文子串匹配忽略大小写；不引入跨语言翻译匹配 | AC-7.9 / AC-8.4 / AC-8.7 |
| 版本升级 | 适用 | 保留 TEXT_EDITOR 契约，SA 按事件类型与字段存在性解析搜索载荷；无新增 Public/System API 或持久化格式变更 | 兼容性声明 / AC-17.1 |

## 实现对照与基线条件

下面是对本地 `8742cdf09ee61f7f8acecd69e74974598b1eff09` 的静态核对，不是运行结果。源码路径见输入文档，函数名用于避免归档行号漂移。需求归档的实现状态与当前代码不一致时，以 AC 保留目标行为，以本表记录差异，不降低 AC。

| 编号 | 目标契约 / 关联 AC | 已观察到的实现差异或验证缺口 | 关闭条件 |
|------|--------------------|----------------------------|----------|
| GAP-1 | Inspector ID 模糊匹配参与存在性 / AC-13.13 | `SearchSnapshotMatcher::FindKeywordHit` 在 keywords 为空时直接返回；`FindKeywordHitInNode` 只用 keywords 匹配节点 ID，未使用 rule.inspectorIds 列表 | 仅配置 inspectorIds、无其他证据仍可在关键区域命中；增加大小写/子串用例 |
| GAP-2 | 事件来源与响应控件摘要 / AC-14.1～AC-14.2 | `search_scene_snapshot.cpp` 输出 placeholder/value/a11y，目标 schema 为 placeholderValue/accessibility；`SearchClickMatcher::Match` 的 ID 精确路径未填 rect，回退返回命中后代节点而非实际响应控件 | 对齐来源枚举，精确与回退均上报响应控件正确 ID/Type/Rect |
| GAP-3 | 同事件一次 IPC、按规则集分发 / AC-14.4～AC-14.6 | `UIContentImpl` 对 clickResults 逐条调用 ReportPageSceneEvent；`UiReportStub::ReportPageSceneEvent` 将完整合并 JSON 传给每个 callback，未裁成各集结果 | 多 rule/双 ruleSet 点击一次 IPC；明确并验证 callback 各自载荷 |
| GAP-4 | 单集注销隔离、无遗留事件 / AC-16.1 | `UnregisterSearchPageSceneRules` 删除服务层规则；另一个集仍在时未通知 PageSceneRuleManager 删除该集派生缓存。未找到该 UI 链路调用 UnregisterSearchRuleSet；重复注销返回 PARAM_INVALID | A 注销后只保留 B 的匹配与 callback；重复清理无副作用，明确重复注销返回语义 |
| GAP-5 | 路由退出身份和 Dialog 状态 / AC-10.5 / AC-12.2 / AC-12.4 | 旧页退出依赖下一次检测；退出序列化传入新 snapshot.pageName，可能把 A false 标为 B；presence 按 pid+pageName 维护，子窗后缀仅在序列化按 anySubwindow 添加 | 验证旧页 false 的 PageName、A false 先于 B true、主页面/子窗独立退出 |
| GAP-6 | 稳定门控与独立操作 / AC-11.3 / AC-13.11～AC-13.12 | 注册成功直接 TriggerPageSceneDetect；检测回调未再次检查稳定状态。候选以同 nodeId 的 500ms 窗口合并，不能据此证明仅去重同一次操作 | 转场/滚动中注册、同节点两次独立操作、重复稳定通知均按 AC 验收 |
| GAP-7 | 最终可见几何与数据最小化 / AC-8.8 / AC-10.7 / AC-14.7 | `BuildNodeFeature` 已做祖先裁剪和 px→vp，但未见显式窗口有效边界求交；子树文本来自 GetGroupText(true)，需验证被裁剪后代文本不参与 | 窗口边界/祖先裁剪/不可见子树用例及日志检查通过；明确统一使用主窗坐标、vp 单位 |
| GAP-8 | 多 SA / 当前 UIContent 隔离 / AC-18.2 / R-27 | `ConsumeSearchClickCandidates` 遍历多个 pid 后返回不含 pid 的结果，调用方使用当前 processId 上报；候选观察器为全局单例 | 两 SA 与两 UIContent 并存时无串报；候选和消费按实例及订阅归属 |
| GAP-9 | 搜索主动查询 | `UiSessionManagerOhos::GetPageScene` / `PrepareGetPageSceneLocked` 仍查文本编辑规则表，未接入 searchPageSceneRuleSets_ | 补齐搜索查询契约与测试，或经需求修订明确不支持 |
| GAP-10 | 控件约束、生命周期及完整测试 / AC-9.x / AC-16.x / AC-17.x / AC-18.5～AC-18.6 | autoPlay=false 的匹配约束、SA 死亡/断链和局部快照 10 层边界仍需专项核对；本地已有 SearchDualRuleSet / SearchMatcher / SearchClickMatcher 等 UT，但本次未编译执行。归档也记录设备性能、平板与交接缺口 | 完成 VM-7～VM-14 的非零用例执行、故障注入及 10ms/1ms/5ms 性能证据 |

升级 Baselined 前应完成需求/实现差异闭环并完成本仓评审；归档的 Approved 不自动转换成本仓 Baselined。业务验证报告需标注源码提交、设备、用例数、原始结果和未达项。

## Spec 自审清单

- [x] 需求来源、源码版本、FuncID/FeatID 与目标版本可追溯。
- [x] 存量编号保留，搜索 AC/规则/VM 与归档逐项对应。
- [x] 接口签名、规则 JSON 与三类事件契约已补充。
- [x] 需求目标、实现差异和未执行验证已明确区分。
- [ ] GAP-1～GAP-10 已关闭并取得完整业务验证证据。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmonyAI/design-docs"
    query: "20260828398121 RR-30095586 proposal spec design execution-plan metadata_tracking; baseline cb29cc06bf1ac5739a280f4f017b3027311c6487"
  - repo: "openharmony/arkui_ace_engine"
    query: "baseline 8742cdf09ee61f7f8acecd69e74974598b1eff09; ui_content_service_interface.h RegisterPageSceneRules UnregisterPageSceneRules GetPageScene PageSceneEventCallback"
  - repo: "openharmony/arkui_ace_engine"
    query: "page_scene_rule_manager.cpp ParseSearchRuleSet MatchSearchScene UpdateSearchPresence ConsumeSearchClickCandidates; search_scene_matcher.cpp; search_scene_click_matcher.cpp"
  - repo: "openharmony/arkui_ace_engine"
    query: "search_scene_context_collector.cpp current UIContent subcontainers; search_scene_snapshot.cpp final visible rect keywordSources"
  - repo: "openharmony/arkui_ace_engine"
    query: "content_change_manager.cpp OnVsyncEnd FlushPageSceneNodeChanged; ui_session_manager.h pageSceneRuleRegistered_ atomic<bool>"
  - repo: "openharmony/arkui_ace_engine"
    query: "ui_session_manager_ohos.cpp RegisterSearchPageSceneRules UnregisterSearchPageSceneRules; ui_content_impl.cpp BuildSearchPresenceEventJson BuildSearchClickEventJson; ui_report_stub.cpp ReportPageSceneEvent"
  - repo: "openharmony/arkui_ace_engine"
    query: "test/unittest/core/manager/page_scene_rule_manager_test_ng.cpp Search; test/unittest/adapter/ohos/entrance/ui_session/ui_content_stub_test.cpp DualRuleSet"
```

**关键文档：**

- [UISession 服务设计](design.md)
- [需求与设计入口：design-docs PR #807](https://gitcode.com/OpenHarmonyAI/design-docs/pull/807)
