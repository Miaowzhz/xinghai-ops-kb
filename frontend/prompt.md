# 所有页面设计提示词
你是前端开发工程师。请基于 Vue 3 + Element Plus + Vite + JavaScript 实现「星海运维智能知识库」的智能问答页（全项目最核心的页面）。
请使用这三个skills完成页面开发：
- ui-ux-pro-max 
- make-interfaces-feel-better 
- frontend design

## 登录页

硬性技术要求：
- 使用 Vue 3 Composition API 和 `<script setup>`。
- 只使用 JavaScript，不要使用 TypeScript。
- 不要生成 `.ts` 文件，不要写 `lang="ts"`。
- UI 组件优先使用 Element Plus（2.14.x）。
- HTTP 请求使用 Axios（1.19.x）。
- 状态管理使用 Pinia（4.x），路由使用 Vue Router（5.x）。
- API 路径必须与下方接口约定一致，统一以 `/api` 为前缀。
- 建议文件路径（本任务只创建第一个文件，其余如已存在则复用、不存在则在代码中 import 并同步创建最小可用版本）：
  - `frontend/src/views/LoginView.vue`（本页面，核心交付物）
  - `frontend/src/stores/user.js`（Pinia user store：token + user，login/logout action，localStorage 持久化）
  - `frontend/src/utils/request.js`（axios 实例：baseURL '/api'；请求拦截器从 Pinia 取 token 加 `Authorization: Bearer <token>` 头；响应拦截器遇 401 清空登录态并跳 `/login`）
  - `frontend/src/api/auth.js`（导出 `login(data)`、`getProfile()` 两个函数，内部调用 request.js）
  - `frontend/src/router/index.js`（如已存在则只补充 `/login` 路由和全局守卫说明，不要覆盖已有路由）

业务目标：
- 页面服务于「系统登录与角色分流」，是系统唯一入口。
- 用户角色：运维工程师 engineer、知识管理员 admin，只有这两类。
- 用户在本页面要完成：输入账号密码登录 → 登录成功后按角色跳转（engineer → `/qa` 智能问答页，admin → `/documents` 知识库文档管理页）。
- 本项目不提供注册功能，不要出现注册链接或注册按钮。

页面布局：
- 整体：全屏居中布局，深色或渐变背景均可（风格偏"运维技术平台"，简洁克制），页面上方显示系统名「星海运维智能知识库」和一句副标题（如"运维故障排查与知识问答 Copilot"）。
- 内容区域：一张居中的 ElCard 登录卡片，宽度约 400px，内含标题"账号登录"、用户名输入框、密码输入框、登录按钮。
- 辅助区域：卡片底部用小号灰字展示演示账号提示“演示账号：engineer01 / admin01（密码 123456）”，并注明这两个账号仅 `USE_MOCK` 前端 mock 模式可用；对接真实后端后改用数据库种子账号 admin（知识管理员）/ liqiang / wangfang（运维工程师），初始密码 XhOps@2026。
- 不要顶部导航、侧边栏——登录页是独立全屏页。

Element Plus 组件要求：
- 使用 ElCard、ElForm、ElFormItem、ElInput、ElButton，提示消息用 ElMessage。
- 密码框使用 `<el-input type="password" show-password>`，支持回车键提交（`@keyup.enter`）。
- 登录按钮 `type="primary"`，宽度 100%，提交期间 `:loading="true"` 并禁用，防止重复点击。
- 表单校验规则（ElForm `:rules`，提交前 `formRef.validate()`）：
  - username：必填，提示"请输入用户名"；长度 2~64，超出提示"用户名长度需在 2~64 个字符之间"。
  - password：必填，提示"请输入密码"；长度 6~64，超出提示"密码长度需在 6~64 个字符之间"。
  - 校验不通过时不发请求。

接口约定：
- `POST /api/auth/login`：登录，返回 JWT 和用户信息。
  - 请求参数（body，JSON）：`username`（字符串）、`password`（字符串）。
  - 响应字段：`access_token`（JWT 字符串）、`token_type`（固定 "bearer"）、`user`（对象，含 `id`、`username`、`display_name`、`role`，role 取值为 "engineer" 或 "admin"）。
  - 成功后行为：
    1. 调用 user store 的 login action，把 `access_token` 和 `user` 存入 Pinia，并同步写 localStorage（建议 key：`xinghai_token`、`xinghai_user`），store 初始化时从 localStorage 恢复，保证刷新不掉登录。
    2. ElMessage 成功提示"登录成功，欢迎回来 {display_name}"。
    3. 按 `user.role` 跳转：`'engineer'` → `router.push('/qa')`；`'admin'` → `router.push('/documents')`；未知角色默认跳 `/qa`。
  - 失败后行为：HTTP 401 时 ElMessage 错误提示"用户名或密码错误"（后端不区分账号不存在还是密码错，前端也不要区分）；网络错误提示"网络异常，请稍后重试"；表单保留已填内容，按钮恢复可点击。
- `GET /api/auth/profile`：获取当前登录用户信息（本页面不直接调用，由 router/index.js 的全局前置守卫在"有 token 但 Pinia 中无用户信息"时调用，刷新用户信息）。
  - 请求参数：无（token 走请求头 `Authorization: Bearer <token>`，由 axios 拦截器自动添加）。
  - 响应字段：`id`、`username`、`display_name`、`role`。
  - 成功后行为：把用户信息写回 Pinia store。
  - 失败后行为：401 时清空 token 与用户信息（localStorage 同步清除），重定向到 `/login`。
- 路由守卫要求（写在 router/index.js 中，用注释说明）：
  - 全局前置守卫：目标路由不是 `/login` 且 Pinia 中无 token 时，重定向 `/login`。
  - 目标路由是 `/login` 且已有 token 时，直接按角色跳到对应首页，不让已登录用户再看登录页。

状态处理：
- loading：登录按钮 loading + 禁用；页面级不需要骨架屏。
- empty：本页面无列表数据，不涉及。
- error：账号密码错误（401）和网络异常分别给出上文指定的中文提示；其他 HTTP 错误统一提示"登录失败，请稍后重试"。
- permission：本页面不涉及页面级权限；角色分流只决定登录后跳去哪。真正的接口级权限由后端控制（engineer 调 admin 接口会得 403），前端不在登录页做额外判断。

Mock 数据：
- 后端未完成时，在 `frontend/src/api/auth.js` 顶部提供可整体替换的 mock 实现（用一个 `USE_MOCK` 布尔开关切换，默认 true），mock 字段必须与上方接口响应完全一致。
- mock 至少包含两个账号（密码任意非空即可通过，或固定为 `123456` 并在注释中写明）：
  - 正常-engineer：`{ username: 'engineer01', password: '123456' }` → 返回 `access_token: 'mock-token-engineer'`、`token_type: 'bearer'`、`user: { id: 1, username: 'engineer01', display_name: '张工', role: 'engineer' }`。
  - 正常-admin：`{ username: 'admin01', password: '123456' }` → 返回 `access_token: 'mock-token-admin'`、`token_type: 'bearer'`、`user: { id: 2, username: 'admin01', display_name: '李管理', role: 'admin' }`。
  - 异常：其余任意账号密码返回 401 等效结果（mock 中 reject 一个带 `response.status = 401` 的错误对象，模拟"用户名或密码错误"）。
- mock 的 `getProfile()` 根据当前存储的 token 返回对应用户信息；token 不存在时 reject 401。
- mock 登录加 500ms 延时模拟网络，便于观察 loading 态。

响应式要求：
- 桌面端：登录卡片水平垂直居中，宽度约 400px。
- 窄屏（< 768px）：卡片宽度改为 90%，左右留白自适应，系统标题字号适当缩小，不出现横向滚动条。

完成后自查：
- 页面能在 Vite 开发环境运行（`npm run dev`，前端端口 5173，vite 代理把 `/api` 转发到后端 8000）。
- 没有 TypeScript：无 `.ts` 文件、无 `lang="ts"`、无类型标注。
- 主要交互可点击并有反馈：空表单点登录出现校验提示；错误账号提示"用户名或密码错误"；engineer01 登录进 `/qa`、admin01 登录进 `/documents`；刷新页面登录态不丢。
- API 方法、路径、参数与上方约定一致（`/api/auth/login`、`/api/auth/profile`）。
- loading、error、路由守卫（未登录拦截、已登录跳过登录页）都有可见处理。

## 智能问答页

