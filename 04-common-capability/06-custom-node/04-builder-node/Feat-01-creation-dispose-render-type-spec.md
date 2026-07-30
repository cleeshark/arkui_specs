# 特性规格

> Func-04-06-04-Feat-01 BuilderNode 创建、释放与渲染类型：固化 constructor/dispose/isDisposed 与 RenderOptions/NodeRenderType 的行为规格。主角 ArkTS BuilderNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | BuilderNode 创建、释放与渲染类型 |
| 特性编号 | Func-04-06-04-Feat-01 |
| 所属 Epic | 自定义节点能力 / BuilderNode |
| 优先级 | P1 |
| 目标版本 | API 11（dynamic 起始）；isDisposed API 20；静态 @since 23；enableMinimized API 26.0.0 staticonly |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | constructor/dispose | API 11 |
| ADDED | isDisposed | API 20 |
| ADDED | RenderOptions/NodeRenderType | API 11；enableMinimized API 26.0.0 staticonly |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/04-builder-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/BuilderNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 创建 BuilderNode
**作为** 应用开发者，**我想要** 用 UIContext + 渲染选项创建 BuilderNode，
**以便** 使用该节点。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `new BuilderNode(uiContext, options?)` 且 uiContext 有效 THEN 返回实例，绑定 UIContext；注册 GC 终结回收 | 正常 |
| AC-1.2 | WHEN uiContext 无效 THEN 创建失败 | 异常 |
| AC-1.3 | WHEN options.selfIdealSize 未显式设置且内容嵌入其他 RenderNode THEN 根子树默认尺寸 [0,0] | 边界 |

### US-2: 释放与有效性
**作为** 应用开发者，**我想要** 释放引用并查询有效性，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `dispose()` THEN 释放前后端引用；幂等 | 正常 |
| AC-2.2 | WHEN `isDisposed()` THEN 返回是否已释放（dispose 后 true） | 正常 |
| AC-2.3 | WHEN dispose 后调用其他 API THEN 可能崩溃或返默认值（SDK NOTE 明示） | 异常 |

