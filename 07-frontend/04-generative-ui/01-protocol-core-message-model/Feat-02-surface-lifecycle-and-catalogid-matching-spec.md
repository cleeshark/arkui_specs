# 特性规格

> Func-07-04-01-Feat-02 Surface 生命周期与 catalogId 匹配：固化 Surface 的 create/update/delete 生命周期状态机、catalogId 大小写不敏感匹配决定标准/扩展协议模式（`isExtendedCatalog`）、最低支持 API 版本（20）门禁、`handleMessage` 中 native 字符串 errorCode 到 `SurfaceErrorCode` 枚举的映射链路。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Surface 生命周期与 catalogId 匹配 |
| 特性编号 | Func-07-04-01-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-02 承接 design.md 生命周期与错误码映射章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/01-protocol-core-message-model/design.md` | Baselined |
| 控制器实现 | `genui/src/main/ets/core/base/SurfaceControllerImpl.ets` | — |
| 目录能力 | `genui/src/main/ets/core/base/CapabilitiesCore.ets` | — |
| Surface 槽位 | `genui/src/main/cpp/SurfaceSlot.cpp` / `SurfaceSlot.h` | — |
| Surface 管理 | `genui/src/main/cpp/SurfaceManager.cpp` / `SurfaceManager.h` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 生命周期状态机

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎按 create→update*→delete 管理 Surface,
**以便** 正确绑定/解绑渲染资源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `handleMessage` 处理 `createSurface` 且成功 THEN `applySurfaceLifecycle` 对 CREATE_SURFACE 调用 `bindSurface`+`registerWarningEmitter`（`SurfaceControllerImpl.ets:287-294`） | 正常 |
| AC-1.2 | WHEN 处理 `deleteSurface` 且成功 THEN `applySurfaceLifecycle` 对 DELETE_SURFACE 调用 `unbindSurface`+`unregisterWarningEmitter`（`SurfaceControllerImpl.ets:295-298`） | 正常 |
| AC-1.3 | WHEN 处理 `updateComponents`/`updateDataModel` 消息 THEN `applySurfaceLifecycle` 不改变绑定（default 分支 no-op，`SurfaceControllerImpl.ets:299-300`） | 正常 |
| AC-1.4 | WHEN 消息处理成功后 THEN `notifyHandlingResult` 按 messageType 派发 `SURFACE_CREATED`/`SURFACE_COMPONENTS_UPDATED`/`SURFACE_DATA_MODEL_UPDATED`/`SURFACE_DELETED`（`SurfaceControllerImpl.ets:1089-1110`） | 正常 |
| AC-1.5 | WHEN 向已 `destroy` 的控制器发消息 THEN 直接返回 no-op（`destroyed` 守卫，`SurfaceControllerImpl.ets:683-687`） | 边界 |

### US-2: catalogId 匹配协议模式

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎按 catalogId 区分标准/扩展协议,
**以便** 走对应渲染路径。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `catalog.getCatalogId().toLowerCase() === 'ohos.a2ui.extended.catalog'.toLowerCase()` THEN `isExtendedCatalog` 返回 true（`SurfaceControllerImpl.ets:169-171`） | 正常 |
| AC-2.2 | WHEN catalogId 为 `https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json` THEN `isExtendedCatalog` 返回 false | 边界 |
| AC-2.3 | WHEN catalogId 大小写不一致（如 `OHOS.A2UI.EXTENDED.CATALOG`） THEN 因 toLowerCase 比较仍判定为扩展协议（`SurfaceControllerImpl.ets:170`） | 边界 |
| AC-2.4 | WHEN `createSurface` 缺少 `catalogId` 字段 THEN native 返回 `CATALOG_ID_MISSING`，`handleMessage` 映射为 `SCHEMA_CATALOG_ID_MISSING`(2106)（`SurfaceControllerImpl.ets:835-844`） | 异常 |

### US-3: 最低 API 版本门禁

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎在不支持的环境下降级,
**以便** 不稳定设备不被 native 渲染器误伤。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `deviceInfo.sdkApiVersion < 20`（`MIN_SUPPORTED_API_VERSION=20`）THEN 构造时 `apiSupported=false`，不初始化 native renderSlot（`SurfaceControllerImpl.ets:88,138-148`） | 边界 |
| AC-3.2 | WHEN `apiSupported=false` 时调用 `handleMessage` THEN 报 `NATIVE_PROCESS_FAILED`(1002) 且不调用 native（`SurfaceControllerImpl.ets:688-694`） | 边界 |
| AC-3.3 | WHEN `apiSupported=true` THEN 构造时执行 `initRenderSlot`+安装 action/schemaWarning/crossLanguageAttribute/runtimeError 四类 bridge（`SurfaceControllerImpl.ets:149-162`） | 正常 |

### US-4: 错误码映射链路

**作为** 生成式 UI 宿主开发者,
**我想要** native 处理失败映射到稳定错误码,
**以便** 宿主按枚举分类处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN native 返回 `processResult.success=false` 且 `errorCode='SURFACE_NOT_FOUND'` THEN 映射为 `NO_SURFACE_MATCHED`(1001)（`SurfaceControllerImpl.ets:845-855`） | 异常 |
| AC-4.2 | WHEN `processResult.undefined/null` THEN 映射为 `NATIVE_PROCESS_FAILED`(1002)（`SurfaceControllerImpl.ets:715-721`） | 异常 |
| AC-4.3 | WHEN `processResult.surfaceResultCode` 为多 Surface 策略码（`MULTI_SURFACE_DISABLED`/`MAX_SURFACE_LIMIT_REACHED`/`ALREADY_EXISTS`）THEN 走 `reportSurfacePolicyFailure`（`SurfaceControllerImpl.ets:856-862,677-681`） | 异常 |
| AC-4.4 | WHEN 未匹配任何已知 errorCode 字符串 THEN 兜底映射为 `NATIVE_PROCESS_FAILED`(1002)（`SurfaceControllerImpl.ets:863-870`） | 异常 |
| AC-4.5 | WHEN native 失败后 THFROM 若有待发 schema warning 则 `emitSchemaWarningsIfNeeded` 冲刷（`SurfaceControllerImpl.ets:761,852,868`） | 异常 |

### US-5: 根槽位绑定

**作为** 生成式 UI 宿主开发者,
**我想要** 控制器绑定到宿主 UI 节点,
**以便** native 渲染树挂载到宿主。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 首次 `bindToRender(rootSlot)` THEN 记录 `currentRootSlot` 并调 `NativeEngineBridge.bindSurfaceToRender`（`SurfaceControllerImpl.ets:945-966`） | 正常 |
| AC-5.2 | WHEN 重复绑定同一 rootSlot THEN no-op（`SurfaceControllerImpl.ets:954-957`） | 边界 |
| AC-5.3 | WHEN 绑定不同 rootSlot THEN 先记 rebind 再重新绑定（`SurfaceControllerImpl.ets:958-964`） | 正常 |
| AC-5.4 | WHEN `unbindFromRender(rootSlot)` 且 rootSlot 非当前（stale）THEN no-op（`SurfaceControllerImpl.ets:979-982`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-2 | ArkTS 单测：applySurfaceLifecycle/notifyHandlingResult | `SurfaceControllerImpl.ets:287-302,1089-1110` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-3 | T-2 | ArkTS 单测：isExtendedCatalog | `SurfaceControllerImpl.ets:169-171` |
| AC-3.1,AC-3.2,AC-3.3 | R-4 | T-2 | ArkTS 单测：apiSupported 门禁 | `SurfaceControllerImpl.ets:88,138-162` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-5 | T-2 | ArkTS 单测：错误码映射 | `SurfaceControllerImpl.ets:715-870` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-6 | T-2 | ArkTS 单测：bindToRender/unbind | `SurfaceControllerImpl.ets:945-986` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | create/delete 消息成功 | bind/unbind surface 路由 + 派发生命周期事件 | update 不改变绑定 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 边界 | 控制器已 destroy | handleMessage no-op | destroyed 幂等 | AC-1.5 |
| R-3 | 行为 | catalogId 匹配 | toLowerCase 比较 `ohos.a2ui.extended.catalog` 判扩展协议 | 缺失→2106 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-4 | 边界 | sdkApiVersion<20 | 不初始化 native，handleMessage 报 1002 | MIN_SUPPORTED_API_VERSION=20 | AC-3.1,AC-3.2,AC-3.3 |
| R-5 | 异常 | native 失败 | errorCode 字符串映射 SurfaceErrorCode 枚举 | 未匹配兜底 1002 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-6 | 行为 | 根槽位绑定 | 记录 currentRootSlot + native 绑定 | stale unbind no-op | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 生命周期 | ArkTS 单测 | bind/unbind + 事件派发 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 catalogId | ArkTS 单测 | 大小写不敏感、缺省 2106 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 API 门禁 | ArkTS 单测 | apiSupported=false 降级 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 错误码映射 | ArkTS 单测 | 全映射表覆盖 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 根槽位 | ArkTS 单测 | stale/重复绑定 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceController.handleMessage` | 既有 | 消息处理入口 | 生命周期由内部状态机管理 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| `SurfaceController.destroy` | 既有 | 资源释放 | 幂等 | AC-1.5 |
| `SurfaceController.bindToRender/unbindFromRender`（内部 Impl） | 既有 | 宿主节点挂载 | — | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

