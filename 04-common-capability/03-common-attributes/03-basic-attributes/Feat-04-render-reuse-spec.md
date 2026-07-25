# 特性规格

> Func-04-03-03-Feat-04 渲染与复用：固化 renderGroup/renderFit/freez/useEffect/reuseId/reuse 六个渲染与组件复用属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 渲染与复用 (Render & Reuse) |
| 特性编号 | Func-04-03-03-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8 起支持，API 10/12/14/21 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | renderGroup 规格补录 | 子树整体渲染单元优化 |
| ADDED | renderFit 规格补录 | 内容填充模式 16 枚举值 |
| ADDED | freeze 规格补录 | RS 渲染侧冻结标记（rsNode_->SetFreeze），与 UINode::SetFreeze/isFreeze_ 内部路径无关 |
| ADDED | useEffect 规格补录 | 效果回调机制 |
| ADDED | reuseId 规格补录 | 组件回收标识 |
| ADDED | reuse 规格补录 | 组件回收标记 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/03-basic-attributes/design.md` | Draft |

---

## 用户故事

### US-1: 设置 renderGroup 实现子树整体渲染优化

**作为** 应用开发者,
**我想要** 通过 `.renderGroup(true)` 将组件及其子树作为单个渲染单元,
**以便** 减少子节点单独重绘的次数，提升渲染性能。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.renderGroup(true)` THEN 组件及其整个子树被标记为单个渲染组（rsNode_->MarkNodeGroup(true)） | 正常 |
| AC-1.2 | WHEN renderGroup=true 且子节点产生 PROPERTY_UPDATE_RENDER 类型脏标记 THEN 子节点的脏标记不触发单独重绘，整个渲染组合并重绘 | 正常 |
| AC-1.3 | WHEN 调用 `.renderGroup(false)` THEN 渲染组标记取消，子节点恢复独立脏传播和单独重绘机制 | 恢复 |
| AC-1.4 | WHEN 调用 `.renderGroup(undefined)` THEN 重置 RenderGroup 属性（等同默认值 false） | 异常 |
| AC-1.5 | WHEN 组件设置了 renderGroup(true) THEN frameNode->SetApplicationRenderGroupMarked(true) 被调用，标记此组件由应用显式设置渲染组 | 正常 |
| AC-1.6 | WHEN 未设置 renderGroup THEN 默认行为由系统自适应渲染组（SuggestedRenderGroup）算法决定 | 正常 |
| AC-1.7 | WHEN 调用 `.excludeFromRenderGroup(true)` THEN 该组件及其子树从渲染组中排除，不参与组渲染 | 正常 |

### US-2: 设置 renderFit 控制内容填充模式

