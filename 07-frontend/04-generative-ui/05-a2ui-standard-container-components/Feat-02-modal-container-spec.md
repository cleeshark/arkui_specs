# 特性规格

> Func-07-04-05-Feat-02 Modal 模态框：固化 A2UI 标准协议 Modal 组件的行为——Modal 不创建可见组件节点，而是作为「协议节点」由 `ModalCoordinator` 绑定 `trigger`/`content`，点击 trigger 弹原生 dialog；覆盖描述符解析、绑定校验链（多条件跳过并 retain）、期望栈与活动 dialog 差分协调、原生 dialog 生命周期、`weight`/`accessibility` 属性转发。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Modal 模态框 |
| 特性编号 | Func-07-04-05-Feat-02 |
| 优先级 | P0 |
| 目标版本 | API Version 20；A2UI 标准协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 与 Feat-01 并列，共享 Func-07-04-05 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/05-a2ui-standard-container-components/design.md` | Baselined |
| Modal 类目（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIModal.ets` | — |
| Modal 协调器（C++） | `genui/src/main/cpp/components/A2UI/modal/ModalCoordinator.cpp/.h` | — |
| 树分发（C++） | `genui/src/main/cpp/SurfaceSlot.cpp` | — |
| Modal 文档（Docs） | `reference/standard-components/modal.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Modal 类目注册与协议节点识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `component: "Modal"` 描述符,
**以便** 声明模态框而不产生普通可见组件节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ArkTS 类目项声明类型为 `Modal` THEN `A2UIModal.type=="Modal"` 且 `asCatalogItem()` 注册并 `markCategory(A2UI_STANDARD).markInnerNative(true)`（`A2UIModal.ets:24-34`） | 正常 |
| AC-1.2 | WHEN `SurfaceSlot::HandleSpecialRootBuildDescriptor` 见 `componentType=="Modal"` THEN 经 `TryCreateDescriptor` 收集描述符并入 `state.modalDescriptors`（`SurfaceSlot.cpp:1170-1176`） | 正常 |
| AC-1.3 | WHEN 描述符为非对象或 `component!="Modal"` THEN `TryCreateDescriptor` 返回 false 不生成描述符（`ModalCoordinator.cpp:374-380`） | 异常 |
| AC-1.4 | WHEN 根构建完成 THEN `HandlePendingModalDescriptors` 被调用并传入 `allComponents_`/`parentsRelations_`（`SurfaceSlot.cpp:1246`） | 正常 |

### US-2: Modal 描述符解析与字段校验

**作为** 生成式 UI 宿主开发者,
**我想要** Modal 描述符被严格解析,
**以便** 非法字段/缺字段以 schema warning 提示并回退默认值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `TryCreateDescriptor` 成功 THEN 读取 `id`/`trigger`/`content`（required）并序列化动态字符串字面量（`ModalCoordinator.cpp:382-389`） | 正常 |
| AC-2.2 | WHEN `id` 缺失或非 string THEN `ReadStringProperty` 派发 `SCHEMA_ERROR_CODE_REQUIRED_MISS`/`TYPE_MISMATCH` 并返回空串（`ModalCoordinator.cpp:132-153`） | 异常 |
| AC-2.3 | WHEN `trigger`/`content` 缺失 → `ReadDynamicStringPropertyLiteral` 派发 required 警告；非 string 且非动态描述符 → `TYPE_MISMATCH`（`ModalCoordinator.cpp:155-184`） | 异常 |
| AC-2.4 | WHEN 出现未知顶层字段 THEN 派发 `SCHEMA_ERROR_CODE_UNDEFINED_FIELD` warning；已知字段是 `id/component/trigger/content/accessibility/weight`（`ModalCoordinator.cpp:72-76,104-130`） | 边界 |
| AC-2.5 | WHEN `accessibility` 下出现未知字段 THEN 仅认可 `label`/`description`，其余派发 undefined 警告（`ModalCoordinator.cpp:67-70,80-102`） | 边界 |
| AC-2.6 | WHEN `weight` 非 number THEN 派发 `TYPE_MISMATCH` 且忽略；为 number 则 `hasWeight=true` 记录其值（`ModalCoordinator.cpp:391-404`） | 边界 |

### US-3: Modal 绑定校验链

**作为** 生成式 UI 宿主开发者,
**我想要** 无效的 trigger/content 引用被拒绝且不崩溃,
**以便** 只对合法绑定弹框，非法绑定留待后续数据更新重试。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `content` 动态解析为 `"root"` THEN 绑定跳过并 retain（root 不可作 modal content）（`ModalCoordinator.cpp:620-626`） | 边界 |
| AC-3.2 | WHEN `trigger` 组件不存在或非 `A2UIComponent`（不支持点击） THEN 跳过并保留描述符待重试（`ModalCoordinator.cpp:633-655`） | 异常 |
| AC-3.3 | WHEN `content` 组件不存在或无 native view THEN 跳过并 retain（`ModalCoordinator.cpp:640-663`） | 异常 |
| AC-3.4 | WHEN `content` 已挂载于正常组件树（`parentsRelations_` 含其 id） THEN 跳过并 retain（`ModalCoordinator.cpp:664-671`） | 边界 |
| AC-3.5 | WHEN 出现重复 trigger id 或重复 content id THEN `ReserveModalBindingIds` 拒绝重复绑定（`ModalCoordinator.cpp:674-692`） | 异常 |
| AC-3.6 | WHEN 动态 `trigger`/`content` id 无法解析 THEN `ResolveModalDescriptorIds` 返回 false，绑定跳过（`ModalCoordinator.cpp:712-744`） | 异常 |

### US-4: trigger 点击与模态栈

**作为** 生成式 UI 宿主开发者,
**我想要** 点击 trigger 打开/切换/关闭 modal,
**以便** 支持叠层的模态呈现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 绑定生效 THEN `ApplyResolvedModalBinding` 经 `SetAuxiliaryOnClick(MODAL_CLICK_BINDING_KEY, ...)` 挂 trigger 点击（`ModalCoordinator.cpp:707-709`） | 正常 |
| AC-4.2 | WHEN `HandleModalTriggerClick` 收到空 modalId THEN 直接返回不改变栈（`ModalCoordinator.cpp:488-490`） | 边界 |
| AC-4.3 | WHEN 被点 modalId 不在栈中 THEN 追加到栈顶；已在栈顶则弹出；在栈中则截断其后（`ModalCoordinator.cpp:492-501`） | 正常 |
| AC-4.4 | WHEN 期望栈经 `BuildDesiredDialogStack` 遍历到无效 content THEN 截断栈至有效项（`ModalCoordinator.cpp:505-531`） | 异常 |

### US-5: 原生 dialog 呈现与差分协调

**作为** 生成式 UI 宿主开发者,
**我想要** 期望栈与实际原生 dialog 保持差分一致,
**以便** 最小化原生 dialog 重建并支持叠层。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 活动 dialog 多于公共前缀 THEN `CloseTopActiveDialogForTransition` 逐层关闭并 `DialogDispose`（`ModalCoordinator.cpp:812-820,916-936`） | 正常 |
| AC-5.2 | WHEN 期望 dialog 多于活动 dialog THEN `PresentNativeDialog` 创建并 `DialogShow`（`ModalCoordinator.cpp:822-836,882-914`） | 正常 |
| AC-5.3 | WHEN 配置原生 dialog THEN 依次设置 content/自定义样式/居中/模态/自动取消/`onWillDismiss` 后 show（`ModalCoordinator.cpp:839-880`） | 正常 |
| AC-5.4 | WHEN `dialogCloseInProgress_` 为 true THEN `UpdateModalPresentation` 直接返回（防重入）（`ModalCoordinator.cpp:798-800`） | 边界 |
| AC-5.5 | WHEN 呈现失败（dialog null 或配置失败） THEN 打 `LOG_ERROR` 并 `cleanup` 释放句柄/上下文（`ModalCoordinator.cpp:890-906`） | 异常 |

### US-6: dismiss 回调和生命周期回收

**作为** 生成式 UI 宿主开发者,
**我想要** 原生 dismiss 与主动关闭正确回收资源,
**以便** 无内存泄漏、无 double-free。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 原生 dialog 触发 `onWillDismiss` THEN 静态 `OnNativeDialogWillDismiss` 经全局注册表回查 `ModalCoordinator` 并 `HandleNativeDialogDismiss`（`ModalCoordinator.cpp:1105-1126`） | 正常 |
| AC-6.2 | WHEN dismiss 的 context 不在活动栈 THEN 依次尝试退休表/脱离表释放，均未命中则直接 `delete`（`ModalCoordinator.cpp:1043-1050`） | 恢复 |
| AC-6.3 | WHEN `SurfaceSlot::DismissActiveModal`（如 BACK 手势） THEN `ModalCoordinator::DismissActiveModal` 清栈并 `ForceCloseAllActiveDialogs`（`SurfaceSlot.cpp:477-483`、`ModalCoordinator.cpp:419-427`） | 正常 |
| AC-6.4 | WHEN `Dispose`（surface 销毁） THEN 清触发绑定/栈/dialog/描述符/绑定并注销 owner（`ModalCoordinator.cpp:429-442`） | 正常 |
| AC-6.5 | WHEN `RegisterOwner`/`UnregisterOwner` 进行 THEN owner 身份需 `renderId>=0 && surfaceId` 非空（`ModalCoordinator.cpp:1064-1088`） | 边界 |

### US-7: 属性转发到 trigger

**作为** 生成式 UI 宿主开发者,
**我想要** Modal 的 `weight`/`accessibility` 转发到 trigger,
**以便** trigger 呈现时拥有相应布局与无障碍属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `weight` 存在且 finite 且 >0 THEN `SetTriggerLayoutWeight` 归一化为 uint32（≤0/非有限 → 0，0 值视作未转发）（`ModalCoordinator.cpp:188-204`） | 边界 |
| AC-7.2 | WHEN `accessibility.label`/`description` 为合法动态串 THEN 解析后 `SetTriggerAccessibilityLabel/Description` 下发到 trigger（`ModalCoordinator.cpp:746-791`） | 正常 |
| AC-7.3 | WHEN 取消绑定/重建 THEN `ResetTriggerCommonAttributes` 重置曾转发的 weight/accessibility（`ModalCoordinator.cpp:553-565`） | 恢复 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-2 | 静态比对 + C++ UT | `A2UIModal.ets:24-34`、`SurfaceSlot.cpp:1170-1246` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 | R-2,R-6 | T-2 | C++ UT：TryCreateDescriptor + 字段校验 | `ModalCoordinator.cpp:132-409` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-3 | T-2 | C++ UT（TDD_BUILD）绑定校验链 | `ModalCoordinator.cpp:611-744` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-2 | C++ UT（TDD_BUILD）栈操作 | `ModalCoordinator.cpp:487-531` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-5 | T-2 | C++ UT（TDD_BUILD）差分呈现 | `ModalCoordinator.cpp:793-936` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 | R-7 | T-2 | C++ UT（TDD_BUILD）dismiss 生命周期 | `ModalCoordinator.cpp:419-442,1037-1126` |
| AC-7.1,AC-7.2,AC-7.3 | R-8 | T-2 | C++ UT（TDD_BUILD）属性转发 | `ModalCoordinator.cpp:188-204,746-791` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor `component=="Modal"` | 收集描述符并经协调器绑定，不产生可见组件节点 | innerNative=true | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 异常 | id/trigger/content 缺失或类型错 | schema warning 并回退默认值 | required 字段派发 `REQUIRED_MISS` | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |
| R-3 | 异常 | 绑定引用非法（root/不存在/无 native view/已挂载/重复） | 跳过绑定并 retain 待重试 | 逐条短路校验 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| R-4 | 行为 | trigger 点击 | 更新 `openModalStack_`（push/pop/截断） | 空 modalId 忽略 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-5 | 行为 | 期望栈与活动 dialog 差分 | 公共前缀保留、多关闭、少呈现 | `dialogCloseInProgress_` 防重入 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |
| R-6 | 恢复 | 原生 dismiss/主动关闭 | 同步栈 + 释放 dismiss context | 退休/脱离表防 double-free | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |
| R-7 | 边界 | 未知字段 | 类型不符/未知字段警告 | known 字段白名单 | AC-2.4,AC-2.5,AC-2.6 |
| R-8 | 行为 | weight/accessibility 存在 | 转发到 trigger；重建时重置 | weight 归一化 | AC-7.1,AC-7.2,AC-7.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 协议节点识别 | 静态比对 + C++ UT | Modal 描述符收集不建节点 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 描述符校验 | C++ UT | 必填/类型/未知字段警告 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 绑定校验链 | C++ UT（TDD_BUILD） | 各跳过条件与 retain |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 模态栈 | C++ UT（TDD_BUILD） | push/pop/截断 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 差分呈现 | C++ UT（TDD_BUILD） | 原生 dialog 重建/关闭 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 生命周期 | C++ UT（TDD_BUILD） | dismiss 回调 + 资源回收 |
| VM-7 | AC-7.1,AC-7.2,AC-7.3 属性转发 | C++ UT（TDD_BUILD） | weight 归一化 + accessibility + 重置 |

## API 变更分析

> 存量补录，无新增/变更公开 ArkTS/C-API。本节列出受影响组件协议。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Modal` 组件协议（`component`/`trigger`/`content`/`weight`/`accessibility`） | 既有 | 模态框声明 | trigger/content 引用同 surfaceId 组件 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |
| `ModalCoordinator`（内部 native 类） | 既有 | 原生 dialog 协调 | 不直接暴露给宿主 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

