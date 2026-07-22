# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Rosen渲染后端适配 |
| 特性编号 | Func-02-01-01-Feat-01 |
| 所属 Epic | 跨平台适配层 |
| 优先级 | P1 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

> 全新特性补录，无存量变更。本节跳过。

## 输入文档

- 源码路径：`adapter/ohos/` + `frameworks/core/components_ng/render/adapter/`
- 设计文档：`02-cross-platform/01-platform-adapter/01-oh-platform-adapter/design.md`
- 无独立 requirement.md（已有实现补录）

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: RenderContext 初始化与 RSNode 创建

作为一个 ACE 引擎开发者，我希望 RosenRenderContext 在初始化时正确创建 RSNode 并建立与 RSUIDirector 的双引用关系，以便 NG 组件树能通过 Rosen 渲染后端完成渲染节点映射。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 RosenRenderContext::InitContext THEN 创建 RSCanvasNode 作为 rsNode_，若当前节点为 Surface 类型则创建 RSSurfaceNode，若为 Texture 类型则创建 RSTextureNode | 正常 |
| AC-1.2 | WHEN RosenRenderContext 创建完成 THEN rsNode_ 和 rsUIDirector_ 两个核心引用均已正确初始化，rsNode_ 通过 AttachToUITree 注册到 RSUIDirector 的节点树 | 正常 |
| AC-1.3 | WHEN ENABLE_ROSEN_BACKEND 未定义 THEN RenderContext::Create() 工厂不返回 RosenRenderContext，而是返回空实现或抛出编译错误 | 边界 |
| AC-1.4 | WHEN 调用 RosenRenderContext::SetRSUIContext THEN rsUIDirector_ 的 RSUIContext 被更新，后续 RS 调用使用新上下文 | 正常 |
| AC-1.5 | WHEN 节点类型为 Surface 且设置了 TextureExport THEN 创建 RSTextureNode 并设置 RSWindowKeyframeNode 用于纹理导出 | 正常 |

### US-2: RSNode 子树管理（混合子列表）

作为一个 ACE 引擎开发者，我希望 RosenRenderContext 正确管理混合类型的子节点列表（FrameNodeChild 和 PureRenderChild），以便 NG 组件树和纯渲染节点能在同一父节点下有序共存。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 添加一个 FrameNode 类型子节点 THEN RosenMixedRenderChildList 记录为 FRAME_NODE_CHILD 并维护其弱引用 RSNode | 正常 |
| AC-2.2 | WHEN 添加一个纯渲染节点（如 Modifier 产生的 RSNode）THEN RosenMixedRenderChildList 记录为 PURE_RENDER_NODE 并维护其弱引用 RSNode | 正常 |
| AC-2.3 | WHEN 调用 BuildTargetRSNodes THEN 混合列表按插入顺序组装出最终的有序 RSNode 子列表，FrameNodeChild 和 PureRenderChild 按逻辑顺序交错排列 | 正常 |
| AC-2.4 | WHEN 一个 FrameNodeChild 被移除 THEN 从混合列表中删除对应条目，且通过 RemoveChild 从 rsNode_ 移除该子 RSNode | 正常 |
| AC-2.5 | WHEN 一个 PureRenderChild 的 RSNode 弱引用失效 THEN CanSwitchToSingleIfRenderNode 返回 true，混合列表可自动切换为单模式 | 边界 |

### US-3: DetachedRsNodeManager 延迟销毁

作为一个 ACE 引镜开发者，我希望脱离渲染管线的 RSNode 通过 DetachedRsNodeManager 延迟销毁并在 PreFreeze 空闲时段冲刷渲染命令，以便避免 RS 资源泄露和管线卡顿。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN RSUIContext 从管线脱离 THEN DetachedRsNodeManager 将该 RSUIContext* 加入 unordered_set 管理 | 正常 |
| AC-3.2 | WHEN 调用 PostDestructorTask THEN 通过后台 TaskRunnerAdapter 提交 FlushImplicitTransaction 任务，向 RS 发送清理命令 | 正常 |
| AC-3.3 | WHEN Ark 空闲监视器回调 PreFreezeFlushForAllContexts THEN 对所有已脱离的 RSUIContext 执行 FlushImplicitTransaction 冲刷渲染命令 | 正常 |
| AC-3.4 | WHEN RSUIContext 被移除（RemoveRSUIContext）THEN 从管理集合中删除该上下文指针 | 正常 |
| AC-3.5 | WHEN PreFreeze 实例注册/注销 THEN RegisterPreFreezeInstance/UnregisterPreFreezeInstance 更新空闲冲刷回调注册表 | 正常 |

### US-4: Drawing Commands / Canvas Image 适配

