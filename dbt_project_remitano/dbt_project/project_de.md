# Project for Data Engineer Position

Chào bạn,

Cảm ơn bạn đã quan tâm đến vị trí Data Engineer tại công ty chúng tôi. Bài test take-home này được thiết kế để mô phỏng một yêu cầu nghiệp vụ thực tế. Mục tiêu là để chúng tôi hiểu hơn về kỹ năng xử lý dữ liệu, tư duy data modeling và cách bạn cấu trúc một dự án.
Dữ liệu cung cấp
Chúng tôi cung cấp 2 file CSV trong link này:

`transactions.csv`: Ghi lại lịch sử giao dịch của người dùng.

tx_id: Mã giao dịch (unique)

user_id: Mã người dùng

source_currency: Loại tiền tệ nguồn (ví dụ: BTC, ETH)

destination_currency: Loại tiền tệ đích (ví dụ: USDT, VND)

source_amount: Số lượng tiền nguồn

destination_amount: Số lượng tiền đích

created_at: Thời gian giao dịch (UTC)

status: Trạng thái 


`users.csv`: Thông tin người dùng.

user_id: Mã người dùng (unique)

kyc_level: Cấp độ xác minh danh tính (ví dụ: L0, L1, L2)

created_at: Thời gian tạo tài khoản

updated_at: Thời gian cập nhật thông tin lần cuối


## Yêu cầu

### Bài 1: Ingestion - Thu thập dữ liệu Tỷ giá
Team Analytics muốn quy đổi tất cả các giao dịch về một đơn vị chung (USD) để tiện so sánh. Bạn cần lấy dữ liệu tỷ giá từ một nguồn bên ngoài.

Xác định phạm vi:

Từ file `transactions.csv`, hãy xác định tất cả các loại tiền tệ ở destination_currency xuất hiện.
Xác định khoảng thời gian (ngày bắt đầu, ngày kết thúc) của dữ liệu giao dịch.

Gọi API:

- Sử dụng API public của Binance (endpoint: /api/v3/klines) để lấy dữ liệu tỷ giá theo giờ (1h).
- Giả định: Chúng ta chỉ cần lấy tỷ giá của các loại tiền tệ so với USDT (ví dụ: BTCUSDT, ETHUSDT). Bạn có thể bỏ qua các cặp không có trên Binance hoặc không trade với USDT.
- Lấy dữ liệu cho toàn bộ khoảng thời gian bạn đã xác định ở bước 1.
- Lưu trữ:
Lưu kết quả (dữ liệu klines) xuống một file (ví dụ: JSONL, CSV, hoặc Parquet) trong thư mục /output/raw_rates/. Đây sẽ là nguồn "bronze data" cho bước sau.

### Bài 2: Transformation & Data Modeling (sử dụng dbt)

Team Analytics cần một bộ dữ liệu tin cậy (Single Source of Truth) trong DWH để xây dựng dashboard. Họ có một số câu hỏi nghiệp vụ chính:

- "Chúng tôi muốn phân tích tổng khối lượng giao dịch (tính bằng USD) theo ngày/tháng/quý."
- "Chúng tôi cần xem các giao dịch đã hoàn thành (COMPLETED) được thực hiện bởi những người dùng ở mỗi cấp độ KYC (kyc_level)."
- "Một yêu cầu rất quan trọng: Khi chúng tôi xem một giao dịch cũ từ 6 tháng trước, chúng tôi muốn biết kyc_level của người dùng đó tại thời điểm giao dịch đó diễn ra là gì, chứ không phải kyc_level hiện tại của họ."

Nhiệm vụ của bạn:

Sử dụng `dbt`, hãy thiết kế Data Model và xây dựng DWH từ `bronze-silver-gold` data để trả lời các câu hỏi nghiệp vụ trên.
* Yêu cầu về Bronze (models/staging/):

- Xây dựng các model staging cho cả 3 nguồn dữ liệu (users, transactions, rates).
- Công việc cơ bản: Dọn dẹp, đổi tên cột, ép kiểu.
- Thêm các data tests cần thiết (ví dụ: unique, not_null) cho các khóa chính và các cột quan trọng.
* Yêu cầu về Silver (models/int/) /Gold (models/marts/):

Bạn được toàn quyền quyết định cấu trúc model của mình (ví dụ: Snowflake Schema, OBT, hay một cấu trúc khác).

- Model cuối cùng phải "sạch" và sẵn sàng cho team BI sử dụng.
- Model phải giải quyết được cả 3 yêu cầu nghiệp vụ ở trên, đặc biệt là yêu cầu số 3 (theo dõi lịch sử kyc_level) và yêu cầu tính toán giá trị USD.


* Yêu cầu về tài liệu (Bổ sung vào `ARCHITECTURE.md`):

- Hãy mô tả ngắn gọn (hoặc vẽ sơ đồ text-based) data model bạn đã chọn.
- Giải thích lý do tại sao bạn chọn mô hình đó.
- Giải thích cách bạn giải quyết "Yêu cầu nghiệp vụ số 3" (việc theo dõi lịch sử kyc_level).

### Bài 3: Kiến trúc & Lưu trữ
Chúng tôi muốn hiểu tư duy hệ thống của bạn. Bạn không cần setup bất kỳ DWH nào, chỉ cần trả lời các câu hỏi sau trong một file `ARCHITECTURE.md`:

- Lựa chọn DWH: Nếu triển khai thực tế, bạn sẽ chọn DWH nào (ví dụ: BigQuery, Snowflake, Redshift, Databricks, Postgres...) để chạy dbt project này? Giải thích ngắn gọn (3-5 gạch đầu dòng) lý do bạn chọn.
- Chiến lược Materialization: Trong dbt, bạn chọn chiến lược materialization (view, table, incremental, ephemeral) cho các model sau như thế nào và tại sao?
- Orchestration (Lên lịch): Mô tả ngắn gọn cách bạn sẽ lên lịch (orchestrate) để pipeline này chạy hàng ngày (bao gồm cả Bài 1 và Bài 2). Nêu công cụ bạn chọn (ví dụ: Airflow, Dagster, dbt Cloud, Cron...) và mô tả các dependencies giữa các task.

* Yêu cầu nộp bài

Bạn cần nộp lại một Repo Git (public, hoặc private và cấp quyền cho chúng tôi) với cấu trúc thư mục rõ ràng.