**作为** 应用开发者,
**我想要** 通过 `.renderFit(RenderFit.XXX)` 控制组件渲染内容在边界内的对齐和缩放方式,
**以便** 实现内容居中、拉伸填充、等比缩放等布局效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.renderFit(RenderFit.CENTER)` THEN 渲染内容在组件边界内居中，不拉伸不裁剪 | 正常 |
| AC-2.2 | WHEN 调用 `.renderFit(RenderFit.RESIZE_FILL)` THEN 渲染内容拉伸填满整个组件边界，可能变形 | 正常 |
| AC-2.3 | WHEN 调用 `.renderFit(RenderFit.RESIZE_COVER)` THEN 渲染内容等比缩放覆盖组件边界，超出部分裁剪 | 边界 |
| AC-2.4 | WHEN 调用 `.renderFit(RenderFit.RESIZE_CONTAIN)` THEN 渲染内容等比缩放使内容完全可见，可能留空 | 正常 |
| AC-2.5 | WHEN 调用 `.renderFit(RenderFit.TOP_LEFT)` THEN 渲染内容在组件边界内对齐到左上角，不拉伸不裁剪 | 正常 |
| AC-2.6 | WHEN 调用 `.renderFit(RenderFit.RESIZE_COVER_TOP_LEFT)` THEN 渲染内容等比缩放覆盖边界，锚定左上角裁剪 | 正常 |
| AC-2.7 | WHEN 调用 `.renderFit(RenderFit.RESIZE_COVER_BOTTOM_RIGHT)` THEN 渲染内容等比缩放覆盖边界，锚定右下角裁剪 | 正常 |
| AC-2.8 | WHEN 调用 `.renderFit(RenderFit.RESIZE_CONTAIN_TOP_LEFT)` THEN 渲染内容等比缩放完全可见，锚定左上角 | 正常 |
| AC-2.9 | WHEN 调用 `.renderFit(RenderFit.RESIZE_CONTAIN_BOTTOM_RIGHT)` THEN 渲染内容等比缩放完全可见，锚定右下角 | 正常 |
| AC-2.10 | WHEN 调用 `.renderFit(RenderFit.BOTTOM_RIGHT)` THEN 渲染内容在组件边界内对齐到右下角，不拉伸不裁剪 | 正常 |
| AC-2.11 | WHEN 调用 `.renderFit(undefined)` THEN 重置为默认 RenderFit 值（各组件默认值不同，如 XComponent 默认 RESIZE_FILL，Web 默认 TOP_LEFT） | 异常 |

### US-3: 设置 freeze 实现 RS 渲染侧子树冻结

**作为** 应用开发者,
**我想要** 通过 `.freeze(true)` 设置组件及其子树在 RS 渲染侧的冻结标记,
**以便** RS 渲染系统对冻结子树跳过绘制，减少渲染开销。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.freeze(true)` THEN rsNode_->SetFreeze(true) 被调用 | 正常 |
| AC-3.2 | WHEN freeze=true THEN rsNode_->SetFreeze(true) 使 RS 渲染系统对冻结子树跳过绘制；ACE 侧 Measure/Layout 管线不受影响 | 正常 |
| AC-3.3 | WHEN freeze=true THEN RenderContext::propFreeze_ 存储为 true | 正常 |
| AC-3.4 | WHEN freeze=true THEN 与 FrameNode::SetNodeFreeze() 无关（FrameNode::SetNodeFreeze 受 SystemProperties::IsPageTransitionFreeze 条件控制，仅在页面转场场景生效） | 边界 |
| AC-3.5 | WHEN 调用 `.freeze(false)` 解冻 THEN rsNode_->SetFreeze(false) 被调用 | 恢复 |
| AC-3.6 | WHEN freeze=false 解冻 THEN RS 渲染侧恢复绘制，子树节点重新参与渲染帧 | 恢复 |
| AC-3.7 | WHEN freeze=false 解冻 THEN RenderContext::propFreeze_ 重置为 false | 恢复 |
| AC-3.8 | WHEN freeze 属性设置 THEN 仅影响 rsNode_->SetFreeze，不触发 UINode::SetFreeze 内部路径 | 正常 |
| AC-3.9 | WHEN freeze=true THEN 不阻塞 VSync 刷新，不影响 ACE 侧 Measure/Layout 管线 | 边界 |

### US-4: 设置 reuseId 和 reuse 实现组件回收复用

