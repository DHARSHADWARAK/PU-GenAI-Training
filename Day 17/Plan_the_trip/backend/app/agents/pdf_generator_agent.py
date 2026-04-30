from typing import Any

from app.observability.langsmith import traceable
from app.services.pdf_service import PDFService
from app.state_schema import TripPlannerState

pdf_service = PDFService()


@traceable(name="PDF Generator Agent", run_type="tool")
async def pdf_generator_agent(state: TripPlannerState) -> dict[str, Any]:
    pdf_status = pdf_service.generate_trip_pdf(state)
    return {"pdf_status": pdf_status}
