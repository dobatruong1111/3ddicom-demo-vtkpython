import vtk
import numpy as np
from typing import List

"""
    description: 
        calculate input data for transfer function
    params:
        colormap: a standard for color map with each CT number (HU)
    return: a list contains other lists, sub lists have size = 4 with format: [CT number, red color, green color, blue color], colors between 0 and 1
"""
def to_rgb_points(colormap: List[dict]) -> List[list]:
    rgb_points = []
    for item in colormap:
        crange = item["range"]
        color = item["color"]
        for idx, r in enumerate(crange):
            if len(color) == len(crange):
                rgb_points.append([r] + color[idx])
            else:
                rgb_points.append([r] + color[0])
    return rgb_points

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
def convertFromDisplayCoords2WorldCoords(focalPoint: List[float], point: List[int], renderer: vtk.vtkRenderer) -> List[float]:
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
    return pickPosition

"""
    description: convert a point from the world coordinate system to the display coordinate system
    params:
        renderer: vtkRenderer object used to convert coordinates
        point: a point (in the world coordinate system)
    return: a point (in the display coordinate system)
"""
def convertFromWorldCoords2DisplayCoords(renderer: vtk.vtkRenderer, point: List[float]) -> List[float]:
    renderer.SetWorldPoint(point[0], point[1], point[2], 1)
    renderer.WorldToDisplay()
    return list(renderer.GetDisplayPoint())

"""
    description: calculate the euclide distance between two points, note: two points in the same coordinate system
    params: two points
    return: the euclidean distance
"""
def getEuclideanDistanceBetween2Points(firstPoint: List[float], secondPoint: List[float]) -> float:
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
def findProjectionPoint(firstPoint: List[float], secondPoint: List[float], directionOfProjection: List[float]) -> List[float]:
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
    return [x(t), y(t), z(t)]

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
def getPickPosition(cellPicker: vtk.vtkCellPicker, point: List[int], renderer: vtk.vtkRenderer, camera: vtk.vtkCamera, checkToGetProjectionPoint=False, firstPoint=None) -> List[float]:
    pickPosition = None
    check = cellPicker.Pick(point[0], point[1], 0, renderer)
    if check:
        pickPosition = list(cellPicker.GetPickPosition())
    else:
        pickPosition = convertFromDisplayCoords2WorldCoords(camera.GetFocalPoint(), point, renderer)
        if checkToGetProjectionPoint:
            projectionPoint = findProjectionPoint(firstPoint, pickPosition, camera.GetDirectionOfProjection())
            pickPosition = projectionPoint
    return pickPosition

"""
    description:
        class contains objects for drawing line in the world coordinate system
"""
class MeasureLengthPipeLine():
    def __init__(self) -> None:
        self.color = vtk.vtkNamedColors()
        self.isDragging = False

        # Line
        # vtkPolyData represents a geometric structure consisting of vertices, lines, polygons, and/or triangle strips
        self.line = vtk.vtkPolyData()
        # vtkTubeFilter is a filter that generates a tube around each input line
        self.tubeFilter = vtk.vtkTubeFilter()
        self.tubeFilter.SetInputData(self.line)
        self.tubeFilter.SetNumberOfSides(20)
        self.tubeFilter.SetRadius(1)
        # line mapper
        self.lineMapper = vtk.vtkPolyDataMapper()
        self.lineMapper.SetInputConnection(self.tubeFilter.GetOutputPort())
        # line actor
        self.lineActor = vtk.vtkActor()
        self.lineActor.SetMapper(self.lineMapper)
        self.lineActor.GetProperty().SetColor(self.color.GetColor3d("Tomato"))
        self.lineActor.GetProperty().SetLineWidth(2)
        self.lineActor.VisibilityOff()

        # Display the length of two points in the world coordinate system
        # vtkTextActor is an actor that displays text
        self.textActor = vtk.vtkTextActor()
        textProperty = self.textActor.GetTextProperty()
        textProperty.SetColor(self.color.GetColor3d("Tomato"))
        textProperty.SetFontSize(15)
        textProperty.ShadowOn()
        textProperty.BoldOn()
        self.textActor.VisibilityOff()

        # Marking the first point and the second point by two spheres
        self.sphere = vtk.vtkSphereSource()
        self.sphere.SetRadius(5)
        
        self.firstSphereMapper = vtk.vtkPolyDataMapper()
        self.firstSphereMapper.SetInputConnection(self.sphere.GetOutputPort())
        
        self.firstSphereActor = vtk.vtkActor()
        self.firstSphereActor.GetProperty().SetColor(1, 0, 0)
        self.firstSphereActor.SetMapper(self.firstSphereMapper)
        self.firstSphereActor.VisibilityOff()
        # ---
        self.secondSphereMapper = vtk.vtkPolyDataMapper()
        self.secondSphereMapper.SetInputConnection(self.sphere.GetOutputPort())
        
        self.secondSphereActor = vtk.vtkActor()
        self.secondSphereActor.GetProperty().SetColor(1, 0, 0)
        self.secondSphereActor.SetMapper(self.secondSphereMapper)
        self.secondSphereActor.VisibilityOff()

