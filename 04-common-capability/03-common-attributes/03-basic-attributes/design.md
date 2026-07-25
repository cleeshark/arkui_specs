# 架构设计

> 基础属性功能域的架构设计文档，补录已有实现。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-03-03 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 组件标识与显隐, Feat-02 背景设置, Feat-03 浮层, Feat-04 渲染与复用, Feat-05 状态效果与自定义 |
| 复杂度 | 复杂 |
| 目标版本 | API 7 起支持，API 7~21 多版本行为变更 |
| Owner | ArkUI SIG |
| 状态 | Baselined（已有实现补录） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | 开发者需要通过声明式 API 控制组件的标识、显隐、背景外观、浮层叠加、渲染行为复用控制、以及交互状态效果与自定义绘制 |
| 核心目标 | （Feat-01）提供 id/key/restoreId/inspectorLabel/uniqueId 组件标识属性和 visibility/zIndex/obscured/allowForceDark/clickDistance/enableClickSoundEffect 显隐及辅助属性，支持组件定位、布局参与控制、隐私保护和无障碍交互；（Feat-02）提供 backgroundColor/backgroundImage/backgroundImageSize/backgroundImagePosition/backgroundBlurStyle/backdropBlur/backgroundEffect/backgroundBrightness/backgroundImageResizable/background(CustomBuilder) 背景设置属性，支持颜色/图像/模糊/亮度/可拉伸图/自定义浮层式背景；（Feat-03）提供 overlay 浮层属性，支持在组件之上叠加自定义内容并控制对齐和偏移；（Feat-04）提供 renderGroup/renderFit/freeze/useEffect/reuseId/reuse 渲染与复用属性，支持子树脏传播聚合、内容适配方式、RS 渲染冻结标记、动效开关和组件复用标识；（Feat-05）提供 stateStyles/hoverEffect/clickEffect/attributeModifier/customProperty/drawModifier 状态效果与自定义属性，支持按压/悬停/聚焦/禁用等状态样式、交互反馈效果、属性动态覆盖和自定义绘制 |
| P0 AC | （Feat-01）id 可设置并通过 ElementRegister 查询；visibility 三态（Visible/Hidden/None）布局参与行为正确；zIndex 绘制层级生效；obscured 截图/录屏区域屏蔽；（Feat-02）backgroundColor 支持颜色和 ColorMetrics 动态颜色；backgroundImage 加载和位置/尺寸设置生效；background(CustomBuilder) 通过 PixelMap snapshot 渲染；（Feat-03）overlay 在组件之上叠加自定义内容，alignment/offset 定位生效；（Feat-04）renderGroup 子树变更聚合为组级重绘；freeze 设置 RS 渲染侧冻结标记；reuseId 标记组件复用身份；（Feat-05）stateStyles 按状态应用样式覆盖；attributeModifier 动态属性控制（与 stateStyles 在 ArkTS 层互斥）；drawModifier 自定义绘制生效 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块/路径 | 当前职责 | 本 Feature 影响 |
|------|-----------|----------|-----------------|
| ace_engine | `frameworks/core/components_ng/base/view_abstract.h/cpp` | API 入口，SetVisibility/SetBackgroundColor/SetOverlay/SetRenderGroup 等统一入口 | API 层 |
| ace_engine | `frameworks/core/components_ng/render/render_context.h/cpp` | RenderContext 存储背景属性（backgroundColor/backgroundImage/backgroundImageSize/backgroundImagePosition/backgroundBlurStyle/backdropBlur/backgroundEffect/backgroundBrightness）、zIndex/obscured 等 | 核心数据结构（背景+隐私） |
| ace_engine | `frameworks/core/components_ng/base/frame_node.h/cpp` | FrameNode 存储 overlayNode/backgroundNode 等；UINode（基类）存储 id/uniqueId/restoreId/inspectorLabel | 核心数据结构（浮层+背景节点） |
| ace_engine | `frameworks/core/components_ng/pattern/pattern.cpp` | Pattern 处理 stateStyles/attributeModifier 状态切换和属性覆盖 | 状态效果管线 |
| ace_engine | `frameworks/core/components_ng/property/property.h` | Property 存储框架（ACE_DEFINE_PROPERTY_GROUP_ITEM 宏） | 属性存储基础设施 |
| ace_engine | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | ArkTS 桥接层，参数解析与校验（SetVisibility/JsBackgroundColor/JsOverlay 等） | 输入校验 |
| ace_engine | `interfaces/native/node/style_modifier.cpp` | C-API 到框架层桥接（SetVisibility/SetZIndex/SetBackgroundColor/SetRenderGroup/SetOverlay 等） | 多语言入口 |
| ace_engine | `frameworks/core/pipeline/base/element_register.h` | ElementRegister 单例存储 id → FrameNode 映射（AddFrameNodeByInspectorId/GetAttachedFrameNodeById） | id 查找 |
| ace_engine | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp` | Rosen 渲染上下文实现，消费背景/显隐/zIndex 属性进行绘制 | 渲染绘制层 |
| ace_engine | `interfaces/native/native_node.h` | C-API (NDK) 接口定义 | NDK 枚举定义 |
| sdk-js | `api/@internal/component/ets/common.d.ts` | ArkTS 接口声明 | 类型定义 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| JS Bridge | `declarative_frontend/jsview/js_view_abstract` | 解析 ArkTS 属性调用（SetVisibility/JsBackgroundColor/JsOverlay/JsRenderGroup 等），参数校验、API 版本分支 | 存量分析 |
| C-API 定义 | `interfaces/native/native_node.h` | 定义 NDK 属性枚举（NODE_VISIBILITY/NODE_Z_INDEX/NODE_BACKGROUND_COLOR/NODE_RENDER_GROUP/NODE_OVERLAY 等）；obscured/freeze 无独立 NDK 枚举 | 存量分析 |
| C-API 桥接 | `interfaces/native/node/style_modifier` | 将 C-API 调用转换为框架层 ViewAbstract::Set* 调用，执行参数单位转换 | 存量分析 |
| API 层 | `core/components_ng/base/view_abstract` | 框架属性设置统一入口（SetVisibility/SetBackgroundColor/SetOverlay/SetRenderGroup/SetFreeze 等），更新 LayoutProperty/RenderContext/FrameNode | 存量分析 |
| Property 层 (显隐) | `core/components_ng/layout/layout_property` | 存储 visibility 属性（propVisibility_），通过 OnVisibilityUpdate 触发布局/渲染树刷新 | 存量分析 |
| Property 层 (背景+隐私) | `core/components_ng/render/render_context` | 存储 RenderContext 内所有背景属性和 zIndex/obscured/freeze/renderGroup 等，通过 Has* 查询和 Get* 读取，触发 OnPropertyUpdate 回调 | 存量分析 |
| Property 层 (标识+复用+浮层) | `core/components_ng/base/frame_node` + `custom_node_base` | FrameNode 存储 overlayNode_/backgroundNode_；UINode（基类）存储 id/restoreId/inspectorLabel；CustomNodeBase 存储 reuseId_ | 存量分析 |
| Property 层 (状态) | `core/components_ng/event/state_style_manager` | StateStyleManager 管理 stateStyles 和 attributeModifier 状态回调，按组件状态（normal/pressed/focused/disabled）切换样式 | 存量分析 |
| id 查找 | `core/pipeline/base/element_register` | ElementRegister 单例存储 id → FrameNode 映射（AddFrameNodeByInspectorId/GetAttachedFrameNodeById） | 存量分析 |
| 渲染绘制 | `core/components_ng/render/adapter/rosen_render_context` | Rosen 渲染上下文消费背景色/背景图/模糊/亮度/visibility/zIndex/obscured，设置到 RSNode | 存量分析 |
| 浮层挂载 | `core/components_ng/base/frame_node` | overlayNode 作为子节点挂载到 FrameNode，在布局/渲染阶段叠加绘制 | 存量分析 |
| 渲染控制 | RenderContext + FrameNode | renderGroup/freeze 存于 RenderContext（propRenderGroup_/propFreeze_），通过 RS 层生效；reuseId 存于 CustomNodeBase | 存量分析 |

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 基础属性涉及 JS Bridge → C-API → API 层 → Property 层 → Render 层单向调用 | JS Bridge/C-API(ViewAbstract) → Property(RenderContext/FrameNode/Pattern) → Render(RosenRenderContext)，严格单向 | 代码评审/依赖检查 |
| OH-ARCH-API-LEVEL | visibility/backgroundColor 等从 API 7 起支持，多版本行为变更 | 各 API 标注 @since 版本号，API 7/10/12/15/21 行为差异需标注 | API 评审/XTS |
| OH-ARCH-COMPONENT-BUILD | 基础属性属于 ace_core_ng，所有组件依赖 | 无需新增 BUILD.gn target，已在 ace_core_ng_source_set 中 | 构建验证 |

## 不涉及项承接

| 维度 | 需求阶段结论 | 设计阶段处理方式 | 设计结论 |
|------|---------|-------------|----------|
| IPC/跨进程 | N/A | 保持 N/A | 基础属性仅在 UI 线程内处理 |
| 安全与权限 | 涉及（obscured） | 展开设计 | obscured 涉及隐私保护（截图/录屏区域屏蔽），通过 ObscuredReasons 枚举区分场景，无权限要求 |
| 构建与部件 | N/A | 保持 N/A | 无新增部件或 target |
| 兼容性 | 涉及 | 展开设计 | API 版本行为差异：visibility None 布局参与、background(CustomBuilder) 双机制、renderGroup 聚合行为等需标注 |
| API/SDK | 涉及 | 展开设计 | CommonMethod 接口 + C-API 双通道 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|-----------------|------|------|
| ADR-1 | visibility None vs Hidden 布局参与差异 | 三态 Visible/Hidden/None，不同布局行为：Visible 正常参与布局和渲染；Hidden 不可见但保留空间（触发 Measure/Layout 但从渲染树排除，不绘制），None 不可见且不参与布局（frameSize={0,0}、跳过子节点 Measure） | 方案A：Hidden 和 None 都不参与布局（Hidden 失去保留空间语义）；方案B：None 也参与布局（浪费计算资源） | 三态设计对齐 CSS visibility（visible/hidden）+ display（none）语义，兼顾开发者保留空间和节省性能两种需求 | visibility=Hidden 时 frameSize 正常但节点从 RS 渲染树排除；visibility=None/GONE 时 frameSize={0,0}，子节点不测量 |
| ADR-2 | background(CustomBuilder) 双机制架构 | 两套独立存储与渲染路径并存：属性式背景（backgroundColor/backgroundImage 等）存储在 RenderContext，CustomBuilder 浮层式背景通过 PixelMap snapshot 渲染（builder 构建 Column 节点 → ComponentSnapshot 生成 PixelMap → BackgroundModifier 绘制在组件内容之下） | 方案A：统一到 RenderContext（CustomBuilder 无法转换为渲染属性）；方案B：统一到子节点挂载（backgroundColor 等无法作为子节点） | 属性式背景适合简单颜色/图像场景（性能好、渲染管线统一），CustomBuilder 适合复杂动态背景（需要布局能力后 snapshot）。两套机制覆盖不同使用场景 | 属性式背景和 CustomBuilder 浮层式背景独立存储、独立生效、互不干扰 |
| ADR-3 | renderGroup 子树脏传播聚合 | 开启 renderGroup 时，子树任意节点变更聚合为组级重绘，整组重绘；关闭时恢复个体脏传播 | 方案A：始终个体传播（频繁微小变更时性能差）；方案B：始终组级传播（单个子节点变更浪费整组绘制） | renderGroup 为高频变更子树提供聚合绘制优化，适合列表项、卡片等频繁整体更新的场景 | renderGroup=true 时子树脏标记上溯到组根节点，统一重绘 |
| ADR-4 | stateStyles 与 attributeModifier 关系 | ArkTS 层两者互斥：使用 attributeModifier 的组件调用 stateStyles 会抛出 BusinessError(100201)；C++ 回调层两者有序执行（inner stateStyles → user attributeModifier），attributeModifier 可通过 excludeInner 排除 stateStyles 回调 | 方案A：stateStyles 优先（Modifier 无法覆盖状态样式，灵活性不足）；方案B：两者互斥（开发者无法同时使用） | attributeModifier 提供更灵活的动态属性控制能力，在 C++ 回调层可以排除或覆盖 stateStyles 结果；ArkTS 层选择互斥以避免开发者困惑 | attributeModifier 与 stateStyles 在 ArkTS 层互斥；C++ 回调层 attributeModifier 后执行可覆盖 stateStyles |
| ADR-5 | obscured 安全隐私机制 | ObscuredReasons 枚举当前仅定义 PLACEHOLDER，设置后组件内容替换为占位显示（文本→密码圆点，图片→占位图）且截图/录屏时区域显示为遮罩色 | 方案A：布尔值开关（无法区分场景）；方案B：权限要求（增加开发者负担） | PLACEHOLDER 同时触发内容占位替换和截图/录屏拦截，不引入权限要求降低开发者使用门槛 | 截图/录屏区域显示遮罩色，开发者通过 ObscuredReasons.PLACEHOLDER 指定屏蔽 |
| ADR-6 | 背景设置与 04-03-02 范围重叠 | 04-03-03 按官方文档「基础属性 → 背景设置」分类覆盖 backgroundColor/backgroundImage/backgroundImageSize/backgroundImagePosition，04-03-02 后续调整范围以消除重叠 | 方案A：04-03-03 不覆盖重叠属性（官方分类不一致）；方案B：合并为单一功能域（破坏分类层级） | 官方文档将背景设置归入基础属性，按文档分类补录更准确。重叠属性在两个域交叉引用而非互斥 | backgroundColor 等在 04-03-03 和 04-03-02 中交叉引用 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|----------|
| 标识与显隐属性存储 | id→ElementRegister + UINode::propInspectorId_, visibility→LayoutProperty, zIndex/obscured→RenderContext, uniqueId→UINode | id 冲突解决策略 | 编译通过 + 属性读取正确 |
| 背景属性存储 | backgroundColor/backgroundImage/blur/brightness→RenderContext, background(CustomBuilder)→PixelMap snapshot + BackgroundModifier | 背景图像解码/缓存机制 | 属性读取正确 |
| 浮层挂载机制 | overlay→FrameNode overlayNode_ 子节点 | overlay 布局算法内部细节 | overlay 内容正确叠加 |
| 渲染控制属性 | renderGroup→RenderContext, freeze→RenderContext, reuseId→CustomNodeBase | renderGroup 聚合绘制的 RS 层细节 | 脏标记传播正确 |
| 状态效果管线 | stateStyles/attributeModifier→StateStyleManager（C++ 回调层有序；ArkTS 层互斥）, drawModifier→Pattern | 各状态样式的具体属性值 | 状态切换时属性覆盖链正确 |

### 骨架 Spec 拆分

| Task ID | 目标 | 受影响文件 | AC |
|---------|------|------------|-----|
| TASK-SKELETON-1 | 标识与显隐属性存储与查找 | view_abstract.h, layout_property.h, render_context.h, frame_node.h, element_register.h | WHEN id 设置 THEN ElementRegister 可查询；WHEN visibility 设置 THEN 布局参与行为正确 |

## 后续 Task 拆分

| Spec | 目的 | 依赖 | 输出 |
|------|------|------|------|
| baseline-design | 基础属性功能域设计基线 | 无 | 本 design.md |
| Feat-01-component-id-visibility-spec.md | 固化 id/key/restoreId/inspectorLabel/uniqueId/visibility/zIndex/obscured/allowForceDark/clickDistance/enableClickSoundEffect 的行为规格 | 本 Design | 完整行为规格与 AC |
| Feat-02-background-setting-spec.md | 固化 backgroundColor/backgroundImage/backgroundImageSize/backgroundImagePosition/backgroundBlurStyle/backdropBlur/backgroundEffect/backgroundBrightness/backgroundImageResizable/background(CustomBuilder) 的行为规格 | 本 Design | 完整行为规格与 AC |
| Feat-03-overlay-spec.md | 固化 overlay(alignment/offset) 的行为规格 | 本 Design | 完整行为规格与 AC |
| Feat-04-render-reuse-spec.md | 固化 renderGroup/renderFit/freeze/useEffect/reuseId/reuse 的行为规格 | 本 Design | 完整行为规格与 AC |
| Feat-05-state-effect-custom-spec.md | 固化 stateStyles/hoverEffect/clickEffect/attributeModifier/customProperty/drawModifier 的行为规格 | 本 Design | 完整行为规格与 AC |

---

## API 签名、Kit 与权限

### 新增 API

| API 签名 | 类型 | d.ts 位置 | 权限要求 | SysCap |
|----------|------|-----------|----------|--------|
| N/A | — | — | — | — |

> 本功能域为已有实现补录，不新增 API。

### 变更/废弃 API

| 原有 API | 变更类型 | 新 API | 迁移说明 |
|----------|----------|--------|----------|
| — | — | — | 无变更/废弃 API |

## 构建系统影响

### BUILD.gn 变更

```
无变更。基础属性实现位于 ace_core_ng_source_set，已有构建配置覆盖。
```

### bundle.json 变更

无变更。

---

## 可选设计扩展

### 架构图

```mermaid
graph TB
    subgraph API["API 层"]
        F1["Feat-01 组件标识与显隐<br/>id / visibility / zIndex / obscured / allowForceDark"]
        F2["Feat-02 背景设置<br/>backgroundColor / backgroundImage… / background(CustomBuilder)"]
        F3["Feat-03 浮层<br/>overlay + alignment / offset"]
        F4["Feat-04 渲染与复用<br/>renderGroup / freeze / reuseId"]
        F5["Feat-05 状态效果与自定义<br/>stateStyles / attributeModifier / drawModifier"]
    end

    subgraph PROP["Property 层"]
        LP["LayoutProperty<br/>visibility (VisibleType)"]
        RC["RenderContext<br/>backgroundColor · backgroundImage · blur · brightness · freeze<br/>zIndex · obscured · renderGroup"]
        FN["FrameNode<br/>overlayNode · backgroundNode_(RefPtr)"]
        UIN["UINode（基类）<br/>id(propInspectorId_) · uniqueId(nodeId_)<br/>restoreId · inspectorLabel"]
        CB["CustomNodeBase<br/>reuseId_"]
        ER["ElementRegister<br/>id → FrameNode 映射"]
        SSM["StateStyleManager<br/>stateStyles/attributeModifier 回调"]
    end

    subgraph LAYOUT["Layout 层"]
        VIS_L["visibility 布局决策<br/>Visible→正常 · Hidden→保留空间 · None→{0,0}"]
        CHILD_L["子节点布局<br/>overlayNode / background(CustomBuilder)<br/>按 alignment+offset 定位"]
    end

    subgraph RENDER["Render 层"]
        BG_RS["背景→RS<br/>SetBackgroundColor · DrawImage · SetFilter"]
        VIS_RS["显隐→RS<br/>SetVisible · SetZIndex · obscured 遮罩"]
        RG_RS["renderGroup→RS<br/>子树脏聚合 · 整组重绘"]
        FRZ_RS["freeze→RS<br/>rsNode_->SetFreeze"]
        DM_RS["drawModifier→RS<br/>beforeDraw / afterDraw 回调"]
    end

    F1 -->|"ViewAbstract::Set*"| RC
    F1 -->|"SetId"| UIN
    F1 -->|"SetVisibility"| LP
    F2 -->|"属性式"| RC
    F2 -->|"CustomBuilder"| FN
    F3 -->|"SetOverlay"| FN
    F4 -->|"SetRenderGroup/SetFreeze"| RC
    F4 -->|"SetReuseId"| CB
    F5 -->|"StateStyleManager"| SSM

    UIN -->|"id 注册"| ER
    LP -->|"visibility"| VIS_L
    FN -->|"overlayNode/backgroundNode"| CHILD_L
    RC --> BG_RS
    RC --> VIS_RS
    RC --> FRZ_RS
    RC --> RG_RS
    SSM --> DM_RS
