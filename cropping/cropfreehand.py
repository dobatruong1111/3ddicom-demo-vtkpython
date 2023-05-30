import vtk
from typing import List, Tuple
import math

class ScissorsPipeline:
    def __init__(self) -> None:
        # 2D Contour Pipeline
        self.isDragging = False
        self.polyData = vtk.vtkPolyData()

        self.mapper = vtk.vtkPolyDataMapper2D()
        self.mapper.SetInputData(self.polyData)

        self.actor = vtk.vtkActor2D()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetColor(1, 1, 0)
        self.actor.GetProperty().SetLineWidth(2)
        self.actor.VisibilityOff()

        # Thin
        self.polyDataThin = vtk.vtkPolyData()
        
        self.mapperThin = vtk.vtkPolyDataMapper2D()
        self.mapperThin.SetInputData(self.polyDataThin)

        self.actorThin = vtk.vtkActor2D()
        self.actorThin.SetMapper(self.mapperThin)
        self.actorThin.GetProperty().SetColor(0.7, 0.7, 0)
        self.actorThin.GetProperty().SetLineWidth(1)
        self.actorThin.GetProperty().SetLineStipplePattern(0xff00)
        self.actorThin.VisibilityOff()

class InteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline, imageData, map):
        self.pipeline = pipeline
        self.imageData = imageData
        self.map = map
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.leftButtonReleaseEvent)

    def leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.OnLeftButtonUp()
        style = CropFreehandInteractorStyle(self.pipeline, self.imageData, self.map)
        self.GetInteractor().SetInteractorStyle(style)

class CropFreehandInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline, imageData, map) -> None:
        self.pipeline = pipeline
        self.imageData = imageData
        self.map = map

        self.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.__leftButtonPressEvent)
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)
        
        self.brushPolyDataNormals = vtk.vtkPolyDataNormals()
        self.brushPolyDataNormals.AutoOrientNormalsOn()

        self.worldToModifierLabelmapIjkTransformer = vtk.vtkTransformPolyDataFilter()
        self.worldToModifierLabelmapIjkTransform = vtk.vtkTransform()
        self.worldToModifierLabelmapIjkTransformer.SetTransform(self.worldToModifierLabelmapIjkTransform)
        self.worldToModifierLabelmapIjkTransformer.SetInputConnection(self.brushPolyDataNormals.GetOutputPort()) # vtkPolyData

        self.brushPolyDataToStencil = vtk.vtkPolyDataToImageStencil()
        self.brushPolyDataToStencil .SetOutputOrigin(0, 0, 0)
        self.brushPolyDataToStencil.SetOutputSpacing(1, 1, 1)
        self.brushPolyDataToStencil.SetInputConnection(self.worldToModifierLabelmapIjkTransformer.GetOutputPort())

    @staticmethod
    def createGlyph(pipeline: ScissorsPipeline, eventPosition: Tuple) -> None:
        if pipeline.isDragging:
            pipeline.polyData.Initialize()
            pipeline.polyDataThin.Initialize()

            points = vtk.vtkPoints()
            lines = vtk.vtkCellArray()
            pipeline.polyData.SetPoints(points)
            pipeline.polyData.SetLines(lines)

            points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

            # Thin
            pointsThin = vtk.vtkPoints()
            linesThin = vtk.vtkCellArray()
            pipeline.polyDataThin.SetPoints(pointsThin)
            pipeline.polyDataThin.SetLines(linesThin)

            pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

            idList = vtk.vtkIdList()
            idList.InsertNextId(0)
            idList.InsertNextId(1)
            pipeline.polyDataThin.InsertNextCell(vtk.VTK_LINE, idList)

            pipeline.actorThin.VisibilityOn()
            pipeline.actor.VisibilityOn()
        else:
            pipeline.actor.VisibilityOff()
            pipeline.actorThin.VisibilityOff()

    @staticmethod
    def updateGlyphWithNewPosition(pipeline: ScissorsPipeline, eventPosition: Tuple, finalize: bool):
        if pipeline.isDragging:
            points = pipeline.polyData.GetPoints()
            newPointIndex = points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            points.Modified()

            idList = vtk.vtkIdList()
            if finalize:
                idList.InsertNextId(newPointIndex)
                idList.InsertNextId(0)
            else:
                idList.InsertNextId(newPointIndex - 1)
                idList.InsertNextId(newPointIndex)
            pipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)
            
            pipeline.polyDataThin.GetPoints().SetPoint(1, eventPosition[0], eventPosition[1], 0)
            pipeline.polyDataThin.GetPoints().Modified()
        else:
            pipeline.actor.VisibilityOff()
            pipeline.actorThin.VisibilityOff()

    def __leftButtonPressEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str):
        self.pipeline.isDragging = True
        eventPosition = self.GetInteractor().GetEventPosition()
        self.createGlyph(self.pipeline, eventPosition)
        self.OnLeftButtonDown()

    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str):
        if self.pipeline.isDragging:
            eventPosition = self.GetInteractor().GetEventPosition()
            self.updateGlyphWithNewPosition(self.pipeline, eventPosition, False)
            self.GetInteractor().Render()
            
    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str):
        if self.pipeline.isDragging:
            self.pipeline.isDragging = False
            eventPosition = self.GetInteractor().GetEventPosition()
            self.updateGlyphWithNewPosition(self.pipeline, eventPosition, True)

            self.paintApply()

            self.OnLeftButtonUp()

            style = vtk.vtkInteractorStyleTrackballCamera()
            self.GetInteractor().SetInteractorStyle(style)

    def updateBrushModel(self):
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()
        pointsXY = self.pipeline.polyData.GetPoints()
        numberOfPoints = pointsXY.GetNumberOfPoints()

        closedSurfacePoints = vtk.vtkPoints()

        # Camera parameters
        # Camera position
        cameraPos = list(camera.GetPosition())
        cameraPos.append(1)
        # Focal point
        cameraFP = list(camera.GetFocalPoint())
        cameraFP.append(1)
        # Direction of projection
        cameraDOP = [0, 0, 0]
        for i in range(3):
            cameraDOP[i] = cameraFP[i] - cameraPos[i]
        vtk.vtkMath().Normalize(cameraDOP)

        renderer.SetWorldPoint(cameraFP[0], cameraFP[1], cameraFP[2], cameraFP[3])
        renderer.WorldToDisplay()
        displayCoords = renderer.GetDisplayPoint()
        selectionZ = displayCoords[2]

        clipRangeFromCamera = camera.GetClippingRange()
        clipRange = [clipRangeFromCamera[0], clipRangeFromCamera[1]]

        # Step 2: Mapping display space points to world positions
        for pointIndex in range(numberOfPoints):
            # Convert the selection point into world coordinates
            pointXY = pointsXY.GetPoint(pointIndex)
            renderer.SetDisplayPoint(pointXY[0], pointXY[1], selectionZ)
            renderer.DisplayToWorld()
            worldCoords = renderer.GetWorldPoint()
            
            # Convert from homo coordinates to world coordinates
            pickPosition = [0, 0, 0]
            for i in range(3):
                pickPosition[i] = worldCoords[i] / worldCoords[3] if worldCoords[3] else worldCoords[i]

            # Compute the ray endpoints. The ray is along the line running from
            # the camera position to the selection point, starting where this line
            # intersects the front clipping plane, and terminating where this line
            # intersects the back clipping plane.
            ray = [0, 0, 0]
            for i in range(3):
                ray[i] = pickPosition[i] - cameraPos[i] # vector
            rayLength = vtk.vtkMath().Dot(cameraDOP, ray)

            p1World, p2World = [0, 0, 0], [0, 0, 0]
            tF = clipRange[0] / rayLength
            tB = clipRange[1] / rayLength
            for i in range(3):
                p1World[i] = cameraPos[i] + tF * ray[i]
                p2World[i] = cameraPos[i] + tB * ray[i]
            closedSurfacePoints.InsertNextPoint(p1World)
            closedSurfacePoints.InsertNextPoint(p2World)

        # Step 3: Take 2d contour as polydata line, and extrude surfaces from the near clipping plane to the far clipping plane
        # Skirt
        # Object to represent cell connectivity
        closedSurfaceStrips = vtk.vtkCellArray() 
        # Create cells by specifying a count of total points to be inserted,
        # and then adding points one at a time using method InsertCellPoint()
        closedSurfaceStrips.InsertNextCell(numberOfPoints * 2 + 2)
        for i in range(numberOfPoints * 2):
            closedSurfaceStrips.InsertCellPoint(i)
        closedSurfaceStrips.InsertCellPoint(0)
        closedSurfaceStrips.InsertCellPoint(1)
        # Front cap
        closedSurfacePolys = vtk.vtkCellArray() # object to represent cell connectivity
        closedSurfacePolys.InsertNextCell(numberOfPoints)
        for i in range(numberOfPoints):
            closedSurfacePolys.InsertCellPoint(i * 2)
        # Back cap
        closedSurfacePolys.InsertNextCell(numberOfPoints)
        for i in range(numberOfPoints):
            closedSurfacePolys.InsertCellPoint(i * 2 + 1)
        # Construct polydata
        closedSurfacePolyData = vtk.vtkPolyData()
        closedSurfacePolyData.SetPoints(closedSurfacePoints)
        closedSurfacePolyData.SetStrips(closedSurfaceStrips)
        closedSurfacePolyData.SetPolys(closedSurfacePolys)

        # Step 4: Take the polydata from step 3, and do a 3D stencil filter
        self.brushPolyDataNormals.SetInputData(closedSurfacePolyData)
        self.brushPolyDataNormals.Update()

    def updateBrushStencil(self):
        self.worldToModifierLabelmapIjkTransformer.Update()
        closedSurfacePolyData = self.worldToModifierLabelmapIjkTransformer.GetOutput()
        bounds = closedSurfacePolyData.GetBounds()
        self.brushPolyDataToStencil.SetOutputWholeExtent(
            math.floor(bounds[0]) - 1, math.ceil(bounds[1]) + 1,
            math.floor(bounds[2]) - 1, math.ceil(bounds[3]) + 1,
            math.floor(bounds[4]) - 1, math.ceil(bounds[5]) + 1,
        )
        self.brushPolyDataToStencil.Update()

    def paintApply(self):
        self.updateBrushModel()
        self.updateBrushStencil()

        # Step 5: Convert from Image Stencil Data to Image Data
        # vtkImageStencilToImage will convert an image stencil into a binary image
        # The default output will be an 8-bit image with a value of 1 inside the stencil and 0 outside
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetInputData(self.brushPolyDataToStencil.GetOutput())
        # print(self.brushPolyDataToStencil.GetOutput())
        stencilToImage.SetInsideValue(1)
        stencilToImage.SetOutsideValue(0)
        stencilToImage.SetOutputScalarType(self.imageData.GetScalarType()) # vtk.VTK_SHORT: [-32768->32767], vtk.VTK_UNSIGNED_CHAR: [0->255]
        stencilToImage.Update()

        # Step 6: Create a Image Data extends origin image data some properties, all scalar values equal 0
        baseImage = vtk.vtkImageData()
        baseImage.SetExtent(self.imageData.GetExtent())
        baseImage.SetSpacing(self.imageData.GetSpacing())
        baseImage.SetOrigin(self.imageData.GetOrigin())
        baseImage.AllocateScalars(self.imageData.GetScalarType(), 1)

        modifierImage = stencilToImage.GetOutput()

        self.modifyImage(baseImage, modifierImage)
    
    def modifyImage(self, baseImage: vtk.vtkImageData, modifierImage: vtk.vtkImageData):

        # Step 7: Filter scalar values inside, all inside values equal 1, and outside equal 0
        baseExtent = baseImage.GetExtent()
        updateExtent = [v for v in baseExtent]
        modifierExtent = modifierImage.GetExtent()
        for idx in range(3):
            if modifierExtent[idx * 2] > updateExtent[idx * 2]:
                updateExtent[idx * 2] = modifierExtent[idx * 2]
            if modifierExtent[idx * 2 + 1] < updateExtent[idx * 2 + 1]:
                updateExtent[idx * 2 + 1] = modifierExtent[idx * 2 + 1]
        if updateExtent[0] > updateExtent[1] or updateExtent[2] > updateExtent[3] or updateExtent[4] > updateExtent[5]:
            return

        baseImageModified = False
        for z in range(updateExtent[4], updateExtent[5] + 1):
            for y in range(updateExtent[2], updateExtent[3] + 1):
                for x in range(updateExtent[0], updateExtent[1] + 1):
                    if modifierImage.GetScalarComponentAsFloat(x, y, z, 0) > baseImage.GetScalarComponentAsFloat(x, y, z, 0):
                        baseImage.SetScalarComponentFromFloat(x, y, z, 0, modifierImage.GetScalarComponentAsFloat(x, y, z, 0))
                        baseImageModified = True
        if baseImageModified:
            baseImage.Modified()

        self.maskVolume(baseImage)

    def maskVolume(self, baseImage):

        # Step 8: Apply mask volume
        maskToStencil = vtk.vtkImageToImageStencil()
        maskToStencil.ThresholdByLower(0)
        maskToStencil.SetInputData(baseImage)
        maskToStencil.Update()
        
        stencil = vtk.vtkImageStencil()
        stencil.SetInputData(self.imageData)
        stencil.SetStencilConnection(maskToStencil.GetOutputPort())
        stencil.Update()

        # Step 9: Render the new volume
        self.map.SetInputData(stencil.GetOutput())

