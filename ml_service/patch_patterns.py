"""Script to patch skill provider patterns to handle plural/verb forms."""
import re

path = "app/providers/skill_provider.py"
content = open(path, encoding="utf-8").read()

# Find the patterns block and replace it
old_block_start = "# Deterministic skill patterns for the electrician trade."
old_block_end = "]"

# Use line-by-line replacement
lines = content.split("\n")

# Find line numbers for the block
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "# Deterministic skill patterns" in line:
        start_idx = i
    if start_idx is not None and i > start_idx and line.strip() == "]":
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"ERROR: could not find block. start={start_idx} end={end_idx}")
    exit(1)

print(f"Replacing lines {start_idx}..{end_idx}")

new_block = r"""# Deterministic skill patterns for the electrician trade.
# Each entry: (regex_pattern, skill_name, confidence)
# Confidence is derived from pattern specificity — not random.
# \w* at end of stems handles plurals and inflections (switches, fans, installs…)
_ELECTRICIAN_PATTERNS: list[tuple[str, str, float]] = [
    # ── Wiring ──────────────────────────────────────────────────────────────
    (r"\b(house\s+wiring|domestic\s+wiring|ghar\s+ki\s+wiring|internal\s+wiring)\b",
     "house wiring", 0.93),
    (r"\b(wiring|wire)\b", "electrical wiring", 0.82),
    (r"\b(conduit|pipe\s+mein\s+wire)\b", "conduit installation", 0.80),

    # ── Switches ─────────────────────────────────────────────────────────────
    # Compound: verb then object, or object then verb
    (r"\b(switch\s+install\w*|install\w*\s+switch\w*|switch\s+lagana|switch\s+fit)\b",
     "switch installation", 0.92),
    # Standalone: switch OR switches
    (r"\bswitch(es)?\b", "switch installation", 0.78),

    # ── Fans ─────────────────────────────────────────────────────────────────
    (r"\b(fan\s+install\w*|install\w*\s+fan\w*|ceiling\s+fan\w*|pankha\s+lagana|fan\s+fit)\b",
     "fan installation", 0.91),
    # Standalone: fan OR fans
    (r"\bfan(s)?\b", "fan installation", 0.76),

    # ── Other fixtures ────────────────────────────────────────────────────────
    (r"\b(light\s+point|light\s+install\w*|light\s+fixture\w*)\b",
     "light fixture installation", 0.85),
    (r"\b(socket\w*|outlet\w*|plug\s+point|power\s+point|point\s+lagana)\b",
     "socket outlet installation", 0.84),

    # ── Fault finding ─────────────────────────────────────────────────────────
    (r"\b(fault\s+find\w*|fault\s+diagnos\w*|fault\s+dhundh\w*|troubleshoot\w*"
     r"|fault\s+nikalna|bijli\s+ki\s+garbari)\b",
     "electrical fault diagnosis", 0.92),
    # "find faults" / "finds fault" / "finding faults"
    (r"\bfind\w*\s+fault\w*\b", "electrical fault diagnosis", 0.88),
    # Standalone: fault OR faults
    (r"\bfault(s)?\b", "electrical fault diagnosis", 0.72),

    # ── Testing / instruments ──────────────────────────────────────────────────
    (r"\b(line\s+tester|voltage\s+tester|phase\s+tester|neon\s+tester"
     r"|meter\s+se\s+fault|multimeter\s+se)\b",
     "electrical testing", 0.90),
    (r"\b(multimeter|tester\w*|test\s+instrument|megger)\b",
     "use of test instruments", 0.85),

    # ── Distribution board ─────────────────────────────────────────────────────
    (r"\b(distribution\s+board|DB\s+board|fuse\s+board|panel\s+board|MCB\s+board)\b",
     "distribution board installation", 0.88),
    (r"\b(MCB|ELCB|RCD|RCCB|circuit\s+breaker)\b",
     "circuit protection device installation", 0.82),

    # ── Earthing ───────────────────────────────────────────────────────────────
    (r"\b(earthing|grounding|earth\s+wire|earth\s+lagana|earthing\s+karna)\b",
     "earthing installation", 0.88),

    # ── Safety ─────────────────────────────────────────────────────────────────
    (r"\b(safe\s+isolation|lockout|tagout|LOTO)\b", "safe isolation", 0.92),
    (r"\b(PPE|safety\s+equipment|protective\s+equipment|safety\s+helmet|gloves)\b",
     "safety equipment use", 0.84),

    # ── Planning ───────────────────────────────────────────────────────────────
    (r"\b(electrical\s+drawing|wiring\s+diagram|circuit\s+diagram)\b",
     "reading electrical drawings", 0.87),
    (r"\b(permit|work\s+order|job\s+card)\b", "work permit and planning", 0.80),
]"""

new_lines = lines[:start_idx] + new_block.split("\n") + lines[end_idx + 1:]
open(path, "w", encoding="utf-8").write("\n".join(new_lines))
print("Patched successfully.")
print(f"New file has {len(new_lines)} lines.")