```

### 数据流/控制流

| 步骤 | 调用方 | 被调用方 | 数据/接口 | 说明 |
|------|--------|----------|-----------|------|
| 1 | 开发者 ArkTS | JSViewAbstract::SetVisibility | `VisibleType value` | 桥接层解析参数 |
| 2 | JSViewAbstract | ViewAbstract::SetVisibility | `VisibleType` | 调用框架层 |
| 3 | ViewAbstract | LayoutProperty::UpdateVisibility | `VisibleType` | 存储到 LayoutProperty，触发 OnVisibilityUpdate（非 GONE 间仅刷新渲染树；涉及 GONE 时触发 measure） |
| 4 | Pipeline | FrameNode::Measure | `parentConstraint` | 布局管线调度 |
| 5 | FrameNode | visibility 布局决策 | `GetVisibility()` | Visible→正常测量；Hidden→正常测量但从渲染树排除；None→frameSize={0,0} |
| 6 | FrameNode | RosenRenderContext::ApplyProperty + 渲染树同步 | `RenderContext + LayoutProperty` | 将背景/zIndex/obscured 应用到 RSNode；visibility 通过渲染树同步（非 GONE→MarkNeedSyncRenderTree, 涉及 GONE→MarkDirtyNode） |
| 7 | 开发者 ArkTS | JSViewAbstract::JsBackgroundColor | `Color value` | 桥接层解析颜色参数 |
| 8 | JSViewAbstract | ViewAbstract::SetBackgroundColor | `Color` | 调用框架层 |
| 9 | ViewAbstract | RenderContext::UpdateBackgroundColor | `Color` | 存储到 RenderContext |
| 10 | RosenRenderContext | RSNode::SetBackgroundColor | `Color` | 渲染层绘制背景色 |
| 11 | 开发者 ArkTS | JSViewAbstract::JsOverlay | `OverlayOptions + builder` | 桥接层解析浮层参数 |
| 12 | JSViewAbstract | ViewAbstract::SetOverlayBuilder | `builder + options` | 创建 overlay 子节点 |
| 13 | ViewAbstract | FrameNode::SetOverlayNode | `RefPtr<FrameNode>` | overlayNode 作为子节点挂载 |
| 14 | 开发者 ArkTS | JSViewAbstract::JsRenderGroup | `bool value` | 桥接层解析参数 |
| 15 | JSViewAbstract | ViewAbstract::SetRenderGroup | `bool` | 设置子树脏传播聚合开关 |
| 16 | ViewAbstract | RenderContext::UpdateRenderGroup | `bool` | 存储到 RenderContext propRenderGroup_ |
| 17 | 开发者 ArkTS | JSViewAbstract::JsStateStyles | `StateStyle object` | 桥接层解析状态样式 |
| 18 | JSViewAbstract | ViewAbstract::SetStateStyles | `StateStyle` | 注册到 StateStyleManager inner 回调 |
| 19 | 开发者 ArkTS | JSViewAbstract::attributeModifier | `AttributeModifier` | 桥接层解析 Modifier（与 stateStyles 互斥） |
| 20 | StateStyleManager | HandleStateChangeInternal | `inner → frontend → user 回调链` | inner(stateStyles) → user(attributeModifier) 有序执行 |

### 算法与状态机

#### visibility 状态机

```mermaid
stateDiagram-v2
    [*] --> Visible : 默认状态

    Visible --> Hidden : visibility(Visibility.Hidden)
    Visible --> None : visibility(Visibility.None)
    Hidden --> Visible : visibility(Visibility.Visible)
    Hidden --> None : visibility(Visibility.None)
    None --> Visible : visibility(Visibility.Visible)
    None --> Hidden : visibility(Visibility.Hidden)

    state Visible {
        [*] --> Measure : 正常测量
        Measure --> Layout : 正常布局
        Layout --> Draw : 正常绘制
    }
    state Hidden {
        [*] --> Measure : frameSize 正常
        Measure --> Layout : 布局偏移正常
        Layout --> SkipDraw : 从渲染树排除<br/>不绘制但保留空间
    }
    state None {
        [*] --> SkipMeasure : frameSize={0,0}<br/>子节点不测量
        SkipMeasure --> SkipLayout : 不参与布局
        SkipLayout --> SkipDraw : 不绘制
    }