**作为** 应用开发者,
**我想要** 通过 `.reuseId(id)` 和 `.reuse(true)` 标记组件可回收复用,
**以便** 在 LazyForEach 中复用节点，减少创建/销毁开销。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.reuseId(id)` THEN CustomNodeBase 的 reuseId_ 存储为 id | 正常 |
| AC-4.2 | WHEN LazyForEach 数据变更且节点设置了 reuseId THEN LazyForEachBuilder 按 reuseId 匹配回收节点池（recyclableNodeSet_）中的可复用节点 | 正常 |
| AC-4.3 | WHEN 新数据项的 reuseId 与回收池中某节点的 reuseId 匹配 THEN 该节点被复用而非重新创建 | 正常 |
| AC-4.4 | WHEN 回收节点被复用 THEN 触发 onReuseFunc 回调（而非 onAppear），开发者可在此回调中更新节点状态 | 正常 |
| AC-4.5 | WHEN 节点被回收进入回收池 THEN 触发 onRecycleFunc 回调，开发者可在此清理状态 | 正常 |
| AC-4.6 | WHEN 节点从回收池取出复用 THEN 从 recyclableNodeSet_ 中移除该节点 | 正常 |
| AC-4.7 | WHEN reuseId 不匹配 THEN 回收池中没有匹配节点，LazyForEach 创建新节点 | 正常 |
| AC-4.8 | WHEN 调用 `.reuseId(undefined)` THEN 重置 reuseId_ 为空字符串 | 异常 |
| AC-4.9 | WHEN TryReleaseExpiringNode(reuseId) 被调用 THEN 在 recyclableNodeSet_ 中查找 reuseId 匹配的过期节点，若找到则释放 | 正常 |

### US-5: 设置 useEffect 启用效果回调

**作为** 应用开发者,
**我想要** 通过 `.useEffect(true)` 启用组件的效果回调机制,
**以便** 系统在窗口焦点等状态变化时回调组件更新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.useEffect(true, EffectType.WINDOW_EFFECT)` THEN renderContext->UpdateUseEffect(true) 和 UpdateUseEffectType(WINDOW_EFFECT) 被调用 | 正常 |
| AC-5.2 | WHEN useEffect=true 且 effectType=WINDOW_EFFECT THEN pipeline->AddWindowActivateChangedCallback(frameNodeId) 注册窗口焦点回调 | 正常 |
| AC-5.3 | WHEN useEffect=false THEN pipeline->RemoveWindowActivateChangedCallback(frameNodeId) 移除窗口焦点回调 | 正常 |
| AC-5.4 | WHEN 调用 `.useEffect(true)` 不指定 effectType THEN effectType 默认为 EffectType::DEFAULT | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.7 | R-1, R-7 | 已有实现 | 单测 | `frameworks/core/components_ng/render/` |
| AC-2.1~2.11 | R-2, R-8 | 已有实现 | 单测 | 同上 |
| AC-3.1~3.9 | R-3, R-6 | 已有实现 | 单测 | `frameworks/core/components_ng/base/ui_node.cpp` |
| AC-4.1~4.9 | R-4, R-5 | 已有实现 | 单测 | `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp` |
| AC-5.1~5.4 | R-9 | 已有实现 | 单测 | `frameworks/core/components_ng/base/view_abstract.cpp` |

