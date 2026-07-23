# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 渲染后端核心架构 |
| 特性编号 | Func-02-02-01-Feat-01 |
| 所属 Epic | 跨平台适配层 |
| 优先级 | P1 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

> 全新特性补录，无存量变更。本节跳过。

## 输入文档

- 源码路径：`frameworks/core/components_ng/render/` + `frameworks/core/components_ng/render/adapter/`
- 设计文档：`02-cross-platform/02-render-backend-adapter/01-rosen-render-backend-adapter/design.md`

## 用户故事

### US-1: RenderContext 抽象基类与三层可插拔架构

作为一个 ACE 引擎开发者，我希望 RenderContext 基类通过 300+ 虚方法（默认 no-op）定义完整的渲染属性接口，工厂通过编译宏+运行时标志选择后端实现，使新渲染后端只需覆盖关心的方法即可插入。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN RenderContext 基类定义 THEN 300+ 虚方法均为默认 no-op（非纯虚，实际约 364 个，0 个纯虚），新后端仅覆盖需要的方法 | 正常 |
| AC-1.2 | WHEN RenderContext::Create() THEN 双层选择：编译时 ENABLE_ROSEN_BACKEND 宏控制 RosenRenderContext 可见性，运行时 SystemProperties::GetRosenBackendEnabled() 控制工厂返回 | 正常 |
| AC-1.3 | WHEN ENABLE_ROSEN_BACKEND 未定义 THEN Create() 返回 nullptr（无后端可用） | 边界 |
| AC-1.4 | WHEN ContextType 枚举 THEN 定义 CANVAS/ROOT/SURFACE/EFFECT/EXTERNAL/INCREMENTAL_CANVAS/HARDWARE_SURFACE/COMPOSITE_COMPONENT/UNION/DEPTH 等 10 种节点类型；RENDER_EXTRACT_SUPPORTED 条件下额外有 HARDWARE_TEXTURE 类型 | 正常 |
| AC-1.5 | WHEN Preview 平台构建 THEN ENABLE_ROSEN_BACKEND=true，RosenRenderContext 被编译和链接（与 OHOS 使用同一实现） | 正常 |
| AC-1.6 | WHEN ACE_UNITTEST 定义 THEN Drawing API 通过 type alias 替换为 Testing 假类（97 drawing.h + 22 drawing_forward.h + 84 drawing_mock.h = 203 alias），编译时零运行时开销 | 边界 |

### US-2: RSNode 创建与节点类型映射

作为一个 ACE 引擎开发者，我希望 RosenRenderContext 在 InitContext 中根据 ContextType 创建对应 RSNode 子类，使 NG 组件树的渲染节点映射能根据节点用途动态选择。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN InitContext(isRoot=true) THEN 创建 RSRootNode | 正常 |
| AC-2.2 | WHEN InitContext 无 param THEN 创建 RSCanvasNode | 正常 |
| AC-2.3 | WHEN CreateNodeByType(CANVAS) THEN 创建 RSCanvasNode | 正常 |
| AC-2.4 | WHEN CreateNodeByType(SURFACE) THEN 创建 RSSurfaceNode | 正常 |
| AC-2.5 | WHEN CreateNodeByType(EFFECT) THEN 创建 RSEffectNode | 正常 |
| AC-2.6 | WHEN CreateNodeByType(HARDWARE_SURFACE) THEN 创建 HardwareSurface 节点 | 边界 |
| AC-2.7 | WHEN RENDER_EXTRACT_SUPPORTED + HARDWARE_TEXTURE THEN 创建 HardwareTexture 节点 | 边界 |

### US-3: Drawing API 编译时替换层