```

#### stateStyles 状态切换（C++ 回调层）；ArkTS 层 attributeModifier 与 stateStyles 互斥

> **ArkTS 层**：使用 attributeModifier 的组件调用 `stateStyles()` 会抛出 `BusinessError(100201)`；两者互斥不可同时设置。
>
> **C++ 回调层**：StateStyleManager 按 inner（stateStyles）→ frontend → user（attributeModifier）顺序执行回调；attributeModifier 可通过 excludeInner 排除 stateStyles 回调。

```mermaid
stateDiagram-v2
    [*] --> Normal : 默认状态

    Normal --> Pressed : 触摸按下
    Normal --> Focused : 焦点获得
    Normal --> Disabled : enabled=false
    Pressed --> Normal : 触摸释放
    Focused --> Normal : 焦点丢失
    Disabled --> Normal : enabled=true

    state Normal {
        [*] --> ApplyNormalStyles : stateStyles.normal
        ApplyNormalStyles --> ApplyModifier : attributeModifier.applyNormal()
    }
    state Pressed {
        [*] --> ApplyPressedStyles : stateStyles.pressed
        ApplyPressedStyles --> ApplyModifier : attributeModifier.applyPressed()
    }
    state Focused {
        [*] --> ApplyFocusedStyles : stateStyles.focused
        ApplyFocusedStyles --> ApplyModifier : attributeModifier.applyFocused()
    }
    state Disabled {
        [*] --> ApplyDisabledStyles : stateStyles.disabled
        ApplyDisabledStyles --> ApplyModifier : attributeModifier.applyDisabled()
    }
