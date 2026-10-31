interface LoadingBlockProps {
  /** Số khối skeleton hiển thị. */
  rows?: number;
  /** Mô tả ngắn cho người dùng biết hệ thống đang làm gì. */
  message?: string;
}

/**
 * Trạng thái đang tải giả lập: khối skeleton kèm dòng chữ thông báo.
 */
export default function LoadingBlock({ rows = 3, message = 'Đang tải dữ liệu mô phỏng...' }: LoadingBlockProps) {
  return (
    <div role="status" aria-live="polite" className="space-y-3">
      <p className="text-sm text-slate-400">{message}</p>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="card p-5 space-y-3 animate-pulse">
          <div className="h-4 w-1/3 rounded bg-slate-200" />
          <div className="h-3 w-2/3 rounded bg-slate-100" />
          <div className="h-3 w-1/2 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}
