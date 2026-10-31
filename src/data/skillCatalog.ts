import { sampleJobs } from './jobs';

/**
 * Từ đồng nghĩa của kỹ năng: tên chuẩn → các cách viết thường gặp.
 * Dùng chung cho bước chuẩn hóa ETL và cho việc dò kỹ năng trong CV.
 * Không đưa các viết tắt quá ngắn (như "js", "ts") vì dễ nhận nhầm.
 */
export const skillAliases: Record<string, string[]> = {
  React: ['reactjs', 'react.js', 'react js'],
  'Node.js': ['nodejs', 'node js'],
  HTML: ['html5'],
  CSS: ['css3'],
  JavaScript: ['javascript es6', 'ecmascript'],
  TypeScript: [],
  'REST API': ['restful api', 'restful', 'rest apis'],
  PostgreSQL: ['postgres', 'postgre sql'],
  Python: ['python3'],
  Excel: ['microsoft excel', 'ms excel'],
  'Power BI': ['powerbi'],
  'Tailwind CSS': ['tailwind', 'tailwindcss'],
  'Thống kê cơ bản': ['thống kê', 'statistics'],
  'Kiểm thử phần mềm': ['kiểm thử', 'software testing'],
  'Giao tiếp': ['kỹ năng giao tiếp', 'communication'],
  'Agile/Scrum': ['agile', 'scrum'],
  Figma: [],
  Git: [],
  Docker: [],
  SQL: [],
};

/** Tên kỹ năng có dạng nhiều lựa chọn ("A hoặc B") không dùng làm từ khóa dò. */
const isCompositeName = (s: string) => /\s+hoặc\s+/.test(s);

/**
 * Danh mục kỹ năng chuẩn: hợp của kỹ năng trong tin tuyển dụng mẫu và bảng từ đồng nghĩa.
 */
export const skillCatalog: string[] = Array.from(
  new Set([
    ...Object.keys(skillAliases),
    ...sampleJobs.flatMap((j) => [...j.requiredSkills, ...j.preferredSkills]).filter((s) => !isCompositeName(s)),
  ])
);
