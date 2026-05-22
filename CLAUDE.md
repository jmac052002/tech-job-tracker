# Tech Job Tracker — Android
**Stack:** React Native · Expo · TypeScript · Python · FastAPI  
**Platform:** Android only (Expo managed workflow)  
**Developer:** Joseph McCoy · github.com/jmac052002

---

## Current Status

### Backend — COMPLETE ✅
- **Routes:** `POST /api/jobs` · `GET /api/jobs` · `GET /api/jobs/{id}` · `PUT /api/jobs/{id}` · `DELETE /api/jobs/{id}`
- **Model:** `JobApplication` — id, company, position, status, date_applied, notes, follow_up_date
- **Database:** SQLite (dev) · PostgreSQL-ready via DATABASE_URL env var
- **Auth:** Not yet implemented — planned (JWT or AWS Cognito under evaluation)
- **Migrations:** Using `Base.metadata.create_all()` on startup — Alembic needed before production
- **Docs:** Auto-generated Swagger UI at `http://localhost:8000/docs`

### Frontend — NOT STARTED
- Expo scaffold not yet created
- `mobile/` directory does not exist yet
- Next session will scaffold Expo Router project

### Known Issues / Tech Debt
- No authentication on any endpoint — all routes are currently open
- `Base.metadata.create_all()` is a dev shortcut — needs Alembic before production
- CORS currently set to `allow_origins=["*"]` — must be locked down before production

---

## Session Setup (Read Before Starting)

```bash
cd ~/projects/tech-job-tracker       # navigate to project root
source venv/bin/activate             # activate Python virtual environment
code .                               # open VSCode watching this folder
claude                               # then launch Claude Code
```

> If venv does not exist yet:
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip install -r backend/requirements.txt
> ```

### Remote Work (Telegram + tmux)
Claude Code must be actively running inside a tmux session for the Telegram plugin to work.
```bash
# Before leaving machine — detach, don't close
Ctrl+B then D

# Reattach later
tmux attach
```

---

## Environment

- Python version: 3.12.3
- Node version: v24.14.1
- Expo SDK version: [FILL IN — check mobile/package.json once scaffolded]

---

## Project Structure

tech-job-tracker/
├── CLAUDE.md                  # this file — living document, update often
├── PLAN.md                    # original backend build plan — reference only
├── backend/
│   ├── main.py                # FastAPI entry point · CORS · router mount
│   ├── database.py            # DB connection · SessionLocal · get_db()
│   ├── requirements.txt       # Python dependencies
│   ├── models/
│   │   ├── init.py
│   │   ├── job_application.py # SQLAlchemy model
│   │   └── schemas.py         # Pydantic request/response schemas
│   └── routes/
│       ├── init.py
│       └── job_applications.py # CRUD route handlers
├── mobile/                    # NOT CREATED YET — Expo scaffold next
├── .env                       # never commit this
└── .env.example               # DATABASE_URL placeholder — safe to commit

---

## Stack & Commands

### Backend (Python · FastAPI)

```bash
source venv/bin/activate             # always activate first
uvicorn backend.main:app --reload    # start dev server (port 8000)
pytest                               # run all tests
pip install -r backend/requirements.txt
```

API docs available at `http://localhost:8000/docs` when server is running.

### Frontend (React Native · Expo · TypeScript)

```bash
cd mobile
npm install                          # install dependencies
npm start                            # start Expo dev server
npm run android                      # run on Android emulator
```

### Expo Go — Physical Device Development
Development runs on physical device via Expo Go — preferred over emulator.
Device and laptop must be on the same WiFi network.
Point API calls at your machine's local IP, 
never localhost:http://192.168.x.x:8000

Never hardcode this — use environment config.

---

## Test Devices

| Device | OS | Role |
|---|---|---|
| Pixel 9 Pro XL | Android 17 beta | Primary dev device |
| Samsung S23 Ultra | Stable Android | Sanity check — isolates beta OS issues |
| Xiaomi Mi 11 | MIUI | Stress test — aggressive battery/process limits |

If something looks broken: test on S23 Ultra first.
If it works on S23 but not Pixel, suspect Android 17 beta.
If it works everywhere else but not Xiaomi, suspect MIUI killing background processes.

---

## Behavioral Guidelines
Karpathy principles installed globally via plugin — applies to all sessions.
Plugin: forrestchang/andrej-karpathy-skills

---

## CLAUDE.md Maintenance (Boris Cherny's Rule)

This file is a living document — not a one-time setup.

**After every correction during a session:**
> "Update your CLAUDE.md so you don't make that mistake again."

Claude is good at writing rules for itself. Use that.
Ruthlessly edit this file over time. Keep iterating until mistake rate drops.

---

## Code Conventions

### Python (Backend)
- `snake_case` for all variables, functions, and file names
- Type hints on all function signatures — always
- Pydantic models for request/response validation
- Keep route handlers thin — business logic goes in service functions
- Never commit `.env` — use `.env.example` with placeholder values
- Never use bare `except` — always catch specific exceptions
- Never use `any` as a type — always be explicit

### TypeScript (Frontend)
- `camelCase` for variables and functions
- `PascalCase` for component names and TypeScript interfaces
- Keep components small and single-purpose
- All API calls go through `services/` layer — never call fetch directly in a component
- Never hardcode API URLs — use environment config
- Never use `any` — always be explicit with types

### Both
- Comments explain **why**, not what the code is doing
- No dead code committed — clean it up before committing
- `.env` files never get committed under any circumstances

---

## How I Learn (Important — Please Follow)

I am actively learning while building. When making changes:

1. **Explain your reasoning** — not just what you changed, but why you made that choice
2. **Flag anything security-related** — I want to understand security implications, not just accept them
3. **If there is more than one way to solve something**, briefly mention the tradeoff so I can learn the decision-making
4. **Don't hide complexity from me** — I want to understand the code, not just ship it
5. **I review all generated code** — explain any non-obvious decision before moving on. I should be able to defend everything
   in this codebase in an interview.

---

## What NOT to Do

- Do NOT modify the `venv/` folder
- Do NOT commit `.env` files (use `.env.example` instead)
- Do NOT use `any` in TypeScript — use proper types
- Do NOT put business logic inside route handlers — use service functions
- Do NOT auto-generate migrations without reviewing schema changes first
- Do NOT silently skip explaining a security concern — always flag it
- Do NOT suggest iOS-specific solutions — this app is Android only

---

## Git Workflow

```bash
git checkout -b feature/your-feature-name
git add .
git commit -m "descriptive message"
git push origin feature/your-feature-name
```

Claude Code may generate commit messages during sessions. Standards:
- Imperative mood — "Add job status filter" not "Added job status filter"
- Subject line under 50 characters
- Explains what changed and why — not just that something changed
- One logical change per commit — no "fix stuff" or "updates" dumps
- Never commit: venv/, .env, __pycache__, *.db, *.pyc

---

## AWS Integration (Planned — Future)

- **S3** — resume/document storage
- **RDS (PostgreSQL)** — production database (DATABASE_URL already env-var driven ✅)
- **Lambda** — background processing or notifications
- **Cognito** — authentication (under evaluation)

Do not build for AWS yet. Flag any current decision that will affect future cloud integration.

---

## Useful References

- GitHub: github.com/jmac052002
- Expo Docs: https://docs.expo.dev
- FastAPI Docs: https://fastapi.tiangolo.com
- React Native Docs: https://reactnative.dev
- Karpathy Skills: https://github.com/forrestchang/andrej-karpathy-skills