作为一个 ACE 引擎开发者，我希望三种图像类型（DrawingImage/PixelMapImage/SvgCanvasImage）各自通过独立的适配路径将图像数据转换为 RS 绘制命令，以便 NG 渲染层能通过 Rosen 后端完成图像绘制。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN DrawingImage::DrawToRSCanvas 被调用 THEN 将 RSImage 绘制到 RSCanvas 上，支持 src/dst rect、borderRadius、nine-patch、lattice 等绘制模式 | 正常 |
| AC-4.2 | WHEN PixelMapImage::DrawToRSCanvas 被调用 THEN 将 PixelMap 数据绘制到 RSCanvas 上，支持圆角裁剪和自适应拉伸 | 正常 |
| AC-4.3 | WHEN SvgCanvasImage::DrawToRSCanvas 被调用 THEN 将 SvgDomBase 绘制到 RSCanvas 上，支持动画控制、填充色设置、平滑边缘和颜色过滤 | 正常 |
| AC-4.4 | WHEN AnimatedRSImage::DecodeImpl 被调用 THEN 通过 SkCodec 解码帧数据到 RSBitmap 再转换为 RSImage，继承 DrawingImage 的绘制路径 | 正常 |
| AC-4.5 | WHEN AnimatedPixmap::DecodeImpl 被调用 THEN 通过 SkCodec 解码帧数据到 PixelMap，继承 PixelMapImage 的绘制路径 | 正常 |
| AC-4.6 | WHEN DrawingImage::MakeRSImageFromPixmap 被调用 THEN 从 PixelMap 创建 RSImage 和 RSData 压缩数据，完成 PixelMap→RSImage 的桥接 | 正常 |
| AC-4.7 | WHEN ImagePainterUtils::ToRSRadius 被调用 THEN 将 BorderRadiusArray 转换为 RSPoint[] 四圆角参数 | 正常 |
| AC-4.8 | WHEN ImagePainterUtils::ClipRRect 被调用 THEN 在 RSCanvas 上执行圆角矩形裁剪 | 正常 |

### US-5: RS Modifier / Effect / Transition 适配

作为一个 ACE 引擎开发者，我希望 NG 的 Content/Overlay/Foreground 三层 Modifier 和 15+ 过渡效果类型通过各自的适配器桥接到 Rosen RS Modifier 系统，以便 NG 自定义绘制和组件过渡动画能通过 Rosen 后端执行。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN ContentModifierAdapter::Draw 被调用 THEN 委托到被包装的 NG ContentModifier 的绘制函数，在 RSContentStyleModifier 上下文中执行 | 正常 |
| AC-5.2 | WHEN OverlayModifierAdapter::Draw 被调用 THEN 委托到被包装的 NG OverlayModifier 的绘制函数，在 RSOverlayStyleModifier 上下文中执行 | 正常 |
| AC-5.3 | WHEN ForegroundModifierAdapter::Draw 被调用 THEN 委托到被包装的 NG ForegroundModifier 的绘制函数，在 RSForegroundStyleModifier 上下文中执行 | 正常 |
| AC-5.4 | WHEN 任意 ModifierAdapter 的 AttachProperties 被调用 THEN 将 NG 属性链到 RS 可动画属性（RSAnimatableProperty），使属性变化可驱动 RS 动画 | 正常 |
| AC-5.5 | WHEN RSNodeModifierImpl::AddProperty 被调用 THEN 将 RSPropertyBase 添加到 RSNodeModifier，使节点级属性（如 clip、transform、alpha）可被 RS 管线处理 | 正常 |
| AC-5.6 | WHEN RosenTransitionEffect::Appear 被调用 THEN 创建 RS 出现过渡效果并 Attach 到 RosenRenderContext | 正常 |
| AC-5.7 | WHEN RosenTransitionEffect::Disappear 被调用 THEN 创建 RS 消失过渡效果并 Attach 到 RosenRenderContext | 正常 |
| AC-5.8 | WHEN ConvertToRosenTransitionEffect(ChainedTransitionEffect) 被调用 THEN 递归转换链式过渡效果为 RosenTransitionEffect 组合链 | 正常 |
| AC-5.9 | WHEN 组合过渡效果通过 CombineWith 链接 THEN 多个过渡效果按顺序 Apply，支持混合类型组合 | 正常 |
| AC-5.10 | WHEN 过渡效果包含动画选项 THEN SetAnimationOption 将 RSAnimationTimingProtocol/RSAnimationTimingCurve 设置到 RS 过渡效果上 | 正常 |

### US-6: Visual Effect / Material Filter 适配

