// Xuất 12 tin mẫu của frontend để sinh jobs.csv (giữ nguyên nội dung demo cũ).
// Chạy:  npx tsx scripts/export-legacy-jobs.ts
import { writeFileSync } from 'node:fs';
import { sampleJobs } from '../src/data/jobs';
import { defaultStudentProfile } from '../src/data/profile';
import { sampleCandidates } from '../src/data/candidates';

writeFileSync('backend/seed/data/legacy_jobs.json', JSON.stringify({ jobs: sampleJobs, demoProfile: defaultStudentProfile, candidates: sampleCandidates }, null, 1));
console.log(`legacy jobs: ${sampleJobs.length}`);