硬性技术要求：
- 使用 Vue 3 Composition API 和 `<script setup>`。
- 只使用 JavaScript，不要使用 TypeScript。
- 不要生成 `.ts` 文件，不要写 `lang="ts"`。
- UI 组件优先使用 Element Plus（2.14.x）。
- 普通 HTTP 请求使用 Axios（1.19.x）；SSE 流式请求必须按下文指定方式用 fetch 实现（原因见下）。
- 状态管理使用 Pinia（4.x，用户 token 在 user store 中），路由使用 Vue Router（5.x）。
- API 路径必须与下方接口约定一致，统一以 `/api` 为前缀；除登录接口外都需请求头 `Authorization: Bearer <token>`。
- 建议文件路径（本任务核心交付第一个文件，其余如已存在则复用，不存在则创建最小可用版本）：
  - `frontend/src/views/QaView.vue`（本页面，核心交付物）
  - `frontend/src/api/qa.js`（封装会话与消息接口；SSE 的 fetch 流式读取逻辑也放这里，导出成函数供页面调用）
  - `frontend/src/api/feedback.js`（封装提交反馈接口）
  - `frontend/src/utils/request.js`（已存在的 axios 封装：baseURL '/api'，请求拦截器自动带 `Authorization: Bearer <token>`，401 统一清空登录态跳 `/login`；如不存在请按此约定创建）
  - `frontend/src/stores/user.js`（已存在的 Pinia user store，含 token 与 user；如不存在请按此约定创建，含 localStorage 持久化）

业务目标：
- 页面服务于「运维问答流程」：运维工程师用自然语言描述故障现象，系统基于 RAG 知识库流式返回带引用来源的答案。
- 用户角色：运维工程师 engineer（主要使用者）、知识管理员 admin 也可使用问答功能。
- 用户在本页面要完成：
  1. 新建会话、切换历史会话、查看会话内全部历史消息。
  2. 输入问题发送，可选产品线筛选（作为检索 metadata 过滤条件）。
  3. 观看答案逐字流式输出，查看答案下方的引用来源卡片。
  4. 对答案点赞/点踩；点踩必须在弹窗中填写原因后提交。
  5. 在同一会话中多轮追问（后端会自动携带会话历史，前端只需传 session_id）。

页面布局：
- 顶部区域：系统名「星海运维智能知识库」；右侧显示当前用户 display_name、角色 ElTag（engineer/admin）、退出登录按钮（点击清空登录态并跳 `/login`）。
- 左侧区域（宽约 260px）：顶部一个整行宽的「+ 新建会话」主按钮；下方是会话列表，每项显示会话标题（超长省略号）和更新时间，当前选中会话高亮；列表可滚动。
- 右侧内容区域：
  - 对话消息区：占满剩余高度、可滚动。用户消息气泡靠右（深色背景白字）；assistant 消息气泡靠左（浅色卡片）。assistant 气泡内从上到下依次是：答案正文 → 引用来源卡片区 → 反馈按钮行（👍/👎 + 消息时间）。
  - 底部输入区：产品线 ElSelect（选项：全部、ECS、VPC、RDS，默认"全部"，可清空即不筛选）+ 多行输入框 + 发送按钮，三者一行排列。
- 辅助区域：点踩原因 ElDialog（标题"告诉我们哪里不对"，一个多行输入框，确定/取消按钮）。

Element Plus 组件要求：
- 使用 ElButton、ElSelect、ElOption、ElInput、ElDialog、ElForm、ElFormItem、ElTag、ElAlert、ElEmpty、ElMessage、ElScrollbar（或原生滚动容器）。
- 表单校验规则：
  - 提问输入框：必填（去除首尾空格后为空则不允许发送，发送按钮禁用），最大长度 2000 字符，超出时输入框 `maxlength` 直接限制。
  - 点踩原因（ElForm `:rules`）：必填，提示"请填写点踩原因，方便管理员定位问题"；长度 1~500，提交前 `formRef.validate()`，不通过不发请求。
- 会话列表：不属于表格，用 v-for 列表实现；空会话列表时在对话区显示 ElEmpty，描述"暂无会话，输入问题开始你的第一次提问"。
- 反馈按钮：status 为 normal 和 status 为 refused 的 assistant 消息显示 👍/👎 两个按钮（refused 消息点踩用于沉淀知识缺失，会生成“知识缺失”方向的审核任务）；blocked/failed 消息不显示反馈按钮。已点过的按钮高亮（type="primary" 或加激活样式），同一消息重复点击另一种态度允许改投（后端会覆盖旧反馈）。

接口约定（共 5 个）：
- `GET /api/qa/sessions`：查询当前用户的会话列表。
  - 请求参数：无（按 JWT 用户过滤，token 走请求头）。
  - 响应字段：会话数组，每项含 `id`、`title`、`created_at`、`updated_at`，按 updated_at 倒序。
  - 成功后行为：渲染左侧会话列表；若有会话，默认选中第一个并加载其消息。
  - 失败后行为：ElMessage 提示"会话列表加载失败"，列表区显示错误占位和"重试"按钮。
- `POST /api/qa/sessions`：新建会话。
  - 请求参数（body，JSON）：`title`（可选，不传后端默认"新会话"）。
  - 响应字段：`id`、`title`、`created_at`、`updated_at`。
  - 成功后行为：把新会话插入列表顶部并选中，清空右侧对话区，输入框聚焦。
  - 失败后行为：ElMessage 提示"创建会话失败，请重试"。
- `GET /api/qa/sessions/{session_id}/messages`：查询会话内全部消息。
  - 请求参数：path 参数 `session_id`。
  - 响应字段：消息数组，每项含 `id`、`session_id`、`role`（"user"/"assistant"）、`content`、`citations`（引用数组或 null，元素含 `chunk_id`、`document_id`、`document_title`、`product_line`、`product_version`、`snippet`）、`status`（"normal"/"blocked"/"refused"/"failed"）、`created_at`。
  - 成功后行为：按顺序渲染消息；assistant 消息若 citations 非空则渲染引用卡片；status=blocked 的用警示样式渲染。
  - 失败后行为：ElMessage 提示"消息加载失败"，对话区显示错误占位和"重试"按钮。
- `POST /api/qa/chat`：发送问题，SSE 流式返回答案。**这是本页面最关键的接口，必须严格按下面的方式实现**。
  - 请求参数（body，JSON）：`session_id`（可选，新建会话后的首次提问可以不传，后端自动建会话；若当前已选中会话则必传）、`question`（必填，1~2000 字符）、`product_line`（可选，产品线筛选，如 "ECS"；不筛选则不传或传 null）、`product_version`（可选，本页面不暴露版本筛选，恒不传）。
  - 响应不是普通 JSON，而是 `text/event-stream` 的 SSE 流。每个事件的格式是 `data: {JSON}\n\n`，JSON 内含 `type` 字段区分事件类型：
    - `{"type":"token","content":"答案片段"}`：答案的一小段，追加到当前 assistant 气泡。
    - `{"type":"citations","items":[...]}`：引用列表（字段同上文消息的 citations），渲染引用卡片。
    - `{"type":"status","status":"blocked"}`：消息最终状态非正常（blocked/refused/failed）时给出，切换气泡样式。
    - `{"type":"done","session_id":123}`：本次回答结束，携带 session_id（首次提问后端自动建会话时，用它更新当前会话 id 并刷新会话列表）。
    - `{"type":"error","message":"系统繁忙，请稍后重试。"}`：服务端异常，展示错误提示并结束流式状态。
  - **SSE 读取实现要求（务必照做）**：
    - 不要用 EventSource——浏览器原生 EventSource 只支持 GET，而本接口是 POST，无法用。
    - 用 `fetch('/api/qa/chat', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(payload) })`。
    - 从 `response.body.getReader()` 拿到 reader，配合 `new TextDecoder('utf-8')` 循环 `await reader.read()`，把每个 chunk 解码后追加到一个字符串缓冲区。
    - 按 `\n\n` 切分缓冲区得到完整事件块；每个事件块取以 `data: ` 开头的行，去掉前缀后 `JSON.parse`；解析不完整（JSON 报错）说明事件被拆在两个网络包里，要留在缓冲区等待下一次拼接，不能丢弃。
    - 按 `type` 分发：token → 追加文本；citations → 存引用列表；status → 记录消息状态；done → 收尾（恢复发送按钮、用返回的 session_id 更新当前会话、刷新会话列表）；error → 展示错误并收尾。
    - 用一个标志位（如 `streaming`）表示"回答进行中"：期间禁用发送按钮和新会话/切换会话点击，防止并发提问打乱消息顺序。
    - fetch 本身抛异常（网络断开）时，等同于收到 error 事件处理：提示"网络异常，回答中断，请重试"，恢复界面。
  - 成功后行为：用户气泡立即上屏；assistant 气泡随 token 事件逐字增长（对话区自动滚动到底部）；citations 到达后渲染引用卡片；done 后恢复输入。
  - 失败后行为：收到 error 事件或 HTTP 非 200 时，气泡内显示错误文案（ElAlert type="error" 样式），发送按钮恢复。
