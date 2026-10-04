# Week 3: The Register

*A utility's new billing system goes live on the 1st. Every half hour of every smart meter has to move over, and the meter feed is the only copy.*

[The Gauntlet on DataDriven](https://datadriven.io/community/week-3)

You're a data engineer at an electric utility. Each half hour, every smart meter reports the energy it used and its register, the total it has counted since it was installed. A feed forwards each report as 1 JSON line, and billing needs 1 clean row per meter per half hour from it. Write the code that turns the feed into that table.

## Result

| | |
|---|---|
| Score | 0.8469 |
| Rank | #5 of 14, top 36% |
| Points | +40 |
| Records recovered | 787,171 of 900,971 |
| Work per record | 1.1x median |
| Statements | 186 |
| Scored | 2026-10-04 |

## Columns

| Column | Correct | Wrong | Missed |
|---|---:|---:|---:|
| `usage_kwh` | 82% | 19,325 | 140,755 |
| `register_kwh` | 84% | 17,269 | 122,562 |
| `quality` | 86% | 1,611 | 121,639 |
| `meter_id` | 87% | 0 | 113,800 |
| `interval_end` | 87% | 0 | 113,800 |

## What the stream held

Every condition in the data, ordered by what it cost. "Handled" means its records came through about as well as the rest of the run.

| Condition | Of stream | Recovered | Handled |
|---|---:|---:|:---:|
| Local time, CDT or CST | 8.0% | 29% | no |
| Stamped at the start | 5.0% | 9% | no |
| Key order changes | 30.0% | 85% | yes |
| Running totals, no usage | 20.0% | 81% | no |
| Wh in place of kWh | 8.0% | 71% | no |
| JSON as a quoted string | 2.0% | 9% | no |
| Broken JSON structure | 2.0% | 15% | no |
| Head-end bookkeeping fields | 10.0% | 85% | yes |
| Read flags per maker | 6.0% | 82% | yes |
| Padding and casing | 6.0% | 85% | yes |
| Numbers as strings | 5.0% | 85% | yes |
| Epoch seconds or millis | 5.0% | 90% | yes |
| CDC envelopes | 2.5% | 93% | yes |
| Fill-in, then the real read | 10.0% | 96% | yes |
| Nulls spelled as strings | 15.0% | 90% | yes |
| Reads that come in late | 3.0% | 96% | yes |
| Duplicate records | 2.0% | 92% | yes |
| Truncated lines | 0.5% | 1% | no |
| Flag outside the contract | 1.0% | 83% | yes |

### Why these happen

**Local time, CDT or CST.** Meter clocks and some head-ends keep the utility's wall time and label it with the zone in force. On the fall-back night 01:30 happens twice, once as CDT and once as CST, and only the label tells the 2 half hours apart.

**Stamped at the start.** Interval data has 2 conventions: name the half hour by when it ends, or by when it begins. 1 head-end uses the beginning. Read as an end, every such row lands on the half hour before and overwrites it.

**Key order changes.** JSON objects are unordered, and every head-end builds them from a map. Key order carries no meaning and should never be relied on.

**Running totals, no usage.** Older meters report only their register, the count of energy since installation, so the half hour's usage is the difference from the previous half hour's register. That difference has to be taken in interval order, not in the order lines arrive.

**Wh in place of kWh.** A meter counts in watt hours internally and each head-end decides what to send: the raw count with a unit beside it, a unit written into the value, or a field named for the unit. The number means nothing without it.

**JSON as a quoted string.** Every line crosses a message queue, and 1 producer serialized the read to text before handing it to a client that serialized it again. The record is intact inside a string, sometimes inside the queue's own envelope.

**Broken JSON structure.** Some collectors assemble their lines by hand: a log prefix, a byte-order mark, a stray trailing character, quoting that depends on the value, a tab written into a string unescaped. A strict parser rejects the whole line.

**Head-end bookkeeping fields.** The feed adds its own collector, sequence and receipt markers. They describe how the read travelled, not the read, and do not belong in the table.

**Read flags per maker.** Each head-end writes its own code for a read taken from the meter and for one the system filled in. SUB, short for substituted, is the validation step's word for an estimate.

**Padding and casing.** Meter ids were keyed in at installation and printed on work orders, so they carry the padding, casing and missing dashes of whoever typed them.

**Numbers as strings.** Values that passed through a CSV stage or a shell template arrive quoted. The number is intact; the type is not.

**Epoch seconds or millis.** Different services wrote the same field as epoch seconds or milliseconds, sometimes as a string. Both look like plausible integers.

**CDC envelopes.** Part of the feed is replicated out of the meter database by change data capture: each line is an operation with the row before and after it. The row is the after image; the before image is what it replaced.

**Fill-in, then the real read.** The real read replaces the estimate whenever it lands. A replay of the estimation run can also re-send an estimate after its real read went out, and the real read still stands.

**Nulls spelled as strings.** A head-end that had no value writes whatever its template uses for absence, and 3 templates means several spellings of nothing.

**Reads that come in late.** A meter that loses its radio link keeps its half hours in memory and uploads them when the link returns, as 1 burst in interval order.

**Duplicate records.** A collector that times out resends its whole batch. At-least-once delivery is the norm, so the reader has to settle identity.

**Truncated lines.** A collector whose buffer fills mid-write leaves a partial line. What was written before the cut is still real; the rest is gone.

**Flag outside the contract.** Reads waiting in the validation queue carry workflow states like PENDING or HOLD. They say where the read is in a process, not whether it came from the meter, so billing stages them as unknown.

Concepts exercised: pyArithmetic, pyBooleanOps, pyClassBasic, pyCsvJson, pyDataTypes, pyDictComprehension, pyDictCreate, pyDictIterate, pyDictMerge, pyDictMethods, pyDunderMethods, pyExceptionTypes, pyFStrings, pyForBasic, pyFuncDef, pyGuardClauses, pyIfElse, pyJsonHandling, pyListCreate, pyListModify, pyMathOps, pyModules, pyRecursion, pyRegex, pySlicing, pyStackQueue, pyStringBasic, pyStringMethods, pyTernary, pyTryExcept, pyTuples, pyTypeConversion, pyUnpacking, pyVariables, pyWhileLoops

## Submission

The handler that was graded is in [`handler.py`](./handler.py).
