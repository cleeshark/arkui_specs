# 特性规格

> Func-05-14-01-Feat-02 Shape 通用绘制样式存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Shape 通用绘制样式 |
| 特性编号 | Func-05-14-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性覆盖 Shape、Rect、Circle、Ellipse、Line、Polyline、Polygon、Path 共用的 fill/stroke、opacity、width、dash、cap、join、miter、antiAlias、Resource/ColorMetrics 以及父 Shape 绘制属性向子图形合并的规则。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 填充与描边 | 颜色、透明度、宽度、Resource 和 reset |
| ADDED | 线型 | dash、offset、cap、join、miter 与非法值 |
| ADDED | 抗锯齿与继承 | antiAlias、父 Shape 属性合并和前景色关系 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/01-shape/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Shape SDK | `interface/sdk-js/api/@internal/component/ets/shape.d.ts` | 已核对 |
| Model | `frameworks/core/components_ng/pattern/shape/shape_abstract_model_ng.cpp` | 已核对 |
| Painter | `frameworks/core/components_ng/pattern/shape/drawing_painter.cpp` | 已核对 |

## 用户故事

### US-1: 配置填充和描边

**作为** 图形应用开发者  
**我想要** 为任意 Shape 类组件设置通用绘制样式  
**以便** 获得一致的视觉语言

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN fill/stroke 接收合法 ResourceColor 或该组件支持的 ColorMetrics THEN 对应 Brush/Pen 使用解析颜色 | 正常 |
| AC-1.2 | WHEN fillOpacity/strokeOpacity 为 0、1 或区间内数值/字符串/Resource THEN 透明度按解析结果作用于填充/描边 | 正常 |
| AC-1.3 | WHEN opacity 超出 [0,1]、为 NaN/Infinity 或资源失败 THEN 按 SDK/bridge 默认或钳制路径处理，不向 Painter 传非有限值 | 异常 |
| AC-1.4 | WHEN strokeWidth 合法且非负 THEN Pen 使用该宽度；负数/非法值按默认或 reset 处理 | 边界 |

### US-2: 配置线型与抗锯齿

**作为** 图形应用开发者
**我想要** 配置描边线型和抗锯齿选项
**以便** 控制 Shape 轮廓的绘制质量与视觉效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN strokeDashArray 含合法非负长度且数量满足实现规则 THEN Pen 使用对应 dash pattern；Resource 变化后刷新 | 正常 |
| AC-2.2 | WHEN dash 数组为空、含负数/非有限值或 Resource 失败 THEN 清除或回退 dash，不生成非法 PathEffect | 异常 |
| AC-2.3 | WHEN设置 lineCap/lineJoin/miterLimit/dashOffset THEN Painter 使用合法枚举和长度；非法枚举恢复默认 | 正常 |
| AC-2.4 | WHEN antiAlias 设置 true/false/undefined THEN Brush/Pen 分别启用、禁用或恢复属性默认值 | 正常 |

### US-3: 合并父 Shape 与子图形属性

**作为** 图形应用开发者
**我想要** 在 Shape 容器中组合父级与子图形的绘制属性
**以便** 得到可预测的继承、覆盖和最终绘制结果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 子图形位于 Shape 容器且自身未覆盖某通用样式 THEN PaintMethod 合并祖先 Shape 对应绘制属性 | 正常 |
| AC-3.2 | WHEN 子图形显式设置同名样式 THEN 子图形值覆盖继承值；独立图形只使用自身/默认属性 | 边界 |
| AC-3.3 | WHEN foregroundColor 或通用颜色策略参与 THEN 按当前 RenderContext/Shape 属性优先级得到最终颜色，不静默统一不同入口 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Model/Painter UT | `frameworks/core/components_ng/pattern/shape/shape_abstract_model_ng.cpp:27-108,203-254`; `frameworks/core/components_ng/pattern/shape/drawing_painter.cpp:116-177` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Dash/line style UT | `frameworks/core/components_ng/pattern/shape/shape_abstract_model_ng.cpp:60-108,155-184`; `frameworks/core/components_ng/pattern/shape/drawing_painter.cpp:129-168` |
| AC-3.1~AC-3.3 | R-9~R-11 | 已有实现 | Parent merge UT | `frameworks/core/components_ng/pattern/shape/polygon_paint_method.cpp:28-34`; `frameworks/core/components_ng/pattern/shape/shape_paint_property.h:27-133` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 合法 fill/stroke | Brush/Pen 使用解析颜色 | 类型按 SDK | AC-1.1 |
| R-2 | 行为 | opacity∈[0,1] | 分别作用 fill/stroke | Resource 可刷新 | AC-1.2 |
| R-3 | 异常 | opacity 非有限/越界/资源失败 | 默认/钳制/拒绝 | 不传非有限值 | AC-1.3 |
| R-4 | 边界 | strokeWidth 非负/非法 | 使用合法值或默认/reset | 不使用负宽度 | AC-1.4 |
| R-5 | 行为 | dash 数组合法 | 设置 PathEffect | 长度非负有限 | AC-2.1 |
| R-6 | 异常 | dash 空/非法 | 清除或回退 | 不生成非法效果 | AC-2.2 |
| R-7 | 行为 | cap/join/miter/offset 合法 | 写对应 Pen 属性 | 非法枚举默认 | AC-2.3 |
| R-8 | 恢复 | antiAlias undefined/reset | 恢复默认 | true/false 可显式覆盖 | AC-2.4 |
| R-9 | 行为 | 子项未覆盖 | 合并父 Shape 属性 | 仅容器后代 | AC-3.1 |
| R-10 | 边界 | 子项显式设置 | 子项值优先 | 独立图形无父继承 | AC-3.2 |
| R-11 | 边界 | foregroundColor 参与 | 按现有优先级选最终颜色 | 通道差异显式记录 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | Shape/common modifier UT | 颜色、透明度、宽度 |
| VM-2 | AC-2.1~AC-2.4 | dash/line/antiAlias UT | 全设置形式与非法值 |
| VM-3 | AC-3.1~AC-3.3 | 容器/独立图形对照 UT | 继承和覆盖 |

