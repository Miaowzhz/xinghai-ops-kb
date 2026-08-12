# xinghai-ops-kb（前端）

基于 Vue 3 + Vite + Element Plus 的运维知识库单页应用。

- **工程标识**：`xinghai-ops-kb`
- **技术栈**：Vue 3、Vite、Element Plus、Vue Router、Pinia、Axios
- **启动**：`npm install && npm run dev`
- **构建**：`npm run build`，产物输出到 `dist/`
- **开发代理**：`/api` 转发至 `http://localhost:8000`
- **与后端约定**：所有接口路径使用 `/api` 前缀，Axios 统一注入 JWT
