# CDN quiz: 15 questions

Multiple choice, one correct answer each. Five questions per level.

## Level 1: Easy

**1.** On a cache HIT, what does the origin see?

- A. The full request
- B. Only the headers
- C. A revalidation request
- D. Nothing

**Đáp án: D.** Edge có bản còn fresh nên tự trả lời; origin không thấy request nào. (slide 2.2)

**2.** What is a PoP?

- A. A location that holds edge servers
- B. The server that keeps the master copy
- C. A DNS record type
- D. A cache header

**Đáp án: A.** PoP là một địa điểm vật lý chứa nhiều edge server; bản gốc nằm ở origin. (slide 2.1)

**3.** What mostly decides time to first byte from a far-away server?

- A. Bandwidth
- B. Round trips × distance
- C. Server CPU
- D. Page size

**Đáp án: B.** Latency bằng số round trip nhân với khoảng cách; bandwidth hay CPU không rút ngắn được đường đi. (slide 1.1)

**4.** Which headers tell you first whether a response came from cache?

- A. Content-Type and ETag
- B. Host and Accept
- C. Age and X-Cache
- D. Set-Cookie and Vary

**Đáp án: C.** `Age` cho biết response đã nằm trong cache bao lâu, `X-Cache` báo HIT hay MISS. (slide 8.3)

**5.** Which HTTP methods can a CDN cache?

- A. POST and PUT
- B. All methods
- C. GET and HEAD
- D. DELETE only

**Đáp án: C.** GET và HEAD là safe method; POST, PUT, DELETE luôn đi tới origin. (slide 4.2)

## Level 2: Medium

**6.** What does `Cache-Control: no-cache` mean?

- A. Never store it
- B. Store it, but revalidate before use
- C. Cache for 0 seconds, browsers only
- D. Bypass the CDN

**Đáp án: B.** `no-cache` là "hỏi lại trước khi dùng"; "không lưu" là `no-store`. (slide 3.1)

**7.** One page is shared as `?utm_source=fb` and `?utm_source=zalo`. By default the CDN stores…

- A. One shared copy
- B. Nothing
- C. Only the first one
- D. Two separate copies

**Đáp án: D.** Query string mặc định nằm trong cache key, nên hai URL thành hai cache entry. (slide 3.2)

**8.** The origin is down. Which directive lets the edge keep answering?

- A. stale-if-error
- B. must-revalidate
- C. no-store
- D. immutable

**Đáp án: A.** `stale-if-error` cho phép trả bản stale khi origin lỗi hoặc không kết nối được. (slide 3.6)

**9.** Browsers cached `app.js` for one year. How do users get the new version quickly?

- A. Purge the file on the CDN
- B. Lower `s-maxage` on the file
- C. Put a content hash in the file name
- D. Add `no-store` to the new version

**Đáp án: C.** Tên mới là URL mới nên browser phải tải lại; purge và `s-maxage` không với tới cache của browser. (slide 3.4, 3.5)

**10.** With Anycast, what happens when a PoP fails?

- A. Its route is withdrawn; traffic shifts within seconds
- B. Users move to another PoP only after the DNS TTL expires
- C. All traffic skips the CDN and goes straight to the origin
- D. Each user must switch to a new IP address by hand

**Đáp án: A.** PoP hỏng rút route BGP và router tự chuyển sang PoP khác; chờ DNS TTL là hành vi của GeoDNS. (slide 2.3)

## Level 3: Hard

**11.** A page is sent with `Cache-Control: max-age=0, s-maxage=60`. What happens?

- A. Nobody caches it; every request goes to the origin
- B. Browser and CDN both keep it 60 s without asking again
- C. Browser revalidates every time; CDN keeps it 60 s
- D. Browser keeps it for 60 s; the CDN never stores a copy

**Đáp án: C.** `s-maxage` chỉ dành cho CDN và ghi đè `max-age` ở đó; browser vẫn theo `max-age=0`. (slide 3.1)

**12.** The origin adds `Vary: User-Agent` to a cached page. What happens to the hit ratio?

- A. Nothing changes
- B. It drops near zero: one copy per browser string
- C. It rises: browsers share more copies
- D. The CDN stops caching the page

**Đáp án: B.** `Vary` thêm User-Agent vào cache key; giá trị quá đa dạng nên gần như mỗi request một bản riêng. (slide 3.2)

**13.** Edge code attached to the "origin request" event runs…

- A. On every request
- B. Only on a cache HIT
- C. Only when the origin is down
- D. Only on a cache MISS

**Đáp án: D.** Origin request chỉ xảy ra khi edge phải gọi origin, tức là MISS; chạy trên mọi request là viewer request. (slide 7.1)

**14.** A logged-in victim opens `/account/profile.css`, and the CDN caches their account page. What is the cause?

- A. The CDN trusts the `.css` ending; the origin ignores it
- B. A header changes the response but is not in the cache key
- C. The signed URL expired too late
- D. The origin's real IP address leaked

**Đáp án: A.** Đây là web cache deception: origin trả trang account, CDN thấy `.css` nên coi là static. Đáp án B là nguyên nhân của cache poisoning. (slide 6.5)

**15.** Your origin firewall accepts only the CDN's IP ranges. Why is that not enough?

- A. A firewall cannot filter traffic by IP
- B. All CDN customers share those ranges, so another account can reach your origin
- C. CDNs keep their IP ranges secret
- D. The allowlist turns off caching at the edge

**Đáp án: B.** Các dải IP dùng chung cho mọi khách hàng của CDN; cần thêm secret header hoặc mTLS. (slide 6.3)

## Answer key

| Question | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Answer | D | A | B | C | C | B | D | A | C | A | C | B | D | A | B |