- `POST /api/feedback`：对某条答案点赞/点踩。仅适用于 status 为 normal 或 refused 的 assistant 消息；blocked/failed 消息不开放反馈。
  - 请求参数（body，JSON）：`message_id`（assistant 消息 id，必填）、`feedback_type`（"like" 或 "dislike"）、`reason`（点踩必填，1~500 字符；点赞传 null）。
  - 响应字段：`id`、`message_id`、`feedback_type`、`reason`、`status`。
  - 成功后行为：点赞 → ElMessage"感谢反馈"，👍 按钮高亮；点踩 → 先弹 ElDialog 收集原因，提交成功后 ElMessage"已记录，将转交知识管理员审核"，👎 按钮高亮。
  - 失败后行为：ElMessage 提示"反馈提交失败，请重试"，按钮状态不变。
  - 注意：同一消息重复点另一种态度是允许的业务行为（后端覆盖旧反馈），前端直接发请求即可。

状态处理：
- loading：会话列表/消息列表加载时显示加载占位（可用 v-loading 或骨架文本）；发送后 assistant 气泡先显示打字动画（三个跳动的点或闪烁光标），第一个 token 到达后消失。
- empty：无会话时对话区 ElEmpty 引导语"暂无会话，输入问题开始你的第一次提问"；会话内无消息时显示提示"开始提问吧，例如：ECS 无法连接 RDS 怎么排查"。
- error：接口失败都有中文 ElMessage 提示 + 可重试入口；SSE error 事件按上文约定展示。
- permission：本页面对 engineer 和 admin 都开放，无页面级权限拦截；未登录访问由全局路由守卫挡回 `/login`（本页面不用重复实现）。

Mock 数据：
- 后端未完成时，在 `frontend/src/api/qa.js` 和 `frontend/src/api/feedback.js` 顶部提供可整体替换的 mock 实现（用 `USE_MOCK` 布尔开关切换，默认 true），mock 字段必须与上方接口响应完全一致。
- mock 数据要覆盖：
  - 正常：2~3 个会话（如"ECS挂载RDS内网超时""VPC跨域组网案例"）；其中一个会话含 2~3 对历史消息，assistant 消息带 2 条 citations（如 `{ chunk_id: 101, document_id: 1, document_title: 'RDS 产品手册', product_line: 'RDS', product_version: 'V3.2', snippet: '白名单配置：登录 RDS 控制台，在数据安全性页签添加 ECS 内网 IP...' }`）。
  - SSE mock：mock 的 chat 函数要模拟流式效果——把一段预置答案按每 30~50ms 一小段（每段 3~10 个字符）通过回调逐个推给页面，推完后依次回调 citations、done（带一个 mock session_id）。mock 同样走"token/citations/status/done/error"事件类型，让页面代码在 mock 和真实后端之间零改动切换。
  - 空数据：一个空会话列表的 mock 分支（可用某个开关或特殊注释触发），验证 ElEmpty 展示。
  - 异常：mock 一个 blocked 分支（问题中含"删除生产"等关键词时返回 status=blocked 事件和拦截话术"该问题涉及生产环境高危操作，建议提交工单或联系值班专家处理。"）和一个 error 分支（模拟 error 事件"系统繁忙，请稍后重试。"）。
- mock 的反馈接口：返回 `{ id: 1, message_id, feedback_type, reason, status: 'pending' }`，加 300ms 延时。

响应式要求：
- 桌面端：左侧会话栏固定约 260px，右侧对话区自适应；消息气泡最大宽度约 75%。
- 窄屏（< 768px）：左侧会话栏可折叠（提供折叠按钮，折叠后只剩图标宽度的条），对话区占满剩余宽度；输入区的产品线筛选和发送按钮允许换行。

完成后自查：
- 页面能在 Vite 开发环境运行（`npm run dev`，前端端口 5173，vite 代理把 `/api` 转发到后端 8000）。
- 没有 TypeScript：无 `.ts` 文件、无 `lang="ts"`、无类型标注。
- 主要交互可点击并有反馈：新建会话、切换会话、发送问题、点赞、点踩（弹窗填原因）、退出登录全部可用。
- SSE 是逐字渲染的（能明显看到答案一个字一个字出现），不是一次性弹出；回答进行中发送按钮禁用。
- blocked 消息是警示样式；引用卡片显示文档名、产品版本、原文片段。
- API 方法、路径、参数与上方约定一致（`/api/qa/sessions`、`/api/qa/sessions/{id}/messages`、`/api/qa/chat`、`/api/feedback`）。
- loading、empty、error 状态都有可见处理；mock 开关关闭后页面直接对接真实后端无需改页面代码。

## 知识库文档管理页

硬性技术要求：
- 使用 Vue 3 Composition API 和 `<script setup>`。
- 只使用 JavaScript，不要使用 TypeScript。
- 不要生成 `.ts` 文件，不要写 `lang="ts"`。
- UI 组件优先使用 Element Plus（2.14.x）。
- HTTP 请求使用 Axios（1.19.x）；文件上传用 axios 的 `FormData`（multipart）。
- 状态管理使用 Pinia（4.x，用户 token 和角色在 user store 中），路由使用 Vue Router（5.x）。
- API 路径必须与下方接口约定一致，统一以 `/api` 为前缀；所有接口都需请求头 `Authorization: Bearer <token>`。
- 建议文件路径（本任务核心交付第一个文件，其余如已存在则复用，不存在则创建最小可用版本）：
  - `frontend/src/views/DocumentManageView.vue`（本页面，核心交付物）
  - `frontend/src/api/document.js`（封装本页 4 个接口调用）
  - `frontend/src/utils/request.js`（已存在的 axios 封装：baseURL '/api'，请求拦截器自动带 `Authorization: Bearer <token>`，401 清空登录态跳 `/login`；如不存在请按此约定创建）
  - `frontend/src/stores/user.js`（已存在的 Pinia user store，含 token、user；如不存在请按此约定创建，含 localStorage 持久化）

业务目标：
- 页面服务于「知识入库流程」的文档生命周期管理：知识管理员在这里监控入库状态、查看失败原因、对文档重新上传新版（增量替换 chunk）、删除作废文档。
- 用户角色：仅知识管理员 admin。运维工程师 engineer 无权使用本页。
- 用户在本页面要完成：
  1. 按类型/产品线/状态筛选并分页浏览文档列表。
  2. 查看文档详情（抽屉展示，含失败原因等完整字段）。
  3. 对失败或旧版文档执行"重新上传新版"。
  4. 删除文档（二次确认；入库中的文档禁止删除）。

页面布局：
- 顶部区域：系统名「星海运维智能知识库」；右侧当前用户 display_name、角色 ElTag（admin）、退出登录按钮（清空登录态跳 `/login`）。
- 标题区：页面标题"知识库文档管理"（本页不放"上传文档"按钮，新文档上传在另一个页面 P04 完成，不要在本页实现上传功能）。
- 查询区域：一行 inline 表单——文档类型 ElSelect（全部/产品手册/故障案例/运维 SOP/API 文档）、产品线 ElSelect（全部/ECS/VPC/RDS/OSS）、状态 ElSelect（全部/待入库/入库中/成功/失败）、查询按钮、重置按钮。三个筛选默认都是"全部"。
- 内容区域：ElTable 文档表格 + 底部 ElPagination。
- 辅助区域：ElDrawer（文档详情）、ElDialog（重新上传新版）、ElMessageBox（删除确认）。

