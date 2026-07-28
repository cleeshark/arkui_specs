# 特性规格

> Func-04-06-02-Feat-03 FrameNode 布局与度量：固化 onMeasure/onLayout 回调、measure/layout 触发、setMeasuredSize/setLayoutPosition、getMeasuredSize/getLayoutPosition、setNeedsLayout/invalidate、getUserConfig{BorderWidth/Padding/Margin/Size}、LayoutConstraint 共 14 个公开 API 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameNode 布局与度量 |
| 特性编号 | Func-04-06-02-Feat-03 |
| 所属 Epic | 自定义节点能力 / FrameNode |
| 优先级 | P1 |
| 目标版本 | API 12（dynamic 起始）；静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂（L2） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | onMeasure/onLayout/setMeasuredSize/setLayoutPosition/measure/layout/setNeedsLayout/invalidate/getMeasuredSize/getLayoutPosition/getUserConfig{BorderWidth,Padding,Margin,Size}/LayoutConstraint | API 12 起始 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/02-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `FrameNode.static.d.ets` | — |

## 用户故事

### US-1: 触发度量与布局
**作为** 应用开发者，**我想要** 主动触发节点的度量与布局。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `measure(constraint)` 传入有效 LayoutConstraint THEN 拆为 6 浮点(minW,minH,maxW,maxH,pctW,pctH)调用 MeasureNode→FrameNode::Measure | 正常 |
| AC-1.2 | WHEN constraint 中 minSize==maxSize THEN 设置 selfIdealSize 为精确尺寸 | 边界 |
| AC-1.3 | WHEN 节点 VisibleType::GONE THEN 度量结果尺寸为 (0,0) | 边界 |
| AC-1.4 | WHEN `layout(position)` THEN SetMarginFrameOffset 设定偏移并触发 FrameNode::Layout | 正常 |

### US-2: 用户自定义度量/布局回调
**作为** 应用开发者，**我想要** 重写 onMeasure/onLayout 自定义度量布局逻辑。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 在 FrameNode 实例定义 onMeasure(constraint) THEN 构造时 SetDrawFunc/SetCustomFunc 读取并注入 ExtensionCustomNode | 正常 |
| AC-2.2 | WHEN 调用 measure/layout 引擎度量 THEN onMeasure 回调被调用，参数为 LayoutConstraint | 正常 |
| AC-2.3 | WHEN 未定义 onMeasure/onLayout THEN 走默认 CustomFrameNode 布局策略 | 边界 |

### US-3: 直接写入度量结果
**作为** 应用开发者，**我想要** 直接设置度量尺寸与布局位置。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `setMeasuredSize(size)` THEN 负值 clamp 至 0，直接写 geometryNode frame size | 正常 |
| AC-3.2 | WHEN `setLayoutPosition(position)` THEN 直接写 margin frame offset（含 margin） | 正常 |
| AC-3.3 | WHEN 仅 setMeasuredSize/setLayoutPosition 不触发 layout THEN 改动不可见（须另触发 measure/layout 或 setNeedsLayout） | 边界 |

### US-4: 读取度量结果
**作为** 应用开发者，**我想要** 读取度量尺寸与布局位置。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN `getMeasuredSize()` 且节点有效 THEN 返回 frame size（px，无 VP 转换） | 正常 |
| AC-4.2 | WHEN 节点 disposed THEN 抛 100026（getValidNodePtr 守卫） | 异常 |
| AC-4.3 | WHEN `getLayoutPosition()` THEN 返回 margin-box 偏移（px，减去 margin） | 正常 |
| AC-4.4 | WHEN 节点 disposed 调 getLayoutPosition THEN 抛 100026 | 异常 |

### US-5: 标记脏节点
**作为** 应用开发者，**我想要** 标记节点需要重新度量/重绘。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN `setNeedsLayout()` THEN MarkDirty(MEASURE_SELF_AND_PARENT)，下帧重新度量自身+父 | 正常 |
| AC-5.2 | WHEN `invalidate()` 且节点为 CustomFrameNode THEN pattern->Invalidate()+RequestNextFrame（仅渲染脏） | 正常 |
| AC-5.3 | WHEN invalidate() 在非 CustomFrameNode THEN 静默 no-op | 边界 |
| AC-5.4 | WHEN setNeedsLayout vs invalidate THEN 前者 layout 脏（重度量），后者 render 脏（仅重绘） | 边界 |

