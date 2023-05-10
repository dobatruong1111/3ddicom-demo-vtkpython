from typing import List
import vtk
import utils

"""
    description:
        class contains objects for angle measurement in the world coordinate system
"""
class AngleMeasurementPipeline():
    def __init__(self) -> None:
        colors = vtk.vtkNamedColors()
        self.isDragging = False

        # Line
        self.line = vtk.vtkPolyData()

        # Arc
        self.arc = vtk.vtkArcSource()
        self.arc.SetResolution(30)

        # Sphere
        self.sphere = vtk.vtkSphereSource()
        self.sphere.SetRadius(5)

        # Filter
        # vtkTubeFilter is a filter that generates a tube around each input line
        self.tubeFilter = vtk.vtkTubeFilter()
        self.tubeFilter.SetInputData(self.line)
        self.tubeFilter.SetNumberOfSides(20)
        self.tubeFilter.SetRadius(1)

        self.arcTubeFilter = vtk.vtkTubeFilter()
        self.arcTubeFilter.SetInputConnection(self.arc.GetOutputPort())
        self.arcTubeFilter.SetNumberOfSides(20)
        self.arcTubeFilter.SetRadius(1)

        # Mappers
        self.firstLineMapper = vtk.vtkPolyDataMapper()
        self.firstLineMapper.SetInputConnection(self.tubeFilter.GetOutputPort())

        self.secondLineMapper = vtk.vtkPolyDataMapper()
        self.secondLineMapper.SetInputConnection(self.tubeFilter.GetOutputPort())

        self.arcMapper = vtk.vtkPolyDataMapper()
        self.arcMapper.SetInputConnection(self.arcTubeFilter.GetOutputPort())

        self.firstSphereMapper = vtk.vtkPolyDataMapper()
        self.firstSphereMapper.SetInputConnection(self.sphere.GetOutputPort())

        self.secondSphereMapper = vtk.vtkPolyDataMapper()
        self.secondSphereMapper.SetInputConnection(self.sphere.GetOutputPort())

        self.thirdSphereMapper =  vtk.vtkPolyDataMapper()
        self.thirdSphereMapper.SetInputConnection(self.sphere.GetOutputPort())

        # Actors
        property = vtk.vtkProperty()
        property.SetColor(colors.GetColor3d("Tomato"))
        property.SetLineWidth(2)

        # connecting the first point with the second point
        self.firstLineActor = vtk.vtkActor()
        self.firstLineActor.SetMapper(self.firstLineMapper)
        self.firstLineActor.SetProperty(property)
        self.firstLineActor.VisibilityOff()

        # connecting the second point with the third point
        self.secondLineActor = vtk.vtkActor()
        self.secondLineActor.SetMapper(self.secondLineMapper)
        self.secondLineActor.SetProperty(property)
        self.secondLineActor.VisibilityOff()

        # arc
        self.arcActor = vtk.vtkActor()
        self.arcActor.SetMapper(self.arcMapper)
        self.arcActor.SetProperty(property)
        self.arcActor.VisibilityOff()

        # used to display angle between two vectors
        self.textActor = vtk.vtkTextActor()
        textProperty = self.textActor.GetTextProperty()
        textProperty.SetColor(colors.GetColor3d("Tomato"))
        textProperty.SetFontSize(15)
        textProperty.ShadowOn()
        textProperty.BoldOn()
        self.textActor.VisibilityOff()

        # used to mark the first point
        self.firstSphereActor = vtk.vtkActor()
        self.firstSphereActor.SetMapper(self.firstSphereMapper)
        self.firstSphereActor.GetProperty().SetColor(0, 1, 0)
        self.firstSphereActor.VisibilityOff()

        # used to mark the second point
        self.secondSphereActor = vtk.vtkActor()
        self.secondSphereActor.SetMapper(self.secondSphereMapper)
        self.secondSphereActor.GetProperty().SetColor(0, 1, 0)
        self.secondSphereActor.VisibilityOff()

        # used to mark the third point
        self.thirdSphereActor = vtk.vtkActor()
        self.thirdSphereActor.SetMapper(self.thirdSphereMapper)
        self.thirdSphereActor.GetProperty().SetColor(0, 1, 0)
        self.thirdSphereActor.VisibilityOff()

