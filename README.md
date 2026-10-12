# SAT Prep

A SAT practice app built with Streamlit for family use. It reads 70 SAT-style questions from `SAT_question_bank_MVP.csv` and saves the student profile, practice history, preparation goals, and test scores in local SQLite or a configured PostgreSQL database such as Neon.

## Current features

| Area | Features |
| --- | --- |
| Home | Student-friendly navy welcome panel, daily mission, streak/goal status, Math and Reading & Writing learning cards, dashboard/review shortcuts, and profile editing in an expander. |
| Practice | Fixed 20-minute goal, live timer, subject and difficulty filters, shuffled questions, immediate answer feedback, a basic skill hint after answering, and explanations. |
| Progress | Overall answer-attempt accuracy, up to 20 recent mistakes to review, and up to three skill recommendations based on low accuracy. |
| Dashboard | First-attempt accuracy, subject and skill breakdowns, daily charts, and question-bank coverage. |
| Score analyzer | Saved SAT, Bluebook SAT practice, and PSAT results with test dates; SAT comparisons with 2025 averages and readiness benchmarks; SAT/Bluebook score trends and deletion of incorrect entries. |
| 2025 statistics | Interactive bar graph of six SAT total-score bands, with student counts and calculated percentages in tooltips. |
| Preparation goals | Editable graduation year and target SAT score, initially 2030 and 1400. |
| Daily vocabulary | A word and quick meaning at the top right of every page, rotating through 30 words daily. |
| Question bank | 35 Math and 35 Reading & Writing questions, including a balanced 20-question original pilot with Easy, Medium, and Hard questions. |

Use the sidebar to switch between **Home**, **Dashboard**, **Practice**, and **Progress**. This version uses one shared student profile, including when hosted in the cloud.

## Architecture

The app can run locally or on a Streamlit host. Arrows show component calls or data access; the browser displays the UI while Python handles practice rules and storage. Configuring `SAT_DATABASE_URL` selects PostgreSQL; otherwise the app uses SQLite.

```mermaid
flowchart TB
    browser["Student browser"] <--> app

    subgraph runtime["Local Streamlit application"]
        app["app.py<br/>Initialize database, load questions,<br/>route pages and render shared vocabulary card"]

        subgraph pages["UI pages"]
            home["home.py<br/>Profile, daily goal, streak"]
            dashboard["dashboard.py<br/>Practice trends, score log,<br/>2025 bar graph, comparison and goals"]
            practice["practice.py<br/>Timer, filters, answers, explanations"]
            progress["progress.py<br/>Accuracy, mistakes, recommendations"]
        end

        subgraph services["Business logic"]
            bank["question_bank.py<br/>CSV validation and question filtering"]
            rules["practice.py<br/>Answer checking, completion rules,<br/>skill recommendations"]
            streaks["streaks.py<br/>Consecutive completed practice days"]
            performance["performance.py<br/>First-attempt accuracy, score validation,<br/>2025 statistics and historical comparison"]
            vocabulary["vocabulary.py<br/>30 words and meanings,<br/>daily selection in Los Angeles time"]
        end

        state["Streamlit session_state<br/>Navigation, active session, timer,<br/>question order and answer feedback"]
        repo["storage/repository.py<br/>Profile, sessions, answers, mistakes,<br/>preparation goals and score reports"]
        database["storage/database.py<br/>Schema, connections and transactions"]
        configuration["storage/configuration.py<br/>Private database settings and URL validation"]

        app --> home
        app --> dashboard
        app --> practice
        app --> progress
        app --> bank
        app --> configuration
        app -->|"Word card on every page"| vocabulary
        app -->|"Initialize schema"| database
        home --> streaks
        home --> repo
        dashboard --> performance
        dashboard --> repo
        practice --> bank
        practice --> rules
        practice --> repo
        progress --> rules
        progress --> repo
        home <--> state
        practice <--> state
        app -->|"Pass loaded questions"| practice
        app -->|"Pass loaded questions"| progress
        app -->|"Pass loaded questions"| dashboard
        repo --> database
        repo -->|"Validate entered scores"| performance
    end

    csv[("SAT_question_bank_MVP.csv<br/>Questions, choices, answers and explanations")]
    sqlite[("data/sat_prep.db<br/>SQLite: profile, sessions, answers,<br/>preparation_plan, score_reports")]
    postgres[("Neon PostgreSQL<br/>Same five progress tables<br/>plus schema_migrations")]
    bank -->|"Read question bank"| csv
    database <-->|"No cloud setting"| sqlite
    database <-->|"Configured encrypted connection"| postgres
```

