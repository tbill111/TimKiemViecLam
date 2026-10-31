import { useState, useCallback, useEffect } from 'react';
import type { AppState, Application, SavedJob, StudentProfile, SkillGapItem } from '../types';
import { defaultStudentProfile } from '../data/profile';
import { defaultSkillGapItems } from '../data/skillGap';
import { calculateProfileCompletion } from '../utils';
import { OFFLINE } from '../config';
import { useAuth } from '../context/AuthContext';
import { applicationApi, profileApi, savedApi } from '../api/endpoints';
import { asUtc, fromProfilePatch, toApplication, toProfile } from '../api/adapters';
import { errorMessage } from '../api/client';

/** Giao diện chung của hai chế độ: demo (localStorage) và online (gọi API). Các trang không cần biết đang ở chế độ nào. */
export interface UseAppState {
  state: AppState;
  savedJobs: SavedJob[];
  applications: Application[];
  studentProfile: StudentProfile;
  skillGapItems: SkillGapItem[];
  /** true khi dữ liệu đến từ API: trạng thái hồ sơ do nhà tuyển dụng quyết định, ứng viên chỉ xem. */
  online: boolean;
  loading: boolean;
  error: string | null;
  saveJob: (jobId: string) => void;
  unsaveJob: (jobId: string) => void;
  isJobSaved: (jobId: string) => boolean;
  applyToJob: (jobId: string) => void;
  updateApplicationStatus: (appId: string, status: Application['status']) => void;
  hasApplied: (jobId: string) => boolean;
  updateProfile: (updates: Partial<StudentProfile>) => void;
  toggleSkillLearned: (skillId: string) => void;
  updateSkillGapItems: (items: SkillGapItem[]) => void;
  resetToDemo: () => void;
  refresh: () => void;
}

// ============================================================
// CHẾ ĐỘ DEMO: toàn bộ trạng thái nằm trong localStorage, dữ liệu mẫu ở src/data
// ============================================================

const STORAGE_KEY = 'smartcareer_app_state';

const defaultState: AppState = {
  savedJobs: [],
  applications: [],
  studentProfile: defaultStudentProfile,
  skillGapItems: defaultSkillGapItems,
};

/** Dữ liệu lưu từ phiên bản cũ có trạng thái "Đã kết thúc" (đã bỏ khi mở rộng sang 6 trạng thái). */
function migrateStatus(status: string): Application['status'] {
  return status === 'Đã kết thúc' ? 'Từ chối' : (status as Application['status']);
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
      applications: (saved.applications ?? []).map((a) => ({ ...a, status: migrateStatus(a.status) })),
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

function useOfflineAppState(): UseAppState {
  const [state, setState] = useState<AppState>(loadState);

  const updateState = useCallback((updater: (prev: AppState) => AppState) => {
    setState((prev) => {
      const next = updater(prev);
      saveState(next);
      return next;
    });
  }, []);

  const saveJob = useCallback(
    (jobId: string) => {
      updateState((prev) => {
        if (prev.savedJobs.some((j) => j.jobId === jobId)) return prev;
        return { ...prev, savedJobs: [...prev.savedJobs, { jobId, savedAt: new Date().toISOString() }] };
      });
    },
    [updateState]
  );

  const unsaveJob = useCallback(
    (jobId: string) => updateState((prev) => ({ ...prev, savedJobs: prev.savedJobs.filter((j) => j.jobId !== jobId) })),
    [updateState]
  );

  const isJobSaved = useCallback((jobId: string) => state.savedJobs.some((j) => j.jobId === jobId), [state.savedJobs]);

  const applyToJob = useCallback(
    (jobId: string) => {
      updateState((prev) => {
        if (prev.applications.some((a) => a.jobId === jobId)) return prev;
        const newApp: Application = { id: `app-${Date.now()}`, jobId, appliedAt: new Date().toISOString(), status: 'Đã ứng tuyển' };
        return { ...prev, applications: [...prev.applications, newApp] };
      });
    },
    [updateState]
  );

  const updateApplicationStatus = useCallback(
    (appId: string, status: Application['status']) => {
      updateState((prev) => ({ ...prev, applications: prev.applications.map((a) => (a.id === appId ? { ...a, status } : a)) }));
    },
    [updateState]
  );

  const hasApplied = useCallback((jobId: string) => state.applications.some((a) => a.jobId === jobId), [state.applications]);

  const updateProfile = useCallback(
    (updates: Partial<StudentProfile>) => {
      updateState((prev) => {
        const updated = { ...prev.studentProfile, ...updates };
        return { ...prev, studentProfile: { ...updated, profileCompletion: calculateProfileCompletion(updated) } };
      });
    },
    [updateState]
  );

  const toggleSkillLearned = useCallback(
    (skillId: string) => {
      updateState((prev) => ({
        ...prev,
        skillGapItems: prev.skillGapItems.map((item) => (item.id === skillId ? { ...item, learned: !item.learned } : item)),
      }));
    },
    [updateState]
  );

  const updateSkillGapItems = useCallback(
    (items: SkillGapItem[]) => updateState((prev) => ({ ...prev, skillGapItems: items })),
    [updateState]
  );

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
    online: false,
    loading: false,
    error: null,
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
    refresh: () => undefined,
  };
}