"""
    description:
        BeforeAngleMeasurementInteractorStyle class extends vtkInteractorStyleTrackballCamera class
        vtkInteractorStyleTrackballCamera allows the user to interactively manipulate (rotate, pan, etc.) the camera
        Set interactor style before angle measurement
"""
class BeforeAngleMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: AngleMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)
    
    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.OnLeftButtonUp()
        style = AngleMeasurementInteractorStyle(self.pipeline)
        self.GetInteractor().SetInteractorStyle(style)

"""
    description: 
        AngleMeasurementInteractorStyle class extends vtkInteractorStyleTrackballCamera class
        Set interactor style for angle measurement
"""
class AngleMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: AngleMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.checkNumberOfPoints = 0 # used to check current number of points
        self.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.__leftButtonPressEvent)
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)

    """
        description:
            method used to calculate the angle between vectors (in the world coordinate system), the arc and the position of text actor (in the display coordinate system)
        params:
            renderer: used to convert coordinates
            vtkmath: used to calculate
            pipeline: a class contains objects for angle measurement
    """
    @staticmethod
    def buildArc(renderer: vtk.vtkRenderer, vtkmath: vtk.vtkMath, pipeline: AngleMeasurementPipeline) -> None:
        points = pipeline.line.GetPoints() # vtkPoints object contains three points

        # Get three points
        p1 = points.GetPoint(0)
        c = points.GetPoint(1)
        p2 = points.GetPoint(2)

        angle = utils.getAngleDegrees(p1, c, p2) # Calculate the angle
        longArc = False # By default the arc spans the shortest angular sector

        vector1 = [p1[0] - c[0], p1[1] - c[1], p1[2] - c[2]]
        vector2 = [p2[0] - c[0], p2[1] - c[1], p2[2] - c[2]]

        if (abs(vector1[0]) < 0.001 and abs(vector1[1]) < 0.001 and abs(vector1[2]) < 0.001) or (abs(vector2[0]) < 0.001 and abs(vector2[1]) < 0.001 and abs(vector2[2]) < 0.001):
            return
        
        # Return norm of vector
        l1 = vtkmath.Normalize(vector1) 
        l2 = vtkmath.Normalize(vector2)

        length = l1 if l1 < l2 else l2 # Get min
        anglePlacementRatio = 0.5
        angleTextPlacementRatio = 0.7
        lArc = length * anglePlacementRatio
        lText = length * angleTextPlacementRatio

        arcp1 = [lArc * vector1[0] + c[0], lArc * vector1[1] + c[1], lArc * vector1[2] + c[2]]
        arcp2 = [lArc * vector2[0] + c[0], lArc * vector2[1] + c[1], lArc * vector2[2] + c[2]]

        pipeline.arc.SetPoint1(arcp1)
        pipeline.arc.SetPoint2(arcp2)
        pipeline.arc.SetCenter(c)
        pipeline.arc.SetNegative(longArc)
        pipeline.arc.Update()

        # Add two vectors
        vector3 = [vector1[0] + vector2[0], vector1[1] + vector2[1], vector1[2] + vector2[2]]
        vtkmath.Normalize(vector3)

        # Calculate the position of text actor in the world coordinate system
        textActorPositionWorld = [
            lText * (-1.0 if longArc else 1.0) * vector3[0] + c[0],
            lText * (-1.0 if longArc else 1.0) * vector3[1] + c[1],
            lText * (-1.0 if longArc else 1.0) * vector3[2] + c[2]
        ]
        # Convert to the display coordinate system
        textActorPositionDisplay = utils.convertFromWorldCoords2DisplayCoords(renderer, textActorPositionWorld)
        pipeline.textActor.SetInput(f"{round(angle, 1)}")
        pipeline.textActor.SetPosition(round(textActorPositionDisplay[0]), round(textActorPositionDisplay[1]))
    
    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # print("mouse move event")
        # vtkCellPicker object, it shoots a ray into the volume and returns the point where the ray intersects an isosurface of a chosen opacity
        cellPicker = self.GetInteractor().GetPicker()
        # The position of mouse in the display coordinate system
        eventPosition = self.GetInteractor().GetEventPosition()
        # vtkRenderer object
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        # vtkCamera object
        camera = renderer.GetActiveCamera()

        if not self.pipeline.isDragging:
            # Return a point in the world coordinate system on surface or out
            pickPosition = utils.getPickPosition(cellPicker, eventPosition, renderer, camera)
            # Used to mark the position of mouse in the world coordinate system
            self.pipeline.firstSphereActor.SetPosition(pickPosition)
            self.pipeline.firstSphereActor.VisibilityOn()
        else:
            # vtkPoints represents 3D points used to save three points in the world coordinate system
            points = self.pipeline.line.GetPoints()

            # The first point used to find the projection point
            firstPoint = points.GetPoint(0)

            # Return a point in the world coordinate system on surface, if out then finding the projection point
            pickPosition = utils.getPickPosition(cellPicker, eventPosition, renderer, camera, True, firstPoint)
            if self.checkNumberOfPoints == 1:
                # Used to mark the position of mouse in the world coordinate system
                self.pipeline.secondSphereActor.SetPosition(pickPosition)
                self.pipeline.secondSphereActor.VisibilityOn()

                # Save the second point with its id into vtkPoints object
                points.SetPoint(1, pickPosition)
                # Update the modification time for this object and its Data
                points.Modified()

                # vtkIdList may represent any type of integer id, but usually represents point and cell ids
                idList = vtk.vtkIdList()
                idList.InsertNextId(0)
                idList.InsertNextId(1)

                # Insert a cell of type VTK_LINE
                self.pipeline.line.InsertNextCell(vtk.VTK_LINE, idList)
            if self.checkNumberOfPoints == 2:
                # Used to mark the position of mouse in the world coordinate system
                self.pipeline.thirdSphereActor.SetPosition(pickPosition)
                self.pipeline.thirdSphereActor.VisibilityOn()

                # Save the third point with its id into vtkPoints object
                points.SetPoint(2, pickPosition)
                # Update the modification time for this object and its Data
                points.Modified()

                # vtkIdList may represent any type of integer id, but usually represents point and cell ids
                idList = vtk.vtkIdList()
                idList.InsertNextId(1)
                idList.InsertNextId(2)

                # Insert a cell of type VTK_LINE
                self.pipeline.line.InsertNextCell(vtk.VTK_LINE, idList)

                # vtkMath object used to calculate
                vtkmath = vtk.vtkMath()
                # Method used to calculate the angle, the arc and the position of text actor
                self.buildArc(renderer, vtkmath, self.pipeline)
        self.GetInteractor().Render()

    def __leftButtonPressEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # print("left button press event")
        # vtkRenderer object
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        # vtkCamera object
        camera = renderer.GetActiveCamera()
        # The position of mouse in the display coordinate system
        eventPosition = self.GetInteractor().GetEventPosition()
        # vtkCellPicker object, it shoots a ray into the volume and returns the point where the ray intersects an isosurface of a chosen opacity
        cellPicker = self.GetInteractor().GetPicker()
        
        self.checkNumberOfPoints += 1
        if self.checkNumberOfPoints == 1:
            self.pipeline.isDragging = True # Start drawing

            # Return a point in the world coordinate system on surface or out
            pickPosition = utils.getPickPosition(cellPicker, eventPosition, renderer, camera)

            # Marking the first point when left button press
            self.pipeline.firstSphereActor.GetProperty().SetColor(1, 0, 0)
            self.pipeline.firstSphereActor.SetPosition(pickPosition)
            self.pipeline.firstSphereActor.VisibilityOn()

            # vtkPoints represents 3D points
            points = vtk.vtkPoints()
            # vtkCellArray object to represent cell connectivity
            aline = vtk.vtkCellArray()
            # Set objects into vtkPolyData object
            self.pipeline.line.SetPoints(points)
            self.pipeline.line.SetLines(aline)
        
            # Insert the first point into vtkPoints object when having left button press
            points.InsertNextPoint(pickPosition)
            # Insert the second point into vtkPoints object when having left button press, default value
            points.InsertNextPoint(0, 0, 0)
            # Insert the third point into vtkPoints object when having left button press, default value
            points.InsertNextPoint(0, 0, 0)

            # Turn on the first line actor object
            self.pipeline.firstLineActor.VisibilityOn()
        else:
            # vtkPoints represents 3D points used to save three points in the world coordinate system
            points = self.pipeline.line.GetPoints()
            if self.checkNumberOfPoints == 2:
                # Get the second point in vtkPoints object
                pickPosition = points.GetPoint(1)

                # Marking the second point when left button press
                self.pipeline.secondSphereActor.GetProperty().SetColor(1, 0, 0)
                self.pipeline.secondSphereActor.SetPosition(pickPosition)
                self.pipeline.secondSphereActor.VisibilityOn()

                # Turn on the second line actor object
                self.pipeline.secondLineActor.VisibilityOn()
                # Turn on the arc actor object
                self.pipeline.arcActor.VisibilityOn()
                # Turn on the text actor object
                self.pipeline.textActor.VisibilityOn()
            elif self.checkNumberOfPoints == 3:
                # Get the third point in vtkPoints object
                pickPosition = points.GetPoint(2)

                # Marking the third point when left button press
                self.pipeline.thirdSphereActor.GetProperty().SetColor(1, 0, 0)
                self.pipeline.thirdSphereActor.SetPosition(pickPosition)
                self.pipeline.thirdSphereActor.VisibilityOn()
        # Override method of super class
        self.OnLeftButtonDown()

    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # print("left button release event")
        self.OnLeftButtonUp()
        if self.checkNumberOfPoints == 3:
            self.pipeline.isDragging = False # Stop drawing
            # Set interactor style when stop drawing
            style = AfterAngleMeasurementInteractorStyle(self.pipeline)
            self.GetInteractor().SetInteractorStyle(style)

