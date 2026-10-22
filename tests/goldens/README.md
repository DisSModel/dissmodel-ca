# TerraME reference values for the ca models

An extract of the `ca` suite of
[`terrame-goldens`](https://github.com/LambdaGeo/terrame-goldens) v0.1.0:
what TerraME 2.0.1 computed running the models of the
[`ca`](https://github.com/TerraME/ca) package (commit `854a5c4`) with default
parameters.

- `grids/<case>.csv.gz`: the state of every cell (columns `step, y, x0, x1,
  ...`, TerraME's values) for the deterministic models, at every step up to
  10 and then at steps 20, 50, 100, ... and the final one. Step 0 is the
  state the test starts from. `grids/cases.csv` lists model, arguments,
  seed, final time and size of each case.
- `ensembles.csv.gz`: for the stochastic models, the number of cells in each
  state at a few steps, for seeds 1 to 50 (columns `case, value, step, seed,
  count`). For SolidDiffusion, `atom1_right` and `atom2_left` count the atoms
  past the middle column.
- `reference.json`: the source version, the package commit, the steps kept
  and the SHA-256 of each source file.

To make the extract again from a copy of `terrame-goldens`:

```bash
python tests/goldens/make_reference.py /path/to/terrame-goldens
```

The values are the output of TerraME and of the `ca` package (INPE and
TerraLAB/UFOP); the extract is offered under CC-BY-4.0, as the goldens it
comes from.
