import { useNavigate } from 'react-router-dom';
import JobForm from '../components/jobs/JobForm';

export default function PostJobPage() {
  const navigate = useNavigate();
  return <JobForm onSaved={() => navigate('/employer/jobs')} onCancel={() => navigate('/employer/jobs')} />;
}
