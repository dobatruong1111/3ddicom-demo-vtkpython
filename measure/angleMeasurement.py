from typing import List
import vtk
import utils

"""
    Description: class contains objects for angle measurement in the world coordinate system.
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

        # Connecting the first point with the second point
        self.firstLineActor = vtk.vtkActor()
        self.firstLineActor.SetMapper(self.firstLineMapper)
        self.firstLineActor.SetProperty(property)
        self.firstLineActor.VisibilityOff()

        # Connecting the second point with the third point
        self.secondLineActor = vtk.vtkActor()
        self.secondLineActor.SetMapper(self.secondLineMapper)
        self.secondLineActor.SetProperty(property)
        self.secondLineActor.VisibilityOff()

        # Arc
        self.arcActor = vtk.vtkActor()
        self.arcActor.SetMapper(self.arcMapper)
        self.arcActor.SetProperty(property)
        self.arcActor.VisibilityOff()

        # Used to display angle between two vectors
        self.textActor = vtk.vtkTextActor()
        textProperty = self.textActor.GetTextProperty()
        textProperty.SetColor(colors.GetColor3d("Tomato"))
        textProperty.SetFontSize(15)
        textProperty.ShadowOn()
        textProperty.BoldOn()
        self.textActor.VisibilityOff()

        # Used to mark the first point
        self.firstSphereActor = vtk.vtkActor()
        self.firstSphereActor.SetMapper(self.firstSphereMapper)
        self.firstSphereActor.GetProperty().SetColor(0, 1, 0)
        self.firstSphereActor.VisibilityOff()

        # Used to mark the second point
        self.secondSphereActor = vtk.vtkActor()
        self.secondSphereActor.SetMapper(self.secondSphereMapper)
        self.secondSphereActor.GetProperty().SetColor(0, 1, 0)
        self.secondSphereActor.VisibilityOff()

        # Used to mark the third point
        self.thirdSphereActor = vtk.vtkActor()
        self.thirdSphereActor.SetMapper(self.thirdSphereMapper)
        self.thirdSphereActor.GetProperty().SetColor(0, 1, 0)
        self.thirdSphereActor.VisibilityOff()

"""
    Description:
        BeforeAngleMeasurementInteractorStyle class extends vtkInteractorStyleTrackballCamera class.
        vtkInteractorStyleTrackballCamera allows the user to interactively manipulate (rotate, pan, etc.),
        the camera.
        Class used to rotate, pan,... before angle measurement.
"""
class BeforeAngleMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: AngleMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)
    
    """
        Description:
            A handle function used to set angle measurement interactor style
            when having left button release event.
    """
    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.OnLeftButtonUp()
        style = AngleMeasurementInteractorStyle(self.pipeline)
        self.GetInteractor().SetInteractorStyle(style)

"""
    Description: 
        AngleMeasurementInteractorStyle class extends vtkInteractorStyleTrackballCamera class.
        Set interactor style for angle measurement.
