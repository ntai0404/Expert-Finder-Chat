# 📍 AI Expert Finder & Mentor Connector (Hệ thống tìm kiếm Chuyên gia & Cố vấn)

## 1. Tổng Quan

Hệ thống cho phép người dùng (học viên, nghiên cứu sinh) tìm kiếm Chuyên gia hoặc Cố vấn (Mentors/Experts) thông qua giao diện Chat. Hệ thống sẽ tự động xác định nhu cầu học tập/nghiên cứu, tìm Chuyên gia phù hợp nhất (từ danh sách trong Google Sheets), cung cấp quyền truy cập vào Knowledge Base (NotebookLM) của chuyên gia đó và dùng AI để tư vấn lộ trình học tập cá nhân hóa.

Hệ thống hỗ trợ đăng nhập qua Zalo OAuth để cá nhân hóa trải nghiệm và cho phép kết nối trực tiếp với cộng đồng Zalo của Chuyên gia.

## 2. Actors (Tác nhân)

- **User (Người dùng)**: Học viên, nghiên cứu sinh hoặc người cần tìm kiếm tri thức chuyên sâu.
- **System (Backend)**: Xử lý logic tìm kiếm, phân tích ý định (intent), và quản lý kết nối.
- **Zalo OAuth Service**: Cung cấp API để xác thực người dùng qua tài khoản Zalo.
- **Google Maps Service**: Hỗ trợ định vị (nếu cần tư vấn offline) và chuẩn hóa địa chỉ.
- **Google Sheets (Database)**: Lưu trữ hồ sơ chuyên gia, lĩnh vực chuyên môn, và các liên kết tri thức (NotebookLM).
- **AI Engine (DeepSeek V3)**: Phân tích nhu cầu người dùng và sinh câu trả lời tư vấn tự nhiên. Chú trọng biến đại diện cho chuyên gia, chủ đề, ý muốn ở đây sẽ tạm gọi lần lượt là Expert, Topic, Intent.
---

## 3. Use Case 1: "Đăng nhập với Zalo OAuth"

**Pre-conditions (Điều kiện tiên quyết)**
- Người dùng có tài khoản Zalo.
- Ứng dụng đã được cấu hình Zalo App và Backend.

**Basic Flow (Luồng chính)**
1. **User**: Truy cập trang đăng nhập.
2. **System**: Kiểm tra session hiện có. Nếu hợp lệ -> Chuyển vào trang chủ.
3. **User**: Click "Đăng nhập với Zalo".
4. **Backend**: Thực hiện quy trình trao đổi code lấy access token và thông tin profile Zalo.
5. **System**: Tạo session và lưu thông tin người dùng (Tên, Avatar) vào `localStorage`.
6. **User**: Bắt đầu tìm kiếm chuyên gia với tư cách đã đăng nhập.

---

## 4. Use Case 2: "Chat với AI"

**Pre-conditions (Điều kiện tiên quyết)**
- Dữ liệu Chuyên gia đã được nạp đầy đủ vào Google Sheets (Tên, Chuyên môn, Link Knowledge Base, Link Zalo).
- 
**Basic Flow (Luồng chính)**
1. **User**: Nhập câu hỏi vào khung chat (Ví dụ: "Tôi muốn tìm người hướng dẫn về AI và Machine Learning").
2. **Backend**: Gọi AI để phân tích **Chủ đề (Topic)** và **Nhu cầu nghiên cứu**.
3. **AI Engine**: Trích xuất các từ khóa chuyên môn (AI, ML).
4. **Backend**:
   - Quét danh sách Chuyên gia từ Google Sheets.
   - Lọc ra các Chuyên gia có chuyên môn khớp với từ khóa.
   - Ưu tiên các chuyên gia có Knowledge Base (NotebookLM) sẵn sàng.
5. **AI Engine**: Nhận ngữ cảnh về các Chuyên gia tìm được để soạn câu trả lời tư vấn:
   - "Chào bạn, mình tìm thấy Chuyên gia A rất giỏi về AI. Bạn có thể chat với Knowledge Base của anh ấy hoặc tham gia nhóm Zalo để trao đổi thêm."
