import type { SkillGapItem } from '../types';

/**
 * Tạo lộ trình học mẫu cho một kỹ năng chưa có trong dữ liệu gợi ý.
 */
export function buildLearningSteps(skill: string): string[] {
  return [
    `Tìm hiểu khái niệm cơ bản của ${skill} qua tài liệu chính thức`,
    `Thực hành ${skill} bằng một bài tập nhỏ hoặc mini project`,
    `Đưa ${skill} vào dự án cá nhân và mô tả trong CV`,
  ];
}

/**
 * Dữ liệu lộ trình học mẫu cho các kỹ năng thường gặp trong tin tuyển dụng.
 * Trang Skill Gap dùng danh sách này để gợi ý cách học khi kỹ năng nằm trong công việc mục tiêu.
 */
export const defaultSkillGapItems: SkillGapItem[] = [
  {
    id: 'gap-001',
    skill: 'TypeScript',
    priority: 'Cao',
    category: 'Frontend Development',
    learned: false,
    learningSteps: [
      'Hoàn thành khóa TypeScript cơ bản trên freeCodeCamp hoặc Udemy',
      'Chuyển đổi một project React hiện có sang TypeScript',
      'Áp dụng generic types và utility types trong project thực tế',
    ],
  },
  {
    id: 'gap-002',
    skill: 'REST API',
    priority: 'Cao',
    category: 'Backend & Integration',
    learned: false,
    learningSteps: [
      'Học cách gọi API với fetch() và axios',
      'Thực hành với các public API (GitHub API, OpenWeatherMap,...)',
      'Xử lý loading states, error handling và authentication token',
    ],
  },
  {
    id: 'gap-003',
    skill: 'Node.js',
    priority: 'Cao',
    category: 'Backend Development',
    learned: false,
    learningSteps: [
      'Học Node.js cơ bản: modules, event loop, file system',
      'Xây dựng REST API đơn giản với Express.js',
      'Kết nối database và xử lý CRUD operations',
    ],
  },
  {
    id: 'gap-004',
    skill: 'Docker cơ bản',
    priority: 'Trung bình',
    category: 'DevOps & Infrastructure',
    learned: false,
    learningSteps: [
      'Hiểu khái niệm container và image',
      'Tạo Dockerfile cho ứng dụng Node.js hoặc Python',
      'Sử dụng Docker Compose để chạy multi-container apps',
    ],
  },
  {
    id: 'gap-005',
    skill: 'Kiểm thử phần mềm (Jest)',
    priority: 'Trung bình',
    category: 'QA & Testing',
    learned: false,
    learningSteps: [
      'Học khái niệm unit test, integration test',
      'Viết test với Jest cho React components',
      'Đạt mức code coverage >60% trong project cá nhân',
    ],
  },
  {
    id: 'gap-006',
    skill: 'Kỹ năng thuyết trình kỹ thuật',
    priority: 'Trung bình',
    category: 'Kỹ năng Mềm',
    learned: false,
    learningSteps: [
      'Luyện thuyết trình project ở CLB hoặc hackathon',
      'Tham gia các buổi demo ngắn (lightning talk) với bạn bè',
      'Thực hành giải thích code cho người không kỹ thuật',
    ],
  },
  {
    id: 'gap-007',
    skill: 'Agile / Scrum',
    priority: 'Thấp',
    category: 'Quy trình Làm việc',
    learned: false,
    learningSteps: [
      'Tìm hiểu Scrum Guide (tài liệu chính thức)',
      'Sử dụng Jira hoặc Trello để quản lý sprint cá nhân',
      'Tham gia hackathon hoặc side project có áp dụng Agile',
    ],
  },
  {
    id: 'gap-008',
    skill: 'PostgreSQL',
    priority: 'Thấp',
    category: 'Cơ sở dữ liệu',
    learned: false,
    learningSteps: [
      'Cài đặt PostgreSQL và làm quen với pgAdmin',
      'Thực hành viết các câu truy vấn phức tạp: JOIN, subquery, window function',
      'Tích hợp PostgreSQL vào project backend cá nhân',
    ],
  },
];