---

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 SetRenderGroup | renderGroup 存储在 RenderContext 的 propRenderGroup_，通过 ACE_UPDATE_RENDER_CONTEXT 更新；Rosen 路径调用 rsNode_->MarkNodeGroup(isRenderGroup) | RenderContext | AC-1.1 |
| R-2 | 行为 | 调用 SetRenderFit | renderFit 存储在 RenderContext 的 propRenderFit_，通过 ACE_UPDATE_RENDER_CONTEXT 更新；Rosen 路径调用 rsNode_->SetRenderFit(renderFit) | RenderContext | AC-2.1~2.11 |
| R-3 | 行为 | 调用 SetFreeze | freeze 存储在 RenderContext 的 propFreeze_，通过 ACE_UPDATE_RENDER_CONTEXT 更新；Rosen 路径调用 rsNode_->SetFreeze(isFreezed)，RS 渲染侧对冻结节点跳过绘制 | RenderContext | AC-3.1~3.9 |
| R-4 | 行为 | 调用 SetReuseId | reuseId 存储在 CustomNodeBase::reuseId_，LazyForEachBuilder 使用 recyclableNodeSet_（map<reuseId, map<key, WeakPtr<UINode>>）管理回收池 | CustomNodeBase + LazyForEachBuilder | AC-4.1~4.9 |
| R-5 | 行为 | RecycleNode 复用流程 | 回收：节点离开可视区 → onRecycleFunc → 进入 recyclableNodeSet_[reuseId][key]；复用：新数据到来 → 按 reuseId 匹配 → 从回收池取出 → onReuseFunc | LazyForEachBuilder | AC-4.3~4.6 |
| R-6 | 恢复 | freeze 从 true 变为 false | rsNode_->SetFreeze(false) 使 RS 侧恢复绘制 | RenderContext | AC-3.5~3.7 |
| R-7 | 恢复 | renderGroup 从 true 变为 false | 取消渲染组标记（rsNode_->MarkNodeGroup(false, isForced, includeProperty)），子节点恢复独立脏传播 | RosenRenderContext | AC-1.3 |
| R-8 | 边界 | RenderFit.RESIZE_COVER | 渲染内容等比缩放覆盖边界，超出部分裁剪；内容宽高比与边界不一致时必然裁剪 | render_context | AC-2.3 |
| R-9 | 行为 | 调用 SetUseEffect | useEffect 存储在 RenderContext 的 propUseEffect_；effectType 存储在 propUseEffectType_；WINDOW_EFFECT 类型额外注册 AddWindowActivateChangedCallback | RenderContext + Pipeline | AC-5.1~5.4 |
| R-10 | 边界 | freeze 与 FrameNode::SetNodeFreeze | CommonMethod.freeze() 仅设置 rsNode_->SetFreeze 属性，与 FrameNode::SetNodeFreeze()（受 SystemProperties::IsPageTransitionFreeze 控制、仅在页面转场场景生效）无关 | frame_node.cpp:2998 | AC-3.4 |
| R-11 | 边界 | freeze 不阻塞管线 | freeze 仅设置 rsNode 属性，不阻塞 VSync 刷新，不影响 ACE 侧 Measure/Layout 管线 | RosenRenderContext | AC-3.9 |
| R-12 | 行为 | renderGroup 脏聚合 | renderGroup=true 时子节点的 PROPERTY_UPDATE_RENDER 不触发 RS 单独重绘，整个 group 标记为脏后合并重绘 | Rosen RS 层 | AC-1.2 |
| R-13 | 行为 | RenderFit 16 枚举值 | CENTER=0, TOP=1, BOTTOM=2, LEFT=3, RIGHT=4, TOP_LEFT=5, TOP_RIGHT=6, BOTTOM_LEFT=7, BOTTOM_RIGHT=8, RESIZE_FILL=9, RESIZE_CONTAIN=10, RESIZE_CONTAIN_TOP_LEFT=11, RESIZE_CONTAIN_BOTTOM_RIGHT=12, RESIZE_COVER=13, RESIZE_COVER_TOP_LEFT=14, RESIZE_COVER_BOTTOM_RIGHT=15 | constants.h:871 | AC-2.1~2.11 |
| R-14 | 行为 | excludeFromRenderGroup | 排除自身及子树从渲染组，通过 ACE_UPDATE_NODE_RENDER_CONTEXT(ExcludeFromRenderGroup, exclude, frameNode) 更新 | RenderContext | AC-1.7 |
| R-15 | 异常 | renderGroup/renderFit/freeze/useEffect 传入 undefined | 调用 ResetRenderGroup/ResetRenderFit/ResetFreeze/ResetUseEffect 重置为默认值 | RenderContext | AC-1.4, AC-2.11, AC-3.5 |
| R-16 | 异常 | reuseId 传入 undefined | reuseId_ 重置为空字符串 | CustomNodeBase | AC-4.8 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, R-7, R-12, AC-1.1~1.7 | 单测 | renderGroup 标记、脏聚合、取消恢复 |
| VM-2 | R-2, R-13, AC-2.1~2.11 | 单测 | RenderFit 16 枚举值行为 |
| VM-3 | R-3, R-6, R-10, R-11, AC-3.1~3.9 | 单测 | freeze RS 渲染冻结标记、解冻恢复、用户/系统优先级 |
| VM-4 | R-4, R-5, AC-4.1~4.9 | 单测 | reuseId 匹配、RecycleNode 流程 |
| VM-5 | R-9, AC-5.1~5.4 | 单测 | useEffect 回调机制 |
| VM-6 | R-8, AC-2.3 | 单测 | RESIZE_COVER 裁剪行为 |
| VM-7 | 全量 | XTS/集成 | 端到端渲染与复用行为 |

