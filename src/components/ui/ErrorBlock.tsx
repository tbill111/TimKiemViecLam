interface ErrorBlockProps { message: string; onRetry?: () => void }
export default function ErrorBlock({ message, onRetry }: ErrorBlockProps) {
  return <div role="alert" className="card p-8 text-center"><p className="text-sm text-red-600">{message}</p>{onRetry && <button className="btn-secondary mt-3" onClick={onRetry}>Thử lại</button>}</div>;
}
