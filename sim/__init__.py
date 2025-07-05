"""Simulation utilities and classes extracted from ``MySim.ipynb``."""

from __future__ import annotations

import pandas as pd
from uuid import uuid4
import json
import yaml
import simpy

ALL_MONTHS = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]

NIRATE = 0.138
NITHRESHOLD = 175
EMPLOYERPENSIONRATE = 0.09
PENSIONFTETHRESHOLD = 0.2
REALLIVINGWAGE = 12
FCRDATA: list[dict] = []
SUPPORTDATA: list[dict] = []


def get_current_month(start_month: str = "apr", month: int = 0) -> str:
    elapsed_months_adjusted = month
    current_month_index = (3 + elapsed_months_adjusted) % len(ALL_MONTHS)
    return ALL_MONTHS[current_month_index]


def printtimestamp(env: simpy.Environment):
    month = get_current_month("apr", env.now - 1)
    print(f"\nMonth: {env.now} ({month})")


def pivotbudget(db: pd.DataFrame) -> pd.DataFrame:
    df = db.pivot_table(index=['item'], columns=['step'], values='budget', aggfunc='sum', fill_value=0)
    lookup_dict_description = {row['item']: row.get('description', '') for _, row in db.iterrows()}
    lookup_dict_type = {row['item']: row.get('type', '') for _, row in db.iterrows()}
    df['description'] = df.index.map(lookup_dict_description).fillna('')
    df['type'] = df.index.map(lookup_dict_type).fillna('')
    columns_except_extra = [col for col in df.columns if col not in ['description', 'type']]
    new_column_order = ['description', 'type'] + columns_except_extra
    df = df[new_column_order]
    pf = df.iloc[::-1]
    pf = pf.sort_values(by='type', ascending=True)
    return pf


def parseYAML(yamltext: str):
    def map_cls_strings_to_objects(data):
        if isinstance(data, list):
            for index, item in enumerate(data):
                data[index] = map_cls_strings_to_objects(item)
        elif isinstance(data, dict):
            for key, value in data.items():
                if key == 'cls' and isinstance(value, str):
                    data[key] = globals().get(value, value)
                else:
                    data[key] = map_cls_strings_to_objects(value)
        return data

    data = yaml.safe_load(yamltext)
    return map_cls_strings_to_objects(data)


def yaml_to_react_flow_json(yaml_file_path: str, json_file_path: str | None = None):
    with open(yaml_file_path, "r") as file:
        yaml_data = yaml.safe_load(file)

    def yaml_to_react_flow(yaml_data):
        nodes = []
        edges = []
        for index, phase in enumerate(yaml_data):
            parent_node_id = str(uuid4())
            attributes = []
            for key, value in phase.items():
                if not isinstance(value, list):
                    attributes.append(f"{key}: {value}")
                else:
                    for item in value:
                        subattribute = [f"{subkey}: {item[subkey]}" for subkey in item]
                        child_node_id = str(uuid4())
                        child_node = {
                            "id": child_node_id,
                            "type": "UMLClassNode",
                            "position": {"x": 250 * index + 100, "y": 200},
                            "data": {"name": f"{key}", "attributes": subattribute},
                        }
                        nodes.append(child_node)
                        edges.append({"id": str(uuid4()), "source": parent_node_id, "target": child_node_id})
            node = {
                "id": parent_node_id,
                "type": "UMLClassNode",
                "position": {"x": 250 * index, "y": 100},
                "data": {"name": phase["name"], "attributes": attributes},
            }
            nodes.append(node)
        return {"nodes": nodes, "edges": edges}

    react_flow_data = yaml_to_react_flow(yaml_data)
    if json_file_path:
        with open(json_file_path, "w") as file:
            json.dump(react_flow_data, file, indent=4)
    return react_flow_data


