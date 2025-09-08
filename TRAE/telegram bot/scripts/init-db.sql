-- 初始化数据库脚本
-- 创建 PostGIS 扩展
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建自定义类型
DO $$
BEGIN
    -- 广告状态枚举
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ad_status') THEN
        CREATE TYPE ad_status AS ENUM (
            'draft',                -- 草稿
            'pending_review',       -- 待审核
            'pending_ai_review',    -- 待 AI 审核
            'active',              -- 已发布
            'rejected',            -- 已拒绝
            'expired',             -- 已过期
            'deleted'              -- 已删除
        );
    END IF;

    -- 用户角色枚举
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM (
            'user',                -- 普通用户
            'business',            -- 商业用户
            'moderator',           -- 管理员
            'admin'                -- 超级管理员
        );
    END IF;

    -- 支付状态枚举
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status') THEN
        CREATE TYPE payment_status AS ENUM (
            'pending',             -- 待支付
            'processing',          -- 处理中
            'completed',           -- 已完成
            'failed',              -- 失败
            'refunded'             -- 已退款
        );
    END IF;

    -- AI 审核结果枚举
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ai_review_result') THEN
        CREATE TYPE ai_review_result AS ENUM (
            'approved',            -- 通过
            'rejected',            -- 拒绝
            'needs_human_review'   -- 需要人工审核
        );
    END IF;
END
$$;

-- 创建基础索引函数
CREATE OR REPLACE FUNCTION create_updated_at_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
    RAISE NOTICE 'PostGIS version: %', PostGIS_Version();
END
$$;