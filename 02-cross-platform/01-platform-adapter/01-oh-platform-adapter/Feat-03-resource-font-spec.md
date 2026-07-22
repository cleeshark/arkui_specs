# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 资源与字体适配 |
| 特性编号 | Func-02-01-01-Feat-03 |
| 所属 Epic | 跨平台适配层 |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 全新特性补录，无存量变更。本节跳过。

## 输入文档

- 源码路径：`adapter/ohos/osal/` + `adapter/ohos/capability/clipboard/` + `adapter/ohos/capability/interaction/`
- 设计文档：`02-cross-platform/01-platform-adapter/01-oh-platform-adapter/design.md`
- 无独立 requirement.md（已有实现补录）

## 用户故事

### US-1: ResourceManager 资源适配

作为一个 ACE 引擎开发者，我希望 ResourceAdapterImpl/V2 正确桥接 OHOS Global::Resource::ResourceManager，支持类型化资源查询、暗色模式检测和跨 bundle 资源访问。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN ResourceAdapterImpl::Init(resourceInfo) 被调用 THEN 初始化 resourceManager_、sysResourceManager_ 和 resConfig_ | 正常 |
| AC-1.2 | WHEN 调用 GetColor(resId) / GetDimension(resId) / GetString(resId) 等 THEN 通过 OHOS ResourceManager 查询对应类型资源 | 正常 |
| AC-1.3 | WHEN 调用 GetColorByName / GetDimensionByName 等按名称查询 THEN 通过名称而非 ID 查询资源 | 正常 |
| AC-1.4 | WHEN 调用 GetRawfile / GetRawFileData THEN 读取 rawfile 内容，支持跨 bundle 版本 | 正常 |
| AC-1.5 | WHEN 调用 GetMediaData(resId/name) THEN 读取媒体资源数据，支持跨 bundle 版本 | 正常 |
| AC-1.6 | WHEN 调用 UpdateResourceManager(bundleName, moduleName) THEN 切换到指定 bundle/module 的 ResourceManager | 正常 |
| AC-1.7 | WHEN ResourceAdapterImplV2::GetPatternByName THEN 通过 patternNameMap_ 查询 pattern 对应的 ThemeStyle | 正常 |
| AC-1.8 | WHEN ResourceAdapterImplV2::UpdateColorMode THEN 更新资源颜色模式（暗色/亮色） | 正常 |
| AC-1.9 | WHEN ResourceAdapterImplV2::ExistDarkResById/ByName THEN 检查指定资源是否存在暗色版本 | 正常 |
| AC-1.10 | WHEN ResourceAdapterImplV2::GetOverrideResourceAdapter THEN 创建配置化 override 适配器 | 正常 |
| AC-1.11 | WHEN ResourceConvertor::ConvertConfigToGlobal THEN 将 ResourceConfiguration 转换为 Global::Resource::ResConfig | 正常 |
| AC-1.12 | WHEN 多线程并发访问 THEN shared_mutex (resourceMutex_) 保证线程安全 | 边界 |

### US-2: FontManager 字体适配

作为一个 ACE 引擎开发者，我希望 RosenFontManager 正确实现字体权重缩放和系统字体加载，且 FontManager 基类提供完整的字体注册/加载/查询/观察者能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN VaryFontCollectionWithFontWeightScale(scale) 被调用 THEN 通过 RosenFontCollection::GetInstance().VaryFontCollectionWithFontWeightScale(scale) 变化字体集，并通知 VariationNodes | 正常 |
| AC-2.2 | WHEN LoadSystemFont 被调用 THEN 通过 RosenFontCollection::GetInstance().LoadSystemFont() 加载系统字体 | 正常 |
| AC-2.3 | WHEN FontManager::RegisterFont 被调用 THEN 注册指定字体族 | 正常 |
| AC-2.4 | WHEN FontManager::SetFontFamily 被调用 THEN 设置字体族并重建字体节点 | 正常 |
| AC-2.5 | WHEN FontManager::GetSystemFontList 被调用 THEN 返回系统字体列表 | 正常 |
| AC-2.6 | WHEN FontManager::UpdateFontWeightScale 被调用 THEN 更新权重缩放值并通知 VariationNodes | 正常 |
| AC-2.7 | WHEN FontManager::AddVariationNode/RemoveVariationNode THEN 添加/移除需要权重缩放通知的节点 | 正常 |
| AC-2.8 | WHEN FontManager::NotifyVariationNodes THEN 对所有 VariationNodes 通知字体变化 | 正常 |
| AC-2.9 | WHEN FontManager::RegisterTextEngineLoadCallback THEN 注册字体引擎加载回调 | 正常 |
| AC-2.10 | WHEN FontManager::UpdateStyleOptimizeFlagInCurrentLanguage THEN 更新当前语言下的样式优化标志 | 正常 |

