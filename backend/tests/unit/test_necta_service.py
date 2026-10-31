import pytest
import uuid
from app.services.necta_service import NectaResultParser, NectaMatcher
from app.models.necta import NectaExamination, NectaCandidate, NectaExamType, NectaMatchStatus, NectaStudentMatch
from app.models.academic import Student, Gender
from app.core.database import set_rls_tenant_context


def test_parse_candidate_row_pipe_format():
    raw = "S0101/0001 | AMINA BAKARI | F | I | 12 | CIV - 'C' HIST - 'B' GEO - 'B' KISW - 'A' ENGL - 'A' B/MATH - 'B'"
    cand = NectaResultParser.parse_candidate_row(raw)
    assert cand is not None
    assert cand["index_number"] == "S0101/0001"
    assert cand["candidate_name"] == "AMINA BAKARI"
    assert cand["sex"] == "F"
    assert cand["division"] == "I"
    assert cand["points"] == 12
    assert len(cand["subjects"]) == 6
    assert cand["subjects"][3]["code"] == "KISW"
    assert cand["subjects"][3]["grade"] == "A"


def test_parse_candidate_row_regex_fallback():
    raw = "S0101/0002 M II 18 CIV - 'C' HIST - 'C' KISW - 'B' ENGL - 'C'"
    cand = NectaResultParser.parse_candidate_row(raw)
    assert cand is not None
    assert cand["index_number"] == "S0101/0002"
    assert cand["sex"] == "M"
    assert cand["division"] == "II"
    assert cand["points"] == 18
    assert len(cand["subjects"]) == 4


def test_parse_candidate_row_invalid():
    assert NectaResultParser.parse_candidate_row("") is None
    assert NectaResultParser.parse_candidate_row("   ") is None
    assert NectaResultParser.parse_candidate_row("Not a candidate line") is None


def test_necta_matcher_exact_and_review(db_session, test_school, test_user):
    set_rls_tenant_context(db_session, test_school.id)

    # 1. Create NECTA Exam
    uid = uuid.uuid4().hex[:4]
    exam = NectaExamination(
        school_id=test_school.id,
        exam_type=NectaExamType.CSEE,
        exam_year=2025,
        center_number=f"S01{uid}",
        center_name="Test Secondary Center",
        source_url=f"https://maktaba.tetea.org/exam-results/CSEE2025/s01{uid}.htm",
        is_published=True,
    )
    db_session.add(exam)
    db_session.flush()

    # 2. Create Candidate 1 (exact match on index)
    cand1 = NectaCandidate(
        examination_id=exam.id,
        index_number="S0101/0010",
        candidate_name="Rashid Mussa",
        sex="M",
        division="I",
        points=14,
    )
    # Candidate 2 (name match)
    cand2 = NectaCandidate(
        examination_id=exam.id,
        index_number="S0101/0020",
        candidate_name="Amina Juma",
        sex="F",
        division="II",
        points=19,
    )
    # Candidate 3 (unmatched)
    cand3 = NectaCandidate(
        examination_id=exam.id,
        index_number="S0101/0030",
        candidate_name="Unknown Person",
        sex="M",
        division="IV",
        points=28,
    )
    db_session.add_all([cand1, cand2, cand3])
    db_session.flush()

    # 3. Create Students
    std1 = Student(
        school_id=test_school.id,
        admission_number="S0101/0010",
        first_name="Rashid",
        last_name="Mussa",
        gender=Gender.MALE,
        ussd_access_id="991122",
        is_active=True,
    )
    std2 = Student(
        school_id=test_school.id,
        admission_number="STD-8899",
        first_name="Amina",
        last_name="Juma",
        gender=Gender.FEMALE,
        ussd_access_id="991123",
        is_active=True,
    )
    db_session.add_all([std1, std2])
    db_session.commit()

    # 4. Run Matcher
    matcher = NectaMatcher(db_session, test_school.id)
    summary = matcher.match_candidates(exam.id)

    assert summary["total_candidates"] == 3
    assert summary["exact_matches"] == 1
    assert summary["pending_manual_review"] == 1

    # Verify Matches in DB
    match1 = db_session.query(NectaStudentMatch).filter(NectaStudentMatch.candidate_id == cand1.id).first()
    assert match1 is not None
    assert match1.student_id == std1.id
    assert match1.status == NectaMatchStatus.MATCHED
    assert float(match1.match_confidence) == 1.0

    match2 = db_session.query(NectaStudentMatch).filter(NectaStudentMatch.candidate_id == cand2.id).first()
    assert match2 is not None
    assert match2.student_id == std2.id
    assert match2.status == NectaMatchStatus.PENDING_REVIEW
    assert float(match2.match_confidence) == 0.900
