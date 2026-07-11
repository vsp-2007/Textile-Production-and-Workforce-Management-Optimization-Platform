-- TexWorkforce Optimizer Database Schema
-- MySQL 8.0 compatible
-- Run this script to create the database schema

SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing tables if they exist (for clean install)
DROP TABLE IF EXISTS `user_sessions`;
DROP TABLE IF EXISTS `alerts`;
DROP TABLE IF EXISTS `daily_reports`;
DROP TABLE IF EXISTS `production_logs`;
DROP TABLE IF EXISTS `machine_downtime`;
DROP TABLE IF EXISTS `machine_telemetry`;
DROP TABLE IF EXISTS `shift_assignments`;
DROP TABLE IF EXISTS `shifts`;
DROP TABLE IF EXISTS `operator_certifications`;
DROP TABLE IF EXISTS `certifications`;
DROP TABLE IF EXISTS `machines`;
DROP TABLE IF EXISTS `machine_types`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `departments`;

-- Create tables in dependency order

-- Departments
CREATE TABLE `departments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `manager_id` INT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_departments_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` VARCHAR(50) NOT NULL UNIQUE,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('admin', 'supervisor', 'operator') NOT NULL DEFAULT 'operator',
    `department_id` INT NULL,
    `shift_pattern` VARCHAR(50) NULL,
    `is_active` BOOLEAN DEFAULT TRUE,
    `last_login` DATETIME NULL,
    `failed_login_attempts` INT DEFAULT 0,
    `locked_until` DATETIME NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_employee_id` (`employee_id`),
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_role` (`role`),
    INDEX `idx_users_department` (`department_id`),
    INDEX `idx_users_active` (`is_active`),
    FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Machine Types
CREATE TABLE `machine_types` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `required_certifications` JSON NULL,
    `default_capacity` INT NULL,
    `maintenance_interval_hours` INT DEFAULT 8,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_machine_types_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Machines
CREATE TABLE `machines` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `machine_code` VARCHAR(50) NOT NULL UNIQUE,
    `name` VARCHAR(100) NOT NULL,
    `machine_type_id` INT NOT NULL,
    `department_id` INT NULL,
    `location_x` FLOAT NULL,
    `location_y` FLOAT NULL,
    `floor_zone` VARCHAR(50) NULL,
    `capacity_max` INT NULL,
    `status` ENUM('active', 'idle', 'maintenance', 'fault', 'offline', 'disconnected') DEFAULT 'offline',
    `last_maintenance` DATETIME NULL,
    `maintenance_interval_hours` INT DEFAULT 8,
    `is_active` BOOLEAN DEFAULT TRUE,
    `mqtt_topic` VARCHAR(200) NULL,
    `last_telemetry_at` DATETIME NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_machines_code` (`machine_code`),
    INDEX `idx_machines_status` (`status`),
    INDEX `idx_machines_type` (`machine_type_id`),
    INDEX `idx_machines_department` (`department_id`),
    INDEX `idx_machines_zone` (`floor_zone`),
    INDEX `idx_machines_active` (`is_active`),
    FOREIGN KEY (`machine_type_id`) REFERENCES `machine_types`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Certifications
CREATE TABLE `certifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `level` INT DEFAULT 1,
    `description` TEXT NULL,
    `validity_months` INT DEFAULT 12,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_certifications_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Operator Certifications