---

## API 变更分析

N/A，已有能力补录，API 行为无变化。

### 新增 API（补录已有）

| API 签名 | 类型 | 功能 | @since | 权限要求 |
|----------|------|------|--------|----------|
| `renderGroup(value: boolean): T` | Public | 子树整体渲染单元 | 10 | - |
| `renderFit(fitMode: RenderFit): T` | Public | 内容填充模式 | 14 | - |
| `freeze(value: boolean): T` | Public | 子树 RS 渲染冻结标记 | 21 | - |
| `useEffect(useEffect: boolean, effectType?: EffectType): T` | Public | 效果回调机制 | 14 | - |
| `reuseId(id: string): T` | Public | 组件回收标识 | 8 | - |
| `excludeFromRenderGroup(value: boolean): T` | Public | 排除渲染组 | 10 | - |

**C-API (NDK) 接口：**

| 属性枚举 | 值格式 | 功能 | @since |
|----------|--------|------|--------|
| `NODE_RENDER_GROUP` | `.value[0].i32` (1 或 0) | 设置渲染组 | 10 |
| `NODE_RENDER_FIT` | `.value[0].i32` (ArkUI_RenderFit) | 设置内容填充模式 | 10 |

> 注：freeze、useEffect、reuseId/reuse 无独立 C-API (NDK) 属性枚举。freeze 通过 FrameNode::SetNodeFreeze 内部路径设置；reuseId 仅在 ArkTS/JS 层面可用（CustomNodeBase::SetReuseId）。

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `RenderFit` | `enum { CENTER=0, TOP=1, BOTTOM=2, LEFT=3, RIGHT=4, TOP_LEFT=5, TOP_RIGHT=6, BOTTOM_LEFT=7, BOTTOM_RIGHT=8, RESIZE_FILL=9, RESIZE_CONTAIN=10, RESIZE_CONTAIN_TOP_LEFT=11, RESIZE_CONTAIN_BOTTOM_RIGHT=12, RESIZE_COVER=13, RESIZE_COVER_TOP_LEFT=14, RESIZE_COVER_BOTTOM_RIGHT=15 }` | `constants.h:871` |
| `ArkUI_RenderFit` | C enum, 16 values (ARKUI_RENDER_FIT_CENTER=0 ... ARKUI_RENDER_FIT_RESIZE_COVER_BOTTOM_RIGHT=15) | `native_type.h:1238` |
| `EffectType` | `enum class { DEFAULT=0, WINDOW_EFFECT=1 }` | `blur_style_option.h:83` |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

---

## 接口规格

### renderGroup

- **存储**: RenderContext::propRenderGroup_（std::optional<bool>）
- **生效路径**: ViewAbstract::SetRenderGroup → ACE_UPDATE_RENDER_CONTEXT → RosenRenderContext::OnRenderGroupUpdate → rsNode_->MarkNodeGroup(isRenderGroup)
- **帧节点标记**: frameNode->SetApplicationRenderGroupMarked(true) 标记由应用显式设置
- **脏聚合**: renderGroup=true 时子树脏标记聚合到组级别，RS 层整体重绘
- **恢复**: renderGroup=false 时 MarkNodeGroup(false, isForced, includeProperty) 取消组标记，恢复独立脏传播

### freeze