作为一个 ACE 引擎开发者，我希望 ACE 视效参数（模糊、毛玻璃、滤镜等）通过 RosenEffectConverter 转换为 RS NGFilter/NGShader，且预定义材质通过 ui_material_filter_creator 创建，以便 NG 视效系统能通过 Rosen 后端渲染。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN RosenEffectConverter::ConvertToFrostedGlassFilter 被调用 THEN 将 ACE 毛玻璃参数（blurRadius, scale, mode）转换为 RSNGFilterBase | 正常 |
| AC-6.2 | WHEN RosenEffectConverter::ConvertToFrostedGlassFilterEC 被调用 THEN 创建带 EC（Extended Canvas）子效果的毛玻璃 NGShader | 正常 |
| AC-6.3 | WHEN ui_material_filter_creator 按 Gentle Regular 预设创建 THEN 使用预定义常量（blurRadius=20, scale=7, mode=2）构建毛玻璃 RSNGFilter | 正常 |
| AC-6.4 | WHEN ui_material_filter_creator 按 Gentle Dark 预设创建 THEN 使用预定义暗色常量构建毛玻璃 RSNGFilter | 正常 |
| AC-6.5 | WHEN RosenRenderContext::UpdateBackgroundFilter 被调用 THEN 将 NG 背景滤镜设置到 rsNode_ 的 RSModifier 上 | 正常 |
| AC-6.6 | WHEN RosenRenderContext::UpdateForegroundFilter 被调用 THEN 将 NG 前景滤镜设置到 rsNode_ 的 RSModifier 上 | 正常 |
| AC-6.7 | WHEN RosenRenderContext::UpdateCompositingFilter 被调用 THEN 将 NG 合成滤镜设置到 rsNode_ 的 RSModifier 上 | 正常 |
| AC-6.8 | WHEN RosenRenderContext::UpdateUiMaterialFilter 被调用 THEN 将 UiMaterial/FrostedGlassParam 转换为 RSNGFilter 并设置到 rsNode_ | 正常 |
| AC-6.9 | WHEN LuminanceSamplingHelper::RegisterSamplingCallback 被调用 THEN 注册 Rosen 亮度采样回调，指定采样间隔和阈值 | 正常 |

### US-7: Animation Utils Rosen 桥接

