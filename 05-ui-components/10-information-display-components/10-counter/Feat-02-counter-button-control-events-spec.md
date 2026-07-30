# 特性规格

## 概述

| Field | Content |
|-------|---------|
| 特性名称 | Counter 按钮控制与事件回调 |
| 特性编号 | Func-05-10-10-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 按钮控制属性 | enableInc, enableDec |
| ADDED | 事件回调 | onInc, onDec |
| ADDED | 按钮创建逻辑 | CreateButtonChild, 符号设置 |

## 输入文档

- 设计文档: `specs/05-ui-components/10-information-display-components/10-counter/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/counter/`

## 用户故事

### US-1: 控制加号按钮状态

**作为** 应用开发者  
**我想要** 禁用或启用加号按钮  
**以便** 控制用户能否增加数值

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 enableInc=true THEN 加号按钮可点击 | 正常 |
| AC-1.2 | WHEN 设置 enableInc=false THEN 加号按钮禁用，透明度为 0.4 | 正常 |
| AC-1.3 | WHEN 加号按钮禁用 THEN 显示半透明效果，不响应点击 | 正常 |
| AC-1.4 | WHEN 未设置 enableInc THEN 默认启用 | 边界 |

### US-2: 控制减号按钮状态

**作为** 应用开发者  
**我想要** 禁用或启用减号按钮  
**以便** 控制用户能否减少数值

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 enableDec=true THEN 减号按钮可点击 | 正常 |
| AC-2.2 | WHEN 设置 enableDec=false THEN 减号按钮禁用，透明度为 0.4 | 正常 |
| AC-2.3 | WHEN 减号按钮禁用 THEN 显示半透明效果，不响应点击 | 正常 |
| AC-2.4 | WHEN 未设置 enableDec THEN 默认启用 | 边界 |

### US-3: 处理加号按钮点击

**作为** 应用开发者  
**我想要** 在用户点击加号按钮时收到回调  
**以便** 更新数值状态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 点击加号按钮 THEN 触发 onInc 回调 | 正常 |
| AC-3.2 | WHEN onInc 回调触发 THEN 无参数传递 | 正常 |
| AC-3.3 | WHEN 加号按钮禁用 THEN 不触发 onInc 回调 | 边界 |

### US-4: 处理减号按钮点击

**作为** 应用开发者  
**我想要** 在用户点击减号按钮时收到回调  
**以便** 更新数值状态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 点击减号按钮 THEN 触发 onDec 回调 | 正常 |
| AC-4.2 | WHEN onDec 回调触发 THEN 无参数传递 | 正常 |
| AC-4.3 | WHEN 减号按钮禁用 THEN 不触发 onDec 回调 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-2 | 状态测试 | enableInc=true 测试 |
| AC-1.2 | R-2 | TASK-2 | 视觉测试 | enableInc=false 测试 |
| AC-1.3 | R-3 | TASK-2 | 交互测试 | 禁用点击验证 |
| AC-1.4 | R-4 | TASK-2 | 默认值测试 | 默认启用验证 |
| AC-2.1 | R-5 | TASK-2 | 状态测试 | enableDec=true 测试 |
| AC-2.2 | R-6 | TASK-2 | 视觉测试 | enableDec=false 测试 |
| AC-2.3 | R-7 | TASK-2 | 交互测试 | 禁用点击验证 |
| AC-2.4 | R-8 | TASK-2 | 默认值测试 | 默认启用验证 |
| AC-3.1 | R-9 | TASK-2 | 事件测试 | onInc 触发测试 |
| AC-3.2 | R-10 | TASK-2 | 参数测试 | 无参数验证 |
| AC-3.3 | R-11 | TASK-2 | 边界测试 | 禁用不触发验证 |
| AC-4.1 | R-12 | TASK-2 | 事件测试 | onDec 触发测试 |
| AC-4.2 | R-13 | TASK-2 | 参数测试 | 无参数验证 |
| AC-4.3 | R-14 | TASK-2 | 边界测试 | 禁用不触发验证 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 enableInc=true | 加号按钮 EventHub::enabled_=true，opacity=1.0 | 无 | AC-1.1 |
| R-2 | 行为 | 设置 enableInc=false | 加号按钮 EventHub::enabled_=false，opacity=0.4 | alphaDisabled=0.4 | AC-1.2 |
| R-3 | 行为 | 加号按钮禁用 | 不响应点击，显示半透明效果 | 无 | AC-1.3 |
| R-4 | 边界 | 未设置 enableInc | 默认 EventHub::enabled_=true | 无 | AC-1.4 |
| R-5 | 行为 | 设置 enableDec=true | 减号按钮 EventHub::enabled_=true，opacity=1.0 | 无 | AC-2.1 |
| R-6 | 行为 | 设置 enableDec=false | 减号按钮 EventHub::enabled_=false，opacity=0.4 | alphaDisabled=0.4 | AC-2.2 |
| R-7 | 行为 | 减号按钮禁用 | 不响应点击，显示半透明效果 | 无 | AC-2.3 |
| R-8 | 边界 | 未设置 enableDec | 默认 EventHub::enabled_=true | 无 | AC-2.4 |
| R-9 | 行为 | 点击加号按钮（启用状态） | 触发 GestureEventHub::SetUserOnClick 注册的回调 | 无 | AC-3.1 |
| R-10 | 行为 | onInc 回调触发 | 无参数，直接调用 CounterEventFunc | 无 | AC-3.2 |
| R-11 | 边界 | 点击加号按钮（禁用状态） | 不触发 onInc 回调 | 无 | AC-3.3 |
| R-12 | 行为 | 点击减号按钮（启用状态） | 触发 GestureEventHub::SetUserOnClick 注册的回调 | 无 | AC-4.1 |
| R-13 | 行为 | onDec 回调触发 | 无参数，直接调用 CounterEventFunc | 无 | AC-4.2 |
| R-14 | 边界 | 点击减号按钮（禁用状态） | 不触发 onDec 回调 | 无 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4（加号按钮控制） | 状态测试 | enableInc 开关行为 |
| VM-2 | AC-2.1~2.4（减号按钮控制） | 状态测试 | enableDec 开关行为 |
| VM-3 | AC-3.1~3.3（加号事件） | 事件测试 | onInc 回调触发 |
| VM-4 | AC-4.1~4.3（减号事件） | 事件测试 | onDec 回调触发 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。

