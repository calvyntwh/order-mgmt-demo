-- seed-admin.sql: insert an admin user for CI/e2e smoke
-- This creates a user 'ci-admin' with password 'adminpass123' hashed using bcrypt rounds matching CI.

-- Insert a deterministic admin user for CI smoke tests.
-- Password is `adminpass123` stored as base64-encoded bcrypt bytes to match app verification.
INSERT INTO users (username, password_hash, is_admin)
VALUES (
	'ci-admin',
	'JDJiJDA0JC9xUndNYmtYQjhjbDZoMDRHaU91cXVJa0w2QXA4ejBGWkVEdzR1S1Rqa1lBQnY4TDJWYmNp',
	TRUE
)
ON CONFLICT (username) DO UPDATE SET is_admin = TRUE;