作为一个 ACE 引擎开发者，我希望 AnimationUtils 的隐式动画、显式动画和弹簧动画接口通过 rosen_animation_utils.cpp 桥接到 RSNode 动画系统，且在无 ENABLE_ROSEN_BACKEND 时回退到空操作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN OpenImplicitAnimation 被调用 THEN 通过 RSNode::OpenImplicitAnimation 开启 RS 隐式动画事务 | 正常 |
| AC-7.2 | WHEN CloseImplicitAnimation 被调用 THEN 通过 RSNode::CloseImplicitAnimation 关闭 RS 隐式动画事务并提交所有累积属性变化 | 正常 |
| AC-7.3 | WHEN Animate 被调用 THEN 创建 RSAnimationTimingProtocol 和 RSAnimationTimingCurve，通过 RSNode 执行显式动画 | 正常 |
| AC-7.4 | WHEN CreateAnimator 被调用 THEN 创建 RS Animator 对象并关联到目标 RSNode | 正常 |
| AC-7.5 | WHEN InterpolateSpring 被调用 THEN 使用 RS 弹簧插值算法计算动画值 | 正常 |
| AC-7.6 | WHEN ENABLE_ROSEN_BACKEND 未定义 THEN fake_animation_utils.cpp 的所有方法为空操作，OpenImplicitAnimation/CloseImplicitAnimation 不产生任何 RS 调用 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-F01-01 | 单测：InitContext RSNode 类型验证 | rosen_render_context.cpp |
| AC-1.2 | R-2 | TASK-F01-01 | 单测：rsNode_ + rsUIDirector_ 初始化检查 | rosen_render_context.h |
| AC-1.3 | R-3 | TASK-F01-01 | 编译检查：ENABLE_ROSEN_BACKEND 宏条件 | render_context_creator.cpp |
| AC-1.4 | R-4 | TASK-F01-01 | 单测：SetRSUIContext 上下文更新 | rosen_render_context.cpp |
| AC-1.5 | R-5 | TASK-F01-01 | 单测：TextureExport 节点类型创建 | rosen_render_context.cpp |
| AC-2.1 | R-6 | TASK-F01-02 | 单测：FrameNodeChild 添加 | rosen_mixed_render_child_list.h |
| AC-2.2 | R-7 | TASK-F01-02 | 单测：PureRenderChild 添加 | rosen_mixed_render_child_list.h |
| AC-2.3 | R-8 | TASK-F01-02 | 单测：BuildTargetRSNodes 输出顺序 | rosen_mixed_render_child_list.cpp |
| AC-2.4 | R-9 | TASK-F01-02 | 单测：FrameNodeChild 移除 | rosen_mixed_render_child_list.cpp |
| AC-2.5 | R-10 | TASK-F01-02 | 单测：弱引用失效时 CanSwitchToSingleIfRenderNode | rosen_mixed_render_child_list.h |
| AC-3.1 | R-11 | TASK-F01-03 | 单测：RSUIContext 脱离管理 | detached_rs_node_manager.h |
| AC-3.2 | R-12 | TASK-F01-03 | 单测：PostDestructorTask 冲刷 | detached_rs_node_manager.cpp |
| AC-3.3 | R-13 | TASK-F01-03 | 集成测试：PreFreeze 空闲冲刷 | detached_rs_node_manager.cpp |
| AC-3.4 | R-14 | TASK-F01-03 | 单测：RemoveRSUIContext | detached_rs_node_manager.h |
| AC-3.5 | R-15 | TASK-F01-03 | 单测：PreFreeze 注册/注销 | detached_rs_node_manager.h |
| AC-4.1 | R-16 | TASK-F01-04 | 单测：DrawingImage DrawToRSCanvas | drawing_image.cpp |
| AC-4.2 | R-17 | TASK-F01-04 | 单测：PixelMapImage DrawToRSCanvas | pixelmap_image.cpp |
| AC-4.3 | R-18 | TASK-F01-04 | 单测：SvgCanvasImage DrawToRSCanvas | svg_canvas_image.cpp |
| AC-4.4 | R-19 | TASK-F01-04 | 单测：AnimatedRSImage DecodeImpl | animated_image.h |
| AC-4.5 | R-20 | TASK-F01-04 | 单测：AnimatedPixmap DecodeImpl | animated_image.h |
| AC-4.6 | R-21 | TASK-F01-04 | 单测：MakeRSImageFromPixmap | drawing_image.cpp |
| AC-4.7 | R-22 | TASK-F01-04 | 单测：ToRSRadius 转换 | image_painter_utils.h |
| AC-4.8 | R-23 | TASK-F01-04 | 单测：ClipRRect 裁剪 | image_painter_utils.h |
| AC-5.1 | R-24 | TASK-F01-05 | 单测：ContentModifierAdapter Draw | rosen_modifier_adapter.h |
| AC-5.2 | R-25 | TASK-F01-05 | 单测：OverlayModifierAdapter Draw | rosen_modifier_adapter.h |
| AC-5.3 | R-26 | TASK-F01-05 | 单测：ForegroundModifierAdapter Draw | rosen_modifier_adapter.h |
| AC-5.4 | R-27 | TASK-F01-05 | 单测：AttachProperties 链接 | rosen_modifier_adapter.h |
| AC-5.5 | R-28 | TASK-F01-05 | 单测：RSNodeModifierImpl AddProperty | rosen_modifier_adapter.h |
| AC-5.6 | R-29 | TASK-F01-06 | 单测：Appear 过渡 | rosen_transition_effect.cpp |
| AC-5.7 | R-30 | TASK-F01-06 | 单测：Disappear 过渡 | rosen_transition_effect.cpp |
| AC-5.8 | R-31 | TASK-F01-06 | 单测：链式过渡转换 | rosen_transition_effect.h |
| AC-5.9 | R-32 | TASK-F01-06 | 单测：CombineWith 组合 | rosen_transition_effect.cpp |
| AC-5.10 | R-33 | TASK-F01-06 | 单测：SetAnimationOption | rosen_transition_effect.cpp |
| AC-6.1 | R-34 | TASK-F01-07 | 单测：ConvertToFrostedGlassFilter | rosen_effect_converter.cpp |
| AC-6.2 | R-35 | TASK-F01-07 | 单测：ConvertToFrostedGlassFilterEC | rosen_effect_converter.cpp |
| AC-6.3 | R-36 | TASK-F01-07 | 单测：Gentle Regular 预设 | ui_material_filter_creator.cpp |
| AC-6.4 | R-37 | TASK-F01-07 | 单测：Gentle Dark 预设 | ui_material_filter_creator.cpp |
| AC-6.5 | R-38 | TASK-F01-07 | 单测：UpdateBackgroundFilter | rosen_render_context.cpp |
| AC-6.6 | R-39 | TASK-F01-07 | 单测：UpdateForegroundFilter | rosen_render_context.cpp |
| AC-6.7 | R-40 | TASK-F01-07 | 单测：UpdateCompositingFilter | rosen_render_context.cpp |
| AC-6.8 | R-41 | TASK-F01-07 | 单测：UpdateUiMaterialFilter | rosen_render_context.cpp |
| AC-6.9 | R-42 | TASK-F01-07 | 单测：LuminanceSampling 回调注册 | rosen_luminance_sampling_helper.h |
| AC-7.1 | R-43 | TASK-F01-08 | 单测：OpenImplicitAnimation | rosen_animation_utils.cpp |
| AC-7.2 | R-44 | TASK-F01-08 | 单测：CloseImplicitAnimation | rosen_animation_utils.cpp |
| AC-7.3 | R-45 | TASK-F01-08 | 单测：Animate | rosen_animation_utils.cpp |
| AC-7.4 | R-46 | TASK-F01-08 | 单测：CreateAnimator | rosen_animation_utils.cpp |
| AC-7.5 | R-47 | TASK-F01-08 | 单测：InterpolateSpring | rosen_animation_utils.cpp |
| AC-7.6 | R-48 | TASK-F01-08 | 编译检查：fake_animation_utils 空操作 | fake_animation_utils.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 RosenRenderContext::InitContext | 根据 SurfaceType 创建对应 RSNode（RSCanvasNode/RSSurfaceNode/RSTextureNode） | SurfaceType=Canvas→RSCanvasNode; Surface→RSSurfaceNode; Texture→RSTextureNode | AC-1.1 |
| R-2 | 行为 | InitContext 完成后检查 rsNode_ 和 rsUIDirector_ | rsNode_ 已创建，rsUIDirector_ 已通过 SetRSUIContext 或从 Window 获取初始化，rsNode_ 已 AttachToUITree | rsUIDirector_ 可为 nullptr（无窗口场景） | AC-1.2 |
| R-3 | 边界 | ENABLE_ROSEN_BACKEND 未定义时编译 | RenderContext::Create() 不返回 RosenRenderContext | 编译期静态选择 | AC-1.3 |
| R-4 | 行为 | 调用 SetRSUIContext | rsUIDirector_ 的上下文更新，后续 RS 调用使用新 RSUIContext | RSUIContext 可跨实例共享 | AC-1.4 |
| R-5 | 行为 | 节点设置 TextureExport 标志 | 创建 RSTextureNode + RSWindowKeyframeNode | TextureExport 需 RSSurfaceNode 配合 | AC-1.5 |
| R-6 | 行为 | AddChild(FrameNode类型子节点) | RosenMixedRenderChildList 添加 FRAME_NODE_CHILD 条目 | 弱引用 RSNode，来源为子节点的 RenderContext::rsNode_ | AC-2.1 |
| R-7 | 行为 | 添加纯渲染子节点 | RosenMixedRenderChildList 添加 PURE_RENDER_NODE 条目 | 弱引用 RSNode，来源为 Modifier 或纯渲染创建 | AC-2.2 |
| R-8 | 行为 | 调用 BuildTargetRSNodes | 按插入顺序组装有序 RSNode 子列表 | FrameNodeChild 和 PureRenderChild 交错排列，顺序由 InsertPureRenderChildAt/InsertFrameChildBefore 的调用顺序决定 | AC-2.3 |
| R-9 | 行为 | 移除 FrameNodeChild | 从混合列表删除条目，rsNode_->RemoveChild | 移除后需 RebuildFrame 更新子列表 | AC-2.4 |
| R-10 | 边界 | PureRenderChild 的 RSNode 弱引用失效 | CanSwitchToSingleIfRenderNode=true，列表可降级为单模式 | 仅当所有条目均为 FrameNodeChild 或所有 PureRenderChild 已失效时 | AC-2.5 |
| R-11 | 行为 | RSUIContext 从管线脱离 | DetachedRsNodeManager 将 RSUIContext* 加入管理集合 | 集合类型 unordered_set | AC-3.1 |
| R-12 | 行为 | 调用 PostDestructorTask | 通过后台 TaskRunnerAdapter 提交 FlushImplicitTransaction | 后台线程执行，不阻塞 UI 线程 | AC-3.2 |
| R-13 | 行为 | Ark 空闲监视器触发 PreFreezeFlushForAllContexts | 对所有已脱离 RSUIContext 执行 FlushImplicitTransaction | 仅在 RSS 报告前的空闲时段执行 | AC-3.3 |
| R-14 | 行为 | 调用 RemoveRSUIContext | 从管理集合删除 RSUIContext* 指针 | 删除后不再冲刷该上下文 | AC-3.4 |
| R-15 | 行为 | RegisterPreFreezeInstance/UnregisterPreFreezeInstance | 更新空闲冲刷回调注册表 | 注册后参与 PreFreeze 回调 | AC-3.5 |
| R-16 | 行为 | DrawingImage::DrawToRSCanvas 被调用 | 将 RSImage 绘制到 RSCanvas，支持 srcRect/dstRect/borderRadius/nine-patch/lattice | RSImage 持有 RSData 压缩数据 | AC-4.1 |
| R-17 | 行为 | PixelMapImage::DrawToRSCanvas 被调用 | 将 PixelMap 绘制到 RSCanvas，支持圆角裁剪和自适应拉伸 | CheckIfNeedForStretching 判断是否需拉伸 | AC-4.2 |
| R-18 | 行为 | SvgCanvasImage::DrawToRSCanvas 被调用 | 将 SvgDomBase 绘制到 RSCanvas，支持动画、填充色、平滑边缘和颜色过滤 | 动画帧由 SvgDomBase.ControlAnimation 管理 | AC-4.3 |
| R-19 | 行为 | AnimatedRSImage::DecodeImpl 被调用 | SkCodec 解码帧→RSBitmap→RSImage | 双继承 DrawingImage+AnimatedImage | AC-4.4 |
| R-20 | 行为 | AnimatedPixmap::DecodeImpl 被调用 | SkCodec 解码帧→PixelMap | 双继承 PixelMapImage+AnimatedImage | AC-4.5 |
| R-21 | 行为 | MakeRSImageFromPixmap 被调用 | 从 PixelMap 创建 RSImage + RSData | 静态工厂方法 | AC-4.6 |
| R-22 | 行为 | ToRSRadius 被调用 | BorderRadiusArray→RSPoint[4] | 四角参数，左上→右上→右下→左下 | AC-4.7 |
| R-23 | 行为 | ClipRRect 被调用 | 在 RSCanvas 上执行圆角矩形裁剪 | 裁剪区域为 borderRadius + contentRect | AC-4.8 |
| R-24 | 行为 | ContentModifierAdapter::Draw | 委托 NG ContentModifier 的绘制函数 | 继承 RSContentStyleModifier | AC-5.1 |
| R-25 | 行为 | OverlayModifierAdapter::Draw | 委托 NG OverlayModifier 的绘制函数 | 继承 RSOverlayStyleModifier | AC-5.2 |
| R-26 | 行为 | ForegroundModifierAdapter::Draw | 委托 NG ForegroundModifier 的绘制函数 | 继承 RSForegroundStyleModifier | AC-5.3 |
| R-27 | 行为 | AttachProperties 被调用 | 将 NG 属性链接到 RSAnimatableProperty | 属性变化驱动 RS 动画 | AC-5.4 |
| R-28 | 行为 | RSNodeModifierImpl::AddProperty | 将 RSPropertyBase 添加到 RSNodeModifier | 节点级属性（clip/transform/alpha 等） | AC-5.5 |
| R-29 | 行为 | RosenTransitionEffect::Appear | 创建 RS 出现过渡并 Attach 到 RenderContext | 出现效果在节点首次添加时触发 | AC-5.6 |
| R-30 | 行为 | RosenTransitionEffect::Disappear | 创建 RS 消失过渡并 Attach 到 RenderContext | 消失效果在节点移除时触发 | AC-5.7 |
| R-31 | 行为 | ConvertToRosenTransitionEffect(链式效果) | 递归转换 ChainedTransitionEffect→RosenTransitionEffect 组合链 | 递归深度等于链式效果层数 | AC-5.8 |
| R-32 | 行为 | CombineWith 链接过渡效果 | 多个效果按顺序 Apply | 顺序由链式结构决定 | AC-5.9 |
| R-33 | 行为 | SetAnimationOption 设置 | RSAnimationTimingProtocol + RSAnimationTimingCurve → RS 过渡效果 | curve 类型：EaseIn/EaseOut/EaseInOut/Linear/Spring 等 | AC-5.10 |
| R-34 | 行为 | ConvertToFrostedGlassFilter 被调用 | ACE 毛玻璃参数→RSNGFilterBase | blurRadius≥0, scale>0, mode=0/1/2 | AC-6.1 |
| R-35 | 行为 | ConvertToFrostedGlassFilterEC 被调用 | 创建带 EC 子效果的毛玻璃 NGShader | EC 支持扩展画布 | AC-6.2 |
| R-36 | 行为 | Gentle Regular 预设创建 | 预定义常量构建 RSNGFilter | blurRadius=20, scale=7, mode=2 | AC-6.3 |
| R-37 | 行为 | Gentle Dark 预设创建 | 暗色常量构建 RSNGFilter | 暗色参数由预设定义 | AC-6.4 |
| R-38 | 行为 | UpdateBackgroundFilter 被调用 | NG 背景滤镜→rsNode_ RSModifier | 滤镜类型：blur/filter/material | AC-6.5 |
| R-39 | 行为 | UpdateForegroundFilter 被调用 | NG 前景滤镜→rsNode_ RSModifier | 同背景滤镜接口 | AC-6.6 |
| R-40 | 行为 | UpdateCompositingFilter 被调用 | NG 合成滤镜→rsNode_ RSModifier | 合成滤镜影响整节点 | AC-6.7 |
| R-41 | 行为 | UpdateUiMaterialFilter 被调用 | UiMaterial/FrostedGlassParam→RSNGFilter→rsNode_ | 材质等级由 qualityLevel 决定 | AC-6.8 |
| R-42 | 行为 | RegisterSamplingCallback 被调用 | 注册 Rosen 亮度采样回调 | interval>0, threshold 数组 | AC-6.9 |
| R-43 | 行为 | OpenImplicitAnimation 被调用 | RSNode::OpenImplicitAnimation | 隐式事务开启 | AC-7.1 |
| R-44 | 行为 | CloseImplicitAnimation 被调用 | RSNode::CloseImplicitAnimation | 事务关闭并提交 | AC-7.2 |
| R-45 | 行为 | Animate 被调用 | 创建 RSAnimationTimingProtocol + RSAnimationTimingCurve，执行显式动画 | curve 类型影响动画曲线 | AC-7.3 |
| R-46 | 行为 | CreateAnimator 被调用 | 创建 RS Animator 对象 | Animator 可控制播放/暂停/停止 | AC-7.4 |
| R-47 | 行为 | InterpolateSpring 袾调用 | RS 弹簧插值算法计算动画值 | 参数：stiffness, damping, mass | AC-7.5 |
| R-48 | 边界 | ENABLE_ROSEN_BACKEND 未定义 | fake_animation_utils.cpp 全空操作 | OpenImplicitAnimation/CloseImplicitAnimation/Animate 等无任何 RS 调用 | AC-7.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.5 RenderContext 初始化 | 单测 + 编译检查 | RSNode 类型创建、双引用初始化、工厂切换 |
| VM-2 | AC-2.1~2.5 混合子列表 | 单测 | 子节点添加/移除、BuildTargetRSNodes 顺序、弱引用失效处理 |
| VM-3 | AC-3.1~3.5 DetachedRsNodeManager | 单测 + 集成测试 | RSUIContext 脱离管理、PostDestructorTask 冲刷、PreFreeze 回调 |
| VM-4 | AC-4.1~4.8 Canvas Image | 单测 | 三路径绘制、动画解码、圆角/裁剪转换 |
| VM-5 | AC-5.1~5.10 Modifier/Transition | 单测 | 三层 Draw 委托、AttachProperties 链接、15+ 过渡子类创建 |
| VM-6 | AC-6.1~6.9 Visual Effect/Material | 单测 | 滤镜转换、材质预设、背景/前景/合成滤镜设置 |
| VM-7 | AC-7.1~7.6 Animation Utils | 单测 + 编译检查 | 隐式/显式动画桥接、弹簧插值、空操作回退 |

