-- TexWorkforce Optimizer Seed Data
-- Run this after schema.sql to populate initial data
-- Compatible with MySQL 8.0+

SET FOREIGN_KEY_CHECKS = 0;

-- Clear existing data (in reverse dependency order)
DELETE FROM `user_sessions`;
DELETE FROM `alerts`;
DELETE FROM `daily_reports`;
DELETE FROM `production_logs`;
DELETE FROM `machine_downtime`;
DELETE FROM `machine_telemetry`;
DELETE FROM `shift_assignments`;
DELETE FROM `shifts`;
DELETE FROM `operator_certifications`;
DELETE FROM `certifications`;
DELETE FROM `machines`;
DELETE FROM `machine_types`;
DELETE FROM `users`;
DELETE FROM `departments`;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- DEPARTMENTS
-- ============================================
INSERT INTO `departments` (`name`, `code`, `description`) VALUES
('Spinning', 'SPN', 'Yarn spinning and fiber preparation department'),
('Weaving', 'WVG', 'Fabric weaving and loom operations'),
('Dyeing', 'DYE', 'Fabric dyeing and color processing'),
('Finishing', 'FNS', 'Fabric finishing and treatment'),
('Quality Control', 'QC', 'Quality inspection and testing'),
('Maintenance', 'MNT', 'Machine maintenance and repair');

-- ============================================
-- MACHINE TYPES
-- ============================================
INSERT INTO `machine_types` (`name`, `code`, `description`, `required_certifications`, `default_capacity`, `maintenance_interval_hours`) VALUES
('Ring Spinning Frame', 'RSF', 'Ring spinning machine for yarn production', 
 JSON_ARRAY(
  JSON_OBJECT('code', 'RSO', 'level', 1),
  JSON_OBJECT('code', 'RSO', 'level', 2)
 ),
 500, 8),

('Air Jet Loom', 'AJL', 'Air jet weaving loom for high-speed fabric production',
 JSON_ARRAY(
  JSON_OBJECT('code', 'AJL', 'level', 1),
  JSON_OBJECT('code', 'AJL', 'level', 2)
 ),
 200, 8),

('Rapier Loom', 'RPL', 'Rapier weaving loom for versatile fabric production',
 JSON_ARRAY(
  JSON_OBJECT('code', 'RPL', 'level', 1),
  JSON_OBJECT('code', 'RPL', 'level', 2)
 ),
 180, 8),

('Jacquard Loom', 'JQL', 'Jacquard weaving loom for complex patterns',
 JSON_ARRAY(
  JSON_OBJECT('code', 'JQW', 'level', 2),
  JSON_OBJECT('code', 'JQW', 'level', 3)
 ),
 120, 6),

('Winch Dyeing Machine', 'WDM', 'Winch dyeing machine for fabric dyeing',
 JSON_ARRAY(
  JSON_OBJECT('code', 'WDO', 'level', 1)
 ),
 1000, 12),

('Jet Dyeing Machine', 'JDM', 'High temperature jet dyeing machine',
 JSON_ARRAY(
  JSON_OBJECT('code', 'JDO', 'level', 1),
  JSON_OBJECT('code', 'JDO', 'level', 2)
 ),
 800, 10),

('Stenter Frame', 'STF', 'Fabric finishing stenter frame',
 JSON_ARRAY(
  JSON_OBJECT('code', 'STO', 'level', 1)
 ),
 1500, 8);

-- ============================================
-- CERTIFICATIONS
-- ============================================
INSERT INTO `certifications` (`name`, `code`, `level`, `description`, `validity_months`) VALUES
('Ring Spinning Operation', 'RSO', 1, 'Basic ring spinning frame operation', 12),
('Ring Spinning Operation', 'RSO', 2, 'Advanced ring spinning frame operation', 12),
('Ring Spinning Operation', 'RSO', 3, 'Expert ring spinning frame operation & troubleshooting', 12),
('Air Jet Loom Operation', 'AJL', 1, 'Basic air jet loom operation', 12),
('Air Jet Loom Operation', 'AJL', 2, 'Advanced air jet loom operation', 12),
('Air Jet Loom Operation', 'AJL', 3, 'Expert air jet loom operation & maintenance', 12),
('Rapier Loom Operation', 'RPL', 1, 'Basic rapier loom operation', 12),
('Rapier Loom Operation', 'RPL', 2, 'Advanced rapier loom operation', 12),
('Jacquard Weaving', 'JQW', 1, 'Basic jacquard loom operation', 12),
('Jacquard Weaving', 'JQW', 2, 'Advanced jacquard pattern programming', 12),
('Jacquard Weaving', 'JQW', 3, 'Expert jacquard design & troubleshooting', 12),
('Winch Dyeing Operation', 'WDO', 1, 'Winch dyeing machine operation', 12),
('Jet Dyeing Operation', 'JDO', 1, 'Jet dyeing machine operation', 12),
('Jet Dyeing Operation', 'JDO', 2, 'Advanced jet dyeing process control', 12),
('Stenter Operation', 'STO', 1, 'Stenter frame operation & finishing', 12),
('Machine Maintenance', 'MNT', 1, 'General machine maintenance & repair', 24),
('Quality Inspection', 'QCI', 1, 'Fabric quality inspection & grading', 12);

