import vtk
from typing import List, Tuple
import numpy as np
import math

"""
    description:
        1. convert the focal point to the homogenous coordinate system
        2. convert the focal point to the display coordinate system then select the z element
        3. convert the input point (in the display coordinate system) with the z element selected above to the world coordinate system
    params:
        focalPoint: the focal point of the camera object (in world coordinate system)
        point: a point (in the display coordinate system) with z = 0
        renderer: vtkRenderer object used to convert coordinates
    return: a point (in the world coordinate system)
"""
def convertFromDisplayCoords2WorldCoords(focalPoint: Tuple[float], point: Tuple[int], renderer: vtk.vtkRenderer) -> Tuple[float]:
    # Get z when convert the focal point from the homogeneous coordinate system to the display coordinate system
    renderer.SetWorldPoint(focalPoint[0], focalPoint[1], focalPoint[2], 1) 
    renderer.WorldToDisplay()
    displayCoord = renderer.GetDisplayPoint()
    selectionz = displayCoord[2] # the distance from the camera position to the screen

    # Convert from the display coordinate system to the world coordinate system
    renderer.SetDisplayPoint(point[0], point[1], selectionz)
    renderer.DisplayToWorld()
    worldPoint = renderer.GetWorldPoint()

    # Convert from the homogeneous coordinate system to the world coordinate system
    pickPosition = [0, 0, 0]
    for i in range(3):
        pickPosition[i] = worldPoint[i] / worldPoint[3] if worldPoint[3] else worldPoint[i]
    return tuple(pickPosition)

"""
    description: convert a point from the world coordinate system to the display coordinate system
    params:
        renderer: vtkRenderer object used to convert coordinates
        point: a point (in the world coordinate system)
    return: a point (in the display coordinate system)
"""
def convertFromWorldCoords2DisplayCoords(renderer: vtk.vtkRenderer, point: Tuple[float]) -> Tuple[float]:
    renderer.SetWorldPoint(point[0], point[1], point[2], 1)
    renderer.WorldToDisplay()
    return renderer.GetDisplayPoint()

"""
    description: calculate the euclide distance between two points, note: two points in the same coordinate system
    params: two points
    return: the euclidean distance
"""
def getEuclideanDistanceBetween2Points(firstPoint: Tuple[float], secondPoint: Tuple[float]) -> float:
    return np.linalg.norm(np.array(secondPoint) - np.array(firstPoint))

"""
    description: 
        1. building a plane by the first point and the direction vector of projection
        2. after finding the projection point of the second point
    params:
        firstPoint: a point (in the world coordinate system)
        sencondPoint: a point (in the world coordinate system)
        directionOfProjection: a vector (in the world coordinate system)
    return: a projection point
"""
def findProjectionPoint(firstPoint: Tuple[float], secondPoint: Tuple[float], directionOfProjection: Tuple[float]) -> Tuple[float]:
    x1 = firstPoint[0]; y1 = firstPoint[1]; z1 = firstPoint[2]
    a = directionOfProjection[0]; b = directionOfProjection[1]; c = directionOfProjection[2]
    x2 = secondPoint[0]; y2 = secondPoint[1]; z2 = secondPoint[2]
    '''
        the first point: [x1, y1, z1] (in the world coordinate system)
        the direction of projection: [a, b, c] (the normal vector of the plane, the direction vector of the straight line)
        the second point: [x2, y2, z2] (in the world coordinate system)
        the plane equation: 
            a(x - x1) + b(y - y1) + c(z - z1) = 0
        linear equations:
            x = x2 + at
            y = y2 + bt
            z = z2 + ct
    '''
    x = lambda t: x2 + a * t
    y = lambda t: y2 + b * t
    z = lambda t: z2 + c * t
    t = (a * x1 - a * x2 + b * y1 - b * y2 + c * z1 - c * z2) / (a*a + b*b + c*c)
    return (x(t), y(t), z(t))

"""
    description:
        method returns a point (on surface or out in the world coordinate system) through vtkCellPicker object
        method can return a projection point (in case out).
    params:
        cellPicker: vtkCellPicker object used to get a point on surface
        point: a point (in the display coordinate system)
        renderer: vtkRenderer object used to convert coordinates
        camera: vtkCamera object used to get focal point and direction of projection

        checkToGetProjectionPoint: check to get a projection point of the second point, default=False, type=bool
        firstPoint: a point (in the world coordinate system), default=None, type=List
        if checkToGetProjectionPoint=True, finding a plane thought the first point. After finding a projection point of the second point on plane
    return: a point (in the world coordinate system)
"""
def getPickPosition(cellPicker: vtk.vtkCellPicker, point: Tuple[int], renderer: vtk.vtkRenderer, camera: vtk.vtkCamera, checkToGetProjectionPoint=False, firstPoint=None) -> Tuple[float]:
    pickPosition = None
    check = cellPicker.Pick(point[0], point[1], 0, renderer)
    if check:
        pickPosition = cellPicker.GetPickPosition()
    else:
        pickPosition = convertFromDisplayCoords2WorldCoords(camera.GetFocalPoint(), point, renderer)
        if checkToGetProjectionPoint:
            projectionPoint = findProjectionPoint(firstPoint, pickPosition, camera.GetDirectionOfProjection())
            pickPosition = projectionPoint
    return pickPosition

def getAngleDegrees(p1: Tuple[float], c: Tuple[float], p2: Tuple[float], option="Minimal") -> float:
    vtkmath = vtk.vtkMath()
    EPSILON = 1e-5

    if vtkmath.Distance2BetweenPoints(p1, c) <= EPSILON and vtkmath.Distance2BetweenPoints(p2, c) <= EPSILON:
        return 0.0

    vector1 = [p1[0] - c[0], p1[1] - c[1], p2[2] - c[2]]
    vector2 = [p2[0] - c[0], p2[1] - c[1], p2[2] - c[2]]
    vtkmath.Normalize(vector1)
    vtkmath.Normalize(vector2)
    angleRad = math.acos(vtkmath.Dot(vector1, vector2))
    angleDeg = vtkmath.DegreesFromRadians(angleRad)
    
    if option == "Minimal":
        return angleDeg
    else:
        if option == "OrientedSigned":
            return -1.0 * angleDeg
        elif option == "OrientedPositive":
            return 360.0 - angleDeg
    return 0.0