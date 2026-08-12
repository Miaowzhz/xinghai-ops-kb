-- 02-guardrail_rule.sql
-- 护栏规则：高危命令拦截、商务价格转人工、敏感操作确认，外加 1 条已停用（enabled=0）示例
-- pattern 中的 \\s 在 MySQL 字符串里存储为 \s（正则空白符）；4 条规则的 pattern 均含 | 或 \s，match_type 均为 regex

INSERT INTO guardrail_rule (id, rule_name, rule_type, match_type, pattern, action, reply_text, enabled, created_at, updated_at) VALUES
(1, '生产环境高危命令拦截', 'high_risk_cmd', 'regex', 'rm\\s+-rf|iptables\\s+-F|shutdown|reboot|drop\\s+database|mkfs|dd\\s+if=', 'block', '您的问题涉及生产环境高危命令（如 rm -rf、iptables -F 等），智能问答不执行也不指导此类操作。请通过变更工单流程提交申请，或联系值班专家协助处理。', 1, '2026-07-21 10:00:00', '2026-07-21 10:00:00'),
(2, '商务价格类问题转人工', 'price', 'regex', '价格|报价|多少钱|折扣|优惠|商务|合同', 'block', '您咨询的是价格、商务类问题，已超出运维知识库的服务范围。请联系您的客户经理或拨打天翼云商务热线获取报价信息。', 1, '2026-07-21 10:05:00', '2026-07-21 10:05:00'),
(3, '敏感操作二次确认', 'sensitive_op', 'regex', '主备切换|释放实例|删除实例|清空数据|重置密码|重启数据库', 'confirm', '您的问题涉及敏感运维操作（如主备切换、释放实例等）。此类操作可能影响业务连续性，执行前请确认：1）已完成数据备份；2）已获得变更审批；3）已通知相关业务方。确认无误后建议通过工单系统走变更流程执行。', 1, '2026-07-21 10:10:00', '2026-07-21 10:10:00'),
(4, '内网测试环境调试命令放行（已停用）', 'high_risk_cmd', 'regex', 'tcpdump|strace|perf\\s+top', 'block', '调试类命令请在测试环境执行。（该规则为早期调试配置，因误伤正常排查咨询已停用，保留记录供参考。）', 0, '2026-07-22 14:00:00', '2026-07-25 18:30:00');
