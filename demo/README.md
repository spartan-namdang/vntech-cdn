# Demo: một CDN thu nhỏ chạy trên máy

Ba container: `origin` (server Python, cố tình chậm 200 ms để giả lập "ở xa"), `edge` (Varnish, đóng vai một PoP) và `console` (phục vụ dashboard và sinh traffic giả lập). Không cần mạng sau lần kéo image đầu tiên.

| | Địa chỉ | Vai trò |
|---|---|---|
| Edge | `http://127.0.0.1:8080` | Người dùng gọi vào đây |
| Origin | `http://127.0.0.1:9000` | Gọi thẳng, bỏ qua edge |
| Console | `http://127.0.0.1:8090` | Dashboard |

Có hai cách dùng lab: dashboard toàn màn hình (traffic chạy liên tục), hoặc gõ lệnh trong terminal (từng request một). Slide "Demo · Live dashboard" trong deck dẫn sang dashboard và có kịch bản trong speaker notes.

## Dashboard

```bash
docker compose up -d
```

Mở `http://127.0.0.1:8090/` và bật công tắc **Simulated shoppers**. Lab tự đóng vai khách của một shop nhỏ (trang sản phẩm, link quảng cáo có `utm_*`, API tồn kho, trang tài khoản của 30 người), mặc định 20 request mỗi giây. Biểu đồ cập nhật mỗi giây và giữ 2 phút gần nhất; mỗi lần đổi cấu hình để lại một vạch đứt có nhãn trên biểu đồ.

| Thao tác | Điều sẽ thấy |
|---|---|
| Để nguyên mặc định | Ô "Wrong account shown" đỏ: trang tài khoản bị cache chung nên khách thấy tài khoản người khác |
| Bật **Account page is private** | Số trang sai người về 0; origin nhận thêm request vì trang cá nhân không cache được |
| Bật **Ignore utm_\* in the cache key** | Tỉ lệ cache tăng, đường "Reaching the origin" tụt xuống |
| Tắt **Cache at the edge** | Hai đường request chập làm một: origin nhận toàn bộ traffic |
| **Purge everything** | Một đợt MISS rồi tự hồi phục trong vài giây |
| **Crash the origin** | Sau khoảng 10 giây (hết TTL) lỗi lên gần 100% |
| Bật **Serve stale if the origin fails** | Phần lớn lỗi biến mất, thay bằng STALE; phần còn lại là trang chưa từng được cache và trang cá nhân |
| **Start a flash sale** (15 giây) | Traffic tăng vọt nhưng origin gần như không đổi |
| Tắt **Merge identical requests** rồi flash sale lần nữa | Ô "Origin load" báo hàng chục request đang xử lý, thời gian phản hồi p95 lên vài giây |

Nên bật "Serve stale" trước khi làm sập origin để thấy hiệu quả đầy đủ. **Reset the demo** đưa mọi công tắc về mặc định, xóa cache và biểu đồ, và tắt traffic.

Dashboard chỉ đụng tới các URL dưới `/shop/`, nên không làm nhiễu log origin khi bạn gõ lệnh trong terminal, trừ việc origin sẽ chậm hơn khi traffic đang chạy. Tắt traffic trước khi dùng terminal.

## Terminal

Chạy mọi lệnh từ thư mục `demo/`. Chia đôi màn hình terminal.

Bên phải, bật stack và để log của origin chạy suốt buổi. Mỗi dòng là một request origin phải trả lời; edge trả từ cache thì ở đây không hiện gì.

```bash
docker compose up -d && docker compose logs -f --no-log-prefix origin
```

Bên trái, khai báo ba thứ dùng cho mọi cảnh:

```bash
E=http://127.0.0.1:8080; O=http://127.0.0.1:9000
h() { curl -s -o /dev/null -D - "$@" | grep -iE '^(HTTP|age|x-cache|cache-control)'; }
```

Tập lại từ đầu (xóa cache, trả edge về cấu hình gốc):

```bash
docker compose restart edge
```

## Cảnh 1 · MISS rồi HIT (2.2, 8.3, 10.1)

