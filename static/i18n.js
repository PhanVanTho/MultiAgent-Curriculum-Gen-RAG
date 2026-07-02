/**
 * i18n.js — Hệ thống đa ngôn ngữ VI/EN
 * Sử dụng: thêm data-i18n="key" vào element, gọi applyLanguage() khi load
 */

const TRANSLATIONS = {
  /* ===== NAVBAR (shared) ===== */
  'nav.intro':          { vi: 'Giới Thiệu',    en: 'About' },
  'nav.guide':          { vi: 'Hướng Dẫn',     en: 'Guide' },
  'nav.products':       { vi: 'Sản Phẩm',      en: 'Products' },
  'nav.pricing':        { vi: 'Bảng Giá',      en: 'Pricing' },
  'nav.history':        { vi: 'Lịch Sử',       en: 'History' },
  'nav.logout':         { vi: 'Đăng xuất',     en: 'Logout' },
  'nav.login':          { vi: 'Đăng nhập',     en: 'Sign In' },
  'nav.account':        { vi: 'Tài khoản',     en: 'Account' },
  'nav.create':         { vi: 'Tạo giáo trình', en: 'Create Curriculum' },

  /* ===== INDEX PAGE ===== */
  'index.hero.title':   { vi: 'Tại sao nên chọn Giáo Trình AI?', en: 'Why Choose AI Curriculum?' },
  'index.hero.desc':    { vi: 'Chúng tôi kết hợp trí tuệ nhân tạo tiên tiến với phương pháp sư phạm hiện đại để tạo ra một môi trường học tập cá nhân hóa, tối ưu hóa mọi tiềm năng của học viên.', en: 'We combine advanced artificial intelligence with modern pedagogical methods to create a personalized learning environment that optimizes every learner\'s potential.' },
  'index.hero.cta':     { vi: 'Tạo giáo trình ngay', en: 'Create Curriculum Now' },

  'index.feat1.title':  { vi: 'Biên soạn thần tốc',    en: 'Lightning-Fast Authoring' },
  'index.feat1.desc':   { vi: 'Thay vì tốn hàng tuần nghiên cứu, AI giúp bạn hoàn thiện một bộ giáo trình đầy đủ chỉ trong vài phút với độ chi tiết cực cao.', en: 'Instead of weeks of research, AI helps you complete a full curriculum in minutes with exceptional detail.' },
  'index.feat2.title':  { vi: 'Nghiên cứu đa tầng',    en: 'Multi-Layer Research' },
  'index.feat2.desc':   { vi: 'Công nghệ EKRE giúp tìm kiếm kiến thức đa nguồn, đảm bảo nội dung giáo trình có cơ sở khoa học và tính cập nhật mới nhất.', en: 'EKRE technology searches multi-source knowledge, ensuring curriculum content is scientifically grounded and up-to-date.' },
  'index.feat3.title':  { vi: 'Chế độ linh hoạt',      en: 'Flexible Modes' },
  'index.feat3.desc':   { vi: 'Tự do lựa chọn giữa chế độ Auto, Expert hoặc Creative để phù hợp với mọi nhu cầu sư phạm và phong cách giảng dạy.', en: 'Freely choose between Auto, Expert, or Creative mode to suit any pedagogical need and teaching style.' },
  'index.feat4.title':  { vi: 'Xuất bản chuyên nghiệp', en: 'Professional Publishing' },
  'index.feat4.desc':   { vi: 'Tự động chuyển đổi nội dung sang định dạng tài liệu chuẩn (Docx/PDF), sẵn sàng cho việc in ấn và giảng dạy ngay lập tức.', en: 'Automatically convert content to standard document formats (Docx/PDF), ready for immediate printing and teaching.' },

  'index.guide.title':  { vi: 'Hướng dẫn sử dụng', en: 'How to Use' },
  'index.guide.desc':   { vi: 'Bắt đầu hành trình nâng tầm giáo dục của bạn chỉ với 4 bước đơn giản, được thiết kế tối ưu cho mọi thiết bị.', en: 'Start your educational journey in just 4 simple steps, optimized for all devices.' },

  'index.step1.title':  { vi: 'Đăng nhập & Nạp Token', en: 'Login & Top Up Tokens' },
  'index.step1.desc':   { vi: 'Truy cập hệ thống và kiểm tra số dư Token để sẵn sàng cho hành trình biên soạn giáo trình thông minh.', en: 'Access the system and check your Token balance to get ready for intelligent curriculum creation.' },
  'index.step2.title':  { vi: 'Nhập chủ đề & Chọn chế độ', en: 'Enter Topic & Select Mode' },
  'index.step2.desc':   { vi: 'Nhập từ khóa môn học và lựa chọn chế độ biên soạn (Auto, Expert, Creative) phù hợp với mục tiêu của bạn.', en: 'Enter subject keywords and select the authoring mode (Auto, Expert, Creative) that fits your goals.' },
  'index.step3.title':  { vi: 'Biên soạn & Giám sát', en: 'Compose & Monitor' },
  'index.step3.desc':   { vi: 'AI thực hiện nghiên cứu đa nguồn và viết nội dung chi tiết từng chương dưới sự giám sát trực tiếp của bạn.', en: 'AI performs multi-source research and writes detailed content for each chapter under your direct supervision.' },
  'index.step4.title':  { vi: 'Xuất bản & Lưu trữ', en: 'Publish & Archive' },
  'index.step4.desc':   { vi: 'Xuất kết quả ra định dạng Docx/PDF chuyên nghiệp và lưu trữ vĩnh viễn trong thư viện cá nhân để giảng dạy.', en: 'Export results to professional Docx/PDF format and permanently store them in your personal library for teaching.' },

  'index.cta.title':    { vi: 'Sẵn sàng nâng tầm tri thức của bạn?', en: 'Ready to Elevate Your Knowledge?' },
  'index.cta.btn':      { vi: 'Bắt đầu ngay hôm nay', en: 'Get Started Today' },

  /* ===== SHOWCASE PAGE ===== */
  'showcase.title':     { vi: 'Sản Phẩm Tiêu Biểu', en: 'Featured Products' },
  'showcase.desc':      { vi: 'Khám phá các giáo trình chuyên sâu được hệ thống AI tự động tổng hợp và biên soạn từ những nguồn tài liệu học thuật uy tín nhất.', en: 'Explore in-depth curricula automatically synthesized and compiled by our AI system from the most reputable academic sources.' },
  'showcase.view':      { vi: 'Xem chi tiết', en: 'View Details' },
  'showcase.chapters':  { vi: 'chương', en: 'chapters' },
  'showcase.empty':     { vi: 'Chưa có sản phẩm nào được xuất bản.', en: 'No products published yet.' },
  'showcase.product_default_desc': { vi: 'Giáo trình được hệ thống Giáo Trình AI tổng hợp tự động với nội dung chi tiết, cập nhật và trình bày chuẩn học thuật.', en: 'Curriculum automatically compiled by the AI Curriculum system with detailed, updated content and scholarly presentation.' },
  'showcase.chapters_label': { vi: 'Chương', en: 'Chapters' },
  'showcase.accuracy_label': { vi: 'Chính xác', en: 'Accuracy' },
  'showcase.citations_label': { vi: 'Trích dẫn', en: 'Citations' },
  'showcase.view_curriculum': { vi: 'Xem giáo trình', en: 'View Curriculum' },
  'showcase.download_pdf': { vi: 'Tải Bản PDF', en: 'Download PDF' },
  'showcase.alert_title': { vi: 'Giáo trình mẫu', en: 'Sample Curriculum' },
  'showcase.alert_text': { vi: 'Đây là giáo trình mẫu để bạn tham khảo văn phong và cách trình bày của AI. Để tải file riêng của bạn, vui lòng sử dụng chức năng Tạo giáo trình.', en: 'This is a sample curriculum for style and layout reference. To download your own files, please use the Create Curriculum function.' },
  'showcase.alert_confirm': { vi: 'Tôi đã hiểu', en: 'Got it' },
  'showcase.prod1.badge': { vi: 'Khoa Học Máy Tính', en: 'Computer Science' },
  'showcase.prod1.title': { vi: 'Kiến Trúc Máy Tính & HĐH', en: 'Computer Architecture & OS' },
  'showcase.prod1.desc': { vi: 'Giáo trình chuyên sâu phân tích cấu trúc phần cứng, cách thức hoạt động của CPU, bộ nhớ, và nhân hệ điều hành Linux/Windows. Phù hợp cho sinh viên năm 2.', en: 'In-depth curriculum analyzing hardware architecture, CPU operations, memory, and Linux/Windows OS kernel. Suitable for sophomores.' },
  'showcase.prod2.badge': { vi: 'Kinh Tế Học', en: 'Economics' },
  'showcase.prod2.title': { vi: 'Kinh Tế Vĩ Mô Ứng Dụng', en: 'Applied Macroeconomics' },
  'showcase.prod2.desc': { vi: 'Tìm hiểu các mô hình tăng trưởng kinh tế, lạm phát, chính sách tiền tệ của ngân hàng trung ương và sự vận hành của nền kinh tế toàn cầu.', en: 'Learn about economic growth models, inflation, central bank monetary policy, and global economic operations.' },
  'showcase.prod3.badge': { vi: 'Y Khoa', en: 'Medicine' },
  'showcase.prod3.title': { vi: 'Sinh Lý Học Cơ Sở', en: 'Basic Physiology' },
  'showcase.prod3.desc': { vi: 'Tài liệu chi tiết về hoạt động chức năng của các cơ quan trong cơ thể người, từ tế bào đến hệ thống hô hấp, tuần hoàn, bài tiết và thần kinh.', en: 'Detailed material on functional activities of human organs, from cells to respiratory, circulatory, excretory, and nervous systems.' },

  /* ===== HISTORY PAGE ===== */
  'history.title':             { vi: 'Lịch sử giáo trình', en: 'Curriculum History' },
  'history.desc':              { vi: 'Xem lại các giáo trình đã tạo', en: 'Review your created curricula' },
  'history.empty':             { vi: 'Chưa có giáo trình nào.', en: 'No curricula yet.' },
  'history.empty.desc':        { vi: 'Hãy tạo giáo trình đầu tiên của bạn!', en: 'Create your first curriculum!' },
  'history.col.topic':         { vi: 'Chủ đề', en: 'Topic' },
  'history.col.date':          { vi: 'Ngày tạo', en: 'Date Created' },
  'history.col.status':        { vi: 'Trạng thái', en: 'Status' },
  'history.col.action':        { vi: 'Hành động', en: 'Actions' },
  'history.view':              { vi: 'Xem', en: 'View' },
  'history.delete':            { vi: 'Xóa', en: 'Delete' },
  'history.done':              { vi: 'Hoàn thành', en: 'Done' },
  'history.processing':        { vi: 'Đang chạy', en: 'Running' },
  'history.failed':            { vi: 'Thất bại', en: 'Failed' },
  'history.label':             { vi: 'Tài liệu đã tạo', en: 'Created Documents' },
  'history.badge_items':       { vi: 'mục', en: 'items' },
  'history.col_topic':         { vi: 'Chủ đề giáo trình', en: 'Curriculum Topic' },
  'history.col_time':          { vi: 'Thời gian', en: 'Time' },
  'history.col_status':        { vi: 'Trạng thái', en: 'Status' },
  'history.col_action':        { vi: 'Hành động', en: 'Actions' },
  'history.char_count':        { vi: 'ký tự', en: 'characters' },
  'history.step_label':        { vi: 'Bước', en: 'Step' },
  'history.error_label':       { vi: 'Lỗi', en: 'Error' },
  'history.btn_progress':      { vi: 'Tiến trình', en: 'Progress' },
  'history.btn_cancel':        { vi: 'Hủy', en: 'Cancel' },
  'history.btn_retry':         { vi: 'Thử lại', en: 'Retry' },
  'history.empty_title':       { vi: 'Chưa có giáo trình nào!', en: 'No curricula yet!' },
  'history.empty_desc':        { vi: 'Bạn chưa tạo giáo trình nào. Hãy bắt đầu ngay.', en: 'You haven\'t created any curricula. Start now.' },
  'history.empty_btn':         { vi: 'Tạo giáo trình mới', en: 'Create new curriculum' },
  'history.active_creating':   { vi: 'Đang tạo giáo trình...', en: 'Creating curriculum...' },
  'history.active_processing': { vi: 'Đang xử lý', en: 'Processing' },
  'history.active_view_progress':{ vi: 'Xem tiến trình', en: 'View Progress' },
  'history.confirm_cancel':    { vi: 'Bạn có chắc chắn muốn hủy tiến trình biên soạn này?', en: 'Are you sure you want to cancel this compilation process?' },
  'history.cancel_success':    { vi: 'Đã gửi yêu cầu hủy thành công.', en: 'Cancellation request sent successfully.' },
  'history.error_prefix':      { vi: 'Lỗi: ', en: 'Error: ' },
  'history.done_redirect':     { vi: 'Hoàn tất! Đang chuyển hướng...', en: 'Done! Redirecting...' },

  /* ===== PRICING PAGE ===== */
  'pricing.title':      { vi: 'Bảng Giá', en: 'Pricing' },
  'pricing.desc':       { vi: 'Chọn gói cước phù hợp với nhu cầu của bạn. Tỷ lệ quy đổi: 1.000 VND = 1 Token.\nNạp càng nhiều, ưu đãi càng lớn.', en: 'Choose the plan that fits your needs. Conversion rate: 1,000 VND = 1 Token.\nBuy more, get more discounts.' },
  'pricing.buy':        { vi: 'Mua ngay', en: 'Buy Now' },
  'pricing.popular':    { vi: 'Phổ biến nhất', en: 'Most Popular' },
  'pricing.tokens':     { vi: 'Token', en: 'Tokens' },
  'pricing.free.title': { vi: 'Miễn phí', en: 'Free' },
  'pricing.your_balance': { vi: 'Số dư hiện tại', en: 'Current Balance' },
  'pricing.receive_prefix': { vi: 'nhận', en: 'receive' },
  'pricing.feat_in_depth': { vi: 'Tạo giáo trình chuyên sâu', en: 'Create in-depth curricula' },
  'pricing.feat_priority': { vi: 'Tốc độ ưu tiên cao', en: 'High priority speed' },
  'pricing.feat_support':  { vi: 'Hỗ trợ 24/7', en: '24/7 support' },
  'pricing.buy_now':       { vi: 'Mua Ngay', en: 'Buy Now' },
  'pricing.modal_title':   { vi: 'Thanh toán nạp Token', en: 'Token Payment' },
  'pricing.modal_amount':  { vi: 'Số tiền cần thanh toán', en: 'Amount to Pay' },
  'pricing.modal_package': { vi: 'Gói cước', en: 'Package Plan' },
  'pricing.modal_desc':    { vi: 'Bạn sẽ được chuyển hướng sang cổng thanh toán VNPAY/SePay để thực hiện giao dịch an toàn.', en: 'You will be redirected to VNPAY/SePay to complete the secure payment transaction.' },
  'pricing.modal_method':  { vi: 'Chọn phương thức thanh toán', en: 'Select Payment Method' },
  'pricing.method_vnpay_title': { vi: 'Thanh toán qua VNPAY', en: 'Pay with VNPAY' },
  'pricing.method_vnpay_desc':  { vi: 'Hỗ trợ thẻ ATM nội địa, QR Code', en: 'Supports local ATM cards and QR Code' },
  'pricing.method_sepay_title': { vi: 'Chuyển khoản Ngân hàng (Tự động)', en: 'Bank Transfer (Automatic)' },
  'pricing.method_sepay_desc':  { vi: 'Quét mã QR VietQR, duyệt tự động 24/7 qua SePay', en: 'Scan VietQR, auto-processed 24/7 via SePay' },
  'pricing.modal_btn':          { vi: 'Tiến hành thanh toán', en: 'Proceed to Payment' },
  
  /* ===== SIDEBAR / ADMIN ===== */
  'nav.home':             { vi: 'Trang Chủ', en: 'Home' },
  'nav.overview':         { vi: 'Tổng Quan', en: 'Overview' },
  'nav.create':           { vi: 'Tạo Giáo Trình', en: 'Create Curriculum' },
  'nav.pricing':          { vi: 'Gói Cước', en: 'Pricing' },
  'nav.history':          { vi: 'Lịch Sử', en: 'History' },
  'nav.logo':             { vi: 'Giáo Trình AI', en: 'AI Curriculum' },
  'nav.logout':           { vi: 'Đăng xuất', en: 'Logout' },
  'nav.admin_dashboard':  { vi: 'Dashboard Quản trị', en: 'Admin Dashboard' },
  'nav.admin_curriculums': { vi: 'Quản lý giáo trình', en: 'Manage Curricula' },
  
  
  /* ===== PACKAGE NAMES & FEATURES (Dynamic support) ===== */
  'Gói Đồng':           { vi: 'Gói Đồng', en: 'Bronze Plan' },
  'Gói Bạc':            { vi: 'Gói Bạc', en: 'Silver Plan' },
  'Gói Vàng':           { vi: 'Gói Vàng', en: 'Gold Plan' },
  'Gói Kim Cương':       { vi: 'Gói Kim Cương', en: 'Diamond Plan' },
  'Tạo giáo trình tối đa 5 chương': { vi: 'Tạo giáo trình tối đa 5 chương', en: 'Create curricula up to 5 chapters' },
  'Tạo giáo trình tối đa 10 chương': { vi: 'Tạo giáo trình tối đa 10 chương', en: 'Create curricula up to 10 chapters' },
  'Tạo giáo trình tối đa 15 chương': { vi: 'Tạo giáo trình tối đa 15 chương', en: 'Create curricula up to 15 chapters' },
  'Hỗ trợ xuất PDF/Word/MD': { vi: 'Hỗ trợ xuất PDF/Word/MD', en: 'Export to PDF/Word/MD supported' },
  'Hỗ trợ chế độ Expert': { vi: 'Hỗ trợ chế độ Expert', en: 'Expert mode supported' },
  'Tốc độ biên soạn trung bình': { vi: 'Tốc độ biên soạn trung bình', en: 'Standard compile speed' },
  'Tốc độ biên soạn nhanh': { vi: 'Tốc độ biên soạn nhanh', en: 'Fast compile speed' },
  'Tốc độ biên soạn ưu tiên': { vi: 'Tốc độ biên soạn ưu tiên', en: 'Priority compile speed' },

  /* ===== PROFILE PAGE ===== */
  /* ===== PROFILE PAGE ===== */
  'profile.title':      { vi: 'Hồ sơ cá nhân', en: 'My Profile' },
  'profile.edit':       { vi: 'Chỉnh sửa hồ sơ', en: 'Edit Profile' },
  'profile.tab.info':   { vi: 'Thông tin cá nhân', en: 'Personal Info' },
  'profile.tab.pw':     { vi: 'Đổi mật khẩu', en: 'Change Password' },
  'profile.name':       { vi: 'Họ và tên', en: 'Full Name' },
  'profile.email':      { vi: 'Địa chỉ email', en: 'Email Address' },
  'profile.username':   { vi: 'Tên đăng nhập', en: 'Username' },
  'profile.pw.current': { vi: 'Mật khẩu hiện tại', en: 'Current Password' },
  'profile.pw.new':     { vi: 'Mật khẩu mới', en: 'New Password' },
  'profile.pw.confirm': { vi: 'Xác nhận mật khẩu mới', en: 'Confirm New Password' },
  'profile.save':       { vi: 'Lưu thay đổi', en: 'Save Changes' },
  'profile.cancel':     { vi: 'Hủy bỏ', en: 'Cancel' },
  'profile.joined':     { vi: 'Ngày tham gia', en: 'Joined' },
  'profile.balance':    { vi: 'Số dư Token', en: 'Token Balance' },
  'profile.curriculums': { vi: 'Giáo trình đã tạo', en: 'Curricula Created' },
  'profile.status.active': { vi: 'Hoạt động', en: 'Active' },
  'profile.verify_email_note': { vi: 'Thay đổi email cần xác thực OTP', en: 'Email change requires OTP verification' },
  'profile.credits':    { vi: 'Credits', en: 'Credits' },
  'profile.welcome':    { vi: 'Chào mừng trở lại', en: 'Welcome back' },
  'profile.welcome_sub': { vi: 'Hôm nay bạn muốn biên soạn giáo trình gì?', en: 'What curriculum would you like to compile today?' },
  'profile.create_btn': { vi: 'Tạo Giáo Trình Mới', en: 'Create New Curriculum' },
  'profile.stat_balance': { vi: 'Số dư hiện tại', en: 'Current Balance' },
  'profile.stat_created': { vi: 'Giáo trình đã tạo', en: 'Curricula Created' },
  'profile.stat_spent':   { vi: 'Tổng chi tiêu', en: 'Total Spent' },
  'profile.quick_actions': { vi: 'Thao tác nhanh', en: 'Quick Actions' },
  'profile.act_buy':    { vi: 'Mua Token', en: 'Buy Tokens' },
  'profile.act_buy_desc': { vi: 'Nạp thêm vào tài khoản', en: 'Add credits to your account' },
  'profile.act_history': { vi: 'Xem Lịch Sử', en: 'View History' },
  'profile.act_history_desc': { vi: 'Xem lại các giáo trình đã tạo', en: 'Review your created curricula' },
  'profile.edit_title': { vi: 'Chỉnh sửa hồ sơ', en: 'Edit Profile' },
  'profile.change_avatar': { vi: 'Thay đổi', en: 'Change' },
  'profile.tab_info':   { vi: 'Thông tin cá nhân', en: 'Personal Info' },
  'profile.tab_security': { vi: 'Đổi mật khẩu', en: 'Change Password' },
  'profile.label_fullname': { vi: 'Họ và tên', en: 'Full Name' },
  'profile.label_username': { vi: 'Tên đăng nhập', en: 'Username' },
  'profile.label_email': { vi: 'Địa chỉ Email', en: 'Email Address' },
  'profile.email_change_note': { vi: 'Lưu ý: Nếu thay đổi Email, hệ thống sẽ gửi một mã OTP xác thực tới Email mới của bạn để xác nhận.', en: 'Note: If you change your email, the system will send a verification OTP to your new email to confirm.' },
  'profile.label_pw_old': { vi: 'Mật khẩu hiện tại', en: 'Current Password' },
  'profile.google_pw_note': { vi: 'Tài khoản của bạn được liên kết qua Google và chưa thiết lập mật khẩu trực tiếp. Bạn có thể đặt mật khẩu mới ngay tại đây.', en: 'Your account is linked via Google and has no direct password. You can set a new password here.' },
  'profile.label_pw_new': { vi: 'Mật khẩu mới', en: 'New Password' },
  'profile.label_pw_confirm': { vi: 'Xác nhận mật khẩu mới', en: 'Confirm New Password' },
  'profile.pw_mismatch': { vi: 'Mật khẩu mới không trùng khớp.', en: 'Passwords do not match.' },
  'profile.btn_cancel': { vi: 'Hủy bỏ', en: 'Cancel' },
  'profile.btn_save':   { vi: 'Lưu thay đổi', en: 'Save Changes' },
  'profile.no_email':   { vi: 'Chưa cập nhật email', en: 'Email not updated' },

  /* ===== LOGIN PAGE ===== */
  'login.title':        { vi: 'Đăng nhập', en: 'Sign In' },
  'login.subtitle':     { vi: 'Chào mừng trở lại!', en: 'Welcome back!' },
  'login.username':     { vi: 'Tên đăng nhập', en: 'Username' },
  'login.password':     { vi: 'Mật khẩu', en: 'Password' },
  'login.forgot':       { vi: 'Quên mật khẩu?', en: 'Forgot password?' },
  'login.btn':          { vi: 'Đăng nhập', en: 'Sign In' },
  'login.no_account':   { vi: 'Chưa có tài khoản?', en: 'No account yet?' },
  'login.register':     { vi: 'Đăng ký ngay', en: 'Register now' },
  'login.or':           { vi: 'hoặc đăng nhập bằng', en: 'or sign in with' },

  /* ===== REGISTER PAGE ===== */
  'register.title':     { vi: 'Tạo tài khoản mới', en: 'Create New Account' },
  'register.subtitle':  { vi: 'Đăng ký để bắt đầu sử dụng hệ thống', en: 'Register to start using the system' },
  'register.username':  { vi: 'Tên đăng nhập', en: 'Username' },
  'register.email':     { vi: 'Địa chỉ email', en: 'Email Address' },
  'register.password':  { vi: 'Mật khẩu', en: 'Password' },
  'register.confirm_pw': { vi: 'Nhập lại mật khẩu', en: 'Confirm Password' },
  'register.btn':       { vi: 'Đăng ký', en: 'Register' },
  'register.have_account': { vi: 'Đã có tài khoản?', en: 'Already have an account?' },
  'register.login':     { vi: 'Đăng nhập ngay', en: 'Sign in now' },
  'register.or':        { vi: 'hoặc đăng ký bằng tài khoản', en: 'or register with' },

  /* ===== FORGOT PASSWORD PAGE ===== */
  'forgot.title':       { vi: 'Quên mật khẩu', en: 'Forgot Password' },
  'forgot.desc':        { vi: 'Nhập email để nhận mã OTP đặt lại mật khẩu', en: 'Enter your email to receive a password reset OTP' },
  'forgot.email':       { vi: 'Địa chỉ email', en: 'Email Address' },
  'forgot.btn':         { vi: 'Gửi mã OTP', en: 'Send OTP' },
  'forgot.back':        { vi: 'Quay lại Đăng nhập', en: 'Back to Sign In' },

  /* ===== RESET PASSWORD PAGE ===== */
  'reset.title':        { vi: 'Đặt lại mật khẩu', en: 'Reset Password' },
  'reset.otp':          { vi: 'Mã xác thực OTP (6 chữ số)', en: 'OTP Verification Code (6 digits)' },
  'reset.pw_new':       { vi: 'Mật khẩu mới', en: 'New Password' },
  'reset.pw_confirm':   { vi: 'Xác nhận mật khẩu mới', en: 'Confirm New Password' },
  'reset.btn':          { vi: 'Đặt lại mật khẩu', en: 'Reset Password' },
  'reset.back':         { vi: 'Quay lại Nhận OTP', en: 'Back to OTP Request' },

  /* ===== RESULT PAGE ===== */
  'result.download_docx': { vi: 'Tải DOCX', en: 'Download DOCX' },
  'result.download_pdf':  { vi: 'Tải PDF',  en: 'Download PDF' },
  'result.download_md':   { vi: 'Tải MD',   en: 'Download MD' },
  'result.back':          { vi: 'Tạo mới',  en: 'Create New' },
  'result.share':         { vi: 'Chia sẻ',  en: 'Share' },
  'result.toc':           { vi: 'Mục Lục',  en: 'Table of Contents' },
  'result.references':    { vi: 'Tài liệu tham khảo', en: 'References' },
  'result.error_title':   { vi: 'Rất tiếc, đã xảy ra lỗi!', en: 'Oops, an error occurred!' },
  'result.chapter_prefix': { vi: 'Chương', en: 'Chapter' },
  'result.cover_label':   { vi: 'Giáo trình Đại học', en: 'University Curriculum' },
  'result.cover_subtitle': { vi: 'Biên soạn tự động bởi Hệ thống AI Data Aggregator', en: 'Automatically compiled by AI Data Aggregator System' },
  'result.chapters_suffix': { vi: 'Chương', en: 'Chapters' },
  'result.citation_format': { vi: 'Định dạng trích dẫn:', en: 'Citation Format:' },
  'result.sources_suffix': { vi: 'nguồn', en: 'sources' },
  'result.no_references': { vi: 'Không có dữ liệu nguồn chi tiết.', en: 'No detailed source references found.' },
  'result.summaries_title': { vi: 'Tóm tắt các chương', en: 'Chapter Summaries' },
  'result.export_docx':    { vi: 'Xuất file (.docx)', en: 'Export (.docx)' },
  'result.no_summary':    { vi: 'Chưa có tóm tắt cho chương này.', en: 'No summary available for this chapter.' },
  'result.glossary_title': { vi: 'Bảng thuật ngữ toàn tập', en: 'Comprehensive Glossary' },
  'result.total_prefix':  { vi: 'Tổng cộng', en: 'Total of' },
  'result.total_suffix':  { vi: 'thuật ngữ trong toàn bộ giáo trình', en: 'terms across the entire curriculum' },
  'result.no_glossary':   { vi: 'Chưa có dữ liệu bảng thuật ngữ.', en: 'No glossary data available.' },
  'result.download_title': { vi: 'Tải xuống giáo trình', en: 'Download Curriculum' },
  'result.docx_label':     { vi: 'Word (.docx)', en: 'Word (.docx)' },
  'result.pdf_label':      { vi: 'PDF (.pdf)', en: 'PDF (.pdf)' },
  'result.zip_label':      { vi: 'Gói tất cả (Word & PDF)', en: 'Zip Package (Word & PDF)' },
  'result.tech_details_btn': { vi: 'Chi tiết kỹ thuật AI', en: 'AI Technical Details' },
  'result.download_clean_title': { vi: 'Tải xuống (Bản sạch)', en: 'Download (Clean copy)' },
  'result.download_clean_desc':  { vi: 'Phiên bản không đính kèm trích dẫn nguồn APA.', en: 'Version without APA citation anchors.' },
  'result.docx_clean_label':     { vi: 'Word sạch (.docx)', en: 'Clean Word (.docx)' },
  'result.pdf_clean_label':      { vi: 'PDF sạch (.pdf)', en: 'Clean PDF (.pdf)' },
  'result.zip_clean_label':      { vi: 'Gói bản sạch (.zip)', en: 'Clean Zip (.zip)' },
  'result.view_mode_title':      { vi: 'Chế độ xem', en: 'View Mode' },
  'result.view_content':         { vi: 'Nội dung giáo trình', en: 'Curriculum Content' },
  'result.view_summaries':       { vi: 'Tóm tắt các chương', en: 'Chapter Summaries' },
  'result.view_glossary':        { vi: 'Bảng thuật ngữ', en: 'Glossary' },
  'result.scale_warning_title':  { vi: '⚠️ Cảnh báo quy mô giáo trình', en: '⚠️ Curriculum Scale Warning' },
  'result.scale_warning_desc':   { vi: 'Quy mô thực tế chưa đạt hoàn toàn so với mức lựa chọn ban đầu do nguồn tư liệu Wikipedia bị giới hạn hoặc thiếu tính tương thích học thuật sâu sắc. Tuy nhiên, hệ thống đã nỗ lực biên soạn và đóng gói phiên bản tối ưu nhất dưới đây.', en: 'The actual curriculum scale did not fully meet the initial setting due to limited source materials on Wikipedia or lack of deeper academic compatibility. However, the system has successfully compiled and packaged the best possible version below.' },
  'result.scale_warning_detail': { vi: 'Chi tiết đánh giá của AI Supervisor:', en: 'AI Supervisor Evaluation Details:' },
  'result.scale_warning_coverage': { vi: 'Độ bao phủ:', en: 'Coverage:' },
  'result.scale_warning_density': { vi: 'Độ đậm đặc:', en: 'Density:' },
  'result.scale_warning_length':  { vi: 'Độ dài trang:', en: 'Page Length:' },
  'result.scale_warning_expected': { vi: 'yêu cầu tối thiểu', en: 'minimum required' },
  'result.scale_warning_pages':   { vi: 'trang', en: 'pages' },
  'result.scale_warning_missing_topics': { vi: 'Chủ đề còn thiếu khuyến nghị tìm thêm:', en: 'Missing topics recommended for further research:' },
  
  /* ===== TECHNICALtransparency MODAL ===== */
  'tech.modal_title':      { vi: 'AI Analytics & Transparency Dashboard', en: 'AI Analytics & Transparency Dashboard' },
  'tech.tab_journal':      { vi: 'Nhật ký AI', en: 'AI Compilation Log' },
  'tech.tab_terms':        { vi: 'Thuật ngữ (Glossary)', en: 'Glossary & Terms' },
  'tech.tab_sources':      { vi: 'Nguồn tri thức', en: 'Knowledge Sources' },
  'tech.tab_grounding':    { vi: 'Grounding Score', en: 'Grounding Score' },
  'tech.no_journal':       { vi: 'Không có dữ liệu tiến trình chi tiết.', en: 'No detailed process log available.' },
  'tech.terms_desc':       { vi: 'thuật ngữ với định nghĩa học thuật', en: 'terms with academic definitions' },
  'tech.no_terms':         { vi: 'Không tìm thấy danh sách thuật ngữ.', en: 'No terms list found.' },
  'tech.sources_desc':     { vi: 'nguồn tri thức được sử dụng — sắp xếp theo điểm chất lượng', en: 'knowledge sources used — sorted by quality score' },
  'tech.quality_good':     { vi: '🟢 Quality ≥ 1.5 (Tốt)', en: '🟢 Quality ≥ 1.5 (Good)' },
  'tech.quality_medium':   { vi: '🟡 Quality 0.5–1.5 (Trung bình)', en: '🟡 Quality 0.5–1.5 (Medium)' },
  'tech.quality_weak':     { vi: '🔴 Quality < 0.5 (Yếu)', en: '🔴 Quality < 0.5 (Weak)' },
  'tech.col_source':       { vi: 'Nguồn', en: 'Source' },
  'tech.col_length':       { vi: 'Độ dài', en: 'Length' },
  'tech.no_discovery':     { vi: 'Chưa lưu dữ liệu Discovery log.', en: 'Discovery log not saved yet.' },
  'tech.grounded':         { vi: 'Grounded', en: 'Grounded' },
  'tech.grounding_reliable': { vi: '🔬 Đáng tin cậy', en: '🔬 Highly Reliable' },
  'tech.grounding_medium':   { vi: '⚠️ Trung bình', en: '⚠️ Moderately Reliable' },
  'tech.grounding_poor':     { vi: '🔴 Cần cải thiện', en: '🔴 Needs Improvement' },
  'tech.grounded_desc':      { vi: 'đoạn có nguồn trích dẫn', en: 'paragraphs with source citations' },
  'tech.grounding_detail_title': { vi: 'Chi tiết theo chương', en: 'Detail by Chapter' },
  'tech.col_chapter':        { vi: 'Chương', en: 'Chapter' },
  'tech.col_total_paras':    { vi: 'Tổng đoạn', en: 'Total Paras' },
  'tech.col_grounded_paras': { vi: 'Có nguồn', en: 'Grounded' },
  'tech.col_ratio':          { vi: 'Tỷ lệ', en: 'Ratio' },
  'tech.col_rating':         { vi: 'Đánh giá', en: 'Rating' },
  'tech.no_grounding':       { vi: 'Chưa có dữ liệu Grounding Score.', en: 'No Grounding Score data available.' },
  'tech.btn_close':          { vi: 'Đóng', en: 'Close' },
  
  /* ===== FOOTER ===== */
  'footer.policy':           { vi: 'Chính sách bảo mật', en: 'Privacy Policy' },
  'footer.terms':            { vi: 'Điều khoản dịch vụ', en: 'Terms of Service' },
  'footer.ai_terms':         { vi: 'Điều khoản AI', en: 'AI Terms' },
  'footer.data_deletion':    { vi: 'Chính sách xóa dữ liệu', en: 'Data Deletion Policy' },
  'footer.support_faq':      { vi: 'Hỗ trợ & FAQs', en: 'Support & FAQs' },
  'footer.xoa_tai_khoan':    { vi: 'Yêu cầu xóa tài khoản', en: 'Request Account Deletion' },
  'footer.tagline':          { vi: 'Hệ thống biên soạn giáo trình tự động', en: 'Automated Curriculum Compilation System' },
  'footer.desc':             { vi: 'Hệ thống biên soạn giáo trình thông minh bằng trí tuệ nhân tạo, kết hợp nghiên cứu khoa học đa tầng và phương pháp sư phạm hiện đại.', en: 'Intelligent curriculum compilation system powered by AI, combining multi-layer scientific research and modern pedagogy.' },
  'footer.col_explore':      { vi: 'Khám Phá', en: 'Explore' },
  'footer.col_support':      { vi: 'Hỗ Trợ & Pháp Lý', en: 'Support & Legal' },
  'footer.col_contact':      { vi: 'Liên Hệ', en: 'Contact Us' },
  'footer.home':             { vi: 'Trang chủ', en: 'Home' },
  'footer.showcase':         { vi: 'Sản phẩm tiêu biểu', en: 'Featured Products' },
  'footer.guide':            { vi: 'Hướng dẫn', en: 'Guide' },
  'footer.pricing':          { vi: 'Gói cước', en: 'Pricing' },
  'footer.faqs':             { vi: 'Câu hỏi thường gặp', en: 'FAQs' },
  'footer.contact_support':  { vi: 'Liên hệ hỗ trợ', en: 'Contact Support' },
  'footer.email_val':        { vi: 'phanvantho082019@gmail.com', en: 'phanvantho082019@gmail.com' },
  'footer.phone_val':        { vi: '0327152710', en: '0327152710' },
  'footer.address_val':      { vi: 'Cần Thơ, Việt Nam', en: 'Can Tho, Vietnam' },

  /* ===== DELETE ACCOUNT REQUEST PAGE ===== */
  'delete_account.title':            { vi: 'Yêu cầu xóa tài khoản', en: 'Account Deletion Request' },
  'delete_account.desc':             { vi: 'Vui lòng cung cấp thông tin tài khoản của bạn. Yêu cầu của bạn sẽ được gửi tới Ban quản trị hệ thống để xử lý.', en: 'Please provide your account details. Your request will be sent to the System Administrator for processing.' },
  'delete_account.username':         { vi: 'Tên đăng nhập', en: 'Username' },
  'delete_account.email':            { vi: 'Email đăng ký', en: 'Registered Email' },
  'delete_account.reason':           { vi: 'Lý do yêu cầu xóa', en: 'Reason for deletion' },
  'delete_account.reason_select':    { vi: '--- Chọn lý do ---', en: '--- Select a reason ---' },
  'delete_account.reason_1':         { vi: 'Không còn nhu cầu sử dụng', en: 'No longer needed' },
  'delete_account.reason_2':         { vi: 'Lý do bảo mật dữ liệu', en: 'Data privacy concerns' },
  'delete_account.reason_3':         { vi: 'Gặp sự cố kỹ thuật', en: 'Technical issues' },
  'delete_account.reason_4':         { vi: 'Lý do khác', en: 'Other' },
  'delete_account.notes':            { vi: 'Chi tiết yêu cầu / Ghi chú thêm', en: 'Detailed Request / Additional Notes' },
  'delete_account.notes_placeholder': { vi: 'Nhập thông tin chi tiết hoặc lý do cụ thể (nếu có)...', en: 'Enter detailed information or specific reason (if any)...' },
  'delete_account.submit':           { vi: 'Gửi yêu cầu xóa tài khoản', en: 'Submit Deletion Request' },
  'delete_account.back_home':        { vi: 'Quay lại Trang chủ', en: 'Back to Home' },
  'delete_account.alert_warn':       { vi: 'Hành động này không thể hoàn tác sau khi được Admin phê duyệt. Vui lòng cân nhắc kỹ.', en: 'This action cannot be undone once approved by the Admin. Please consider carefully.' },


  /* ===== APP CONFIG PAGE ===== */
  'app.title':            { vi: 'Thiết lập giáo trình', en: 'Curriculum Setup' },
  'app.subtitle':         { vi: 'Cấu hình các tham số để AI bắt đầu biên soạn.', en: 'Configure parameters for AI compilation.' },
  'app.ai_params':        { vi: 'Thông số AI', en: 'AI Parameters' },
  'app.label_topic':      { vi: 'Chủ đề giáo trình', en: 'Curriculum Topic' },
  'app.placeholder_topic':{ vi: 'Ví dụ: Cơ học lượng tử, Kinh tế vĩ mô nâng cao...', en: 'E.g., Quantum mechanics, Advanced macroeconomics...' },
  'app.label_output_lang':{ vi: 'Ngôn ngữ đầu ra', en: 'Output Language' },
  'app.label_mode':       { vi: 'Chế độ biên soạn', en: 'Compilation Mode' },
  'app.mode_auto_desc':   { vi: 'Tự động hoàn toàn', en: 'Fully automatic' },
  'app.mode_expert_desc': { vi: 'Chuyên gia audit', en: 'Expert audit' },
  'app.mode_creative_desc':{ vi: 'Sáng tạo nội dung', en: 'Content creation' },
  'app.scale':            { vi: 'QUY MÔ GIÁO TRÌNH', en: 'CURRICULUM SCALE' },
  'app.scale_basic':      { vi: 'Căn bản', en: 'Basic' },
  'app.scale_standard':   { vi: 'Tiêu chuẩn', en: 'Standard' },
  'app.scale_advanced':   { vi: 'Chuyên sâu', en: 'Advanced' },
  'app.scale_basic_desc': { vi: '3-6 chương. Tóm tắt cốt lõi, nhanh chóng.', en: '3-6 chapters. Core summary, quick.' },
  'app.scale_standard_desc':{ vi: '7-10 chương. Chuẩn đại học, đầy đủ kiến thức.', en: '7-10 chapters. College level, comprehensive.' },
  'app.scale_advanced_desc':{ vi: '11-14 chương. Nghiên cứu sâu, học thuật.', en: '11-14 chapters. Deep research, academic.' },
  'app.advanced_toggle':  { vi: 'Cấu hình nâng cao (Tùy chọn số chương & Tên chương)', en: 'Advanced Settings (Optional chapter count & names)' },
  'app.chapters_count':   { vi: 'Số lượng chương', en: 'Number of Chapters' },
  'app.chapters_hint':    { vi: 'Nhập số chương mong muốn (3-15). Để trống để tự động phân tích quy mô.', en: 'Enter desired chapters (3-15). Leave blank to auto-detect by scale.' },
  'app.chapter_names':    { vi: 'Tên các chương (Tùy chọn)', en: 'Chapter Names (Optional)' },
  'app.section_words_help': { vi: '(Số từ tối thiểu áp dụng cho mỗi mục con cấp 2 của chương, ví dụ: mục 1.1, 1.2)', en: '(Minimum word count applied to each level 2 subsection/topic in a chapter, e.g. section 1.1, 1.2)' },
  'app.approve_outline': { vi: 'Tôi muốn duyệt dàn ý chi tiết trước khi sinh nội dung', en: 'Review detailed outline before generating content' },
  'app.approve_outline_title': { vi: 'Duyệt dàn ý chi tiết', en: 'Review Detailed Outline' },
  'app.approve_outline_desc': { vi: 'Đánh dấu chọn các mục con cấp 2 bạn muốn giữ lại để viết nội dung:', en: 'Select the level 2 sections you want to keep for content generation:' },
  'app.btn_approve_outline': { vi: 'Tiến hành viết', en: 'Proceed to Write' },
  'app.btn_submit':       { vi: 'KHỞI TẠO GIÁO TRÌNH', en: 'INITIALIZE CURRICULUM' },

  /* ===== VERIFY EMAIL CHANGE & OTP ===== */
  'verify.email_title':        { vi: 'Xác nhận Thay đổi Email', en: 'Verify Email Change' },
  'verify.email_subtitle':     { vi: 'Mã xác thực đã được gửi tới email mới', en: 'A verification code has been sent to your new email' },
  'verify.otp_title':          { vi: 'Xác thực tài khoản', en: 'Verify Account' },
  'verify.otp_subtitle':       { vi: 'Mã xác thực đã được gửi tới email', en: 'A verification code has been sent to your email' },
  'verify.otp_label':          { vi: 'Nhập mã OTP (6 chữ số)', en: 'Enter OTP (6 digits)' },
  'verify.btn_confirm_change': { vi: 'Xác nhận thay đổi', en: 'Confirm Change' },
  'verify.btn_confirm_account':{ vi: 'Xác nhận tài khoản', en: 'Confirm Account' },
  'verify.back_profile':       { vi: 'Hủy & Quay lại Hồ sơ', en: 'Cancel & Back to Profile' },
  'verify.back_register':      { vi: 'Quay lại Đăng ký', en: 'Back to Register' },
  'verify.resend_otp':         { vi: 'Gửi lại mã OTP', en: 'Resend OTP' },
  'verify.policy':             { vi: 'Chính sách', en: 'Policy' },
  'verify.terms':              { vi: 'Điều khoản', en: 'Terms' },
  'verify.support':            { vi: 'Hỗ trợ', en: 'Support' },

  /* ===== PAYMENTS ===== */
  'pay.success_title':         { vi: 'Thành công!', en: 'Success!' },
  'pay.success_desc':          { vi: 'Cảm ơn bạn. Giao dịch nạp token của bạn đã được hoàn tất thành công.', en: 'Thank you. Your token purchase has been successfully completed.' },
  'pay.failed_title':          { vi: 'Giao dịch thất bại!', en: 'Transaction Failed!' },
  'pay.failed_desc':           { vi: 'Rất tiếc. Đã xảy ra lỗi hoặc giao dịch nạp tiền của bạn đã bị hủy bỏ từ phía khách hàng.', en: 'Sorry. An error occurred or your transaction was cancelled.' },
  'pay.error_detail':          { vi: 'Chi tiết lỗi', en: 'Error Detail' },
  'pay.tx_id':                 { vi: 'Mã giao dịch', en: 'Transaction ID' },
  'pay.amount':                { vi: 'Số tiền', en: 'Amount' },
  'pay.gateway':               { vi: 'Cổng thanh toán', en: 'Payment Gateway' },
  'pay.tokens_received':       { vi: 'Số Token đã nhận', en: 'Tokens Received' },
  'pay.back_profile':          { vi: 'Quay lại Trang cá nhân', en: 'Back to My Profile' },
  'pay.retry':                 { vi: 'Thực hiện lại giao dịch', en: 'Retry Transaction' },
  'pay.cancel_profile':        { vi: 'Hủy và quay về trang cá nhân', en: 'Cancel and return to profile' },
  'pay.checkout_title':        { vi: 'Thanh Toán Nạp Token', en: 'Token Payment' },
  'pay.checkout_subtitle':     { vi: 'Quét mã QR để chuyển khoản', en: 'Scan QR code to transfer' },
  'pay.bank':                  { vi: 'Ngân hàng', en: 'Bank' },
  'pay.account_number':        { vi: 'Số tài khoản', en: 'Account Number' },
  'pay.transfer_content':      { vi: 'Nội dung chuyển khoản', en: 'Transfer Content' },
  'pay.waiting':               { vi: 'Đang chờ thanh toán... Hệ thống sẽ tự động xác nhận trong ít phút.', en: 'Waiting for payment... The system will automatically confirm in a few minutes.' },
  'pay.cancel_back':           { vi: 'Hủy giao dịch & Quay lại', en: 'Cancel & Go Back' },

  /* ===== SIDEBAR / COMMON ===== */
  'sidebar.create':     { vi: 'Tạo Giáo Trình', en: 'Create Curriculum' },
  'sidebar.history':    { vi: 'Lịch Sử',         en: 'History' },
  'sidebar.profile':    { vi: 'Hồ Sơ',           en: 'Profile' },
  'sidebar.pricing':    { vi: 'Nâng Cấp',         en: 'Upgrade' },
  'sidebar.logout':     { vi: 'Đăng Xuất',        en: 'Logout' },

  /* ===== FOOTER ===== */
  'footer.copy':        { vi: '© 2026 GIÁO TRÌNH AI. THE INTELLECTUAL LIGHT.', en: '© 2026 AI CURRICULUM. THE INTELLECTUAL LIGHT.' },
  'footer.ai_terms':    { vi: 'Điều khoản AI', en: 'AI Terms' },


  /* ===== AUTH / LOGIN / REGISTER / FORGOT / RESET ===== */
  'login.page_title':      { vi: 'Đăng nhập - Giáo Trình AI', en: 'Sign In - AI Curriculum' },
  'login.title':           { vi: 'Chào mừng trở lại', en: 'Welcome Back' },
  'login.subtitle':        { vi: 'Đăng nhập để sử dụng hệ thống tạo giáo trình', en: 'Sign in to use the curriculum creation system' },
  'login.username':        { vi: 'Tên đăng nhập', en: 'Username' },
  'login.username_placeholder': { vi: 'Nhập tên đăng nhập', en: 'Enter username' },
  'login.password':        { vi: 'Mật khẩu', en: 'Password' },
  'login.forgot':          { vi: 'Quên mật khẩu?', en: 'Forgot Password?' },
  'login.btn':             { vi: 'Đăng nhập', en: 'Sign In' },
  'login.no_account':      { vi: 'Chưa có tài khoản?', en: 'Don\'t have an account?' },
  'login.register':        { vi: 'Đăng ký ngay', en: 'Register now' },
  'login.or':              { vi: 'hoặc đăng nhập bằng tài khoản', en: 'or sign in with account' },
  'register.google_loading': { vi: 'Đang xử lý...', en: 'Processing...' },

  'register.page_title':   { vi: 'Đăng ký - Giáo Trình AI', en: 'Register - AI Curriculum' },
  'register.title':        { vi: 'Tạo tài khoản mới', en: 'Create New Account' },
  'register.subtitle':     { vi: 'Hệ thống biên soạn giáo trình tự động', en: 'Automated Curriculum Compilation System' },
  'register.username':     { vi: 'Tên đăng nhập', en: 'Username' },
  'register.username_placeholder': { vi: 'Tối thiểu 3 ký tự', en: 'Min 3 characters' },
  'register.email':        { vi: 'Địa chỉ email', en: 'Email Address' },
  'register.password':     { vi: 'Mật khẩu', en: 'Password' },
  'register.password_placeholder': { vi: 'Tối thiểu 6 ký tự', en: 'Min 6 characters' },
  'register.confirm_pw':   { vi: 'Nhập lại mật khẩu', en: 'Confirm Password' },
  'register.confirm_pw_placeholder': { vi: 'Xác nhận mật khẩu', en: 'Confirm password' },
  'register.btn':          { vi: 'Đăng ký', en: 'Register' },
  'register.have_account': { vi: 'Đã có tài khoản?', en: 'Already have an account?' },
  'register.login':        { vi: 'Đăng nhập ngay', en: 'Sign In now' },
  'register.or':           { vi: 'hoặc đăng ký bằng tài khoản', en: 'or register with account' },
  'register.google_info_prefix': { vi: 'Đang hoàn tất đăng ký cho tài khoản Google:', en: 'Completing registration for Google account:' },
  'register.google_info_suffix': { vi: '. Vui lòng tạo mật khẩu và tên đăng nhập.', en: '. Please create a password and username.' },

  'forgot.title':          { vi: 'Quên mật khẩu', en: 'Forgot Password' },
  'forgot.desc':           { vi: 'Nhập email của bạn để nhận mã OTP khôi phục mật khẩu', en: 'Enter your email to receive an OTP to reset your password' },
  'forgot.email':          { vi: 'Địa chỉ Email', en: 'Email Address' },
  'forgot.email_placeholder': { vi: 'Nhập email tài khoản của bạn...', en: 'Enter your account email...' },
  'forgot.btn':            { vi: 'Gửi mã OTP', en: 'Send OTP Code' },
  'forgot.back':           { vi: 'Quay lại Đăng nhập', en: 'Back to Sign In' },

  'reset.page_title':      { vi: 'Đặt lại mật khẩu - Giáo Trình AI', en: 'Reset Password - AI Curriculum' },
  'reset.title':           { vi: 'Đặt lại mật khẩu', en: 'Reset Password' },
  'reset.subtitle_prefix': { vi: 'Nhập mã OTP được gửi tới email', en: 'Enter the OTP sent to email' },
  'reset.subtitle_suffix': { vi: 'và mật khẩu mới của bạn.', en: 'and your new password.' },
  'reset.otp':             { vi: 'Mã xác thực OTP (6 chữ số)', en: 'Verification OTP Code (6 digits)' },
  'reset.otp_placeholder': { vi: 'Nhập mã OTP...', en: 'Enter OTP code...' },
  'reset.pw_new':          { vi: 'Mật khẩu mới', en: 'New Password' },
  'reset.pw_confirm':      { vi: 'Xác nhận mật khẩu mới', en: 'Confirm New Password' },
  'reset.btn':             { vi: 'Đặt lại mật khẩu', en: 'Reset Password' },
  'reset.back':            { vi: 'Quay lại Nhận OTP', en: 'Back to Request OTP' },
  
  'profile.pw_eye_title':  { vi: 'Hiện/ẩn mật khẩu', en: 'Show/hide password' },

  /* ===== PRICING ===== */
  'pricing.page_title':         { vi: 'Gói cước & Token - Giáo Trình AI', en: 'Pricing & Tokens - AI Curriculum' },
  'pricing.desc':               { vi: 'Chọn gói cước phù hợp với nhu cầu của bạn. Tỷ lệ quy đổi: 1.000 VND = 1 Token. Nạp càng nhiều, ưu đãi càng lớn.', en: 'Choose the pricing pack that fits your needs. Conversion rate: 1,000 VND = 1 Token. Buy more, save more.' },
  'pricing.receive_prefix':     { vi: 'nhận', en: 'receive' },
  'pricing.buy_now':            { vi: 'Mua Ngay', en: 'Buy Now' },
  'pricing.modal_title':        { vi: 'Thanh toán nạp Token', en: 'Token Payment' },
  'pricing.modal_amount':       { vi: 'Số tiền cần thanh toán', en: 'Amount to pay' },
  'pricing.modal_package':      { vi: 'Gói cước', en: 'Pricing Pack' },
  'pricing.modal_desc':         { vi: 'Bạn sẽ được chuyển hướng sang cổng thanh toán hoặc thực hiện chuyển khoản để hoàn tất giao dịch.', en: 'You will be redirected to the payment gateway or bank transfer to complete your transaction.' },
  'pricing.modal_method':       { vi: 'Chọn phương thức thanh toán', en: 'Select Payment Method' },
  'pricing.method_vnpay_title': { vi: 'Thanh toán qua VNPAY', en: 'Pay with VNPAY' },
  'pricing.method_vnpay_desc':  { vi: 'Hỗ trợ thẻ ATM nội địa, QR Code', en: 'Supports domestic ATM cards, QR Code' },
  'pricing.method_sepay_title': { vi: 'Chuyển khoản Ngân hàng (Tự động)', en: 'Bank Transfer (Auto)' },
  'pricing.method_sepay_desc':  { vi: 'Quét mã QR VietQR, duyệt tự động 24/7 qua SePay', en: 'Scan VietQR, auto-processed 24/7 via SePay' },
  'pricing.modal_btn':          { vi: 'Tiến hành thanh toán', en: 'Proceed to Payment' },
  'pricing.no_method':          { vi: 'Hiện tại không có dịch vụ thanh toán nào khả dụng. Vui lòng liên hệ Admin.', en: 'Currently no payment methods are available. Please contact Admin.' },

  /* ===== PACKAGES ===== */
  'Gói Bạc':                    { vi: 'Gói Bạc', en: 'Silver Pack' },
  'Gói Vàng':                   { vi: 'Gói Vàng', en: 'Gold Pack' },
  'Gói Kim Cương':              { vi: 'Gói Kim Cương', en: 'Diamond Pack' },

  /* ===== ADMIN PORTAL ===== */
  'admin.brand':                { vi: 'Quản trị', en: 'Admin Portal' },
  'admin.brand_desc':           { vi: 'Bảng điều khiển hệ thống', en: 'System Control Dashboard' },
  'admin.overview':             { vi: 'Tổng quan', en: 'Overview' },
  'admin.users':                { vi: 'Người dùng', en: 'Users' },
  'admin.packages':             { vi: 'Gói cước', en: 'Pricing Packages' },
  'admin.curriculums':          { vi: 'Giáo trình', en: 'Curriculums' },
  'admin.settings':             { vi: 'Cài đặt', en: 'Settings' },
  'admin.pages':                { vi: 'Quản lý trang', en: 'Manage Pages' },

  'admin.create':               { vi: 'Tạo giáo trình', en: 'Create Curriculum' },

  'admin.overview.title':       { vi: 'Tổng quan hệ thống', en: 'System Overview' },
  'admin.overview.subtitle':    { vi: 'Thống kê hoạt động và dữ liệu tổng hợp.', en: 'Activity statistics and aggregated data.' },
  'admin.overview.status_active': { vi: 'Hoạt động', en: 'Active' },
  'admin.overview.total_users': { vi: 'Tổng người dùng', en: 'Total Users' },
  'admin.overview.total_curriculums': { vi: 'Giáo trình đã tạo', en: 'Curriculums Created' },
  'admin.overview.total_files': { vi: 'File đã lưu', en: 'Saved Files' },

  'admin.users.title':          { vi: 'Quản lý người dùng', en: 'User Management' },
  'admin.users.subtitle':       { vi: 'Xem danh sách, thêm và chỉnh sửa thông tin thành viên.', en: 'View list, add and edit member information.' },
  'admin.users.add_title':      { vi: 'Thêm người dùng', en: 'Add User' },
  'admin.users.new_username':   { vi: 'Tên đăng nhập', en: 'Username' },
  'admin.users.new_password':   { vi: 'Mật khẩu', en: 'Password' },
  'admin.users.add_btn':        { vi: 'Thêm', en: 'Add' },
  'admin.users.list_title':     { vi: 'Danh sách người dùng', en: 'User List' },
  'admin.users.search_placeholder': { vi: 'Tìm kiếm người dùng (Tên, ID, Vai trò)...', en: 'Search users (Name, ID, Role)...' },
  'admin.users.col_id':         { vi: 'ID', en: 'ID' },
  'admin.users.col_username':   { vi: 'Tên đăng nhập', en: 'Username' },
  'admin.users.col_role':       { vi: 'Vai trò', en: 'Role' },
  'admin.users.col_status':     { vi: 'Trạng thái', en: 'Status' },
  'admin.users.col_token':      { vi: 'Token', en: 'Tokens' },
  'admin.users.col_date':       { vi: 'Ngày tạo', en: 'Date Created' },
  'admin.users.col_action':     { vi: 'Thao tác', en: 'Actions' },
  'admin.users.status_blocked': { vi: 'Bị khóa', en: 'Blocked' },
  'admin.users.status_active':  { vi: 'Hoạt động', en: 'Active' },
  'admin.users.show_count':     { vi: 'Hiển thị {count} tài khoản', en: 'Showing {count} accounts' },
  'admin.users.edit_title':     { vi: 'Chỉnh sửa thành viên', en: 'Edit Member' },
  'admin.users.edit_fullname':  { vi: 'Họ và tên', en: 'Full Name' },
  'admin.users.edit_email':     { vi: 'Email', en: 'Email' },
  'admin.users.edit_token':     { vi: 'Số dư Token (Credits)', en: 'Token Balance (Credits)' },
  'admin.users.edit_password':  { vi: 'Mật khẩu mới (để trống nếu không đổi)', en: 'New Password (leave empty if no change)' },
  'admin.users.password_note':  { vi: 'Mật khẩu được mã hóa một chiều. Bạn không thể xem mật khẩu hiện tại nhưng có thể cấp lại mật khẩu mới tại đây.', en: 'Passwords are one-way encrypted. You cannot view the current password but can issue a new one here.' },
  'admin.users.btn_generate':   { vi: 'Tạo ngẫu nhiên', en: 'Generate' },
  'admin.users.edit_admin_role': { vi: 'Quyền quản trị viên (Admin)', en: 'Administrator Privileges (Admin)' },
  'admin.users.btn_cancel':     { vi: 'Hủy', en: 'Cancel' },
  'admin.users.btn_save':       { vi: 'Lưu thay đổi', en: 'Save Changes' },

  'admin.packages.title':       { vi: 'Quản lý gói cước', en: 'Package Management' },
  'admin.packages.subtitle':    { vi: 'Thiết lập và tùy chỉnh các gói cước nạp Token động cho người dùng.', en: 'Set up and customize dynamic Token packages for users.' },
  'admin.packages.add_title':   { vi: 'Thêm gói cước mới', en: 'Add New Package' },
  'admin.packages.pkg_name':    { vi: 'Tên gói cước', en: 'Package Name' },
  'admin.packages.pkg_price':   { vi: 'Giá tiền (VND)', en: 'Price (VND)' },
  'admin.packages.pkg_token':   { vi: 'Số Token nhận được', en: 'Tokens Received' },
  'admin.packages.pkg_features': { vi: 'Tính năng (Ngăn cách bằng dấu phẩy)', en: 'Features (Comma-separated)' },
  'admin.packages.pkg_active':  { vi: 'Kích hoạt ngay', en: 'Activate Now' },
  'admin.packages.add_btn':     { vi: 'Thêm Gói', en: 'Add Package' },
  'admin.packages.list_title':  { vi: 'Danh sách gói cước hiện tại', en: 'Current Packages List' },
  'admin.packages.exchange_rate_badge': { vi: 'Tỷ giá mặc định: 1 Token = 1,000 VND', en: 'Default Rate: 1 Token = 1,000 VND' },
  'admin.packages.col_name':    { vi: 'Tên gói cước', en: 'Package Name' },
  'admin.packages.col_price':   { vi: 'Giá tiền', en: 'Price' },
  'admin.packages.col_tokens':  { vi: 'Số Token', en: 'Tokens' },
  'admin.packages.col_features': { vi: 'Các tính năng / Mô tả', en: 'Features / Description' },
  'admin.packages.col_status':  { vi: 'Trạng thái', en: 'Status' },
  'admin.packages.col_action':  { vi: 'Thao tác', en: 'Actions' },
  'admin.packages.status_selling': { vi: 'Đang bán', en: 'Active' },
  'admin.packages.status_hidden': { vi: 'Tạm ẩn', en: 'Hidden' },
  'admin.packages.no_packages': { vi: 'Chưa có gói cước nào được thiết lập. Hãy tạo gói cước đầu tiên ở trên!', en: 'No packages configured yet. Create the first package above!' },
  'admin.packages.show_count':  { vi: 'Tổng số: {count} gói cước', en: 'Total: {count} packages' },
  'admin.packages.edit_title':  { vi: 'Chỉnh sửa gói cước', en: 'Edit Package' },
  'admin.packages.edit_pkg_active': { vi: 'Kích hoạt bán gói cước này', en: 'Activate this package for sale' },

  'admin.curriculums.title':    { vi: 'Thư viện giáo trình', en: 'Curriculum Library' },
  'admin.curriculums.subtitle': { vi: 'Xem danh sách các giáo trình được biên soạn tự động.', en: 'View the list of automatically generated curricula.' },
  'admin.curriculums.list_title': { vi: 'Thư viện giáo trình', en: 'Curriculum Library' },
  'admin.curriculums.search_placeholder': { vi: 'Tìm kiếm giáo trình (Chủ đề, ID, Người tạo)...', en: 'Search curriculums (Topic, ID, Creator)...' },
  'admin.curriculums.col_id':   { vi: 'ID', en: 'ID' },
  'admin.curriculums.col_user': { vi: 'Người tạo', en: 'Created By' },
  'admin.curriculums.col_topic': { vi: 'Chủ đề', en: 'Topic' },
  'admin.curriculums.col_date':  { vi: 'Ngày tạo', en: 'Date Created' },
  'admin.curriculums.col_status': { vi: 'Trạng thái', en: 'Status' },
  'admin.curriculums.col_action': { vi: 'Thao tác', en: 'Actions' },
  'admin.curriculums.status_available': { vi: 'Có sẵn', en: 'Available' },
  'admin.curriculums.status_not_saved': { vi: 'Chưa lưu', en: 'Not Saved' },

  'admin.settings.title':       { vi: 'Cài đặt hệ thống (API & Models)', en: 'System Settings (API & Models)' },
  'admin.settings.subtitle':    { vi: 'Điều chỉnh API Key, Model Engines và Cấu hình phương thức thanh toán.', en: 'Adjust API Keys, Model Engines and Payment Gateway configurations.' },
  'admin.settings.card_title':  { vi: 'Cài đặt hệ thống (API & Models)', en: 'System Settings (API & Models)' },
  'admin.settings.openai_desc': { vi: 'Dùng cho gpt-4o-mini (Writer/Search)', en: 'Used for gpt-4o-mini (Writer/Search)' },
  'admin.settings.gemini_desc': { vi: 'Các key phân cách nhau bởi dấu phẩy (,). Hệ thống sẽ tự động xoay vòng (round-robin) khi hết quota.', en: 'Keys separated by commas (,). The system will auto-rotate (round-robin) when quota is exceeded.' },
  'admin.settings.gemini_pro_desc': { vi: 'Dùng làm core engine (phân tích tri thức lớn).', en: 'Used as the core engine (large knowledge analysis).' },
  'admin.settings.gemini_lite_desc': { vi: 'Dùng làm model gọn cho các tác vụ phụ.', en: 'Used as a lightweight model for helper tasks.' },
  'admin.settings.task_assignments': { vi: 'Cấu hình Phân vai trò Model (Task Assignments)', en: 'Model Task Assignments Configuration' },
  'admin.settings.writer_model': { vi: 'Biên soạn & Viết nội dung (Writer Model)', en: 'Writer Model' },
  'admin.settings.writer_model_desc': { vi: 'Model đảm nhận sinh văn bản chi tiết cho các mục trong giáo trình.', en: 'Model responsible for generating detailed text for curriculum sections.' },
  'admin.settings.search_model': { vi: 'Tìm kiếm & Phân tích (Search/Crawler Model)', en: 'Search/Crawler Model' },
  'admin.settings.search_model_desc': { vi: 'Model phụ trách trích xuất thực thể, lọc liên kết và lập chỉ mục.', en: 'Model responsible for entity extraction, link filtering, and indexing.' },
  'admin.settings.lite_supervisor': { vi: 'Giám sát nhẹ (Lite Supervisor)', en: 'Lite Supervisor' },
  'admin.settings.lite_supervisor_desc': { vi: 'Model dùng để đánh giá độ trôi chảy, logic cơ bản và kiểm duyệt nhanh.', en: 'Model used for evaluating basic flow, logic, and quick moderation.' },
  'admin.settings.pro_supervisor': { vi: 'Giám sát nâng cao (Pro Supervisor)', en: 'Pro Supervisor' },
  'admin.settings.pro_supervisor_desc': { vi: 'Model phụ trách kiểm tra dàn ý chi tiết, audit trích dẫn và viết lại bài lỗi.', en: 'Model responsible for detailed outline verification, citation audit, and rewriting failures.' },
  'admin.settings.payment_gateways': { vi: 'Cấu hình Cổng thanh toán (Payment Gateways)', en: 'Payment Gateways Configuration' },
  'admin.settings.vnpay_active': { vi: 'Kích hoạt thanh toán VNPAY', en: 'Enable VNPAY Payments' },
  'admin.settings.sepay_active': { vi: 'Kích hoạt thanh toán SePay', en: 'Enable SePay Payments' },
  'admin.settings.save_btn':     { vi: 'Lưu Cài đặt', en: 'Save Settings' },
  'admin.settings.saving_text':  { vi: 'Đang lưu...', en: 'Saving...' },
  'admin.settings.token_pricing_section': { vi: 'Cấu hình giá Token cho các chế độ biên soạn', en: 'Token Pricing Configuration for Compilation Modes' },
  'admin.settings.phi_token_auto': { vi: 'Chế độ Auto (Tokens)', en: 'Auto Mode Cost (Tokens)' },
  'admin.settings.phi_token_auto_desc': { vi: 'Phí token khi chạy chế độ Tự động hoàn toàn (mặc định: 1)', en: 'Token fee for Fully Automatic mode (default: 1)' },
  'admin.settings.phi_token_expert': { vi: 'Chế độ Expert (Tokens)', en: 'Expert Mode Cost (Tokens)' },
  'admin.settings.phi_token_expert_desc': { vi: 'Phí token khi chạy chế độ Chuyên gia audit (mặc định: 2)', en: 'Token fee for Expert Audit mode (default: 2)' },
  'admin.settings.phi_token_creative': { vi: 'Chế độ Creative (Tokens)', en: 'Creative Mode Cost (Tokens)' },
  'admin.settings.phi_token_creative_desc': { vi: 'Phí token khi chạy chế độ Sáng tạo nội dung (mặc định: 3)', en: 'Token fee for Content Creation mode (default: 3)' }
};

