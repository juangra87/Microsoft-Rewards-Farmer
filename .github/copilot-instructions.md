# GitHub Copilot / AI agent instructions for Microsoft-Rewards-Farmer

Quick, focused guidance to help an AI code agent be productive in this repository.

## Big picture 🔧
- **Purpose**: Selenium-based Python bot automating Microsoft Rewards tasks (searches, daily set, punch cards, promotions) across multiple accounts.
- **Architecture**: Single-process CLI (`main.py`) → account loop → `Browser` wrapper → activity modules (Login, Searches, DailySet, etc.). Each activity completes one reward task.
- **Persistence**: Browser sessions in `sessions/<uuid>/<desktop|mobile>/<timestamp>/` with `config.json` (caches user agent, browser config). Logs to `logs/activity.log`.
- **Flow**: Main loop iterates accounts, runs activities until no points earned, sleeps 30min, repeats. Per-account optional sleep interval between searches (`accounts.json`).

## Key files (read first) 📂
- `main.py` — account orchestration, CLI args, pause/retry logic, points tracking, logging setup.
- `src/browser.py` — WebDriver wrapper (context manager), user-data profile, proxy/lang/mobile config, headless setup.
- `src/utils.py` — **shared helpers**: wait strategies, element selection, dashboard parsing, config I/O. Prefer these over ad-hoc waits.
- `src/activities.py` — base class for opening/clicking activity cards (daily set, promotions, quizzes, surveys).
- `src/login.py` — email/password entry with fallback selectors and password escaping (handles special chars).
- `src/searches.py`, `src/dailySet.py`, `src/punchCards.py`, `src/morePromotions.py`, `src/readToEarn.py` — activity implementations (inherit Activities or standalone).
- `src/userAgentGenerator.py` — fetches Edge/Chrome versions, caches in browser config to avoid external calls.
- `accounts.json.sample` — credential format: `username`, `password`, optional `proxy`, optional `sleep` (seconds between searches).

## Running locally 🚀
```bash
pip install -r requirements.txt
python main.py [-v] [-l en] [-g US] [-p proxy] [-t TOKEN CHAT_ID] [-d WEBHOOK]
# or auto-update then run:
python autoupdate_main.py
```
- `-v/--visible` → show browser (default headless)
- `-l/--lang` → force locale (e.g., `en`)
- `-g/--geo` → force geolocation (e.g., `US`)
- `-p/--proxy` → override account proxy
- `-t/--telegram` → Discord/Telegram notifications

## Patterns to follow 🧭
1. **Browser lifecycle**: Always use `with Browser(...):` context manager. Ensures `close_browser()` cleanup and session write.
2. **Error recovery**: Catch broad exceptions → `browser.utils.reset_tabs()` (close extra tabs) or `remove_sessions_folder()` (nuke failed session).
3. **Waits**: Use `Utils` methods (`wait_until_visible`, `wait_until_clickable`, `wait_until_quiz_loads`) not bare `WebDriverWait`. Customizes timeout/refresh behavior.
4. **Activity pattern**: Inherit `Activities` for UI navigation (click cards, enter forms). Use `webdriver.execute_script(...)` to read page JS state (e.g., quiz question count).
5. **Logging**: Prefix logs: `[LOGIN]`, `[BROWSER]`, `[POINTS]`, `[HERO]`. Matches existing style.
6. **Selectors**: Prefer `By.XPATH` or `By.ID`; XPaths are brittle but specific to Rewards UI. Add fallback selectors (e.g., `Login.getEmailField()` tries two IDs).
7. **Config persistence**: Use `Utils.save_browser_config(session_path, config)` to cache UA metadata. Reload with `Utils.get_browser_config()`.

## Critical implementation details ⚙️
- **WebDriver chain**: `undetected_chromedriver` → `selenium-wire` (proxy support) → `Selenium 4.10+` webdriver manager. Do **not** change driver init without testing proxy/headless.
- **Mobile detection**: `Browser(mobile=True/False)` sets viewport, user agent, device metrics. Searches run both desktop then mobile if remaining quota.
- **Locale/geo**: Resolved from flags or `ipapi.co` lookup. Passed to Chrome via `--lang` and WebDriver default geo setting.
- **Points tracking**: Each activity returns points earned. `execute_bot()` subtracts start from final to report daily gain. Locale-aware numeric parsing via `locale.atof()`.
- **Session folder structure**: `sessions/<uuid>/<desktop|mobile>/<YYYY_MM_DD_-_HH_MM>/config.json`. Folder auto-generated, session reused per browser type.
- **Password escaping**: Special chars escaped with backslash (e.g., `"` → `\"`). Necessary for JavaScript-based form entry.

## Common tasks 🔨
- **Add new reward activity**: Create `src/newActivity.py`, inherit `Activities`, override `execute()`. Register in `main.py` `execute_bot()` flow.
- **Add CLI flag**: Update `argument_parser()`, pass via `args` → `Browser.__init__` or activity methods.
- **Debug selector failure**: Use `-v` flag to see browser, inspect element in DevTools, update XPATH/ID in code.
- **Cache user agent**: `UserAgentGenerator` auto-caches to session `config.json`. If external fetch fails, reuses cached UA.
- **Mock external calls**: Test should stub `userAgentGenerator.get_edge_versions()`, `ipapi.co` calls, `requests` to Bing/Rewards.

## Editing checklist ✅
- Update `requirements.txt` if adding packages.
- Preserve `Browser` context manager usage and cleanup.
- Use `Utils` helpers for waits (don't add custom `WebDriverWait` logic).
- Test proxy/headless/mobile flags still work.
- Update `README.md` if adding user-facing CLI flags.
- Add logging prefixes matching existing style (`[MODULE]`).

## Testing strategy ⚠️
- No automated tests currently. When writing:
  - Unit test `userAgentGenerator` with mocked Edge/Chrome endpoints.
  - Unit test `Utils` helper methods with mock WebDriver.
  - Integration test `Login` with mocked form selectors.
  - Mock all external network calls and WebDriver interactions.

---
Last updated: Jan 2026. Ask for clarification on browser internals, activity patterns, or test mocking strategy.