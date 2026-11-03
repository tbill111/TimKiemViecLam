import { useState, useCallback, useEffect } from 'react';
import type { AppState, Application, StudentProfile, SkillGapItem } from '../types';
import { defaultStudentProfile } from '../data/profile';
import { defaultSkillGapItems } from '../data/skillGap';
import { calculateProfileCompletion } from '../utils';
import { isOfflineDemo } from '../api/client';
import { fetchApplications, createApplication, updateApplicationStatus as updateApplicationStatusRequest } from '../api/applications';
import { fetchSavedJobs, saveJob as saveJobRequest, unsaveJob as unsaveJobRequest } from '../api/savedJobs';
import { fetchProfile, updateProfile as updateProfileRequest } from '../api/candidates';
import { useAuth } from '../context/AuthContext';

const STORAGE_KEY = 'smartcareer_app_state';

const defaultState: AppState = {
  savedJobs: [],
  applications: [],
  studentProfile: defaultStudentProfile,
  skillGapItems: defaultSkillGapItems,
};

function emptyOnlineProfile(profile: StudentProfile): StudentProfile {
  return {
    ...profile,
    fullName: profile.fullName ?? '',
    university: profile.university ?? '',
    major: profile.major ?? '',
    year: profile.year ?? '',
    email: profile.email ?? '',
    careerGoal: profile.careerGoal ?? '',
    projects: profile.projects ?? [],
    experience: profile.experience ?? [],
    certificates: profile.certificates ?? [],
    skills: profile.skills ?? [],
    preferredLocations: profile.preferredLocations ?? [],
    preferredWorkTypes: profile.preferredWorkTypes ?? [],
    languages: profile.languages ?? [],
    profileCompletion: calculateProfileCompletion(profile),
  };
}

function loadState(): AppState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState;
    const saved = JSON.parse(raw) as Partial<AppState>;
    // Gộp với hồ sơ mặc định để dữ liệu lưu từ phiên bản cũ vẫn có đủ các trường mới
    return {
      ...defaultState,
      ...saved,
      studentProfile: { ...defaultStudentProfile, ...saved.studentProfile },
    };
  } catch {
    return defaultState;
  }
}

function saveState(state: AppState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore localStorage errors
  }
}

