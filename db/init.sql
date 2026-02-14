-- Database initialization script for the Parking Reservation System
-- This script runs automatically on first PostgreSQL container start.
-- It seeds the database with sample data so developers can try the app immediately.

-- =============================================================================
-- Parking Spaces
-- =============================================================================
INSERT INTO parking_spaces (space_id, location, is_available, hourly_rate, space_type) VALUES
    ('A1', 'Level 1, Section A', true, 5.00, 'standard'),
    ('A2', 'Level 1, Section A', true, 5.00, 'standard'),
    ('A3', 'Level 1, Section A', true, 5.00, 'standard'),
    ('B1', 'Level 1, Section B', true, 7.00, 'electric'),
    ('B2', 'Level 1, Section B', true, 7.00, 'electric'),
    ('C1', 'Level 2, Section C', true, 4.00, 'standard'),
    ('C2', 'Level 2, Section C', true, 4.00, 'standard'),
    ('D1', 'Level 2, Section D', true, 6.00, 'handicap'),
    ('E1', 'Outdoor, Section E', true, 3.00, 'standard'),
    ('E2', 'Outdoor, Section E', true, 3.00, 'standard')
ON CONFLICT (space_id) DO NOTHING;

-- =============================================================================
-- Sample Users
-- =============================================================================
-- Client user: use this ID when testing as a client
-- UUID: 00000000-0000-0000-0000-000000000001
INSERT INTO users (user_id, username, email, role, full_name) VALUES
    ('00000000-0000-0000-0000-000000000001', 'alice', 'alice@example.com', 'client', 'Alice Johnson'),
    ('00000000-0000-0000-0000-000000000002', 'bob', 'bob@example.com', 'client', 'Bob Smith'),
    ('00000000-0000-0000-0000-000000000099', 'admin', 'admin@example.com', 'admin', 'System Admin')
ON CONFLICT (user_id) DO NOTHING;

-- =============================================================================
-- Sample Reservations (various statuses for demo purposes)
-- =============================================================================
INSERT INTO reservations (reservation_id, user_id, space_id, start_time, end_time, status, created_at, updated_at, admin_notes) VALUES
    -- Alice's pending reservation (awaiting approval)
    ('10000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000001', 'A1',
     NOW() + INTERVAL '1 day', NOW() + INTERVAL '1 day 3 hours',
     'pending', NOW(), NOW(), ''),

    -- Alice's confirmed reservation
    ('10000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000001', 'B1',
     NOW() + INTERVAL '2 days', NOW() + INTERVAL '2 days 2 hours',
     'confirmed', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', 'Approved - regular customer'),

    -- Bob's pending reservation
    ('10000000-0000-0000-0000-000000000003',
     '00000000-0000-0000-0000-000000000002', 'C1',
     NOW() + INTERVAL '1 day 4 hours', NOW() + INTERVAL '1 day 6 hours',
     'pending', NOW(), NOW(), ''),

    -- Bob's rejected reservation
    ('10000000-0000-0000-0000-000000000004',
     '00000000-0000-0000-0000-000000000002', 'D1',
     NOW() + INTERVAL '3 days', NOW() + INTERVAL '3 days 1 hour',
     'rejected', NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day', 'Handicap space requires permit'),

    -- Alice's cancelled reservation
    ('10000000-0000-0000-0000-000000000005',
     '00000000-0000-0000-0000-000000000001', 'E1',
     NOW() + INTERVAL '5 days', NOW() + INTERVAL '5 days 4 hours',
     'cancelled', NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days', '')
ON CONFLICT (reservation_id) DO NOTHING;