- **Question content:** Loaded and validated from CSV, then passed to Practice, Progress, and Dashboard. Subject and difficulty filters operate on the loaded questions.
- **Active practice:** Streamlit session state tracks the timer and current question across UI reruns.
- **Saved progress:** The selected SQLite or PostgreSQL database persists the student profile, sessions, answers, preparation plan, and score reports. Each answer belongs to a session through `answers.session_id`; new tables are created automatically without replacing existing history. A configured cloud connection failure stops the app instead of falling back to a separate local history.
- **Recommendations and streaks:** Computed from saved answer history and completed session dates.
- **Dashboard calculations:** First-attempt summaries ignore subsequent submissions for the same question within a session. The existing Progress page reports all saved answer attempts.
- **Historical statistics:** The 2025 averages and score-band counts are stored in `services/performance.py`. Charts render locally; the app does not call College Board or Google at runtime. Source links and the verification date appear in the dashboard.
- **Daily vocabulary:** The entry point renders a shared card using `services/vocabulary.py`. A Streamlit fragment refreshes it every 60 seconds; the practice timer has its own one-second fragment.

### Code and storage map

| Location | Responsibility |
| --- | --- |
| `src/sat_prep/app.py` | Startup, sidebar routing, question-bank loading, and shared vocabulary card. |
| `.streamlit/config.toml` | Navy/teal/ivory theme, white cards, navy sidebar, semantic feedback colors, and chart colors. |
| `src/sat_prep/pages/` | Home, Dashboard, Practice, and Progress UI. |
| `src/sat_prep/services/` | Question filtering, practice rules, streaks, performance summaries, score statistics, and vocabulary selection. |
| `src/sat_prep/storage/` | SQLite/PostgreSQL connections, private configuration, transactions, persistence, and the import CLI. |
| `src/sat_prep/storage/migrations/001_postgresql.sql` | Versioned PostgreSQL schema; applied transactionally under an advisory lock. |
| `SAT_question_bank_MVP.csv` | Question content, choices, keyed answers, explanations, and provenance. |
| `data/sat_prep.db` | Local `profile`, `sessions`, `answers`, `preparation_plan`, and `score_reports` tables; excluded from Git. |
| `tests/` | Question-bank integrity, practice rules, streaks, persistence, score analysis, vocabulary rotation, and Streamlit UI/navigation checks. |

## Performance dashboard

A **SAT word of the day** card appears at the top right of each page. It rotates through 30 locally authored word meanings on a daily schedule using America/Los_Angeles time and refreshes within a minute of midnight while the page is open. These are SAT-style vocabulary practice, not an official SAT word list.

Open **Dashboard** in the sidebar to see first-attempt practice accuracy, subject and skill breakdowns, daily trends, and question-bank coverage. Only the first submission for a question within a session counts toward dashboard accuracy; the same question in a later session counts as another attempt.

The **Test scores and 2025 comparison** tab saves manually entered SAT, Bluebook SAT practice, and PSAT results locally. SAT and Bluebook SAT practice results can be compared with College Board's graduating class of 2025 averages: **1029 total, 521 Reading & Writing, and 508 Math**. PSAT scores are logged separately rather than treated as SAT scores. Scores can be removed if entered incorrectly.

That tab also displays a **2025 SAT total-score distribution** bar chart covering six score ranges, from 400–590 to 1400–1600. Bar heights are percentages computed from published counts for 2,004,965 students; tooltips show the range, student count, and percentage. The chart is available even before a personal score is entered.

The preparation plan defaults to high school graduation in **2030** and an editable **1400** SAT target. Neither is a forecast or an admissions requirement. Practice accuracy is not converted into a SAT score; the question bank is not calibrated to official scoring. The historical averages describe 2025 graduates' most recent SAT scores, not expected 2030 performance. SAT readiness benchmarks are 480 Reading & Writing and 530 Math.