"""
    description: 
        BeforeMeasureLengthInteractorStyle class extends vtkInteractorStyleTrackballCamera class
        vtkInteractorStyleTrackballCamera allows the user to interactively manipulate (rotate, pan, etc.) the camera
        Set interactor style before measure length 
"""
class BeforeMeasureLengthInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: MeasureLengthPipeLine) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)

    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # Override method of super class
        self.OnLeftButtonUp()
        
        style = MeasureLengthInteractorStyle(self.pipeline)
        self.GetInteractor().SetInteractorStyle(style)

"""
    description: 
        MeasureLengthInteractorStyle class extends vtkInteractorStyleTrackballCamera class
        Set interactor style for measure length
"""
class MeasureLengthInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: MeasureLengthPipeLine) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.__leftButtonPressEvent)
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)

    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # vtkRenderer object
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()

        # vtkCamera object
        camera = renderer.GetActiveCamera()

        # The position of mouse in the display coordinate system
        eventPosition = self.GetInteractor().GetEventPosition()

        # vtkCellPicker object, it shoots a ray into the volume and returns the point where the ray intersects an isosurface of a chosen opacity
        cellPicker = self.GetInteractor().GetPicker()

        if self.pipeline.isDragging:
            # vtkPoints represents 3D points
            points = self.pipeline.line.GetPoints()
            firstPoint = points.GetPoint(0)
            pickPosition = getPickPosition(cellPicker, eventPosition, renderer, camera, True, firstPoint)

            # Marking the second point when drawing
            self.pipeline.secondSphereActor.SetPosition(pickPosition)
            self.pipeline.secondSphereActor.VisibilityOn()

            # Save the second point
            points.SetPoint(1, pickPosition)

            # vtkIdList may represent any type of integer id, but usually represents point and cell ids
            idList = vtk.vtkIdList()
            idList.InsertNextId(0) # Insert id of the first point
            idList.InsertNextId(1) # Insert id of the second point

            # Insert a cell of type VTK_LINE
            self.pipeline.line.InsertNextCell(vtk.VTK_LINE, idList)

            # Update the modification time for this object and its Data
            points.Modified()

            secondPoint = points.GetPoint(1)
            # Calculate the middle point
            midPoint = list(map(lambda i,j: (i+j)/2, firstPoint, secondPoint))
            # Calculate the euclidean distance between the first point and the second point
            distance = getEuclideanDistanceBetween2Points(firstPoint, secondPoint)
            # Convert the middle point from the world coordinate system to the display coordinate system 
            displayCoords = convertFromWorldCoords2DisplayCoords(renderer, midPoint)

            # Display the distance and set position of text
            self.pipeline.textActor.SetInput(f"{round(distance, 1)}mm")
            self.pipeline.textActor.SetDisplayPosition(round(displayCoords[0]), round(displayCoords[1]))
            self.pipeline.textActor.VisibilityOn()
        else: # TODO: code need to processed in javascript
            pickPosition = getPickPosition(cellPicker, eventPosition, renderer, camera)
            # Marking the position of mouse in the world coordinate system when moving mouse 
            self.pipeline.firstSphereActor.SetPosition(pickPosition)
            self.pipeline.firstSphereActor.VisibilityOn()
        self.GetInteractor().Render()
    
    def __leftButtonPressEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.pipeline.isDragging = True # Start drawing
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()
        eventPosition = self.GetInteractor().GetEventPosition() # the position of mouse in display coordinate system 
        
        # vtkCellPicker object, it shoots a ray into the volume and returns the point where the ray intersects an isosurface of a chosen opacity
        cellPicker = self.GetInteractor().GetPicker()

        pickPosition = getPickPosition(cellPicker, eventPosition, renderer, camera)
    
        # Marking the first point when having left button down event
        self.pipeline.firstSphereActor.SetPosition(pickPosition)
        self.pipeline.firstSphereActor.VisibilityOn()

        # vtkPoints represents 3D points
        points = vtk.vtkPoints()
        # vtkCellArray object to represent cell connectivity
        aline = vtk.vtkCellArray()
        # Set objects into vtkPolyData object
        self.pipeline.line.SetPoints(points)
        self.pipeline.line.SetLines(aline)

        # Insert the first point into vtkPoints object when having left button down
        points.InsertNextPoint(pickPosition)
        # Insert the second point into vtkPoints object
        points.InsertNextPoint(0, 0, 0) # defauld

        # Turn on line actor object
        self.pipeline.lineActor.VisibilityOn()
        # Override method of super class
        self.OnLeftButtonDown()

    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.pipeline.isDragging = False # Stop drawing
        # Override method of super class
        self.OnLeftButtonUp()
        # Set interactor style when stop drawing
        style = UpdateLengthPositionInteractorStyle(self.pipeline)
        self.GetInteractor().SetInteractorStyle(style)

