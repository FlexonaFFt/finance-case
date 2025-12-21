WITH c AS (
    INSERT INTO clients (name, email, password_hash) VALUES
        ('Acme Corp', 'finance@acme.example', NULL),
        ('Orbit Retail', 'ops@orbit.example', NULL),
        ('Sierra Labs', 'team@sierra.example', NULL)
    RETURNING id, name
),
a1 AS (
    INSERT INTO accounts (id, client_id, currency, balance_minor)
    VALUES ('0000-acme-000-001', (SELECT id FROM c WHERE name='Acme Corp'), 'USD', 9500)
    RETURNING id
),
a2 AS (
    INSERT INTO accounts (id, client_id, currency, balance_minor)
    VALUES ('0000-acme-000-002', (SELECT id FROM c WHERE name='Acme Corp'), 'RUB', 82000)
    RETURNING id
),
a3 AS (
    INSERT INTO accounts (id, client_id, currency, balance_minor)
    VALUES ('0000-orbt-000-003', (SELECT id FROM c WHERE name='Orbit Retail'), 'USD', 8700)
    RETURNING id
),
a4 AS (
    INSERT INTO accounts (id, client_id, currency, balance_minor)
    VALUES ('0000-sier-000-004', (SELECT id FROM c WHERE name='Sierra Labs'), 'RUB', 98500)
    RETURNING id
)
INSERT INTO transactions (account_id, amount_minor, currency, description, occurred_at)
VALUES
    ((SELECT id FROM a1), -4500, 'USD', 'Coffee + snacks', NOW() - INTERVAL '2 days'),
    ((SELECT id FROM a1), -23000, 'USD', 'Cloud services', NOW() - INTERVAL '5 days'),
    ((SELECT id FROM a2), 120000, 'EUR', 'Client payment', NOW() - INTERVAL '7 days'),
    ((SELECT id FROM a3), -15000, 'USD', 'Supplies', NOW() - INTERVAL '1 day'),
    ((SELECT id FROM a4), -3200, 'GBP', 'Coffee meeting', NOW() - INTERVAL '3 days'),
    ((SELECT id FROM a4), 50000, 'GBP', 'Contract revenue', NOW() - INTERVAL '9 days');
