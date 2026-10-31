import type { StudentProfile } from '../types';

/**
 * Hồ sơ sinh viên mẫu – Giang Thanh Tùng.
 * Dùng nhất quán xuyên suốt ứng dụng.
 */
export const defaultStudentProfile: StudentProfile = {
  fullName: 'Giang Thanh Tùng',
  university: 'Trường Đại học Thủy lợi',
  major: 'Công nghệ Thông tin',
  year: 'Năm 4 (2022–2026)',
  email: 'thanhtung.demo@example.edu.vn',
  phone: '0912 345 678',
  githubUrl: '',
  linkedinUrl: '',
  careerGoal:
    'Mong muốn trở thành Frontend Developer tại một công ty công nghệ năng động, nơi tôi có thể áp dụng kỹ năng React và TypeScript để xây dựng sản phẩm thực sự có ý nghĩa với người dùng. Định hướng lâu dài là phát triển thành Full-stack Developer hoặc Tech Lead.',
  skills: [
    'HTML',
    'CSS',
    'JavaScript',
    'React',
    'Git',
    'SQL',
    'Python cơ bản',
    'Figma',
    'Responsive Design',
  ],
  preferredLocations: ['Hà Nội', 'Remote'],
  preferredWorkTypes: ['Thực tập', 'Remote'],
  languages: ['Tiếng Việt (Bản ngữ)', 'Tiếng Anh (B2 – IELTS 6.5)'],
  projects: [
    {
      id: 'proj-001',
      name: 'SmartTask – Quản lý Công việc Nhóm',
      description:
        'Ứng dụng web quản lý công việc nhóm với tính năng tạo board Kanban, phân công nhiệm vụ và theo dõi tiến độ theo thời gian thực.',
      technologies: ['React', 'Node.js', 'MongoDB', 'Socket.IO', 'Tailwind CSS'],
      url: 'https://github.com/minhanh/smarttask',
    },
    {
      id: 'proj-002',
      name: 'EcoMarket – Sàn Thương mại Điện tử Xanh',
      description:
        'Website thương mại điện tử hướng đến sản phẩm thân thiện môi trường, có tích hợp tìm kiếm nâng cao và hệ thống đánh giá sản phẩm.',
      technologies: ['React', 'Django', 'PostgreSQL', 'Redux', 'Bootstrap'],
      url: 'https://github.com/minhanh/ecomarket',
    },
    {
      id: 'proj-003',
      name: 'StudentHub – Mạng xã hội Học thuật',
      description:
        'Nền tảng kết nối sinh viên để chia sẻ tài liệu học tập, thảo luận và tìm kiếm bạn học theo môn học hoặc trường đại học.',
      technologies: ['HTML', 'CSS', 'JavaScript', 'PHP', 'MySQL'],
      url: 'https://github.com/minhanh/studenthub',
    },
  ],
  experience: [
    {
      id: 'exp-001',
      position: 'Frontend Developer Part-time',
      company: 'Studio404 Design Agency',
      duration: 'Tháng 6/2025 – Tháng 9/2025 (4 tháng)',
      description:
        'Xây dựng landing page và giao diện quảng cáo cho các thương hiệu FMCG. Áp dụng React và Tailwind CSS, đảm bảo responsive trên mọi thiết bị. Tham gia review thiết kế với UI/UX Designer.',
    },
    {
      id: 'exp-002',
      position: 'Trưởng nhóm Kỹ thuật – CLB Tin học',
      company: 'Câu lạc bộ Tin học – Trường Đại học Thủy lợi',
      duration: 'Tháng 9/2024 – Tháng 6/2025 (9 tháng)',
      description:
        'Lãnh đạo nhóm 8 sinh viên trong việc tổ chức workshop, hackathon và duy trì website của câu lạc bộ. Phụ trách tuyển thành viên và đào tạo kỹ năng lập trình web cơ bản.',
    },
  ],
  certificates: [
    {
      id: 'cert-001',
      name: 'Meta Front-End Developer Professional Certificate',
      issuer: 'Meta / Coursera',
      year: '2025',
    },
    {
      id: 'cert-002',
      name: 'Google Data Analytics Certificate',
      issuer: 'Google / Coursera',
      year: '2024',
    },
    {
      id: 'cert-003',
      name: 'IELTS Academic 6.5',
      issuer: 'British Council',
      year: '2024',
    },
  ],
  profileCompletion: 82,
};
