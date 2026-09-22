# 特性规格

> Func-07-04-06-Feat-02 AudioPlayer 组件：固化 A2UI 标准 `AudioPlayer` 组件的 `url`（required）与 `description`（optional）属性解析、音频格式白名单校验（`.mp3/.m4a/.aac/.wav/.ogg/.oga/.flac/.amr/.opus` 或 `data:audio/` 前缀）、基于 `@kit.MediaKit` AVPlayer 的播放/暂停控制、跨组件独占播放协调（`AudioPlaybackCoordinator`）与加载竞态防护。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 标准协议高级组件 — AudioPlayer 组件 |
| 特性编号 | Func-07-04-06-Feat-02 |
| 优先级 | P1 |
| 目标版本 | A2UI 原生协议 v0.9（API Version 20） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-06 第二个 Feat，与 Feat-01 共享 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/06-a2ui-standard-advanced-components/design.md` | Baselined |
| 组件实现（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomAudioPlayer.ets` | — |
| 组件工具（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomComponentUtils.ets` | — |
| 组件工厂（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomComponentFactory.ets` | — |
| 组件 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/AudioPlayer.json` | — |
| 错误码（ArkTS） | `genui/src/main/ets/interface/Types.ets` | — |
| 组件文档参考 | `reference/standard-components/audioPlayer.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: url/description 属性解析

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎解析 AudioPlayer 的 `url`（必填）与 `description`（可选）属性,
**以便** 缺失/空/非法 url 与类型不符被拦截或降级。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `url` 为合法非空 string THEN `resolveAudioPlayerDynamicStringProperty` 返回该 string（`CustomAudioPlayer.ets:88-91`） | 正常 |
| AC-1.2 | WHEN `url` 缺失 THEN 记 `REQUIRED_MISS` warning「audioPlayer Property url is required」并返回 undefined（`CustomAudioPlayer.ets:81-85`） | 异常 |
| AC-1.3 | WHEN `url` 为空串 THEN 记 `INVALID_VALUE` warning 并返回 undefined（`CustomAudioPlayer.ets:88-93`） | 边界 |
| AC-1.4 | WHEN `description` 为任意 string（含空串）THEN 因 `allowEmpty=true` 返回该 string 且不记 warning（`CustomAudioPlayer.ets:88-90,104`） | 正常 |
| AC-1.5 | WHEN `description` 或 `url` 为 `{value}` 对象（非空 string）THEN 记 `TYPE_MISMATCH` 并强转返回；`{path}`/`{call}` 对象经 `resolveDynamicStringOptionValue` 解析（`CustomAudioPlayer.ets:96-114`） | 边界 |
| AC-1.6 | WHEN 含 url/description 之外未知字段 THEN `recordUnknownFields(parsed, ['url','description'], 'AudioPlayer', ...)` 记 `UNDEFINED_FIELD`（`CustomAudioPlayer.ets:187`） | 异常 |

### US-2: 音频格式校验与组件丢弃

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎校验 url 是否为受支持音频格式,
**以便** 不支持格式的组件被丢弃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN url 以音频白名单扩展名结尾（`.mp3/.m4a/.aac/.wav/.ogg/.oga/.flac/.amr/.opus`） THEN `isSupportedAudioUrl` 返回 true（`CustomAudioPlayer.ets:48-58,147-149`） | 正常 |
| AC-2.2 | WHEN url 以 `data:audio/` 前缀开头 THEN `isSupportedAudioUrl` 返回 true（`CustomAudioPlayer.ets:148`、`CustomComponentUtils.ets:314-316`） | 边界 |
| AC-2.3 | WHEN url 非空但格式不支持 THEN `normalizeAudioPlayerOptionsForSchemaWarning` 记 `INVALID_VALUE`、`url=''`、`renderContent=false`（组件丢弃）（`CustomAudioPlayer.ets:161-169`） | 异常 |

### US-3: AVPlayer 播放与状态同步

