import { useState, useCallback } from 'react';
import type { AppState, Application, StudentProfile, SkillGapItem } from '../types';
import { defaultStudentProfile } from '../data/profile';
import { defaultSkillGapItems } from '../data/skillGap';
import { calculateProfileCompletion } from '../utils';

const STORAGE_KEY = 'smartcareer_app_state';

const defaultState: AppState = {
  savedJobs: [],
  applications: [],
  studentProfile: defaultStudentProfile,
  skillGapItems: defaultSkillGapItems,
};

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
  const [state, setState] = useState<AppState>(loadState);

  const updateState = useCallback((updater: (prev: AppState) => AppState) => {
    setState((prev) => {
      const next = updater(prev);
      saveState(next);
      return next;
    });
  }, []);

  // ── Saved Jobs ──────────────────────────────────────────────
  const saveJob = useCallback(
    (jobId: string) => {
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
    (jobId: string) => {
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
    (jobId: string) => {
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
    (appId: string, status: Application['status']) => {
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
    (updates: Partial<StudentProfile>) => {
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
    saveState(defaultState);
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
  };
}

// Re-export type so it can be used outside the hook
export type UseAppState = ReturnType<typeof useAppState>;
