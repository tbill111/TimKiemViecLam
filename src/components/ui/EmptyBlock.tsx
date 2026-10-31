import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface EmptyBlockProps {
  title: string;
  hint?: string;
  action?: ReactNode;
}

/** Trạng thái rỗng dùng chung. */
export default function EmptyBlock({ title, hint, action }: EmptyBlockProps) {
  return (
    <div className="card p-12 text-center">
      <Inbox size={40} className="mx-auto text-slate-200 mb-3" />
      <h3 className="font-semibold text-slate-500 mb-1">{title}</h3>
      {hint && <p className="text-sm text-slate-400">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
