# SOC 2 Evidence Collection — Communication Templates

> Copy, customize bracketed values, and send. Designed for Slack but adaptable to Teams/email.

---

## Kickoff Announcement

**Channel:** Main team channel or dedicated audit channel  
**When:** Day 1  
**Audience:** All control owners and stakeholders

```
SOC 2 [Year] Audit — Evidence Requests Issued

Hey team — [Auditor Name] has issued our SOC 2 Type II information requests for the [Year] audit. I'll be coordinating evidence collection and need help from several teams.

KEY DATES:
- [Deadline 1 Date] ([X] days): Policies, configs, populations, screenshots, IPE
- [Deadline 2 Date] ([Y] days): Sample evidence (auditor selects from our populations)

CRITICAL REQUIREMENTS:
- All evidence must be dated within [Audit Period Start] - [Audit Period End]
- Reports/populations must show: parameters, row count, system clock at generation
- Screenshots must show: system clock visible at time of capture
- Point-in-time evidence should be as recent as possible

WHAT HAPPENS NEXT:
1. I'm creating [ticket system] tickets for every request (link coming shortly)
2. Each of you will receive specific assignments with clear deadlines
3. I'll send weekly status updates and escalate blockers

SHARED RESOURCES:
- Tracker: [link to epic/board]
- Evidence folder: [link to shared drive]
- Questions: Ask in [this channel / thread] or DM me

Internal deadlines are set [3-5] days before external deadlines to allow for QA. Please flag blockers immediately — don't wait.
```

---

## Per-Owner Assignment Message

**Channel:** DM or team-specific channel  
**When:** Day 1-2  
**Audience:** Individual control owner or team

```
SOC 2 [Year] — Your Evidence Requests

Hi [Name] — here are your SOC 2 evidence assignments. I've created tickets for each one.

YOUR REQUESTS ([N] items):

Due [Deadline 1 Date]:
- [Req ##]: [Brief description] | [Evidence Type] | [System]
- [Req ##]: [Brief description] | [Evidence Type] | [System]
- [Req ##]: [Brief description] | [Evidence Type] | [System]

Due [Deadline 2 Date] (samples — blocked until auditor selects):
- [Req ##]: [Brief description]
- [Req ##]: [Brief description]

YOUR TICKETS: [link to filtered view showing only their tasks]

FORMAT REQUIREMENTS FOR YOUR EVIDENCE TYPES:

[Include only the relevant sections below based on their evidence types]

For Screenshots:
- System clock must be visible in the screenshot
- Show full URL or navigation path
- Save as PNG: [ControlID]_[System]_[Description]_[Date].png

For Populations/Reports:
- Must include: parameters used, row count, system clock at generation time
- Date range: [exact range needed]
- Export as Excel/CSV preferred
- I'll need IPE documentation for each (I can help with that)

For Policies:
- Must be the version effective during [Audit Period]
- Include version date or approval metadata

DEADLINES:
- Internal deadline: [Deadline 1 - buffer days] (gives me time to QA before submission)
- Hard deadline: [Deadline 1]

Please let me know by [Day 3]:
1. Any requests you can't fulfill (evidence doesn't exist, need access, etc.)
2. Estimated completion date for your items
3. Whether you need a backup person assigned

Happy to hop on a quick call if anything is unclear. Thanks!
```

---

## Population Request (Detailed)

**When:** When requesting a population/report from a system owner  
**Audience:** Person generating the population report

```
Population Request — [Control ID] — [System Name]

Hi [Name] — I need a population report for the SOC 2 audit. Details below.

WHAT I NEED:
[Paste exact auditor request text]

SPECIFICATIONS:
- System: [System Name]
- Date range: [Exact start] to [Exact end]
- Format: Excel or CSV preferred

CRITICAL — THE REPORT MUST INCLUDE:
1. Parameters used to generate it (filters, date range, any criteria)
2. Total row count
3. System clock/timestamp showing when the report was generated

I also need you to take a screenshot showing:
- The query/filter parameters you used
- The system clock at the time of generation
- The total count displayed

This is for IPE (Integrity of Processing Evidence) — it proves to the auditor that the report is complete and was generated correctly.

FILE NAMING: [ControlID]_[System]_Population_[Date].xlsx
SCREENSHOT: [ControlID]_[System]_Population_IPE_[Date].png

UPLOAD TO: [shared folder path]
TICKET: [link to Jira/Linear task]
DUE: [Internal deadline]

Example of what good output looks like:
- Excel file with all [items] from [date range]
- Column headers clearly labeled
- No truncation (full dataset)
- Separate screenshot showing how you generated it

Let me know if you have questions about the date range or filters to use.
```

---

## Screenshot Guidance

**When:** Attached to any request for screenshot evidence  
**Audience:** Anyone collecting screenshot evidence

```
Screenshot Evidence Guide

When capturing screenshots for SOC 2 evidence:

MUST INCLUDE:
- System clock (date and time) visible in the screenshot
- Full URL or navigation breadcrumb (proves which system/page)
- User context / who is logged in (if relevant to the control)

FORMATTING:
- Capture full window (don't crop out surrounding context)
- Save as PNG (not JPEG — compression artifacts reduce readability)
- Filename: [ControlID]_[System]_[WhatIsShown]_[YYYY-MM-DD].png

TIPS:
- If the system clock isn't naturally visible, show your OS clock in the taskbar/menubar
- For web apps, include the browser tab and address bar
- If multiple screenshots needed for one request, number them: ..._01.png, ..._02.png
- Take screenshots as recently as possible (auditors prefer current-state over months-old)

UPLOAD:
- Folder: [shared drive path]/Screenshots/[ControlFamily]/
- Update your ticket with the file location when done
```

