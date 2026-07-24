# 特性规格

> Func-05-14-01-Feat-01 Shape 容器、视口与 Mesh 存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Shape 容器、视口与 Mesh |
| 特性编号 | Func-05-14-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Shape 是绘制组件容器，可按自身尺寸与 `viewPort` 建立坐标映射，也可将 PixelMap 通过 `mesh` 网格变形绘制；子图形既可位于 Shape 内，也可独立创建。本特性覆盖容器、尺寸、viewport、mesh、非法值、资源与子属性继承边界。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Shape 容器 | 创建、子组件、尺寸与绘制目标 |
| ADDED | viewport | 坐标系、Resource、reset 和退化范围 |
| ADDED | mesh | PixelMap 网格、数组长度、非有限值和清除 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/01-shape/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/shape.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/shape.static.d.ets` | 已核对 |
| Model | `frameworks/core/components_ng/pattern/shape/shape_model_ng.cpp` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/shape/shape_container_pattern.cpp` | 已核对 |

## 用户故事

### US-1: 建立 Shape 绘制容器

**作为** 应用开发者  
**我想要** 在 Shape 中组合图形并使用独立坐标系  
**以便** 构建类似 SVG 的矢量场景

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 创建 Shape 且包含受支持子节点 THEN 容器创建 ShapeContainerPattern 并按节点顺序绘制子内容 | 正常 |
| AC-1.2 | WHEN Shape 未设置显式尺寸 THEN 按父约束、子项及既有 Shape 布局规则确定画布尺寸 | 正常 |
| AC-1.3 | WHEN viewPort 的 x/y/width/height 均合法且宽高大于 0 THEN 将 viewport 坐标映射到 Shape 实际绘制区域 | 正常 |
| AC-1.4 | WHEN viewPort 缺失、reset、宽高为 0/负数/非有限值或资源解析失败 THEN 按既有默认坐标路径绘制，不执行非法比例变换 | 异常 |

### US-2: 通过 Mesh 变形 PixelMap

**作为** 图形应用开发者  
**我想要** 使用网格顶点变形位图  
**以便** 实现非线性图像效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN mesh 数组长度满足 (row+1)*(column+1)*2 且 row/column 为有效非负整数 THEN ShapeContainerModifier 接收线性网格并绘制 PixelMap | 正常 |
| AC-2.2 | WHEN mesh 数组为空 THEN row/column 按 0 处理并清除当前网格效果 | 边界 |
| AC-2.3 | WHEN Static mesh 的 row/column 缺失或不大于 0 THEN converter 将其归一为 0；WHEN 归一后的长度不匹配 THEN 写入 mesh 但将 row/column 置 0，不进入指定网格维度绘制 | 边界 |
| AC-2.4 | WHEN Dynamic mesh 的 row/column 可解析为负整数 THEN 当前 Bridge/Model 不校验非负性；`mesh=[]、column=-1、row=1` 可满足长度等式并把负维度传入 painter，属于安全风险而非“已拒绝”行为 | 异常 |
| AC-2.5 | WHEN PixelMap 或节点在绘制前失效 THEN PaintMethod 安全跳过网格绘制，不影响其他合法 Shape 子节点 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Shape container/layout UT | `frameworks/core/components_ng/pattern/shape/shape_model_ng.cpp:55-124`; `frameworks/core/components_ng/pattern/shape/shape_container_pattern.cpp:42-59` |
| AC-2.1~AC-2.5 | R-5~R-9 | 已有实现 | 源码审查；负维度 UT/Fuzz 待补 | `interface/sdk-js/api/@internal/component/ets/shape.d.ts:430-448`; `frameworks/core/components_ng/pattern/shape/bridge/arkts_native_shape_bridge.cpp:135-166`; `frameworks/core/components_ng/pattern/shape/bridge/shape_static_modifier.cpp:192-206`; `frameworks/core/components_ng/pattern/shape/shape_container_modifier.cpp:23-38,62-78` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Shape 含合法子节点 | 创建容器并按树序绘制 | 子节点类型按 SDK/实现 | AC-1.1 |
| R-2 | 行为 | 无显式尺寸 | 使用父约束/子项确定尺寸 | 不生成负尺寸 | AC-1.2 |
| R-3 | 行为 | viewport 宽高>0 | 建立坐标映射 | x/y 可为合法 Length | AC-1.3 |
| R-4 | 异常 | viewport 退化/解析失败 | 使用默认坐标路径 | 不除以 0 | AC-1.4 |
| R-5 | 行为 | mesh 长度与网格一致 | 写线性顶点并绘制 PixelMap | 固定二维顶点格式 | AC-2.1 |
| R-6 | 边界 | mesh=[] | 正常 reset 路径按 0/0 清除 | 与 SDK reset 语义一致 | AC-2.2 |
| R-7 | 边界 | Static 缺失/非正维度或长度不匹配 | 维度归一为 0；不匹配时以 0/0 写入 | Static 路径具备维度保护 | AC-2.3 |
| R-8 | 异常 | Dynamic 负维度 | 负值原样进入 Model；特定空数组组合可通过长度等式 | 当前缺少安全兜底，不得声称拒绝或无越界风险 | AC-2.4 |
| R-9 | 恢复 | PixelMap/节点失效 | 跳过当前 mesh | 其他子节点继续 | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.2 | ShapeContainer Pattern/Layout UT | 容器和尺寸 |
| VM-2 | AC-1.3~AC-1.4 | viewport 参数矩阵 | 坐标映射和退化值 |
| VM-3 | AC-2.1~AC-2.5 | 源码审查+待补 Dynamic/Static mesh UT/Fuzz | 正常长度、Static 归一、Dynamic 负维度危险组合和失效对象；现有 invalid CAPI 用例为 DISABLED |

