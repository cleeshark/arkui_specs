# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 资源访问公开能力（$r / $rawfile 解析与 Resource 对象构造） |
| 特性编号 | Func-03-03-01-Feat-02 |
| FuncID | 03-03-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 6 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 6 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `$r` / `$rawfile` 全局函数 | @since 6，构造 Resource 对象字面量 `{id, type, params}` |
| ADDED | 组件解析层 JSViewAbstract | @since 6，CompleteResourceObject / ParseDollarResource / GetResourceObject |
| ADDED | modifier 解析层 ArkTSUtils | @since 6，组件化 modifier 中 `$r` 解析与 ResourceObject 构造 |
| ADDED | Resource 接口与 ResourceStr/ResourceColor/Length 类型别名 | @since 9，bundleName/moduleName/id/params/type |
| ADDED | `@sys` / `@app` 资源名解析 | 系统资源 ID 偏移 SYSTEM_RES_ID_START，应用资源按名查找 |
| ADDED | C-API ResourceConverter | @since 12，NDK 类型联合体经 ResourceConverter 走同一解析逻辑 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/03-resource-theme/01-resource-access/design.md`
- **SDK 类型定义**:
  - `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/units.d.ts`（ResourceStr/ResourceColor/Length）

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 组件中使用 `$r` 引用资源

**角色**: 应用开发者
**期望**: 我想要在 ArkUI 组件代码中通过 `$r('app.type.name')` 引用 HAP 包资源
**价值**: 以便组件属性值随资源配置动态解析，支持深浅色与多语言切换

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 应用代码调用 `$r('app.string.title')` THEN 返回 Resource 对象字面量 `{id:'app.string.title', type:undefined, params:[]}`（`jsEnumStyle.js:1082-1084`） | 正常 |
| AC-1.2 | WHEN 组件属性接收该 Resource 对象 THEN `JSViewAbstract::CompleteResourceObject` 按 `RESOURCE_TOKEN_PATTERN=(app\|sys\|[\[.\]+?])\.(\S+?)\.(\S+)` 回填 bundleName/moduleName/数值 id 与 ResourceType（`js_view_abstract.cpp:6481,6439,119`） | 正常 |
| AC-1.3 | WHEN `ConvertResourceType` 解析类型 token THEN color/float/string/plural/pattern/boolean/integer/strarray/intarray/media 映射为对应 ResourceType 枚举（`js_view_abstract.cpp:6459`） | 正常 |
| AC-1.4 | WHEN `GetResourceObjectInternal` 构造 native 载体 THEN 调用 `MakeRefPtr<ResourceObject>(id, type, params, bundleName, moduleName, instanceId)`（`js_view_abstract.cpp:1865,1902`） | 正常 |
| AC-1.5 | WHEN 资源 token 为非法格式 THEN CompleteResourceObjectInner 回退默认值，不构造有效 ResourceObject（`js_view_abstract.cpp:6528`） | 异常 |

### US-2: modifier 中使用 `$r` 引用资源

**角色**: 应用开发者
**期望**: 我想要在 modifier 中直接使用 `$r` 引用资源并参与配置刷新
**价值**: 以便自定义属性修改器复用同一资源解析链路

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN modifier 侧收到 `$r` 产生的对象 THEN `ArkTSUtils::CompleteResourceObject` 回填 id/type/bundle/module（`arkts_utils.cpp:1065,1067`） | 正常 |
| AC-2.2 | WHEN `ArkTSUtils::GetResourceObject` 读取对象字段 THEN 分类 params 为 STRING/INT/FLOAT 并构造 `ResourceObject`（`arkts_utils.cpp:730,736,778`） | 正常 |
| AC-2.3 | WHEN modifier 桥接调用 `ParseJsResource`/`ParseJsColor`/`ParseJsMedia` THEN 走 ArkTSUtils 解析层与组件侧等价（`arkts_native_common_bridge.cpp:259`） | 正常 |

### US-3: 使用 `$rawfile` 引用原始文件

**角色**: 应用开发者
**期望**: 我想要通过 `$rawfile('path')` 引用 HAP 包 rawfile 资源
**价值**: 以便媒体/文件类组件直接读取打包的原始文件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 应用代码调用 `$rawfile('res.png')` THEN 返回 `{id:0, type:30000, params:['res.png']}`（30000=RAWFILE）（`jsEnumStyle.js:1086-1088`，`arkts_utils.h:60`） | 正常 |
| AC-3.2 | WHEN 组件侧解析 RAWFILE 类型 THEN `ParseJSMediaWithRawFile` 调用 `resourceAdapter->GetRawfile(fileName)` 返回文件路径（`js_view_abstract.cpp:7856,7868`） | 正常 |
| AC-3.3 | WHEN modifier 侧解析 RAWFILE 类型 THEN `ArkTSUtils::ParseJsMediaFromResource` 调用 `resourceAdapter->GetRawfile(...)`（`arkts_utils.cpp:2343,2356,2367`） | 正常 |
| AC-3.4 | WHEN C-API 侧解析 RAWFILE THEN `ResourceConverter::GetRawfilePath` 调用 `resAdapter_->GetRawfile`（`converter.cpp:414,418`） | 正常 |

### US-4: 系统资源与应用资源命名解析

**角色**: 应用开发者
**期望**: 我想要通过 `@sys.` / `@app.` 前缀分别引用系统资源与应用资源
**价值**: 以便组件能区分系统内置资源与 HAP 包自带资源

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 资源 id 以 `@sys.` 开头 THEN `ParseThemeIdReference` 将数值 id 加 `SYSTEM_RES_ID_START=0x7000000`（`theme_utils.cpp:32,49`） | 正常 |
| AC-4.2 | WHEN 资源 id 以 `@app.` 开头 THEN 按 `APP_TYPE_RES_NAME_REGEX=^@app\.(\w+)\.(\w+)$` 经 `GetResourceIdByName` 解析（`theme_utils.cpp:38,44,49`） | 正常 |
| AC-4.3 | WHEN 系统资源 id 未命中 THEN 回退到默认系统资源或空值，不抛异常 | 异常 |

### US-5: 类型别名支持字面量与 Resource 双形态

**角色**: 应用开发者
**期望**: 我想要在 `ResourceStr`/`ResourceColor`/`Length` 类型属性上传字面量或 `$r` 资源
**价值**: 以便同一属性既支持硬编码值也支持资源化

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 属性类型为 `ResourceColor` THEN 接受 number/Color/string/Resource（`ark_component/types/index.d.ts:25`） | 正常 |
| AC-5.2 | WHEN 属性类型为 `Length` THEN 接受 string/number/Resource/LengthMetrics（`ark_component/types/index.d.ts:52`） | 正常 |
| AC-5.3 | WHEN 属性类型为 `ResourceStr` THEN 接受 string/Resource（`ark_component/types/index.d.ts:579`） | 正常 |
| AC-5.4 | WHEN `ParseJs*` 收到对象分支 THEN 判定为 `$r` 产物并调用 CompleteResourceObject + GetResourceObject（`js_view_abstract.cpp:7389,7826`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-RES-02 | UT | `jsEnumStyle.js:1082` |
| AC-1.2 | R-1 | TASK-RES-02 | UT | `js_view_abstract.cpp:6481,6439` |
| AC-1.3 | R-2 | TASK-RES-02 | UT | `js_view_abstract.cpp:6459` |
| AC-1.4 | R-3 | TASK-RES-02 | UT | `js_view_abstract.cpp:1865,1902` |
| AC-1.5 | R-4 | TASK-RES-02 | UT | `js_view_abstract.cpp:6528` |
| AC-2.1 | R-5 | TASK-RES-02 | UT | `arkts_utils.cpp:1065` |
| AC-2.2 | R-3 | TASK-RES-02 | UT | `arkts_utils.cpp:730,778` |
| AC-2.3 | R-5 | TASK-RES-02 | UT | `arkts_native_common_bridge.cpp:259` |
| AC-3.1 | R-6 | TASK-RES-02 | UT | `jsEnumStyle.js:1086` |
| AC-3.2 | R-7 | TASK-RES-02 | UT | `js_view_abstract.cpp:7856` |
| AC-3.3 | R-7 | TASK-RES-02 | UT | `arkts_utils.cpp:2343` |
| AC-3.4 | R-7 | TASK-RES-02 | UT | `converter.cpp:414` |
| AC-4.1 | R-8 | TASK-RES-02 | UT | `theme_utils.cpp:32,49` |
| AC-4.2 | R-8 | TASK-RES-02 | UT | `theme_utils.cpp:38,49` |
| AC-4.3 | R-9 | TASK-RES-02 | UT | `theme_utils.cpp:49` |
| AC-5.1 | R-10 | TASK-RES-02 | UT | `ark_component/types/index.d.ts:25` |
| AC-5.2 | R-10 | TASK-RES-02 | UT | `ark_component/types/index.d.ts:52` |
| AC-5.3 | R-10 | TASK-RES-02 | UT | `ark_component/types/index.d.ts:579` |
| AC-5.4 | R-1 | TASK-RES-02 | UT | `js_view_abstract.cpp:7389,7826` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 组件中收到 `$r` 产生的对象 | CompleteResourceObject 按 token 正则回填 bundle/module/数值 id/type，再 GetResourceObject 构造 ResourceObject | token 须匹配 `(app\|sys\|[\[.\]+?])\.(\S+?)\.(\S+)` | AC-1.1~AC-1.4, AC-5.4 |
| R-2 | 行为 | ConvertResourceType 解析类型 token | 按已知类型字符串映射 ResourceType 枚举 | 未知 token 返回 NONE | AC-1.3 |
| R-3 | 行为 | GetResourceObject 读取对象字段 | 分类 params STRING/INT/FLOAT，MakeRefPtr<ResourceObject>(id,type,params,bundleName,moduleName,instanceId) | instanceId 取 CurrentIdSafely | AC-1.4, AC-2.2 |
| R-4 | 异常 | 资源 token 非法 | CompleteResourceObjectInner 回退默认值，不构造有效 ResourceObject | 无 | AC-1.5 |
| R-5 | 行为 | modifier 侧收到 `$r` 对象 | ArkTSUtils::CompleteResourceObject + GetResourceObject 走与组件侧等价逻辑 | 基于 panda Local<JSValueRef> | AC-2.1~AC-2.3 |
| R-6 | 行为 | 调用 `$rawfile(fileName)` | 返回 `{id:0,type:30000,params:[fileName]}` | type=30000=RAWFILE | AC-3.1 |
| R-7 | 行为 | 解析 RAWFILE 类型资源 | 经 ResourceAdapter::GetRawfile 返回文件路径 | 组件/modifier/C-API 三路径一致 | AC-3.2~AC-3.4 |
| R-8 | 行为 | 资源 id 以 `@sys.`/`@app.` 开头 | `@sys` id 加 SYSTEM_RES_ID_START=0x7000000；`@app` 按名 GetResourceIdByName | 系统资源与应用资源 ID 空间分离 | AC-4.1, AC-4.2 |
| R-9 | 异常 | 系统资源 id 未命中 | 回退默认系统资源或空值 | 无 | AC-4.3 |
| R-10 | 行为 | 属性类型为 ResourceColor/Length/ResourceStr | 接受字面量或 Resource 对象，对象分支走 $r 解析 | 无 | AC-5.1~AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | 组件侧 $r token 解析、CompleteResourceObject、GetResourceObject 构造、异常回退 |
| VM-2 | AC-2.1 ~ AC-2.3 | UT | modifier 侧 ArkTSUtils 解析等价性 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | $rawfile 字面量与三路径 GetRawfile 一致性 |
| VM-4 | AC-4.1 ~ AC-4.3 | UT | @sys/@app 命名空间解析与异常回退 |
| VM-5 | AC-5.1 ~ AC-5.4 | UT | 类型别名双形态与对象分支调度 |

## API 变更分析

> 本特性为已有实现补录，以下列出已有的公开和 InnerAPI 接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `$r(id, type, ...params)` | Public | string, [string], ...any | Resource | 无 | 构造资源引用对象字面量 | AC-1.1 |
| `$rawfile(fileName)` | Public | string | Resource | 无 | 构造 rawfile 引用对象字面量 | AC-3.1 |
| `JSViewAbstract::CompleteResourceObject` | InnerApi | JSRef<JSObject>& | void | 无 | 回填 Resource 对象 bundle/module/id/type | AC-1.2 |
| `JSViewAbstract::ParseDollarResource` | InnerApi | JSRef<JSObject>& | bool | 无 | 按 token 正则解析 $r 引用 | AC-1.2 |
| `JSViewAbstract::GetResourceObject` | InnerApi | const JSRef<JSObject>& | RefPtr<ResourceObject> | 无 | 构造 native ResourceObject | AC-1.4 |
| `ArkTSUtils::CompleteResourceObject` | InnerApi | EcmaVM*, Local<JSValueRef> | void | 无 | modifier 侧回填 Resource 对象 | AC-2.1 |
| `ArkTSUtils::GetResourceObject` | InnerApi | EcmaVM*, Local<JSValueRef> | RefPtr<ResourceObject> | 无 | modifier 侧构造 ResourceObject | AC-2.2 |
| `ResourceAdapter::GetRawfile(fileName)` | InnerApi | string | string | 无 | 返回 rawfile 文件路径 | AC-3.2~AC-3.4 |
| `ResourceConverter::GetRawfilePath` | InnerApi | Ark_Resource | string | 无 | C-API 侧 rawfile 解析 | AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `Resource` 接口 | MODIFIED | @since 9 新增 bundleName/moduleName/params/type 完整字段 | 优先使用完整 Resource 重载 | AC-1.1, AC-5.1~AC-5.3 |

## 兼容性声明

- **已有 API 行为变更:** 否，`$r`/`$rawfile` 行为自 API 6 保持一致
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 6
- **API 版本号策略:** @since 6（`$r`/`$rawfile`/解析层），@since 9（Resource 完整字段），@since 12（C-API ResourceConverter）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双解析层等价 | 组件 JSViewAbstract 与 modifier ArkTSUtils 解析逻辑等价，二者均构造 ResourceObject 传入 native | AC-1.4, AC-2.2 |
| `@ohos.resourceManager` 公开 SDK 不走本解析层 | 公开 SDK 接口为全球化资源管理子系统路径，不经 JSViewAbstract/ArkTSUtils；仅 `$r`/`$rawfile` 走本层 | AC-1.2, AC-2.1 |
| 系统与应用资源 ID 空间分离 | `@sys` 资源 id 加 SYSTEM_RES_ID_START=0x7000000，`@app` 按名查找 | AC-4.1, AC-4.2 |
| instanceId 隔离 | ResourceObject 携带 Container::CurrentIdSafely()，多实例资源互不干扰 | AC-1.4 |

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "JSViewAbstract CompleteResourceObject ParseDollarResource GetResourceObject $r parsing"
  - repo: "openharmony/arkui_ace_engine"
    query: "ArkTSUtils CompleteResourceObject GetResourceObject modifier $r parsing"
  - repo: "openharmony/arkui_ace_engine"
    query: "ResourceAdapter GetRawfile $rawfile resolution"
  - repo: "openharmony/arkui_ace_engine"
    query: "ThemeUtils ParseThemeIdReference @sys @app SYSTEM_RES_ID_START"
```

**关键文档:** design.md (`specs/03-engine-framework/03-resource-theme/01-resource-access/design.md`)
