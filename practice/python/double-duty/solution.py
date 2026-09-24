from collections import defaultdict
def allocate_budget(projects: list[dict], assignments: list[dict]) -> dict[str, float]:
    total_assist = defaultdict(list)
    total_project = defaultdict(int)
    for assist in assignments:
      total_assist[assist['project_id']].append(assist['employee_id'])
    for pro in projects:
      total_project[pro['project_id']] = pro['budget']
    cost_per_person = defaultdict(int)
    for t in total_assist:
      cost_per_person[t] = total_project[t]/len(total_assist[t])
    person_cost = defaultdict(int)
    for assist in assignments:
      person_cost[assist['employee_id']] += cost_per_person.get(assist['project_id'])
    return person_cost
