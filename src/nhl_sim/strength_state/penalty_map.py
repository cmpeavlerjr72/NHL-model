"""Explicit pen_type / pen_desc / pen_minutes -> SS-R1 target class mapping. Unknown combinations raise (L13).

Classes of a single penalty event:
  minor        2 min with a strength effect (MIN 2, BEN 2; bench minors are served by a skater)
  double       double minor (MIN 4, BEN 4)
  major        5 min with a strength effect, never ended by a goal (MAJ 5, MAT 5, MAT 10: the API's
               "match-penatly-10-minutes" behaves as a 5-minute strength penalty in pbp situation codes)
  misconduct   no strength effect (MIS 10); tallied, not a target
  game_misc    no strength effect (GAM 0/10); tallied, not a target
  ps           penalty shot awarded (PS 0); no box time; tallied, not a target

Per-stoppage resolution into penalty-taking events (target) lives in `nhl_sim.strength_state.events`.
"""
from __future__ import annotations

STRENGTH_CLASSES = ("minor", "double", "major")
NON_TARGET = ("misconduct", "game_misc", "ps")

# (pen_type, pen_minutes) -> class
TYPE_MINUTES = {
    ("MIN", 2.0): "minor", ("BEN", 2.0): "minor",
    ("MIN", 4.0): "double", ("BEN", 4.0): "double",
    ("MAJ", 5.0): "major", ("MAT", 5.0): "major", ("MAT", 10.0): "major",
    ("MIS", 10.0): "misconduct",
    ("GAM", 0.0): "game_misc", ("GAM", 10.0): "game_misc",
    ("PS", 0.0): "ps",
}

# every (pen_type, pen_desc) seen in 2021-22 .. 2024-25 and 2026-27 (2025-26 sealed, unread); a new one fails
KNOWN_DESC = {
    "BEN": {"abuse-of-officials", "bench", "delaying-game-bench", "delaying-game-bench-face-off-violation",
            "delaying-game-unsuccessful-challenge", "ineligible-player", "interference-bench",
            "too-many-men-on-the-ice", "unsportsmanlike-conduct-bench",
            "delaying-game-unsuccessful-challenge-double-minor"},
    "GAM": {"game-misconduct-head-coach", "abuse-of-officials", "abusive-language", "aggressor", "game-misconduct"},
    "MAJ": {"boarding", "charging", "checking-from-behind", "cross-checking", "elbowing", "fighting",
            "interference", "kneeing", "slashing", "spearing"},
    "MAT": {"match-penalty", "match-penatly-10-minutes"},
    "MIN": {"abuse-of-officials", "boarding", "broken-stick", "charging", "clipping", "closing-hand-on-puck",
            "cross-checking", "delaying-game", "delaying-game-equipment", "delaying-game-face-off-violation",
            "delaying-game-illegal-play-by-goalie", "delaying-game-puck-over-glass", "delaying-game-smothering-puck",
            "elbowing", "embellishment", "goalie-leave-crease", "goalie-participation-beyond-center",
            "goalie-removed-own-mask", "high-sticking", "holding", "holding-the-stick", "hooking",
            "illegal-check-to-head", "illegal-stick", "instigator", "interference", "interference-goalkeeper",
            "kneeing", "playing-without-a-helmet", "puck-thrown-forward-goalkeeper", "roughing",
            "roughing-removing-opponents-helmet", "slashing", "throwing-equipment", "tripping",
            "unsportsmanlike-conduct", "butt-ending-double-minor", "high-sticking-double-minor",
            "spearing-double-minor"},
    "MIS": {"abusive-language", "instigator-misconduct", "misconduct"},
    "PS": {"ps-covering-puck-in-crease", "ps-goalkeeper-displaced-net", "ps-holding-on-breakaway",
           "ps-holding-stick-on-breakaway", "ps-hooking-on-breakaway", "ps-net-displaced", "ps-slash-on-breakaway",
           "ps-throwing-object-at-puck", "ps-tripping-on-breakaway"},
}


class UnmappedPenalty(KeyError):
    pass


def classify(pen_type, pen_desc, pen_minutes) -> str:
    try:
        cls = TYPE_MINUTES[(pen_type, float(pen_minutes))]
    except (KeyError, TypeError, ValueError):
        raise UnmappedPenalty(f"unmapped penalty type/minutes: {pen_type!r} {pen_minutes!r} ({pen_desc!r})") from None
    if pen_desc not in KNOWN_DESC.get(pen_type, ()):
        raise UnmappedPenalty(f"unmapped penalty type/desc: {pen_type!r} {pen_desc!r}")
    return cls


def classify_frame(df):
    """Vector form over a frame with pen_type, pen_desc, pen_minutes; raises on the first unmapped row."""
    combos = df[["pen_type", "pen_desc", "pen_minutes"]].drop_duplicates()
    lut = {(r.pen_type, r.pen_desc, r.pen_minutes): classify(r.pen_type, r.pen_desc, r.pen_minutes)
           for r in combos.itertuples()}
    return [lut[k] for k in zip(df.pen_type, df.pen_desc, df.pen_minutes)]