Element Plus 组件要求：
- 使用 ElTable、ElTableColumn、ElTag、ElTooltip、ElButton、ElForm、ElFormItem、ElSelect、ElOption、ElPagination、ElDrawer、ElDescriptions、ElDescriptionsItem、ElDialog、ElInput、ElUpload、ElEmpty、ElMessage、ElMessageBox。
- 表格列（共 9 列）：
  1. 标题 `title`：超长省略号 + ElTooltip 显示完整标题。
  2. 类型 `doc_type`：用映射表转中文展示——manual→产品手册、case→故障案例、sop→运维 SOP、api→API 文档。
  3. 产品线 `product_line`。
  4. 版本 `product_version`：同时展示入库次数，格式如 `V3.2（第2次入库）`（用 `version` 字段）。
  5. chunk 数 `chunk_count`。
  6. 状态 `status`：ElTag 展示——pending→"待入库"(info)、parsing→"入库中"(warning)、success→"成功"(success)、failed→"失败"(danger)；failed 状态外套 ElTooltip，内容为 `fail_reason`（失败原因）。
  7. 上传人 `created_by_name`：上传人显示名（见接口约定备注）。
  8. 上传时间 `created_at`：格式化为 `YYYY-MM-DD HH:mm`。
  9. 操作列：详情、重新上传新版、删除三个 link 型按钮；`status === 'parsing'` 时"重新上传新版"和"删除"两个按钮禁用，删除按钮悬浮提示"入库中，暂不可删除"。
- 分页规则：ElPagination 用 `layout="total, sizes, prev, pager, next"`；请求参数 `page`（从 1 开始）、`page_size`（可选 10/20/50，默认 10）；翻页或改页大小时保持当前筛选条件；点"查询"时 page 重置为 1。
- 表单校验规则（重新上传新版弹窗的 ElForm `:rules`，提交前 `formRef.validate()`）：
  - 新版本号 `product_version`：必填，提示"请输入新版本号"；长度 1~32。
  - 文件：必选（ElUpload 用 `:auto-upload="false"` 手动模式 + `limit=1`），校验提示"请选择新版文档文件"；限制扩展名为 .pdf/.docx/.md/.txt，选择其他格式时 ElMessage 提示"仅支持 PDF / DOCX / MD / TXT 格式"并清空选择。

接口约定（共 4 个）：
- `GET /api/documents`：分页查询文档列表。
  - 请求参数（query）：`page`（默认 1）、`page_size`（默认 10）、`doc_type`（可选，manual/case/sop/api）、`product_line`（可选）、`status`（可选，pending/parsing/success/failed）。筛选项为"全部"时该参数不传。
  - 响应字段：`total`（总条数）、`items`（数组，每项含 `id`、`title`、`doc_type`、`product_line`、`product_version`、`status`、`fail_reason`、`chunk_count`、`version`、`created_by_name`、`created_at`）。
  - 备注：`fail_reason` 和 `created_by_name`（上传人显示名）是 `kg_document` 表已有字段（`fail_reason`、`created_by` 关联 `sys_user.display_name`）的透出；后端模块文档 M02 的列表响应未显式列出这两个字段，实现时需在后端列表 schema 中补充，字段含义以本约定为准。
  - 成功后行为：渲染表格与分页器 total。
  - 失败后行为：ElMessage 提示"文档列表加载失败"，表格区显示错误占位和"重试"按钮。
- `GET /api/documents/{doc_id}`：文档详情。
  - 请求参数：path 参数 `doc_id`。
  - 响应字段：文档全部字段——`id`、`title`、`doc_type`、`product_line`、`product_version`、`file_type`、`status`、`fail_reason`、`chunk_count`、`version`、`created_by_name`、`created_at`、`updated_at`。
  - 成功后行为：ElDrawer 从右侧滑出，用 ElDescriptions 展示全部字段；`fail_reason` 为 null 时显示"-"；时间格式化为 `YYYY-MM-DD HH:mm:ss`。
  - 失败后行为：ElMessage 提示"详情加载失败"，抽屉不打开。
- `POST /api/documents/{doc_id}/reingest`：重新上传新版文档（multipart）。
  - 请求参数：path 参数 `doc_id`；body 为 FormData，含 `file`（文件）、`product_version`（新版本号字符串）。
  - 响应字段：`doc_id`、`status`（"pending"）、`version`（递增后的入库次数）。
  - 成功后行为：关闭弹窗，ElMessage 提示"已提交，正在重新入库"；刷新列表，对应行 status 变为 pending（随后轮询看到 parsing→success/failed）。
  - 失败后行为：HTTP 409（文档正在入库中）提示"文档正在入库中，请稍后再操作"；400（格式不支持）提示"仅支持 PDF / DOCX / MD / TXT 格式"；其他错误提示"提交失败，请重试"。弹窗保持打开，表单内容不清空。
- `DELETE /api/documents/{doc_id}`：删除文档。
  - 请求参数：path 参数 `doc_id`。
  - 响应字段：`doc_id`、`deleted`（true）。
  - 前置行为：必须先弹 `ElMessageBox.confirm`，文案"删除后不可恢复，将同时删除该文档在知识库中的全部 {chunk_count} 个分片，确认删除《{title}》吗？"，确认按钮 type="danger"；用户取消则什么都不做。
  - 成功后行为：ElMessage 提示"删除成功"，刷新列表（若当前页删空了就回退到前一页）。
  - 失败后行为：HTTP 409 提示"文档正在入库中，请稍后再删除"；404 提示"文档不存在或已被删除"并刷新列表；403 提示"仅知识管理员可执行此操作"。

状态处理：
- loading：表格加载时 `v-loading`；详情抽屉打开前按钮 loading；reingest 提交中弹窗确定按钮 loading；删除请求中操作按钮 loading。
- empty：表格无数据时用 ElTable 的 empty 插槽放 ElEmpty，描述"暂无文档，请先到文档上传页上传资料"；筛选无结果时描述改为"没有符合条件的文档，试试调整筛选条件"。
- error：各接口失败按上文约定给出中文提示；列表加载失败显示错误占位 + 重试按钮。
- permission：
  - 页面级：进入本路由前检查 Pinia 中 `user.role === 'admin'`，不是 admin 则 ElMessage 提示"仅知识管理员可访问"并跳回 `/qa`（把这段守卫逻辑写在 router/index.js 的路由 meta + 全局守卫里，用注释说明；如路由文件尚不存在，至少在本页面 onMounted 中做检查并跳回）。
  - 接口级：任何接口返回 403 都提示"仅知识管理员可执行此操作"。
- 轮询：列表中存在 status 为 pending 或 parsing 的文档时，每 3~5 秒自动重新调用列表接口刷新状态；没有进行中文档时停止轮询；组件卸载（onUnmounted）时清除定时器，避免内存泄漏。

Mock 数据：
- 后端未完成时，在 `frontend/src/api/document.js` 顶部提供可整体替换的 mock 实现（用 `USE_MOCK` 布尔开关切换，默认 true），mock 字段必须与上方接口响应完全一致。
- mock 数据要覆盖：
  - 正常：12 条以上文档（验证分页），覆盖四种 doc_type（manual/case/sop/api）、多个产品线（ECS/VPC/RDS/OSS）、四种状态（pending/parsing/success/failed）。failed 的文档带 `fail_reason`，例如"未解析到文本内容，请确认不是纯图片扫描件"。每条带 `created_by_name: '李管理'`、`version`、`chunk_count`。
  - 状态流转模拟：mock 中对 pending/parsing 文档，每次调用列表接口时按"pending→parsing→success"推进状态（可在 mock 内用计数器实现），让前端轮询效果可见。
  - 空数据：mock 一个分支（如筛选 status=failed 且组合某产品线时返回 `total: 0, items: []`），验证空态。
  - 异常：mock 删除 parsing 文档返回 409 等效错误；mock reingest 对 parsing 文档返回 409 等效错误（错误对象带 `response.status` 和 `response.data.detail`）。
- mock 的 reingest 成功后把该文档 version +1、status 置 pending、chunk_count 置 0；mock 的删除把文档从 mock 数组移除。

响应式要求：
- 桌面端：筛选区一行排开；表格全宽，操作列固定在右侧（`fixed="right"`）。
- 窄屏（< 768px）：筛选区允许换行（每个筛选项占半行或整行）；表格开启横向滚动（ElTable 默认行为即可，不要强行压缩列宽导致文字重叠）；详情抽屉宽度改为 90%。