- **存储**: RenderContext::propFreeze_（std::optional<bool>）
- **生效路径**: ViewAbstract::SetFreeze → ACE_UPDATE_RENDER_CONTEXT(Freeze) → RosenRenderContext::OnFreezeUpdate → rsNode_->SetFreeze(isFreezed)
- **与 FrameNode::SetNodeFreeze 的关系**: 本规格描述的 `CommonMethod.freeze()` 仅做 `rsNode_->SetFreeze` 属性设置，与 `FrameNode::SetNodeFreeze()` 内部路径无关。`FrameNode::SetNodeFreeze()` 受 `SystemProperties::IsPageTransitionFreeze()` 条件控制，仅在页面转场场景下生效，不属于通用属性的公开 API 范围
- **解冻恢复**: freeze=false → rsNode_->SetFreeze(false) 使 RS 侧恢复绘制

### reuseId

- **存储**: CustomNodeBase::reuseId_（std::string）
- **回收池**: LazyForEachBuilder::recyclableNodeSet_（std::map<reuseId, std::map<key, WeakPtr<UINode>>）
- **匹配**: 新数据到来时按 reuseId 匹配回收池中的可复用节点
- **生命周期**: 回收→onRecycleFunc；复用→onReuseFunc
- **释放**: TryReleaseExpiringNode(reuseId) 按 reuseId 查找过期节点释放

---

## 兼容性声明

- **已有 API 行为变更:** 无（均为补录）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（reuseId），API 10（renderGroup），API 14（renderFit、useEffect），API 21（freeze）
- **API 版本号策略:** @since 8 为 reuseId 基础，@since 10 为 renderGroup，@since 14 为 renderFit/useEffect，@since 21 为 freeze

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| renderGroup/renderFit/freeze/useEffect 存储在 RenderContext | 不参与 Measure/Layout 管线约束计算，仅影响 RS 节点渲染行为 | AC-1.1, AC-2.1, AC-3.1 |
| freeze 额外存储在 UINode::isFreeze_ | 不适用：CommonMethod.freeze() 仅设置 rsNode_->SetFreeze，与 UINode::isFreeze_/userFreeze_/UpdateChildrenFreezeState 无关 | AC-3.4 |
| reuseId 存储在 CustomNodeBase | 仅在 LazyForEach 管线中使用，不影响布局/渲染 | AC-4.1~4.9 |
| RenderFit 16 枚举值 | 包含 4 个基础对齐 + 4 角对齐 + 3 RESIZE 变体 + 5 RESIZE_* 角锚定变体 | AC-2.1~2.11 |
| renderGroup 应用级 vs 系统自适应 | 应用通过 renderGroup(true) 显式设置（applicationRenderGroupMarked_）；系统通过 SuggestedRenderGroup 算法自适应决定 | AC-1.5, AC-1.6 |
| freeze 用户级 vs 系统级 | 不适用：CommonMethod.freeze() 仅设置 rsNode 属性，UINode userFreeze_/isFreeze_ 是 FrameNode::SetNodeFreeze 内部机制 | AC-3.4 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | renderGroup=true 减少子树重绘次数：单次组重绘替代 N 次独立重绘 | benchmark | — |
| 性能 | freeze=true RS 侧跳过子树绘制，减少渲染开销 | benchmark | — |
| 性能 | reuseId 复用减少节点创建/销毁开销：复用 O(1) vs 创建 O(N) | benchmark | — |
| 性能 | renderGroup/renderFit/freeze/useEffect 设置 < 1μs（仅更新 RenderContext 属性） | benchmark | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | freeze=true RS 侧冻结子树绘制可能影响无障碍信息时效性 | freeze 场景 |
| RTL/国际化 | N/A | renderGroup/renderFit/freeze/reuseId 不涉及方向 | — |
| 大字体 | N/A | 渲染与复用属性不涉及字体缩放 | — |
| 深色模式 | N/A | 渲染与复用属性与颜色无关 | — |
| 多窗口/分屏 | 是 | freeze 在多窗口场景下对不可见窗口冻结 RS 渲染更有意义 | freeze 场景 |
| 版本升级 | 是 | freeze API 21 新增，renderGroup API 10 新增，renderFit API 14 新增 | API 版本 |
| 生态兼容 | 是 | C-API 提供 NODE_RENDER_GROUP 和 NODE_RENDER_FIT；freeze/reuseId 无独立 C-API | C-API 属性 |