### US-3: Clipboard 剪贴板适配

作为一个 ACE 引擎开发者，我希望 ClipboardImpl 正确桥接 OHOS MiscServices::PasteboardClient，支持多类型读写、同步/异步模式和自动填充检测。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN ClipboardImpl::SetData(text, copyOption, isDragData) THEN 写入文本到剪贴板，设置 CopyOptions(InApp/Local/Distributed) 和拖拽标志 | 正常 |
| AC-3.2 | WHEN ClipboardImpl::SetPixelMapData(pixmap, copyOption) THEN 写入 PixelMap 图像到剪贴板 | 正常 |
| AC-3.3 | WHEN ClipboardImpl::SetData(pasteDataMix, copyOption) THEN 写入混合 PasteData 到剪贴板 | 正常 |
| AC-3.4 | WHEN ClipboardImpl::GetData(callback, syncMode) THEN 从剪贴板读取文本，支持同步/异步模式 | 正常 |
| AC-3.5 | WHEN ClipboardImpl::GetPixelMapData(callback, syncMode) THEN 从剪贴板读取 PixelMap | 正常 |
| AC-3.6 | WHEN ClipboardImpl::GetData(textCb, pixelMapCb, urlCb, syncMode) THEN 读取多类型记录（逐条处理文本/PixelMap/URL） | 正常 |
| AC-3.7 | WHEN ClipboardImpl::GetSpanStringData(callback, syncMode) THEN 读取 SpanString（样式化字符串）数据 | 正常 |
| AC-3.8 | WHEN ClipboardImpl::HasData(callback) THEN 检查剪贴板是否有数据 | 正常 |
| AC-3.9 | WHEN ClipboardImpl::HasDataType(callback, mimeTypes) THEN 按 MIME 类型检查剪贴板数据，含自动填充检测 | 正常 |
| AC-3.10 | WHEN ClipboardImpl::Clear THEN 清空剪贴板 | 正常 |
| AC-3.11 | WHEN IsPasteFromAutoFill 检测 THEN 标识剪贴板数据来自自动填充 | 边界 |
| AC-3.12 | WHEN PasteDataImpl::GetPasteDataData THEN 延迟创建 OHOS MiscServices::PasteData | 正常 |
| AC-3.13 | WHEN MultiTypeRecordImpl::SetPlainText/SetPixelMap/SetHtmlText THEN 设置多类型记录各字段 | 正常 |
| AC-3.14 | WHEN ClipboardProxyImpl::GetClipboard THEN 创建 ClipboardImpl 实例 | 正常 |

### US-4: Drag 拖拽适配

