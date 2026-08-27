# SOC 2 Evidence Collection — Ticket Structure Template

> This template defines the hierarchy, naming conventions, workflow, labels, and filters for tracking SOC 2 evidence collection in a project management tool.

---

## Hierarchy

```
EPIC: SOC 2 [Year] Evidence Collection (Audit Period: [Start] - [End])
│
├── STORY: [ControlFamily].[Control#] - [Control Name]
│   ├── TASK: Req [##] - [EvidenceType] - [System/Scope] - [Owner]
│   ├── TASK: Req [##] - [EvidenceType] - [System/Scope] - [Owner]
│   └── TASK: Req [##] - [EvidenceType] - [System/Scope] - [Owner]
│
├── STORY: [ControlFamily].[Control#] - [Control Name]
│   └── ...
```

**Why this structure:**
- **Story = Control** — Keeps related evidence together, mirrors audit structure
- **Task = Individual Request + System** — Clear ownership, granular tracking
- Splitting multi-system requests into separate tasks per system ensures accountability

---

## Epic

**Title:** `SOC 2 [Year] Evidence Collection (Audit Period: [Start] - [End])`

**Description:**
```markdown
# SOC 2 [Year] Evidence Collection

**Audit Period:** [Start Date] - [End Date]
**Auditor:** [Firm Name]
**Client:** [Your Company / Entity Being Audited]

## Key Dates
- **[Deadline 1 Date]:** Policies, Configurations, Populations, IPE
- **[Deadline 2 Date]:** Sample Evidence

## Evidence Requirements
All evidence must:
- Fall within the audit period
- Include system clock for screenshots
- Include parameters + row count + timestamp for reports/populations

## Scope
- **In-Scope Systems:** [List systems]
- **Control Families:** [List families present in request list]

## Request Summary
- **Total Requests:** ~[N]
- **Control Requirements:** [N]
- **Stories:** One per control requirement
- **Tasks:** One per request (split by system if multi-system)

## Links
- [Request List Spreadsheet](link)
- [Evidence Submission Folder](link)
- [Plan Document](link)
```

---

## Story Template

**Naming:** `[ControlFamily].[Control#] - [Short Control Description]`

Examples:
- `CM.01 - SDLC and Change Management Process`
- `LS.02 - User Access Provisioning and Approval`
- `CO.09 - Security Incident Response`
- `IT.06 - Vulnerability Scanning`

**Description:**
```markdown
## Control Statement
[Full control wording from auditor's request list]

## Control Owner(s)
- Primary: [Name]
- Secondary: [Name] (if applicable)

## Evidence Requests
This control has [X] evidence requests:
- Req [##]: [Brief description] — Due [Deadline 1]
- Req [##]: [Brief description] — Due [Deadline 1]
- Req [##]: [Brief description] — Due [Deadline 2] (samples)

## Systems In Scope
[List which systems this control applies to]

## Acceptance Criteria
- [ ] All requested evidence collected
- [ ] Evidence falls within audit period
- [ ] IPE provided where required
- [ ] Evidence passes QA review
- [ ] Evidence uploaded to shared folder
```

---

## Task Template

**Naming:** `Req [##] - [EvidenceType] - [System/Scope] - [Owner]`

Examples:
- `Req 26 - Policy - SDLC & Change Management - [Engineer Name]`
- `Req 27 - Population - [System A] Changes - [Engineer Name]`
- `Req 35 - Screenshot - [System B] Env Segregation - [Infra Name]`
- `Req 46 - Population - Access Provisioning - [IT Ops Name]`

**Description:**
```markdown
## Request Details
**Request #:** [##]
**Control:** [ControlFamily.##] [Control Name]
**Due Date:** [Deadline 1 or Deadline 2]
**Priority:** [P1/P2/P3]

## Evidence Request (From Auditor)
[Paste exact request text from spreadsheet]

## System/Scope
[Specific system or "All in-scope systems" or "N/A"]

## Assigned To
**Primary:** [Name]
**Backup:** [Name]

## Evidence Type
[Policy / Population / IPE / Screenshot / Config / Sample / Report / Contract / Other]

## Submission Requirements

### For Screenshots:
- [ ] System clock visible
- [ ] Full URL/breadcrumb visible
- [ ] User context shown (if relevant)
- [ ] Saved as PNG: [ControlID]_[System]_[Description]_[Date].png

### For Populations/Reports:
- [ ] Parameters included
- [ ] Row count visible
- [ ] System timestamp visible
- [ ] IPE documentation created (link to IPE task)
- [ ] Date range matches: [specified range]

### For Policies:
- [ ] Effective during audit period
- [ ] Version metadata included
- [ ] Approval visible (if applicable)

### For Samples:
- [ ] Matches auditor-selected sample
- [ ] Shows approval (if required)
- [ ] Shows completion (if required)
- [ ] Covers correct date

## Evidence Location
**Folder:** [Path in shared drive]
**Filename:** [Following naming convention]

## QA Checklist
- [ ] Self-review completed
- [ ] Peer review completed
- [ ] Final QA completed
- [ ] Uploaded to correct location

## Related Tasks
- IPE Task: [link if applicable]
- Population Task: [link if this is a sample]
- Same Request (Other Systems): [links]
```

