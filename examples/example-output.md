# Example: What the Generated Plan Looks Like

> This is a simplified example of what `/soc2-evidence-plan` produces when given an auditor's request list. The real output is customized to your specific request list, team, and tooling.

---

## Context (User Inputs)

- **Auditor:** Example Audit Firm LLP
- **Audit period:** January 1, 2026 - December 31, 2026
- **Deadline 1:** November 15, 2026 (Configs, Policies, Populations, IPE)
- **Deadline 2:** December 15, 2026 (Samples)
- **In-scope systems:** App Platform, Data Pipeline, Customer Portal
- **Teams:**
  - Security: Alex (GRC lead)
  - Infrastructure: Jordan
  - Engineering: Sam
  - IT Ops: Casey
  - HR: Morgan
- **Tooling:** Linear, Slack, Google Drive
- **Request list:** 85 individual requests across 30 controls

---

## Generated Output (5 files)

### File 1: SOC2_Evidence_Plan.md (excerpt)

```markdown
# SOC 2 2026 Evidence Collection Plan

**Audit Period:** January 1, 2026 - December 31, 2026
**Auditor:** Example Audit Firm LLP
**Today:** October 1, 2026
**Deadline 1:** November 15 (45 days) — Configs/Policies/Populations/IPE
**Deadline 2:** December 15 (75 days) — Sample Evidence

---

## Phase 1: Setup (Days 1-3)

- Create Linear project with all issues
- Send kickoff in #soc2-audit
- Per-team DMs with specific assignments:
  - Jordan (Infrastructure): 18 items — backups, monitoring, env segregation
  - Casey (IT Ops): 22 items — access mgmt, network, encryption
  - Sam (Engineering): 12 items — SDLC, change populations, DB access
  - Morgan (HR): 6 items — background checks, org chart, perf reviews

## Priority Assignments

### P1 — Critical (feeds sample selection, due Nov 15)
- Change populations across 3 systems (Sam)
- Access provisioning population (Casey)
- Vulnerability scan reports for sample months (Alex)
- Security incidents list (Alex)

### P2 — High (due Nov 15, no downstream dependency)
- All screenshots and configs
- All policies
- All IPE documentation

### P3 — Blocked (due Dec 15, after sample selection)
- All sample evidence (22 items, blocked until auditor selects)
```

---

### File 2: SOC2_Ticket_Structure.md (excerpt)

```markdown
## Linear Project Structure

### AC.02 - User Access Provisioning
**Owner:** Casey | **Requests:** 4

Issues:
1. `Req 12 - Population - Access Requests (All Systems) - Casey`
   - Priority: P1 | Due: Nov 12 (internal) | Type: Population
   - Labels: 2026-audit, deadline-nov-15, evidence-population, owner-it-ops
   
2. `Req 13 - IPE - Access Requests - Casey`
   - Priority: P1 | Due: Nov 12 | Type: IPE
   - Labels: 2026-audit, deadline-nov-15, evidence-ipe, owner-it-ops
   - Depends on: Req 12
   
3. `Req 14 - Policy - Access Management - Casey`
   - Priority: P2 | Due: Nov 12 | Type: Policy
   - Labels: 2026-audit, deadline-nov-15, evidence-policy, owner-it-ops

4. `Req 15 - Samples - Access Approval Tickets - Casey`
   - Priority: P3 | Due: Dec 12 | Type: Sample | Status: Blocked
   - Labels: 2026-audit, deadline-dec-15, evidence-sample, blocked, owner-it-ops
   - Depends on: Req 12 (auditor selects from this population)
```

---

### File 3: SOC2_Communication_Templates.md (excerpt)

