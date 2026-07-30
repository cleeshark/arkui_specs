# 特性规格

## 概述

| Field | Content |
|-------|---------|
| 特性名称 | Counter 多范式接口与 C-API |
| 特性编号 | Func-05-10-10-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 动态 API (ModelNG) | Create() 返回 void，子节点同步创建 |
| ADDED | 静态 API (ModelStatic) | CreateFrameNode() 返回 FrameNode |
| ADDED | C-API (Native Modifier) | ArkUICounterModifier 结构 |

## 输入文档

- 设计文档: `specs/05-ui-components/10-information-display-components/10-counter/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/counter/`

## 用户故事

### US-1: 动态 API 使用

**作为** ArkTS 应用开发者  
**我想要** 使用链式调用方式创建 Counter 组件  
**以便** 在动态范式下开发应用

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 Counter() THEN 创建 Counter FrameNode 并推入 ViewStack | 正常 |
| AC-1.2 | WHEN Create() 完成 THEN 三子节点已同步创建并挂载 | 正常 |
| AC-1.3 | WHEN 使用动态 API THEN 子节点通过 ViewStackProcessor 管理 | 正常 |

### US-2: 静态 API 使用

**作为** 静态范式应用开发者  
**我想要** 通过全静态方法创建和配置 Counter 组件  
**以便** 支持静态编译优化（不依赖 ViewStackProcessor）

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 CounterModelStatic 全静态方法 THEN 不依赖 ViewStackProcessor | 正常 |
| AC-2.2 | WHEN 使用静态 API THEN 子节点在创建时同步创建并挂载 | 正常 |
| AC-2.3 | WHEN 使用静态 API 属性设置方法 THEN 需显式传入 FrameNode 参数 | 正常 |

### US-3: C-API 使用

**作为** NDK 开发者  
**我想要** 通过 C 接口操作 Counter 组件  
**以便** 在原生代码中集成

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 C-API create() THEN 创建 Counter 节点 | 正常 |
| AC-3.2 | WHEN 调用 C-API set* 函数 THEN 设置对应属性 | 正常 |
| AC-3.3 | WHEN 使用资源类型参数 THEN 调用 *Res 函数 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-3 | 单元测试 | ModelNG::Create 测试 |
| AC-1.2 | R-2 | TASK-3 | 结构测试 | 三子节点创建验证 |
| AC-1.3 | R-3 | TASK-3 | 架构测试 | ViewStackProcessor 验证 |
| AC-2.1 | R-4 | TASK-3 | 架构测试 | ModelStatic 静态方法验证 |
| AC-2.2 | R-5 | TASK-3 | 结构测试 | 子节点创建验证 |
| AC-2.3 | R-6 | TASK-3 | 单元测试 | FrameNode 参数传递验证 |
| AC-3.1 | R-7 | TASK-3 | C-API 测试 | create 测试 |
| AC-3.2 | R-8 | TASK-3 | C-API 测试 | set* 测试 |
| AC-3.3 | R-9 | TASK-3 | 资源测试 | *Res 测试 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 CounterModelNG::Create() | 创建 Counter FrameNode，推入 ViewStack | 无 | AC-1.1 |
| R-2 | 行为 | Create() 执行 | 同步创建 SUB_BUTTON、CONTENT、ADD_BUTTON 三子节点 | 固定顺序 | AC-1.2 |
| R-3 | 行为 | 使用动态 API | 子节点通过 ViewStackProcessor 管理 | 无 | AC-1.3 |
| R-4 | 行为 | 调用 CounterModelStatic 静态方法 | 不依赖 ViewStackProcessor，全静态方法 | 无 | AC-2.1 |
| R-5 | 行为 | CreateFrameNode() 执行 | 同步创建三子节点并挂载 | 固定顺序 | AC-2.2 |
| R-6 | 行为 | 调用静态 API 属性设置方法 | 需显式传入 FrameNode 参数 | 无 | AC-2.3 |
| R-7 | 行为 | 调用 C-API create() | 创建 Counter 节点句柄 | 无 | AC-3.1 |
| R-8 | 行为 | 调用 C-API set* 函数 | 设置对应属性 | 无 | AC-3.2 |
| R-9 | 行为 | 使用资源类型参数 | 调用 *Res 函数，传递资源指针 | 资源指针需有效 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3（动态 API） | 单元测试 | Create 流程和节点管理 |
| VM-2 | AC-2.1~2.3（静态 API） | 单元测试 | CreateFrameNode 流程 |
| VM-3 | AC-3.1~3.3（C-API） | C-API 测试 | Native Modifier 函数 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。

