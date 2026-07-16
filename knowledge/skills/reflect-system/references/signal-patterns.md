# Signal Pattern Library

This document catalogs all patterns used to detect learning signals from conversations.

## HIGH Confidence - Corrections

### Explicit Negation
**Pattern**: `(?i)no,?\s+don't\s+(?:do|use)\s+(.+?)[,.]?\s+(?:do|use)\s+(.+)`
**Example**: "No, don't use pip directly, use uv instead"
**Action**: Add critical correction with old/new comparison
**Rationale**: User explicitly rejects one approach in favor of another

### Actually/Instead Corrections
**Pattern**: `(?i)actually,?\s+(.+?)\s+(?:is|should be)\s+(.+)`
**Example**: "Actually, the button is called 'SubmitButton'"
**Action**: Replace incorrect reference with correct one
**Rationale**: User corrects factual error or misunderstanding

### Instead Of Pattern
**Pattern**: `(?i)instead\s+of\s+(.+?),?\s+(?:you\s+should|use|do)\s+(.+)`
**Example**: "Instead of using var, you should use const"
**Action**: Document preferred alternative
**Rationale**: User guides toward better practice

### Never/Always Directives
**Pattern**: `(?i)(?:never|always)\s+(?:do|use|check for)\s+(.+)`
**Example**: "Always check for SQL injections in user input"
**Action**: Add to required checks section
**Rationale**: User establishes absolute rule

## MEDIUM Confidence - Approvals

### Success Confirmation
**Pattern**: `(?i)(?:yes,?\s+)?(?:that's\s+)?(?:perfect|great|exactly|correct)`
**Example**: "Yes, that's exactly right"
**Context**: After Claude proposes approach
**Action**: Add approach to Best Practices
**Rationale**: User validates Claude's decision

### Pattern Works
**Pattern**: `(?i)works?\s+(?:perfectly|great|well)`
**Example**: "This works perfectly"
**Context**: After implementation
**Action**: Document successful pattern
**Rationale**: User confirms solution effectiveness

### Positive Feedback
**Pattern**: `(?i)(?:good|nice)\s+(?:job|work)`
**Example**: "Good job on the error handling"
**Context**: After task completion
**Action**: Reinforce successful patterns
**Rationale**: User praises specific implementation

## LOW Confidence - Observations

### Consideration Questions
**Pattern**: `(?i)have\s+you\s+considered\s+(.+)`
**Example**: "Have you considered using TypeScript instead?"
**Action**: Add to Advanced Considerations
**Rationale**: User suggests alternative without requiring it

### Alternative Suggestions
**Pattern**: `(?i)why\s+not\s+(?:try|use)\s+(.+)`
**Example**: "Why not use async/await here?"
**Action**: Note alternative approach
**Rationale**: User proposes option without mandating change

### What About Questions
**Pattern**: `(?i)what\s+about\s+(.+)`
**Example**: "What about edge cases with empty arrays?"
**Action**: Document consideration for future
**Rationale**: User raises point for awareness

## Pattern Matching Strategy

### Context Analysis
For each pattern match, the system:
1. Extracts 5-message context window (before signal)
2. Identifies the skill being discussed
3. Captures Claude's previous approach (for comparisons)
4. Determines if correction/approval relates to code, process, or preference

### False Positive Mitigation
To reduce false positives:
- **Check message role**: Only process user messages for corrections
- **Verify context**: Approval patterns must follow assistant messages
- **Skill attribution**: Only attribute to skills actually invoked in session
- **Length filtering**: Ignore extremely short messages (<10 chars)

### Pattern Evolution
This library should evolve based on:
- Patterns that frequently match but aren't actionable → Remove or refine
- Common corrections not caught by patterns → Add new patterns
- User feedback on pattern detection accuracy → Adjust confidence levels

## Extending Patterns

### Adding New Patterns

To add a new detection pattern:

1. **Identify the signal type** (correction/approval/observation)
2. **Write a regex pattern** that matches the phrasing
3. **Choose confidence level** (HIGH/MEDIUM/LOW)
4. **Document with examples**
5. **Test against historical transcripts**
6. **Add to extract_signals.py**

Example:
```python
# In extract_signals.py
NEW_PATTERN = r"(?i)please\s+(?:always|never)\s+(.+)"
CORRECTION_PATTERNS.append(NEW_PATTERN)
```

### Pattern Testing

Before adding patterns to production:
- Test against 10+ real conversation transcripts
- Verify precision (% of matches that are valid)
- Verify recall (% of valid signals caught)
- Target: >80% precision, >60% recall

## Common Pitfalls

### Over-Matching
- Pattern: `(?i)yes` → Too broad, matches casual affirmations
- Solution: Require more context, e.g., `(?i)yes,?\s+(?:that's|it's)`

### Under-Matching
- Pattern: `(?i)use\s+X\s+instead` → Too specific, misses variations
- Solution: Add alternations, e.g., `(?i)use|leverage|prefer`

### Language Variations
- English-only patterns miss multilingual users
- Future: Add German, French, Spanish pattern variants
- Example: `(?i)nein,?\s+nicht\s+(.+)` (German "No, not...")

## Signal Quality Metrics

Track these metrics to improve pattern quality:
- **Detection rate**: % of sessions with ≥1 signal detected
- **Action rate**: % of detected signals that lead to skill updates
- **User approval rate**: % of proposed changes accepted by user
- **False positive rate**: % of signals flagged as incorrect by user

Target metrics:
- Detection rate: 30-40% (not every session has learnings)
- Action rate: 50-70% (most signals should be actionable)
- Approval rate: 70-90% (user should accept most proposals)
- False positive rate: <10% (keep noise low)

## Future Enhancements

### ML-Based Detection
Instead of regex patterns, train classifier on:
- Input: Message text + context + previous approach
- Output: Signal type + confidence + extracted info
- Benefits: Handle natural language variations better
- Challenges: Requires labeled training data

### Cross-Skill Learning
Detect patterns that apply across all skills:
- "Always use descriptive variable names"
- "Never hardcode credentials"
- Store in global best-practices skill

### Temporal Patterns
Detect patterns that emerge over multiple sessions:
- User consistently prefers approach X over Y
- Skill Z is frequently corrected in similar ways
- Aggregate signals for more confident updates
