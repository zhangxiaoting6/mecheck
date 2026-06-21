const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

const DEMO_USER = {
  username: "demo",
  password: "123456",
};

app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

app.post("/api/login", (req, res) => {
  const { username, password } = req.body || {};

  if (!username || !password) {
    return res.status(400).json({
      success: false,
      message: "請輸入帳號與密碼",
    });
  }

  const isValid =
    username === DEMO_USER.username && password === DEMO_USER.password;

  if (!isValid) {
    return res.status(401).json({
      success: false,
      message: "帳號或密碼錯誤",
    });
  }

  return res.json({
    success: true,
    message: "登入成功",
    token: "demo-token-abc123",
    user: {
      username: DEMO_USER.username,
    },
  });
});

if (require.main === module) {
  app.listen(PORT, () => {
    // eslint-disable-next-line no-console
    console.log(`Login demo is running on http://localhost:${PORT}`);
  });
}

module.exports = app;
