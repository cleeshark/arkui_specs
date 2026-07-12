# ArkUI Specs Agent Quick Guide

This repository is an ArkUI ace_engine feature specification repository. It is not a runnable application project. The main maintenance task is keeping `registry/`, the Markdown documents on disk, and the generated `index.md` consistent.

## What Matters

- `registry/functions.yaml` is the source of truth for FuncID functional domains.
- `registry/features.yaml` is the source of truth for FeatID feature specs.
- `index.md` is generated output. Do not edit it by hand.
- `tools/generate_index.py` validates the registry and regenerates `index.md`.
- `tools/generate_site.py` generates Docusaurus inputs from the registry.
- `site/docs`, `site/sidebars.js`, and `site/src/data/registry.json` are generated site inputs. Do not edit them by hand.
- A functional-domain directory usually contains one `design.md` and one or more `Feat-NN-*-spec.md` files.

Typical layout:

```text
<L1>/<L2>/<L3>/
  design.md
  Feat-01-xxx-spec.md
  Feat-02-yyy-spec.md
```

## Required Commands

After changing registry entries or registered document paths, run:

```bash
python3 tools/generate_index.py
python3 tools/generate_index.py --check
python3 tools/generate_site.py
```

Before finishing a change, use this optional consistency check to find unregistered files and broken registered paths:

```bash
python3 - <<'PY'
import yaml
from pathlib import Path

root = Path('.')
funcs = yaml.safe_load((root / 'registry/functions.yaml').read_text(encoding='utf-8'))['functions']
features = yaml.safe_load((root / 'registry/features.yaml').read_text(encoding='utf-8'))['features']

registered_designs = {f.get('design') for f in funcs if f.get('design')}
registered_specs = {f.get('spec') for f in features if f.get('spec')}
designs = {str(p) for p in root.rglob('design.md') if '.git' not in p.parts}
specs = {str(p) for p in root.rglob('Feat-*.md') if '.git' not in p.parts}

print('unregistered_designs', sorted(designs - registered_designs))
print('unregistered_specs', sorted(specs - registered_specs))

missing = []
for func in funcs:
    if func.get('design') and not (root / func['design']).is_file():
        missing.append(('design', func['id'], func['design']))
for feature in features:
    if feature.get('spec') and not (root / feature['spec']).is_file():
        missing.append(('spec', feature['func_id'] + '/' + feature['id'], feature['spec']))
print('missing_registered_paths', missing)
PY
```

## Spec Content Validation

`tools/validate_specs.py` checks the spec documents themselves (not the registry). It is the specs-repo counterpart of the spec checks in `docs/validate_context.py`, so a Feat spec passes or fails identically under either tool. The generated `site/` tree is excluded from the scan.

```bash
python3 tools/validate_specs.py              # print every finding
python3 tools/validate_specs.py --quiet      # print only the summary
python3 tools/validate_specs.py --warnings-as-errors
```

It reports:

- `index.md`: every registered Spec link resolves to an existing file; every `| Feat-` row has at least four columns and a valid status (`Draft` / `Baselined` / `Deprecated`); `待补充` rows are warnings.
- Each `Feat-NN-*-spec.md`: a valid `| 状态 | <status> |` row (or `status:` header); an overview metadata table with the required fields `特性名称` / `特性编号` / `优先级` / `目标版本` / `复杂度` (plus `状态`), where `特性编号` matches `Func-NN-NN-NN-Feat-NN` and `优先级` is `P0`–`P3`; a `## context-references` section; at least one `AC-<n>` marker; at least one `VM-<n>` marker; when `Baselined`, no `TODO` / `TBD` / `待定` placeholder text (self-audit lines are recognized and skipped); and in the `## 本次变更范围（Delta）` section, every table must use the exact header `| 类型 | 内容 | 说明 |` with `类型` cells being `ADDED` / `MODIFIED` / `REMOVED`.

A few legacy specs predate the current template and currently trip this check (missing status row, missing VM entries, etc.). Treat new errors as real and fix the spec rather than relaxing the rule; `--quiet` returns a non-zero exit code only when errors remain.

## Adding Content

### Add A Functional Domain

1. Add one `functions` entry to `registry/functions.yaml`.
2. Use a three-part FuncID: `L1-L2-L3`, for example `05-08-01`.
3. Set `path` to the real directory path. Directory names should use lowercase English slugs with hyphens.
4. If `design.md` exists, set `design` to its path. If it does not exist yet, set `design: null`.
5. Run the required generation and check commands.

Minimal example:

```yaml
- id: 05-08-01
  l1:
    id: '05'
    title: Component Layer
  l2:
    id: '08'
    title: Image Components
  l3:
    id: '01'
    title: Image
  path: 05-ui-components/08-image-components/01-image/
  design: 05-ui-components/08-image-components/01-image/design.md
  status: active
```

When editing existing Chinese registry titles, preserve the existing language unless the task explicitly asks for translation. The example above is illustrative; the current registry mostly uses Chinese titles.

### Add A Feature Spec

