from manimator.contracts.intent import ConceptType, IntentResult, Modality

async def classify_intent(raw_query: str) -> IntentResult:
    return IntentResult(
        in_scope=True, 
        raw_query=raw_query,
        concept_type=ConceptType.MATH,
        modality=Modality.THREE_D,
        complexity=3,
        confidence=0.95,
    )

