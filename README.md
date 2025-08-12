# N-SnapRecorder

N-SnapRecorder là ứng dụng ghi màn hình và chụp ảnh tự động viết bằng Python, có giao diện đồ họa (GUI) thân thiện, dễ sử dụng.  
Ứng dụng phù hợp cho nhu cầu quay video hướng dẫn, lưu lại thao tác, hoặc chụp ảnh màn hình định kỳ.

---

## ✨ Tính năng nổi bật
- Ghi màn hình với điều khiển bắt đầu/tạm dừng/dừng.
- Chụp ảnh màn hình tự động theo khoảng thời gian tùy chỉnh.
- Hiển thị thông tin thời lượng, dung lượng file trong khi ghi.
- Tùy chỉnh cài đặt lưu trữ và chất lượng ảnh/video.
- Giao diện đơn giản, dễ sử dụng, chạy được trên Windows.

---

## 🚀 Cài đặt & chạy thử

### 1. Tải mã nguồn
```bash
git clone https://github.com/Nhan-Moon-04/N-SnapRecorder.git
cd N-SnapRecorder
```

### 2. Cài đặt thư viện cần thiết
```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng
```bash
python main_gui.py
```

---

## 📂 Cấu trúc dự án
- `main_gui.py` — Giao diện người dùng chính.
- `recording_engine.py` — Xử lý ghi video màn hình.
- `screenshot_engine.py` — Xử lý chụp ảnh tự động.
- `utils.py` — Hàm tiện ích hỗ trợ.
- `requirements.txt` — Danh sách thư viện cần thiết.

---

## ⚙️ Cấu hình
- File `settings.json` cho phép tùy chỉnh đường dẫn lưu, chất lượng, và thời gian chụp.
- Có thể chỉnh trực tiếp trong ứng dụng qua menu **Cài đặt**.

---

## 🤝 Đóng góp
Rất hoan nghênh các đóng góp để cải thiện dự án:
1. Fork repository.
2. Tạo branch mới: `git checkout -b feature/new-feature`.
3. Commit thay đổi: `git commit -m "Thêm tính năng mới"`.
4. Push branch: `git push origin feature/new-feature`.
5. Mở Pull Request.

---

## 📜 Giấy phép
Phát hành dưới giấy phép **MIT** — bạn có thể sử dụng, sửa đổi, và phân phối tự do.
