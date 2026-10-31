import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Plus, Save, Trash2 } from 'lucide-react';
import { adminApi, type AdminSkill } from '../api/endpoints';
import { errorMessage } from '../api/client';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';

const CATEGORIES = ['Frontend', 'Backend', 'Dữ liệu', 'DevOps', 'Thiết kế', 'Marketing', 'Nghiệp vụ', 'Kỹ năng mềm'];

/** Quản trị danh mục kỹ năng và từ đồng nghĩa (F10): dữ liệu này quyết định cách parser chuẩn hoá `reactjs` → React. */
export default function AdminSkillsPage() {
  const [skills, setSkills] = useState<AdminSkill[] | null>(null);
  const [aliases, setAliases] = useState<{ alias: string; skill_name: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const [newName, setNewName] = useState('');
  const [newCategory, setNewCategory] = useState(CATEGORIES[0]);
  const [newAlias, setNewAlias] = useState('');
  const [stepsText, setStepsText] = useState('');
  const [categoryEdit, setCategoryEdit] = useState('');

  const load = useCallback(() => {
    setError(null);
    Promise.all([adminApi.skills(), adminApi.aliases()])
      .then(([s, a]) => {
        setSkills(s);
        setAliases(a);
      })
      .catch((e) => setError(errorMessage(e)));
  }, []);

  useEffect(load, [load]);

  const selected = useMemo(() => skills?.find((s) => s.id === selectedId) ?? null, [skills, selectedId]);
  useEffect(() => {
    setStepsText(selected?.learning_steps.join('\n') ?? '');
    setCategoryEdit(selected?.category ?? '');
  }, [selected]);

  const shown = useMemo(() => (skills ?? []).filter((s) => s.name.toLowerCase().includes(query.trim().toLowerCase())), [skills, query]);
  const selectedAliases = aliases.filter((a) => a.skill_name === selected?.name);

  const run = async (action: () => Promise<unknown>, message: string) => {
    setError(null);
    setNotice(null);
    try {
      await action();
      setNotice(message);
      load();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const addSkill = (e: FormEvent) => {
    e.preventDefault();
    void run(async () => {
      const created = await adminApi.addSkill({ name: newName.trim(), category: newCategory });
      setNewName('');
      setSelectedId(created.id);
    }, 'Đã thêm kỹ năng.');
  };

  const addAlias = (e: FormEvent) => {
    e.preventDefault();
    if (!selected) return;
    void run(async () => {
      await adminApi.addAlias(newAlias.trim(), selected.name);
      setNewAlias('');
    }, 'Đã thêm từ đồng nghĩa.');
  };

  const save = () => {
    if (!selected) return;
    void run(() => adminApi.updateSkill(selected.id, { category: categoryEdit, learning_steps: stepsText.split('\n') }), 'Đã lưu thay đổi.');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Quản lý danh mục kỹ năng</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Thêm kỹ năng, từ đồng nghĩa (ví dụ <code>reactjs</code> → React) và lộ trình học. Tên chuẩn không đổi sau khi tạo để không làm lệch hồ sơ và tin đã gắn.
        </p>
      </div>

      {error && <ErrorBlock message={error} onRetry={load} />}
      {notice && <p role="status" className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg p-2.5">{notice}</p>}
      {!skills && !error && <LoadingBlock rows={2} message="Đang tải danh mục..." />}

      {skills && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <section className="card p-5 lg:col-span-2 space-y-4" aria-label="Danh sách kỹ năng">
            <form onSubmit={addSkill} className="flex flex-wrap gap-2 items-end" aria-label="Thêm kỹ năng">
              <div className="flex-1 min-w-32">
                <label htmlFor="new-skill" className="block text-xs font-medium text-slate-500 mb-1">Kỹ năng mới</label>
                <input id="new-skill" required maxLength={100} className="input-field" value={newName} onChange={(e) => setNewName(e.target.value)} />
              </div>
              <div>
                <label htmlFor="new-skill-cat" className="block text-xs font-medium text-slate-500 mb-1">Nhóm</label>
                <select id="new-skill-cat" className="select-field" value={newCategory} onChange={(e) => setNewCategory(e.target.value)}>
                  {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
              <button type="submit" className="btn-primary text-sm"><Plus size={14} />Thêm</button>
            </form>

            <div>
              <label htmlFor="skill-filter" className="block text-xs font-medium text-slate-500 mb-1">Tìm trong {skills.length} kỹ năng</label>
              <input id="skill-filter" className="input-field" value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>
            <ul className="max-h-[420px] overflow-y-auto scrollbar-thin space-y-1" aria-label="Kỹ năng">
              {shown.map((s) => (
                <li key={s.id}>
                  <button
                    onClick={() => setSelectedId(s.id)}
                    aria-pressed={s.id === selectedId}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm border ${s.id === selectedId ? 'border-blue-300 bg-blue-50' : 'border-transparent hover:bg-slate-50'}`}
                  >
                    <span className="font-medium text-slate-800">{s.name}</span>
                    <span className="ml-2 text-xs text-slate-400">{s.category}{s.learning_steps.length > 0 && ` · ${s.learning_steps.length} bước học`}</span>
                  </button>
                </li>
              ))}
              {shown.length === 0 && <li className="text-xs text-slate-400 px-3 py-2">Không có kỹ năng phù hợp.</li>}
            </ul>
          </section>

          <section className="card p-5 lg:col-span-3 space-y-5" aria-label="Chi tiết kỹ năng">
            {!selected ? (
              <p className="text-sm text-slate-400">Chọn một kỹ năng ở bên trái để sửa nhóm, lộ trình học và từ đồng nghĩa.</p>
            ) : (
              <>
                <h2 className="text-lg font-bold text-slate-900">{selected.name}</h2>
                <div>
                  <label htmlFor="edit-cat" className="block text-xs font-medium text-slate-500 mb-1">Nhóm</label>
                  <select id="edit-cat" className="select-field" value={categoryEdit} onChange={(e) => setCategoryEdit(e.target.value)}>
                    {[...new Set([categoryEdit, ...CATEGORIES])].filter(Boolean).map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="edit-steps" className="block text-xs font-medium text-slate-500 mb-1">Lộ trình học (mỗi dòng một bước; để trống = dùng lộ trình mặc định)</label>
                  <textarea id="edit-steps" rows={5} className="input-field" value={stepsText} onChange={(e) => setStepsText(e.target.value)} />
                </div>
                <button onClick={save} className="btn-primary text-sm"><Save size={14} />Lưu thay đổi</button>

                <div className="pt-4 border-t border-slate-100 space-y-3">
                  <h3 className="font-semibold text-sm text-slate-800">Từ đồng nghĩa ({selectedAliases.length})</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedAliases.map((a) => (
                      <span key={a.alias} className="inline-flex items-center gap-1 text-xs pl-2.5 pr-1 py-1 rounded-full bg-slate-100 text-slate-700">
                        {a.alias}
                        <button onClick={() => void run(() => adminApi.deleteAlias(a.alias), 'Đã xóa từ đồng nghĩa.')} aria-label={`Xóa từ đồng nghĩa ${a.alias}`} className="p-0.5 hover:bg-white rounded-full">
                          <Trash2 size={11} />
                        </button>
                      </span>
                    ))}
                    {selectedAliases.length === 0 && <span className="text-xs text-slate-400">Chưa có từ đồng nghĩa.</span>}
                  </div>
                  <form onSubmit={addAlias} className="flex gap-2 items-end" aria-label="Thêm từ đồng nghĩa">
                    <div className="flex-1">
                      <label htmlFor="new-alias" className="block text-xs font-medium text-slate-500 mb-1">Từ đồng nghĩa mới</label>
                      <input id="new-alias" required maxLength={100} className="input-field" value={newAlias} onChange={(e) => setNewAlias(e.target.value)} placeholder="ví dụ: reactjs" />
                    </div>
                    <button type="submit" className="btn-secondary text-sm"><Plus size={14} />Thêm</button>
                  </form>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