作为一个 ACE 引擎开发者，我希望 drawing.h/drawing_forward.h/drawing_mock.h 通过 203 type alias（97+22+84）在编译时将 RS* 类型映射到 Rosen::Drawing 或 Testing 假类，使渲染层代码无需修改即可在不同编译配置下切换后端。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 非 ACE_UNITTEST 编译 THEN RS* 类型 alias 映射到 Rosen::Drawing::*（97 个唯一 alias，如 RSCanvas=Rosen::Drawing::Canvas） | 正常 |
| AC-3.2 | WHEN ACE_UNITTEST 编译 THEN RS* 类型 alias 映射到 Testing::*（如 RSCanvas=Testing::TestingCanvas） | 边界 |
| AC-3.3 | WHEN drawing_forward.h THEN 提供 22 轻量前向声明 alias | 正常 |
| AC-3.4 | WHEN drawing.h THEN 提供 97 个唯一 type alias（104 行含 7 个重复） | 正常 |
| AC-3.5 | WHEN drawing_mock.h THEN 提供 84 Testing 假类 alias | 正常 |

### US-4: 混合子列表与延迟销毁

作为一个 ACE 引擎开发者，我希望 RosenMixedRenderChildList 管理 FrameNodeChild 和 PureRenderChild 的混合子列表，DetachedRsNodeManager 管理脱离管线 RSNode 的延迟销毁。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 添加 FrameNodeChild THEN RosenMixedRenderChildList 记录为 FRAME_NODE_CHILD 并维护弱引用 | 正常 |
| AC-4.2 | WHEN 添加 PureRenderChild THEN 记录为 PURE_RENDER_NODE 并维护弱引用 | 正常 |
| AC-4.3 | WHEN BuildTargetRSNodes THEN 按插入顺序组装有序 RSNode 子列表 | 正常 |
| AC-4.4 | WHEN PureRenderChild 弱引用失效 THEN CanSwitchToSingleIfRenderNode 返回 true 可降级 | 边界 |
| AC-4.5 | WHEN RSUIContext 脱离管线 THEN DetachedRsNodeManager 加入 unordered_set 管理 | 正常 |
| AC-4.6 | WHEN PreFreeze 空闲 THEN 对所有脱离 RSUIContext 执行 FlushImplicitTransaction | 正常 |

### US-5: RenderSurface 双路径工厂

作为一个 ACE 引擎开发者，我希望 RenderSurface 工厂根据平台和后端类型选择 OHOS Native Surface 或跨平台 SurfaceImpl，使不同平台能使用各自最优的 Surface 实现。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN OHOS_PLATFORM + ENABLE_ROSEN_BACKEND THEN RenderSurface::Create() 返回 RosenRenderSurface（OHOS Native producer/consumer Surface） | 正常 |
| AC-5.2 | WHEN 非 OHOS_PLATFORM（Preview）THEN 使用 RenderSurfaceImpl（跨平台 ExtSurface 实现） | 正常 |
| AC-5.3 | WHEN GetRosenBackendEnabled=false THEN 返回 no-op RenderSurface 基类 | 边界 |
| AC-5.4 | WHEN RENDER_EXTRACT_SUPPORTED + TEXTURE 类型 THEN 返回 RenderTextureImpl | 边界 |

### US-6: 空操作 Stub 层