-- ============================================
-- SHIFTS
-- ============================================
INSERT INTO `shifts` (`name`, `code`, `start_time`, `end_time`, `duration_hours`, `rest_period_hours`) VALUES
('Morning Shift', 'MOR', '06:00:00', '14:00:00', 8.0, 11.0),
('Evening Shift', 'EVE', '14:00:00', '22:00:00', 8.0, 11.0),
('Night Shift', 'NIT', '22:00:00', '06:00:00', 8.0, 11.0),
('Extended Morning', 'EMR', '06:00:00', '18:00:00', 12.0, 11.0),
('Extended Evening', 'EEV', '18:00:00', '06:00:00', 12.0, 11.0);

-- ============================================
-- USERS (Passwords are bcrypt hashes of: Admin@123, Supervisor@123, Operator@123)
-- Hash for 'Admin@123': $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S
-- Hash for 'Supervisor@123': $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S
-- Hash for 'Operator@123': $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S
-- All use same hash for simplicity in seed data
-- ============================================

-- Admin User
INSERT INTO `users` (`employee_id`, `name`, `email`, `password_hash`, `role`, `department_id`, `shift_pattern`, `is_active`) VALUES
('ADMIN001', 'System Administrator', 'admin@texworkforce.com', 
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'admin', 3, 'morning', TRUE);

