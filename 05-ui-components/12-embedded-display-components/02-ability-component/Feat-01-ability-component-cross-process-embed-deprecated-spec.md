# 特性规格

> ⚠️ **废弃声明：** `AbilityComponent` 自 `@since 10` 起废弃（`@deprecated since 10`、`@useinstead UIExtensionComponent`）。继任者为 **05-12-03 UIExtensionComponent**（`@since 12`）和 **05-12-04 EmbeddedComponent**（`@since 12`）。本规格固化既有实现行为，不作演进建议。
>
> Func-05-12-02-Feat-01 AbilityComponent 跨进程能力嵌入（已废弃）：固化 `AbilityComponent({want})`（dynamic `@since 9` `@syscap` `@deprecated since 10`）、`AbilityComponentAttribute.onConnect`/`onDisconnect`、`AbilityComponentPattern : WindowPattern`（WindowExtension/ExtensionSession 跨进程嵌入）、rect/visibility 同步、SceneBoard vs legacy `ConnectExtension` 行为分支行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | AbilityComponent 跨进程能力嵌入（已废弃） |
| 特性编号 | Func-05-12-02-Feat-01 |
| 优先级 | P2 |
| 目标版本 | dynamic `@since 9 dynamiconly`（全套 5 SDK 符号）；`@deprecated since 10`（`@useinstead UIExtensionComponent`）；无 static `.d.ets`（仅 `@internal` + `@syscap`） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-05-12-02（AbilityComponent）首个 Feat。**已废弃**，继任者见 05-12-03（UIExtensionComponent）/ 05-12-04（EmbeddedComponent）。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/12-embedded-display-components/02-ability-component/design.md` | Baselined |
| Dynamic API（SDK 契约） | `interface/sdk-js/api/@internal/component/ets/ability_component.d.ts` | — |
| NG Pattern | `frameworks/core/components_ng/pattern/ability_component/ability_component_pattern.h` / `.cpp` | — |
| NG Model | `frameworks/core/components_ng/pattern/ability_component/ability_component_model_ng.h` / `.cpp` / `ability_component_model.h` | — |
| NG Layout | `frameworks/core/components_ng/pattern/ability_component/ability_component_layout_algorithm.h` / `.cpp` | — |
| NG EventHub | `frameworks/core/components_ng/pattern/ability_component/ability_component_event_hub.h` | — |
| NG RenderProperty | `frameworks/core/components_ng/pattern/ability_component/ability_component_render_property.h` | — |
| JS 桥接 | `frameworks/bridge/declarative_frontend/jsview/js_ability_component.h` / `.cpp` | — |
| JS Controller | `frameworks/bridge/declarative_frontend/jsview/js_ability_component_controller.h` / `.cpp` | — |
| legacy Model | `frameworks/bridge/declarative_frontend/jsview/models/ability_component_model_impl.h` / `.cpp` | — |
| 继任者 | `specs/05-ui-components/12-embedded-display-components/03-ui-extension-component/`（05-12-03）、`04-embedded-component/`（05-12-04） | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 构造与 Want 解析

**作为** 系统应用开发者,
**我想要** 用 `AbilityComponent({want})` 嵌入另一能力的 UI,
**以便** 在当前页面展示跨进程能力界面。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN dynamic 调用 `AbilityComponent({want})`（`ability_component.d.ts` `@since 9 dynamiconly` `@syscap` `@deprecated since 10`）THEN 返回 `AbilityComponentAttribute`（extends `CommonMethod`） | 正常 |
| AC-1.2 | WHEN `JSAbilityComponent::Create` 解析参数 THEN 从 JS 对象读 `want.bundleName`+`want.abilityName`，经 `AbilityComponentModel::GetInstance()->SetWant` 下发 | 正常 |
| AC-1.3 | WHEN SDK 标记 `@deprecated since 10 @useinstead UIExtensionComponent` THEN 本组件已废弃，下游应迁移至 05-12-03（UIExtensionComponent）或 05-12-04（EmbeddedComponent） | 边界 |
| AC-1.4 | WHEN 无 static `.d.ets` THEN AbilityComponent 仅 `@internal` + `@syscap`（系统 API），无公开 static 范式 | 边界 |

### US-2: 连接生命周期

**作为** 系统应用开发者,
**我想要** 通过 `onConnect`/`onDisconnect` 回调感知嵌入能力的连接状态,
**以便** 在能力 UI 就绪/断开时执行逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 链式 `.onConnect(callback)`（`ability_component.d.ts` `@since 9` `@deprecated since 10 @useinstead UIExtensionComponent#onRemoteReady`）THEN `AbilityComponentEventHub` 存储 callback；连接成功时 fire | 正常 |
| AC-2.2 | WHEN 链式 `.onDisconnect(callback)`（`@since 9` `@deprecated since 10 @useinstead UIExtensionComponent#onRelease`）THEN EventHub 存储 callback；断开时 fire | 正常 |
| AC-2.3 | WHEN JS 桥接 `JSAbilityComponent::JSBind` THEN 额外绑定 legacy `onReady`/`onDestroy`/`onAbilityCreated`/`onAbilityMoveToFront`/`onAbilityWillRemove`/`width`/`height`——这些**不在当前 `.d.ts` 公开面** | 边界 |

