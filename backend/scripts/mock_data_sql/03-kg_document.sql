-- 03-kg_document.sql
-- 知识库文档：4 篇 success（chunk_count 与实际 chunk 数一致）、1 篇 failed（扫描件）、1 篇 parsing
-- file_path 指向后端 uploads/ 目录（将在 Stage 1 随项目骨架创建），mock 阶段文件实体可不存在

INSERT INTO kg_document (id, title, doc_type, product_line, product_version, version, file_path, file_size, file_type, status, fail_reason, chunk_count, created_by, created_at, updated_at) VALUES
(1, '弹性云主机 ECS 产品手册 V3.2', 'manual', 'ECS', 'V3.2', 1, 'uploads/2026/07/ecs-product-manual-v3.2.pdf', 8388608, 'pdf', 'success', NULL, 3, 1, '2026-07-28 10:00:00', '2026-07-28 10:02:31'),
(2, 'VPC 跨域组网故障案例集', 'case', 'VPC', 'V1.5', 1, 'uploads/2026/07/vpc-cross-region-cases.pdf', 2097152, 'pdf', 'success', NULL, 3, 1, '2026-07-28 10:10:00', '2026-07-28 10:11:12'),
(3, 'RDS 主备切换 SOP V2.0', 'sop', 'RDS', 'V2.0', 2, 'uploads/2026/07/rds-ha-switchover-sop-v2.0.md', 524288, 'md', 'success', NULL, 3, 1, '2026-07-28 10:20:00', '2026-08-02 09:15:40'),
(4, '云数据库 RDS API 参考', 'api', 'RDS', 'V2.0', 1, 'uploads/2026/07/rds-api-reference.pdf', 3145728, 'pdf', 'success', NULL, 2, 1, '2026-07-28 10:30:00', '2026-07-28 10:31:55'),
(5, '对象存储 OOS 运维手册（扫描件）', 'manual', 'OOS', 'V1.8', 1, 'uploads/2026/08/oos-ops-manual-scan.pdf', 12582912, 'pdf', 'failed', '未解析到文本内容，请确认不是纯图片扫描件', 0, 1, '2026-08-03 14:00:00', '2026-08-03 14:00:47'),
(6, '云主机备份 CBS 操作手册 V1.0', 'manual', 'CBS', 'V1.0', 1, 'uploads/2026/08/cbs-ops-manual-v1.0.pdf', 4194304, 'pdf', 'parsing', NULL, 0, 1, '2026-08-06 09:30:00', '2026-08-06 09:30:05');