-- Supervisors
INSERT INTO `users` (`employee_id`, `name`, `email`, `password_hash`, `role`, `department_id`, `shift_pattern`, `is_active`) VALUES
('SUPV001', 'Shift Supervisor', 'supervisor@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'supervisor', 2, 'morning', TRUE),
('SUPV002', 'Evening Supervisor', 'evening.sup@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'supervisor', 2, 'evening', TRUE),
('SUPV003', 'Night Supervisor', 'night.sup@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'supervisor', 2, 'night', TRUE);

-- Operators - Spinning
INSERT INTO `users` (`employee_id`, `name`, `email`, `password_hash`, `role`, `department_id`, `shift_pattern`, `is_active`) VALUES
('OPR001', 'John Doe', 'john.doe@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 1, 'morning', TRUE),
('OPR002', 'Jane Smith', 'jane.smith@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 1, 'morning', TRUE),
('OPR003', 'Mike Johnson', 'mike.johnson@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 1, 'evening', TRUE),
('OPR004', 'Sarah Wilson', 'sarah.wilson@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 1, 'evening', TRUE),
('OPR005', 'David Brown', 'david.brown@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 1, 'night', TRUE),
('OPR006', 'Lisa Davis', 'lisa.davis@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 1, 'night', TRUE);

-- Operators - Weaving
INSERT INTO `users` (`employee_id`, `name`, `email`, `password_hash`, `role`, `department_id`, `shift_pattern`, `is_active`) VALUES
('OPR007', 'Robert Miller', 'robert.miller@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 2, 'morning', TRUE),
('OPR008', 'Emily Taylor', 'emily.taylor@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 2, 'morning', TRUE),
('OPR009', 'James Anderson', 'james.anderson@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 2, 'evening', TRUE),
('OPR010', 'Maria Garcia', 'maria.garcia@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 2, 'evening', TRUE),
('OPR011', 'William Martinez', 'william.martinez@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 2, 'night', TRUE),
('OPR012', 'Jennifer Robinson', 'jennifer.robinson@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 2, 'night', TRUE);

-- Operators - Dyeing
INSERT INTO `users` (`employee_id`, `name`, `email`, `password_hash`, `role`, `department_id`, `shift_pattern`, `is_active`) VALUES
('OPR013', 'Christopher Clark', 'christopher.clark@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 3, 'morning', TRUE),
('OPR014', 'Amanda Rodriguez', 'amanda.rodriguez@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 3, 'morning', TRUE),
('OPR015', 'Daniel Lewis', 'daniel.lewis@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 3, 'evening', TRUE),
('OPR016', 'Michelle Lee', 'michelle.lee@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 3, 'evening', TRUE),
('OPR017', 'Matthew Walker', 'matthew.walker@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 3, 'night', TRUE),
('OPR018', 'Stephanie Hall', 'stephanie.hall@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 3, 'night', TRUE);

-- Operators - Finishing
INSERT INTO `users` (`employee_id`, `name`, `email`, `password_hash`, `role`, `department_id`, `shift_pattern`, `is_active`) VALUES
('OPR019', 'Andrew Allen', 'andrew.allen@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 4, 'morning', TRUE),
('OPR020', 'Nicole Young', 'nicole.young@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 4, 'morning', TRUE),
('OPR021', 'Joshua King', 'joshua.king@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 4, 'evening', TRUE),
('OPR022', 'Elizabeth Wright', 'elizabeth.wright@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 4, 'evening', TRUE),
('OPR023', 'Kevin Scott', 'kevin.scott@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 4, 'night', TRUE),
('OPR024', 'Rachel Green', 'rachel.green@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 4, 'night', TRUE);

-- Maintenance Operators
INSERT INTO `users` (`employee_id`, `name`, `email`, `password_hash`, `role`, `department_id`, `shift_pattern`, `is_active`) VALUES
('MNT001', 'Maintenance Tech 1', 'maintenance1@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 6, 'morning', TRUE),
('MNT002', 'Maintenance Tech 2', 'maintenance2@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 6, 'evening', TRUE);

-- QC Operators
INSERT INTO `users` (`employee_id`, `name`, `email`, `password_hash`, `role`, `department_id`, `shift_pattern`, `is_active`) VALUES
('QC001', 'QC Inspector 1', 'qc1@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 5, 'morning', TRUE),
('QC002', 'QC Inspector 2', 'qc2@texworkforce.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'operator', 5, 'evening', TRUE);

-- Update department managers
UPDATE `departments` SET `manager_id` = (SELECT `id` FROM `users` WHERE `employee_id` = 'SUPV001' LIMIT 1) WHERE `code` = 'WVG';
UPDATE `departments` SET `manager_id` = (SELECT `id` FROM `users` WHERE `employee_id` = 'OPR001' LIMIT 1) WHERE `code` = 'SPN';
UPDATE `departments` SET `manager_id` = (SELECT `id` FROM `users` WHERE `employee_id` = 'OPR013' LIMIT 1) WHERE `code` = 'DYE';
UPDATE `departments` SET `manager_id` = (SELECT `id` FROM `users` WHERE `employee_id` = 'OPR019' LIMIT 1) WHERE `code` = 'FNS';
UPDATE `departments` SET `manager_id` = (SELECT `id` FROM `users` WHERE `employee_id` = 'QC001' LIMIT 1) WHERE `code` = 'QC';
UPDATE `departments` SET `manager_id` = (SELECT `id` FROM `users` WHERE `employee_id` = 'MNT001' LIMIT 1) WHERE `code` = 'MNT';

-- ============================================
-- OPERATOR CERTIFICATIONS
-- ============================================
-- OPR001 (John Doe) - Spinning: RSO L2, RSO L3
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR001'), (SELECT id FROM certifications WHERE code = 'RSO' AND level = 2), '2023-01-15', '2024-01-15', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR001'), (SELECT id FROM certifications WHERE code = 'RSO' AND level = 3), '2023-06-01', '2024-06-01', 'active', 1);

-- OPR002 (Jane Smith) - Weaving: JQW L3, AJL L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR002'), (SELECT id FROM certifications WHERE code = 'JQW' AND level = 3), '2022-12-01', '2023-12-01', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR002'), (SELECT id FROM certifications WHERE code = 'AJL' AND level = 1), '2023-03-01', '2024-03-01', 'active', 1);

-- OPR003 (Mike Johnson) - Spinning: RSO L3
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR003'), (SELECT id FROM certifications WHERE code = 'RSO' AND level = 3), '2023-02-01', '2024-02-01', 'active', 1);

-- OPR004 (Sarah Wilson) - Spinning: RSO L2, Weaving: AJL L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR004'), (SELECT id FROM certifications WHERE code = 'RSO' AND level = 2), '2023-01-10', '2024-01-10', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR004'), (SELECT id FROM certifications WHERE code = 'AJL' AND level = 1), '2023-04-01', '2024-04-01', 'active', 1);

-- OPR005 (David Brown) - Dyeing: JDO L2, WDO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR005'), (SELECT id FROM certifications WHERE code = 'JDO' AND level = 2), '2023-01-20', '2024-01-20', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR005'), (SELECT id FROM certifications WHERE code = 'WDO' AND level = 1), '2023-05-01', '2024-05-01', 'active', 1);

-- OPR006 (Lisa Davis) - Finishing: STO L1, JDO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR006'), (SELECT id FROM certifications WHERE code = 'STO' AND level = 1), '2023-02-15', '2024-02-15', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR006'), (SELECT id FROM certifications WHERE code = 'JDO' AND level = 1), '2023-06-10', '2024-06-10', 'active', 1);

-- OPR007 (Robert Miller) - Weaving: AJL L2, RPL L2
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR007'), (SELECT id FROM certifications WHERE code = 'AJL' AND level = 2), '2023-01-05', '2024-01-05', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR007'), (SELECT id FROM certifications WHERE code = 'RPL' AND level = 2), '2023-04-10', '2024-04-10', 'active', 1);

-- OPR008 (Emily Taylor) - Weaving: JQW L3, AJL L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR008'), (SELECT id FROM certifications WHERE code = 'JQW' AND level = 3), '2022-11-15', '2023-11-15', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR008'), (SELECT id FROM certifications WHERE code = 'AJL' AND level = 1), '2023-02-20', '2024-02-20', 'active', 1);

-- OPR009 (James Anderson) - Weaving: RPL L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR009'), (SELECT id FROM certifications WHERE code = 'RPL' AND level = 1), '2023-03-10', '2024-03-10', 'active', 1);

-- OPR010 (Maria Garcia) - Weaving: RPL L2, AJL L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR010'), (SELECT id FROM certifications WHERE code = 'RPL' AND level = 2), '2023-01-25', '2024-01-25', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR010'), (SELECT id FROM certifications WHERE code = 'AJL' AND level = 1), '2023-05-15', '2024-05-15', 'active', 1);

-- OPR011 (William Martinez) - Weaving: JQW L2
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR011'), (SELECT id FROM certifications WHERE code = 'JQW' AND level = 2), '2023-02-01', '2024-02-01', 'active', 1);

-- OPR012 (Jennifer Robinson) - Weaving: AJL L2
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR012'), (SELECT id FROM certifications WHERE code = 'AJL' AND level = 2), '2023-03-20', '2024-03-20', 'active', 1);

-- OPR013 (Christopher Clark) - Dyeing: JDO L2, WDO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR013'), (SELECT id FROM certifications WHERE code = 'JDO' AND level = 2), '2023-01-10', '2024-01-10', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR013'), (SELECT id FROM certifications WHERE code = 'WDO' AND level = 1), '2023-04-01', '2024-04-01', 'active', 1);

-- OPR014 (Amanda Rodriguez) - Dyeing: JDO L1, WDO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR014'), (SELECT id FROM certifications WHERE code = 'JDO' AND level = 1), '2023-02-10', '2024-02-10', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR014'), (SELECT id FROM certifications WHERE code = 'WDO' AND level = 1), '2023-05-01', '2024-05-01', 'active', 1);

-- OPR015 (Daniel Lewis) - Dyeing: JDO L2
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR015'), (SELECT id FROM certifications WHERE code = 'JDO' AND level = 2), '2023-01-15', '2024-01-15', 'active', 1);

-- OPR016 (Michelle Lee) - Dyeing: WDO L1, JDO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR016'), (SELECT id FROM certifications WHERE code = 'WDO' AND level = 1), '2023-03-01', '2024-03-01', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR016'), (SELECT id FROM certifications WHERE code = 'JDO' AND level = 1), '2023-06-01', '2024-06-01', 'active', 1);

-- OPR017 (Matthew Walker) - Dyeing: JDO L2, MNT L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR017'), (SELECT id FROM certifications WHERE code = 'JDO' AND level = 2), '2023-01-20', '2024-01-20', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR017'), (SELECT id FROM certifications WHERE code = 'MNT' AND level = 1), '2022-12-01', '2024-12-01', 'active', 1);

-- OPR018 (Stephanie Hall) - Dyeing: WDO L1, QCI L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR018'), (SELECT id FROM certifications WHERE code = 'WDO' AND level = 1), '2023-02-01', '2024-02-01', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR018'), (SELECT id FROM certifications WHERE code = 'QCI' AND level = 1), '2023-05-01', '2024-05-01', 'active', 1);

-- OPR019 (Andrew Allen) - Finishing: STO L1, JDO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR019'), (SELECT id FROM certifications WHERE code = 'STO' AND level = 1), '2023-01-10', '2024-01-10', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR019'), (SELECT id FROM certifications WHERE code = 'JDO' AND level = 1), '2023-04-01', '2024-04-01', 'active', 1);

-- OPR020 (Nicole Young) - Finishing: STO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR020'), (SELECT id FROM certifications WHERE code = 'STO' AND level = 1), '2023-02-10', '2024-02-10', 'active', 1);

-- OPR021 (Joshua King) - Finishing: STO L1, MNT L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR021'), (SELECT id FROM certifications WHERE code = 'STO' AND level = 1), '2023-03-01', '2024-03-01', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR021'), (SELECT id FROM certifications WHERE code = 'MNT' AND level = 1), '2022-11-01', '2024-11-01', 'active', 1);

-- OPR022 (Elizabeth Wright) - Finishing: STO L1, QCI L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR022'), (SELECT id FROM certifications WHERE code = 'STO' AND level = 1), '2023-01-15', '2024-01-15', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'OPR022'), (SELECT id FROM certifications WHERE code = 'QCI' AND level = 1), '2023-04-01', '2024-04-01', 'active', 1);

-- OPR023 (Kevin Scott) - Finishing: STO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR023'), (SELECT id FROM certifications WHERE code = 'STO' AND level = 1), '2023-02-20', '2024-02-20', 'active', 1);

-- OPR024 (Rachel Green) - Finishing: STO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'OPR024'), (SELECT id FROM certifications WHERE code = 'STO' AND level = 1), '2023-03-10', '2024-03-10', 'active', 1);

