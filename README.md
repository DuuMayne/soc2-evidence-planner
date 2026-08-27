# SOC 2 Evidence Planner

A repeatable framework for planning and organizing SOC 2 Type II evidence collection. Built to work with Claude Code as a custom slash command, or as standalone reference templates.

## What This Does

When you receive an auditor's information request list (the big spreadsheet with 50-300 individual evidence requests), this tool helps you:

1. **Parse the request list** and categorize by control family, evidence type, owner, and deadline
2. **Generate a phased project plan** with timeline, priorities, and risk mitigation
3. **Create a complete ticket structure** (Jira/Linear/etc.) with naming conventions, labels, and workflows
4. **Produce communication templates** — kickoff messages, status updates, escalation paths
5. **Build a QA checklist** tailored to evidence type requirements (IPE, screenshots, populations, samples)

## Quick Start

### With Claude Code (Recommended)

1. Copy the `.claude/` directory into your project root (or your home directory for global access):

```bash
cp -r .claude/ ~/your-project/.claude/
# or for global access:
cp -r .claude/ ~/.claude/
```

2. Place your auditor's request list spreadsheet somewhere accessible (e.g., your project directory or Downloads).

3. Run the command:

```
/soc2-evidence-plan
```

Claude will ask you a few questions about your org, then generate a complete evidence collection plan customized to your request list.

### Without Claude Code

Use the templates in `templates/` directly:

- `templates/project-plan.md` — Phased plan structure with timeline
- `templates/ticket-structure.md` — Jira/Linear hierarchy and workflow
- `templates/communication-templates.md` — Slack/email templates for stakeholders
- `templates/evidence-requirements.md` — Per-evidence-type checklists (IPE, screenshots, populations, etc.)
- `templates/qa-checklist.md` — Quality assurance process before submission

## How It Works

### The SOC 2 Evidence Collection Problem

Every SOC 2 Type II audit follows the same pattern:

1. Auditor sends a request list (spreadsheet with 50-300 line items)
2. Each request maps to a control, has an evidence type, and a deadline
3. Some requests depend on others (populations must come before sample selections)
4. Evidence has strict formatting requirements (IPE, system clocks, parameters)
5. Multiple teams own different controls
6. Two major deadlines: configurations/populations first, samples second

This framework encodes the organizational knowledge needed to execute that process efficiently — the phasing, the prioritization logic, the communication cadence, the QA gates.

### Evidence Types

| Type | What It Is | Key Requirements |
|------|-----------|-----------------|
| **Policy** | Written procedures governing a control | Must be effective during audit period, version-controlled |
| **Population** | Complete list of items for a control period | Parameters, row count, system clock at generation |
| **IPE** | Integrity of Processing Evidence | Proves the population/report is complete and accurate |
| **Screenshot** | Point-in-time configuration capture | System clock visible, full URL/breadcrumb, recent as possible |
| **Config** | System configuration export | Shows settings match control requirements |
| **Sample** | Specific items from a population | Selected by auditor, must show control operated for that item |
| **Report** | Generated output from a system | Parameters, filters, timestamp visible |

### Phasing Strategy

The framework uses a 5-phase approach:

1. **Setup & Communication** (Days 1-3) — Create tracking, notify owners, identify blockers
2. **Organize & Prioritize** (Days 3-5) — Group by owner, set priorities, identify dependencies
3. **Population Sprint** (Days 5-14) — Collect populations first (they feed sample selections)
4. **Evidence Collection** (Days 7-deadline 1) — Parallel collection of all non-sample evidence
5. **Sample Sprint** (After auditor selects samples) — Rapid collection of specific sample evidence

## Customization

The slash command will ask you for:

- **Audit firm name** — Who's auditing you
- **Audit period** — Start and end dates
- **In-scope systems** — What applications/platforms are covered
- **Deadlines** — When configurations vs. samples are due
- **Team structure** — Who owns which control families
- **Tooling** — Jira/Linear, Slack/Teams, Google Drive/SharePoint

Everything else is derived from your request list spreadsheet.

## Repository Structure

```
soc2-evidence-planner/
├── .claude/
│   └── commands/
│       └── soc2-evidence-plan.md    # The Claude Code custom command
├── templates/
│   ├── project-plan.md              # Phased plan structure
│   ├── ticket-structure.md          # Ticket hierarchy and workflow
│   ├── communication-templates.md   # Stakeholder messaging
│   ├── evidence-requirements.md     # Per-type evidence checklists
│   └── qa-checklist.md              # QA process and gates
├── examples/
│   └── example-output.md            # What a generated plan looks like
└── README.md
```

## Who This Is For

- **GRC practitioners** managing SOC 2 evidence collection for the first time (or the tenth)
- **Security program managers** coordinating across engineering, IT, HR, and legal
- **Compliance teams** at startups/mid-size companies without dedicated audit tooling
- **Anyone** who's received a 200-row evidence request spreadsheet and thought "where do I even start"

## Contributing

PRs welcome. The most valuable contributions are:

- Additional evidence type patterns (SOC 2 + HITRUST, ISO 27001 mappings)
- Ticket system templates beyond Jira (Linear, Shortcut, Azure DevOps)
- Communication templates for Teams/email (currently Slack-focused)
- Automation scripts for bulk ticket creation

## License

MIT
