# 特性规格

> Func-03-01-02-Feat-01 子管线与多容器 VSync 协调：固化子管线实例创建注册、多实例 VSync fan-out 分发、跨管线 Touch 事件偏移、后台 RequestFrame 门控的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 子管线与多容器 VSync 协调 |
| 特性编号 | Func-03-01-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 10 起支持（框架内部能力） |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 子管线实例创建与注册规格 | 补录 isSubPipeline_/parentPipeline_ 标记、Frontend::AttachSubPipelineContext、RenderSubContainer 桥接 |
| ADDED | 多实例 VSync 协调规格 | 补录 RosenWindow VSync fan-out、子管线独立 RequestVsync |
| ADDED | 跨管线 Touch 事件偏移规格 | 补录 SetSubPipelineGlobalOffset 坐标偏移转换 |
| ADDED | 后台 RequestFrame 门控规格 | 补录 window_->Lock/Unlock 门控、FindWindowScene 适配 |
| ADDED | 子管线类型分类规格 | 补录 7 类子管线（Form/Plugin/UIExtension/SecurityUE/DynamicComponent/IsolatedComponent/PreviewUE）的进程模型、线程模型、渲染模型、事件模型差异 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/03-engine-framework/01-render-pipeline/02-multi-level-render-pipeline/design.md` | Draft |

---

## 用户故事

### US-1: 子管线实例创建与注册

**作为** ArkUI 引擎开发者,
**我想要** 通过 isSubPipeline_/parentPipeline_ 标记建立子管线与父管线的归属关系,
**以便** Plugin/Form/DynamicComponent 等场景拥有独立的渲染管线实例。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建子 PipelineContext THEN 设置 isSubPipeline_=true 并保存 parentPipeline_ 指向父管线 | 正常 |
| AC-1.2 | WHEN 调用 Frontend::AttachSubPipelineContext(pipeline) THEN 将子管线注册到 Frontend 的子管线列表 | 正常 |
| AC-1.3 | WHEN RenderSubContainer::GetSubPipelineContext() THEN 返回关联的子管线 PipelineContext 实例 | 正常 |
| AC-1.4 | WHEN 子管线 rootNode 挂载到父管线 tree THEN 子管线渲染节点仍嵌入父管线节点树 | 正常 |
| AC-1.5 | WHEN 子管线销毁 THEN 从 Frontend 子管线列表移除并断开 parentPipeline_ 引用 | 边界 |

### US-2: 多实例 VSync 协调

**作为** ArkUI 引擎开发者,
**我想要** 主管线 VSync 到达时通过 fan-out 分发给所有子管线，
**以便** 多管线在同一 VSync 周期协同渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 主管线 VSync 回调触发 THEN RosenWindow 通过 multi-instance callback fan-out 分发给所有已注册管线实例 | 正常 |
| AC-2.2 | WHEN 子管线需要主动请求帧 THEN 通过自身 RequestVsync() 独立订阅 VSync | 正常 |
| AC-2.3 | WHEN 子管线在 fan-out 分发中 THEN 按 parentPipeline_ 确定的时序在同一 FlushVsync 流程中执行 | 正常 |

### US-3: 跨管线 Touch 事件偏移

**作为** ArkUI 引擎开发者,
**我想要** 跨管线 Touch 事件通过 SetSubPipelineGlobalOffset 进行坐标系偏移转换,
**以便** 子管线坐标相对于父管线有正确偏移。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN Touch 事件从父管线传递到子管线 THEN SetSubPipelineGlobalOffset 将触摸坐标转换为子管线本地坐标系 | 正常 |
| AC-3.2 | WHEN 子管线有多个层级偏移 THEN offset = parentOffset + subPipelineLocalOffset | 正常 |
| AC-3.3 | WHEN 子管线坐标偏移为零 THEN Touch 事件直接使用原始坐标 | 边界 |

### US-4: 后台 RequestFrame 门控

**作为** ArkUI 引擎开发者,
**我想要** 后台管线通过 RequestFrame 门控防止在没有渲染目标时浪费 VSync,
**以便** 节省后台场景的功耗。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 管线处于后台 THEN window_->Lock() 阻止 RequestFrame 发起 VSync 请求 | 正常 |
| AC-4.2 | WHEN 管线切换到前台 THEN window_->Unlock() 允许 RequestFrame 发起 VSync 请求 | 正常 |
| AC-4.3 | WHEN 子管线没有可见窗口 THEN 不订阅 VSync、不执行 FlushVsync | 边界 |
| AC-4.4 | WHEN FindWindowScene 查找 WINDOW_SCENE_ETS_TAG THEN 子管线渲染挂载到正确窗口场景 | 正常 |

### US-5: 子管线类型分类

**作为** ArkUI 引擎开发者,
**我想要** 了解各子管线类型（Form/Plugin/UIExtension/SecurityUE/DynamicComponent/IsolatedComponent/PreviewUE）的进程模型、线程模型、渲染模型和事件模型差异,
**以便** 正确理解不同嵌入内容场景的管线架构。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN Form/Card 子管线 THEN 进程内、宿主 UI 线程、SubContainer 创建 PipelineContext、CardFrontend 驱动、DrawDelegate/RSSurfaceNode 渲染 | 正常 |
| AC-5.2 | WHEN Plugin 子管线 THEN 进程内、宿主 UI 线程、PluginSubContainer 创建 PipelineContext、PluginFrontend 驱动、DrawDelegate/RSSurfaceNode 渲染 | 正常 |
| AC-5.3 | WHEN UIExtension 子管线 THEN 跨进程 IPC Session、宿主无 PipelineContext、SessionWrapper 通信、RSSurfaceNode 嵌入宿主渲染树 | 正常 |
| AC-5.4 | WHEN SecurityUIExtension THEN 跨进程 IPC Session、SecuritySessionWrapperImpl、PlatformPattern 基类 | 正常 |
| AC-5.5 | WHEN DynamicComponent THEN 进程内隔离 Worker 线程、UIContent 创建独立 PipelineContext、ContainerScope::MarkIsolatedThread、RenderContext attach | 正常 |
| AC-5.6 | WHEN IsolatedComponent THEN 进程内受限 Worker 线程、UIContent(nullptr) 创建独立 PipelineContext、无 AbilityContext、必须运行在受限线程 | 正常 |
| AC-5.7 | WHEN PreviewUIExtension THEN 继承 SecurityUIExtensionPattern、PreviewSessionWrapperImpl | 正常 |
| AC-5.8 | WHEN 子管线为进程内类型（Form/Plugin） THEN Container::IsSubContainer()=true | 边界 |
| AC-5.9 | WHEN 子管线为隔离线程类型（DC/Isolated） THEN Container::IsDynamicRender()=true 且 PipelineContext::IsIsolatedThread()=true | 边界 |
| AC-5.10 | WHEN 子管线为跨进程类型（UIExtension） THEN 宿主不创建 PipelineContext、仅持有 SessionWrapper | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-5 | 无 | 单元测试 | pipeline_base.h:1185 |
| AC-2.1~2.3 | R-6~R-8 | 无 | 单元测试 | rosen_window.cpp:147 |
| AC-3.1~3.3 | R-9~R-11 | 无 | 单元测试 | touch_event.h:197 |
| AC-4.1~4.4 | R-12~R-15 | 无 | 单元测试 | rosen_window.cpp:258 |
| AC-5.1~5.10 | R-16~R-25 | 无 | 单元测试 | 各 Pattern/Container 类 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建子 PipelineContext | isSubPipeline_=true, parentPipeline_=父管线指针 | PipelineBase 构造时设置 | AC-1.1 |
| R-2 | 行为 | AttachSubPipelineContext | 子管线注册到 Frontend 子管线列表 | Frontend 维护列表 | AC-1.2 |
| R-3 | 行为 | GetSubPipelineContext | 返回关联子管线 PipelineContext | RenderSubContainer 桥接 | AC-1.3 |
| R-4 | 行为 | 子管线 rootNode 嵌入父树 | 子管线渲染节点仍嵌入父管线节点树 | 子管线不拥有独立渲染树根 | AC-1.4 |
| R-5 | 边界 | 子管线销毁 | 从 Frontend 列表移除、断开 parentPipeline_ | 弱引用防循环 | AC-1.5 |
| R-6 | 行为 | 主管线 VSync fan-out | RosenWindow multi-instance callback 分发给所有管线实例 | 回调列表遍历 | AC-2.1 |
| R-7 | 行为 | 子管线独立 RequestVsync | 通过自身 RequestVsync() 订阅 | 子管线可独立请求帧 | AC-2.2 |
| R-8 | 行为 | fan-out 时序执行 | 子管线在同一 FlushVsync 流程中按 parentPipeline_ 时序执行 | 避免帧间延迟 | AC-2.3 |
| R-9 | 行为 | 跨管线 Touch 偏移 | SetSubPipelineGlobalOffset 将坐标转换为子管线本地坐标系 | 像素级偏移 | AC-3.1 |
| R-10 | 行为 | 多层级偏移 | offset = parentOffset + subPipelineLocalOffset | 偏移累加 | AC-3.2 |
| R-11 | 边界 | 偏移为零 | Touch 事件直接使用原始坐标 | 无转换开销 | AC-3.3 |
| R-12 | 行为 | 后台 Lock | window_->Lock() 阻止 RequestFrame | 后台功耗节省 | AC-4.1 |
| R-13 | 行为 | 前台 Unlock | window_->Unlock() 允许 RequestFrame | 前台恢复渲染 | AC-4.2 |
| R-14 | 边界 | 无可见窗口 | 不订阅 VSync、不执行 FlushVsync | 子管线静默 | AC-4.3 |
| R-15 | 行为 | FindWindowScene | 查找 WINDOW_SCENE_ETS_TAG 挂载子管线渲染 | SceneBoard 场景 | AC-4.4 |
| R-16 | 行为 | Form/Card 子管线 | 进程内、宿主 UI 线程、SubContainer 创建 PipelineContext | CardFrontend | AC-5.1 |
| R-17 | 行为 | Plugin 子管线 | 进程内、宿主 UI 线程、PluginSubContainer 创建 PipelineContext | PluginFrontend | AC-5.2 |
| R-18 | 行为 | UIExtension 子管线 | 跨进程 IPC Session、宿主无 PipelineContext | SessionWrapper | AC-5.3 |
| R-19 | 行为 | SecurityUIExtension | 跨进程 IPC Session、SecuritySessionWrapperImpl | PlatformPattern 基类 | AC-5.4 |
| R-20 | 行为 | DynamicComponent | 进程内隔离 Worker 线程、UIContent 创建独立 PipelineContext | MarkIsolatedThread | AC-5.5 |
| R-21 | 行为 | IsolatedComponent | 进程内受限 Worker 线程、UIContent(nullptr) 无 AbilityContext | IsRestrictedWorkerThread | AC-5.6 |
| R-22 | 行为 | PreviewUIExtension | 继承 SecurityUIExtensionPattern、PreviewSessionWrapperImpl | — | AC-5.7 |
| R-23 | 边界 | 进程内类型（Form/Plugin） | Container::IsSubContainer()=true | 旧管线 SubContainer | AC-5.8 |
| R-24 | 边界 | 隔离线程类型（DC/Isolated） | Container::IsDynamicRender()=true + PipelineContext::IsIsolatedThread()=true | Worker 线程创建 | AC-5.9 |
| R-25 | 边界 | 跨进程类型（UIExtension） | 宿主不创建 PipelineContext、仅持有 SessionWrapper | RSSurfaceNode 嵌入 | AC-5.10 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~1.5 | 单元测试 | 子管线创建注册与生命周期 |
| VM-2 | R-6~R-8, AC-2.1~2.3 | 单元测试 | VSync fan-out 与独立 RequestVsync |
| VM-3 | R-9~R-11, AC-3.1~3.3 | 单元测试 | 跨管线 Touch 坐标偏移 |
| VM-4 | R-12~R-15, AC-4.1~4.4 | 单元测试 | 后台门控与窗口适配 |
| VM-5 | R-16~R-25, AC-5.1~5.10 | 单元测试 | 子管线类型分类差异 |

## API 变更分析

N/A — 框架内部能力，无新增/变更/废弃 API。

## 接口规格

N/A — 框架内部能力，无新增接口规格。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10 (框架内部能力，无版本策略)
- **API 版本号策略:** N/A（框架内部）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|--------|--------|
| 子管线用标记而非子类化 | isSubPipeline_/parentPipeline_ 是布尔标记+指针，非 PipelineBase 子类 | AC-1.1 |
| VSync fan-out 而非独立订阅 | 主管线 VSync 分发给所有子管线，而非每子管线独立订阅 | AC-2.1 |
| 子管线 rootNode 嵌入父管线树 | 子管线渲染节点仍是父管线节点树的子节点 | AC-1.4 |
| 后台 Lock/Unlock 门控 | window_->Lock/Unlock 阻止/允许 VSync 请求 | AC-4.1~4.2 |
| 三类进程模型 | 进程内（Form/Plugin）、隔离线程（DC/Isolated）、跨进程（UIExtension） | AC-5.1~5.10 |
| DC/Isolated 禁止嵌套 | 不可在 DC 内嵌套 DC 或 Isolated、不可在 Isolated 内嵌套 Isolated 或 DC | AC-5.5~5.6 |
| IsolatedComponent 无 AbilityContext | InitUiContent(nullptr) 创建 UIContent，不关联宿主 Ability | AC-5.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | VSync fan-out 分发延迟 < 0.5ms | 单元测试 | rosen_window.cpp:147 |
| 功耗 | 后台管线无 VSync 请求 | 单元测试 | window_->Lock() |
| 可靠性 | 子管线销毁不导致父管线崩溃 | 单元测试 | parentPipeline_ 弱引用 |

## 多设备适配声明

无差异（框架内部能力，设备无关）。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口/分屏 | 是 | FindWindowScene 保证子管线挂载到正确窗口 | AC-4.4 |
| 无障碍 | 是 | 各类型使用不同 AccessibilitySessionAdapter（Form/UIExtension/IsolatedComponent） | AC-5.1~5.10 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 范围边界明确（仅覆盖子管线与多容器 VSync 协调，不含 dirty flag/UITaskScheduler/Modifier/DisplaySync）
- [ ] 无语义模糊表述
- [ ] AC 与规则表交叉一致
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "子管线 isSubPipeline/parentPipeline 机制与 Frontend 注册流程"
  - repo: "openharmony/arkui_ace_engine"
    query: "RosenWindow VSync fan-out 多实例分发机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "跨管线 Touch 事件偏移转换 SetSubPipelineGlobalOffset"
  - repo: "openharmony/arkui_ace_engine"
    query: "后台 RequestFrame 门控 Lock/Unlock"
  - repo: "openharmony/arkui_ace_engine"
    query: "子管线类型分类：Form/Plugin/UIExtension/DynamicComponent/IsolatedComponent 进程模型/线程模型/渲染模型差异"
```