-- MNT001 - Maintenance: MNT L1, RSO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'MNT001'), (SELECT id FROM certifications WHERE code = 'MNT' AND level = 1), '2022-10-01', '2024-10-01', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'MNT001'), (SELECT id FROM certifications WHERE code = 'RSO' AND level = 1), '2023-01-01', '2024-01-01', 'active', 1);

-- MNT002 - Maintenance: MNT L1, AJL L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'MNT002'), (SELECT id FROM certifications WHERE code = 'MNT' AND level = 1), '2022-11-01', '2024-11-01', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'MNT002'), (SELECT id FROM certifications WHERE code = 'AJL' AND level = 1), '2023-02-01', '2024-02-01', 'active', 1);

-- QC001 - Quality: QCI L1, RSO L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'QC001'), (SELECT id FROM certifications WHERE code = 'QCI' AND level = 1), '2023-01-01', '2024-01-01', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'QC001'), (SELECT id FROM certifications WHERE code = 'RSO' AND level = 1), '2023-03-01', '2024-03-01', 'active', 1);

-- QC002 - Quality: QCI L1, AJL L1
INSERT INTO `operator_certifications` (`user_id`, `certification_id`, `obtained_date`, `expiry_date`, `status`, `issued_by`) VALUES
((SELECT id FROM users WHERE employee_id = 'QC002'), (SELECT id FROM certifications WHERE code = 'QCI' AND level = 1), '2023-01-15', '2024-01-15', 'active', 1),
((SELECT id FROM users WHERE employee_id = 'QC002'), (SELECT id FROM certifications WHERE code = 'AJL' AND level = 1), '2023-04-01', '2024-04-01', 'active', 1);