def react_flow_to_yaml(json_file_path: str, yaml_file_path: str | None = None):
    with open(json_file_path, 'r') as json_file:
        react_flow_data = json.load(json_file)

    nodes = react_flow_data['nodes']
    edges = react_flow_data['edges']
    node_data_map = {node['id']: node for node in nodes}
    yaml_data = []
    parent_ids = set(node_data_map.keys()) - set(edge['target'] for edge in edges)

    for parent_id in parent_ids:
        parent_node = node_data_map[parent_id]
        phase_data = {}
        for attr in parent_node['data']['attributes']:
            key, value = attr.split(': ', 1)
            try:
                if value.isdigit():
                    value = int(value)
                else:
                    value = eval(value)
            except Exception:
                pass
            phase_data[key] = value
        child_edges = [edge for edge in edges if edge['source'] == parent_id]
        for edge in child_edges:
            child_node = node_data_map[edge['target']]
            category = child_node['data']['name']
            child_attrs = {}
            for attr in child_node['data']['attributes']:
                if ': ' in attr:
                    key, value = attr.split(': ', 1)
                    try:
                        if value.isdigit():
                            value = int(value)
                        elif value.startswith('{') and value.endswith('}'):
                            value = value
                        else:
                            value = str(value)
                    except Exception:
                        pass
                else:
                    key = 'unknown'
                    value = attr
                child_attrs[key] = value
            if category not in phase_data:
                phase_data[category] = []
            phase_data[category].append(child_attrs)
        yaml_data.append(phase_data)

    yaml_output = yaml.dump(yaml_data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    if yaml_file_path:
        with open(yaml_file_path, 'w', encoding='utf-8') as yaml_file:
            yaml_file.write(yaml_output)
    return yaml_output


class worker:
    def __init__(self, **kwargs):
        self.position = kwargs.get('position', 'undesignated')
        self.name = kwargs.get('name', 'staff member')
        self.age = kwargs.get('age', 49)
        self.department = kwargs.get('department', 'unspecified')
        self.mobilephone = kwargs.get('mobilephone', 'not assigned')
        self.linemanagerrate = kwargs.get('linemanagerrate', 0)
        self.employerpensionrate = kwargs.get('employerpensionrate', EMPLOYERPENSIONRATE)
        self.fte_salary = kwargs.get('salary', 0)
        self.fte = kwargs.get('fte', 1)
        self.salary = self.fte * self.fte_salary

    def info(self):
        for attr, value in self.__dict__.items():
            print(f"{attr} : {value}")

    def getbreakdown(self, month: int):
        salary = self.getMonthSalary(month)
        data = [
            {'step': month, 'item': 'salary', 'budget': salary, 'type': '1. Staffing'},
            {'step': month, 'item': 'ni', 'budget': self.getNI(salary), 'type': '1. Staffing'},
            {'step': month, 'item': 'pension', 'budget': self.getPension(salary, self.fte), 'type': '1. Staffing'},
        ]
        return data

    def getSalaryCost(self) -> float:
        monthlysalary = self.salary / 12
        monthlycost = monthlysalary + self.getNI(monthlysalary) + self.getPension(monthlysalary, self.fte)
        return monthlycost * 12

    def getMonthSalaryCost(self, month: int) -> float:
        return self.getSalaryCost() / 12

    def getMonthSalary(self, month: int) -> float:
        return self.salary / 12

    def getNI(self, monthlySalary: float) -> float:
        monthlyThreshold = NITHRESHOLD / 7 * 365 / 12
        if self.salary > monthlyThreshold:
            ni = max(0, (monthlySalary - monthlyThreshold)) * NIRATE
        else:
            ni = 0
        return ni

    def getPension(self, salary: float, fte: float) -> float:
        if fte > PENSIONFTETHRESHOLD:
            pension = salary * self.employerpensionrate
        else:
            pension = 0
        return pension


class project:
    def __init__(self, portfolio, env: simpy.Environment, **kwargs):
        self.kwargs = kwargs
        self.name = kwargs.get('name', 'New Project')
        self.term = kwargs.get('term', 0)
        self.directcosts = kwargs.get('directcosts', [])
        self.supports = kwargs.get('supports', [])
        self.env = env
        self.portfolio = portfolio
        self.startstep = env.now
        self.consolidated_account = portfolio.consolidated_account
        self.budget = kwargs.get('budget', 0)
        self.policies = []
        policies = kwargs.get('policies')
        if policies:
            for policy in policies:
                cls = globals().get(policy['policy'])
                if callable(cls):
                    self.policies.append(cls(self.env, self, **policy))
        self.staff = []
        staffing = kwargs.get('staffing', [])
        for person in staffing:
            self.addstaff(worker(**person))
        self.costs_thismonth = 0
        self.income_thismonth = 0
        self.cost = 0
        self.income = 0
        self.env.process(self.start())

    def calculate(self, step: int):
        dcosts = self.getdirectcosts(step)
        directcost = sum(d['budget'] for d in dcosts if 'budget' in d)
        scosts = self.getsupports(step)
        supportcost = sum(d['budget'] for d in scosts if 'budget' in d)
        self.costs_thismonth += self.getsalarycosts(step) + directcost + supportcost
        self.income_thismonth += 0

    def getsupports(self, step: int):
        costs = []
        for support in self.supports:
            item = support.get('item', 'unspecified')
            applystep = support.get('step', 0)
            description = support.get('description', '')
            freq = support.get('frequency', 'oneoff')
            matching = [d for d in SUPPORTDATA if d.get('item') == item]
            eligiblestep = freq == 'monthly' or (freq == 'oneoff' and applystep == step) or (freq == 'annual' and (step - applystep) % 12 == 0)
            if eligiblestep and matching:
                lookup = matching[0]
                cost = support['units'] * lookup['dayrate'] * lookup['daysperunit']
            else:
                cost = 0
            costs.append({'step': step, 'item': item, 'budget': cost, 'description': description})
        return costs

    def getdirectcosts(self, step: int):
        costs = []
        for directcost in self.directcosts:
            freq = directcost.get('frequency', 'oneoff')
            applystep = directcost.get('step', 0)
            item = directcost.get('item', 'unspecified')
            cost = directcost.get('cost', 0)
            description = directcost.get('description', '')
            type_desc = directcost.get('type', '2. Standard')
            if freq == 'monthly' or (freq == 'oneoff' and applystep == step) or (freq == 'annual' and (step - applystep) % 12 == 0):
                pass
            else:
                cost = 0
            costs.append({'step': step, 'item': item, 'budget': cost, 'description': description, 'type': type_desc})
        return costs

    def getstaffcosts(self, step: int | None = None):
        fcr_policy = next((p for p in self.policies if isinstance(p, FullCostRecovery)), None)

        def getstep(step: int):
            stepregister = []
            for person in self.staff:
                breakdown = person.getbreakdown(step)
                for entry in breakdown:
                    entry['name'] = person.name
                stepregister.extend(breakdown)
                if fcr_policy is not None:
                    fcr_entries = fcr_policy.getfcr(person, step)
                    for entry in fcr_entries:
                        entry['name'] = person.name
                    stepregister.extend(fcr_entries)
            return stepregister

        register = []
        if step is not None:
            register.extend(getstep(step))
        else:
            for s in range(self.term):
                register.extend(getstep(s))
        return pd.DataFrame(register)

    def getbudget(self) -> pd.DataFrame:
        budget = []
        for i in range(self.term):
            directcosts = self.getdirectcosts(i)
            supportcosts = self.getsupports(i)
            budget.extend(directcosts)
            budget.extend(supportcosts)
            for st in self.staff:
                budget.extend(st.getbreakdown(i))
        for policy in self.policies:
            if hasattr(policy, 'getbudget') and callable(policy.getbudget):
                budget.extend(policy.getbudget())
        df = pd.DataFrame(budget)
        return df

    def getbudgetadjusted(self) -> pd.DataFrame:
        df = self.getbudget()
        if 'step' in df.columns:
            df['step'] = df['step'] + self.startstep
        return df

    def getsalarycosts(self, step: int) -> float:
        cost = 0
        for worker in self.staff:
            cost += worker.getMonthSalaryCost(step)
        return cost

    def addstaff(self, staff: worker):
        self.staff.append(staff)

    def sweep_policies(self, step: int):
        for policy in self.policies:
            policy.calculate(step)

    def start(self):
        for i in range(self.term):
            self.income_thismonth = self.costs_thismonth = 0
            self.calculate(i)
            self.sweep_policies(i)
            self.income += self.income_thismonth
            self.cost += self.costs_thismonth
            cons = self.portfolio.consolidated_account
            cons.update({'type': 'expenditure', 'title': 'project costs', 'project': self.name, 'amount': self.costs_thismonth})
            cons.update({'type': 'income', 'title': 'project income', 'project': self.name, 'amount': self.income_thismonth})
            yield self.env.timeout(1)
        printtimestamp(self.env)
        print(f"Project {self.name} cost {self.cost:.2f} and generated {self.income:.2f} with budget {self.budget:.2f}")


class ConsolidatedAccount:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.total_capital = 0
        self.total_payments = 0
        self.total_income = 0
        self.balance = 0
        self.register = []

    def update(self, transaction: dict):
        transaction['amount'] = float(transaction['amount'])
        if transaction['type'] == 'expenditure':
            self.total_payments += transaction['amount']
        if transaction['type'] == 'income':
            self.total_income += transaction['amount']
            transaction['amount'] = -transaction['amount']
        self.balance = self.total_income - self.total_payments
        transaction['date'] = self.env.now
        transaction['balance'] = self.balance
        self.register.append(transaction)

    def report(self):
        print(f"Consolidated Account Report: Payments to date: {self.total_payments:.2f}, Income to date: {self.total_income:.2f}, Balance: {self.balance:.2f}")


class Portfolio:
    def __init__(self, env: simpy.Environment, name: str = 'My Portfolio'):
        self.env = env
        self.name = name
        self.consolidated_account = ConsolidatedAccount(env)
        self.projects: list[project] = []

    def counter(self):
        for i in range(1, 31):
            month = get_current_month(start_month='apr', month=self.env.now)
            print(f"\nMonth: {i} {month}")
            yield self.env.timeout(1)

    def set_event(self, event: dict):
        e = self.env.event()
        e.details = event
        yield self.env.timeout(event['time'])
        printtimestamp(self.env)
        message = event.get('message', event.get('name', 'new project'))
        print(f'Event {message} succeeds')
        e.succeed()
        self.env.process(self.create_project(**event))

    def set_portfolio(self, events: list[dict]):
        for event in events:
            self.env.process(self.set_event(event))

    def getbudget(self) -> pd.DataFrame:
        data = {'item': [], 'step': [], 'budget': []}
        consol_budget = pd.DataFrame(data)
        for prj in self.projects:
            budget = prj.getbudgetadjusted()
            consol_budget = pd.concat([consol_budget, budget], ignore_index=True)
        return consol_budget

    def list_projects(self) -> pd.DataFrame:
        data = []
        for prj in self.projects:
            data.append({k: v for k, v in prj.__dict__.items() if isinstance(v, (str, int, float, bool))})
        return pd.DataFrame(data)

    def run(self, until: int):
        self.env.run(until=until)

    def list_transactions(self) -> pd.DataFrame:
        transactions = self.consolidated_account.register
        df = pd.DataFrame(transactions)
        self.consolidated_account.report()
        return df

    def create_project(self, cls=project, **kwargs):
        prj = cls(self, self.env, **kwargs)
        self.projects.append(prj)
        staff_names = ', '.join(person.name for person in prj.staff)
        print(f"Project {prj.name} created with budget {prj.budget:.2f} and assigned staff {staff_names}")
        yield self.env.timeout(1)

    def finance(self, term: int, capital: float, rate: float = 0.05):
        repayment = capital / term
        account = capital
        print(f'New capital received {capital}')
        self.consolidated_account.update({'type': 'income', 'title': 'finance capitalisation', 'project': 'headoffice', 'amount': capital})
        totpay = 0
        for i in range(term):
            interest = rate * account
            account = account - repayment
            payment = repayment + interest
            totpay += payment
            self.consolidated_account.update({'type': 'expenditure', 'title': 'finance servicing', 'project': 'headoffice', 'amount': payment})
            yield self.env.timeout(1)
        printtimestamp(self.env)
        print(f"Finance: Final account {account:.2f}, total paid {totpay:.2f}")


class Policy:
    def __init__(self, env: simpy.Environment, prj: project, **kwargs):
        self.env = env
        self.prj = prj

    def calculate(self, step: int):
        pass


class FullCostRecovery(Policy):
    def __init__(self, env: simpy.Environment, prj: project, **kwargs):
        super().__init__(env, prj, **kwargs)
        self.fcr = self.getfcrdata()
        self.register = []

    def getfcrdata(self):
        fcr = []
        for item in FCRDATA:
            fcr.append(item)
        return fcr

    def getfcr(self, person: worker, step: int):
        register = []
        linemanagerrate = person.linemanagerrate
        for item in self.fcr:
            itemname = item['item']
            daysperfte = item['daysperfte']
            dayrate = linemanagerrate if itemname == 'Line Management' else item['dayrate']
            frequency = item['frequency']
            cost = person.fte * daysperfte * dayrate
            if frequency == 'oneoff':
                cost = cost if step == 0 else 0
            if frequency == 'monthly':
                pass
            if frequency == 'annual':
                cost = cost if step % 12 == 0 else 0
            register.append({'step': step, 'item': itemname, 'budget': cost, 'type': '3. FullCostRecovery'})
        return register

    def calcfcr(self, person: worker, step: int):
        register = self.getfcr(person, step)
        self.register.extend(register)
        return sum(item['budget'] for item in register if 'budget' in item)

    def calculate(self, step: int):
        totalcost = 0
        for person in self.prj.staff:
            totalcost += self.calcfcr(person, step)
        self.prj.costs_thismonth += totalcost

    def getbudget(self):
        return self.register


class Grant(Policy):
    def __init__(self, env: simpy.Environment, prj: project, **kwargs):
        super().__init__(env, prj, **kwargs)
        self.amount = kwargs.get('amount', 0)
        self.fund = kwargs.get('fund', 'unspecified')
        self.startstep = kwargs.get('step', 0)
        self.register = []

    def calculate(self, step: int):
        prj = self.prj
        amount = self.amount
        if step == self.startstep:
            prj.income_thismonth += amount
            self.register.append({'item': f'{self.fund} grant', 'step': step, 'budget': -amount, 'type': '4. Funding'})

    def getbudget(self):
        return self.register


class Subsidy(Policy):
    def calculate(self, step: int):
        payment = 100000
        prj = self.prj
        prj.income_thismonth += payment
        prj.consolidated_account.update({'type': 'income', 'title': 'government subsidy', 'project': prj.name, 'amount': payment})


class Rename(Policy):
    def calculate(self, step: int):
        self.prj.name = f'Fancy project in step {step}'


class Finance(Policy):
    def __init__(self, env: simpy.Environment, prj: project, **kwargs):
        super().__init__(env, prj, **kwargs)
        self.term = kwargs.get('term', prj.term)
        self.account = self.capital = kwargs.get('capital', 0)
        self.rate = kwargs.get('rate', 0)
        self.consolidated_account = prj.consolidated_account
        self.totpay = 0
        print(f'New capital received {self.capital}')
        self.consolidated_account.update({'type': 'income', 'title': 'finance capitalisation', 'project': 'headoffice', 'amount': self.capital})

    def calculate(self, step: int):
        repayment = self.capital / self.term
        interest = self.rate * self.account
        self.account -= repayment
        payment = repayment + interest
        self.totpay += payment
        self.consolidated_account.update({'type': 'expenditure', 'title': 'finance servicing', 'project': 'headoffice', 'amount': payment})
        if step == self.term - 1:
            self.finalize()

    def finalize(self):
        printtimestamp(self.env)
        print(f"Finance: Final account {self.account:.2f}, total paid {self.totpay:.2f}")


class CarbonFinancing(Policy):
    def __init__(self, env: simpy.Environment, prj: project, **kwargs):
        super().__init__(env, prj, **kwargs)
        self.prj = prj
        self.budget = prj.budget
        self.investment = kwargs.get('investment')
        self.tree_planting_cost_per_unit = kwargs.get('tree_planting_cost_per_unit')
        self.carbon_credit_per_unit = kwargs.get('carbon_credit_per_unit')
        self.trees_planted = self.calculate_trees_planted()
        self.carbon_credits_generated = self.calculate_carbon_credits()
        self.prj.consolidated_account.update({'type': 'expenditure', 'title': 'capital cost tree planting', 'project': self.prj.name, 'amount': self.investment - self.budget})
        print(f'Trees planted: {self.trees_planted:.0f} will generate {self.calculate_carbon_credits():.0f} carbon credits over 40 years worth £{self.calculate_carbon_income():.2f}')

    def calculate_trees_planted(self) -> float:
        return (self.investment - self.budget) / self.tree_planting_cost_per_unit

    def calculate_carbon_credits(self) -> float:
        unitpertreelifetime = 1.1
        return self.trees_planted * unitpertreelifetime

    def calculate_carbon_income(self) -> float:
        return self.calculate_carbon_credits() * self.carbon_credit_per_unit

    def report(self):
        return {
            "investment": self.investment,
            "trees_planted": self.trees_planted,
            "carbon_credits_generated": self.carbon_credits_generated,
        }

    def calculate(self, step: int):
        if step == 0:
            carbonincome = self.investment
        else:
            carbonincome = 0
        self.prj.income_thismonth += carbonincome
        return
