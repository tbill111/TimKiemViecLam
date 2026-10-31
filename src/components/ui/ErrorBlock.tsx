import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorBlockProps {
  message: string;
  onRetry?: () => void;
}

/** Trạng thái lỗi dùng chung: thông báo tiếng Việt kèm nút thử lại. */
export default function ErrorBlock({ message, onRetry }: ErrorBlockProps) {
  return (
    <div role="alert" className="card p-6 flex items-start gap-3 border-red-100 bg-red-50/60">
      <AlertCircle size={18} className="text-red-500 shrink-0 mt-0.5" />
      <div className="flex-1 text-sm text-red-700">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary text-xs py-1.5 shrink-0">
          <RefreshCw size={13} />
          Thử lại
        </button>
      )}
    </div>
  );
}