"""
    description:
        UpdateLengthPositionInteractorStyle class extends vtkInteractorStyleTrackballCamera class
        Set interactor style after drawing will update the position of text when having mouse move event
"""
class UpdateLengthPositionInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: MeasureLengthPipeLine) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
    
    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        points = self.pipeline.line.GetPoints()

        firstPoint = points.GetPoint(0); secondPoint = points.GetPoint(1)
        midPoint = list(map(lambda i,j: (i+j)/2, firstPoint, secondPoint))
        displayCoords = convertFromWorldCoords2DisplayCoords(renderer, midPoint)
        self.pipeline.textActor.SetDisplayPosition(round(displayCoords[0]), round(displayCoords[1]))

        self.GetInteractor().Render()
        # Override method of super class
        self.OnMouseMove()

def main():
    STANDARD = [
            {
                "name": 'air',
                "range": [-1000],
                "color": [[0, 0, 0]] # black
            },
            {
                "name": 'lung',
                "range": [-600, -400],
                "color": [[194 / 255, 105 / 255, 82 / 255]]
            },
            {
                "name": 'fat',
                "range": [-100, -60],
                "color": [[194 / 255, 166 / 255, 115 / 255]]
            },
            {
                "name": 'soft tissue',
                "range": [40, 80],
                "color": [[102 / 255, 0, 0], [153 / 255, 0, 0]] # red
            },
            {
                "name": 'bone',
                "range": [400, 1000],
                "color": [[255 / 255, 217 / 255, 163 / 255]] # ~ white
            }
        ]
    path = "../dicomdata/Ankle"
    path2 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/220277460 Nguyen Thanh Dat/Unknown Study/CT 1.25mm Stnd KHONG TIEM"
    path3 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/64733 NGUYEN TAN THANH/DONG MACH CHI DUOI CTA/CT CTA iDose 5"

    rgb_points = to_rgb_points(STANDARD)
    colors = vtk.vtkNamedColors()
    reader = vtk.vtkDICOMImageReader()
    map = vtk.vtkSmartVolumeMapper()
    vol = vtk.vtkVolume()
    volProperty = vtk.vtkVolumeProperty()
    render = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    gradientOpacity = vtk.vtkPiecewiseFunction()
    scalarOpacity = vtk.vtkPiecewiseFunction()
    color = vtk.vtkColorTransferFunction()
    renIn = vtk.vtkRenderWindowInteractor()
    pipeline = MeasureLengthPipeLine()

    # outline
    # description: drawing a bounding box out volume object
    outline = vtk.vtkOutlineFilter()
    outline.SetInputConnection(reader.GetOutputPort())
    outlineMapper = vtk.vtkPolyDataMapper()
    outlineMapper.SetInputConnection(outline.GetOutputPort())
    outlineActor = vtk.vtkActor()
    outlineActor.SetMapper(outlineMapper)
    outlineActor.GetProperty().SetColor(0, 0, 0)
    
    reader.SetDirectoryName(path)
    reader.Update()
    
    # This option will use hardware accelerated rendering exclusively
    # This is a good option if you know there is hardware acceleration
    map.SetRequestedRenderModeToGPU()
    map.SetInputData(reader.GetOutput())

    volProperty.SetInterpolationTypeToLinear()
    volProperty.ShadeOn()
    # Lighting of volume
    volProperty.SetAmbient(0.1)
    volProperty.SetDiffuse(0.9)
    volProperty.SetSpecular(0.2)
    # Color map thought a transfer function
    for rgb_point in rgb_points:
        color.AddRGBPoint(rgb_point[0], rgb_point[1], rgb_point[2], rgb_point[3])
    volProperty.SetColor(color)

    # bone preset
    scalarOpacity.AddPoint(80, 0)
    scalarOpacity.AddPoint(400, 0.2)
    scalarOpacity.AddPoint(1000, 1)
    # muscle preset
    # scalarOpacity.AddPoint(-63.16470588235279, 0)
    # scalarOpacity.AddPoint(559.1764705882356, 1)
    volProperty.SetScalarOpacity(scalarOpacity)

    vol.SetMapper(map)
    vol.SetProperty(volProperty)

    render.SetBackground(colors.GetColor3d("White"))
    render.AddVolume(vol)
    render.AddActor(outlineActor)
    # Add actors of pipeline
    render.AddActor(pipeline.lineActor)
    render.AddActor(pipeline.textActor)
    render.AddActor(pipeline.firstSphereActor)
    render.AddActor(pipeline.secondSphereActor)
    
    renWin.SetWindowName("3D Dicom")
    renWin.SetSize(500, 500)
    renWin.AddRenderer(render)
    
    renIn.SetRenderWindow(renWin)
    cellPicker = vtk.vtkCellPicker()
    cellPicker.AddPickList(vol)
    cellPicker.PickFromListOn()
    renIn.SetPicker(cellPicker)
    style = BeforeMeasureLengthInteractorStyle(pipeline)
    renIn.SetInteractorStyle(style)

    renIn.Initialize()
    renIn.Start()

if __name__ == "__main__":
    main()