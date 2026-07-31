# 特性规格

> Func-04-10-01-Feat-03 固化 UIContext Builder 与 ComponentContent 的离屏截图调用链。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIContext Builder 与 ComponentContent 离屏截图 |
| 特性编号 | Func-04-10-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Builder API 12；ComponentContent API 18 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | UIContext 离屏截图 | 补录 Builder/ComponentContent 两种离屏节点来源。 |

## 输入文档

- `design.md`
- `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts:4080-4185,4274-4314`
- `frameworks/bridge/declarative_frontend/ng/frontend_delegate_declarative_ng.cpp:1487-1528`
- `frameworks/core/components_ng/render/adapter/component_snapshot.cpp:468-598`

## 用户故事

### US-1: 从 Builder 构建离屏截图

作为应用开发者，我想要从 CustomBuilder 生成 PixelMap，而不把组件挂载到可见树。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `createFromBuilder(builder, callback|delay?, checkImageStatus?, options?)` THEN SDK 提供 callback 与 Promise 重载。 | 正常 |
| AC-1.2 | WHEN Delegate 完成 builder THEN 调用 `ComponentSnapshot::Create`，处理离屏节点并请求 Rosen capture。 | 正常 |
| AC-1.3 | WHEN delay/checkImageStatus 未传 THEN 使用 `SnapshotParam` 的既有默认构造行为。 | 边界 |

### US-2: 从 ComponentContent 构建离屏截图

作为应用开发者，我想要从 API 18 ComponentContent 创建离屏截图。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 `createFromComponent(content, delay?, checkImageStatus?, options?)` THEN 返回 Promise<PixelMap>。 | 正常 |
| AC-2.2 | WHEN content 进入 Delegate THEN 调用 `CreateSnapshotFromComponent` 后复用 ComponentSnapshot::Create。 | 正常 |
| AC-2.3 | WHEN 静态前端调用其声明 THEN Promise 返回类型可为 `Promise<PixelMap> | null`，不得写成动态的严格非空契约。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-3 | SDK 审查 | `UIContext.d.ts:4132-4185` |
| AC-1.2 | R-2 | TASK-3 | 源码审查 | `frontend_delegate_declarative_ng.cpp:1518-1528`; `component_snapshot.cpp:468-598` |
| AC-1.3 | R-3 | TASK-3 | 源码审查 | `snapshot_param.h:88-98` |
| AC-2.1 | R-4 | TASK-3 | SDK 审查 | `UIContext.d.ts:4313-4314` |
| AC-2.2 | R-5 | TASK-3 | 源码审查 | `frontend_delegate_declarative_ng.cpp:1487-1492` |
| AC-2.3 | R-6 | TASK-3 | SDK 对照 | `UIContext.static.d.ets:3190-3191` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Builder 调用 | 提供 callback/Promise 两种异步形态 | API 12 | AC-1.1 |
| R-2 | 行为 | Builder 完成 | Delegate→ComponentSnapshot::Create→Rosen capture | 非组件 Pattern 链路 | AC-1.2 |
| R-3 | 边界 | 可选 delay/checkImageStatus 缺省 | 使用 SnapshotParam 默认值 | 默认值由实现定义 | AC-1.3 |
| R-4 | 行为 | ComponentContent API 18 调用 | Promise 方式请求离屏截图 | 动态 SDK API 18 | AC-2.1 |
| R-5 | 行为 | Delegate 接收 content node | 复用 CreateSnapshotFromComponent 核心路径 | 共享输出为 PixelMap | AC-2.2 |
| R-6 | 边界 | 静态 createFromComponent | 可返回 null | 与动态声明不同 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | SDK/Delegate/核心审查 | Builder 重载、默认参数、离屏调用链。 |
| VM-2 | AC-2.1~2.3 | SDK/Delegate 审查 | Content 路径与静态非空差异。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `createFromBuilder` | Public | builder、callback/delay、check、options | void/Promise<PixelMap> | 异步错误 | Builder 离屏截图 | AC-1.1~1.3 |
| `createFromComponent` | Public | ComponentContent、delay、check、options | Promise<PixelMap> | 异步错误 | Content 离屏截图 | AC-2.1~2.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `createFromComponent` | 变更 | API 18 新增 | 低版本使用 Builder 路径 | AC-2.1 |

## 接口规格

### 接口定义

| 属性 | 值 |
|------|-----|
| 函数签名 | `createFromBuilder(builder, callback|delay?, checkImageStatus?, options?)`; `createFromComponent(content, delay?, checkImageStatus?, options?)` |
| 返回值 | callback 形式 void；Promise 形式 PixelMap；静态 Content 可为 null |
| 开放范围 | Public |
| 错误码 | callback/Promise 错误，Options 异常详见 Feat-04 |
| 关联 AC | AC-1.1~2.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| builder/content | CustomBuilder/ComponentContent | 是 | 无 | 产生可由离屏服务处理的 UINode。 |
| delay/checkImageStatus/options | number/boolean/SnapshotOptions | 否 | `SnapshotParam` 默认值 | isAuto 限制详见 Feat-04。 |

## 兼容性声明

- **已有 API 行为变更:** 无。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** Builder API 12；Content API 18。
- **API 版本号策略:** 静态/动态 Promise 可空性分别声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 服务链路 | 必须经 Delegate 与 ComponentSnapshot，不直接由组件 Pattern 截图 | AC-1.2, AC-2.2 |
| 渲染后端 | 最终调用 Rosen capture | AC-1.2 |
| 外部输入 | Builder/Content 内容、delay、图片加载状态影响输出 | AC-1.1~2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 两种节点来源各有 SDK 与 Delegate 证据 | 代码审查 | 输入文档 |
| 可靠性 | 异步完成通过 callback/Promise 交付 | 代码审查 | `component_snapshot.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 输出受密度、内容与渲染后端影响 | 不承诺相同 PixelMap 尺寸 | 设备测试 | SnapshotOptions |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 深色/HDR | 是 | Options 可改变输出，离屏 auto 受限 | AC-1.1, AC-2.1 |
| 多窗口 | 是 | UIContext 所属容器参与构建/捕获 | AC-1.2 |
| 版本升级 | 是 | Content 仅 API 18+ | AC-2.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 离屏组件截图
  Scenario: Builder 截图
    Given 应用提供 CustomBuilder
    When 调用 createFromBuilder
    Then Delegate 创建离屏节点并异步返回 PixelMap
```

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] Builder 与 Content 的版本边界明确
- [x] 所有规则关联 AC

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "UIContext createFromBuilder createFromComponent FrontendDelegate ComponentSnapshot offscreen pipeline"
```
