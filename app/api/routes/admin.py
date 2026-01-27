from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from typing import List, Dict, Any, Optional
from app.core.security import get_current_user, get_admin_user, get_service_supabase_client
from app.services.report_service import ReportService
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_user), Depends(get_admin_user)]
)

@router.get("/users", response_model=List[Dict[str, Any]])
async def list_registered_users(
    admin_user: dict = Depends(get_admin_user)
):
    """
    List all registered users from auth and profiles.
    Requires Admin privileges.
    """
    print("[ADMIN DEBUG] Entering list_registered_users...")
    try:
        supabase = get_service_supabase_client()
        
        # 1. Fetch Profiles
        profiles_res = supabase.table("profiles").select("*").execute()
        profiles_list = profiles_res.data or []
        profiles = {p["id"]: p for p in profiles_list if "id" in p}
        print(f"[ADMIN DEBUG] Found {len(profiles)} profiles in DB")
        
        # 2. Fetch Auth Users
        auth_users = []
        try:
            auth_users_res = supabase.auth.admin.list_users()
            # Handle different response formats
            if isinstance(auth_users_res, list):
                auth_users = auth_users_res
            elif hasattr(auth_users_res, "users"):
                auth_users = auth_users_res.users
            elif isinstance(auth_users_res, dict) and "users" in auth_users_res:
                auth_users = auth_users_res["users"]
        except Exception as auth_err:
            print(f"[ADMIN WARNING] Auth fetch failed: {auth_err}")

        print(f"[ADMIN DEBUG] Found {len(auth_users)} auth users")

        # 3. Combine Data
        combined_users = []
        
        if auth_users:
            for u in auth_users:
                # Handle both object and dict
                u_id = getattr(u, "id", None) or (u.get("id") if isinstance(u, dict) else None)
                u_email = getattr(u, "email", "No Email") or (u.get("email") if isinstance(u, dict) else "No Email")
                u_created = getattr(u, "created_at", None) or (u.get("created_at") if isinstance(u, dict) else None)
                u_confirmed = getattr(u, "email_confirmed_at", None) or (u.get("email_confirmed_at") if isinstance(u, dict) else None)
                
                if not u_id: continue
                
                profile = profiles.get(u_id, {})
                combined_users.append({
                    "id": u_id,
                    "email": u_email,
                    "full_name": profile.get("full_name"),
                    "phone_number": profile.get("phone_number"),
                    "created_at": str(u_created) if u_created else None,
                    "status": "active" if u_confirmed else "pending"
                })
        
        # 4. Fallback if combined list is empty but profiles exist
        if not combined_users and profiles:
            print("[ADMIN DEBUG] Combined list empty, using profiles fallback")
            for p_id, p in profiles.items():
                combined_users.append({
                    "id": p_id,
                    "email": "Unknown (Auth match failed)",
                    "full_name": p.get("full_name"),
                    "phone_number": p.get("phone_number"),
                    "created_at": p.get("created_at"),
                    "status": "profile_only"
                })
            
        print(f"[ADMIN DEBUG] Final user count: {len(combined_users)}")
        return combined_users
        
    except Exception as e:
        print(f"[ADMIN ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Admin list error: {str(e)}"
        )

@router.post("/users/{target_user_id}/reports/upload")
async def upload_report_as_admin(
    target_user_id: str,
    request: Request,
    file: UploadFile = File(...),
    report_type: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    admin_user: dict = Depends(get_admin_user)
):
    """Upload a report on behalf of a user"""
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    image_data = await file.read()
    try:
        service = ReportService(request)
        report_id = await service.create_report(
            user_id=target_user_id,
            image_data=image_data,
            filename=file.filename or "report.jpg",
            report_type=report_type,
            background_tasks=background_tasks,
        )
        return {"report_id": report_id, "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all-reports")
async def list_all_reports_as_admin(
    admin_user: dict = Depends(get_admin_user),
    limit: int = 50
):
    supabase = get_service_supabase_client()
    res = supabase.table("reports").select("*").order("created_at", desc=True).limit(limit).execute()
    return res.data or []

@router.get("/users/{target_user_id}/reports")
async def list_user_reports_as_admin(target_user_id: str, admin_user: dict = Depends(get_admin_user)):
    supabase = get_service_supabase_client()
    res = supabase.table("reports").select("*").eq("user_id", target_user_id).execute()
    return res.data or []

@router.delete("/reports/{report_id}")
async def delete_report_as_admin(report_id: str, admin_user: dict = Depends(get_admin_user)):
    supabase = get_service_supabase_client()
    supabase.table("report_parameters").delete().eq("report_id", report_id).execute()
    supabase.table("reports").delete().eq("id", report_id).execute()
    return {"status": "deleted"}
