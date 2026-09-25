#!/usr/bin/env python3
"""CLI del grafo de prerrequisitos — Fase 39.

Deriva `knowledge/concept-graph.json` a partir del Coverage Ledger (F15/F38)
y del SDM (F13). Los nodos son unidades `definition`; las aristas son unidades
`cross-reference` con `content.relation: "prerequisite"`. Respeta
`profile.yaml::graph.cycle_policy` (F39 spec §4 R3).

Spec normativa: `references/03-knowledge/concept-graph.md`.

Uso:
    python3 concept_graph.py --workdir PATH [--profile PATH] <subcommand> [args]
    python3 concept_graph.py build
    python3 concept_graph.py routes [--goal <concept_id>] [--domain <d>]
        [--strategy {shortest,broadest,all}]
    python3 concept_graph.py export [--out-dir <dir>]
    python3 concept_graph.py check

Códigos:
    0 = OK
    1 = validación (ciclos con cycle_policy=block)
    2 = uso (paths faltantes)
"""

from __future__ import annotations

import argparse
import importlib.util as _importlib_util
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from heapq import heappop, heappush
from pathlib import Path
from typing import Any, Optional

# Comparte escritura atómica con ledger.py (F38).
_IO_PATH = Path(__file__).resolve().parent / "_io.py"
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

ALLOWED_RELATIONS = {"prerequisite"}
CYCLE_POLICIES = {"block", "allow"}
MAX_LABEL_LEN = 80
SLUG_RE = re.compile(r"[^a-z0-9]+")


# -------------------------------------------------------------------
# Slug + dominio.
# -------------------------------------------------------------------

def slugify(text: str) -> str:
    s = SLUG_RE.sub("-", text.lower()).strip("-")
    return s or "concepto"


def derive_domain(source: dict) -> str:
    vendor = (source.get("vendor") or "").strip()
    product = (source.get("product") or "").strip()
    if vendor and product:
        return f"{vendor}+{product}"
    return "unknown"


# -------------------------------------------------------------------
# Resolución de paths.
# -------------------------------------------------------------------

def _resolve_paths(args: argparse.Namespace) -> dict[str, Path]:
    workdir = Path(args.workdir).resolve()
    profile = Path(args.profile).resolve() if args.profile else workdir / "profile.yaml"
    ledger = workdir / "knowledge" / "ledger.json"
    sdm = workdir / "sdm.json"
    graph = workdir / "knowledge" / "concept-graph.json"
    return {"workdir": workdir, "profile": profile, "ledger": ledger, "sdm": sdm, "graph": graph}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_path(path: Path, what: str) -> None:
    if not path.exists():
        sys.stderr.write(f"FAIL: {what} no encontrado: {path}\n")
        sys.exit(EXIT_USAGE)


# -------------------------------------------------------------------
# Carga de profile (YAML opcional) — sólo lee graph.cycle_policy.
# -------------------------------------------------------------------

def _load_cycle_policy(profile_path: Path) -> str:
    """Lee graph.cycle_policy del profile YAML. Si el archivo falta o no
    contiene la clave, devuelve el default `block`."""
    if not profile_path.exists():
        return "block"
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.stderr.write(
            "WARNING: PyYAML ausente; usando cycle_policy=block por default\n"
        )
        return "block"
    try:
        with profile_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        sys.stderr.write(f"WARNING: no se pudo parsear {profile_path}: {e}; default block\n")
        return "block"
    policy = ((data or {}).get("graph") or {}).get("cycle_policy") or "block"
    if policy not in CYCLE_POLICIES:
        sys.stderr.write(
            f"WARNING: cycle_policy={policy!r} no está en {sorted(CYCLE_POLICIES)}; usando block\n"
        )
        return "block"
    return policy


# -------------------------------------------------------------------
# Construcción del grafo.
# -------------------------------------------------------------------