---

## Workflow

```
To Do → In Progress → QA Review → QA Approved → Submitted → Done
                          ↓
                     QA Failed → Back to In Progress
```

### Status Definitions

| Status | Meaning |
|--------|---------|
| **To Do** | Created, assigned, not started. Owner has been notified. |
| **In Progress** | Owner is actively collecting evidence. |
| **QA Review** | Evidence uploaded, awaiting review. |
| **QA Approved** | Passed all QA checks, ready for submission. |
| **Submitted** | Sent to auditor. Awaiting acceptance. |
| **Done** | Auditor accepted. No follow-ups. |

### Blocked Handling

When a task is blocked:
1. Add `blocked` label
2. Document blocker reason in task
3. Tag the person who can unblock
4. If not resolved in 24 hours, escalate to their manager

---

## Labels

### Required on Every Task

| Category | Labels |
|----------|--------|
| Audit year | `[year]-audit` |
| Deadline | `deadline-[date]` (e.g., `deadline-sept-11`, `deadline-sept-30`) |
| Control family | `[family]-[area]` (e.g., `cm-change-mgmt`, `ls-logical-sec`) |

### Evidence Type

- `evidence-policy`
- `evidence-population`
- `evidence-ipe`
- `evidence-screenshot`
- `evidence-config`
- `evidence-sample`
- `evidence-report`
- `evidence-contract`
- `evidence-other`

### System (if applicable)

- `system-[name]` for each in-scope system
- `system-all` if applies to all
- `system-na` if not system-specific

### Owner Group

- `owner-[team]` (e.g., `owner-security`, `owner-engineering`, `owner-it-ops`, `owner-hr`, `owner-legal`)

### Status

- `blocked`
- `needs-qa`
- `qa-passed`
- `qa-failed`
- `urgent`
- `submitted`

---

## Multi-System Request Handling

When a single request says "for all in-scope systems" or "for each system":

**Create one task per system:**
```
Req 27 - Population - [System A] Changes - [Owner A]
Req 27 - Population - [System B] Changes - [Owner A]
Req 27 - Population - [System C] Changes - [Owner B]  ← different owner!
```

**Link them:** "is related to" each other

**Benefits:**
- Each owner sees only their tasks
- Per-system completion tracking
- Handles cases where different people own different systems
- No ambiguity about responsibility

---

## Dependency Linking

| Relationship | When to Use |
|-------------|-------------|
| "blocks" | Population task blocks its sample task |
| "is documented by" | IPE task documents a population task |
| "is related to" | Same request split across systems |

---

## Filters to Create

### 1. My Open Tasks
```
assignee = currentUser AND status != Done AND label = "[year]-audit"
ORDER BY priority DESC, duedate ASC
```

### 2. Deadline At Risk
```
label IN ("[deadline-label]", "[year]-audit")
AND status NOT IN ("QA Approved", "Submitted", "Done")
AND duedate <= [deadline date]
ORDER BY priority DESC
```

### 3. Blocked Items
```
label IN ("blocked", "[year]-audit") AND status != Done
ORDER BY priority DESC, created ASC
```

### 4. QA Queue
```
status = "QA Review" AND label = "[year]-audit"
ORDER BY duedate ASC
```

### 5. By Owner/Team
```
label IN ("owner-[team]", "[year]-audit") AND status != Done
ORDER BY duedate ASC, priority DESC
```

### 6. By Evidence Type
```
label IN ("evidence-[type]", "[year]-audit")
ORDER BY duedate ASC
```

### 7. Completed This Week
```
status = Done AND label = "[year]-audit" AND resolved >= startOfWeek()
ORDER BY resolved DESC
```

---

## Dashboard Widgets

| Widget | Purpose |
|--------|---------|
| Pie: Tasks by Status | Overall progress at a glance |
| Bar: Tasks by Assignee | Workload distribution |
| Table: Blocked Items | Immediate action needed |
| Gauge: Deadline 1 Progress | % complete for first deadline |
| Gauge: Deadline 2 Progress | % complete for second deadline |
| Table: Due This Week | Focus area for the week |
| Activity Stream | Recent completions and updates |

---

## Bulk Creation Strategy

### Option A: CSV Import

Most ticket systems support CSV import. Create a CSV with:
```csv
Issue Type,Summary,Description,Assignee,Due Date,Priority,Labels
Story,[ControlFamily.##] - [Name],[description],[owner],[date],High,[labels]
Task,Req [##] - [Type] - [System] - [Owner],[description],[owner],[date],P1,[labels]
```

### Option B: API Script

Use your ticket system's API to bulk-create from the parsed request list. Most useful for 100+ tasks.

### Option C: Manual with Templates

Copy-paste the task template for each item. Most control, slowest for large request lists.

**Recommended approach:** Create stories manually (only ~20-40), then use CSV import for tasks (~60-120).

---

## Recommended Creation Order

1. **Epic** (1 item)
2. **Stories** — one per control (~20-40 items)
3. **P1 Tasks** — populations, policies that feed downstream work
4. **P2 Tasks** — remaining Deadline 1 items
5. **P3 Tasks** — sample placeholders (mark as blocked)
6. **Filters & Dashboard**
7. **Send kickoff communications with links**
