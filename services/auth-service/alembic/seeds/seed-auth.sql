-- Simple seed data for auth-service used by CI/tests
INSERT INTO users (username, password_hash, is_admin) VALUES ('seed-admin', '', true);
