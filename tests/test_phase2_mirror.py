"""Exercise self-contained Phase 2 notebook upload cells without cloud access.

The miniature uploaded batch is synthesized from already-public, user-owned
geometry fixtures for TEST purposes. It is not asserted as a Studio export.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import patch

from test_public_mirror import FakeMarimo, FakeUI

ROOT=Path(__file__).resolve().parents[1]


def sample_batch():
    files=sorted((ROOT/"samples").glob("studio-fefco-0201-*.json"))
    assert len(files)==2
    variants=[]
    for n,file in enumerate(files):
        public=json.loads(file.read_text(encoding="utf-8"))
        die={
            "schemaVersion":1,
            "templateId":"fefco-0201",
            "unit":"mm",
            "panelTopology":None,
            "entities":[{
                "id":f"source-op-{i}",
                "sourceIndex":i,
                "operation":e["operation"],
                "nativeEntityType":e["kind"],
                "nativeDXFColor":None,
                "closed":e["closed"],
                "pointsMm":[{"x":p[0],"y":p[1]} for p in e["pointsMm"]],
                "analyticArc":None,
            } for i,e in enumerate(public["entities"])],
        }
        digest=hashlib.sha256(
            json.dumps(die,ensure_ascii=True,separators=(",", ":")).encode()
        ).hexdigest()
        variants.append({
            "sourceId":"fefco-0201",
            "variantId":f"test-upload-v{n+1}",
            "sourceSHA256":public["geometrySHA256"],
            "sourceArtifactSHA256":digest,
            "sourceHashScope":"hand-authored-test-wrapper-of-public-qa-not-original-source",
            "sourceCoordinateUnit":"mm",
            "engineVersion":{"gitBase":"test-only"},
            "inputParameters":{"L":180+n*30,"W":120+n*20,"D":200-n*20,"DX":0,
                               "fefco":{},"material":{"caliperMm":1.5,
                                                         "materialClass":"corrugated"}},
            "dieIR":die,
            "candidateOnly":True,"manufacturingApproved":False,
        })
    return {
        "schemaVersion":"packpoc.geometry-lab.dieir-batch/v1",
        "unit":"mm",
        "generator":"A20StudioEngine.calculate->StudioDieIR.compile",
        "approval":{"studioActivationPermitted":False,"manufacturingApproved":False,
                    "sourceCADIndependentlyVerifiedByThisBatch":False,
                    "physical3DVerified":False},
        "models":[{"id":"fefco-0201","dimensionSemantics":"test-only",
                   "sourceDefaultDimensions":{"L":180,"W":120,"D":200}}],
        "variants":variants,
    }


def run_upload_case(batch):
    fake=FakeMarimo()
    FakeUI.file=staticmethod(lambda **kw:types.SimpleNamespace(value=[]))
    with patch.dict(sys.modules,{"marimo":fake}):
        runpy.run_path(str(ROOT/"notebooks"/"geometry_lab.py"))
        cells=fake.apps[0].cells
        assert len(cells)==11, len(cells)
        (mo,)=cells[0]()
        analyze,candidates,entity,from_fixture,hashlib_,json_,time_,tracemalloc_=cells[1]()
        process,merge_batches,compare_candidates=cells[6](analyze,entity,hashlib_,json_)
        batch_upload,reference_upload=cells[8](mo)
        batch_upload.value=[types.SimpleNamespace(name="test.json",
                    contents=json.dumps(batch).encode("utf-8"))]
        result,evidence,comparison,measure=cells[9](batch_upload,compare_candidates,
            json_,merge_batches,mo,process,reference_upload,time_,tracemalloc_)
        return result,evidence,measure


class Phase2NotebookTests(unittest.TestCase):
    def test_file_upload_processor_runs_real_inlined_geometry_functions(self):
        result,evidence,measure=run_upload_case(sample_batch())
        self.assertEqual(len(result["models"]),2)
        self.assertEqual(len(result["candidateGroups"]),1)
        self.assertEqual(measure["sourceModels"],1)
        self.assertEqual(measure["sourceVariants"],2)
        self.assertFalse(any(result["approval"].values()))
        self.assertTrue(result["models"][0]["sourceSHA256"])
        self.assertEqual(evidence["fefco-0201"]["independentWitnesses"],[])

    def test_bad_uploaded_geometry_digest_fails_closed(self):
        sample=sample_batch()
        sample["variants"][0]["sourceArtifactSHA256"]="0"*64
        result,ledger,measure=run_upload_case(sample)
        self.assertIsNone(result)
        self.assertIsNone(ledger)
        self.assertIsNone(measure)

    def test_upload_is_optional_and_not_performed_on_import(self):
        text=(ROOT/"notebooks"/"geometry_lab.py").read_text(encoding="utf-8")
        self.assertIn("batch_upload = mo.ui.file",text)
        self.assertIn("if not batch_upload.value",text)
        self.assertNotIn("from src.",text)
        self.assertNotIn("local_private/",text)
        self.assertNotIn("urllib.request",text)
        self.assertNotIn("requests.get(",text)


if __name__=="__main__":
    unittest.main()
