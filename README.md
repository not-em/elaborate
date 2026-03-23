# elaborate

[![PyPI version](https://img.shields.io/pypi/v/elaborate)](https://pypi.org/project/elaborate/)
[![Python versions](https://img.shields.io/pypi/pyversions/elaborate)](https://pypi.org/project/elaborate/)
[![License](https://img.shields.io/pypi/l/elaborate)](https://github.com/not-em/elaborate/blob/main/LICENSE)

Look up a PyPI package without leaving the terminal.

```
elaborate pandas
elaborate requests --deps
```

## Example

```
$ elaborate flask

  Flask  v3.1.3  ·  updated 28 days ago
  ────────────────────────────────────────────────────────────

  A simple framework for building complex web applications.

  Requires  Python >=3.9

  Links
    Docs       https://flask.palletsprojects.com/
    GitHub     https://github.com/pallets/flask
    PyPI       https://pypi.org/project/Flask

  ────────────────────────────────────────────────────────────
```

---

## Install

```bash
uv tool install elaborate
```

Then:

```bash
elaborate numpy
elaborate flask --deps
```

## Options

| flag | does |
|---|---|
| `--deps` | show dependencies |
| `--no-color` | disable colour output |