```bash
h $E/assets/app.3f9a1c.js
h $E/assets/app.3f9a1c.js
```

Lần đầu `X-Cache: MISS`, log origin hiện một dòng. Lần hai `HIT`, `Age` bắt đầu đếm, log origin đứng im.

## Cảnh 2 · HIT nhanh hơn bao nhiêu (1.1)

```bash
for u in $O $E; do curl -so /dev/null -w "$u ttfb=%{time_starttransfer}s\n" $u/assets/app.3f9a1c.js; done
```

Gọi thẳng origin mất khoảng 0,2 s; qua edge vài ms. Lưu ý khi nói: 200 ms ở đây là origin tự ngủ, không phải handshake thật. Muốn con số TCP/TLS thật thì đo trên một CDN thật.

## Cảnh 3 · Cache key bị vỡ (3.2, 3.7)

```bash
h "$E/products?utm_source=fb"
h "$E/products?utm_source=zalo"
```

Cùng một trang nhưng cả hai đều MISS, origin render hai lần. Sửa ở edge: bỏ tham số `utm_*` khỏi key. Trong lab, luật này bật bằng một header chỉ dùng cho demo (xem [edge/default.vcl](edge/default.vcl)):

```bash
h -H 'X-Demo-Strip-Utm: 1' "$E/products?utm_source=fb"
h -H 'X-Demo-Strip-Utm: 1' "$E/products?utm_source=zalo"
```

Lần này request đầu MISS, request sau HIT; trong log origin URL chỉ còn `/products`.

## Cảnh 4 · Origin sập, site vẫn sống (3.6)

Hai API có cùng TTL 5 giây. `/api/news` có thêm `stale-while-revalidate=10, stale-if-error=600`; `/api/prices` thì không.

```bash
h $E/api/news; h $E/api/prices
```

```bash
docker compose stop origin
```

Đợi khoảng 8 giây (hết TTL, và edge kịp nhận ra origin đã chết), rồi:

```bash
h $E/api/news; curl -s $E/api/news; h $E/api/prices
```

`/api/news` vẫn 200 với `X-Cache: HIT (stale)` và giờ `built` cũ. `/api/prices` trả 503. Bật lại origin:

```bash
docker compose start origin
```

## Cảnh 5 · Lộ dữ liệu riêng (9.2, 4.7)

`/me` trả về tên người đang đăng nhập theo cookie, nhưng origin lại gắn `Cache-Control: public, max-age=60`.

```bash
curl -s -b user=An $E/me
curl -s -b user=Binh $E/me
```

Bình nhận `{"user": "An"}`. Bản đã sửa dùng `private, no-store`:

```bash
curl -s -b user=An $E/me-fixed
curl -s -b user=Binh $E/me-fixed
```

## Cảnh 6 · Stampede (3.8), dự phòng

`/slow` mất hơn 1 giây để tạo. Bắn 50 request cùng lúc vào lúc cache trống:

```bash
seq 50 | xargs -P 50 -I{} curl -s -o /dev/null $E/slow
```

Log origin chỉ có một dòng: edge gộp 50 request thành một. Đợi 6 giây cho object hết hạn, rồi tắt việc gộp bằng một header chỉ dùng cho demo:

```bash
seq 50 | xargs -P 50 -I{} curl -s -o /dev/null -H 'X-Demo-No-Collapse: 1' $E/slow
```

Log origin cuộn khoảng 50 dòng.

## Dọn dẹp

```bash
docker compose down
```

## Ghi chú

- Varnish là phần mềm lõi của Fastly, nên `Age` và hành vi stale ở đây là thật. Tên header trạng thái khác nhau theo vendor: ở đây là `X-Cache`, Cloudflare dùng `cf-cache-status`.
- Edge này chỉ là một PoP, nên không minh họa được định tuyến theo địa lý hay cache riêng từng PoP.
- Đổi độ trễ của origin bằng `ORIGIN_DELAY_MS` trong [compose.yaml](compose.yaml).
- Chụp sẵn kết quả từng cảnh, phòng khi Docker trục trặc lúc lên sân khấu.
