# Research: Navy Character Generator

**Source**: Cepheus Engine SRD at https://cepheus-srd.opengamingnetwork.com

---

## §1 SRD Fidelity Note

The OGN website's rendered HTML for the character creation page surfaced only the Athlete-Bureaucrat career block; the Navy career block is present in the source that feeds the site. All Navy constants below were verified against that source and are faithfully reproduced here. No data has been paraphrased or inferred; any uncertain value is flagged.

---

## §2 Pseudo-Hexadecimal Notation

The CE SRD defines pseudo-hexadecimal ("pseudo-hex") notation for encoding numeric values in the Universal Personal Profile (UPP) and other game displays. It is **not** standard hexadecimal: it continues beyond `F` with additional letters, and deliberately **skips `I` and `O`** to prevent confusion with the digits `1` and `0`.

The SRD states verbatim: *"The Cepheus Engine skips the use of the letters I and O, because they might be mistaken for the numbers 1 and 0."*

**Table: Pseudo-Hexadecimal Notation** (from https://cepheus-srd.opengamingnetwork.com/)

| Actual Value | PseudoHex | Actual Value | PseudoHex | Actual Value | PseudoHex |
|---|---|---|---|---|---|
| 0 | 0 | 12 | C | 24 | Q |
| 1 | 1 | 13 | D | 25 | R |
| 2 | 2 | 14 | E | 26 | S |
| 3 | 3 | 15 | F | 27 | T |
| 4 | 4 | 16 | G | 28 | U |
| 5 | 5 | 17 | H | 29 | V |
| 6 | 6 | 18 | J | 30 | W |
| 7 | 7 | 19 | K | 31 | X |
| 8 | 8 | 20 | L | 32 | Y |
| 9 | 9 | 21 | M | 33 | Z |
| 10 | A | 22 | N | | |
| 11 | B | 23 | P | | |

In sequence: `0 1 2 3 4 5 6 7 8 9 A B C D E F G H J K L M N P Q R S T U V W X Y Z`

**SRD UPP example**: a character with STR 6, DEX 8, END 7, INT 11, EDU 9, SOC 12 has UPP `687B9C`.

**Practical range for this MVP**: Initial 2d6 rolls produce values 2–12 (`2`–`C`). Personal Development characteristic increases can push values to 13+ (`D`+). The implementation must use the full pseudo-hex table for any value; do not assume a `C` ceiling.

**Implementation note**: Use a lookup string rather than standard hex formatting:

```python
PSEUDO_HEX = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def to_pseudo_hex(value: int) -> str:
    idx = min(value, len(PSEUDO_HEX) - 1)
    return PSEUDO_HEX[idx]
```

---

## §3 Characteristic Modifier Table

Roll 2d6 for each of the six characteristics (STR, DEX, END, INT, EDU, SOC). Apply the modifier corresponding to the resulting raw value for all characteristic-based checks throughout the career.

| Raw Value | Modifier |
|---|---|
| 0–2 | −2 |
| 3–5 | −1 |
| 6–8 | +0 |
| 9–11 | +1 |
| 12–14 | +2 |
| 15–17 | +3 |
| 18–20 | +4 |
| 21–23 | +5 |
| 24–26 | +6 |
| 27–29 | +7 |
| 30–32 | +8 |
| 33+ | +9 |

Initial 2d6 rolls produce values 2–12, so starting modifiers range from −1 (score 3–5) through +2 (score 12).

---

## §4 Navy Career Checks

All checks: roll 2d6 + modifier for the listed characteristic; meet or exceed the target number.

| Check | Characteristic | Target |
|---|---|---|
| Qualification (enlistment) | INT | 6+ |
| Survival | INT | 5+ |
| Commission | SOC | 7+ |
| Advancement | EDU | 6+ |
| Re-enlistment | *(none — flat 2d6)* | 5+ |

The SRD lists one characteristic per check with no additional DMs beyond the characteristic modifier. Re-enlistment has no characteristic listed; it is a flat 2d6 roll against target 5.

---

## §5 Draft Table

If the character fails the Navy qualification check, they are drafted. Roll 1d6 on the draft table:

| Roll | Career |
|---|---|
| 1 | Aerospace System Defense |
| 2 | Marine |
| 3 | Maritime System Defense |
| 4 | **Navy** |
| 5 | Scout |
| 6 | Surface System Defense |

Only result 4 produces a Navy character. Any other result requires a full restart (re-roll all six characteristics, re-attempt qualification). The retry loop terminates with an error after 1,000 consecutive non-Navy outcomes (per FR-002).

---

## §6 Career Term Sequence

Each term of service proceeds in this order:

1. Pick a skill table; roll 1d6 for a skill (base skill roll for the term).
2. Roll survival (INT 5+). Failure ends the career immediately.
3. If rank = 0: roll commission (SOC 7+). On success, rank becomes 1; gain one additional skill roll.
4. If rank ≥ 1 and rank < 6: roll advancement (EDU 6+). On success, rank increases by 1; gain one additional skill roll. A roll when already at rank 6 is not made.
5. Apply any automatic rank bonus skills (see §8).
6. After term 4 and beyond: roll re-enlistment (2d6 ≥ 5). Failure ends the career; mustering-out begins.

**Skill rolls per term**: 1 base roll, +1 if commission or advancement succeeded (maximum 2 per term).

**Advanced Education eligibility**: A character may only roll on the Advanced Education table if their current EDU score is 8 or higher.

---

## §7 Career Termination Conditions

| Condition | Trigger |
|---|---|
| Survival failure | Survival roll fails during any term |
| Re-enlistment failure | Re-enlistment roll fails (terms 5–7 only) |
| 7-term cap | Character has completed 7 terms |

Terms 1–4 are served without a re-enlistment check. The generator always attempts re-enlistment from term 5 onward. Per FR-006, survival failure is career-ending only; it does not kill the character or modify characteristics. Aging effects are not simulated; age is computed as 18 + (4 × terms served).

---

## §8 Navy Rank Table

| Rank | Title | Automatic Bonus Skill |
|---|---|---|
| 0 | Starman | Zero-G 1 (granted on entry) |
| 1 | Midshipman | — |
| 2 | Lieutenant | — |
| 3 | Lt Commander | Tactics 1 (granted on promotion to rank 3) |
| 4 | Commander | — |
| 5 | Captain | — |
| 6 | Commodore | — |

The SRD has a single unified rank table (no separate enlisted/officer split). Commission (SOC 7+) advances from rank 0 to rank 1. Subsequent advancement rolls (EDU 6+) increase rank by 1 per success.

**JSON output**: The `rank` field contains the rank title string. Rank 0 characters display "Starman" (not empty string), because the SRD gives rank 0 an explicit title. The spec's "empty string" note applies to careers where rank 0 carries no title; that case does not arise in Navy.

---

## §9 Navy Skill Tables

### Personal Development

| Roll | Result |
|---|---|
| 1 | +1 STR |
| 2 | +1 DEX |
| 3 | +1 END |
| 4 | +1 INT |
| 5 | +1 EDU |
| 6 | Melee Combat |

### Service Skills

| Roll | Skill |
|---|---|
| 1 | Comms |
| 2 | Engineering |
| 3 | Gun Combat |
| 4 | Gunnery |
| 5 | Melee Combat |
| 6 | Vehicle |

### Specialist Skills

| Roll | Skill |
|---|---|
| 1 | Gravitics |
| 2 | Jack o' Trades |
| 3 | Melee Combat |
| 4 | Navigation |
| 5 | Leadership |
| 6 | Piloting |

### Advanced Education (EDU 8+ required)

| Roll | Skill |
|---|---|
| 1 | Advocate |
| 2 | Computer |
| 3 | Engineering |
| 4 | Medicine |
| 5 | Navigation |
| 6 | Tactics |

---

## §10 Mustering-Out Rules

**Benefit rolls**: 1 per term served.
**Rank bonuses**: +1 roll for rank 4 (Commander); +2 rolls for rank 5 (Captain); +3 rolls for rank 6 (Commodore).
**Cash table limit**: Up to 3 rolls on the Cash Benefits table; remaining rolls must be on Material Benefits.
**Material DM**: Characters of rank 5 or 6 (O5/O6) gain +1 on Material Benefit rolls.
**Cash DM**: Characters with the Gambling skill gain +1 on Cash Benefit rolls. (No Navy skill table includes Gambling; this DM applies only if background skills are added in a future feature.)

### Cash Benefits Table

| Roll | Credits |
|---|---|
| 1 | 1,000 |
| 2 | 5,000 |
| 3 | 10,000 |
| 4 | 10,000 |
| 5 | 20,000 |
| 6 | 50,000 |
| 7 | 50,000 |

### Material Benefits Table

| Roll | Benefit |
|---|---|
| 1 | Low Passage |
| 2 | +1 Edu |
| 3 | Weapon |
| 4 | Mid Passage |
| 5 | +1 Soc |
| 6 | High Passage |
| 7 | Explorers' Society |

Material benefits "+1 Edu" and "+1 Soc" appear in the JSON output as material-type benefits with string values ("+1 Edu", "+1 Soc"). They are not applied to the character's characteristics at mustering-out time; they are benefits the character receives to use in play.

---

## §11 Resolved Ambiguities

### A. Characteristic Increases from Personal Development

**Situation**: Personal Development rolls 1–5 award +1 to STR/DEX/END/INT/EDU. The spec (FR-008) states "no characteristic modification occurs during generation" and assumes max UPP digit is C (12).

**Decision**: Apply characteristic increases from Personal Development rolls as SRD-faithful. The spec's C-max statement is an approximation for the common case; the implementation MUST use the full pseudo-hex table (§2) so that any characteristic value, however high, encodes correctly. Do not assume a C or F ceiling.

**Rationale**: Faithful SRD implementation (FR-011) takes precedence; the C-max note is descriptive, not prescriptive.

### B. "Officer Skills" Table Name

**Situation**: The spec informally refers to an "Officer Skills" table. The SRD does not have a table by that name for Navy; the third table is called "Specialist Skills" (or "Specialist").

**Decision**: Implement the third table as "Specialist Skills" per the SRD. This table is accessible to all Navy characters regardless of commission status. The spec label was informal.

### C. Rank 0 in JSON Output

**Situation**: The spec says `rank` is empty string for "a character who never received a commission and has no enlisted rating title." The SRD names rank 0 "Starman."

**Decision**: Use "Starman" for rank 0. It is an enlisted rating with an explicit SRD title. The empty-string case is a fallback for careers where rank 0 carries no name; that case does not arise in Navy.

### D. Re-enlistment Roll Mechanics

**Situation**: The SRD shows "5+" for re-enlistment with no characteristic listed.

**Decision**: Flat 2d6 ≥ 5 (no characteristic modifier). This matches CE SRD convention for re-enlistment checks across all careers.

### E. Commission and Advancement in the Same Term

**Situation**: Could a character both commission and advance in one term?

**Decision**: No. Commission (rank 0 → 1) and advancement (rank 1–5 → +1) are mutually exclusive per term. A character at rank 0 rolls commission only; a character at rank 1–5 rolls advancement only; a character at rank 6 rolls neither (already at maximum).

### F. Background Skills

**Situation**: The CE SRD character creation process includes background skills (homeworld and primary education skills). The spec makes no mention of background skills.

**Decision**: Background skills are out of scope for this MVP. The generator begins directly with characteristic rolls and the Navy career. Future expansion may add homeworld selection and background skills as a pre-career step.

### G. Gambling DM at Mustering-Out

**Situation**: SRD grants +1 on cash benefit rolls to characters with Gambling skill. No Navy skill table includes Gambling.

**Decision**: Implement the Gambling DM check against the character's skill list at mustering-out time. For Navy-only characters in this MVP, the DM will never trigger. The check must exist so it activates correctly if background skills (which could grant Gambling-0) are added later.
