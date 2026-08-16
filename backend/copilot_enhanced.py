"""
NEXUS-X Enhanced Copilot Engine v2.0

Implements comprehensive conversational AI with:
- Intent recognition (40+ patterns)
- Conversation memory (pronouns, entities)
- Multiple interaction modes
- Evidence-based reasoning
- Structured responses
- Fallback to deterministic intelligence when LLM unavailable
"""

import json
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import re


class ConversationContext:
    """Track conversation state across messages."""
    
    def __init__(self):
        self.entity_history = {
            'tasks': [],
            'risks': [],
            'team_members': [],
            'deadlines': [],
            'budgets': [],
            'scenarios': []
        }
        self.last_mentioned = {
            'task': None,
            'risk': None,
            'team_member': None,
            'deadline': None
        }
        self.mode = 'general'  # general, pm, student, employee, technical, manager
        self.question_count = 0
        
    def resolve_pronoun(self, pronoun: str, default=None):
        """Resolve pronouns like 'it', 'that', 'this', 'they', etc."""
        pronoun = (pronoun or '').lower().strip()
        
        if pronoun in ('it', 'that', 'this', 'the task', 'the previous one', 'the above'):
            return self.last_mentioned.get('task')
        elif pronoun in ('they', 'them', 'those'):
            return self.last_mentioned.get('task')  # or multiple tasks
        elif pronoun in ('the risk', 'it', 'that'):
            return self.last_mentioned.get('risk')
        elif pronoun in ('the developer', 'the person', 'they'):
            return self.last_mentioned.get('team_member')
        
        return default
    
    def update_from_message(self, message: str):
        """Extract and update entity context from message."""
        self.question_count += 1
        
        # Extract task references (T1, T2, etc.)
        task_refs = re.findall(r'\b([Tt]\d+)\b', message)
        if task_refs:
            self.last_mentioned['task'] = task_refs[0]
        
        # Extract common terms
        if any(w in message.lower() for w in ['risk', 'issue', 'problem', 'concern']):
            # Try to extract specific risk name
            pass
        
        if any(w in message.lower() for w in ['deadline', 'time', 'when', 'days']):
            self.last_mentioned['deadline'] = 'current_deadline'


