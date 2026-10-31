import type { RawJobRecord } from '../types';

/**
 * Dữ liệu tin tuyển dụng "thô" minh họa, gom từ ba nguồn với cách ghi khác nhau.
 * Cố tình chứa lỗi thường gặp (viết tắt địa điểm, tên kỹ năng không thống nhất,
 * thiếu trường, email sai, tin trùng, tin hết hạn) để chạy thử quy trình làm sạch.
 * Tên công ty là dữ liệu minh họa.
 */
export const rawJobFeed: RawJobRecord[] = [
  { id: 'raw-01', source: 'Doanh nghiệp', title: 'Frontend Intern', company: 'Lumen Tech', location: 'HN', workType: 'Intern', skills: 'ReactJS, HTML5, CSS3, Git', salary: '4–6 triệu', deadline: '2026-11-15', contactEmail: 'hr@lumen.example.com' },
  { id: 'raw-02', source: 'Đối tác', title: 'Frontend Intern', company: 'Lumen Tech', location: 'Ha Noi', workType: 'Thực tập sinh', skills: 'React.js, HTML, CSS', salary: '', deadline: '2026-11-10', contactEmail: 'jobs@lumen.example.com' },
  { id: 'raw-03', source: 'Tệp CSV', title: 'Data Analyst Intern', company: 'Orbit Data', location: 'TP.HCM', workType: 'internship', skills: 'SQL; Python3; Excel; PowerBI', salary: '', deadline: '2026-11-30', contactEmail: 'talent@orbit.example.com' },
  { id: 'raw-04', source: 'Doanh nghiệp', title: '', company: 'Nova Retail', location: 'Đà Nẵng', workType: 'Thực tập', skills: 'Excel, Giao tiếp', salary: '3 triệu', deadline: '2026-11-20', contactEmail: 'hr@nova.example.com' },
  { id: 'raw-05', source: 'Đối tác', title: 'Backend Developer Intern', company: 'Kite Systems', location: 'Sài Gòn', workType: 'Full-time', skills: 'NodeJS, Postgres, RESTful API, Docker', salary: '8–10 triệu', deadline: '2026-10-01', contactEmail: 'hr@kite.example.com' },
  { id: 'raw-06', source: 'Doanh nghiệp', title: 'Tester Intern', company: 'QualityHub', location: 'Da Nang', workType: 'intern', skills: 'Kiểm thử, Selenium, Git', salary: '3–4 triệu', deadline: '2026-11-25', contactEmail: 'hr@qualityhub' },
  { id: 'raw-07', source: 'Tệp CSV', title: 'UI/UX Designer Intern', company: 'Pixel Studio', location: 'hcm', workType: 'Part-time', skills: 'Figma, Prototyping, kỹ năng giao tiếp', salary: '', deadline: '2026-12-05', contactEmail: 'design@pixel.example.com' },
  { id: 'raw-08', source: 'Đối tác', title: 'Business Analyst Intern', company: 'FinBridge', location: 'Hà Nội', workType: 'Thực tập', skills: '', salary: '5 triệu', deadline: '2026-11-18', contactEmail: 'hr@finbridge.example.com' },
  { id: 'raw-09', source: 'Doanh nghiệp', title: 'React Developer', company: 'AppNest', location: 'Remote', workType: 'remote', skills: 'React, TypeScript, Tailwind, REST API', salary: '7–9 triệu', deadline: '2026-11-28', contactEmail: 'team@appnest.example.com' },
  { id: 'raw-10', source: 'Tệp CSV', title: 'data analyst intern ', company: 'Orbit Data', location: 'Hồ Chí Minh', workType: 'Thực tập', skills: 'SQL, Excel', salary: '', deadline: '2026-11-20', contactEmail: 'talent@orbit.example.com' },
  { id: 'raw-11', source: 'Đối tác', title: 'IT Support Intern', company: 'Helio Telecom', location: 'TP. Hà Nội', workType: 'Thực tập sinh', skills: 'Mạng cơ bản, Windows Server, Xử lý sự cố', salary: '3 triệu', deadline: '2026-09-30', contactEmail: 'hr@helio.example.com' },
  { id: 'raw-12', source: 'Doanh nghiệp', title: 'Software Engineer Fresher', company: 'Bright Code', location: 'HN', workType: 'Toàn thời gian', skills: 'JavaScript, Node.js, SQL, Git, Agile', salary: '10–14 triệu', deadline: '2026-12-01', contactEmail: 'careers@brightcode.example.com' },
];
