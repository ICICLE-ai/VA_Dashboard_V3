from typing import Optional, Set


# The base class for all plans
class Plan:
    def __init__(self,
                 plan: str,
                 plan_str: str = None,
                 height: int = None,
                 rtn_type: str = None,
                 function: str = None,
                 denotation: Optional[Set] = None,
                 finalized: bool = False):
        """
        Initialize a base plan wrapper
        :param plan: the executable plan itself
        :param plan_str: the form of the plan to be scored by the LMScorer; by default plan_str is the same as plan
        :param rtn_type: the return type of the plan
        :param denotation: the execution result of the plan (optional)
        """
        self.plan = plan
        self.plan_str = plan_str
        self.height = height
        self.rtn_type = rtn_type
        self.function = function
        self.denotation = denotation
        self.finalized = finalized
        self.score = None

    def __str__(self):
        return self.plan

    def __eq__(self, other):  # can be customized to support more advanced equality checking
        return self.plan == other.plan

    def __hash__(self):
        return hash(self.plan)

    def __repr__(self):
        return self.plan

