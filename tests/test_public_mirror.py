"""Independent standard-library execution of public marimo notebook cells.

This test executes Python cell bodies with a minimal UI test double. It is NOT
claimed to be marimo runtime or MoLab cloud execution. GitHub Actions separately
runs actual marimo export with the installed marimo package.
"""
from __future__ import annotations

import json
import re
import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class FakeUI:
    @staticmethod
    def multiselect(*, options, value, label):
        assert set(value) <= set(options)
        return types.SimpleNamespace(value=value)

    @staticmethod
    def table(items, label):
        assert isinstance(items, list)
        return items


class FakeMarimo(types.ModuleType):
    ui = FakeUI()

    def __init__(self):
        super().__init__("marimo")
        self.apps = []

    def App(self, **kwargs):
        app = types.SimpleNamespace(cells=[])

        def cell(fn):
            app.cells.append(fn)
            return fn

        app.cell = cell
        self.apps.append(app)
        return app

    @staticmethod
    def md(value):
        assert isinstance(value, str)
        return value

    @staticmethod
    def vstack(contents):
        return contents

    @staticmethod
    def download(*, data, filename, mimetype, label):
        assert data and filename.endswith(".json") and mimetype == "application/json"
        return data


def execute_notebook_cells():
    fake = FakeMarimo()
    with patch.dict(sys.modules, {"marimo": fake}):
        runpy.run_path(str(ROOT / "notebooks" / "geometry_lab.py"))
        app = fake.apps[0]
        assert len(app.cells) == 6
        (mo,) = app.cells[0]()
        analyze, candidates, from_fixture, _, json_module, timer, tracemalloc = app.cells[1]()
        (samples,) = app.cells[2](json_module)
        (selected,) = app.cells[3](mo, samples)
        (result,) = app.cells[4](
            analyze, candidates, from_fixture, mo, samples, selected, timer, tracemalloc
        )
        app.cells[5](json_module, mo, result)
        return result, samples, from_fixture, analyze


class PublicMirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result, samples, from_fixture, analyze = execute_notebook_cells()
        cls.result = result
        cls.samples = samples
        cls.from_fixture = staticmethod(from_fixture)
        cls.analyze = staticmethod(analyze)

    def test_self_contained_and_no_private_source_paths(self):
        text = (ROOT / "notebooks" / "geometry_lab.py").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?i)[A-Z]:[/\\]")
        self.assertNotIn("from src", text)
        self.assertNotIn("import requests", text)
        self.assertNotIn("subprocess", text)
        self.assertNotIn("local_private", text)
        self.assertIn("@app.cell", text)

    def test_actual_studio_source_generated_samples_embedded(self):
        self.assertEqual(len(self.samples), 3)
        self.assertEqual({s["templateId"] for s in self.samples},
                         {"fefco-0201", "compact-reverse-tuck-01"})
        for sample in self.samples:
            stored = json.loads((ROOT / "samples" / (sample["sourceId"] + ".json")).read_text())
            self.assertEqual(sample, stored)
            self.assertEqual(sample["unit"], "mm")
            self.assertEqual(sample["status"], "nonproduction-demonstration-only")
            self.assertGreater(sum(len(item["pointsMm"]) for item in sample["entities"]), 20)

    def test_groups_are_never_certification(self):
        self.assertEqual(self.result["schemaVersion"], "packpoc.geometry-lab.candidate/v1")
        self.assertEqual(len(self.result["models"]), 3)
        self.assertEqual(len(self.result["candidateGroups"]), 2)
        self.assertTrue(all(v is False for v in self.result["approval"].values()))
        self.assertTrue(all(g["evidenceLevel"] == "structural-candidate-only"
                            and g["familyId"] is None for g in self.result["candidateGroups"]))

    def test_repeated_family_geometry_has_same_topological_fingerprint(self):
        by_id = {item["sourceId"]: item for item in self.result["models"]}
        one = by_id["studio-fefco-0201-standard"]
        two = by_id["studio-fefco-0201-second-size"]
        self.assertEqual(one["structuralFingerprint"], two["structuralFingerprint"])
        self.assertNotEqual(one["sourceSHA256"], two["sourceSHA256"])
        self.assertEqual(one["operationKinds"], two["operationKinds"])
        self.assertGreater(one["operationKinds"].get("cut:LINE", 0), 0)
        self.assertGreater(one["operationKinds"].get("crease:LINE", 0), 0)
        self.assertEqual(one["structuralFingerprint"],
                         "03cd69d79f4f1de6b06e5ab48b28ea7f72997d283dcece85b816980d7767ecd6")

    def test_public_geometry_matches_locally_verified_studio_baselines(self):
        by_id = {item["sourceId"]: item for item in self.result["models"]}
        expected = {
            "studio-fefco-0201-standard": (44, 12, 44, 56, 1, 13),
            "studio-fefco-0201-second-size": (44, 12, 44, 56, 1, 13),
            "studio-compact-reverse-tuck": (72, 12, 73, 85, 1, 13),
        }
        for source_id, (cut, crease, vertices, edges, components, cycles) in expected.items():
            actual = by_id[source_id]
            self.assertEqual(actual["operationKinds"]["cut:LINE"], cut)
            self.assertEqual(actual["operationKinds"]["crease:LINE"], crease)
            self.assertEqual(actual["topology"]["vertices"], vertices)
            self.assertEqual(actual["topology"]["edges"], edges)
            self.assertEqual(actual["topology"]["components"], components)
            self.assertEqual(actual["topology"]["cycles"], cycles)

    def test_original_geometry_checksums_reject_tampering(self):
        sample = json.loads(json.dumps(self.samples[0]))
        sample["entities"][0]["pointsMm"][1][0] += 0.5
        with self.assertRaises(ValueError):
            self.from_fixture(sample)

    def test_one_source_produces_typed_line_graph(self):
        graph = self.analyze(self.from_fixture(self.samples[0]))
        topology = graph["topology"]
        self.assertGreater(topology["vertices"], 5)
        self.assertGreater(topology["edges"], 5)
        self.assertGreater(topology["components"], 0)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", graph["structuralFingerprint"]))


if __name__ == "__main__":
    unittest.main()
