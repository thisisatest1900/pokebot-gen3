from abc import ABC, abstractmethod
from enum import Enum
import struct

from modules.Inputs import PressButton
from modules.Memory import ReadSymbol
from modules.Trainer import GetTrainer

class Action(ABC):

    @abstractmethod
    def doAction(self) -> None: # implement some action
        pass
    @abstractmethod
    def actionSucceeded(self) -> bool: # check if the action preformed correctly to allow re call of the action
        pass

class Direction(Enum): #changed to match decomp remember to change in Map class
    Down = 1
    UP = 2
    LEFT = 3
    RIGHT = 4
    DIVE = 5
    EMERGE = 6 # when going up from DIVE

OBJECT_EVENT_ID_OFFSET = 0x05
PREVIOUS_MOVEMENT_DIRECTION_OFFSET = 0x20
OBJECT_EVENT_SIZE = 0x24

class MoveAction(Action):

    def __init__(self, direction: Direction, run: bool = True) -> None:
        super().__init__()
        self.direction = direction
        self.run = run
        self.firstCall = True
        self.trainerCoords = None
    
    def actionSucceeded(self) -> bool:
        return GetTrainer()['coords'] != self.trainerCoords

    def doAction(self) -> None:
        # playerObjectId = struct.unpack('<B',ReadSymbol('gplayeravatar')[OBJECT_EVENT_ID_OFFSET:OBJECT_EVENT_ID_OFFSET + 1])[0]
        # currDirection = Direction(readByte(GetSymbolAddr('gObjectEvents') \
        #                                    + playerObjectId * OBJECT_EVENT_SIZE + PREVIOUS_MOVEMENT_DIRECTION_OFFSET))
        if self.firstCall:
            self.trainerCoords = GetTrainer()['coords']
            self.firstCall = False

        toPress = [self.direction.name.capitalize()]
        if self.run:
            toPress.append('B')
        PressButton(toPress,1)

class ActionRunner(object):

    def __init__(self,actions:list[Action]) -> None:
        self.actions: list[Action] = actions
        self.currentAction: int = 0
        self.firstRun: bool = True
    
    def runNextAction(self) -> bool:
        if self.firstRun:
            self.actions[0].doAction()
            self.firstRun = False
        else:
            if self.actions[self.currentAction].actionSucceeded() == True:
                self.currentAction += 1
                if self.currentAction == len(self.actions):
                    return False

            self.actions[self.currentAction].doAction()
        return True

# def runActions(actions: list[Action]):
#     for index,action in enumerate(actions):
#         print(index)
#         action.doAction()