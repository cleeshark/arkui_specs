from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from spec_eval.checks.reference_checks import ReferenceChecker
from spec_eval.checks.sdk_contract_checks import SdkContractChecker
from spec_eval.config import EvaluationConfig
from spec_eval.discovery.function_locator import FunctionLocator
from spec_eval.evidence.evidence_builder import FunctionEvidenceBuilder
from spec_eval.parser.citation_parser import CitationParser
from spec_eval.parser.markdown_parser import MarkdownParser


class EvidenceFixture:
    def __init__(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.oh_root = Path(self.temp.name) / "openharmony"
        self.repo_root = self.oh_root / "foundation" / "arkui" / "ace_engine"
        self.specs_root = self.repo_root / "specs"
        registry_root = self.specs_root / "registry"
        function_root = self.specs_root / "06-common-interface" / "01-test" / "01-sample"
        source_root = self.repo_root / "frameworks" / "core"
        sdk_root = self.oh_root / "interface" / "sdk-js" / "api" / "arkui"
        registry_root.mkdir(parents=True)
        function_root.mkdir(parents=True)
        source_root.mkdir(parents=True)
        sdk_root.mkdir(parents=True)
        self.spec_path = function_root / "Feat-01-sample-spec.md"
        self.design_path = function_root / "design.md"
        self.source_path = source_root / "sample.cpp"
        self.source_path.write_text("zero\none\ntwo\nthree\nfour\n", encoding="utf-8")
        (sdk_root / "sample.d.ts").write_text("declare function SampleApi(): void;\n", encoding="utf-8")
        functions = {
            "functions": [
                {
                    "id": "06-01-01",
                    "path": "06-common-interface/01-test/01-sample/",
                    "design": "06-common-interface/01-test/01-sample/design.md",
                    "status": "active",
                }
            ]
        }
        features = {
            "features": [
                {
                    "func_id": "06-01-01",
                    "id": "Feat-01",
                    "title": "sample",
                    "spec": "06-common-interface/01-test/01-sample/Feat-01-sample-spec.md",
                    "status": "Baselined",
                }
            ]
        }
        (registry_root / "functions.yaml").write_text(yaml.safe_dump(functions, allow_unicode=True), encoding="utf-8")
        (registry_root / "features.yaml").write_text(yaml.safe_dump(features, allow_unicode=True), encoding="utf-8")
        self.spec_path.write_text(
            """# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性名称 | sample |
| 特性编号 | Func-06-01-01-Feat-01 |
| 优先级 | P1 |
| 目标版本 | API 1 |
| 状态 | Baselined |
| 复杂度 | 标准 |
## 用户故事
### US-1: sample
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN input THEN output | 正常 |
## 验收追溯
| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-06-01-01-F1 | unit | `frameworks/core/sample.cpp:2-3` |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | input | output | `frameworks/core/sample.cpp:4` | AC-1.1 |
## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 | unit | output |
## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `SampleApi()` | Public | none | void | N/A | sample | AC-1.1 |
## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 可靠性 | stable | unit | `frameworks/core/sample.cpp:4` |
## 兼容性声明
- **已有 API 行为变更:** 否
## context-references
`frameworks/core/sample.cpp`
`frameworks/core/sample.cpp:99`
`/home/user/sample.cpp:1`
""",
            encoding="utf-8",
        )
        self.design_path.write_text(
            """# 架构设计
## 设计元数据
| 字段 | 内容 |
|---|---|
| Design ID | DESIGN-Func-06-01-01 |
| 目标 Feature | Feat-01 sample |
## 关键设计决策
| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---|---|---|---|---|---|
| ADR-1 | x | use sample | other | reason | behavior |
## 上下文和现状
### 调用链层级分析
| 层 | 模块 | 职责 | 修改类型 |
|---|---|---|---|
| 1 | SampleApi | dispatch | verify |
""",
            encoding="utf-8",
        )
        self.config = EvaluationConfig(
            repo_root=self.repo_root,
            specs_root=self.specs_root,
            oh_root=self.oh_root,
            functions_registry=registry_root / "functions.yaml",
            features_registry=registry_root / "features.yaml",
            rules_root=self.specs_root / "evaluation",
            schemas_root=self.specs_root / "evaluation" / "schemas",
            output_root=self.repo_root / "out",
        )
        self.context = FunctionLocator(self.config).locate("06-01-01")
        parser = MarkdownParser(self.config)
        self.documents = [parser.parse(path) for path in self.context.all_documents() if path.is_file()]

    def cleanup(self) -> None:
        self.temp.cleanup()


class Infra009To011Test(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = EvidenceFixture()

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def test_absolute_citation_path_keeps_line_range_separate(self) -> None:
        citation = CitationParser().parse("/home/user/sample.cpp:10-12")[0]
        self.assertEqual(citation.path, "/home/user/sample.cpp")
        self.assertEqual(citation.line_ranges, ((10, 12),))
        self.assertEqual(CitationParser().parse("WaterFlow/FlowItem creation"), [])

    def test_citation_parser_does_not_promote_embedded_slashes_to_absolute_paths(self) -> None:
        parser = CitationParser()
        false_positive_samples = (
            "`docs/architecture/Ace_Engine_Build_Architecture_Knowledge_Base_CN.md`",
            "调用 `build/hb/main.py` 完成构建",
            "生成 `arkoala-arkts/BUILD.gn`",
            "`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:25-55`",
            'python3 "${SOURCE_ROOT_DIR}/build/hb/main.py" build',
            "$(repo_root)/frameworks/core/sample.cpp:2-3",
            'deps = [ "//foundation/arkui/ace_engine:ace_engine" ]',
            "idlize_gen<br/>gen_obj/ohos_abc/idlize_gen/components.abc",
            "runScopedTask 使用 withInstanceId 实现同步/恢复（jsUIContext.js:2036-2043）",
        )
        for sample in false_positive_samples:
            with self.subTest(sample=sample):
                citations = parser.parse(sample)
                self.assertFalse(any(citation.path.startswith("/") for citation in citations), citations)

    def test_citation_parser_stops_repository_path_at_fullwidth_parenthesis(self) -> None:
        citations = CitationParser().parse(
            "Kit::FrameNode（interfaces/inner_api/ace_kit）为独立的布局/度量公开 C++ 接口通道"
        )
        self.assertEqual([citation.path for citation in citations], ["interfaces/inner_api/ace_kit"])

    def test_citation_parser_ignores_template_and_schematic_paths(self) -> None:
        parser = CitationParser()
        non_citation_samples = (
            "`adapter/{android,ios}/build`",
            "`frameworks/*/BUILD.gn`",
            "`adapter/<platform>/build/platform.gni`",
            'ADAPTER["frameworks/base<br/>ace_base_*"]',
            "participant ADP as adapter/platform.gni",
            "新平台必须提供 adapter/build/platform.gni；ArkUI-X 还需要额外配置",
        )
        for sample in non_citation_samples:
            with self.subTest(sample=sample):
                self.assertEqual(parser.parse(sample), [])

    def test_citation_parser_keeps_exact_directory_and_gn_target_paths(self) -> None:
        parser = CitationParser()
        directory = parser.parse("`adapter/ohos/build`")[0]
        target_directory = parser.parse("`adapter/android/build:libarkui_android`")[0]
        self.assertEqual(directory.path, "adapter/ohos/build")
        self.assertEqual(target_directory.path, "adapter/android/build")

    def test_citation_parser_keeps_exact_missing_file_candidates(self) -> None:
        parser = CitationParser()
        numbered = parser.parse("证据为 frameworks/core/missing.cpp:1")[0]
        unnumbered = parser.parse("证据为 `frameworks/core/missing.cpp`")[0]
        self.assertEqual(numbered.path, "frameworks/core/missing.cpp")
        self.assertEqual(numbered.line_ranges, ((1, 1),))
        self.assertEqual(unnumbered.path, "frameworks/core/missing.cpp")
        self.assertFalse(unnumbered.line_ranges)
        self.assertEqual(parser.parse("示意路径 frameworks/core/missing.cpp"), [])

    def test_citation_parser_expands_combined_header_source_extensions(self) -> None:
        parser = CitationParser()
        citations = parser.parse("`adapter/ohos/entrance/ace_container.h/cpp`")
        self.assertEqual(
            [citation.path for citation in citations],
            [
                "adapter/ohos/entrance/ace_container.h",
                "adapter/ohos/entrance/ace_container.cpp",
            ],
        )
        dotted = parser.parse("`adapter/ohos/entrance/ui_content_impl.hpp/.cc`")
        self.assertEqual(
            [citation.path for citation in dotted],
            [
                "adapter/ohos/entrance/ui_content_impl.hpp",
                "adapter/ohos/entrance/ui_content_impl.cc",
            ],
        )

    def test_citation_parser_preserves_valid_path_start_boundaries(self) -> None:
        parser = CitationParser()
        absolute = parser.parse("证据：`/home/user/sample.cpp:10-12`")[0]
        relative = parser.parse("证据：`frameworks/core/sample.cpp:2-3`")[0]
        self.assertEqual(absolute.path, "/home/user/sample.cpp")
        self.assertEqual(absolute.line_ranges, ((10, 12),))
        self.assertEqual(relative.path, "frameworks/core/sample.cpp")
        self.assertEqual(relative.line_ranges, ((2, 3),))

    def test_citation_parser_preserves_at_prefixed_sdk_names_without_nested_match(self) -> None:
        parser = CitationParser()
        short = parser.parse("`@ohos.arkui.UIContext.d.ts:5319`")
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].path, "@ohos.arkui.UIContext.d.ts")
        self.assertEqual(short[0].raw, "@ohos.arkui.UIContext.d.ts:5319")

        full = parser.parse("`interface/sdk-js/api/@ohos.arkui.UIContext.d.ts:5319`")
        self.assertEqual(len(full), 1)
        self.assertEqual(full[0].path, "interface/sdk-js/api/@ohos.arkui.UIContext.d.ts")

        internal = parser.parse("`interface/sdk-js/api/@internal/component/ets/enums.d.ts:1149`")
        self.assertEqual(len(internal), 1)
        self.assertEqual(internal[0].path, "interface/sdk-js/api/@internal/component/ets/enums.d.ts")

    def test_reference_checker_resolves_content_and_reports_invalid_evidence(self) -> None:
        result = ReferenceChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)
        rules = {item.rule_id for item in result.findings}
        self.assertNotIn("REF-NO-LINE-001", rules)
        self.assertIn("REF-LINE-RANGE-001", rules)
        self.assertIn("REF-ABSOLUTE-PATH-001", rules)
        resolved = next(item for item in result.citations if item.raw == "frameworks/core/sample.cpp:2-3")
        self.assertTrue(resolved.resolved)
        self.assertIn("2: one", resolved.content)
        self.assertIn("3: two", resolved.content)
        unnumbered = next(item for item in result.citations if item.raw == "frameworks/core/sample.cpp")
        self.assertTrue(unnumbered.resolved)
        self.assertFalse(unnumbered.line_ranges)

    def test_reference_checker_validates_exact_directories_and_skips_mermaid(self) -> None:
        self.fixture.spec_path.write_text(
            self.fixture.spec_path.read_text(encoding="utf-8")
            + "\n`frameworks/core`\n"
            + "`adapter/android/build`\n"
            + "```mermaid\n"
            + 'MISSING["adapter/ios/build"]\n'
            + "```\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = ReferenceChecker(self.fixture.config).run(self.fixture.context, documents)
        missing = [item for item in result.findings if item.rule_id == "REF-NOT-FOUND-001"]
        self.assertEqual([item.details.get("raw") for item in missing], ["adapter/android/build"])
        resolved_directory = next(item for item in result.citations if item.raw == "frameworks/core")
        self.assertTrue(resolved_directory.resolved)
        self.assertEqual(resolved_directory.source_path, "frameworks/core")
        self.assertFalse(any(item.raw == "adapter/ios/build" for item in result.citations))

    def test_reference_checker_resolves_chinese_wrapped_directory_and_sdk_root_relative_path(self) -> None:
        ace_kit = self.fixture.repo_root / "interfaces" / "inner_api" / "ace_kit"
        ace_kit.mkdir(parents=True)
        self.fixture.spec_path.write_text(
            self.fixture.spec_path.read_text(encoding="utf-8")
            + "\nKit::FrameNode（interfaces/inner_api/ace_kit）为独立接口通道\n"
            + "`api/arkui/sample.d.ts:1`\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = ReferenceChecker(self.fixture.config).run(self.fixture.context, documents)

        checked_raw = {"interfaces/inner_api/ace_kit", "api/arkui/sample.d.ts:1"}
        self.assertFalse(
            any(
                item.rule_id in ("REF-NOT-FOUND-001", "REF-ABSOLUTE-PATH-001")
                and item.details.get("raw") in checked_raw
                for item in result.findings
            )
        )
        resolved = {item.raw: item for item in result.citations if item.raw in checked_raw}
        self.assertTrue(resolved["interfaces/inner_api/ace_kit"].resolved)
        self.assertTrue(resolved["api/arkui/sample.d.ts:1"].resolved)
        self.assertTrue(resolved["api/arkui/sample.d.ts:1"].source_path.endswith("/interface/sdk-js/api/arkui/sample.d.ts"))

    def test_reference_checker_checks_each_combined_extension_file(self) -> None:
        (self.fixture.repo_root / "frameworks" / "core" / "sample.h").write_text("header\n", encoding="utf-8")
        (self.fixture.repo_root / "frameworks" / "core" / "partial.h").write_text("header\n", encoding="utf-8")
        self.fixture.spec_path.write_text(
            self.fixture.spec_path.read_text(encoding="utf-8")
            + "\n`frameworks/core/sample.h/cpp`\n"
            + "`frameworks/core/partial.h/cpp`\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = ReferenceChecker(self.fixture.config).run(self.fixture.context, documents)
        missing = [item for item in result.findings if item.rule_id == "REF-NOT-FOUND-001"]
        self.assertEqual([item.details.get("raw") for item in missing], ["frameworks/core/partial.cpp"])
        resolved_paths = {item.source_path for item in result.citations if item.resolved}
        self.assertIn("frameworks/core/sample.h", resolved_paths)
        self.assertIn("frameworks/core/sample.cpp", resolved_paths)
        self.assertIn("frameworks/core/partial.h", resolved_paths)

    def test_ambiguous_basename_requests_complete_repository_path(self) -> None:
        duplicate = self.fixture.repo_root / "adapter" / "test" / "sample.cpp"
        duplicate.parent.mkdir(parents=True)
        duplicate.write_text("duplicate\n", encoding="utf-8")
        self.fixture.spec_path.write_text(
            self.fixture.spec_path.read_text(encoding="utf-8") + "\n`sample.cpp:1`\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = ReferenceChecker(self.fixture.config).run(self.fixture.context, documents)

        finding = next(item for item in result.findings if item.rule_id == "REF-AMBIGUOUS-001")
        self.assertIn("source citation is ambiguous: `sample.cpp`", finding.message)
        self.assertIn("complete repository-relative path from the ace_engine root", finding.message)
        self.assertIn("`frameworks/.../sample.cpp`", finding.message)
        self.assertEqual(
            finding.details["required_path_style"],
            "complete repository-relative path from ace_engine root",
        )

    def test_sdk_declaration_basename_search_includes_openharmony_sdk(self) -> None:
        names = ("shared.d.ts", "shared.d.ets", "shared.static.d.ets")
        citations = []
        for name in names:
            local = self.fixture.repo_root / "frameworks" / "core" / name
            sdk = self.fixture.oh_root / "interface" / "sdk-js" / "api" / "arkui" / name
            local.write_text("declare const localValue: number;\n", encoding="utf-8")
            sdk.write_text("declare const sdkValue: number;\n", encoding="utf-8")
            citations.append(f"`{name}:1`")
        self.fixture.spec_path.write_text(
            self.fixture.spec_path.read_text(encoding="utf-8") + "\n" + "\n".join(citations) + "\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = ReferenceChecker(self.fixture.config).run(self.fixture.context, documents)

        for name in names:
            with self.subTest(name=name):
                finding = next(
                    item
                    for item in result.findings
                    if item.rule_id == "REF-AMBIGUOUS-001" and item.details.get("raw") == f"{name}:1"
                )
                self.assertIn(f"source citation is ambiguous: `{name}`", finding.message)
                self.assertIn(f"`interface/sdk-js/.../{name}`", finding.message)
                self.assertIn(f"`frameworks/.../{name}`", finding.message)
                self.assertEqual(finding.details["searched_roots"], ["ace_engine", "interface/sdk-js"])
                self.assertFalse(
                    any(
                        item.rule_id == "REF-LINE-RANGE-001" and item.line == finding.line
                        for item in result.findings
                    )
                )

    def test_at_prefixed_sdk_basename_excludes_localized_copy_and_resolves(self) -> None:
        name = "@ohos.arkui.UIContext.d.ts"
        api = self.fixture.oh_root / "interface" / "sdk-js" / "api" / name
        localized = self.fixture.oh_root / "interface" / "sdk-js" / "zh-cn" / "api" / name
        api.write_text("declare class UIContext {}\n", encoding="utf-8")
        localized.parent.mkdir(parents=True)
        localized.write_text("declare class UIContext {}\n", encoding="utf-8")
        self.fixture.spec_path.write_text(
            self.fixture.spec_path.read_text(encoding="utf-8")
            + f"\n`{name}:1`\n"
            + f"`interface/sdk-js/api/{name}:1`\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = ReferenceChecker(self.fixture.config).run(self.fixture.context, documents)

        self.assertFalse(
            any(
                item.rule_id in ("REF-AMBIGUOUS-001", "REF-NOT-FOUND-001")
                and "ohos.arkui.UIContext.d.ts" in item.details.get("raw", "")
                for item in result.findings
            )
        )
        short = next(
            item
            for item in result.citations
            if item.raw == f"{name}:1"
        )
        self.assertTrue(short.resolved)
        self.assertTrue(short.source_path.endswith(f"/interface/sdk-js/api/{name}"))
        full = next(
            item
            for item in result.citations
            if item.raw == f"interface/sdk-js/api/{name}:1"
        )
        self.assertTrue(full.resolved)

    def test_sdk_checker_locates_canonical_declaration(self) -> None:
        result = SdkContractChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)
        self.assertFalse(any(item.rule_id == "SDK-API-NOT-FOUND-001" for item in result.findings))
        declarations = [value for values in result.declarations.values() for value in values]
        self.assertTrue(any("SampleApi" in str(item["declaration"]) for item in declarations))

    def test_sdk_checker_matches_dollar_prefixed_public_apis(self) -> None:
        sdk = self.fixture.oh_root / "interface" / "sdk-js" / "api" / "arkui" / "resource.d.ts"
        sdk.write_text(
            "declare function $r(value: string): Resource;\n"
            "declare function $rawfile(value: string): Resource;\n",
            encoding="utf-8",
        )
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace(
                "| `SampleApi()` | Public | none | void | N/A | sample | AC-1.1 |",
                "| `SampleApi()` | Public | none | void | N/A | sample | AC-1.1 |\n"
                "| `$r(value)` | Public | string | Resource | N/A | resource | AC-1.1 |\n"
                "| `$rawfile(value)` | Public | string | Resource | N/A | rawfile | AC-1.1 |",
                1,
            ),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = SdkContractChecker(self.fixture.config).run(self.fixture.context, documents)

        missing = {item.details.get("api") for item in result.findings if item.rule_id == "SDK-API-NOT-FOUND-001"}
        self.assertNotIn("$r", missing)
        self.assertNotIn("$rawfile", missing)
        declarations = [item["declaration"] for values in result.declarations.values() for item in values]
        self.assertTrue(any("function $r(" in declaration for declaration in declarations))
        self.assertTrue(any("function $rawfile(" in declaration for declaration in declarations))

    def test_sdk_checker_locates_ndk_api_and_excludes_localized_header(self) -> None:
        ndk = self.fixture.oh_root / "interface" / "sdk_c" / "arkui" / "native" / "sample.h"
        localized = self.fixture.oh_root / "interface" / "sdk_c" / "zh-cn" / "arkui" / "native" / "localized.h"
        ndk.parent.mkdir(parents=True)
        localized.parent.mkdir(parents=True)
        ndk.write_text("int32_t OH_ArkUI_SampleNdkApi(void);\n", encoding="utf-8")
        localized.write_text("int32_t OH_ArkUI_LocalizedOnlyApi(void);\n", encoding="utf-8")
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace(
                "| `SampleApi()` | Public | none | void | N/A | sample | AC-1.1 |",
                "| `SampleApi()` | Public | none | void | N/A | sample | AC-1.1 |\n"
                "| `OH_ArkUI_SampleNdkApi()` | Public(NDK) | none | int32_t | N/A | ndk | AC-1.1 |\n"
                "| `OH_ArkUI_LocalizedOnlyApi()` | Public(NDK) | none | int32_t | N/A | localized | AC-1.1 |",
                1,
            ),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = SdkContractChecker(self.fixture.config).run(self.fixture.context, documents)

        missing = {item.details.get("api") for item in result.findings if item.rule_id == "SDK-API-NOT-FOUND-001"}
        self.assertNotIn("OH_ArkUI_SampleNdkApi", missing)
        self.assertIn("OH_ArkUI_LocalizedOnlyApi", missing)
        declarations = [item for values in result.declarations.values() for item in values]
        self.assertTrue(
            any(
                item["path"] == "interface/sdk_c/arkui/native/sample.h"
                and "OH_ArkUI_SampleNdkApi" in item["declaration"]
                for item in declarations
            )
        )
        self.assertFalse(any("interface/sdk_c/zh-cn/" in item["path"] for item in declarations))

    def test_sdk_checker_skips_internal_or_unclassified_rows_but_keeps_public_missing(self) -> None:
        self.fixture.spec_path.write_text(
            self.fixture.spec_path.read_text(encoding="utf-8")
            + "\n### SDK audit scope fixture\n"
            + "| API 名称 | 开放范围 | 功能描述 |\n"
            + "|---|---|---|\n"
            + "| `MissingPublicApi()` | Public | missing public |\n"
            + "| `ExplicitInnerApi()` | InnerApi | internal |\n"
            + "\n| API 名称 | 变更类型 | 影响场景 |\n"
            + "|---|---|---|\n"
            + "| `InternalThing::Update()` | MODIFIED | internal change |\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = SdkContractChecker(self.fixture.config).run(self.fixture.context, documents)

        missing = {item.details.get("api") for item in result.findings if item.rule_id == "SDK-API-NOT-FOUND-001"}
        self.assertIn("MissingPublicApi", missing)
        self.assertNotIn("ExplicitInnerApi", missing)
        self.assertNotIn("InternalThing", missing)
        self.assertNotIn("Update", missing)

    def test_sdk_checker_rejects_module_only_placeholder_and_requests_concrete_apis(self) -> None:
        module_file = self.fixture.oh_root / "interface" / "sdk-js" / "api" / "@ohos.arkui.StateManagement.d.ts"
        module_file.write_text("export declare class UIUtils {}\n", encoding="utf-8")
        self.fixture.spec_path.write_text(
            self.fixture.spec_path.read_text(encoding="utf-8")
            + "\n### Non-concrete SDK fixture\n"
            + "| API 签名 | 类型 | 功能描述 |\n"
            + "|---|---|---|\n"
            + "| （已有实现补录，API 通过 `@ohos.arkui.StateManagement` 模块暴露，具体签名见各 Feature spec） | Public | placeholder |\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = SdkContractChecker(self.fixture.config).run(self.fixture.context, documents)

        findings = [
            item
            for item in result.findings
            if item.rule_id == "SDK-API-NOT-FOUND-001"
            and item.details.get("non_concrete_api_entry") is True
        ]
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertIn("does not list concrete API names/signatures", finding.message)
        self.assertIn("enumerate each Public/System API explicitly", finding.message)
        self.assertEqual(finding.details["modules"], ["@ohos.arkui.StateManagement"])
        self.assertEqual(
            finding.details["required_content"],
            "concrete Public/System API names or signatures",
        )

    def test_evidence_builder_produces_function_scoped_claims(self) -> None:
        references = ReferenceChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)
        sdk = SdkContractChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)
        bundle = FunctionEvidenceBuilder().build(self.fixture.context, self.fixture.documents, references, sdk)
        by_id = {claim.claim_id: claim for claim in bundle.claims}
        self.assertIn("Feat-01/AC-1.1", by_id)
        self.assertIn("Feat-01/R-1", by_id)
        self.assertIn("design/ADR-1", by_id)
        self.assertEqual(by_id["Feat-01/AC-1.1"].evidence_status, "RESOLVED")
        api_claim = next(claim for claim in bundle.claims if claim.claim_type == "api")
        self.assertTrue(api_claim.sdk_declarations)
        self.assertGreater(bundle.metrics["claim_count"], 3)

    def test_legacy_trace_ac_header_still_builds_evidence(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace(
                "| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |",
                "| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |",
                1,
            ),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        references = ReferenceChecker(self.fixture.config).run(self.fixture.context, documents)
        sdk = SdkContractChecker(self.fixture.config).run(self.fixture.context, documents)
        bundle = FunctionEvidenceBuilder().build(self.fixture.context, documents, references, sdk)
        ac_claim = next(claim for claim in bundle.claims if claim.claim_id == "Feat-01/AC-1.1")
        self.assertEqual(ac_claim.evidence_status, "RESOLVED")


if __name__ == "__main__":
    unittest.main()
