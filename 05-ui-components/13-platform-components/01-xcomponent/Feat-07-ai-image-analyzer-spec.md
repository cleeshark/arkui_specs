# 特性规格

> Func-05-13-01-Feat-07 AI 图像分析（analyzer）：固化 NODE_XCOMPONENT_ENABLE_ANALYZER（@since 18）、OH_ArkUI_XComponent_StartImageAnalyzer/StopImageAnalyzer（@since 18，异步回调）、ArkUI_XComponent_ImageAnalyzerState 状态机、ArkTS Controller promise 路径，及类型限制（仅 SURFACE/TEXTURE）的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | AI 图像分析（analyzer） |
| 特性编号 | Func-05-13-01-Feat-07 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | @since 18 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ENABLE_ANALYZER 规格 | NODE_XCOMPONENT_ENABLE_ANALYZER set/get/reset（仅 SURFACE/TEXTURE） |
| ADDED | Start/Stop 规格 | OH_ArkUI_XComponent_Start/StopImageAnalyzer（异步，回调一次） + ArkTS promise |
| ADDED | 状态机规格 | ArkUI_XComponent_ImageAnalyzerState（FINISHED/DISABLED/UNSUPPORTED/ONGOING/STOPPED） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/13-platform-components/01-xcomponent/design.md` | Baselined |

---

## 用户故事

### US-1: 启用/禁用分析器

**作为** 应用开发者,
**我想要** 通过 ENABLE_ANALYZER 开关图像分析能力,
**以便** 在 XComponent 上启用 AI 识别。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `setAttribute(NODE_XCOMPONENT_ENABLE_ANALYZER, {i32:1})` 且 type=SURFACE/TEXTURE THEN EnableAnalyzer(true)，创建 ImageAnalyzerManager | 正常 |
| AC-1.2 | WHEN type=COMPONENT 或 NODE THEN set 为 no-op；get 返回 false | 边界 |
| AC-1.3 | WHEN `getAttribute(NODE_XCOMPONENT_ENABLE_ANALYZER)` THEN 返回 isEnableAnalyzer_（SURFACE/TEXTURE）；其它类型返回 false | 正常 |
| AC-1.4 | WHEN `resetAttribute(NODE_XCOMPONENT_ENABLE_ANALYZER)` THEN EnableAnalyzer(false)，DestroyAnalyzerOverlay | 正常 |
| AC-1.5 | WHEN set 参数非法（非 1 个） THEN 返回 ERROR_CODE_PARAM_INVALID(401) | 异常 |

### US-2: 启动/停止分析（NDK 异步回调）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `OH_ArkUI_XComponent_StartImageAnalyzer(node, userData, cb)` 且节点有效 + cb 非空 THEN 立即返回 ERROR_CODE_NO_ERROR(0)，结果经 cb 异步回调一次 | 正常 |
| AC-2.2 | WHEN 节点无效或 cb null THEN 返回 ERROR_CODE_PARAM_INVALID(401) | 异常 |
| AC-2.3 | WHEN 启动时 !isOnTree_ 或 !isEnableAnalyzer_ THEN cb(ARKUI_XCOMPONENT_AI_ANALYSIS_DISABLED=110000) | 边界 |
| AC-2.4 | WHEN !IsSupportImageAnalyzerFeature() THEN cb(UNSUPPORTED=110001) | 边界 |
| AC-2.5 | WHEN isNativeImageAnalyzing_==true（进行中） THEN cb(ONGOING=110002) | 边界 |
| AC-2.6 | WHEN 分析正常完成 THEN cb(FINISHED=0) 并清除 isNativeImageAnalyzing_ | 正常 |
| AC-2.7 | WHEN `OH_ArkUI_XComponent_StopImageAnalyzer(node)` THEN DestroyAnalyzerOverlay，返回 NO_ERROR(0) | 正常 |

### US-3: ArkTS Controller promise 路径

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `startImageAnalyzer(config, cb)` 且已分析中 THEN Promise reject(ONGOING=110002) | 边界 |
| AC-3.2 | WHEN inner controller 缺失 THEN onAnalyzed(STOPPED=110003) | 边界 |
| AC-3.3 | WHEN !IsSupportImageAnalyzerFeature() THEN reject(UNSUPPORTED=110001) | 边界 |
| AC-3.4 | WHEN 分析完成空错误 THEN Promise resolve（FINISHED）；有错则 reject(CreateAIError(state)) | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.x | R-1~R-3 | C-API 单测 | `style_modifier.cpp:9852-9877` |
| AC-2.x | R-4~R-8 | 代码评审 | `native_interface_xcomponent.cpp:490-519`, `xcomponent_pattern.cpp:2641-2682` |
| AC-3.x | R-9 | 代码评审 | `xcomponent_controller_peer_impl.cpp:35-70` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ENABLE_ANALYZER set=1 且 SURFACE/TEXTURE | EnableAnalyzer(true)，创建 Manager | @since 18 | AC-1.1 |
| R-2 | 边界 | type=COMPONENT/NODE | set no-op；get 返回 false | — | AC-1.2, AC-1.3 |
| R-3 | 行为/异常 | reset / 参数非法 | reset→EnableAnalyzer(false)+DestroyOverlay；非 1 参→401 | — | AC-1.4, AC-1.5 |
| R-4 | 行为 | StartImageAnalyzer 有效节点+cb | 立即返回 0，cb 异步回调一次 | — | AC-2.1 |
| R-5 | 异常 | 节点无效/cb null | 返回 401 | — | AC-2.2 |
| R-6 | 边界 | !onTree/!enabled | cb(DISABLED=110000) | — | AC-2.3 |
| R-7 | 边界 | !supported / 进行中 | cb(UNSUPPORTED=110001) / cb(ONGOING=110002) | — | AC-2.4, AC-2.5 |
| R-8 | 行为 | 完成/停止 | cb(FINISHED=0) 清除标志；Stop→DestroyOverlay 返回 0 | — | AC-2.6, AC-2.7 |
| R-9 | 行为 | ArkTS promise | 已分析中 reject ONGOING；缺 controller→STOPPED；!supported→UNSUPPORTED；完成 resolve | CreateAIError 映射 | AC-3.x |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.x, R-1~R-3 | C-API 单测 | ENABLE_ANALYZER 类型限制与 reset |
| VM-2 | AC-2.x, R-4~R-8 | 代码评审 | 异步回调一次与 5 态状态机 |
| VM-3 | AC-3.x, R-9 | 代码评审 | promise reject 映射 |

---

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| setAttribute(NODE_XCOMPONENT_ENABLE_ANALYZER) | Public（NDK @since 18） | i32 1/0 | ArkUI_ErrorCode | 401 | 开关分析器 | AC-1.1 |
| OH_ArkUI_XComponent_StartImageAnalyzer | Public（NDK @since 18） | node, userData, cb | ArkUI_ErrorCode | 0/401 | 启动分析（异步） | AC-2.1 |
| OH_ArkUI_XComponent_StopImageAnalyzer | Public（NDK @since 18） | node | ArkUI_ErrorCode | 0/401 | 停止分析 | AC-2.7 |

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

**OH_ArkUI_XComponent_StartImageAnalyzer(node, userData, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_XComponent_StartImageAnalyzer(ArkUI_NodeHandle, void* userData, void(*cb)(ArkUI_NodeHandle, ArkUI_XComponent_ImageAnalyzerState, void*))` |
| 返回值 | ArkUI_ErrorCode — 0=NO_ERROR |
| 开放范围 | Public（NDK） |
| 错误码 | PARAM_INVALID(401) |
| 关联 AC | AC-2.1, AC-2.2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效节点+cb | 返回 0，cb 异步回调一次（FINISHED/DISABLED/UNSUPPORTED/ONGOING/STOPPED） | AC-2.1 |
| 2 | !onTree/!enabled | cb(110000) | AC-2.3 |
| 3 | 进行中 | cb(110002) | AC-2.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** @since 18
- **类型限制:** 仅 SURFACE/TEXTURE 生效；COMPONENT/NODE set no-op、get false

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 仅 SURFACE/TEXTURE | COMPONENT/NODE 不支持 | AC-1.2 |
| 异步回调一次 | 每次启动恰一次 cb | AC-2.1 |
| 进行中拒绝 | ONGOING 状态 | AC-2.5 |
| SUPPORT_IMAGE_ANALYZER 编译开关 | 不支持时 IsSupport 返回 false | AC-2.4 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 分析延迟由 AI 服务决定，不设量化指标 | 集成测试 | `xcomponent_pattern.cpp` |
| 可测试性 | 状态机可经 Mock 验证 | 单测 | `xcomponent_utils.cpp:227-242` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | 集成测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | analyzer 为图像识别，不经无障碍树 | — |
| 其余 | 否 | — | — |

---

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN
- [x] 范围边界明确
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "XComponent NativeStartImageAnalyzer 异步回调一次与 5 态状态机门控"
  - repo: "openharmony/ace_engine"
    query: "ENABLE_ANALYZER 仅 SURFACE/TEXTURE 的类型守卫"
```

**关键文档：** `native_interface_xcomponent.h:78-89,868-881`、`style_modifier.cpp:9852-9877`、`xcomponent_pattern.cpp:2406-2682`
