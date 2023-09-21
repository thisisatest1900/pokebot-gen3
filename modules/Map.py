import struct
import json
from collections import defaultdict
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
        self.map = map

emeraldPath = "C:\Home\pokeemerald\\" # where the emerald decomp is would be changed 

class Map(object):
    def __init__(self, mapInfo: dict) -> None:
        self.width = mapInfo['width']
        self.height = mapInfo['height']
        self.name = mapInfo['name']
        path = emeraldPath + mapInfo['blockdata_filepath']
        with open(path, "rb") as file:
            self.tiles = list()
            for y in range(self.height):
                self.tiles.append(list())
                for x in range(self.width):
                    data = struct.unpack("<H",file.read(2))[0]
                    self.tiles[y].append(Tile(data, x, y, self))

    def getCollisionAt(self, x: int, y: int) -> int:
        return self.tiles[y][x].collision
    def getTileAt(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]


class Graph(object):
    def __init__(self,maps: dict[str, Map]) -> None:
        self.graph = defaultdict(list)
        self.createVertex(maps)
        self.createEdges(maps)
    
    def createVertex(self,maps: dict[str, Map]) -> None:
        for map in maps:
            for row in maps[map].tiles:
                for tile in row:
                    self.graph[tile] = list()

    def createEdges(self, maps: dict[str,Map]):
        for vertex in self.graph:
            if vertex.map.width > vertex.x + 1 and vertex.map.getCollisionAt(vertex.x + 1, vertex.y) == 0:
                self.graph[vertex].append(vertex.map.getTileAt(vertex.x + 1, vertex.y))

            if 0 <= vertex.x - 1 and vertex.map.getCollisionAt(vertex.x - 1, vertex.y) == 0:
                self.graph[vertex].append(vertex.map.getTileAt(vertex.x - 1, vertex.y))

            if vertex.map.height > vertex.y + 1 and vertex.map.getCollisionAt(vertex.x, vertex.y + 1) == 0:
                self.graph[vertex].append(vertex.map.getTileAt(vertex.x, vertex.y + 1))

            if 0 <= vertex.y - 1 and vertex.map.getCollisionAt(vertex.x, vertex.y - 1) == 0:
                self.graph[vertex].append(vertex.map.getTileAt(vertex.x, vertex.y - 1))

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



def findMapIndex(name: str,layoutArr: list) ->int:
    for i,layout in enumerate(layoutArr):
        if layout['name'] == name:
            return i
    return -1


def printCollision(mapName: str, layouts: list) -> None:
    map = Map(layouts[findMapIndex(mapName,layouts)])
    for i in range(map.height):
        for j in range(map.width):
            print(str(map.getCollisionAt(j,i)) + ' ',end='')
        print()

    

layouts = json.load(open(emeraldPath + '\data\layouts\layouts.json'))['layouts']
mapName = 'Route101_Layout'
maps = {mapName: Map(layouts[findMapIndex(mapName,layouts)])}
testGraph = Graph(maps)

def convertPathToTuple(path: dict, start: Tile,end: Tile) -> list[tuple[int, int]]:
    returnPath = [(end.x,end.y)]
    current = end
    while path[current][2] != start:
        returnPath.insert(0,(path[current][2].x,path[current][2].y)) #change it to better data struct
        current = path[current][2]
    returnPath.insert(0,(start.x, start.y))
    return returnPath


def getPath(start: tuple[int, int],end: tuple[int, int]):
    startTile = maps[mapName].getTileAt(start[0],start[1])
    endTile = maps[mapName].getTileAt(end[0],end[1])
    path = testGraph.shortestPath(startTile,endTile)
    return convertPathToTuple(path,startTile,endTile)

