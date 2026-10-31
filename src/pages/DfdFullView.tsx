import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { dfdLevel0, dfdLevel1 } from '../data/dfdLayout';
import DfdSvg from '../components/data-flow/DfdSvg';

/**
 * Xem một sơ đồ DFD toàn màn hình, không có thanh điều hướng.
 * Dùng khi trình chiếu hoặc chụp hình minh họa cho báo cáo.
 */
export default function DfdFullView() {
  const { level } = useParams();
  const isLevel0 = level === '0';
  const diagram = isLevel0 ? dfdLevel0 : dfdLevel1;
  const title = isLevel0 ? 'DFD mức 0 – Sơ đồ ngữ cảnh' : 'DFD mức 1 – SmartCareer';

  return (
    <div className="min-h-screen bg-white px-6 py-4">
      <div className="flex items-center justify-between mb-2 print:hidden">
        <h1 className="text-lg font-bold text-slate-900">{title}</h1>
        <Link to="/dfd" className="btn-ghost text-xs py-1.5">
          <ArrowLeft size={14} />
          Quay lại
        </Link>
      </div>
      <DfdSvg diagram={diagram} idPrefix={`full${isLevel0 ? 0 : 1}`} ariaLabel={title} minWidth={0} />
    </div>
  );
}
