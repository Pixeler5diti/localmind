from model import query

def run_agent(goal):
    """
    Intelligent multi-step agent with adaptive planning.
    """
    print("\n[ AGENT MODE - INTELLIGENT PLANNING]\n")
    
    # STEP 1: Deep analysis of user problem and goal
    understanding_prompt = f"""Analyze this goal in depth:

GOAL: {goal}

Provide:
1. What success looks like (measurable)
2. Key challenges and blockers
3. Required prerequisites
4. Dependencies and order of execution
5. Potential pitfalls

Be specific, not generic."""
    
    print(" Analyzing goal in depth...\n")
    understanding = query(understanding_prompt)
    print(understanding)
    print("\n" + "="*70 + "\n")
    
    # STEP 2: Comprehensive action plan
    planning_prompt = f"""Create a detailed, step-by-step action plan:

GOAL: {goal}

ANALYSIS:
{understanding}

Provide 5-7 concrete steps with:
- What to do (specific, not vague)
- Why it matters
- Success criteria
- Effort estimate
- Common mistakes to avoid

Order by dependencies. Make each step independent."""
    
    print(" Creating comprehensive plan...\n")
    plan = query(planning_prompt)
    print(plan)
    print("\n" + "="*70 + "\n")
    
    # STEP 3: Deep execution guidance for Step 1
    execution_prompt = f"""Provide detailed, actionable guidance for executing Step 1:

GOAL: {goal}

PLAN:
{plan}

For STEP 1 only:
1. Pre-flight checklist (what to prepare)
2. Detailed step-by-step instructions
3. Expected outputs/deliverables
4. Validation/testing approach
5. Common failure modes and how to avoid them
6. How to know you're done (success criteria)

Be VERY specific and practical."""
    
    print(" Step 1 execution plan (detailed)...\n")
    execution = query(execution_prompt)
    print(execution)
    print("\n" + "="*70 + "\n")
    
    # STEP 4: Smart continuation planning
    continuation_prompt = f"""Review Step 1 and plan for continuation:

GOAL: {goal}

PLAN:
{plan}

STEP 1 GUIDANCE:
{execution}

Provide:
1. What you should have after Step 1 is complete
2. How to verify Step 1 success
3. Blockers to watch for
4. What to prepare before Step 2
5. Brief outline of Step 2 (high level)
6. Final tips for success"""
    
    print(" Continuation guidance...\n")
    continuation = query(continuation_prompt)
    print(continuation)
    print("\n" + "="*70)
    print("\n PLANNING COMPLETE - Ready to execute Step 1")
    print("   After completion, return for Step 2 details")
    print("="*70 + "\n")