## API 变更分析

N/A，本特性为框架内部适配层，无 SDK API 变更。

## 接口规格

### 接口定义

**RosenRenderContext::InitContext**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void RosenRenderContext::InitContext(RefPtr<NG::PipelineContext> context, bool isSurface)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| context | RefPtr<NG::PipelineContext> | 是 | 无 | pipeline 上下文，提供 RSUIDirector |
| isSurface | bool | 否 | false | true 时创建 RSSurfaceNode |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | isSurface=false | 创建 RSCanvasNode 作为 rsNode_ | AC-1.1 |
| 2 | isSurface=true | 创建 RSSurfaceNode 作为 rsNode_ | AC-1.1 |
| 3 | TextureExport=true | 创建 RSTextureNode + RSWindowKeyframeNode | AC-1.5 |

---

**RosenRenderContext::SetRSUIContext**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void RosenRenderContext::SetRSUIContext(std::shared_ptr<Rosen::RSUIContext> context)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| context | shared_ptr<RSUIContext> | 是 | 无 | RS UI 上下文，可为 nullptr |

---

**RosenMixedRenderChildList::BuildTargetRSNodes**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void RosenMixedRenderChildList::BuildTargetRSNodes(std::shared_ptr<Rosen::RSNode> parent)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| parent | shared_ptr<RSNode> | 是 | 无 | 父 RSNode，用于重建子列表 |

