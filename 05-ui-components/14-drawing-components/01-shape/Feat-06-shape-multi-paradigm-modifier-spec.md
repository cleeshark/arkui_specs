# 特性规格

> Func-05-14-01-Feat-06 Shape 多范式与 Modifier 存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Shape 多范式与 Modifier |
| 特性编号 | Func-05-14-01-Feat-06 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

本特性覆盖 Shape、Rect、Circle、Ellipse、Line、Polyline、Polygon、Path 的 Dynamic/Static 入口、AttributeModifier、构造参数动态更新、Builder/setOptions、CJ/内部桥接及 API 7/8/18/20/23/26 版本演进。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 多组件入口矩阵 | 八类声明式绘制组件 |
| ADDED | 多范式与版本 | Dynamic、Static、Modifier、Builder、options |
| ADDED | 通道差异 | Modifier 文件不对称、类型演进和 reset |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/01-shape/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/shape.d.ts` 等八份组件声明 | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/shape.static.d.ets` 等 | 已核对 |
| Modifier SDK | `interface/sdk-js/api/arkui/ShapeModifier.d.ts` 等 | 已核对 |
| Build | `frameworks/core/components_ng/pattern/shape/BUILD.gn` | 已核对 |

## 用户故事

### US-1: 按范式创建绘制组件

**作为** 应用开发者  
**我想要** 在支持版本使用 Dynamic 或 Static 绘制组件  
**以便** 创建相同几何能力

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN API 7+ 使用 Dynamic Shape/Rect/Circle/Ellipse/Line/Polyline/Polygon/Path THEN 创建对应 Model/Pattern | 正常 |
| AC-1.2 | WHEN API 8+ 使用 Shape.mesh THEN 仅 Shape 容器开放网格能力 | 边界 |
| AC-1.3 | WHEN API 18+ 使用标准化 Options 或 API 20 Length/构造参数更新 THEN 按对应组件 SDK 类型更新当前节点 | 正常 |
| AC-1.4 | WHEN API 23+ 使用 Static 组件入口 THEN 调用对应 static modifier/model 并返回属性接口 | 正常 |

### US-2: 使用 Modifier 与 Builder

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN组件存在 Dynamic/Static AttributeModifier THEN applyNormalAttribute/attributeModifier 只应用该组件声明属性 | 正常 |
| AC-2.2 | WHEN Circle/Ellipse 缺少与其他图形同名独立 Dynamic Modifier 文件但 Static attributeModifier 存在 THEN 按实际 SDK/bridge 通道记录，不虚构文件或能力 | 边界 |
| AC-2.3 | WHEN API 26 使用 Builder 与 set*Options THEN 先设置 options/style，再构建声明内容或完成无内容图形构造 | 正常 |
| AC-2.4 | WHEN undefined/null/reset 通过不同范式传入 THEN 使用各自 bridge 的 reset/default 路径，不静默统一签名差异 | 边界 |

### US-3: 保持构建和实现边界

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN构建 Shape 模块 THEN BUILD 同时包含八类图形的 Model/Pattern/Paint 与 dynamic/static bridge | 正常 |
| AC-3.2 | WHEN内部 Native node modifier 存在 THEN 只作为组件实现通道记录，不自动创建 08-NDK 规格或声明未公开 C API | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | SDK/Model/Static UT | `frameworks/core/components_ng/pattern/shape/BUILD.gn:22-175`; `interface/sdk-js/api/arkui/component/shape.static.d.ets:20-265` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Modifier/Builder/reset UT | `interface/sdk-js/api/arkui/ShapeModifier.d.ts:20-58`; `frameworks/core/components_ng/pattern/shape/bridge/common_shape_static_modifier.cpp:20-180` |
| AC-3.1~AC-3.2 | R-9~R-10 | 已有实现 | Build/API review | `frameworks/core/components_ng/pattern/shape/BUILD.gn:22-175` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Dynamic API>=7 | 创建对应图形节点 | 八类独立 Model | AC-1.1 |
| R-2 | 边界 | Shape mesh API>=8 | 仅容器开放 | 子图形不外推 | AC-1.2 |
| R-3 | 行为 | Options/Length/Updater 版本满足 | 按 SDK 类型更新 | API 18/20 | AC-1.3 |
| R-4 | 行为 | Static API>=23 | 调用 static 通道 | staticonly | AC-1.4 |
| R-5 | 行为 | Modifier 存在 | 只应用声明属性 | 组件边界明确 | AC-2.1 |
| R-6 | 边界 | Modifier 文件不对称 | 按实际通道记录 | 不虚构 | AC-2.2 |
| R-7 | 行为 | Builder API>=26 | options/style 先于构造 | 顺序保持 | AC-2.3 |
| R-8 | 恢复 | undefined/null/reset | 当前 bridge 默认恢复 | 范式签名不混用 | AC-2.4 |
| R-9 | 行为 | Shape BUILD | 包含 Model/Pattern/Paint/bridge | dynamic/static 同建 | AC-3.1 |
| R-10 | 边界 | 内部 native modifier | 仅实现通道 | 非公开 C API | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | 八组件构造/version UT | API 7/8/18/20/23 |
| VM-2 | AC-2.1~AC-2.4 | Modifier/Builder/reset UT | 通道不对称和 API 26 |
| VM-3 | AC-3.1~AC-3.2 | BUILD/API review | 构建完整性与公开边界 |