**作为** 生成式 UI 宿主开发者,
**我想要** AudioPlayer 经 AVPlayer 加载并播放音频,
**以便** 播放/暂停/加载态正确同步到 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `aboutToAppear` THEN `Register(playerId, {pause})` 注册独占控制器并 `prepareForCurrentUrl` 预载（`CustomAudioPlayer.ets:272-277`） | 正常 |
| AC-3.2 | WHEN `togglePlay` 且 AVPlayer 状态为 `prepared`/`paused`/`completed` THEN 先 `AudioPlaybackCoordinator.RequestActive(this.playerId)` 再 `play()` 并置 `isPlaying=true`（`CustomAudioPlayer.ets:436-441`） | 正常 |
| AC-3.3 | WHEN `togglePlay` 且状态为 `playing` THEN `pause()` 并置 `isPlaying=false`（`CustomAudioPlayer.ets:426-429`） | 正常 |
| AC-3.4 | WHEN `stateChange` 为 `prepared`/`paused`/`completed`/`playing` THEN `isLoading=false`、`isPrepared=true`（`CustomAudioPlayer.ets:517-520`） | 正常 |
| AC-3.5 | WHEN `stateChange` 为 `released`/`stopped`/`error` THEN `isPlaying=false`、`isPrepared=false`、`isLoading=false` 并 `ClearActive(this.playerId)`（`CustomAudioPlayer.ets:529-534`） | 异常 |

### US-4: 独占播放协调

**作为** 生成式 UI 宿主开发者,
**我想要** 多个 AudioPlayer 同时存在时仅一个活跃播放,
**以便** 新播放自动暂停前一播放器。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 新播放器 `RequestActive(playerId)` 且已存在其它活跃播放器 THEN 先 `await controller.pause()` 暂停旧播放器再置新为活跃（`CustomAudioPlayer.ets:240-247`） | 正常 |
| AC-4.2 | WHEN 组件 `aboutToDisappear` THEN `Unregister(playerId)` 并 `releasePlayer()`（`CustomAudioPlayer.ets:279-284`） | 正常 |
| AC-4.3 | WHEN `Unregister(playerId)` 且其当前为活跃 THEN `ClearActive(playerId)` 将 `activePlayerId` 置空（`CustomAudioPlayer.ets:235-238,250-254`） | 边界 |
| AC-4.4 | WHEN 玩家错误（`on('error')`） THEN `ClearActive`、`isPlaying=false`、`isPrepared=false`、`isLoading=false` 并 `dispatchRuntimeAudioWarning`（`CustomAudioPlayer.ets:537-547`） | 异常 |

### US-5: 加载态与竞态防护

**作为** 生成式 UI 宿主开发者,
**我想要** url 切换/预载时无竞态与卡死,
**以便** 加载态能正确收敛。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `prepareForCurrentUrl` 且 url 为空 THEN `isLoading=false` 并 `releasePlayer()`（`CustomAudioPlayer.ets:379-383`） | 边界 |
| AC-5.2 | WHEN url 快速切换 THEN `prepareSequence` 递增使旧序列请求被丢弃（`sequence !== prepareSequence` 即返回）（`CustomAudioPlayer.ets:376,395-410`） | 异常 |
| AC-5.3 | WHEN 等待 AVPlayer 进入目标态超时 THEN `waitForAnyPlayerState` 以 `PLAYER_STATE_TIMEOUT_MS=5000` 兜底返回 false（`CustomAudioPlayer.ets:45,626-629`） | 边界 |
| AC-5.4 | WHEN 预载完成且总耗时不足 `MIN_LOADING_VISIBLE_MS=400` THEN `waitForMinimumLoading` 补足剩余时长再结束 loading（`CustomAudioPlayer.ets:46,640-649`） | 边界 |
| AC-5.5 | WHEN `initPlayer` 失败 THEN `dispatchRuntimeAudioWarning('AudioPlayer url failed to initialize as an audio resource')` 并经 `SCHEMA_WARNING` 上报（`CustomAudioPlayer.ets:496-506,739-752`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2 | T-2 | ArkTS 单测：`resolveAudioPlayerDynamicStringProperty` | `CustomAudioPlayer.ets:71-123` |
| AC-2.1,AC-2.2,AC-2.3 | R-3,R-4 | T-2 | ArkTS 单测：`isSupportedAudioUrl` + `normalize*` | `CustomAudioPlayer.ets:147-171` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-5 | T-2 | ohosTest：`BasicAudioPlayerProperty.test.ets`（SymbolGlyph 物化） | `CustomAudioPlayer.ets:272-548` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-6 | T-2 | ArkTS 单测：`AudioPlaybackCoordinator` | `CustomAudioPlayer.ets:217-255` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-7,R-8 | T-2 | ArkTS 单测：`prepareForCurrentUrl`/`waitForAnyPlayerState` | `CustomAudioPlayer.ets:374-414,575-631` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `url` 非空 string / `description` 任意 string | 返回 string | url allowEmpty=false，description allowEmpty=true | AC-1.1,AC-1.4 |
| R-2 | 异常 | `url` 缺失/空串/未知字段 | 记 `REQUIRED_MISS`/`INVALID_VALUE`/`UNDEFINED_FIELD` 并返回 undefined | url required=true | AC-1.2,AC-1.3,AC-1.6 |
| R-3 | 行为 | url 满足音频扩展名白名单或 `data:audio/` | `isSupportedAudioUrl` 返回 true | 剥离 `?`/`#` 后比较 | AC-2.1,AC-2.2 |
| R-4 | 异常 | url 非空但格式不支持 | 记 `INVALID_VALUE`，`url=''`，`renderContent=false` 丢弃组件 | 组件不渲染 | AC-2.3 |
| R-5 | 行为 | `togglePlay`/`stateChange`/`error` 触发 | 同步 `isPlaying`/`isPrepared`/`isLoading` 并切换播放/暂停 | 播放前 RequestActive | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-6 | 行为 | 多实例并存或组件销毁 | 独占播放：新活跃暂停旧活跃，销毁 Unregister+release | 单活跃播放器 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-7 | 边界 | url 为空或切换 | 空 url→release；切换经 `prepareSequence` 防竞态 | 序列号递增 | AC-5.1,AC-5.2 |
| R-8 | 恢复 | 状态等待超时或 initPlayer 失败 | `PLAYER_STATE_TIMEOUT_MS=5000` 兜底；失败记 `SCHEMA_WARNING` | 最小 loading 400ms | AC-5.3,AC-5.4,AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 属性解析 | ArkTS 单测 | url 必填/allowEmpty、description 可选/可空 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 格式校验 | ArkTS 单测 | 音频白名单、`data:audio/`、丢弃 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 播放状态 | ohosTest（Inspector） | SymbolGlyph 物化、状态同步 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 独占播放 | ArkTS 单测 | RequestActive/Unregister/ClearActive |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 加载竞态 | ArkTS 单测 | 序列号防竞态、5000ms 超时、400ms 最小 loading |

