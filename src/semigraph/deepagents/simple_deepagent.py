"""Interactive Vector/Graph retrieval demo; add --retrieve-only to skip synthesis."""

import argparse
import json

from semigraph.deepagents import Deepagent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="Question; otherwise ask interactively")
    parser.add_argument("--tool", choices=("vector", "graph"), default="vector")
    parser.add_argument("--retrieve-only", action="store_true")
    args = parser.parse_args()
    question = (args.query or input("Ask Deep Agent: ")).strip()
    if not question:
        print("No question entered.")
        return

    result = Deepagent(question, args.tool, FullAnswer=not args.retrieve_only)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
