# SOC 2 Evidence Collection — Project Plan Template

> Fill in bracketed values for your organization. This template assumes a standard SOC 2 Type II with two submission deadlines.

**Audit Period:** [Start Date] - [End Date]  
**Auditor:** [Firm Name]  
**Today's Date:** [Date]  
**Deadline 1 (Configs/Populations):** [Date] — [X] days away  
**Deadline 2 (Samples):** [Date] — [Y] days away

---

## Timeline Overview

### Deadlines

| Deadline | What's Due | Days Away |
|----------|-----------|-----------|
| [Date 1] | Policies, configurations, populations, IPE, screenshots | [X] |
| [Date 2] | Sample evidence (selected by auditor from populations) | [Y] |

### Evidence Date Requirements

- All evidence must fall within the audit period: [Start] - [End]
- Point-in-time evidence (screenshots, configs) should be as recent as possible
- Populations must cover the specified date range exactly (often Start to ~1 month before Deadline 1)

### IPE Requirements

Every population and report must include:
- **Parameters** used to generate the report
- **Row count** / total records
- **System clock** at generation time (screenshot)
- Filter criteria documented

---

## Phase Breakdown

### Phase 1: Setup & Communication (Days 1-3)

**Objective:** Everyone knows what's needed and when.

- [ ] Create master tracking epic/project in ticket system
- [ ] Create all stories (one per control)
- [ ] Create all P1 tasks (populations + policies that feed downstream work)
- [ ] Send kickoff message to all control owners
- [ ] Identify blockers and gaps immediately (evidence that may not exist)
- [ ] Set up shared evidence folder structure
- [ ] Create status dashboard/filters

**Shared Folder Structure:**
```
SOC2_[Year]_Evidence/
├── Policies/
├── Populations/
├── Screenshots/
│   ├── [ControlFamily]_[ControlArea]/
│   └── ...
├── Configs/
├── Samples/
├── Reports/
├── IPE/
└── Contracts/
```

### Phase 2: Prioritize & Assign (Days 3-5)

**Objective:** Every request has an owner with a clear deadline.

- [ ] Create remaining P2 and P3 tasks
- [ ] Assign all tasks to specific individuals
- [ ] Identify multi-system requests and split into per-system tasks
- [ ] Map dependencies (population → IPE, population → sample)
- [ ] Flag any evidence that requires coordination between teams
- [ ] Set internal deadlines (buffer of 3-5 days before external deadlines)

**Priority Matrix:**

| Priority | Criteria | Internal Deadline |
|----------|----------|-------------------|
| P1 | Due Deadline 1 + feeds sample selection OR high audit risk | [Deadline 1 - 5 days] |
| P2 | Due Deadline 1, no downstream dependencies | [Deadline 1 - 3 days] |
| P3 | Due Deadline 2 (samples, blocked until selection) | [Deadline 2 - 3 days] |
| P4 | Supporting/optional documentation | Best effort |

### Phase 3: Population Sprint (Days 5-14)

**Objective:** All populations submitted so auditor can select samples.

- [ ] All population reports generated with proper IPE
- [ ] All IPE documentation complete (parameters, row counts, timestamps)
- [ ] Populations QA'd for correct date ranges
- [ ] Populations QA'd for completeness (no missing items)
- [ ] Submit populations to auditor on or before Deadline 1

**Why populations first:** The auditor selects samples FROM your populations. Late populations = late sample selections = compressed timeline for sample evidence.

### Phase 4: Parallel Evidence Collection (Days 7 through Deadline 1)

**Objective:** All non-sample evidence collected, QA'd, and packaged.

Running in parallel with Phase 3:
- [ ] Policy documents gathered and version-verified
- [ ] Configuration screenshots captured (with system clocks)
- [ ] Reports generated for specified time periods
- [ ] Contracts located and verified for audit period coverage
- [ ] IPE created for all populations and reports
- [ ] Peer review completed on all evidence

### Phase 5: Sample Sprint (After auditor selects samples through Deadline 2)

**Objective:** All sample evidence collected for auditor-selected items.

- [ ] Receive sample selections from auditor
- [ ] Split placeholder tickets into specific per-sample tasks
- [ ] Map each sample to its evidence location (ticket system, system logs, etc.)
- [ ] Collect evidence showing control operated for each sample
- [ ] QA each sample (correct date, shows approval/completion as required)
- [ ] Package and submit by Deadline 2

### Phase 6: QA & Submission (Final 3-5 days before each deadline)

**Objective:** Everything submitted is complete, correct, and auditor-ready.

