import json
import logging
import math
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        if self.settings.openai_api_key:
            try:
                from langchain_openai import ChatOpenAI

                self._client = ChatOpenAI(model=self.settings.openai_model, temperature=0.4)
            except Exception as exc:
                logger.warning("OpenAI client unavailable, using deterministic itinerary fallback: %s", exc)

    async def generate_itinerary(self, context: dict[str, Any]) -> dict[str, Any]:
        if self._client:
            prompt = self._build_itinerary_prompt(context)
            try:
                response = await self._client.ainvoke(prompt)
                content = str(response.content).strip().removeprefix("```json").removesuffix("```").strip()
                itinerary = json.loads(content)
                if self._is_valid_itinerary(itinerary, context):
                    return itinerary
                logger.warning("LLM itinerary failed validation, using deterministic planner")
            except Exception as exc:
                logger.warning("LLM itinerary generation failed, using fallback: %s", exc)
        return self._fallback_itinerary(context)

    def _build_itinerary_prompt(self, context: dict[str, Any]) -> str:
        return (
            "You are a senior travel planner. Build a realistic, non-repetitive itinerary from the provided structured data.\n\n"
            "Hard rules:\n"
            "1. Do not repeat the same place across multiple days. Each place may appear at most once.\n"
            "2. Spread places evenly across all dates. Each day must contain 2-3 unique places maximum.\n"
            "3. Every day must follow this structure: Morning = 1 main attraction; Afternoon = 1-2 nearby attractions; "
            "Evening = relaxation, food, or local experience near the final afternoon stop.\n"
            "4. Assume each day starts from the selected hotel. Group nearby places together using latitude/longitude. "
            "Do not randomly assign distant places to the same day.\n"
            "5. Prioritize landmarks, museums, major sights, and user preferences before lower-value places.\n"
            "6. If weather_data.risk is bad, prioritize indoor places such as museums. If weather is good, include outdoor landmarks.\n"
            "7. Use actual place names from places_data. Avoid generic phrases like 'explore area' or 'local highlight'.\n"
            "8. If places are limited, reuse only as a last resort and keep repetition as low as possible.\n\n"
            "Return JSON only with keys: title, days, formatted_itinerary, packing_checklist, emergency_contacts, notes.\n"
            "Each item in days must have keys: day, date, morning, afternoon, evening, places.\n"
            "The formatted_itinerary string must follow exactly this format for each day, separated by a blank line:\n"
            "Day X - YYYY-MM-DD\n"
            "Morning: ...\n"
            "Afternoon: ...\n"
            "Evening: ...\n\n"
            f"Context:\n{json.dumps(context, default=str)}"
        )

    def _fallback_itinerary(self, context: dict[str, Any]) -> dict[str, Any]:
        prefs = context.get("trip_preferences", {})
        destination = prefs.get("destination", "Destination")
        dates = prefs.get("date_list", [])
        places = self._prepare_places(context.get("places_data", {}).get("places", []), context.get("weather_data", {}))
        hotel = context.get("hotel_data", {}).get("selected", {})
        grouped_places = self._group_places_by_day(places, len(dates or ["Day 1", "Day 2", "Day 3"]), hotel)
        days = []
        for idx, day in enumerate(dates or ["Day 1", "Day 2", "Day 3"]):
            day_places = grouped_places[idx] if idx < len(grouped_places) else []
            if not day_places:
                day_places = self._last_resort_places(places, destination, idx)
            morning_place = day_places[0]
            afternoon_places = day_places[1:3]
            afternoon_names = [place["name"] for place in afternoon_places]
            evening_anchor = afternoon_names[-1] if afternoon_names else hotel.get("name", "the hotel")
            days.append(
                {
                    "day": idx + 1,
                    "date": str(day),
                    "morning": f"Start from {hotel.get('name', 'the hotel')} and visit {morning_place['name']}.",
                    "afternoon": self._afternoon_plan(afternoon_names),
                    "evening": f"Relax over dinner near {evening_anchor}.",
                    "places": [place["name"] for place in day_places],
                    "estimated_cost": 2500,
                }
            )
        formatted_itinerary = self._format_itinerary(days)
        return {
            "title": f"{destination} Trip Plan",
            "days": days,
            "formatted_itinerary": formatted_itinerary,
            "packing_checklist": ["ID documents", "Phone charger", "Weather-appropriate clothes", "Medicines", "Comfortable shoes"],
            "emergency_contacts": ["Local emergency number", "Hotel front desk", "Nearest hospital", "Travel insurance helpline"],
            "notes": "Bookings and weather should be rechecked 24 hours before departure.",
        }

    def _prepare_places(self, places: list[dict[str, Any]], weather_data: dict[str, Any]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        clean_places = []
        weather_risk = weather_data.get("risk", "unknown")
        for place in places:
            name = str(place.get("name") or "").strip()
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            clean_place = {
                "name": name,
                "address": place.get("address") or "",
                "lat": place.get("lat"),
                "lon": place.get("lon"),
                "score": self._place_score(place, weather_risk),
            }
            clean_places.append(clean_place)
        return sorted(clean_places, key=lambda item: item["score"], reverse=True)

    def _place_score(self, place: dict[str, Any], weather_risk: str) -> int:
        text = " ".join(str(place.get(key, "")) for key in ["name", "category", "address"]).lower()
        score = 10
        if any(word in text for word in ["tower", "palace", "fort", "cathedral", "temple", "monument", "landmark"]):
            score += 30
        if any(word in text for word in ["museum", "gallery", "heritage"]):
            score += 26
        if any(word in text for word in ["garden", "park", "viewpoint", "beach", "sight"]):
            score += 18
        if any(word in text for word in ["restaurant", "shop", "mall", "market"]):
            score -= 18
        if weather_risk == "bad" and any(word in text for word in ["museum", "gallery", "palace"]):
            score += 22
        if weather_risk == "good" and any(word in text for word in ["tower", "garden", "park", "viewpoint", "beach"]):
            score += 12
        return score

    def _group_places_by_day(self, places: list[dict[str, Any]], day_count: int, hotel: dict[str, Any]) -> list[list[dict[str, Any]]]:
        groups: list[list[dict[str, Any]]] = [[] for _ in range(day_count)]
        unused = places[: day_count * 3]
        for day_index in range(day_count):
            if not unused:
                break
            seed_index = self._best_seed_index(unused, hotel) if day_index == 0 else 0
            seed = unused.pop(seed_index)
            group = [seed]
            while unused and len(group) < 3 and self._target_group_size(len(places), day_count, day_index) > len(group):
                nearest_index = self._nearest_place_index(group[-1], unused)
                group.append(unused.pop(nearest_index))
            groups[day_index] = group
        return groups

    def _best_seed_index(self, candidates: list[dict[str, Any]], hotel: dict[str, Any]) -> int:
        hotel_origin = {"lat": hotel.get("lat"), "lon": hotel.get("lon")}
        if hotel_origin["lat"] is None or hotel_origin["lon"] is None:
            return 0
        ranked = []
        for index, place in enumerate(candidates):
            distance_penalty = min(self._distance_km(hotel_origin, place), 25)
            ranked.append((place.get("score", 0) - distance_penalty, index))
        return max(ranked, key=lambda item: item[0])[1]

    def _target_group_size(self, place_count: int, day_count: int, day_index: int) -> int:
        if place_count <= day_count:
            return 1
        base = min(3, max(2, math.ceil(place_count / max(day_count, 1))))
        remaining_places = min(place_count, day_count * 3) - day_index * base
        remaining_days = max(day_count - day_index, 1)
        return min(3, max(1, math.ceil(remaining_places / remaining_days)))

    def _nearest_place_index(self, origin: dict[str, Any], candidates: list[dict[str, Any]]) -> int:
        distances = [self._distance_km(origin, candidate) for candidate in candidates]
        return min(range(len(candidates)), key=lambda index: distances[index])

    def _distance_km(self, first: dict[str, Any], second: dict[str, Any]) -> float:
        lat1, lon1 = first.get("lat"), first.get("lon")
        lat2, lon2 = second.get("lat"), second.get("lon")
        if None in (lat1, lon1, lat2, lon2):
            return 9999.0
        radius = 6371.0
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))
        haversine = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        return radius * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))

    def _last_resort_places(self, places: list[dict[str, Any]], destination: str, day_index: int) -> list[dict[str, Any]]:
        if places:
            return [places[day_index % len(places)]]
        return [{"name": f"{destination} main attraction", "lat": None, "lon": None, "address": "", "score": 1}]

    def _join_names(self, names: list[str]) -> str:
        if not names:
            return "the selected attraction"
        if len(names) == 1:
            return names[0]
        return f"{', '.join(names[:-1])} and {names[-1]}"

    def _afternoon_plan(self, names: list[str]) -> str:
        if not names:
            return "No additional unique attraction available; return to the hotel for rest."
        return f"Visit {self._join_names(names)}."

    def _format_itinerary(self, days: list[dict[str, Any]]) -> str:
        blocks = []
        for day in days:
            blocks.append(
                "\n".join(
                    [
                        f"Day {day.get('day')} - {day.get('date')}",
                        f"Morning: {day.get('morning', '')}",
                        f"Afternoon: {day.get('afternoon', '')}",
                        f"Evening: {day.get('evening', '')}",
                    ]
                )
            )
        return "\n\n".join(blocks)

    def _is_valid_itinerary(self, itinerary: dict[str, Any], context: dict[str, Any]) -> bool:
        days = itinerary.get("days")
        if not isinstance(days, list) or not days:
            return False
        seen_places: set[str] = set()
        available_names = {
            str(place.get("name", "")).casefold()
            for place in context.get("places_data", {}).get("places", [])
            if place.get("name")
        }
        for day in days:
            if not all(day.get(key) for key in ["date", "morning", "afternoon", "evening"]):
                return False
            day_places = day.get("places") or []
            if len(day_places) > 3:
                return False
            for place_name in day_places:
                normalized = str(place_name).casefold()
                if normalized in seen_places and len(available_names) >= len(days):
                    return False
                if available_names and normalized not in available_names:
                    return False
                seen_places.add(normalized)
        if "formatted_itinerary" not in itinerary:
            itinerary["formatted_itinerary"] = self._format_itinerary(days)
        return True