-- ============================================
-- MACHINES
-- ============================================
-- Spinning Machines (Zone A)
INSERT INTO `machines` (`machine_code`, `name`, `machine_type_id`, `department_id`, `location_x`, `location_y`, `floor_zone`, `capacity_max`, `mqtt_topic`, `status`) VALUES
('RSF-01', 'Ring Spinning Frame 1', (SELECT id FROM machine_types WHERE code = 'RSF'), (SELECT id FROM departments WHERE code = 'SPN'), 100, 100, 'A', 500, 'texworkforce/machines/RSF-01/telemetry', 'active'),
('RSF-02', 'Ring Spinning Frame 2', (SELECT id FROM machine_types WHERE code = 'RSF'), (SELECT id FROM departments WHERE code = 'SPN'), 200, 100, 'A', 500, 'texworkforce/machines/RSF-02/telemetry', 'active'),
('RSF-03', 'Ring Spinning Frame 3', (SELECT id FROM machine_types WHERE code = 'RSF'), (SELECT id FROM departments WHERE code = 'SPN'), 300, 100, 'A', 500, 'texworkforce/machines/RSF-03/telemetry', 'idle'),
('RSF-04', 'Ring Spinning Frame 4', (SELECT id FROM machine_types WHERE code = 'RSF'), (SELECT id FROM departments WHERE code = 'SPN'), 400, 100, 'A', 500, 'texworkforce/machines/RSF-04/telemetry', 'active'),
('RSF-05', 'Ring Spinning Frame 5', (SELECT id FROM machine_types WHERE code = 'RSF'), (SELECT id FROM departments WHERE code = 'SPN'), 500, 100, 'A', 500, 'texworkforce/machines/RSF-05/telemetry', 'idle');

-- Weaving Machines (Zone B)
INSERT INTO `machines` (`machine_code`, `name`, `machine_type_id`, `department_id`, `location_x`, `location_y`, `floor_zone`, `capacity_max`, `mqtt_topic`, `status`) VALUES
('AJL-01', 'Air Jet Loom 1', (SELECT id FROM machine_types WHERE code = 'AJL'), (SELECT id FROM departments WHERE code = 'WVG'), 100, 300, 'B', 200, 'texworkforce/machines/AJL-01/telemetry', 'active'),
('AJL-02', 'Air Jet Loom 2', (SELECT id FROM machine_types WHERE code = 'AJL'), (SELECT id FROM departments WHERE code = 'WVG'), 200, 300, 'B', 200, 'texworkforce/machines/AJL-02/telemetry', 'active'),
('AJL-03', 'Air Jet Loom 3', (SELECT id FROM machine_types WHERE code = 'AJL'), (SELECT id FROM departments WHERE code = 'WVG'), 300, 300, 'B', 200, 'texworkforce/machines/AJL-03/telemetry', 'idle'),
('RPL-01', 'Rapier Loom 1', (SELECT id FROM machine_types WHERE code = 'RPL'), (SELECT id FROM departments WHERE code = 'WVG'), 100, 400, 'B', 180, 'texworkforce/machines/RPL-01/telemetry', 'active'),
('RPL-02', 'Rapier Loom 2', (SELECT id FROM machine_types WHERE code = 'RPL'), (SELECT id FROM departments WHERE code = 'WVG'), 200, 400, 'B', 180, 'texworkforce/machines/RPL-02/telemetry', 'idle'),
('RPL-03', 'Rapier Loom 3', (SELECT id FROM machine_types WHERE code = 'RPL'), (SELECT id FROM departments WHERE code = 'WVG'), 300, 400, 'B', 180, 'texworkforce/machines/RPL-03/telemetry', 'active'),
('JQL-01', 'Jacquard Loom 1', (SELECT id FROM machine_types WHERE code = 'JQL'), (SELECT id FROM departments WHERE code = 'WVG'), 100, 500, 'C', 120, 'texworkforce/machines/JQL-01/telemetry', 'active'),
('JQL-02', 'Jacquard Loom 2', (SELECT id FROM machine_types WHERE code = 'JQL'), (SELECT id FROM departments WHERE code = 'WVG'), 200, 500, 'C', 120, 'texworkforce/machines/JQL-02/telemetry', 'maintenance');

