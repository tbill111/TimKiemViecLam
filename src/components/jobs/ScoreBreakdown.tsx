import type { SkillMatchResult } from '../../types';
import { MATCH_WEIGHTS } from '../../utils';

interface ScoreBreakdownProps {
  result: SkillMatchResult;
  /** Bản gọn: chữ nhỏ hơn, không có dòng giải thích. */
  compact?: boolean;
}

const barColor = (score: number) => {
  if (score >= 80) return 'bg-emerald-500';
  if (score >= 50) return 'bg-blue-500';
  if (score >= 25) return 'bg-amber-500';
  return 'bg-slate-400';
};

/**
 * Hiển thị ba thành phần của điểm phù hợp và trọng số của từng phần,
 * để người dùng thấy vì sao có con số tổng.
 */
export default function ScoreBreakdown({ result, compact = false }: ScoreBreakdownProps) {
  const preferredTotal = result.matchedPreferred.length + result.missingPreferred.length;
  const rows = [
    {
      label: 'Kỹ năng bắt buộc',
      weight: MATCH_WEIGHTS.required,
      score: result.requiredScore,
      detail: `${result.matchedSkills.length}/${result.totalRequired} kỹ năng`,
    },
    {
      label: 'Kỹ năng ưu tiên',
      weight: MATCH_WEIGHTS.preferred,
      score: result.preferredScore,
      detail: preferredTotal === 0 ? 'Không yêu cầu' : `${result.matchedPreferred.length}/${preferredTotal} kỹ năng`,
    },
    {
      label: 'Mong muốn',
      weight: MATCH_WEIGHTS.preference,
      score: result.preferenceScore,
      detail: `Địa điểm ${result.locationMatch ? 'khớp' : 'không khớp'} · Hình thức ${result.workTypeMatch ? 'khớp' : 'không khớp'}`,
    },
  ];

  return (
    <div className={compact ? 'space-y-2' : 'space-y-3'}>
      {rows.map((row) => (
        <div key={row.label}>
          <div className={`flex items-center justify-between gap-2 ${compact ? 'text-xs' : 'text-sm'}`}>
            <span className="font-medium text-slate-700">
              {row.label} <span className="text-slate-400 font-normal">({Math.round(row.weight * 100)}%)</span>
            </span>
            <span className="font-semibold text-slate-800">{row.score}%</span>
          </div>
          <div className="progress-bar h-1.5 mt-1">
            <div className={`progress-fill ${barColor(row.score)}`} style={{ width: `${row.score}%` }} />
          </div>
          {!compact && <div className="text-xs text-slate-400 mt-1">{row.detail}</div>}
        </div>
      ))}
      {!compact && (
        <p className="text-xs text-slate-500 pt-1 border-t border-slate-100">
          Điểm tổng = 60% × bắt buộc + 25% × ưu tiên + 15% × mong muốn ={' '}
          <span className="font-semibold text-slate-700">{result.matchScore}%</span>
        </p>
      )}
    </div>
  );
}
