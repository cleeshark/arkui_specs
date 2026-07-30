# 特性规格

> Func-04-06-05-Feat-05 Transfer 转换变体：固化经 `transferDynamic`（动态→静态 ArkTS 对象转换）产生的 TransComponentContent/TransReactiveComponentContent 的 isTransferred 标识、只读限制（100031）与转换工厂。主角 ArkTS TransComponentContent。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Transfer 转换变体 (Transfer Variants) |
| 特性编号 | Func-04-06-05-Feat-05 |
| 所属 Epic | 自定义节点能力 / ComponentContent |
| 优先级 | P2 |
| 目标版本 | transferDynamic @since 23 staticonly（@ohos.transfer 模块）；isTransferred @since 24 dynamic / 26.0.0 static；100031 @since 22 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Transfer 变体（isTransferred=true + 100031） | API 22 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/05-component-content/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/ComponentContent.d.ts` / `.static.d.ets` | — |
| Transfer 模块 | `interface/sdk-js/api/@ohos.transfer.d.ets` | transferDynamic @since 23 staticonly |

## 定位

`transferDynamic`（`@ohos.transfer` 模块，@since 23 staticonly）将**动态 ArkTS 对象转换为静态 ArkTS 对象**——动态范式的运行时对象（如动态创建的 ComponentContent）经转换后可在静态范式（StageModel）中使用。转换产生的 ComponentContent 称为 TransComponentContent（或 TransReactiveComponentContent），是 ComponentContent 的只读变体：

- 经 `createComponentContentByTrans` / `createReactiveComponentContentByTrans` 工厂从现有 native 指针构建（不重新创建组件树）
- `isTransferred()` 返回 `true`（标识为转换产生）
- 只读：reuse/update/recycle/updateConfiguration/inheritFreezeOptions/flushState 抛 100031（转换产生的节点不允许变更，因为底层 native 指针归原动态对象所有）

## 用户故事

### US-1: Transfer 转换变体
**作为** 应用开发者，**我想要** 将动态创建的 ComponentContent 经 transferDynamic 转换为静态范式可用的只读变体，
**以便** 在静态 ArkTS 代码中引用动态范式已构建的组件树。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 经 transferDynamic 转换产生 TransComponentContent/TransReactiveComponentContent THEN isTransferred() 返回 true（标识为转换产生，@since 24 dynamic / 26.0.0 static） | 正常 |
| AC-1.2 | WHEN Trans 变体调 reuse/update/recycle/updateConfiguration/inheritFreezeOptions/flushState THEN 抛 BusinessError(100031, "ComponentContent created by transferDynamic not support...")——转换产生的节点只读，底层 native 指针归原动态对象所有 | 异常 |
| AC-1.3 | WHEN createComponentContentByTrans/createReactiveComponentContentByTrans THEN 从现有 native 指针（nodePtr/frameNodePtr）构建 TransComponentContent，不重新创建组件树（trans_component_content.ts 构造调 createBuilderNode） | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.3 | R-1,R-2,R-3 | 单测 | trans_component_content.ts |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Trans 变体 | isTransferred() 返回 true | 标识为 transferDynamic 转换产生 | AC-1.1 |
| R-2 | 异常 | Trans 变体调 reuse/update/recycle/updateConfiguration/inheritFreezeOptions/flushState | 抛 100031 | 转换产生节点只读（native 指针归原动态对象） | AC-1.2 |
| R-3 | 行为 | createComponentContentByTrans/createReactiveComponentContentByTrans | 从现有 native 指针构建（trans_component_content.ts 构造调 createBuilderNode） | 不重新创建组件树 | AC-1.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 Transfer | 单测 | isTransferred、100031、trans 工厂 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| isTransferred() | Public | 无 | boolean | — | 标识是否经 transferDynamic 转换产生 | AC-1.1 |
| Trans 变体变更 API（reuse/update/recycle/updateConfiguration/inheritFreezeOptions/flushState） | Public | 各方法原参 | void | 100031 | 转换产生节点只读，抛 100031 | AC-1.2 |
| createComponentContentByTrans / createReactiveComponentContentByTrans | Public | uiContext, nodePtr, frameNodePtr | TransComponentContent / TransReactiveComponentContent | — | 从现有 native 指针构建转换变体 | AC-1.3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**TransComponentContent / TransReactiveComponentContent**

| 属性 | 值 |
|------|-----|
| 函数签名 | `isTransferred(): boolean`; `reuse/update/recycle/updateConfiguration/inheritFreezeOptions/flushState(): void`（抛 100031） |
| 返回值 | boolean / void |
| 开放范围 | Public |
| 错误码 | 100031 |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Trans 变体 | isTransferred=true，变更 API 抛 100031 | AC-1.1,1.2 |
| 2 | trans 工厂 | 从现有 native 指针构建（不重新创建组件树） | AC-1.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** transferDynamic @since 23 staticonly（@ohos.transfer）；isTransferred @since 24 dynamic / 26.0.0 static；100031 @since 22。
- **API 版本号策略:** transferDynamic staticonly @since 23；isTransferred 动态 @since 24 / 静态 @since 26.0.0；100031 @since 22。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| Trans 变体抛 100031 | 转换产生节点只读（native 指针归原动态对象） | trans_component_content.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Trans 变体只读 | 变更 API 抛 100031（native 指针归原动态对象，不允许变更） | AC-1.2 |
| transferDynamic 是 staticonly | @ohos.transfer 模块 @since 23 staticonly，仅静态范式可用 | AC-1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | Trans 变体明确抛错 | 单测 | trans_component_content.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | transferDynamic(23 staticonly) / isTransferred(24 dyn / 26 static) / 100031(22) 演进 | AC-1 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（Transfer 变体——动态→静态 ArkTS 对象转换；ComponentContent 本体在 Feat-01..04）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "trans_component_content.ts TransComponentContent isTransferred=true 与变更 API 抛 100031"
  - repo: "openharmony/interface/sdk-js"
    query: "@ohos.transfer transferDynamic 动态转静态 ArkTS 对象转换"
```
