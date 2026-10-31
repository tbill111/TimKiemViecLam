/**
 * Nhóm kỹ năng dùng cho biểu đồ radar ở Tổng quan.
 * Điểm của mỗi nhóm = % kỹ năng trong nhóm mà hồ sơ đã có (xem getSkillCoverage).
 */
export interface SkillCategory {
  name: string;
  skills: string[];
}

export const skillCategories: SkillCategory[] = [
  { name: 'Frontend', skills: ['HTML', 'CSS', 'JavaScript', 'React', 'TypeScript', 'Responsive Design'] },
  { name: 'Backend', skills: ['Node.js', 'REST API', 'SQL', 'PostgreSQL', 'Python'] },
  { name: 'Dữ liệu', skills: ['SQL', 'Python', 'Excel', 'Thống kê cơ bản', 'Power BI'] },
  { name: 'Thiết kế', skills: ['Figma', 'Nguyên lý UX', 'Thiết kế UI', 'Responsive Design'] },
  { name: 'Kỹ năng mềm', skills: ['Giao tiếp', 'Viết tài liệu', 'Tư duy logic', 'Thuyết trình'] },
  { name: 'DevOps', skills: ['Git', 'Docker', 'Linux cơ bản', 'CI/CD'] },
];
