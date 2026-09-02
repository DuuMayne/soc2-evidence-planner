"""Atlassian Document Format (ADF) builder helpers for Jira Cloud v3 API."""


def doc(*blocks):
    return {
        "version": 1,
        "type": "doc",
        "content": list(blocks),
    }


def paragraph(*inlines):
    return {
        "type": "paragraph",
        "content": list(inlines),
    }


def heading(content, level=2):
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [text(content)],
    }


def text(content, marks=None):
    node = {
        "type": "text",
        "text": str(content),
    }
    if marks:
        node["marks"] = marks
    return node


def bold(content):
    return text(content, marks=[{"type": "strong"}])


def italic(content):
    return text(content, marks=[{"type": "em"}])


def code_inline(content):
    return text(content, marks=[{"type": "code"}])


def link_text(content, href):
    return text(content, marks=[{"type": "link", "attrs": {"href": href}}])


def bullet_list(*items):
    return {
        "type": "bulletList",
        "content": list(items),
    }


def ordered_list(*items):
    return {
        "type": "orderedList",
        "content": list(items),
    }


def list_item(*blocks):
    return {
        "type": "listItem",
        "content": list(blocks),
    }


def task_list(*items):
    return {
        "type": "taskList",
        "attrs": {"localId": ""},
        "content": list(items),
    }


def task_item(content, checked=False):
    return {
        "type": "taskItem",
        "attrs": {"localId": "", "state": "DONE" if checked else "TODO"},
        "content": [paragraph(text(content))],
    }


def rule():
    return {"type": "rule"}


def code_block(content, language=None):
    node = {
        "type": "codeBlock",
        "content": [text(content)],
    }
    if language:
        node["attrs"] = {"language": language}
    return node


def table(headers, rows):
    header_row = {
        "type": "tableRow",
        "content": [
            {
                "type": "tableHeader",
                "content": [paragraph(bold(h))],
            }
            for h in headers
        ],
    }
    data_rows = [
        {
            "type": "tableRow",
            "content": [
                {
                    "type": "tableCell",
                    "content": [paragraph(text(str(cell)))],
                }
                for cell in row
            ],
        }
        for row in rows
    ]
    return {
        "type": "table",
        "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
        "content": [header_row] + data_rows,
    }


def panel(panel_type, *blocks):
    """panel_type: info, note, warning, error, success"""
    return {
        "type": "panel",
        "attrs": {"panelType": panel_type},
        "content": list(blocks),
    }
