# 特性规格

> Func-04-06-02-Feat-08 FrameNode 生命周期、回收与跨语言：固化 recycle、reuse、setCrossLanguageOptions、getCrossLanguageOptions 共 4 个公开 API 与 CrossLanguageOptions 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameNode 生命周期、回收与跨语言 |
| 特性编号 | Func-04-06-02-Feat-08 |
| 所属 Epic | 自定义节点能力 / FrameNode |
| 优先级 | P1 |
| 目标版本 | API 15（setCrossLanguageOptions 起始）；recycle/reuse API 18；treeOperating API 26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂（L2） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | setCrossLanguageOptions/getCrossLanguageOptions | API 15（attributeSetting）；treeOperating API 26.0.0 |
| ADDED | recycle/reuse | API 18 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/02-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `FrameNode.static.d.ets` | — |

## 用户故事

### US-1: 回收与复用节点
**作为** 应用开发者，**我想要** 手动触发节点的回收/复用回调，
**以便** 驱动对应行为。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `recycle()` THEN triggerOnRecycle→FrameNode::OnRecycle：fire destroyCallbacks、ResetGeometryTransition、pattern OnRecycle、UINode OnRecycle 递归、ClearAccessibilityFocus | 正常 |
| AC-1.2 | WHEN `reuse()` THEN triggerOnReuse→FrameNode::OnReuse：pattern OnReuse、UINode OnReuse 递归、dev 模式 PaintDebugBoundary | 正常 |
| AC-1.3 | WHEN recycle/reuse 手动调用 THEN 仅触发 pattern 回调与清理，不移动节点至回收池（池管理由 LazyForEach/Repeat/@Reusable 框架负责） | 边界 |
| AC-1.4 | WHEN 节点 null/disposed THEN 静默返回 Undefined（不抛异常） | 边界 |

### US-2: 设置跨语言选项
**作为** 应用开发者，**我想要** 控制非 ArkTS 语言对本节点的属性设置与树操作权限，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `setCrossLanguageOptions({attributeSetting:true})` 且节点 tag 在 CROSS_LANGUAGE_NODE_TYPE_ARRAY THEN SetIsCrossLanguageAttributeSetting(true) | 正常 |
| AC-2.2 | WHEN `setCrossLanguageOptions({treeOperating:true/false})`（attributeSetting=false）THEN 跳过 tag 校验，任意节点允许设置 TreeOperatingStatus | 正常 |
| AC-2.3 | WHEN 本节点不可改（如 ProxyFrameNode）THEN 抛 100022 | 异常 |
| AC-2.4 | WHEN attributeSetting==true 且 tag 不在 CROSS_LANGUAGE_NODE_TYPE_ARRAY（如 CustomFrameNode）THEN native 返 PARAM_INVALID→抛 100022 | 异常 |
| AC-2.5 | WHEN treeOperating 未传（UNDEFINED）且 tag 不在数组 THEN 抛 100022（needValidation 含 treeOperating UNDEFINED） | 异常 |

### US-3: 读取跨语言选项
**作为** 应用开发者，**我想要** 读取当前跨语言选项，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `getCrossLanguageOptions()` THEN 返回 {attributeSetting: bool, treeOperating: bool}，二者默认 false | 正常 |
| AC-3.2 | WHEN treeOperatingStatus 非 ENABLE THEN treeOperating 返 false | 边界 |

