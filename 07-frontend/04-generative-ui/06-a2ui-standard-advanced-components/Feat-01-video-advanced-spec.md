# 特性规格

> Func-07-04-06-Feat-01 Video 组件：固化 A2UI 标准 `Video` 组件的 `url` 属性解析（required、DynamicString 兼容 `path`/`call`/`value`）、视频格式白名单校验（`.mp4/.m4v/.mov/.webm/.mkv/.avi/.3gp/.mpeg/.mpg/.m3u8` 或 `data:video/` 前缀）、不支持格式「丢弃组件」行为，以及固定播放控制（`objectFit(Contain)`/`autoPlay(false)`/`controls(true)`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 标准协议高级组件 — Video 组件 |
| 特性编号 | Func-07-04-06-Feat-01 |
| 优先级 | P1 |
| 目标版本 | A2UI 原生协议 v0.9（API Version 20） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-06 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/06-a2ui-standard-advanced-components/design.md` | Baselined |
| 组件实现（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomVideo.ets` | — |
| 组件工具（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomComponentUtils.ets` | — |
| 组件工厂（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomComponentFactory.ets` | — |
| 组件 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Video.json` | — |
| 错误码（ArkTS） | `genui/src/main/ets/interface/Types.ets` | — |
| 组件文档参考 | `reference/standard-components/video.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: url 属性解析与必填校验

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎解析 Video 组件的 `url` 属性并校验其必填性,
**以便** 缺失或空 url 在解析期被拦截。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `url` 为合法非空 string（如 `"https://example.com/v.mp4"`） THEN `resolveVideoUrlProperty` 返回该 string（`CustomVideo.ets:86-88`） | 正常 |
| AC-1.2 | WHEN `url` 缺失（`customProps` 不含 `url` 键） THEN `resolveVideoOptionsForSchemaWarning` 记 `REQUIRED_MISS` warning「Property url is required」并返回默认 options（url=`''`）（`CustomVideo.ets:79-83,134-137`） | 异常 |
| AC-1.3 | WHEN `customProps` 为 undefined/null 或非对象 THEN `parseCustomProps` 返回 undefined，`resolveVideoOptionsForSchemaWarning` 记 `REQUIRED_MISS` 并返回默认 options（`CustomVideo.ets:133-138`、`CustomComponentUtils.ets:102-105`） | 异常 |
| AC-1.4 | WHEN `url` 为空 string（`""`） THEN 记 `INVALID_VALUE` warning「Property url expects non-empty string」并返回 undefined（`CustomVideo.ets:90-91`） | 边界 |

### US-2: 视频格式校验与组件丢弃

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎校验 url 是否为受支持的视频资源格式,
**以便** 不支持格式的组件被丢弃而非渲染失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN url 以白名单扩展名结尾（如 `x.mp4`/`x.m4v`/`x.mov`/`x.webm`/`x.mkv`/`x.avi`/`x.3gp`/`x.mpeg`/`x.mpg`/`x.m3u8`） THEN `isSupportedVideoUrl` 返回 true（`CustomVideo.ets:40-51,123-125`） | 正常 |
| AC-2.2 | WHEN url 以 `data:video/` 前缀开头 THEN `isSupportedVideoUrl` 返回 true（`CustomVideo.ets:124`、`CustomComponentUtils.ets:314-316`） | 边界 |
| AC-2.3 | WHEN url 含查询串/锚点（如 `x.mp4?t=1`/`x.mp4#frag`） THEN 剥离 `?`/`#` 后仍按扩展名匹配成功（`CustomComponentUtils.ets:318-325`） | 边界 |
| AC-2.4 | WHEN url 非空但格式不受支持 THEN 记 `INVALID_VALUE` warning「Property url expects a supported video resource format, drop current component」且 `renderContent=false`（组件丢弃）（`CustomVideo.ets:144-152`） | 异常 |

### US-3: 渲染行为与固定播放控制

