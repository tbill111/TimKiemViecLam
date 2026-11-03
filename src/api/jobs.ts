import type { Job } from '../types';
import { apiClient } from './client';
import type { JobsResponseDto } from './dto';
import { adaptJob } from './adapters';

const PAGE_SIZE = 100; // backend giới hạn tối đa 100 tin/trang

type JobsPayload = (JobsResponseDto & { page?: number; page_size?: number }) | unknown[];

/** Tải toàn bộ tin (nhiều trang nếu cần) để danh sách và thống kê không bị cắt ở 100 tin. */
export async function fetchJobs(params?: Record<string, string>): Promise<Job[]> {
  const items: unknown[] = [];
  let page = 1;
  for (;;) {
    const response = await apiClient.get<JobsPayload>('/jobs', { params: { page_size: String(PAGE_SIZE), ...params, page: String(page) } });
    const data = response.data;
    if (Array.isArray(data)) return data.map((item) => adaptJob(item as Parameters<typeof adaptJob>[0]));
    items.push(...data.items);
    const total = data.total ?? items.length;
    if (data.items.length === 0 || items.length >= total) break;
    page += 1;
  }
  return items.map((item) => adaptJob(item as Parameters<typeof adaptJob>[0]));
}