---

**DetachedRsNodeManager::PostDestructorTask**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void DetachedRsNodeManager::PostDestructorTask(std::function<void()>&& task)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| task | function<void()>&& | 是 | 无 | 清理任务，在后台线程执行 |

---

**ContentModifierAdapter::Draw**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ContentModifierAdapter::Draw(Rosen::RSDrawingContext& context)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| context | RSDrawingContext& | 是 | 无 | RS 绘制上下文，包含 RSCanvas |

---

**RosenEffectConverter::ConvertToFrostedGlassFilter**

| 属性 | 值 |
|------|-----|
| 函数签名 | `std::shared_ptr<Rosen::RSNGFilterBase> RosenEffectConverter::ConvertToFrostedGlassFilter(float blurRadius, float scale, int mode)` |
| 返回值 | `shared_ptr<RSNGFilterBase>` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-6.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| blurRadius | float | 是 | 无 | ≥0，模糊半径 |
| scale | float | 是 | 无 | >0，缩放比 |
| mode | int | 是 | 无 | 0/1/2，毛玻璃模式 |

---

**AnimationUtils::OpenImplicitAnimation**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void AnimationUtils::OpenImplicitAnimation(const RSAnimationTimingProtocol& protocol, const RSAnimationTimingCurve& curve)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-7.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| protocol | RSAnimationTimingProtocol | 是 | 无 | 动画时长/延迟等参数 |
| curve | RSAnimationTimingCurve | 是 | 无 | 动画曲线类型 |

