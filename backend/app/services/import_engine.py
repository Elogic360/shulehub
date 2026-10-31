import csv
import io
import hashlib
import os
import re
import uuid
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date, timezone
import openpyxl

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.imports import (
    ImportBatch,
    ImportBatchFile,
    ImportStagingRow,
    ImportValidationError,
    ImportChangeRecord,
    ImportWorkflowType,
    ImportStatus,
    ImportRowStatus,
)
from app.models.academic import (
    Student,
    StudentEnrollment,
    Guardian,
    GuardianContact,
    StudentGuardian,
    GuardianRelationship,
    EnrollmentStatus,
    ClassGroup,
    AcademicYear,
    AcademicTerm,
    Gender,
)
from app.models.examinations import (
    Examination,
    Subject,
    ExaminationSubject,
    StudentExamResult,
    ResultStatus,
)
from app.models.fees import (
    FeeCategory,
    FeeStructure,
    FeeAssignment,
    FeeInvoice,
    FeeInvoiceItem,
    FeePayment,
    FeeStatus,
)
from app.utils.phone import normalize_tanzanian_phone

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


def sanitize_cell_value(val: Any) -> Any:
    """
    Prevents spreadsheet formula injection (CSV/Excel Formula Injection).
    If a string starts with =, +, -, @, or tab/carriage return, escapes or strips it.
    """
    if val is None:
        return ""
    if isinstance(val, (int, float, bool, date, datetime)):
        return val
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        # Strip dangerous leading characters for safe processing
        s = re.sub(r"^[\=\+\-\@\t\r]+", "", s).strip()
    return s


