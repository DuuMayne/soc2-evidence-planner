# SOC 2 Evidence Collection — Evidence Type Requirements

> Reference guide for what each evidence type requires. Use when assigning tasks or training control owners on submission expectations.

---

## Evidence Type Overview

| Type | What It Is | Key Requirement | Common Mistakes |
|------|-----------|-----------------|-----------------|
| Policy | Written procedures | Must be effective during audit period | Providing a draft or expired version |
| Population | Complete list of items | Parameters + row count + timestamp | Wrong date range, missing items |
| IPE | Integrity proof for populations | Screenshots of generation process | Forgetting system clock |
| Screenshot | Point-in-time config capture | System clock visible | Cropping out context, old screenshots |
| Config | System settings export | Shows control is in place | Showing test/dev instead of prod |
| Sample | Specific item from population | Matches auditor's selection exactly | Wrong item, missing approval step |
| Report | Generated system output | Parameters + timestamp | Regenerated outside audit period |
| Contract | Legal agreements | Effective during audit period | Expired contract, wrong entity |

---

## Policy Evidence

### What Auditors Want
A formal, approved document that defines how your organization implements a specific control. Must have been in effect during the audit period.

### Requirements Checklist
- [ ] Document title clearly identifies the policy/procedure
- [ ] Effective date falls within or before the audit period start
- [ ] If policy was updated mid-period, provide both versions with effective dates
- [ ] Version control metadata visible (version number, last updated, approved by)
- [ ] Approval evidence (signature, email approval, or change log showing approval)
- [ ] Content actually addresses the control the auditor is asking about

### File Naming
`[ControlID]_Policy_[PolicyName]_v[Version].pdf`

Example: `CM01_Policy_SDLC_ChangeManagement_v3.2.pdf`

### Common Issues
- **Expired policy:** If the policy expired or was superseded during the audit period, provide the version that WAS effective during that time
- **No formal policy exists:** Flag immediately — this may result in an audit finding. Consider whether there's an informal process that could be documented retroactively (with auditor awareness)
- **Policy doesn't cover the control:** Read the control statement carefully. The auditor wants to see that YOUR policy specifically addresses what THEY'RE testing

---

## Population Evidence

### What Auditors Want
A complete list of all items/events/transactions for a control during the audit period. They use this to select samples for testing.