### US-6: 读取用户配置几何属性
**作为** 应用开发者，**我想要** 读取用户配置的 border/padding/margin/size。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN `getUserConfigBorderWidth()` THEN 返回 Edges(top,right,bottom,left) LengthMetrics（value+unit） | 正常 |
| AC-6.2 | WHEN `getUserConfigPadding()`/`getUserConfigMargin()` THEN 同 8 数组 T,R,B,L 编码 | 正常 |
| AC-6.3 | WHEN `getUserConfigSize()` THEN 返回 Size(width,height) LengthMetrics（用户配置尺寸，非度量尺寸） | 正常 |
| AC-6.4 | WHEN 节点 disposed THEN 不抛 100026（用 getNodePtr），native 返默认 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3 | 单测 | view_model.cpp:1011; frame_node.cpp:6080,6248 |
| AC-2.1..2.3 | R-4,R-5 | 单测 | bridge:303 SetDrawFunc; lazy_layout_algorithm.ts:96 |
| AC-3.1..3.3 | R-6,R-7,R-8 | 单测 | node_api.cpp:1751,1809; geometry_node.h:80 |
| AC-4.1..4.4 | R-9,R-10,R-11 | 单测 | frame_node.ts:675,680; bridge:1942,2025 |
| AC-5.1..5.4 | R-12,R-13,R-14 | 单测 | node_api.cpp:1612; frame_node_modifier.cpp:84; frame_node.cpp:3502,3611 |
| AC-6.1..6.4 | R-15,R-16 | 单测 | bridge:2042,2060,2077,2094 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | measure(constraint) | 按 constraint（min/max/percentReference）触发度量；结果可经 getMeasuredSize 读取 | min==max 视为精确尺寸 | AC-1.1,1.2 |
| R-2 | 行为 | layout(position) | 按 position 触发布局；结果可经 getLayoutPosition 读取 | — | AC-1.4 |
| R-3 | 边界 | VisibleType::GONE 时 measure | 度量结果尺寸为 (0,0) | — | AC-1.3 |
| R-4 | 行为 | 构造时定义 onMeasure/onLayout | 用户回调在构造时注入 | 未定义走默认策略 | AC-2.1,2.3 |
| R-5 | 行为 | 引擎度量触发 onMeasure 回调 | 回调获 LayoutConstraint 参数 | — | AC-2.2 |
| R-6 | 行为 | setMeasuredSize(size) | 负值 clamp 至 0；直接设置度量尺寸 | int32 截断；须另触发方可见 | AC-3.1 |
| R-7 | 行为 | setLayoutPosition(position) | 直接设置布局位置 | int32 截断；须另触发方可见 | AC-3.2 |
| R-8 | 边界 | 仅 set 不触发 layout | 改动不可见，须另触发 measure/layout/setNeedsLayout | — | AC-3.3 |
| R-9 | 行为 | getMeasuredSize() 有效节点 | 返回度量尺寸（px） | 无 VP 转换 | AC-4.1 |
| R-10 | 异常 | getMeasuredSize/getLayoutPosition disposed | 抛 100026 | ArkTS 守卫 | AC-4.2,4.4 |
| R-11 | 行为 | getLayoutPosition() | 返回布局位置（px，不含 margin） | 与 getPositionToParent 不同 | AC-4.3 |
| R-12 | 行为 | setNeedsLayout() | 标记 layout 脏，下帧重新度量自身与父节点 | frozen 则延后 | AC-5.1 |
| R-13 | 行为 | invalidate() CustomFrameNode | 标记 render 脏并请求重绘 | 非 CustomFrameNode no-op | AC-5.2,5.3 |
| R-14 | 边界 | setNeedsLayout vs invalidate | 前者 layout 脏重度量；后者 render 脏仅重绘 | — | AC-5.4 |
| R-15 | 行为 | getUserConfig{BorderWidth/Padding/Margin} | 返回用户配置的 border/padding/margin（Edges，T/R/B/L 顺序） | 无 transform/relayout | AC-6.1,6.2 |
| R-16 | 行为 | getUserConfigSize | 返回用户配置的尺寸（width/height） | 非度量尺寸 | AC-6.3,6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1,R-2,R-3 measure/layout | 单测 | min==max、GONE 零尺寸 |
| VM-2 | R-4,R-5 回调注入 | 单测 | SetDrawFunc、未定义默认 |
| VM-3 | R-6,R-7,R-8 直接写入 | 单测 | clamp 负值、int32 截断、不可见 |
| VM-4 | R-9,R-10,R-11 读取 | 单测 | px、100026、margin 差异 |
| VM-5 | R-12,R-13,R-14 脏标记 | 单测 | layout vs render 脏、CustomFrameNode 限制 |
| VM-6 | R-15,R-16 用户配置 | 单测 | T,R,B,L 编码、size 非度量 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| onMeasure(constraint) | Public | constraint: LayoutConstraint | void | — | 用户度量回调 | AC-2 |
| onLayout(position) | Public | position: Position | void | — | 用户布局回调 | AC-2 |
| measure(constraint) | Public | constraint: LayoutConstraint | void | — | 触发度量 | AC-1 |
| layout(position) | Public | position: Position | void | — | 触发布局 | AC-1 |
| setMeasuredSize(size) | Public | size: Size | void | — | 写度量尺寸 | AC-3 |
| setLayoutPosition(position) | Public | position: Position | void | — | 写布局位置 | AC-3 |
| setNeedsLayout() | Public | — | void | — | 标记 layout 脏 | AC-5 |
| invalidate() | Public | — | void | — | 标记 render 脏(CustomFrameNode) | AC-5 |
| getMeasuredSize() | Public | — | Size | 100026 | 读度量尺寸(px) | AC-4 |
| getLayoutPosition() | Public | — | Position | 100026 | 读布局位置(px) | AC-4 |
| getUserConfigBorderWidth() | Public | — | Edges\<LengthMetrics\> | — | 读 border | AC-6 |
| getUserConfigPadding() | Public | — | Edges\<LengthMetrics\> | — | 读 padding | AC-6 |
| getUserConfigMargin() | Public | — | Edges\<LengthMetrics\> | — | 读 margin | AC-6 |
| getUserConfigSize() | Public | — | SizeT\<LengthMetrics\> | — | 读用户配置 size | AC-6 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**measure / layout**