完成后自查：
- 页面能在 Vite 开发环境运行（`npm run dev`，前端端口 5173，vite 代理把 `/api` 转发到后端 8000）。
- 没有 TypeScript：无 `.ts` 文件、无 `lang="ts"`、无类型标注。
- 主要交互可点击并有反馈：筛选、重置、翻页、详情抽屉、重新上传新版（校验 + 提交）、删除（二次确认）全部可用。
- parsing 状态文档的"重新上传新版"和"删除"按钮处于禁用态；failed 文档悬浮状态标签可见失败原因。
- pending/parsing 文档状态能被轮询自动推进（mock 模式下可见状态变化）。
- API 方法、路径、参数与上方约定一致（`/api/documents`、`/api/documents/{id}`、`/api/documents/{id}/reingest`、DELETE `/api/documents/{id}`）。
- loading、empty、error、permission（非 admin 访问被挡）状态都有可见处理；mock 开关关闭后页面直接对接真实后端无需改页面代码。

## 文档上传与入库进度页

硬性技术要求：
- 使用 Vue 3（版本基线 3.5.41）Composition API 和 `<script setup>`。
- 只使用 JavaScript，不要使用 TypeScript。不要生成 `.ts` 文件，不要写 `lang="ts"`，不要写 TS 类型定义。
- UI 组件使用 Element Plus（版本基线 2.14.4）。
- HTTP 请求使用 Axios（版本基线 1.19.0），统一走封装好的实例 `frontend/src/utils/request.js`（baseURL 为 `/api`，自动带 `Authorization: Bearer <token>` 头；该文件将在 Stage 7 创建，本页面先按"它已存在"来 import）。
- API 路径必须与下方接口约定完全一致，不得自创路径。
- 建议文件路径（均将在 Stage 7 创建）：
  - 页面：`frontend/src/views/DocumentUploadView.vue`
  - 接口封装：`frontend/src/api/document.js`（导出 `uploadDocument(formData)`、`getDocumentList(params)`、`getDocumentDetail(docId)` 三个函数）
  - 路由登记：`frontend/src/router/index.js` 中加 `{ path: '/documents/upload', component: DocumentUploadView, meta: { role: 'admin' } }`

业务目标：
- 页面服务于"知识入库流程"：知识管理员把 PDF/DOCX/MD/TXT 运维文档上传进知识库，后台流水线异步完成解析、切块、向量化、建索引，本页面负责"上传 + 盯进度"。
- 用户角色：仅知识管理员（admin）。运维工程师（engineer）无权访问。
- 用户在本页面要完成：
  1. 选择本地文档文件并填写元信息（文档类型、产品线、产品版本），提交上传；
  2. 在入库进度列表中实时看到文档状态从 pending → parsing → success/failed 的流转；
  3. 文档失败时能看到具体失败原因；
  4. 列表全部到达终态后自动停止轮询。

页面布局：
- 顶部区域：页面标题"文档上传与入库进度"，右上角显示当前登录管理员姓名（从 `frontend/src/stores/user.js` 的 Pinia store 读取）。
- 上半区（ElCard"上传新文档"）：
  - ElUpload 文件选择区：`auto-upload=false`，`limit=1`，`drag` 拖拽模式，提示文案"点击选择或拖拽文件到此处，支持 PDF / DOCX / MD / TXT"；选中后显示文件名；选择不支持的扩展名时 ElMessage.warning 提示并清空选择。
  - 表单项：文档标题（ElInput，默认用所选文件名去掉扩展名自动填充、可修改）、文档类型（ElSelect）、产品线（ElInput，placeholder 提示"例如 ECS / VPC / RDS"）、产品版本（ElInput，placeholder 提示"例如 V3.2"）。
  - 右下角"开始上传"按钮（type=primary），提交期间 loading 且禁用。
- 下半区（ElCard"入库进度"）：
  - 卡片标题右侧放一个小字提示"每 3 秒自动刷新，全部入库完成后停止"（仅在轮询中显示）。
  - ElTable 展示文档列表。
- 辅助区域：无弹窗；failed 行的失败原因直接在表格行下方展开的 ElAlert（type=error）中展示。

Element Plus 组件要求：
- 表单校验规则（ElForm rules）：
  - file：必填，提交前校验"必须已选择文件"，且扩展名只能是 pdf / docx / md / txt（小写比较）；
  - title：必填，1~255 字符；
  - doc_type：必选，四个选项——`manual` 产品手册、`case` 故障案例、`sop` 运维 SOP、`api` API 文档（value 用英文枚举值，label 用中文）；
  - product_line：必填，1~64 字符；
  - product_version：必填，1~32 字符。
- 表格列（ElTable）：
  - title 文档标题；
  - doc_type 类型（用映射把 manual/case/sop/api 显示为中文）；
  - product_line 产品线；
  - product_version 版本；
  - status 状态：自定义列，`pending` 显示灰色 ElTag"待入库"，`parsing` 显示蓝色 ElTag"入库中"并附带一条 ElProgress（`percentage=50`、`:indeterminate="true"` 风格的动画即可，仅作"进行中"视觉提示，不需要真实百分比），`success` 显示绿色 ElTag"成功"，`failed` 显示红色 ElTag"失败"；
  - chunk_count chunk 数（parsing/pending/failed 显示 "-"）；
  - created_at 上传时间（格式化为 YYYY-MM-DD HH:mm）。
- 失败行展开：当某行 status 为 failed 时，额外调用 `GET /api/documents/{id}` 取 `fail_reason`，在该行下方用 ElAlert（type=error）展示；fail_reason 为空时显示"入库失败，请重试"。
- 分页：本页是"最近上传进度"场景，固定请求 `page=1&page_size=20`，不做分页器（说明文案注明"显示最近 20 篇文档"）；响应字段为 `{ total, items }`。

接口约定（所有接口都需要 `Authorization: Bearer <token>`，且仅 admin 可调用）：
- `POST /api/documents/upload`：上传文档并触发异步入库流水线。
  - 请求参数：multipart/form-data，字段 `file`（文件）、`title`、`doc_type`、`product_line`、`product_version`，五个全部必填。
  - 响应字段：`{ doc_id, status }`，status 恒为 `pending`。
  - 成功后行为：ElMessage.success("上传成功，已开始入库")；清空上传表单和已选文件；立即刷新一次列表；如果轮询未启动则启动轮询。
  - 失败后行为：HTTP 400（格式不支持）或 409（同 title + product_line 已存在）时，用 ElMessage.error 展示后端返回的 detail 文案（如"已存在同名文档，请使用重新上传新版"），表单内容保留不清空；其他错误提示"上传失败，请稍后重试"。
- `GET /api/documents`：分页查询文档列表（本页用作进度轮询）。
  - 请求参数（query）：`page`、`page_size`；可选过滤 `doc_type`、`product_line`、`status`（本页面固定只传 page=1、page_size=20）。
  - 响应字段：`{ total, items: [{ id, title, doc_type, product_line, product_version, status, chunk_count, version, created_at }] }`，status 取值为 pending / parsing / success / failed。
  - 成功后行为：更新表格数据；检查 items 中是否还存在 status 为 pending 或 parsing 的文档——有则保持 3 秒轮询，没有则清除定时器停止轮询。
  - 失败后行为：轮询请求失败不打断页面，仅 console.error 并用 ElMessage.warning 提示一次"进度刷新失败，将在 3 秒后重试"；连续失败也保持每 3 秒重试，页面已有数据不清空。
- `GET /api/documents/{doc_id}`：文档详情（本页只用于取失败原因）。
  - 请求参数：路径参数 `doc_id`。
  - 响应字段：文档全部字段，含 `fail_reason`、`file_type`、`updated_at`。
  - 成功后行为：把 `fail_reason` 显示在对应行的 ElAlert 中。
  - 失败后行为：ElAlert 中显示兜底文案"入库失败，请重试"。

状态处理：
- loading：上传按钮提交期间 loading + 禁用；首次进入页面加载列表时 ElTable 加 `v-loading`；轮询刷新时不显示全表 loading（静默更新，避免闪烁）。
- empty：列表为空时 ElTable 空态用 ElEmpty，文案"还没有上传过文档，从上方表单开始"。
- error：列表首次加载失败显示 ElAlert（type=error）+ "重新加载"按钮。
- permission：进入页面前端先判断 Pinia user store 中 role 是否为 admin，不是则显示 ElResult（icon=error，标题"无权限"，副标题"本页面仅知识管理员可用"），不渲染任何表单和表格；接口返回 403 时做同样处理。
- 轮询生命周期：用 `setInterval` 每 3 秒轮询；所有文档到达终态后 `clearInterval`；组件 `onUnmounted` 时必须清除定时器，防止页面跳转后还在发请求。

