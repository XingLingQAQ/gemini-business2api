# Refresh Architecture

This repository's mainline stays focused on the Gemini Business `2api` gateway and the admin panel.

Refresh, login automation, browser execution, and account replenishment run in a separate worker image. The main service still keeps the shared settings UI so that the worker, local tools, and account import/export flows all point to one consistent source of truth.

## Design Goals

- Keep `main` / `beta` focused on the `2api` gateway.
- Keep refresh execution outside the main web process.
- Preserve shared refresh/email settings in the admin panel.
- Preserve per-account email fields for import/export and local tooling.
- Support both same-machine Docker deployments and external/local refresh workers.

## Configuration Boundaries

There are three different configuration layers:

### 1. Shared system settings

Configured in the admin panel under `System Settings`.

These values are shared defaults used by the standalone refresh worker:

- auth proxy
- temp mail provider
- browser mode / headless mode
- DuckMail / Moemail / Freemail / GPTMail / CFMail shared settings
- scheduled refresh switches and intervals
- refresh batch / cooldown / auto-register thresholds
- register domain and default register count

These values are exposed by `GET /admin/settings` as `refresh_settings`.

The database stores them in canonical `refresh_settings` form. Inside the main service they are mapped back into runtime `basic` / `retry` fields so existing in-process code can keep reading a stable config object.

### 2. Per-account mail configuration

Configured in the admin panel under `Accounts`, and stored through `/admin/accounts-config`.

This is where account-level fields remain, such as:

- `mail_provider`
- `mail_address`
- `mail_password`
- `mail_client_id`
- `mail_refresh_token`
- `mail_tenant`
- `mail_base_url`
- `mail_api_key`
- `mail_jwt_token`
- `mail_verify_ssl`
- `mail_domain`

These fields are not replaced by shared `refresh_settings`. Shared settings provide defaults and worker-wide behavior; account records still carry their own imported credentials when needed.

### 3. Worker environment overrides

Configured only on the refresh worker container or local refresh branch.

Use these when the execution environment needs machine-local overrides, for example:

- `FORCE_REFRESH_ENABLED`
- `REFRESH_INTERVAL_MINUTES`
- `REFRESH_WINDOW_HOURS`
- `BROWSER_HEADLESS`
- `PROXY_FOR_AUTH`

If these are not set, the worker falls back to the shared settings stored by the main service.

## Deployment Modes

### Mode A: Same machine, same compose project

This repository now supports an optional second service:

- `gemini-api`
- `refresh-worker`

The worker is disabled by default and starts only with:

```bash
docker compose --profile refresh up -d
```

In this mode:

- the main service uses `./data`
- the worker also mounts `./data`
- the worker reads SQLite from `/app/data/data.db`

This is the simplest local deployment.

### Mode B: Different machines or local refresh branch

When the refresh worker runs outside this compose project, use a shared `DATABASE_URL`.

That lets the following consumers point at the same source of truth:

- this repository's `2api` service
- the standalone `gemini-refresh-worker` image
- the local refresh branch/tooling

In this mode:

- the admin panel remains the place where shared refresh settings are edited
- account import/export still stays in the main service
- the external worker reads settings/accounts from the shared database
- worker env vars remain optional overrides for local execution details

## Recommended Mainline Layout

For the current project, the cleanest layout is:

- main repository: `2api` gateway + admin panel + shared settings
- separate refresh worker image: browser automation and scheduled refresh
- optional local refresh branch: developer/local operator tooling that can also connect to the same shared config source

That keeps the web service clear while still preserving the settings and import/export capabilities you still need.
