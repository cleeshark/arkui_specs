# 特性规格

> Func-04-03-09-Feat-04 无障碍动作与虚拟节点：固化 accessibilityActionOptions / accessibilityCustomActions / onAccessibilityActionIntercept / accessibilityVirtualNode / onAccessibilityHover / onAccessibilityHoverTransparent / onAccessibility 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍动作与虚拟节点 (Accessibility Actions & Virtual Node) |
| 特性编号 | Func-04-03-09-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 18+（actionOptions @since 18, customActions @since 20, actionIntercept @since 20）；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | accessibilityActionOptions 行为规格 | 补录 scrollStep 配置 |
| ADDED | accessibilityCustomActions 行为规格 | 补录自定义动作（最多16个，名称最长128字节） |
| ADDED | onAccessibilityActionIntercept 行为规格 | 补录动作拦截回调（ACTION_INTERCEPT/CONTINUE/RISE） |
| ADDED | accessibilityVirtualNode 行为规格 | 补录虚拟节点构建器及 FrameNode 集成 |
| ADDED | onAccessibilityHover / onAccessibilityHoverTransparent 行为规格 | 补录悬停事件与透传事件 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/09-accessibility-attributes/design.md` | Baselined |
| Public SDK | `interface_sdk-js/api/arkui/component/common.static.d.ets` | `@since 23 static` |

---

## 用户故事

### US-1: 配置无障碍动作选项

**作为** 应用开发者,
**我想要** 通过 `.accessibilityActionOptions()` 配置无障碍动作参数,
**以便** 控制无障碍模式下的滚动步长。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.accessibilityActionOptions({scrollStep: 3})` THEN `accessibilityActionOptions_.scrollStep` 设为 3（clamp 到 >= 1） | 正常 |
| AC-1.2 | WHEN 传入 `undefined` THEN 调用 `ResetAccessibilityActionOptions` 重置 | 异常 |

### US-2: 注册自定义无障碍动作

**作为** 应用开发者,
**我想要** 通过 `.accessibilityCustomActions()` 注册自定义动作,
**以便** 屏幕阅读器提供自定义操作（如"删除""标记"等）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.accessibilityCustomActions([{name: "删除", onAction: () => {...}}])` THEN 存储到 `accessibilityCustomActions_`，触发 `ELEMENT_INFO_CHANGE` | 正常 |
| AC-2.2 | WHEN 动作数量超过 16 个 THEN 截断到前 16 个（`ACCESSIBILITY_CUSTOM_ACTION_MAX_COUNT = 16`） | 边界 |
| AC-2.3 | WHEN 动作名称超过 128 字节 THEN 截断到 128 字节（`ACCESSIBILITY_CUSTOM_ACTION_NAME_MAX_BYTES = 128`） | 边界 |
| AC-2.4 | WHEN 传入 `undefined` THEN 调用 `ResetAccessibilityCustomActions` 清空 | 异常 |

### US-3: 拦截无障碍动作

**作为** 应用开发者,
**我想要** 通过 `.onAccessibilityActionIntercept()` 拦截无障碍动作,
**以便** 在框架处理前自定义动作响应。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 注册 `.onAccessibilityActionIntercept((action) => AccessibilityActionInterceptResult.ACTION_INTERCEPT)` 返回 ACTION_INTERCEPT (0) THEN 框架不处理该动作 | 正常 |
| AC-3.2 | WHEN 回调返回 ACTION_CONTINUE (1) THEN 框架继续处理该动作 | 正常 |
| AC-3.3 | WHEN 回调返回 ACTION_RISE (2) THEN 动作向上传播到父组件 | 正常 |

### US-4: 创建无障碍虚拟节点

**作为** 应用开发者,
**我想要** 通过 `.accessibilityVirtualNode()` 创建虚拟无障碍节点,
**以便** 为自绘内容提供无障碍支持。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.accessibilityVirtualNode(() => { ... })` 传入 Builder THEN 创建虚拟 FrameNode 树，标记 `isAccessibilityVirtualNode_`，触发 `PROPERTY_UPDATE_LAYOUT` | 正常 |
| AC-4.2 | WHEN 虚拟节点创建后 THEN FrameNode 的 `ProcessAccessibilityVirtualNode` 在布局阶段应用约束并处理离屏节点树 | 正常 |

### US-5: 监听无障碍悬停