```

## 详细设计

### 组件标识与显隐

#### id 存储与查找

组件 id 通过 `ViewAbstract::SetInspectorId` 设置，存储在 UINode 的 `propInspectorId_` 属性中，并通过 `ElementRegister` 单例注册 id → FrameNode 的映射关系（`ElementRegister::AddFrameNodeByInspectorId`）。查找通过 `ElementRegister::GetInstance()->GetAttachedFrameNodeById(id)` 完成。

```cpp
// view_abstract.cpp:5881 — id 设置入口
ViewAbstract::SetInspectorId(frameNode, id);

// element_register.h — id 注册与查找
ElementRegister::GetInstance()->AddFrameNodeByInspectorId(id, frameNode);
RefPtr<FrameNode> ElementRegister::GetInstance()->GetAttachedFrameNodeById(const std::string& id);
```

**关键标识属性：**

| 属性 | 存储位置 | 类型 | 说明 |
|------|----------|------|------|
| id | UINode::propInspectorId_ + ElementRegister | string | 开发者设置，通过 ElementRegister 查找组件 |
| key | UINode::propInspectorId_（与 id 共享存储）/ SyntaxItem::key_（ForEach 回收键） | string | .key() 与 .id() 共用 InspectorId 存储；ForEach 回收键在 SyntaxItem |
| restoreId | UINode（FrameNode 继承） | int32_t | 状态持久化恢复标识，默认值 -1 |
| uniqueId | UINode::nodeId_ (int32_t) / accessibilityId_ (int64_t) | int32_t / int64_t | nodeId_ 为框架自增 ID（int32_t）；accessibilityId_ 为无障碍 ID（int64_t） |
| inspectorLabel | UINode（FrameNode 继承） | string | API 12+，无障碍 inspector 标签 |

#### visibility 布局参与行为

visibility 的三种状态在布局管线中具有不同的行为：

| visibility 状态 | ArkTS 枚举 | 引擎内部 | Measure 行为 | Layout 行为 | Draw 行为 | frameSize |
|----------------|-----------|---------|-------------|------------|----------|-----------|
| Visible | Visibility.Visible | VisibleType::VISIBLE | 正常测量 | 正常布局 | 正常绘制 | 正常尺寸 |
| Hidden | Visibility.Hidden | VisibleType::INVISIBLE | 正常测量 | 正常布局 | 从渲染树排除（不绘制） | 正常尺寸（保留空间） |
| None | Visibility.None | VisibleType::GONE | 跳过测量 | 跳过布局 | 跳过绘制 | {0, 0} |

```cpp
// frame_node.cpp:6115 — GONE 路径（简化示意）
if (layoutProperty_->GetVisibility().value_or(VisibleType::VISIBLE) == VisibleType::GONE) {
    layoutAlgorithm_->SetSkipMeasure();   // 跳过子节点 Measure
    layoutAlgorithm_->SetSkipLayout();    // 跳过子节点 Layout
    geometryNode_->SetFrameSize(SizeF()); // frameSize = {0, 0}
    return;                               // 不继续测量子节点
}
// INVISIBLE 不匹配 GONE 检查，走正常 Measure/Layout 路径
// 但在渲染树构建时（OnGenerateOneDepthVisibleFrameWithTransition）从 RSNode 子列表中排除
```

#### obscured 隐私保护

obscured 通过 `ObscuredReasons` 枚举指定屏蔽场景：

| ObscuredReasons | 场景 | 效果 |
|----------------|------|------|
| PLACEHOLDER | 输入框占位文本/敏感内容 | 内容替换为占位显示（文本→密码圆点，图片→占位图）；截图/录屏时区域显示遮罩色 |

```cpp
// view_abstract.cpp — SetObscured（简化示意，实际通过 ACE_UPDATE_NODE_RENDER_CONTEXT 宏调用）
void ViewAbstract::SetObscured(FrameNode* frameNode, const std::vector<ObscuredReasons>& reasons)
{
    CHECK_NULL_VOID(frameNode);
    // 宏展开为: frameNode->GetRenderContext()->UpdateObscured(reasons)
    ACE_UPDATE_NODE_RENDER_CONTEXT(Obscured, reasons, frameNode);
    frameNode->MarkDirtyNode(PROPERTY_UPDATE_RENDER);  // 标记节点脏，触发重绘
}
```

### 背景设置

#### 双机制架构

背景设置存在两套独立机制：

1. **属性式背景**：backgroundColor/backgroundImage/backgroundImageSize/backgroundImagePosition/backgroundBlurStyle/backdropBlur/backgroundEffect/backgroundBrightness/backgroundImageResizable，存储在 `RenderContext`，通过 RS 渲染管线绘制
2. **浮层式背景**：background(CustomBuilder)，builder 构建内容被 snapshot 为 PixelMap 后通过 BackgroundModifier 渲染在组件内容之下；backgroundNode_ 作为 RefPtr 引用存储在 FrameNode 但不在渲染树中作为子节点

```mermaid
graph TD
    BG_START["background 设置入口"]
    PROP_BG{"设置类型"}
    ATTR["属性式背景<br/>backgroundColor/backgroundImage<br/>backgroundBlurStyle/backdropBlur<br/>backgroundEffect/backgroundBrightness<br/>backgroundImageResizable"]
    CB["浮层式背景<br/>background(CustomBuilder)<br/>→ builder 构建 Column 节点<br/>→ ComponentSnapshot 生成 PixelMap<br/>→ BackgroundModifier 绘制"]
    RC["RenderContext 存储"]
    FN_BG["FrameNode backgroundNode_（RefPtr引用，非渲染树子节点）"]
    RS["RS 渲染管线<br/>SetBackgroundColor/SetFilter<br/>DrawImage"]
    SNAPSHOT["Snapshot 管线<br/>CreateBackgroundPixelMap"]

    BG_START --> PROP_BG
    PROP_BG -->|"属性式"| ATTR --> RC --> RS
    PROP_BG -->|"CustomBuilder"| CB --> FN_BG --> SNAPSHOT --> RS
