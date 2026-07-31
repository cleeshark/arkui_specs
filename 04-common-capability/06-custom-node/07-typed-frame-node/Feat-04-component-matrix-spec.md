# 特性规格

> Func-04-06-07-Feat-04 组件支持矩阵：固化 40 组件 createNode 引入波次与 accessor 版本分波。主角 ArkTS typeNode 组件矩阵。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件支持矩阵 |
| 特性编号 | Func-04-06-07-Feat-04 |
| 所属 Epic | 自定义节点能力 / TypedFrameNode |
| 优先级 | P2 |
| 目标版本 | API 12—26.0.0（分波引入） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | createNode 40 组件分波（12/14/18） | — |
| ADDED | accessor 版本分波（动态 15/19/20；静态 23/24/26） | — |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/07-typed-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: createNode 引入波次
**作为** 应用开发者，**我想要** 了解各组件 createNode 的引入版本，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN @since 12（24 组件）THEN Text/Column/Row/Stack/GridRow/GridCol/Flex/Swiper/Progress/Scroll/RelativeContainer/Divider/LoadingProgress/Search/Blank/Image/List/ListItem/TextInput/Button/ListItemGroup/WaterFlow/FlowItem/XComponent 可创建 | 正常 |
| AC-1.2 | WHEN @since 14（9 组件）THEN Marquee/TextArea/SymbolGlyph/QRCode/Badge/TextClock/TextTimer/Grid/GridItem 可创建 | 正常 |
| AC-1.3 | WHEN @since 18（7 组件）THEN Checkbox/CheckboxGroup/Radio/Rating/Select/Slider/Toggle 可创建 | 正常 |

### US-2: accessor 版本分波

**作为** 应用开发者，
**我想要** 了解 accessor 版本分波，
**以便** 按版本使用对应 accessor。
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 动态 getAttribute @since 20（除 Scroll @since 15）THEN 可获取属性 | 正常 |
| AC-2.2 | WHEN 动态 getEvent @since 19（Scroll/List/WaterFlow/Grid）THEN 可获取事件 | 正常 |
| AC-2.3 | WHEN 动态 bindController @since 15(Scroll)/20（Text/Swiper/List/TextInput/WaterFlow/TextArea/Grid）THEN 可绑定控制器 | 正常 |
| AC-2.4 | WHEN 静态 accessor @since 23 基线/24(文本输入)/26(滚动容器+GridRow)THEN 按版本可用 | 正常 |

### US-3: XComponent 多重载

**作为** 应用开发者，
**我想要** XComponent 多重载/多函数，
**以便** 按需创建 XComponent 节点。
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN XComponent createNode THEN 支持 3 重载：bare @since 12、options: XComponentOptions @since 12、parameters: NativeXComponentParameters @since 19 | 正常 |
| AC-3.2 | WHEN 静态 XComponent THEN 拆 3 函数 createXComponentNodeDefault/WithOptions/WithNativeParameters | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.3 | R-1,R-2,R-3 | 单测 | FrameNode.d.ts typeNode createNode |
| AC-2.1..2.4 | R-4,R-5,R-6,R-7 | 单测 | FrameNode.d.ts/.static.d.ets accessor |
| AC-3.1..3.2 | R-8,R-9 | 单测 | FrameNode.d.ts/.static.d.ets XComponent |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | createNode @since 12 | 24 组件可创建 | — | AC-1.1 |
| R-2 | 行为 | createNode @since 14 | 9 组件可创建 | — | AC-1.2 |
| R-3 | 行为 | createNode @since 18 | 7 组件可创建 | — | AC-1.3 |
| R-4 | 行为 | 动态 getAttribute @since 20（Scroll @since 15） | 可获取属性 | — | AC-2.1 |
| R-5 | 行为 | 动态 getEvent @since 19 | Scroll/List/WaterFlow/Grid 可获取事件 | — | AC-2.2 |
| R-6 | 行为 | 动态 bindController @since 15(Scroll)/20 | 可绑定控制器 | — | AC-2.3 |
| R-7 | 行为 | 静态 accessor @since 23/24/26 | 按版本可用 | 23 基线/24 文本输入/26 滚动容器 | AC-2.4 |
| R-8 | 边界 | XComponent 动态 3 重载 | bare/options/parameters @since 12/19 | — | AC-3.1 |
| R-9 | 边界 | XComponent 静态 3 函数 | Default/WithOptions/WithNativeParameters | — | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 createNode 波次 | 单测 | 12/14/18 三波 |
| VM-2 | R-4..R-7 accessor 分波 | 单测 | 动态 15/19/20、静态 23/24/26 |
| VM-3 | R-8..R-9 XComponent | 单测 | 3 重载/3 函数 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| (40 组件 createNode + accessor) | Public | 见规则定义 | TypedFrameNode/Attribute/Event/void | — | 组件矩阵 | AC-1,2,3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**组件支持矩阵**

| 属性 | 值 |
|------|-----|
| 函数签名 | 40 组件 createNode（动态 string-literal / 静态命名）+ accessor（getAttribute/getEvent/bindController） |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1,2,3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | @since 12 | 24 组件可创建 | AC-1.1 |
| 2 | @since 14/18 | 9/7 组件可创建 | AC-1.2,1.3 |
| 3 | accessor 版本分波 | 按版本可用 | AC-2.1..2.4 |
| 4 | XComponent 多重载 | 3 重载/3 函数 | AC-3.1,3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** createNode @since 12/14/18；动态 accessor @since 15/19/20；静态 accessor @since 23/24/26。
- **API 版本号策略:** 分波 @since 标注。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| 40 组件矩阵维护 | 新增组件需同步矩阵 | FrameNode.d.ts |
| accessor 版本分波复杂 | 动态/静态 + 各波次 | .d.ts/.static.d.ets |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 分波引入 | createNode 12/14/18 | AC-1 |
| accessor 分波 | 动态 15/19/20、静态 23/24/26 | AC-2 |
| XComponent 特殊 | 3 重载/3 函数 | AC-3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可维护性 | 矩阵集中管理 | 单测 | FrameNode.d.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | 12-26 分波演进 | AC-1,2 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（矩阵；类型 Feat-01/动态 Feat-02/静态 Feat-03）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode.d.ts/.static.d.ets typeNode 40 组件 createNode 分波与 accessor 版本矩阵"
```
