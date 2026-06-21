# mecheck

## 壓力測試腳本

已提供可直接執行的 HTTP 壓測腳本：`scripts/load_test.py`（無需第三方套件）。

### 範例

固定總請求數：

```bash
python3 scripts/load_test.py \
  --url http://localhost:8080/health \
  --requests 1000 \
  --concurrency 20
```

固定執行秒數：

```bash
python3 scripts/load_test.py \
  --url http://localhost:8080/api/ping \
  --duration 30 \
  --concurrency 50
```

POST JSON：

```bash
python3 scripts/load_test.py \
  --url http://localhost:8080/api/test \
  --method POST \
  --header "Content-Type: application/json" \
  --body '{"hello":"world"}' \
  --requests 500 \
  --concurrency 10
```
