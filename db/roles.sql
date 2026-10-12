-- Roles for the reconciliations database. Locally a superuser runs this; on Neon
-- `reconciliations-db provision` creates the same roles through the migrator.
--
-- reconciliations_migrator  owns the schema and runs migrations only.
-- reconciliations_api       the API at runtime: no superuser, no BYPASSRLS, owns nothing.
-- reconciliations_publisher sweeps and marks the outbox across workspaces; nothing else.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reconciliations_migrator') THEN
        CREATE ROLE reconciliations_migrator LOGIN NOSUPERUSER NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reconciliations_api') THEN
        CREATE ROLE reconciliations_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reconciliations_publisher') THEN
        CREATE ROLE reconciliations_publisher LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
END
$$;
