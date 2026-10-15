from pathlib import Path
import py_compile
import subprocess
from collections import defaultdict
import datetime
import io
import os
import sys
import html

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# =============================================================
# CONFIGURATION
# =============================================================

COLLEGE_NAME = (
    "Swami Keshvanand Institute of Technology,"
    "Management & Gramothan, Jaipur"
)
DEPARTMENT_NAME = "Department of Computer Science & Engineering"


# =============================================================
# REPOSITORY INFORMATION
# =============================================================

def get_repo_info():
    """Return repository name and current Git branch."""
    repo_name = "Project-Repository"
    branch_name = "main"

    try:
        root_path = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            encoding="utf-8",
            errors="replace",
        ).strip()
        repo_name = os.path.basename(root_path)
    except Exception:
        try:
            remote_url = subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                encoding="utf-8",
                errors="replace",
            ).strip()
            repo_name = (
                remote_url.rstrip("/")
                .split("/")[-1]
                .replace(".git", "")
            )
        except Exception:
            repo_name = os.path.basename(os.getcwd())

    try:
        branch_name = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            encoding="utf-8",
            errors="replace",
        ).strip()
    except Exception:
        pass

    return repo_name, branch_name


# =============================================================
# GIT METRICS
# =============================================================

def get_git_metrics(
    interval="weekly",
    start_date=None,
    end_date=None,
):
    """
    Read Git history and calculate contribution metrics.

    Supported interval values:
        weekly
        monthly
        final
        custom
    """

    today = datetime.date.today()

    git_args = [
        "git",
        "log",
        "--no-merges",
        "--pretty=format:COMMIT|||%h|||%an|||%ad|||%s",
        "--date=short",
        "--numstat",
    ]

    if start_date and end_date:
        since = start_date.strftime("%Y-%m-%d")
        until = end_date.strftime("%Y-%m-%d")

        git_args.append(f"--since={since} 00:00:00")
        git_args.append(f"--until={until} 00:00:00")

        scope_title = (
            f"{start_date.strftime('%B %d, %Y')} - "
            f"{end_date.strftime('%B %d, %Y')}"
        )

        timeline_mode = "weekly"

    elif interval == "weekly":
        since_date = today - datetime.timedelta(days=7)

        git_args.append(
            f"--since={since_date.strftime('%Y-%m-%d')} 00:00:00"
        )

        scope_title = (
            f"Last 7 Days "
            f"(Since {since_date.strftime('%B %d, %Y')})"
        )

        timeline_mode = "weekly"

    elif interval == "monthly":
        since_date = today - datetime.timedelta(days=30)

        git_args.append(
            f"--since={since_date.strftime('%Y-%m-%d')} 00:00:00"
        )

        scope_title = (
            f"Last 30 Days "
            f"(Since {since_date.strftime('%B %d, %Y')})"
        )

        timeline_mode = "monthly"

    else:
        scope_title = "Complete Project Lifecycle (All Commits)"
        timeline_mode = "final"

    try:
        raw_output = subprocess.check_output(
            git_args,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError:
        print(
            "[ERROR] Git command failed. "
            "Please ensure you are inside a Git repository."
        )
        return None, None, None, scope_title

    students = defaultdict(
        lambda: {
            "commits": 0,
            "added": 0,
            "deleted": 0,
            "active_days": set(),
        }
    )

    timeline_activity = defaultdict(lambda: defaultdict(int))
    student_logs = defaultdict(list)

    current_author = None
    current_date_str = None

    for line in raw_output.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("COMMIT|||"):
            parts = line.split("|||")

            if len(parts) < 5:
                current_author = None
                continue

            sha = parts[1].strip()
            author = parts[2].strip()
            date_str = parts[3].strip()
            message = parts[4].strip()

            # Ignore GitHub automation/bot commits.
            author_lower = author.lower()
            if "bot" in author_lower or "github-actions" in author_lower:
                current_author = None
                current_date_str = None
                continue

            current_author = author
            current_date_str = date_str

            students[current_author]["commits"] += 1
            students[current_author]["active_days"].add(date_str)
            students[current_author]["logs"] = student_logs[current_author]

            student_logs[current_author].append(
                (date_str, sha, message)
            )

            try:
                commit_date = datetime.datetime.strptime(
                    date_str,
                    "%Y-%m-%d",
                ).date()

                if timeline_mode == "monthly":
                    period_key = (
                        f"{commit_date.isocalendar()[0]}-"
                        f"W{commit_date.isocalendar()[1]:02d}"
                    )
                elif timeline_mode == "final":
                    period_key = commit_date.strftime("%Y-%m")
                else:
                    period_key = commit_date.strftime("%a (%b %d)")

                timeline_activity[period_key][current_author] += 1

            except Exception:
                pass

        elif current_author and not line.startswith("COMMIT|||"):
            parts = line.split()

            if len(parts) >= 2:
                added_text = parts[0]
                deleted_text = parts[1]

                # Binary files are shown by Git as "- -".
                if added_text.isdigit() and deleted_text.isdigit():
                    students[current_author]["added"] += int(added_text)
                    students[current_author]["deleted"] += int(
                        deleted_text
                    )

    return (
        students,
        timeline_activity,
        student_logs,
        scope_title,
    )


# =============================================================
# CHARTS
# =============================================================

def create_charts(students, timeline_activity, interval):
    """Create commit timeline and net LOC charts."""
    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(11, 3.8),
    )

    authors = list(students.keys())
    periods = sorted(timeline_activity.keys())

    # Commit timeline
    if periods and authors:
        for author in authors:
            counts = [
                timeline_activity[p].get(author, 0)
                for p in periods
            ]

            ax1.plot(
                periods,
                counts,
                marker="o",
                linewidth=2,
                label=author,
            )

        ax1.set_title(
            f"Commit Timeline ({interval.capitalize()})",
            fontsize=10,
            fontweight="bold",
        )
        ax1.set_ylabel("Commits")
        ax1.tick_params(axis="x", rotation=30)
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend(fontsize=8)
    else:
        ax1.text(
            0.5,
            0.5,
            "No commits found in this interval",
            ha="center",
            va="center",
        )
        ax1.set_axis_off()

    # Net LOC
    if authors:
        net_loc = [
            students[a]["added"] - students[a]["deleted"]
            for a in authors
        ]

        ax2.bar(
            authors,
            net_loc,
            width=0.45,
        )

        ax2.set_title(
            "Net Lines of Code Written",
            fontsize=10,
            fontweight="bold",
        )
        ax2.set_ylabel("LOC (Added - Deleted)")
        ax2.tick_params(axis="x", rotation=30)
        ax2.grid(axis="y", linestyle="--", alpha=0.5)
    else:
        ax2.text(
            0.5,
            0.5,
            "No LOC changes recorded",
            ha="center",
            va="center",
        )
        ax2.set_axis_off()

    plt.tight_layout()

    image_buffer = io.BytesIO()
    plt.savefig(
        image_buffer,
        format="png",
        dpi=200,
        bbox_inches="tight",
    )
    plt.close(fig)

    image_buffer.seek(0)

    return Image(
        image_buffer,
        width=500,
        height=175,
    )


