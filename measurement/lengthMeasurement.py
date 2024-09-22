import vtk
import utils
from typing import List

"""
    Description:
        Class contains objects for drawing line in the world coordinate system.
"""
class LengthMeasurementPipeline():
    def __init__(self) -> None:
        colors = vtk.vtkNamedColors()
        self.isDragging = False

        # Line
        # vtkPolyData represents a geometric structure consisting of vertices, lines, polygons, and/or triangle strips
        self.line = vtk.vtkPolyData()

        # Sphere source
        self.sphere = vtk.vtkSphereSource()
        self.sphere.SetRadius(5)

        # Filter
        # vtkTubeFilter is a filter that generates a tube around each input line
        self.tubeFilter = vtk.vtkTubeFilter()
        self.tubeFilter.SetInputData(self.line)
        self.tubeFilter.SetNumberOfSides(20)
        self.tubeFilter.SetRadius(1)

        # Mappers
        self.lineMapper = vtk.vtkPolyDataMapper()
        self.lineMapper.SetInputConnection(self.tubeFilter.GetOutputPort())

        self.firstSphereMapper = vtk.vtkPolyDataMapper()
        self.firstSphereMapper.SetInputConnection(self.sphere.GetOutputPort())

        self.secondSphereMapper = vtk.vtkPolyDataMapper()
        self.secondSphereMapper.SetInputConnection(self.sphere.GetOutputPort())
        
        # Actors
        self.lineActor = vtk.vtkActor()
        self.lineActor.SetMapper(self.lineMapper)
        self.lineActor.GetProperty().SetColor(colors.GetColor3d("Tomato"))
        self.lineActor.GetProperty().SetLineWidth(2)
        self.lineActor.VisibilityOff()

        # Display the length of two points in the world coordinate system
        # vtkTextActor is an actor that displays text
        self.textActor = vtk.vtkTextActor()
        textProperty = self.textActor.GetTextProperty()
        textProperty.SetColor(colors.GetColor3d("Tomato"))
        textProperty.SetFontSize(15)
        textProperty.ShadowOn()
        textProperty.BoldOn()
        self.textActor.VisibilityOff()

        # Marking the first point and the second point by two spheres
        self.firstSphereActor = vtk.vtkActor()
        self.firstSphereActor.GetProperty().SetColor(0, 1, 0)
        self.firstSphereActor.SetMapper(self.firstSphereMapper)
        self.firstSphereActor.VisibilityOff()
        
        self.secondSphereActor = vtk.vtkActor()
        self.secondSphereActor.GetProperty().SetColor(0, 1, 0)
        self.secondSphereActor.SetMapper(self.secondSphereMapper)
        self.secondSphereActor.VisibilityOff()

"""
    Description: 
        BeforeMeasureLengthInteractorStyle class extends vtkInteractorStyleTrackballCamera class.
        vtkInteractorStyleTrackballCamera allows the user to interactively manipulate (rotate, pan, etc.)
        the camera.
        Class used to rotate, pan,... before angle measurement.
"""
class BeforeLengthMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: LengthMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)

    """
        Description:
            A handle function used to set length measurement interactor style
            when having left button release event.
    """
    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # Override method of super class
        self.OnLeftButtonUp()
        style = LengthMeasurementInteractorStyle(self.pipeline)
        self.GetInteractor().SetInteractorStyle(style)

