import re
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import get_settings


class PDFService:
    def __init__(self) -> None:
        self.settings = get_settings()
        Path(self.settings.pdf_output_dir).mkdir(parents=True, exist_ok=True)

    def generate_trip_pdf(self, state: dict[str, Any]) -> dict[str, Any]:
        prefs = state["trip_preferences"]
        slug = re.sub(r"[^a-z0-9]+", "-", str(prefs.get("destination", "trip")).lower()).strip("-")
        filename = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        path = Path(self.settings.pdf_output_dir) / filename
        doc = SimpleDocTemplate(str(path), pagesize=A4, title=f"{prefs.get('destination')} Trip Plan")
        styles = getSampleStyleSheet()
        story: list[Any] = []

        story += [
            Paragraph(f"{prefs.get('destination')} Trip Plan", styles["Title"]),
            Spacer(1, 24),
            Paragraph(f"From {prefs.get('source')} | {prefs.get('start_date')} to {prefs.get('end_date')}", styles["Heading2"]),
            Paragraph(f"Budget: {prefs.get('currency')} {prefs.get('budget')} | Travellers: {prefs.get('travellers')}", styles["Normal"]),
            PageBreak(),
        ]
        self._section(story, styles, "Trip Summary", [
            f"Preferences: {', '.join(prefs.get('preferences', [])) or 'Balanced sightseeing'}",
            f"Weather: {state['weather_data'].get('summary', 'Not available')}",
            f"Review status: {'Approved' if state['review_status'].get('approved') else 'Needs review'}",
        ])
        self._section(story, styles, "Transport Details", [
            state["transport_data"].get("summary", "Transport details unavailable."),
            f"Mode: {state['transport_data'].get('mode', 'mixed')}",
            f"Estimated cost: {prefs.get('currency')} {state['transport_data'].get('estimated_cost', 'N/A')}",
        ])
        hotel = state["hotel_data"].get("selected", {})
        self._section(story, styles, "Hotel Details", [
            f"Selected: {hotel.get('name', 'To be confirmed')}",
            f"Nightly price: {prefs.get('currency')} {hotel.get('price_per_night', 'N/A')}",
            f"Rating: {hotel.get('rating', 'N/A')}",
        ])
        story.append(Paragraph("Day-wise Itinerary", styles["Heading1"]))
        for day in state["itinerary"].get("days", []):
            story.append(Paragraph(f"Day {day.get('day')} - {day.get('date')}", styles["Heading3"]))
            for key in ["morning", "afternoon", "evening"]:
                story.append(Paragraph(f"<b>{key.title()}:</b> {day.get(key, '')}", styles["Normal"]))
            story.append(Spacer(1, 8))
        story.append(PageBreak())
        budget = state["budget_summary"]
        table_data = [["Category", "Amount"], *[[k.title(), str(v)] for k, v in budget.items() if k not in {"currency"}]]
        table = Table(table_data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(Paragraph("Budget Breakdown", styles["Heading1"]))
        story.append(table)
        story.append(Spacer(1, 18))
        self._section(story, styles, "Packing Checklist", state["itinerary"].get("packing_checklist", []))
        self._section(story, styles, "Emergency Contacts", state["itinerary"].get("emergency_contacts", []))
        doc.build(story)
        return {"generated": True, "filename": filename, "path": str(path), "url": f"/pdfs/{filename}"}

    def _section(self, story: list[Any], styles: Any, title: str, lines: list[Any]) -> None:
        story.append(Paragraph(title, styles["Heading1"]))
        for line in lines:
            story.append(Paragraph(str(line), styles["Normal"]))
            story.append(Spacer(1, 5))
        story.append(Spacer(1, 10))
