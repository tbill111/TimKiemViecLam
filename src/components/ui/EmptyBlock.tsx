export default function EmptyBlock({ message = 'Chưa có dữ liệu.' }: { message?: string }) {
  return <div className="card p-8 text-center text-sm text-slate-400">{message}</div>;
}
