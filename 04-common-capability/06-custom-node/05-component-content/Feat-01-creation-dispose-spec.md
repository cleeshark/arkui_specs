# 特性规格

> Func-04-06-05-Feat-01 ComponentContent 创建与释放：固化 constructor(3 重载)/dispose/isDisposed/isTransferred。主角 ArkTS ComponentContent。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ComponentContent 创建与释放 |
| 特性编号 | Func-04-06-05-Feat-01 |
| 所属 Epic | 自定义节点能力 / ComponentContent |
| 优先级 | P1 |
| 目标版本 | API 12（constructor/dispose）；isDisposed API 20；isTransferred API 24；静态 @since 23-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | constructor(3 重载)/dispose | API 12 |
| ADDED | isDisposed | API 20（静态 26） |
| ADDED | isTransferred | API 24（静态 26） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/05-component-content/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/ComponentContent.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 创建 ComponentContent
**作为** 应用开发者，**我想要** 用 UIContext + WrappedBuilder 创建 ComponentContent。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `new ComponentContent(uiContext, builder)` THEN 返回实例，内部建 BuilderNode 并 build | 正常 |
| AC-1.2 | WHEN `new ComponentContent(uiContext, builder, args)` THEN 用 args 构建 | 正常 |
| AC-1.3 | WHEN `new ComponentContent(uiContext, builder, args, options)` THEN 用 BuildOptions 配置 | 正常 |
| AC-1.4 | WHEN uiContext 无效 THEN 创建失败 | 异常 |

### US-2: 释放与有效性
**作为** 应用开发者，**我想要** 释放引用并查询有效性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `dispose()` THEN 释放前后端引用（fire 生命周期回调 + detach + 释放 BuilderNode）；幂等 | 正常 |
| AC-2.2 | WHEN `isDisposed()` THEN 返回是否已释放（dispose 后且 BuilderNode 已释放时 true） | 正常 |
| AC-2.3 | WHEN 未释放前端引用 THEN 警告内存泄漏风险 | 边界 |

### US-3: 转换标记
**作为** 应用开发者，**我想要** 查询是否经动态静态转换产生。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `isTransferred()` THEN 返回是否经 transferDynamic 转换产生（普通实例 false，Trans 变体 true） | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2 | 单测 | component_content.ts constructor |
| AC-2.1..2.3 | R-3,R-4,R-5 | 单测 | component_content.ts dispose/isDisposed |
| AC-3.1 | R-6 | 单测 | component_content.ts isTransferred |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | constructor(uiContext, builder[, args, options]) 有效 | 返回实例，内部建 BuilderNode 并 build | uiContext 须有效 | AC-1.1,1.2,1.3 |
| R-2 | 异常 | uiContext 无效 | 创建失败 | — | AC-1.4 |
| R-3 | 行为 | dispose() | 释放引用（生命周期回调+detach+释放 BuilderNode） | 幂等 | AC-2.1 |
| R-4 | 行为 | isDisposed() | 返回是否已释放 | dispose 后 + BuilderNode 已释放 | AC-2.2 |
| R-5 | 边界 | 未释放前端引用 | 警告内存泄漏 | SDK 警告 | AC-2.3 |
| R-6 | 行为 | isTransferred() | 返回是否经 transferDynamic 转换 | 普通实例 false，Trans 变体 true | AC-3.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-2 创建 | 单测 | 3 重载、uiContext 校验 |
| VM-2 | R-3..R-5 释放 | 单测 | 幂等、isDisposed、泄漏警告 |
| VM-3 | R-6 转换标记 | 单测 | false/true |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| constructor(uiContext, builder[, args, options]) | Public | UIContext, WrappedBuilder, args?, BuildOptions? | ComponentContent | 401 | 创建 | AC-1 |
| dispose() | Public | — | void | — | 释放 | AC-2 |
| isDisposed() | Public | — | boolean | — | 释放状态 | AC-2 |
| isTransferred() | Public | — | boolean | — | 转换标记 | AC-3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**constructor / dispose / isDisposed / isTransferred**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor(uiContext, builder[, args, options])`; `dispose(): void`; `isDisposed(): boolean`; `isTransferred(): boolean` |
| 返回值 | ComponentContent / void / boolean / boolean |
| 开放范围 | Public |
| 错误码 | 401(uiContext 无效) |
| 关联 AC | AC-1,2,3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | constructor 有效 | 返回实例，内部建 BuilderNode | AC-1.1 |
| 2 | uiContext 无效 | 创建失败 | AC-1.4 |
| 3 | dispose | 释放引用，幂等 | AC-2.1 |
| 4 | isDisposed | 返回释放状态 | AC-2.2 |
| 5 | isTransferred | 返回转换标记 | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** constructor/dispose API 12；isDisposed API 20（静态 26）；isTransferred API 24（静态 26）；静态 @since 23。
- **API 版本号策略:** 逐 API @since；静态 isDisposed/isTransferred @since 26。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| 未释放前端引用泄漏 | SDK 警告 | ComponentContent.d.ts |
| 静态 isDisposed/isTransferred @since 26 | 版本差异 | .static.d.ets |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 内部用 BuilderNode | 创建时建 BuilderNode 并 build | AC-1.1 |
| 幂等 dispose | 重复 dispose 安全 | AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | dispose 幂等 | 单测 | component_content.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | isDisposed(20)/isTransferred(24) 演进 | AC-2.2,3.1 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（创建释放；不含更新 Feat-02）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "component_content.ts ComponentContent constructor 内部建 BuilderNode + dispose 生命周期回调"
```