Mock 数据：
- 后端未完成时，在 `frontend/src/api/document.js` 同目录或页面内提供一个显眼的 mock 开关（如文件顶部 `const USE_MOCK = true`），打开时用内置 mock 数据、不发真实请求；字段必须与上方接口响应完全一致，方便后端就绪后一行切换。
- mock 列表数据要覆盖：1 条 pending、1 条 parsing、1 条 success（chunk_count=42）、1 条 failed 的文档；failed 文档的详情 mock 返回 `fail_reason: "未解析到文本内容，请确认不是纯图片扫描件"`。
- mock 空数据场景：提供一个空 items 的注释示例，方便手动验证 ElEmpty。
- mock 异常场景：提供一个"返回 409 同名冲突"的注释示例，方便验证上传失败提示。
- 为便于演示状态流转，mock 可以写一个简易计数器：同一份 mock 列表被轮询读取时，pending 文档第二次读取变 parsing、第四次变 success，让开发者不开后端也能看到状态变化和"全部终态后停止轮询"的效果（用注释说明这段逻辑联调时删除）。

响应式要求：
- 桌面端（≥1200px）：上下两个 ElCard 纵向排列，表单一行放 2~4 个表单项，表格全宽展示所有列。
- 窄屏（<768px）：表单项改为每行 1 个；表格允许横向滚动（ElTable 每列设 min-width），上传卡片和进度卡片间距缩小。

完成后自查：
- 页面能在 Vite 开发环境（Node.js ≥ 20，`npm run dev`）正常运行，无控制台报错。
- 全部是 JavaScript：没有 `.ts` 文件、没有 `lang="ts"`、没有 TS 类型标注。
- 选择文件、填表单、点上传、看状态流转、看失败原因，每一步都可点击且有可见反馈。
- 三个 API 的方法、路径、参数与上方约定完全一致，multipart 请求正确设置了文件和四个文本字段。
- 轮询逻辑正确：有 pending/parsing 才轮询，全部终态后停止，离开页面清除定时器。
- loading、empty、error、无权限（非 admin）四种状态都有可见处理。
- 没有任何 TypeScript 痕迹，且只使用了 Element Plus + Axios + Pinia + Vue Router，没有引入新依赖。

## 反馈审核工作台

硬性技术要求：
- 使用 Vue 3（版本基线 3.5.41）Composition API 和 `<script setup>`。
- 只使用 JavaScript，不要使用 TypeScript。不要生成 `.ts` 文件，不要写 `lang="ts"`，不要写 TS 类型定义。
- UI 组件使用 Element Plus（版本基线 2.14.4）。
- HTTP 请求使用 Axios（版本基线 1.19.0），统一走封装好的实例 `frontend/src/utils/request.js`（baseURL 为 `/api`，自动带 `Authorization: Bearer <token>` 头；该文件将在 Stage 7 创建，本页面先按"它已存在"来 import）。
- API 路径必须与下方接口约定完全一致，不得自创路径。
- 建议文件路径（均将在 Stage 7 创建）：
  - 页面：`frontend/src/views/AuditWorkbenchView.vue`
  - 接口封装：`frontend/src/api/audit.js`（导出 `getAuditTasks(params)`、`getAuditTaskDetail(taskId)`、`resolveAuditTask(taskId, body)`）和 `frontend/src/api/guardrail.js`（导出 `getGuardrailRules()`、`createGuardrailRule(body)`、`updateGuardrailRule(ruleId, body)`）
  - 路由登记：`frontend/src/router/index.js` 中加 `{ path: '/audit', component: AuditWorkbenchView, meta: { role: 'admin' } }`

业务目标：
- 页面服务于"反馈进化流程"：运维工程师对问答答案点踩后系统自动生成审核任务，知识管理员在本页面回看完整问答上下文并给出处理结论，形成"反馈 → 审核 → 修正"闭环。
- 页内第二个 Tab 服务于"护栏规则维护"：管理员维护问答护栏规则（命中即拦截或提示确认），规则不写死在代码里。
- 用户角色：仅知识管理员（admin）。
- 用户在本页面要完成：
  1. 按状态筛选、分页浏览审核任务；
  2. 打开任务抽屉，完整回看原始问题、答案全文、引用片段、点踩原因；
  3. 选择结论类型（已解决/已驳回）并填写必填的处理结论，提交；
  4. 任务已被别人处理时看到明确的冲突提示；
  5. 在护栏规则 Tab 新增、编辑、启停规则。

页面布局：
- 顶部区域：页面标题"反馈审核工作台"，右上角显示当前登录管理员姓名（从 `frontend/src/stores/user.js` 的 Pinia store 读取）。
- 主体区域：ElTabs，两个 Tab——"审核任务"（默认激活）和"护栏规则"。
- Tab1"审核任务"：
  - 查询区域：左侧状态筛选 ElSelect（选项：待处理 pending【默认】、已解决 resolved、已驳回 rejected、全部【不传 status 参数】）；右侧显示"共 N 条"。
  - 内容区域：ElTable 任务表格 + 底部右对齐 ElPagination。
  - 辅助区域：点"处理/查看"后从右侧弹出 ElDrawer（宽度建议 50%），上半部分是只读上下文，下半部分是处理表单。
- Tab2"护栏规则"：
  - 查询区域：无筛选，左上角"新增规则"按钮（type=primary）。
  - 内容区域：ElTable 规则表格（一次性展示全部规则，不分页）。
  - 辅助区域：ElDialog 新增/编辑规则表单（同一个弹窗复用，标题随模式变化）。

Element Plus 组件要求：
- 审核任务表格列：任务 ID（id）、点踩原因摘要（dislike_reason 截断显示，表格行内只显示前 30 字加省略号——注意：列表接口不返回 dislike_reason，表格摘要列可显示 resolution 或留待抽屉展示；实现时列表列显示"任务 ID / 状态 / 处理结论 resolution / 处理时间 resolved_at / 创建时间 created_at / 操作"）、状态（status 用 ElTag：pending 橙色"待处理"、resolved 绿色"已解决"、rejected 灰色"已驳回"）、创建时间（created_at 格式化 YYYY-MM-DD HH:mm）、操作列（pending 行按钮文案"处理" type=primary，非 pending 行文案"查看" type=info 且抽屉内表单只读）。
- 分页规则：ElPagination，`layout="total, prev, pager, next"`，page_size 固定 20；请求参数 `page`（从 1 开始）、`page_size`；响应取 `total`、`items`。切换筛选状态后 page 重置为 1。
- 任务详情抽屉（ElDrawer）内容：
  - 原始问题：字段 `question`，普通文本块；
  - 答案全文：字段 `answer`，用带边框的卡片展示，卡片右上角用 ElTag 显示 `message_status`（normal 绿"正常"、blocked 红"护栏拦截"、refused 橙"无依据拒答"、failed 灰"系统失败"）；
  - 引用片段：`citations` 数组逐条渲染为引用卡片，每条显示序号、`document_title`、`product_version`（ElTag）、`snippet`（原文片段）；citations 为空或 null 时显示"无引用"；
  - `document_deleted` 为 true 时，在引用片段区上方显示 ElAlert（type=warning）"关联文档已被删除，以下为当时留存的引用快照"；
  - 点踩原因：字段 `dislike_reason`，用 ElAlert（type=error）样式突出显示。
- 处理表单（抽屉下半区，ElForm rules）：
  - 结论类型：ElRadioGroup，两个选项——`resolved` 已解决、`rejected` 已驳回（value 用英文枚举，label 中文）；必填；
  - 处理结论 resolution：ElInput type=textarea（rows=4），必填，1~1000 字符，placeholder 提示"请说明处理方式与依据，例如：已重新上传 V3.2 新版 SOP 并重新入库"；
  - 提交按钮：type=primary，提交期间 loading 且禁用；
  - 任务非 pending 时（从"查看"进入）：整个表单禁用，结论区域直接展示已有的 `resolution` 和 `resolved_at`。
