# Agent instructions

Single source of agent instructions for this repository. `CLAUDE.md` only
imports this file. Add a nested `AGENTS.md` only when a package gains its own
commands or rules; the nearest file then wins. Long reference material stays in
[README.md](README.md); keep this file under 200 lines.

## Project overview

Django 6 + Django Ninja multi-tenant B2B API: JWT auth, organizations, teams,
memberships and invitations. PostgreSQL through `psycopg`, dependencies and
virtualenv through `uv`, API docs at `/api/docs` while the server runs.

| Path | Contents |
| --- | --- |
| `apps/users/` | Custom user model, auth controllers and schemas. |
| `apps/organizations/` | Organizations, teams, memberships, invitations: `controllers/`, `schemas/`, `models/`. |
| `apps/api.py` | The `NinjaAPI` instance; routers mount in `apps/*/controllers/routes.py`. |
| `config/` | Settings: `settings.py`, `settings_test.py` (SQLite tests), `settings_ci.py` (PostgreSQL CI), `migration_lint.py` (migration checks). |
| `tests/` | pytest suite. |
| `scripts/` | Repository tooling: migration checks and renumbering, file-length and agent-doc checks. |

## Commands

Every target is defined in the [Makefile](Makefile); `make help` lists them.
Prerequisites: Python 3.13, pinned in `.python-version` (`pyproject.toml`
accepts 3.12+, but `psycopg-binary` has no wheel for newer interpreters),
[`uv`](https://docs.astral.sh/uv/), and Docker only for the PostgreSQL/Redis
services.

| Task | Command |
| --- | --- |
| Install production dependencies | `make install` |
| Install with dev dependencies | `make dev` |
| Run the development server | `make run` |
| Apply migrations | `make migrate` |
| Create migrations | `make migrations` |
| Run the test suite | `make test` (coverage) or `make test-fast` |
| Lint and type check | `make lint` (ruff, then mypy) |
| Format | `make format` |
| Lint plus tests | `make check` |
| Migration policy checks | `make migrations-check` |
| Renumber conflicting migrations | `make migrations-renumber` then `make migrations-renumber ARGS=--apply` |
| Start PostgreSQL and Redis | `make docker-up` |
| Stop the stack | `make docker-down` |
| Run the pre-commit hooks | `make pre-commit` |

The test suite uses in-memory SQLite (`config/settings_test.py`), so it needs no
database. CI runs the same suite against PostgreSQL with `config/settings_ci`
(see [.github/workflows/ci.yml](.github/workflows/ci.yml)).

`make migrate` and `make run` need a database. By default it is PostgreSQL on
`localhost:5432`, which `make docker-up` starts; without Docker, set
`USE_SQLITE=true` (for example `USE_SQLITE=true make migrate`) to use a local
`db.sqlite3`.

`make lint` runs ruff and then mypy. Ruff must pass. Mypy is advisory in CI
(`continue-on-error`) and currently reports pre-existing errors in
`apps/core/management/commands/seed_data.py`; do not add new ones.

## Code standards

- Lint and formatting come from [pyproject.toml](pyproject.toml): ruff with
  line length 100 and rules `E, F, I, N, W, UP`; mypy on `apps/`.
- Keep Python files under 400 lines; `scripts/check_file_length.py` enforces it
  in pre-commit.
- Follow the existing layout instead of adding a second convention: endpoints in
  `controllers/` routers, request/response models in `schemas/`, persistence in
  `models/`.
- Type-annotate public functions and controller handlers. Validate input at the
  schema boundary; keep business rules in controllers and models.
- Organization-scoped endpoints resolve membership with `get_membership_or_404`
  and gate writes with `require_admin` or `require_owner` from
  `apps/organizations/controllers/utils.py`.
- Reuse the Ninja router composition in `apps/*/controllers/routes.py`; register
  new routers there and in `apps/api.py`, not ad hoc in `config/urls.py`.

## Migrations

- Migrations are linearized, never merged. **Never run `makemigrations --merge`**
  and never add a merge migration.
- Never edit a migration that is already on `main`. Add a new migration instead.
- After you add or change a model or a migration, and before you push, run
  `make migrations-check`.
- On a migration conflict (two leaf nodes, or the same number as `main`), run
  `make migrations-renumber` (dry run), then
  `make migrations-renumber ARGS=--apply`. It renames only your own files after
  the latest migration on `main`.
- When it prints `escalate to owner` (`RunPython`, `RunSQL`, `RemoveField`,
  `RenameField`, `DeleteModel`, `replaces`, or a clashing `AlterField`), stop and
  report it.
- Rule exceptions for django-safe-migrations go in `config/migration_lint.py`.
  Existing findings sit in `scripts/baselines/migration-safety.json`. Inline
  `# safe-migrations: ignore` comments are banned.

## Testing policy

- Tests live in `tests/` and run with pytest (`testpaths` and `python_files` in
  [pyproject.toml](pyproject.toml)); fixtures are in `tests/conftest.py`.
- A behaviour change updates or adds a test that covers it. Doc-only and
  tooling-only changes need the checks above, not a new test.
- Run `make test-fast` before pushing; keep the suite green. CI also runs it
  against PostgreSQL.

## Git and commits

- Conventional Commits: `type(scope): Imperative summary`, subject at most 50
  characters, body wrapped at 72. Valid types include `feat`, `fix`, `chore`,
  `docs`, `test`, `refactor`, `ci`, `build`, `style`, `perf`.
- One logical change per commit; keep `git status` clean before you stop.
- Branch from `main`. Do not rewrite history on shared branches or force-push
  them.

## Agent-run spec workflow

- Work only the issue or spec you were given; its acceptance criteria define
  done. When a task ships a spec under `tasks/specs/`, stay inside the files it
  owns.
- Branch `agent/issue-<n>`. The pull request title is one plain-English,
  sentence-case, imperative line of at most 72 characters, with no spec ID and
  no `type(scope):` prefix.
- Do not push or open the pull request yourself; the agent-run gate pushes after
  the static checks, smoke tests and e2e tests pass.
- Verify with the commands above and report the command and its result.

## Security

- Secrets come from the environment. `.env` is gitignored; copy
  [.env.example](.env.example) and never commit a real key. Pre-commit runs
  `detect-private-key`.
- Production needs `SECRET_KEY`, `DEBUG=False` and `ALLOWED_HOSTS`; see
  [README.md](README.md).
- Never log tokens or passwords, and never disable authentication or permission
  checks to make a request pass.

## Skills

No skills are defined yet. If one is added, it lives in
`.claude/skills/<name>/SKILL.md` with `name` and `description` frontmatter, so
only the description loads until the skill is used. Procedures go in skills,
facts stay here.

## Enforcement

- [.github/workflows/ci.yml](.github/workflows/ci.yml) runs ruff lint and format
  check, pytest with coverage, mypy, the migration checks on pull requests, and
  `scripts/check_agent_docs.py` for this file.
- [.pre-commit-config.yaml](.pre-commit-config.yaml) runs whitespace, large-file
  and secret checks, ruff, the 400-line limit and the migration no-merge check.