### US-3: 渲染选项与类型
**作为** 应用开发者，**我想要** 通过 RenderOptions 配置理想尺寸/渲染类型/surface，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `RenderOptions.selfIdealSize` THEN 设置理想尺寸（默认 {0,0}） | 正常 |
| AC-3.2 | WHEN `RenderOptions.type` THEN 设置渲染类型（默认 RENDER_TYPE_DISPLAY=0） | 正常 |
| AC-3.3 | WHEN `RenderOptions.surfaceId` THEN 设置纹理接收 surface（仅 TEXTURE 生效，默认 ""） | 边界 |
| AC-3.4 | WHEN 静态 `RenderOptions.enableMinimized=true`（默认 false，@since 26.0.0 staticonly）THEN BuilderNode 设 `__isWeak=true`（BuilderNode.ets:361），getFrameNode 返回 `BuilderRootWeakFrameNode`（FrameNode.ets:1210）——一个轻量代理 FrameNode，`isMinimized()` 返回 true、`getRenderNode()` 返回 null、`getChild()` 返回 null（能力最小集，SDK 文档 "smallest set of capabilities"） | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.3 | R-1,R-2,R-3 | 单测 | builder_node.ts constructor |
| AC-2.1..2.3 | R-4,R-5,R-6 | 单测 | builder_node.ts dispose/isDisposed |
| AC-3.1..3.4 | R-7,R-8,R-9,R-10 | 单测 | BuilderNode.d.ts RenderOptions |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `new BuilderNode(uiContext, options?)` 有效 | 返回实例，绑定 UIContext，注册 GC 回收 | uiContext 须有效 | AC-1.1 |
| R-2 | 异常 | uiContext 无效 | 创建失败 | — | AC-1.2 |
| R-3 | 边界 | selfIdealSize 未设且嵌入 RenderNode | 根子树默认 [0,0] | — | AC-1.3 |
| R-4 | 行为 | `dispose()` | 释放前后端引用 | 幂等 | AC-2.1 |
| R-5 | 行为 | `isDisposed()` | 返回是否已释放 | — | AC-2.2 |
| R-6 | 异常 | dispose 后调其他 API | 可能崩溃或返默认值 | SDK NOTE | AC-2.3 |
| R-7 | 行为 | RenderOptions.selfIdealSize | 设置理想尺寸 | 默认 {0,0} | AC-3.1 |
| R-8 | 行为 | RenderOptions.type | 设置渲染类型 | 默认 DISPLAY(0) | AC-3.2 |
| R-9 | 边界 | RenderOptions.surfaceId | 仅 TEXTURE 生效 | 默认 "" | AC-3.3 |
| R-10 | 边界 | enableMinimized（staticonly） | BuilderNode 设 __isWeak=true，getFrameNode 返回 BuilderRootWeakFrameNode（轻量代理：isMinimized=true、getRenderNode=null、getChild=null） | 默认 false；@since 26.0.0 staticonly | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 创建 | 单测 | GC 注册、selfIdealSize 默认 |
| VM-2 | R-4..R-6 释放 | 单测 | 幂等、isDisposed |
| VM-3 | R-7..R-10 渲染选项 | 单测 | 默认值、enableMinimized staticonly |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| constructor(uiContext, options?) | Public | uiContext: UIContext; options?: RenderOptions | BuilderNode | 401 | 创建 | AC-1 |
| dispose() | Public | — | void | — | 释放 | AC-2 |
| isDisposed() | Public | — | boolean | — | 释放状态 | AC-2 |
| RenderOptions | Public | {selfIdealSize?, type?, surfaceId?, enableMinimized?(static)} | — | — | 渲染选项 | AC-3 |
| NodeRenderType | Public | RENDER_TYPE_DISPLAY=0 / RENDER_TYPE_TEXTURE=1 | — | — | 渲染类型枚举 | AC-3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**constructor / dispose / isDisposed**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor(uiContext: UIContext, options?: RenderOptions)`; `dispose(): void`; `isDisposed(): boolean` |
| 返回值 | BuilderNode / void / boolean |
| 开放范围 | Public |
| 错误码 | 401(uiContext 无效) |
| 关联 AC | AC-1,2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | uiContext 有效 | 返回实例+GC 注册 | AC-1.1 |
| 2 | uiContext 无效 | 创建失败 | AC-1.2 |
| 3 | dispose | 释放引用，幂等 | AC-2.1 |
| 4 | dispose 后调 API | 崩溃或默认值 | AC-2.3 |

**RenderOptions / NodeRenderType**

| 属性 | 值 |
|------|-----|
| 类型 | `RenderOptions { selfIdealSize?: Size; type?: NodeRenderType; surfaceId?: string; enableMinimized?: boolean(staticonly) }`; `NodeRenderType { DISPLAY=0, TEXTURE=1 }` |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | selfIdealSize | 设理想尺寸（默认 {0,0}） | AC-3.1 |
| 2 | type | 设渲染类型（默认 DISPLAY） | AC-3.2 |
| 3 | surfaceId | 仅 TEXTURE 生效（默认 ""） | AC-3.3 |
| 4 | enableMinimized(staticonly) | getFrameNode 返回 BuilderRootWeakFrameNode（轻量代理：isMinimized=true、getRenderNode=null、getChild=null） | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** constructor/dispose/RenderOptions/NodeRenderType API 11；isDisposed API 20；静态 @since 23；enableMinimized API 26.0.0 staticonly。
- **API 版本号策略:** 逐 API @since；enableMinimized staticonly。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| 嵌入 RenderNode 时 selfIdealSize 须显式 | 否则默认 [0,0] | BuilderNode.d.ts |
| enableMinimized 仅静态 | 动态无此选项 | BuilderNode.static.d.ets |
| dispose 后崩溃 | SDK NOTE 警告 | BuilderNode.d.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| GC 终结回收 | 构造时注册 BuilderNodeFinalizationRegisterProxy | AC-1.1 |
| surfaceId 仅 TEXTURE | 非 TEXTURE 时 surfaceId 不应用 | AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | dispose 幂等 | 单测 | builder_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | isDisposed(20)/enableMinimized(26) 演进 | AC-2.2,3.4 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（创建释放渲染类型；不含 build Feat-02）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "builder_node.ts BuilderNode constructor + BuilderNodeFinalizationRegisterProxy GC 注册"
  - repo: "openharmony/arkui_ace_engine"
    query: "BuilderNode.d.ts RenderOptions/NodeRenderType 与 enableMinimized staticonly"
```