作为一个 ACE 引擎开发者，我希望 fake_animation_utils.cpp 和 fake_modifier_adapter.cpp 在 ENABLE_ROSEN_BACKEND 未定义时提供空操作 stub，确保框架无后端时编译链接不失败。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN #ifndef ENABLE_ROSEN_BACKEND THEN fake_animation_utils.cpp 所有方法为空操作 | 边界 |
| AC-6.2 | WHEN #ifndef ENABLE_ROSEN_BACKEND THEN fake_modifier_adapter.cpp RemoveModifier 为空操作 | 边界 |
| AC-6.3 | WHEN ENABLE_ROSEN_BACKEND 定义 THEN rosen_animation_utils.cpp 和 rosen_modifier_adapter.cpp 提供真实实现，fake 文件被宏排除 | 正常 |
| AC-6.4 | WHEN 无后端可用 THEN AnimationUtils::CloseImplicitAnimation 返回 false，StartAnimation 返回 nullptr | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1~6 | TASK-F01-01 | 单测+编译检查 | render_context.h, render_context_creator.cpp |
| AC-2.1~2.7 | R-7~13 | TASK-F01-02 | 单测 | rosen_render_context.cpp |
| AC-3.1~3.5 | R-14~18 | TASK-F01-03 | 编译检查 | drawing.h, drawing_forward.h, drawing_mock.h |
| AC-4.1~4.6 | R-19~24 | TASK-F01-04 | 单测+集成测试 | rosen_mixed_render_child_list.h, detached_rs_node_manager.h |
| AC-5.1~5.4 | R-25~28 | TASK-F01-05 | 编译检查 | render_surface_creator.cpp |
| AC-6.1~6.4 | R-29~32 | TASK-F01-06 | 编译检查 | fake_animation_utils.cpp, fake_modifier_adapter.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | RenderContext 基类定义 | 300+ 虚方法均为默认 no-op | 非纯虚，实际约 364 个，可实例化但无渲染效果 | AC-1.1 |
| R-2 | 行为 | RenderContext::Create() | 双层选择：编译宏+运行时标志 | ENABLE_ROSEN_BACKEND 编译时守卫 | AC-1.2 |
| R-3 | 边界 | ENABLE_ROSEN_BACKEND 未定义 | Create() 返回 nullptr | 无后端可用 | AC-1.3 |
| R-4 | 行为 | ContextType 枚举 | 10 种节点类型定义 + 1 条件类型 | RENDER_EXTRACT_SUPPORTED 增加 HARDWARE_TEXTURE | AC-1.4 |
| R-5 | 行为 | Preview 构建 | ENABLE_ROSEN_BACKEND=true，使用同一 RosenRenderContext | Preview 与 OHOS 共用 Rosen 后端 | AC-1.5 |
| R-6 | 边界 | ACE_UNITTEST 定义 | Drawing API 替换为 Testing 假类 | 97+22+84=203 alias 编译时替换 | AC-1.6 |
| R-7 | 行为 | InitContext(isRoot=true) | 创建 RSRootNode | 根节点专用 | AC-2.1 |
| R-8 | 行为 | InitContext 无 param | 创建 RSCanvasNode | 默认节点类型 | AC-2.2 |
| R-9 | 行为 | CreateNodeByType(CANVAS) | 创建 RSCanvasNode | 通用绘制节点 | AC-2.3 |
| R-10 | 行为 | CreateNodeByType(SURFACE) | 创建 RSSurfaceNode | Surface 节点用于独立渲染 | AC-2.4 |
| R-11 | 行为 | CreateNodeByType(EFFECT) | 创建 RSEffectNode | 视效节点 | AC-2.5 |
| R-12 | 边界 | CreateNodeByType(HARDWARE_SURFACE) | 创建 HardwareSurface | 条件编译 | AC-2.6 |
| R-13 | 边界 | RENDER_EXTRACT_SUPPORTED + HARDWARE_TEXTURE | 创建 HardwareTexture | 纹理导出专用 | AC-2.7 |
| R-14 | 行为 | 非 ACE_UNITTEST 编译 | RS*→Rosen::Drawing::* | 实际渲染使用 | AC-3.1 |
| R-15 | 边界 | ACE_UNITTEST 编译 | RS*→Testing::* | 单测使用 | AC-3.2 |
| R-16 | 行为 | drawing_forward.h | 22 轻量 alias | 前向声明 | AC-3.3 |
| R-17 | 行为 | drawing.h | 97 个唯一 alias（104 行含 7 个重复） | 含 Typography/Effects | AC-3.4 |
| R-18 | 行为 | drawing_mock.h | 84 Testing alias | 单测 Mock | AC-3.5 |
| R-19 | 行为 | 添加 FrameNodeChild | 混合列表记录 FRAME_NODE_CHILD | 弱引用 RSNode | AC-4.1 |
| R-20 | 行为 | 添加 PureRenderChild | 混合列表记录 PURE_RENDER_NODE | 弱引用 RSNode | AC-4.2 |
| R-21 | 行为 | BuildTargetRSNodes | 按插入顺序组装子列表 | 交错排列 | AC-4.3 |
| R-22 | 边界 | PureRenderChild 弱引用失效 | CanSwitchToSingleIfRenderNode=true | 降级为单模式 | AC-4.4 |
| R-23 | 行为 | RSUIContext 脱离管线 | DetachedRsNodeManager 加入管理集合 | unordered_set | AC-4.5 |
| R-24 | 行为 | PreFreeze 空闲 | FlushImplicitTransaction 冲刷脱离节点 | 空闲时段执行 | AC-4.6 |
| R-25 | 行为 | OHOS_PLATFORM + ENABLE_ROSEN_BACKEND | 返回 RosenRenderSurface | Native Surface | AC-5.1 |
| R-26 | 行为 | 非 OHOS_PLATFORM | 返回 RenderSurfaceImpl | 跨平台 Surface | AC-5.2 |
| R-27 | 边界 | GetRosenBackendEnabled=false | 返回 no-op 基类 | 无渲染能力 | AC-5.3 |
| R-28 | 边界 | RENDER_EXTRACT_SUPPORTED + TEXTURE | 返回 RenderTextureImpl | 纹理 Surface | AC-5.4 |
| R-29 | 边界 | #ifndef ENABLE_ROSEN_BACKEND | fake_animation_utils 空操作 | 编译链接不失败 | AC-6.1 |
| R-30 | 边界 | #ifndef ENABLE_ROSEN_BACKEND | fake_modifier_adapter 空操作 | RemoveModifier 无效果 | AC-6.2 |
| R-31 | 行为 | ENABLE_ROSEN_BACKEND 定义 | 真实实现提供，fake 文件宏排除 | 链接时选择真实实现 | AC-6.3 |
| R-32 | 边界 | 无后端可用 | CloseImplicitAnimation 返回 false | StartAnimation 返回 nullptr | AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.6 RenderContext 抽象 | 单测+编译检查 | no-op 默认（300+ 虚方法）、双层工厂、type alias 替换 |
| VM-2 | AC-2.1~2.7 RSNode 类型映射 | 单测 | 10 种 ContextType 对应 RSNode 子类 |
| VM-3 | AC-3.1~3.5 Drawing 替换层 | 编译检查 | alias 数量、Testing/真实映射 |
| VM-4 | AC-4.1~4.6 混合子列表+延迟销毁 | 单测+集成测试 | 子列表有序组装、弱引用失效、PreFreeze |
| VM-5 | AC-5.1~5.4 Surface 双路径 | 编译检查 | OHOS/Preview/Texture 工厂选择 |
| VM-6 | AC-6.1~6.4 空操作 Stub | 编译检查 | 宏守卫、空操作行为 |

