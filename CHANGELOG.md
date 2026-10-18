# Changelog

We follow [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/). HoryHours Notes is a single **Desktop** surface.

<details>
<summary>To see more about versioning, expand this.</summary>

Every version string starts with `v` (required), e.g. `v0.1.0-stable`, `v0.1.0-beta`.

The installable surface here is **Desktop** (Python + PyQt6). Other Option apps swap in their own names — e.g. **CLI**, **GNOME**, **Web** — according to what they actually ship.

| Part | What you install | Example |
| --- | --- | --- |
| **Desktop** | `horyhours-notes` floating quick-note app | `v0.1.0-beta` |

With one surface there is no `m` in the tag and no per-surface sections — just the version notes.

Each release heading is the version and date (`## v0.1.0-beta · 11/08/2026`); under it, a short summary ends with a plain sentence like: “This version was made for Desktop with a beta release channel on 11/08/2026 (v0.1.0-beta).”

### What the channel suffix means

| Suffix | In plain words |
| --- | --- |
| **-alpha** | Very early. Expect missing pieces and lots of bugs. |
| **-beta** | Mostly there, but still rough. Fine to try; not the “official” install. |
| **-stable** | Ready for daily use. This is what we put on GitHub Releases and the AUR. |

We only call something **stable** when we mean it. The first public iteration stays **beta** while desktop and compositor behaviour settles.

</details>

## v0.1.2-beta · 17/10/2026

Histórico bem maior, guardando até 1024 partidas arquivadas. This version was made for Desktop with a beta release channel on 17/10/2026 (v0.1.2-beta).

- Raised the local match history cap from 124 to 1024 entries (`MAX_HISTORY_ENTRIES`), with the history counter and trimming following the new limit.
- Registered the Desktop application version as `0.1.2-beta`.

## v0.1.1-beta · 11/08/2026

Tarefas mais leves, legíveis e fáceis de consultar durante a partida. This version was made for Desktop with a beta release channel on 11/08/2026 (v0.1.1-beta).

- Reworked the tasks dialog into a wider but still compact reference, with the map selector and view switcher sharing one tidy control row.
- Simplified category and room sections: task locations now sit inline with each task, removing the stacked cards that made the list feel cramped.
- Refined surface spacing, radii and hierarchy so category counts, map selection and task names scan more naturally.
- Registered the Desktop application version as `0.1.1-beta`.

## v0.1.0-beta · 11/08/2026

Floating local notes became a compact Among Us match companion. This version was made for Desktop with a beta release channel on 11/08/2026 (v0.1.0-beta).

- The draggable `✦` bubble expands into a dark quick-note editor, persists its note, position and size locally, and honors reduced-motion requests.
- `Ctrl+Shift+Space` toggles the note globally on X11/XWayland; native Wayland keeps the focused-window fallback.
- The Skeld reference lists common, short and long tasks in Portuguese, with locations and visual-task markers.
- `Concluído` archives a non-empty match note and starts a fresh one; the local history retains up to 124 matches.
- History supports individual `.txt` exports, an all-matches `.zip` export, and confirmed per-match removal.
- Various other UI polish, drag behaviour, and compositor compatibility tweaks
