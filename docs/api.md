# API request examples

### [Private Repo]

請從 `examples` 目錄執行：

```cmd
cd examples
python health\health.py
python auth\login.py
```

## 設定

使用 `config.py`

## API 分類

### Health

| Method | Path | Example |
|---|---|---|
| GET | `/health` | `health/health.py` |

### Auth

| Method | Path | Example |
|---|---|---|
| POST | `/auth/register` | `auth/register.py` |
| POST | `/auth/login` | `auth/login.py` |
| GET | `/auth/me` | `auth/me.py` |
| PUT | `/auth/me` | `auth/profile.py` |
| POST | `/auth/reset` | `auth/resetpassword.py` |
| POST | `/auth/logout` | `auth/logout.py` |

### Groups

| Method | Path | Example |
|---|---|---|
| POST | `/groups` | `groups/create.py` |
| GET | `/groups/:group_id` | `groups/get.py` |
| DELETE | `/groups/:group_id` | `groups/delete.py` |
| POST | `/groups/:group_id/members` | `groups/join.py` |
| DELETE | `/groups/:group_id/members` | `groups/leave.py` |

### Chat

| Method | Path | Example |
|---|---|---|
| POST | `/groups/:group_id/messages` | `chat/send.py` |

### WebSocket

| Method | Path | Example |
|---|---|---|
| GET | `/ws?token=<token>` | `websocket/connection.py` |
| GET | `/ws?token=<token>` + message request | `websocket/events.py` |

### Security

`security/ratelimit.py` 會重複請求群組 API，用來觀察 rate limit 回應。
