# trim-spaces-in-paths (pre-commit hook)

![CI](https://github.com/leodrivera/pre-commit-trim-spaces-in-paths/actions/workflows/ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/leodrivera/pre-commit-trim-spaces-in-paths/graph/badge.svg)

A `pre-commit` hook that **auto-fixes** file and folder names with unwanted spaces.

- Always trims **leading/trailing spaces** from each path component.
- Optionally handles **internal spaces** with `--internal-style`:
  - `none` (default): do not touch internal spaces
  - `collapse`: collapse multiple spaces to a single space
  - `underscore`: replace **all** internal spaces with `_`
  - `remove`: remove **all** internal spaces entirely

If multiple staged paths normalize to the **same** destination, the hook blocks and reports a conflict.

---

## Why?

Paths with leading/trailing spaces or weird spacing inside components cause headaches across OSes, shells, and tools. Git does allow them, but you probably don't want them.

This hook cleans up filenames **before** the commit lands.

---

## Quick start

1. **Install pre-commit** (if you haven't):

   ```bash
   pip install pre-commit
   pre-commit --version
   ```

2. **Add this repo to your project's .pre-commit-config.yaml**:

   ```yaml
   repos:
     - repo: https://github.com/leodrivera/pre-commit-trim-spaces-in-paths
       rev: v1.0.0
       hooks:
         - id: trim-spaces-in-paths
           # Choose one behavior (default is none):
           # args: ["--internal-style=collapse"]
           # args: ["--internal-style=underscore"]
           # args: ["--internal-style=remove"]
   ```

3. **Install the hook**:

   ```bash
   pre-commit install
   ```

Now any commit will run the hook and rename staged paths as needed.

---

## Usage example

Suppose you accidentally create and stage a file with leading/trailing and internal spaces:

```bash
git add " reports /  My   Report .ipynb "
git commit -m "Add messy file"
```

With `--internal-style=collapse`, the hook will auto-fix:

```
🔧 Renamed (internal-style=collapse):
  - ' reports /  My   Report .ipynb ' -> 'reports/My Report .ipynb'
```

The commit is then blocked once, so you can review the change.
Re-run `git commit` and it will succeed with the corrected filename.

### Other modes:

- **none**: ` reports / My Report .ipynb ` → `reports/My Report .ipynb`
- **collapse**: ` reports / My Report .ipynb ` → `reports/My Report .ipynb`
- **underscore**: ` reports / My Report .ipynb ` → `reports/My__Report_.ipynb`
- **remove**: ` reports / My Report .ipynb ` → `reports/MyReport.ipynb`

---

## Hook ID and options

**Hook ID**: `trim-spaces-in-paths`

**Args**:
- `--internal-style=none|collapse|underscore|remove`

---

## Notes & caveats

- The hook renames only the staged paths passed by pre-commit.
- Uses `git mv` when possible (keeps history), otherwise falls back to `os.replace` + `git add`.
- Exits with 3 if it changes filenames (so pre-commit re-runs), or 1 on conflicts.
- On Windows, creating files with trailing spaces is not possible — but the hook can still clean them if they exist in Git history.

---

## Development

### Setup development environment

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Run tests

```bash
poetry run pytest -q
```

### Lint

```bash
poetry run ruff check .
```

---

## License

MIT
