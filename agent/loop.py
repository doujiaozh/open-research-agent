import os
from rich.console import Console
from .schema import AgentState, Step, Decision
from .llm import decide, summarize, write_report
from .tools import TOOLS, DANGEROUS
from .safety import confirm
from .memory import save_run

console = Console()
MAX_STEPS = int(os.getenv("MAX_STEPS", "15"))
MAX_SEARCHES = int(os.getenv("MAX_SEARCHES", "5"))


def run_agent(goal, auto_confirm=False):
    state = AgentState(goal=goal)
    console.print("[bold green]目标:[/bold green] " + goal + "\n")

    visited_queries = set()
    visited_urls = set()
    search_count = 0

    # 第 0 步：强制首次搜索，绕过 LLM，直接把 goal 作为 query
    console.print("[cyan]初始搜索[/cyan] -> web_search")
    console.print("  查询: " + goal)
    try:
        obs0 = TOOLS["web_search"](goal, 5)
    except Exception as e:
        obs0 = "工具错误: " + str(e)
    console.print("  结果: " + obs0[:200].replace("\n", " ") + "...")
    state.history.append(Step(
        step=0,
        action="web_search",
        args={"query": goal, "top_k": 5},
        observation=obs0,
    ))
    visited_queries.add(goal)
    search_count += 1

    for step in range(MAX_STEPS):
        try:
            raw = decide(state.dict())
            decision = Decision(**raw)
        except Exception as e:
            console.print("[red]解析决策失败:[/red] " + str(e))
            return "决策失败: " + str(e)

        console.print("[cyan]第 " + str(step + 1) + " 步[/cyan] -> " + decision.action)
        if decision.thought:
            console.print("  思考: " + decision.thought)

        if decision.done or decision.action == "final":
            console.print("\n[cyan]正在生成报告...[/cyan]")
            observations = [s.observation for s in state.history]
            if not observations:
                return "未收集到任何资料，无法生成报告"
            try:
                result = write_report(goal, observations)
            except Exception as e:
                return "生成报告失败: " + str(e)
            console.print("\n[bold green]完成[/bold green]\n")
            save_run(goal, [s.dict() for s in state.history], result)
            return result

        if decision.action in DANGEROUS and not auto_confirm:
            if not confirm(decision.action, decision.args):
                obs = "用户拒绝执行"
                state.history.append(Step(
                    step=step,
                    action=decision.action,
                    args=decision.args,
                    observation=obs
                ))
                continue

        # query 为空或太短，用 goal 顶替
        if decision.action == "web_search":
            q = (decision.args or {}).get("query", "")
            if not q or len(str(q).strip()) < 3:
                decision.args = {"query": goal, "top_k": 5}
                console.print("  [yellow](query 为空，已用目标顶替)[/yellow]")

        # 去重 + 搜索次数上限
        if decision.action == "web_search":
            q = (decision.args or {}).get("query", "")
            if q in visited_queries:
                console.print("  [yellow](重复 query, 跳过)[/yellow]")
                state.history.append(Step(
                    step=step,
                    action="web_search",
                    args=decision.args,
                    observation="重复 query, 已跳过"
                ))
                continue
            if search_count >= MAX_SEARCHES:
                console.print("  [yellow](搜索已达 " + str(MAX_SEARCHES) + " 次上限, 强制 final)[/yellow]")
                observations = [s.observation for s in state.history]
                if not observations:
                    return "未收集到任何资料，无法生成报告"
                try:
                    result = write_report(goal, observations)
                except Exception as e:
                    return "生成报告失败: " + str(e)
                console.print("\n[bold green]完成[/bold green]\n")
                save_run(goal, [s.dict() for s in state.history], result)
                return result
            visited_queries.add(q)
            search_count += 1

        elif decision.action == "fetch_url":
            u = (decision.args or {}).get("url", "")
            if u in visited_urls:
                console.print("  [yellow](重复 url, 跳过)[/yellow]")
                state.history.append(Step(
                    step=step,
                    action="fetch_url",
                    args=decision.args,
                    observation="重复 url, 已跳过"
                ))
                continue
            visited_urls.add(u)

        try:
            obs = TOOLS[decision.action](**decision.args)
        except Exception as e:
            obs = "工具错误: " + str(e)

        preview = obs[:200].replace("\n", " ")
        console.print("  结果: " + preview + "...")

        state.history.append(Step(
            step=step,
            action=decision.action,
            args=decision.args,
            observation=obs
        ))

        if len(state.history) % 3 == 0:
            try:
                state.short_memory.append(summarize(obs))
            except Exception:
                pass

    return "达到最大步数，未完成"