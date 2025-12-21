-- Helper to generate ids like abcd-1234-5
CREATE OR REPLACE FUNCTION gen_short_id() RETURNS TEXT AS $$
DECLARE
    prefix TEXT;
    mid TEXT;
    suffix TEXT;
BEGIN
    prefix := substring(md5(random()::text) for 4);
    mid := lpad((floor(random() * 10000))::int::text, 4, '0');
    suffix := (floor(random() * 10))::int::text;
    RETURN prefix || '-' || mid || '-' || suffix;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY DEFAULT gen_short_id(),
    name TEXT NOT NULL,
    email TEXT,
    password_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY DEFAULT gen_short_id(),
    client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    currency TEXT NOT NULL,
    balance_minor BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY DEFAULT gen_short_id(),
    account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    amount_minor BIGINT NOT NULL,
    currency TEXT NOT NULL,
    description TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transfers (
    id TEXT PRIMARY KEY DEFAULT gen_short_id(),
    from_account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    to_account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    amount_minor BIGINT NOT NULL,
    currency TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
