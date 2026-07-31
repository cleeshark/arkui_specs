# 特性规格

> Func-04-10-01-Feat-01 固化独立 `@ohos.arkui.componentSnapshot` 动态模块的完整 API 面及其 API 18 迁移语义。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 独立 componentSnapshot 模块接口与迁移 |
| 特性编号 | Func-04-10-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10 至 API 18 弃用后仍需兼容 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 独立 componentSnapshot 模块 | 补录 API 10 动态模块而非仅记录 UIContext 迁移。 |

## 输入文档

- `design.md`
- `interface/sdk-js/api/@ohos.arkui.componentSnapshot.d.ts:517-700`
- `interfaces/napi/kits/component_snapshot/js_component_snapshot.cpp:498-926`

## 用户故事

### US-1: 使用独立模块捕获已挂载组件

作为存量动态 ArkTS 应用开发者，我想要调用独立模块的 get/getSync，以便兼容已有截图代码。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `componentSnapshot.get(id, callback|options)` THEN SDK 提供 callback 和 Promise 两个重载。 | 正常 |
| AC-1.2 | WHEN 调用 `getSync(id, options)` THEN 返回 PixelMap；同步路径的超时由实现返回错误。 | 边界 |
| AC-1.3 | WHEN id 对应节点不在树上或未完成渲染 THEN 不承诺有效 PixelMap，按实现错误路径完成。 | 异常 |

### US-2: 使用旧 Builder 接口并迁移

作为存量应用开发者，我想要继续使用 createFromBuilder 并获得明确迁移指引，以便平滑升级。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 `createFromBuilder` THEN SDK 提供 callback 和 Promise 重载，参数为 builder、delay、checkImageStatus 和 options。 | 正常 |
| AC-2.2 | WHEN 目标 API 为 18 或以上 THEN API 元数据标记旧 get/createFromBuilder 为 deprecated，并指向 UIContext 对应方法。 | 边界 |
| AC-2.3 | WHEN 使用 API 10-17 动态应用 THEN 旧模块保持其公开声明的调用契约。 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-1 | SDK 审查 | `componentSnapshot.d.ts:517-554` |
| AC-1.2 | R-2 | TASK-1 | SDK/核心审查 | `componentSnapshot.d.ts:696-700`; `component_snapshot.cpp:601-655` |
| AC-1.3 | R-3 | TASK-1 | 源码审查 | `component_snapshot.cpp:731-745` |
| AC-2.1 | R-4 | TASK-1 | SDK/NAPI 审查 | `componentSnapshot.d.ts:607-672`; `js_component_snapshot.cpp:534-572` |
| AC-2.2 | R-5 | TASK-1 | SDK 审查 | `componentSnapshot.d.ts:520-521,551-552,610-611,668-669` |
| AC-2.3 | R-6 | TASK-1 | SDK 审查 | `componentSnapshot.d.ts:519,550,609,667` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | get 使用 callback 或 options | 按 SDK 返回 void 或 Promise<PixelMap> | API 10 dynamic only，API 18 deprecated | AC-1.1 |
| R-2 | 边界 | getSync 捕获 | 在 UI 线程使用核心同步捕获路径 | 等待超时由核心处理 | AC-1.2 |
| R-3 | 异常 | id 未解析为可截图节点 | 不产生成功 PixelMap | 节点树与渲染状态为外部输入 | AC-1.3 |
| R-4 | 行为 | createFromBuilder 调用 | NAPI 解析 builder/param 并委托截图服务 | 两种异步形态 | AC-2.1 |
| R-5 | 边界 | API >=18 读取旧 API | SDK 标记 deprecated/useinstead UIContext | 弃用不是删除 | AC-2.2 |
| R-6 | 恢复 | API 10-17 使用旧模块 | 保持存量动态模块契约 | 不适用于静态 SDK | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | SDK/核心代码审查 | 两个 get 异步形态、同步错误边界。 |
| VM-2 | AC-2.1~2.3 | SDK/NAPI 审查 | Builder 参数与 API 18 弃用迁移。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `componentSnapshot.get` | Public，API 10 dynamic | id、callback/options | void 或 Promise<PixelMap> | 异步错误 | 已挂载节点截图 | AC-1.1 |
| `componentSnapshot.getSync` | Public，API 12 dynamic | id、options | PixelMap | 超时/内部错误 | 同步截图 | AC-1.2 |
| `componentSnapshot.createFromBuilder` | Public，API 10 dynamic | builder、delay、checkImageStatus、options | void 或 Promise<PixelMap> | 异步错误 | 离屏 Builder 截图 | AC-2.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `get` / `createFromBuilder` | 废弃，API 18 | 新应用 | 使用 `uiContext.getComponentSnapshot()` 返回的服务实例 | AC-2.2 |

## 接口规格

### 接口定义

**componentSnapshot module**

| 属性 | 值 |
|------|-----|
| 函数签名 | `get(id, callback|options)`、`getSync(id, options?)`、`createFromBuilder(builder, callback|delay?, checkImageStatus?, options?)` |
| 返回值 | void、Promise<PixelMap> 或 PixelMap |
| 开放范围 | Public dynamic only；get/createFromBuilder API 18 deprecated |
| 错误码 | callback/Promise 错误；同步核心超时/内部错误 |
| 关联 AC | AC-1.1~2.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| id | string | get/getSync 是 | 无 | 必须解析为已渲染目标节点。 |
| builder | CustomBuilder | create 是 | 无 | 由离屏服务构建。 |
| delay/checkImageStatus/options | number/boolean/SnapshotOptions | 否 | 由 SDK/实现默认值决定 | 后续 Feat-04 定义 Options。 |

## 兼容性声明

- **已有 API 行为变更:** API 18 将 `get` 和 `createFromBuilder` 标记为废弃，未移除。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** 模块 API 10 dynamic；getSync API 12。
- **API 版本号策略:** API 18+ 优先 UIContext，存量动态代码保留旧模块语义。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 独立入口 | NAPI 在 `ComponentSnapshotExport` 中导出模块函数 | 全部 |
| 同步风险 | getSync 运行核心同步捕获路径 | AC-1.2 |
| 节点状态 | 节点在树/渲染状态决定捕获结果 | AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 兼容性 | API 18 保留弃用元数据 | SDK 审查 | `componentSnapshot.d.ts` |
| 可测试性 | NAPI 和核心路径可定位 | 代码审查 | 输入文档 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 接口相同，渲染内容随实际节点和屏幕环境变化 | 不承诺跨设备同 PixelMap 像素值 | 设备测试 | 核心截图路径 |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 版本升级 | 是 | API 18 迁移至 UIContext | AC-2.2 |
| 多窗口 | 是 | id 在当前前端容器解析 | AC-1.3 |
| 深色/动态范围 | 是 | Options 影响输出，详见 Feat-04 | AC-2.1 |

## 行为场景（可选，Gherkin）

L1 规格由接口定义的参数和行为规则覆盖。

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] 范围含独立模块，不把它降级为迁移注记
- [x] 所有规则关联 AC

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "independent @ohos.arkui.componentSnapshot NAPI module APIs and API 18 UIContext migration"
```
