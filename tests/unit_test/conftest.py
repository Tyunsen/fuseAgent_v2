import os
import sys

import pytest
from dotenv import load_dotenv

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

print(f"Added to sys.path: {project_root}")


def load_test_environment():
    """Loads environment variables from .env.test located in the same directory as this conftest.py."""
    # Assuming .env.test is in tests/unit_test/ alongside conftest.py
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env.test")
    print(f"\n--- Attempting to load environment variables from: {dotenv_path} ---")
    # override=True ensures that variables from .env.test take precedence
    loaded = load_dotenv(dotenv_path=dotenv_path, override=True, verbose=True)
    if loaded:
        print(f"Successfully loaded: {dotenv_path}")
    else:
        abs_dotenv_path = os.path.abspath(dotenv_path)
        print(f"Warning: .env.test file not found or empty at {abs_dotenv_path}")


# --- Pytest Hook to Load Environment *Before* Collection ---
def pytest_configure(config):
    """
    Pytest hook called after command line options are parsed and before
    test collection begins. This is the right place to load environment
    variables needed for module-level decorators like skipif.
    """
    config.option.log_cli = True
    config.option.log_cli_level = "INFO"
    print("\npytest_configure: Loading test environment...")
    load_test_environment()


@pytest.fixture
def trace_reference_rows():
    return [
        {
            "source_row_id": "row_1",
            "text": "2026年3月，阿布扎比举行联合演训。",
            "snippet": "2026年3月，阿布扎比举行联合演训。",
            "document_id": "doc_1",
            "document_name": "briefing-1.md",
            "preview_title": "briefing-1.md - p.1",
            "page_idx": 0,
            "section_label": "阿布扎比",
            "chunk_ids": ["chunk_1"],
            "paragraph_precise": True,
            "md_source_map": [0, 8],
            "pdf_source_map": [],
        },
        {
            "source_row_id": "row_2",
            "text": "伊朗代表团参与了本次演训准备会议。",
            "snippet": "伊朗代表团参与了本次演训准备会议。",
            "document_id": "doc_2",
            "document_name": "briefing-2.md",
            "preview_title": "briefing-2.md - p.2",
            "page_idx": 1,
            "section_label": "准备会议",
            "chunk_ids": ["chunk_2"],
            "paragraph_precise": False,
            "md_source_map": [10, 14],
            "pdf_source_map": [],
        },
    ]


@pytest.fixture
def trace_conclusions():
    return [
        {
            "id": "conclusion_1",
            "title": "时间结论 1",
            "statement": "2026年3月在阿布扎比举行了联合演训。",
            "source_row_ids": ["row_1"],
            "locator_quality": "precise",
            "time_label": "2026-03",
            "place_label": "阿布扎比",
            "focus_entity": None,
        }
    ]
