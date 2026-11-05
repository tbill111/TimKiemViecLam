"""Print PostgreSQL BI view data for comparison with the Superset dashboard."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(REPOSITORY_ROOT / ".env")

VIEWS = (
    ("vw_candidate_skills", "Kỹ năng ứng viên"),
    ("vw_salary_trends", "Xu hướng lương"),
    ("vw_ai_matching_stats", "Thống kê AI Matching"),
)
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

console = Console()
error_console = Console(stderr=True)


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        error_console.print(
            "[red]Thiếu DATABASE_URL. Hãy cấu hình biến này trong file .env ở thư mục gốc.[/red]"
        )
        return 1

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            for view_name, title in VIEWS:
                result = connection.execute(text(f"SELECT * FROM {view_name}"))
                table = Table(title=title)
                for column in result.keys():
                    table.add_column(column, overflow="fold")
                rows = result.fetchall()
                table.title = f"{title} ({len(rows)} dòng)"
                for row in rows:
                    table.add_row(*(str(value) if value is not None else "NULL" for value in row))
                if not rows:
                    table.add_row(*("(không có dữ liệu)" if index == 0 else "" for index in range(len(result.keys()))))
                console.print(table)
    except SQLAlchemyError as exc:
        error_console.print(f"[red]Không thể truy vấn các BI View: {exc}[/red]")
        return 1
    finally:
        engine.dispose()

    console.print(
        "\n[green]✅ Dữ liệu truy vấn thành công. "
        "Vui lòng đối chiếu các bảng trên với biểu đồ trên Superset Dashboard.[/green]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
