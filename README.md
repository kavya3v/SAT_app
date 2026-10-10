# SAT Prep

A local-first SAT practice app built with Streamlit. It reads the question bank from `SAT_question_bank_MVP.csv` and stores profile, practice sessions, and answer history in SQLite.

## Architecture

The app runs as a local Streamlit application. Arrows show component calls or data access; the browser displays the UI while Python handles practice rules and storage.

```mermaid
flowchart TB
    browser["Student browser"] <--> app

    subgraph runtime["Local Streamlit application"]
        app["app.py<br/>Initialize database, load questions, route pages"]

        subgraph pages["UI pages"]
            home["home.py<br/>Profile, daily goal, streak"]
            practice["practice.py<br/>Timer, filters, answers, explanations"]
            progress["progress.py<br/>Accuracy, mistakes, recommendations"]
        end

        subgraph services["Business logic"]
            bank["question_bank.py<br/>CSV validation and question filtering"]
            rules["practice.py<br/>Answer checking, completion rules,<br/>skill recommendations"]
            streaks["streaks.py<br/>Consecutive completed practice days"]
        end

        state["Streamlit session_state<br/>Navigation, active session, timer,<br/>question order and answer feedback"]
        repo["storage/repository.py<br/>Profile, sessions, answer history and mistakes"]
        database["storage/database.py<br/>Schema, connections and transactions"]

        app --> home
        app --> practice
        app --> progress
        app --> bank
        app -->|"Initialize schema"| database
        home --> streaks
        home --> repo
        practice --> bank
        practice --> rules
        practice --> repo
        progress --> rules
        progress --> repo
        home <--> state
        practice <--> state
        app -->|"Pass loaded questions"| practice
        app -->|"Pass loaded questions"| progress
        repo --> database
    end

    csv[("SAT_question_bank_MVP.csv<br/>Questions, choices, answers and explanations")]
    sqlite[("data/sat_prep.db<br/>SQLite: profile, sessions, answers")]
    bank -->|"Read question bank"| csv
    database <-->|"Read / write"| sqlite
```

- **Question content:** Loaded from CSV into memory and passed to Practice and Progress.
- **Active practice:** Streamlit session state tracks the timer and current question across UI reruns.
- **Saved progress:** SQLite persists the student profile, session records and answer history. Each answer belongs to a session through `answers.session_id`.
- **Recommendations and streaks:** Computed from saved answer history and completed session dates.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not already installed, then run:

```powershell
uv sync
uv run streamlit run src/sat_prep/app.py
```

The database is created automatically at `data/sat_prep.db`. It stays local to this machine and is excluded from git.

## Run tests

```powershell
uv run pytest
```

## Notes about the supplied question bank

The current CSV has 50 questions, all with Easy or Medium difficulty. Its `Estimated_Time_Sec` values are blank and no correct answers are keyed as D. The app therefore uses a 20-minute session timer rather than per-question time estimates, and the question bank should be balanced before using answer-choice patterns as an indicator of correctness.
