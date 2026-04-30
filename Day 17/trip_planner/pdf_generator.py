"""ReportLab PDF generator for the trip report."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_trip_pdf(state: Dict[str, Any]) -> Path:
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    prefs = state["trip_preferences"]
    filename = f"{prefs['destination'].replace(' ', '_').lower()}_trip_plan.pdf"
    path = reports_dir / filename

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]
    small_style = ParagraphStyle("Small", parent=body_style, fontSize=9, leading=12, textColor=colors.HexColor("#4f5b6d"))

    story = [
        Paragraph("AI Trip Planner Report", title_style),
        Paragraph(f"{prefs['days']}-Day {prefs['destination']} Trip from {prefs['source']}", heading_style),
        Paragraph(
            f"Travelers: {prefs['travelers']} ({prefs['travel_type']}) | Budget: Rs. {prefs['budget']} | "
            f"Preference: {prefs['style']}",
            body_style,
        ),
        Spacer(1, 0.35 * cm),
        _table(
            [
                ["Agent", "Source"],
                ["Transport", state["transport_data"].get("source", "unknown")],
                ["Weather", state["weather_data"].get("source", "unknown")],
                ["Hotels", state["hotel_data"]["selected"].get("source", "unknown")],
                ["Places", state["places_data"].get("source", "unknown")],
                ["Budget", state["budget_summary"].get("source", "Python calculator")],
                ["Itinerary", state["itinerary"].get("source", "Python fallback")],
                ["Review", state["review_status"].get("source", "Python rules")],
                ["PDF", "ReportLab"],
            ]
        ),
        Spacer(1, 0.45 * cm),
        Paragraph("Flights / Transfers", heading_style),
        Paragraph(_transport_text(state), body_style),
        Spacer(1, 0.25 * cm),
        Paragraph("Hotel Details", heading_style),
        Paragraph(_hotel_text(state), body_style),
        Spacer(1, 0.25 * cm),
        Paragraph("Day-wise Itinerary", heading_style),
    ]

    for day in state["itinerary"].get("days", []):
        story.extend(
            [
                Paragraph(f"Day {day['day']}", styles["Heading3"]),
                Paragraph(f"<b>Morning:</b> {day['morning']}", body_style),
                Paragraph(f"<b>Afternoon:</b> {day['afternoon']}", body_style),
                Paragraph(f"<b>Evening:</b> {day['evening']}", body_style),
                Paragraph(f"<i>{day['tip']}</i>", small_style),
                Spacer(1, 0.18 * cm),
            ]
        )

    budget = state["budget_summary"]
    story.extend(
        [
            Spacer(1, 0.2 * cm),
            Paragraph("Budget Report", heading_style),
            _table(
                [
                    ["Item", "Cost"],
                    ["Transport", f"Rs. {budget['transport']}"],
                    ["Hotel", f"Rs. {budget['hotel']}"],
                    ["Food", f"Rs. {budget['food']}"],
                    ["Local transfers", f"Rs. {budget['local_transfers']}"],
                    ["Activities", f"Rs. {budget['activities']}"],
                    ["Buffer", f"Rs. {budget['buffer']}"],
                    ["Estimated total", f"Rs. {budget['estimated_total']}"],
                    ["Status", budget["status"]],
                ]
            ),
            Paragraph(budget["optimization_tip"], body_style),
            Spacer(1, 0.3 * cm),
            Paragraph("Packing Checklist", heading_style),
            Paragraph(", ".join(state["itinerary"].get("packing_checklist", [])), body_style),
            Spacer(1, 0.2 * cm),
            Paragraph("Emergency Contacts", heading_style),
            Paragraph(", ".join(state["itinerary"].get("emergency_contacts", [])), body_style),
            Spacer(1, 0.2 * cm),
            Paragraph("Attractions", heading_style),
            Paragraph(", ".join(state["places_data"].get("attractions", [])), body_style),
        ]
    )

    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=1.4 * cm, leftMargin=1.4 * cm, topMargin=1.2 * cm, bottomMargin=1.2 * cm)
    doc.build(story)
    return path


def _table(rows):
    table = Table(rows, hAlign="LEFT", colWidths=[5 * cm, 10 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176b87")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7dee8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _transport_text(state: Dict[str, Any]) -> str:
    transport = state["transport_data"]["recommended"]
    return f"{transport['mode']} - {transport['summary']} Estimated cost: Rs. {transport['cost']}."


def _hotel_text(state: Dict[str, Any]) -> str:
    hotel = state["hotel_data"]["selected"]
    return (
        f"{hotel['name']} | {hotel['category']} | {hotel['nights']} nights | "
        f"Estimated cost: Rs. {hotel['total_cost']} | Source: {hotel.get('source', 'unknown')}."
    )
