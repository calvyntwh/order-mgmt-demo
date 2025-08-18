Migration note: convert Order.id from text/varchar to UUID

Description:
- The `Order` SQLModel primary key was changed from `str` to `UUID` with a `default_factory=uuid.uuid4` to ensure strongly-typed UUID primary keys.

Suggested Postgres migration steps (manual or use your migration tool):
1. Install the uuid-ossp extension if not present:
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

2. Add a new UUID column with defaults, backfill, then switch primary key:
   ALTER TABLE orders ADD COLUMN id_new UUID DEFAULT uuid_generate_v4();
   UPDATE orders SET id_new = uuid_generate_v4() WHERE id_new IS NULL;

   -- If there are FK constraints referencing orders(id), update those first.

   -- Drop old PK constraint and column, then rename
   ALTER TABLE orders DROP CONSTRAINT orders_pkey;
   ALTER TABLE orders DROP COLUMN id;
   ALTER TABLE orders RENAME COLUMN id_new TO id;
   ALTER TABLE orders ADD PRIMARY KEY (id);

Notes:
- If your table is named differently, adjust the SQL accordingly.
- For zero-downtime migrations consider adding the new column, migrating FKs, and performing a controlled switchover during a maintenance window.
- Update any code/tests that assume string IDs (they may need to use str(uuid) when interacting with HTTP APIs).

Verification:
- Run application tests and integration tests after migration.
- Verify new orders have UUID ids and existing orders are preserved.