def parse_spreadsheet_file(
    content_bytes: bytes,
    filename: str,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Parses CSV or XLSX into a list of row dictionaries.
    Returns: (rows, detected_format)
    """
    lower_name = filename.lower()
    rows: List[Dict[str, Any]] = []

    if lower_name.endswith(".xlsx"):
        wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True, read_only=True)
        sheet = wb.active
        headers = []
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
            if row_idx == 0:
                headers = [str(sanitize_cell_value(h or "")).strip().lower() for h in row]
                continue
            if not any(row):
                continue
            row_dict = {}
            for col_idx, cell in enumerate(row):
                if col_idx < len(headers) and headers[col_idx]:
                    row_dict[headers[col_idx]] = sanitize_cell_value(cell)
            if row_dict:
                rows.append(row_dict)
        wb.close()
        return rows, "XLSX"

    elif lower_name.endswith(".csv"):
        text_content = content_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text_content))
        for row in reader:
            clean_row = {
                str(k).strip().lower(): sanitize_cell_value(v)
                for k, v in row.items()
                if k is not None
            }
            if any(clean_row.values()):
                rows.append(clean_row)
        return rows, "CSV"

    else:
        raise ValueError(f"Unsupported file format for {filename}. Only .xlsx and .csv are supported.")


def generate_unique_ussd_access_id(db: Session) -> str:
    """Generates a collision-free 6-digit numeric USSD identifier for student lookup."""
    import random
    for _ in range(50):
        candidate = f"{random.randint(100000, 999999)}"
        exists = db.execute(select(Student.id).where(Student.ussd_access_id == candidate)).scalar_one_or_none()
        if not exists:
            return candidate
    return f"{uuid.uuid4().int % 900000 + 100000}"


class ImportProcessor:
    def __init__(self, db: Session, batch: ImportBatch):
        self.db = db
        self.batch = batch
        self.school_id = batch.school_id

    def stage_file(self, content_bytes: bytes, filename: str) -> ImportBatch:
        """Parses file content, saves file record, stages rows, and validates."""
        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum allowed size ({MAX_FILE_SIZE_BYTES // (1024*1024)} MB)")

        sha256 = hashlib.sha256(content_bytes).hexdigest()

        # Check duplicate file
        existing_file = self.db.execute(
            select(ImportBatchFile).where(
                ImportBatchFile.sha256_hash == sha256,
                ImportBatchFile.batch_id != self.batch.id,
            )
        ).scalars().first()

        rows, file_fmt = parse_spreadsheet_file(content_bytes, filename)
        if not rows:
            raise ValueError("Uploaded spreadsheet contains no data rows.")

        # Save batch file record
        batch_file = ImportBatchFile(
            batch_id=self.batch.id,
            filename=filename,
            storage_path=f"storage/imports/{self.batch.id}_{filename}",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if file_fmt == "XLSX" else "text/csv",
            file_size_bytes=len(content_bytes),
            sha256_hash=sha256,
        )
        self.db.add(batch_file)

        self.batch.status = ImportStatus.PARSING
        self.batch.total_rows = len(rows)
        self.db.flush()

        # Stage rows
        staging_records = []
        for idx, row in enumerate(rows, start=1):
            staging_rec = ImportStagingRow(
                batch_id=self.batch.id,
                row_number=idx,
                raw_data=row,
                mapped_data=row,
                status=ImportRowStatus.PENDING,
                is_duplicate=bool(existing_file),
            )
            staging_records.append(staging_rec)
        self.db.add_all(staging_records)
        self.db.flush()

        # Validate rows
        self.validate_batch()
        return self.batch

    def validate_batch(self) -> None:
        """Validates all staged rows according to the batch workflow type."""
        self.batch.status = ImportStatus.VALIDATING
        self.db.flush()

        rows = self.db.execute(
            select(ImportStagingRow)
            .where(ImportStagingRow.batch_id == self.batch.id)
            .order_by(ImportStagingRow.row_number)
        ).scalars().all()

        # Clear existing validation errors
        for r in rows:
            r.status = ImportRowStatus.PENDING
            r.error_summary = None

        new_count = 0
        updated_count = 0
        unchanged_count = 0
        rejected_count = 0
        duplicate_count = 0
        warning_count = 0

        # Workflow-specific validation
        if self.batch.workflow_type == ImportWorkflowType.STUDENT_REGISTRATION:
            new_count, updated_count, rejected_count, duplicate_count, warning_count = self._validate_students(rows)
        elif self.batch.workflow_type == ImportWorkflowType.EXAM_RESULTS:
            new_count, updated_count, rejected_count, duplicate_count, warning_count = self._validate_exam_results(rows)
        elif self.batch.workflow_type == ImportWorkflowType.FEE_STRUCTURES:
            new_count, updated_count, rejected_count, duplicate_count, warning_count = self._validate_fee_structures(rows)
        elif self.batch.workflow_type == ImportWorkflowType.FEE_BALANCES:
            new_count, updated_count, rejected_count, duplicate_count, warning_count = self._validate_fee_balances(rows)

        self.batch.new_records_count = new_count
        self.batch.updated_records_count = updated_count
        self.batch.unchanged_records_count = unchanged_count
        self.batch.rejected_records_count = rejected_count
        self.batch.duplicate_records_count = duplicate_count
        self.batch.warning_count = warning_count

        self.batch.status = ImportStatus.PREVIEW_READY if rejected_count < len(rows) else ImportStatus.FAILED
        self.db.commit()

    def _validate_students(self, rows: List[ImportStagingRow]) -> Tuple[int, int, int, int, int]:
        new_cnt = 0
        upd_cnt = 0
        rej_cnt = 0
        dup_cnt = 0
        warn_cnt = 0

        seen_admissions = set()

        for stg in rows:
            data = stg.mapped_data
            errors = []

            # Admission number resolution
            adm = str(data.get("reg_no") or data.get("admission_number") or "").strip()
            full_name = str(data.get("full_name") or "").strip()
            if not full_name:
                first = str(data.get("first_name") or "").strip()
                last = str(data.get("last_name") or "").strip()
                if first and last:
                    full_name = f"{first} {last}"

            if not full_name:
                errors.append(("full_name", "MISSING_NAME", "Student full name is required."))

            if not adm:
                # Auto-generated flag
                stg.mapped_data["auto_generate_admission"] = True
            else:
                if adm in seen_admissions:
                    errors.append(("admission_number", "DUPLICATE_ROW", f"Duplicate admission number '{adm}' within file."))
                    dup_cnt += 1
                seen_admissions.add(adm)

            # Gender check
            gender_val = str(data.get("gender") or "").strip().upper()
            if gender_val not in ("M", "F", "MALE", "FEMALE"):
                errors.append(("gender", "INVALID_GENDER", f"Gender must be 'M' or 'F' (got: {gender_val})."))

            # Guardian phone check
            guardian_phone = str(data.get("guardian_phone") or data.get("phone") or "").strip()
            if guardian_phone:
                try:
                    norm = normalize_tanzanian_phone(guardian_phone)
                    stg.mapped_data["normalized_guardian_phone"] = norm
                except ValueError as e:
                    errors.append(("guardian_phone", "INVALID_PHONE", str(e)))

            if errors:
                stg.status = ImportRowStatus.ERROR
                stg.error_summary = "; ".join(e[2] for e in errors)
                rej_cnt += 1
                for col, code, msg in errors:
                    self.db.add(ImportValidationError(
                        batch_id=self.batch.id,
                        row_number=stg.row_number,
                        column_name=col,
                        error_code=code,
                        error_message=msg,
                        raw_value=str(data.get(col, "")),
                    ))
            else:
                stg.status = ImportRowStatus.VALID
                # Check if student exists in database
                if adm:
                    existing = self.db.execute(
                        select(Student).where(
                            Student.school_id == self.school_id,
                            Student.admission_number == adm,
                        )
                    ).scalar_one_or_none()
                    if existing:
                        stg.action_type = "UPDATE"
                        stg.target_entity_id = existing.id
                        upd_cnt += 1
                    else:
                        stg.action_type = "INSERT"
                        new_cnt += 1
                else:
                    stg.action_type = "INSERT"
                    new_cnt += 1

        return new_cnt, upd_cnt, rej_cnt, dup_cnt, warn_cnt

    def _validate_exam_results(self, rows: List[ImportStagingRow]) -> Tuple[int, int, int, int, int]:
        new_cnt = 0
        upd_cnt = 0
        rej_cnt = 0
        dup_cnt = 0
        warn_cnt = 0

        # Exam ID must be in metadata
        exam_id_str = self.batch.metadata_info.get("examination_id")
        if not exam_id_str:
            raise ValueError("Examination ID must be provided in batch metadata for EXAM_RESULTS import.")
        exam_id = uuid.UUID(exam_id_str)

        exam = self.db.execute(select(Examination).where(Examination.id == exam_id)).scalar_one_or_none()
        if not exam:
            raise ValueError(f"Examination with id '{exam_id}' does not exist.")

        class_group_id = self.batch.class_group_id

        # Cache existing students and subject mappings
        students_by_adm = {
            s.admission_number.upper(): s
            for s in self.db.execute(
                select(Student).where(Student.school_id == self.school_id)
            ).scalars().all()
        }

        # Find active subjects for school
        subjects_by_code = {
            s.code.upper(): s
            for s in self.db.execute(
                select(Subject).where(Subject.school_id == self.school_id)
            ).scalars().all()
        }

        for stg in rows:
            data = stg.mapped_data
            errors = []

            adm = str(data.get("admission_number") or data.get("reg_no") or "").strip().upper()
            if not adm:
                errors.append(("admission_number", "MISSING_ADMISSION", "Admission number is required."))
            elif adm not in students_by_adm:
                errors.append(("admission_number", "STUDENT_NOT_FOUND", f"No student found with admission '{adm}'."))

            # Inspect subject score columns
            subject_scores = {}
            for k, v in data.items():
                uk = k.upper()
                if uk in subjects_by_code:
                    val_str = str(v).strip().upper()
                    if val_str in ("ABS", "A", "ABSENT", "-"):
                        subject_scores[uk] = 0.0
                    else:
                        try:
                            score = float(val_str)
                            if score < 0 or score > 100:
                                errors.append((k, "SCORE_OUT_OF_BOUNDS", f"Score {score} exceeds 0-100 range."))
                            else:
                                subject_scores[uk] = score
                        except ValueError:
                            errors.append((k, "INVALID_NUMERIC_SCORE", f"Invalid score value '{val_str}'."))

            if not subject_scores and not errors:
                errors.append(("subjects", "NO_SUBJECT_SCORES", "No valid subject scores found in row."))

            stg.mapped_data["parsed_subject_scores"] = subject_scores

            if errors:
                stg.status = ImportRowStatus.ERROR
                stg.error_summary = "; ".join(e[2] for e in errors)
                rej_cnt += 1
                for col, code, msg in errors:
                    self.db.add(ImportValidationError(
                        batch_id=self.batch.id,
                        row_number=stg.row_number,
                        column_name=col,
                        error_code=code,
                        error_message=msg,
                        raw_value=str(data.get(col, "")),
                    ))
            else:
                stg.status = ImportRowStatus.VALID
                new_cnt += 1

        return new_cnt, upd_cnt, rej_cnt, dup_cnt, warn_cnt

    def _validate_fee_structures(self, rows: List[ImportStagingRow]) -> Tuple[int, int, int, int, int]:
        new_cnt = 0
        upd_cnt = 0
        rej_cnt = 0
        dup_cnt = 0
        warn_cnt = 0

        # Cache fee categories
        categories = {
            c.code.upper(): c
            for c in self.db.execute(
                select(FeeCategory).where(FeeCategory.school_id == self.school_id)
            ).scalars().all()
        }

        # Cache academic years
        years = {
            str(y.name): y
            for y in self.db.execute(
                select(AcademicYear).where(AcademicYear.school_id == self.school_id)
            ).scalars().all()
        }

        for stg in rows:
            data = stg.mapped_data
            errors = []

            cat_code = str(data.get("fee_category") or "TUITION").strip().upper()
            if cat_code not in categories:
                # Auto-create fee category if missing
                new_cat = FeeCategory(
                    school_id=self.school_id,
                    name=cat_code.capitalize(),
                    code=cat_code,
                    description=f"Auto-imported category {cat_code}",
                )
                self.db.add(new_cat)
                self.db.flush()
                categories[cat_code] = new_cat

            amt_raw = str(data.get("amount") or "0").replace(",", "").strip()
            try:
                amt = float(amt_raw)
                if amt <= 0:
                    errors.append(("amount", "INVALID_AMOUNT", "Fee amount must be greater than zero."))
                stg.mapped_data["parsed_amount"] = amt
            except ValueError:
                errors.append(("amount", "NON_NUMERIC_AMOUNT", f"Invalid fee amount '{amt_raw}'."))

            if errors:
                stg.status = ImportRowStatus.ERROR
                stg.error_summary = "; ".join(e[2] for e in errors)
                rej_cnt += 1
                for col, code, msg in errors:
                    self.db.add(ImportValidationError(
                        batch_id=self.batch.id,
                        row_number=stg.row_number,
                        column_name=col,
                        error_code=code,
                        error_message=msg,
                        raw_value=str(data.get(col, "")),
                    ))
            else:
                stg.status = ImportRowStatus.VALID
                new_cnt += 1

        return new_cnt, upd_cnt, rej_cnt, dup_cnt, warn_cnt

    def _validate_fee_balances(self, rows: List[ImportStagingRow]) -> Tuple[int, int, int, int, int]:
        new_cnt = 0
        upd_cnt = 0
        rej_cnt = 0
        dup_cnt = 0
        warn_cnt = 0

        students_by_adm = {
            s.admission_number.upper(): s
            for s in self.db.execute(
                select(Student).where(Student.school_id == self.school_id)
            ).scalars().all()
        }

        for stg in rows:
            data = stg.mapped_data
            errors = []

            adm = str(data.get("admission_number") or data.get("reg_no") or "").strip().upper()
            if not adm:
                errors.append(("admission_number", "MISSING_ADMISSION", "Admission number is required."))
            elif adm not in students_by_adm:
                errors.append(("admission_number", "STUDENT_NOT_FOUND", f"No student found with admission '{adm}'."))

            bal_raw = str(data.get("balance") or data.get("outstanding_balance") or "0").replace(",", "").strip()
            try:
                bal = float(bal_raw)
                stg.mapped_data["parsed_balance"] = bal
            except ValueError:
                errors.append(("balance", "NON_NUMERIC_BALANCE", f"Invalid balance '{bal_raw}'."))

            if errors:
                stg.status = ImportRowStatus.ERROR
                stg.error_summary = "; ".join(e[2] for e in errors)
                rej_cnt += 1
                for col, code, msg in errors:
                    self.db.add(ImportValidationError(
                        batch_id=self.batch.id,
                        row_number=stg.row_number,
                        column_name=col,
                        error_code=code,
                        error_message=msg,
                        raw_value=str(data.get(col, "")),
                    ))
            else:
                stg.status = ImportRowStatus.VALID
                new_cnt += 1

        return new_cnt, upd_cnt, rej_cnt, dup_cnt, warn_cnt

    def commit_batch(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Atomically commits all VALID rows in the staging table to application records."""
        if self.batch.status not in (ImportStatus.PREVIEW_READY, ImportStatus.APPROVED):
            raise ValueError(f"Cannot commit batch in status '{self.batch.status}'. Must be PREVIEW_READY or APPROVED.")

        self.batch.status = ImportStatus.COMMITTING
        self.db.flush()

        valid_rows = self.db.execute(
            select(ImportStagingRow).where(
                ImportStagingRow.batch_id == self.batch.id,
                ImportStagingRow.status.in_([ImportRowStatus.VALID, ImportRowStatus.WARNING]),
            ).order_by(ImportStagingRow.row_number)
        ).scalars().all()

        committed_count = 0
        change_records = []

        if self.batch.workflow_type == ImportWorkflowType.STUDENT_REGISTRATION:
            committed_count = self._commit_students(valid_rows, change_records)
        elif self.batch.workflow_type == ImportWorkflowType.EXAM_RESULTS:
            committed_count = self._commit_exam_results(valid_rows, change_records)
        elif self.batch.workflow_type == ImportWorkflowType.FEE_STRUCTURES:
            committed_count = self._commit_fee_structures(valid_rows, change_records)
        elif self.batch.workflow_type == ImportWorkflowType.FEE_BALANCES:
            committed_count = self._commit_fee_balances(valid_rows, change_records)

        self.batch.status = ImportStatus.COMMITTED
        self.batch.committed_at = datetime.now(timezone.utc)
        self.batch.approved_by_id = user_id
        self.db.commit()

        return {
            "batch_id": str(self.batch.id),
            "status": self.batch.status.value,
            "committed_rows": committed_count,
            "workflow_type": self.batch.workflow_type.value,
        }

    def _commit_students(self, valid_rows: List[ImportStagingRow], change_records: list) -> int:
        committed = 0
        default_year = self.db.execute(
            select(AcademicYear).where(AcademicYear.school_id == self.school_id).order_by(AcademicYear.start_date.desc())
        ).scalars().first()

        for stg in valid_rows:
            data = stg.mapped_data
            adm = str(data.get("reg_no") or data.get("admission_number") or "").strip()
            if not adm or data.get("auto_generate_admission"):
                # Collision-free admission number
                adm = f"SC{date.today().year}/{self.db.query(Student).filter(Student.school_id == self.school_id).count() + 1:04d}"

            name_parts = str(data.get("full_name") or "").split()
            first_name = name_parts[0] if name_parts else "Student"
            last_name = name_parts[-1] if len(name_parts) > 1 else "Child"
            middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else None

            gender_str = str(data.get("gender") or "M").upper()
            gender = Gender.FEMALE if gender_str.startswith("F") else Gender.MALE

            ussd_id = generate_unique_ussd_access_id(self.db)

            # Insert or update student
            student = self.db.execute(
                select(Student).where(Student.school_id == self.school_id, Student.admission_number == adm)
            ).scalar_one_or_none()

            action = "UPDATE" if student else "INSERT"
            before_state = {"admission_number": student.admission_number, "first_name": student.first_name} if student else None

            if not student:
                student = Student(
                    school_id=self.school_id,
                    admission_number=adm,
                    ussd_access_id=ussd_id,
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    gender=gender,
                    is_active=True,
                )
                self.db.add(student)
                self.db.flush()
            else:
                student.first_name = first_name
                student.last_name = last_name
                if not student.ussd_access_id:
                    student.ussd_access_id = ussd_id

            # Enroll in class group if provided
            class_id = self.batch.class_group_id
            if class_id and default_year:
                enrollment = self.db.execute(
                    select(StudentEnrollment).where(
                        StudentEnrollment.student_id == student.id,
                        StudentEnrollment.academic_year_id == default_year.id,
                    )
                ).scalar_one_or_none()
                if not enrollment:
                    enrollment = StudentEnrollment(
                        school_id=self.school_id,
                        student_id=student.id,
                        class_group_id=class_id,
                        academic_year_id=default_year.id,
                        enrollment_status=EnrollmentStatus.ACTIVE,
                    )
                    self.db.add(enrollment)

            # Guardian linking
            phone = data.get("normalized_guardian_phone")
            guardian_name = str(data.get("guardian_name") or f"Parent of {student.first_name}").strip()
            if phone:
                guardian = self.db.execute(
                    select(Guardian).where(Guardian.primary_phone == phone)
                ).scalar_one_or_none()
                if not guardian:
                    guardian = Guardian(
                        full_name=guardian_name,
                        primary_phone=phone,
                        preferred_language="sw",
                        is_verified=True,
                    )
                    self.db.add(guardian)
                    self.db.flush()

                # Link student to guardian
                link = self.db.execute(
                    select(StudentGuardian).where(
                        StudentGuardian.student_id == student.id,
                        StudentGuardian.guardian_id == guardian.id,
                    )
                ).scalar_one_or_none()
                if not link:
                    self.db.add(StudentGuardian(
                        student_id=student.id,
                        guardian_id=guardian.id,
                        relationship_type=GuardianRelationship.GUARDIAN,
                        is_fee_payer=True,
                        can_receive_results=True,
                    ))

            # Record change
            self.db.add(ImportChangeRecord(
                batch_id=self.batch.id,
                entity_type="Student",
                entity_id=student.id,
                action=action,
                before_state=before_state,
                after_state={"admission_number": student.admission_number, "name": f"{student.first_name} {student.last_name}"},
            ))

            stg.status = ImportRowStatus.COMMITTED
            committed += 1

        return committed

    def _commit_exam_results(self, valid_rows: List[ImportStagingRow], change_records: list) -> int:
        committed = 0
        exam_id = uuid.UUID(self.batch.metadata_info["examination_id"])
        class_group_id = self.batch.class_group_id

        subjects_by_code = {
            s.code.upper(): s
            for s in self.db.execute(
                select(Subject).where(Subject.school_id == self.school_id)
            ).scalars().all()
        }

        students_by_adm = {
            s.admission_number.upper(): s
            for s in self.db.execute(
                select(Student).where(Student.school_id == self.school_id)
            ).scalars().all()
        }

        for stg in valid_rows:
            data = stg.mapped_data
            adm = str(data.get("admission_number") or data.get("reg_no")).strip().upper()
            student = students_by_adm[adm]
            scores = data.get("parsed_subject_scores", {})

            for subj_code, score in scores.items():
                subject = subjects_by_code[subj_code]
                # Ensure ExaminationSubject exists
                exam_subj = self.db.execute(
                    select(ExaminationSubject).where(
                        ExaminationSubject.examination_id == exam_id,
                        ExaminationSubject.subject_id == subject.id,
                        ExaminationSubject.class_group_id == class_group_id,
                    )
                ).scalar_one_or_none()

                if not exam_subj:
                    exam_subj = ExaminationSubject(
                        examination_id=exam_id,
                        subject_id=subject.id,
                        class_group_id=class_group_id,
                        max_score=100.0,
                        pass_mark=40.0,
                    )
                    self.db.add(exam_subj)
                    self.db.flush()

                # Calculate letter grade (NECTA scale: A >= 75, B >= 65, C >= 45, D >= 30, F < 30)
                grade = "A" if score >= 75 else ("B" if score >= 65 else ("C" if score >= 45 else ("D" if score >= 30 else "F")))

                # Upsert StudentExamResult
                res = self.db.execute(
                    select(StudentExamResult).where(
                        StudentExamResult.examination_subject_id == exam_subj.id,
                        StudentExamResult.student_id == student.id,
                    )
                ).scalar_one_or_none()

                action = "UPDATE" if res else "INSERT"
                before_state = {"score": float(res.score), "grade": res.grade} if res else None

                if not res:
                    res = StudentExamResult(
                        examination_subject_id=exam_subj.id,
                        student_id=student.id,
                        score=score,
                        grade=grade,
                        status=ResultStatus.DRAFT,
                    )
                    self.db.add(res)
                    self.db.flush()
                else:
                    res.score = score
                    res.grade = grade

                self.db.add(ImportChangeRecord(
                    batch_id=self.batch.id,
                    entity_type="StudentExamResult",
                    entity_id=res.id,
                    action=action,
                    before_state=before_state,
                    after_state={"score": score, "grade": grade},
                ))

            stg.status = ImportRowStatus.COMMITTED
            committed += 1

        return committed

    def _commit_fee_structures(self, valid_rows: List[ImportStagingRow], change_records: list) -> int:
        committed = 0
        default_year = self.db.execute(
            select(AcademicYear).where(AcademicYear.school_id == self.school_id).order_by(AcademicYear.start_date.desc())
        ).scalars().first()

        for stg in valid_rows:
            data = stg.mapped_data
            amt = data.get("parsed_amount", 0.0)
            cat_code = str(data.get("fee_category") or "TUITION").strip().upper()
            cat = self.db.execute(
                select(FeeCategory).where(FeeCategory.school_id == self.school_id, FeeCategory.code == cat_code)
            ).scalars().first()

            desc = str(data.get("fee_description") or f"{cat_code} Fee").strip()
            due_date_val = date.today().replace(month=12, day=31)

            fee_struct = FeeStructure(
                school_id=self.school_id,
                academic_year_id=default_year.id,
                fee_category_id=cat.id,
                name=desc,
                amount_tzs=amt,
                due_date=due_date_val,
            )
            self.db.add(fee_struct)
            self.db.flush()

            self.db.add(ImportChangeRecord(
                batch_id=self.batch.id,
                entity_type="FeeStructure",
                entity_id=fee_struct.id,
                action="INSERT",
                before_state=None,
                after_state={"name": fee_struct.name, "amount_tzs": amt},
            ))

            stg.status = ImportRowStatus.COMMITTED
            committed += 1

        return committed

    def _commit_fee_balances(self, valid_rows: List[ImportStagingRow], change_records: list) -> int:
        committed = 0
        students_by_adm = {
            s.admission_number.upper(): s
            for s in self.db.execute(
                select(Student).where(Student.school_id == self.school_id)
            ).scalars().all()
        }
        default_year = self.db.execute(
            select(AcademicYear).where(AcademicYear.school_id == self.school_id).order_by(AcademicYear.start_date.desc())
        ).scalars().first()

        for stg in valid_rows:
            data = stg.mapped_data
            adm = str(data.get("admission_number") or data.get("reg_no")).strip().upper()
            student = students_by_adm[adm]
            bal = data.get("parsed_balance", 0.0)

            # Reconcile or adjust invoice balance
            inv = self.db.execute(
                select(FeeInvoice).where(
                    FeeInvoice.student_id == student.id,
                    FeeInvoice.academic_year_id == default_year.id,
                )
            ).scalar_one_or_none()

            if not inv and bal > 0:
                inv = FeeInvoice(
                    school_id=self.school_id,
                    student_id=student.id,
                    academic_year_id=default_year.id,
                    invoice_number=f"INV-{adm}-{date.today().year}",
                    total_amount_tzs=bal,
                    balance_due_tzs=bal,
                    status=FeeStatus.UNPAID,
                    due_date=date.today(),
                )
                self.db.add(inv)
                self.db.flush()
                self.db.add(ImportChangeRecord(
                    batch_id=self.batch.id,
                    entity_type="FeeInvoice",
                    entity_id=inv.id,
                    action="INSERT",
                    before_state=None,
                    after_state={"invoice_number": inv.invoice_number, "balance_due_tzs": bal},
                ))
            elif inv:
                before_state = {"balance_due_tzs": float(inv.balance_due_tzs)}
                inv.balance_due_tzs = bal
                inv.status = FeeStatus.PAID if bal <= 0 else (FeeStatus.PARTIALLY_PAID if bal < float(inv.total_amount_tzs) else FeeStatus.UNPAID)
                self.db.add(ImportChangeRecord(
                    batch_id=self.batch.id,
                    entity_type="FeeInvoice",
                    entity_id=inv.id,
                    action="UPDATE",
                    before_state=before_state,
                    after_state={"balance_due_tzs": bal, "status": inv.status.value},
                ))

            stg.status = ImportRowStatus.COMMITTED
            committed += 1

        return committed

    def revert_batch(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Safely rolls back changes recorded in import_change_records."""
        if self.batch.status != ImportStatus.COMMITTED:
            raise ValueError(f"Cannot revert batch in status '{self.batch.status}'. Only COMMITTED batches can be reverted.")

        records = self.db.execute(
            select(ImportChangeRecord).where(ImportChangeRecord.batch_id == self.batch.id)
        ).scalars().all()

        reverted_count = 0
        for rec in reversed(records):
            if rec.action == "INSERT":
                # Delete inserted entity
                if rec.entity_type == "Student":
                    s = self.db.get(Student, rec.entity_id)
                    if s:
                        self.db.delete(s)
                elif rec.entity_type == "StudentExamResult":
                    r = self.db.get(StudentExamResult, rec.entity_id)
                    if r:
                        self.db.delete(r)
                elif rec.entity_type == "FeeStructure":
                    fs = self.db.get(FeeStructure, rec.entity_id)
                    if fs:
                        self.db.delete(fs)
                elif rec.entity_type == "FeeInvoice":
                    fi = self.db.get(FeeInvoice, rec.entity_id)
                    if fi:
                        self.db.delete(fi)
                reverted_count += 1
            elif rec.action == "UPDATE" and rec.before_state:
                # Restore previous values
                if rec.entity_type == "StudentExamResult":
                    r = self.db.get(StudentExamResult, rec.entity_id)
                    if r and "score" in rec.before_state:
                        r.score = rec.before_state["score"]
                        r.grade = rec.before_state["grade"]
                        reverted_count += 1
                elif rec.entity_type == "FeeInvoice":
                    fi = self.db.get(FeeInvoice, rec.entity_id)
                    if fi and "balance_due_tzs" in rec.before_state:
                        fi.balance_due_tzs = rec.before_state["balance_due_tzs"]
                        reverted_count += 1

        self.batch.status = ImportStatus.REVERTED
        self.batch.reverted_at = datetime.now(timezone.utc)
        self.batch.reverted_by_id = user_id

        # Update staging rows status
        for stg in self.batch.staging_rows:
            stg.status = ImportRowStatus.REVERTED

        self.db.commit()

        return {
            "batch_id": str(self.batch.id),
            "status": self.batch.status.value,
            "reverted_records": reverted_count,
        }