## API 变更分析

N/A，框架内部适配层，无 SDK API 变更。

## 接口规格

### 接口定义

**RenderContext::Create**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<RenderContext> RenderContext::Create()` |
| 返回值 | `RefPtr<RenderContext>` — RosenRenderContext 或 nullptr |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**RosenRenderContext::InitContext**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void RosenRenderContext::InitContext(bool isRoot, const std::optional<ContextParam>& param, FrameNode* frameNode)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**RenderSurface::Create**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<RenderSurface> RenderSurface::Create()` |
| 返回值 | `RefPtr<RenderSurface>` — RosenRenderSurface/RenderSurfaceImpl/no-op |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** InnerApi

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| No-op 默认层 | RenderContext 基类无纯虚方法，300+ 方法为默认空操作（实际约 364 个） | AC-1.1 |
| 编译时替换 | Drawing API 通过 type alias 在编译时替换，运行时零开销 | AC-3.1~3.5 |
| 单后端现状 | 当前只有 Rosen 一个后端，架构预留三层可插拔但无第二后端 | AC-1.2, AC-1.3 |
| 基类 RS 耦合 | CanvasImage::DrawToRSCanvas 方法名含 RS 前缀，基类接口已与 Rosen 耦合 | AC-1.1 |
| 双层工厂 | 编译宏+运行时标志双层选择机制 | AC-1.2, AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | RenderContext::InitContext ≤1ms | 单测计时 | rosen_render_context.cpp |
| 内存 | 每个 RosenRenderContext 持 1 rsNode_ + 1 rsUIDirector_ | 内存分析 | rosen_render_context.h |
| 可测试性 | RenderContext 基类可通过 Mock 测试（no-op 默认） | 单测覆盖率 | UT 报告 |
| 自动化维测 | DetachedRsNodeManager PreFreeze 回调自动冲刷 | 集成测试 | detached_rs_node_manager.cpp |