### US-3: 跨进程嵌入与 SceneBoard 分支

**作为** 框架维护者,
**我想要** 了解 AbilityComponent 如何经 WindowExtension/ExtensionSession 嵌入跨进程 UI,
**以便** 理解废弃组件的既有行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `AbilityComponentPattern::OnModifyDone` THEN 创建 `WindowExtensionConnectionAdapterNG`（`adapter_`）；SceneBoard 启用时经 `Rosen::ExtensionSessionManager::RequestExtensionSession` 创建 ExtensionSession 并 `SetExtensionSession` | 正常 |
| AC-3.2 | WHEN SceneBoard 未启用 THEN 走 legacy `adapter_->ConnectExtension(host, windowId)` 路径 | 边界 |
| AC-3.3 | WHEN rect 变化 THEN `UpdateRect`→`adapter_->UpdateRect` 同步嵌入能力 surface 尺寸 | 正常 |
| AC-3.4 | WHEN 可见性/active/window-show 变化 THEN Pattern 转发 show/hide 到 adapter（嵌入能力 surface 随宿主可见性联动） | 正常 |
| AC-3.5 | WHEN Pattern 初始化 THEN touch/mouse/key/focus event 经 `InitEvent` 转发到嵌入能力 surface | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1,R-2,R-8 | T-1 | UT + SDK 比对 | `ability_component.d.ts`、`js_ability_component.cpp` |
| AC-2.1~2.3 | R-3,R-4,R-9 | T-1 | UT：EventHub onConnect/onDisconnect | `ability_component_event_hub.h`、`js_ability_component.cpp` |
| AC-3.1~3.5 | R-5,R-6,R-7 | T-1 | UT：Pattern OnModifyDone/SceneBoard/UpdateRect/visibility | `ability_component_pattern.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `AbilityComponent({want})` | 返回 AbilityComponentAttribute；JSCreate 解析 want | @since 9 @deprecated since 10 | AC-1.1,AC-1.2 |
| R-2 | 边界 | 废弃状态 | @useinstead UIExtensionComponent；继任 05-12-03/04 | 仅 @internal+@syscap | AC-1.3,AC-1.4 |
| R-3 | 行为 | onConnect | EventHub 存储+连接成功 fire | @deprecated @useinstead onRemoteReady | AC-2.1 |
| R-4 | 行为 | onDisconnect | EventHub 存储+断开 fire | @deprecated @useinstead onRelease | AC-2.2 |
| R-5 | 行为 | OnModifyDone | 创建 adapter；SceneBoard→ExtensionSession；legacy→ConnectExtension | 行为分支 | AC-3.1,AC-3.2 |
| R-6 | 行为 | rect 变化 | UpdateRect→adapter->UpdateRect | — | AC-3.3 |
| R-7 | 行为 | 可见性变化 | 转发 show/hide 到 adapter | — | AC-3.4 |
| R-8 | 边界 | 无 static | 仅 @internal+@syscap | — | AC-1.4 |
| R-9 | 边界 | legacy 绑定 | JSBind 额外绑定非公开面方法 | 不在 .d.ts | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 构造/want/废弃 | UT + SDK | want 解析、@deprecated since 10、无 static |
| VM-2 | AC-2.x 连接生命周期 | UT | onConnect/onDisconnect EventHub、legacy 绑定 |
| VM-3 | AC-3.x 跨进程嵌入 | UT | SceneBoard vs legacy、rect/visibility/event 同步 |

## API 变更分析

> 存量补录（已废弃），无新增 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `AbilityComponent({want})` + `AbilityComponentAttribute`（dyn `@since 9`） | 废弃（`@deprecated since 10`） | 跨进程能力嵌入 | `@useinstead UIExtensionComponent`（05-12-03） | AC-1.1,AC-1.3 |
| `AbilityComponentAttribute.onConnect`（`@since 9`） | 废弃 | 连接回调 | `@useinstead UIExtensionComponent#onRemoteReady` | AC-2.1 |
| `AbilityComponentAttribute.onDisconnect`（`@since 9`） | 废弃 | 断开回调 | `@useinstead UIExtensionComponent#onRelease` | AC-2.2 |

