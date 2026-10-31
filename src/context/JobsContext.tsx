import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { Job, SkillMatchResult, StudentProfile } from '../types';
import { sampleJobs } from '../data/jobs';
import { calculateSkillMatch, getAllMatchScores, SUITABLE_THRESHOLD } from '../utils';
import { OFFLINE } from '../config';
import { useAuth } from './AuthContext';
import { aiApi, jobsApi } from '../api/endpoints';
import { toJob, toMatch } from '../api/adapters';
import { errorMessage } from '../api/client';
import type { ModelId } from '../api/dto';

interface JobsValue {
  /** Tin đang mở (online: từ API; demo: 12 tin mẫu). */
  jobs: Job[];
  /** Điểm khớp của hồ sơ hiện tại với từng tin (online: do mô hình ở backend tính). */
  matchScores: Map<string, SkillMatchResult>;
  /** Điểm khớp của một tin; tin chưa có trong bảng thì tính bằng quy tắc M0 cục bộ. */
  getMatch: (job: Job) => SkillMatchResult;
  suitableCount: number;
  loading: boolean;
  error: string | null;
  model: ModelId;
  setModel: (m: ModelId) => void;
  reload: () => void;
}

const JobsContext = createContext<JobsValue | null>(null);

/** `profile` đổi (kỹ năng, mong muốn) thì điểm khớp được tính lại. */
export function JobsProvider({ profile, children }: { profile: StudentProfile; children: ReactNode }) {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>(OFFLINE ? sampleJobs : []);
  const [remoteScores, setRemoteScores] = useState<Map<string, SkillMatchResult>>(new Map());
  const [loading, setLoading] = useState(!OFFLINE);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState<ModelId>('m3');
  const [tick, setTick] = useState(0);

  const isCandidate = user?.role === 'candidate';
  const profileKey = JSON.stringify([profile.skills, profile.preferredLocations, profile.preferredWorkTypes]);

  useEffect(() => {
    if (OFFLINE || !user) return;
    if (!isCandidate) {
      setLoading(false); // nhà tuyển dụng/quản trị dùng API riêng ở các trang /employer, không cần danh sách tin ứng viên
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const list = await jobsApi.list({ sort: 'newest' });
        if (cancelled) return;
        setJobs(list.items.map(toJob));
        const matches = await aiApi.matches(model);
        if (cancelled) return;
        setRemoteScores(new Map(matches.map((m) => [String(m.job_id), toMatch(m.match, String(m.job_id))])));
      } catch (e) {
        if (!cancelled) setError(errorMessage(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // profileKey: tính lại điểm khi hồ sơ đổi
  }, [user, isCandidate, model, profileKey, tick]);

  const matchScores = useMemo(() => (OFFLINE ? getAllMatchScores(profile, jobs) : remoteScores), [profile, jobs, remoteScores]);
  const getMatch = useCallback((job: Job) => matchScores.get(job.id) ?? calculateSkillMatch(profile, job), [matchScores, profile]);
  const suitableCount = useMemo(() => [...matchScores.values()].filter((m) => m.matchScore >= SUITABLE_THRESHOLD).length, [matchScores]);

  const value: JobsValue = { jobs, matchScores, getMatch, suitableCount, loading, error, model, setModel, reload: () => setTick((t) => t + 1) };
  return <JobsContext.Provider value={value}>{children}</JobsContext.Provider>;
}

export function useJobs(): JobsValue {
  const ctx = useContext(JobsContext);
  if (!ctx) throw new Error('useJobs phải nằm trong JobsProvider');
  return ctx;
}
