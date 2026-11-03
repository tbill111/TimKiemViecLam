import { createContext, useContext, useEffect, useMemo, useState, useCallback, type ReactNode } from 'react';
import type { Job, SkillMatchResult } from '../types';
import { sampleJobs } from '../data/jobs';
import { defaultStudentProfile } from '../data/profile';
import { getAllMatchScores } from '../utils';
import { fetchJobs } from '../api/jobs';
import { isOfflineDemo } from '../api/client';
import { fetchMatches } from '../api/candidates';
import { useAuth } from './AuthContext';

interface JobsContextValue {
  jobs: Job[];
  matchScores: Map<string, SkillMatchResult>;
  loading: boolean;
  error: string | null;
  reload: (params?: Record<string, string>) => Promise<void>;
  refreshMatches: () => Promise<void>;
}

const JobsContext = createContext<JobsContextValue | null>(null);

export function JobsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>(isOfflineDemo ? sampleJobs : []);
  const [loading, setLoading] = useState(!isOfflineDemo);
  const [error, setError] = useState<string | null>(null);
  const [onlineMatchScores, setOnlineMatchScores] = useState<Map<string, SkillMatchResult>>(new Map());

  const refreshMatches = useCallback(async () => {
    if (isOfflineDemo || user?.role !== 'candidate') return;
    try {
      const items = await fetchMatches();
      setOnlineMatchScores(new Map(items.map((item) => [item.jobId, item.match])));
    } catch (requestError: unknown) {
      setError(requestError instanceof Error ? requestError.message : 'Không tải được điểm phù hợp.');
    }
  }, [user]);

  const reload = useCallback(async (params?: Record<string, string>) => {
    if (isOfflineDemo) return;
    setLoading(true);
    setError(null);
    try {
      setJobs(await fetchJobs(params));
      await refreshMatches();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Không tải được danh sách việc làm.');
    } finally {
      setLoading(false);
    }
  }, [refreshMatches]);

  useEffect(() => { void reload(); }, [reload, user]);

  const matchScores = useMemo(
    () => isOfflineDemo ? getAllMatchScores(defaultStudentProfile, jobs) : onlineMatchScores,
    [jobs, onlineMatchScores]
  );

  return <JobsContext.Provider value={{ jobs, matchScores, loading, error, reload, refreshMatches }}>{children}</JobsContext.Provider>;
}

export function useJobs(): JobsContextValue {
  const context = useContext(JobsContext);
  if (!context) throw new Error('useJobs phải được gọi bên trong JobsProvider');
  return context;
}