/* ──────────────────────────────────────────
   Core functions
────────────────────────────────────────── */

function getCurrentLang() {
  return localStorage.getItem('app_lang') || 'vi';
}

function applyLanguage(lang) {
  document.documentElement.lang = lang;

  /* Translate all data-i18n elements */
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const t = TRANSLATIONS[key];
    if (!t) return;
    let text = t[lang] || t['vi'];

    if (el.hasAttribute('data-i18n-count')) {
      text = text.replace('{count}', el.getAttribute('data-i18n-count'));
    }

    /* Placeholder vs text content */
    if (el.hasAttribute('placeholder')) {
      el.setAttribute('placeholder', text);
    } else {
      el.textContent = text;
    }
  });

  /* Translate all data-i18n-title elements */
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    const t = TRANSLATIONS[key];
    if (!t) return;
    const text = t[lang] || t['vi'];
    el.setAttribute('title', text);
  });

  /* Update language button label */
  const langLabel = document.getElementById('langLabel');
  const langFlag  = document.getElementById('langFlag');
  if (langLabel) langLabel.textContent = lang === 'vi' ? 'VI' : 'EN';
  if (langFlag)  langFlag.textContent  = lang === 'vi' ? '🇻🇳' : '🇬🇧';

  const langLabelMobile = document.getElementById('langLabelMobile');
  const langFlagMobile  = document.getElementById('langFlagMobile');
  if (langLabelMobile) langLabelMobile.textContent = lang === 'vi' ? 'VI' : 'EN';
  if (langFlagMobile)  langFlagMobile.textContent  = lang === 'vi' ? '🇻🇳' : '🇬🇧';

  document.querySelectorAll('.lang-label').forEach(el => el.textContent = lang === 'vi' ? 'VI' : 'EN');
  document.querySelectorAll('.lang-flag').forEach(el => el.textContent = lang === 'vi' ? '🇻🇳' : '🇬🇧');

  /* Dispatch event for page-specific translations */
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang: lang } }));
}

function toggleLanguage() {
  const current = getCurrentLang();
  const next = current === 'vi' ? 'en' : 'vi';
  localStorage.setItem('app_lang', next);
  applyLanguage(next);
}

/* Auto-apply on page load */
document.addEventListener('DOMContentLoaded', () => {
  applyLanguage(getCurrentLang());
});
