-- init-orders.sql: creates orders table for order-service

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  item_name TEXT NOT NULL,
  quantity INT NOT NULL CHECK (quantity >= 1 AND quantity <= 100),
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  admin_action_at TIMESTAMP WITH TIME ZONE
);
