from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from generate_site import load_archived_semantic_evaluation


class Next009SiteEvaluationTest(unittest.TestCase):
    """The reviews-based ``site-evaluation`` export has been retired; the
    semantic archive is now published from real CI runtime archives (see
    ``generate_site.publish_archive`` and ``spec_eval.service.site_export``).
    What remains to guard here is that STATIC mode reads only the archived
    ``site-evaluation-report.json`` document."""

    def test_site_generator_reads_only_archived_semantic_json(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertFalse(load_archived_semantic_evaluation(root)["available"])
            value = {
                "schemaVersion": 1, "reportVersion": "test", "available": True,
                "sourceRevision": "abc123", "staticReport": {}, "summary": {}, "functions": [],
            }
            (root / "site-evaluation-report.json").write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(load_archived_semantic_evaluation(root), value)


if __name__ == "__main__":
    unittest.main()
