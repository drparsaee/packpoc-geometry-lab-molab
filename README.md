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
