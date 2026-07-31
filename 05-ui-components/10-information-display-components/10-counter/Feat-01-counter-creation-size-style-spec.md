# 特性规格

## 概述

| Field | Content |
|-------|---------|
| 特性名称 | Counter 创建、尺寸与基础样式 |
| 特性编号 | Func-05-10-10-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Counter 组件核心属性规格 | height, width, backgroundColor |
| ADDED | 三节点结构规格 | SUB_BUTTON, CONTENT, ADD_BUTTON |
| ADDED | 布局算法规格 | Measure/Layout 流程，RTL/LTR 处理 |

## 输入文档

- 设计文档: `specs/05-ui-components/10-information-display-components/10-counter/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/counter/`

## 用户故事

### US-1: 创建基础计数器组件

**作为** 应用开发者  
**我想要** 创建一个 Counter 组件  
**以便** 提供数量选择功能

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 Counter() 创建组件 THEN 创建包含三子节点的 Counter FrameNode | 正常 |
| AC-1.2 | WHEN 创建完成 THEN 子节点顺序为 SUB_BUTTON(0) → CONTENT(1) → ADD_BUTTON(2) | 正常 |
| AC-1.3 | WHEN 未设置尺寸 THEN 使用主题默认值（height=32vp, width=100vp） | 正常 |

### US-2: 设置高度

**作为** 应用开发者  
**我想要** 自定义 Counter 组件的高度  
**以便** 适配不同的 UI 布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 height 为有效正值 THEN Counter 容器和所有子节点高度同步更新 | 正常 |
| AC-2.2 | WHEN 高度更新 THEN 减号按钮、内容区域、加号按钮及其文本子节点高度一致 | 正常 |
| AC-2.3 | WHEN 未设置 height THEN 使用主题默认值 32vp | 正常 |

### US-3: 设置宽度

**作为** 应用开发者  
**我想要** 自定义 Counter 组件的宽度  
**以便** 控制组件的整体尺寸

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 width 为有效正值 THEN 仅 Counter 容器宽度更新 | 正常 |
| AC-3.2 | WHEN 宽度设置后 THEN 按钮宽度由主题 controlWidth(32vp) 控制 | 正常 |
| AC-3.3 | WHEN 宽度设置后 THEN 内容区域使用 LayoutWeight 填充剩余空间 | 正常 |
| AC-3.4 | WHEN 未设置 width THEN 使用主题默认值 100vp | 正常 |

### US-4: 设置背景色

**作为** 应用开发者  
**我想要** 自定义 Counter 组件的背景色  
**以便** 匹配应用的整体视觉风格

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 设置 backgroundColor 为有效颜色 THEN Counter 容器背景更新 | 正常 |
| AC-4.2 | WHEN 背景色存储 THEN 存储在 RenderContext 而非 LayoutProperty | 正常 |
| AC-4.3 | WHEN 未设置 backgroundColor THEN 使用默认透明背景 | 边界 |

### US-5: RTL/LTR 自动适配

**作为** 应用开发者  
**我想要** Counter 组件自动适配文本方向  
**以便** 支持国际化布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 文本方向为 LTR THEN 布局顺序为：减号按钮(左) → 内容区域 → 加号按钮(右) | 正常 |
| AC-5.2 | WHEN 文本方向为 RTL THEN 布局顺序为：加号按钮(左) → 内容区域 → 减号按钮(右) | 正常 |
| AC-5.3 | WHEN 边框圆角应用 THEN LTR 模式下减号按钮左侧圆角、加号按钮右侧圆角 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-1 | 单元测试 | counter_pattern_test |
| AC-1.2 | R-2 | TASK-1 | 结构验证 | 三节点索引检查 |
| AC-1.3 | R-3 | TASK-1 | 默认值测试 | 主题获取验证 |
| AC-2.1 | R-4 | TASK-1 | 属性测试 | SetHeight 测试 |
| AC-2.2 | R-5 | TASK-1 | 传播测试 | 子节点高度验证 |
| AC-2.3 | R-6 | TASK-1 | 默认值测试 | 主题 height 默认值 |
| AC-3.1 | R-7 | TASK-1 | 属性测试 | SetWidth 测试 |
| AC-3.2 | R-8 | TASK-1 | 布局测试 | 按钮宽度验证 |
| AC-3.3 | R-9 | TASK-1 | 布局测试 | LayoutWeight 验证 |
| AC-3.4 | R-10 | TASK-1 | 默认值测试 | 主题 width 默认值 |
| AC-4.1 | R-11 | TASK-1 | 属性测试 | SetBackgroundColor 测试 |
| AC-4.2 | R-12 | TASK-1 | 存储验证 | RenderContext 检查 |
| AC-4.3 | R-13 | TASK-1 | 边界测试 | 未设置背景色验证 |
| AC-5.1 | R-14 | TASK-1 | 布局测试 | LTR 布局验证 |
| AC-5.2 | R-15 | TASK-1 | 布局测试 | RTL 布局验证 |
| AC-5.3 | R-16 | TASK-1 | 样式测试 | 边框圆角验证 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 Counter() | 创建 Counter FrameNode，初始化三子节点 | 无 | AC-1.1 |
| R-2 | 行为 | 创建子节点 | 按 SUB_BUTTON(0) → CONTENT(1) → ADD_BUTTON(2) 顺序创建 | 固定索引 | AC-1.2 |
| R-3 | 行为 | 未设置尺寸 | 使用主题默认值 height=32vp, width=100vp | 从 CounterTheme 获取 | AC-1.3 |
| R-4 | 行为 | 设置 height > 0 | 更新 Counter 容器和所有子节点高度 | 无 | AC-2.1 |
| R-5 | 行为 | 高度传播 | 减号按钮、内容区域、加号按钮及其文本子节点高度一致 | 5 个节点同步 | AC-2.2 |
| R-6 | 行为 | 未设置 height | 使用主题默认值 32vp | 无 | AC-2.3 |
| R-7 | 行为 | 设置 width > 0 | 仅更新 Counter 容器宽度，子节点不受影响 | 无 | AC-3.1 |
| R-8 | 行为 | 宽度设置后 | 按钮宽度由主题 controlWidth(32vp) 控制 | 无 | AC-3.2 |
| R-9 | 行为 | 宽度设置后 | 内容区域使用 LayoutWeight 填充剩余空间 | 自动计算 | AC-3.3 |
| R-10 | 行为 | 未设置 width | 使用主题默认值 100vp | 无 | AC-3.4 |
| R-11 | 行为 | 设置 backgroundColor 有效值 | 更新 Counter 容器背景色 | 无 | AC-4.1 |
| R-12 | 行为 | 背景色存储 | 存储在 RenderContext，非 LayoutProperty | 触发 RENDER | AC-4.2 |
| R-13 | 边界 | 未设置 backgroundColor | 使用默认透明背景 | 无 | AC-4.3 |
| R-14 | 行为 | TextDirection = LTR | 布局顺序：SUB_BUTTON → CONTENT → ADD_BUTTON | 无 | AC-5.1 |
| R-15 | 行为 | TextDirection = RTL | 布局顺序：ADD_BUTTON → CONTENT → SUB_BUTTON | 无 | AC-5.2 |
| R-16 | 行为 | LTR 边框圆角 | 减号按钮左侧圆角，加号按钮右侧圆角 | 圆角值从主题获取 | AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3（组件创建） | 单元测试 | 三节点结构验证 |
| VM-2 | AC-2.1~2.3（高度属性） | 属性测试 | 高度传播机制验证 |
| VM-3 | AC-3.1~3.4（宽度属性） | 布局测试 | 宽度计算和 LayoutWeight |
| VM-4 | AC-4.1~4.3（背景色） | 渲染测试 | RenderContext 存储验证 |
| VM-5 | AC-5.1~5.3（RTL/LTR） | 布局测试 | 文本方向适配验证 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。