### US-4: 跨语言门控行为
**作为** 应用开发者，**我想要** 了解跨语言选项如何门控属性设置与树操作，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN ArkTS FrameNode（可改）THEN checkIfCanCrossLanguageAttributeSetting 返 true（可改即允许 native 属性设置） | 正常 |
| AC-4.2 | WHEN ProxyFrameNode（C 节点）且未开 attributeSetting THEN checkIfCanCrossLanguageAttributeSetting 返 false，typeNode.getAttribute 返 undefined | 边界 |
| AC-4.3 | WHEN ProxyFrameNode 开 treeOperating=true THEN appendChild 等树操作允许；否则抛 100021 | 正常 |
| AC-4.4 | WHEN ArkTS 不可改节点（非 C 节点）THEN checkIfCanCrossLanguageTreeOperating 返 false，树操作抛 100021 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3,R-4 | 单测 | frame_node.ts:932,926; bridge:2704,2716; frame_node.cpp:5432,5448 |
| AC-2.1..2.5 | R-5,R-6,R-7,R-8,R-9 | 单测 | frame_node.ts:824; modifier:805; bridge:2728 |
| AC-3.1..3.2 | R-10,R-11 | 单测 | frame_node.ts:840; bridge:2751,2771 |
| AC-4.1..4.4 | R-12,R-13,R-14,R-15 | 单测 | frame_node.ts:853; bridge:2783; ImmutableFrameNode:1133 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | recycle() | 触发回收回调（清理与 pattern 回调，递归子树） | 不移入回收池 | AC-1.1,1.3 |
| R-2 | 行为 | reuse() | 触发复用回调（pattern 回调，递归子树） | — | AC-1.2 |
| R-3 | 边界 | recycle/reuse 不移动至池 | 仅触发回调与清理；池管理由 LazyForEach/Repeat 框架 | — | AC-1.3 |
| R-4 | 边界 | null/disposed 节点 | 静默返回 | 不抛异常 | AC-1.4 |
| R-5 | 行为 | setCrossLanguageOptions({attributeSetting:true}) tag 在白名单 | 开启跨语言属性设置 | — | AC-2.1 |
| R-6 | 行为 | setCrossLanguageOptions({treeOperating:bool}) attributeSetting=false | 跳过 tag 校验，任意节点允许设置树操作权限 | — | AC-2.2 |
| R-7 | 异常 | 本节点不可改 | 抛 100022 | — | AC-2.3 |
| R-8 | 异常 | attributeSetting==true 且 tag 不在白名单 | 抛 100022 | CustomFrameNode 不在白名单 | AC-2.4 |
| R-9 | 异常 | treeOperating 未传 且 tag 不在白名单 | 抛 100022 | — | AC-2.5 |
| R-10 | 行为 | getCrossLanguageOptions() | 返回 {attributeSetting, treeOperating}，默认 false | — | AC-3.1 |
| R-11 | 边界 | treeOperatingStatus 非 ENABLE | treeOperating 返回 false | — | AC-3.2 |
| R-12 | 行为 | ArkTS FrameNode（可改）checkIfCanCrossLanguageAttributeSetting | 返回 true | 可改即允许 | AC-4.1 |
| R-13 | 边界 | ProxyFrameNode 未开 attributeSetting | 返回 false，属性设置被阻 | — | AC-4.2 |
| R-14 | 行为 | ProxyFrameNode 开 treeOperating=true | 树操作允许；否则抛 100021 | 仅 C 节点+ENABLE | AC-4.3 |
| R-15 | 边界 | ArkTS 不可改节点 checkIfCanCrossLanguageTreeOperating | 返回 false，树操作抛 100021 | 非 C 节点不可树操作 | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-4 回收/复用 | 单测 | OnRecycle/OnReuse 回调链、不移入池、null 静默 |
| VM-2 | R-5..R-9 setCrossLanguageOptions | 单测 | tag 数组校验、treeOperating 跳过、100022 触发 |
| VM-3 | R-10,R-11 getCrossLanguageOptions | 单测 | 默认 false、非 ENABLE |
| VM-4 | R-12..R-15 跨语言门控 | 单测 | 可改即允许、C 节点+ENABLE、100021 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| recycle() | Public | — | void | — | 触发回收回调 | AC-1 |
| reuse() | Public | — | void | — | 触发复用回调 | AC-1 |
| setCrossLanguageOptions(options) | Public | options: CrossLanguageOptions | void | 100022 | 设置跨语言选项 | AC-2 |
| getCrossLanguageOptions() | Public | — | CrossLanguageOptions | — | 读取跨语言选项 | AC-3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**recycle / reuse**

| 属性 | 值 |
|------|-----|
| 函数签名 | `recycle(): void`; `reuse(): void` (@since 18 dyn/23 static) |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | recycle | OnRecycle 回调链（不移入池） | AC-1.1,1.3 |
| 2 | reuse | OnReuse 回调链 | AC-1.2 |
| 3 | null/disposed | 静默返 Undefined | AC-1.4 |