"""
    Description: 
        MeasureLengthInteractorStyle class extends vtkInteractorStyleTrackballCamera class.
        Set interactor style for length measurement.
"""
class LengthMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: LengthMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.checkNumberOfPoints = 0 # used to check current number of points, max = 2 points
        self.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.__leftButtonPressEvent)
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)

    """
        Description:
            A handle function when having mouse move event.
            Used to mark the position of mouse in world coordinates when moving.
            Used to draw a line connecting two points.
    """
    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # vtkRenderer object
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        # vtkCamera object
        camera = renderer.GetActiveCamera()
        # The position of mouse in the display coordinate system
        eventPosition = list(self.GetInteractor().GetEventPosition())
        # vtkCellPicker object, it shoots a ray into the volume and returns the point where the ray intersects an isosurface of a chosen opacity
        cellPicker = self.GetInteractor().GetPicker()

        if self.pipeline.isDragging:
            if self.checkNumberOfPoints == 1:
                # Return vtkPoints object
                points = self.pipeline.line.GetPoints()

                firstPoint = list(points.GetPoint(0)) # Return the first point
                # Return a point in the world coordinate system on surface, if out then finding the projection point
                pickPosition = utils.getPickPosition(eventPosition, cellPicker, renderer, camera, True, firstPoint)
                
                # Marking the second point when drawing
                self.pipeline.secondSphereActor.SetPosition(pickPosition)
                self.pipeline.secondSphereActor.VisibilityOn() # Turn on the second sphere

                # Save the second point
                points.SetPoint(1, pickPosition)
                # Update the modification time for this object and its Data
                points.Modified()

                # vtkIdList may represent any type of integer id, but usually represents point and cell ids
                idList = vtk.vtkIdList()
                idList.InsertNextId(0) # Insert id of the first point
                idList.InsertNextId(1) # Insert id of the second point

                # Insert a cell of type VTK_LINE
                self.pipeline.line.InsertNextCell(vtk.VTK_LINE, idList)
                # Method used to calculate the position of text actor
                utils.buildTextActorLengthMeasurement(self.pipeline.textActor, renderer, points)

        else: # TODO: code need to processed in javascript
            pickPosition = utils.getPickPosition(eventPosition, cellPicker, renderer, camera)
            # Marking the position of mouse in world coordinates
            self.pipeline.firstSphereActor.SetPosition(pickPosition)
            self.pipeline.firstSphereActor.VisibilityOn() # Turn on the first sphere
        self.GetInteractor().Render()
    
    """
        Description:
            A handle function when having left button press event.
            Used to mark the position of points in world coordinates when click.
    """
    def __leftButtonPressEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # vtkRenderer object
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        # vtkCamera object
        camera = renderer.GetActiveCamera()
        # The position of mouse in the display coordinate system
        eventPosition = list(self.GetInteractor().GetEventPosition()) # the position of mouse in display coordinate system 
        # vtkCellPicker object, it shoots a ray into the volume and returns the point where the ray intersects an isosurface of a chosen opacity
        cellPicker = self.GetInteractor().GetPicker()

        self.checkNumberOfPoints += 1 # Add a point
        if self.checkNumberOfPoints == 1:
            self.pipeline.isDragging = True # Start drawing

            # Return a point in the world coordinate system on surface or out
            pickPosition = utils.getPickPosition(eventPosition, cellPicker, renderer, camera)
    
            # Marking the first point when having left button down event
            self.pipeline.firstSphereActor.GetProperty().SetColor(1, 0, 0)
            self.pipeline.firstSphereActor.SetPosition(pickPosition)

            # vtkPoints represents 3D points used to save 2 points in world coordinates
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

            self.pipeline.lineActor.VisibilityOn() # Turn on line actor object
            self.pipeline.textActor.VisibilityOn() # Turn on text actor object
        elif self.checkNumberOfPoints == 2:
            points = self.pipeline.line.GetPoints()
            pickPosition = points.GetPoint(1) # Return the second point
            self.pipeline.secondSphereActor.GetProperty().SetColor(1, 0, 0) # Set red color for the second sphere
            self.pipeline.secondSphereActor.SetPosition(pickPosition) # Set position for the second sphere
        # Override method of super class
        self.OnLeftButtonDown()

    """
        Description:
            A handle function when having left button release event.
            If number of points equals 2, set interactor style after length measurement finished.
    """
    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # Override method of super class
        self.OnLeftButtonUp()
        if self.checkNumberOfPoints == 2:
            self.pipeline.isDragging = False # Stop drawing
            # Set interactor style when stop drawing
            style = AfterLengthMeasurementInteractorStyle(self.pipeline)
            self.GetInteractor().SetInteractorStyle(style)

"""
    Description:
        UpdateLengthPositionInteractorStyle class extends vtkInteractorStyleTrackballCamera class.
        Class used to rotate, pan,... after angle measurement.
"""
class AfterLengthMeasurementInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: LengthMeasurementPipeline) -> None:
        self.pipeline = pipeline
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
    
    """
        Description:
            A handle function used to update the position of text actor when having mouse move event.
    """
    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        points = self.pipeline.line.GetPoints()

        # Method used to update the position of text actor
        utils.buildTextActorLengthMeasurement(self.pipeline.textActor, renderer, points)

        self.GetInteractor().Render()
        # Override method of super class
        self.OnMouseMove()