CREATE TABLE `operator_certifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `certification_id` INT NOT NULL,
    `obtained_date` DATE NOT NULL,
    `expiry_date` DATE NULL,
    `status` ENUM('active', 'expired', 'revoked', 'pending') DEFAULT 'active',
    `issued_by` INT NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_operator_certs_user` (`user_id`),
    INDEX `idx_operator_certs_cert` (`certification_id`),
    INDEX `idx_operator_certs_status` (`status`),
    INDEX `idx_operator_certs_expiry` (`expiry_date`),
    UNIQUE KEY `uk_user_cert` (`user_id`, `certification_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`certification_id`) REFERENCES `certifications`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`issued_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Shifts
CREATE TABLE `shifts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `start_time` TIME NOT NULL,
    `end_time` TIME NOT NULL,
    `duration_hours` FLOAT NOT NULL,
    `rest_period_hours` FLOAT DEFAULT 11,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_shifts_code` (`code`),
    INDEX `idx_shifts_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Shift Assignments
CREATE TABLE `shift_assignments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `shift_id` INT NOT NULL,
    `machine_id` INT NOT NULL,
    `operator_id` INT NOT NULL,
    `supervisor_id` INT NULL,
    `status` ENUM('assigned', 'started', 'completed', 'reassigned', 'cancelled') DEFAULT 'assigned',
    `assigned_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `started_at` DATETIME NULL,
    `ended_at` DATETIME NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_shift_assignments_shift` (`shift_id`),
    INDEX `idx_shift_assignments_machine` (`machine_id`),
    INDEX `idx_shift_assignments_operator` (`operator_id`),
    INDEX `idx_shift_assignments_supervisor` (`supervisor_id`),
    INDEX `idx_shift_assignments_status` (`status`),
    INDEX `idx_shift_assignments_shift_operator` (`shift_id`, `operator_id`),
    INDEX `idx_shift_assignments_shift_machine` (`shift_id`, `machine_id`),
    FOREIGN KEY (`shift_id`) REFERENCES `shifts`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`machine_id`) REFERENCES `machines`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`operator_id`) REFERENCES `users`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`supervisor_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Machine Telemetry
CREATE TABLE `machine_telemetry` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `machine_id` INT NOT NULL,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `status` ENUM('active', 'idle', 'maintenance', 'fault', 'offline', 'disconnected') NOT NULL,
    `rpm` FLOAT NULL,
    `temperature` FLOAT NULL,
    `vibration` FLOAT NULL,
    `output_count` INT NULL,
    `error_code` VARCHAR(50) NULL,
    `raw_payload` JSON NULL,
    INDEX `idx_telemetry_machine` (`machine_id`),
    INDEX `idx_telemetry_timestamp` (`timestamp`),
    INDEX `idx_telemetry_machine_time` (`machine_id`, `timestamp`),
    FOREIGN KEY (`machine_id`) REFERENCES `machines`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Machine Downtime
CREATE TABLE `machine_downtime` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `machine_id` INT NOT NULL,
    `start_time` DATETIME NOT NULL,
    `end_time` DATETIME NULL,
    `reason` VARCHAR(200) NOT NULL,
    `reported_by` INT NULL,
    `resolved_by` INT NULL,
    `duration_minutes` INT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_downtime_machine` (`machine_id`),
    INDEX `idx_downtime_start` (`start_time`),
    INDEX `idx_downtime_end` (`end_time`),
    FOREIGN KEY (`machine_id`) REFERENCES `machines`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`reported_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`resolved_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Production Logs
CREATE TABLE `production_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `shift_assignment_id` INT NOT NULL,
    `machine_id` INT NOT NULL,
    `operator_id` INT NOT NULL,
    `start_time` DATETIME NOT NULL,
    `end_time` DATETIME NULL,
    `target_yards` INT NULL,
    `actual_yards` INT NULL,
    `waste_yards` INT DEFAULT 0,
    `quality_grade` VARCHAR(20) NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_production_assignment` (`shift_assignment_id`),
    INDEX `idx_production_machine` (`machine_id`),
    INDEX `idx_production_operator` (`operator_id`),
    INDEX `idx_production_start` (`start_time`),
    FOREIGN KEY (`shift_assignment_id`) REFERENCES `shift_assignments`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`machine_id`) REFERENCES `machines`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`operator_id`) REFERENCES `users`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Daily Reports
