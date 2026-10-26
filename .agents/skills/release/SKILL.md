---
name: release
description:
  Use when a new version needs cutting — a CalVer version, changelog entry, git
  tag, GitHub release, and plugin zip assets.
---

# Release

Create a versioned release with changelog, tag, GitHub release, and plugin zip
assets.

## Arguments

None. The version is derived from today's date.

## Instructions

1. Determine the release month: today's `YYYY.0M` (e.g. `2026.11`).

2. Get the current version:

   - Check `git tag --sort=-v:refname | head -1` for the latest tag
   - Tags before `v2026.11.0` used SemVer (`v0.2.0`); ignore them for the MICRO
     calculation

3. Calculate the new version following [CalVer](https://calver.org/)
   `YYYY.0M.MICRO`, as [xarray](https://github.com/pydata/xarray/tags) does —
   see [Version Guidelines](#version-guidelines).

4. Verify readiness:

   - `git status` — must be on `main` with no uncommitted changes
   - `git pull origin main` — must be up to date
   - Warn and stop if not on `main` or if there are uncommitted changes

5. Read `CHANGELOG.md` and check that the `[Unreleased]` section has content.

6. Update `CHANGELOG.md` and `pyproject.toml`:

   - Rename `[Unreleased]` to `[YYYY.0M.MICRO] -- YYYY-MM-DD` (today's date)
   - Add a new empty `[Unreleased]` section above it
   - Set `version = "YYYY.0M.MICRO"` in `pyproject.toml`, then run
     `pixi install` so the editable install reports the new version

7. Commit the release preparation:

   ```bash
   git add CHANGELOG.md pyproject.toml
   git commit -m "chore(release): prepare vYYYY.0M.MICRO" -m "Assisted-by: <harness>:<model>"
   ```

   See the `commit` skill for the trailer format. Omit it entirely if the
   release was cut without AI assistance.

8. Create the git tag:

   ```bash
   git tag -a vYYYY.0M.MICRO -m "vYYYY.0M.MICRO"
   ```

9. Push the commit and tag:

   ```bash
   git push origin main --follow-tags
   ```

10. Build plugin zip assets:

    - For each directory in `plugins/`, create a zip archive
    - **Zip naming convention:**
      - Default: `plugin_name_MM_DD_YYYY.zip` (snake_case plugin name + date)
      - If a release already exists for today (check `gh release list`), append
        a sequence suffix: `plugin_name_MM_DD_YYYY_2.zip`, `_3.zip`, etc.
    - Example: `recipe_workshop_03_30_2026.zip`, or
      `recipe_workshop_03_30_2026_2.zip` for a second release that day
    - Create zips from within the `plugins/` directory so the zip root is the
      plugin folder itself:
      ```bash
      cd plugins && zip -r ../plugin_name_MM_DD_YYYY.zip plugin-dir-name/ -x "*.DS_Store" "*__pycache__/*" "*.pyc" && cd ..
      ```
    - Exclude unnecessary files from zip: `.DS_Store`, `__pycache__`, `*.pyc`

11. Create a GitHub release with plugin zips as assets:

    ```bash
    gh release create vYYYY.0M.MICRO --title "vYYYY.0M.MICRO" \
      --notes "$(cat <<'EOF'
    ## What's Changed

    <extract the relevant section from CHANGELOG.md>

    ## Plugin Assets

    <list each plugin zip with name and description>

    **Full Changelog**: <repo compare URL>/compare/vPREVIOUS...vYYYY.0M.MICRO
    EOF
    )" \
      plugin_name_MM_DD_YYYY.zip
    ```

    Publishing the release triggers `.github/workflows/publish.yml`, which
    uploads the package to PyPI. That job fails unless the tag equals `v` + the
    `pyproject.toml` version.

12. Clean up zip files from the repo root after successful upload.

13. Confirm: "Released vYYYY.0M.MICRO — <release URL>"

## Version Guidelines

Format: `YYYY.0M.MICRO` — four-digit year, zero-padded month, and a MICRO
counter that starts at `0` for the first release of the month and increments for
each further release that month. The version carries no compatibility meaning;
note breaking changes in `CHANGELOG.md`.

| Situation                         | Example                     |
| --------------------------------- | --------------------------- |
| First release in a month          | `v2026.11.0`                |
| Another release in the same month | `v2026.11.0` → `v2026.11.1` |
| First release in a new month      | `v2026.11.1` → `v2026.12.0` |

`pyproject.toml` holds the same string without the `v` (`2026.11.0`).

## Zip Naming Rules

- Plugin directory name is converted to snake_case: `recipe-workshop` →
  `recipe_workshop`
- Date format is `MM_DD_YYYY`
- Sequence suffix only added when multiple releases occur on the same day
- Sequence starts at `_2` (first release of the day has no suffix)

## Rules

- Must be on `main` branch with no uncommitted changes
- Must have content in `[Unreleased]` section of CHANGELOG.md
- Never create a release from a feature branch
- Tag format is always `vYYYY.0M.MICRO` (with `v` prefix, zero-padded month)
- Ask for confirmation before pushing the tag and creating the release
- If CHANGELOG.md doesn't exist or has no `[Unreleased]` section, warn and ask
  how to proceed
- Never commit generated zip files — they are upload artifacts only
- NEVER add "Generated with" or similar marketing lines to the release notes
- NEVER include sensitive information in the release notes or changelog
