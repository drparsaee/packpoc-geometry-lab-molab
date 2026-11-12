# Pack P.O.C. Geometry Lab | Public MoLab Mirror

This is a public, source-filtered and single-file marimo mirror for Pack P.O.C. Geometry Lab. The canonical Lab and Studio repositories remain PRIVATE and authoritative.

## Open in MoLab

Public GitHub notebook:

https://github.com/drparsaee/packpoc-geometry-lab-molab/blob/main/notebooks/geometry_lab.py

MoLab mirror preview:

https://molab.marimo.io/github/drparsaee/packpoc-geometry-lab-molab/blob/main/notebooks/geometry_lab.py

The notebook is self-contained. It has no sibling src import, private GitHub dependency, Windows path, cloud credentials, dynamic code download, or network calls. Three review-only Studio QA fixtures are embedded because GitHub notebook mirroring cannot guarantee adjacent files.

## Local execution

    python -m unittest discover -s tests -v
    python -m pip install "marimo>=0.17,<1"
    marimo check notebooks/geometry_lab.py
    marimo export html notebooks/geometry_lab.py -o mirror-preview.html
    marimo edit notebooks/geometry_lab.py

The Python unit suite executes notebook cell Python bodies using a minimal marimo UI test double. It does NOT prove actual marimo or MoLab execution. GitHub Actions separately attempts a real marimo check and HTML export; check its results rather than treating the workflow's existence as success.

## Real Pack P.O.C. Studio QA data

The only bundled inputs are filtered noncustomer 2D QA outputs produced by our own Studio A20 to DieIR path. No proprietary vendor templates, ARD/ACD, Pacdora data, customer projects, licensed source or CAD-X witness data are included.

| Public QA case | Native Studio active model | 2D segments |
| --- | --- | --- |
| studio-fefco-0201-standard | fefco-0201, L180 W120 D200 mm | 44 CUT, 12 CREASE |
| studio-fefco-0201-second-size | fefco-0201, L210 W140 D180 mm | 44 CUT, 12 CREASE |
| studio-compact-reverse-tuck | compact-reverse-tuck-01, L120 W40 D100 mm | 72 CUT, 12 CREASE |

The two 0201 models share a structural graph fingerprint at two different dimensions; the reverse tuck forms another candidate group. This establishes only structural similarity, NOT a general parametric family formula or approval.

Public JSON fixtures are available in samples/ for audit, while the mirror runtime uses an embedded identical copy. Source identity, mm coordinates, operations and SHA-256 of the filtered published geometry are retained. Private source-module hashes and original commercial witness identifiers are intentionally omitted. The public fixtures are only locally generated Studio QA illustrations, never industrially verified CAD designs.

## Why a separate public mirror

The original private GitHub repository is not anonymously accessible to the MoLab GitHub mirror, and its original notebook imports sibling code. This public bundle solves both restrictions without changing the authoritative Studio or private Geometry Lab.

All Lab export flags for manufacturing, 3D approval and Studio activation remain false. Only Prime inside original Studio can approve a source-backed parametric family after independent geometry and physical QA.

## Phase 2: optional real Studio DieIR batch upload

The single-file notebook now includes a second, general source-geometry
processing section. Its source is the **same** reviewed Python research
functions used by the separate private Lab. This is not a per-model generator.

You may:

1. Run the preinstalled three public safe QA examples above without any
   upload. They remain test fixtures, not the production batch.
2. With separate authorization for cloud transfer, check the mandatory
   upload-authorization control, then select one or more
   approved versioned Studio batch JSON files in the **Upload** input.
   The expected contract is
   packpoc.geometry-lab.dieir-batch/v1 (schema in schemas/).
   All batches must use the real A20StudioEngine -> StudioDieIR path,
   include real metric entities, their SHA256, L/W/D inputs, optional
   source N/board/caliper and panels/hinges, and explicitly denied
   production activation flags.
3. View source operations and topology invariants, observed possible
   material dependencies, conditional one-parameter affine holdout
   candidates and explicitly observed accepted input ranges. Upload an
   optional separately generated Studio reference to compare hash,
   operation types and original source geometry connectivity.
4. Download review-only candidate JSON for the authoritative Studio's
   StudioGeometryLabCandidateInbox.php. The output is never auto-activated.

**Privacy warning:** the public Mirror contains zero private full
Studio/CAD-X batches. Do NOT upload confidential 52-model/616-variant
source data to MoLab merely because a file chooser is present.
Cloud transfer of the private file requires an explicit source, legal,
privacy and ownership review. The local Lab can run the complete
analysis entirely offline without transferring data.

The numeric similarities are hypotheses based on multiple source-generated
samples, not mathematical proof of the original source formula. The
notebook does not discover independent vendor CAD witnesses, validate
physical folded 3D/locks, or certify continuous manufacturing domains.
Changing material alone may alter geometry, but a thickness rule is
not independently established by that observation.

For private local batch analysis (no cloud transfer), refer to the
canonical private Lab's src/batch_families.py and its
docs/STUDIO_MOLAB_BATCH_PHASE2_20261112.md. The public GitHub Actions
workflow runs real marimo check/export on **only** the public fixture
defaults, and runs synthetic uploaded-batch Python tests. It does not
upload the private batch or attest to a live MoLab-hosted session.

### Phase 2 execution evidence

- Current public Mirror main:
  **177eb60105a94e03daeb3e4be09cc2b6fa309fb5**.
- https://github.com/drparsaee/packpoc-geometry-lab-molab/actions/runs/43264986263
  is a **successful** hosted GitHub Actions run on that exact Commit:
  10 Python tests, real marimo check, real marimo HTML export, nonempty HTML.
- Separately, the private local Studio source exporter and Lab analyzed
  52 active models and 616 authentic source-generated variants; all
  output approvals remain false, and no private CAD files were published.
- A successful GitHub Actions marimo execution is **not** evidence that
  this Phase 2 notebook ran with uploaded data inside a MoLab session.
  Actual MoLab account execution and cloud-vs-local benchmark are
  still **unverified**.
