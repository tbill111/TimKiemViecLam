import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { Job } from '../types';
import { fetchEmployerJobs } from '../api/employer';
import { apiErrorMessage, isOfflineDemo } from '../api/client';
import { sampleJobs } from '../data/jobs';
import LoadingBlock from '../components/ui/LoadingBlock';
import JobForm from '../components/jobs/JobForm';

export default function EditJobPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job>();
  const [error, setError] = useState('');
  useEffect(() => {
    if (!id) return;
    if (isOfflineDemo) { setJob(sampleJobs.find((item) => item.id === id)); return; }
    void fetchEmployerJobs().then((items) => setJob(items.find((item) => item.id === id))).catch((e) => setError(apiErrorMessage(e, 'Không tải được tin tuyển dụng.')));
  }, [id]);
  if (error || (id && !job)) return <p role="alert" className="text-sm text-red-600">{error || 'Không tìm thấy tin tuyển dụng.'}</p>;
  if (!job) return <LoadingBlock message="Đang tải nội dung tin tuyển dụng..." />;
  return <JobForm job={job} onSaved={() => navigate('/employer/jobs')} onCancel={() => navigate('/employer/jobs')} />;
}