CREATE TABLE `daily_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `report_date` DATE NOT NULL,
    `shift_id` INT NOT NULL,
    `total_machines` INT DEFAULT 0,
    `active_machines` INT DEFAULT 0,
    `total_operators` INT DEFAULT 0,
    `present_operators` INT DEFAULT 0,
    `total_yards` INT DEFAULT 0,
    `total_waste` INT DEFAULT 0,
    `avg_oee` FLOAT NULL,
    `downtime_minutes` INT DEFAULT 0,
    `generated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_daily_report` (`report_date`, `shift_id`),
    INDEX `idx_daily_reports_date` (`report_date`),
    INDEX `idx_daily_reports_shift` (`shift_id`),
    FOREIGN KEY (`shift_id`) REFERENCES `shifts`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Alerts
CREATE TABLE `alerts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `alert_type` ENUM(
        'machine_fault', 'machine_idle', 'maintenance_due',
        'operator_absent', 'certification_expiring',
        'shift_violation', 'reallocation_needed', 'connection_lost'
    ) NOT NULL,
    `severity` ENUM('info', 'warning', 'critical') DEFAULT 'warning',
    `machine_id` INT NULL,
    `operator_id` INT NULL,
    `shift_id` INT NULL,
    `message` TEXT NOT NULL,
    `is_read` BOOLEAN DEFAULT FALSE,
    `acknowledged_at` DATETIME NULL,
    `acknowledged_by` INT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_alerts_type` (`alert_type`),
    INDEX `idx_alerts_severity` (`severity`),
    INDEX `idx_alerts_machine` (`machine_id`),
    INDEX `idx_alerts_operator` (`operator_id`),
    INDEX `idx_alerts_shift` (`shift_id`),
    INDEX `idx_alerts_read` (`is_read`),
    INDEX `idx_alerts_created` (`created_at`),
    FOREIGN KEY (`machine_id`) REFERENCES `machines`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`operator_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`shift_id`) REFERENCES `shifts`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`acknowledged_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User Sessions (for concurrent session tracking)
CREATE TABLE `user_sessions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `session_token` VARCHAR(255) NOT NULL UNIQUE,
    `device_info` VARCHAR(500) NULL,
    `ip_address` VARCHAR(45) NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `last_activity` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `expires_at` DATETIME NOT NULL,
    `is_active` BOOLEAN DEFAULT TRUE,
    INDEX `idx_sessions_user` (`user_id`),
    INDEX `idx_sessions_token` (`session_token`),
    INDEX `idx_sessions_active` (`is_active`, `expires_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add foreign key for department manager
ALTER TABLE `departments` 
ADD CONSTRAINT `fk_departments_manager` 
FOREIGN KEY (`manager_id`) REFERENCES `users`(`id`) ON DELETE SET NULL;

SET FOREIGN_KEY_CHECKS = 1;

-- Create views for common queries

-- View: Machine with latest telemetry
CREATE OR REPLACE VIEW `v_machine_status` AS
SELECT 
    m.*,
    mt.name AS machine_type_name,
    mt.code AS machine_type_code,
    d.name AS department_name,
    d.code AS department_code,
    t.timestamp AS last_telemetry_time,
    t.status AS telemetry_status,
    t.rpm,
    t.temperature,
    t.vibration,
    t.output_count,
    t.error_code
FROM `machines` m
LEFT JOIN `machine_types` mt ON m.machine_type_id = mt.id
LEFT JOIN `departments` d ON m.department_id = d.id
LEFT JOIN (
    SELECT machine_id, MAX(timestamp) AS max_time
    FROM `machine_telemetry`
    GROUP BY machine_id
) latest ON m.id = latest.machine_id
LEFT JOIN `machine_telemetry` t ON latest.machine_id = t.machine_id AND latest.max_time = t.timestamp;

-- View: Active shift assignments with details
CREATE OR REPLACE VIEW `v_active_assignments` AS
SELECT 
    sa.*,
    s.name AS shift_name,
    s.code AS shift_code,
    s.start_time,
    s.end_time,
    m.machine_code,
    m.name AS machine_name,
    m.status AS machine_status,
    u.name AS operator_name,
    u.employee_id AS operator_employee_id,
    sup.name AS supervisor_name
FROM `shift_assignments` sa
JOIN `shifts` s ON sa.shift_id = s.id
JOIN `machines` m ON sa.machine_id = m.id
JOIN `users` u ON sa.operator_id = u.id
LEFT JOIN `users` sup ON sa.supervisor_id = sup.id
WHERE sa.status IN ('assigned', 'started');

-- View: Operator with certifications
CREATE OR REPLACE VIEW `v_operator_skills` AS
SELECT 
    u.id AS operator_id,
    u.employee_id,
    u.name,
    u.department_id,
    d.name AS department_name,
    JSON_ARRAYAGG(
        JSON_OBJECT(
            'certification_id', c.id,
            'certification_name', c.name,
            'certification_code', c.code,
            'level', c.level,
            'obtained_date', oc.obtained_date,
            'expiry_date', oc.expiry_date,
            'status', oc.status,
            'is_valid', (oc.status = 'active' AND (oc.expiry_date IS NULL OR oc.expiry_date >= CURDATE()))
        )
    ) AS certifications
FROM `users` u
LEFT JOIN `departments` d ON u.department_id = d.id
LEFT JOIN `operator_certifications` oc ON u.id = oc.user_id AND oc.status = 'active'
LEFT JOIN `certifications` c ON oc.certification_id = c.id AND c.is_active = TRUE
WHERE u.role = 'operator' AND u.is_active = TRUE
GROUP BY u.id;

-- View: Production summary by shift
CREATE OR REPLACE VIEW `v_shift_production` AS
SELECT 
    sa.shift_id,
    s.name AS shift_name,
    s.code AS shift_code,
    COUNT(DISTINCT sa.id) AS total_assignments,
    COUNT(DISTINCT CASE WHEN sa.status = 'started' THEN sa.id END) AS active_assignments,
    COUNT(DISTINCT CASE WHEN sa.status = 'completed' THEN sa.id END) AS completed_assignments,
    SUM(pl.target_yards) AS total_target,
    SUM(pl.actual_yards) AS total_actual,
    SUM(pl.waste_yards) AS total_waste,
    AVG(pl.efficiency) AS avg_efficiency
FROM `shift_assignments` sa
JOIN `shifts` s ON sa.shift_id = s.id
LEFT JOIN `production_logs` pl ON sa.id = pl.shift_assignment_id
GROUP BY sa.shift_id, s.name, s.code;

COMMIT;