6. **Backend**: Trả về Response gồm: Văn bản tư vấn + Danh sách Expert Cards (Thẻ chuyên gia).
7. **User**: Xem thông tin chuyên gia và chọn hành động tiếp theo.

**Alternative Flows (Luồng thay thế)**
- **A1. Tìm chuyên gia theo vị trí**: Nếu người dùng muốn gặp trực tiếp, hệ thống sẽ lọc chuyên gia gần vị trí của người dùng nhất.
- **A2. Không tìm thấy chuyên gia cụ thể**: AI sẽ đưa ra lời khuyên chung về lộ trình học tập và gợi ý các nguồn tài liệu liên quan.
- **A3. Tham gia cộng đồng**: Người dùng click "Tham gia cộng đồng" -> Ghi nhận Lead (Học viên tiềm năng) vào Google Sheets -> Chuyển hướng sang Zalo Group của chuyên gia.

**Post-conditions (Kết quả)**
- Người dùng kết nối được với nguồn tri thức phù hợp.
- Hệ thống ghi nhận được nhu cầu của học viên để chuyên gia có thể hỗ trợ sâu hơn.

Luồng chí tiết cho UC "Chat với AI ":
1. User nhập yêu cầu vào khung chat.
2. Hệ thống triển khai lấy yêu cầu của user chuẩn bị gọi AI với hệ thống prompt gồm
   2.1. Nội dung user nhập.
   2.2. Prompt đóng vai trợ lý truy cứu và cung cấp thông tin về các chuyên gia và đề tài nghiện cứu/học tập
   2.3. 1 bộ menu các lĩnh vựa của chuyên gia, 1 bộ menu các loại đề tài, 1 menu cho các intent 
   2.3. Yêu cầu trả về 1 json đẩm bảo: có đủ đầu ra cho 3 biến + các trường khác tùy nhà cung cấp api
3.Hệ thống call prompt tới LLM , tại đây LLM sẽ xử lý theo flow:
   3.1. LLM nhận ra yêu cầu từ user là lời chào, xin lỗi , cảm ơn, ... thể hiện cảm xúc.
      -> Trả biến Expert=false, Topic=false, Intent=[loại cảm xúc tương ứng trong menu intent] kèm theo câu trả lời tương ứng cho hệ thống theo cùng ngôn ngữ câu hỏi của user để hệ thống trả lời lại user.
   3.2. LLM nhận ra yêu cầu từ user là tìm kiếm thông tin chỉ về các chuyên gia.
      -> Trả biến Expert=[kinh nghiệm của chuyên gia trong menu kinh nghiệm], Topic=false, Intent=[loại tìm kiếm thông tin về chuyên gia trong menu intent].
      -> Hệ thống sẽ tìm kiếm thông tin về các chuyên gia từ Google Sheets và trả về 1 list các chuyên gia có cột chứa thông tin kinh nghiệm có chưa expert mà LLM vừa trả.
      ->  Hệ thống call LLM một lần nữa , gửi chính list dữ liệu chuyên gia trên và yêu cầu LLM thực hiện lọc dữ liệu 1 lần (loại bỏ dữ liệu lỗi ngữ nghĩa từ hệ thống) và trả về list đã lọc kèm theo 1 câu trả lời cho user bao gồm thông tin về chuyên gia được chọn một cách ngắn gọn.
      -> Hệ thống trả lời lại user thông qua chat bao gồm : message + Expert Card của các dữ liệu đã lọc.
      
         Chú ý : case này thẻ chuyên gia chứa all các topic họ phụ trách trong csdl.
   3.3. LLM nhận ra yêu cầu từ user là tìm kiếm thông tin chỉ về các đề tài
      -> Trả biến Expert=false, Topic=[tên topic phù hợp trong list menu], Intent=[loại tìm kiếm thông tin về đề tài trong menu intent].
      -> Hệ thống sẽ tìm kiếm thông tin về các đề tài từ Google Sheets và trả về 1 list các đề tài có cột chứa thông tin topic phù hợp mà LLM vừa trả.
      -> Hệ thống call LLM một lần nữa , gửi chính list dữ liệu đề tài trên và yêu cầu LLM thực hiện lọc dữ liệu 1 lần (loại bỏ dữ liệu lỗi ngữ nghĩa từ hệ thống) và trả về list đã lọc kèm theo 1 câu trả lời cho user bao gồm thông tin về đề tài được chọn một cách ngắn gọn.
      -> Hệ thống trả lời lại user thông qua chat bao gồm : message + Expert Card của các dữ liệu đã lọc.
         Chú ý :case này các expert card là lấy từ cột Expert_id trong list dữ liệu đã lọc; và trong expert card cũng chỉ hiện các đề tài họ phụ trách và có hiện diện trong list đã lọc.
         ** case này có độ phức tạp cao hơn case 3.2 nếu agent code đến đoạn này còn chưa rõ gì hãy hỏi lại người đang dùng thiết bị code nhé.  
   3.4. LLM nhận ra yêu cầu từ user là tra cứu vị trí của user:
      -> Trả luôn biến Expert=false, Topic=false, Intent=my_location.
      -> Hệ thống gọi api gg map lấy vị trí và trả lời user theo form có sẵn.
   3.5. LLM nhận ra user hỏi cả về chuyên gia và đề tài: (ví dụ: có biết ai giỏi về AI và bạn có sẵn chương trình hay tài liệu về AI hay không?)
      -> Thực hiện các bước như 3.2.
   3.6. LLM nhận ra user hỏi về chức năng hệ thống chat bot:
      -> Trả luôn biến Expert=false, Topic=false, Intent=help 
      -> Hệ thống trả lời lại bằng 1 mẫu câu soạn trước.