## 兼容性声明

- **已有 API 行为变更:** 否，本特性为新增框架内部适配层
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9（Rosen 渲染后端自 API 9 引入）
- **API 版本号策略:** 本特性无 @since 标注（InnerApi）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ENABLE_ROSEN_BACKEND 编译宏 | RosenRenderContext 仅在 ENABLE_ROSEN_BACKEND 定义时可用，否则使用空回退 | AC-1.3, AC-7.6 |
| RSNode 生命周期由 RS 渲染服务管理 | rsNode_ 的创建/销毁必须通过 RSUIDirector 协调 | AC-1.2, AC-3.1~3.5 |
| 双引用架构（rsNode_ + rsUIDirector_） | rsNode_ 持节点引用，rsUIDirector_ 持管线引用，两者必须同步初始化 | AC-1.2 |
| Modifier 三层分离 | Content/Overlay/Foreground 各有独立 RSModifier 子类，不可混用 | AC-5.1~5.3 |
| DetachedRsNodeManager 单例 | 延迟销毁管理器为全局单例，跨实例共享 | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | RenderContext::InitContext ≤1ms | 单测计时 | rosen_render_context.cpp |
| 内存 | 每个 RosenRenderContext 持 1个 rsNode_ + 1个 rsUIDirector_ | 内存分析 | rosen_render_context.h |
| 可测试性 | 所有适配器可通过 Mock RSNode 进行单测 | 单测覆盖率 | UT 报告 |
| 自动化维测 | DetachedRsNodeManager PreFreeze 回调自动冲刷脱离节点 | 集成测试 | detached_rs_node_manager.cpp |

