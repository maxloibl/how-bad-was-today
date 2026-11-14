-- Runs once, on first initialisation of the PostgreSQL data volume.
-- Creates the disposable database used by the integration test suite so a
-- developer can point TEST_DATABASE_URL at the Compose database. The owner
-- defaults to the configured POSTGRES_USER, which is the user this script
-- connects as.
CREATE DATABASE daily_signal_test;
