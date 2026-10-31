# ShuleConnect Security & Compliance Policy

## 1. Security Architecture & Threat Model

ShuleConnect processes sensitive academic, financial, and personal data belonging to minors and their legal guardians in Tanzania. The security architecture adheres to **Defense in Depth** principles across physical, network, application, database, and administrative tiers.

### Core Threat Vectors Addressed
1. **Cross-Tenant Data Leakage**: Malicious or accidental disclosure of student rosters, examination rankings, or fee structures between rival private schools.
2. **Horizontal Privilege Escalation**: A class teacher accessing or modifying academic records belonging to another class.
3. **Insecure Communications / Unencrypted Data in Transit**: Exposing sensitive minor examination scores over open telecommunication SMS networks.
4. **Credential Harvesting & Session Hijacking**: Brute-force attacks against staff portals or replay of expired authentication tokens.

---

## 2. Authentication & Authorization Controls

### 2.1 Password Hashing
All user passwords must meet institutional strength requirements and are hashed using **Argon2id** (via `argon2-cffi`), the state-of-the-art memory-hard key derivation function recommended by OWASP:
- Time cost: 3 iterations
- Memory cost: 65,536 KiB (64 MiB)
- Parallelism: 4 lanes

Plain-text passwords are never logged, persisted in cache, or exposed in error tracebacks.

### 2.2 JWT Token Lifetime & Rotation
- **Access Tokens**: Short-lived (`60 minutes`), signed with HMAC-SHA256 (`HS256`) using high-entropy secrets (`SECRET_KEY`). Contains claims: `sub` (User UUID), `school_id`, `role`, and `exp`.
- **Refresh Tokens**: Cryptographically random 64-character tokens with a `7-day` sliding expiry stored in PostgreSQL with one-time rotation and invalidation on logout.

### 2.3 Class-Scoped Authorization Engine
Class Teachers are restricted to their assigned classes. Any API request affecting students, marks, or campaigns in a class verifies that the authenticated user possesses an active `teacher_assignments` record linking them to that specific `class_group_id`.

---

## 3. Database Isolation: Row-Level Security (RLS)

PostgreSQL 18 Row-Level Security (RLS) provides an immutable kernel-level barrier:
1. Every authenticated database transaction executes `SELECT set_config('app.current_school_id', :school_id, true)`.
2. Tables have `FORCE ROW LEVEL SECURITY` enabled to prevent table owners or unintended connection pool leaks from bypassing policies.
3. If an attacker bypasses application-level `WHERE` clauses via SQL injection, the PostgreSQL query planner automatically appends the RLS policy filter, ensuring zero records from other schools can be read or modified.

---

## 4. Tanzania Personal Data Protection Act (PDPA 2022) Compliance

ShuleConnect complies with the **Personal Data Protection Act (PDPA No. 11 of 2022)** and regulations enforced by the Personal Data Protection Commission (PDPC) of Tanzania:

### 4.1 Minor Data Privacy
1. **Academic Confidentiality**: A student's examination marks, overall percentage, and class ranking are strictly confidential personal data.
2. **No Plaintext Mark Broadcasts**: Broadcast SMS notifications must never disclose raw marks or rank. Messages are restricted to:
   > *"Habari [Mzazi]. Matokeo ya mtihani wa [Mtoto] wa [Mtihani] yametangazwa. Tafadhali piga *148*99# au tembelea [Kiunganishi Salama] kuona ripoti."*
3. **One-Time Tokenized Verification**: Accessing the report card link requires entering the registered parent's mobile number and verifying an OTP.

### 4.2 Data Subject Rights
- **Right to Rectification**: Parents may request corrections to their mobile number or student details through the verified school administrator.
- **Right to Erasure**: Academic records for graduated students are retained for the statutory 7-year educational audit window, after which personal identifiable contacts (phone numbers, photos) may be scrubbed upon written request.

---

## 5. Telecommunications & Messaging Security

1. **E.164 Normalization**: Eliminates dialer ambiguity by enforcing `+255...` formatting before gateway submission.
2. **SMS Rate Limiting & Fraud Prevention**:
   - Outbound campaign queues are rate-limited to 50 SMS/second to comply with Africa's Talking provider limits and prevent accidental telco blacklisting.
   - Idempotency keys are assigned to each outbound message to prevent duplicate charges or spamming recipients during network retries.
3. **Delivery Webhook Authentication**: Africa's Talking delivery report webhooks validate gateway signatures and user agents before accepting status updates.

---

## 6. Audit Logging & Traceability

All privileged administrative operations generate immutable audit log entries in the `audit_logs` table:
- Action type (`SCHOOL_REGISTERED`, `STAFF_CREATED`, `MARKS_PUBLISHED`, `PAYMENT_RECORDED`)
- User ID and IP address of the actor
- School ID
- JSONB diff of the resource before and after mutation
- Accurate timestamp (`TIMESTAMPTZ`)

---

## 7. Incident Response & Vulnerability Reporting

If a potential security vulnerability or unauthorized access incident is detected:
1. **Notification Window**: The Incident Response Team must be alerted within 1 hour at `security@shuleconnect.co.tz`.
2. **Breach Notification**: Under PDPA 2022 requirements, affected schools and the Personal Data Protection Commission (PDPC) will be formally notified within 72 hours of confirmation of any data breach involving personal identifiers.