### 变更/废弃 API

> 无变更或废弃 API。

## 接口规格

### 接口定义

**SetEnableInc()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableInc(value: boolean): Counter` |
| 返回值 | `Counter` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2, AC-1.3, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 否 | true | 无 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value=true | 加号按钮启用，opacity=1.0 | AC-1.1 |
| 2 | value=false | 加号按钮禁用，opacity=0.4 | AC-1.2, AC-1.3 |
| 3 | 未调用 | 默认启用 | AC-1.4 |

---

**SetEnableDec()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableDec(value: boolean): Counter` |
| 返回值 | `Counter` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2, AC-2.3, AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 否 | true | 无 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value=true | 减号按钮启用，opacity=1.0 | AC-2.1 |
| 2 | value=false | 减号按钮禁用，opacity=0.4 | AC-2.2, AC-2.3 |
| 3 | 未调用 | 默认启用 | AC-2.4 |

---

**SetOnInc()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onInc(callback: () => void): Counter` |
| 返回值 | `Counter` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.2, AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | function | 否 | 无 | 无参数回调函数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 点击加号按钮（启用） | 触发 callback，无参数 | AC-3.1, AC-3.2 |
| 2 | 点击加号按钮（禁用） | 不触发 callback | AC-3.3 |

---

**SetOnDec()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onDec(callback: () => void): Counter` |
| 返回值 | `Counter` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1, AC-4.2, AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | function | 否 | 无 | 无参数回调函数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 点击减号按钮（启用） | 触发 callback，无参数 | AC-4.1, AC-4.2 |
| 2 | 点击减号按钮（禁用） | 不触发 callback | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 启用状态存储 | 存储在 EventHub::enabled_ 和 developerEnabled_ | AC-1.1~1.4, AC-2.1~2.4 |
| 禁用透明度 | 存储在 RenderContext::opacity，值为 0.4 | AC-1.2, AC-2.2 |
| 事件回调无参数 | CounterEventFunc 为 std::function<void()> | AC-3.2, AC-4.2 |
| 事件注册机制 | 通过 GestureEventHub::SetUserOnClick 注册 | AC-3.1, AC-4.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 事件注册无额外开销 | 代码审查 | GestureEventHub 使用 |
| 可测试性 | 支持模拟点击事件 | 测试框架验证 | counter_test_ng.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 标准行为 | 交互测试 | - |
| 平板 | 无差异 | 标准行为 | 交互测试 | - |
| 折叠屏 | 无差异 | 标准行为 | 交互测试 | - |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 禁用状态通过 EventHub 管理，影响无障碍状态 | 按钮无障碍 |
| 大字体 | 否 | 组件尺寸由 height/width 属性决定 | - |
| 深色模式 | 否 | 禁用透明度固定为 0.4 | - |
| 多窗口/分屏 | 否 | 组件无窗口状态依赖 | - |
| 多用户 | 否 | 无用户状态 | - |
| 版本升级 | 否 | 无版本差异 | - |
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
    query: "Counter 按钮启用状态的 EventHub 存储机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "禁用状态下透明度 0.4 的主题配置"
  - repo: "openharmony/arkui_ace_engine"
    query: "onInc/onDec 事件通过 GestureEventHub 注册的实现"
```

**关键文档：**
- design.md: `specs/05-ui-components/10-information-display-components/10-counter/design.md`
- 源码: `frameworks/core/components_ng/pattern/counter/`