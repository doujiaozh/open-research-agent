from rich.console import Console
from rich.prompt import Confirm

console = Console()

def confirm(action, args):
    console.print("\n[yellow]需要确认[/yellow] action=" + action)
    for k, v in args.items():
        preview = str(v)[:200]
        console.print("  " + k + ": " + preview)
    return Confirm.ask("是否执行？", default=False)