# WillChat

WillChat是一個專案計畫所製作的專案，未來可能會將聊天伺服器後端進行開源。此專案庫主要為客戶端請求，第一版本可能會比較不穩定。

## 結構

```
willchat/
├─ src/
│  ├─ python-client/          # Client
│  │  ├─ app.py               # 事件監聽與指令註冊
│  │  ├─ config.py            # 連線設定
│  │  └─ willclient/          # 用戶端程式庫
│  │     ├─ __init__.py       # Client / Message / Group / Member / EventType / MessageType
│  │     ├─ client.py         # Client
│  │     ├─ request.py        # Requester:REST
│  │     ├─ objects.py        # Group / Member / Message
│  │     ├─ enums.py          # MessageType / EventType
│  │     ├─ exceptions.py     # 例外類別
│  │     ├─ commands/         # 指令框架
│  │     └─ events/           # 事件分派
│  ├─ frontend/               # 未來前端開源
│  └─ software/               # 未來前端開源
├─ LICENSE                    # GNU GPL v3.0
└─ README.md
```

## PythonClient
[Client Path](/src/python-client/)

### 切換路徑
```ini
cd src/python-client
```

### 安裝套件
使用requirements進行安裝

```ini
pip install -r requirements.txt
```

或直接安裝套件

```ini
pip install aiohttp websockets
```

### 如何使用
```ini
python app.py
```

*目前僅給予貢獻者進行測試與其他使用者查看專案架構

## 貢獻者
- [littlecommandcat](https://github.com/littlecommandcat/)

- [william2177561](https://github.com/william2177561)

- [lazyyezi](https://github.com/lazyyezi)