import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { Job, SkillMatchResult } from '../types';
import { sampleJobs } from '../data/jobs';
import { defaultStudentProfile } from '../data/profile';
import { calculateSkillMatch, getAllMatchScores } from '../utils';
import { fetchJobs } from '../api/jobs';
import { isOfflineDemo } from '../api/client';

interface JobsContextValue {
  jobs: Job[];
  matchScores: Map<string, SkillMatchResult>;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

const JobsContext = createContext<JobsContextValue | null>(null);

export function JobsProvider({ children }: { children: ReactNode }) {
  const [jobs, setJobs] = useState<Job[]>(isOfflineDemo ? sampleJobs : []);
  const [loading, setLoading] = useState(!isOfflineDemo);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    if (isOfflineDemo) return;
    setLoading(true);
    setError(null);
    try {
      setJobs(await fetchJobs());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Không tải được danh sách việc làm.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
  }, []);

  const matchScores = useMemo(
    () => isOfflineDemo ? getAllMatchScores(defaultStudentProfile, jobs) : new Map(jobs.map((job) => [job.id, calculateSkillMatch(defaultStudentProfile, job)])),
    [jobs]
  );

  return <JobsContext.Provider value={{ jobs, matchScores, loading, error, reload }}>{children}</JobsContext.Provider>;
}

export function useJobs(): JobsContextValue {
  const context = useContext(JobsContext);
  if (!context) throw new Error('useJobs phải được gọi bên trong JobsProvider');
  return context;
}