**作为** 生成式 UI 宿主开发者,
**我想要** Video 组件渲染为 ArkUI Video 并遵循固定播放控制,
**以便** 视频以「有控制条、不自动播放」的方式呈现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `shouldRenderContent` 为 true THEN `build()` 渲染 `Column → Video({src: resolvedUrl})`（`CustomVideo.ets:175-192`） | 正常 |
| AC-3.2 | WHEN `renderContent=false`（url 不支持） THEN `build()` 不渲染任何内容节点（组件被丢弃）（`CustomVideo.ets:176,150-151`） | 异常 |
| AC-3.3 | WHEN 渲染 Video THEN 固定应用 `.objectFit(ImageFit.Contain)`、`.autoPlay(false)`、`.controls(true)`（`CustomVideo.ets:181-183`） | 正常 |
| AC-3.4 | WHEN 渲染 Video THEN 应用 `layoutWeight`（`resolveWeight`，weight>0 时返回 weight 否则 0）与 `margin`（`resolveMargin`）（`CustomVideo.ets:186-187,207-217`） | 正常 |
| AC-3.5 | WHEN 渲染 Video THEN 应用 `.accessibilityGroup(true)`、`.accessibilityText(label)`、`.accessibilityDescription(description)` 与 `.id(attribute.id)`（`CustomVideo.ets:188-191`） | 正常 |

### US-4: 动态值解析

**作为** 生成式 UI 宿主开发者,
**我想要** url 支持 DynamicString 语义（`path`/`call`/`value`/表达式）,
**以便** url 可绑定数据模型或函数调用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN url 为对象且含 `path` 或 `call`（string） THEN 经 `resolveDynamicStringOptionValue` 解析（`CustomVideo.ets:94-98`、`CustomComponentUtils.ets:224-243`） | 正常 |
| AC-4.2 | WHEN url 为对象且含 `value`（非空 string） THEN 记 `TYPE_MISMATCH` warning「object.value has been coerced」并返回 `value`（`CustomVideo.ets:100-109`） | 边界 |
| AC-4.3 | WHEN url 为对象但既非 `path`/`call` 也非合法 `value`（或 value 为空） THEN 记 `TYPE_MISMATCH`/`INVALID_VALUE` 并返回 undefined（`CustomVideo.ets:110-120`） | 异常 |

### US-5: schema warning 上报