作为一个 ACE 引擎开发者，我希望 InteractionImpl 正确桥接 OHOS Msdp::DeviceStatus::InteractionManager，支持拖拽生命周期、风格更新和跨设备协调。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN InteractionImpl::StartDrag(dragData, callback) THEN 将 DragDataCore 转换为 Msdp DragData，包装 StartDragListenerImpl，启动拖拽 | 正常 |
| AC-4.2 | WHEN InteractionImpl::StopDrag(result, callback) THEN 将 DragDropRet 转换为 Msdp DragDropResult，包装 StopDragListenerImpl，停止拖拽 | 正常 |
| AC-4.3 | WHEN InteractionImpl::UpdateShadowPic(shadowInfo) THEN 更新拖拽阴影 PixelMap | 正常 |
| AC-4.4 | WHEN InteractionImpl::SetDragWindowVisible(visible, rsTransaction) THEN 显示/隐藏拖拽窗口 | 正常 |
| AC-4.5 | WHEN InteractionImpl::UpdateDragStyle(style, eventId) THEN 更新拖拽光标风格(DEFAULT/FORBIDDEN/COPY/MOVE) | 正常 |
| AC-4.6 | WHEN InteractionImpl::UpdatePreviewStyle(previewStyle) THEN 更新拖拽预览样式 | 正常 |
| AC-4.7 | WHEN InteractionImpl::UpdatePreviewStyleWithAnimation(previewStyle, animation) THEN 更新预览样式并带动画参数 | 正常 |
| AC-4.8 | WHEN InteractionImpl::GetDragState THEN 返回当前拖拽状态(ERROR/START/STOP/CANCEL/MOTION_DRAGGING) | 正常 |
| AC-4.9 | WHEN InteractionImpl::GetDragSummary THEN 返回拖拽数据摘要 | 正常 |
| AC-4.10 | WHEN InteractionImpl::RegisterCoordinationListener THEN 注册跨设备协调监听器(CoordinationListenerImpl) | 正常 |
| AC-4.11 | WHEN InteractionImpl::UnRegisterCoordinationListener THEN 注销跨设备协调监听器 | 正常 |
| AC-4.12 | WHEN InteractionImpl::SetMouseDragMonitorState THEN 启用/禁用鼠标拖拽监视 | 正常 |

### US-5: Cursor 光标适配

作为一个 ACE 引擎开发者，我希望 MouseStyleOhos 正确桥接 OHOS MMI 设置光标类型（49+ 种）、自定义图标和可见性控制。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN MouseStyleOhos::SetPointerStyle(windowId, pointerStyle) THEN 将 MouseFormat(49+种) 转换为 MMI pointerStyle ID 并设置 | 正常 |
| AC-5.2 | WHEN MouseStyleOhos::GetPointerStyle(windowId) THEN 读取当前 MMI pointerStyle ID | 正常 |
| AC-5.3 | WHEN MouseStyleOhos::SetMouseIcon(windowId, style, pixelMap) THEN 设置自定义鼠标图标（支持 CONTEXT_MENU 和 ALIAS 样式） | 正常 |
| AC-5.4 | WHEN MouseStyleOhos::SetCustomCursor(windowId, focusX, focusY, pixelMap) THEN 设置自定义光标（带焦点偏移），使用 MMI::CustomCursor + CursorOptions | 正常 |
| AC-5.5 | WHEN MouseStyleOhos::SetUeaCustomCursor(hostWindowId, pixelMap, focusX, focusY) THEN 在 UIExtension 场景设置自定义光标（使用 host 窗口 ID） | 正常 |
| AC-5.6 | WHEN MouseStyleOhos::SetPointerVisible(style) THEN 设置光标可见性（CURSOR_NONE 时隐藏，其他时显示） | 正常 |
| AC-5.7 | WHEN UIExtension 场景 SetPointerStyle THEN 通过 token 获取真实 host 窗口 ID | 边界 |

### US-6: Picture/PixelMap OSAL

