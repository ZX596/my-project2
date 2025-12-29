/*
/*
 竞赛证书智能识别与管理系统 - 数据库表结构
 基于MySQL 8.0
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for certificates
-- ----------------------------
DROP TABLE IF EXISTS `certificates`;
CREATE TABLE `certificates` (
  `cert_id` int NOT NULL AUTO_INCREMENT COMMENT '证书ID',
  `submitter_id` int NOT NULL COMMENT '提交者user_id',
  `submitter_role` enum('student','teacher') NOT NULL COMMENT '提交者角色',
  `student_id` varchar(13) NOT NULL COMMENT '学号（13位）',
  `student_name` varchar(50) NOT NULL COMMENT '学生姓名',
  `department` varchar(100) DEFAULT NULL COMMENT '学生所在学院',
  `competition_name` varchar(200) DEFAULT NULL COMMENT '竞赛项目',
  `award_category` varchar(50) DEFAULT NULL COMMENT '获奖类别（国家级、省级）',
  `award_level` varchar(50) DEFAULT NULL COMMENT '获奖等级（一等奖、二等奖、三等奖、金奖、银奖、铜奖、优秀奖）',
  `competition_type` varchar(20) DEFAULT NULL COMMENT '竞赛类型（A类、B类）',
  `organizer` varchar(200) DEFAULT NULL COMMENT '主办单位',
  `award_date` date DEFAULT NULL COMMENT '获奖时间',
  `advisor` varchar(50) NOT NULL COMMENT '指导教师',
  `file_id` int DEFAULT NULL COMMENT '关联文件ID',
  `file_path` varchar(500) DEFAULT NULL COMMENT '证书文件路径',
  `extraction_method` varchar(50) DEFAULT NULL COMMENT '识别方式（glm4v/baidu/local等）',
  `extraction_confidence` decimal(5,2) DEFAULT NULL COMMENT '识别置信度',
  `status` enum('draft','submitted') NOT NULL DEFAULT 'draft' COMMENT '状态（draft/submitted）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `submitted_at` timestamp NULL DEFAULT NULL COMMENT '提交时间',
  PRIMARY KEY (`cert_id`),
  KEY `idx_submitter` (`submitter_id`),
  KEY `idx_student_id` (`student_id`),
  KEY `idx_status` (`status`),
  KEY `idx_file_id` (`file_id`),
  CONSTRAINT `fk_cert_file` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_cert_submitter` FOREIGN KEY (`submitter_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='证书信息表';

-- ----------------------------
-- Table structure for system_config
-- ----------------------------
DROP TABLE IF EXISTS `system_config`;
CREATE TABLE `system_config` (
  `config_id` int NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `config_key` varchar(100) NOT NULL COMMENT '配置键',
  `config_value` text COMMENT '配置值',
  `description` varchar(255) DEFAULT NULL COMMENT '配置说明',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` int DEFAULT NULL COMMENT '更新者user_id',
  PRIMARY KEY (`config_id`),
  UNIQUE KEY `uk_config_key` (`config_key`),
  KEY `idx_updated_by` (`updated_by`),
  CONSTRAINT `fk_config_user` FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统配置表';

-- 初始化系统配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('submission_deadline', '2025-12-30 23:59:59', '证书提交截止时间'),
('default_extraction_api', 'glm4v', '默认信息提取API'),
('max_file_size_mb', '10', '最大文件大小（MB）');

-- 更新files表，添加必要的字段（如果不存在）
ALTER TABLE `files` 
ADD COLUMN IF NOT EXISTS `file_name` varchar(255) COMMENT '原始文件名' AFTER `id`,
ADD COLUMN IF NOT EXISTS `user_id` int COMMENT '用户ID' AFTER `file_name`,
ADD COLUMN IF NOT EXISTS `upload_time` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间' AFTER `file_size`;

-- 如果files表没有user_id外键，添加外键约束
-- ALTER TABLE `files` ADD CONSTRAINT `fk_file_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

SET FOREIGN_KEY_CHECKS = 1;

*/
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for certificates
-- ----------------------------
DROP TABLE IF EXISTS `certificates`;
CREATE TABLE `certificates` (
  `cert_id` int NOT NULL AUTO_INCREMENT COMMENT '证书ID',
  `submitter_id` int NOT NULL COMMENT '提交者user_id',
  `submitter_role` enum('student','teacher') NOT NULL COMMENT '提交者角色',
  `student_id` varchar(13) NOT NULL COMMENT '学号（13位）',
  `student_name` varchar(50) NOT NULL COMMENT '学生姓名',
  `department` varchar(100) DEFAULT NULL COMMENT '学生所在学院',
  `competition_name` varchar(200) DEFAULT NULL COMMENT '竞赛项目',
  `award_category` varchar(50) DEFAULT NULL COMMENT '获奖类别（国家级、省级）',
  `award_level` varchar(50) DEFAULT NULL COMMENT '获奖等级（一等奖、二等奖、三等奖、金奖、银奖、铜奖、优秀奖）',
  `competition_type` varchar(20) DEFAULT NULL COMMENT '竞赛类型（A类、B类）',
  `organizer` varchar(200) DEFAULT NULL COMMENT '主办单位',
  `award_date` date DEFAULT NULL COMMENT '获奖时间',
  `advisor` varchar(50) NOT NULL COMMENT '指导教师',
  `file_id` int DEFAULT NULL COMMENT '关联文件ID',
  `file_path` varchar(500) DEFAULT NULL COMMENT '证书文件路径',
  `extraction_method` varchar(50) DEFAULT NULL COMMENT '识别方式（glm4v/baidu/local等）',
  `extraction_confidence` decimal(5,2) DEFAULT NULL COMMENT '识别置信度',
  `status` enum('draft','submitted') NOT NULL DEFAULT 'draft' COMMENT '状态（draft/submitted）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `submitted_at` timestamp NULL DEFAULT NULL COMMENT '提交时间',
  PRIMARY KEY (`cert_id`),
  KEY `idx_submitter` (`submitter_id`),
  KEY `idx_student_id` (`student_id`),
  KEY `idx_status` (`status`),
  KEY `idx_file_id` (`file_id`),
  CONSTRAINT `fk_cert_file` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_cert_submitter` FOREIGN KEY (`submitter_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='证书信息表';

-- ----------------------------
-- Table structure for system_config
-- ----------------------------
DROP TABLE IF EXISTS `system_config`;
CREATE TABLE `system_config` (
  `config_id` int NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `config_key` varchar(100) NOT NULL COMMENT '配置键',
  `config_value` text COMMENT '配置值',
  `description` varchar(255) DEFAULT NULL COMMENT '配置说明',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` int DEFAULT NULL COMMENT '更新者user_id',
  PRIMARY KEY (`config_id`),
  UNIQUE KEY `uk_config_key` (`config_key`),
  KEY `idx_updated_by` (`updated_by`),
  CONSTRAINT `fk_config_user` FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统配置表';

-- 初始化系统配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('submission_deadline', '2025-12-30 23:59:59', '证书提交截止时间'),
('default_extraction_api', 'glm4v', '默认信息提取API'),
('max_file_size_mb', '10', '最大文件大小（MB）');

-- 更新files表，添加必要的字段（使用存储过程检查列是否存在）
DELIMITER $$
CREATE PROCEDURE AddColumnIfNotExists()
BEGIN
    -- 检查 file_name 列是否存在
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'files' 
        AND COLUMN_NAME = 'file_name'
    ) THEN
        ALTER TABLE `files` ADD COLUMN `file_name` varchar(255) COMMENT '原始文件名' AFTER `id`;
    END IF;
    
    -- 检查 user_id 列是否存在
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'files' 
        AND COLUMN_NAME = 'user_id'
    ) THEN
        ALTER TABLE `files` ADD COLUMN `user_id` int COMMENT '用户ID' AFTER `file_name`;
    END IF;
    
    -- 检查 upload_time 列是否存在
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'files' 
        AND COLUMN_NAME = 'upload_time'
    ) THEN
        ALTER TABLE `files` ADD COLUMN `upload_time` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间' AFTER `file_size`;
    END IF;
END
$$
DELIMITER ;

-- 执行存储过程
CALL AddColumnIfNotExists();

-- 删除存储过程
DROP PROCEDURE IF EXISTS AddColumnIfNotExists;

-- 可选：如果files表没有user_id外键，添加外键约束
-- 注意：需要先确保user_id列存在
/*
ALTER TABLE `files` 
ADD CONSTRAINT `fk_file_user` 
FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
*/

SET FOREIGN_KEY_CHECKS = 1;