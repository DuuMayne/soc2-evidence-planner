"""Render story and task descriptions as Atlassian Document Format (ADF)."""

from . import adf


EVIDENCE_CHECKLISTS = {
    "screenshot": [
        "System clock visible (date AND time)",
        "Full URL/breadcrumb visible",
        "User context shown (if relevant)",
        "Captured from production environment",
        "PNG format, descriptive filename",
        "Captured within last 30 days of deadline",
    ],
    "population": [
        "Date range matches exactly what was requested",
        "Parameters used to generate are documented",
        "Total row count explicitly stated",
        "System clock/timestamp at time of generation",
        "Export format: Excel/CSV (not PDF)",
        "Paired IPE documentation created",
    ],
    "ipe": [
        "Links to corresponding population/report",
        "Parameters documented",
        "Row count documented",
        "System clock screenshot attached",
        "Spot-check validation described (2-3 items)",
    ],
    "policy": [
        "Effective during audit period",
        "Version control metadata present",
        "Approval visible (if applicable)",
        "Content addresses the specific control statement",
    ],
    "sample": [
        "Matches auditor-selected sample exactly",
        "Shows approval (if required by control)",
        "Shows completion (if required by control)",
        "Covers the correct date from sample selection",
        "Control clearly operated for this specific item",
    ],
    "config": [
        "Exported from PRODUCTION environment",
        "Shows the specific setting the control requires",
        "Date of export documented",
        "System/source identified clearly",
        "Sensitive data redacted if necessary (note redactions)",
    ],
    "report": [
        "Report covers exact time period requested",
        "Generated from authoritative source system",
        "Parameters/filters visible or documented",
        "Generation timestamp visible",
        "Report is complete (not truncated)",
    ],
    "contract": [
        "Contract is fully executed (signed by all parties)",
        "Effective dates cover the audit period",
        "Correct legal entities named",
        "Relevant sections visible (SLA, security terms)",
    ],
}

QA_CHECKLIST = [
    "Self-review completed",
    "Peer review completed",
    "Final QA completed",
    "Uploaded to correct location",
    "File naming convention followed",
    "No PII/sensitive data unnecessarily exposed",
]


def render_story_description(control_id, control_name, control_description, tasks, config):
    audit = config.get("audit", {})

    task_items = []
    for t in tasks:
        system = t.systems[0] if t.systems else "N/A"
        dl = audit.get(f"deadline_{t.deadline_group}", {})
        dl_date = dl.get("date", "TBD")
        task_items.append(adf.list_item(
            adf.paragraph(
                adf.bold(f"Req {t.request_number:02d}"),
                adf.text(f": {t.evidence_description[:80]} — "),
                adf.text(f"Due {dl_date}"),
            )
        ))

    systems_in_scope = sorted(set(
        t.systems[0] for t in tasks if t.systems and t.systems[0] != "N/A"
    ))

    blocks = [
        adf.heading("Control Statement", 2),
        adf.paragraph(adf.text(control_description or control_name)),
        adf.rule(),
        adf.heading("Evidence Requests", 2),
        adf.paragraph(adf.text(f"This control has {len(tasks)} evidence request(s):")),
        adf.bullet_list(*task_items),
    ]

    if systems_in_scope:
        blocks.append(adf.heading("Systems In Scope", 2))
        blocks.append(adf.bullet_list(*[
            adf.list_item(adf.paragraph(adf.text(s))) for s in systems_in_scope
        ]))

    blocks.append(adf.rule())
    blocks.append(adf.heading("Acceptance Criteria", 2))
    blocks.append(adf.task_list(
        adf.task_item("All requested evidence collected"),
        adf.task_item("Evidence falls within audit period"),
        adf.task_item("IPE provided where required"),
        adf.task_item("Evidence passes QA review"),
        adf.task_item("Evidence uploaded to shared folder"),
    ))

    return adf.doc(*blocks)


def render_task_description(request, config):
    audit = config.get("audit", {})
    dl = audit.get(f"deadline_{request.deadline_group}", {})
    system = request.systems[0] if request.systems else "N/A"

    blocks = [
        adf.heading("Request Details", 2),
        adf.table(
            ["Field", "Value"],
            [
                ["Request #", str(request.request_number)],
                ["Control", f"{request.control_id} — {request.control_name}"],
                ["Due Date", dl.get("date", "TBD")],
                ["Priority", request.priority],
                ["Evidence Type", request.evidence_type.title()],
                ["System/Scope", system],
            ],
        ),
        adf.rule(),
        adf.heading("Evidence Request (From Auditor)", 2),
        adf.panel("info", adf.paragraph(adf.text(request.evidence_description))),
        adf.rule(),
        adf.heading("Assigned To", 2),
        adf.paragraph(
            adf.bold("Primary: "),
            adf.text(request.owner_name),
        ),
    ]

    checklist_items = EVIDENCE_CHECKLISTS.get(request.evidence_type, [])
    if checklist_items:
        blocks.append(adf.rule())
        blocks.append(adf.heading(f"Submission Requirements ({request.evidence_type.title()})", 2))
        blocks.append(adf.task_list(*[
            adf.task_item(item) for item in checklist_items
        ]))

    blocks.append(adf.rule())
    blocks.append(adf.heading("QA Checklist", 2))
    blocks.append(adf.task_list(*[
        adf.task_item(item) for item in QA_CHECKLIST
    ]))

    if request.evidence_type == "sample":
        blocks.append(adf.rule())
        blocks.append(adf.panel("warning", adf.paragraph(
            adf.bold("Blocked: "),
            adf.text("This task is blocked until the auditor selects samples from the corresponding population."),
        )))

    return adf.doc(*blocks)