**setCrossLanguageOptions / getCrossLanguageOptions**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setCrossLanguageOptions(options: CrossLanguageOptions): void`(@since 15 dyn/23 static); `getCrossLanguageOptions(): CrossLanguageOptions` |
| 返回值 | void / CrossLanguageOptions |
| 开放范围 | Public |
| 错误码 | setCrossLanguageOptions: 100022 |
| 关联 AC | AC-2,3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options.attributeSetting | boolean | 否 | false | @since 15；true 时需 tag 在数组，否则 100022 |
| options.treeOperating | boolean | 否 | false | @since 26.0.0；未传(UNDEFINED)+tag 不在数组→100022 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | attributeSetting=true tag 在数组 | SetIsCrossLanguageAttributeSetting(true) | AC-2.1 |
| 2 | treeOperating 显式 + attributeSetting=false | 跳过 tag 校验 | AC-2.2 |
| 3 | 不可改 | 抛 100022 | AC-2.3 |
| 4 | attributeSetting=true tag 不在数组 | 抛 100022 | AC-2.4 |
| 5 | getCrossLanguageOptions | 返 {attributeSetting,treeOperating} 默认 false | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** setCrossLanguageOptions(attributeSetting) API 15；recycle/reuse API 18；treeOperating API 26.0.0；静态 @since 23。
- **API 版本号策略:** attributeSetting @since 15；treeOperating @since 26.0.0；recycle/reuse @since 18。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| recycle/reuse 不移入回收池 | 仅触发 pattern 回调；池管理由 LazyForEach/Repeat 框架，用户误以为手动入池 | frame_node.cpp:5432,5448 |
| setCrossLanguageOptions tag 白名单 | attributeSetting=true 仅支持内置组件，CustomFrameNode 抛 100022 | modifier:55-64,805 |
| treeOperating UNDEFINED+tag 不在数组误抛 100022 | needValidation 含 UNDEFINED，即使未意图开 attributeSetting | modifier:805 |
| ArkTS 不可改节点不可树操作 | checkIfCanCrossLanguageTreeOperating 仅 CNode+ENABLE，ArkTS 不可改节点树操作抛 100021 | bridge:2783 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 回收回调非池管理 | recycle/reuse 仅触发 OnRecycle/OnReuse 回调 | AC-1.3 |
| 跨语言 tag 白名单 | attributeSetting=true 须 tag 在 CROSS_LANGUAGE_NODE_TYPE_ARRAY | AC-2.1,2.4 |
| 树操作仅 C 节点+ENABLE | checkIfCanCrossLanguageTreeOperating=IsCNode()&&ENABLE | AC-4.3,4.4 |
| attributeSetting 门控 | 可改节点（ArkTS FrameNode）isModifiable 即允许；C 节点须显式开 | AC-4.1,4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | recycle 触发 destroyCallbacks 清理，防止回调泄漏 | 单测 | frame_node.cpp:5432 |
| 自动化维测 | OnConfigurationUpdate/NotifyColorModeChange 处理多类配置更新 | 单测 | frame_node.cpp:1993,1944 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 是 | OnConfigurationUpdate/NotifyColorModeChange 处理 colorMode | AC-1 |
| 多窗口/分屏 | 是 | OnWindowShow/Hide/Focused 等窗口生命周期 | AC-1 |
| 版本升级 | 是 | attributeSetting(15)/recycle(18)/treeOperating(26) 演进 | AC-2 |

## 行为场景

```gherkin
Feature: FrameNode 生命周期、回收与跨语言
  Scenario: recycle 不移入回收池
    Given 节点 N
    When 调用 N.recycle()
    Then 触发 OnRecycle 回调链
    And N 仍在原树位置（不移入池）

  Scenario Outline: setCrossLanguageOptions attributeSetting 校验
    When 调用 node.setCrossLanguageOptions({attributeSetting:true})
    Then <期望>

    Examples:
      | node tag | 期望 |
      | Scroll | 设置成功 |
      | CustomFrameNode | 抛 100022 |

  Scenario: treeOperating 门控树操作
    Given ProxyFrameNode 已 setCrossLanguageOptions({treeOperating:true})
    When 调用 proxy.appendChild(child)
    Then 树操作允许
    And 未开 treeOperating 时抛 100021
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（生命周期/回收/跨语言；不含树操作本身 Feat-02）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode::OnRecycle/OnReuse 回调链与 LazyForEach/Repeat 池管理关系"
  - repo: "openharmony/arkui_ace_engine"
    query: "SetCrossLanguageOptionsFull CROSS_LANGUAGE_NODE_TYPE_ARRAY 白名单与 needValidation"
  - repo: "openharmony/arkui_ace_engine"
    query: "checkIfCanCrossLanguageAttributeSetting/TreeOperating 门控与 ImmutableFrameNode 树操作 override"
  - repo: "openharmony/arkui_ace_engine"
    query: "OnConfigurationUpdate/NotifyColorModeChange/OnWindow* 生命周期回调"
```
