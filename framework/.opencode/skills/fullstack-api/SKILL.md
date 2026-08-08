---
name: fullstack-api
description: "Guidelines for building fullstack APIs with FastAPI backend and React frontend."
---

# Skill: fullstack-api

## Stack
- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL
- **Frontend:** React + TypeScript + Vite
- **API Style:** RESTful with OpenAPI documentation

## Backend Rules
1. Use Pydantic v2 for request/response models
2. Use dependency injection for DB sessions
3. Implement proper HTTP status codes
4. Add pagination for list endpoints
5. Include rate limiting on public endpoints

## Frontend Rules
1. Use React Query for server state
2. Use Zustand for client state
3. Implement proper error boundaries
4. Add loading states for all async operations
5. Use TypeScript strict mode

## API Contract Rules
1. Version the API (`/api/v1/`)
2. Use consistent naming (kebab-case URLs, camelCase JSON)
3. Document all endpoints with OpenAPI annotations
4. Include example requests/responses
