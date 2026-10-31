import type { Candidate } from '../types';

/**
 * Ứng viên mẫu cho cổng nhà tuyển dụng.
 * Tên và thông tin đều là dữ liệu minh họa, không phải người thật.
 */
export const sampleCandidates: Candidate[] = [
  {
    id: 'cand-001',
    fullName: 'Trần Quốc Bảo',
    major: 'Kỹ thuật Phần mềm',
    university: 'Đại học Công nghệ – ĐHQGHN',
    year: 'Năm 4',
    skills: ['Node.js', 'JavaScript', 'SQL', 'REST API', 'Git', 'Docker', 'PostgreSQL'],
    preferredLocations: ['Hồ Chí Minh'],
    preferredWorkTypes: ['Thực tập'],
  },
  {
    id: 'cand-002',
    fullName: 'Lê Thu Hà',
    major: 'Hệ thống Thông tin',
    university: 'Đại học Kinh tế Quốc dân',
    year: 'Năm 3',
    skills: ['SQL', 'Python', 'Excel', 'Power BI', 'Thống kê cơ bản', 'Pandas'],
    preferredLocations: ['Hà Nội'],
    preferredWorkTypes: ['Thực tập', 'Bán thời gian'],
  },
  {
    id: 'cand-003',
    fullName: 'Phạm Gia Huy',
    major: 'Công nghệ Thông tin',
    university: 'Học viện Công nghệ Bưu chính Viễn thông',
    year: 'Năm 4',
    skills: ['React', 'TypeScript', 'HTML', 'CSS', 'Git', 'REST API', 'Tailwind CSS', 'Jest'],
    preferredLocations: ['Hà Nội', 'Remote'],
    preferredWorkTypes: ['Remote', 'Thực tập'],
  },
  {
    id: 'cand-004',
    fullName: 'Đỗ Mai Linh',
    major: 'Hệ thống Thông tin Quản lý',
    university: 'Học viện Ngân hàng',
    year: 'Năm 4',
    skills: ['Phân tích nghiệp vụ', 'Excel', 'Giao tiếp', 'Viết tài liệu', 'UML', 'SQL', 'BPMN'],
    preferredLocations: ['Hà Nội'],
    preferredWorkTypes: ['Toàn thời gian', 'Thực tập'],
  },
  {
    id: 'cand-005',
    fullName: 'Vũ Đức Nam',
    major: 'Công nghệ Thông tin',
    university: 'Đại học Bách khoa – ĐH Đà Nẵng',
    year: 'Năm 3',
    skills: ['Kiểm thử phần mềm', 'Viết test case', 'Excel', 'Git', 'Tư duy phân tích', 'Postman'],
    preferredLocations: ['Đà Nẵng'],
    preferredWorkTypes: ['Thực tập'],
  },
  {
    id: 'cand-006',
    fullName: 'Hoàng Minh Châu',
    major: 'Thiết kế Đồ họa',
    university: 'Đại học Kiến trúc TP.HCM',
    year: 'Năm 4',
    skills: ['Figma', 'Nguyên lý UX', 'Thiết kế UI', 'Tư duy sáng tạo', 'Giao tiếp', 'Prototyping'],
    preferredLocations: ['Hồ Chí Minh'],
    preferredWorkTypes: ['Thực tập'],
  },
];