```

**关键背景属性存储：**

| 属性 | 存储位置 | 类型 | 触发回调 |
|------|----------|------|----------|
| backgroundColor | RenderContext | Color / ColorMetrics | OnBackgroundColorUpdate |
| backgroundImage | RenderContext | ImageSourceInfo | OnBackgroundImageUpdate |
| backgroundImageSize | RenderContext | BackgroundImageSize | OnBackgroundImageSizeUpdate |
| backgroundImagePosition | RenderContext | BackgroundImagePosition | OnBackgroundImagePositionUpdate |
| backgroundBlurStyle | RenderContext | BlurStyleOption | OnBackgroundBlurStyleUpdate |
| backdropBlur | RenderContext | Dimension (radius) + BlurOption | OnBackdropBlurUpdate |
| backgroundEffect | RenderContext | EffectOption | — |
| backgroundBrightness | RenderContext | BrightnessOption | — |
| backgroundImageResizable | RenderContext | ImageResizableSlice | — |
| background(CustomBuilder) | FrameNode backgroundNode_（RefPtr引用，非渲染树子节点） | CustomBuilder → PixelMap snapshot | ComponentSnapshot::Create → BackgroundModifier 绘制 |

### 浮层

#### overlay 子节点挂载

overlay 通过 `ViewAbstract::SetOverlayBuilder` 将 CustomBuilder 创建的内容作为 overlayNode 子节点挂载到 FrameNode：

```cpp
// frame_node.h — overlayNode 存储
RefPtr<FrameNode> overlayNode_;

