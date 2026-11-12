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

    return (analyze, candidates, from_public_fixture, hashlib, json, time, tracemalloc)

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

if __name__ == "__main__":
    app.run()