---

## Weekly Status Update

**Channel:** Main audit channel  
**When:** Every Monday  
**Audience:** All stakeholders

```
SOC 2 [Year] Weekly Status — Week of [Date]

OVERALL PROGRESS:
- Completed: [X]/[Total] requests ([%])
- In Progress: [Y] requests
- Blocked: [Z] requests
- Not Started: [W] requests

[DEADLINE 1] STATUS: [ON TRACK / AT RISK / BLOCKED]
- [%] complete
- [Days] remaining
- Key items still outstanding: [list 2-3 biggest items]

[DEADLINE 2] STATUS: [PENDING SAMPLE SELECTION / ON TRACK / AT RISK]
- Populations submitted: [X]/[Y]
- Sample selections received: [Yes/No]

COMPLETED THIS WEEK:
- [Brief list of what was finished]

BLOCKERS (need help):
- [Blocker 1]: Owned by [Name], blocked because [reason]
- [Blocker 2]: Owned by [Name], blocked because [reason]

FOCUS THIS WEEK:
- [Priority 1]
- [Priority 2]
- [Priority 3]

Full tracker: [link]
```

---

## Escalation Message

**When:** Evidence is overdue or a blocker isn't being resolved  
**Audience:** The blocker owner's manager

```
SOC 2 Evidence — Escalation: [Control ID] at Risk

Hi [Manager Name] — escalating a SOC 2 evidence item that's at risk of missing our deadline.

ITEM: [Request description]
OWNER: [Person Name]
DEADLINE: [Date] ([X] days away)
STATUS: [Blocked / Overdue / No response]

ISSUE:
[Describe what's blocking — e.g., "Hasn't been started", "Waiting on system access", "Owner unresponsive for 3 days"]

IMPACT IF MISSED:
- This [feeds sample selection / is a direct audit request / etc.]
- Missing it could result in [audit finding / delayed report / exception noted]

WHAT I NEED:
- [Specific ask — e.g., "Can you help prioritize this on [Person]'s plate?"]
- Target completion: [Date]

Happy to discuss or find an alternative owner if [Person] is overloaded. Thanks for the help.
```

---

## Auditor Communication — Request for Sample Selections

**When:** After submitting populations, requesting the auditor select their samples  
**Audience:** Audit lead at the audit firm

```
Subject: SOC 2 [Year] — Populations Submitted, Requesting Sample Selections

Hi [Auditor Name],

We've submitted all population reports and supporting IPE for the [Year] SOC 2 Type II examination. The evidence is available in [location / portal / shared folder].

Submitted populations:
- [Control ID]: [Description] — [Row count] items
- [Control ID]: [Description] — [Row count] items
- [Control ID]: [Description] — [Row count] items
[...]

Each population includes IPE documentation (generation parameters, row counts, system timestamps).

Could you provide your sample selections at your earliest convenience? Our internal target is to have all sample evidence collected by [Deadline 2 - 5 days] to allow time for quality review before the [Deadline 2] submission date.

Please let me know if you have questions about any of the populations or need additional information to make selections.

Thank you,
[Your Name]
```

---

## No-Incidents Confirmation Request

**When:** A control requires confirmation that no incidents/events occurred  
**Audience:** 2+ people who can confirm (auditors typically want independent confirmation)

```
SOC 2 Evidence — No Incidents Confirmation Needed

Hi [Name 1] and [Name 2] — for the SOC 2 audit, I need independent confirmation from at least 2 people that [no security incidents occurred / no asset disposals occurred / etc.] during [date range].

CONTROL: [Control ID] - [Description]
PERIOD: [Start Date] - [End Date]
WHAT AUDITOR NEEDS: Written confirmation from 2+ individuals

Please reply to this message (or the linked ticket) with a statement like:

"I confirm that to my knowledge, [no security incidents were reported/escalated / no assets were disposed of / etc.] during the period [Start Date] through [End Date]."

If there WERE [incidents/disposals/etc.], let me know and I'll gather the evidence for those instead.

TICKET: [link]
DUE: [Date]

Thanks!
```

---

## Deadline Reminder (3 Days Out)

**Channel:** DM to owners with open items  
**When:** 3 days before each deadline

```
Reminder: SOC 2 Evidence Due in 3 Days

Hi [Name] — friendly reminder that the following items are due [Deadline Date] (3 days from now):

STILL OPEN:
- [Req ##]: [Brief description] — Status: [In Progress / Not Started]
- [Req ##]: [Brief description] — Status: [In Progress / Not Started]

If you're on track, great — just update your ticket status when you upload evidence.

If you're blocked or won't make it:
- Let me know TODAY so I can help unblock or reassign
- Even partial evidence is better than nothing — we can supplement with a note to the auditor

Upload location: [folder path]
Your tickets: [filtered link]

Thanks!
```

---

## Completion Celebration

**Channel:** Main audit channel  
**When:** After each deadline submission

```
SOC 2 [Year] — [Deadline 1/Deadline 2] Evidence Submitted!

Team — we just submitted [X] pieces of evidence to [Auditor Name] for the SOC 2 [Year] audit. [Deadline] met.

BY THE NUMBERS:
- [X] requests fulfilled
- [Y] control families covered
- [Z] team members contributed

SPECIAL THANKS TO:
- [Names of people who went above and beyond]

WHAT'S NEXT:
- [If Deadline 1: "Waiting for sample selections from auditor. I'll distribute those as soon as they arrive. Next deadline: [Deadline 2]."]
- [If Deadline 2: "Now we wait for the auditor to review. I'll communicate any follow-up questions. Thanks everyone for the hard work!"]
```