"""
class AngleMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: AngleMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.checkNumberOfPoints = 0 # used to check current number of points
        self.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.__leftButtonPressEvent)
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)
    
    """
        Description:
            A handle function when having mouse move event.
            Used to mark the position of mouse in world coordinates when moving.
            Used to draw two lines connecting the first point with the second point
            and the second point with the third point.
            Display the arc and the text actor.
    """
    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
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
            pickPosition = utils.getPickPosition(eventPosition, cellPicker, renderer, camera)
            # Used to mark the position of mouse in the world coordinate system
            self.pipeline.firstSphereActor.SetPosition(pickPosition)
            self.pipeline.firstSphereActor.VisibilityOn()
        else:
            # Return vtkPoints object
            points = self.pipeline.line.GetPoints()
            # The first point used to find the projection point
            firstPoint = points.GetPoint(0)
            # Return a point in the world coordinate system on surface, if out then finding the projection point
            pickPosition = utils.getPickPosition(eventPosition, cellPicker, renderer, camera, True, firstPoint)
            
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

                # Method used to calculate the angle, the arc and the position of text actor
                utils.buildArcAngleMeasurement(self.pipeline.arc, self.pipeline.textActor, renderer, points)
        self.GetInteractor().Render()

    """
        Description:
            A handle function when having left button event.
            Used to mark the position of points in world coordinates when click.
    """
    def __leftButtonPressEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # vtkRenderer object
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        # vtkCamera object
        camera = renderer.GetActiveCamera()
        # The position of mouse in the display coordinate system
        eventPosition = self.GetInteractor().GetEventPosition()
        # Return vtkCellPicker object, it shoots a ray into the volume and returns the point where the ray intersects an isosurface of a chosen opacity
        cellPicker = self.GetInteractor().GetPicker()
        
        self.checkNumberOfPoints += 1
        if self.checkNumberOfPoints == 1:
            self.pipeline.isDragging = True # Start drawing

            # Return a point in the world coordinate system on surface or out
            pickPosition = utils.getPickPosition(eventPosition, cellPicker, renderer, camera)

            # Marking the first point
            self.pipeline.firstSphereActor.GetProperty().SetColor(1, 0, 0)
            self.pipeline.firstSphereActor.SetPosition(pickPosition)

            # vtkPoints represents 3D points used to save 2 points in world coordinates
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
            # Return vtkPoints object
            points = self.pipeline.line.GetPoints()
            if self.checkNumberOfPoints == 2:
                # Return the second point in vtkPoints object
                pickPosition = points.GetPoint(1)

                # Marking the second point
                self.pipeline.secondSphereActor.GetProperty().SetColor(1, 0, 0)
                self.pipeline.secondSphereActor.SetPosition(pickPosition)

                # Turn on the second line actor object
                self.pipeline.secondLineActor.VisibilityOn()
                # Turn on the arc actor object
                self.pipeline.arcActor.VisibilityOn()
                # Turn on the text actor object
                self.pipeline.textActor.VisibilityOn()
            elif self.checkNumberOfPoints == 3:
                # Return the third point in vtkPoints object
                pickPosition = points.GetPoint(2)

                # Marking the third point
                self.pipeline.thirdSphereActor.GetProperty().SetColor(1, 0, 0)
                self.pipeline.thirdSphereActor.SetPosition(pickPosition)
        # Override method of super class
        self.OnLeftButtonDown()

    """
        Description:
            A handle function when having left button release event.
            If number of points equals 3 then stop drawing and
            set interactor style after length measurement finished.
    """
    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.OnLeftButtonUp()
        if self.checkNumberOfPoints == 3:
            self.pipeline.isDragging = False # Stop drawing

            # Set interactor style when stop drawing
            style = AfterAngleMeasurementInteractorStyle(self.pipeline)
            self.GetInteractor().SetInteractorStyle(style)

"""
    Description:
        AfterAngleMeasurementInteractorStyle class extends vtkInteractorStyleTrackballCamera class.
        Class used to rotate, pan,... before angle measurement.
"""
class AfterAngleMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: AngleMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)

    """
        Description:
            A handle function used to update the position of text actor when having mouse move event.
    """
    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        points = self.pipeline.line.GetPoints()
        # Update the position of text actor
        utils.buildArcAngleMeasurement(self.pipeline.arc, self.pipeline.textActor, renderer, points)
        self.GetInteractor().Render()
        self.OnMouseMove()

"""
    Description: calculate input data for transfer function
    Params:
        colormap: a standard for color map with each CT number (HU)
    Return: a list contains other lists, sub lists have size = 4 
    with format: [CT number, red color, green color, blue color],
    colors between 0 and 1.
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

    # Outline
    # Description: drawing a bounding box out volume object
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

    # Bone preset
    scalarOpacity.AddPoint(80, 0)
    scalarOpacity.AddPoint(400, 0.2)
    scalarOpacity.AddPoint(1000, 1)
    # Muscle preset
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