---
name: new-feature
argument-hint: [feature-name]
---

Scaffold a complete full-stack feature called "$ARGUMENTS" for the ACCTA Portal:

## Step 1 — Plan
Write the plan to `tasks/todo.md`:
- What the feature does
- Which collections/models are needed
- API endpoints (method, path, roles)
- Frontend pages/components needed

## Step 2 — Backend
1. Add Pydantic model to `backend/models.py`
2. Create `backend/routes/$ARGUMENTS.py` with:
   - FastAPI router with `/$ARGUMENTS` prefix (the shared `api_router` adds the `/api` prefix)
   - Auth dependency on all protected endpoints: `Depends(get_current_user)`
   - Role checks where applicable
   - `create_audit_log()` on admin write actions
   - `create_notification()` or `notify_users()` where relevant
3. Register router in `backend/routes/__init__.py` (add `from routes.$ARGUMENTS import router as $ARGUMENTS_router` and `api_router.include_router($ARGUMENTS_router)`; `api_router` already has `prefix="/api"`)
4. Add indexes to `backend/database.py` via `ensure_schema()` if needed

## Step 3 — Frontend
1. Add API group to `frontend/src/utils/api.js`
2. Create page at `frontend/src/pages/private/$ARGUMENTS_Page.js`:
   - Use shadcn/ui components
   - Tailwind CSS with ACCTA brand tokens
   - Loading/error/empty states
   - Sonner toast for feedback
3. Add route to `frontend/src/App.js` with `<ProtectedRoute>`
4. Add sidebar link in `frontend/src/layouts/PrivateLayout.js` if needed

## Step 4 — Verify
- `cd backend && ruff check .`
- `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60`
- Test the feature manually end-to-end
- Mark `tasks/todo.md` complete