作为一个 ACE 引擎开发者，我希望 PictureOhos 和 PixelMapOhos 正确桥接 OHOS Media::Picture 和 Media::PixelMap，支持 HDR 组合、TLV 编码、缩放裁剪。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN PictureOhos::GetMainPixel THEN 返回主像素 PixelMap | 正常 |
| AC-6.2 | WHEN PictureOhos::GetAuxPicturePixelMap THEN 返回辅助像素 PixelMap | 正常 |
| AC-6.3 | WHEN PictureOhos::GetHdrComposedPixelMap THEN 返回 HDR 组合 PixelMap | 正常 |
| AC-6.4 | WHEN PixelMapOhos::GetWidth/GetHeight THEN 返回像素映射宽高 | 正常 |
| AC-6.5 | WHEN PixelMapOhos::GetPixels THEN 返回像素数据指针 | 正常 |
| AC-6.6 | WHEN PixelMapOhos::GetPixelFormat/GetAlphaType THEN 返回像素格式和透明类型 | 正常 |
| AC-6.7 | WHEN PixelMapOhos::IsHdr THEN 检查是否为 HDR 像素映射 | 正常 |
| AC-6.8 | WHEN PixelMapOhos::Scale THEN 缩放像素映射 | 正常 |
| AC-6.9 | WHEN PixelMapOhos::GetCropPixelMap THEN 返回裁剪后的像素映射 | 正常 |
| AC-6.10 | WHEN PixelMapOhos::EncodeTlv THEN 编码 TLV 格式 | 正常 |
| AC-6.11 | WHEN PixelMapOhos::WritePixels THEN 写入像素数据 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.12 | R-1~12 | TASK-F03-01 | 单测 | resource_adapter_impl.cpp |
| AC-2.1~2.10 | R-13~22 | TASK-F03-02 | 单测 | rosen_font_manager.cpp |
| AC-3.1~3.14 | R-23~36 | TASK-F03-03 | 单测+集成测试 | clipboard_impl.cpp |
| AC-4.1~4.12 | R-37~48 | TASK-F03-04 | 单测 | interaction_impl.cpp |
| AC-5.1~5.7 | R-49~55 | TASK-F03-05 | 单测 | mouse_style_ohos.cpp |
| AC-6.1~6.11 | R-56~66 | TASK-F03-06 | 单测 | picture_ohos.cpp, pixel_map_ohos.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ResourceAdapterImpl::Init | 初始化 resourceManager_+sysResourceManager_+resConfig_ | thread-safe shared_mutex | AC-1.1 |
| R-2 | 行为 | GetColor/GetDimension/GetString(resId) | 通过 OHOS ResourceManager 查询 | resId 为整数 ID | AC-1.2 |
| R-3 | 行为 | GetColorByName/GetDimensionByName | 通过名称查询 | 名称格式: bundle:module:type:name | AC-1.3 |
| R-4 | 行为 | GetRawfile/GetRawFileData | 读取 rawfile 内容 | 支持跨 bundle 版本 | AC-1.4 |
| R-5 | 行为 | GetMediaData(resId/name) | 读取媒体资源数据 | 支持跨 bundle 版本 | AC-1.5 |
| R-6 | 行为 | UpdateResourceManager(bundleName, moduleName) | 切换到指定 bundle/module ResourceManager | resourceManagers_ map 缓存 | AC-1.6 |
| R-7 | 行为 | ResourceAdapterImplV2::GetPatternByName | 通过 patternNameMap_ 查询 ThemeStyle | pattern 名称映射 | AC-1.7 |
| R-8 | 行为 | ResourceAdapterImplV2::UpdateColorMode | 更新颜色模式（暗色/亮色） | colorMode: 0=亮, 1=暗 | AC-1.8 |
| R-9 | 行为 | ExistDarkResById/ByName | 检查暗色版本存在 | appHasDarkRes_ flag | AC-1.9 |
| R-10 | 行为 | GetOverrideResourceAdapter | 创建配置化 override 适配器 | isOverrideResourceAdapter_=true | AC-1.10 |
| R-11 | 行为 | ResourceConvertor::ConvertConfigToGlobal | ResourceConfiguration→Global::Resource::ResConfig | 类型/方向/密度/颜色模式转换 | AC-1.11 |
| R-12 | 边界 | 多线程并发访问 | shared_mutex(resourceMutex_) 保护 | 读用 shared_lock, 写用 unique_lock | AC-1.12 |
| R-13 | 行为 | VaryFontCollectionWithFontWeightScale | RosenFontCollection::VaryFontCollectionWithFontWeightScale + NotifyVariationNodes | scale > 0 执行变化 | AC-2.1 |
| R-14 | 行为 | LoadSystemFont | RosenFontCollection::LoadSystemFont | 系统字体加载 | AC-2.2 |
| R-15 | 行为 | RegisterFont | 注册字体族 | 字体族名+文件路径 | AC-2.3 |
| R-16 | 行为 | SetFontFamily | 设置字体族并重建节点 | 触发 RebuildFontNode | AC-2.4 |
| R-17 | 行为 | GetSystemFontList | 返回系统字体列表 | 列表由系统配置 | AC-2.5 |
| R-18 | 行为 | UpdateFontWeightScale | 更新缩放值并通知 | scale 值变化驱动 | AC-2.6 |
| R-19 | 行为 | AddVariationNode/RemoveVariationNode | 添加/移除 VariationNode | NG 和旧管线各有方法 | AC-2.7 |
| R-20 | 行为 | NotifyVariationNodes | 通知所有节点字体变化 | NG 和旧管线各有方法 | AC-2.8 |
| R-21 | 行为 | RegisterTextEngineLoadCallback | 注册字体引擎加载回调 | 回调在字体加载完成时触发 | AC-2.9 |
| R-22 | 行为 | UpdateStyleOptimizeFlagInCurrentLanguage | 更新样式优化标志 | 影响行间距和标点溢出 | AC-2.10 |
| R-23 | 行为 | SetData(text, copyOption, isDragData) | 写入文本到剪贴板 | CopyOptions: InApp/Local/Distributed | AC-3.1 |
| R-24 | 行为 | SetPixelMapData(pixmap, copyOption) | 写入 PixelMap | CopyOptions 同上 | AC-3.2 |
| R-25 | 行为 | SetData(pasteDataMix, copyOption) | 写入混合 PasteData | PasteDataImpl→OHOS PasteData | AC-3.3 |
| R-26 | 行为 | GetData(callback, syncMode) | 读取文本 | syncMode: sync/async | AC-3.4 |
| R-27 | 行为 | GetPixelMapData(callback, syncMode) | 读取 PixelMap | syncMode 同上 | AC-3.5 |
| R-28 | 行为 | GetData(textCb, pixelMapCb, urlCb, syncMode) | 读取多类型记录 | 逐条 ProcessPasteDataRecord | AC-3.6 |
| R-29 | 行为 | GetSpanStringData(callback, syncMode) | 读取 SpanString | styled-string 支持 | AC-3.7 |
| R-30 | 行为 | HasData(callback) | 检查有数据 | 回调返回 bool | AC-3.8 |
| R-31 | 行为 | HasDataType(callback, mimeTypes) | 按 MIME 类型检查 | 含 IsPasteFromAutoFill | AC-3.9 |
| R-32 | 行为 | Clear | 清空剪贴板 | MiscServices::PasteboardClient::Clear | AC-3.10 |
| R-33 | 边界 | IsPasteFromAutoFill | 检测数据来自自动填充 | 自动填充粘贴有特殊处理 | AC-3.11 |
| R-34 | 行为 | PasteDataImpl::GetPasteDataData | 延迟创建 OHOS PasteData | 懒加载 | AC-3.12 |
| R-35 | 行为 | MultiTypeRecordImpl::SetPlainText/SetPixelMap/SetHtmlText | 设置多类型记录 | 支持4种MIME类型 | AC-3.13 |
| R-36 | 行为 | ClipboardProxyImpl::GetClipboard | 创建 ClipboardImpl | 工厂方法 | AC-3.14 |
| R-37 | 行为 | StartDrag(dragData, callback) | 转换 DragDataCore→Msdp DragData + StartDragListenerImpl | 启动拖拽会话 | AC-4.1 |
| R-38 | 行为 | StopDrag(result, callback) | 转换 DragDropRet→Msdp DragDropResult + StopDragListenerImpl + DragDropBehaviorReporter | 结束拖拽 | AC-4.2 |
| R-39 | 行为 | UpdateShadowPic(shadowInfo) | 更新拖拽阴影 | PixelMap 类型阴影 | AC-4.3 |
| R-40 | 行为 | SetDragWindowVisible(visible, rsTransaction) | 显示/隐藏拖拽窗口 | rsTransaction 用于同步 | AC-4.4 |
| R-41 | 行为 | UpdateDragStyle(style, eventId) | 更新光标风格 | DEFAULT/FORBIDDEN/COPY/MOVE | AC-4.5 |
| R-42 | 行为 | UpdatePreviewStyle(previewStyle) | 更新预览样式 | 角度/缩放等 | AC-4.6 |
| R-43 | 行为 | UpdatePreviewStyleWithAnimation(previewStyle, animation) | 更新预览+动画 | 动画参数控制过渡 | AC-4.7 |
| R-44 | 行为 | GetDragState | 返回当前拖拽状态 | ERROR/START/STOP/CANCEL/MOTION_DRAGGING | AC-4.8 |
| R-45 | 行为 | GetDragSummary | 返回数据摘要 | 概要+详细+格式+版本+大小+tag | AC-4.9 |
| R-46 | 行为 | RegisterCoordinationListener | 注册 CoordinationListenerImpl | 跨设备协调 | AC-4.10 |
| R-47 | 行为 | UnRegisterCoordinationListener | 注销协调监听 | 取消跨设备监听 | AC-4.11 |
| R-48 | 行为 | SetMouseDragMonitorState | 启用/禁用鼠标拖拽监视 | state: enable/disable | AC-4.12 |
| R-49 | 行为 | SetPointerStyle(windowId, style) | MouseFormat→MMI ID 并设置 | 49+种映射 | AC-5.1 |
| R-50 | 行为 | GetPointerStyle(windowId) | 读取 MMI ID | 返回当前光标类型 | AC-5.2 |
| R-51 | 行为 | SetMouseIcon(windowId, style, pixelMap) | 设置自定义图标 | 支持 CONTEXT_MENU/ALIAS | AC-5.3 |
| R-52 | 行为 | SetCustomCursor(windowId, focusX, focusY, pixelMap) | 设置自定义光标+焦点偏移 | MMI::CustomCursor+CursorOptions | AC-5.4 |
| R-53 | 行为 | SetUeaCustomCursor(hostWindowId, pixelMap, focusX, focusY) | UIExtension 自定义光标 | 使用 host 窗口 ID+token | AC-5.5 |
| R-54 | 行为 | SetPointerVisible(style) | 设置可见性 | CURSOR_NONE→隐藏, 其他→显示 | AC-5.6 |
| R-55 | 边界 | UIExtension 场景 SetPointerStyle | 通过 token 获取 host 窗口 ID | token→realHostWindowId | AC-5.7 |
| R-56 | 行为 | PictureOhos::GetMainPixel | 返回主像素 PixelMap | Media::Picture→PixelMap | AC-6.1 |
| R-57 | 行为 | PictureOhos::GetAuxPicturePixelMap | 返回辅助像素 | 辅图层像素 | AC-6.2 |
| R-58 | 行为 | PictureOhos::GetHdrComposedPixelMap | HDR 组合 | HDR 合成像素映射 | AC-6.3 |
| R-59 | 行为 | PixelMapOhos::GetWidth/Height | 返回宽高 | Media::PixelMap 尺寸 | AC-6.4 |
| R-60 | 行为 | PixelMapOhos::GetPixels | 返回数据指针 | 原始像素数据 | AC-6.5 |
| R-61 | 行为 | PixelMapOhos::GetPixelFormat/GetAlphaType | 返回格式和透明类型 | RGBA_8888 等格式 | AC-6.6 |
| R-62 | 行为 | PixelMapOhos::IsHdr | 检查 HDR | HDR 标志 | AC-6.7 |
| R-63 | 行为 | PixelMapOhos::Scale | 缩放 | x/y 缩放比例 | AC-6.8 |
| R-64 | 行为 | PixelMapOhos::GetCropPixelMap | 裁剪 | Rect 区域裁剪 | AC-6.9 |
| R-65 | 行为 | PixelMapOhos::EncodeTlv | TLV 编码 | 二进制序列化 | AC-6.10 |
| R-66 | 行为 | PixelMapOhos::WritePixels | 写入像素 | 数据缓冲写入 | AC-6.11 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.12 ResourceManager | 单测 | 双版本适配器、线程安全、暗色模式 |
| VM-2 | AC-2.1~2.10 FontManager | 单测 | 权重缩放、系统字体、VariationNodes |
| VM-3 | AC-3.1~3.14 Clipboard | 单测+集成测试 | 多类型读写、自动填充检测、同步/异步 |
| VM-4 | AC-4.1~4.12 Drag | 单测 | 拖拽生命周期、跨设备协调 |
| VM-5 | AC-5.1~5.7 Cursor | 单测 | 49+光标类型、自定义图标、UEA扩展 |
| VM-6 | AC-6.1~6.11 Picture/PixelMap | 单测 | HDR、TLV、缩放裁剪 |