"""
    Description: calculate input data for transfer function.
    Params:
        colormap: a standard for color map with each CT number (HU)
    Return: a list contains other lists, sub lists have size = 4 with format: [CT number, red color, green color, blue color], colors between 0 and 1
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

def set_volume_properties(volumeProperty: vtk.vtkVolumeProperty) -> None:
    gradientOpacity = vtk.vtkPiecewiseFunction()
    scalarOpacity = vtk.vtkPiecewiseFunction()
    color = vtk.vtkColorTransferFunction()

    volumeProperty.ShadeOn()
    volumeProperty.SetScalarOpacityUnitDistance(0.1)
    volumeProperty.SetInterpolationTypeToLinear()

    volumeProperty.SetAmbient(0.1)
    volumeProperty.SetDiffuse(0.9)
    volumeProperty.SetSpecular(0.2)
    volumeProperty.SetSpecularPower(10)

    gradientOpacity.AddPoint(0.0, 0.0)
    gradientOpacity.AddPoint(2000.0, 1.0)
    volumeProperty.SetGradientOpacity(gradientOpacity)

    scalarOpacity.AddPoint(-800.0, 0.0)
    scalarOpacity.AddPoint(-750.0, 1.0)
    scalarOpacity.AddPoint(-350.0, 1.0)
    scalarOpacity.AddPoint(-300.0, 0.0)
    scalarOpacity.AddPoint(-200.0, 0.0)
    scalarOpacity.AddPoint(-100.0, 1.0)
    scalarOpacity.AddPoint(1000.0, 0.0)
    scalarOpacity.AddPoint(2750.0, 0.0)
    scalarOpacity.AddPoint(2976.0, 1.0)
    scalarOpacity.AddPoint(3000.0, 0.0)
    volumeProperty.SetScalarOpacity(scalarOpacity)

    color.AddRGBPoint(-750.0, 0.08, 0.05, 0.03)
    color.AddRGBPoint(-350.0, 0.39, 0.25, 0.16)
    color.AddRGBPoint(-200.0, 0.80, 0.80, 0.80)
    color.AddRGBPoint(2750.0, 0.70, 0.70, 0.70)
    color.AddRGBPoint(3000.0, 0.35, 0.35, 0.35)
    volumeProperty.SetColor(color)

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
    path2 = "D:/javaworkspace/viewer-core/server3d/data/1.2.840.113704.9.1000.16.0.20240527133901371/1.2.840.113704.9.1000.16.1.2024052713392627100020002/data"
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
    pipeline = LengthMeasurementPipeline()

    # Outline
    # Description: drawing a bounding box out volume object
    # outline = vtk.vtkOutlineFilter()
    # outline.SetInputConnection(reader.GetOutputPort())
    # outlineMapper = vtk.vtkPolyDataMapper()
    # outlineMapper.SetInputConnection(outline.GetOutputPort())
    # outlineActor = vtk.vtkActor()
    # outlineActor.SetMapper(outlineMapper)
    # outlineActor.GetProperty().SetColor(0, 0, 0)
    
    reader.SetDirectoryName(path2)
    reader.Update()
    
    # This option will use hardware accelerated rendering exclusively
    # This is a good option if you know there is hardware acceleration
    # map.SetRequestedRenderModeToGPU()
    map.SetInputData(reader.GetOutput())

    # volProperty.SetInterpolationTypeToLinear()
    # volProperty.ShadeOn()
    # # Lighting of volume
    # volProperty.SetAmbient(0.1)
    # volProperty.SetDiffuse(0.9)
    # volProperty.SetSpecular(0.2)
    # # Color map thought a transfer function
    # for rgb_point in rgb_points:
    #     color.AddRGBPoint(rgb_point[0], rgb_point[1], rgb_point[2], rgb_point[3])
    # volProperty.SetColor(color)

    # # Bone preset
    # scalarOpacity.AddPoint(80, 0)
    # scalarOpacity.AddPoint(400, 0.2)
    # scalarOpacity.AddPoint(1000, 1)
    # volProperty.SetScalarOpacity(scalarOpacity)

    vol.SetMapper(map)

    set_volume_properties(volProperty)
    vol.SetProperty(volProperty)

    render.SetBackground(colors.GetColor3d("White"))
    render.AddVolume(vol)
    # render.AddActor(outlineActor)
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
    style = BeforeLengthMeasurementInteractorStyle(pipeline)
    renIn.SetInteractorStyle(style)

    renIn.Initialize()
    renIn.Start()

if __name__ == "__main__":
    main()