### 变更/废弃 API

> 无变更或废弃 API。

## 接口规格

### 接口定义

**SetHeight()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `height(value: Length): Counter` |
| 返回值 | `Counter` — 组件本身，支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2, AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | Length | 否 | 主题默认值（32vp） | 无特殊验证 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value > 0 | 更新 Counter 容器和所有子节点高度 | AC-2.1, AC-2.2 |
| 2 | 未调用 | 使用主题默认值 32vp | AC-2.3 |

---

**SetWidth()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `width(value: Length): Counter` |
| 返回值 | `Counter` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.2, AC-3.3, AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | Length | 否 | 主题默认值（100vp） | 无特殊验证 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value > 0 | 仅更新 Counter 容器宽度 | AC-3.1 |
| 2 | 布局时 | 按钮宽度由 controlWidth 控制，内容区域自动填充 | AC-3.2, AC-3.3 |
| 3 | 未调用 | 使用主题默认值 100vp | AC-3.4 |

---

**SetBackgroundColor()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `backgroundColor(value: ResourceColor): Counter` |
| 返回值 | `Counter` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1, AC-4.2, AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor | 否 | 透明背景 | 支持颜色值、资源引用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置有效颜色 | 存储到 RenderContext，触发渲染更新 | AC-4.1, AC-4.2 |
| 2 | 未调用 | 使用默认透明背景 | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 三节点固定顺序 | SUB_BUTTON(0) → CONTENT(1) → ADD_BUTTON(2) | AC-1.2 |
| 高度传播机制 | 设置高度时同步更新 5 个节点 | AC-2.2 |
| 宽度仅更新容器 | 子节点使用 LayoutWeight 自动分配 | AC-3.3 |
| 背景色存储位置 | RenderContext 而非 LayoutProperty | AC-4.2 |
| RTL/LTR 自动切换 | 布局算法根据 TextDirection 调整 | AC-5.1, AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 高度设置遍历 5 个节点，无额外开销 | 代码审查 | SetHeight 实现 |
| 内存 | 三节点结构固定，无动态分配 | 静态分析 | CounterPattern |
| 可测试性 | 支持 Host 单元测试 | 测试框架验证 | counter_test_ng.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 标准行为 | 渲染测试 | - |
| 平板 | 无差异 | 标准行为 | 渲染测试 | - |
| 折叠屏 | 无差异 | 标准行为 | 渲染测试 | - |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 子节点 Button 和 Text 提供无障碍支持 | 按钮无障碍 |
| 大字体 | 否 | 组件尺寸由 height/width 属性决定 | - |
| 深色模式 | 否 | 背景色由用户设置 | - |
| 多窗口/分屏 | 否 | 组件无窗口状态依赖 | - |
| 多用户 | 否 | 无用户状态 | - |
| 版本升级 | 是 | API 18+ 使用 FocusType::SCOPE 焦点模式 | 版本兼容 |
| 生态兼容 | 否 | 无外部依赖 | - |

## 行为场景（可选，Gherkin）

> L1 标准复杂度，使用"接口规格 → 行为场景"表覆盖，无需 Gherkin。

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Counter 三节点结构的创建顺序和索引分配机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "SetHeight 属性传播到所有子节点的实现细节"
  - repo: "openharmony/arkui_ace_engine"
    query: "RTL/LTR 布局算法的边框圆角处理逻辑"
```

**关键文档：**
- design.md: `specs/05-ui-components/10-information-display-components/10-counter/design.md`
- 源码: `frameworks/core/components_ng/pattern/counter/`