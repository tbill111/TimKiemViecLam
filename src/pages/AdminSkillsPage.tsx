import { useEffect, useState } from 'react';
import { createAlias as addAlias, deleteAlias, fetchAdminSkills, fetchAliases, saveAdminSkill, updateAdminSkill, type AliasAdmin, type SkillAdmin } from '../api/admin';
import { apiErrorMessage, isOfflineDemo } from '../api/client';
import LoadingBlock from '../components/ui/LoadingBlock';

export default function AdminSkillsPage() {
  const [tab, setTab] = useState<'skills' | 'aliases'>('skills');
  const [skills, setSkills] = useState<SkillAdmin[]>([]);
  const [aliases, setAliases] = useState<AliasAdmin[]>([]);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Khác');
  const [learningSteps, setLearningSteps] = useState('');
  const [editing, setEditing] = useState<SkillAdmin | null>(null);
  const [alias, setAlias] = useState('');
  const [skillName, setSkillName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const load = async () => {
    if (isOfflineDemo) { setLoading(false); return; }
    try { const [s, a] = await Promise.all([fetchAdminSkills(), fetchAliases()]); setSkills(s); setAliases(a); }
    catch (e) { setError(apiErrorMessage(e, 'Không tải được danh mục kỹ năng.')); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);
  const resetSkillForm = () => { setEditing(null); setName(''); setCategory('Khác'); setLearningSteps(''); };
  const saveSkill = async () => {
    try {
      const payload = { name: name.trim(), category: category.trim() || 'Khác', learning_steps: learningSteps.split('\n').map((step) => step.trim()).filter(Boolean) };
      if (!payload.name) return;
      if (editing) await updateAdminSkill(editing.id, payload);
      else await saveAdminSkill(payload);
      resetSkillForm(); await load();
    } catch (e) { setError(apiErrorMessage(e, editing ? 'Không cập nhật được kỹ năng.' : 'Không thêm được kỹ năng.')); }
  };
  const editSkill = (skill: SkillAdmin) => { setEditing(skill); setName(skill.name); setCategory(skill.category); setLearningSteps(skill.learning_steps.join('\n')); };
  const addSkillAlias = async () => { try { await addAlias(alias, skillName); setAlias(''); setSkillName(''); await load(); } catch (e) { setError(apiErrorMessage(e, 'Không thêm được alias.')); } };
  const removeAlias = async (item: AliasAdmin) => { try { await deleteAlias(item.alias); await load(); } catch (e) { setError(apiErrorMessage(e, 'Không xoá được alias.')); } };
  if (loading) return <LoadingBlock message="Đang tải quản trị kỹ năng..." />;
  return <div className="space-y-5"><h1 className="text-2xl font-bold">Quản lý kỹ năng</h1>{error && <p role="alert" className="text-sm text-red-600">{error}</p>}<div className="flex gap-2 border-b border-slate-200"><button className={tab === 'skills' ? 'border-b-2 border-blue-600 px-4 py-2 text-sm font-semibold text-blue-600' : 'px-4 py-2 text-sm text-slate-500'} onClick={() => setTab('skills')}>Kỹ năng</button><button className={tab === 'aliases' ? 'border-b-2 border-blue-600 px-4 py-2 text-sm font-semibold text-blue-600' : 'px-4 py-2 text-sm text-slate-500'} onClick={() => setTab('aliases')}>Alias</button></div>{tab === 'skills' ? <><div className="card p-4 space-y-3"><h2 className="font-semibold">{editing ? 'Sửa kỹ năng' : 'Thêm kỹ năng'}</h2><div className="grid md:grid-cols-2 gap-2"><input className="input-field" placeholder="Tên kỹ năng" value={name} onChange={(e) => setName(e.target.value)} /><input className="input-field" placeholder="Nhóm" value={category} onChange={(e) => setCategory(e.target.value)} /></div><textarea className="input-field min-h-24" placeholder="Lộ trình học (mỗi dòng một bước)" value={learningSteps} onChange={(e) => setLearningSteps(e.target.value)} /><div className="flex gap-2"><button className="btn-primary" onClick={() => void saveSkill()}>{editing ? 'Lưu thay đổi' : 'Thêm kỹ năng'}</button>{editing && <button className="btn-secondary" onClick={resetSkillForm}>Hủy</button>}</div></div><div className="card overflow-auto"><table className="w-full text-sm"><thead><tr className="text-left border-b"><th className="p-3">Kỹ năng</th><th className="p-3">Nhóm</th><th className="p-3">Lộ trình học</th><th className="p-3">Thao tác</th></tr></thead><tbody>{skills.map((skill) => <tr className="border-b" key={skill.id}><td className="p-3">{skill.name}</td><td className="p-3">{skill.category}</td><td className="p-3">{skill.learning_steps.join(' · ') || 'Chưa có'}</td><td className="p-3"><button className="text-blue-600" onClick={() => editSkill(skill)}>Sửa</button></td></tr>)}</tbody></table></div></> : <><div className="card p-4 flex flex-wrap gap-2"><input className="input-field max-w-xs" placeholder="Alias" value={alias} onChange={(e) => setAlias(e.target.value)} /><input className="input-field max-w-xs" placeholder="Tên kỹ năng chuẩn" value={skillName} onChange={(e) => setSkillName(e.target.value)} /><button className="btn-secondary" onClick={() => void addSkillAlias()}>Thêm alias</button></div><div className="card p-4"><h2 className="font-semibold mb-2">Alias hiện có</h2>{aliases.map((item) => <div className="flex justify-between border-b py-2 text-sm" key={item.alias}><span>{item.alias} → {item.skill_name}</span><button className="text-red-600" onClick={() => void removeAlias(item)}>Xoá</button></div>)}</div></>}</div>;
}
