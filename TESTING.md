# Testing Guide

## Backend Tests (Python/pytest)

### Setup
```bash
cd backend
pip install -r requirements.txt
```

### Run Tests
```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

### Test Files
- `tests/conftest.py` - Test fixtures and configuration
- `tests/test_api.py` - API endpoint tests

## Frontend Tests (Jest/React Testing Library)

### Setup
```bash
cd frontend
npm install
```

### Run Tests
```bash
# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm test -- --coverage
```

### Test Files
- `src/__tests__/api.test.ts` - API integration tests
- `src/__tests__/components.test.tsx` - Component tests

## E2E Tests (Playwright)

### Setup
```bash
cd frontend
npx playwright install
```

### Run Tests
```bash
# Run all E2E tests
npm run test:e2e

# Run with UI mode
npm run test:e2e:ui

# Run specific test
npx playwright test e2e/dashboard.spec.ts
```

### Test Files
- `e2e/dashboard.spec.ts` - Dashboard and trading flows

## Manual Testing Checklist

### Connection
- [ ] Backend starts successfully
- [ ] Frontend connects to backend
- [ ] Tailscale Funnel active (for remote access)

### Dashboard
- [ ] Price displays and updates
- [ ] Chart renders
- [ ] Account info shows

### Trading
- [ ] Can view positions
- [ ] Can open buy position
- [ ] Can open sell position
- [ ] Can close positions

### Error Handling
- [ ] Shows error when backend disconnected
- [ ] Handles network timeouts
- [ ] Validates invalid inputs
