import {
  AlertTriangle,
  Lightbulb,
  Cpu,
  Server,
  Code2,
  CheckCircle2,
  Clock,
  Users,
  Search,
  BarChart2,
  BookOpen,
  Layers,
} from 'lucide-react';

const targetUsers = [
  {
    title: 'Sinh viên năm 3–4',
    desc: 'Chuẩn bị tìm thực tập hoặc việc làm đầu tiên, cần biết mình thiếu kỹ năng nào.',
  },
  {
    title: 'Sinh viên mới ra trường',
    desc: 'Đang tìm vị trí fresher, cần so sánh hồ sơ với yêu cầu thực tế của nhà tuyển dụng.',
  },
  {
    title: 'Sinh viên đổi hướng nghề',
    desc: 'Muốn khám phá các lĩnh vực mới như dữ liệu, thiết kế hay quản trị hệ thống trước khi chọn.',
  },
];

const problems = [
  {
    icon: <Search size={20} className="text-red-500" />,
    title: 'Tin tuyển dụng phân tán',
    desc: 'Sinh viên phải tìm kiếm trên nhiều nền tảng khác nhau, tốn thời gian và dễ bỏ lỡ cơ hội phù hợp.',
  },
  {
    icon: <Users size={20} className="text-red-500" />,
    title: 'CV chưa thể hiện đúng năng lực',
    desc: 'Sinh viên thiếu kinh nghiệm viết CV theo đúng yêu cầu tuyển dụng, khó nổi bật trước nhà tuyển dụng.',
  },
  {
    icon: <BarChart2 size={20} className="text-red-500" />,
    title: 'Không biết kỹ năng còn thiếu',
    desc: 'Không có công cụ so sánh kỹ năng hiện có với yêu cầu thực tế, dẫn đến thiếu định hướng học tập.',
  },
  {
    icon: <BookOpen size={20} className="text-red-500" />,
    title: 'Thiếu định hướng nghề nghiệp',
    desc: 'Nhiều sinh viên chưa biết ngành nghề nào phù hợp với bản thân, nên khó lên kế hoạch phát triển.',
  },
];

const solutions = [
  {
    icon: <Layers size={20} className="text-blue-600" />,
    title: 'Tập trung hóa tin tuyển dụng',
    desc: 'Một nền tảng duy nhất tổng hợp từ nhiều nguồn đáng tin cậy, giảm thời gian tìm kiếm.',
  },
  {
    icon: <Search size={20} className="text-blue-600" />,
    title: 'Gợi ý việc theo kỹ năng',
    desc: 'Thuật toán ghép nối đa tiêu chí: 60% kỹ năng bắt buộc, 25% kỹ năng ưu tiên, 15% địa điểm và hình thức mong muốn.',
  },
  {
    icon: <Users size={20} className="text-blue-600" />,
    title: 'Kết nối nhà tuyển dụng',
    desc: 'Doanh nghiệp xem ứng viên được xếp hạng theo mức phù hợp và cập nhật trạng thái hồ sơ cho sinh viên.',
  },
  {
    icon: <BarChart2 size={20} className="text-blue-600" />,
    title: 'Phân tích CV–JD tức thì',
    desc: 'So sánh hồ sơ với từng tin tuyển dụng, hiển thị kỹ năng đã đáp ứng và còn thiếu cụ thể.',
  },
  {
    icon: <Lightbulb size={20} className="text-blue-600" />,
    title: 'Skill Gap & Lộ trình học',
    desc: 'Phân tích khoảng trống kỹ năng và gợi ý lộ trình học theo mức ưu tiên phù hợp với thị trường.',
  },
  {
    icon: <CheckCircle2 size={20} className="text-blue-600" />,
    title: 'Theo dõi ứng tuyển',
    desc: 'Quản lý toàn bộ quá trình ứng tuyển từ lưu hồ sơ đến theo dõi trạng thái phỏng vấn.',
  },
];

const techCurrent = [
  { name: 'React 19', note: 'UI framework', color: 'badge-blue' },
  { name: 'TypeScript', note: 'Type safety', color: 'badge-blue' },
  { name: 'Tailwind CSS', note: 'Styling', color: 'badge-blue' },
  { name: 'Vite', note: 'Build tool', color: 'badge-blue' },
  { name: 'React Router', note: 'Navigation', color: 'badge-blue' },
  { name: 'Recharts', note: 'Biểu đồ', color: 'badge-blue' },
  { name: 'localStorage', note: 'Lưu trạng thái', color: 'badge-blue' },
];