// view_abstract.cpp — SetOverlayBuilder
void ViewAbstract::SetOverlayBuilder(FrameNode* frameNode, ...)
{
    // 创建 overlay FrameNode
    auto overlayNode = FrameNode::CreateFrameNode(...);
    // 按 OverlayOptions 设置 alignment 和 offset
    // 挂载为 FrameNode 的子节点
    frameNode->SetOverlayNode(overlayNode, options);
}
```

**OverlayOptions 参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| alignment | Alignment | 浮层对齐方式（默认 TopStart） |
| offset | Position | 浮层偏移量 |

浮层在渲染时叠加在组件内容之上绘制：

```mermaid
graph TD
    DRAW["绘制顺序"]
    CONTENT["① 绘制组件内容"]
    OVERLAY["② 绘制 overlay 浮层<br/>（按 alignment/offset 定位）"]
    DRAW --> CONTENT --> OVERLAY
```

### 渲染与复用

#### renderGroup 子树脏传播聚合

renderGroup 控制子树脏标记传播策略：

| renderGroup | 脏传播行为 | 适用场景 |
|-------------|----------|----------|
| false（默认） | 个体传播，每个子节点独立脏标记 | 静态或低频变更子树 |
| true | 聚合传播，子树任意变更聚合为组级重绘 | 高频整体变更的列表项/卡片 |

```cpp
// frame_node.cpp — renderGroup 聚合逻辑
// 当 renderGroup=true 时:
// 子节点标记脏 → 上溯到 renderGroup 根节点
// 根节点统一重绘整组子树
// 避免频繁的个体 RS 绘制命令
```

#### freeze RS 渲染侧冻结标记

freeze 是 `CommonMethod` 的通用属性 API，仅设置 `rsNode_->SetFreeze(bool)` 属性，由 RS 渲染系统决定冻结子树的绘制行为：

| freeze | 行为 | 适用场景 |
|--------|------|----------|
| false（默认） | RS 正常绘制 | 活动组件 |
| true | rsNode_->SetFreeze(true) 使 RS 侧跳过绘制 | 不可见/冻结的列表项 |

> **与 FrameNode::SetNodeFreeze 的关系**：本规格描述的 `CommonMethod.freeze()` 仅做 `rsNode_->SetFreeze` 属性设置，与 `FrameNode::SetNodeFreeze()` 内部路径无关。`FrameNode::SetNodeFreeze()` 是系统级冻结机制（受 `SystemProperties::IsPageTransitionFreeze()` 条件控制，仅在页面转场场景下生效），不属于通用属性的公开 API 范围。
>
> freeze 不阻塞 VSync 刷新，不影响 ACE 侧 Measure/Layout 管线。

#### reuseId 与 reuse

reuseId 标记组件的复用身份，配合 LazyForEach 的组件复用机制：

| 属性 | 类型 | 说明 |
|------|------|------|
| reuseId | string | 复用标识，相同 reuseId 的组件可互相复用节点树 |
| reuse | — | 组件复用触发入口（LazyForEach 场景） |

#### renderFit 内容适配

renderFit 控制组件内容在帧尺寸内的适配方式（对应 gravity 属性）：

| RenderFit 枚举值 | 行为 |
|-----------------|------|
| CENTER | 内容居中 |
| TOP | 内容顶部对齐 |
| BOTTOM | 内容底部对齐 |
| LEFT | 内容左对齐 |
| RIGHT | 内容右对齐 |
| ... | 其他 16 个枚举值覆盖各种对齐组合 |

> 注：RenderFit 枚举值实际 16 个，超出官方文档标注的 10 个，需文档同步。

### 状态效果与自定义

#### stateStyles 状态样式覆盖链

stateStyles 提供四种状态下的样式覆盖：

| 状态 | 属性键 | 说明 |
|------|--------|------|
| normal | .normal | 默认状态样式 |
| pressed | .pressed | 按压状态样式 |
| focused | .focused | 焦点状态样式 |
| disabled | .disabled | 禁用状态样式 |

stateStyles 在组件状态变化时自动切换样式，由 Pattern 负责状态检测和样式应用。

#### attributeModifier 动态属性控制（与 stateStyles 互斥）

> **ArkTS 层互斥**：使用 attributeModifier 的组件调用 `stateStyles()` 会抛出 `BusinessError(100201)`，两者不可同时设置。

attributeModifier 提供比 stateStyles 更灵活的动态属性控制。在 C++ 回调层，StateStyleManager 按 inner（stateStyles）→ user（attributeModifier）顺序执行；attributeModifier 可通过 `excludeInner` 排除 stateStyles 对同一状态的回调：

```
C++ 回调层应用顺序：inner stateStyles → user attributeModifier（可 excludeInner）→ 最终生效
ArkTS 层：stateStyles 与 attributeModifier 互斥，不可同时使用
```

```mermaid
graph TD
    STATE["组件状态变化<br/>Normal/Pressed/Focused/Disabled"]
    SS["Step 1: inner 回调<br/>stateStyles 按状态选择样式集<br/>pressed → pressedStyles<br/>focused → focusedStyles"]
    AM["Step 2: user 回调<br/>attributeModifier 按状态调用 apply*<br/>applyNormal()/applyPressed()<br/>applyFocused()/applyDisabled()<br/>（可通过 excludeInner 排除 Step 1）"]
    FINAL["最终生效属性<br/>ArkTS 层两者互斥<br/>C++ 回调层有序执行"]

    STATE --> SS --> AM --> FINAL