## API 变更分析

> 存量补录，无新增/变更公开 API。本节列出受影响契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| A2UI `AudioPlayer` 组件（`CustomAudioPlayer` 结构体） | 既有 | A2UI 音频播放 | 经 `CatalogItem.forComponent(...).markInnerNative(false)` 挂载 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| `AudioPlayerOptions`/`AudioPlaybackCoordinator`/`createAudioPlayerDefinition`（内部） | 既有 | 组件解析/独占播放/注册 | 不直接暴露给宿主 | AC-1.1,AC-4.1 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/CustomAudioPlayer.ets`（ArkTS 源即契约）；组件 DSL 契约 `components/AudioPlayer.json`。Kit：`@arkui-genius/genui`；媒体能力依赖系统 `@kit.MediaKit`（AVPlayer）。权限：组件层无新增权限。

## 接口规格

### 接口定义

**`resolveAudioPlayerDynamicStringProperty(source, key, attribute, required, allowEmpty, propertyPath)`（内部，`CustomAudioPlayer.ets:71`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `function resolveAudioPlayerDynamicStringProperty(source: Record<string, Object>, key: string, attribute: CustomComponentAttribute | undefined, required?: boolean, allowEmpty?: boolean, propertyPath?: string): string | undefined` |
| 返回值 | `string` — 解析成功；`undefined` — 缺失/空串/类型不符 |
| 开放范围 | 内部 |
| 错误码 | N/A（warning 走 `SchemaErrorCode`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

**`resolveAudioPlayerOptionsForSchemaWarning(attribute)`（`CustomAudioPlayer.ets:173`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `function resolveAudioPlayerOptionsForSchemaWarning(attribute: CustomComponentAttribute | undefined): AudioPlayerOptions` |
| 返回值 | `AudioPlayerOptions` — `{ url, description, renderContent }` |
| 开放范围 | 内部 |
| 错误码 | N/A（warning 经 `recordAudioPlayerWarning` 上报） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.3 |

**`AudioPlaybackCoordinator.RequestActive(playerId)`（静态，`CustomAudioPlayer.ets:240`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static async RequestActive(playerId: string): Promise<void>` |
| 返回值 | `Promise<void>` — 暂停旧活跃播放器后设置新活跃 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| url | string \| DynamicString | 是 | `''`（`DEFAULT_AUDIO_URL`） | 非空（allowEmpty=false）；音频扩展名白名单或 `data:audio/` |
| description | string \| DynamicString | 否 | `''` | 任意 string（allowEmpty=true） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | url 非空合法 string | 返回 string | AC-1.1 |
| 2 | url 缺失 | `REQUIRED_MISS` | AC-1.2 |
| 3 | url 空串 | `INVALID_VALUE` | AC-1.3 |
| 4 | url 格式不支持 | `INVALID_VALUE`，`renderContent=false` | AC-2.3 |
| 5 | description 空串/非空 | 返回 string，不记 warning | AC-1.4 |
| 6 | 多实例播放 | 新活跃暂停旧活跃 | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（组件 DSL 契约）；媒体组件 API 起始于 API Version 20。
- **API 版本号策略:** 组件经 `CatalogItem` 动态挂载，`schemaProvider` 按 `version` 加载 `components/AudioPlayer.json`。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 独占播放 | `AudioPlaybackCoordinator` 保证单一活跃播放器，播放前暂停旧播放器 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| 组件丢弃语义 | 不支持格式记 warning 且不渲染（`renderContent=false`） | AC-2.3 |
| 白名单校验 | 音频扩展名 + `data:audio/` 前缀 | AC-2.1,AC-2.2,AC-2.3 |
| 竞态防护 | `prepareSequence` 序列号 + `PLAYER_STATE_TIMEOUT_MS=5000` 超时 | AC-5.2,AC-5.3 |
| warning 通道 | `recordAudioPlayerWarning` 固定 itemType=component,itemName=AudioPlayer | AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 播放失败/超时不抛异常，记 `SCHEMA_WARNING` 并复位状态 | ArkTS 单测 | `CustomAudioPlayer.ets:537-547,626-629` |
| 性能 | 加载态 16ms 帧延迟 + 最小 400ms 展示，避免闪烁 | 代码评审 | `CustomAudioPlayer.ets:46-47` |
| 可靠性 | url 快速切换经序列号防竞态，旧请求不覆盖新请求 | ArkTS 单测 | `CustomAudioPlayer.ets:376,395-410` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 播放控制与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityGroup(true)` + `accessibilityText`/`accessibilityDescription` | `CustomAudioPlayer.ets:309-311` |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 是 | 播放/加载图标颜色按 `componentTheme.colorMode`（`ThemeMode.DARK`）区分 | `CustomAudioPlayer.ets:719-725` |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | `schemaProvider` 按协议版本加载 `AudioPlayer.json` | 兼容性声明 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 `AudioPlayer` 组件契约 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: A2UI 标准 AudioPlayer 组件
  作为 生成式 UI 宿主开发者
  我想要 引擎解析 AudioPlayer 的 url/description 并经 AVPlayer 播放
  以便 非法 url 快速失败/丢弃，且仅一个播放器活跃

  Scenario: 合法 url 渲染播放按钮并播放
    Given DSL 组件 { "component": "AudioPlayer", "id": "a1", "url": "https://example.com/a.mp3" }
    When 引擎解析并渲染该组件
    Then 渲染 Stack+SymbolGlyph，点击后 RequestActive 并 play

  Scenario Outline: 非法 url 丢弃组件
    Given DSL 组件 { "component": "AudioPlayer", "url": <url> }
    When 引擎解析该组件
    Then 记 INVALID_VALUE warning 且组件不渲染

    Examples:
      | url |
      | "https://example.com/a.txt" |
      | "" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做 AudioPlayer 解析/播放/独占协调；Video 见 Feat-01）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomAudioPlayer resolveAudioPlayerDynamicStringProperty url description allowEmpty allowedAudioUrl 白名单"
  - repo: "GenerativeUI/A2UIRender"
    query: "AudioPlaybackCoordinator RequestActive ClearActive 独占播放 media.AVPlayer prepare"
  - repo: "GenerativeUI/A2UIRender"
    query: "prepareSequence 竞态 PLAYER_STATE_TIMEOUT_MS MIN_LOADING_VISIBLE_MS SCHEMA_WARNING 2001 dispatchRuntimeAudioWarning"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/CustomAudioPlayer.ets`、`genui/src/main/ets/core/components/A2UI/CustomComponentUtils.ets`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/AudioPlayer.json`、`genui/src/main/ets/interface/Types.ets`