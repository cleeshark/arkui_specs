# 特性规格

## 概述

| Field | Content |
|-------|---------|
| 特性名称 | PatternLock 多范式接口与 C-API |
| 特性编号 | Func-05-10-04-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 动态 API (ModelNG) | 实例方法 + 静态方法，返回 PatternLockController |
| ADDED | 静态 API (ModelStatic) | 全静态方法，std::optional 参数支持重置 |
| ADDED | C-API (Native Modifier) | ArkUIPatternLockModifier + GENERATED_ArkUIPatternLockModifier |
| ADDED | 控制器访问器 | PatternLockControllerAccessor C-API |

## 输入文档

- 设计文档: `specs/05-ui-components/10-information-display-components/04-pattern-lock/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/patternlock/`, `interfaces/native/`

## 用户故事

### US-1: 动态 API 使用

**作为** ArkTS 应用开发者  
**我想要** 使用链式调用方式创建和配置 PatternLock 组件  
**以便** 在动态范式下开发应用

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 PatternLock() THEN 返回 PatternLockController 实例 | 正常 |
| AC-1.2 | WHEN 链式调用 .selectedColor(color) THEN 属性被正确设置 | 正常 |
| AC-1.3 | WHEN 使用动态 API THEN 支持 SetByUser 追踪机制 | 正常 |

### US-2: 静态 API 使用

**作为** 静态范式应用开发者  
**我想要** 通过全静态方法（显式传入 FrameNode）配置 PatternLock 组件  
**以便** 支持静态编译优化和属性重置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 ModelStatic 静态方法设置属性 THEN 需显式传入 FrameNode 参数 | 正常 |
| AC-2.2 | WHEN 调用 GetController(frameNode) THEN 返回 PatternLockController | 正常 |
| AC-2.3 | WHEN 属性参数为 std::nullopt THEN 重置属性为默认值 | 正常 |

### US-3: C-API 使用

**作为** NDK 开发者  
**我想要** 通过 C 接口操作 PatternLock 组件  
**以便** 在原生代码中集成

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 createFrameNode(nodeId) THEN 返回 ArkUINodeHandle | 正常 |
| AC-3.2 | WHEN 调用 setPatternLockActiveColor(node, color) THEN 设置激活颜色 | 正常 |
| AC-3.3 | WHEN 调用 resetPatternLockActiveColor(node) THEN 重置为默认颜色 | 正常 |
| AC-3.4 | WHEN 使用资源类型参数 THEN 调用 setPatternLockActiveColorRes(node, value, resPtr) | 正常 |

### US-4: 控制器 C-API