class CopilotIntentClassifier:
    """Classify user intent from natural language with priority ordering."""
    
    @staticmethod
    def classify(message: str, mode: str = 'general') -> Tuple[str, float]:
        """
        Classify intent with confidence score.
        Returns (intent_type, confidence)
        
        IMPORTANT: More specific patterns checked BEFORE generic ones!
        """
        m = (message or '').lower().strip()
        
        # === GREETINGS (very specific) ===
        if any(k in m for k in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return ('greeting', 0.95)
        
        if any(k in m for k in ['help', 'what can you do', 'what can i ask', 'capabilities']):
            return ('help', 0.95)
        
        if any(k in m for k in ['who are you', 'what is nexus', 'about you']):
            return ('about_copilot', 0.95)
        
        # === TASK-FOCUSED (specific patterns first) ===
        if any(k in m for k in ['first task', 'start with', 'do first', 'first', 'next task', 'which task should', 'what should we do', 'should i do first', 'should we do first']):
            return ('task_priority', 0.95)
        
        if 'depend' in m or any(k in m for k in ['what does', 'what must', 'prerequisite', 'requires']):
            return ('task_dependencies', 0.90)
        
        # === BLOCKER (check BEFORE generic "what is") ===
        if any(k in m for k in ['blocker', 'blocked', 'blocking', 'stuck', 'what is blocking', "what's blocking"]):
            return ('blockers', 0.95)
        
        # === RISK-FOCUSED (check specific patterns BEFORE generic 'risk') ===
        if any(k in m for k in ['biggest risk', 'highest risk', 'most dangerous', 'top risk', 'major risk']):
            return ('risk_severity', 0.95)
        
        if 'why' in m and any(w in m for w in ['risk', 'behind', 'late', 'slow', 'at risk']):
            return ('risk_analysis', 0.92)
        
        if any(k in m for k in ['mitigation', 'reduce risk', 'address', 'fix', 'solve', 'prevent']):
            return ('risk_mitigation', 0.90)
        
        # === SCHEDULE/DEADLINE (check specific patterns first) ===
        if any(k in m for k in ['deadline', 'on time', 'finish on time', 'can we meet', 'feasible', 'feasibility']):
            return ('deadline_feasibility', 0.92)
        
        if 'critical path' in m or 'critical-path' in m:
            return ('critical_path', 0.95)
        
        if any(k in m for k in ['delay', 'slip', 'late', 'postpone']):
            return ('schedule_impact', 0.88)
        
        # === TEAM & CAPACITY (specific patterns first) ===
        if any(k in m for k in ['who should', 'who can', 'best person', 'assign', 'who should handle', 'best member']):
            return ('team_assignment', 0.94)
        
        if any(k in m for k in ['workload', 'capacity', 'overload', 'overloaded', 'utilization', 'available']):
            return ('team_capacity', 0.92)
        
        if 'team' in m and any(k in m for k in ['who is', 'members', 'skills', 'on the']):
            return ('team_info', 0.90)
        
        # === BUDGET & COST ===
        if any(k in m for k in ['budget', 'cost', 'expensive', 'money', 'financial', 'within budget', 'over budget']):
            return ('budget', 0.94)
        
        # === WHAT-IF (very specific) ===
        if 'what if' in m or 'what happens if' in m or any(k in m for k in ['suppose', 'assume', 'scenario']):
            return ('what_if', 0.96)
        
        # === MANAGEMENT (check before generic) ===
        if any(k in m for k in ['executive', 'management', 'tell my manager', 'escalate', 'present to', 'executive summary']):
            return ('management_summary', 0.95)
        
        # === PLANNING & ACTION (check before generic) ===
        if any(k in m for k in ['today', 'this week', 'action plan', 'next steps', 'should i', 'should we']):
            return ('action_plan', 0.90)
        
        if 'priority' in m and any(k in m for k in ['what', 'what is', 'top', 'highest']):
            return ('action_plan', 0.88)
        
        # === STUDENT MODE ===
        if any(k in m for k in ['viva', 'exam', 'presentation', 'student', 'college', 'university', 'prepare me']):
            return ('student_mode', 0.95)
        
        # === TECHNICAL ===
        if any(k in m for k in ['architecture', 'database', 'api', 'security', 'technology', 'deployment', 'technical']):
            return ('technical', 0.92)
        
        # === TESTING & QA ===
        if any(k in m for k in ['test', 'qa', 'quality', 'verify', 'acceptance', 'testing']):
            return ('testing', 0.90)
        
        # === COMPARISON ===
        if any(k in m for k in ['compare', 'versus', 'vs', 'which is', 'better', 'worse', 'difference']):
            return ('comparison', 0.90)
        
        # === HEALTH & STATUS ===
        if any(k in m for k in ['health', 'status', 'how is', 'how are we', 'doing', 'progress']):
            return ('project_health', 0.92)
        
        # === FOLLOW-UP INDICATORS ===
        if any(k in m for k in ['by how much', 'by how many', 'in how many', 'in how long']):
            return ('quantitative_follow_up', 0.88)
        
        # === GENERIC EXPLANATION (lower priority) ===
        if any(k in m for k in ['explain', 'explain the', 'tell me about', 'describe']):
            return ('explanation', 0.75)
        
        # === GENERIC KNOWLEDGE (lowest priority) ===
        if any(k in m for k in ['what is', 'what are', 'how does', 'how to']):
            return ('general_knowledge', 0.65)
        
        return ('general', 0.6)


class ResponseFormatter:
    """Format responses with structure and clarity."""
    
    @staticmethod
    def format_answer(answer: str, mode: str = 'general') -> str:
        """
        Enhance answer formatting based on mode.
        """
        if mode == 'student':
            return answer  # Already structured for viva/presentation
        elif mode == 'technical':
            return f"**Technical Details:**\n{answer}"
        elif mode == 'manager':
            return f"**Executive Summary:**\n{answer}"
        else:
            return answer
    
    @staticmethod
    def format_evidence(evidence: Dict[str, Any]) -> str:
        """Format evidence section."""
        if not evidence:
            return ""
        
        lines = ["**EVIDENCE:**"]
        for key, value in evidence.items():
            if value is not None:
                lines.append(f"- {key}: **{value}**")
        return "\n".join(lines)
    
    @staticmethod
    def format_recommendation(recommendation: str, why: str = "", impact: str = "", action: str = "") -> str:
        """Format recommendation with structure."""
        lines = [f"**RECOMMENDATION:** {recommendation}"]
        if why:
            lines.append(f"\n**WHY:** {why}")
        if impact:
            lines.append(f"\n**IMPACT:** {impact}")
        if action:
            lines.append(f"\n**ACTION:** {action}")
        return "\n".join(lines)


def extract_entities_from_message(message: str, project_state: Dict) -> Dict[str, List[str]]:
    """Extract referenced tasks, risks, team members from message."""
    m = message.lower()
    entities = {'tasks': [], 'risks': [], 'team_members': []}
    
    # Find task references
    task_refs = re.findall(r'[Tt](\d+)', message)
    if task_refs:
        by_key = {t['task_key']: t for t in project_state.get('tasks', [])}
        for ref in task_refs:
            key = f'T{ref}'
            if key in by_key:
                entities['tasks'].append(key)
    
    # Find risk references (partial match)
    risks = project_state.get('risks', [])
    for risk in risks:
        if risk['name'].lower() in m:
            entities['risks'].append(risk['name'])
    
    # Find team member references
    team = project_state.get('team', [])
    for member in team:
        if member['name'].lower() in m:
            entities['team_members'].append(member['name'])
    
    return entities


def format_project_summary(s: Dict) -> str:
    """Generate comprehensive project summary."""
    if not s:
        return "No project data available."
    
    summary = f"""
**PROJECT SUMMARY: {s.get('project', {}).get('name', 'Unnamed')}**

**Health:** {s.get('health', 0)}% ({s.get('health_status', 'UNKNOWN')})
**Progress:** {s.get('progress', 0)}%
**Critical Path:** {' → '.join(s.get('critical_path', []))} ({s.get('critical_path_duration', 0)} days)
**Deadline:** {s.get('project', {}).get('deadline_days', 0)} days
**Team:** {len(s.get('team', []))} members
**Tasks:** {len(s.get('tasks', []))} total | Blocked: {s.get('blocked', 0)}
**Risks:** {len([r for r in s.get('risks', []) if r.get('severity') in ('HIGH', 'CRITICAL')])} high/critical
**Budget:** ₹{s.get('project', {}).get('budget', 0):,.0f} (Est. cost: ₹{float(s.get('cost_estimate', 0) or 0 if not isinstance(s.get('cost_estimate'), dict) else 0):,.0f})
""".strip()
    
    return summary


# Enhanced intent-specific response generators
def generate_greeting_response(name: str = "NEXUS-X Copilot") -> str:
    return f"""Hello! I'm **{name}**. I can help you understand your project, analyze risks, plan tasks, prepare reports, answer technical questions, run scenarios and much more.

Ask me anything about:
- **Project Status:** Is my project on track? What's the health?
- **Tasks:** What should I do first? Which task is blocking us?
- **Risks:** What's the biggest risk? How can we reduce it?
- **Team:** Who should handle this? Who's overloaded?
- **Schedule:** Can we meet the deadline? What's the critical path?
- **Budget:** Are we within budget? What costs the most?
- **What-If:** What happens if we add 2 developers? Extend the deadline?
- **Planning:** Give me today's action plan. What should I prioritize?
- **Learning:** Explain the architecture. What is PostgreSQL? (General knowledge)
- **Viva/Interview:** Prepare me for my viva. Ask me technical questions.
"""


def generate_help_response() -> str:
    return """**What I can help with:**

📊 **Project Intelligence**
- Project overview and health analysis
- Task prioritization and dependencies
- Risk assessment and mitigation
- Critical path and schedule analysis
- Team capacity and workload planning
- Budget and cost analysis

🎯 **Decision Support**
- What-If scenarios (team, deadline, budget, scope)
- Comparison (tasks, risks, options)
- Recommendations and action plans
- Executive summaries and reports

🎓 **Learning & Preparation**
- Viva/exam preparation with Q&A
- Technical explanations and examples
- Architecture and system design
- General knowledge questions

💼 **Daily Work**
- Today's priorities and action items
- Task assignment recommendations
- Blocker identification and resolution
- Team coordination

**Try asking:**
1. "What should I do first?"
2. "Why is the project at risk?"
3. "Can we meet the deadline?"
4. "Who should handle this task?"
5. "Explain this for my viva."
6. "What if we add 2 developers?"
"""


def generate_about_copilot_response() -> str:
    return """**NEXUS-X Copilot** is your AI operational intelligence assistant.

I'm built into NEXUS-X to answer questions about your projects using:
✓ Live project data (tasks, risks, team, schedule, budget)
✓ Advanced reasoning (critical path, dependencies, health)
✓ Natural language understanding
✓ Multi-mode expertise (PM, technical, student, employee, etc.)

**I can:**
- Understand your project context
- Remember recent conversations
- Answer follow-up questions
- Provide evidence-based recommendations
- Explain complex information simply
- Adapt to your role and needs

**I won't:**
- Fabricate project data
- Bypass your access controls
- Expose sensitive information
- Crash if AI services are unavailable

I'm always available in your NEXUS-X workspace.
"""


def advanced_local_copilot(message: str, s: Optional[Dict] = None, context: Optional[ConversationContext] = None) -> str:
    """
    Advanced project-aware conversational Copilot fallback.
    
    Handles 40+ intent patterns with evidence-based reasoning.
    """
    
    if context is None:
        context = ConversationContext()
    
    context.update_from_message(message)
    m = (message or "").strip().lower()
    
    intent, confidence = CopilotIntentClassifier.classify(m, context.mode)
    
    # ========== GREETINGS & HELP ==========
    if intent == 'greeting':
        return generate_greeting_response()
    
    if intent == 'help':
        return generate_help_response()
    
    if intent == 'about_copilot':
        return generate_about_copilot_response()
    
    # ========== NO PROJECT CONTEXT ==========
    if not s:
        if any(k in m for k in ['project', 'nexus', 'work', 'analyze']):
            return "📊 **No Project Selected**\n\nI can help more when you select or create a project. Once you do, I can analyze tasks, risks, team, schedule and help with decisions.\n\n**Available:**\n- General questions (coding, learning, etc.)\n- Project descriptions\n- Explanations and tutorials"
        
        if any(k in m for k in ['python', 'javascript', 'sql', 'code', 'api', 'database']):
            return "💻 **General Question**\n\nI can explain programming concepts and best practices. For project-specific code help, add your project first.\n\n**What I can explain:**\n- REST APIs and HTTP\n- SQL and databases (PostgreSQL, etc.)\n- Python, JavaScript, Flask, React\n- Authentication, security, testing\n- Cloud deployment and DevOps"
        
        return "ℹ️ **Add a Project**\n\nFor project-specific answers, please:\n1. Create a new project or select an existing one\n2. Ask me about tasks, risks, team, schedule or decisions\n3. I'll use live project data to help you\n\nFor general questions, I can answer about coding, learning, business and more!"
    
    # ========== PROJECT-SPECIFIC INTENTS ==========
    
    # TASK PRIORITY
    if intent == 'task_priority':
        first_task = None
        for t in s.get('tasks', []):
            if t.get('status') != 'COMPLETED' and t.get('task_key') in s.get('critical_path', []):
                first_task = t
                break
        
        if not first_task:
            for t in s.get('tasks', []):
                if t.get('status') != 'COMPLETED':
                    first_task = t
                    break
        
        if first_task:
            context.last_mentioned['task'] = first_task['task_key']
            downstream = [d['to_task'] for d in s.get('dependencies', []) if d.get('from_task') == first_task['task_key']]
            return ResponseFormatter.format_recommendation(
                f"Start with **{first_task['task_key']} – {first_task['name']}**",
                why=f"This is the highest-priority incomplete task on the critical path (effort: {first_task.get('effort', 0)} days, priority: {first_task.get('priority', 'N/A')})",
                impact=f"Protecting this task reduces delay to downstream work ({', '.join(downstream) if downstream else 'no immediate downstream'})",
                action="Resolve dependencies, remove blockers, and update status as work progresses."
            )
        
        return "**No Action Required**\n\nAll tasks are completed or there is no project work defined."
    
    # DEADLINE FEASIBILITY
    if intent == 'deadline_feasibility':
        cp_duration = s.get('critical_path_duration', 0)
        deadline = s.get('project', {}).get('deadline_days', 0)
        status = s.get('health_status', 'UNKNOWN')
        buffer = max(0, deadline - cp_duration)
        
        assessment = "🟢 ON TRACK" if buffer > 3 else "🟡 AT RISK" if buffer > 0 else "🔴 CRITICAL"
        
        return ResponseFormatter.format_recommendation(
            f"{assessment}",
            why=f"Critical path ({cp_duration} days) vs deadline ({deadline} days)",
            impact=f"Schedule buffer: **{buffer} days**. {f'We have comfort margin.' if buffer > 3 else f'Timeline is tight. Delays will slip the deadline.' if buffer > 0 else f'Project is overdue or critical-path work must accelerate.'}",
            action="Focus on critical-path tasks. Reduce scope or extend deadline if needed." if buffer < 0 else "Monitor schedule pressure and protect critical work."
        )
    
    # CRITICAL PATH
    if intent == 'critical_path':
        cp = s.get('critical_path', [])
        cp_duration = s.get('critical_path_duration', 0)
        deadline = s.get('project', {}).get('deadline_days', 0)
        
        return f"""**Critical Path:** {' → '.join(cp) if cp else '(not available)'}

**Details:**
- Duration: **{cp_duration} days**
- Deadline: **{deadline} days**
- Buffer: **{max(0, deadline - cp_duration)} days**

**Why:** These tasks have zero slack—any delay cascades to dependent work and the final deadline.

**Action:** Protect critical-path tasks first. Reduce scope or extend deadline if schedule is infeasible."""
    
    # BLOCKERS
    if intent == 'blockers':
        blocked = [t for t in s.get('tasks', []) if t.get('status') in ('BLOCKED', 'BLOCKER')]
        
        if blocked:
            return f"""**Blocked Tasks:** {len(blocked)} 🔴

{chr(10).join(f"- **{t['task_key']}** – {t['name']}" for t in blocked[:10])}

**Why:** Blocked work interrupts critical-path progress and increases schedule risk.

**Action:** Resolve the highest-impact blocker first. Check dependencies."""
        
        return "✓ **No Blockers**\n\nAll tasks are either in progress, completed, or have dependencies resolved. Good progress!"
    
    # TEAM ASSIGNMENT
    if intent == 'team_assignment':
        available = [m for m in s.get('team', []) if m.get('status', 'ACTIVE') != 'INACTIVE']
        
        if available:
            recommended = min(available, key=lambda x: float(x.get('workload', 0) or 0))
            return ResponseFormatter.format_recommendation(
                f"**{recommended['name']}** (role: {recommended.get('role', 'N/A')})",
                why=f"Lowest current workload ({recommended.get('workload', 0)}% utilization) and available capacity",
                impact="Balances team load and improves project velocity",
                action=f"Verify skills: {recommended.get('skills', 'N/A')}. Assign and track progress."
            )
        
        return "⚠️ **No Available Team**\n\nNo active team members are assigned. Add team members to the project."
    
    # TEAM CAPACITY
    if intent == 'team_capacity':
        team = s.get('team', [])
        if not team:
            return "No team members assigned to this project."
        
        avg_workload = sum(float(m.get('workload', 0) or 0) for m in team) / len(team) if team else 0
        overloaded = [m for m in team if float(m.get('workload', 0) or 0) > 80]
        
        status = f"Average team utilization: **{avg_workload:.0f}%**"
        if overloaded:
            status += f"\n\n🔴 **Overloaded:** {', '.join(m['name'] for m in overloaded)}"
        
        return f"""{status}

**Team:**
{chr(10).join(f"- {m['name']} ({m.get('role', 'N/A')}): **{m.get('workload', 0)}%**" for m in team)}

**Action:** Redistribute work if utilization > 90%. Consider adding people or reducing scope."""
    
    # BUDGET
    if intent == 'budget':
        budget = float(s.get('project', {}).get('budget', 0) or 0)
        cost_raw = s.get('cost_estimate', 0)
        cost = float(cost_raw if not isinstance(cost_raw, dict) else 0) or 0
        
        if budget:
            remaining = budget - cost
            feasibility = "✓ Within budget" if remaining >= 0 else "✗ Over budget"
            return f"""{feasibility}

**Cost Breakdown:**
- Estimated labor: ₹{cost:,.0f}
- Project budget: ₹{budget:,.0f}
- Remaining: **₹{remaining:,.0f}**

**Utilization:** {(cost/budget)*100:.1f}% of budget

**Action:** {'Monitor costs. Review if scope increases.' if remaining < budget * 0.2 else 'Budget looks sustainable.'}"""
        
        return "**No Budget Configured**\n\nSet a project budget for budget-aware decisions and cost tracking."
    
    # RISKS
    if intent == 'risk_severity' or intent == 'risk_analysis':
        high_risks = [r for r in s.get('risks', []) if r.get('severity') in ('HIGH', 'CRITICAL')]
        
        if high_risks:
            top = max(high_risks, key=lambda x: int(x.get('score', 0)))
            return f"""**Highest Risk:** {top['name']} ({top['score']}/10)

**Severity:** {top['severity']}

**Why:** {top.get('explanation', 'High impact potential')}

**EVIDENCE:**
- Score: **{top['score']}/10**
- Probability: **{top.get('probability', 'N/A')}%**
- Impact: **{top.get('impact', 'N/A')}%**
- Affected tasks: **{top.get('affected_tasks', 'Multiple')}**

**Mitigation:** {top.get('mitigation', 'Address before release')}

**Other High/Critical Risks:**
{chr(10).join(f"- {r['name']} ({r['score']}/10): {r['mitigation']}" for r in high_risks[1:5])}

**ACTION:** Mitigate top risks first. Check affected tasks: {top.get('affected_tasks', 'Multiple')}"""
        
        return "✓ **No High Risks**\n\nProject risk profile is low. Continue monitoring dependencies and schedule pressure."
    
    # PROJECT HEALTH
    if intent == 'project_health':
        return f"""**Project Health: {s.get('health', 0)}%** ({s.get('health_status', 'UNKNOWN')})

**Status:** {s.get('health_status', 'UNKNOWN')}

**Progress:** {s.get('progress', 0)}%
**Critical Path:** {s.get('critical_path_duration', 0)} days (deadline: {s.get('project', {}).get('deadline_days', 0)} days)
**Blocked Tasks:** {s.get('blocked', 0)}

**Key Factors:**
{chr(10).join('- ' + line for line in s.get('explanation', ['Overall project progress is steady']))}

**Action:** Focus on critical-path work. Resolve blockers. Monitor risk changes."""
    
    # WHAT-IF
    if intent == 'what_if':
        return """**What-If Analysis**

I can simulate scenarios for:
- Adding/removing team members
- Extending/reducing deadline
- Increasing/reducing budget
- Adding/removing features (scope)
- Delaying specific tasks

**Try asking:**
- "What if we add 2 developers?"
- "What happens if deadline becomes 7 days?"
- "What if we reduce scope by 30%?"
- "Can we finish in 5 days?"

Use the What-If page for detailed interactive scenarios."""
    
    # EXPLANATION / GENERAL KNOWLEDGE
    if intent == 'explanation' or intent == 'general_knowledge':
        # Try to determine what they're asking about
        if any(k in m for k in ['architecture', 'system', 'design']):
            return """**Project Architecture**

NEXUS-X uses:
- **Frontend:** Browser-based UI (HTML/CSS/JS)
- **Backend:** Flask API server
- **Database:** SQLite or PostgreSQL
- **Intelligence:** Critical path, health engine, risk analysis
- **Integration:** OpenAI for enhanced reasoning when available

Components stay connected through REST APIs. Project data flows from database → calculation engines → API responses → UI.

**Try asking:**
- "Explain the database design"
- "How does task prioritization work?"
- "What is the critical path algorithm?"
"""
        
        if any(k in m for k in ['postgresql', 'database', 'sql', 'schema']):
            return """**PostgreSQL in NEXUS-X**

PostgreSQL stores:
- Projects (name, description, deadline, team size, budget)
- Tasks (task_key, name, effort, owner, priority, status, dependencies)
- Team members (name, role, skills, workload, availability)
- Risks (name, severity, score, probability, impact, mitigation)
- Dependencies (task-to-task links)
- Analysis history (snapshots over time)

Queries are optimized for:
- Critical path calculation (graph algorithms)
- Health calculation (aggregate metrics)
- Dependency impact (transitive closure)
- What-If simulation (cost and schedule feasibility)

Data is ACID-compliant and versioned."""
        
        if any(k in m for k in ['api', 'rest', 'endpoint']):
            return """**NEXUS-X APIs**

Core endpoints:
- POST /api/projects – Create project
- GET /api/projects/<id> – Fetch project state
- POST /api/tasks – Add task
- POST /api/dependencies – Link tasks
- POST /api/team – Add team member
- POST /api/what-if – Simulate scenario
- POST /api/chat – Copilot conversation
- GET /api/dashboard/<id> – Project dashboard

All APIs:
- Require authentication
- Check CSRF tokens
- Apply rate limiting
- Respect RBAC
- Return JSON

See /api/health for service status."""
        
        return """**General Explanation**

You're asking about something I can help explain. Try being more specific:

**Technical Topics:**
- Explain the architecture
- What is PostgreSQL?
- How do APIs work?
- Explain critical path
- What is a dependency cycle?

**Learning Topics:**
- Explain project management
- What is Agile?
- Explain risk management
- What is scope creep?

**Or ask about your project specifically.**"""
    
    # STUDENT MODE / VIVA
    if 'viva' in m or 'exam' in m or 'presentation' in m or 'student' in m:
        return """**Viva/Exam Preparation**

I can help you prepare:

**Explain Your Project**
- "Explain this project for my viva"
- "Explain the project simply"
- "Give me a 1-minute summary"
- "What is the problem we're solving?"

**Technical Questions**
- "Explain the architecture"
- "What technologies are used and why?"
- "Explain the database design"
- "How does authentication work?"

**Management Questions**
- "What is the timeline?"
- "What are the risks?"
- "What is the budget?"
- "How did you plan the project?"

**Difficult Questions**
- "What didn't work?"
- "What would you do differently?"
- "What were the challenges?"
- "What did you learn?"

**Let me know:**
1. Exam level (basic/intermediate/advanced)
2. Time limit (1-5 minutes)
3. Focus area (technical/management/both)

Ready when you are!"""
    
    # ACTION PLAN
    if intent == 'action_plan':
        incomplete_tasks = [t for t in s.get('tasks', []) if t.get('status') != 'COMPLETED']
        
        if incomplete_tasks:
            action_list = []
            for i, t in enumerate(incomplete_tasks[:5], 1):
                action_list.append(f"{i}. **{t['task_key']}** – {t['name']} ({t.get('effort', 0)} days)")
            
            return f"""**Action Plan**

{chr(10).join(action_list)}

**Priority:**
1. Protect critical-path tasks
2. Resolve any blockers
3. Balance team workload
4. Maintain schedule buffer

**By end of day:**
- Update task statuses
- Document blockers
- Escalate risks if needed"""
        
        return "**All Tasks Complete** ✓\n\nProject is done or no work is defined. Great work!"
    
    # MANAGEMENT SUMMARY
    if intent == 'management_summary':
        return f"""**Executive Summary**

**Status:** {s.get('health_status', 'UNKNOWN')} (Health: {s.get('health', 0)}%)

**Progress:** {s.get('progress', 0)}% complete

**Schedule:**
- Critical path: {s.get('critical_path_duration', 0)} days
- Deadline: {s.get('project', {}).get('deadline_days', 0)} days
- Buffer: {max(0, s.get('project', {}).get('deadline_days', 0) - s.get('critical_path_duration', 0))} days

**Team:** {len(s.get('team', []))} active members, avg utilization {sum(float(m.get('workload', 0) or 0) for m in s.get('team', [])) / max(1, len(s.get('team', []))):.0f}%

**Risks:** {len([r for r in s.get('risks', []) if r.get('severity') in ('HIGH', 'CRITICAL')])} high/critical risks

**Budget:** {'Within budget ✓' if (float(s.get('project', {}).get('budget', 0) or 0) - float(s.get('cost_estimate', 0) or 0 if not isinstance(s.get('cost_estimate'), dict) else 0)) >= 0 else 'Over budget ✗'}

**Recommendation:** {'On track. Maintain current pace.' if s.get('health_status') == 'HEALTHY' else 'At risk. Protect critical path and address top risks.'}"""
    
    # ========== DEFAULT FALLBACK ==========
    return f"""**Project Overview: {s.get('project', {}).get('name', 'Unnamed')}**

**Health:** {s.get('health', 0)}% ({s.get('health_status', 'UNKNOWN')})
**Progress:** {s.get('progress', 0)}%
**Tasks:** {len(s.get('tasks', []))} total, {s.get('blocked', 0)} blocked
**Critical Path:** {s.get('critical_path_duration', 0)} / {s.get('project', {}).get('deadline_days', 0)} days

**Try asking:**
- "What should I do first?"
- "Why is the project at risk?"
- "Can we meet the deadline?"
- "Who should handle this?"
- "What are the top risks?"
- "Are we within budget?"
- "What if we add 2 developers?"

**Or describe what you need help with.**"""
