# mecheck

## Login Demo

一個最小可執行的登入示範（Node.js + Express + 原生 HTML）。

### 啟動方式

```bash
npm install
npm start
```

啟動後開啟：`http://localhost:3000`

### 測試帳號

- username: `demo`
- password: `123456`

### API

- `POST /api/login`
  - Request JSON:
    ```json
    {
      "username": "demo",
      "password": "123456"
    }
    ```
  - 成功時回傳 `success: true` 與 demo token。
