import { apiClient } from './client';
export interface SkillAdmin { id: number; name: string; category: string; learning_steps: string[] }
export interface AliasAdmin { alias: string; skill_id: number; skill_name: string }
export async function fetchAdminSkills(): Promise<SkillAdmin[]> { return (await apiClient.get<{ items: SkillAdmin[] }>('/admin/skills')).data.items; }
export async function saveAdminSkill(payload: { name: string; category: string; learning_steps: string[] }): Promise<SkillAdmin> { return (await apiClient.post<SkillAdmin>('/admin/skills', payload)).data; }
export async function updateAdminSkill(id: number, payload: Partial<SkillAdmin>): Promise<SkillAdmin> { return (await apiClient.put<SkillAdmin>(`/admin/skills/${id}`, payload)).data; }
export async function fetchAliases(): Promise<AliasAdmin[]> { return (await apiClient.get<{ items: AliasAdmin[] }>('/admin/skill-aliases')).data.items; }
export async function createAlias(alias: string, skillName: string): Promise<void> { await apiClient.post('/admin/skill-aliases', { alias, skill_name: skillName }); }
export async function deleteAlias(alias: string): Promise<void> { await apiClient.delete(`/admin/skill-aliases/${encodeURIComponent(alias)}`); }
