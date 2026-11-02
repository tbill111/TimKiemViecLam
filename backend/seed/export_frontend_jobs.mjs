// Copy the existing 12 frontend fixtures into the documented backend CSV contract.
// Run from the repository root with Node and the already installed TypeScript compiler.
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const input = fs.readFileSync('src/data/jobs.ts', 'utf8');
const javascript = ts.transpile(input, { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 });
const sandbox = { exports: {} };
vm.runInNewContext(javascript, sandbox, { timeout: 5000 });
const jobs = sandbox.exports.sampleJobs;
const header = ['external_id','company_name','title','category','level','job_type','work_mode','location','salary_min','salary_max','min_years_exp','min_education','posted_at','deadline','description','responsibilities','required_skills','preferred_skills'];
const quote = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
const year = 2026;
const rows = jobs.map((job) => {
  const match = job.salary.match(/([\d,]+)\s*[–-]\s*([\d,]+)/);
  const min = match ? Number(match[1].replaceAll(',', '')) / 1_000_000 : '';
  const max = match ? Number(match[2].replaceAll(',', '')) / 1_000_000 : '';
  const internship = job.workType === 'Thực tập';
  const workMode = job.workType === 'Remote' ? 'remote' : 'onsite';
  const jobType = internship ? 'internship' : job.workType === 'Bán thời gian' ? 'part_time' : 'full_time';
  const years = job.experienceLevel === '3+ năm' ? 3 : job.experienceLevel === '2-3 năm' ? 2 : job.experienceLevel === '1-2 năm' ? 1 : job.experienceLevel === 'Dưới 1 năm' ? 0.5 : 0;
  const req = [];
  const pref = [...job.preferredSkills];
  for (const skill of job.requiredSkills) {
    if (/\s+hoặc\s+/i.test(skill)) pref.push(...skill.split(/\s+hoặc\s+/i));
    else req.push(skill);
  }
  return [job.id, job.company, job.title, job.category, internship ? 'intern' : years >= 3 ? 'senior' : years >= 2 ? 'middle' : years >= 1 ? 'junior' : 'fresher', jobType, workMode, job.location, min, max, years, 0, job.postedAt.slice(0,10), `${year}-12-31`, job.description, job.responsibilities.join('|'), req.join('|'), pref.join('|')];
});
fs.writeFileSync('backend/seed/data/frontend_jobs.csv', `${header.join(',')}\n${rows.map((row) => row.map(quote).join(',')).join('\n')}\n`, 'utf8');
process.stdout.write(`Wrote ${rows.length} legacy frontend jobs to backend/seed/data/frontend_jobs.csv\n`);