## 接口规格

### 接口定义

**`SurfaceControllerImpl.handleMessage(dsl)`（`SurfaceControllerImpl.ets:683`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `public handleMessage(dsl: string): void` |
| 返回值 | `void`（异步经 `onError`/`onSurfaceEvent` 回调通知） |
| 开放范围 | Public（ArkTS） |
| 错误码 | `NO_ERROR`/`NATIVE_PROCESS_FAILED`/`SCHEMA_*`/`NO_SURFACE_MATCHED`/多 Surface 策略码 |
| 关联 AC | AC-1.1,AC-3.2,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

**`isExtendedCatalog(catalog)`（`SurfaceControllerImpl.ets:169`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `private static isExtendedCatalog(catalog: CatalogImpl): boolean` |
| 返回值 | `boolean` — catalogId 是否等于 `ohos.a2ui.extended.catalog`（大小写不敏感） |
| 开放范围 | 内部 |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| dsl | string | 是 | — | 非空合法 JSON |
| catalogId | string | 是（createSurface） | — | basic/extended 之一 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | create 成功 | bind + SURFACE_CREATED | AC-1.1,AC-1.4 |
| 2 | delete 成功 | unbind + SURFACE_DELETED | AC-1.2,AC-1.4 |
| 3 | catalogId 扩展协议 | isExtend=true | AC-2.1 |
| 4 | 缺 catalogId | 2106 | AC-2.4 |
| 5 | api<20 | 1002 降级 | AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 设备 SDK API 20（`MIN_SUPPORTED_API_VERSION`）。
- **API 版本号策略:** 协议 v0.9；扩展协议 catalogId `ohos.a2ui.extended.catalog`。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 生命周期状态机 | create/delete 管绑定，update 无关 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| catalogId 大小写不敏感 | toLowerCase 比对 | AC-2.1,AC-2.2,AC-2.3 |
| 错误码双层映射 | native 字符串→ArkTS 枚举 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 低版本设备安全降级 | ArkTS 单测 | `SurfaceControllerImpl.ets:138-148` |
| 性能 | stale 绑定 no-op 避免重复挂载 | ArkTS 单测 | `SurfaceControllerImpl.ets:979-982` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 生命周期设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | — | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | 主题归 07-04-24 | — |
| 多窗口/分屏 | 否 | 多 Surface 见 Feat-06 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 20 门禁 | AC-3.1,AC-3.2,AC-3.3 |
| 生态兼容 | 是 | catalogId 大小写不敏感 | AC-2.1,AC-2.2,AC-2.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Surface 生命周期与 catalogId 匹配
  作为 生成式 UI 宿主开发者
  我想要 引擎按 create→update→delete 管理 Surface 并按 catalogId 选协议
  以便 正确绑定渲染资源

  Scenario: 创建 Surface 绑定
    Given 收到 createSurface 且处理成功
    When applySurfaceLifecycle(CREATE_SURFACE)
    Then bindSurface + registerWarningEmitter + 派发 SURFACE_CREATED

  Scenario: 扩展协议目录识别
    Given catalogId = "OHOS.A2UI.EXTENDED.CATALOG"
    When isExtendedCatalog
    Then 返回 true（toLowerCase 比较）
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（组件语法归 07-04-02~24）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceControllerImpl applySurfaceLifecycle notifyHandlingResult 生命周期事件"
  - repo: "GenerativeUI/A2UIRender"
    query: "isExtendedCatalog ohos.a2ui.extended.catalog catalogId 匹配"
  - repo: "GenerativeUI/A2UIRender"
    query: "handleMessage errorCode 映射 SurfaceErrorCode SCHEMA_*"
```

**关键文档：** `genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/cpp/SurfaceSlot.cpp`、`genui/src/main/cpp/SurfaceErrorCodes.h`