-- 05-qa_session_message.sql
-- 3 个会话：
--   会话 1（李强，跨产品问题 VPC+ECS+RDS，带引用答案，两轮问答）
--   会话 2（王芳，命中高危命令护栏，答案 status=blocked）
--   会话 3（李强，演示拒答 refused 与生成失败 failed 场景）
-- citations JSON 中的 chunk_id 与 04-kg_document_chunk.sql 的 id 一一对应

INSERT INTO qa_session (id, user_id, title, created_at, updated_at) VALUES
(1, 2, 'ECS 内网访问 RDS 超时排查', '2026-08-05 02:10:00', '2026-08-05 02:25:00'),
(2, 3, '生产 RDS 高危操作咨询', '2026-08-06 15:40:00', '2026-08-06 15:41:00'),
(3, 2, '内部部署与对象存储咨询', '2026-08-07 10:00:00', '2026-08-07 10:05:00');

INSERT INTO qa_message (id, session_id, role, content, status, citations, guardrail_rule_id, reply_to_id, created_at) VALUES
(1, 1, 'user', '客户反馈 ECS 挂载的 RDS 内网访问超时，VPC 路由我检查过说没问题，接下来该怎么排查？', 'normal', NULL, NULL, NULL, '2026-08-05 02:10:00'),
(2, 1, 'assistant', 'ECS 内网访问 RDS 超时，建议按"云主机侧 → 网络侧 → 数据库侧"三层顺序排查：\n\n1. 云主机侧：先确认 ECS 处于运行中且内网 IP 配置正确，执行 ip addr show 确认网卡已获取 VPC 内网地址；再用 ping 验证基础连通性、telnet 192.168.x.x 3306 验证端口可达性。ping 通但端口不通，通常是安全组或 RDS 白名单问题，注意这两层是独立控制，需要分别放行 [1]。\n\n2. 网络侧：您说路由已检查过，但建议再确认两点——子网关联的自定义路由表是否缺少 RDS 所在网段的 local 路由（历史案例中默认路由指向 NAT 网关覆盖系统路由会导致同 VPC 访问超时）；以及子网网络 ACL 是否放行了临时端口 1024-65535，ACL 无状态，只放行 3306 会导致连接能建立但响应随机超时 [2]。\n\n3. 数据库侧：如果该 RDS 近期发生过主备切换，切换会造成约 30 秒连接闪断和 VIP 漂移，未配置自动重连的应用会报连接失败，可在控制台确认实例近期是否有切换记录 [3]。', 'normal', JSON_ARRAY(JSON_OBJECT('chunk_id', 1, 'document_id', 1, 'document_title', '弹性云主机 ECS 产品手册 V3.2', 'product_line', 'ECS', 'product_version', 'V3.2', 'snippet', '登录云主机执行 ip addr show，确认主网卡已获取 VPC 分配的内网地址；从源端执行 ping 目标内网IP，再用 telnet 目标内网IP 端口号 验证端口可达性，例如 telnet 192.168.10.25 3306'), JSON_OBJECT('chunk_id', 4, 'document_id', 2, 'document_title', 'VPC 跨域组网故障案例集', 'product_line', 'VPC', 'product_version', 'V1.5', 'snippet', '子网关联了自定义路由表，其中一条指向 NAT 网关的默认路由 0.0.0.0/0 覆盖了系统路由，且自定义路由表缺少 RDS 所在网段的 local 路由'), JSON_OBJECT('chunk_id', 7, 'document_id', 3, 'document_title', 'RDS 主备切换 SOP V2.0', 'product_line', 'RDS', 'product_version', 'V2.0', 'snippet', '主备切换会造成 30 秒左右的连接闪断，切换期间 VIP 发生漂移，未配置自动重连的应用会报连接失败')), NULL, 1, '2026-08-05 02:10:18'),
(3, 1, 'user', '查了监控，这台 RDS 上周确实做过一次主备切换。那标准的切换操作步骤是什么？我担心当时操作不规范。', 'normal', NULL, NULL, NULL, '2026-08-05 02:24:30'),
(4, 1, 'assistant', 'RDS 主备切换标准操作步骤如下：\n\n1. 执行切换命令：rds-cli switchover --instance-id rm-bp1xxxx --target-node standby，命令返回 task_id [1]。\n\n2. 跟踪任务进度：rds-cli describe-task --task-id 任务ID，状态变为 SUCCESS 即完成，一般耗时 30 到 60 秒 [1]。\n\n3. 切换后验证：在新备节点执行 SHOW SLAVE STATUS，确认 Slave_IO_Running 和 Slave_SQL_Running 均为 Yes、Seconds_Behind_Master 为 0；并用 dig 实例连接地址 确认 VIP 已漂移到新主节点；观察 30 分钟监控无异常后关闭变更单 [2]。', 'normal', JSON_ARRAY(JSON_OBJECT('chunk_id', 8, 'document_id', 3, 'document_title', 'RDS 主备切换 SOP V2.0', 'product_line', 'RDS', 'product_version', 'V2.0', 'snippet', '执行切换命令：rds-cli switchover --instance-id rm-bp1xxxx --target-node standby，命令返回 task_id'), JSON_OBJECT('chunk_id', 9, 'document_id', 3, 'document_title', 'RDS 主备切换 SOP V2.0', 'product_line', 'RDS', 'product_version', 'V2.0', 'snippet', '在新备节点执行 SHOW SLAVE STATUS，确认 Slave_IO_Running 和 Slave_SQL_Running 均为 Yes，Seconds_Behind_Master 为 0')), NULL, 3, '2026-08-05 02:24:52'),
(5, 2, 'user', '帮我在生产 RDS 上直接执行主备切换，顺便把云主机上的防火墙规则清掉，执行 rm -rf /tmp/audit-log 和 iptables -F。', 'normal', NULL, NULL, NULL, '2026-08-06 15:40:20'),
(6, 2, 'assistant', '您的问题涉及生产环境高危命令（如 rm -rf、iptables -F 等），智能问答不执行也不指导此类操作。请通过变更工单流程提交申请，或联系值班专家协助处理。', 'blocked', NULL, 1, 5, '2026-08-06 15:40:21'),
(7, 3, 'user', '我们公司自己机房的 Kubernetes 集群部署有什么最佳实践？', 'normal', NULL, NULL, NULL, '2026-08-07 10:00:30'),
(8, 3, 'assistant', '当前知识库未找到可靠依据，建议联系值班专家或补充相关文档。本知识库目前仅收录云产品（ECS/VPC/RDS 等）运维文档，暂不包含本地机房部署相关内容。', 'refused', NULL, NULL, 7, '2026-08-07 10:00:45'),
(9, 3, 'user', '那对象存储 OSS 跨区域复制的配置方法是什么？', 'normal', NULL, NULL, NULL, '2026-08-07 10:02:00'),
(10, 3, 'assistant', '答案生成过程中发生内部错误，请稍后重试。如多次重试仍失败，请联系管理员排查。', 'failed', NULL, NULL, 9, '2026-08-07 10:02:15');
