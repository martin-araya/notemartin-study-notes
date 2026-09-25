# Eval — Fase 42: reglas de fidelidad

Verifica los 3 criterios del roadmap + no-regresión F15/F37/F38/F39/F40/F41.

## Criterios del roadmap

1. **Todo contenido externo va en bloque identificable.**
   - Verifica que frases "externas" (e.g., "mayoría", "RFC", "generalmente") estén dentro de `:::external`.
   - Verifica que los diagramas Mermaid estén dentro de `:::derived`.
2. **Fuente incompleta → nota declara ausencia (regla de la duda).**
   - Verifica palabras prohibidas (`probablemente`, `típicamente`, etc.) fuera de bloques marcados.
   - Verifica formas aceptables de declarar ausencia cuando la fuente es silenciosa.
3. **Ningún valor técnico aparece sin respaldo en el ledger.**
   - Parsea defaults, parámetros, códigos de error y versiones.
   - Cada valor debe tener entry en el ledger (F15/F38) del tipo correspondiente.

## Estructura

```
evals/fidelity-sample/
├── README.md
├── build_fixtures.py          # stdlib puro
├── fixtures/
│   ├── note-good.md                # 3 bloques (source/derived/external) + ledger con respaldo
│   ├── note-derived-missing.md     # bloque :::derived sin ledger entry
│   ├── note-external-missing.md    # contenido externo sin :::external + mermaid sin :::derived
│   ├── note-doubtful.md            # palabras prohibidas
│   ├── note-incomplete-good.md     # declara ausencia correctamente
│   ├── note-incomplete-bad.md      # completa lo que la fuente omite
│   ├── ledger-good.json
│   ├── ledger-missing.json
│   ├── ledger-incomplete.json
│   └── source-incomplete.json      # SDM sin rango de shared_buffers
├── expected/
└── run_eval.py
```

## Uso

```bash
python3 evals/fidelity-sample/build_fixtures.py   # genera fixtures
python3 evals/fidelity-sample/run_eval.py         # verifica los 3 criterios
```

Exit codes: `0` PASS, `1` FAIL, `2` usage.

## Diseño

- **Criterio 1** — heurística: busca palabras/frases que sugieren contenido "externo" o "derivado" y verifica que estén en bloques marcados.
- **Criterio 2** — lista cerrada de palabras prohibidas + lista cerrada de frases aceptables de ausencia.
- **Criterio 3** — regex sobre defaults/parámetros/errores/versiones; búsqueda en el ledger por tipo y valor.

## Sin regresión

```bash
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json
python3 evals/information-units-sample/run_eval.py
python3 evals/ledger-operativo-sample/run_eval.py
python3 evals/concept-graph-sample/run_eval.py
python3 evals/terminology-sample/run_eval.py
python3 evals/conflicts-sample/run_eval.py
python3 evals/fidelity-sample/run_eval.py
```
