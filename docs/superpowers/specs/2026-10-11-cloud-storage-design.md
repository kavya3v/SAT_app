# Persistent family storage

The family app needs saved scores and practice progress to survive Streamlit deployment restarts. Use Neon PostgreSQL for one shared student profile. Keep SQLite when no cloud connection is configured and keep the question bank in CSV.

Configure `SAT_DATABASE_URL` through an environment variable or Streamlit secrets. Require a PostgreSQL URL. A configured connection failure must stop the app rather than create an unrelated SQLite history. Do not display credentials or raw connection errors.

Preserve repository interfaces and text-based dates so the existing pages and analytics continue to work. Adapt parameter styles and generated IDs at the storage boundary. Add a versioned PostgreSQL schema migration with an advisory lock for concurrent initializations.

Provide a CLI to migrate a read-only snapshot of an existing SQLite database. Back it up first; require an empty cloud destination except for untouched seeded profile/plan rows. Import all five tables, preserve IDs, verify complete rows and foreign keys, and reset generated-ID sequences in one transaction. Failed imports roll back. Never accept a secret URL as a CLI argument or print it.

Live Neon provisioning and verification require the user to create the project and configure its secret. Until that happens, report the cloud connection as unverified. Optional PostgreSQL integration tests use a separate explicit test connection.
