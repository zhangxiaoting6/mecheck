# mecheck

## Cursor Cloud specific instructions

### Overview
- The product is a minimal **Node.js + Express login demo** (see `README.md` for the standard `npm install` / `npm start` commands and the `demo` / `123456` test account).
- Single runtime service: `server.js` serves the static frontend from `public/` and exposes `POST /api/login` on port `3000` (override with the `PORT` env var). There is no database, cache, or other external dependency.

### Non-obvious notes
- The `main` branch may contain only `README.md`; the actual application code (`server.js`, `package.json`, `public/`) originated on the `cursor/login-demo-*` feature branch. If `package.json` is missing on your branch, there is nothing to install/run — bring in the app code first.
- `server.js` only calls `app.listen()` when run directly (`require.main === module`) and does `module.exports = app`, so it can be imported into tests without starting the server.
- No lint or automated test scripts are defined in `package.json` (only `start`). Verify changes by running the server and hitting `POST /api/login` (or the browser UI at `http://localhost:3000`).
- Login responses are in Traditional Chinese (e.g. `登入成功`, `帳號或密碼錯誤`); credentials are hard-coded in `server.js`.
