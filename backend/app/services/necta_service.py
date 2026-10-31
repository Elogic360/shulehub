import re
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.necta import (
    NectaExamination,
    NectaCandidate,
    NectaCandidateSubject,
    NectaStudentMatch,
    NectaFetchError,
    NectaExamType,
    NectaMatchStatus,
)
from app.models.academic import Student

logger = logging.getLogger("shuleconnect.necta")


class NectaResultParser:
    """
    Parses structured Tanzanian NECTA examination results (FTNA and CSEE).
    Extracts candidate index numbers (e.g., S0101/0001), sex, division, points,
    and individual subject grades (e.g., CIV - 'C' HIST - 'B' GEO - 'C' KISW - 'A' ENGL - 'B' PHY - 'C' CHE - 'C' BIO - 'C' B/MATH - 'B').
    """

    @staticmethod
    def parse_candidate_row(raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Parses a single candidate result string or structured data entry.
        Example format:
        S0101/0001 | F | I | 14 | CIV - 'C' HIST - 'B' GEO - 'C' KISW - 'A' ENGL - 'B' B/MATH - 'A'
        """
        if not raw_text or not raw_text.strip():
            return None

        # Clean spaces
        line = raw_text.strip()
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5:
            # Fallback regex extraction
            match = re.search(r"([SP]\d{4}/\d{4})\s+([MF])\s+([I|V|X|0]+|\w+)\s+(\d+)\s+(.+)", line)
            if not match:
                return None
            index_no = match.group(1).upper()
            sex = match.group(2).upper()
            division = match.group(3).upper()
            points = int(match.group(4))
            subj_str = match.group(5)
            name = f"Candidate {index_no}"
        else:
            index_no = parts[0].upper()
            name = parts[1] if len(parts) > 5 else f"Candidate {index_no}"
            sex = parts[2] if len(parts) > 5 else parts[1]
            division = parts[3] if len(parts) > 5 else parts[2]
            try:
                points = int(parts[4] if len(parts) > 5 else parts[3])
            except ValueError:
                points = None
            subj_str = parts[5] if len(parts) > 5 else parts[4]

        # Parse subjects and grades: e.g. "CIV - 'C'  HIST - 'B'  KISW - 'A'"
        subjects = []
        subj_matches = re.findall(r"([A-Za-z/]+)\s*-\s*['\"]?([A-Fa-f])['\"]?", subj_str)
        for scode, sgrade in subj_matches:
            subjects.append({
                "code": scode.upper(),
                "name": scode.upper(),
                "grade": sgrade.upper(),
            })

        return {
            "index_number": index_no,
            "candidate_name": name,
            "sex": sex.upper(),
            "division": division.upper(),
            "points": points,
            "subjects": subjects,
        }


class NectaMatcher:
    def __init__(self, db: Session, school_id: uuid.UUID):
        self.db = db
        self.school_id = school_id

    def match_candidates(self, examination_id: uuid.UUID) -> Dict[str, Any]:
        """
        Matches NECTA candidates against enrolled school students.
        Primary match: Exact examination index number / admission number.
        Secondary match: Full student name similarity with high threshold.
        """
        candidates = self.db.execute(
            select(NectaCandidate).where(NectaCandidate.examination_id == examination_id)
        ).scalars().all()

        students = self.db.execute(
            select(Student).where(Student.school_id == self.school_id, Student.is_active == True)
        ).scalars().all()

        students_by_adm = {s.admission_number.upper(): s for s in students}
        students_by_name = {f"{s.first_name} {s.last_name}".upper(): s for s in students}

        exact_matches = 0
        manual_review = 0

        for cand in candidates:
            # Check existing match
            existing = self.db.execute(
                select(NectaStudentMatch).where(NectaStudentMatch.candidate_id == cand.id)
            ).scalar_one_or_none()
            if existing:
                continue

            matched_student = None
            confidence = 0.0

            # 1. Exact index match (e.g. student's admission number matches index number)
            clean_index = cand.index_number.upper()
            if clean_index in students_by_adm:
                matched_student = students_by_adm[clean_index]
                confidence = 1.000
            else:
                # Check candidate name match
                cname = cand.candidate_name.upper()
                if cname in students_by_name:
                    matched_student = students_by_name[cname]
                    confidence = 0.900

            if matched_student:
                status = NectaMatchStatus.MATCHED if confidence >= 0.95 else NectaMatchStatus.PENDING_REVIEW
                match_rec = NectaStudentMatch(
                    school_id=self.school_id,
                    candidate_id=cand.id,
                    student_id=matched_student.id,
                    match_confidence=confidence,
                    status=status,
                    review_notes=f"Auto-matched with confidence {confidence * 100:.1f}%",
                )
                self.db.add(match_rec)
                if status == NectaMatchStatus.MATCHED:
                    exact_matches += 1
                else:
                    manual_review += 1

        self.db.commit()
        return {
            "total_candidates": len(candidates),
            "exact_matches": exact_matches,
            "pending_manual_review": manual_review,
        }