```

#### hoverEffect / clickEffect 交互反馈

| 属性 | 类型 | 说明 |
|------|------|------|
| hoverEffect | HoverEffectType | 悬停反馈效果类型（Auto/Scale/Highlight/None） |
| clickEffect | — | 点击反馈效果 |

#### drawModifier 自定义绘制

drawModifier 提供自定义绘制回调，在组件绘制的 before/after 阶段插入自定义绘制逻辑：

| 回调 | 触发时机 | 说明 |
|------|----------|------|
| beforeDraw | 组件内容绘制前 | 在内容下方绘制 |
| afterDraw | 组件内容绘制后 | 在内容上方绘制 |

---

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| 背景设置与 04-03-02 范围重叠 | 架构 | 中 | backgroundColor/backgroundImage 在 04-03-03 和 04-03-02 交叉引用，04-03-02 后续调整范围 | ArkUI SIG |
| RenderFit 枚举值 16 个超出官方文档标注 10 个 | API | 低 | 需文档同步，枚举值完整列表在规格中标注 | 文档 |
| freeze 仅设置 RS 渲染侧属性 | API | 低 | freeze 通过 rsNode_->SetFreeze 设置，ACE 侧 Measure/Layout 不受影响；NDK 场景受限 | 标注 |
| visibility None 布局参与行为与开发者直觉 | 兼容性 | 中 | None(GONE) 不参与布局（frameSize={0,0}），与 Hidden(INVISIBLE) 保留空间行为差异需明确标注 | ArkUI SIG |
| background(CustomBuilder) 与属性式背景并存 | 架构 | 低 | CustomBuilder 通过 PixelMap snapshot 渲染而非子节点挂载；开发者可能困惑于两种机制的差异 | 文档/标注 |
| attributeModifier 与 stateStyles 互斥 | 架构 | 中 | ArkTS 层两者互斥（BusinessError(100201)); C++ 回调层 attributeModifier 后执行可 excludeInner | 文档/标注 |
| obscured ObscuredReasons 枚举扩展性 | API | 低 | 当前仅 PLACEHOLDER，未来可能新增枚举值（如 SENSITIVE_DATA）以支持纯截图拦截不替换内容的场景 | ArkUI SIG |
| renderGroup 聚合绘制的性能权衡 | 性能 | 低 | 开启后整组重绘，单个子节点变更时可能比个体传播更慢 | 标注 |

---

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0/P1 AC
- [x] 不涉及项已承接，N/A 和展开项都有结论
- [x] 涉及仓和模块职责清楚
- [x] 调用链层级分析完整，每层覆盖到位
- [x] 适用架构规则已识别并形成设计结论
- [x] 分层和子系统边界合规
- [x] API 变更有签名、权限、错误码和兼容性说明
- [x] BUILD.gn/bundle.json 影响明确
- [x] 设计输出和后续 Task 拆分明确
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner

**结论:** 通过（已有实现补录）
