import { useState } from 'react';
import { FileUp, Info, CheckCircle2, AlertCircle, Download, Link2 } from 'lucide-react';
import type { StudentProfile } from '../../types';
import { hasSkill } from '../../utils';
import { extractFromCv, readCvText, type CvExtraction } from '../../utils/cvParser';
import { OFFLINE } from '../../config';
import { resumeApi } from '../../api/endpoints';
import { errorMessage } from '../../api/client';

interface CvImportProps {
  profile: StudentProfile;
  /** Không cho nhập khi đang ở chế độ chỉnh sửa hồ sơ để tránh ghi đè lẫn nhau. */
  disabled: boolean;
  onApply: (patch: Partial<StudentProfile>) => void;
}

type Status = 'idle' | 'reading' | 'done' | 'error';

/**
 * Nhập kỹ năng từ CV: đọc tệp ngay trên trình duyệt, dò kỹ năng theo danh mục,
 * người dùng chọn kỹ năng nào được thêm vào hồ sơ.
 */
export default function CvImport({ profile, disabled, onApply }: CvImportProps) {
  const [status, setStatus] = useState<Status>('idle');
  const [fileName, setFileName] = useState('');
  const [charCount, setCharCount] = useState(0);
  const [result, setResult] = useState<CvExtraction | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [keepLinks, setKeepLinks] = useState(true);
  const [error, setError] = useState('');
  const [applied, setApplied] = useState('');
  // Chế độ online: người dùng phải đồng ý cho hệ thống xử lý CV; nguồn của từng kỹ năng để phân biệt gợi ý độ tin cậy thấp
  const [consent, setConsent] = useState(false);
  const [sources, setSources] = useState<Record<string, string>>({});

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    setApplied('');
    setError('');
    if (!OFFLINE && !consent) {
      setError('Bạn cần tích vào ô đồng ý để hệ thống xử lý dữ liệu CV.');
      setStatus('error');
      return;
    }
    setStatus('reading');
    setFileName(file.name);
    try {
      if (!OFFLINE) {
        const uploaded = await resumeApi.upload(file, consent);
        const extraction: CvExtraction = { skills: uploaded.skills.map((s) => s.name) };
        setCharCount(0);
        setResult(extraction);
        setSources(Object.fromEntries(uploaded.skills.map((s) => [s.name, s.source])));
        setSelected(new Set(extraction.skills.filter((s) => !hasSkill(profile.skills, s))));
        setStatus('done');
        return;
      }
      const text = await readCvText(file);
      if (text.trim().length === 0) {
        throw new Error('Không đọc được chữ trong tệp. Tệp có thể là ảnh scan.');
      }
      const extraction = extractFromCv(text);
      setCharCount(text.trim().length);
      setResult(extraction);
      // Mặc định chọn sẵn các kỹ năng chưa có trong hồ sơ
      setSelected(new Set(extraction.skills.filter((s) => !hasSkill(profile.skills, s))));
      setStatus('done');
    } catch (e) {
      setError(OFFLINE ? (e instanceof Error ? e.message : 'Không đọc được tệp.') : errorMessage(e));
      setStatus('error');
    }
  };

  const toggle = (skill: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(skill)) next.delete(skill);
      else next.add(skill);
      return next;
    });

  const apply = () => {
    if (!result) return;
    const added = [...selected];
    const patch: Partial<StudentProfile> = { skills: [...profile.skills, ...added] };
    if (keepLinks) {
      if (result.githubUrl) patch.githubUrl = result.githubUrl;
      if (result.linkedinUrl) patch.linkedinUrl = result.linkedinUrl;
    }
    onApply(patch);
    setApplied(
      added.length > 0
        ? `Đã thêm ${added.length} kỹ năng: ${added.join(', ')}. Điểm phù hợp đã được tính lại.`
        : 'Đã lưu liên kết. Không có kỹ năng mới được thêm.'
    );
    setSelected(new Set());
  };

  const hasLinks = Boolean(result?.githubUrl || result?.linkedinUrl);

  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-1">
        <FileUp size={16} className="text-blue-600" />
        <h2 className="section-title text-xs">Nhập kỹ năng từ CV</h2>
      </div>
      <p className="text-xs text-slate-500 mb-3">
        Đọc CV PDF, DOCX hoặc TXT và dò kỹ năng theo danh mục. Hồ sơ LinkedIn lưu dạng PDF cũng dùng được.
      </p>

      <div className="flex flex-wrap gap-2">
        <label
          className={`btn-primary text-xs py-1.5 ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          aria-disabled={disabled}
        >
          <FileUp size={14} />
          Chọn tệp CV
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            className="sr-only"
            disabled={disabled}
            onChange={(e) => {
              void handleFile(e.target.files?.[0]);
              e.target.value = '';
            }}
          />
        </label>
        <a href={`${import.meta.env.BASE_URL}cv-mau.pdf`} download className="btn-secondary text-xs py-1.5">
          <Download size={14} />
          CV mẫu
        </a>
      </div>
      {!OFFLINE && (
        <label className="flex items-start gap-2 text-xs text-slate-600 mt-3">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
          <span>
            Tôi đồng ý để hệ thống lưu và phân tích CV nhằm gợi ý việc làm. Tôi có thể xóa hồ sơ bất kỳ lúc nào.
          </span>
        </label>
      )}
      {disabled && <p className="text-xs text-amber-600 mt-2">Lưu hoặc hủy chỉnh sửa hồ sơ trước khi nhập CV.</p>}

      {status === 'reading' && (
        <p role="status" className="text-xs text-slate-500 mt-3 animate-pulse">Đang đọc {fileName}...</p>
      )}

      {status === 'error' && (
        <div className="flex items-start gap-2 mt-3 p-2.5 bg-red-50 border border-red-100 rounded-lg text-xs text-red-700">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {status === 'done' && result && (
        <div className="mt-3 space-y-3">
          <p className="text-xs text-slate-600">
            Đã đọc <strong>{fileName}</strong>{charCount > 0 && ` (${charCount.toLocaleString()} ký tự)`}. Phát hiện{' '}
            <strong>{result.skills.length}</strong> kỹ năng.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {result.skills.map((skill) => {
              const owned = hasSkill(profile.skills, skill);
              const isOn = selected.has(skill);
              if (owned) {
                return (
                  <span key={skill} className="badge-gray" title="Đã có trong hồ sơ">
                    {skill} · đã có
                  </span>
                );
              }
              return (
                <button
                  key={skill}
                  onClick={() => toggle(skill)}
                  aria-pressed={isOn}
                  className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                    isOn ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-white text-slate-500 border-slate-200'
                  }`}
                >
                  {isOn ? '✓ ' : '+ '}
                  {skill}
                  {sources[skill] === 'embedding' && <span className="ml-1 text-amber-600" title="Gợi ý độ tin cậy thấp, hãy kiểm tra lại">(gợi ý)</span>}
                  {sources[skill] === 'fuzzy' && <span className="ml-1 text-slate-400" title="Đã sửa lỗi chính tả">(đã sửa)</span>}
                </button>
              );
            })}
            {result.skills.length === 0 && <span className="text-xs text-slate-400">Không tìm thấy kỹ năng nào trong danh mục.</span>}
          </div>

          {hasLinks && (
            <label className="flex items-start gap-2 text-xs text-slate-600">
              <input type="checkbox" checked={keepLinks} onChange={(e) => setKeepLinks(e.target.checked)} className="mt-0.5" />
              <span>
                <Link2 size={12} className="inline mr-1" />
                Lưu liên kết tìm thấy: {[result.githubUrl, result.linkedinUrl].filter(Boolean).join(', ')}
              </span>
            </label>
          )}

          <button onClick={apply} className="btn-primary text-xs py-1.5 w-full justify-center">
            Thêm {selected.size} kỹ năng vào hồ sơ
          </button>
        </div>
      )}

      {applied && (
        <div className="flex items-start gap-2 mt-3 p-2.5 bg-emerald-50 border border-emerald-100 rounded-lg text-xs text-emerald-700">
          <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
          {applied}
        </div>
      )}

      <p className="flex items-start gap-1.5 text-xs text-slate-400 mt-3">
        <Info size={12} className="shrink-0 mt-0.5" />
        {OFFLINE
          ? 'Tệp chỉ được đọc trên trình duyệt, không gửi lên máy chủ và không được lưu. Chỉ kỹ năng bạn chọn mới được lưu. Kỹ năng được dò theo danh mục từ khóa, không phải mô hình AI.'
          : 'CV được gửi lên máy chủ để phân tích (từ điển kỹ năng, so khớp mờ và embedding). Kỹ năng được đề xuất để bạn xác nhận; chỉ kỹ năng bạn chọn mới tính vào hồ sơ.'}
      </p>
    </div>
  );
}