-- Dyeing Machines (Zone D)
INSERT INTO `machines` (`machine_code`, `name`, `machine_type_id`, `department_id`, `location_x`, `location_y`, `floor_zone`, `capacity_max`, `mqtt_topic`, `status`) VALUES
('WDM-01', 'Winch Dyeing Machine 1', (SELECT id FROM machine_types WHERE code = 'WDM'), (SELECT id FROM departments WHERE code = 'DYE'), 100, 200, 'D', 1000, 'texworkforce/machines/WDM-01/telemetry', 'active'),
('JDM-01', 'Jet Dyeing Machine 1', (SELECT id FROM machine_types WHERE code = 'JDM'), (SELECT id FROM departments WHERE code = 'DYE'), 200, 200, 'D', 800, 'texworkforce/machines/JDM-01/telemetry', 'active'),
('JDM-02', 'Jet Dyeing Machine 2', (SELECT id FROM machine_types WHERE code = 'JDM'), (SELECT id FROM departments WHERE code = 'DYE'), 300, 200, 'D', 800, 'texworkforce/machines/JDM-02/telemetry', 'idle');

-- Finishing Machines (Zone E)
INSERT INTO `machines` (`machine_code`, `name`, `machine_type_id`, `department_id`, `location_x`, `location_y`, `floor_zone`, `capacity_max`, `mqtt_topic`, `status`) VALUES
('STF-01', 'Stenter Frame 1', (SELECT id FROM machine_types WHERE code = 'STF'), (SELECT id FROM departments WHERE code = 'FNS'), 100, 100, 'E', 1500, 'texworkforce/machines/STF-01/telemetry', 'active'),
('STF-02', 'Stenter Frame 2', (SELECT id FROM machine_types WHERE code = 'STF'), (SELECT id FROM departments WHERE code = 'FNS'), 200, 100, 'E', 1500, 'texworkforce/machines/STF-02/telemetry', 'idle');

-- ============================================
-- SAMPLE SHIFT ASSIGNMENTS (for today)
-- ============================================
-- Get today's date for assignments
SET @today = CURDATE();

-- Morning shift assignments
INSERT INTO `shift_assignments` (`shift_id`, `machine_id`, `operator_id`, `supervisor_id`, `status`, `assigned_at`) VALUES
-- Spinning Morning
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'RSF-01'), (SELECT id FROM users WHERE employee_id = 'OPR001'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'started', NOW()),
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'RSF-02'), (SELECT id FROM users WHERE employee_id = 'OPR002'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'started', NOW()),
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'RSF-04'), (SELECT id FROM users WHERE employee_id = 'OPR003'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'assigned', NOW()),
-- Weaving Morning
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'AJL-01'), (SELECT id FROM users WHERE employee_id = 'OPR007'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'started', NOW()),
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'AJL-02'), (SELECT id FROM users WHERE employee_id = 'OPR008'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'started', NOW()),
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'RPL-01'), (SELECT id FROM users WHERE employee_id = 'OPR009'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'started', NOW()),
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'JQL-01'), (SELECT id FROM users WHERE employee_id = 'OPR010'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'assigned', NOW()),
-- Dyeing Morning
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'WDM-01'), (SELECT id FROM users WHERE employee_id = 'OPR013'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'started', NOW()),
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'JDM-01'), (SELECT id FROM users WHERE employee_id = 'OPR014'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'assigned', NOW()),
-- Finishing Morning
((SELECT id FROM shifts WHERE code = 'MOR'), (SELECT id FROM machines WHERE machine_code = 'STF-01'), (SELECT id FROM users WHERE employee_id = 'OPR019'), (SELECT id FROM users WHERE employee_id = 'SUPV001'), 'started', NOW());