## API 变更分析

### 新增 API

N/A，通用 Shape 样式均为已有 API。

### 变更/废弃 API

N/A；Circle 的 ColorMetrics overload 等版本差异仅作兼容记录。

## 接口规格

### 接口定义

**CommonShapeMethod 样式集合**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fill/stroke/strokeWidth/strokeOpacity/fillOpacity/strokeDashArray/strokeDashOffset/strokeLineCap/strokeLineJoin/strokeMiterLimit/antiAlias` |
| 返回值 | 当前 Shape Attribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.3 |

**参数约束**

| 参数组 | 类型 | 必填 | 默认值 | 约束条件 |
|--------|------|------|--------|----------|
| color | ResourceColor/ColorMetrics | 是 | 组件默认 | ColorMetrics 仅声明支持的接口 |
| opacity | number/string/Resource | 是 | 1 | 有效区间 [0,1] |
| width/offset/miter | Length/Resource | 是 | 属性默认 | 非负有限值 |
| dash | Array<any> | 是 | [] | 元素为非负长度 |
| cap/join | enum | 是 | 枚举默认 | 只接受 SDK 枚举 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 父 Shape 有样式、子项未设置 | 子项继承 | AC-3.1 |
| 2 | 子项显式设置 | 子项覆盖 | AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 是；Resource、ColorMetrics、Static/Builder 支持按 API 版本演进。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** Dynamic 起始版本、API 20 类型演进、Static 23、Builder 26 全量记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 公共 PaintProperty | 各图形复用 ShapePaintProperty | AC-1.1 |
| 父属性合并 | 子 PaintMethod 在绘制前合并祖先属性 | AC-3.1 |
| Resource 生命周期 | ResourceObject 更新必须回写并标脏 | AC-1.2, AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单图形样式合并为固定属性集合 | Trace | `frameworks/core/components_ng/pattern/shape/polygon_paint_method.cpp:28-34` |
| 功耗 | 仅绘制时生效 | 审查 | VM-1 |
| 内存 | Resource 回调随节点释放 | 生命周期 UT | VM-1 |
| 安全 | 非法数组/数值不进入 Painter | Fuzz | VM-2 |
| 可靠性 | reset/资源失败恢复默认 | 边界 UT | VM-1, VM-2 |
| 可测试性 | PaintProperty/Pen/Brush 可断言 | UT | VM-1~VM-3 |
| 自动化维测 | 样式可 Inspector/Dump | Inspector | AC-1.1 |
| 定界定位 | SDK→bridge→model→paint 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 低密度/小尺寸线条常见 | 按 density 转换 | 像素测试 | AC-1.4 |
| 平板 | 大面积绘制 | 样式语义不变 | 截图测试 | VM-1 |
| 折叠屏 | density/资源可能变化 | Resource 重载 | 折叠态测试 | AC-2.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 颜色/透明度不自动补语义 | AC-1.1 |
| 大字体 | 否 | 不涉及文本 | VM-1 |
| 深色模式 | 是 | ResourceColor 可随主题刷新 | AC-1.1 |
| 多窗口/分屏 | 是 | density/尺寸重绘 | AC-2.1 |
| 多用户 | 否 | 无用户状态 | VM-1 |
| 版本升级 | 是 | ColorMetrics/Static/Builder 需回归 | 兼容性声明 |
| 生态兼容 | 是 | 父子优先级保持 | AC-3.1, AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Shape 样式继承
  Scenario: 子图形覆盖父描边
    Given 父 Shape 设置红色 stroke
    And 子 Rect 设置蓝色 stroke
    When 绘制 Shape 树
    Then Rect 使用蓝色描边且未覆盖属性仍继承父 Shape
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 颜色、Resource、数值、数组、继承与 reset 边界明确
- [x] API 版本差异保留
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ShapePaintProperty stroke fill dash antiAlias inherit"
  - repo: "openharmony/interface_sdk-js"
    query: "CommonShapeMethod fill stroke API"
```

**关键文档：** `05-ui-components/14-drawing-components/01-shape/design.md`
