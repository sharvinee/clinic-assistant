from typing import Any, cast

from langgraph.types import interrupt
from pydantic import BaseModel, Field


class ApprovalResponse(BaseModel):
    """The normal approval form shown before clinic data changes."""

    approved: bool = Field(description="Approve this clinic data change.")
    note: str | None = Field(default=None, description="Optional reviewer note.")


def request_approval(action: str, details: dict[str, Any]) -> ApprovalResponse:
    """Pause and return the validated response from the Studio form."""
    response = interrupt(
        {"question": f"Approve {action}?", "details": details},
        response_schema=ApprovalResponse,
    )
    return cast(ApprovalResponse, response)