## API 变更分析

N/A，本特性为框架内部适配层，无 SDK API 变更。

## 接口规格

### 接口定义

**ResourceAdapterImpl::GetColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Color ResourceAdapterImpl::GetColor(uint32_t resId)` |
| 返回值 | `Color` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**ClipboardImpl::SetData**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ClipboardImpl::SetData(const std::string& text, int32_t copyOption, bool isDragData)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**InteractionImpl::StartDrag**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void InteractionImpl::StartDrag(std::shared_ptr<DragDataCore> dragData, DragEndingCallback callback)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**MouseStyleOhos::SetPointerStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool MouseStyleOhos::SetPointerStyle(int32_t windowId, MouseFormat pointerStyle)` |
| 返回值 | `bool` — 是否成功设置 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** InnerApi

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双版本资源适配器并存 | ResourceAdapterImpl(V1) 和 ResourceAdapterImplV2(V2) 并存，V2增加 pattern/dark-mode/override | AC-1.7~1.10 |
| FontManager 权重缩放委托到 RosenFontCollection | RosenFontManager 仅实现2个抽象方法，其余40+方法在基类中 | AC-2.1~2.2 |
| Clipboard 同步/异步双路径 | GetDataSync(同步)/GetDataAsync(异步) 条件编译(SYSTEM_CLIPBOARD_SUPPORTED) | AC-3.4 |
| Drag 适配通过 InteractionManager 单例 | InteractionImpl 委托到 Msdp::DeviceStatus::InteractionManager::GetInstance() | AC-4.1~4.12 |
| Cursor 49+ MouseFormat→MMI ID 映射 | MouseFormat enum 值与 MMI pointerStyle ID 不一致，需转换表 | AC-5.1 |
| UIExtension 场景 Cursor 使用 host 窗口 ID | SetUeaCustomCursor 使用 hostWindowId+token | AC-5.5~5.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | ResourceAdapterImpl::GetColor ≤0.5ms | 单测计时 | resource_adapter_impl.cpp |
| 内存 | ClipboardImpl 持 PasteboardClient 代理 | 内存分析 | clipboard_impl.h |
| 安全 | Clipboard CopyOptions 控制分布式传播 | 权限检查 | clipboard_impl.cpp |
| 可测试性 | InteractionImpl 可通过 Mock InteractionManager 测试 | 单测 | interaction_impl.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | - | - | - |
| 平板 | 无差异 | - | - | - |
| 折叠屏 | Drag CoordinationListener 跨设备协调在折叠切换时可能触发 | CoordinationMessage 包含 networkId | 集成测试 | interaction_impl.cpp |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 适配层不直接影响 | N/A |
| 大字体 | 间接 | FontManager UpdateFontWeightScale 驱动大字体适配 | AC-2.6 |
| 深色模式 | 间接 | ResourceAdapterImplV2 ExistDarkResById/ByName 检查暗色资源 | AC-1.8~1.9 |
| 多窗口/分屏 | 否 | 适配层不直接影响多窗口 | N/A |
| 版本升级 | 否 | 适配层无版本差异 | N/A |
| 生态兼容 | 否 | 适配层为框架内部 | N/A |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围边界明确（5个子能力集群，全量覆盖）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "ResourceAdapterImpl 与 ResourceAdapterImplV2 双版本适配器的差异和 V2 的 pattern/dark-mode/override 能力"
  - repo: "openharmony/ace_engine"
    query: "RosenFontManager VaryFontCollectionWithFontWeightScale 权重缩放机制和 VariationNodes 通知链"
  - repo: "openharmony/ace_engine"
    query: "ClipboardImpl 多类型读写(GetData 多回调版) 和 IsPasteFromAutoFill 自动填充检测"
  - repo: "openharmony/ace_engine"
    query: "InteractionImpl StartDrag/StopDrag 拖拽生命周期和 CoordinationListener 跨设备协调"
  - repo: "openharmony/ace_engine"
    query: "MouseStyleOhos 49+ MouseFormat→MMI pointerStyle ID 映射表和 SetUeaCustomCursor UIExtension 场景"
```

**关键文档：** ace_engine `adapter/ohos/osal/` + `adapter/ohos/capability/clipboard/` + `adapter/ohos/capability/interaction/`
