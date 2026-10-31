import { useEffect, useState } from 'react';

/**
 * Giả lập thời gian tải ngắn mỗi khi `key` thay đổi.
 * Trả về true trong lúc "đang tải", false khi đã xong.
 *
 * Lưu lại `key` đã tải xong thay vì dùng cờ boolean, để không phải đặt state đồng bộ trong effect.
 */
export function useSimulatedLoading(key: unknown, delay = 350): boolean {
  const [readyKey, setReadyKey] = useState<unknown>(undefined);

  useEffect(() => {
    const timer = window.setTimeout(() => setReadyKey(key), delay);
    return () => window.clearTimeout(timer);
  }, [key, delay]);

  return readyKey !== key;
}