const techFuture = [
  { name: 'FastAPI', note: 'Backend REST', color: 'badge-purple' },
  { name: 'Node.js', note: 'Backend alt.', color: 'badge-purple' },
  { name: 'PostgreSQL', note: 'Database', color: 'badge-purple' },
  { name: 'Redis', note: 'Caching', color: 'badge-purple' },
  { name: 'ETL Pipeline', note: 'Data processing', color: 'badge-purple' },
  { name: 'NLP / Skill Extraction', note: 'AI dự kiến', color: 'badge-yellow' },
  { name: 'Matching Algorithm', note: 'AI dự kiến', color: 'badge-yellow' },
  { name: 'Ranking Model', note: 'AI dự kiến', color: 'badge-yellow' },
];

export default function AboutPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto">
        <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Cpu size={28} className="text-white" />
        </div>
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Về SmartCareer</h1>
        <p className="text-slate-500">
          Hệ thống Tìm kiếm Việc làm Thông minh dành cho Sinh viên — Prototype phục vụ bài tập học phần
          "Thiết kế Ý tưởng Hệ thống & Chiến lược Thu thập Dữ liệu".
        </p>
      </div>

      {/* Target users */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-5">
          <Users size={20} className="text-blue-600" />
          <h2 className="text-lg font-bold text-slate-800">Đối tượng mục tiêu</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {targetUsers.map((u) => (
            <div key={u.title} className="p-4 bg-slate-50 border border-slate-100 rounded-xl">
              <div className="font-semibold text-sm text-slate-800 mb-1">{u.title}</div>
              <div className="text-xs text-slate-600 leading-relaxed">{u.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Problems */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-5">
          <AlertTriangle size={20} className="text-red-500" />
          <h2 className="text-lg font-bold text-slate-800">Vấn đề sinh viên gặp phải khi tìm việc</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {problems.map((p, i) => (
            <div key={i} className="flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-xl">
              <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shrink-0 shadow-sm border border-red-100">
                {p.icon}
              </div>
              <div>
                <div className="font-semibold text-sm text-slate-800 mb-0.5">{p.title}</div>
                <div className="text-xs text-slate-600 leading-relaxed">{p.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Solutions */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-5">
          <Lightbulb size={20} className="text-blue-600" />
          <h2 className="text-lg font-bold text-slate-800">Giải pháp SmartCareer đề xuất</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {solutions.map((s, i) => (
            <div key={i} className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-100 rounded-xl">
              <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shrink-0 shadow-sm border border-blue-100">
                {s.icon}
              </div>
              <div>
                <div className="font-semibold text-sm text-slate-800 mb-0.5">{s.title}</div>
                <div className="text-xs text-slate-600 leading-relaxed">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech stack */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Current */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-1">
            <Code2 size={18} className="text-blue-600" />
            <h2 className="font-bold text-slate-800">Công nghệ đang dùng</h2>
            <span className="badge-green ml-auto">Prototype</span>
          </div>
          <p className="text-xs text-slate-400 mb-4">Đang chạy trong bản demo này</p>
          <div className="flex flex-wrap gap-2">
            {techCurrent.map((t) => (
              <div key={t.name} className="flex items-center gap-1.5">
                <span className={t.color}>{t.name}</span>
                <span className="text-xs text-slate-400">{t.note}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Future */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-1">
            <Server size={18} className="text-purple-600" />
            <h2 className="font-bold text-slate-800">Công nghệ dự kiến</h2>
            <span className="badge-yellow ml-auto">Kế hoạch</span>
          </div>
          <p className="text-xs text-slate-400 mb-4">Cho phiên bản production trong tương lai</p>
          <div className="flex flex-wrap gap-2">
            {techFuture.map((t) => (
              <div key={t.name} className="flex items-center gap-1.5">
                <span className={t.color}>{t.name}</span>
                <span className="text-xs text-slate-400">{t.note}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Limitations */}
      <div className="card p-6 bg-slate-50 border-slate-200">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={18} className="text-slate-500" />
          <h2 className="font-bold text-slate-700">Giới hạn của Prototype hiện tại</h2>
        </div>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {[
            'Không có backend – toàn bộ chạy trên trình duyệt.',
            'Dữ liệu mẫu cố định, không thu thập từ nguồn thật.',
            'Ghép nối CV–JD đa tiêu chí dựa trên quy tắc, không phải AI thật.',
            'Không có xác thực người dùng thật.',
            'Điểm phù hợp không tính trọng số theo mức độ thành thạo.',
            'Không tích hợp API tuyển dụng bên ngoài.',
            'Tính năng tải CV chưa xử lý file thật.',
            'Gợi ý lộ trình học là dữ liệu mẫu, không cá nhân hóa.',
          ].map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-2 shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-slate-400 pb-4">
        SmartCareer Prototype v1.0 · Bài tập học phần Hệ thống Kinh doanh · 2026
      </div>
    </div>
  );
}
