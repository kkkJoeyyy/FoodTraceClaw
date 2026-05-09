# WeChat Bot 白名单

## 说明

微信 Bot 仅处理白名单中用户的昵称发来的消息。不在白名单中的用户发送消息不会得到任何回复。

## 配置

启动时通过 `WHITELIST` 环境变量指定，多个昵称用英文逗号分隔：

```bash
WHITELIST="Chiu.Yin,朋友昵称" BACKEND_URL=http://localhost:8000 npm start
```

不设置 `WHITELIST` 时，默认允许所有人。

## 白名单列表

| 昵称 | 备注 |
|------|------|
| Chiu.Yin | 管理员 |
| | |
| | |
