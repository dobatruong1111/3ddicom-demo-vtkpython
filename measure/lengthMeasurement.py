import vtk
import utils
from typing import List

"""
    description:
        class contains objects for drawing line in the world coordinate system
"""
class MeasureLengthPipeLine():
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

        # display the length of two points in the world coordinate system
        # vtkTextActor is an actor that displays text
        self.textActor = vtk.vtkTextActor()
        textProperty = self.textActor.GetTextProperty()
        textProperty.SetColor(colors.GetColor3d("Tomato"))
        textProperty.SetFontSize(15)
        textProperty.ShadowOn()
        textProperty.BoldOn()
        self.textActor.VisibilityOff()

        # marking the first point and the second point by two spheres
        self.firstSphereActor = vtk.vtkActor()
        self.firstSphereActor.GetProperty().SetColor(1, 0, 0)
        self.firstSphereActor.SetMapper(self.firstSphereMapper)
        self.firstSphereActor.VisibilityOff()
        
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
        eventPosition = self.GetInteractor().GetEventPosition() # tuple

        # vtkCellPicker object, it shoots a ray into the volume and returns the point where the ray intersects an isosurface of a chosen opacity
        cellPicker = self.GetInteractor().GetPicker()

        if self.pipeline.isDragging:
            # vtkPoints represents 3D points
            points = self.pipeline.line.GetPoints()
            firstPoint = points.GetPoint(0) # tuple
            pickPosition = utils.getPickPosition(cellPicker, eventPosition, renderer, camera, True, firstPoint)
            
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

            secondPoint = points.GetPoint(1) # tuple
            # Calculate the middle point
            midPoint = tuple(map(lambda i,j: (i+j)/2, firstPoint, secondPoint))
            # Calculate the euclidean distance between the first point and the second point
            distance = utils.getEuclideanDistanceBetween2Points(firstPoint, secondPoint)
            # Convert the middle point from the world coordinate system to the display coordinate system 
            displayCoords = utils.convertFromWorldCoords2DisplayCoords(renderer, midPoint)

            # Display the distance and set position of text
            self.pipeline.textActor.SetInput(f"{round(distance, 1)}mm")
            self.pipeline.textActor.SetDisplayPosition(round(displayCoords[0]), round(displayCoords[1]))
            self.pipeline.textActor.VisibilityOn()
        else: # TODO: code need to processed in javascript
            pickPosition = utils.getPickPosition(cellPicker, eventPosition, renderer, camera)
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

        pickPosition = utils.getPickPosition(cellPicker, eventPosition, renderer, camera)
    
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
        midPoint = tuple(map(lambda i,j: (i+j)/2, firstPoint, secondPoint))
        displayCoords = utils.convertFromWorldCoords2DisplayCoords(renderer, midPoint)
        self.pipeline.textActor.SetDisplayPosition(round(displayCoords[0]), round(displayCoords[1]))

        self.GetInteractor().Render()
        # Override method of super class
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