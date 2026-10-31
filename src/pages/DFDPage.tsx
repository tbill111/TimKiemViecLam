import { Link } from 'react-router-dom';
import { Info, Maximize2 } from 'lucide-react';
import { dfdLevel0, dfdLevel1 } from '../data/dfdLayout';
import DfdSvg from '../components/data-flow/DfdSvg';

/**
 * Màn hình 9: Sơ đồ Luồng Dữ liệu (DFD) mức 0 và mức 1.
 * Bố cục nằm trong data/dfdLayout.ts và đã được kiểm tra tự động:
 * nhãn không đè đường nối hay nút, các đường nối không cắt nhau.
 */

const legendRows: { id: string; name: string; desc: string }[] = [
  { id: 'E1', name: 'Sinh viên', desc: 'Cung cấp hồ sơ, CV và yêu cầu tìm kiếm; nhận việc làm phù hợp và kỹ năng còn thiếu.' },
  { id: 'E2', name: 'Doanh nghiệp', desc: 'Cung cấp tin tuyển dụng và trạng thái hồ sơ; nhận danh sách ứng viên xếp hạng.' },
  { id: 'E3', name: 'Nguồn tuyển dụng ngoài', desc: 'Đối tác dữ liệu được cấp phép (API hoặc thỏa thuận), không tự ý thu thập.' },
  { id: 'E4', name: 'Nhà trường', desc: 'Cung cấp chương trình đào tạo; nhận báo cáo kỹ năng được yêu cầu và kỹ năng sinh viên còn thiếu.' },
  { id: 'P1', name: 'Tiếp nhận & kiểm tra', desc: 'Nhận dữ liệu từ bốn tác nhân, đọc CV, kiểm tra trường bắt buộc và định dạng.' },
  { id: 'P2', name: 'Làm sạch & chuẩn hóa', desc: 'Chuẩn hóa kỹ năng theo D3, địa điểm, hình thức; loại trùng. Bổ sung kỹ năng mới và khóa học vào D3.' },
  { id: 'P3', name: 'Lưu trữ & quản lý', desc: 'Ghi dữ liệu đã chuẩn hóa vào kho hồ sơ D1 và kho tin D2.' },
  { id: 'P4', name: 'Phân tích & ghép nối', desc: 'Đọc D1, D2, tính điểm phù hợp đa tiêu chí; ghi kết quả và hành vi vào D4.' },
  { id: 'P5', name: 'Trả kết quả & báo cáo', desc: 'Trả việc phù hợp cho sinh viên, ứng viên xếp hạng cho doanh nghiệp, báo cáo kỹ năng cho nhà trường.' },
  { id: 'D1', name: 'Hồ sơ & CV', desc: 'Hồ sơ sinh viên đã kiểm tra và chuẩn hóa.' },
  { id: 'D2', name: 'Tin tuyển dụng', desc: 'Tin tuyển dụng từ doanh nghiệp và đối tác, đã chuẩn hóa.' },
  { id: 'D3', name: 'Kỹ năng & khóa học', desc: 'Tên kỹ năng chuẩn, từ đồng nghĩa, lộ trình học; được P2 đọc và cập nhật.' },
  { id: 'D4', name: 'Kết quả & hành vi', desc: 'Kết quả ghép nối, lịch sử ứng tuyển và hành vi (lưu, ứng tuyển) khi người dùng đồng ý.' },
];

export default function DFDPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Sơ đồ Luồng Dữ liệu (DFD)</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Mức 0 cho thấy hệ thống trong bối cảnh; mức 1 chi tiết các tiến trình từ nguồn thu thập đến kết quả hiển thị.
        </p>
      </div>

      <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700">
        <Info size={16} className="shrink-0 mt-0.5" />
        <span>
          Đây là sơ đồ luồng dữ liệu, không phải sơ đồ kiến trúc kỹ thuật. P1–P3 tương ứng với Extract, Transform, Load ở
          màn hình Trung tâm Dữ liệu & ETL.
        </span>
      </div>

      {/* Legend */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Chú giải ký hiệu (Gane–Sarson)</h2>
        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-3">
            <div className="w-16 h-10 border-2 border-blue-600 rounded-md flex items-center justify-center bg-blue-50">
              <span className="text-xs font-bold text-blue-700">E</span>
            </div>
            <span className="text-xs text-slate-600">Tác nhân ngoài</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full border-2 border-orange-600 flex items-center justify-center bg-orange-50">
              <span className="text-xs font-bold text-orange-700">P</span>
            </div>
            <span className="text-xs text-slate-600">Tiến trình</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-20 h-10 flex flex-col justify-between">
              <div className="border-t-2 border-slate-500" />
              <div className="text-center text-xs font-bold text-slate-600">D</div>
              <div className="border-b-2 border-slate-500" />
            </div>
            <span className="text-xs text-slate-600">Kho dữ liệu</span>
          </div>
          <div className="flex items-center gap-3">
            <svg width="48" height="12" aria-hidden="true">
              <line x1="0" y1="6" x2="40" y2="6" stroke="#475569" strokeWidth="1.5" />
              <polygon points="40,2 48,6 40,10" fill="#475569" />
            </svg>
            <span className="text-xs text-slate-600">Luồng dữ liệu (xanh lá: kết quả trả ra)</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-blue-700">E1*</span>
            <span className="text-xs text-slate-600">Tác nhân vẽ lặp để sơ đồ gọn</span>
          </div>
        </div>
      </div>

      {[
        { level: 0, title: 'DFD mức 0 – Sơ đồ ngữ cảnh', diagram: dfdLevel0, minWidth: 640 },
        { level: 1, title: 'DFD mức 1', diagram: dfdLevel1, minWidth: 760 },
      ].map(({ level, title, diagram, minWidth }) => (
        <div key={level} className="card p-4">
          <div className="flex items-center justify-between gap-3 mb-2">
            <h2 className="section-title text-sm">{title}</h2>
            <Link to={`/dfd/view/${level}`} className="btn-ghost text-xs py-1.5">
              <Maximize2 size={14} />
              Toàn màn hình
            </Link>
          </div>
          <div className="overflow-x-auto">
            <DfdSvg diagram={diagram} idPrefix={`l${level}`} ariaLabel={title} minWidth={minWidth} />
          </div>
        </div>
      ))}

      {/* Description table */}
      <div className="card p-5">
        <h2 className="section-title text-sm mb-1">Mô tả các thành phần</h2>
        <p className="text-xs text-slate-400 mb-4">
          Mọi kho dữ liệu đều có luồng ghi vào và luồng đọc ra. Ba nhóm người dùng đều nhận lại kết quả qua P5.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left py-2 pr-4 font-semibold text-slate-600 text-xs uppercase">Ký hiệu</th>
                <th className="text-left py-2 pr-4 font-semibold text-slate-600 text-xs uppercase">Tên</th>
                <th className="text-left py-2 font-semibold text-slate-600 text-xs uppercase">Mô tả</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {legendRows.map((row) => (
                <tr key={row.id}>
                  <td className="py-2.5 pr-4">
                    <span className="badge-blue font-bold">{row.id}</span>
                  </td>
                  <td className="py-2.5 pr-4 font-medium text-slate-800 whitespace-nowrap">{row.name}</td>
                  <td className="py-2.5 text-slate-600 text-xs leading-relaxed">{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
