# GitHub Copilot / AI agent instructions for Microsoft-Rewards-Farmer

Quick, focused guidance to help an AI code agent be productive in this repository.

## Big picture 🔧
- Purpose: a Selenium-based Python bot that automates Microsoft Rewards tasks (searches, daily set, punch cards, promotions).
- Runtime: single-process CLI tool (`main.py`) that iterates through accounts defined in `accounts.json` and performs browser flows using a `Browser` wrapper.
- Persistence: browser sessions written to `sessions/<uuid>/<desktop|mobile>/<timestamp>/` with an optional `config.json` per session. Logs are written to `logs/activity.log`.

## Key components & files (where to look first) 📂
- `main.py` — orchestrator: argument parsing, account loop, pause/retry policy, notifier integration.
- `autoupdate_main.py` — self-update helper: fetches latest master zip and restarts.
- `src/browser.py` — WebDriver wrapper (context manager), user-data profile handling, proxy/lang handling, window/viewport setup.
- `src/utils.py` — utilities for waiting/selecting elements, dashboard parsing, retrying requests, and browser config I/O. Prefer using these helpers when integrating new flows.
- `src/*.py` (Login, DailySet, Activities, Searches, PunchCards, MorePromotions, ReadToEarn) — domain logic examples of how activities are implemented.
- `src/userAgentGenerator.py` — network calls to fetch Edge/Chrome versions for UA strings (external calls; cache, mock or stub in tests).
- `src/notifier.py` — Discord/Telegram notification mechanics.
- `accounts.json.sample` — required account format (username/password, optional proxy, optional sleep interval).

## Running / dev workflows 🚀
- Install deps: `pip install -r requirements.txt` (project uses `selenium >= 4.10` behaviour: webdriver manager built-in).
- Run locally: `python main.py` (or `python autoupdate_main.py` to auto-update then run).
- Flags:
  - `-v/--visible` to run with visible browser (default is headless)
  - `-l/--lang`, `-g/--geo` to force locale/geolocation
  - `-p/--proxy` to override account proxy
  - `-t/--telegram` `TOKEN CHAT_ID` and `-d/--discord` WEBHOOK to enable notifications
- Docker: `docker build -t ... .` and `docker-compose up -d` using provided `Dockerfile` and `docker-compose.yml`.

## Conventions & patterns to follow 🧭
- Use `Browser` context manager (`with Browser(...):`) like `main.py` does; it ensures clean close and session writes.
- Use `Utils` helpers for waiting, refresh/timeout strategies, and to get dashboard data rather than ad-hoc WebDriver waits.
- Error-recovery pattern: many modules use broad `try/except` + `browser.utils.reset_tabs()` or `remove_sessions_folder()`; follow this pattern for robustness.
- Session configuration: write to the current session folder using `Utils.save_browser_config(session_path, config)`; user agent metadata is persisted there.
- Timeouts and sleeps: existing logic uses short sleeps and `pause.until(...)` for long backoffs; follow existing timing semantics when adding features.

## Integration & external dependencies ⚙️
- Selenium + `undetected_chromedriver` + `selenium-wire` — network interception and stealth are used; be careful when changing the WebDriver setup in `src/browser.py`.
- `ipapi` used to resolve locale/geo when flags not passed.
- `requests` used throughout (autoupdate, user agent lookup, notifier). When adding network code, use `Utils.make_requests_session()` for retry logic.

## Tests & CI ⚠️
- There are currently no automated tests or CI config in the repo. When adding tests:
  - Prefer isolated unit tests for `userAgentGenerator` and utils.
  - Mock external network calls (Edge/Chrome endpoints, ipapi, requests to Bing) and the WebDriver interface for src modules.

## Editing guidelines / PR checklist ✅
- Update `requirements.txt` for any new runtime deps used by code.
- Add a short example in `README.md` if you add a new CLI flag or notable runtime behaviour.
- Keep browser behaviour consistent: prefer `Utils` helpers and `Activities` patterns instead of introducing custom wait logic.
- If touching `browser.py`, ensure proxy, headless, and device metric configuration are preserved.

## Examples to cite in PRs (where reviewers should look) 🔍
- `Login.execute_login()` — demonstrates form entry + fallback ID handling and password quoting.
- `Activities.complete_quiz()` — demonstrates `webdriver.execute_script(...)` usage to access page JS state.
- `userAgentGenerator.get_edge_versions()` — external API call that should be mocked in tests.

---
Questions or missing bits? I can refine wording, add a short contributor checklist, or include example unit-test stubs for `userAgentGenerator` and `Utils`. Please tell me which you prefer.