## 多设备适配声明

无差异。所有设备类型（手机/平板/折叠屏）使用相同的 Rosen 渲染后端适配代码。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 适配层不直接影响无障碍 | N/A |
| 大字体 | 否 | 适配层不直接影响大字体 | N/A |
| 深色模式 | 间接 | 毛玻璃材质预设区分 Regular/Dark 暗色变体 | AC-6.3~6.4 |
| 多窗口/分屏 | 是 | DetachedRsNodeManager 管理脱离管线的 RSNode，多窗口场景下节点脱离更频繁 | AC-3.1~3.5 |
| 多用户 | 否 | 适配层不直接影响多用户 | N/A |
| 版本升级 | 是 | ENABLE_ROSEN_BACKEND 宏在不同 API 版本下有不同行为 | AC-1.3, AC-7.6 |
| 生态兼容 | 否 | 适配层为框架内部 | N/A |

## 行为场景（可选，Gherkin）

> 本特性为 L2+（关键复杂度），使用 Gherkin 场景描述核心行为。

```gherkin
Feature: Rosen渲染后端适配
  作为 ACE 引擎开发者
  我想要 NG 渲染系统通过 Rosen 渲染后端完成节点映射和绘制
  以便组件树能在 OHOS 平台上正确渲染

  Scenario: RosenRenderContext 初始化创建 RSCanvasNode
    Given 一个 NG FrameNode 需要创建 RenderContext
    When 调用 RosenRenderContext::InitContext(pipeline, false)
    Then 创建 RSCanvasNode 作为 rsNode_
    And rsUIDirector_ 从 pipeline 的 Window 获取
    And rsNode_ 通过 AttachToUITree 注册到 RSUIDirector

  Scenario: 混合子列表 BuildTargetRSNodes 组装有序子列表
    Given 一个 RosenRenderContext 拥有混合子列表
    And 子列表包含 1个 FrameNodeChild 和 2个 PureRenderChild
    When 调用 BuildTargetRSNodes(parentRSNode)
    Then 按 InsertFrameChildBefore 和 InsertPureRenderChildAt 的调用顺序组装 RSNode 子列表
    And parentRSNode 的子列表更新为有序混合列表

  Scenario: DetachedRsNodeManager PreFreeze 空闲冲刷
    Given 3个 RSUIContext 已脱离管线并被 DetachedRsNodeManager 管理
    When Ark 空闲监视器触发 PreFreezeFlushForAllContexts
    Then 对所有 3个 RSUIContext 执行 FlushImplicitTransaction
    And RS 渲染服务收到清理命令

  Scenario: ContentModifierAdapter 委托绘制
    Given 一个 NG ContentModifier 需要在 Rosen 后端绘制
    When ContentModifierAdapter::Draw(RSDrawingContext) 被调用
    Then 委托到被包装的 NG ContentModifier 的绘制函数
    And 绘制结果反映在 RSContentStyleModifier 的 RSDrawingContext 上

  Scenario: ENABLE_ROSEN_BACKEND 未定义时空操作回退
    Given 编译配置中 ENABLE_ROSEN_BACKEND 未定义
    When 调用 AnimationUtils::OpenImplicitAnimation
    Then fake_animation_utils.cpp 的实现为空操作
    And 不产生任何 RS 调用
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（6个子能力集群，全量覆盖）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RosenRenderContext 双引用架构：rsNode_ 和 rsUIDirector_ 的初始化顺序和同步机制"
  - repo: "openharmony/ace_engine"
    query: "RosenMixedRenderChildList 混合子列表 BuildTargetRSNodes 的排序算法和帧/纯渲染节点交错规则"
  - repo: "openharmony/ace_engine"
    query: "DetachedRsNodeManager PreFreezeFlushForAllContexts 与 Ark 空闲监视器的集成机制"
  - repo: "openharmony/ace_engine"
    query: "Content/Overlay/Foreground 三层 ModifierAdapter 的 Draw 委托和 AttachProperties 属性链接机制"
  - repo: "openharmony/ace_engine"
    query: "RosenTransitionEffect 15+ 过渡效果子类的 Create 和 ConvertToRosenTransitionEffect 递归转换逻辑"
```

**关键文档：** ace_engine `frameworks/core/components_ng/render/adapter/` 目录下所有适配器源码