// ============================================================
// CHẾ ĐỘ ONLINE: hồ sơ, việc đã lưu, ứng tuyển lấy từ API; chỉ tiến độ học (Skill Gap) lưu cục bộ
// ============================================================

const SKILLGAP_KEY = 'smartcareer_skillgap_online';

const blankProfile: StudentProfile = {
  fullName: '', university: '', major: '', year: '', email: '', phone: '', githubUrl: '', linkedinUrl: '', careerGoal: '', skills: [],
  preferredLocations: [], preferredWorkTypes: [], languages: [], projects: [], experience: [], certificates: [], profileCompletion: 0,
};

function loadSkillGap(): SkillGapItem[] {
  try {
    const raw = localStorage.getItem(SKILLGAP_KEY);
    return raw ? (JSON.parse(raw) as SkillGapItem[]) : defaultSkillGapItems;
  } catch {
    return defaultSkillGapItems;
  }
}

function useOnlineAppState(): UseAppState {
  const { user } = useAuth();
  const isCandidate = user?.role === 'candidate';
  const [studentProfile, setProfile] = useState<StudentProfile>(blankProfile);
  const [savedJobs, setSaved] = useState<SavedJob[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [skillGapItems, setSkillGapItems] = useState<SkillGapItem[]>(loadSkillGap);
  const [loading, setLoading] = useState(isCandidate);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!isCandidate) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [profile, saved, apps] = await Promise.all([profileApi.get(), savedApi.list(), applicationApi.mine()]);
      setProfile(toProfile(profile));
      setSaved(saved.map((s) => ({ jobId: String(s.job_id), savedAt: asUtc(s.saved_at) })));
      setApplications(apps.map(toApplication));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [isCandidate]);

  useEffect(() => {
    if (!user) {
      setProfile(blankProfile);
      setSaved([]);
      setApplications([]);
    }
    void load();
  }, [user, load]);

  const saveJob = useCallback((jobId: string) => {
    setSaved((prev) => (prev.some((j) => j.jobId === jobId) ? prev : [...prev, { jobId, savedAt: new Date().toISOString() }]));
    savedApi.save(jobId).catch((e) => {
      setSaved((prev) => prev.filter((j) => j.jobId !== jobId));
      setError(errorMessage(e));
    });
  }, []);

  const unsaveJob = useCallback((jobId: string) => {
    let removed: SavedJob | undefined;
    setSaved((prev) => {
      removed = prev.find((j) => j.jobId === jobId);
      return prev.filter((j) => j.jobId !== jobId);
    });
    savedApi.remove(jobId).catch((e) => {
      if (removed) setSaved((prev) => [...prev, removed as SavedJob]);
      setError(errorMessage(e));
    });
  }, []);

  const applyToJob = useCallback(
    (jobId: string) => {
      applicationApi
        .apply(jobId)
        .then((dto) => setApplications((prev) => (prev.some((a) => a.jobId === jobId) ? prev : [toApplication(dto), ...prev])))
        .catch((e) => {
          setError(errorMessage(e));
          void load(); // đã nộp ở phiên khác: đồng bộ lại danh sách
        });
    },
    [load]
  );

  const updateProfile = useCallback((updates: Partial<StudentProfile>) => {
    setProfile((prev) => ({ ...prev, ...updates })); // cập nhật ngay để giao diện không bị chậm
    profileApi
      .put(fromProfilePatch(updates))
      .then((dto) => setProfile(toProfile(dto)))
      .catch((e) => setError(errorMessage(e)));
  }, []);

  const persistGap = useCallback((items: SkillGapItem[]) => {
    setSkillGapItems(items);
    try {
      localStorage.setItem(SKILLGAP_KEY, JSON.stringify(items));
    } catch {
      // bỏ qua lỗi localStorage
    }
  }, []);

  const toggleSkillLearned = useCallback(
    (skillId: string) => persistGap(skillGapItems.map((i) => (i.id === skillId ? { ...i, learned: !i.learned } : i))),
    [persistGap, skillGapItems]
  );

  const state: AppState = { savedJobs, applications, studentProfile, skillGapItems };
  return {
    state,
    savedJobs,
    applications,
    studentProfile,
    skillGapItems,
    online: true,
    loading,
    error,
    saveJob,
    unsaveJob,
    isJobSaved: (jobId) => savedJobs.some((j) => j.jobId === jobId),
    applyToJob,
    updateApplicationStatus: () => undefined, // ứng viên không tự đổi trạng thái; nhà tuyển dụng làm việc này
    hasApplied: (jobId) => applications.some((a) => a.jobId === jobId),
    updateProfile,
    toggleSkillLearned,
    updateSkillGapItems: persistGap,
    resetToDemo: () => void load(),
    refresh: () => void load(),
  };
}

/** Hook duy nhất các trang dùng; chế độ được chọn một lần theo VITE_OFFLINE_DEMO nên thứ tự hook luôn ổn định. */
export const useAppState: () => UseAppState = OFFLINE ? useOfflineAppState : useOnlineAppState;