1. Confirm that the target FuncID already exists in `registry/functions.yaml`.
2. Create or confirm the `Feat-NN-xxx-spec.md` file.
3. Add one entry to `registry/features.yaml`.
4. FeatIDs under the same FuncID must be contiguous from `Feat-01`; do not skip numbers.
5. If the spec file exists, set `spec` to its path. For a placeholder entry, use `spec: null`, usually with `status: 待补充`.
6. Run the required generation and check commands.

Example:

```yaml
- func_id: 05-08-01
  id: Feat-05
  title: Image component base memory optimization
  spec: 05-ui-components/08-image-components/01-image/Feat-05-image-base-memory-opt-spec.md
  status: Draft
```

Common status values:

- `待补充`: The work is known, but the spec has not landed yet.
- `Draft`: Draft spec or not yet baselined.
- `Baselined`: Reviewed and baselined.
- `Deprecated`: Kept for history but replaced or obsolete.

## Updating Content

### Update Design Or Spec Text

- If only Markdown body text changes, registry updates are usually not needed.
- If a feature title, status, file path, or FeatID changes, update `registry/features.yaml`.
- If a functional-domain title, directory path, or design path changes, update `registry/functions.yaml`.
- Regenerate `index.md` after registry changes.
- Regenerate site inputs after registry changes with `python3 tools/generate_site.py`.

## Docusaurus Site

The static site lives under `site/` and is deployed by `.github/workflows/deploy-pages.yml` using GitHub Pages.

Source files to edit:

- `site/docusaurus.config.js`
- `site/src/pages/index.js`
- `site/src/css/custom.css`
- `site/package.json`
- `site/package-lock.json`
- `tools/generate_site.py`
- `.github/workflows/deploy-pages.yml`

Generated files and directories:

- `site/docs/`
- `site/sidebars.js`
- `site/src/data/registry.json`
- `site/build/`
- `site/.docusaurus/`
- `site/node_modules/`

Local build flow:

```bash
python3 tools/generate_index.py --check
python3 tools/generate_site.py
cd site
npm ci
npm run build
```

GitHub Pages deployment flow:

```text
push to main
  -> validate registry index
  -> generate Docusaurus inputs
  -> install site dependencies
  -> build static site
  -> deploy Pages artifact
```

The site sidebar is registry-driven. Do not hand-maintain navigation; update registry and rerun the generator instead.

### Rename A Directory Or File

1. Rename the real directory or file.
2. Update `path` / `design` in `registry/functions.yaml`.
3. Update `spec` in `registry/features.yaml`.
4. Run `python3 tools/generate_index.py`.
5. Check that `missing_registered_paths` is empty.

## Deleting Content

First decide whether deletion is really appropriate.

- For baselined or historically valid specs, prefer changing status to `Deprecated` instead of deleting.
- For drafts, mistaken registrations, or not-started placeholders, deleting the registry entry and document can be acceptable.
- Before deleting a FuncID, delete or migrate every feature entry that references it.
- Deleting a middle FeatID under one FuncID breaks the contiguous sequence rule. If deletion is required, renumber later FeatIDs and update file names and references.

After deletion, run:

```bash
python3 tools/generate_index.py
python3 tools/generate_index.py --check
```

## Document Shape

`design.md` usually contains:

- Design metadata
- Requirement baseline
- Context and current state
- Architecture decision records, usually ADR entries
- Design skeleton and task breakdown
- API, build, compatibility, data flow, or detailed design sections

`Feat-NN-xxx-spec.md` usually contains:

- Overview
- Delta scope
- Input documents
- User stories, or US entries
- Acceptance criteria, or AC entries
- Business rules, or BR entries
- Functional rules, or FR entries
- Exception or exemption rules, or ER entries
- Recovery contracts, or RC entries
- Verification mapping, or VM entries
- API changes, compatibility notes, Gherkin scenarios, and self-review checklist

Historical documents are not perfectly uniform. When maintaining registry entries, prefer the real `design.md` and `Feat-*.md` files on disk, and take titles/statuses from each document's header metadata when available.

## Common Pitfalls

- Do not edit `index.md` manually; it is overwritten by the generator.
- FeatIDs under the same FuncID must be contiguous.
- `features.yaml` may use `spec: null`, but if a real file exists, point to it.
- `functions.yaml` may use `design: null`, but if a real `design.md` exists, point to it.
- Registry paths must match the real file system paths, especially after historical directory renames.
- YAML may parse unquoted numeric-looking values as numbers. For new two-digit node ids, prefer quotes, for example `'08'`.
- Preserve existing user changes in unrelated files. This repository can have generated and manual edits in the same working tree.

## Minimum Done Criteria

After an add, update, or delete task, make sure all of this is true:

```text
python3 tools/generate_index.py --check passes
python3 tools/generate_site.py passes
python3 tools/validate_specs.py --quiet reports no new errors on the specs you touched
Every design.md on disk is registered in functions.yaml
Every Feat-*.md on disk is registered in features.yaml
Every registered design/spec path exists on disk
git diff contains no unrelated formatting or reordering churn
```
