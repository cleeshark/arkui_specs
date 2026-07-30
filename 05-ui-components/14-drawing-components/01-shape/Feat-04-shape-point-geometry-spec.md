# 特性规格

> Func-05-14-01-Feat-04 Shape 点集图形存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Shape 点集图形 |
| 特性编号 | Func-05-14-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

本特性覆盖 Line 的 startPoint/endPoint，以及 Polyline/Polygon 的 points 数组解析、坐标测量、轮廓开闭与 fill 行为、Resource/Length、空数组、奇数/非法元素和版本化入口。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Line 几何 | 起点、终点、边界盒和绘制 |
| ADDED | Polyline/Polygon 点集 | 开放/闭合、测量与非法数组 |
| ADDED | 支持边界 | Shape 子组件清单未列 Line 的存量差异 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/01-shape/design.md` | 并行补录 |
| Line SDK | `interface/sdk-js/api/@internal/component/ets/line.d.ts` | 已核对 |
| Polyline SDK | `interface/sdk-js/api/@internal/component/ets/polyline.d.ts` | 已核对 |
| Polygon SDK | `interface/sdk-js/api/@internal/component/ets/polygon.d.ts` | 已核对 |
| Line Model | `frameworks/core/components_ng/pattern/shape/line_model_ng.cpp` | 已核对 |
| Polygon Model | `frameworks/core/components_ng/pattern/shape/polygon_model_ng.cpp` | 已核对 |

## 用户故事

### US-1: 绘制线段

**作为** 应用开发者  
**我想要** 使用两个端点绘制 Line  
**以便** 表达独立直线几何

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN startPoint/endPoint 均为两个合法坐标 THEN Line 按两点建立边界盒并绘制线段 | 正常 |
| AC-1.2 | WHEN端点坐标使用 Length/Resource THEN 按当前 density/资源解析并在变化后重测 | 正常 |
| AC-1.3 | WHEN端点缺失、数组长度不足、元素非数值/非有限或 Resource 失败 THEN 该端点按默认/拒绝路径处理，不越界读取 | 异常 |
| AC-1.4 | WHEN Line 作为独立组件使用 THEN 按自身 Pattern 绘制；WHEN 作为 Shape 子项的支持性不由 SDK 清单明确 THEN 作为兼容风险验证，不直接承诺 | 边界 |

### US-2: 绘制折线与多边形

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Polyline points 含至少两个合法点 THEN stroke/轮廓按顺序连接且不显式闭合末点到首点；WHEN fill 生效 THEN painter 仍挂载 Brush 并对开放 Path 执行填充，光栅填充可形成隐式闭合区域 | 正常 |
| AC-2.2 | WHEN Polygon points 含足够合法点 THEN 按顺序连接并闭合末点到首点，fill 作用于闭合区域 | 正常 |
| AC-2.3 | WHEN points 为空、点数不足、嵌套格式/坐标非法 THEN 不绘制非法几何并保持节点安全 | 异常 |
| AC-2.4 | WHEN points 更新、Resource 或构造参数变化 THEN 重算边界盒并标记 Measure/Paint | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Line Model/Layout/Paint UT | `frameworks/core/components_ng/pattern/shape/line_model_ng.cpp:20-150`; `frameworks/core/components_ng/pattern/shape/line_layout_algorithm.cpp:20-95` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | 源码审查；Polyline fill 像素 UT 待补 | `frameworks/core/components_ng/pattern/shape/polygon_model_ng.cpp:20-101`; `frameworks/core/components_ng/pattern/shape/polygon_painter.cpp:21-45`; `frameworks/core/components_ng/pattern/shape/shape_painter.cpp:93-109` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 两端点合法 | 建立边界并绘制线段 | 每点两个坐标 | AC-1.1 |
| R-2 | 行为 | Length/Resource 坐标 | 解析并可刷新 | density 有效 | AC-1.2 |
| R-3 | 异常 | 缺失/短数组/非法元素 | 默认或拒绝 | 不越界读取 | AC-1.3 |
| R-4 | 边界 | Line 独立/Shape 子项 | 独立有契约；容器支持列为风险 | 不推断清单外能力 | AC-1.4 |
| R-5 | 行为 | Polyline 至少两点 | stroke/轮廓不显式闭合；fill Brush 仍对开放 Path 绘制 | 不承诺 fill“不形成闭合面” | AC-2.1 |
| R-6 | 行为 | Polygon 足够点 | 顺序连接并闭合 | fill 作用闭合区域 | AC-2.2 |
| R-7 | 异常 | points 空/不足/非法 | 不绘制非法几何 | 节点仍安全 | AC-2.3 |
| R-8 | 行为 | points/资源/参数更新 | 重算边界并标脏 | 使用最新点集 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | Line 参数/Resource UT | 两点、非法数组、刷新 |
| VM-2 | AC-1.4 | 独立/容器集成测试 | SDK 清单差异 |
| VM-3 | AC-2.1~AC-2.4 | Polygon UT+待补 Polyline fill 像素测试 | stroke 轮廓开闭、Polyline fill 隐式闭合效果和更新；现有 false-path 覆盖不足 |

## API 变更分析

### 新增 API

N/A，Line/Polyline/Polygon 为已有 API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**Line / Polyline / Polygon 点集接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `startPoint(Array<any>)`; `endPoint(Array<any>)`; `points(Array<any>)` |
| 返回值 | 对应 Attribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| start/end | Array<any> | 是 | 默认点 | 正好表达 x/y 两坐标 |
| points | Array<any> | 是 | [] | 每点含两个合法坐标 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Polyline 相同点集 | stroke 轮廓开放；设置 fill 时仍绘制填充区域 | AC-2.1 |
| 2 | Polygon 相同点集 | 闭合图形 | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 是；Options/Length/Static/Builder 按 API 18/20/23/26 演进。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** API 7/18/20/23/26 全量记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| Model 分离 | Line 与 Polygon/Polyline 使用不同 Model/Pattern | AC-1.1, AC-2.1 |
| 开闭语义 | Polyline 轮廓不显式闭合但仍可 fill；Polygon 轮廓闭合 | AC-2.1, AC-2.2 |
| SDK 清单 | Line 的 Shape 子项支持性不得凭源码存在静默推断 | AC-1.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 点集测量/绘制随点数线性增长 | 性能 UT | VM-3 |
| 功耗 | 无后台任务 | 审查 | VM-1 |
| 内存 | 点集数组随节点生命周期 | 内存 UT | VM-3 |
| 安全 | 非法嵌套数组不越界 | Fuzz | AC-1.3, AC-2.3 |
| 可靠性 | 空/不足点集安全无绘制 | 边界 UT | VM-1, VM-3 |
| 可测试性 | 边界盒和像素结果可断言 | UT/截图 | VM-1~VM-3 |
| 自动化维测 | points 可 Inspector/Dump | Inspector | AC-2.4 |
| 定界定位 | SDK/Model/Layout/Paint 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 小尺寸坐标精度敏感 | density 转换一致 | 像素测试 | AC-1.2 |
| 平板 | 大点集常见 | 线性复杂度 | 性能测试 | AC-2.4 |
| 折叠屏 | 尺寸/density 变化 | Resource 重载重测 | 折叠态测试 | AC-2.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 图形不自动产生文本语义 | AC-2.2 |
| 大字体 | 否 | 不涉及文本 | VM-1 |
| 深色模式 | 是 | 样式由 Feat-02 处理 | AC-2.2 |
| 多窗口/分屏 | 是 | 坐标重测 | AC-2.4 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | Static/Builder 和清单风险需回归 | AC-1.4 |
| 生态兼容 | 是 | 轮廓开闭与 fill 行为分别保持 | AC-2.1, AC-2.2 |

## 行为场景（可选，Gherkin）

本 Feat 为标准复杂度，接口规格行为场景已覆盖。

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 坐标、Resource、数组、轮廓开闭、Polyline fill 和清单偏差明确
- [x] AC、规则、VM 一致
- [x] 未推断 Line 容器支持

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Line Polyline Polygon points Shape Pattern"
  - repo: "openharmony/interface_sdk-js"
    query: "Line startPoint Polygon Polyline points"
```

**关键文档：** `05-ui-components/14-drawing-components/01-shape/design.md`
