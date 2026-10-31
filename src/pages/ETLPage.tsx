import React, { useMemo, useState } from 'react';
import {
  Database,
  ArrowRight,
  CheckCircle2,
  Users,
  Building2,
  Globe,
  Tags,
  FileInput,
  Upload,
  Copy,
  AlertCircle,
  Flag,
  MapPin,
  UserCircle,
  Briefcase,
  Star,
  Link,
  Info,
  Activity,
  GraduationCap,
  PlayCircle,
} from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import type { UseAppState } from '../hooks/useAppState';
import type { PipelineStatus } from '../types';
import { sampleJobs } from '../data/jobs';
import { dataSources, etlSteps } from '../data/etl';
import { rawJobFeed } from '../data/rawJobFeed';
import { getDataQualityMetrics, getSourceRecordCounts } from '../utils';
import { runCleaningPipeline } from '../utils/etlPipeline';

const pipelineBadge: Record<PipelineStatus, { label: string; className: string }> = {
  clean: { label: 'Sạch', className: 'badge-green' },
  rejected: { label: 'Bị loại', className: 'badge-red' },
  duplicate: { label: 'Trùng lặp', className: 'badge-yellow' },
  expired: { label: 'Hết hạn', className: 'badge-gray' },
};

interface ETLPageProps {
  appState: UseAppState;
}

const statusLabel: Record<string, string> = {
  active: 'Hoạt động',
  pending: 'Chờ thỏa thuận',
  inactive: 'Tạm dừng',
};

const statusBadge: Record<string, string> = {
  active: 'badge-green',
  pending: 'badge-yellow',
  inactive: 'badge-gray',
};

const sourceIcons: Record<string, React.ReactNode> = {
  'ds-001': <Users size={20} className="text-blue-600" />,
  'ds-002': <Building2 size={20} className="text-emerald-600" />,
  'ds-003': <Globe size={20} className="text-purple-600" />,
  'ds-004': <Tags size={20} className="text-amber-600" />,
  'ds-005': <Activity size={20} className="text-rose-600" />,
  'ds-006': <GraduationCap size={20} className="text-sky-600" />,
};

const sourceColors: Record<string, string> = {
  'ds-001': 'border-blue-200 bg-blue-50',
  'ds-002': 'border-emerald-200 bg-emerald-50',
  'ds-003': 'border-purple-200 bg-purple-50',
  'ds-004': 'border-amber-200 bg-amber-50',
  'ds-005': 'border-rose-200 bg-rose-50',
  'ds-006': 'border-sky-200 bg-sky-50',
};

const stepIconMap: Record<string, React.ReactNode> = {
  FileInput: <FileInput size={16} />,
  Building2: <Building2 size={16} />,
  Upload: <Upload size={16} />,
  Globe: <Globe size={16} />,
  CheckCircle: <CheckCircle2 size={16} />,
  Tags: <Tags size={16} />,
  MapPin: <MapPin size={16} />,
  Copy: <Copy size={16} />,
  AlertCircle: <AlertCircle size={16} />,
  Flag: <Flag size={16} />,
  UserCircle: <UserCircle size={16} />,
  Briefcase: <Briefcase size={16} />,
  Star: <Star size={16} />,
  Link: <Link size={16} />,
};

type ActiveSection = 'sources' | 'extract' | 'transform' | 'load' | 'pipeline' | 'quality';
const SECTION_IDS: ActiveSection[] = ['sources', 'extract', 'transform', 'load', 'pipeline', 'quality'];

