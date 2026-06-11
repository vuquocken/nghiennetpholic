# 🌐 Đưa Nghiện Netflix lên online (miễn phí)

> ⚠️ **Quan trọng:** Netflix thường **chặn IP máy chủ đám mây**. Nếu host trên Render/Hugging Face,
> chức năng tạo token **có thể bị lỗi/không ổn định**. Muốn chạy ỔN ĐỊNH thì dùng **Hướng A (Tunnel)**
> vì nó vẫn gọi Netflix bằng IP nhà bạn.

---

## 🟢 HƯỚNG A — Tunnel (KHUYÊN DÙNG, ổn định nhất)

Server vẫn chạy trên máy bạn, nhưng có link `https://...` mở được từ mọi nơi.

### Cách 1: ngrok (dễ nhất)
1. Tải ngrok: https://ngrok.com/download → giải nén ra `ngrok.exe`
2. Đăng ký tài khoản free → copy authtoken trên trang ngrok
3. Mở PowerShell, chạy:
   ```
   ngrok config add-authtoken <TOKEN_CỦA_BẠN>
   ```
4. Đảm bảo server đang chạy (mở `Khởi động.bat`)
5. Chạy:
   ```
   ngrok http 8799
   ```
6. ngrok hiện 1 dòng `Forwarding  https://xxxx-xx.ngrok-free.app` → **đó là link public của bạn**,
   gửi cho ai cũng mở được.

> Nhược điểm: máy phải bật + giữ cả `Khởi động.bat` lẫn cửa sổ ngrok. Link đổi mỗi lần chạy lại (bản free).

### Cách 2: Cloudflare Tunnel (link đẹp hơn, cũng free)
1. Tải `cloudflared`: https://github.com/cloudflare/cloudflared/releases (file `cloudflared-windows-amd64.exe`)
2. Mở server (`Khởi động.bat`)
3. Chạy:
   ```
   cloudflared tunnel --url http://localhost:8799
   ```
4. Nó in ra link `https://xxx.trycloudflare.com` → dùng ngay, không cần đăng ký.

---

## 🟡 HƯỚNG B — Host đám mây (online 24/7, tắt máy vẫn chạy)

> Lưu ý: có thể bị Netflix chặn IP datacenter. Cứ thử, nếu token lỗi thì quay lại Hướng A.

### Render.com (free)
1. Tạo tài khoản https://render.com
2. Đưa thư mục `NghienNetflix` lên một repo GitHub (hoặc dùng "Deploy from Git").
3. New → **Web Service** → chọn repo.
4. Cấu hình:
   - **Runtime:** Python 3  (hoặc Docker — đã có sẵn `Dockerfile`)
   - **Build Command:** (để trống — không cần thư viện gì)
   - **Start Command:** `python server.py`
5. Bấm Deploy. Render tự cấp link `https://ten-app.onrender.com`.

> Bản free "ngủ" sau 15 phút không dùng, lần mở sau chờ ~50 giây khởi động lại.

### Hugging Face Spaces (free, không ngủ)
1. Tạo tài khoản https://huggingface.co
2. New → **Space** → chọn **Docker** (Blank).
3. Upload toàn bộ file trong thư mục này (kéo thả trên web: `server.py`, `index.html`, `avatar.jpg`, `Dockerfile`).
4. Space tự build và chạy → có link `https://huggingface.co/spaces/<bạn>/<ten>`.

---

## 🔒 Lưu ý an toàn (đọc kỹ)
- Khi online, **cookie người dùng dán vào sẽ đi qua server của bạn**. Chỉ chia sẻ link cho người tin tưởng.
- Công cụ xử lý tài khoản Netflix có thể **vi phạm điều khoản** của nhà cung cấp host → có thể bị khoá. Nên dùng cho mục đích cá nhân.
- Không công khai link rộng rãi để tránh bị lạm dụng.

## 📌 Mẹo nhanh: dùng trong cùng WiFi (không cần internet/host)
Server giờ mở `0.0.0.0` khi có biến PORT. Để điện thoại cùng WiFi truy cập:
1. Xem IP máy tính: PowerShell gõ `ipconfig` → tìm `IPv4 Address` (vd `192.168.1.10`)
2. Trên điện thoại mở: `http://192.168.1.10:8799`
   (nếu không vào được, mở port 8799 trong Windows Firewall)