Sources checked October 11, 2026: [2025 College Board annual report](https://reports.collegeboard.org/media/pdf/2025-total-group-sat-suite-of-assessments-annual-report.pdf), [readiness benchmarks](https://satsuite.collegeboard.org/k12-educators/about/understand-scores-benchmarks/benchmarks), and [SAT scoring](https://satsuite.collegeboard.org/scores/what-scores-mean/how-scores-calculated). Existing local databases gain preparation-plan and score-report tables automatically when the app starts.

## Student-friendly Home page

The Home page uses a navy, teal, and warm ivory palette with a welcoming illustration, encouraging copy, white learning cards, and a prominent **Start today's practice** button. Navy (`#142D4E`) provides structure, teal (`#087E8B`) marks actions and charts, ivory (`#F8F7F3`) softens the background, forest green (`#237A4B`) marks success, and soft gold (`#F2C66D`) highlights the graduation goal and illustration. **Practice math** and **Practice reading & writing** start a 20-minute session with the chosen subject selected. **View my dashboard** and **Review my progress** open the corresponding pages. The daily vocabulary card remains at the top right.

The theme is configured in `.streamlit/config.toml`; the compact welcome illustration and responsive hero styles are owned by the Home page. The illustration hides on narrow screens to keep the greeting readable. Automatic Streamlit `pages/` navigation is disabled through `client.showSidebarNavigation`, leaving one custom sidebar menu. Restart Streamlit after configuration changes if the new colors or navigation do not appear. The design is independently created for SAT_app, with no Khan Academy assets or affiliation.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not already installed, then run:

```powershell
uv sync
uv run streamlit run src/sat_prep/app.py
```

Without a cloud setting, the database is created automatically at `data/sat_prep.db`. It stays local to this machine and is excluded from Git.

## Persistent cloud storage with Neon

The PostgreSQL code is ready to configure. A Neon project and live connection have not yet been set up or verified for this app. Cloud storage preserves progress independently of the Streamlit server; local SQLite files on Community Cloud are not guaranteed to persist.

1. Create a project in the [Neon console](https://console.neon.tech/) for this family app. Use a database reserved for SAT_app, not one containing unrelated tables.
2. Use **Connect** to copy its PostgreSQL connection URL. Keep `sslmode=require` (or a stronger verification mode) and any `channel_binding` setting supplied by Neon. A direct connection is suitable for the one-time schema/import operations.
3. Create `.streamlit/secrets.toml` locally with the following setting, replacing the placeholder with the real URL **privately in your editor**:

   ```toml
   SAT_DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
   ```

4. Run `uv sync`, then the commands below from the project root. `--check` contacts the cloud and initializes its schema but does not import local progress. `--dry-run` reads local data without contacting the cloud or changing files.

   ```powershell
   uv run python -m sat_prep.storage.migrate --dry-run
   uv run python -m sat_prep.storage.migrate --check
   uv run python -m sat_prep.storage.migrate --apply
   uv run python -m sat_prep.storage.migrate --check
   ```

5. Restart the app. The new secret switches all profile, session, answer, goal, and score operations to PostgreSQL. Your original SQLite database remains available if you remove the cloud setting, but local and cloud histories are not automatically synchronized.
6. For Streamlit Community Cloud, add the same TOML setting in the app's **Settings → Secrets**, then reboot. Verify saved history after a reboot. Keep the hosted app private for family use because this version shares one profile.

The connection can also be supplied through the `SAT_DATABASE_URL` environment variable, which takes precedence over the secrets file. An invalid or blank configured URL produces an error rather than silently switching databases. The app does not display raw connection errors or credentials. Do not paste the real URL into chat or commit it to Git; `.streamlit/secrets.toml` and `.env` files are ignored.

The import creates a uniquely named `data/sat_prep.before-cloud-*.db` backup before connecting, preserves IDs and relationships, compares every imported row against the snapshot, and commits only after verification. It refuses to overwrite existing scores, sessions, answers, or edited cloud profile/goal rows. Stop practice while taking the final migration snapshot so new local answers are not left behind. Running `--apply` again after a successful import is refused if progress exists. Older local databases without the dashboard tables import with an empty score log and default preparation goals.

PostgreSQL uses the same five application tables plus `schema_migrations`. Date/time values remain ISO text to preserve the current analytics behavior. The CSV question bank stays in Git, and no question-content API is needed. Check and configure the backup/retention options for your chosen Neon plan separately; persistent storage does not replace backups.

References: [Neon connection guide](https://neon.com/docs/get-started-with-neon/connect-neon), [Streamlit secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management), and [Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html).

## Run tests

```powershell
uv run pytest
```

The suite covers dashboard score entry/deletion, PSAT separation, vocabulary navigation, cloud configuration, credential-safe errors, migration backups, overwrite refusal, and rollback. Live PostgreSQL coverage is skipped unless a separate `SAT_TEST_DATABASE_URL` is configured. That test creates and removes an isolated schema in the test database; do not point it at the family database. Local tests and adapter tests do not establish that a live Neon connection works.

## Notes about the supplied question bank

The CSV contains 70 SAT-style practice questions: the original 50 plus a 20-question pilot with IDs `P_M001`–`P_M010` and `P_R001`–`P_R010`. The pilot includes 10 Math and 10 Reading & Writing questions; each subject has 3 Easy, 4 Medium, and 3 Hard questions. Across the pilot, each answer letter is correct five times.

The pilot questions are original, AI-authored content with checked answers and worked explanations. They are not official College Board questions and have not been independently reviewed by an educator. Difficulty labels and time estimates are author estimates, not calibrated measurements. Review them with a parent or tutor before relying on them for assessment; practice accuracy is not an official SAT score estimate.

Pilot rows include provenance, a `pilot-20` tag, and estimated question times. The app continues to use a fixed 20-minute session goal. The original 50 questions have blank time estimates and no correct answers keyed as D, so the combined bank still needs broader balancing.
