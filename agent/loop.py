import os, re

from rich.console import Console

from .schema import AgentState, Step, Decision

from .llm import decide, summarize, write_report

from .tools import TOOLS, DANGEROUS

from .safety import confirm

from .memory import save_run



console = Console()

MAX_STEPS = int(os.getenv("MAX_STEPS", "15"))



STOPWORDS = set([

    "最新", "进展", "研究", "数据", "报告", "消息", "动态", "新闻", "信息",

    "中国", "全球", "市场", "产业", "行业", "领域", "方面", "情况", "问题",

    "分析", "观察", "解读", "深度", "全部", "内容", "相关", "有关", "关于",

    "百度", "百科", "知乎", "新浪", "腾讯", "搜狐", "网易", "今日", "头条",

    "我们", "他们", "什么", "为什么", "如何", "怎样",

])





def _build_candidates(goal, first_obs, max_n=5):

    candidates = []

    seen = set()

    titles = re.findall(r"-\s*([^\n]+)", first_obs)

    for t in titles:

        for w in re.findall(r"[\u4e00-\u9fa5]{2,6}", t):

            w = w.strip()

            if len(w) < 2:

                continue

            if w in STOPWORDS:

                continue

            if w in goal:

                continue

            q = goal + " " + w

            if q in seen:

                continue

            seen.add(q)

            candidates.append(q)

            if len(candidates) >= max_n:

                return candidates

    return candidates





def run_agent(goal, auto_confirm=False):

    state = AgentState(goal=goal)

    console.print("[bold green]目标:[/bold green] " + goal + "\n")



    console.print("[cyan]初始搜索[/cyan] -> web_search")

    console.print("  查询: " + goal)

    try:

        obs0 = TOOLS["web_search"](goal, 5)

    except Exception as e:

        obs0 = "工具错误: " + str(e)

    console.print("  结果: " + obs0[:200].replace("\n", " ") + "...")

    state.history.append(Step(

        step=0, action="web_search",

        args={"query": goal, "top_k": 5}, observation=obs0,

    ))



    candidates = _build_candidates(goal, obs0)

    console.print("\n[cyan]候选 query:[/cyan]")

    for i, c in enumerate(candidates):

        console.print("  " + str(i + 1) + ". " + c)

    console.print("")



    cand_idx = 0



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

                    step=step, action=decision.action,

                    args=decision.args, observation=obs

                ))

                continue



        if decision.action == "web_search":

            if cand_idx >= len(candidates):

                console.print("  [yellow](候选 query 用完，强制 final)[/yellow]")

                observations = [s.observation for s in state.history]

                try:

                    result = write_report(goal, observations)

                except Exception as e:

                    return "生成报告失败: " + str(e)

                console.print("\n[bold green]完成[/bold green]\n")

                save_run(goal, [s.dict() for s in state.history], result)

                return result

            forced_q = candidates[cand_idx]

            console.print("  [yellow](强制使用候选 query: " + forced_q + ")[/yellow]")

            decision.args = {"query": forced_q, "top_k": 5}

            cand_idx += 1



        try:

            obs = TOOLS[decision.action](**decision.args)

        except Exception as e:

            obs = "工具错误: " + str(e)



        preview = obs[:200].replace("\n", " ")

        console.print("  结果: " + preview + "...")



        state.history.append(Step(

            step=step, action=decision.action,

            args=decision.args, observation=obs

        ))



        if len(state.history) % 3 == 0:

            try:

                state.short_memory.append(summarize(obs))

            except Exception:

                pass



    return "达到最大步数，未完成"