**作为** NDK 开发者  
**我想要** 通过 C 接口调用控制器方法  
**以便** 在原生代码中重置图案

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 调用 ResetImpl(peer) THEN 清空已选点 | 正常 |
| AC-4.2 | WHEN 调用 SetChallengeResultImpl(peer, result) THEN 设置挑战结果 | 正常 |
| AC-4.3 | WHEN 调用 ConstructImpl() THEN 创建新的控制器对等对象 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-3 | 单元测试 | ModelNG::Create 测试 |
| AC-1.2 | R-2 | TASK-3 | 链式调用测试 | 属性设置验证 |
| AC-1.3 | R-3 | TASK-3 | 追踪测试 | SetByUser 验证 |
| AC-2.1 | R-4 | TASK-3 | 单元测试 | ModelStatic 静态方法测试 |
| AC-2.2 | R-5 | TASK-3 | 控制器测试 | GetController 验证 |
| AC-2.3 | R-6 | TASK-3 | 重置测试 | std::optional 重置验证 |
| AC-3.1 | R-7 | TASK-3 | C-API 测试 | createFrameNode 测试 |
| AC-3.2 | R-8 | TASK-3 | C-API 测试 | set* 函数测试 |
| AC-3.3 | R-9 | TASK-3 | C-API 测试 | reset* 函数测试 |
| AC-3.4 | R-10 | TASK-3 | 资源测试 | *Res 函数测试 |
| AC-4.1 | R-11 | TASK-3 | 控制器测试 | ResetImpl 测试 |
| AC-4.2 | R-12 | TASK-3 | 控制器测试 | SetChallengeResultImpl 测试 |
| AC-4.3 | R-13 | TASK-3 | 构造测试 | ConstructImpl 测试 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 PatternLockModelNG::Create() | 返回 RefPtr<V2::PatternLockController> | 无 | AC-1.1 |
| R-2 | 行为 | 调用 ModelNG 实例方法设置属性 | 通过 ViewStackProcessor 获取 FrameNode 并设置属性 | 无 | AC-1.2 |
| R-3 | 行为 | 调用 ModelNG 颜色设置方法 | 设置 SetByUser 标志位为 true | 仅 ModelNG 支持 | AC-1.3 |
| R-4 | 行为 | 调用 PatternLockModelStatic 静态方法 | 需显式传入 FrameNode* 参数，不依赖 ViewStackProcessor | 无 | AC-2.1 |
| R-5 | 行为 | 调用 GetController(frameNode) | 返回 RefPtr<V2::PatternLockController> | frameNode 非空 | AC-2.2 |
| R-6 | 行为 | std::optional 参数为 nullopt | 调用 ACE_RESET_NODE_PAINT_PROPERTY 重置属性 | 无 | AC-2.3 |
| R-7 | 行为 | 调用 C-API createFrameNode(nodeId) | 返回 ArkUINodeHandle | 无 | AC-3.1 |
| R-8 | 行为 | 调用 C-API set* 函数 | 调用对应的 ModelStatic 方法设置属性 | 无 | AC-3.2 |
| R-9 | 行为 | 调用 C-API reset* 函数 | 重置属性为默认值（从主题获取） | 无 | AC-3.3 |
| R-10 | 行为 | 使用资源类型参数 | 调用 *Res 函数，传递资源指针 | 资源指针需有效 | AC-3.4 |
| R-11 | 行为 | 调用 ResetImpl(peer) | 调用 handler->Reset() 清空选择 | peer 必须有效 | AC-4.1 |
| R-12 | 行为 | 调用 SetChallengeResultImpl(peer, result) | 设置挑战结果（CORRECT/WRONG） | peer 必须有效 | AC-4.2 |
| R-13 | 行为 | 调用 ConstructImpl() | 创建新的 Ark_PatternLockController 对等对象 | 无 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3（动态 API） | 单元测试 | Create 返回值和属性设置 |
| VM-2 | AC-2.1~2.3（静态 API） | 单元测试 | FrameNode 创建和 optional 重置 |
| VM-3 | AC-3.1~3.4（C-API） | C-API 测试 | Native Modifier 函数 |
| VM-4 | AC-4.1~4.3（控制器 C-API） | C-API 测试 | Controller Accessor 函数 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。

### 变更/废弃 API

> 无变更或废弃 API。

## 接口规格

### 接口定义

**PatternLockModelNG::Create()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<V2::PatternLockController> Create() override` |
| 返回值 | `RefPtr<V2::PatternLockController>` — 控制器实例 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 通过 ViewStackProcessor 创建 FrameNode，返回 Controller | AC-1.1 |

---

**PatternLockModelStatic::CreateFrameNode()**

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
| 1 | nodeId 有效 | 创建 FrameNode，初始化 Pattern 和 Controller | AC-2.1 |

---

**PatternLockModelStatic::GetController()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static const RefPtr<V2::PatternLockController> GetController(FrameNode* frameNode)` |
| 返回值 | `RefPtr<V2::PatternLockController>` — 控制器实例 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| frameNode | FrameNode* | 是 | 无 | 必须非空 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | frameNode 非空 | 返回关联的 PatternLockController | AC-2.2 |
| 2 | frameNode 为空 | 返回 nullptr | 边界 |

---

