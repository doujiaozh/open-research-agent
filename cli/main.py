import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.markdown import Markdown
from agent.loop import run_agent
from agent.memory import list_runs

console = Console()

def cmd_research(args):
    result = run_agent(args.topic, auto_confirm=args.yes)
    console.print(Markdown(result))

def cmd_history(args):
    for row in list_runs(args.limit):
        console.print("[" + str(row[0]) + "] " + row[1] + "  " + row[2])

def main():
    parser = argparse.ArgumentParser(prog="ora", description="Open Research Agent")
    sub = parser.add_subparsers(dest="command")

    p1 = sub.add_parser("research", help="研究一个主题并生成报告")
    p1.add_argument("topic", help="研究主题")
    p1.add_argument("-y", "--yes", action="store_true", help="自动确认危险操作")
    p1.set_defaults(func=cmd_research)

    p2 = sub.add_parser("history", help="查看历史任务")
    p2.add_argument("--limit", type=int, default=10)
    p2.set_defaults(func=cmd_history)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()