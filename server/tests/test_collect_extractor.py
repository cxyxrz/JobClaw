from app.modules.collect.extractor import extract_fields


def test_extract_labeled_text():
    text = """后端开发工程师（Python）
字节跳动
工作地点：北京
招聘对象：2026届
薪资：25-40K·16薪
负责服务端业务系统设计与开发。"""
    job = extract_fields(text)
    assert job.title == "后端开发工程师（Python）"
    assert job.company == "字节跳动"
    assert job.city == "北京"
    assert job.batch == "2026届"
    assert job.salary_text == "25-40K·16薪"
    assert job.confidence >= 0.9


def test_extract_fallback_heuristics():
    text = """前端开发工程师
阿里巴巴
杭州  2026届  22-38K
负责电商前端研发。"""
    job = extract_fields(text)
    assert job.title == "前端开发工程师"
    assert job.company == "阿里巴巴"
    assert job.city == "杭州"
    assert job.confidence > 0.5


def test_low_confidence_when_missing_core():
    text = "一段没有明确职位和公司的模糊描述"
    job = extract_fields(text)
    # 没有公司和城市，置信度应较低
    assert job.confidence < 0.7