# =============================================================
# PDF GENERATION
# =============================================================

def generate_pdf(
    interval="weekly",
    start_date=None,
    end_date=None,
    filename_date=None,
):
    repo_name, branch_name = get_repo_info()

    (
        students,
        timeline_activity,
        student_logs,
        scope_title,
    ) = get_git_metrics(
        interval=interval,
        start_date=start_date,
        end_date=end_date,
    )

    if students is None:
        return None

    if filename_date is None:
        filename_date = datetime.date.today()

    date_stamp = filename_date.strftime("%Y-%m-%d")

    if start_date and end_date:
        report_title = "Weekly Progress Report (Form-3)"
        doc_name = (
            f"{repo_name}_Weekly_Progress_Report_Form-3_"
            f"{date_stamp}.pdf"
        )
        chart_interval = "weekly"

    elif interval == "weekly":
        report_title = "Weekly Progress Report (Form-3)"
        doc_name = (
            f"{repo_name}_Weekly_Progress_Report_Form-3_"
            f"{date_stamp}.pdf"
        )
        chart_interval = "weekly"

    elif interval == "monthly":
        report_title = "Monthly Progress Report (Form-3)"
        doc_name = (
            f"{repo_name}_Monthly_Progress_Report_Form-3_"
            f"{date_stamp}.pdf"
        )
        chart_interval = "monthly"

    else:
        report_title = "Final Project Evaluation Report"
        doc_name = (
            f"{repo_name}_Final_Report_{date_stamp}.pdf"
        )
        chart_interval = "final"

    doc = SimpleDocTemplate(
        doc_name,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    college_style = ParagraphStyle(
        "CollegeStyle",
        parent=styles["Heading1"],
        fontSize=13.5,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
        spaceAfter=2,
    )

    dept_style = ParagraphStyle(
        "DeptStyle",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=6,
    )

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1A365D"),
        alignment=1,
        spaceAfter=5,
    )

    repo_style = ParagraphStyle(
        "RepoStyle",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )

    meta_style = ParagraphStyle(
        "MetaStyle",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=8,
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=7,
        spaceAfter=4,
    )

    sub_section_style = ParagraphStyle(
        "SubSectionStyle",
        parent=styles["Heading3"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2563EB"),
        spaceBefore=5,
        spaceAfter=2,
    )

    msg_style = ParagraphStyle(
        "MsgStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1E293B"),
    )

    meta_cell_style = ParagraphStyle(
        "MetaCellStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )

    marks_style = ParagraphStyle(
        "MarksStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )

    sig_block_style = ParagraphStyle(
        "SigBlockStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
        alignment=0,
    )

    story = []

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            f"<b>{html.escape(COLLEGE_NAME)}</b>",
            college_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>{html.escape(DEPARTMENT_NAME)}</b>",
            dept_style,
        )
    )

    story.append(
        Paragraph(
            f"<u><b>{report_title}</b></u>",
            title_style,
        )
    )

    story.append(Spacer(1, 3))

    # ---------------------------------------------------------
    # Repository metadata
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            f"<b>Project Repository:</b> "
            f"<font color='#2563EB'><b>"
            f"{html.escape(repo_name)}"
            f"</b></font>"
            f" &nbsp;|&nbsp; "
            f"<b>Branch:</b> "
            f"<code>{html.escape(branch_name)}</code>",
            repo_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Evaluation Window:</b> {scope_title}"
            f" &nbsp;|&nbsp; "
            f"<b>Generated On:</b> "
            f"{datetime.date.today().strftime('%B %d, %Y')}",
            meta_style,
        )
    )

    # ---------------------------------------------------------
    # Contribution summary
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "1. Individual Contribution Breakdown",
            section_style,
        )
    )

    total_commits = sum(
        data["commits"]
        for data in students.values()
    )

    table_data = [
        [
            "Student Name",
            "Commits (%)",
            "Lines Added",
            "Lines Deleted",
            "Net LOC",
            "Active Days",
        ]
    ]

    if students:
        sorted_students = sorted(
            students.items(),
            key=lambda item: (
                -item[1]["commits"],
                item[0].lower(),
            ),
        )

        for name, data in sorted_students:
            pct = (
                data["commits"] / total_commits * 100
                if total_commits
                else 0
            )

            net = data["added"] - data["deleted"]

            table_data.append(
                [
                    html.escape(name),
                    f"{data['commits']} ({pct:.1f}%)",
                    f"+{data['added']:,}",
                    f"-{data['deleted']:,}",
                    f"{net:,}",
                    f"{len(data['active_days'])} days",
                ]
            )
    else:
        table_data.append(
            [
                "No commits found in this period.",
                "-",
                "-",
                "-",
                "-",
                "-",
            ]
        )

    table = Table(
        table_data,
        colWidths=[120, 80, 80, 80, 80, 100],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1E293B"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "ALIGN",
                    (0, 1),
                    (0, -1),
                    "LEFT",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3.5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3.5,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC"),
                    ],
                ),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 6))

    # ---------------------------------------------------------
    # Charts
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "2. Visual Trends & Volume",
            section_style,
        )
    )

    chart_image = create_charts(
        students,
        timeline_activity,
        chart_interval,
    )

    story.append(chart_image)
    story.append(Spacer(1, 6))

    # ---------------------------------------------------------
    # Detailed commit logs
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "3. Detailed Commit Logs & Mentor Evaluation",
            section_style,
        )
    )

    if not student_logs:
        story.append(
            Paragraph(
                "<i>No commit logs found for this timeframe.</i>",
                styles["Normal"],
            )
        )
    else:
        sorted_logs = sorted(
            student_logs.items(),
            key=lambda item: item[0].lower(),
        )

        for student_name, logs in sorted_logs:
            student_section = []

            student_section.append(
                Paragraph(
                    f"<b>Student:</b> "
                    f"{html.escape(student_name)} — "
                    f"<i>{len(logs)} commit(s)</i>",
                    sub_section_style,
                )
            )

            log_table_data = [
                [
                    "Date",
                    "Hash",
                    "Commit Message",
                    "Mentor Marks (/10)",
                ]
            ]

            first_date, first_sha, first_msg = logs[0]

            log_table_data.append(
                [
                    Paragraph(
                        first_date,
                        meta_cell_style,
                    ),
                    Paragraph(
                        f"<code>{html.escape(first_sha)}</code>",
                        meta_cell_style,
                    ),
                    Paragraph(
                        html.escape(first_msg)
                        if first_msg
                        else "(No commit message)",
                        msg_style,
                    ),
                    Paragraph(
                        "<b>_____ / 10</b>",
                        marks_style,
                    ),
                ]
            )

            for date_val, sha_val, msg_val in logs[1:]:
                log_table_data.append(
                    [
                        Paragraph(
                            date_val,
                            meta_cell_style,
                        ),
                        Paragraph(
                            f"<code>{html.escape(sha_val)}</code>",
                            meta_cell_style,
                        ),
                        Paragraph(
                            html.escape(msg_val)
                            if msg_val
                            else "(No commit message)",
                            msg_style,
                        ),
                        "",
                    ]
                )

            num_rows = len(log_table_data)

            log_table = Table(
                log_table_data,
                colWidths=[65, 50, 335, 90],
                repeatRows=1,
            )

            style_commands = [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#475569"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "LEFT",
                ),
                (
                    "ALIGN",
                    (3, 0),
                    (3, -1),
                    "CENTER",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2.5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2.5,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (2, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC"),
                    ],
                ),
            ]

            if num_rows > 1:
                style_commands.extend(
                    [
                        (
                            "SPAN",
                            (3, 1),
                            (3, num_rows - 1),
                        ),
                        (
                            "VALIGN",
                            (3, 1),
                            (3, num_rows - 1),
                            "MIDDLE",
                        ),
                        (
                            "BACKGROUND",
                            (3, 1),
                            (3, num_rows - 1),
                            colors.HexColor("#FEF3C7"),
                        ),
                    ]
                )

            log_table.setStyle(
                TableStyle(style_commands)
            )

            student_section.append(log_table)
            student_section.append(Spacer(1, 5))

            story.append(
                KeepTogether(student_section)
            )

    # ---------------------------------------------------------
    # Signatures
    # ---------------------------------------------------------

    story.append(Spacer(1, 16))

    mentor_cell = [
        Paragraph(
            "<b>Name:</b> ___________________________",
            sig_block_style,
        ),
        Paragraph(
            "<b>Designation:</b> Project Mentor",
            sig_block_style,
        ),
        Spacer(1, 6),
        Paragraph(
            "<b>Signature:</b> ________________________",
            sig_block_style,
        ),
    ]

    coordinator_cell = [
        Paragraph(
            "<b>Name:</b> ___________________________",
            sig_block_style,
        ),
        Paragraph(
            "<b>Designation:</b> Lab Coordinator",
            sig_block_style,
        ),
        Spacer(1, 6),
        Paragraph(
            "<b>Signature:</b> ________________________",
            sig_block_style,
        ),
    ]

    sig_table = Table(
        [[mentor_cell, coordinator_cell]],
        colWidths=[270, 270],
    )

    sig_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (0, -1),
                    0,
                ),
                (
                    "LEFTPADDING",
                    (1, 0),
                    (1, -1),
                    40,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(KeepTogether(sig_table))

    doc.build(story)

    print(
        f"\n[SUCCESS] Generated: {doc_name}"
    )
    print(
        f" -> Found {len(students)} student(s) "
        f"and {total_commits} total commits."
    )

    return doc_name


# =============================================================
# LAST 4 COMPLETED THURSDAY-TO-THURSDAY WEEKS
# =============================================================

def get_last_four_weeks():
    """
    Return the four most recent Thursday-to-Thursday weekly periods.

    Example when today is Sunday, 13 Sep 2026:
        13 Aug -> 20 Aug
        20 Aug -> 27 Aug
        27 Aug -> 03 Sep
        03 Sep -> 10 Sep
    """

    today = datetime.date.today()

    # Monday=0 ... Thursday=3
    days_since_thursday = (
        today.weekday() - 3
    ) % 7

    latest_thursday = (
        today
        - datetime.timedelta(days=days_since_thursday)
    )

    weeks = []

    for index in range(4):
        end_date = (
            latest_thursday
            - datetime.timedelta(days=index * 7)
        )
        start_date = (
            end_date
            - datetime.timedelta(days=7)
        )

        weeks.append(
            (start_date, end_date)
        )

    weeks.reverse()

    return weeks


def generate_last_four_weeks():
    """Generate four separate historical weekly Form-3 PDFs."""
    print("\nGenerating last 4 weekly Form-3 reports...\n")

    generated_files = []

    for number, (start_date, end_date) in enumerate(
        get_last_four_weeks(),
        start=1,
    ):
        print(
            f"[{number}/4] "
            f"{start_date.strftime('%d %b %Y')} -> "
            f"{end_date.strftime('%d %b %Y')}"
        )

        filename = generate_pdf(
            interval="weekly",
            start_date=start_date,
            end_date=end_date,
            filename_date=end_date,
        )

        if filename:
            generated_files.append(filename)

    print("\n[SUCCESS] Last 4 weekly reports generated:")
    for filename in generated_files:
        print(f" - {filename}")

    return generated_files


# =============================================================
# COMMAND LINE
# =============================================================

def print_usage():
    print(
        """
Usage:
    python generate_report.py weekly
        Generate the current rolling 7-day report.

    python generate_report.py last4
        Generate the last 4 separate Thursday-to-Thursday
        weekly reports.

    python generate_report.py monthly
        Generate the current 30-day report.

    python generate_report.py final
        Generate the complete project lifecycle report.
"""
    )


if __name__ == "__main__":
    chosen_interval = (
        sys.argv[1].lower()
        if len(sys.argv) > 1
        else "weekly"
    )

    if chosen_interval == "last4":
        generate_last_four_weeks()

    elif chosen_interval in {
        "weekly",
        "monthly",
        "final",
    }:
        generate_pdf(chosen_interval)

    else:
        print(f"[ERROR] Unknown option: {chosen_interval}")
        print_usage()
        sys.exit(1)
#'''

# path = Path("/mnt/data/generate_report_final.py")
# path.write_text(code, encoding="utf-8")
# py_compile.compile(str(path), doraise=True)

# print(f"Created and syntax-checked: {path}")