"""
    description:
        AfterAngleMeasurementInteractorStyle class extends vtkInteractorStyleTrackballCamera class
        Set interactor style after drawing will update the position of text when having mouse move event
"""
class AfterAngleMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: AngleMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)

    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        vtkmath = vtk.vtkMath()
        # Update the position of text actor
        AngleMeasurementInteractorStyle.buildArc(renderer, vtkmath, self.pipeline)
        self.GetInteractor().Render()
        self.OnMouseMove()

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
    scalarOpacity = vtk.vtkPiecewiseFunction()
    color = vtk.vtkColorTransferFunction()
    renIn = vtk.vtkRenderWindowInteractor()

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

    pipeline = AngleMeasurementPipeline()
    render.SetBackground(colors.GetColor3d("White"))
    render.AddVolume(vol)
    render.AddActor(outlineActor)
    render.AddActor(pipeline.firstSphereActor); render.AddActor(pipeline.secondSphereActor); render.AddActor(pipeline.thirdSphereActor)
    render.AddActor(pipeline.firstLineActor); render.AddActor(pipeline.secondLineActor)
    render.AddActor(pipeline.arcActor)
    render.AddActor(pipeline.textActor)
    
    renWin.SetWindowName("3D Dicom")
    renWin.SetSize(500, 500)
    renWin.AddRenderer(render)
    
    renIn.SetRenderWindow(renWin)
    cellPicker = vtk.vtkCellPicker()
    cellPicker.AddPickList(vol)
    cellPicker.PickFromListOn()
    renIn.SetPicker(cellPicker)
    style = BeforeAngleMeasurementInteractorStyle(pipeline)
    renIn.SetInteractorStyle(style)

    renIn.Initialize()
    renIn.Start()

if __name__ == "__main__":
    main()