**PatternLockModelStatic::Set*()（std::optional 模式）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static void SetActiveColor(FrameNode* frameNode, const std::optional<Color>& activeColor)` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| frameNode | FrameNode* | 是 | 无 | 必须非空 |
| activeColor | std::optional<Color> | 否 | nullopt | nullopt 时重置属性 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | activeColor.has_value() | 调用 ACE_UPDATE_NODE_PAINT_PROPERTY 设置属性 | AC-2.3 |
| 2 | !activeColor.has_value() | 调用 ACE_RESET_NODE_PAINT_PROPERTY 重置属性 | AC-2.3 |

---

**C-API: ArkUIPatternLockModifier**

| 属性 | 值 |
|------|-----|
| 结构体 | `ArkUIPatternLockModifier` |
| 开放范围 | Public (NDK) |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.4 |

**函数列表**

| 函数签名 | 用途 | 关联 AC |
|----------|------|---------|
| `void (*createModel)(ArkUI_Bool isObject, void* controller)` | 创建组件模型 | AC-3.1 |
| `void (*setPatternLockActiveColor)(ArkUINodeHandle node, ArkUI_Uint32 value)` | 设置激活颜色 | AC-3.2 |
| `void (*resetPatternLockActiveColor)(ArkUINodeHandle node)` | 重置激活颜色 | AC-3.3 |
| `void (*setPatternLockActiveColorRes)(ArkUINodeHandle node, ArkUI_Uint32 value, void* resPtr)` | 设置激活颜色（资源类型） | AC-3.4 |
| `ArkUINodeHandle (*createFrameNode)(ArkUI_Int32 nodeId)` | 创建帧节点 | AC-3.1 |

---

**C-API: PatternLockControllerAccessor**

| 属性 | 值 |
|------|-----|
| 模块 | `pattern_lock_controller_accessor` |
| 开放范围 | Public (NDK) |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.3 |

**函数列表**

| 函数签名 | 用途 | 关联 AC |
|----------|------|---------|
| `void ResetImpl(Ark_PatternLockController peer)` | 重置图案 | AC-4.1 |
| `void SetChallengeResultImpl(Ark_PatternLockController peer, Ark_PatternLockChallengeResult result)` | 设置挑战结果 | AC-4.2 |
| `Ark_PatternLockController ConstructImpl()` | 构造控制器对等对象 | AC-4.3 |
| `void DestroyPeerImpl(Ark_PatternLockController peer)` | 销毁对等对象 | 边界 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 动态 API 返回类型 | Create() 返回 Controller 而非 FrameNode | AC-1.1 |
| 静态 API 可选参数 | 使用 std::optional 支持属性重置 | AC-2.3 |
| C-API 分离设计 | 动态/静态接口分离，新旧管线兼容 | AC-3.1~3.4 |
| 控制器访问器模式 | 通过 peer 指针访问底层 Controller | AC-4.1~4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | C-API 调用无额外开销 | 直接函数调用 | 静态分析 |
| 兼容性 | 支持新旧管线切换 | Container::IsCurrentUseNewPipeline() | 运行时检查 |
| 可测试性 | 支持 Host C-API 单元测试 | capi modifiers 测试 | pattern_lock_modifier_test.cpp |

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
| 版本升级 | 是 | 支持新旧管线运行时切换 | 版本兼容 |
| 生态兼容 | 是 | 支持多前端（ArkTS、CJ、C） | 多范式 |

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
    query: "PatternLock 动态 API 与静态 API 的返回类型差异原因"
  - repo: "openharmony/arkui_ace_engine"
    query: "C-API ArkUIPatternLockModifier 的动态/静态接口分离设计"
  - repo: "openharmony/arkui_ace_engine"
    query: "PatternLockControllerAccessor 的 peer 对象生命周期管理"
```

**关键文档：**
- design.md: `specs/05-ui-components/10-information-display-components/04-pattern-lock/design.md`
- 源码: `frameworks/core/components_ng/pattern/patternlock/`, `interfaces/native/`