- 护栏规则表格列：规则名 rule_name、类型 rule_type（ElTag：sensitive_op"敏感操作"蓝、high_risk_cmd"高危命令"红、price"价格商务"橙）、动作 action（ElTag：block"拦截"红、confirm"提示确认"橙）、匹配方式 match_type（keyword"关键词"/regex"正则"）、匹配内容 pattern（等宽字体风格）、拦截话术 reply_text（截断 30 字，悬停 ElTooltip 显示全文）、启用 enabled（ElSwitch，拨动即调 PUT 接口只传 `{ enabled: 新值 }`）、操作列（"编辑"按钮）。
- 规则表单（ElDialog 内 ElForm rules）：
  - rule_name 规则名：必填，1~100 字符；
  - rule_type 规则类型：ElSelect 必选，选项 `sensitive_op` 敏感操作 / `high_risk_cmd` 高危命令 / `price` 价格商务；
  - action 命中动作：ElSelect 必选，选项 `block` 直接拦截 / `confirm` 提示确认；
  - match_type 匹配方式：ElSelect 必选，选项 `keyword` 关键词包含 / `regex` 正则表达式；选 regex 时在表单项下方给一行灰色小字提示"请确认正则写法正确，写错的规则会被系统跳过"；
  - pattern 匹配内容：ElInput 必填，1~500 字符，placeholder 按 match_type 变化（keyword："如：rm -rf"；regex："如：rm\\s+-rf"）；
  - reply_text 拦截话术：ElInput type=textarea 必填，placeholder"命中后回复给用户的话术，如：该操作属于高危命令，请提交变更工单"；
  - enabled 是否启用：ElSwitch，新增时默认开；
  - 编辑模式打开时回填全部字段；编辑和新增共用同一校验规则。

接口约定（所有接口都需要 `Authorization: Bearer <token>`，且仅 admin 可调用）：
- `GET /api/audit/tasks`：分页查询审核任务。
  - 请求参数（query）：`status`（可选，pending/resolved/rejected，筛选"全部"时不传）、`page`（默认 1）、`page_size`（固定 20）。
  - 响应字段：`{ items: [{ id, feedback_id, message_id, status, resolution, resolved_by, resolved_at, created_at }], total, page, page_size }`。
  - 成功后行为：更新表格与分页器。
  - 失败后行为：ElAlert（type=error）+ "重新加载"按钮。
- `GET /api/audit/tasks/{task_id}`：审核任务详情。
  - 请求参数：路径参数 `task_id`。
  - 响应字段：任务全部字段 + `question`（原始问题）、`answer`（答案全文）、`message_status`（normal/blocked/refused/failed）、`citations`（引用快照数组，元素结构 `{ chunk_id, document_id, document_title, product_line, product_version, snippet }`，可为 null）、`dislike_reason`（点踩原因）、`document_deleted`（布尔，关联文档是否已删除）。
  - 成功后行为：打开 ElDrawer 渲染上述区块；返回 404 时 ElMessage.error"任务不存在或已被删除"并刷新列表。
  - 失败后行为：ElMessage.error 提示"详情加载失败，请重试"，抽屉不打开。
- `POST /api/audit/tasks/{task_id}/resolve`：提交处理结论。
  - 请求参数：路径参数 `task_id`；body `{ status: "resolved" 或 "rejected", resolution: "结论文本" }`，两个都必填。
  - 响应字段：任务全字段（更新后的 status/resolution/resolved_by/resolved_at）。
  - 成功后行为：ElMessage.success"处理完成"，关闭抽屉，刷新任务列表（保持当前筛选和页码）。
  - 失败后行为：HTTP 409 时用 ElMessageBox.alert 提示"任务已被处理，请刷新查看最新状态"，关闭抽屉并刷新列表；422（结论为空）由前端表单校验提前拦截，不会发出；其他错误 ElMessage.error"提交失败，请稍后重试"。
- `GET /api/guardrail/rules`：查询护栏规则列表。
  - 请求参数：无。
  - 响应字段：规则数组 `[{ id, rule_name, rule_type, action, match_type, pattern, reply_text, enabled }]`（不分页）。
  - 成功后行为：更新规则表格。
  - 失败后行为：表格区域显示 ElAlert（type=error）+ "重新加载"按钮。
- `POST /api/guardrail/rules`：新增护栏规则。
  - 请求参数（body）：`rule_name, rule_type, action, match_type, pattern, reply_text, enabled`，全部必填（enabled 默认 true）。
  - 响应字段：单条规则完整字段。
  - 成功后行为：ElMessage.success"规则已新增"，关闭弹窗，刷新规则表格。
  - 失败后行为：ElMessage.error 展示后端 detail 或"新增失败，请稍后重试"，弹窗保持打开、表单内容保留。
- `PUT /api/guardrail/rules/{rule_id}`：修改/启停护栏规则。
  - 请求参数：路径参数 `rule_id`；body 为任意可更新字段的子集——编辑时传全部表单字段；启停开关只传 `{ enabled: true/false }`。
  - 响应字段：更新后的单条规则。
  - 成功后行为：编辑场景同新增（提示+关弹窗+刷新）；启停场景 ElMessage.success"已启用/已停用"，就地更新该行。
  - 失败后行为：404 提示"规则不存在"并刷新表格；其他错误 ElMessage.error，开关拨动失败要把开关拨回原状态（用 :loading 或失败后回滚值实现）。

状态处理：
- loading：两个表格首次加载用 `v-loading`；抽屉打开前详情请求期间按钮 loading；所有提交按钮提交期间 loading+禁用。
- empty：任务表格空时 ElEmpty 文案"当前没有待处理的审核任务"（按筛选状态变化文案）；规则表格空时 ElEmpty 文案"还没有护栏规则，点左上方新增"。
- error：各列表加载失败都有 ElAlert + 重试按钮；操作类失败用 ElMessage/ElMessageBox。
- permission：进入页面前端先判断 Pinia user store 中 role 是否为 admin，不是则显示 ElResult（icon=error，标题"无权限"，副标题"本页面仅知识管理员可用"），不渲染 Tabs；接口返回 403 时做同样处理。

Mock 数据：
- 后端未完成时，在 `frontend/src/api/audit.js` 和 `guardrail.js` 内提供显眼的 mock 开关（如文件顶部 `const USE_MOCK = true`），打开时用内置 mock、不发真实请求；字段必须与上方接口响应完全一致，后端就绪后一行切换。
- audit mock：至少 4 条任务——2 条 pending、1 条 resolved（带 resolution 和 resolved_at）、1 条 rejected；详情 mock 要包含完整字段，其中 1 条的 `document_deleted: true`、1 条的 `message_status: "refused"` 且 `citations: null`，用于验证边界展示；另提供"空列表"和"resolve 返回 409"两个注释示例。
- guardrail mock：至少 3 条规则——high_risk_cmd+block+keyword（pattern "rm -rf"）、price+block+keyword（pattern "多少钱"）、sensitive_op+confirm+regex（pattern 一个合法正则），其中 1 条 `enabled: false`；另提供"空列表"注释示例。
- mock 的"提交/新增/编辑"操作可以直接改内存数组模拟成功（用注释说明联调时删除）。

响应式要求：
- 桌面端（≥1200px）：Tabs 全宽，抽屉宽度 50%，规则表格全列展示。
- 窄屏（<768px）：抽屉宽度 100%；任务表格和规则表格列设 min-width 允许横向滚动；筛选区纵向堆叠。

完成后自查：
- 页面能在 Vite 开发环境（Node.js ≥ 20，`npm run dev`）正常运行，无控制台报错。
- 全部是 JavaScript：没有 `.ts` 文件、没有 `lang="ts"`、没有 TS 类型标注。
- 六个 API 的方法、路径、参数与上方约定完全一致；启停规则的 PUT 只传 `{ enabled }` 一个字段。
- 任务"处理"流程可完整走通：开抽屉 → 看上下文（问题/答案/引用/点踩原因）→ 选结论类型 → 填结论 → 提交 → 列表刷新；409 冲突提示已单独验证。
- 规则"新增/编辑/启停"三类操作都可点击并有反馈；表单校验（必填、枚举、长度）全部生效。
- loading、empty、error、无权限（非 admin）四种状态都有可见处理。
- 只使用 Element Plus + Axios + Pinia + Vue Router，没有引入新依赖。

## 问答历史记录页

硬性技术要求：
- 使用 Vue 3（版本基线 3.5.41）Composition API 和 `<script setup>`。
- 只使用 JavaScript，不要使用 TypeScript。不要生成 `.ts` 文件，不要写 `lang="ts"`，不要写 TS 类型定义。
- UI 组件使用 Element Plus（版本基线 2.14.4）。
- HTTP 请求使用 Axios（版本基线 1.19.0），统一走封装好的实例 `frontend/src/utils/request.js`（baseURL 为 `/api`，自动带 `Authorization: Bearer <token>` 头；该文件将在 Stage 7 创建，本页面先按"它已存在"来 import）。
- API 路径必须与下方接口约定完全一致，不得自创路径。
- 建议文件路径（均将在 Stage 7 创建）：
  - 页面：`frontend/src/views/QaHistoryView.vue`
  - 接口封装：`frontend/src/api/qa.js`（导出 `getQaSessions()`、`getSessionMessages(sessionId)`、`createQaSession(body)`）
  - 路由登记：`frontend/src/router/index.js` 中加 `{ path: '/qa/history', component: QaHistoryView }`（P02 智能问答页路径为 `/qa`，本页跳转它时带 query 参数）

