# 特性规格

> Func-04-06-02-Feat-04 FrameNode 坐标转换与位置查询：固化 getPositionTo{Window,Parent,Screen}、getGlobalPositionOnDisplay、三个 WithTransform 变体、convertPosition/convertPositionToWindow/convertPositionFromWindow 共 9 个公开 API 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameNode 坐标转换与位置查询 |
| 特性编号 | Func-04-06-02-Feat-04 |
| 所属 Epic | 自定义节点能力 / FrameNode |
| 优先级 | P1 |
| 目标版本 | API 12（dynamic 起始）；convertPosition API 22；convertPositionTo/FromWindow、getGlobalPositionOnDisplay API 23/20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂（L2） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | getPositionToWindow/Parent/Screen + 三 WithTransform | API 12 |
| ADDED | getGlobalPositionOnDisplay | API 20 |
| ADDED | convertPosition | API 22 |
| ADDED | convertPositionToWindow/convertPositionFromWindow | API 23 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/02-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `FrameNode.static.d.ets` | — |

## 用户故事

### US-1: 查询节点位置（无变换）
**作为** 应用开发者，**我想要** 获取节点相对窗口/父/屏幕的位置（不含图形变换）。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `getPositionToWindow()` THEN 返回相对窗口偏移（vp），累加父 paintRectWithoutTransform offset，不含 rotate/scale/translate 变换 | 正常 |
| AC-1.2 | WHEN `getPositionToParent()` THEN 返回父 paintRect 内偏移（vp），position 属性优先 | 正常 |
| AC-1.3 | WHEN `getPositionToScreen()` THEN 返回窗口偏移(+浮动窗口 scale)+窗口屏幕偏移（vp） | 正常 |
| AC-1.4 | WHEN 节点 disposed THEN 不抛 100026（用 getNodePtr），native 返默认 | 边界 |

### US-2: 查询节点位置（含变换）
**作为** 应用开发者，**我想要** 获取含图形变换矩阵的位置。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `getPositionToWindowWithTransform()` THEN 累加本节点+各祖先 GetPointTransformRotate，无浮动 scale | 正常 |
| AC-2.2 | WHEN `getPositionToParentWithTransform()` THEN 仅应用本节点 transform | 正常 |
| AC-2.3 | WHEN `getPositionToScreenWithTransform()` THEN transform 窗口偏移+屏幕偏移+浮动 scale | 正常 |
| AC-2.4 | WHEN 无变换 THEN WithTransform 与无变换变体结果一致 | 边界 |

### US-3: 查询全局显示位置
**作为** 应用开发者，**我想要** 获取相对全局显示器位置（多显示器/IME）。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `getGlobalPositionOnDisplay()` THEN 返回 GetFinalOffsetRelativeToWindow(+浮动 scale)+GetGlobalDisplayWindowRect offset | 正常 |

### US-4: 跨节点坐标转换
**作为** 应用开发者，**我想要** 将坐标在本节点与目标节点局部坐标系间转换。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN `convertPosition(pos, target)` 且有共同祖先 THEN 经 inverse/forward transform 矩阵链转换为 target 局部坐标 | 正常 |
| AC-4.2 | WHEN target 无共同祖先 THEN 抛 100024 ("no common ancestor") | 异常 |
| AC-4.3 | WHEN target/position null THEN 抛 100025 | 异常 |
| AC-4.4 | WHEN this disposed THEN null ptr→ConvertPoint false→误抛 100024（非 100026） | 边界 |

