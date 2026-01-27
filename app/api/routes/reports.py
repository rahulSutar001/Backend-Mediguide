"""
Report API routes
"""
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    BackgroundTasks,
    Request,
)

from app.core.dependencies import get_user_id, require_premium
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportUploadResponse,
    ReportResponse,
    ReportListRequest,
    ReportStatusResponse,
    CompareReportsRequest,
    TestParameterResponse,
)
from typing import Optional, List
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/upload",
    response_model=ReportUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_report(
    request: Request,  # ✅ REQUIRED
    file: UploadFile = File(...),
    report_type: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    print(f"[DEBUG] Upload Endpoint Hit. Type: {report_type}, Filename: {file.filename}, Content-Type: {file.content_type}")
    if file.content_type not in [
        "image/jpeg",
        "image/png",
        "image/jpg",
        "image/webp",
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type",
        )

    image_data = await file.read()

    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 10MB)",
        )

    try:
        # Pass request to service layer to handle auth and background processing
        service = ReportService(request)
        report_id = await service.create_report(
            user_id=user_id,
            image_data=image_data,
            filename=file.filename or "report.jpg",
            report_type=report_type,
            background_tasks=background_tasks,
        )

        return ReportUploadResponse(
            report_id=report_id,
            status="processing",
            message="Report uploaded successfully",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR IN UPLOAD]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process report: {str(e)}",
        )


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(
    request: Request,
    report_id: str,
    user_id: str = Depends(get_user_id),
):
    service = ReportService(request)
    report = await service.get_report(report_id, user_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    print(f"[DEBUG] Report {report_id} status: {report.get('status')}")
    return ReportStatusResponse(
        report_id=report_id,
        status=report.get("status", "processing"),
        progress=report.get("progress"),
        error_message=report.get("error_message"),
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    request: Request,
    report_id: str,
    user_id: str = Depends(get_user_id),
):
    service = ReportService(request)
    report = await service.get_report(report_id, user_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(**report)


@router.get("", response_model=PaginatedResponse)
async def list_reports(
    request: Request,
    search: Optional[str] = None,
    report_type: Optional[str] = None,
    flag_level: Optional[str] = None,
    time_range: str = "all",
    target_user_id: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user_id: str = Depends(get_user_id),
):
    service = ReportService(request)
    
    # Handle shared access
    fetch_user_id = user_id
    if target_user_id and target_user_id != user_id:
        has_access = await service.verify_family_access(user_id, target_user_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this user's reports"
            )
        fetch_user_id = target_user_id
        
    result = await service.list_reports(
        user_id=fetch_user_id,
        search=search,
        report_type=report_type,
        flag_level=flag_level,
        time_range=time_range,
        page=page,
        limit=limit,
    )

    return PaginatedResponse(**result)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    request: Request,
    report_id: str,
    user_id: str = Depends(get_user_id),
):
    service = ReportService(request)
    deleted = await service.delete_report(report_id, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")


@router.get("/{report_id}/parameters", response_model=List[TestParameterResponse])
async def get_report_parameters(
    request: Request,
    report_id: str,
    user_id: str = Depends(get_user_id),
):
    service = ReportService(request)
    params = await service.get_report_parameters(report_id, user_id)
    return params


@router.get("/{report_id}/explanations", response_model=list)
async def get_report_explanations(
    request: Request,
    report_id: str,
    user_id: str = Depends(get_user_id),
):
    service = ReportService(request)
    explanations = await service.get_report_explanations(report_id, user_id)
    return explanations


@router.get("/{report_id}/synthesis")
async def get_report_synthesis(
    request: Request,
    report_id: str,
    user_id: str = Depends(get_user_id),
):
    """
    Get AI synthesis for a report. 
    Reads from CACHE only. No real-time AI generation.
    """
    service = ReportService(request)
    try:
        synthesis = await service.get_report_synthesis(report_id, user_id)
        return synthesis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Get synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve synthesis")


@router.post("/{report_id}/generate-synthesis")
async def generate_report_synthesis_trigger(
    report_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    user_id: str = Depends(get_user_id),
):
    """
    Trigger background generation of AI synthesis.
    Safe and idempotent.
    """
    try:
        service = ReportService(request)
        # Verify access first
        report = await service.get_report(report_id, user_id)
        if not report:
             raise HTTPException(status_code=404, detail="Report not found")

        # Run in background
        background_tasks.add_task(
            service.generate_and_cache_synthesis,
            report_id,
            user_id,
            force_regenerate=True # Force new attempt
        )
        
        return {"status": "accepted", "message": "Synthesis generation started"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Trigger synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger synthesis")