业务目标：
- 页面服务于"运维问答流程"的回看环节：用户翻查自己历史会话的完整对话（含引用来源卡片），并可以跳到智能问答页在旧会话里继续追问。
- 用户角色：所有登录用户（engineer 和 admin），各自只能看到自己的会话（后端按 JWT 用户过滤，前端不做跨用户逻辑）。
- 用户在本页面要完成：
  1. 浏览、按标题搜索自己的历史会话；
  2. 点开会话只读回看完整对话，包括答案的引用来源卡片；
  3. 一眼分辨哪些回答是正常、被护栏拦截、无依据拒答、系统失败；
  4. 点"继续追问"跳转到智能问答页（`/qa?session_id={id}`）接着聊；
  5. 点"发起新问答"创建新会话并跳转。
- 本页面全部只读：不提供任何编辑、删除历史的入口。

页面布局：
- 顶部区域：页面标题"问答历史记录"，右上角显示当前登录用户名（从 `frontend/src/stores/user.js` 的 Pinia store 读取）。
- 左侧会话面板（约占 1/3 宽）：
  - 顶部一个搜索 ElInput（placeholder"搜索会话标题"，可清空）+ 一个"发起新问答"按钮（type=primary）；
  - 下方是可滚动的会话卡片列表，按最近时间倒序；每张卡片显示：会话标题（超长省略）、消息数与最近更新时间（一行灰色小字）、右下角"继续追问"文字链接按钮；当前选中的卡片有高亮边框/底色。
- 右侧对话面板（约占 2/3 宽）：
  - 头部：会话标题 + "共 N 条消息 · 最近更新 YYYY-MM-DD HH:mm"；
  - 消息区：聊天气泡样式，用户消息靠右（浅色背景），系统消息靠左（白色卡片背景）；
  - 未选中任何会话（例如列表为空）时右侧显示 ElEmpty 占位"选择左侧会话查看对话记录"。

Element Plus 组件要求：
- 会话卡片：用普通 div + 样式实现或 ElCard 均可，选中态要有明显视觉区分；标题最多显示一行，超出省略号。
- 搜索：输入即对当前列表做前端本地过滤（标题包含匹配，不区分大小写），不发请求；搜索无结果时显示"没有匹配的会话"。
- 消息气泡：
  - `role === "user"`：右对齐气泡，显示消息 `content` 和 `created_at`（格式 HH:mm）；
  - `role === "assistant"`：左对齐卡片，显示 `content`；卡片右上角用 ElTag 显示消息状态——`normal` 绿色"正常"、`blocked` 红色"护栏拦截"、`refused` 橙色"无依据拒答"、`failed` 灰色"系统失败"；
  - `blocked / refused / failed` 的系统消息整体用 ElAlert 风格（对应 type=error / warning / info）展示，与正常答案明显区分；
  - `citations` 非空数组时，在系统消息卡片下方渲染"引用来源"区块：每条 citation 一张小卡片，显示序号、`document_title`、`product_version`（ElTag）、`snippet`（原文片段）；citations 为 null 或空数组时不显示该区块。
- 本页面无分页器：会话列表一次加载全部（接口不分页）；消息列表一次加载该会话全部消息。

接口约定（所有接口都需要 `Authorization: Bearer <token>`，只返回当前登录用户自己的数据）：
- `GET /api/qa/sessions`：查询当前用户的会话列表。
  - 请求参数：无。
  - 响应字段：会话数组 `[{ id, title, created_at, updated_at, message_count }]`，后端已按 `updated_at` 倒序返回；`message_count` 为该会话的消息数，由后端 `COUNT(qa_message)` 派生。
  - 成功后行为：渲染左侧列表；列表非空时自动选中第一条并触发消息加载。
  - 失败后行为：左侧面板显示 ElAlert（type=error）+ "重新加载"按钮。
- `GET /api/qa/sessions/{session_id}/messages`：查询会话内全部消息。
  - 请求参数：路径参数 `session_id`。
  - 响应字段：消息数组 `[{ id, session_id, role, content, citations, status, created_at }]`；`role` 为 user/assistant；`citations` 为引用快照数组（元素结构 `{ chunk_id, document_id, document_title, product_line, product_version, snippet }`）或 null；`status` 为 normal/blocked/refused/failed。
  - 成功后行为：右侧渲染对话；头部"共 N 条消息"的 N 取返回数组的长度。
  - 失败后行为：右侧显示 ElAlert（type=error）+ "重试"按钮；404（会话不存在或不属于当前用户）时用 ElMessage.error 提示"会话不存在或无权访问"，并把该会话从左侧列表移除。
- `POST /api/qa/sessions`：新建会话（"发起新问答"按钮）。
  - 请求参数：body `{ title: null }`（可不传 title，由后端生成默认标题）。
  - 响应字段：`{ id, title, created_at, updated_at }`。
  - 成功后行为：跳转到 `/qa?session_id={新会话id}`。
  - 失败后行为：ElMessage.error"创建会话失败，请稍后重试"。
- 路由跳转约定：本页"继续追问"和"发起新问答"都用 vue-router 跳转：`router.push({ path: '/qa', query: { session_id: id } })`。P02 智能问答页由另一份提示词生成，本页只负责带参跳转，不要在本页实现提问功能。

状态处理：
- loading：会话列表首次加载时左侧显示骨架屏或 `v-loading`；切换会话时消息区 `v-loading`；点击"继续追问"/"发起新问答"期间对应按钮 loading。
- empty：无任何会话时左侧 ElEmpty 文案"还没有问答记录，点上方按钮开始第一次问答"；有会话但未选中时右侧 ElEmpty 占位。
- error：见各接口的失败行为；401 未登录交给全局 Axios 拦截器跳登录页，本页不重复实现。
- permission：本页对 engineer 和 admin 都开放，无角色限制；只需处理"未登录跳登录"这一种情况（由全局拦截器负责）。

Mock 数据：
- 后端未完成时，在 `frontend/src/api/qa.js` 内提供显眼的 mock 开关（如文件顶部 `const USE_MOCK = true`），打开时用内置 mock、不发真实请求；字段必须与上方接口响应完全一致，后端就绪后一行切换。
- 会话 mock：至少 3 个会话，updated_at 各不相同（验证倒序），其中一个标题较长（验证省略号）；每个会话对象都要带 `message_count` 字段（与列表卡片展示的“消息数”对应，后端由 `COUNT(qa_message)` 派生）。
- 消息 mock：为其中一个会话准备至少 5 条消息，覆盖：1 条 user 消息、1 条 normal 且带 2 条 citations 的 assistant 消息、1 条 blocked（内容示例"该操作属于高危命令，请提交变更工单"，citations 为 null）、1 条 refused（citations 为 null）、1 条 failed；用于验证四种状态样式和引用卡片。
- 另提供"空会话列表"和"messages 接口返回 404"两个注释示例，方便验证空态和越权处理。
- mock 的"发起新问答"可以直接返回一个 id 递增的假会话对象（用注释说明联调时删除）。

响应式要求：
- 桌面端（≥1200px）：左右两栏，左栏固定约 320px，右栏自适应剩余宽度，消息气泡最大宽度 80%。
- 窄屏（<768px）：改为上下布局——会话列表在上（限高 200px 可滚动），对话区在下；点选会话后自动滚动到对话区顶部。

完成后自查：
- 页面能在 Vite 开发环境（Node.js ≥ 20，`npm run dev`）正常运行，无控制台报错。
- 全部是 JavaScript：没有 `.ts` 文件、没有 `lang="ts"`、没有 TS 类型标注。
- 三个 API 的方法、路径、参数与上方约定完全一致；"继续追问"跳转路径为 `/qa?session_id=xxx`。
- 会话搜索是纯前端过滤，不发请求；搜索无结果有提示。
- 四种消息状态（normal/blocked/refused/failed）样式区分明显；引用卡片在 citations 非空时正确渲染、为空时不渲染。
- 页面全部只读，没有任何编辑/删除入口，也没有提问输入框。
- loading、empty、error 状态都有可见处理。
- 只使用 Element Plus + Axios + Pinia + Vue Router，没有引入新依赖。