from enum import Enum
import struct
import json
from collections import defaultdict
from modules.MapName import MapName
from modules.Memory import ReadSymbol, readBytes, readuInt, readuShort

mapHeaderArr = ReadSymbol('gmapgroups', size=MapName.MAP_GROUPS_COUNT.value * 4)
def getMapHeaderPtr(map:MapName):
    mapGroup = map.value >> 8
    mapNum = map.value & 0xff
    return readuInt(struct.unpack('<I',mapHeaderArr[mapGroup * 4 : mapGroup * 4 +  4])[0] + mapNum * 4) 

mapHeaderConnectionOffset = 0xc
mapConnectionsOffset = 0x4
ConnectionMapGroupOffset = 0x8
mapConnectionSize = 12
def getMapConnectionsData(mapHeaderPtr: int):
    mapConnectionPtr = readuInt(mapHeaderPtr + mapHeaderConnectionOffset)
    connectionSize = readuInt(mapConnectionPtr)
    return (connectionSize, readuInt(mapConnectionPtr + mapConnectionsOffset))

class Direction(Enum):
    DOWN = 0
    UP = 1
    LEFT = 2
    RIGHT = 3

# Masks/shifts for blocks in the map grid
# Map grid blocks consist of a 10 bit metatile id, a 2 bit collision value, and a 4 bit elevation value
# This is the data stored in each data/layouts/*/map.bin file
MAPGRID_METATILE_ID_MASK = 0x03FF # Bits 1-10
MAPGRID_COLLISION_MASK = 0x0C00 # Bits 11-12
MAPGRID_ELEVATION_MASK = 0xF000 # Bits 13-16
MAPGRID_COLLISION_SHIFT = 10
MAPGRID_ELEVATION_SHIFT = 12

# hack for forward declaration for type hints
class Map(object):
    pass

class Tile(object):        
    def __init__(self, num: int, x: int, y: int, map: Map) -> None:
        self.metaTile = num & MAPGRID_METATILE_ID_MASK
        self.collision = (num & MAPGRID_COLLISION_MASK) >> MAPGRID_COLLISION_SHIFT
        self.elevation = (num & MAPGRID_ELEVATION_MASK) >> MAPGRID_ELEVATION_SHIFT
        self.x = x
        self.y = y
        self.map : Map = map

emeraldPath = "C:\Home\pokeemerald\\" # where the emerald decomp is would be changed 

MAP_LAYOUT_HEIGHT_OFFSET = 0x4
MAP_LAYOUT_DATA_OFFSET = 0xc
class Map(object):

    def getMapName(mapIndex: int) -> MapName:
        return MapName(((mapIndex & 0xff) << 8 )+ (mapIndex >> 8))

    def mapConnections(connectionData: tuple[int, int]):
        connectionInfo = [None] * 4
        for connection in range(connectionData[0]):
            direction = Direction(readuInt(connectionData[1] + connection * mapConnectionSize) - 1)
            mapName = Map.getMapName(readuShort(connectionData[1] + connection * mapConnectionSize + ConnectionMapGroupOffset))
            connectionInfo[direction.value] = mapName
        return connectionInfo

    def __init__(self, mapName: MapName) -> None:
        mapHeaderPtr = getMapHeaderPtr(mapName)
        mapLayoutPtr = readuInt(mapHeaderPtr)
        self.width = readuInt(mapLayoutPtr)
        self.height = readuInt(mapLayoutPtr + MAP_LAYOUT_HEIGHT_OFFSET)
        self.name = mapName
        mapLayoutDataPtr = readuInt(mapLayoutPtr + MAP_LAYOUT_DATA_OFFSET)
        self.connections = Map.mapConnections(getMapConnectionsData(mapHeaderPtr))
        self.tiles = list()
        for y in range(self.height):
            self.tiles.append(list())
            for x in range(self.width):
                data = readuShort(mapLayoutDataPtr + (y * self.width + x) * 2)
                self.tiles[y].append(Tile(data, x, y, self))

    def getCollisionAt(self, x: int, y: int) -> int:
        return self.tiles[y][x].collision
    def getTileAt(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]