> SDK：`interface/sdk-js/api/@internal/component/ets/ability_component.d.ts`。Kit：ArkUI（`@syscap`）；权限：系统 API；SysCap：`SystemCapability.ArkUI.ArkUI.Full`。

## 接口规格

### 接口定义

**AbilityComponent（dynamic，`ability_component.d.ts`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `declare const AbilityComponent: AbilityComponentInterface`（`({want: Want}): AbilityComponentAttribute`） |
| 返回值 | `AbilityComponentAttribute`（extends CommonMethod） |
| 开放范围 | System API（`@since 9`，`@syscap`，`@deprecated since 10`） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.3 |

**AbilityComponentAttribute.onConnect / onDisconnect**

| 属性 | 值 |
|------|-----|
| 方法签名 | `onConnect(callback: () => void): AbilityComponentAttribute`；`onDisconnect(callback: () => void): AbilityComponentAttribute` |
| 开放范围 | System API（`@since 9`，`@deprecated since 10`） |
| 关联 AC | AC-2.1,AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| want | `Want`（`{bundleName, abilityName, ...}`） | 是 | — | 须合法 Want |
| callback（onConnect/onDisconnect） | `() => void` | 是 | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 构造 AbilityComponent({want}) | 解析 want→SetWant→OnModifyDone 创建 adapter | AC-1.2,AC-3.1 |
| 2 | SceneBoard 启用 | RequestExtensionSession+SetExtensionSession | AC-3.1 |
| 3 | 连接成功 | fire onConnect | AC-2.1 |
| 4 | rect 变化 | adapter->UpdateRect | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意：全套 API `@deprecated since 10`，`@useinstead UIExtensionComponent`；继任者 05-12-03（`@since 12`）/ 05-12-04（`@since 12`）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since 9`。
- **API 版本号策略:** 按 SDK `@since 9`/`@deprecated since 10` 标注。

> **废弃迁移风险（F-dep）：** AbilityComponent `@deprecated since 10`，继任 UIExtensionComponent（`@since 12`）+ EmbeddedComponent（`@since 12`）。下游新开发应使用继任者；SceneBoard vs legacy `ConnectExtension` 行为分支为既有实现（风险 RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 已废弃 | @deprecated since 10，@useinstead UIExtensionComponent | AC-1.3 |
| 仅 @syscap | 无 static 范式，仅系统 API | AC-1.4 |
| SceneBoard 行为分支 | ExtensionSession vs legacy ConnectExtension | AC-3.1,AC-3.2 |
| WindowPattern 基类 | AbilityComponentPattern extends WindowPattern | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 连接断开/SceneBoard 切换不崩 | UT 异常 | `ability_component_pattern.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 是 | SceneBoard 可能启用→ExtensionSession 路径 | XTS | `ability_component_pattern.cpp` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 嵌入能力 surface 随宿主入无障碍树 | — |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 嵌入能力自行处理 | — |
| 多窗口/分屏 | 是 | 可见性/active 联动 show/hide | AC-3.4 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | `@since 9` `@deprecated since 10` | AC-1.3 |
| 生态兼容 | 否 | 仅 @syscap 系统组件 | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: AbilityComponent 跨进程能力嵌入（已废弃）
  作为 系统应用开发者
  我想要 用 AbilityComponent({want}) 嵌入另一能力 UI
  以便 跨进程展示能力界面（已废弃，用 UIExtensionComponent 替代）

  Scenario: 构造与 want 解析
    Given AbilityComponent({want: {bundleName, abilityName}})
    When JSAbilityComponent::Create
    Then 解析 want→SetWant→OnModifyDone 创建 adapter

  Scenario Outline: SceneBoard 行为分支
    Given OnModifyDone
    When SceneBoard <状态>
    Then <路径>

    Examples:
      | 状态 | 路径 |
      | 启用 | ExtensionSessionManager::RequestExtensionSession+SetExtensionSession |
      | 未启用 | adapter->ConnectExtension(host, windowId) |

  Scenario: 废弃迁移
    Given AbilityComponent @deprecated since 10
    When 新开发
    Then 使用 UIExtensionComponent（05-12-03）或 EmbeddedComponent（05-12-04）
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做废弃组件全量；继任者见 05-12-03/04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AbilityComponentPattern WindowExtension ExtensionSession ConnectExtension SceneBoard 跨进程嵌入"
  - repo: "openharmony/arkui_ace_engine"
    query: "JSAbilityComponent Create want bundleName abilityName onConnect onDisconnect 废弃"
  - repo: "openharmony/arkui_ace_engine"
    query: "AbilityComponent @deprecated since 10 @useinstead UIExtensionComponent 继任 05-12-03"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/ability_component.d.ts`、`frameworks/core/components_ng/pattern/ability_component/ability_component_pattern.cpp`、`frameworks/bridge/declarative_frontend/jsview/js_ability_component.cpp`