**作为** 生成式 UI 宿主开发者,
**我想要** Video 配置异常经 schema warning 通道上报,
**以便** 宿主经 `registerErrorCallback` 感知组件问题。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 记 Video warning THEN `recordVideoWarning` 以 `itemType='component'`、`itemName='Video'` 调用 `SchemaErrorInfoManager.recordSchemaWarning`（`CustomVideo.ets:53-55`、`SchemaErrorInfoManager.ets:193-198`） | 正常 |
| AC-5.2 | WHEN 不支持 url 格式 THEN 上报 warning code 为 `ERROR_CODE_INVALID_VALUE`（`SchemaErrorCode.INVALID_VALUE`），对应宿主错误码 `SCHEMA_WARNING`=2001（`CustomVideo.ets:145-147`、`SchemaErrorInfoManager.ets:18`、`interface/Types.ets:71`） | 异常 |
| AC-5.3 | WHEN url 未知字段存在 THEN `recordUnknownFields(parsed, ['url'], 'Video', ...)` 记 `UNDEFINED_FIELD` warning（`CustomVideo.ets:140`、`SchemaLocalPropertyHelper.ets:511-525`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1,R-2 | T-1 | ArkTS 单测：`resolveVideoUrlProperty` | `CustomVideo.ets:72-121` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-3,R-4 | T-1 | ArkTS 单测：`isSupportedVideoUrl` + `resolveVideoOptionsForSchemaWarning` | `CustomVideo.ets:123-157` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-5 | T-1 | ohosTest：`BasicVideoProperty.test.ets`（Inspector 通道） | `CustomVideo.ets:175-217` |
| AC-4.1,AC-4.2,AC-4.3 | R-6 | T-1 | ArkTS 单测：`resolveDynamicStringOptionValue` 分支 | `CustomVideo.ets:94-120`、`CustomComponentUtils.ets:224-243` |
| AC-5.1,AC-5.2,AC-5.3 | R-7 | T-1 | ArkTS 单测/静态比对：`SchemaErrorCode` vs `SurfaceErrorCode` | `SchemaErrorInfoManager.ets:16-23`、`interface/Types.ets:71` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `url` 为非空 string | `resolveVideoUrlProperty` 返回该 string | 字符串长度 > 0 | AC-1.1 |
| R-2 | 异常 | `url` 缺失或空串或 customProps 无效 | 记 `REQUIRED_MISS`（缺失）/`INVALID_VALUE`（空串）并返回 undefined | required=true | AC-1.2,AC-1.3,AC-1.4 |
| R-3 | 行为 | url 满足视频扩展名白名单或 `data:video/` | `isSupportedVideoUrl` 返回 true | 剥离 `?`/`#` 后比较 | AC-2.1,AC-2.2,AC-2.3 |
| R-4 | 异常 | url 非空但格式不支持 | 记 `INVALID_VALUE`，`renderContent=false` 丢弃组件 | 组件不渲染 | AC-2.4 |
| R-5 | 行为 | `shouldRenderContent` 为 true | 渲染 ArkUI `Video`（Contain/不自动播放/有控制条） | weight>0 才生效 | AC-3.1,AC-3.3,AC-3.4,AC-3.5 |
| R-6 | 行为 | url 为 `{path}`/`{call}`/`{value}` 对象 | 动态解析；`value` 强转记 `TYPE_MISMATCH` | 对象非数组 | AC-4.1,AC-4.2,AC-4.3 |
| R-7 | 行为 | Video 配置异常 | 经 `SchemaErrorInfoManager` 上报 warning，宿主码 `SCHEMA_WARNING`=2001 | itemType=component,itemName=Video | AC-5.1,AC-5.2,AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 url 解析 | ArkTS 单测 | 非空 string/缺失/空串/customProps 无效 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 格式校验 | ArkTS 单测 | 白名单、`data:video/`、查询串剥离、丢弃 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 渲染 | ohosTest（Inspector） | Video 节点存在、固定播放控制 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 动态值 | ArkTS 单测 | path/call/value 三分支 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 warning | ArkTS 单测 + 静态比对 | SchemaErrorCode 与 2001 映射 |

## API 变更分析