def build_graph(ledger: dict, sdm: dict, cycle_policy: str) -> dict:
    """Deriva el grafo (R1–R8 del spec §4). Devuelve el payload completo."""
    source_meta = sdm.get("source", {})
    domain_global = derive_domain(source_meta)

    nodes_by_id: dict[str, dict] = {}
    nodes: list[dict] = []
    seen_node_keys: set[tuple[str, str]] = set()

    # R1: nodos desde units type=definition.
    # ADR-0003: el concept_id canónico se declara explícitamente en `content.term`
    # para mantener la disciplina de fuente única. Si falta, fallback a un slug
    # derivado de las primeras 3 palabras del texto (no de la oración completa).
    for entry in ledger.get("entries", []):
        if entry.get("type") != "definition":
            continue
        content = entry.get("content") or {}
        text = content.get("text") or entry.get("unit_id")
        term = content.get("term")
        if term:
            concept_id = slugify(term)[:64]
        else:
            # Fallback: primeras 3 palabras del texto.
            words = (text or "").split()[:3]
            concept_id = slugify(" ".join(words))[:64]
            sys.stderr.write(
                f"WARNING: definition unit_id={entry['unit_id']} sin content.term; "
                f"derivado concept_id={concept_id!r} de las primeras 3 palabras\n"
            )
        node_key = (domain_global, concept_id)
        if node_key in seen_node_keys:
            sys.stderr.write(
                f"WARNING: concepto duplicado {concept_id!r} en dominio {domain_global!r} "
                f"(origen unit_id={entry['unit_id']}); segundo omitido\n"
            )
            continue
        seen_node_keys.add(node_key)
        label = (text or "")[:MAX_LABEL_LEN]
        nodes_by_id[concept_id] = {
            "concept_id": concept_id,
            "domain": domain_global,
            "definition_unit_id": entry["unit_id"],
            "section_path": entry.get("source_section_path", ""),
            "label": label,
        }
        nodes.append(nodes_by_id[concept_id])

    # R2: aristas desde units type=cross-reference con relation=prerequisite.
    edges: list[dict] = []
    edge_keys: set[tuple[str, str]] = set()
    dangling: list[dict] = []

    for entry in ledger.get("entries", []):
        if entry.get("type") != "cross-reference":
            continue
        content = entry.get("content") or {}
        if content.get("relation") != "prerequisite":
            continue
        target = content.get("target_concept")
        if not target:
            sys.stderr.write(
                f"WARNING: cross-reference unit_id={entry['unit_id']} tiene relation=prerequisite "
                f"sin target_concept; omitida\n"
            )
            continue
        # R2 (ADR-0003): el `from_concept_id` debe declararse explícitamente
        # en la cross-reference. Sin inferencia desde section_path.
        from_id = content.get("from_concept")
        if not from_id:
            sys.stderr.write(
                f"WARNING: cross-reference unit_id={entry['unit_id']} tiene relation=prerequisite "
                f"sin from_concept; omitida (ADR-0003 exige declaración explícita)\n"
            )
            continue
        if target not in nodes_by_id:
            dangling.append({
                "from_concept_id": from_id,
                "to_concept_id": target,
                "source_unit_id": entry["unit_id"],
            })
            sys.stderr.write(
                f"WARNING: arista colgante {from_id} → {target} (concepto destino no existe); "
                f"registrada en dangling_edges\n"
            )
            continue
        if from_id not in nodes_by_id:
            dangling.append({
                "from_concept_id": from_id,
                "to_concept_id": target,
                "source_unit_id": entry["unit_id"],
            })
            sys.stderr.write(
                f"WARNING: arista con from_concept_id={from_id!r} inexistente (unit_id={entry['unit_id']}); "
                f"registrada en dangling_edges\n"
            )
            continue
        key = (from_id, target)
        if key in edge_keys:
            continue
        edge_keys.add(key)
        edges.append({
            "from_concept_id": from_id,
            "to_concept_id": target,
            "relation": "prerequisite",
            "source_unit_id": entry["unit_id"],
        })

    # R7 + R8: ordenar.
    nodes.sort(key=lambda n: (n["domain"], n["concept_id"]))
    edges.sort(key=lambda e: (e["from_concept_id"], e["to_concept_id"]))

    # Detección de ciclos (R3).
    cycles = _detect_cycles(nodes_by_id, edges, cycle_policy)

    # Rutas (R5): por dominio, shortest + broadest para cada goal.
    routes = _compute_routes(nodes_by_id, edges)

    return {
        "schema_version": "1.0.0",
        "source": {
            "id": source_meta.get("id", "<unknown>"),
            "hash": source_meta.get("hash", "0" * 64),
            "vendor": source_meta.get("vendor"),
            "product": source_meta.get("product"),
        },
        "domain": domain_global,
        "nodes": nodes,
        "edges": edges,
        "cycles": cycles,
        "routes": routes,
        "dangling_edges": dangling,
        "build_metadata": {
            "built_at": datetime.now(timezone.utc).isoformat(),
            "cycle_policy": cycle_policy,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    }


def _adjacency(nodes: dict[str, dict], edges: list[dict]) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        adj[e["from_concept_id"]].append(e["to_concept_id"])
    return adj


def _detect_cycles(nodes: dict[str, dict], edges: list[dict], cycle_policy: str) -> list[dict]:
    """DFS iterativo con marcas white/gray/black; reporta ciclos.
    Solo analiza aristas entre nodos existentes (dangling_edges ya se filtraron)."""
    adj = _adjacency(nodes, edges)
    color: dict[str, str] = {n: "white" for n in nodes}
    stack: list[str] = []
    cycles: list[dict] = []
    seen_cycle_keys: set[tuple[str, ...]] = set()

    def _cycle_key(path: list[str]) -> tuple[str, ...]:
        # normaliza para deduplicación: rota al menor elemento primero
        if not path:
            return tuple()
        i = path.index(min(path))
        return tuple(path[i:] + path[:i])

    for start in sorted(nodes):
        if color[start] != "white":
            continue
        color[start] = "gray"
        stack.append(start)
        local: list[str] = [start]
        i = 0
        while i < len(local):
            node = local[i]
            children = adj.get(node, [])
            progressed = False
            for child in children:
                if child not in color:
                    continue
                if color[child] == "gray":
                    j = local.index(child)
                    cyc = local[j:] + [child]
                    key = _cycle_key(cyc[:-1])
                    if key and key not in seen_cycle_keys:
                        seen_cycle_keys.add(key)
                        cycles.append({
                            "cycle": cyc,
                            "policy": cycle_policy,
                            "resolved": False,
                        })
                elif color[child] == "white":
                    color[child] = "gray"
                    local.append(child)
                    progressed = True
                    break
            if not progressed:
                color[node] = "black"
                local.pop()
            i = len(local) - 1 if progressed else i + 1
        # vaciar stack
        while stack:
            n = stack.pop()
            color[n] = "black"

    return cycles


def _compute_routes(nodes: dict[str, dict], edges: list[dict]) -> list[dict]:
    """R5: shortest + broadest por dominio, goal = cada nodo del dominio."""
    adj = _adjacency(nodes, edges)
    in_neighbors: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        in_neighbors[e["to_concept_id"]].append(e["from_concept_id"])

    # Agrupa nodos por dominio.
    domains: dict[str, list[str]] = defaultdict(list)
    for cid, n in nodes.items():
        domains[n["domain"]].append(cid)

    out_degree = {cid: len(adj.get(cid, [])) for cid in nodes}

    routes: list[dict] = []

    for domain, cids in sorted(domains.items()):
        # Cada nodo del dominio es un goal potencial; las rutas llevan
        # al goal desde cualquier otro nodo del dominio.
        for goal in sorted(cids):
            # Shortest (Dijkstra).
            shortest = _shortest_path_to_goal(adj, goal, set(cids))
            if shortest:
                routes.append({
                    "domain": domain,
                    "goal_concept_id": goal,
                    "strategy": "shortest",
                    "path": shortest,
                    "length": len(shortest),
                })

            # Broadest (DFS con poda): busca el camino más largo en número de
            # nodos visitados (sin repetir) hasta el goal.
            broadest = _broadest_path_to_goal(adj, goal, set(cids), in_neighbors, out_degree)
            if broadest and (not shortest or broadest != shortest):
                routes.append({
                    "domain": domain,
                    "goal_concept_id": goal,
                    "strategy": "broadest",
                    "path": broadest,
                    "length": len(broadest),
                })

    return routes


def _shortest_path_to_goal(adj: dict[str, list[str]], goal: str, domain: set[str]) -> list[str]:
    """Dijkstra inverso (goal → orígenes) para encontrar el camino más corto
    desde cualquier nodo del dominio hasta `goal`."""
    # Estado: (dist, node, path).
    heap: list[tuple[int, str, list[str]]] = [(0, goal, [goal])]
    seen: dict[str, int] = {goal: 0}
    while heap:
        d, node, path = heappop(heap)
        if d > seen.get(node, float("inf")):
            continue
        # Si llegamos a un nodo del dominio distinto del goal, devolvemos el path.
        if node != goal and node in domain:
            return path
        for prev in []:  # placeholder; usamos la adj invertida abajo
            pass
        break
    # Implementación real: usamos adj normal para explorar from→to;
    # hacemos BFS desde cada nodo del dominio hacia goal.
    best: Optional[list[str]] = None
    for start in domain:
        if start == goal:
            best = [goal]
            continue
        # BFS start → goal.
        visited = {start: [start]}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            if cur == goal:
                if best is None or len(visited[cur]) < len(best):
                    best = visited[cur]
                break
            for nxt in adj.get(cur, []):
                if nxt not in visited:
                    visited[nxt] = visited[cur] + [nxt]
                    queue.append(nxt)
    return best or []


def _broadest_path_to_goal(
    adj: dict[str, list[str]],
    goal: str,
    domain: set[str],
    in_neighbors: dict[str, list[str]],
    out_degree: dict[str, int],
) -> list[str]:
    """DFS que prefiere nodos con más salidas (ramificación), maximizando
    el número de nodos visitados antes de llegar al goal."""
    best: list[str] = []

    def dfs(node: str, visited: set[str], path: list[str]) -> None:
        nonlocal best
        if node == goal:
            if len(path) > len(best):
                best = list(path)
            return
        # Vecinos en el dominio (o el goal) ordenados por out_degree desc.
        neighbors = [n for n in adj.get(node, []) if n not in visited and (n in domain or n == goal)]
        neighbors.sort(key=lambda c: -out_degree.get(c, 0))
        for nxt in neighbors:
            visited.add(nxt)
            path.append(nxt)
            dfs(nxt, visited, path)
            path.pop()
            visited.discard(nxt)

    for start in sorted(domain):
        if start == goal:
            continue
        dfs(start, {start}, [start])

    return best


# -------------------------------------------------------------------
# Subcomandos.
# -------------------------------------------------------------------

def cmd_build(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["ledger"], "ledger.json")
    _require_path(paths["sdm"], "sdm.json")

    cycle_policy = _load_cycle_policy(paths["profile"])
    ledger = _read_json(paths["ledger"])
    sdm = _read_json(paths["sdm"])

    graph = build_graph(ledger, sdm, cycle_policy)

    if graph["cycles"] and cycle_policy == "block":
        sys.stderr.write(
            f"FAIL: cycle_policy=block y se detectaron {len(graph['cycles'])} ciclo(s); "
            f"revisa el ledger (cross-references con relation=prerequisite).\n"
        )
        for c in graph["cycles"]:
            sys.stderr.write(f"  - {' → '.join(c['cycle'])}\n")
        return EXIT_VALIDATION

    _atomic_write_json(paths["graph"], graph)
    sys.stdout.write(
        f"OK — build {paths['graph']} (nodes={len(graph['nodes'])}, "
        f"edges={len(graph['edges'])}, cycles={len(graph['cycles'])}, "
        f"routes={len(graph['routes'])}, dangling={len(graph['dangling_edges'])}, "
        f"cycle_policy={cycle_policy})\n"
    )
    return EXIT_OK


def cmd_routes(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["graph"], "concept-graph.json")
    graph = _read_json(paths["graph"])

    routes = graph.get("routes", [])
    if args.domain:
        routes = [r for r in routes if r["domain"] == args.domain]
    if args.goal:
        routes = [r for r in routes if r["goal_concept_id"] == args.goal]
    if args.strategy and args.strategy != "all":
        routes = [r for r in routes if r["strategy"] == args.strategy]

    if not routes:
        sys.stdout.write("(sin resultados)\n")
        return EXIT_OK

    for r in routes:
        sys.stdout.write(
            f"  domain={r['domain']} goal={r['goal_concept_id']} "
            f"strategy={r['strategy']} length={r['length']} path={' → '.join(r['path'])}\n"
        )
    return EXIT_OK


def cmd_export(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["graph"], "concept-graph.json")
    graph = _read_json(paths["graph"])

    out_dir = Path(args.out_dir).resolve() if args.out_dir else paths["workdir"] / "knowledge" / "concepts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Agrupa nodos y aristas por dominio.
    nodes_by_domain: dict[str, list[dict]] = defaultdict(list)
    for n in graph.get("nodes", []):
        nodes_by_domain[n["domain"]].append(n)

    # Mapa concept_id → domain para clasificar aristas.
    concept_domain: dict[str, str] = {n["concept_id"]: n["domain"] for n in graph.get("nodes", [])}
    edges_by_domain: dict[str, list[dict]] = defaultdict(list)
    for e in graph.get("edges", []):
        domain = concept_domain.get(e["from_concept_id"], graph["domain"])
        edges_by_domain[domain].append(e)

    written: list[Path] = []
    for domain, nodes in sorted(nodes_by_domain.items()):
        safe_domain = domain.replace("+", "_").replace("/", "_") or "unknown"
        out_path = out_dir / safe_domain / "graph.mmd"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        node_ids = {n["concept_id"] for n in nodes}
        edges = [e for e in edges_by_domain.get(domain, []) if e["from_concept_id"] in node_ids and e["to_concept_id"] in node_ids]
        mmd = _render_mermaid(domain, nodes, edges, graph.get("cycles", []))
        out_path.write_text(mmd, encoding="utf-8")
        written.append(out_path)

    sys.stdout.write(f"OK — export {len(written)} archivo(s):\n")
    for p in written:
        sys.stdout.write(f"  - {p}\n")
    return EXIT_OK


def _render_mermaid(domain: str, nodes: list[dict], edges: list[dict], cycles: list[dict]) -> str:
    lines: list[str] = [f"flowchart LR"]
    if cycles:
        cyc_str = "; ".join("→".join(c["cycle"]) for c in cycles)
        lines.append(f"%% cycles: {cyc_str}")
    lines.append(f"    subgraph {domain.replace('+', '_').replace('/', '_')}[\"{domain}\"]")
    for n in nodes:
        nid = n["concept_id"].replace("-", "_")
        label = n["label"].replace('"', "'")
        lines.append(f"        {nid}[\"{label}\"]")
    for e in edges:
        src = e["from_concept_id"].replace("-", "_")
        dst = e["to_concept_id"].replace("-", "_")
        lines.append(f"        {src} -->|prereq| {dst}")
    lines.append("    end")
    return "\n".join(lines) + "\n"


def cmd_check(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    _require_path(paths["graph"], "concept-graph.json")
    graph = _read_json(paths["graph"])

    cycle_policy = graph.get("build_metadata", {}).get("cycle_policy", "block")
    cycles = graph.get("cycles", [])
    dangling = graph.get("dangling_edges", [])

    sys.stdout.write(f"Check: {paths['graph']} (cycle_policy={cycle_policy})\n")
    sys.stdout.write(f"  Cycles: {len(cycles)}\n")
    for c in cycles:
        sys.stdout.write(f"    - {' → '.join(c['cycle'])}\n")
    sys.stdout.write(f"  Dangling edges: {len(dangling)}\n")
    for d in dangling:
        sys.stdout.write(f"    - {d['from_concept_id']} → {d['to_concept_id']}\n")

    has_issues = bool(cycles) or bool(dangling)
    if has_issues and args.strict:
        sys.stdout.write("\nFAIL: --strict activado y hay desviaciones\n")
        return EXIT_VALIDATION
    return EXIT_OK


# -------------------------------------------------------------------
# Parser CLI.
# -------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="concept_graph.py",
        description="CLI del grafo de prerrequisitos (Fase 39). Deriva knowledge/concept-graph.json desde el ledger + SDM.",
    )
    p.add_argument("--workdir", default=".", help="Raíz del workdir (default: directorio actual).")
    p.add_argument("--profile", help="Override de la ruta a profile.yaml.")

    sub = p.add_subparsers(dest="subcommand", required=True)

    p_build = sub.add_parser("build", help="Deriva el grafo y escribe concept-graph.json.")
    p_build.set_defaults(func=cmd_build)

    p_routes = sub.add_parser("routes", help="Imprime las rutas de lectura.")
    p_routes.add_argument("--goal", help="Filtra por goal_concept_id.")
    p_routes.add_argument("--domain", help="Filtra por dominio.")
    p_routes.add_argument("--strategy", choices=["shortest", "broadest", "all"], default="all")
    p_routes.set_defaults(func=cmd_routes)

    p_export = sub.add_parser("export", help="Exporta el grafo a Mermaid por dominio.")
    p_export.add_argument("--out-dir", help="Directorio de salida (default: workdir/knowledge/concepts).")
    p_export.set_defaults(func=cmd_export)

    p_check = sub.add_parser("check", help="Detecta ciclos y aristas colgantes sin escribir.")
    p_check.add_argument("--strict", action="store_true", help="Exit 1 si hay desviaciones.")
    p_check.set_defaults(func=cmd_check)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
