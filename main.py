"""
CLI entry point.

Example:
    python main.py --city "Birmingham" --category "care home" --max-results 20 --no-website-only
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lead_generator"))

from graph.pipeline import run_pipeline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="UK B2B lead generator")
    parser.add_argument("--city", required=True, help="e.g. Birmingham")
    parser.add_argument("--category", required=True, help="e.g. care home")
    parser.add_argument("--country", default="UK")
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--no-website-only", action="store_true",
                         help="Only keep businesses with no website detected")
    args = parser.parse_args()

    final_state = run_pipeline(
        city=args.city,
        category=args.category,
        country=args.country,
        max_results=args.max_results,
        no_website_only=args.no_website_only,
    )

    print("\n--- PIPELINE LOG ---")
    for line in final_state["log"]:
        print(line)

    print(f"\nTotal leads processed: {len(final_state['leads'])}")


if __name__ == "__main__":
    main()
