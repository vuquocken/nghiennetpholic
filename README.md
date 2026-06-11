---
title: Nghien Netflix
emoji: 🎬
colorFrom: red
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# Nghiện Netflix

Công cụ tạo link đăng nhập Netflix trực tiếp từ cookie (nftoken).

- Backend: Python (chỉ dùng thư viện chuẩn, không cần cài thêm).
- Chạy local: `python server.py` → http://127.0.0.1:8799
- Deploy: đã có sẵn `Dockerfile` (Hugging Face Spaces / Render / Fly.io).

Xem `HƯỚNG DẪN ĐƯA LÊN ONLINE.md` để biết cách đưa lên online.

> ⚠️ Netflix có thể chặn IP máy chủ đám mây — nếu tạo token bị lỗi khi host, hãy dùng tunnel (ngrok/Cloudflare) chạy từ máy cá nhân.