### US-5: 局部↔窗口坐标转换
**作为** 应用开发者，**我想要** 在局部坐标与窗口坐标间转换。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN `convertPositionToWindow(posByLocal)` 且节点在主树 THEN 走 ConvertPositionToWindow(fromWindow=false) 转换 | 正常 |
| AC-5.2 | WHEN param null/undefined THEN 抛 401 | 异常 |
| AC-5.3 | WHEN 节点 disposed THEN 抛 100026 | 异常 |
| AC-5.4 | WHEN 节点不在主树 THEN 抛 100028 ("not on the main tree") | 异常 |
| AC-5.5 | WHEN `convertPositionFromWindow(posByWindow)` THEN 复用 ConvertPositionToWindow(fromWindow=true) 反向转换 | 正常 |
| AC-5.6 | WHEN x/y 非数字 THEN 抛 401 | 异常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3,R-12 | 单测 | frame_node.cpp:4756,2529,4794; modifier:471,442,457 |
| AC-2.1..2.4 | R-4,R-5,R-6,R-7 | 单测 | frame_node.cpp:4864,4831,4845 |
| AC-3.1 | R-8 | 单测 | frame_node.cpp:4807 |
| AC-4.1..4.4 | R-9,R-10,R-11 | 单测 | modifier:218; frame_node.cpp:5088 |
| AC-5.1..5.6 | R-13,R-14,R-15,R-16 | 单测 | modifier:238,260; frame_node.ts:1001,1027; frame_node.cpp:5139 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | getPositionToWindow() | 返回相对窗口的位置（不含图形变换；position 属性优先） | 返 vp；无浮动 scale | AC-1.1 |
| R-2 | 行为 | getPositionToParent() | 返回相对父节点的位置（position 属性优先） | 返 vp | AC-1.2 |
| R-3 | 行为 | getPositionToScreen() | 返回相对屏幕的位置（浮动窗口含缩放） | 返 vp | AC-1.3 |
| R-4 | 行为 | getPositionToWindowWithTransform() | 返回含图形变换（本节点+各祖先 transform）的窗口位置 | 返 vp；无浮动 scale | AC-2.1 |
| R-5 | 行为 | getPositionToParentWithTransform() | 返回含本节点 transform 的父位置 | 返 vp | AC-2.2 |
| R-6 | 行为 | getPositionToScreenWithTransform() | 返回含 transform 与浮动缩放的屏幕位置 | 返 vp | AC-2.3 |
| R-7 | 边界 | 无变换时 WithTransform==无变换 | 结果一致 | — | AC-2.4 |
| R-8 | 行为 | getGlobalPositionOnDisplay() | 返回相对全局显示器的位置 | 多显示器/IME | AC-3.1 |
| R-9 | 行为 | convertPosition(pos, target) 有共同祖先 | 将 pos 转换为 target 节点局部坐标系（含 transform 矩阵） | vp↔px 转换 | AC-4.1 |
| R-10 | 异常 | convertPosition 无共同祖先 | 抛 100024 | — | AC-4.2 |
| R-11 | 异常 | convertPosition target/position null | 抛 100025 | — | AC-4.3 |
| R-12 | 边界 | convertPosition this disposed | 误抛 100024（非 100026） | 已知 quirk：未预检 isDisposed | AC-4.4 |
| R-13 | 行为 | convertPositionToWindow(pos) 在主树 | 将局部坐标转换为窗口坐标 | 返 vp | AC-5.1 |
| R-14 | 异常 | convertPositionTo/FromWindow param null | 抛 401 | ArkTS 预检 | AC-5.2 |
| R-15 | 异常 | convertPositionTo/FromWindow disposed | 抛 100026 | — | AC-5.3,5.5 |
| R-16 | 异常 | convertPositionTo/FromWindow 不在主树 | 抛 100028 | — | AC-5.4 |
| R-17 | 异常 | convertPositionTo/FromWindow x/y 非数字 | 抛 401 | — | AC-5.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 无变换位置 | 单测 | vp、浮动 scale、position 优先 |
| VM-2 | R-4..R-7 含变换位置 | 单测 | transform 链、无变换一致 |
| VM-3 | R-8 全局显示 | 单测 | 多显示器 offset |
| VM-4 | R-9..R-12 convertPosition | 单测 | 共同祖先、100024/100025、disposed quirk |
| VM-5 | R-13..R-17 convertTo/FromWindow | 单测 | 401/100026/100028 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| getPositionToWindow() | Public | — | Position(vp) | — | 相对窗口位置 | AC-1 |
| getPositionToParent() | Public | — | Position(vp) | — | 相对父位置 | AC-1 |
| getPositionToScreen() | Public | — | Position(vp) | — | 相对屏幕位置 | AC-1 |
| getGlobalPositionOnDisplay() | Public | — | Position(vp) | — | 全局显示位置 | AC-3 |
| getPositionToWindowWithTransform() | Public | — | Position(vp) | — | 含变换窗口位置 | AC-2 |
| getPositionToParentWithTransform() | Public | — | Position(vp) | — | 含变换父位置 | AC-2 |
| getPositionToScreenWithTransform() | Public | — | Position(vp) | — | 含变换屏幕位置 | AC-2 |
| convertPosition(pos, target) | Public | pos: Position; target: FrameNode | Position | 100024,100025 | 跨节点转换 | AC-4 |
| convertPositionToWindow(posByLocal) | Public | posByLocal: Position | Position | 401,100026,100028 | 局部→窗口 | AC-5 |
| convertPositionFromWindow(posByWindow) | Public | posByWindow: Position | Position | 401,100026,100028 | 窗口→局部 | AC-5 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**getPositionTo*（无变换/含变换）**

