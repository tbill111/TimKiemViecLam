import type { DataSource } from '../types';

/**
 * Dữ liệu minh họa cho màn hình ETL và Data Flow.
 * Đây là kiến trúc dự kiến – không phải pipeline thực tế.
 */
export const dataSources: DataSource[] = [
  {
    id: 'ds-001',
    name: 'Hồ sơ Sinh viên',
    description: 'Thông tin học vấn, kỹ năng, dự án, kinh nghiệm do sinh viên tự nhập hoặc trích xuất từ CV sau khi sinh viên xác nhận.',
    type: 'internal',
    format: 'Biểu mẫu web; tệp CV PDF, DOCX',
    fields: ['Họ tên', 'Trường đại học', 'Chuyên ngành', 'Kỹ năng', 'Dự án cá nhân', 'Kinh nghiệm', 'Mong muốn công việc'],
    status: 'active',
  },
  {
    id: 'ds-002',
    name: 'Tin Tuyển dụng Doanh nghiệp',
    description: 'Tin tuyển dụng do doanh nghiệp đăng trực tiếp qua tài khoản nhà tuyển dụng. Nguồn ưu tiên vì xác minh được.',
    type: 'internal',
    format: 'Biểu mẫu web; tệp CSV/Excel',
    fields: ['Tên vị trí', 'Mô tả công việc', 'Kỹ năng yêu cầu', 'Kinh nghiệm', 'Địa điểm', 'Mức lương', 'Hình thức', 'Hạn nộp'],
    status: 'active',
  },
  {
    id: 'ds-003',
    name: 'Nguồn Tuyển dụng Bên ngoài',
    description: 'Tin từ LinkedIn, Indeed hoặc các trang tuyển dụng trong nước như TopCV, VietnamWorks, ITviec, chỉ khi có thỏa thuận hoặc API được cấp phép. Không tự ý thu thập.',
    type: 'external',
    format: 'JSON qua API đối tác',
    fields: ['Tin tuyển dụng được cấp phép', 'Ngành nghề', 'Nguồn và thời điểm thu thập'],
    status: 'pending',
  },
  {
    id: 'ds-004',
    name: 'Danh mục Kỹ năng và Khóa học',
    description: 'Tên kỹ năng chuẩn, từ đồng nghĩa và lộ trình học gợi ý, phục vụ chuẩn hóa và phân tích kỹ năng thiếu.',
    type: 'internal',
    format: 'Bảng nội bộ (nhóm tự xây dựng)',
    fields: ['Tên kỹ năng chuẩn', 'Từ đồng nghĩa', 'Nhóm kỹ năng', 'Lộ trình học'],
    status: 'active',
  },
  {
    id: 'ds-005',
    name: 'Hành vi Người dùng',
    description: 'Lượt lưu việc, ứng tuyển và trạng thái hồ sơ, dùng để xếp hạng và đánh giá chất lượng gợi ý. Chỉ thu thập khi người dùng đồng ý.',
    type: 'internal',
    format: 'Sự kiện trong ứng dụng',
    fields: ['Việc đã lưu', 'Đơn ứng tuyển', 'Trạng thái hồ sơ', 'Thời điểm'],
    status: 'active',
  },
  {
    id: 'ds-006',
    name: 'Chương trình Đào tạo (Nhà trường)',
    description: 'Danh sách môn học và chuẩn đầu ra do nhà trường cung cấp, giúp đối chiếu kỹ năng đào tạo với nhu cầu tuyển dụng.',
    type: 'partner',
    format: 'Tệp PDF/Excel theo thỏa thuận',
    fields: ['Ngành', 'Môn học', 'Chuẩn đầu ra'],
    status: 'pending',
  },
];

export const etlSteps = {
  extract: [
    {
      id: 'e1',
      title: 'Tiếp nhận từ Biểu mẫu',
      description: 'Nhận dữ liệu hồ sơ khi sinh viên điền và nộp biểu mẫu đăng ký.',
      icon: 'FileInput',
    },
    {
      id: 'e2',
      title: 'Tiếp nhận Tin Tuyển dụng',
      description: 'Nhà tuyển dụng đăng tin qua giao diện quản lý dành riêng.',
      icon: 'Building2',
    },
    {
      id: 'e3',
      title: 'Đọc CV và trích xuất kỹ năng',
      description: 'Đọc CV PDF/DOCX, tách chữ và dò kỹ năng theo danh mục (prototype dùng từ điển; dự kiến dùng mô hình ngôn ngữ như PhoBERT). Sinh viên xác nhận trước khi lưu.',
      icon: 'Upload',
    },
    {
      id: 'e4',
      title: 'Nhận từ Nguồn Đối tác',
      description: 'Dữ liệu tuyển dụng được cung cấp từ các đối tác theo hợp đồng.',
      icon: 'Globe',
    },
  ],
  transform: [
    {
      id: 't1',
      title: 'Kiểm tra Trường Bắt buộc',
      description: 'Xác minh dữ liệu đầu vào có đủ các trường bắt buộc.',
      icon: 'CheckCircle',
    },
    {
      id: 't2',
      title: 'Chuẩn hóa Kỹ năng',
      description: 'Ánh xạ tên kỹ năng về dạng chuẩn trong danh mục (ví dụ: "ReactJS" → "React").',
      icon: 'Tags',
    },
    {
      id: 't3',
      title: 'Chuẩn hóa Địa điểm & Loại',
      description: 'Chuẩn hóa tên tỉnh/thành phố và hình thức làm việc.',
      icon: 'MapPin',
    },
    {
      id: 't4',
      title: 'Phát hiện Trùng lặp',
      description: 'Tìm và loại bỏ các bản ghi có nội dung giống nhau.',
      icon: 'Copy',
    },
    {
      id: 't5',
      title: 'Kiểm tra Định dạng',
      description: 'Xác minh định dạng email, ngày tháng, số điện thoại,...',
      icon: 'AlertCircle',
    },
    {
      id: 't6',
      title: 'Đánh dấu Dữ liệu Lỗi',
      description: 'Gắn nhãn bản ghi thiếu thông tin hoặc hết hạn để xem xét.',
      icon: 'Flag',
    },
  ],
  load: [
    {
      id: 'l1',
      title: 'Hồ sơ Sinh viên',
      description: 'Lưu vào bảng profiles với đầy đủ thông tin đã được xác thực.',
      icon: 'UserCircle',
    },
    {
      id: 'l2',
      title: 'Kho Tin Tuyển dụng',
      description: 'Lưu tin tuyển dụng vào bảng jobs và index để tìm kiếm nhanh.',
      icon: 'Briefcase',
    },
    {
      id: 'l3',
      title: 'Danh mục Kỹ năng',
      description: 'Cập nhật bảng kỹ năng chuẩn hóa khi phát hiện tên mới.',
      icon: 'Star',
    },
    {
      id: 'l4',
      title: 'Kết quả Ghép nối',
      description: 'Lưu kết quả phân tích CV–JD và lịch sử ứng tuyển để cải thiện thuật toán.',
      icon: 'Link',
    },
  ],
};