def main() -> None:
    path = "../dicomdata/CT1.25mmStndKHONGTIEM"

    colors = vtk.vtkNamedColors()
    reader = vtk.vtkDICOMImageReader()
    map = vtk.vtkSmartVolumeMapper()
    vol = vtk.vtkVolume()
    volProperty = vtk.vtkVolumeProperty()
    render = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    scalarOpacity = vtk.vtkPiecewiseFunction()
    renIn = vtk.vtkRenderWindowInteractor()
    pipeline = ScissorsPipeline()

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
    imageData = reader.GetOutput()
    
    # This option will use hardware accelerated rendering exclusively
    # This is a good option if you know there is hardware acceleration
    map.SetRequestedRenderModeToGPU()
    map.SetInputData(reader.GetOutput()) # vtkImageData

    volProperty.SetInterpolationTypeToLinear()
    volProperty.ShadeOn()
    # Lighting of volume
    volProperty.SetAmbient(0.1)
    volProperty.SetDiffuse(0.9)
    volProperty.SetSpecular(0.2)
    
    # Bone preset
    scalarOpacity.AddPoint(80, 0)
    scalarOpacity.AddPoint(400, 0.2)
    scalarOpacity.AddPoint(1000, 1)
    volProperty.SetScalarOpacity(scalarOpacity)

    vol.SetMapper(map)
    vol.SetProperty(volProperty)

    render.SetBackground(colors.GetColor3d("White"))
    render.AddVolume(vol)
    render.AddActor(outlineActor)
    render.AddActor(pipeline.actor)
    render.AddActor(pipeline.actorThin)
    
    renWin.SetWindowName("3D Dicom")
    renWin.SetSize(500, 500)
    renWin.AddRenderer(render)
    
    renIn.SetRenderWindow(renWin)

    # Step 1: Drawing a 2D contour on the screen
    style = InteractorStyle(pipeline, imageData, map)
    renIn.SetInteractorStyle(style)

    renIn.Initialize()
    renIn.Start()

if __name__ == "__main__":
    main()