---

## 行为场景

```gherkin
Feature: 渲染与复用
  作为 应用开发者
  我想要 通过声明式 API 控制渲染优化、内容填充、RS 渲染冻结和组件回收复用
  以便 实现高性能的 UI 渲染

  # ─── renderGroup ──────────────────────────────────

  Scenario: 设置 renderGroup 开启子树整体渲染
    Given 一个 Column 容器包含多个 Text 子组件
    When 设置 Column.renderGroup(true)
    Then Column 及所有子组件被标记为单个渲染组
    And 子组件属性变更触发整组重绘而非单独重绘

  Scenario: 取消 renderGroup 恢复独立脏传播
    Given 一个 Column 容器已设置 renderGroup(true)
    When 设置 Column.renderGroup(false)
    Then 渲染组标记取消
    And 子组件恢复独立脏传播和单独重绘机制

  Scenario: excludeFromRenderGroup 排除子树
    Given 一个 Column 设置了 renderGroup(true)
    And Column 内一个 Text 子组件设置了 excludeFromRenderGroup(true)
    When Column 渲染组重绘
    Then 该 Text 子组件不参与组渲染，仍独立重绘

  # ─── renderFit ─────────────────────────────────────

  Scenario: renderFit CENTER 居中
    Given 一个组件宽 300vp 高 200vp
    And 渲染内容尺寸为 100×50
    When 设置 .renderFit(RenderFit.CENTER)
    Then 渲染内容在组件边界内居中
    And 内容左上角位于 (100, 75)

  Scenario: renderFit RESIZE_FILL 拉伸填充
    Given 一个组件宽 300vp 高 200vp
    And 渲染内容原始尺寸为 100×50
    When 设置 .renderFit(RenderFit.RESIZE_FILL)
    Then 渲染内容拉伸为 300×200 填满组件边界
    And 内容宽高比可能变形

  Scenario: renderFit RESIZE_COVER 等比覆盖裁剪
    Given 一个组件宽 300vp 高 200vp
    And 渲染内容原始尺寸为 100×50（宽高比 2:1）
    When 设置 .renderFit(RenderFit.RESIZE_COVER)
    Then 渲染内容等比缩放至宽度 300vp（高度 150vp）
    And 垂直方向超出 200vp 的部分被裁剪（裁剪 25vp 上下各 12.5vp）

  Scenario: renderFit RESIZE_CONTAIN 等比包含留空
    Given 一个组件宽 300vp 高 200vp
    And 渲染内容原始尺寸为 100×50（宽高比 2:1）
    When 设置 .renderFit(RenderFit.RESIZE_CONTAIN)
    Then 渲染内容等比缩放至高度 200vp（宽度 400vp > 300vp）
    And 宽度受限为 300vp，高度缩放为 150vp
    And 垂直方向留空 50vp

  Scenario: renderFit TOP_LEFT 角对齐
    Given 一个组件宽 300vp 高 200vp
    And 渲染内容尺寸为 100×50
    When 设置 .renderFit(RenderFit.TOP_LEFT)
    Then 渲染内容对齐到组件左上角
    And 内容左上角位于 (0, 0)

  # ─── freeze ────────────────────────────────────────

  Scenario: freeze 设置 RS 渲染侧冻结
    Given 一个 Column 容器包含多个子组件
    When 设置 Column.freeze(true)
    Then rsNode_->SetFreeze(true) 被调用
    And RS 渲染侧对冻结子树跳过绘制
    And ACE 侧 Measure/Layout 管线不受影响
    And 与 FrameNode::SetNodeFreeze() 内部路径无关

  Scenario: freeze 解冻恢复 RS 渲染
    Given 一个 Column 容器已设置 freeze(true)
    When 设置 Column.freeze(false)
    Then rsNode_->SetFreeze(false) 被调用
    And RS 侧恢复绘制

  Scenario: freeze 仅设置 RS 属性，不阻塞管线
    Given 一个 Column 容器设置了 freeze(true)
    When Column 属性变更触发布局刷新
    Then ACE 侧 Measure/Layout 管线正常执行
    And 仅 RS 渲染侧因 SetFreeze(true) 跳过绘制

  # ─── reuseId ────────────────────────────────────────

  Scenario: reuseId 匹配回收节点
    Given 一个 LazyForEach 数据源
    And 数据项 A 使用 reuseId('card') 创建节点
    When 数据项 A 离开可视区
    Then 节点触发 onRecycleFunc 进入回收池 recyclableNodeSet_['card']['key_A']
    When 新数据项 B 到来且 reuseId='card'
    Then 回收池中 reuseId='card' 匹配的节点被取出复用
    And 触发 onReuseFunc 回调而非 onAppear

  Scenario: reuseId 不匹配时创建新节点
    Given 一个 LazyForEach 回收池中有 reuseId='card' 的节点
    When 新数据项到来且 reuseId='list'（不匹配）
    Then 回收池中无 'list' 匹配节点
    And LazyForEach 创建全新节点

  # ─── useEffect ──────────────────────────────────────

  Scenario: useEffect WINDOW_EFFECT 注册窗口焦点回调
    Given 一个组件设置了 .useEffect(true, EffectType.WINDOW_EFFECT)
    When 窗口焦点状态变化
    Then pipeline 通过 AddWindowActivateChangedCallback 回调组件
    And 组件 RenderContext 的 useEffect 状态更新

  Scenario: useEffect 关闭移除回调
    Given 一个组件已设置 .useEffect(true, EffectType.WINDOW_EFFECT)
    When 设置 .useEffect(false)
    Then pipeline->RemoveWindowActivateChangedCallback 移除回调
    And 组件不再响应窗口焦点变化
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（renderGroup/renderFit/freeze/useEffect/reuseId/reuse 六个属性；不含 SuggestedRenderGroup/RenderStrategy/UseShadowBatching/UseUnionEffect/ExcludeFromRenderGroup 独立规格——ExcludeFromRenderGroup 仅作为 renderGroup 附属提及）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致
- [x] RenderFit 枚举值基于源码 constants.h:871 实际 16 值（非 10 值），prompt 中 START/END/TOP_START/TOP_END/COVER 在 RenderFit 枚举中不存在
- [x] freeze 仅设置 rsNode_->SetFreeze 属性，基于 ViewAbstract::SetFreeze → RosenRenderContext::OnFreezeUpdate 源码验证
- [x] reuseId C-API 不存在（仅 ArkTS 层面），已在 C-API 表格中标注

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "renderGroup MarkNodeGroup render group subtree optimization"
  - repo: "openharmony/ace_engine"
    query: "RenderFit enum content fitting RESIZE_FILL RESIZE_COVER RESIZE_CONTAIN"
  - repo: "openharmony/ace_engine"
    query: "freeze ViewAbstract SetFreeze RosenRenderContext OnFreezeUpdate rsNode SetFreeze propFreeze"
  - repo: "openharmony/ace_engine"
    query: "reuseId LazyForEach recyclableNodeSet RecycleNode onReuseFunc onRecycleFunc"
  - repo: "openharmony/ace_engine"
    query: "useEffect EffectType WINDOW_EFFECT AddWindowActivateChangedCallback"
```

**关键文档：**
- SDK API 知识库：`docs/sdk/ArkUI_SDK_API_Knowledge_Base.md`
- 架构设计：`specs/04-common-capability/03-common-attributes/03-basic-attributes/design.md`
- RenderFit 枚举定义：`frameworks/core/components/common/layout/constants.h:871`
- ArkUI_RenderFit C 枚举定义：`interfaces/native/native_type.h:1238`
- UINode freeze 实现：`frameworks/core/components_ng/base/ui_node.cpp:1133`
- RosenRenderContext 渲染属性：`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:7734, 3639`
- LazyForEach 回收池：`frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp:1533`
