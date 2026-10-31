// Xuất kết quả chuẩn của calculateSkillMatch (TypeScript) để so khớp với M0 bên Python.
// Chạy:  npx tsx scripts/export-golden.ts
import { writeFileSync, mkdirSync } from 'node:fs';
import { sampleJobs } from '../src/data/jobs';
import { sampleCandidates } from '../src/data/candidates';
import { defaultStudentProfile } from '../src/data/profile';
import { skillAliases, skillCatalog } from '../src/data/skillCatalog';
import { skillCategories } from '../src/data/skillCategories';
import { calculateSkillMatch } from '../src/utils';

const profiles = [
  { id: 'student-default', skills: defaultStudentProfile.skills, preferredLocations: defaultStudentProfile.preferredLocations, preferredWorkTypes: defaultStudentProfile.preferredWorkTypes },
  ...sampleCandidates.map((c) => ({ id: c.id, skills: c.skills, preferredLocations: c.preferredLocations, preferredWorkTypes: c.preferredWorkTypes })),
];

const cases = profiles.flatMap((p) =>
  sampleJobs.map((job) => ({
    profile: p,
    job: { id: job.id, requiredSkills: job.requiredSkills, preferredSkills: job.preferredSkills, location: job.location, workType: job.workType },
    expected: calculateSkillMatch(p, job),
  }))
);

mkdirSync('backend/tests/golden', { recursive: true });
writeFileSync('backend/tests/golden/m0_golden.json', JSON.stringify({ count: cases.length, cases }, null, 1));

// Từ điển kỹ năng khởi tạo cho parser khi chưa có CSV của Hoàng Hưng.
const skillGroup: Record<string, string> = {};
for (const c of skillCategories) for (const s of c.skills) skillGroup[s] ??= c.name;
writeFileSync(
  'backend/app/ai/default_skills.json',
  JSON.stringify(
    { skills: skillCatalog.map((name) => ({ name, category: skillGroup[name] ?? 'Khác' })), aliases: skillAliases },
    null, 1
  )
);
console.log(`golden cases: ${cases.length}, skills: ${skillCatalog.length}`);
