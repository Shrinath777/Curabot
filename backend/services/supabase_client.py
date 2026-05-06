"""
Supabase Client — Handles auth, user profiles, chat persistence, and medical reports.
Falls back to local SQLite if Supabase is not configured.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)
logger = logging.getLogger(__name__)

# Try Supabase import
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("supabase-py not installed. Using local storage fallback.")

import sqlite3


class SupabaseService:
    """Service layer for Supabase operations with SQLite fallback."""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
        self.client: Optional[Any] = None
        self.use_local = True
        self.local_db_path = os.getenv("SQLITE_DB_PATH", "./curabot_local.db")

        self._init_client()

    def _init_client(self):
        """Initialize Supabase or fallback to SQLite."""
        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                self.use_local = False
                logger.info("Connected to Supabase")
                return
            except Exception as e:
                logger.warning(f"Supabase connection failed: {e}. Using local DB.")

        # Fallback to SQLite
        self.use_local = True
        self._init_local_db()
        logger.info("Using local SQLite database")

    def _init_local_db(self):
        """Initialize local SQLite database."""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY REFERENCES users(id),
                full_name TEXT,
                age INTEGER,
                gender TEXT,
                blood_group TEXT,
                known_conditions TEXT,
                medications TEXT,
                allergies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                title TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES chat_sessions(id),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS medical_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                file_name TEXT,
                file_url TEXT,
                report_type TEXT,
                extracted_text TEXT,
                parsed_data TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS diagnosis_history (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES chat_sessions(id),
                user_id TEXT REFERENCES users(id),
                final_hypotheses TEXT,
                evidence_summary TEXT,
                confidence_trajectory TEXT,
                concluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        conn.close()

    # ==================== AUTH ====================

    async def signup(self, email: str, password: str, full_name: str = "") -> Dict[str, Any]:
        """Register a new user."""
        if not self.use_local and self.client:
            try:
                res = self.client.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {"data": {"full_name": full_name}}
                })
                user_id = res.user.id if res.user else None
                if user_id:
                    # Mirror the auth user into our custom 'users' table to satisfy the foreign key constraint
                    try:
                        self.client.table("users").insert({
                            "id": user_id,
                            "email": email,
                            "password_hash": "handled_by_supabase",
                            "full_name": full_name
                        }).execute()
                    except Exception as mirror_e:
                        logger.warning(f"Failed to mirror user in public table (might already exist): {mirror_e}")

                    self.client.table("user_profiles").insert({
                        "id": user_id, "full_name": full_name
                    }).execute()
                return {"user_id": user_id, "email": email, "status": "success"}
            except Exception as e:
                return {"error": str(e), "status": "error"}
        else:
            return self._local_signup(email, password, full_name)

    def _local_signup(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """Local SQLite signup."""
        import hashlib
        user_id = str(uuid.uuid4())
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (id, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
                (user_id, email, password_hash, full_name)
            )
            cursor.execute(
                "INSERT INTO user_profiles (id, full_name) VALUES (?, ?)",
                (user_id, full_name)
            )
            conn.commit()
            return {"user_id": user_id, "email": email, "status": "success"}
        except sqlite3.IntegrityError:
            return {"error": "Email already exists", "status": "error"}
        finally:
            conn.close()

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user."""
        if not self.use_local and self.client:
            try:
                res = self.client.auth.sign_in_with_password({
                    "email": email, "password": password
                })
                return {
                    "user_id": res.user.id,
                    "email": email,
                    "access_token": res.session.access_token,
                    "status": "success"
                }
            except Exception as e:
                return {"error": str(e), "status": "error"}
        else:
            return self._local_login(email, password)

    def _local_login(self, email: str, password: str) -> Dict[str, Any]:
        """Local SQLite login."""
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, full_name FROM users WHERE email = ? AND password_hash = ?",
            (email, password_hash)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            token = str(uuid.uuid4())  # Simple token for local dev
            return {
                "user_id": row[0],
                "email": row[1],
                "full_name": row[2],
                "access_token": token,
                "status": "success"
            }
        return {"error": "Invalid credentials", "status": "error"}

    # ==================== USER PROFILES ====================

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with medical history."""
        if not self.use_local and self.client:
            try:
                res = self.client.table("user_profiles").select("*").eq("id", user_id).execute()
                return res.data[0] if res.data else None
            except Exception:
                return None
        else:
            conn = sqlite3.connect(self.local_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                profile = dict(row)
                # Parse JSON arrays
                for field in ["known_conditions", "medications", "allergies"]:
                    if profile.get(field):
                        try:
                            profile[field] = json.loads(profile[field])
                        except (json.JSONDecodeError, TypeError):
                            profile[field] = []
                    else:
                        profile[field] = []
                return profile
            return None

    async def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Update user profile."""
        if not self.use_local and self.client:
            try:
                self.client.table("user_profiles").update(data).eq("id", user_id).execute()
                return True
            except Exception:
                return False
        else:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            # Serialize lists to JSON
            for field in ["known_conditions", "medications", "allergies"]:
                if field in data and isinstance(data[field], list):
                    data[field] = json.dumps(data[field])

            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            values = list(data.values()) + [user_id]
            cursor.execute(f"UPDATE user_profiles SET {set_clause} WHERE id = ?", values)
            conn.commit()
            conn.close()
            return True

    # ==================== CHAT SESSIONS ====================

    async def create_session(self, user_id: str, title: str = "New Diagnosis", session_id: Optional[str] = None) -> str:
        """Create a new chat session."""
        session_id = session_id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        if not self.use_local and self.client:
            try:
                self.client.table("chat_sessions").insert({
                    "id": session_id, "user_id": user_id,
                    "title": title, "status": "active",
                    "created_at": now, "updated_at": now
                }).execute()
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
        else:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (id, user_id, title, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, user_id, title, "active", now, now)
            )
            conn.commit()
            conn.close()

        return session_id

    async def save_message(
        self, session_id: str, role: str, content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Save a chat message."""
        msg_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata) if metadata else None

        if not self.use_local and self.client:
            try:
                self.client.table("chat_messages").insert({
                    "id": msg_id, "session_id": session_id,
                    "role": role, "content": content,
                    "metadata": metadata, "created_at": now
                }).execute()
            except Exception as e:
                logger.error(f"Failed to save message: {e}")
        else:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_messages (id, session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, meta_json, now)
            )
            conn.commit()
            conn.close()

        return msg_id

    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        if not self.use_local and self.client:
            try:
                res = self.client.table("chat_messages") \
                    .select("*") \
                    .eq("session_id", session_id) \
                    .order("created_at") \
                    .execute()
                return res.data or []
            except Exception:
                return []
        else:
            conn = sqlite3.connect(self.local_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            for row in rows:
                if row.get("metadata"):
                    try:
                        row["metadata"] = json.loads(row["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        row["metadata"] = {}
            return rows

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        if not self.use_local and self.client:
            try:
                res = self.client.table("chat_sessions") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .order("updated_at", desc=True) \
                    .execute()
                return res.data or []
            except Exception:
                return []
        else:
            conn = sqlite3.connect(self.local_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows

    # ==================== MEDICAL REPORTS ====================

    async def upload_file_to_storage(self, file_bytes: bytes, file_name: str, content_type: str = "application/pdf") -> Optional[str]:
        """Upload a physical file to Supabase Storage bucket."""
        if not self.use_local and self.client:
            try:
                # Upload the file bytes to 'medical_reports' bucket
                self.client.storage.from_("medical_reports").upload(
                    file_name,
                    file_bytes,
                    file_options={"content-type": content_type}
                )
                # Retrieve the public URL
                public_url = self.client.storage.from_("medical_reports").get_public_url(file_name)
                # get_public_url returns a string directly? In supabase-py it returns a string if public
                if type(public_url) == str:
                    return public_url
                elif type(public_url) == dict:
                    return public_url.get("publicURL") # Handle older sdk formats just in case
            except Exception as e:
                logger.error(f"Failed to upload file to storage bucket: {e}")
                return None
        return None

    async def save_medical_report(
        self, user_id: str, file_name: str,
        report_type: str, extracted_text: str = "",
        parsed_data: Optional[Dict] = None,
        file_url: str = ""
    ) -> str:
        """Save a medical report."""
        report_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        if not self.use_local and self.client:
            try:
                self.client.table("medical_reports").insert({
                    "id": report_id, "user_id": user_id,
                    "file_name": file_name, "file_url": file_url, "report_type": report_type,
                    "extracted_text": extracted_text,
                    "parsed_data": parsed_data, "uploaded_at": now
                }).execute()
            except Exception as e:
                logger.error(f"Failed to save report: {e}")
        else:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO medical_reports (id, user_id, file_name, file_url, report_type, extracted_text, parsed_data, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (report_id, user_id, file_name, file_url, report_type, extracted_text,
                 json.dumps(parsed_data) if parsed_data else None, now)
            )
            conn.commit()
            conn.close()

        return report_id

    async def get_user_reports(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all medical reports for a user."""
        if not self.use_local and self.client:
            try:
                res = self.client.table("medical_reports") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .order("uploaded_at", desc=True) \
                    .execute()
                return res.data or []
            except Exception:
                return []
        else:
            conn = sqlite3.connect(self.local_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM medical_reports WHERE user_id = ? ORDER BY uploaded_at DESC",
                (user_id,)
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            for row in rows:
                if row.get("parsed_data"):
                    try:
                        row["parsed_data"] = json.loads(row["parsed_data"])
                    except (json.JSONDecodeError, TypeError):
                        row["parsed_data"] = {}
            return rows

    # ==================== DIAGNOSIS HISTORY ====================

    async def save_diagnosis(
        self, session_id: str, user_id: str,
        hypotheses: List[Dict], evidence: List[Dict],
        confidence_trajectory: List[Dict]
    ) -> str:
        """Save completed diagnosis."""
        diag_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        if not self.use_local and self.client:
            try:
                self.client.table("diagnosis_history").insert({
                    "id": diag_id, "session_id": session_id,
                    "user_id": user_id,
                    "final_hypotheses": hypotheses,
                    "evidence_summary": evidence,
                    "confidence_trajectory": confidence_trajectory,
                    "concluded_at": now
                }).execute()
            except Exception as e:
                logger.error(f"Failed to save diagnosis: {e}")
        else:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO diagnosis_history (id, session_id, user_id, final_hypotheses, evidence_summary, confidence_trajectory, concluded_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (diag_id, session_id, user_id,
                 json.dumps(hypotheses), json.dumps(evidence),
                 json.dumps(confidence_trajectory), now)
            )
            conn.commit()
            conn.close()

        return diag_id

    async def get_user_diagnosis_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get diagnosis history for a user."""
        if not self.use_local and self.client:
            try:
                res = self.client.table("diagnosis_history") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .order("concluded_at", desc=True) \
                    .execute()
                return res.data or []
            except Exception:
                return []
        else:
            conn = sqlite3.connect(self.local_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM diagnosis_history WHERE user_id = ? ORDER BY concluded_at DESC",
                (user_id,)
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            for row in rows:
                for field in ["final_hypotheses", "evidence_summary", "confidence_trajectory"]:
                    if row.get(field):
                        try:
                            row[field] = json.loads(row[field])
                        except (json.JSONDecodeError, TypeError):
                            row[field] = []
            return rows

    # ==================== USER CONTEXT (for old users) ====================

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Build full user context for returning patients.
        Includes profile, past diagnoses with severity tracking,
        medical reports, and recent chat history for longitudinal analysis.
        """
        profile = await self.get_user_profile(user_id)
        diagnoses = await self.get_user_diagnosis_history(user_id)
        reports = await self.get_user_reports(user_id)

        # Get last 3 sessions' messages for context
        sessions = await self.get_user_sessions(user_id)
        recent_conversations = []
        for sess in sessions[:3]:
            messages = await self.get_session_messages(sess["id"])
            recent_conversations.append({
                "session_id": sess["id"],
                "title": sess.get("title", ""),
                "messages": messages[:20]
            })

        # ── SEVERITY TRACKING ──────────────────────────────────────────────────
        # Build a structured history of conditions with their confidence over time
        # so agents can detect worsening, improvement, or recurrence
        severity_history = []
        for dx in diagnoses:
            hyps = dx.get("final_hypotheses", [])
            if not hyps or not isinstance(hyps, list):
                continue
            top = hyps[0] if hyps else {}
            severity_history.append({
                "date": dx.get("concluded_at", ""),
                "condition": top.get("name", "Unknown"),
                "confidence": top.get("confidence", 0),
                "supporting_factors": top.get("supporting", 0),
                "contradicting_factors": top.get("contradicting", 0),
                "reasoning": top.get("reasoning", ""),
                "all_hypotheses": [
                    {"name": h.get("name"), "confidence": h.get("confidence")}
                    for h in hyps[:3]
                ]
            })

        # Group by condition name to detect recurring issues
        condition_frequency: Dict[str, list] = {}
        for entry in severity_history:
            cond = entry["condition"]
            if cond not in condition_frequency:
                condition_frequency[cond] = []
            condition_frequency[cond].append(entry)

        # Find recurring conditions (appeared more than once)
        recurring_conditions = {
            cond: entries
            for cond, entries in condition_frequency.items()
            if len(entries) > 1
        }

        return {
            "profile": profile,
            "past_diagnoses": diagnoses[:5],
            "medical_reports": reports[:10],
            "recent_conversations": recent_conversations,
            "is_returning_user": len(diagnoses) > 0 or len(reports) > 0,
            "severity_history": severity_history,             # all past conditions ordered newest first
            "recurring_conditions": recurring_conditions,     # conditions seen more than once
            "total_past_sessions": len(diagnoses),
        }


# Singleton instance
supabase_service = SupabaseService()
