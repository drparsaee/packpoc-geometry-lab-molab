# This is a self-contained marimo mirror notebook, generated from the
# original PackPOC Geometry Lab's PURE research primitives, not Studio source.
# Only 3 reviewed, public-safe outputs from locally generated Studio QA are
# embedded. There are no relative file imports, vendor CAD witnesses, Windows
# paths, network requests, keys or manufacturing approval routes.
import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")

@app.cell
def _():
    import marimo as mo
    mo.md("""# Pack P.O.C. Geometry Lab | MoLab Mirror

    **Three real, locally generated Pack P.O.C. Studio QA geometries.**
    The notebook runs independently of the private Studio/Geometry Lab
    repositories and does not download code or source files.

    These CUT/CREASE lines are derived from the current **A20 → DieIR**
    test output; no proprietary vendor CAD files, Pacdora listings, CAD-X
    witnesses, user designs or credentials are included.
    Geometry SHA-256 is calculated on the explicitly published sample only.
    Matching graph fingerprints are **research candidates, not proof of a
    parametric family, physical assembly or manufacturing approval**.
    """)
    return (mo,)

@app.cell
def _():
    import hashlib
    import json
    import math
    import time
    import tracemalloc
    from collections import Counter, defaultdict
    MAX_BYTES = 4_000_000
    MAX_ENTITIES = 8_000
    MAX_COORD = 1_000_000.0
    TOL = 1e-5
    VERSION = "packpoc.geometry-lab.candidate/v1"
    OPERATIONS = {"cut", "crease", "perf"}
    def num(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Geometry coordinate is not numeric")
        v = float(value)
        if not math.isfinite(v) or abs(v) > MAX_COORD:
            raise ValueError("Geometry coordinate out of millimetre bounds")
        return v

    def point(x, y):
        return [num(x), num(y)]

    def entity(op, kind, coords, *, center=None, radius=None, angles=None, source_index=None):
        if op not in OPERATIONS or kind not in ("LINE", "ARC"):
            raise ValueError("Unsupported operation or geometric primitive")
        if len(coords) != 2:
            raise ValueError("A geometric edge must have two endpoints")
        p0, p1 = [point(*p) for p in coords]
        if math.dist(p0, p1) <= TOL:
            raise ValueError("Zero-length geometric entity")
        item = {"operation": op, "kind": kind, "pointsMm": [p0, p1]}
        if source_index is not None:
            item["sourceIndex"] = source_index
        if kind == "ARC":
            if center is None or radius is None or angles is None:
                raise ValueError("ARC requires analytic center/radius/sweep")
            c = point(*center)
            r = num(radius)
            start, end = [num(a) for a in angles]
            if r <= TOL or not 0 <= start < 360 or not 0 <= end < 360 or start == end:
                raise ValueError("Unsupported ARC radius/sweep")
            for p, a in ((p0, start), (p1, end)):
                expected = [c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))]
                if math.dist(p, expected) > 0.0025:
                    raise ValueError("ARC endpoint differs from original source circle")
            item["analyticArc"] = {"centerMm": c, "radiusMm": r, "startAngleDeg": start, "endAngleDeg": end}
        return item

    def graph(edges, tolerance=TOL):
        """Endpoint graph with T-junction splitting on LINE segments, no arc chords."""
        if not 0 < tolerance <= 0.05:
            raise ValueError("Snap tolerance out of bounds")
        points = []
        for e in edges:
            points.extend(e["pointsMm"])
        if len(points) > 2 * MAX_ENTITIES:
            raise ValueError("Graph budget exceeded")
        # Quantization is explicit and deterministic for the same input order.
        key = lambda p: (round(p[0]/tolerance), round(p[1]/tolerance))
        unique = {}
        for p in points:
            unique.setdefault(key(p), p)
        split_edges = []
        for edge in edges:
            a, b = edge["pointsMm"]
            mids = [(0.0, a), (1.0, b)]
            if edge["kind"] == "LINE":
                vx, vy = b[0] - a[0], b[1] - a[1]
                length2 = vx*vx + vy*vy
                for p in unique.values():
                    t = ((p[0]-a[0])*vx + (p[1]-a[1])*vy)/length2
                    if tolerance < t < 1-tolerance and math.dist(p, [a[0]+t*vx, a[1]+t*vy]) <= tolerance:
                        mids.append((t, p))
            mids.sort(key=lambda v: v[0])
            for (_, first), (_, second) in zip(mids, mids[1:]):
                if key(first) != key(second):
                    split_edges.append((key(first), key(second), edge["operation"], edge["kind"]))
        adjacency = defaultdict(set)
        for u, v, _, _ in split_edges:
            adjacency[u].add(v); adjacency[v].add(u)
        seen = set()
        components = 0
        for node in adjacency:
            if node in seen:
                continue
            components += 1
            stack = [node]; seen.add(node)
            while stack:
                for neighbour in adjacency[stack.pop()]:
                    if neighbour not in seen:
                        seen.add(neighbour); stack.append(neighbour)
        degree = Counter(len(n) for n in adjacency.values())
        unique_links = {tuple(sorted((a, b))) for a, b, _, _ in split_edges}
        return {
            "vertices": len(adjacency), "edges": len(unique_links),
            "components": components,
            "cycles": max(0, len(unique_links) - len(adjacency) + components),
            "degreeHistogram": dict(sorted(degree.items())),
            "tJunctionSplitEdges": len(split_edges)-len(edges),
        }

    def analyze(record):
        edges = record["entities"]
        topology = graph(edges)
        counts = Counter((e["operation"], e["kind"]) for e in edges)
        signature = {"operationKinds": {f"{op}:{kind}": n for (op, kind), n in sorted(counts.items())},
                     "topology": {k: topology[k] for k in ("vertices", "edges", "components", "cycles", "degreeHistogram")}}
        fingerprint = hashlib.sha256(json.dumps(signature, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        result = {"sourceId": record["sourceId"], "sourceSHA256": record["sourceSHA256"],
                "sourceArtifactSHA256": record.get("sourceArtifactSHA256"),
                "sourceHashScope": record.get("sourceHashScope", "unspecified"),
                "unit": "mm", "entityCount": len(edges), "topology": topology,
                "operationKinds": signature["operationKinds"], "structuralFingerprint": fingerprint}
        if "nativeDXFSHA256" in record:
            result["nativeDXFSHA256"] = record["nativeDXFSHA256"]
        return result

    def candidates(records):
        groups = defaultdict(list)
        for record in records:
            groups[record["structuralFingerprint"]].append(record["sourceId"])
        return {
            "schemaVersion": VERSION,
            "approval": {"parametricFamilyVerified": False, "sourceCADVerified": False,
                         "fold3DVerified": False, "productionApproved": False,
                         "studioActivationPermitted": False},
            "units": "mm",
            "models": records,
            "candidateGroups": [
                {"structuralFingerprint": fp, "sourceIds": sorted(ids),
                 "evidenceLevel": "structural-candidate-only", "familyId": None}
                for fp, ids in sorted(groups.items())
            ],
        }


    def from_public_fixture(f):
        """Expand *actual Studio-generated QA output* to typed metric source lines."""
        required = {"schemaVersion", "sourceId", "templateId", "sourceType", "sourceHashScope",
                    "geometrySHA256", "unit", "status", "entities"}
        if set(f) != required or f["schemaVersion"] != "packpoc.public-studio-qa/v1":
            raise ValueError("Unexpected public QA contract")
        if f["unit"] != "mm" or f["status"] != "nonproduction-demonstration-only":
            raise ValueError("Non-metric or falsely approved QA output")
        if not isinstance(f["entities"], list) or not 1 <= len(f["entities"]) <= MAX_ENTITIES:
            raise ValueError("Bad bounded source geometry")
        canonical = json.dumps(f["entities"], sort_keys=True, separators=(",", ":")).encode()
        checksum = hashlib.sha256(canonical).hexdigest()
        if checksum != f["geometrySHA256"]:
            raise ValueError("Public fixture geometry SHA256 mismatch")
        edges = []
        for source_index, original in enumerate(f["entities"]):
            if set(original) != {"operation", "kind", "closed", "pointsMm"}:
                raise ValueError("Extra or missing original primitive fields")
            if original["operation"] not in ("cut", "crease") or original["kind"] not in ("POLYLINE", "LINE"):
                raise ValueError("Unknown operation or type")
            points = original["pointsMm"]
            if not isinstance(points, list) or not 2 <= len(points) <= MAX_ENTITIES:
                raise ValueError("Malformed source polyline")
            segments = list(zip(points, points[1:]))
            if original["closed"]:
                segments.append((points[-1], points[0]))
            for start, end in segments:
                segment = entity(original["operation"], "LINE", [start, end], source_index=source_index)
                if original["kind"] == "POLYLINE":
                    segment["sourcePrimitiveType"] = "POLYLINE"
                edges.append(segment)
        if len(edges) > MAX_ENTITIES:
            raise ValueError("Flattened source geometry budget exceeded")
        return {
            "sourceId": f["sourceId"],
            "sourceSHA256": checksum,
            "sourceArtifactSHA256": hashlib.sha256(json.dumps(f,sort_keys=True,separators=(",", ":")).encode()).hexdigest(),
            "sourceHashScope": "public-sanitized-Studio-generated-QA-geometry",
            "unit": "mm",
            "entities": edges,
        }

    return (analyze, candidates, entity, from_public_fixture, hashlib, json, time, tracemalloc)

@app.cell
def _(json):
    # Public-approved, sanitized, embedded geometry. GitHub sample JSONs
    # contain the same records, but MoLab mirrors only this notebook file.
    samples = json.loads('[{"schemaVersion":"packpoc.public-studio-qa/v1","sourceId":"studio-compact-reverse-tuck","templateId":"compact-reverse-tuck-01","sourceType":"locally-generated-PackPOC-Studio-A20-DieIR-QA-output","sourceHashScope":"public-filtered-PackPOC-generated-QA-geometry-only","geometrySHA256":"b5bdf00c4d43700e148bef0133711b6f6e7fef91cb871ea3130f7d7c81d4b4a1","unit":"mm","status":"nonproduction-demonstration-only","entities":[{"operation":"cut","kind":"POLYLINE","closed":true,"pointsMm":[[0.0,0.0],[0.0,-40.0],[0.0,-51.0],[0.061597,-51.939789],[0.245334,-52.863497],[0.548067,-53.755321],[0.964617,-54.6],[1.487856,-55.383082],[2.108831,-56.091169],[2.816918,-56.712144],[3.6,-57.235383],[4.444679,-57.651933],[5.336503,-57.954666],[6.260211,-58.138403],[7.2,-58.2],[112.8,-58.2],[113.739789,-58.138403],[114.663497,-57.954666],[115.555321,-57.651933],[116.4,-57.235383],[117.183082,-56.712144],[117.891169,-56.091169],[118.512144,-55.383082],[119.035383,-54.6],[119.451933,-53.755321],[119.754666,-52.863497],[119.938403,-51.939789],[120.0,-51.0],[120.0,-40.0],[150.0,-40.0],[160.0,0.0],[280.0,0.0],[290.0,-40.0],[320.0,-40.0],[320.0,100.0],[310.0,140.0],[280.0,140.0],[280.0,151.0],[279.938403,151.939789],[279.754666,152.863497],[279.451933,153.755321],[279.035383,154.6],[278.512144,155.383082],[277.891169,156.091169],[277.183082,156.712144],[276.4,157.235383],[275.555321,157.651933],[274.663497,157.954666],[273.739789,158.138403],[272.8,158.2],[167.2,158.2],[166.260211,158.138403],[165.336503,157.954666],[164.444679,157.651933],[163.6,157.235383],[162.816918,156.712144],[162.108831,156.091169],[161.487856,155.383082],[160.964617,154.6],[160.548067,153.755321],[160.245334,152.863497],[160.061597,151.939789],[160.0,151.0],[160.0,140.0],[130.0,140.0],[120.0,100.0],[0.0,100.0],[-18.2,94.96],[-18.2,5.04]]},{"operation":"cut","kind":"POLYLINE","closed":false,"pointsMm":[[120.0,0.0],[120.0,-40.0]]},{"operation":"cut","kind":"POLYLINE","closed":false,"pointsMm":[[160.0,100.0],[160.0,140.0]]},{"operation":"cut","kind":"POLYLINE","closed":false,"pointsMm":[[280.0,100.0],[280.0,140.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[120.0,0.0],[120.0,100.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[160.0,0.0],[160.0,100.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[280.0,0.0],[280.0,100.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[0.0,0.0],[0.0,100.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[0.0,0.0],[120.0,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[0.0,-40.0],[120.0,-40.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[120.0,0.0],[160.0,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[280.0,0.0],[320.0,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[160.0,100.0],[280.0,100.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[160.0,140.0],[280.0,140.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[120.0,100.0],[160.0,100.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[280.0,100.0],[320.0,100.0]]}]},{"schemaVersion":"packpoc.public-studio-qa/v1","sourceId":"studio-fefco-0201-second-size","templateId":"fefco-0201","sourceType":"locally-generated-PackPOC-Studio-A20-DieIR-QA-output","sourceHashScope":"public-filtered-PackPOC-generated-QA-geometry-only","geometrySHA256":"36ffdcfe2fea9370467649536892f513cff9e72b4d7cfb1f2ad61732092dc140","unit":"mm","status":"nonproduction-demonstration-only","entities":[{"operation":"cut","kind":"POLYLINE","closed":true,"pointsMm":[[0.0,0.0],[1.25,0.0],[1.25,-70.0],[208.75,-70.0],[208.75,0.0],[210.0,0.0],[211.25,0.0],[211.25,-70.0],[348.75,-70.0],[348.75,0.0],[350.0,0.0],[351.25,0.0],[351.25,-70.0],[558.75,-70.0],[558.75,0.0],[560.0,0.0],[561.25,0.0],[561.25,-70.0],[698.75,-70.0],[698.75,0.0],[700.0,0.0],[700.0,180.0],[698.75,180.0],[698.75,250.0],[561.25,250.0],[561.25,180.0],[560.0,180.0],[558.75,180.0],[558.75,250.0],[351.25,250.0],[351.25,180.0],[350.0,180.0],[348.75,180.0],[348.75,250.0],[211.25,250.0],[211.25,180.0],[210.0,180.0],[208.75,180.0],[208.75,250.0],[1.25,250.0],[1.25,180.0],[0.0,180.0],[-35.0,171.25],[-35.0,8.75]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[210.0,0.0],[210.0,180.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[1.25,0.0],[208.75,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[1.25,180.0],[208.75,180.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[350.0,0.0],[350.0,180.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[211.25,0.0],[348.75,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[211.25,180.0],[348.75,180.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[560.0,0.0],[560.0,180.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[351.25,0.0],[558.75,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[351.25,180.0],[558.75,180.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[561.25,0.0],[698.75,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[561.25,180.0],[698.75,180.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[0.0,0.0],[0.0,180.0]]}]},{"schemaVersion":"packpoc.public-studio-qa/v1","sourceId":"studio-fefco-0201-standard","templateId":"fefco-0201","sourceType":"locally-generated-PackPOC-Studio-A20-DieIR-QA-output","sourceHashScope":"public-filtered-PackPOC-generated-QA-geometry-only","geometrySHA256":"a17c37312b9ee499e529ede1c3d86266b6c1b50f443aea287332afb266a6e6e0","unit":"mm","status":"nonproduction-demonstration-only","entities":[{"operation":"cut","kind":"POLYLINE","closed":true,"pointsMm":[[0.0,0.0],[1.25,0.0],[1.25,-60.0],[178.75,-60.0],[178.75,0.0],[180.0,0.0],[181.25,0.0],[181.25,-60.0],[298.75,-60.0],[298.75,0.0],[300.0,0.0],[301.25,0.0],[301.25,-60.0],[478.75,-60.0],[478.75,0.0],[480.0,0.0],[481.25,0.0],[481.25,-60.0],[598.75,-60.0],[598.75,0.0],[600.0,0.0],[600.0,200.0],[598.75,200.0],[598.75,260.0],[481.25,260.0],[481.25,200.0],[480.0,200.0],[478.75,200.0],[478.75,260.0],[301.25,260.0],[301.25,200.0],[300.0,200.0],[298.75,200.0],[298.75,260.0],[181.25,260.0],[181.25,200.0],[180.0,200.0],[178.75,200.0],[178.75,260.0],[1.25,260.0],[1.25,200.0],[0.0,200.0],[-35.0,191.25],[-35.0,8.75]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[180.0,0.0],[180.0,200.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[1.25,0.0],[178.75,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[1.25,200.0],[178.75,200.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[300.0,0.0],[300.0,200.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[181.25,0.0],[298.75,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[181.25,200.0],[298.75,200.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[480.0,0.0],[480.0,200.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[301.25,0.0],[478.75,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[301.25,200.0],[478.75,200.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[481.25,0.0],[598.75,0.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[481.25,200.0],[598.75,200.0]]},{"operation":"crease","kind":"POLYLINE","closed":false,"pointsMm":[[0.0,0.0],[0.0,200.0]]}]}]')
    return (samples,)

@app.cell
def _(mo, samples):
    selection = mo.ui.multiselect(
        options=[source["sourceId"] for source in samples],
        value=[source["sourceId"] for source in samples],
        label="Select locally generated Studio QA fixtures (no remote fetch)",
    )
    selection
    return (selection,)

@app.cell
def _(analyze, candidates, from_public_fixture, mo, samples, selection, time, tracemalloc):
    tracemalloc.start()
    start = time.perf_counter()
    chosen = [item for item in samples if item["sourceId"] in selection.value]
    models = [analyze(from_public_fixture(item)) for item in chosen]
    result = candidates(models)
    elapsed = time.perf_counter() - start
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    views = []
    if models:
        metrics = [{
            "source": item["sourceId"],
            "CUT": sum(n for op, n in item["operationKinds"].items() if op.startswith("cut:")),
            "CREASE": sum(n for op, n in item["operationKinds"].items() if op.startswith("crease:")),
            "vertices": item["topology"]["vertices"],
            "edges": item["topology"]["edges"],
            "components": item["topology"]["components"],
            "cycles": item["topology"]["cycles"],
            "fingerprint": item["structuralFingerprint"][:12],
        } for item in models]
        views.append(mo.ui.table(metrics, label="Actual Studio 2D source geometry analysis"))
        views.append(mo.ui.table(result["candidateGroups"], label="Structural candidate groups only"))
    views.append(mo.md(
        f"**Inputs:** {len(models)} real Studio QA geometries. "
        f"**Groups:** {len(result['candidateGroups'])}. "
        f"**Elapsed:** {elapsed:.5f}s; **traced peak:** {peak_bytes} bytes. "
        "Runtime values shown are for this actual notebook execution, not comparable to full RAM."
    ))
    views.append(mo.md("All activation, 3D fold verification and manufacturing flags: **FALSE**."))
    mo.vstack(views)
    return (result,)

@app.cell
def _(json, mo, result):
    output = mo.download(
        data=json.dumps(result, indent=2).encode("utf-8"),
        filename="family-registry-candidates-v1.json",
        mimetype="application/json",
        label="Export review-only Studio candidate metadata",
    )
    output
    return

@app.cell
def _(analyze, entity, hashlib, json):
    # Pure Lab functions included at build time; zero imports from private
    # source repositories in the distributed self-contained notebook.
    import math as _phase2_math
    import re
    from collections import Counter as _phase2_Counter, defaultdict as _phase2_defaultdict
    _phase2_VERSION = "packpoc.geometry-lab.candidate/v1"
    INPUT_SCHEMA = "packpoc.geometry-lab.dieir-batch/v1"
    OUTPUT_SCHEMA = "packpoc.geometry-lab.candidate/v1"
    MAX_VARIANTS = 2000
    MAX_ENTITY_RECORDS = 10_000
    TOOL_OPS = {"cut", "crease", "perf"}
    ANNOTATION_OPS = {
        "trim", "adhesive_region", "varnish_exclusion", "partial_cut",
        "reverse_partial_cut", "perforation", "score",
    }
    ALL_OPERATIONS = TOOL_OPS | ANNOTATION_OPS
    SOURCE_TYPES = {"LINE", "ARC", "POLYLINE"}
    APPROVAL = {
        "parametricFamilyVerified": False,
        "sourceCADVerified": False,
        "fold3DVerified": False,
        "productionApproved": False,
        "studioActivationPermitted": False,
    }
    AXES = ("L", "W", "D")
    COORD_TOL_MM = 0.002
    def validate(candidate: dict) -> dict:
        required = {"schemaVersion", "units", "approval", "models", "candidateGroups"}
        if not isinstance(candidate, dict) or set(candidate) != required:
            raise ValueError("Candidate handoff has unsupported/missing keys")
        if candidate["schemaVersion"] != _phase2_VERSION or candidate["units"] != "mm":
            raise ValueError("Unrecognized or non-mm Lab handoff version")
        flags = {"parametricFamilyVerified", "sourceCADVerified", "fold3DVerified",
                 "productionApproved", "studioActivationPermitted"}
        if set(candidate["approval"]) != flags or any(value is not False for value in candidate["approval"].values()):
            raise ValueError("Lab may never assert approval or activation")
        if not isinstance(candidate["models"], list) or len(candidate["models"]) > 8000:
            raise ValueError("Invalid candidate count")
        ids = set()
        fingerprints = {}
        for item in candidate["models"]:
            if not isinstance(item.get("sourceId"), str) or not 1 <= len(item["sourceId"]) <= 256:
                raise ValueError("Invalid source identity")
            if item["sourceId"] in ids:
                raise ValueError("Repeated source identity")
            ids.add(item["sourceId"])
            for sha_key in ("sourceSHA256", "sourceArtifactSHA256", "structuralFingerprint"):
                value = item.get(sha_key)
                if sha_key == "sourceArtifactSHA256" and value is None:
                    continue
                if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                    raise ValueError("Missing original source hash/provenance")
            if item.get("unit") != "mm" or not isinstance(item.get("topology"), dict):
                raise ValueError("Non-metric or absent topology")
            if not isinstance(item.get("operationKinds"), dict) or not isinstance(item.get("entityCount"), int):
                raise ValueError("No typed source geometry inventory")
            fingerprints[item["sourceId"]] = item["structuralFingerprint"]
        seen_groups = set()
        grouped_ids = set()
        for group in candidate["candidateGroups"]:
            fp = group.get("structuralFingerprint")
            members = group.get("sourceIds")
            if group.get("familyId", "invalid") is not None or group.get("evidenceLevel") != "structural-candidate-only":
                raise ValueError("Lab group attempted source family promotion")
            if not isinstance(members, list) or not members or members != sorted(members) or fp in seen_groups:
                raise ValueError("Nondeterministic/duplicate structural grouping")
            seen_groups.add(fp)
            for member in members:
                if member not in ids or member in grouped_ids or fingerprints[member] != fp:
                    raise ValueError("Unknown/repeated source or altered group fingerprint")
                grouped_ids.add(member)
        if grouped_ids != ids:
            raise ValueError("Not every source model grouped exactly once")
        return {"contract": _phase2_VERSION, "status": "REVIEW_ONLY_CANDIDATES",
                "sourceIds": len(ids), "candidateGroups": len(seen_groups),
                "authoritativeStudioIntegration": False,
                "studioCapabilitiesModified": False}

    def sha_json_php(data):
        """Verifies the exact compact PHP JSON_PRESERVE_ZERO_FRACTION form.

        This preserves dictionary insertion order and numeric semantics. If
        Python and PHP serialization disagree, reject instead of claiming proof.
        """
        payload = json.dumps(data, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _sha(value, label):
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"Missing or noncanonical SHA256 {label}")
        return value

    def _scalar(value, label):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} must be a numeric mm scalar")
        number = float(value)
        if not _phase2_math.isfinite(number) or abs(number) > 1_000_000:
            raise ValueError(f"{label} out of bounds")
        return number

    def _shape(record):
        """Keep original DieIR primitives; flatten ONLY actual tool-line topology.

        A source analytic ARC is one topology edge and is never treated as its
        sampled preview chords. Non-tool annotations are retained and counted.
        """
        ir = record["dieIR"]
        if ir.get("schemaVersion") != 1 or ir.get("unit") != "mm":
            raise ValueError("Expected real metric Studio DieIR v1")
        source = ir.get("entities")
        if not isinstance(source, list) or not 1 <= len(source) <= MAX_ENTITY_RECORDS:
            raise ValueError("Missing or unbounded DieIR geometry")
        tool_edges = []
        annotations = _phase2_Counter()
        source_primitives = _phase2_Counter()
        source_ids = set()
        arcs = 0
        for position, original in enumerate(source):
            if not isinstance(original, dict):
                raise ValueError("Invalid source entity")
            eid = original.get("id")
            op = original.get("operation")
            kind = original.get("nativeEntityType")
            if not isinstance(eid, str) or not eid or eid in source_ids:
                raise ValueError("Missing or repeated original entity ID")
            source_ids.add(eid)
            if op not in ALL_OPERATIONS or kind not in SOURCE_TYPES:
                raise ValueError("Unknown source CAD operation/primitive")
            source_primitives[kind] += 1
            pts = original.get("pointsMm")
            if not isinstance(pts, list) or len(pts) < 2:
                raise ValueError("Missing original mm vertex path")
            for point in pts:
                if not isinstance(point, dict) or set(point) != {"x", "y"}:
                    raise ValueError("Source coordinates have missing/extra fields")
                for axis in ("x", "y"):
                    _scalar(point[axis], "source coordinate")
            if op not in TOOL_OPS:
                annotations[op] += 1
                continue
            index = original.get("sourceIndex", position)
            if kind == "ARC":
                analytic = original.get("analyticArc")
                if not isinstance(analytic, dict) or op != "cut":
                    raise ValueError("Native ARC has no supported analytic source")
                c = analytic["centerMm"]
                radius = _scalar(analytic["radiusMm"], "arc radius")
                start = _scalar(analytic["startAngleDeg"], "arc start")
                end = _scalar(analytic["endAngleDeg"], "arc end")
                if not 0 <= start < 360 or not 0 <= end < 360 or start == end:
                    raise ValueError("Unsupported analytic ARC sweep")
                tool_edges.append(entity(op, "ARC",
                    [[pts[0]["x"], pts[0]["y"]], [pts[-1]["x"], pts[-1]["y"]]],
                    center=[c["x"], c["y"]], radius=radius, angles=[start, end],
                    source_index=index))
                arcs += 1
            else:
                if kind == "LINE" and (len(pts) != 2 or original.get("closed")):
                    raise ValueError("Original LINE cannot be reinterpreted as polyline")
                pairs = list(zip(pts, pts[1:]))
                if original.get("closed"):
                    pairs.append((pts[-1], pts[0]))
                for first, last in pairs:
                    tool_edges.append(entity(op, "LINE",
                        [[first["x"], first["y"]], [last["x"], last["y"]]],
                        source_index=index))
            if len(tool_edges) > MAX_ENTITY_RECORDS:
                raise ValueError("Too many flattened CAD tool segments")
        if not tool_edges:
            raise ValueError("DieIR carries no authentic tooling primitive")
        return tool_edges, dict(annotations), dict(source_primitives), arcs

    def _features(ir):
        """Named original-source coordinate features, never reconstructed SVG."""
        result = {}
        for e in ir["entities"]:
            if e["operation"] not in TOOL_OPS:
                continue
            eid = e["id"]
            for i, p in enumerate(e["pointsMm"]):
                for axis in ("x", "y"):
                    result[f"{eid}:p{i}.{axis}"] = float(p[axis])
            if e["nativeEntityType"] == "ARC":
                arc = e["analyticArc"]
                result[f"{eid}:radiusMm"] = float(arc["radiusMm"])
                for axis in ("x", "y"):
                    result[f"{eid}:center.{axis}"] = float(arc["centerMm"][axis])
        return result

    def _parameter_key(record, *, omit=None, include_material=True):
        p = record["inputParameters"]
        signature = {axis: p[axis] for axis in ("L", "W", "D", "DX") if axis != omit}
        signature["fefco"] = p.get("fefco", {})
        if include_material:
            signature["material"] = p.get("material")
        return json.dumps(signature, sort_keys=True, separators=(",", ":"))

    def _numeric_candidate(first, last, holdout, axis):
        left = float(first["inputParameters"][axis])
        right = float(last["inputParameters"][axis])
        middle = float(holdout["inputParameters"][axis])
        if abs(right-left) < 1e-9 or not min(left,right) < middle < max(left,right):
            return None
        maps = [_features(r["dieIR"]) for r in (first,last,holdout)]
        common = sorted(set(maps[0]).intersection(maps[1],maps[2]))
        if not common:
            return None
        affine = []
        nonlinear = []
        for name in common:
            y0,y1,y_mid = (m[name] for m in maps)
            slope = (y1-y0)/(right-left)
            intercept = y0-slope*left
            residual = abs(slope*middle+intercept-y_mid)
            output = {"sourceCoordinate":name,"slope":round(slope,8),
                      "intercept":round(intercept,6),
                      "holdoutResidualMm":round(residual,7)}
            (affine if residual <= COORD_TOL_MM else nonlinear).append(output)
        return {"parameter":axis,"observedInputMm":[left,middle,right],
                "heldOutMiddleValue":middle, "sampleCount":3,
                "featuresCompared":len(common),
                "linearCandidateCount":len(affine),
                "nonlinearObservationCount":len(nonlinear),
                "linearExamples":affine[:12],
                "nonlinearExamples":nonlinear[:8],
                "evidenceLevel":"same-engine-numeric-holdout-not-source-formula-or-independent-CAD-witness",
                "productionVerified":False}

    def _model_observations(model_id, variants, summaries):
        fingerprints = [summaries[v["variantId"]]["structuralFingerprint"] for v in variants]
        sorted_flags = sorted(set(fingerprints))
        all_axes = {axis: sorted({_scalar(v["inputParameters"][axis],axis) for v in variants})
                    for axis in AXES}
        observed = {axis:{"observedMinimumMm":min(values),"observedMaximumMm":max(values),
                          "distinctAcceptedSamples":len(values)}
                    for axis,values in all_axes.items()}
        # Search only explicit univariate experiments that keep other parameters
        # and the board fixed. Correlated axes are NOT independent measurements.
        dependencies = []
        for axis in AXES:
            buckets = _phase2_defaultdict(list)
            for variant in variants:
                buckets[_parameter_key(variant,omit=axis)].append(variant)
            selected = None
            for items in buckets.values():
                unique = {float(v["inputParameters"][axis]):v for v in items}
                xs = sorted(unique)
                if len(xs) < 3:
                    continue
                trial = _numeric_candidate(unique[xs[0]],unique[xs[-1]],
                                           unique[xs[len(xs)//2]],axis)
                if trial and (selected is None or trial["featuresCompared"] > selected["featuresCompared"]):
                    selected = trial
            if selected:
                dependencies.append(selected)
            else:
                dependencies.append({"parameter":axis,"status":"not-identifiable-from-independent-single-axis-samples",
                                     "sampledValuesMm":all_axes[axis]})
        material_groups = _phase2_defaultdict(list)
        for variant in variants:
            material_groups[_parameter_key(variant, include_material=False)].append(variant)
        material_pairs = 0
        material_changed = 0
        for group in material_groups.values():
            for i in range(len(group)):
                for j in range(i+1,len(group)):
                    left,right = group[i],group[j]
                    if left["inputParameters"]["material"] == right["inputParameters"]["material"]:
                        continue
                    material_pairs += 1
                    a = _features(left["dieIR"]); b = _features(right["dieIR"])
                    if a.keys()!=b.keys() or any(abs(a[k]-b[k]) > COORD_TOL_MM for k in a.keys() & b.keys()):
                        material_changed += 1
        inv = {
            "stableAcrossObservedVariants":len(sorted_flags)==1,
            "distinctStructuralFingerprints":len(sorted_flags),
            "fingerprints":sorted_flags,
            "topologyDiscontinuityObserved":len(sorted_flags)>1,
            "sourceSegmentCountRange":[min(summaries[v["variantId"]]["entityCount"] for v in variants),
                                        max(summaries[v["variantId"]]["entityCount"] for v in variants)],
        }
        return {
            "sourceId":model_id,
            "familyStatus":"RESEARCH_CANDIDATE_ONLY",
            "geometryConstraints":{"sourceOriginalIdsAndDirectedGeometryRetained":True,
                                   "observedOnlyNoSourceFormulaExtraction":True,
                                   "univariateAffineHoldoutToleranceMm":COORD_TOL_MM},
            "parameterDependencies":dependencies,
            "topologyInvariants":inv,
            "materialDependencies":{"matchedSameDimensionDifferentMaterialPairs":material_pairs,
                                    "geometryChangedPairs":material_changed,
                                    "thicknessFormulaVerified":False},
            "validParameterDomain":{"status":"only-observed-accepted-samples-not-a-certified-continuous-domain",
                                    "observedAcceptedRanges":observed,
                                    "boundaryContinuityProved":False},
            "independentWitnesses":[],
            "confidence":{"score":None,"level":"candidate-only-insufficient-for-activation",
                          "reason":"Same engine generated every exported variant; no independent CAD oracle is embedded."},
            "testedVariantCount":len(variants),
        }

    def process(batch):
        if not isinstance(batch,dict) or batch.get("schemaVersion") != INPUT_SCHEMA or batch.get("unit") != "mm":
            raise ValueError("Unsupported or non-mm Studio batch contract")
        if batch.get("generator") != "A20StudioEngine.calculate->StudioDieIR.compile":
            raise ValueError("Must originate from actual Studio engine-to-DieIR bridge")
        approval = batch.get("approval",{})
        required = {"studioActivationPermitted","manufacturingApproved",
                    "sourceCADIndependentlyVerifiedByThisBatch","physical3DVerified"}
        if not isinstance(approval,dict) or set(approval)!=required or any(x is not False for x in approval.values()):
            raise ValueError("Forged authority flags")
        records = batch.get("variants")
        models = batch.get("models")
        if not isinstance(records,list) or not isinstance(models,list) or not 1 <= len(records) <= MAX_VARIANTS:
            raise ValueError("Missing/beyond-budget original model batch")
        sources = {x["id"]:x for x in models}
        if len(sources)!=len(models):
            raise ValueError("Repeated source model ID")
        all_summaries=[]
        by_id={}
        by_model=_phase2_defaultdict(list)
        for record in records:
            if record.get("candidateOnly") is not True or record.get("manufacturingApproved") is not False:
                raise ValueError("No Studio activation or manufacture approval allowed")
            model_id=record["sourceId"]
            variant_id=record["variantId"]
            if model_id not in sources or variant_id in by_id or record.get("sourceCoordinateUnit") != "mm":
                raise ValueError("Missing source ID, duplicate variant or wrong unit")
            if record["dieIR"].get("templateId") != model_id:
                raise ValueError("Source and DieIR identities diverge")
            _sha(record.get("sourceSHA256"), "original or module")
            _sha(record.get("sourceArtifactSHA256"), "DieIR artifact")
            if sha_json_php(record["dieIR"]) != record["sourceArtifactSHA256"]:
                raise ValueError("Original source DieIR JSON changed after export")
            tool,notes,primitives,arcs = _shape(record)
            info = analyze({"sourceId":variant_id,"sourceSHA256":record["sourceSHA256"],
                            "sourceArtifactSHA256":record["sourceArtifactSHA256"],
                            "sourceHashScope":record["sourceHashScope"],
                            "entities":tool})
            topo=record["dieIR"].get("panelTopology")
            panel_ids = [p["id"] for p in topo.get("panels", [])] if isinstance(topo,dict) else []
            hinge_ids = [h["entityId"] for h in topo.get("hinges", [])] if isinstance(topo,dict) else []
            if len(panel_ids)!=len(set(panel_ids)) or len(hinge_ids)!=len(set(hinge_ids)):
                raise ValueError("Repeated original source panel/hinge identity")
            info.update({"modelId":model_id,"sourceVariantId":variant_id,
                         "originalEntityCount":len(record["dieIR"]["entities"]),
                         "sourceNativePrimitives":primitives,"nonToolSourceAnnotations":notes,
                         "analyticSourceArcCount":arcs,"panelIds":panel_ids,"hingeEntityIds":hinge_ids,
                         "inputParameters":record["inputParameters"],
                         "originalDieIRSchemaVersion":1,
                         "engineVersion":record["engineVersion"],
                         "originalSourceClaimIsIndependentCADWitness":False})
            by_id[variant_id]=info
            by_model[model_id].append(record)
            all_summaries.append(info)
        if set(by_model)!=set(sources):
            raise ValueError("Missing generated variants for source-declared model")
        family_evidence = {model:_model_observations(model,rows,by_id) for model,rows in by_model.items()}
        grouped=_phase2_defaultdict(list)
        for result in all_summaries:
            grouped[result["structuralFingerprint"]].append(result["sourceId"])
        groups=[]
        for fingerprint,source_ids in sorted(grouped.items()):
            model_ids=sorted({by_id[key]["modelId"] for key in source_ids})
            groups.append({
                "structuralFingerprint":fingerprint,"sourceIds":sorted(source_ids),
                "familyId":None,"evidenceLevel":"structural-candidate-only",
                "familyCandidate":{"modelIds":model_ids,"candidateOnly":True,
                                   "sameTopologyDoesNotProveSameSourceFormula":True,
                                   "confidence":{"score":None,"level":"not-industrially-verified"}},
                "parameterDependencies":{model:family_evidence[model]["parameterDependencies"] for model in model_ids},
                "geometryConstraints":{model:family_evidence[model]["geometryConstraints"] for model in model_ids},
                "topologyInvariants":{model:family_evidence[model]["topologyInvariants"] for model in model_ids},
                "materialDependencies":{model:family_evidence[model]["materialDependencies"] for model in model_ids},
                "validParameterDomain":{model:family_evidence[model]["validParameterDomain"] for model in model_ids},
                "independentWitnesses":[],
            })
        inbox={
            "schemaVersion":OUTPUT_SCHEMA,"units":"mm","approval":dict(APPROVAL),
            "models":all_summaries,"candidateGroups":groups,
        }
        validate_inbox(inbox)
        return inbox, family_evidence

    def merge_batches(batches):
        """Unify independent uploaded JSON batches without changing raw geometry."""
        if not isinstance(batches,list) or not 1 <= len(batches) <= 16:
            raise ValueError("Expected 1..16 explicit Studio batch uploads")
        merged = None
        seen = set()
        model_ids = {}
        for batch in batches:
            if not isinstance(batch,dict) or batch.get("schemaVersion") != INPUT_SCHEMA:
                raise ValueError("Mixed/unsupported uploaded batch version")
            if merged is None:
                merged = {**batch, "models":[], "variants":[]}
            elif (batch.get("unit") != merged.get("unit")
                  or batch.get("generator") != merged.get("generator")
                  or batch.get("approval") != merged.get("approval")):
                raise ValueError("Inconsistent uploaded batch authority, generator or units")
            for model in batch.get("models",[]):
                key=model["id"]
                if key not in model_ids:
                    model_ids[key]=model
                    merged["models"].append(model)
                elif (model_ids[key].get("sourceDefaultDimensions") != model.get("sourceDefaultDimensions")
                      or model_ids[key].get("dimensionSemantics") != model.get("dimensionSemantics")):
                    raise ValueError("Conflicting source model definitions across batches")
            for variant in batch.get("variants",[]):
                key=variant["variantId"]
                if key in seen:
                    raise ValueError("Repeated source variant across uploaded batches")
                seen.add(key)
                merged["variants"].append(variant)
        if len(seen)>MAX_VARIANTS:
            raise ValueError("Merged variant budget exceeded")
        return merged

    def compare_candidates(actual, reference):
        """Detailed exact Source-DieIR artifact and topology parity, no image fit."""
        validate_inbox(actual)
        validate_inbox(reference)
        a={x["sourceId"]:x for x in actual["models"]}
        b={x["sourceId"]:x for x in reference["models"]}
        fields=("sourceSHA256","sourceArtifactSHA256","operationKinds",
                "sourceNativePrimitives","analyticSourceArcCount",
                "topology","panelIds","hingeEntityIds")
        changed=[]
        for key in sorted(a.keys() & b.keys()):
            # JSON object keys are strings. graph.degreeHistogram uses integer
            # degree keys in memory, so canonicalize both before comparison.
            mismatched=[field for field in fields
                        if json.dumps(a[key].get(field),sort_keys=True,ensure_ascii=True)
                        != json.dumps(b[key].get(field),sort_keys=True,ensure_ascii=True)]
            if mismatched:
                changed.append({"sourceId":key,"mismatchedFields":mismatched})
        return {"compared":len(a.keys() & b.keys()),
                "missingInReference":sorted(a.keys()-b.keys()),
                "missingInActual":sorted(b.keys()-a.keys()),
                "changed":changed[:100],
                "changedCount":len(changed),
                "parityVerified":not changed and a.keys()==b.keys(),
                "independentCADWitnessVerified":False,
                "comparisonScope":"same-format-source-linked-DieIR-candidates-not-independent-vendor-oracle"}
    validate_inbox = validate
    return (process, merge_batches, compare_candidates)

@app.cell
def _(mo):
    mo.md("""## Phase 2 | Studio to MoLab batch geometry

    Upload one or more APPROVED source-preserving Studio
    packpoc.geometry-lab.dieir-batch/v1 JSON files.
    The processor reads original A20 -> DieIR entities, CUT/CREASE/PERF,
    analytic ARC, source indices, panel/hinge IDs, L/W/D and materials.

    PRIVACY: Do not upload confidential CAD, unreleased source packages,
    CAD-X private witnesses, customer work or tokens to a public MoLab
    session unless cloud transfer has been separately authorized.
    Nothing is uploaded automatically. The three existing public QA examples
    can still be run as a safe demonstration without any upload.

    Numeric fits are research-only hypotheses, not verified CAD formulas.
    This notebook cannot approve manufacturing or activate a Studio family.
    """)
    return

@app.cell
def _(mo):
    batch_upload = mo.ui.file(
        filetypes=[".json"], multiple=True, kind="area", max_size=64_000_000,
        label="Upload authorized A20-to-DieIR batch JSON (multiple shards supported)",
    )
    reference_upload = mo.ui.file(
        filetypes=[".json"], multiple=False, max_size=64_000_000,
        label="Optional independently produced Studio reference batch or candidate JSON",
    )
    mo.vstack([batch_upload, reference_upload])
    return (batch_upload, reference_upload)

@app.cell
def _(batch_upload, compare_candidates, json, merge_batches, mo, process, reference_upload, time, tracemalloc):
    batch_result = None
    batch_evidence = None
    batch_comparison = None
    batch_measurements = None
    if not batch_upload.value:
        batch_preview = mo.md("No private data uploaded. Public Studio QA fixture demo is above.")
    else:
        try:
            _bytes = [uploaded.contents for uploaded in batch_upload.value]
            if any(not isinstance(raw, bytes) or len(raw)>64_000_000 for raw in _bytes):
                raise ValueError("Upload exceeds 64 MB or is not valid file bytes")
            _batches = [json.loads(raw.decode("utf-8-sig")) for raw in _bytes]
            _merged = merge_batches(_batches)
            tracemalloc.start()
            _start = time.perf_counter()
            batch_result, batch_evidence = process(_merged)
            _peak = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            batch_measurements = {
                "uploadedFiles":len(_bytes),
                "uploadedBytes":sum(len(raw) for raw in _bytes),
                "sourceModels":len(batch_evidence),
                "sourceVariants":len(batch_result["models"]),
                "candidateGroups":len(batch_result["candidateGroups"]),
                "elapsedSeconds":round(time.perf_counter()-_start,5),
                "tracedPeakPythonBytes":_peak,
            }
            if reference_upload.value:
                _reference = json.loads(reference_upload.value[0].contents.decode("utf-8-sig"))
                if _reference.get("schemaVersion")=="packpoc.geometry-lab.dieir-batch/v1":
                    _reference_candidates,_ = process(_reference)
                elif _reference.get("schemaVersion")=="packpoc.geometry-lab.candidate/v1":
                    _reference_candidates = _reference
                else:
                    raise ValueError("Unsupported reference version")
                batch_comparison = compare_candidates(batch_result,_reference_candidates)
            _rows = []
            for model_id,summary in sorted(batch_evidence.items()):
                _rows.append({
                    "model":model_id,
                    "variants":summary["testedVariantCount"],
                    "topology invariant":summary["topologyInvariants"]["stableAcrossObservedVariants"],
                    "fingerprints":summary["topologyInvariants"]["distinctStructuralFingerprints"],
                    "single-axis holdouts": ",".join(
                        axis["parameter"] for axis in summary["parameterDependencies"]
                        if "linearCandidateCount" in axis),
                    "independent CAD witnesses":0,
                })
            batch_preview = mo.vstack([
                mo.md("### Actual uploaded Studio geometry batch analysis"),
                mo.md(f"{batch_measurements['sourceModels']} models, "
                      f"{batch_measurements['sourceVariants']} variants, "
                      f"{batch_measurements['candidateGroups']} groups in "
                      f"{batch_measurements['elapsedSeconds']} s; "
                      f"traced peak {batch_measurements['tracedPeakPythonBytes']:,} Python bytes."),
                mo.ui.table(_rows, label="Observed source/model constraints"),
                mo.md("Reference comparison: " + (
                    json.dumps(batch_comparison, ensure_ascii=False)[:1200]
                    if batch_comparison is not None else "No reference uploaded")),
                mo.md("All production, source CAD approval and activation flags are FALSE."),
            ])
        except Exception as _exc:
            if tracemalloc.is_tracing():
                tracemalloc.stop()
            batch_result = None
            batch_evidence = None
            batch_preview = mo.md("Batch rejected: " + type(_exc).__name__ + ": " + str(_exc)[:250])
    batch_preview
    return (batch_result, batch_evidence, batch_comparison, batch_measurements)

@app.cell
def _(batch_result, json, mo):
    if batch_result is None:
        batch_download = mo.md("Upload an authorized Studio batch to enable candidate export.")
    else:
        batch_download = mo.download(
            data=json.dumps(batch_result,indent=2,ensure_ascii=False).encode("utf-8"),
            filename="studio-geometry-family-candidates-v1.json",
            mimetype="application/json",
            label="Download review-only StudioGeometryLabCandidateInbox JSON",
        )
    batch_download
    return

if __name__ == "__main__":
    app.run()
