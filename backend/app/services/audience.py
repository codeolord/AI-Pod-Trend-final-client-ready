from dataclasses import dataclass
from typing import List

KEYWORD_SEGMENTS = {
    "cat": "Cat lovers / Pet owners",
    "dog": "Dog lovers / Pet owners",
    "mom": "Moms / Parents",
    "dad": "Dads / Parents",
    "teacher": "Teachers / Educators",
    "gamer": "Gamers",
    "fitness": "Fitness / Gym enthusiasts",
    "anime": "Anime / Otaku fans",
}


@dataclass
class AudienceInsight:
    segment_name: str
    demographics: str
    interests: str
    tone: str


def infer_audience_from_text(text: str) -> List[AudienceInsight]:
    text_l = text.lower()
    insights: List[AudienceInsight] = []

    for kw, seg in KEYWORD_SEGMENTS.items():
        if kw in text_l:
            demographics = "Likely adults" if kw in {"mom", "dad", "teacher"} else "Mixed ages"
            tone = "Fun / playful" if any(x in text_l for x in ["funny", "humor", "sarcastic"]) else "Neutral"
            insights.append(
                AudienceInsight(
                    segment_name=seg,
                    demographics=demographics,
                    interests=f"Interests related to {seg}",
                    tone=tone,
                )
            )

    if not insights:
        insights.append(
            AudienceInsight(
                segment_name="General audience",
                demographics="Broad, mixed demographics",
                interests="Depends on niche and design",
                tone="Neutral",
            )
        )

    return insights
