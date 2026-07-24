# 特性规格

> Func-05-14-01-Feat-03 Shape 基础闭合图形存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Shape 基础闭合图形 |
| 特性编号 | Func-05-14-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

本特性覆盖 Rect、Circle、Ellipse 的创建、宽高测量、默认几何、Rect radius/radiusWidth/radiusHeight/逐角半径、Resource/Length/ColorMetrics 及非法值边界。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Rect 几何 | width/height、统一/椭圆/逐角圆角 |
| ADDED | Circle/Ellipse 几何 | 尺寸、边界盒与闭合绘制 |
| ADDED | 全形式与版本 | Resource、Length、ColorMetrics、Static/Builder |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/01-shape/design.md` | 并行补录 |
| Rect SDK | `interface/sdk-js/api/@internal/component/ets/rect.d.ts` | 已核对 |
| Circle SDK | `interface/sdk-js/api/@internal/component/ets/circle.d.ts` | 已核对 |
| Ellipse SDK | `interface/sdk-js/api/@internal/component/ets/ellipse.d.ts` | 已核对 |
| Rect Model | `frameworks/core/components_ng/pattern/shape/rect_model_ng.cpp` | 已核对 |

## 用户故事

### US-1: 创建闭合基础图形

**作为** 应用开发者  
**我想要** 使用尺寸创建矩形、圆和椭圆  
**以便** 绘制常见闭合形状

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Rect/Circle/Ellipse 传入合法 width/height THEN 按边界盒测量并绘制闭合图形 | 正常 |
| AC-1.2 | WHEN Circle 宽高不相等 THEN 按当前 Circle Pattern/Painter 的边界盒规则绘制，不把 SDK Circle 静默改写为 Ellipse 接口 | 边界 |
| AC-1.3 | WHEN尺寸缺失或为 Resource/Length THEN 使用各组件默认/解析结果并在资源变化后重测 | 正常 |
| AC-1.4 | WHEN宽高为负、NaN、Infinity 或资源失败 THEN 按 parser/model 默认或 0 尺寸路径处理，不提交非有限几何 | 异常 |

### US-2: 配置 Rect 圆角

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN radiusWidth/radiusHeight 合法 THEN 所有角使用对应椭圆半径 | 正常 |
| AC-2.2 | WHEN radius 为单个 Length THEN 所有角使用相同圆角；WHEN 为数组/逐角形式 THEN 对应角独立保存 | 正常 |
| AC-2.3 | WHEN圆角超过几何可容纳范围 THEN Painter 按底层圆角矩形约束得到可绘制结果 | 边界 |
| AC-2.4 | WHEN圆角为负、非有限、数组长度/元素非法或 reset THEN 非法部分回退默认 0，不越界读取 | 异常 |

### US-3: 使用版本化颜色和构造参数

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Circle API 26 使用 ColorMetrics fill/stroke THEN 按 SDK overload 解析颜色；其他组件不自动获得未声明 overload | 边界 |
| AC-3.2 | WHEN API 20+ 动态更新构造参数或 API 26 Builder/setOptions THEN 更新当前图形几何并标记对应 Measure/Paint | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Rect/Circle/Ellipse Pattern UT | `frameworks/core/components_ng/pattern/shape/rect_model_ng.cpp:25-103`; `frameworks/core/components_ng/pattern/shape/circle_model_ng.cpp:20-40`; `frameworks/core/components_ng/pattern/shape/ellipse_model_ng.cpp:20-36` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Rect radius UT | `frameworks/core/components_ng/pattern/shape/rect_model_ng.cpp:106-181,255-365` |
| AC-3.1~AC-3.2 | R-9~R-10 | 已有实现 | SDK/Modifier version UT | `interface/sdk-js/api/@internal/component/ets/circle.d.ts:118-151`; `interface/sdk-js/api/arkui/component/rect.static.d.ets:23-211` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 合法 width/height | 按边界盒绘制闭合图形 | 各 Pattern 独立 | AC-1.1 |
| R-2 | 边界 | Circle 宽高不等 | 保持 Circle 实现语义 | 不改接口类型 | AC-1.2 |
| R-3 | 行为 | 缺失/Resource/Length | 使用默认或解析值 | 资源可刷新 | AC-1.3 |
| R-4 | 异常 | 负/非有限/资源失败 | 默认或 0 尺寸 | 不提交非法几何 | AC-1.4 |
| R-5 | 行为 | radiusWidth/Height 合法 | 写全部角椭圆半径 | 非负 | AC-2.1 |
| R-6 | 行为 | radius 标量/数组 | 广播或逐角保存 | 数组格式按 SDK | AC-2.2 |
| R-7 | 边界 | 半径超过尺寸 | 由 RRect 约束为可绘制值 | 不扩大边界盒 | AC-2.3 |
| R-8 | 异常 | 半径非法/reset | 非法部分恢复 0 | 不越界访问 | AC-2.4 |
| R-9 | 边界 | Circle ColorMetrics API 26 | 仅 Circle 声明 overload | 不外推其他组件 | AC-3.1 |
| R-10 | 行为 | 参数更新/Builder | 更新几何并标脏 | 按版本开放 | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | 三组件尺寸矩阵 UT | 缺失、Resource、非法值 |
| VM-2 | AC-2.1~AC-2.4 | Rect radius UT/截图 | 广播、逐角、超限、reset |
| VM-3 | AC-3.1~AC-3.2 | API 20/26 SDK/Modifier UT | overload 与参数更新 |

## API 变更分析

### 新增 API

N/A，均为已有图形 API。

### 变更/废弃 API

N/A；ColorMetrics 与 Builder 为既有版本演进。

## 接口规格

### 接口定义

**Rect / Circle / Ellipse**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Rect(options?)`; `Circle(options?)`; `Ellipse(options?)`; `radiusWidth/radiusHeight/radius` |
| 返回值 | 对应 Attribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| width/height | Length/Resource | 否 | 组件默认 | 非负有限长度 |
| radiusWidth/Height | Length | 否 | 0 | 非负 |
| radius | Length/Array<any> | 否 | 0 | 标量广播或合法逐角数组 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法尺寸 | 绘制闭合图形 | AC-1.1 |
| 2 | Rect 逐角半径 | 各角按对应值绘制 | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 是；Options API 18、Length 演进 API 20、Static 23、Circle ColorMetrics/Builder 26。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** API 7/18/20/23/26 全量记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 独立 Pattern | 三种图形具有独立 Model/Pattern/Painter | AC-1.1 |
| 共享样式 | 绘制样式由 Feat-02 统一定义 | AC-1.1 |
| SDK overload | 只记录各文件明确声明的类型 | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每图形固定几何计算 | Trace | VM-1 |
| 功耗 | 仅布局/绘制阶段 | 审查 | VM-1 |
| 内存 | 固定尺寸/圆角属性 | 内存审查 | VM-2 |
| 安全 | 非法数组不越界 | Fuzz | AC-2.4 |
| 可靠性 | 非有限值和资源失败安全回退 | 边界 UT | VM-1, VM-2 |
| 可测试性 | 几何与像素可断言 | UT/截图 | VM-1~VM-3 |
| 自动化维测 | 属性可 Inspector | Inspector | AC-2.2 |
| 定界定位 | SDK/Model/Pattern/Painter 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 小尺寸圆角常见 | 半径约束不变 | 截图测试 | AC-2.3 |
| 平板 | 大尺寸图形 | 边界盒规则不变 | 尺寸矩阵 | AC-1.1 |
| 折叠屏 | 尺寸/density 变化 | Resource 重载重测 | 折叠态测试 | AC-1.3 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 图形默认不提供额外语义 | AC-1.1 |
| 大字体 | 否 | 不涉及文本 | VM-1 |
| 深色模式 | 是 | 颜色由 Feat-02 管理 | AC-3.1 |
| 多窗口/分屏 | 是 | 重测尺寸 | AC-1.3 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | Options/Static/Builder 需回归 | AC-3.2 |
| 生态兼容 | 是 | 不外推 ColorMetrics | AC-3.1 |

## 行为场景（可选，Gherkin）

本 Feat 为标准复杂度，接口规格行为场景已覆盖。

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 尺寸、Resource、圆角、ColorMetrics 和版本边界明确
- [x] AC、规则、VM 一致
- [x] 未外推未声明 API

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Rect Circle Ellipse radius Shape Pattern"
  - repo: "openharmony/interface_sdk-js"
    query: "Rect Circle Ellipse Options radius ColorMetrics"
```

**关键文档：** `05-ui-components/14-drawing-components/01-shape/design.md`
