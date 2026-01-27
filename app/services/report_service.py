"""
Report service - Core service for managing medical reports
Orchestrates OCR, AI, and data storage
"""
import uuid
from datetime import datetime
import asyncio
from typing import List, Optional, Dict, Any

from fastapi import BackgroundTasks, Request

from app.core.security import get_authed_supabase_client
from app.services.premium_service import PremiumService
from app.services.safety_service import SafetyService
from app.utils.ocr import OCRService
from app.utils.ocr import OCRService
from app.ai.explanations import ExplanationService
from app.ai.synthesis import SynthesisService
from app.schemas.report import ReportResponse, TestParameterResponse
from app.core.config import settings
from app.core.security import get_authed_supabase_client, get_service_supabase_client
from app.supabase.storage_service import upload_to_supabase_storage



class ReportService:
    """Service for managing medical reports"""

    def __init__(self, request: Request):
        # ✅ AUTHENTICATED SUPABASE CLIENT (JWT INCLUDED → RLS SAFE)
        self.db = get_authed_supabase_client(request)
        # ✅ SERVICE ROLE CLIENT FOR STORAGE (BYPASSES RLS)
        self.storage_client = get_service_supabase_client()
        self.premium_service = PremiumService()
        self.safety_service = SafetyService()
        self.ocr_service = OCRService()
        self.ocr_service = OCRService()
        self.explanation_service = ExplanationService()
        self.synthesis_service = SynthesisService()

    async def verify_family_access(self, requester_id: str, target_id: str) -> bool:
        """Verify if requester has family connection with target"""
        if requester_id == target_id:
            return True
            
        # Check for confirmed connection in either direction
        response = self.storage_client.table("family_connections").select("id").or_(
            f"and(user_id.eq.{requester_id},connected_user_id.eq.{target_id},status.eq.connected),"
            f"and(user_id.eq.{target_id},connected_user_id.eq.{requester_id},status.eq.connected)"
        ).execute()
        
        return len(response.data) > 0

    async def create_report(
        self,
        user_id: str,
        image_data: bytes,
        filename: str,
        report_type: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> str:
        
        # --- SEQUENTIAL VALIDATION PIPELINE ---
        
        from app.services.gemini_service import GeminiService
        from app.utils.image_processing import check_blur, enhance_image
        
        gemini = GeminiService()

        # 1. AI Medical Check
        print("[VALIDATION] Checking if image is a medical report...")
        is_medical = gemini.validate_medical_report(image_data)
        if not is_medical:
             raise ValueError("Only medical reports are accepted. Please upload a valid medical document.")

        # 2. Blur Check 1
        print("[VALIDATION] Checking for blur...")
        is_blurry = check_blur(image_data)
        
        final_image_data = image_data
        
        if is_blurry:
            print("[VALIDATION] Image is blurry. Attempting enhancement...")
            # 3. Enhance
            enhanced_data = enhance_image(image_data)
            
            # 4. Blur Check 2
            still_blurry = check_blur(enhanced_data)
            
            if still_blurry:
                # 5. Final Rejection
                 raise ValueError("Image is too blurry and could not be clarified. Please upload a clearer image.")
            
            print("[VALIDATION] Enhancement successful.")
            final_image_data = enhanced_data
        
        # --- VALIDATION PASSED ---

        # Check premium limits
        can_create, error_msg = await self.premium_service.check_report_limit(user_id)
        if not can_create:
            raise ValueError(error_msg)

        report_id = str(uuid.uuid4())
        file_path = f"{user_id}/{report_id}.png"

        # Create report DB record (RLS ENFORCED)
        report_data = {
            "id": report_id,
            "user_id": user_id,
            "type": report_type or "Unknown",
            "status": "processing",
            "flag_level": "green",
            "image_url": file_path,
            "uploaded_to_abdm": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = self.db.table("reports").insert(report_data).execute()

        if not response.data:
            raise RuntimeError("Failed to insert report record")

        # Background processing with FINAL validated image
        if background_tasks:
            background_tasks.add_task(
                self._process_report,
                report_id,
                user_id,
                final_image_data,
            )
        else:
            await self._process_report(report_id, user_id, final_image_data)

        return report_id

    async def create_report_with_data(
        self,
        user_id: str,
        image_data: bytes,
        filename: str,
        extracted_data: Dict[str, Any],
        report_type: Optional[str] = None,
    ) -> str:
        """
        Create a report with pre-extracted data (e.g. from Gemini).
        Bypasses internal OCR pipeline but still runs safety/flagging logic.
        """
        # Check premium limits
        can_create, error_msg = await self.premium_service.check_report_limit(user_id)
        if not can_create:
            raise ValueError(error_msg)

        report_id = str(uuid.uuid4())
        file_path = f"{user_id}/{report_id}.png"

        # Upload image moved to background (handled if background task handles it, or if we need to force it here for data flow?)
        # For 'create_report_with_data', it's usually synchronous in existing flow (from upload endpoint), 
        # BUT since we reverted the route to use 'create_report', this method might be unused for the main flow now.
        # However, to be safe and consistent, we'll keep it synchronous here if this method is intended for direct/blocking usage, 
        # OR better: if this method is used by the reverted route, it's NOT used. 
        # The reverted route calls `create_report` which queues `_process_report`.
        # `create_report_with_data` was for the synchronous route version.
        # So touching this might be irrelevant but let's leave it as is or comment it out to avoid confusion if called properly.
        # Actually, let's keep it sync here as it implies "I have data, just save it". 
        # But wait, the route was reverted to call `create_report`.
        # So we focus on `create_report`.
        
        # NOTE: Leaving this sync for now as it's not the main path.
        upload_to_supabase_storage(
            bucket=settings.STORAGE_BUCKET,
            path=file_path,
            file_bytes=image_data,
            content_type="image/png",
        )

        # Parse Gemini Date & Type
        parsed_type = extracted_data.get("report_type", report_type or "Unknown")
        parsed_lab = extracted_data.get("lab_name")
        parsed_date = extracted_data.get("date")

        # Create report DB record
        report_record = {
            "id": report_id,
            "user_id": user_id,
            "type": parsed_type,
            "lab_name": parsed_lab,
            "date": parsed_date,
            "status": "completed", # Data is ready immediately
            "flag_level": "green", # Will update after param calc
            "image_url": file_path,
            "uploaded_to_abdm": False,
            "progress": 100,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        self.db.table("reports").insert(report_record).execute()

        # Process Parameters
        parameters = []
        param_records = []
        
        for param in extracted_data.get("parameters", []):
            try:
                # Handle "120 mg/dL" vs "120"
                val_str = str(param.get("value", ""))
                numeric_part = ''.join(c for c in val_str if c.isdigit() or c == '.')
                value_float = float(numeric_part) if numeric_part else 0.0
            except:
                value_float = 0.0

            # Safety Service Flagging (Keep our own safety logic or trust Gemini? Trusting Gemini for now but verifying format)
            # Check if Gemini already gave a flag
            gemini_flag = param.get("flag", "normal").lower()
            if gemini_flag not in ["high", "low", "normal"]:
                gemini_flag = "normal"

            param_id = str(uuid.uuid4())
            param_record = {
                "id": param_id,
                "report_id": report_id,
                "name": param.get("name", "Unknown"),
                "value": str(param.get("value", "")),
                "unit": param.get("unit"),
                "normal_range": param.get("normal_range", ""),
                "flag": gemini_flag,
                "created_at": datetime.utcnow().isoformat(),
            }
            
            param_records.append(param_record)
            parameters.append(param_record)

        if param_records:
            self.storage_client.table("report_parameters").insert(param_records).execute()

        # Update Report Flag Level based on parameters
        overall_flag = self.safety_service.get_flag_level(parameters)
        self.db.table("reports").update({"flag_level": overall_flag}).eq("id", report_id).execute()

        # Generate Synthesis immediately if possible or background it
        # Since user wants simplified explanation, we can use Gemini summary if provided
        # or trigger the synthesis service.
        summary = extracted_data.get("summary")
        if summary:
            # We can save this summary as a synthesis directly?
            # Or just let the synthesis service run. Let's background the full synthesis for depth.
            pass
            
        print(f"[SUCCESS] Created report {report_id} from Gemini data")
        return report_id

    async def _process_report(
        self,
        report_id: str,
        user_id: str,
        image_data: bytes,
    ):
        try:
            # 0% - Uploading to Storage (Background)
            file_path = f"{user_id}/{report_id}.png"
            # Use to_thread to prevent blocking the event loop even in background
            await asyncio.to_thread(
                upload_to_supabase_storage,
                bucket=settings.STORAGE_BUCKET,
                path=file_path,
                file_bytes=image_data,
                content_type="image/png",
            )

            # 10% - Starting Analysis
            await self._update_progress(report_id, 10)
            
            # Using Gemini for authentic analysis
            from app.services.gemini_service import GeminiService
            gemini_service = GeminiService()
            
            # 30% - Sending to Gemini
            await self._update_progress(report_id, 30)
            
            extracted_data = gemini_service.analyze_medical_report(image_data)
            
            # 70% - Analysis Complete, Saving Data
            await self._update_progress(report_id, 70)

            print(f"[DEBUG] Gemini Extracted Data: {extracted_data}")

            # Safe Date Parsing
            raw_date = extracted_data.get("date")
            parsed_date = None
            if raw_date:
                try:
                    from dateutil import parser
                    # Fuzzy match to handle "02 Dec, 2X" if possible, or just fail safely
                    # If it contains ambiguous chars, parser might still fail or return weird stuff.
                    # Let's try basic parsing
                    parsed_date = parser.parse(raw_date, fuzzy=True).date().isoformat()
                except Exception:
                    print(f"[WARNING] Could not parse date: {raw_date}. Saving as None.")
                    parsed_date = None

            # Update basic report info
            self.db.table("reports").update(
                {
                    "type": extracted_data.get("report_type", "Unknown"),
                    "lab_name": extracted_data.get("lab_name"),
                    "date": parsed_date,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", report_id).execute()

            # Process Parameters & Explanations
            parameters = []
            param_records = []
            explanation_records = []
            
            for param in extracted_data.get("parameters", []):
                try:
                    val_str = str(param.get("value", ""))
                    numeric_part = ''.join(c for c in val_str if c.isdigit() or c == '.')
                    value_float = float(numeric_part) if numeric_part else 0.0
                except:
                    value_float = 0.0

                gemini_flag = param.get("flag", "normal").lower()
                if gemini_flag not in ["high", "low", "normal"]:
                    gemini_flag = "normal"

                param_id = str(uuid.uuid4())
                param_record = {
                    "id": param_id,
                    "report_id": report_id,
                    "name": param.get("name", "Unknown"),
                    "value": str(param.get("value", "")),
                    "unit": param.get("unit"),
                    "normal_range": param.get("normal_range", ""),
                    "flag": gemini_flag,
                    "created_at": datetime.utcnow().isoformat(),
                }
                
                param_records.append(param_record)
                parameters.append(param_record)
                
                # Save Explanation if provided
                explanation_text = param.get("explanation")
                if explanation_text:
                    explanation_records.append({
                        "id": str(uuid.uuid4()),
                        "parameter_id": param_id,
                        "what": param.get("name", "Test Parameter"),
                        "meaning": explanation_text,
                        "causes": [], # Gemini summary usually doesn't give structured causes list unless asked
                        "next_steps": ["Consult your doctor."],
                        "generated_at": datetime.utcnow().isoformat(),
                    })

            # Batch Insert
            if param_records:
                self.storage_client.table("report_parameters").insert(param_records).execute()
            
            if explanation_records:
                self.storage_client.table("report_explanations").insert(explanation_records).execute()
            
            # Determine overall flag
            flag_level = self.safety_service.get_flag_level(parameters) if parameters else "green"

            # 100% - Complete
            self.db.table("reports").update(
                {
                    "status": "completed",
                    "progress": 100,
                    "flag_level": flag_level,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", report_id).execute()

            print(f"[SUCCESS] Report {report_id} processed with Gemini")
            
            # Trigger Background Synthesis (Optional, if we want detailed summary beyond what extraction gave)
            await self.generate_and_cache_synthesis(report_id, user_id)

        except Exception as e:
            print(f"[ERROR] Processing failed for {report_id}: {e}")
            try:
                self.db.table("reports").update(
                    {
                        "status": "failed",
                        "error_message": str(e),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", report_id).execute()
            except Exception as db_e:
                print(f"[ERROR] Failed to update error status: {db_e}")
            raise

    async def get_report(self, report_id: str, user_id: str) -> Optional[Dict]:
        """Get report details. Checks for ownership OR family connection."""
        
        # 1. Try standard access (Own report)
        response = (
            self.db.table("reports")
            .select("*")
            .eq("id", report_id)
            .eq("user_id", user_id)
            .execute()
        )
        if response.data:
            return response.data[0]
            
        # 2. Try Shared Access (Family report)
        # Fetch report metadata using Service Role to check owner
        admin_res = self.storage_client.table("reports").select("*").eq("id", report_id).execute()
        if not admin_res.data:
            return None # Report doesnt exist at all
            
        report = admin_res.data[0]
        owner_id = report["user_id"]
        
        # Verify connection
        if await self.verify_family_access(user_id, owner_id):
            return report
            
        return None

    async def list_reports(
        self,
        user_id: str,
        search: Optional[str] = None,
        report_type: Optional[str] = None,
        flag_level: Optional[str] = None,
        time_range: str = "all",
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        query = (
            self.storage_client.table("reports")
            .select("*", count="exact")
            .eq("user_id", user_id)
        )

        if search:
            query = query.or_(f"type.ilike.%{search}%,lab_name.ilike.%{search}%")

        if report_type:
            query = query.eq("type", report_type)

        if flag_level:
            query = query.eq("flag_level", flag_level.lower())

        offset = (page - 1) * limit
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        response = query.execute()

        return {
            "items": response.data or [],
            "total": response.count or 0,
            "page": page,
            "limit": limit,
            "has_next": (response.count or 0) > offset + limit,
            "has_prev": page > 1,
        }

    async def delete_report(self, report_id: str, user_id: str) -> bool:
        # Direct delete. RLS policy ("Users can delete their own reports") ensures security.
        self.db.table("reports").delete().eq("id", report_id).execute()
        # Always return True (idempotent: if it's gone, mission accomplished)
        return True

    async def get_report_parameters(self, report_id: str, user_id: str) -> List[Dict]:
        """Get parameters for a report"""
        # Verify report ownership first
        report = await self.get_report(report_id, user_id)
        if not report:
            return []
            
        response = (
            self.storage_client.table("report_parameters")
            .select("*")
            .eq("report_id", report_id)
            .execute()
        )
        params = response.data or []
        
        # Enrich with explanations
        if params:
            param_ids = [p["id"] for p in params]
            explanations_response = (
                self.storage_client.table("report_explanations")
                .select("*")
                .in_("parameter_id", param_ids)
                .execute()
            )
            explanations = explanations_response.data or []
            explanation_map = {e["parameter_id"]: e for e in explanations}
            
            for p in params:
                p["explanation"] = explanation_map.get(p["id"])
                # Frontend might expect 'range' instead of 'normal_range'
                p["range"] = p.get("normal_range")

        return params

    async def get_report_explanations(self, report_id: str, user_id: str) -> List[Dict]:
        """Get AI explanations for a report"""
        # Verify ownership
        report = await self.get_report(report_id, user_id)
        if not report:
            return []
            
        # Get parameter IDs for this report
        params = await self.get_report_parameters(report_id, user_id)
        if not params:
            return []
            
        param_ids = [p["id"] for p in params]
        
        if not param_ids:
            return []
            
        response = (
            self.storage_client.table("report_explanations")
            .select("*")
            .in_("parameter_id", param_ids)
            .execute()
        )
        return response.data or []

    async def find_related_reports(self, report: Dict, user_id: str) -> List[Dict]:
        """Find reports related to the given report (by Type)"""
        if not report or not report.get("type"):
            return []
            
        # Find past reports of same type
        response = (
            self.db.table("reports")
            .select("*")
            .eq("user_id", user_id)
            .eq("type", report["type"])
            .neq("id", report["id"]) # Exclude current
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        
        related_reports = response.data or []
        
        # Enrich with parameters (Synthesis needs data)
        for r in related_reports:
             r["parameters"] = await self.get_report_parameters(r["id"], user_id)
             
        return related_reports

    async def get_cached_synthesis(self, report_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached synthesis from DB. NO OpenAI calls."""
        # 1. Verify Access
        report = await self.get_report(report_id, user_id)
        if not report:
            raise ValueError("Report not found")

        # 2. Get from DB
        response = (
            self.storage_client.table("report_summaries")
            .select("summary_text, status, error_message")
            .eq("report_id", report_id)
            .execute()
        )
        
        if response.data:
            row = response.data[0]
            # Structure the response
            return {
                "status": row.get("status", "completed"), # Default to completed for legacy
                "data": row.get("summary_text"),
                "error": row.get("error_message")
            }
            
        return None

    async def generate_and_cache_synthesis(self, report_id: str, user_id: str, force_regenerate: bool = False) -> bool:
        """
        Atomic synthesis generation using DB constraints.
        Guarantees: Hard Idempotency, Single Execution, No Race Conditions.
        """
        try:
            # 1. Force Regenerate: Atomic Delete checks
            if force_regenerate:
                print(f"[DEBUG] Forcing synthesis regeneration for {report_id}")
                # Delete existing row to clear the lock
                self.storage_client.table("report_summaries").delete().eq("report_id", report_id).execute()

            # 2. Acquire Lock (Atomic Insert)
            # Try to insert 'pending'. If row exists (pending/completed/failed), DB throws unique constraint error.
            # This serves as our atomic lock.
            current_time = datetime.utcnow().isoformat()
            try:
                self.storage_client.table("report_summaries").insert({
                    "report_id": report_id,
                    "status": "pending",
                    "summary_text": None,
                    "error_message": None,
                    "created_at": current_time, 
                    "updated_at": current_time
                }).execute()
            except Exception as e:
                # Lock failed -> Row already exists.
                # This is expected behavior for idempotency (job already running or done).
                print(f"[DEBUG] Synthesis lock held or done for {report_id}. Exiting. Reason: {e}")
                return True

            # --- WE HAVE THE LOCK ---
            
            try:
                # 3. Get Data
                report = await self.get_report(report_id, user_id)
                if not report:
                    self._mark_synthesis_failed(report_id, "Report not found")
                    return False
                    
                report["parameters"] = await self.get_report_parameters(report_id, user_id)
                
                # 4. Find History
                target_user_id = report["user_id"]
                related = await self.find_related_reports(report, target_user_id)
                
                # 5. Generate AI Synthesis
                print(f"[DEBUG] Generating AI synthesis for {report_id}...")
                synthesis = await self.synthesis_service.generate_synthesis(report, related)
                
                # 6. Validate AI Response
                if synthesis.get("doctor_precis") == "AI Synthesis unavailable.":
                    self._mark_synthesis_failed(report_id, "AI service unavailable")
                    return False

                # 7. Mark as COMPLETED
                self.storage_client.table("report_summaries").update({
                    "status": "completed",
                    "summary_text": synthesis,
                    "error_message": None,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("report_id", report_id).execute()
                
                print(f"[SUCCESS] Synthesis completed for {report_id}")
                return True
                
            except Exception as inner_e:
                # Catch internal logic errors and mark failed so user can retry later
                print(f"[ERROR] Logic failed during synthesis: {inner_e}")
                self._mark_synthesis_failed(report_id, str(inner_e))
                return False

        except Exception as e:
            print(f"[CRITICAL] Outer synthesis error: {e}")
            return False

    def _mark_synthesis_failed(self, report_id: str, error_message: str):
        """Helper to mark synthesis as failed"""
        try:
            self.storage_client.table("report_summaries").update({
                "status": "failed",
                "error_message": error_message,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("report_id", report_id).execute()
        except Exception as e:
            print(f"[CRITICAL] Failed to mark synthesis failure: {e}")

    async def _update_progress(self, report_id: str, progress: int):
        """Helper to safely update report progress"""
        try:
            self.db.table("reports").update({"progress": progress}).eq("id", report_id).execute()
        except Exception:
            # Ignore errors (e.g., if progress column doesn't exist yet)
            pass

    async def get_report_synthesis(self, report_id: str, user_id: str) -> Dict[str, Any]:
        """
        DEPRECATED: Use get_cached_synthesis
        Maintains backward compatibility by returning structured response
        """
        cached = await self.get_cached_synthesis(report_id, user_id)
        
        if cached:
            if cached["status"] == "completed" and cached["data"]:
                return {**cached["data"], "status": "completed"}
            elif cached["status"] == "pending":
                return {
                    "status": "pending",
                    "status_summary": "Analysis in progress...",
                    "key_trends": [],
                    "doctor_precis": "Generating your smart health synthesis..."
                }
            elif cached["status"] == "failed":
                return {
                    "status": "failed",
                    "status_summary": "Analysis failed.",
                    "key_trends": [],
                    "doctor_precis": "Could not generate synthesis. Please retry."
                }
            
        return {
            "status": "missing",
            "status_summary": "Analysis not ready.",
            "key_trends": [],
            "doctor_precis": "Smart synthesis not generated yet."
        }
