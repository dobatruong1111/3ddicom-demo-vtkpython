import vtk
import numpy as np
from typing import List

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

class MeasureLengthPipeLine():
    def __init__(self) -> None:
        self.color = vtk.vtkNamedColors()
        self.isDragging = False
        self.polyData = vtk.vtkPolyData()

        self.tubeFilter = vtk.vtkTubeFilter()
        self.tubeFilter.SetInputData(self.polyData)
        self.tubeFilter.SetNumberOfSides(20)
        self.tubeFilter.SetRadius(1)

        self.lineMapper = vtk.vtkPolyDataMapper()
        self.lineMapper.SetInputConnection(self.tubeFilter.GetOutputPort())

        self.lineActor = vtk.vtkActor()
        self.lineActor.SetMapper(self.lineMapper)
        self.lineActor.GetProperty().SetColor(self.color.GetColor3d("Tomato"))
        self.lineActor.GetProperty().SetSelectionPointSize(100)
        self.lineActor.GetProperty().SetLineWidth(2)
        self.lineActor.VisibilityOff()

        # disply the length of two points in world coords
        self.showLength = vtk.vtkTextActor()
        self.showLength.GetTextProperty().SetColor(self.color.GetColor3d("Tomato"))
        self.showLength.GetTextProperty().SetFontSize(15)
        self.showLength.GetTextProperty().SetOpacity(1)
        self.showLength.GetTextProperty().SetBackgroundOpacity(0)
        self.showLength.GetTextProperty().ShadowOn()
        self.showLength.GetTextProperty().BoldOn()
        self.showLength.VisibilityOff()

        # Draw/update the pick marker
        self.firstSphere = vtk.vtkSphereSource()
        self.firstSphere.SetRadius(5)

        self.firstSphereMapper = vtk.vtkPolyDataMapper()
        self.firstSphereMapper.SetInputConnection(self.firstSphere.GetOutputPort())

        self.firstSphereActor = vtk.vtkActor()
        self.firstSphereActor.GetProperty().SetColor(1, 0, 0)
        self.firstSphereActor.SetMapper(self.firstSphereMapper)
        self.firstSphereActor.VisibilityOff()
        # ---
        self.secondSphere = vtk.vtkSphereSource()
        self.secondSphere.SetRadius(5)

        self.secondSphereMapper = vtk.vtkPolyDataMapper()
        self.secondSphereMapper.SetInputConnection(self.secondSphere.GetOutputPort())

        self.secondSphereActor = vtk.vtkActor()
        self.secondSphereActor.GetProperty().SetColor(1, 0, 0)
        self.secondSphereActor.SetMapper(self.secondSphereMapper)
        self.secondSphereActor.VisibilityOff()

class InteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: MeasureLengthPipeLine) -> None:
        self.pipeline = pipeline
        self.AddObserver("LeftButtonReleaseEvent", self.leftButtonUp)

    def leftButtonUp(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.OnLeftButtonUp()
        style = MeasureLengthInteractorStyle(self.pipeline)
        self.GetInteractor().SetInteractorStyle(style)

class MeasureLengthInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: MeasureLengthPipeLine) -> None:
        self.pipeline = pipeline
        self.AddObserver("LeftButtonPressEvent", self.leftButtonDown)
        self.AddObserver("MouseMoveEvent", self.mouseMove)
        self.AddObserver("LeftButtonReleaseEvent", self.leftButtonUp)
    
    """
        description:
            1: convert the focal point to homogenous coordinate system.
            2: convert the focal point to display coordinate system then select the z element.
            3: convert the input point (in display coordinate system) with the z element selected above to world coordinate system
        params:
            focalPoint: a point (in world coordinate system)
            renderer: vtkRenderer object
            point: a point (in display coordinate system) with the z element is None
        return: a point (in world coordinate system)
    """
    @staticmethod
    def convertFromDisplayCoords2WorldCoords(focalPoint: List[float], renderer: vtk.vtkRenderer, point: List[int]) -> List[float]:
        # get z when convert the focal point from homogeneous coords (4D) to display coords (3D)
        renderer.SetWorldPoint(focalPoint[0], focalPoint[1], focalPoint[2], 1) 
        renderer.WorldToDisplay() # 4D -> 3D
        displayCoord = renderer.GetDisplayPoint()
        selectionz = displayCoord[2] # (the distance from the camera position to the screen)

        # get 3D coords when convert from display coords (3D) to world coords (4D)
        renderer.SetDisplayPoint(point[0], point[1], selectionz)
        renderer.DisplayToWorld() # 3D -> 4D
        worldPoint = renderer.GetWorldPoint()
        pickPosition = [0, 0, 0]
        for i in range(3):
            pickPosition[i] = worldPoint[i] / worldPoint[3] if worldPoint[3] else worldPoint[i]
        return pickPosition
    
    @staticmethod
    def convertFromWorldCoords2DisplayCoords(renderer: vtk.vtkRenderer, point: List[float]) -> List[float]:
        renderer.SetWorldPoint(point[0], point[1], point[2], 1)
        renderer.WorldToDisplay()
        return renderer.GetDisplayPoint()
    
    @staticmethod
    def getEuclideDistanceBetween2Points(firstPoint: List[float], secondPoint: List[float]) -> float:
        return np.linalg.norm(np.array(secondPoint) - np.array(firstPoint))

    """
        description: 
            building a plane by the first point and the direction vector of projection.
            after finding the projection point of the second point.
        params:
            firstPoint: a point (in world coordinate system)
            directionOfProjection: a vector (in world coordinate system)
            sencondPoint: a point (in world coordinate system)
        return: a projection point
    """
    @staticmethod
    def findProjectionPoint(firstPoint: List[float], directionOfProjection: List[float], secondPoint: List[float]) -> List[float]:
        x1 = firstPoint[0]; y1 = firstPoint[1]; z1 = firstPoint[2]
        a = directionOfProjection[0]; b = directionOfProjection[1]; c = directionOfProjection[2]
        x2 = secondPoint[0]; y2 = secondPoint[1]; z2 = secondPoint[2]
        '''
            first point: [x1, y1, z1] (in world coordinate system)
            direction of projection: [a, b, c] (the normal vector of the plane, the direction vector of the straight line)
            second point: [x2, y2, z2] (in world coordinate system)
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
            method returns a point (on surface or out in world coordinate system) through vtkCellPicker object.
            method can return a projection point (in case out).
        params:
            cellPicker: vtkCellPicker object
            eventPosition: a point (in display coordinate system)
            renderer: vtkRenderer object
            camera: vtkCamera object
            checkToGetProjectionPoint: default=False, type=bool
            firstPoint: a point (in world coordinate system) if return a projection point, default=None, type=List
        return: a point (in world coordinate system)
    """
    @staticmethod
    def getPickPosition(cellPicker: vtk.vtkCellPicker, eventPosition: List[int], renderer: vtk.vtkRenderer, camera: vtk.vtkCamera, checkToGetProjectionPoint=False, firstPoint=None) -> List:
        pickPosition = None
        check = cellPicker.Pick(eventPosition[0], eventPosition[1], 0, renderer)
        if check:
            pickPosition = cellPicker.GetPickPosition()
        else:
            pickPosition = MeasureLengthInteractorStyle.convertFromDisplayCoords2WorldCoords(camera.GetFocalPoint(), renderer, eventPosition)
            if checkToGetProjectionPoint:
                projectionPoint = MeasureLengthInteractorStyle.findProjectionPoint(firstPoint, camera.GetDirectionOfProjection(), pickPosition)
                pickPosition = projectionPoint
        return pickPosition

    def mouseMove(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()
        eventPosition = self.GetInteractor().GetEventPosition()
        if self.pipeline.isDragging:
            points = self.pipeline.polyData.GetPoints()
            pickPosition = self.getPickPosition(self.GetInteractor().GetPicker(), eventPosition, renderer, camera, True, points.GetPoint(0))

            self.pipeline.secondSphereActor.SetPosition(pickPosition)
            self.pipeline.secondSphereActor.VisibilityOn()

            points.SetPoint(1, [pickPosition[0], pickPosition[1], pickPosition[2]])

            idList = vtk.vtkIdList()
            idList.InsertNextId(0)
            idList.InsertNextId(1)

            self.pipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)
            points.Modified()

            firstPoint = points.GetPoint(0); secondPoint = points.GetPoint(1)
            distance = self.getEuclideDistanceBetween2Points(firstPoint, secondPoint)
            self.pipeline.showLength.SetInput(f"{round(distance, 1)}mm")
            midPoint = [(firstPoint[0] + secondPoint[0])/2, (firstPoint[1] + secondPoint[1])/2, (firstPoint[2] + secondPoint[2])/2]
            temp = self.convertFromWorldCoords2DisplayCoords(renderer, midPoint)
            self.pipeline.showLength.SetDisplayPosition(round(temp[0]), round(temp[1]))
            self.pipeline.showLength.VisibilityOn()
        else:
            pickPosition = self.getPickPosition(self.GetInteractor().GetPicker(), eventPosition, renderer, camera)
            self.pipeline.firstSphereActor.SetPosition(pickPosition)
            self.pipeline.firstSphereActor.VisibilityOn()
        self.GetInteractor().Render()
    
    def leftButtonDown(self, obj:vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.pipeline.isDragging = True
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()
        eventPosition = self.GetInteractor().GetEventPosition()
        pickPosition = self.getPickPosition(self.GetInteractor().GetPicker(), eventPosition, renderer, camera)
    
        self.pipeline.firstSphereActor.SetPosition(pickPosition)
        self.pipeline.firstSphereActor.VisibilityOn()

        points = vtk.vtkPoints()
        line = vtk.vtkCellArray()
        self.pipeline.polyData.SetPoints(points)
        self.pipeline.polyData.SetLines(line)

        points.InsertNextPoint(pickPosition[0], pickPosition[1], pickPosition[2])
        points.InsertNextPoint(0, 0, 0) # defauld

        self.pipeline.lineActor.VisibilityOn()
        self.OnLeftButtonDown()

    def leftButtonUp(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.pipeline.isDragging = False
        self.OnLeftButtonUp()
        style = UpdateLengthPositionInteractorStyle(self.pipeline)
        self.GetInteractor().SetInteractorStyle(style)

class UpdateLengthPositionInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: MeasureLengthPipeLine) -> None:
        self.pipeline = pipeline
        self.AddObserver("MouseMoveEvent", self.mouseMove)
    
    def mouseMove(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        points = self.pipeline.polyData.GetPoints()
        firstPoint = points.GetPoint(0); secondPoint = points.GetPoint(1)
        midPoint = [(firstPoint[0] + secondPoint[0])/2, (firstPoint[1] + secondPoint[1])/2, (firstPoint[2] + secondPoint[2])/2]
        temp = MeasureLengthInteractorStyle.convertFromWorldCoords2DisplayCoords(renderer, midPoint)
        self.pipeline.showLength.SetDisplayPosition(round(temp[0]), round(temp[1]))

        self.GetInteractor().Render()
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
    
    path = "C:/Users/DELL E5540/Desktop/Python/dicom-data/Ankle"
    path2 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/220277460 Nguyen Thanh Dat/Unknown Study/CT 1.25mm Stnd KHONG TIEM"

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
    """
        description: drawing a bounding box out volume object
    """
    outline = vtk.vtkOutlineFilter()
    outline.SetInputConnection(reader.GetOutputPort())
    outlineMapper = vtk.vtkPolyDataMapper()
    outlineMapper.SetInputConnection(outline.GetOutputPort())
    outlineActor = vtk.vtkActor()
    outlineActor.SetMapper(outlineMapper)
    outlineActor.GetProperty().SetColor(0, 0, 0)
    
    reader.SetDirectoryName(path)
    reader.Update()
    
    map.SetBlendModeToComposite()
    map.SetRequestedRenderModeToGPU()
    map.SetInputData(reader.GetOutput())

    volProperty.SetInterpolationTypeToLinear()
    volProperty.ShadeOn()
    volProperty.SetInterpolationTypeToLinear()
    volProperty.SetAmbient(0.1)
    volProperty.SetDiffuse(0.9)
    volProperty.SetSpecular(0.2)
    for rgb_point in rgb_points:
        color.AddRGBPoint(rgb_point[0], rgb_point[1], rgb_point[2], rgb_point[3])
    volProperty.SetColor(color)

    # bone preset
    scalarOpacity.AddPoint(80, 0)
    scalarOpacity.AddPoint(400, 0.2)
    scalarOpacity.AddPoint(1000, 1)
    # scalarOpacity.AddPoint(-63.16470588235279, 0)
    # scalarOpacity.AddPoint(559.1764705882356, 1)
    volProperty.SetScalarOpacity(scalarOpacity)

    vol.SetMapper(map)
    vol.SetProperty(volProperty)

    render.SetBackground(colors.GetColor3d("White"))
    render.AddVolume(vol)
    render.AddActor(outlineActor)
    # render.getActorByName("my3dobject")
    render.AddActor(pipeline.lineActor)
    render.AddActor(pipeline.showLength)
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
    style = InteractorStyle(pipeline)
    renIn.SetInteractorStyle(style)

    renIn.Initialize()
    renIn.Start()

if __name__ == "__main__":
    main()