### Requirements Checklist
- [ ] Date range matches exactly what was requested (not broader, not narrower)
- [ ] All items included (no filtering beyond what's specified)
- [ ] Parameters used to generate the report are documented
- [ ] Total row count explicitly stated
- [ ] System clock/timestamp at time of generation (screenshot)
- [ ] Column headers are clear and labeled
- [ ] Export format: Excel/CSV preferred (not PDF — auditors need to sort/filter)
- [ ] Paired IPE documentation created (separate task)

### File Naming
`[ControlID]_Population_[System]_[Description]_[GenerationDate].xlsx`

Example: `CM02_Population_SLOPlatform_Changes_2026-09-08.xlsx`

### Generation Process
1. Run the query/report with exact parameters specified
2. Before closing the results, screenshot showing:
   - The parameters/filters you used
   - The row count displayed
   - Your system clock
3. Export the full dataset
4. Save both the export and the screenshot
5. Document the process in the paired IPE task

### Common Issues
- **Wrong date range:** Auditor says "10/1/25 - 8/31/26" but you pull "2025 - 2026." Be exact.
- **Filtered too aggressively:** If auditor says "all changes" don't filter out minor changes. Let them decide what matters.
- **Missing items:** If you KNOW items are missing (system migration mid-period, data in two systems, etc.), document this in IPE and notify the auditor
- **Stale data:** Generate populations as close to the submission deadline as possible (the date range typically ends ~1 month before deadline)

---

## IPE (Integrity of Processing Evidence)

### What Auditors Want
Proof that your populations and reports are complete and accurate — that the system generated them correctly and nothing was omitted or manipulated.

### Requirements Checklist
- [ ] Links to the specific population/report it documents
- [ ] Parameters used to generate the report (screenshot of query/filter interface)
- [ ] Row count matches between report and what system displays
- [ ] System clock visible at time of generation (proves when it was pulled)
- [ ] Description of any filters or criteria applied
- [ ] Spot-check validation (manually verified 2-3 items are present that should be)
- [ ] Who generated the report (user context)

### File Naming
`[ControlID]_IPE_[System]_[Description]_[Date].md` (documentation)
`[ControlID]_IPE_[System]_Screenshot_[Date].png` (supporting screenshot)

### IPE Documentation Template
```markdown
# IPE — [Report/Population Name]

**Report File:** [filename of the population/report]
**Generated By:** [Person name]
**Generation Date:** [Date and time]
**Source System:** [System name]

## Parameters Used
- Date range: [Start] to [End]
- Filters applied: [List all filters, or "None — full dataset"]
- Query/view: [Name of saved query or description of how generated]
- User context: [Who was logged in, what permissions they have]

## Results
- Total row count displayed by system: [N]
- Total rows in exported file: [N] (should match)
- Any discrepancies: [None / Explain if different]

## Validation
- Spot check 1: [Verified item X from date Y is present in the export]
- Spot check 2: [Verified item Z from date W is present in the export]
- Spot check 3: [Verified a boundary item — first or last day of range]

## Attachments
1. Screenshot of report parameters at generation time (includes system clock)
2. Screenshot of row count displayed by system
3. The report/population file itself (separate upload)
```

### Common Issues
- **No system clock:** The single most common IPE failure. Make sure the clock is visible in screenshots.
- **Parameters not shown:** Screenshot must show HOW the report was generated, not just the results
- **Mismatch between stated count and actual:** If your screenshot shows "142 results" but the Excel has 140 rows, explain why (header row, summary row, etc.)

---

## Screenshot Evidence

### What Auditors Want
Visual proof that a configuration, setting, or control is in place at a specific point in time.

### Requirements Checklist
- [ ] System clock (date and time) visible in the screenshot
- [ ] Full URL or navigation breadcrumb (proves which system and page)
- [ ] Relevant setting/configuration clearly visible and readable
- [ ] User context shown if relevant (who is logged in)
- [ ] Full window captured (don't crop out surrounding context)
- [ ] As recent as possible (within last 30 days of deadline)
- [ ] PNG format (not JPEG — compression artifacts reduce readability)
- [ ] Descriptive filename following convention

### File Naming
`[ControlID]_[System]_[WhatIsShown]_[YYYY-MM-DD].png`

Examples:
- `LS01_Okta_PasswordSettings_2026-09-08.png`
- `CM07_SLOPlatform_EnvSegregation_2026-09-10.png`
- `CO04_UniFi_SecuritySettings_2026-09-05.png`

### How to Capture

**If system clock is naturally visible (web apps with timestamp):**
- Capture the full browser window including address bar and tab

**If system clock is NOT naturally visible:**
- Expand your window to show the OS taskbar/menubar with the clock
- Or take two screenshots: one of the setting, one of your system clock at the same moment
- Or use a screenshot tool that stamps the date/time automatically

**For multi-page configurations:**
- Number screenshots sequentially: `..._01.png`, `..._02.png`
- Note in the ticket which screenshot shows what

### Common Issues
- **Old screenshots:** "But this setting hasn't changed since 2023!" — Doesn't matter. Auditors want current-period evidence. Recapture it.
- **Cropped too tight:** Auditor can't tell which system or page this is from. Include context.
- **Wrong environment:** Make sure you're showing PRODUCTION, not staging/dev
- **Multiple monitors:** If your clock is on a different monitor, use OS screenshot tools that capture everything, or add the clock to the captured monitor

---

## Configuration Evidence

### What Auditors Want
Exported settings or rules from a system that demonstrate a control is configured correctly. Similar to screenshots but may be text/JSON/XML exports rather than visual captures.

### Requirements Checklist
- [ ] Exported from the PRODUCTION environment
- [ ] Shows the specific setting the control requires
- [ ] Date of export documented (timestamp or file metadata)
- [ ] System/source identified clearly
- [ ] Sensitive data redacted if necessary (passwords, keys) — but note what was redacted
- [ ] Context provided (what does this setting DO)

### File Naming
`[ControlID]_Config_[System]_[SettingName]_[Date].[ext]`

Examples:
- `LS12_Config_AWS_SecurityGroups_2026-09-08.json`
- `CO08_Config_Kandji_FileVaultPolicy_2026-09-05.png`
- `LS06_Config_Okta_MFASettings_2026-09-10.png`

### Common Issues
- **Test environment:** Double-check you're exporting from production
- **Over-redaction:** Redact secrets, but don't redact the setting values the auditor needs to see
- **No context:** A raw JSON export without explanation may confuse the auditor. Add a brief note explaining what the key settings mean

---

## Sample Evidence

### What Auditors Want
For specific items THEY selected from your populations, proof that the control operated correctly for that item.

### Requirements Checklist
- [ ] Matches the EXACT item the auditor selected (right user, right date, right transaction)
- [ ] Shows the control operated (approval was given, review was done, action was taken)
- [ ] Shows timing (when it happened relative to the triggering event)
- [ ] Shows who (which person performed the control activity)
- [ ] Shows completion (not just initiation — the full lifecycle)
- [ ] If control requires approval: approval is visible and from authorized person
- [ ] If control has timing requirements: timestamps show requirement was met

### File Naming
`[ControlID]_Sample[N]_[Description]_[ItemDate].[ext]`

Examples:
- `CM02_Sample3_ChangeTicket_JIR-1234_2026-02-15.pdf`
- `LS02_Sample1_AccessRequest_JSmith_2026-01-20.png`
- `LS04_Sample2_TerminationRemoval_JDoe_2026-03-05.pdf`

### What "Shows the Control Operated" Means

For different control types:

| Control Type | What Sample Must Show |
|-------------|----------------------|
| Change management | Request → Development → Testing → Approval → Implementation |
| Access provisioning | Request → Approval by authorized person → Access granted |
| Access termination | Termination date → Access removed (within required timeframe) |
| Access review | Review performed → Issues identified → Remediation completed |
| Incident response | Detection → Triage → Response → Resolution → Post-mortem |
| Backup verification | Backup scheduled → Backup completed → Verified restorable |
| Vulnerability management | Scan performed → Findings documented → Remediation tracked |

### Common Issues
- **Wrong sample:** You provide evidence for user "J. Smith" but auditor selected "J. Smythe." Match exactly.
- **Incomplete lifecycle:** Showing the request but not the approval. Or showing approval but not implementation.
- **Timing violation:** Control says "within 1 business day" but evidence shows 3 days elapsed. This IS a finding — don't hide it, but make sure you're reading the dates correctly.
- **Missing context:** A Jira ticket with just a title isn't enough. Show the full ticket with comments, approvals, and status changes.

---

## Report Evidence

### What Auditors Want
System-generated reports that demonstrate a control operated over a period of time (e.g., monthly vulnerability scan summaries, email security reports, alert summaries).

### Requirements Checklist
- [ ] Report covers the exact time period requested
- [ ] Generated from the authoritative source system
- [ ] Parameters/filters used are visible or documented
- [ ] Generation timestamp visible
- [ ] Report is complete (not truncated or summarized unless that's what was requested)
- [ ] If for "sample months" — verify you're providing the correct months

### File Naming
`[ControlID]_Report_[System]_[Description]_[Period].[ext]`

Examples:
- `IT06_Report_VulnScan_October2025.pdf`
- `LS13_Report_EmailSecurity_December2025.pdf`
- `CM09_Report_PatchingTickets_June2026.xlsx`

### Common Issues
- **Wrong sample months:** Auditor specifies which months/quarters. Provide those exact periods.
- **Summarized when full detail needed:** If auditor asks for "scan results," they usually want the full report, not just a summary dashboard
- **Regenerated after the fact:** If possible, provide the report as it was generated at the time. If you must regenerate for a past period, document this in IPE.

---

## Contract Evidence

### What Auditors Want
Legal agreements that demonstrate a third-party relationship has appropriate controls, terms, or obligations in place during the audit period.

### Requirements Checklist
- [ ] Contract is fully executed (signed by all parties)
- [ ] Effective dates cover the audit period
- [ ] Correct legal entities named (your company AND the counterparty)
- [ ] Relevant sections visible (SLA, security terms, compliance obligations)
- [ ] If amended during audit period, provide original + amendment
- [ ] Sensitive commercial terms may be redacted (but note redactions)

### File Naming
`[ControlID]_Contract_[VendorName]_[Type]_[EffectiveDate].[ext]`

Example: `EL07_Contract_VendorName_MSA_2024-01-01.pdf`

### Common Issues
- **Expired contract:** Contract ended before audit period ended. Need the replacement or renewal.
- **Wrong entity:** Contract is with your parent company, not the audited subsidiary
- **Draft only:** Unsigned contracts don't demonstrate the obligation is in place