-- Evening shift assignments
INSERT INTO `shift_assignments` (`shift_id`, `machine_id`, `operator_id`, `supervisor_id`, `status`, `assigned_at`) VALUES
-- Spinning Evening
((SELECT id FROM shifts WHERE code = 'EVE'), (SELECT id FROM machines WHERE machine_code = 'RSF-03'), (SELECT id FROM users WHERE employee_id = 'OPR004'), (SELECT id FROM users WHERE employee_id = 'SUPV002'), 'assigned', NOW()),
((SELECT id FROM shifts WHERE code = 'EVE'), (SELECT id FROM machines WHERE machine_code = 'RSF-05'), (SELECT id FROM users WHERE employee_id = 'OPR005'), (SELECT id FROM users WHERE employee_id = 'SUPV002'), 'assigned', NOW()),
-- Weaving Evening
((SELECT id FROM shifts WHERE code = 'EVE'), (SELECT id FROM machines WHERE machine_code = 'AJL-03'), (SELECT id FROM users WHERE employee_id = 'OPR011'), (SELECT id FROM users WHERE employee_id = 'SUPV002'), 'assigned', NOW()),
((SELECT id FROM shifts WHERE code = 'EVE'), (SELECT id FROM machines WHERE machine_code = 'RPL-02'), (SELECT id FROM users WHERE employee_id = 'OPR012'), (SELECT id FROM users WHERE employee_id = 'SUPV002'), 'assigned', NOW()),
((SELECT id FROM shifts WHERE code = 'EVE'), (SELECT id FROM machines WHERE machine_code = 'RPL-03'), (SELECT id FROM users WHERE employee_id = 'OPR011'), (SELECT id FROM users WHERE employee_id = 'SUPV002'), 'assigned', NOW()),
-- Dyeing Evening
((SELECT id FROM shifts WHERE code = 'EVE'), (SELECT id FROM machines WHERE machine_code = 'JDM-02'), (SELECT id FROM users WHERE employee_id = 'OPR015'), (SELECT id FROM users WHERE employee_id = 'SUPV002'), 'assigned', NOW()),
-- Finishing Evening
((SELECT id FROM shifts WHERE code = 'EVE'), (SELECT id FROM machines WHERE machine_code = 'STF-02'), (SELECT id FROM users WHERE employee_id = 'OPR021'), (SELECT id FROM users WHERE employee_id = 'SUPV002'), 'assigned', NOW());

-- Night shift assignments
INSERT INTO `shift_assignments` (`shift_id`, `machine_id`, `operator_id`, `supervisor_id`, `status`, `assigned_at`) VALUES
-- Spinning Night
((SELECT id FROM shifts WHERE code = 'NIT'), (SELECT id FROM machines WHERE machine_code = 'RSF-01'), (SELECT id FROM users WHERE employee_id = 'OPR006'), (SELECT id FROM users WHERE employee_id = 'SUPV003'), 'assigned', NOW()),
((SELECT id FROM shifts WHERE code = 'NIT'), (SELECT id FROM machines WHERE machine_code = 'RSF-02'), (SELECT id FROM users WHERE employee_id = 'OPR005'), (SELECT id FROM users WHERE employee_id = 'SUPV003'), 'assigned', NOW()),
-- Weaving Night
((SELECT id FROM shifts WHERE code = 'NIT'), (SELECT id FROM machines WHERE machine_code = 'AJL-01'), (SELECT id FROM users WHERE employee_id = 'OPR012'), (SELECT id FROM users WHERE employee_id = 'SUPV003'), 'assigned', NOW()),
((SELECT id FROM shifts WHERE code = 'NIT'), (SELECT id FROM machines WHERE machine_code = 'RPL-01'), (SELECT id FROM users WHERE employee_id = 'OPR010'), (SELECT id FROM users WHERE employee_id = 'SUPV003'), 'assigned', NOW()),
-- Dyeing Night
((SELECT id FROM shifts WHERE code = 'NIT'), (SELECT id FROM machines WHERE machine_code = 'WDM-01'), (SELECT id FROM users WHERE employee_id = 'OPR017'), (SELECT id FROM users WHERE employee_id = 'SUPV003'), 'assigned', NOW()),
((SELECT id FROM shifts WHERE code = 'NIT'), (SELECT id FROM machines WHERE machine_code = 'JDM-01'), (SELECT id FROM users WHERE employee_id = 'OPR018'), (SELECT id FROM users WHERE employee_id = 'SUPV003'), 'assigned', NOW()),
-- Finishing Night
((SELECT id FROM shifts WHERE code = 'NIT'), (SELECT id FROM machines WHERE machine_code = 'STF-01'), (SELECT id FROM users WHERE employee_id = 'OPR023'), (SELECT id FROM users WHERE employee_id = 'SUPV003'), 'assigned', NOW());

-- ============================================
-- SAMPLE PRODUCTION LOGS
-- ============================================
INSERT INTO `production_logs` (`shift_assignment_id`, `machine_id`, `operator_id`, `start_time`, `end_time`, `target_yards`, `actual_yards`, `waste_yards`, `quality_grade`, `notes`) VALUES
-- Morning shift production (completed)
((SELECT id FROM shift_assignments WHERE machine_id = (SELECT id FROM machines WHERE machine_code = 'RSF-01') AND shift_id = (SELECT id FROM shifts WHERE code = 'MOR') LIMIT 1), 
 (SELECT id FROM machines WHERE machine_code = 'RSF-01'), 
 (SELECT id FROM users WHERE employee_id = 'OPR001'),
 DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 2 HOUR), 4000, 3850, 120, 'A', 'Good production run'),

