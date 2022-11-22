import mesa
from road_agent import RoadAgent
from smart_traffic_light_agent import SmartTrafficLightAgent
from intersection_traffic_lights import IntersectionTrafficLightsAgent
from driver_agent import DriverAgent
rows = 21
columns = 21

# De aqui solo se modifca el 'driverType'
# 1 -> GoodDriver
# 2 -> Ambulance
# 3 -> CrazyDriver
# 4 -> WannaBeCrazyDriver
# 5 -> Mix of drivers or truck, it's up to you
class CityModel(mesa.Model):     
    def __init__(self, agents, time):
        self.schedule = mesa.time.RandomActivationByType(self)
        self.grid = mesa.space.MultiGrid(rows, columns, False)
        self.agents = agents
        self.current_id = 0
        self.running = True
        self.time = time
        self.steps = 0
        self.crashes = 0
        self.moves = 0
        driverSample = DriverAgent(self.next_id(), self, 0)
        self.driverType = 2 # Solo se modifica segun el driver de cada quien
        self.datacollector = mesa.DataCollector(
            model_reporters= {
            'Crashes': CityModel.getNumberOfCrashes,
            'Congestion': CityModel.getCurrentCongestion,
            'Sanity': CityModel.getSanity,
            'TimeOfTrafficLightOn': CityModel.getTimeOfTrafficLightOn,
            'SuccessRateWithoutCrash': CityModel.getsuccessRateWithoutCrash,
            'MovesByDriver': CityModel.getMovesByDriver}
        ) 
        # Add agents
        for row in range (rows):
            for col in range (columns):
                if row == 0 and (col <= 9 or 10 < col <= 19) or row == 10 and ( 1 <= col <= 9 or 10 < col <= 19):
                    self.addAgent(RoadAgent(self.next_id(), self, ["north"]), row, col)  
                if row == 20 and  1 <= col <= 20:
                    self.addAgent(RoadAgent(self.next_id(), self, ["south"]), row, col) 
                if col == 20 and (0 <= row <= 19) or col == 10 and ( 1 <= row <= 9 or 10 < row <= 19):
                    self.addAgent(RoadAgent(self.next_id(), self, ["east"]), row, col) 
                if col == 0 and (1 <= row <= 9 or 10 < row <= 20):
                    self.addAgent(RoadAgent(self.next_id(), self, ["west"]), row, col) 
                if (row == 0 and col == 10) or (row == 10 and col == 10):
                    self.addAgent(RoadAgent(self.next_id(), self, ["north", "east"]), row, col) 
                if row == 10 and col == 0:
                    self.addAgent(RoadAgent(self.next_id(), self, ["north", "west"]), row, col) 
                # First intersection
                if (col == 10 and row == 9): 
                    smt1 = SmartTrafficLightAgent(self.next_id(), self, 9, "east", driverSample)
                    self.addAgent(smt1, row, col) 
                if (col == 9 and row == 10): 
                    smt2 = SmartTrafficLightAgent(self.next_id(), self, 9, "north", driverSample)
                    self.addAgent(smt2, row, col) 
                # Second intersection
                if (col == 20 and row == 9): 
                    smt3 = SmartTrafficLightAgent(self.next_id(), self, 9, "east", driverSample)
                    self.addAgent(smt3, row, col) 
                if (col == 19 and row == 10): 
                    smt4 = SmartTrafficLightAgent(self.next_id(), self, 9, "north", driverSample)
                    self.addAgent(smt4, row, col)
                # Third intersection
                if (col == 11 and row == 20): 
                    smt5 = SmartTrafficLightAgent(self.next_id(), self, 9, "south", driverSample)
                    self.addAgent(smt5, row, col) 
                if (col == 10 and row == 19): 
                    smt6 = SmartTrafficLightAgent(self.next_id(), self, 9, "east", driverSample)
                    self.addAgent(smt6, row, col) 
        # Add intersections
        self.addAgent(IntersectionTrafficLightsAgent(self.next_id(), self, smt1, smt2, driverSample), 10, 10)
        self.addAgent(IntersectionTrafficLightsAgent(self.next_id(), self, smt3, smt4, driverSample), 10, 20)
        self.addAgent(IntersectionTrafficLightsAgent(self.next_id(), self, smt5, smt6, driverSample), 20, 10)

    def addAgent(self, agent, row, col) -> None:
        self.schedule.add(agent)
        self.grid.place_agent(agent,(row, col))
    
    def next_id(self) -> int:
        self.current_id += 1
        return self.current_id

    def createDriver(self) -> None:
        corners = [(0, 0), (20, 0), (0, 20), (20, 20)]
        index = self.steps % 4
        row, col = corners[index]
        self.addAgent(DriverAgent(self.next_id(), self, self.driverType), row, col)
                  
    def run_model(self) -> None:
        while self.running:
            self.step()
            
    def step(self) -> None:
        self.schedule.step()
        if self.steps < self.agents: self.createDriver()
        self.steps += 1
        self.datacollector.collect(self)
        
    # Funciones se modifica segun heurisitca de cada quien 
    @staticmethod
    def getNumberOfCrashes(model) -> int: # to do
        intersections = [agent for agent in model.schedule.agents if type(agent) == IntersectionTrafficLightsAgent]
        for intersection in intersections:
            agentsInCell =  model.grid.get_cell_list_contents([intersection.pos]) 
            for agent in agentsInCell:
                if type(agent) == DriverAgent and len(agentsInCell) >= 4: model.crashes += 1
        return model.crashes
    
    @staticmethod
    def getCurrentCongestion(model) -> int: # to do 
        currentCongestion = 0
        intersections = [agent for agent in model.schedule.agents if type(agent) == IntersectionTrafficLightsAgent]
        for intersection in intersections:
            currentCongestion += intersection.getCongestion()
        return currentCongestion

    @staticmethod
    def getSanity(model) -> int:
        currentSanity = 0
        drivers = [agent for agent in model.schedule.agents if type(agent) == DriverAgent]
        for driver in drivers:
            currentSanity += driver.getSanity()
        return currentSanity

    @staticmethod
    def getTimeOfTrafficLightOn(model) -> int:
        totalTime = 0
        stoplights = [agent for agent in model.schedule.agents if type(agent) == SmartTrafficLightAgent]
        for stoplight in stoplights:
            if stoplight.color != "red":
                totalTime += 1

        
        return totalTime

    @staticmethod
    def getsuccessRateWithoutCrash(model) -> int:
        success = 0
        if model.crashes > 0:
            success = 0
        else:
            success += 1
        return success            
        


    @staticmethod
    def getMovesByDriver(model) -> int:
        drivers = [agent for agent in model.schedule.agents if type(agent) == DriverAgent]
        for driver in drivers:
            model.moves += driver.getMoves()
        return model.moves
