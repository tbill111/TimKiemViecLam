from app.ai.skills import SkillIndex, alternatives, has_skill, normalize_skill, strip_level, tokenize


def test_normalize_and_strip_level():
    assert normalize_skill("  Power   BI ") == "power bi"
    assert strip_level("python cơ bản") == "python"
    assert strip_level("thống kê cơ bản") == "thống kê"


def test_has_skill_exact_and_level_suffix():
    assert has_skill(["Python cơ bản"], "Python")
    assert has_skill(["Python"], "Python cơ bản")
    assert has_skill(["react"], "React")


def test_has_skill_not_partial():
    # "React" không được coi là có "React Query"
    assert not has_skill(["React"], "React Query")


def test_has_skill_alternatives():
    assert alternatives("React hoặc Node.js") == ["react", "node.js"]
    assert has_skill(["Node.js"], "React hoặc Node.js")
    assert has_skill(["Figma"], "Figma/Sketch")
    assert not has_skill(["Vue"], "React hoặc Node.js")


def test_tokenize_keeps_special():
    assert tokenize("Node.js, C++ và C#") == ["node.js", "c++", "và", "c#"]


def test_default_index_alias_and_composite_skipped():
    idx = SkillIndex.default()
    assert idx.phrases["reactjs"] == "React"
    assert idx.phrases["nodejs"] == "Node.js"
    assert idx.phrases["python"] in ("Python", "Python cơ bản")
    assert not any("hoặc" in k for k in idx.phrases)