((SELECT id FROM shift_assignments WHERE machine_id = (SELECT id FROM machines WHERE machine_code = 'RSF-02') AND shift_id = (SELECT id FROM shifts WHERE code = 'MOR') LIMIT 1), 
 (SELECT id FROM machines WHERE machine_code = 'RSF-02'), 
 (SELECT id FROM users WHERE employee_id = 'OPR002'),
 DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 2 HOUR), 4000, 3920, 80, 'A', 'Target exceeded'),

((SELECT id FROM shift_assignments WHERE machine_id = (SELECT id FROM machines WHERE machine_code = 'AJL-01') AND shift_id = (SELECT id FROM shifts WHERE code = 'MOR') LIMIT 1), 
 (SELECT id FROM machines WHERE machine_code = 'AJL-01'), 
 (SELECT id FROM users WHERE employee_id = 'OPR007'),
 DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 2 HOUR), 1600, 1550, 45, 'B', 'Minor tension issue'),

((SELECT id FROM shift_assignments WHERE machine_id = (SELECT id FROM machines WHERE machine_code = 'AJL-02') AND shift_id = (SELECT id FROM shifts WHERE code = 'MOR') LIMIT 1), 
 (SELECT id FROM machines WHERE machine_code = 'AJL-02'), 
 (SELECT id FROM users WHERE employee_id = 'OPR008'),
 DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 2 HOUR), 1600, 1580, 35, 'A', 'Smooth operation'),

((SELECT id FROM shift_assignments WHERE machine_id = (SELECT id FROM machines WHERE machine_code = 'WDM-01') AND shift_id = (SELECT id FROM shifts WHERE code = 'MOR') LIMIT 1), 
 (SELECT id FROM machines WHERE machine_code = 'WDM-01'), 
 (SELECT id FROM users WHERE employee_id = 'OPR013'),
 DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 2 HOUR), 8000, 7850, 200, 'A', 'Large batch completed'),

((SELECT id FROM shift_assignments WHERE machine_id = (SELECT id FROM machines WHERE machine_code = 'STF-01') AND shift_id = (SELECT id FROM shifts WHERE code = 'MOR') LIMIT 1), 
 (SELECT id FROM machines WHERE machine_code = 'STF-01'), 
 (SELECT id FROM users WHERE employee_id = 'OPR019'),
 DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 2 HOUR), 12000, 11800, 300, 'A', 'Finishing run completed');

-- ============================================
-- SAMPLE ALERTS
-- ============================================
INSERT INTO `alerts` (`alert_type`, `severity`, `machine_id`, `operator_id`, `shift_id`, `message`, `is_read`) VALUES
('machine_fault', 'critical', (SELECT id FROM machines WHERE machine_code = 'JQL-02'), NULL, NULL, 'Jacquard Loom 2 reported fault: Thread breakage detected at position 45', FALSE),
('maintenance_due', 'warning', (SELECT id FROM machines WHERE machine_code = 'RSF-03'), NULL, NULL, 'Ring Spinning Frame 3 maintenance due (150 hours since last maintenance)', FALSE),
('machine_idle', 'warning', (SELECT id FROM machines WHERE machine_code = 'RSF-05'), NULL, NULL, 'Ring Spinning Frame 5 is idle - no operator assigned', FALSE),
('certification_expiring', 'info', NULL, (SELECT id FROM users WHERE employee_id = 'OPR001'), NULL, 'Certification RSO Level 3 for John Doe expires in 30 days', FALSE),
('reallocation_needed', 'warning', (SELECT id FROM machines WHERE machine_code = 'JQL-02'), (SELECT id FROM users WHERE employee_id = 'OPR008'), (SELECT id FROM shifts WHERE code = 'MOR'), 'Operator Jane Smith displaced from Jacquard Loom 2 - reallocation needed', FALSE);

COMMIT;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
SELECT 'Departments' AS table_name, COUNT(*) AS count FROM departments
UNION ALL SELECT 'Users', COUNT(*) FROM users
UNION ALL SELECT 'Machine Types', COUNT(*) FROM machine_types
UNION ALL SELECT 'Machines', COUNT(*) FROM machines
UNION ALL SELECT 'Certifications', COUNT(*) FROM certifications
UNION ALL SELECT 'Operator Certifications', COUNT(*) FROM operator_certifications
UNION ALL SELECT 'Shifts', COUNT(*) FROM shifts
UNION ALL SELECT 'Shift Assignments', COUNT(*) FROM shift_assignments
UNION ALL SELECT 'Production Logs', COUNT(*) FROM production_logs
UNION ALL SELECT 'Alerts', COUNT(*) FROM alerts;