## API 变更分析

### 新增 API

N/A，Shape 自 API 7、mesh 自 API 8 为已有能力。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**Shape / viewPort / mesh**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Shape(value?: PixelMap): ShapeAttribute`; `viewPort(value: ViewportRect)`; `mesh(value, column, row)` |
| 返回值 | ShapeAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | PixelMap | 否 | 无 | mesh 绘制目标 |
| viewPort | ViewportRect | 否 | Shape 实际坐标 | width/height 应大于 0 |
| mesh value | Array<any> | 是 | [] | 长度=(row+1)*(column+1)*2 |
| column/row | number | 是 | 0 | SDK 契约为非负整数；Static 将非正值归零，当前 Dynamic 对可解析负整数缺少校验 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 viewport | 映射子图形坐标 | AC-1.3 |
| 2 | 合法 mesh+PixelMap | 网格变形绘制 | AC-2.1 |
| 3 | Dynamic mesh=[]、column=-1、row=1 | 当前长度检查通过并把负维度送入 painter，作为安全缺口验证 | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 是；Shape API 7、mesh API 8、Resource/构造参数更新及 Static/Builder 按后续版本演进；Dynamic 负维度未按 SDK 非负契约防护，作为已知实现偏差保留。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** API 7/8/20/23/26 全量记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 容器 Pattern | viewport/mesh 由 Shape 容器处理，不下放给单个图形 Pattern | AC-1.3, AC-2.1 |
| 绘制目标 | mesh 需要有效 PixelMap | AC-2.5 |
| 子图形边界 | Line 未出现在 SDK Shape 子组件清单，支持性在风险中单列 | AC-1.1 |
| 输入安全 | Static 归一非正维度；Dynamic 负维度当前可能进入 painter | AC-2.3, AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 网格绘制复杂度随顶点数增长 | 性能测试 | `frameworks/core/components_ng/pattern/shape/shape_container_paint_method.cpp:26-43` |
| 功耗 | 仅绘制阶段执行，无后台任务 | 审查 | VM-3 |
| 内存 | mesh 数组和 PixelMap 生命周期随节点 | 内存测试 | VM-3 |
| 安全 | Dynamic 必须补负维度+长度等式 Fuzz；当前仅靠长度等式不能保证安全 | 源码审查/待补 Fuzz | AC-2.4 |
| 可靠性 | 退化 viewport 和失效 PixelMap 安全回退 | 边界 UT | VM-2, VM-3 |
| 可测试性 | 坐标和网格结果可像素/几何断言 | UT/截图 | VM-1~VM-3 |
| 自动化维测 | viewport/mesh 属性可 Dump | Inspector | AC-1.3 |
| 定界定位 | SDK→Model→Pattern→Modifier 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 较小画布 | viewport 等比映射 | 截图测试 | AC-1.3 |
| 平板 | 大画布/高网格密度 | 顶点长度规则不变 | 性能矩阵 | AC-2.1 |
| 折叠屏 | 画布尺寸变化 | 重新映射 viewport | 折叠态测试 | AC-1.3 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 容器不自动增加图形语义 | AC-1.1 |
| 大字体 | 否 | 几何绘制不依赖字体 | VM-1 |
| 深色模式 | 是 | 颜色由样式 Feat 处理 | AC-1.1 |
| 多窗口/分屏 | 是 | 尺寸变化重映射 | AC-1.3 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | API 8 mesh 和新范式需回归 | AC-2.1 |
| 生态兼容 | 是 | 非法 mesh 行为保持 | AC-2.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Shape mesh
  Scenario: Dynamic 负维度危险组合
    Given Shape 持有有效 PixelMap
    When Dynamic mesh 传入空数组、column -1 和 row 1
    Then 当前长度等式通过并把负维度传入 painter，测试必须暴露该安全风险
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] viewport、Static mesh 归一与 Dynamic 负维度安全偏差完整
- [x] Line 子组件清单差异显式记录
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Shape container viewport mesh PixelMap"
  - repo: "openharmony/interface_sdk-js"
    query: "Shape viewPort mesh API 7 8"
```

**关键文档：** `05-ui-components/14-drawing-components/01-shape/design.md`