### 变更/废弃 API

> 无变更或废弃 API。

## 接口规格

### 接口定义

**CounterModelNG::Create()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void Create() override` |
| 返回值 | void — 不返回值 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 创建 Counter FrameNode，同步创建三子节点 | AC-1.1, AC-1.2 |

---

**CounterModelStatic::CreateFrameNode()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static RefPtr<FrameNode> CreateFrameNode(int32_t nodeId)` |
| 返回值 | `RefPtr<FrameNode>` — 帧节点实例 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| nodeId | int32_t | 是 | 无 | 必须为有效节点 ID |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | nodeId 有效 | 创建 Counter FrameNode，同步创建三子节点 | AC-2.1 |

---

**C-API: ArkUICounterModifier**

| 属性 | 值 |
|------|-----|
| 结构体 | `ArkUICounterModifier` |
| 开放范围 | Public (NDK) |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.3 |

**函数列表**

| 函数签名 | 用途 | 关联 AC |
|----------|------|---------|
| `void (*create)()` | 创建 Counter 节点 | AC-3.1 |
| `void (*setHeight)(ArkUINodeHandle node, ArkUI_Float32 number, ArkUI_Int32 unit)` | 设置高度 | AC-3.2 |
| `void (*setWidth)(ArkUINodeHandle node, ArkUI_Float32 number, ArkUI_Int32 unit)` | 设置宽度 | AC-3.2 |
| `void (*setBackgroundColor)(ArkUINodeHandle node, ArkUI_Uint32 value)` | 设置背景色 | AC-3.2 |
| `void (*setBackgroundColorRes)(ArkUINodeHandle node, ArkUI_Uint32 value, void* resPtr)` | 设置背景色（资源） | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 动态 API 返回类型 | Create() 返回 void，不返回 FrameNode 或 Controller | AC-1.1 |
| 子节点同步创建 | Create() 和 CreateFrameNode() 中同步创建三子节点 | AC-1.2, AC-2.3 |
| 静态 API 参数类型 | 使用 CalcLength 而非 Dimension | AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | C-API 调用无额外开销 | 直接函数调用 | 静态分析 |
| 兼容性 | 支持动态/静态范式切换 | 编译验证 | ModelNG/ModelStatic |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 标准行为 | API 测试 | - |
| 平板 | 无差异 | 标准行为 | API 测试 | - |
| 折叠屏 | 无差异 | 标准行为 | API 测试 | - |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | C-API 不直接涉及无障碍 | - |
| 大字体 | 否 | 尺寸属性由应用设置 | - |
| 深色模式 | 否 | 颜色属性由应用设置 | - |
| 多窗口/分屏 | 否 | 无窗口状态依赖 | - |
| 多用户 | 否 | 无用户状态 | - |
| 版本升级 | 否 | 无版本差异 | - |
| 生态兼容 | 是 | 支持多前端（ArkTS、C） | 多范式 |

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
    query: "Counter 动态 API 与静态 API 的返回类型差异原因"
  - repo: "openharmony/arkui_ace_engine"
    query: "Counter C-API ArkUICounterModifier 的结构设计"
```

**关键文档：**
- design.md: `specs/05-ui-components/10-information-display-components/10-counter/design.md`
- 源码: `frameworks/core/components_ng/pattern/counter/`