| 属性 | 值 |
|------|-----|
| 函数签名 | 见 API 变更分析 (@since 12 dyn/23 static; getGlobalPositionOnDisplay @since 20; WithTransform @since 12) |
| 返回值 | Position (vp) |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1,2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 无变换变体 | 累加 paintRect offset，不含 transform | AC-1 |
| 2 | WithTransform | 应用 GetPointTransformRotate 链 | AC-2 |
| 3 | 浮动窗口 | Screen/Display/ScreenWithTransform 乘 windowScale | AC-1.3,2.3,3.1 |

**convertPosition / convertPositionToWindow / convertPositionFromWindow**

| 属性 | 值 |
|------|-----|
| 函数签名 | convertPosition(pos, target): Position(@since 22); convertPositionToWindow/FromWindow(pos): Position(@since 23) |
| 返回值 | Position (vp) |
| 开放范围 | Public |
| 错误码 | convertPosition: 100024,100025; convertTo/FromWindow: 401,100026,100028 |
| 关联 AC | AC-4,5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | convertPosition 有共同祖先 | 矩阵链转 target 局部 | AC-4.1 |
| 2 | 无共同祖先 | 抛 100024 | AC-4.2 |
| 3 | param null | 抛 401/100025 | AC-4.3,5.2 |
| 4 | disposed | 抛 100026（To/FromWindow）；convertPosition 误抛 100024 | AC-4.4,5.3 |
| 5 | 不在主树 | 抛 100028 | AC-5.4 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** getPositionTo*/WithTransform API 12；getGlobalPositionOnDisplay API 20；convertPosition API 22；convertPositionTo/FromWindow API 23；静态 @since 23。
- **API 版本号策略:** 逐 API @since 标注。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| convertPosition this disposed 误抛 100024 | 未预检 this.isDisposed()，null ptr→ConvertPoint false→100024（应 100026） | frame_node.ts:972; modifier:218 |
| 单位差异 | 位置查询返 vp，getMeasuredSize/getLayoutPosition 返 px | modifier:471 vs bridge:1942 |
| 浮动窗口 scale 仅部分 API 应用 | Window/WindowWithTransform 不乘 scale；Screen/Display/ScreenWithTransform 乘 | frame_node.cpp:4818 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 变换矩阵链 | WithTransform 应用 GetPointTransformRotate；无变换变体忽略 | AC-2 |
| 共同祖先 | convertPosition 须 FindSameParentComponent 命中 | AC-4.2 |
| 主树前置 | convertPositionTo/FromWindow 须 IsOnMainTree | AC-5.4 |
| 浮动窗口 scale | WINDOW_MODE_FLOATING 时 Screen/Display 乘 windowScale | AC-1.3,3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | transform 矩阵链遍历祖先，深树有开销 | 单测 | frame_node.cpp:4864,5088 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 多显示器 | getGlobalPositionOnDisplay 用 GlobalDisplayWindowRect | 验证多屏 offset | 单测 | frame_node.cpp:4807 |
| 浮动窗口 | Screen/Display 乘 windowScale | 验证浮动 scale | 单测 | frame_node.cpp:4818 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口/分屏 | 是 | 浮动窗口 scale 影响 Screen/Display | AC-1.3,3.1 |
| 版本升级 | 是 | convertPosition(22)/To-FromWindow(23) 版本演进 | AC-4,5 |

## 行为场景

```gherkin
Feature: FrameNode 坐标转换与位置查询
  Scenario: convertPosition 无共同祖先
    Given this 与 target 无共同祖先
    When 调用 this.convertPosition(pos, target)
    Then 抛出 BusinessError(100024)

  Scenario: convertPositionToWindow 不在主树
    Given 节点 N 未挂载主树
    When 调用 N.convertPositionToWindow(pos)
    Then 抛出 BusinessError(100028)

  Scenario: 浮动窗口 getPositionToScreen
    Given 窗口模式为 WINDOW_MODE_FLOATING
    When 调用 node.getPositionToScreen()
    Then 结果包含 windowScale 缩放
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（坐标转换；不含渲染 Feat-05）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "GetOffsetRelativeToWindow/GetPositionToScreen 与 GetPointTransformRotate 变换矩阵链"
  - repo: "openharmony/arkui_ace_engine"
    query: "ConvertPoint/ConvertPositionToWindow FindSameParentComponent 共同祖先与 inverse/forward 矩阵"
  - repo: "openharmony/arkui_ace_engine"
    query: "GetFinalOffsetRelativeToWindow 浮动窗口 windowScale 与 GlobalDisplayWindowRect"
```
