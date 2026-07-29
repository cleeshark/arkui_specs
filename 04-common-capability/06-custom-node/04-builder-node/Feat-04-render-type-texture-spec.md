# 特性规格

> Func-04-06-04-Feat-04 BuilderNode 渲染类型与纹理：固化 NodeRenderType 纹理生效条件、surfaceId、enableMinimized 行为。主角 ArkTS BuilderNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | BuilderNode 渲染类型与纹理 |
| 特性编号 | Func-04-06-04-Feat-04 |
| 所属 Epic | 自定义节点能力 / BuilderNode |
| 优先级 | P2 |
| 目标版本 | API 11（NodeRenderType 起始）；enableMinimized API 26.0.0 staticonly |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | NodeRenderType 纹理生效条件 | API 11 |
| ADDED | 支持纹理根组件列表（API12 扩展） | API 11-12 |
| ADDED | enableMinimized 最小化 FrameNode | API 26.0.0 staticonly |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/04-builder-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/BuilderNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 纹理渲染生效条件
**作为** 应用开发者，**我想要** 了解 RENDER_TYPE_TEXTURE 的生效条件。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN RenderOptions.type=RENDER_TYPE_TEXTURE 且为 XComponentNode 或根为自定义组件的 BuilderNode THEN 纹理渲染生效 | 正常 |
| AC-1.2 | WHEN 根组件不在支持列表 THEN changeRenderType 返回 false（静默无抛错，纹理渲染不应用） | 边界 |
| AC-1.3 | WHEN type=RENDER_TYPE_DISPLAY（默认）THEN 普通显示渲染 | 正常 |

### US-2: surface 与最小化
**作为** 应用开发者，**我想要** 配置纹理接收 surface 与最小化 FrameNode。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN RenderOptions.surfaceId 设值且 type=TEXTURE THEN 作为纹理接收 surface（如 OH_NativeImage） | 正常 |
| AC-2.2 | WHEN 非 TEXTURE THEN surfaceId 不应用（changeRenderType 不涉及 surfaceId 设置） | 边界 |
| AC-2.3 | WHEN 静态 RenderOptions.enableMinimized=true THEN getFrameNode 返回最小化 FrameNode（暴露最小能力集） | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.3 | R-1,R-2,R-3 | 单测 | BuilderNode.d.ts NodeRenderType |
| AC-2.1..2.3 | R-4,R-5,R-6 | 单测 | BuilderNode.d.ts RenderOptions |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | type=TEXTURE 且 XComponentNode 或根为自定义组件的 BuilderNode | 纹理渲染生效 | 支持根组件列表 | AC-1.1 |
| R-2 | 边界 | 根组件不在支持列表 | changeRenderType 返回 false（静默无抛错，纹理不应用） | Button/Text/Image/Web 等；API12 扩展 | AC-1.2 |
| R-3 | 行为 | type=DISPLAY（默认） | 普通显示渲染 | 默认值 | AC-1.3 |
| R-4 | 行为 | surfaceId + TEXTURE | 作为纹理接收 surface | 如 OH_NativeImage | AC-2.1 |
| R-5 | 边界 | 非 TEXTURE | surfaceId 不应用（changeRenderType 不涉及 surfaceId） | — | AC-2.2 |
| R-6 | 边界 | enableMinimized(staticonly)=true | getFrameNode 返最小化 FrameNode | 默认 false；API26 staticonly | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 纹理生效 | 单测 | TEXTURE 条件、根组件列表 |
| VM-2 | R-4..R-6 surface/最小化 | 单测 | surfaceId 仅 TEXTURE、enableMinimized staticonly |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| NodeRenderType | Public | DISPLAY=0 / TEXTURE=1 | — | — | 渲染类型枚举 | AC-1 |
| RenderOptions.type/surfaceId | Public | NodeRenderType / string | — | — | 渲染类型与 surface | AC-1,2 |
| RenderOptions.enableMinimized | Public(staticonly) | boolean | — | — | 最小化 FrameNode | AC-2.3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**渲染类型与纹理**

| 属性 | 值 |
|------|-----|
| 函数签名 | `NodeRenderType { RENDER_TYPE_DISPLAY=0, RENDER_TYPE_TEXTURE=1 }`; `RenderOptions { type?, surfaceId?, enableMinimized?(staticonly) }` |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1,2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | TEXTURE + 支持根 | 纹理生效 | AC-1.1 |
| 2 | 根不支持 | changeRenderType 返回 false（静默无抛错） | AC-1.2 |
| 3 | DISPLAY | 普通渲染 | AC-1.3 |
| 4 | surfaceId+TEXTURE | 纹理接收 surface | AC-2.1 |
| 5 | enableMinimized | 最小化 FrameNode | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** NodeRenderType/RenderOptions API 11；支持根组件 API12 扩展；enableMinimized API 26.0.0 staticonly。
- **API 版本号策略:** 逐项 @since；enableMinimized staticonly。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| TEXTURE 根组件限制 | 仅特定根组件生效 | BuilderNode.d.ts |
| enableMinimized 仅静态 | 动态无 | BuilderNode.static.d.ets |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| TEXTURE 生效条件 | XComponentNode 或根为自定义组件的 BuilderNode | AC-1.1 |
| surfaceId 依赖 TEXTURE | 非 TEXTURE surfaceId 不应用 | AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 纹理渲染独立 surface | 单测 | BuilderNode.d.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | 根组件 API12 扩展、enableMinimized API26 | AC-1.2,2.3 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（渲染类型纹理；不含复用回收 Feat-05）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "BuilderNode.d.ts NodeRenderType TEXTURE 生效条件与支持根组件列表"
  - repo: "openharmony/arkui_ace_engine"
    query: "RenderOptions.enableMinimized staticonly 最小化 FrameNode 能力集"
```