4. Các trường hợp ngoại lệ:
   4.1. LLM không map được Intent
      -> Hệ thống trả lời rằng chưa rõ ý của khách hàng, yêu càu hỏi lại.
   4.2. LLM không nhận diên được Expert dù intent là tìm chuyên gia
      -> Hệ thống trả lời rằng hiện tại chưa có sẵn thông tin về chuyên gia phù hợp với yêu cầu của khách hàng.
   4.3. LLM không nhận diên được Topic dù intent là tìm đề tài
      -> Hệ thống trả lời rằng hiện tại chưa có sẵn thông tin về đề tài phù hợp với yêu cầu của khách hàng.
   
##5. menu cho từng từ khóa:
Expert: menu được khởi tạo mỗi khi hệ thống khởi động
   -> Hệ thống lấy sheet về , trong cột kinh nghiệm thì có nhiều kinh nghiệm sẽ cách nhau bằng dấu phẩy
   -> Hệ thống gom dữ liệu cột chứa kinh nghiệm của các chuyên gia thành 1 list duy nhất(vẫn cho cách nhau bởi dấu phẩy+ lọc trùng)
   -> chuyển đổi list đó thành 1 dạng có thể gửi cho LLM được.

Topic : menu được khởi tạo mỗi khi hệ thống khởi động
   -> Hệ thống lấy sheet về , trong cột topic thì có nhiều topic sẽ cách nhau bằng dấu phẩy
   -> Hệ thống gom dữ liệu cột chứa topic của các chuyên gia thành 1 list duy nhất(vẫn cho cách nhau bởi dấu phẩy+ lọc trùng)
   -> chuyển đổi list đó thành 1 dạng có thể gửi cho LLM được.

Intent : menu được giới hạn bởi các kịch bản:
   -> Tìm kiếm thông tin về chuyên gia == Expert
   -> Tìm kiếm thông tin về đề tài == Topic
   -> Tìm kiếm thông tin về vị trí == my_location
   -> Tìm kiếm thông tin về cả chuyên gia và đề tài == Expert + Topic
   -> cảm xúc tiêu cực == angry
   -> cảm xúc cảm ơn == thank
   -> lời chào xã giao == hello.
   -> hỏi về chức năng của hệ thống == help


   
