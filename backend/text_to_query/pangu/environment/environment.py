from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    SupportsFloat,
    Tuple,
    TypeVar,
    Union,
)

ActType = TypeVar("ActType")


class Action:
    pass


class Env:
    def __init__(self, initial_state: Dict[str, Any] = None):
        # e.g., the coordinates of the agent in a physical environment, or the current state of web surfing
        self.state = initial_state

    def step(self, action: Action) -> Dict[str, Any]:
        """
        :param action: an action taken by the agent, which may (implicitly) change the state of the environment
        :return: a set of new observations from the environment
        """
        pass
