from .context import UserContext

def apply_context_boost(genres: list[str], ctx: UserContext) -> float:
    g = set([x.lower() for x in genres])
    boost = 0.0

    # Weekend → Action boost
    if ctx.is_weekend and "action" in g:
        boost += 0.08

    # Group viewing → Comedy boost
    if ctx.viewing_mode == "group" and "comedy" in g:
        boost += 0.1

    # Late night → Horror boost
    if ctx.hour >= 22 and "horror" in g:
        boost += 0.05

    return boost