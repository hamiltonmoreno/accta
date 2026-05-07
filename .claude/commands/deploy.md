---
name: deploy
argument-hint: [environment]
---

Prepare deployment for $ARGUMENTS environment:
1. Run full lint check:
   - `cd backend && ruff check .`
   - `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60`
2. Build frontend: `cd frontend && REACT_APP_BACKEND_URL=https://accta.cv yarn build`
3. Run backend tests: `cd backend && pytest -v`
4. Check git status — ensure no uncommitted changes
5. If all passes, push to main: `git push origin main`
6. Monitor CI/CD: `gh run list --limit 1`
7. Report deployment status