## 多设备适配声明

无差异。所有设备类型使用相同的渲染后端适配代码。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 适配层不直接影响 | N/A |
| 大字体 | 否 | 适配层不直接影响 | N/A |
| 深色模式 | 间接 | 毛玻璃材质预设区分 Regular/Dark | AC-1.1 |
| 多窗口/分屏 | 是 | DetachedRsNodeManager 多窗口场景下节点脱离更频繁 | AC-4.5 |
| 版本升级 | 是 | ENABLE_ROSEN_BACKEND 宏在不同 API 版本有不同行为 | AC-1.2 |
| 生态兼容 | 是 | CROSS_PLATFORM 控制 ArkUI-X 构建选择 | AC-1.2 |

## 行为场景（可选，Gherkin）

> 本特性为 L2+（关键复杂度），使用 Gherkin 场景描述核心行为。

```gherkin
Feature: 渲染后端核心架构
  作为 ACE 引擎开发者
  我想要 渲染后端适配层通过三层可插拔架构支持多后端选择
  以便 NG 组件树能在不同平台和编译配置下使用最优渲染后端

  Scenario: RenderContext 工厂选择 Rosen 后端
    Given ENABLE_ROSEN_BACKEND 编译宏已定义
    And SystemProperties::GetRosenBackendEnabled() = true
    When 调用 RenderContext::Create()
    Then 返回 MakeRefPtr<RosenRenderContext>

  Scenario: 无后端时工厂返回 nullptr
    Given ENABLE_ROSEN_BACKEND 编译宏未定义
    When 调用 RenderContext::Create()
    Then 返回 nullptr

  Scenario: Drawing API 编译时替换为 Testing 假类
    Given ACE_UNITTEST 编译宏已定义
    When 代码使用 RSCanvas 类型
    Then RSCanvas = Testing::TestingCanvas
    And 编译时零运行时虚函数开销（97+22+84=203 alias）

  Scenario: DetachedRsNodeManager PreFreeze 空闲冲刷
    Given 3 个 RSUIContext 已脱离管线
    When Ark 空闲监视器触发 PreFreezeFlushForAllContexts
    Then 对所有 3 个 RSUIContext 执行 FlushImplicitTransaction
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RenderContext 基类 300+ 虚方法 no-op 默认设计和 ENABLE_ROSEN_BACKEND 双层工厂选择机制"
  - repo: "openharmony/ace_engine"
    query: "drawing.h / drawing_forward.h / drawing_mock.h 97+22+84=203 type alias 编译时替换层架构"
  - repo: "openharmony/ace_engine"
    query: "RenderSurface 工厂 OHOS_PLATFORM / RENDER_EXTRACT_SUPPORTED 双路径选择"
  - repo: "openharmony/ace_engine"
    query: "fake_animation_utils / fake_modifier_adapter 空操作 stub 层和 ENABLE_ROSEN_BACKEND 宏守卫"
```

**关键文档：** ace_engine `frameworks/core/components_ng/render/` + `frameworks/core/components_ng/render/adapter/`
