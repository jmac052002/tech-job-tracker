# Tech Job Tracker — Mobile
**Stack:** React Native · Expo · TypeScript · Python · FastAPI  
**Platform:** iOS & Android (Expo managed workflow)  
**Developer:** Joseph McCoy · github.com/jmac052002

---

## Project Overview

A mobile job application tracker built for career changers actively in the job hunt.
Tracks job applications, interview stages, follow-up dates, and application status across companies.
Python FastAPI backend · React Native Expo frontend · SQLite for local dev · PostgreSQL for production.
Future cloud integration planned with AWS (S3, RDS, Lambda).

---

## Session Setup (Read Before Starting)

Before every Claude Code session, these should already be done in the terminal:

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
> pip install -r requirements.txt
> ```

---

## Project Structure

```
tech-job-tracker/
├── CLAUDE.md                  # this file
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── models/                # SQLAlchemy or Pydantic models
│   ├── routes/                # API route handlers
│   ├── database.py            # DB connection and session
│   └── requirements.txt
├── mobile/
│   ├── app/                   # Expo Router screens
│   ├── components/            # Reusable UI components
│   ├── hooks/                 # Custom React hooks
│   ├── types/                 # TypeScript types/interfaces
│   └── package.json
├── .env                       # never commit this
└── .env.example               # safe to commit — no real values
```

---

## Stack & Commands

### Backend (Python · FastAPI)

```bash
source venv/bin/activate             # always activate first
uvicorn backend.main:app --reload    # start dev server (port 8000)
pytest                               # run all tests
pip install -r backend/requirements.txt
```

### Frontend (React Native · Expo · TypeScript)

```bash
cd mobile
npm install                          # install dependencies
npm start                            # start Expo dev server
npm run android                      # run on Android emulator
npm run ios                          # run on iOS simulator (Mac only)
```

---

## Code Conventions

### Python (Backend)
- `snake_case` for all variables, functions, and file names
- Type hints on all function signatures — always
- Pydantic models for request/response validation
- Keep route handlers thin — business logic goes in service functions
- Never commit `.env` — use `.env.example` with placeholder values
- Do not use `any` as a type — always be explicit

### TypeScript (Frontend)
- `camelCase` for variables and functions
- `PascalCase` for component names and TypeScript interfaces
- Keep components small and single-purpose
- All API calls go through a dedicated `services/` or `api/` layer
- Never hardcode API URLs — use environment config

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
5. **I type code myself** when learning new concepts — if I ask to understand something, walk me through it rather than just doing it

---

## What NOT to Do

- Do NOT modify the `venv/` folder
- Do NOT commit `.env` files (use `.env.example` instead)
- Do NOT use `any` in TypeScript — use proper types
- Do NOT put business logic inside route handlers — use service functions
- Do NOT auto-generate migrations without reviewing schema changes first
- Do NOT silently skip explaining a security concern — always flag it

---

## AWS Integration (Planned — Future)

This project will eventually integrate with AWS services:
- **S3** — resume/document storage
- **RDS (PostgreSQL)** — production database
- **Lambda** — background processing or notifications
- **Cognito** — authentication (under evaluation)

Do not build for AWS yet — flag when a decision will affect future cloud integration.

---

## Git Workflow

```bash
git checkout -b feature/your-feature-name   # new branch for each feature
git add .
git commit -m "descriptive message"
git push origin feature/your-feature-name
```

Ask Claude Code to generate commit messages when needed:
> "Write a git commit message for everything we just built"

---

## Useful References

- GitHub: github.com/jmac052002
- Expo Docs: https://docs.expo.dev
- FastAPI Docs: https://fastapi.tiangolo.com
- React Native Docs: https://reactnative.dev