**作为** 应用开发者,
**我想要** 通过 `.onAccessibilityHover()` / `.onAccessibilityHoverTransparent()` 监听悬停,
**以便** 响应屏幕阅读器的悬停事件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 注册 `.onAccessibilityHover((isHover, event) => {...})` THEN 回调存储在 `InputEventHub`，当无障碍服务悬停到当前组件时触发 | 正常 |
| AC-5.2 | WHEN 注册 `.onAccessibilityHoverTransparent((event) => {...})` THEN 回调存储在 `AccessibilityProperty`，当子树中无节点处理悬停时触发，并注册到 `AccessibilityManager` | 正常 |
| AC-5.3 | WHEN `onAccessibilityHover` 与 `onAccessibilityHoverTransparent` 同时注册 THEN 前者在组件自身悬停时触发，后者在悬停事件穿透时触发（语义互补） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `accessibility_property.cpp:1877-1890` |
| AC-1.2 | R-1 | 单元测试 | `js_accessibility.cpp:360-378` |
| AC-2.1 | R-2 | 单元测试 | `accessibility_property.cpp:1892-1922` |
| AC-2.2 | R-2 | 单元测试 | `ACCESSIBILITY_CUSTOM_ACTION_MAX_COUNT = 16` |
| AC-2.3 | R-2 | 单元测试 | `ACCESSIBILITY_CUSTOM_ACTION_NAME_MAX_BYTES = 128` |
| AC-2.4 | R-2 | 单元测试 | `js_accessibility.cpp:380-429` |
| AC-3.1 | R-3 | 单元测试 | `accessibility_property_function.h:86-87` |
| AC-3.2 | R-3 | 单元测试 | 同上 |
| AC-3.3 | R-3 | 单元测试 | 同上 |
| AC-4.1 | R-4 | 单元测试 | `view_abstract_model_ng.cpp:1454-1475` |
| AC-4.2 | R-4 | 单元测试 | `frame_node.cpp:6412-6426` |
| AC-5.1 | R-5 | 单元测试 | `js_view_abstract.cpp:11804-11824` |
| AC-5.2 | R-5 | 单元测试 | `js_accessibility.cpp:340-358` |
| AC-5.3 | R-5 | 单元测试 | 两种回调互补语义 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `SetAccessibilityActionOptions({scrollStep})` | 存储 `AccessibilityActionOptions`；`scrollStep` 默认 1 | `scrollStep` 在 JS 层 clamp 到 >= 1 | AC-1.1, AC-1.2 |
| R-2 | 边界 | 调用 `SetAccessibilityCustomActions(actions)` | 存储到 `accessibilityCustomActions_`；触发 `ELEMENT_INFO_CHANGE`；`ActActionCustom(name)` 按名称匹配执行 | 最多 16 个动作；名称最长 128 字节 | AC-2.1, AC-2.2, AC-2.3, AC-2.4 |
| R-3 | 行为 | 注册 `onAccessibilityActionIntercept` 回调 | 回调返回 `ACTION_INTERCEPT`(0) 阻止框架处理；`ACTION_CONTINUE`(1) 继续框架处理；`ACTION_RISE`(2) 向上传播 | 回调类型为 `ActionAccessibilityActionIntercept` | AC-3.1, AC-3.2, AC-3.3 |
| R-4 | 行为 | 调用 `SetAccessibilityVirtualNode(buildFunc)` | 执行 Builder 创建虚拟 FrameNode 树；标记 `isAccessibilityVirtualNode_`；设置父链接；`SaveAccessibilityVirtualNode`；触发 `PROPERTY_UPDATE_LAYOUT` | 虚拟节点在 `ProcessAccessibilityVirtualNode` 中应用布局约束 | AC-4.1, AC-4.2 |
| R-5 | 行为 | 注册 `onAccessibilityHover` 或 `onAccessibilityHoverTransparent` | `onAccessibilityHover` 存储在 `InputEventHub`，当前组件悬停时触发；`onAccessibilityHoverTransparent` 存储在 `AccessibilityProperty`，子树穿透时触发 | 两者互补：前者处理自身悬停，后者处理穿透事件 | AC-5.1, AC-5.2, AC-5.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.2 | 单元测试 | AccessibilityActionOptions scrollStep |
| VM-2 | AC-2.1 ~ AC-2.4 | 单元测试 | CustomActions 数量/名称截断 |
| VM-3 | AC-3.1 ~ AC-3.3 | 单元测试 | ActionIntercept 三态返回值 |
| VM-4 | AC-4.1 ~ AC-4.2 | 单元测试 | VirtualNode 创建与布局集成 |
| VM-5 | AC-5.1 ~ AC-5.3 | 单元测试 | Hover vs HoverTransparent 语义差异 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

> 精简覆盖，核心接口行为见规则定义。

| API | 签名 | @since |
|-----|------|--------|
| `accessibilityActionOptions` | `(option: AccessibilityActionOptions \| undefined): this` | 23 static |
| `accessibilityCustomActions` | `(actions: Array<AccessibilityCustomAction> \| undefined): this` | 26.0.0 static |
| `onAccessibilityActionIntercept` | `(callback: AccessibilityActionInterceptCallback \| undefined): this` | 23 static |
| `accessibilityVirtualNode` | `(builder: CustomBuilder \| undefined): this` | 23 static |
| `onAccessibilityHover` | `(callback: AccessibilityCallback \| undefined): this` | 23 static |
| `onAccessibilityHoverTransparent` | `(callback: AccessibilityTransparentCallback \| undefined): this` | 23 static |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 18 (actionIntercept), API 20 (customActions)
- **API 版本号策略:** 以 SDK `.d.ts` 为 API 契约，各属性按实际引入版本标注；Static 统一为 @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| VirtualNode 触发 PROPERTY_UPDATE_LAYOUT | 无障碍虚拟节点是唯一触发布局更新的无障碍属性 | AC-4.1 |
| onAccessibilityHover/Transparent 存储位置不同 | 前者在 InputEventHub，后者在 AccessibilityProperty + AccessibilityManager | AC-5.1 ~ AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | 自定义动作最多 16 个，避免内存膨胀 | 代码审查 |
| 可靠性 | 动作名称截断保护（128字节） | 单元测试 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| 无障碍 | 是 | 本特性为无障碍核心能力 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityPropertyInterfaceFunction 中 ActionIntercept 和 TransparentCallback 的注册与调用"
  - repo: "openharmony/arkui_ace_engine"
    query: "ProcessAccessibilityVirtualNode 中虚拟节点布局约束的应用逻辑"
```