class Graph(object):
    def __init__(self,maps: dict[MapName, Map]) -> None:
        self.graph = defaultdict(list)
        self.createVertex(maps)
        self.createEdges(maps)
    
    def createVertex(self,maps: dict[MapName, Map]) -> None:
        for map in maps:
            for row in maps[map].tiles:
                for tile in row:
                    self.graph[tile] = list()

    def addAdjacentEdges(self,vertex: Tile):
        if vertex.map.width > vertex.x + 1 and vertex.map.getCollisionAt(vertex.x + 1, vertex.y) == 0:
            self.graph[vertex].append(vertex.map.getTileAt(vertex.x + 1, vertex.y))

        if 0 <= vertex.x - 1 and vertex.map.getCollisionAt(vertex.x - 1, vertex.y) == 0:
            self.graph[vertex].append(vertex.map.getTileAt(vertex.x - 1, vertex.y))

        if vertex.map.height > vertex.y + 1 and vertex.map.getCollisionAt(vertex.x, vertex.y + 1) == 0:
            self.graph[vertex].append(vertex.map.getTileAt(vertex.x, vertex.y + 1))

        if 0 <= vertex.y - 1 and vertex.map.getCollisionAt(vertex.x, vertex.y - 1) == 0:
            self.graph[vertex].append(vertex.map.getTileAt(vertex.x, vertex.y - 1))

    def addMapConnection(self,vertex: Tile,maps: dict[MapName,Map]):
        mapConnections = vertex.map.connections
        if vertex.collision == 0 and vertex.x == 0:
            if mapConnections[Direction.LEFT.value] != None \
                and mapConnections[Direction.LEFT.value] in maps: # probably there is better way to check for non existans
                otherMap = maps[mapConnections[Direction.LEFT.value]]
                self.graph[vertex].append(otherMap.getTileAt(otherMap.width - 1,vertex.y))

        if vertex.collision == 0 and vertex.x == vertex.map.width - 1:
            if mapConnections[Direction.RIGHT.value] != None \
                and mapConnections[Direction.RIGHT.value] in maps: # probably there is better way to check for non existans
                otherMap = maps[mapConnections[Direction.RIGHT.value]]
                self.graph[vertex].append(otherMap.getTileAt(0,vertex.y))

        if vertex.collision == 0 and vertex.y == 0:
            if mapConnections[Direction.UP.value] != None \
                and mapConnections[Direction.UP.value] in maps: # probably there is better way to check for non existans
                otherMap = maps[mapConnections[Direction.UP.value]]
                self.graph[vertex].append(otherMap.getTileAt(vertex.x,otherMap.height - 1))

        if vertex.collision == 0 and vertex.y == vertex.map.height - 1:
            if mapConnections[Direction.RIGHT.value] != None \
                and mapConnections[Direction.RIGHT.value] in maps: # probably there is better way to check for non existans
                otherMap = maps[mapConnections[Direction.RIGHT.value]]
                self.graph[vertex].append(otherMap.getTileAt(vertex.x,0))



    def createEdges(self, maps: dict[MapName,Map]):
        for vertex in self.graph:
            self.addAdjacentEdges(vertex)
            self.addMapConnection(vertex,maps)
            

    def shortestPath(self, src: Tile, dest: Tile):
        queue = [] # change it to real queue otherwise on big sets not efficient

        # all vertices are unvisited if visited would have true distance and predecessor
        verticesInfo = dict((el,[False]) for el in self.graph.keys())
        
        # now source is first to be visited and
        # distance from source to itself should be 0
        # verticesInfo for each vetrex [0] visted [1] distance from source [2] predecessor tile
        verticesInfo[src][0] = True
        verticesInfo[src].append(0)
        queue.append(src)

        # bfs algorithm 
        while queue:
            u = queue[0]
            queue.pop(0)
            for neighbor in self.graph[u]:
                if (verticesInfo[neighbor][0] == False):
                    verticesInfo[neighbor][0] = True
                    verticesInfo[neighbor].append(verticesInfo[u][1] + 1) 
                    verticesInfo[neighbor].append(u)
                    queue.append(neighbor)
                    # We stop BFS when we find
                    # destination.
                    if (neighbor == dest):
                        return verticesInfo

        return None


def printCollision(mapName: MapName) -> None:
    map = Map(mapName)
    print(map.connections)
    for i in range(map.height):
        for j in range(map.width):
            print(str(map.getCollisionAt(j,i)) + ' ',end='')
        print()

    


# mapName = MapName.MAP_LITTLEROOT_TOWN
# printCollision(mapName)
# testGraph = Graph(maps)

def convertPathToTuple(path: dict, start: Tile,end: Tile) -> list[tuple[int, int]]:
    returnPath = [(end.x,end.y)]
    current = end
    while path[current][2] != start:
        returnPath.insert(0,(path[current][2].x,path[current][2].y)) #change it to better data struct
        current = path[current][2]
    returnPath.insert(0,(start.x, start.y))
    return returnPath


def getPath(start: tuple[int, int],end: tuple[int, int]):
    mapName = MapName.MAP_LITTLEROOT_TOWN
    mapName2 = MapName.MAP_ROUTE101
    maps = {mapName:Map(mapName) , mapName2:Map(mapName2)}
    testGraph = Graph(maps)
    startTile = maps[mapName].getTileAt(start[0],start[1])
    endTile = maps[mapName2].getTileAt(end[0],end[1])
    path = testGraph.shortestPath(startTile,endTile)
    return convertPathToTuple(path,startTile,endTile)



# recursively search all connected maps up to specified depth
def getConnectedMapsRec(map: MapName, depth: int, returnMaps: set):
    returnMaps.add(map)
    if depth <= 0:
       return
    
    mapHeaderPtr = getMapHeaderPtr(map)
    # mapConnectionPtr = readuInt(mapHeaderPtr + mapHeaderConnectionOffset)
    # connectionsPtr = readuInt(mapConnectionPtr + mapConnectionsOffset)
    connections = getMapConnectionsData(mapHeaderPtr)
    for i in range(connections[0]): #first field in connectionPtr is the amount of connections
        mapIndexes = struct.unpack('BB',readBytes(connections[1] + ConnectionMapGroupOffset + i * mapConnectionSize, 2))
        # mapIds =  struct.unpack('BB',mapIndexes) 
        # print(mapIds[1])
        if MapName((mapIndexes[0] << 8) + mapIndexes[1]) not in returnMaps:
            getConnectedMapsRec(MapName((mapIndexes[0] << 8) + mapIndexes[1]), depth - 1, returnMaps)



def getConnectedMaps(map: MapName, depth: int):
    returnList = set()
    getConnectedMapsRec(map, depth, returnList)
    return returnList