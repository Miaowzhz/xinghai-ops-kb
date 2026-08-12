-- 06-qa_feedback_audit.sql
-- 反馈与审核：
--   qa_feedback：1 条点赞（resolved）+ 1 条点踩（pending）+ 1 条点踩拒答消息（resolved，对应 resolved 审核任务）+ 1 条点踩失败消息（pending，对应 rejected 审核任务）
--   audit_task：1 条 pending + 1 条 resolved + 1 条 rejected
-- 点踩对应 qa_message.id=4（RDS 主备切换步骤的答案），审核任务待管理员在 09f-反馈审核工作台处理

INSERT INTO qa_feedback (id, message_id, user_id, feedback_type, reason, status, created_at, updated_at) VALUES
(1, 2, 2, 'like', NULL, 'resolved', '2026-08-05 02:15:00', '2026-08-05 02:15:00'),
(2, 4, 2, 'dislike', '步骤过时且漏了关键一步：SOP V2.0 之后主备切换前必须先冻结写流量（rds-cli freeze-writes），答案直接给出切换命令，按此操作有脑裂丢数风险，疑似按旧版 SOP 生成。', 'pending', '2026-08-05 02:30:00', '2026-08-05 02:30:00'),
(3, 8, 2, 'dislike', '拒答合理，但应引导用户去哪里补充文档或联系谁？答案只说"联系值班专家"缺乏可操作性，建议补充知识缺口反馈入口。', 'resolved', '2026-08-07 10:05:00', '2026-08-08 14:00:00'),
(4, 10, 2, 'dislike', '生成失败没有给出任何有用信息，也没有自动重试，体验差。', 'pending', '2026-08-07 10:10:00', '2026-08-07 10:10:00');

INSERT INTO audit_task (id, feedback_id, message_id, status, resolution, resolved_by, created_at, updated_at) VALUES
(1, 2, 4, 'pending', NULL, NULL, '2026-08-05 02:30:00', '2026-08-05 02:30:00'),
(2, 3, 8, 'resolved', '知识缺失：本地机房 K8s 部署不在当前知识库覆盖范围，已记录补充需求，待后续纳入相关文档后重新入库。', 1, '2026-08-07 10:05:00', '2026-08-08 14:00:00'),
(3, 4, 10, 'rejected', '用户误点：生成失败属系统异常（LLM API 超时），非知识质量问题，已通知运维侧排查 API 稳定性，无需修改知识库内容。', 1, '2026-08-07 10:10:00', '2026-08-08 14:30:00');