**关键文档：**
- `frameworks/core/pipeline/pipeline_base.h` (1185-1204 行: isSubPipeline_/parentPipeline_)
- `frameworks/core/common/frontend.h` (138-139 行: AttachSubPipelineContext)
- `frameworks/core/pipeline/base/render_sub_container.h` (29 行: GetSubPipelineContext)
- `frameworks/core/common/rosen/rosen_window.cpp` (147-178 行: VSync fan-out, 258-289 行: RequestFrame)
- `frameworks/core/event/touch_event.h` (197 行: SetSubPipelineGlobalOffset)
- `frameworks/core/pipeline_ng/pipeline_context.cpp` (FindWindowScene:5294)
- `frameworks/core/components_ng/pattern/form/form_pattern.h` (112 行: FormPattern)
- `frameworks/core/components_ng/pattern/plugin/plugin_pattern.h` (31 行: PluginPattern)
- `frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.h` (102 行: UIExtensionPattern)
- `frameworks/core/components_ng/pattern/ui_extension/dynamic_component/dynamic_pattern.h` (46 行: DynamicPattern)
- `frameworks/core/components_ng/pattern/ui_extension/isolated_component/isolated_pattern.h` (35 行: IsolatedPattern)
- `frameworks/core/common/container.h` (314 行: IsSubContainer, 315 行: IsDynamicRender)
- `frameworks/core/common/container_scope.h` (110 行: MarkIsolatedThread)
- `interfaces/inner_api/ace/constants.h` (44 行: UIContentType enum)
- `frameworks/core/components_ng/pattern/ui_extension/session_wrapper.h` (58 行: SessionType, 81 行: SessionWrapper)
- `adapter/ohos/entrance/dynamic_component/dynamic_component_renderer_impl.h` (40 行: DynamicComponentRendererImpl)
