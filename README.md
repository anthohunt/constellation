# Constellation

Constellation is a personal intelligence-watch pipeline run by AI agents. Agents search a subject along several axes, other agents check each finding against its sources, and the result is published as a bilingual 3D map that the reader rates. The ratings feed the next run: the pipeline learns what this reader cares about.

The agent instructions and most comments are written in French.

## What is in this repository

| Folder | Content |
|---|---|
| `server/` | The website: sign-up and profile form, rating page, 3D map, admin console, email sending. Node.js 22, no npm dependency. |
| `viewer/` | The 3D map template (`constellation.template.html`, three.js) and the Python scripts that build its data from a run (`build_constellation.py`, `build_publie.py`, `gen-template-publie.py`, `deployer-eval.sh`). |
| `pipeline/` | The pipeline graph `workflows/veille.json` (8 steps, each followed by its check) and the blocking validators run at the end of each step (`validate.py`, `validators/etape*.py`). |
| `skills/` | The instructions given to each agent role (hunters, verifiers, writer, publisher…), one folder per role with its `SKILL.md`. |
| `examples/demo-run/` | A small invented run (home solar energy, 9 findings) and the map built from it. All its content is fictional. |

## How it fits with flux

Constellation does not include its own engine. The pipeline graph is executed by **flux**, a separate repository that launches one agent per node, checks its deliverables and moves to the next node. Install flux first, then point it at this repository (see `.env.example`):

```bash
export FLUX_WORKFLOWS_DIR=$CONSTELLATION_HOME/pipeline/workflows
export FLUX_SKILLS_DIR=$CONSTELLATION_HOME/skills
```

The exact interface (launch command, graph format, environment variables) is documented in the flux repository.

## Quick start: the website and the demo map

Requirements: Docker, or Node.js 22 and Python 3.10+. The step validators also need `aspell` with its French dictionary (`apt install aspell aspell-fr`).

```bash
git clone <this repository> constellation && cd constellation
cp .env.example .env            # edit at least ADMIN_PASS and SESSION_SECRET
mkdir -p data veille-owners
docker compose -f docker-compose.example.yml up -d --build
```

Open `http://localhost:8080/` for the profile form and `http://localhost:8080/constellation.html` for the demo map.

To build a map from a run and deploy it as a rating page:

```bash
python3 viewer/build_constellation.py examples/demo-run      # writes examples/demo-run/constellation/
CONSTELLATION_DATA=./data CONSTELLATION_BASE_URL=http://localhost:8080 \
  bash viewer/deployer-eval.sh examples/demo-run              # serves /c/demo-run-eval/
CONSTELLATION_DATA=./data bash viewer/poser-tutoriel.sh       # guided tour shown on a reader's first visit
```

Without Docker: `cd server && DATAROOT=../data PORT=8080 node server.js`.

## Running a full watch

A full run needs flux, Claude Code (or another engine declared in flux) and a paid model subscription or API key: every step launches agents. The steps are:

1. Prepare the run (profile, subject, casting of hunters) — skill `veille-start`.
2. Hunt: one hunter per axis, plus two cross-cutting hunters and a scout; then a check by fresh agents.
3. Assemble: group findings into stories, write the short text of each, build the map.
4. Notify the reader.
5. The reader rates the map (human step).
6. Feedback: rules per axis are induced from the ratings.
7. Publish the deliverables (map, digest, newsletter).
8. Review of the run.

The demo above stops before step 2: everything from the hunt onward calls a model.

## Settings

All machine-specific values (domain, paths, keys, mail settings) are environment variables, listed with example values in `.env.example`. Nothing in the code points to a real server.

Optional services, each enabled only when its key is set: Brevo (fallback email relay), PostHog (visit statistics, behind a consent banner), Groq or Anthropic API (axis suggestions in the form when Claude Code is not installed).

## Not included

- `skills/veille-style/reference-redaction.md`: the writing reference was a transcript of a third-party video and cannot be redistributed. The file explains what to put there.
- `docs/criteres-juges.md`: the scoring grid used by the verifiers, referenced by `veille-launch-researcher`, is not part of this release.
- The optional domain-memory scripts (`veille-memory.py`, `build-source-ledger.py`, `build-watch-preferences.py`) referenced by `veille-start` and `veille-publish`: the steps that call them are skipped when `VEILLE_SCRIPTS` is empty.

## License

- Code: Apache License 2.0 (`LICENSE`, `NOTICE`).
- Texts, agent instructions (`skills/`), documents and diagrams: Creative Commons Attribution 4.0 International (`LICENSE-docs`).
- Third-party components and their licenses are listed in `NOTICE` (three.js, MIT; marked, MIT; fonts under SIL OFL, loaded from Google Fonts).
