import logging
from uuid import UUID

from domain.models.core import ComparisonRun
from fastapi import APIRouter, Depends, HTTPException, status
from orchestration.state_machine import StateMachine, StoreState
from sqlmodel import Session

from apps.api.core import ADAPTER_MAP, broadcast_run_event, get_session
from apps.api.schemas import ResumeStoreRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Retailer Sessions & Challenges"])


@router.get("/retailer-sessions")
async def list_retailer_sessions():
    sessions_status = []
    for ret_id, adapter_cls in ADAPTER_MAP.items():
        adapter = adapter_cls()
        is_auth, msg = await adapter.check_session()
        sessions_status.append(
            {
                "retailer_id": ret_id,
                "is_authenticated": is_auth,
                "status_detail": msg or ("Authenticated" if is_auth else "Session not found or expired"),
            }
        )
    return {"sessions": sessions_status}


@router.post("/retailer-sessions/{retailer_id}/open")
async def open_retailer_session(retailer_id: str):
    if retailer_id not in ADAPTER_MAP:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retailer not supported")
    return {
        "retailer_id": retailer_id,
        "action": "LAUNCH_HEADED_LOGIN",
        "message": f"Please complete login in the opened {retailer_id.capitalize()} browser window.",
    }


@router.post("/comparison-runs/{run_id}/retailers/{retailer_id}/resume")
async def resume_retailer_run(
    run_id: UUID,
    retailer_id: str,
    resume_req: ResumeStoreRequest,
    session: Session = Depends(get_session),
):
    run = session.get(ComparisonRun, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison run not found")

    if not resume_req.resume_token or not resume_req.resume_token.startswith("tok_"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid resume token")

    sm = StateMachine(retailer_id=retailer_id)
    evt = sm.transition(StoreState.INITIALIZING, detail="Resuming workflow after user resolution")
    broadcast_run_event(str(run_id), evt, session=session)

    return {
        "run_id": run_id,
        "retailer_id": retailer_id,
        "status": "RESUMED",
        "message": f"Retailer {retailer_id} workflow resumed successfully.",
    }