export default function ETLPage({ appState }: ETLPageProps) {
  // Cho phép mở thẳng một tab qua đường dẫn, ví dụ /etl?tab=pipeline
  const [searchParams] = useSearchParams();
  const tabParam = searchParams.get('tab') as ActiveSection | null;
  const [activeSection, setActiveSection] = useState<ActiveSection>(
    tabParam && SECTION_IDS.includes(tabParam) ? tabParam : 'sources'
  );
  const { studentProfile, savedJobs, applications } = appState;

  const pipeline = useMemo(() => runCleaningPipeline(rawJobFeed), []);
  const recordCounts = useMemo(
    () => getSourceRecordCounts(studentProfile, sampleJobs, savedJobs.length + applications.length),
    [studentProfile, savedJobs.length, applications.length]
  );
  const quality = useMemo(() => getDataQualityMetrics(studentProfile, sampleJobs), [studentProfile]);
  const qualityPercent = quality.totalRecords > 0 ? Math.round((quality.validRecords / quality.totalRecords) * 100) : 0;

  const sections: { id: ActiveSection; label: string; color: string }[] = [
    { id: 'sources', label: 'Nguồn Dữ liệu', color: 'bg-blue-600' },
    { id: 'extract', label: 'Extract', color: 'bg-purple-600' },
    { id: 'transform', label: 'Transform', color: 'bg-amber-500' },
    { id: 'load', label: 'Load', color: 'bg-emerald-600' },
    { id: 'pipeline', label: 'Chạy thử làm sạch', color: 'bg-rose-600' },
    { id: 'quality', label: 'Chỉ số Chất lượng', color: 'bg-slate-600' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Trung tâm Dữ liệu & Quy trình ETL</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Kiến trúc dữ liệu dự kiến của hệ thống SmartCareer.
        </p>
      </div>

      <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-100 rounded-xl text-sm text-amber-700">
        <Info size={16} className="shrink-0 mt-0.5" />
        <span>
          <strong>Lưu ý:</strong> Đây là kiến trúc dự kiến cho hệ thống hoàn chỉnh trong tương lai.
          Prototype hiện tại sử dụng dữ liệu mẫu ở frontend, <strong>chưa có pipeline ETL hay cơ sở dữ liệu backend thực tế</strong>.
        </span>
      </div>

      {/* ETL Pipeline visualization */}
      <div className="card p-5">
        <h2 className="section-title mb-4">Luồng ETL tổng quan</h2>
        <div className="flex items-center gap-3 overflow-x-auto pb-2">
          {[
            { label: 'Nguồn Dữ liệu', icon: <Database size={20} />, color: 'bg-blue-100 text-blue-700', border: 'border-blue-200' },
            { label: 'Extract', icon: <FileInput size={20} />, color: 'bg-purple-100 text-purple-700', border: 'border-purple-200' },
            { label: 'Transform', icon: <Tags size={20} />, color: 'bg-amber-100 text-amber-700', border: 'border-amber-200' },
            { label: 'Load', icon: <Upload size={20} />, color: 'bg-emerald-100 text-emerald-700', border: 'border-emerald-200' },
          ].map((step, i) => (
            <React.Fragment key={step.label}>
              <div className={`flex flex-col items-center gap-2 p-4 rounded-xl border ${step.border} ${step.color} min-w-[100px]`}>
                {step.icon}
                <span className="text-xs font-semibold whitespace-nowrap">{step.label}</span>
              </div>
              {i < 3 && <ArrowRight size={20} className="text-slate-300 shrink-0" />}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Section tabs */}
      <div className="flex flex-wrap gap-2">
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => setActiveSection(s.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
              activeSection === s.id
                ? `${s.color} text-white border-transparent`
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Sources */}
      {activeSection === 'sources' && (
        <div>
          <h2 className="section-title mb-4">Sáu nhóm Nguồn Dữ liệu</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dataSources.map((source) => (
              <div key={source.id} className={`card p-5 border ${sourceColors[source.id]}`}>
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-sm border border-white">
                    {sourceIcons[source.id]}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-slate-800 text-sm">{source.name}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={statusBadge[source.status]}>
                        {statusLabel[source.status]}
                      </span>
                      <span className="text-xs text-slate-400">
                        {(recordCounts[source.id] ?? 0).toLocaleString()} bản ghi mẫu
                      </span>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-2">{source.description}</p>
                <p className="text-xs text-slate-500 mb-3">
                  <span className="font-semibold">Định dạng:</span> {source.format}
                </p>
                <div>
                  <div className="text-xs font-semibold text-slate-500 mb-1.5">Các trường dữ liệu:</div>
                  <div className="flex flex-wrap gap-1">
                    {source.fields.map((f) => (
                      <span key={f} className="badge-gray">{f}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extract */}
      {activeSection === 'extract' && (
        <div>
          <h2 className="section-title mb-1">Extract – Thu thập dữ liệu</h2>
          <p className="text-sm text-slate-500 mb-4">Nhận và tiếp nhận dữ liệu từ các nguồn khác nhau vào hệ thống.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {etlSteps.extract.map((step) => (
              <div key={step.id} className="card p-5 border-l-4 border-l-purple-400">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-purple-50 text-purple-600 rounded-lg flex items-center justify-center">
                    {stepIconMap[step.icon]}
                  </div>
                  <h3 className="font-semibold text-sm text-slate-800">{step.title}</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transform */}
      {activeSection === 'transform' && (
        <div>
          <h2 className="section-title mb-1">Transform – Làm sạch & Chuẩn hóa</h2>
          <p className="text-sm text-slate-500 mb-4">Kiểm tra, làm sạch và chuẩn hóa dữ liệu trước khi lưu trữ.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {etlSteps.transform.map((step) => (
              <div key={step.id} className="card p-5 border-l-4 border-l-amber-400">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-amber-50 text-amber-600 rounded-lg flex items-center justify-center">
                    {stepIconMap[step.icon]}
                  </div>
                  <h3 className="font-semibold text-sm text-slate-800">{step.title}</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Load */}
      {activeSection === 'load' && (
        <div>
          <h2 className="section-title mb-1">Load – Lưu trữ vào Kho dữ liệu</h2>
          <p className="text-sm text-slate-500 mb-4">Dữ liệu đã chuẩn hóa được lưu vào các bảng tương ứng trong cơ sở dữ liệu dự kiến.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {etlSteps.load.map((step) => (
              <div key={step.id} className="card p-5 border-l-4 border-l-emerald-400">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center">
                    {stepIconMap[step.icon]}
                  </div>
                  <h3 className="font-semibold text-sm text-slate-800">{step.title}</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <div className="text-xs text-slate-400 font-medium mb-2">Kho dữ liệu dự kiến (PostgreSQL)</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {['profiles', 'jobs', 'skills', 'applications'].map((table) => (
                <div key={table} className="flex items-center gap-2 text-xs text-slate-600 bg-white p-2 rounded-lg border border-slate-100">
                  <Database size={12} className="text-slate-400" />
                  {table}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Pipeline: chạy thật các quy tắc làm sạch trên dữ liệu thô */}
      {activeSection === 'pipeline' && (
        <div className="space-y-4">
          <div>
            <h2 className="section-title mb-1 flex items-center gap-2">
              <PlayCircle size={18} className="text-rose-600" />
              Chạy thử quy trình làm sạch
            </h2>
            <p className="text-sm text-slate-500">
              {pipeline.summary.total} bản ghi thô gom từ ba nguồn, cố tình chứa lỗi thường gặp. Quy tắc được áp dụng
              theo thứ tự: kiểm tra trường bắt buộc → chuẩn hóa → loại trùng → kiểm tra hạn nộp.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            {[
              { label: 'Bản ghi thô', value: pipeline.summary.total, color: 'text-slate-800' },
              { label: 'Giữ lại (sạch)', value: pipeline.summary.clean, color: 'text-emerald-600' },
              { label: 'Thiếu hoặc sai', value: pipeline.summary.rejected, color: 'text-red-500' },
              { label: 'Trùng lặp', value: pipeline.summary.duplicate, color: 'text-amber-500' },
              { label: 'Hết hạn', value: pipeline.summary.expired, color: 'text-slate-500' },
              { label: 'Trường chuẩn hóa', value: pipeline.summary.normalizedFields, color: 'text-blue-600' },
            ].map((m) => (
              <div key={m.label} className="stat-card">
                <div className="text-xs text-slate-400 uppercase tracking-wide">{m.label}</div>
                <div className={`text-3xl font-bold ${m.color}`}>{m.value}</div>
              </div>
            ))}
          </div>

          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-500">
                  <th className="py-2.5 px-3">Mã</th>
                  <th className="py-2.5 px-3">Nguồn</th>
                  <th className="py-2.5 px-3">Vị trí – Công ty (thô)</th>
                  <th className="py-2.5 px-3">Kết quả</th>
                  <th className="py-2.5 px-3">Thay đổi hoặc lý do</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {pipeline.records.map((r) => (
                  <tr key={r.raw.id} className="align-top">
                    <td className="py-2.5 px-3 text-xs text-slate-400 whitespace-nowrap">{r.raw.id}</td>
                    <td className="py-2.5 px-3 text-xs text-slate-600 whitespace-nowrap">{r.raw.source}</td>
                    <td className="py-2.5 px-3 text-xs text-slate-800">
                      {r.raw.title || <span className="italic text-red-500">(trống)</span>} – {r.raw.company}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={pipelineBadge[r.status].className}>{pipelineBadge[r.status].label}</span>
                    </td>
                    <td className="py-2.5 px-3 text-xs text-slate-600">
                      {r.reason && <div className="font-medium text-slate-700">{r.reason}</div>}
                      {r.status === 'clean' && r.changes.length === 0 && <div className="text-slate-400">Không cần thay đổi</div>}
                      {r.status !== 'rejected' && r.changes.map((c) => <div key={c}>{c}</div>)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-400 italic">
            * Dữ liệu thô là dữ liệu minh họa. Các quy tắc chạy thật trên trình duyệt; bảng từ đồng nghĩa kỹ năng dùng chung với chức năng nhập CV.
          </p>
        </div>
      )}

      {/* Quality */}
      {activeSection === 'quality' && (
        <div>
          <h2 className="section-title mb-1">Chỉ số Chất lượng Dữ liệu</h2>
          <p className="text-sm text-slate-500 mb-4">
            Số liệu được tính trực tiếp từ dataset mẫu đang dùng trong ứng dụng, tức dữ liệu đầu ra sau khi đã làm sạch.
            Xem tab "Chạy thử làm sạch" để thấy số liệu trước và sau. <span className="italic">Không phải dữ liệu thật thu thập từ nguồn ngoài.</span>
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="stat-card">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Tổng bản ghi</div>
              <div className="text-3xl font-bold text-slate-800">{quality.totalRecords.toLocaleString()}</div>
              <div className="text-xs text-slate-400">Tin mẫu + hồ sơ</div>
            </div>
            <div className="stat-card">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Bản ghi hợp lệ</div>
              <div className="text-3xl font-bold text-emerald-600">{quality.validRecords.toLocaleString()}</div>
              <div className="text-xs text-emerald-500">{qualityPercent}% tổng số</div>
            </div>
            <div className="stat-card">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Trùng lặp</div>
              <div className="text-3xl font-bold text-amber-500">{quality.duplicateRecords}</div>
              <div className="text-xs text-slate-400">Đã phát hiện & loại</div>
            </div>
            <div className="stat-card">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Thiếu thông tin</div>
              <div className="text-3xl font-bold text-red-500">{quality.missingFieldRecords}</div>
              <div className="text-xs text-slate-400">Cần bổ sung</div>
            </div>
          </div>

          <div className="card p-5">
            <h3 className="section-title text-sm mb-3">Tỷ lệ Chất lượng Tổng thể</h3>
            <div className="progress-bar h-4 mb-2">
              <div
                className="progress-fill bg-emerald-500"
                style={{ width: `${qualityPercent}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500">
              <span>Hợp lệ: {quality.validRecords}</span>
              <span className="font-semibold text-emerald-600">{qualityPercent}%</span>
              <span>Tổng: {quality.totalRecords}</span>
            </div>
            <p className="text-xs text-slate-400 italic mt-3">
              * Các chỉ số được kiểm tra theo quy tắc Transform trên dataset mẫu của prototype. Không có dữ liệu thật được thu thập.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
