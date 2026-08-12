-- 01-sys_user.sql
-- 系统用户：1 个知识管理员 + 2 个运维工程师 + 1 个停用账号（演示账号停用场景）
-- password_hash 为 bcrypt 占位哈希，真实初始密码 XhOps@2026 的哈希在 Stage 2 由 passlib 生成（见 00-模拟数据说明.md 第 5 节）

INSERT INTO sys_user (id, username, password_hash, display_name, role, status, created_at, updated_at) VALUES
(1, 'admin', '$2b$12$PLACEHOLDER8replace8by8stage2passlib8generated8hash000000', '张伟', 'admin', 'enabled', '2026-07-20 09:00:00', '2026-07-20 09:00:00'),
(2, 'liqiang', '$2b$12$PLACEHOLDER8replace8by8stage2passlib8generated8hash000001', '李强', 'engineer', 'enabled', '2026-07-20 09:05:00', '2026-07-20 09:05:00'),
(3, 'wangfang', '$2b$12$PLACEHOLDER8replace8by8stage2passlib8generated8hash000002', '王芳', 'engineer', 'enabled', '2026-07-20 09:10:00', '2026-07-20 09:10:00'),
(4, 'disabled_user', '$2b$12$PLACEHOLDER8replace8by8stage2passlib8generated8hash000003', '赵离职', 'engineer', 'disabled', '2026-07-20 09:15:00', '2026-07-25 10:00:00');
