# Week 4: The Interface

*A hospital's lab results arrive as HL7 messages, a text format older than the web. The quality team needs 1 clean row per result.*

[The Gauntlet on DataDriven](https://datadriven.io/community/week-4)

You're a data engineer at a hospital. Every lab result reaches it as an HL7 message: 1 result per message, text segments, | between the fields, filed under the specimen's accession number. An interface engine logs each message as 1 JSON line, and the quality team needs 1 clean row per result from that log. Write the code that turns the log into that table.

## Result

| | |
|---|---|
| Score | 0.5922 |
| Rank | #4 of 6, top 67% |
| Points | +20 |
| Records recovered | 518,641 of 749,978 |
| Work per record | 0.38x median |
| Statements | 129 |
| Scored | 2026-10-11 |

## Columns

| Column | Correct | Wrong | Missed |
|---|---:|---:|---:|
| `patient_id` | 51% | 65,380 | 303,386 |
| `observed_at` | 56% | 7,882 | 318,345 |
| `unit` | 60% | 47,847 | 254,252 |
| `value` | 61% | 16,604 | 278,340 |
| `status` | 68% | 6,391 | 235,152 |
| `accession` | 69% | 0 | 231,337 |
| `test` | 69% | 0 | 231,337 |

## What the stream held

Every condition in the data, ordered by what it cost. "Handled" means its records came through about as well as the rest of the run.

| Condition | Of stream | Recovered | Handled |
|---|---:|---:|:---:|
| Key order changes | 30.0% | 62% | yes |
| Tests named, not coded | 12.0% | 10% | no |
| More than 1 OBX | 12.0% | 35% | no |
| Extra segments | 20.0% | 62% | yes |
| LOINC as the alternate code | 9.0% | 9% | no |
| Values that are not numbers | 18.0% | 59% | no |
| Merged chart numbers | 7.0% | 55% | no |
| Units as typed | 16.0% | 58% | no |
| Test codes, 5 ways | 15.0% | 64% | yes |
| Lines split by LF or CRLF | 6.0% | 9% | no |
| MRN in 6 forms | 12.0% | 58% | no |
| Times with no offset | 12.0% | 62% | yes |
| Times in 5 widths | 10.0% | 57% | no |
| MR numbers from 2 issuers | 11.0% | 58% | no |
| Time in SPM-17 | 12.0% | 55% | no |
| Engine bookkeeping fields | 10.0% | 62% | yes |
| SI units beside US units | 14.0% | 37% | no |
| Time moved to the OBX | 8.0% | 58% | no |
| Backslashes doubled | 3.0% | 9% | no |
| Enter typed inside a field | 7.0% | 62% | yes |
| MLLP framing characters | 3.0% | 12% | no |
| Order-level code | 7.0% | 62% | yes |
| Padding and casing | 6.0% | 59% | no |
| Batch headers around it | 25.0% | 66% | yes |
| Run time beside the draw | 25.0% | 65% | yes |
| Flags written in the value | 20.0% | 57% | no |
| Decimals as written | 5.0% | 62% | yes |
| OBR-3 with a namespace | 4.0% | 62% | yes |
| Revised by a later line | 8.0% | 84% | yes |
| Duplicate records | 3.0% | 62% | yes |
| Flags outside the list | 3.0% | 60% | yes |
| Truncated lines | 0.5% | 0% | no |
| Withdrawn by W | 4.0% | 98% | yes |

### Why these happen

**Key order changes.** JSON objects are unordered, and the engine builds each line from a map. Key order carries no meaning and should never be relied on.

**Tests named, not coded.** A sender with no code mapped for a test sends its catalogue's display name instead, sometimes in the slot the code belongs in. Names follow the catalogue: a specimen after a comma, Na+ and K+ for the electrolytes.

**More than 1 OBX.** A panel's analyzer reports every analyte it ran, and labs send interpretive comments as an OBX under the result's own code. The result is the OBX whose code names it and whose value is a number.

**Extra segments.** A message carries whatever segments the sender adds: notes, the visit, the order, custom Z segments. The result lives in the OBX whatever surrounds it.

**LOINC as the alternate code.** OBX-3 is a coded element with room for 2 codings. Labs that map to LOINC late keep their own catalogue number first and put the LOINC in the alternate identifier, components 4 to 6.

**Values that are not numbers.** HL7 writes a value as text and says its type beside it: a number, a structured number with a comparator, a string, or a note, and some senders leave the type out. A result past the analyzer's range arrives as a comparator and a bound, or as the bound itself with the off-scale flag < or > in OBX-8.

**Merged chart numbers.** The merge message itself: an ADT event (A40, A34 or the older A18, by registration's version and setup) with the kept number in PID and the retired one in MRG. It carries no result, and it changes every result that follows under the retired number.

**Units as typed.** Units are typed at the bench and coded by the sender: cased freely, as a coded element, with a power spelled with ^ or its escape \S\, or with a micro sign that a Latin-1 hop turns into 2 characters. K/uL, x10E3/uL, thou/uL and mEq/L are the bench's names for 10*3/uL and mmol/L.

**Test codes, 5 ways.** Every lab codes a test its own way: a LOINC code, a local code, both at once, the long name, or the name alone. The same analyte reaches the engine under several spellings.

**Lines split by LF or CRLF.** HL7 ends a segment with a carriage return, and some senders and gateways rewrite it as a line feed or both. A split on 1 character leaves the whole message in 1 segment.

**MRN in 6 forms.** PID-3 is a list of identifiers, each with its type and issuer: the chart number beside a social security number, a check digit, a prefix a system added, the zeros of a fixed-width field. Only the type says which one is the chart number.

**Times with no offset.** A time without an offset is the sender's wall clock, and the 2 labs sit in 2 time zones. The same digits mean different instants depending on who sent them.

**Times in 5 widths.** An HL7 time carries as much as the sender had: a day, a minute, a second or a fraction, with or without an offset, and 1 sender writes ISO 8601. The same instant arrives in several widths.

**MR numbers from 2 issuers.** A patient has a chart number in every system that has seen them. The reference lab sends its own beside the hospital's, both typed MR, and only the assigning authority in component 4 says whose is whose.

**Time in SPM-17.** HL7 2.5.1 moved the collection time to the specimen segment, SPM-17, a range of start and end. Senders that follow it leave OBR-7 empty; OBR-14 beside it is when the lab received the tube, which is later.

**Engine bookkeeping fields.** The engine stamps its own sequence, acknowledgement and routing markers on every line. They describe the delivery, not the result.

**SI units beside US units.** Labs that serve clinicians on both conventions report a creatinine in mg/dL and umol/L, a glucose in mg/dL and mmol/L, as 2 OBX. Each carries its own LOINC; only the code tells them apart.

**Time moved to the OBX.** The collection time belongs in OBR-7. Some senders leave it blank there and stamp the time on the OBX instead, and some send no time at all, or the zeros that stand for none.

**Backslashes doubled.** The engine's log writer escapes the message once and the JSON serializer escapes it again. Each carriage return and backslash arrives as 2 characters.

**Enter typed inside a field.** Reference ranges with an age or sex split and addresses keyed at registration carry the line feed someone typed. Inside a segment it splits the segment in 2; a line that does not start with a segment name continues the 1 before it.

**MLLP framing characters.** On the wire every HL7 message travels in an MLLP frame: a vertical tab before MSH, a file separator and a carriage return after. An engine that logs the raw frame keeps those bytes.

**Order-level code.** HL7 carries a result status twice: per observation in OBX-11 and for the whole order in OBR-25. A sender that fills only the order's leaves every OBX-11 empty, and where both are filled each OBX keeps its own.

**Padding and casing.** Accession labels are scanned or keyed in, and status codes retyped. Padding and casing follow whoever typed them.

**Batch headers around it.** Reference labs deliver HL7 batch files: a file header and a batch header, the messages, and 2 trailers. A batch of 1 message still carries all 4, so MSH is not the first segment.

**Run time beside the draw.** HL7 defines OBX-14 as the time of the observation, which for a specimen is its collection, and for years labs filled it with when the analyzer ran the tube. OBR-7 keeps the collection time; OBX-14 is hours later.

**Flags written in the value.** Some result entry screens print the abnormal flag beside the number, and the interface sends the screen's text. The flag belongs to OBX-8; the number in front of it is the result.

**Decimals as written.** Analyzers report at their own precision and some senders pad or trim the decimals. The number is intact; its width is not.

**OBR-3 with a namespace.** An HL7 entity identifier carries its issuing namespace in later components. The accession is the first component; the rest says who issued it.

**Revised by a later line.** The verified result replaces the preliminary one whenever it lands. A replay of the entry run can also re-send a preliminary after its final went out, and the final still stands.

**Duplicate records.** A sender that gets no acknowledgement in time sends the message again with the same control id, and a sender replaying its queue after a restart sends it under a new one. At-least-once delivery means the reader settles identity on the result.

**Flags outside the list.** Result status codes cover a whole workflow: entered, partial, pending, cannot be obtained. Only final, preliminary and corrected describe a result the quality team can use.

**Truncated lines.** A log writer whose buffer fills mid-line leaves a partial line. Segments before the cut are real; the rest is gone.

**Withdrawn by W.** The W line itself: the same accession and test with OBX-11 W. It replaces the preliminary result it withdraws, and the value goes with it.

Concepts exercised: pyBooleanOps, pyBreakContinue, pyClassBasic, pyCsvJson, pyDictComprehension, pyDictCreate, pyDictIterate, pyDictMethods, pyDunderMethods, pyExceptionTypes, pyForBasic, pyFuncDef, pyGuardClauses, pyIfElse, pyJsonHandling, pyListCreate, pyListModify, pyMathOps, pyModules, pyRegex, pySlicing, pyStringBasic, pyStringFormat, pyStringMethods, pyStringSplitJoin, pyTernary, pyTryExcept, pyTuples, pyVariables

## Submission

The handler that was graded is in [`handler.py`](./handler.py).
