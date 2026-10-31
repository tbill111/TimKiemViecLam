import csv
from collections import Counter

from seed.make_pair_list import build_pairs, near_groups

CATS = ["Frontend Development", "Backend Development", "Data Science & Analytics", "QA & Testing", "Software Engineering"]


def _write(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def make_data(tmp_path, n_cand=60, n_jobs=60):
    cands = [(f"cand-{i:04d}", CATS[i % len(CATS)]) for i in range(n_cand)]
    jobs = [(f"job-{i:03d}", CATS[(i * 3) % len(CATS)]) for i in range(n_jobs)]
    _write(tmp_path / "c.csv", ["candidate_id", "occupation"], cands)
    _write(tmp_path / "j.csv", ["external_id", "category"], jobs)
    return tmp_path / "c.csv", tmp_path / "j.csv", dict(jobs)


def test_30_candidates_10_unique_jobs_each(tmp_path):
    c, j, _ = make_data(tmp_path)
    pairs = build_pairs(c, j)
    assert len(pairs) == 300
    per = Counter(cid for cid, _ in pairs)
    assert len(per) == 30 and set(per.values()) == {10}
    assert all(len({jid for cid2, jid in pairs if cid2 == cid}) == 10 for cid in per)


def test_composition_same_near_far(tmp_path):
    c, j, job_cat = make_data(tmp_path)
    occ = {cid: o for cid, o in csv.reader(open(c, encoding="utf-8")) if cid != "candidate_id"}
    pairs = build_pairs(c, j)
    for cid in {p[0] for p in pairs}:
        cats = [job_cat[jid] for c2, jid in pairs if c2 == cid]
        same = sum(x == occ[cid] for x in cats)
        near = sum(x in near_groups(occ[cid]) for x in cats)
        assert same == 4 and near == 3, (cid, same, near)


def test_candidates_spread_over_occupations_and_deterministic(tmp_path):
    c, j, _ = make_data(tmp_path)
    p1, p2 = build_pairs(c, j), build_pairs(c, j)
    assert p1 == p2
    occ = {cid: o for cid, o in csv.reader(open(c, encoding="utf-8")) if cid != "candidate_id"}
    counts = Counter(occ[cid] for cid in {p[0] for p in p1})
    assert set(counts) == set(CATS) and max(counts.values()) - min(counts.values()) <= 1


def test_different_seed_changes_selection(tmp_path):
    c, j, _ = make_data(tmp_path)
    assert build_pairs(c, j, seed=1) != build_pairs(c, j, seed=2)
