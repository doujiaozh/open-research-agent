import os, re

from rich.console import Console

from .schema import AgentState, Step, Decision

from .llm import decide, summarize, write_report

from .tools import TOOLS, DANGEROUS

from .safety import confirm

from .memory import save_run



console = Console()

MAX_STEPS = int(os.getenv("MAX_STEPS", "15"))



STOP_WORDS = set([

    "最新", "进展", "研究", "消息", "动态", "新闻", "信息", "报告",

    "分析", "解读", "观察", "深度", "相关", "有关", "关于", "数据",

    "中国", "全球", "市场", "产业", "行业", "领域", "方面", "情况",

    "问题", "内容", "全部", "百度", "百科", "知乎", "新浪", "腾讯",

    "搜狐", "网易", "今日", "头条", "我们", "他们", "什么", "如何",

])



KEYWORD_POOL = [

    "2026", "2025", "量产", "技术路线", "成本", "产能",

    "中科院", "宁德时代", "比亚迪", "丰田", "三星",

    "硫化物", "氧化物", "聚合物", "能量密度", "固态电解质",

    "产业链", "政策", "专利", "投资",

]





def _extract_core(goal):

    parts = re.findall(r"[\u4e00-\u9fa5]+", goal)

    all_terms = []

    for p in parts:

        temp = p

        for sw in sorted(STOP_WORDS, key=len, reverse=True):

            temp = temp.replace(sw, "|")

        for seg in temp.split("|"):

            seg = seg.strip()

            if len(seg) >= 2:

                all_terms.append(seg)

    if not all_terms:

        return goal

    return max(all_terms, key=len)





def _build_candidates(goal, max_n=5):

    core = _extract_core(goal)

    candidates = []

    for kw in KEYWORD_POOL:

        if kw in goal or kw in core:

            continue

        candidates.append('"' + core + '" ' + kw)

        if len(candidates) >= max_n:

            break

    return candidates





def run_agent(goal, auto_confirm=False, on_event=None):

    """on_event(type, data) 会在关键节点被调用, 用于流式推送到 Web UI"""

    def emit(t, d=None):

        if on_event:

            try:

                on_event(t, d or {})

            except Exception:

                pass



    state = AgentState(goal=goal)

    console.print("[bold green]目标:[/bold green] " + goal + "\n")

    emit("start", {"goal": goal})



    console.print("[cyan]初始搜索[/cyan] -> web_search")

    console.print("  查询: " + goal)

    emit("step", {"step": 0, "action": "web_search", "query": goal})

    try:

        obs0 = TOOLS["web_search"](goal, 5)

    except Exception as e:

        obs0 = "工具错误: " + str(e)

    console.print("  结果: " + obs0[:200].replace("\n", " ") + "...")

    emit("result", {"step": 0, "preview": obs0[:300]})

    state.history.append(Step(

        step=0, action="web_search",

        args={"query": goal, "top_k": 5}, observation=obs0,

    ))



    candidates = _build_candidates(goal)

    console.print("\n[cyan]候选 query:[/cyan]")

    for i, c in enumerate(candidates):

        console.print("  " + str(i + 1) + ". " + c)

    emit("candidates", {"list": candidates})

    console.print("")



    cand_idx = 0



    for step in range(MAX_STEPS):

        try:

            raw = decide(state.dict())

            decision = Decision(**raw)

        except Exception as e:

            console.print("[red]解析决策失败:[/red] " + str(e))

            emit("error", {"message": str(e)})

            return "决策失败: " + str(e)



        console.print("[cyan]第 " + str(step + 1) + " 步[/cyan] -> " + decision.action)

        if decision.thought:

            console.print("  思考: " + decision.thought)

        emit("step", {"step": step + 1, "action": decision.action, "thought": decision.thought})



        if decision.done or decision.action == "final":

            console.print("\n[cyan]正在生成报告...[/cyan]")

            emit("status", {"message": "正在生成报告..."})

            observations = [s.observation for s in state.history]

            if not observations:

                return "未收集到任何资料，无法生成报告"

            try:

                result = write_report(goal, observations)

            except Exception as e:

                emit("error", {"message": str(e)})

                return "生成报告失败: " + str(e)

            console.print("\n[bold green]完成[/bold green]\n")

            save_run(goal, [s.dict() for s in state.history], result)

            emit("done", {"report": result})

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

                emit("status", {"message": "候选 query 用完, 生成报告"})

                observations = [s.observation for s in state.history]

                try:

                    result = write_report(goal, observations)

                except Exception as e:

                    emit("error", {"message": str(e)})

                    return "生成报告失败: " + str(e)

                console.print("\n[bold green]完成[/bold green]\n")

                save_run(goal, [s.dict() for s in state.history], result)

                emit("done", {"report": result})

                return result

            forced_q = candidates[cand_idx]

            console.print("  [yellow](强制使用候选 query: " + forced_q + ")[/yellow]")

            emit("status", {"message": "搜索: " + forced_q})

            decision.args = {"query": forced_q, "top_k": 5}

            cand_idx += 1



        try:

            obs = TOOLS[decision.action](**decision.args)

        except Exception as e:

            obs = "工具错误: " + str(e)



        preview = obs[:200].replace("\n", " ")

        console.print("  结果: " + preview + "...")

        emit("result", {"step": step + 1, "preview": obs[:300]})



        state.history.append(Step(

            step=step, action=decision.action,

            args=decision.args, observation=obs

        ))



        if len(state.history) % 3 == 0:

            try:

                state.short_memory.append(summarize(obs))

            except Exception:

                pass



    emit("error", {"message": "达到最大步数"})

    return "达到最大步数，未完成"