## API 变更分析

### 新增 API

N/A，本次仅补录已有多范式接口。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**Shape 类组件多范式入口**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic `Component(options?)`; Static `Component(...)`; API 26 Builder/setOptions |
| 返回值 | 对应 Attribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | 各组件 Options | 否 | 组件默认 | 以 canonical SDK 为准 |
| style | CustomBuilderT | Builder 重载是 | 无 | API 26 staticonly |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | API 7 Dynamic | 创建对应节点 | AC-1.1 |
| 2 | API 23/26 Static/Builder | 走 static modifier/options | AC-1.4, AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 7 基础、8 mesh、18 Options、20 类型/更新、23 Static、26 Builder。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** API 7/8/18/20/23/26 全量记录，逐组件以 SDK 为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 逐组件契约 | 不从相邻图形推断 overload/modifier | AC-2.2 |
| 共享模块 | 物理 BUILD 共用不等于合并 Pattern | AC-3.1 |
| NDK 边界 | 内部 modifier 不等于公开 08-NDK | AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 多范式最终复用对应 NG Model | Trace | VM-1 |
| 功耗 | 无后台任务 | 审查 | VM-1 |
| 内存 | Modifier/Builder 随节点释放 | 生命周期 UT | VM-2 |
| 安全 | 无权限和敏感数据 | API 审查 | VM-3 |
| 可靠性 | reset 和版本不支持场景安全 | 边界 UT | VM-2 |
| 可测试性 | 各组件/入口可参数化构造 | UT | VM-1~VM-3 |
| 自动化维测 | bridge/module 日志可区分入口 | Trace | AC-2.4 |
| 定界定位 | SDK→bridge→Model/Pattern 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无接口差异 | 按设备 API 范式 | 构建测试 | VM-1 |
| 平板 | 无接口差异 | 同一 NG Model | 构建测试 | VM-1 |
| 折叠屏 | 几何重布局 | 入口不变 | 集成测试 | AC-1.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 范式不改变语义 | VM-1 |
| 大字体 | 否 | 图形接口无文本 | VM-1 |
| 深色模式 | 是 | Resource 由样式 Feat 处理 | AC-1.3 |
| 多窗口/分屏 | 是 | 创建后可重布局 | AC-1.4 |
| 多用户 | 否 | 无用户状态 | VM-1 |
| 版本升级 | 是 | 本 Feat 核心 | AC-1.1~AC-2.3 |
| 生态兼容 | 是 | 不虚构 modifier/C API | AC-2.2, AC-3.2 |

## 行为场景（可选，Gherkin）

本 Feat 为标准复杂度，接口规格行为场景已覆盖。

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 八组件、六版本、Modifier/Builder 和 NDK 边界明确
- [x] AC、规则、VM 一致
- [x] 未静默统一通道差异

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Shape components dynamic static modifier builder BUILD"
  - repo: "openharmony/interface_sdk-js"
    query: "Shape Rect Circle Ellipse Line Polygon Polyline Path static"
```

**关键文档：** `05-ui-components/14-drawing-components/01-shape/design.md`