```markdown
## Kickoff Message (for #soc2-audit)

SOC 2 2026 Audit — Evidence Collection Kickoff

Team — Example Audit Firm has issued our information requests. Here's what's happening:

KEY DATES:
- Nov 15 (45 days): Policies, configs, populations, screenshots, IPE
- Dec 15 (75 days): Sample evidence

I've created a Linear project with all 85 requests broken into individual issues.
Each of you has specific assignments — check your DMs for details.

Critical requirements for all evidence:
- Must be dated within Jan 1 - Dec 31, 2026
- Screenshots must show system clock
- Reports must show parameters + row count + generation timestamp

Project board: [link]
Evidence folder: [link]
Questions: Ask here or DM me

Weekly status updates start next Monday. Flag blockers immediately.

---

## Casey's Assignment DM

Hi Casey — here are your 22 SOC 2 items. I've created Linear issues for each.

Due Nov 15:
- Req 12: Access provisioning population (Jan-Oct 2026) + IPE
- Req 14: Access management policy
- Req 18: VPN/MFA config screenshots
- Req 22-25: Password settings (Okta, Google Workspace, etc.)
- Req 30: Network diagram
- Req 31-33: Firewall configs and security groups
- Req 40: Laptop inventory + IPE
- Req 41: Encryption config (MDM)
[...]

Due Dec 15 (blocked until sample selection):
- Req 15: Sample access approval tickets
- Req 19: Sample termination evidence
[...]

Your filtered view: [link]

Screenshots need system clock visible. Populations need row count + timestamp.
Internal deadline is Nov 12 (3 days buffer).

Let me know by Wednesday if anything is blocked.
```

---

### File 4: SOC2_QA_Checklist.md (excerpt)

```markdown
## QA for Casey's Screenshot Evidence (Reqs 18, 22-25, 41)

For each screenshot, verify:
- [ ] System clock visible (date AND time)
- [ ] Full URL/breadcrumb shows which system
- [ ] Taken from production (not staging)
- [ ] Setting/config the auditor asked about is clearly visible
- [ ] PNG format, descriptive filename
- [ ] Captured within last 30 days

Specific checks:
- Req 18 (VPN/MFA): Shows both TLS encryption setting AND MFA enforcement
- Req 22 (Okta passwords): Shows complexity, length, expiration, lockout settings
- Req 23 (Google passwords): Same as above for Google Workspace
- Req 41 (MDM encryption): Shows FileVault enforcement policy is active
```

---

### File 5: SOC2_Complete_Ticket_List.md (excerpt)

```markdown
## Summary

- Stories: 30
- Tasks: 85
  - Nov 15 deadline: 63 tasks
  - Dec 15 deadline: 22 tasks (blocked)

## By Owner:
- Alex (Security/GRC): 10 tasks
- Jordan (Infrastructure): 18 tasks
- Sam (Engineering): 12 tasks
- Casey (IT Ops): 22 tasks
- Morgan (HR): 6 tasks
- Other (Legal, Vendors): 2 tasks

---

## Full List

### CM - Change Management (3 stories, 12 tasks)

#### CM.01 - SDLC Process
| # | Summary | Owner | Due | Priority | Type |
|---|---------|-------|-----|----------|------|
| 1 | Req 01 - Policy - SDLC | Sam | Nov 12 | P1 | Policy |

#### CM.02 - Change Documentation  
| # | Summary | Owner | Due | Priority | Type |
|---|---------|-------|-----|----------|------|
| 2 | Req 02 - Population - App Platform Changes | Sam | Nov 12 | P1 | Population |
| 3 | Req 02 - Population - Data Pipeline Changes | Sam | Nov 12 | P1 | Population |
| 4 | Req 02 - Population - Customer Portal Changes | Sam | Nov 12 | P1 | Population |
| 5 | Req 03 - IPE - All Change Populations | Sam | Nov 12 | P1 | IPE |
| 6 | Req 04 - Samples - Change Tickets | Sam | Dec 12 | P3 | Sample |

[... continues for all 85 requests ...]
```

---

## What Makes This Useful

The generated plan is NOT generic advice. It's:

1. **Mapped to YOUR request list** — every item from the spreadsheet has a corresponding ticket with owner, deadline, and evidence type
2. **Prioritized correctly** — populations and policies that feed downstream work are P1, samples are blocked until auditor selects
3. **Communication-ready** — messages are pre-written for your specific teams and their specific assignments
4. **QA-specific** — checklists reference the actual control requirements, not generic "make sure it's good"
5. **Timeline-aware** — phases and sprints are calculated from YOUR deadlines, not hypothetical ones

The slash command regenerates all of this fresh each time, customized to whatever request list you feed it.