- [ ] Universal QA pass (dates, naming, completeness)
- [ ] Evidence-type-specific QA pass
- [ ] Package submission with index/mapping document
- [ ] README explaining folder structure
- [ ] Submit to auditor
- [ ] Request confirmation of receipt

---

## Risk Register

| Risk | Impact | Mitigation | Escalation Trigger |
|------|--------|------------|-------------------|
| Evidence doesn't exist | Control finding/exception | Identify in Phase 1, notify auditor early, document compensating controls | Discovery during Phase 1-2 |
| Evidence outside date range | Invalid submission, rework | Regenerate within period; check version control history for policies | Evidence review shows wrong dates |
| Key person unavailable | Missed deadline for their requests | Identify backups in Phase 2, cross-train, get system access for 2+ people | Person unavailable >2 days before deadline |
| Auditor delays sample selection | Compressed sample collection timeline | Set expectation with auditor for selection date; pre-collect common samples | Samples not received by [Deadline 2 - 10 days] |
| Population too large/complex | Generation delays, IPE complexity | Work with system owners early; provide sample output for auditor validation | Population request identified as complex in Phase 2 |
| Conflicting priorities | Team members deprioritize audit work | Executive sponsor communication; link audit evidence to compliance obligations | Task not started within 48 hours of assignment |

---

## Communication Cadence

| When | What | Audience | Channel |
|------|------|----------|---------|
| Day 1 | Kickoff announcement | All control owners | Main channel |
| Day 1 | Per-owner request details | Individual owners | DM or team channel |
| Weekly (Mon) | Status update | All stakeholders | Main channel |
| Daily (final 2 weeks) | Quick sync | Active evidence collectors | Standup/huddle |
| As needed | Blocker escalation | Manager of blocker owner | DM + meeting |
| Deadline day | Submission confirmation | All stakeholders | Main channel |

---

## Success Metrics

Track daily:

| Metric | Target |
|--------|--------|
| Completion rate (completed / total) | 100% by deadline |
| On-time rate (submitted by internal deadline) | >95% |
| QA pass rate (passes QA first try) | >90% |
| Blocker resolution time | <24 hours |
| Evidence response time (assigned → submitted) | <48 hours for P1 |

---

## Day-by-Day Sprint Plan

### Week 1: [Dates]
| Day | Focus | Key Actions |
|-----|-------|-------------|
| 1 | Setup | Create epic, all stories, P1 tasks. Send kickoff messages. |
| 2 | Assign | Receive acknowledgments, identify gaps/blockers. Create P2/P3 tasks. |
| 3 | Triage | First evidence arriving, resolve early blockers. |
| 4-5 | Sprint | Policy collection, population queries started. |

### Week 2: [Dates]
| Day | Focus | Key Actions |
|-----|-------|-------------|
| 6-8 | Collection | Heavy evidence collection, daily check-ins with owners. |
| 9 | QA | Review all collected evidence for completeness. |
| 10 | Buffer | Finalize stragglers, package early submissions. |

### Week 3: [Dates] (if applicable before Deadline 1)
| Day | Focus | Key Actions |
|-----|-------|-------------|
| 11-12 | Final push | Last evidence items, QA reviews. |
| 13 | Package | Create submission package, final QA. |
| 14 | Submit | Submit Deadline 1 evidence. Request sample selections. |

### Weeks 4-5: [Dates] (between deadlines)
| Day | Focus | Key Actions |
|-----|-------|-------------|
| 15-18 | Wait/prep | Await sample selections. Pre-collect anticipated samples. |
| 19-22 | Sample sprint | Rapid sample evidence collection once selections received. |
| 23-24 | QA + Submit | QA sample evidence, package, submit by Deadline 2. |

---

## Appendix: Evidence Collection Tips

**For screenshots:**
- Show system clock in every screenshot
- Include full URL or navigation breadcrumb
- Capture full browser/app window (don't crop out context)
- Use descriptive filenames: `[ControlID]_[System]_[What]_[Date].png`

**For populations:**
- Run the exact date range specified (don't overshoot or undershoot)
- Export to Excel/CSV with column headers
- Screenshot the query parameters separately (for IPE)
- Note the row count explicitly

**For policies:**
- Verify the policy was effective during the audit period
- Include version history/approval dates if available
- If policy changed mid-period, provide both versions with effective dates

**For samples:**
- Match the exact item the auditor selected (user, date, transaction, etc.)
- Show both the action AND the approval (if the control requires approval)
- Include enough context that the auditor can trace the full lifecycle

**General:**
- When in doubt, ask the auditor for clarification before collecting
- More context is better than less (reduces follow-up questions)
- Consistent formatting across evidence makes the auditor's job easier
- Document any assumptions or interpretations in a notes field