> 存量补录，无新增/变更公开 API。本节列出受影响契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| A2UI `Video` 组件（`CustomVideo` 结构体） | 既有 | A2UI 视频展示 | 经 `CatalogItem.forComponent(...).markInnerNative(false)` 挂载 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| `VideoOptions`/`isSupportedVideoUrl`/`createVideoDefinition`（内部） | 既有 | 组件解析/注册 | 不直接暴露给宿主 | AC-1.1,AC-2.1,AC-5.1 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/CustomVideo.ets`（ArkTS 源即契约）；组件 DSL 契约 `components/Video.json`。Kit：`@arkui-genius/genui`；媒体能力依赖系统 `@kit.ArkUI`。权限：无。

## 接口规格

### 接口定义

**`resolveVideoUrlProperty(source, attribute, required)`（内部，`CustomVideo.ets:72`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `function resolveVideoUrlProperty(source: Record<string, Object>, attribute: CustomComponentAttribute | undefined, required: boolean = false): string | undefined` |
| 返回值 | `string` — 解析成功的 url；`undefined` — 缺失/空串/类型不符 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（返回 undefined，warning 走 `SchemaErrorCode`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-4.1,AC-4.2,AC-4.3 |

**`resolveVideoOptionsForSchemaWarning(attribute)`（`CustomVideo.ets:127`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `function resolveVideoOptionsForSchemaWarning(attribute: CustomComponentAttribute | undefined): VideoOptions` |
| 返回值 | `VideoOptions` — `{ url, renderContent }`；格式不支持时 `renderContent=false` |
| 开放范围 | 内部 |
| 错误码 | N/A（warning 经 `recordVideoWarning` 上报） |
| 关联 AC | AC-1.2,AC-1.3,AC-2.4,AC-5.1,AC-5.2,AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| source.url | string \| DynamicString | 是 | `''`（`DEFAULT_VIDEO_URL`） | 非空；满足视频扩展名白名单或 `data:video/` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | url 非空合法 string | 返回该 string | AC-1.1 |
| 2 | url 缺失 | `REQUIRED_MISS`，返回默认 options | AC-1.2,AC-1.3 |
| 3 | url 空串 | `INVALID_VALUE`，返回 undefined | AC-1.4 |
| 4 | url 格式不支持 | `INVALID_VALUE`，`renderContent=false` | AC-2.4 |
| 5 | url 为 `{path}`/`{call}` | 动态解析返回 string | AC-4.1 |
| 6 | url 为 `{value}` | `TYPE_MISMATCH` 强转返回 | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（组件 DSL 契约）；媒体组件 API 起始于 API Version 20。
- **API 版本号策略:** 组件经 `CatalogItem` 动态挂载，`schemaProvider` 按 `version` 加载 `components/Video.json`（`SchemaResourceLoader.loadA2UISchema`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 播放控制固定 | `objectFit(Contain)`/`autoPlay(false)`/`controls(true)` 写死，DSL 不可配置 | AC-3.3 |
| 组件丢弃语义 | 不支持格式记 warning 且不渲染（`renderContent=false`） | AC-2.4,AC-3.2 |
| 白名单校验 | 扩展名 + `data:video/` 前缀，剥离 `?`/`#` | AC-2.1,AC-2.2,AC-2.3 |
| warning 通道 | `recordVideoWarning` 固定 itemType=component,itemName=Video | AC-5.1,AC-5.2,AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 url 不抛异常，统一记 warning 并降级/丢弃 | ArkTS 单测 | `CustomVideo.ets:144-152` |
| 性能 | 格式校验为 O(扩展名数) 白名单比对，无网络探测 | 代码评审 | `CustomComponentUtils.ets:307-333` |
| 可测试性 | `resolveVideoOptionsForSchemaWarning` 纯函数可单测 | ArkTS 单测 | `CustomVideo.ets:127-157` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 渲染与格式校验设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 全屏/断点为 ArkUI Video 内部行为，本域不展开 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityGroup(true)` + `accessibilityText`/`accessibilityDescription` | AC-3.5 |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | Video 无主题态差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | `schemaProvider` 按协议版本加载 `Video.json` | 兼容性声明 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 `Video` 组件契约 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: A2UI 标准 Video 组件
  作为 生成式 UI 宿主开发者
  我想要 引擎解析 Video 的 url 并按固定播放控制渲染
  以便 非法或不受支持的 url 快速失败/丢弃

  Scenario: 合法 url 渲染 Video
    Given DSL 组件 { "component": "Video", "id": "v1", "url": "https://example.com/v.mp4" }
    When 引擎解析并渲染该组件
    Then 渲染 ArkUI Video（Contain/不自动播放/有控制条）

  Scenario Outline: 非法 url 丢弃组件
    Given DSL 组件 { "component": "Video", "url": <url> }
    When 引擎解析该组件
    Then 记 INVALID_VALUE warning 且组件不渲染

    Examples:
      | url |
      | "https://example.com/v.txt" |
      | "" |
      | "https://example.com/v.unknownext" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做 Video url 解析/校验/渲染；AudioPlayer 见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomVideo resolveVideoUrlProperty resolveVideoOptionsForSchemaWarning url 白名单 丢弃组件"
  - repo: "GenerativeUI/A2UIRender"
    query: "isSupportedMediaUrl VIDEO_SUPPORTED_EXTENSIONS data:video 前缀 查询串剥离"
  - repo: "GenerativeUI/A2UIRender"
    query: "SchemaErrorCode INVALID_VALUE SCHEMA_WARNING 2001 recordSchemaWarning itemName Video"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/CustomVideo.ets`、`genui/src/main/ets/core/components/A2UI/CustomComponentUtils.ets`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Video.json`、`genui/src/main/ets/interface/Types.ets`