export function useAppState() {
  const { user } = useAuth();
  const [state, setState] = useState<AppState>(() => isOfflineDemo ? loadState() : defaultState);
  const [onlineError, setOnlineError] = useState<string | null>(null);

  useEffect(() => {
    if (isOfflineDemo || !user || user.role !== 'candidate') return;
    setState(defaultState);
    setOnlineError(null);
    void Promise.all([fetchApplications(), fetchSavedJobs(), fetchProfile()])
      .then(([applications, savedJobs, studentProfile]) => setState({ ...defaultState, applications, savedJobs, studentProfile: emptyOnlineProfile(studentProfile) }))
      .catch((error: unknown) => setOnlineError(error instanceof Error ? error.message : 'Không tải được dữ liệu tài khoản.'));
  }, [user]);

  const updateState = useCallback((updater: (prev: AppState) => AppState) => {
    setState((prev) => {
      const next = updater(prev);
      if (isOfflineDemo) saveState(next);
      return next;
    });
  }, []);

  // ── Saved Jobs ──────────────────────────────────────────────
  const saveJob = useCallback(
    async (jobId: string) => {
      if (!isOfflineDemo) {
        await saveJobRequest(jobId);
        setState((previous) => ({ ...previous, savedJobs: [...previous.savedJobs, { jobId, savedAt: new Date().toISOString() }] }));
        return;
      }
      updateState((prev) => {
        if (prev.savedJobs.some((j) => j.jobId === jobId)) return prev;
        return {
          ...prev,
          savedJobs: [...prev.savedJobs, { jobId, savedAt: new Date().toISOString() }],
        };
      });
    },
    [updateState]
  );

  const unsaveJob = useCallback(
    async (jobId: string) => {
      if (!isOfflineDemo) {
        await unsaveJobRequest(jobId);
        setState((previous) => ({ ...previous, savedJobs: previous.savedJobs.filter((job) => job.jobId !== jobId) }));
        return;
      }
      updateState((prev) => ({
        ...prev,
        savedJobs: prev.savedJobs.filter((j) => j.jobId !== jobId),
      }));
    },
    [updateState]
  );

  const isJobSaved = useCallback(
    (jobId: string) => state.savedJobs.some((j) => j.jobId === jobId),
    [state.savedJobs]
  );

  // ── Applications ─────────────────────────────────────────────
  const applyToJob = useCallback(
    async (jobId: string) => {
      if (!isOfflineDemo) {
        const application = await createApplication(jobId);
        setState((previous) => ({ ...previous, applications: [application, ...previous.applications] }));
        return;
      }
      updateState((prev) => {
        if (prev.applications.some((a) => a.jobId === jobId)) return prev;
        const newApp: Application = {
          id: `app-${Date.now()}`,
          jobId,
          appliedAt: new Date().toISOString(),
          status: 'Đã ứng tuyển',
        };
        return { ...prev, applications: [...prev.applications, newApp] };
      });
    },
    [updateState]
  );

  const updateApplicationStatus = useCallback(
    async (appId: string, status: Application['status']) => {
      if (!isOfflineDemo) {
        const statusApi: Record<Application['status'], string> = {
          'Đã ứng tuyển': 'applied',
          'Đang xem xét': 'screening',
          'Phỏng vấn': 'interview',
          'Đề nghị nhận việc': 'offer',
          'Đã nhận việc': 'hired',
          'Đã từ chối': 'rejected',
        };
        const application = await updateApplicationStatusRequest(appId, statusApi[status]);
        setState((previous) => ({
          ...previous,
          applications: previous.applications.map((item) => item.id === appId ? application : item),
        }));
        return;
      }
      updateState((prev) => ({
        ...prev,
        applications: prev.applications.map((a) =>
          a.id === appId ? { ...a, status } : a
        ),
      }));
    },
    [updateState]
  );

  const hasApplied = useCallback(
    (jobId: string) => state.applications.some((a) => a.jobId === jobId),
    [state.applications]
  );

  // ── Student Profile ───────────────────────────────────────────
  const updateProfile = useCallback(
    async (updates: Partial<StudentProfile>) => {
      if (!isOfflineDemo) {
        const profile = await updateProfileRequest(updates);
        setState((previous) => ({ ...previous, studentProfile: { ...previous.studentProfile, ...profile } }));
        return;
      }
      updateState((prev) => {
        const updated = { ...prev.studentProfile, ...updates };
        return {
          ...prev,
          studentProfile: {
            ...updated,
            profileCompletion: calculateProfileCompletion(updated),
          },
        };
      });
    },
    [updateState]
  );

  // ── Skill Gap ─────────────────────────────────────────────────
  const toggleSkillLearned = useCallback(
    (skillId: string) => {
      updateState((prev) => ({
        ...prev,
        skillGapItems: prev.skillGapItems.map((item) =>
          item.id === skillId ? { ...item, learned: !item.learned } : item
        ),
      }));
    },
    [updateState]
  );

  const updateSkillGapItems = useCallback(
    (items: SkillGapItem[]) => {
      updateState((prev) => ({ ...prev, skillGapItems: items }));
    },
    [updateState]
  );

  // ── Reset ─────────────────────────────────────────────────────
  const resetToDemo = useCallback(() => {
    if (isOfflineDemo) saveState(defaultState);
    setState(defaultState);
  }, []);

  return {
    state,
    savedJobs: state.savedJobs,
    applications: state.applications,
    studentProfile: state.studentProfile,
    skillGapItems: state.skillGapItems,
    // Actions
    saveJob,
    unsaveJob,
    isJobSaved,
    applyToJob,
    updateApplicationStatus,
    hasApplied,
    updateProfile,
    toggleSkillLearned,
    updateSkillGapItems,
    resetToDemo,
    onlineError,
  };
}

// Re-export type so it can be used outside the hook
export type UseAppState = ReturnType<typeof useAppState>;
