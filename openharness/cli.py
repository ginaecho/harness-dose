"""``openharness`` command line — run the demo, print cards, emit a dashboard."""

from __future__ import annotations

import argparse
import os
import sys


def _load_demo():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    from examples import demo_session  # noqa: E402
    return demo_session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="openharness",
        description="See the harness, share the harness, prove the harness works.")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("demo", help="run the demo session and write dashboard.html")
    p_dash = sub.add_parser("dashboard", help="write the dashboard from the demo sessions")
    p_dash.add_argument("-o", "--out", default="dashboard.html")

    args = parser.parse_args(argv)
    demo = _load_demo()

    if args.cmd in (None, "demo"):
        demo.main()
        return 0

    if args.cmd == "dashboard":
        from openharness.card import build_cards
        from openharness.dashboard import render_dashboard
        from openharness.harness import Harness
        from modules import ALL
        obs = []
        for sid, events in demo.sessions().items():
            h = Harness(ALL, session_id=sid)
            h.run(events)
            obs.extend(h.trace.observations)
        cards = build_cards(ALL, obs)
        with open(args.out, "w") as f:
            f.write(render_dashboard(cards.values()))
        print(f"wrote {args.out}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