| 属性 | 值 |
|------|-----|
| 函数签名 | `measure(constraint: LayoutConstraint): void`; `layout(position: Position): void` (@since 12 dyn/23 static) |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| constraint | LayoutConstraint | 是 | — | {minSize,maxSize,percentReference:Size}；min==max 设精确 |
| position | Position | 是 | — | x/y number |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 constraint | MeasureNode→FrameNode::Measure | AC-1.1 |
| 2 | min==max | 设精确 idealSize | AC-1.2 |
| 3 | GONE | 零尺寸 | AC-1.3 |

**getMeasuredSize / getLayoutPosition**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getMeasuredSize(): Size`; `getLayoutPosition(): Position` (@since 12 dyn/23 static) |
| 返回值 | Size / Position (px) |
| 开放范围 | Public |
| 错误码 | 100026 (disposed) |
| 关联 AC | AC-4 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效节点 | 返 px（frame size / margin-frame offset 减 margin） | AC-4.1,4.3 |
| 2 | disposed | 抛 100026 | AC-4.2,4.4 |

**setNeedsLayout / invalidate**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setNeedsLayout(): void`; `invalidate(): void` (@since 12 dyn/23 static) |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | setNeedsLayout | layout 脏，下帧重度量自身+父 | AC-5.1 |
| 2 | invalidate CustomFrameNode | render 脏+RequestNextFrame | AC-5.2 |
| 3 | invalidate 非 CustomFrameNode | 静默 no-op | AC-5.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 12（dynamic）；静态 @since 23。
- **API 版本号策略:** 全部 @since 12 dyn / 23 static。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| getMeasuredSize/getLayoutPosition 返 px 而位置查询返 vp | 单位不一致：geometry 直读 px，position 查询走 modifier VP 转换 | frame_node_modifier.cpp:471; bridge:1942 |
| setMeasuredSize int32 截断 | bridge 传 JS double 隐式截 int32，小数/超 INT_MAX 失精度 | node_api.cpp:1751 |
| onMeasure/onLayout 实际由 LazyLayout 策略承载 | SDK 声明在 FrameNode，运行时回调经 SetCustomFunc 注入，非独立方法 | bridge:303; lazy_layout_algorithm.ts:96 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 单位差异 | getMeasuredSize/getLayoutPosition 返 px；getUserConfig*/position 查询返 vp/LengthMetrics | AC-4,6 |
| dirty 分级 | setNeedsLayout=layout 脏；invalidate=render 脏(仅 CustomFrameNode) | AC-5 |
| 直接写入无 dirty | setMeasuredSize/setLayoutPosition 须另触发方可见 | AC-3.3 |
| LayoutConstraint 精确模式 | min==max 触发 selfIdealSize 精确 | AC-1.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | measure/layout 触发完整度量链，大子树有开销 | 单测/性能 | frame_node.cpp:6080,6248 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 大字体 | 否 | measure 受 fontScale 影响但非本 Feat 直接 | — |
| 版本升级 | 否 | 全部 @since 12/23 | — |

## 行为场景

```gherkin
Feature: FrameNode 布局与度量
  Scenario: measure 精确尺寸
    Given constraint.minSize == constraint.maxSize
    When 调用 node.measure(constraint)
    Then 引擎设置 selfIdealSize 为精确尺寸

  Scenario: disposed 节点读度量尺寸
    Given 节点 N 已 dispose
    When 调用 N.getMeasuredSize()
    Then 抛出 BusinessError(100026)

  Scenario: invalidate 非 CustomFrameNode
    Given 节点 N 为非自定义节点
    When 调用 N.invalidate()
    Then 静默 no-op
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（布局度量；不含坐标转换 Feat-04）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode::Measure/Layout 度量布局核心与 OnLayoutFinish/SyncGeometryNode 几何同步"
  - repo: "openharmony/arkui_ace_engine"
    query: "ViewModel::MeasureNode/LayoutNode LayoutConstraint 拆分与 selfIdealSize 精确模式"
  - repo: "openharmony/arkui_ace_engine"
    query: "MarkDirtyNode PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT 脏标记传播"
```
