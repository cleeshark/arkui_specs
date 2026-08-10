# CI Smoke Test (throwaway)

Verifies the spec-eval CI pipeline end-to-end on a clean, zero-affected change:
webhook scan -> fresh PR comment -> `oh-gc pr test` marks the automated test passed.

Maps to 0 affected Functions (not a spec/tooling-eval path), so against a
current baseline it must yield `delta.added == 0` and reach `test_passed`.
Safe to delete after verification.

Updated!