> Schema 位置：`components/Modal.json`（经 `A2UIModal.ets:26-28` 加载）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ModalCoordinator::TryCreateDescriptor(nodeValue, descriptor)`（`ModalCoordinator.cpp:372`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool TryCreateDescriptor(const JsonValue&, ModalDescriptor&) const` |
| 返回值 | `bool` — 是否成功生成描述符 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（经 `WarningDispatchBridge` 派发 schema warning） |
| 关联 AC | AC-1.2,AC-1.3,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |

**`ModalCoordinator::HandlePendingModalDescriptors(...)`（`ModalCoordinator.cpp:444`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void HandlePendingModalDescriptors(const vector<ModalDescriptor>&, const map<...>&, const map<...>&)` |
| 返回值 | `void` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-1.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id | string | 是 | — | 非空 |
| trigger | string/dynamic | 是 | — | 引用同 surfaceId 可点击组件 |
| content | string/dynamic | 是 | — | 引用同 surfaceId 未挂载组件；不可为 `root` |
| weight | number | 否 | 无转发 | finite 且 >0 |
| accessibility.label/description | string/dynamic | 否 | 无转发 | 解析为 string |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | component=="Modal" | 收集描述符 | AC-1.2 |
| 2 | id/trigger/content 缺失 | schema warning + 空串回退 | AC-2.2,AC-2.3 |
| 3 | 未知字段 | undefined warning | AC-2.4,AC-2.5 |
| 4 | trigger/content 引用非法 | 跳过绑定并 retain | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| 5 | trigger 点击 | 更新模态栈 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| 6 | 原生 dismiss | 同步栈 + 释放 context | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API Version 20（`modal.md:5`）。
- **API 版本号策略:** 组件协议经 JSON Schema 约束；native 未消费 `action.event.name=="modal.trigger"`/`"modal.dismiss"`（风险 RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 协议节点 | Modal 不产生可见组件节点 | AC-1.2 |
| 绑定校验链 | 引用非法则 skip + retain | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| 差分协调 | 期望栈与活动 dialog 差分一致 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |
| 生命周期回收 | dismiss context 退休/脱离防 double-free | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法绑定不崩溃，skip + retain | C++ UT（TDD_BUILD） | `ModalCoordinator.cpp:611-672` |
| 内存 | dialog 句柄/上下文释放无泄漏、无 double-free | C++ UT（TDD_BUILD） | `ModalCoordinator.cpp:882-936,1037-1126` |
| 可测试性 | `#ifdef TDD_BUILD` 暴露绑定/栈计数 | C++ UT | `ModalCoordinator.h:69-101` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 原生 dialog 居中呈现 | ohosTest | `ModalCoordinator.cpp:852` |
| 平板 | 无差异 | 同上 | ohosTest | 同上 |
| 折叠屏 | 无差异 | 同上 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibility.label/description` 转发到 trigger | AC-7.2 |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version 20 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 标准组件协议 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Modal 模态框
  作为 生成式 UI 宿主开发者
  我想要 点击 trigger 打开/切换/关闭模态框
  以便 通过叠加对话引导用户操作

  Scenario: 点击 trigger 打开模态框
    Given DSL 声明 Button("btn") 与 Modal(trigger="btn", content="dlg") 且 dlg 未挂载正常树
    When 点击 btn
    Then 呈现原生 dialog 并展示 dlg 内容

  Scenario Outline: 非法绑定跳过
    Given Modal 描述符 <what>
    When 建立绑定
    Then 跳过该绑定并保留描述符待重试

    Examples:
      | what                              |
      | content="root"                    |
      | trigger 引用不存在                 |
      | content 已挂载正常树               |
      | 重复 trigger id / 重复 content id   |

  Scenario: 原生 dismiss 同步栈
    Given 一个活动 modal
    When 触发 onWillDismiss
    Then 释放 dismiss context 并从期望栈移除该 modal
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Modal 协调语义；action 事件语义归交互域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ModalCoordinator TryCreateDescriptor ValidateModalDescriptorForBinding ResolveModalBindingComponents ReserveModalBindingIds"
  - repo: "GenerativeUI/A2UIRender"
    query: "ModalCoordinator UpdateModalPresentation PresentNativeDialog CloseTopActiveDialogForTransition HandleNativeDialogDismiss"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceSlot HandleSpecialRootBuildDescriptor Modal 描述符 HandlePendingModalDescriptors DismissActiveModal"
```

**关键文档：** `genui/src/main/cpp/components/A2UI/modal/ModalCoordinator.cpp`、`genui/src/main/cpp/components/A2UI/modal/ModalCoordinator.h`、`genui/src/main/cpp/SurfaceSlot.cpp`、`genui/src/main/ets/core/components/A2UI/A2UIModal.ets`