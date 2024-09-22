import vtk
from typing import List
import math
import numpy as np

class Contour2DPipeline():
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

        self.polyDataThin = vtk.vtkPolyData()
        self.mapperThin = vtk.vtkPolyDataMapper2D()
        self.mapperThin.SetInputData(self.polyDataThin)
        self.actorThin = vtk.vtkActor2D()
        self.actorThin.SetMapper(self.mapperThin)
        outlinePropertyThin = self.actorThin.GetProperty()
        outlinePropertyThin.SetColor(0.7, 0.7, 0)
        outlinePropertyThin.SetLineStipplePattern(0xff00)
        outlinePropertyThin.SetLineWidth(1)
        self.actorThin.VisibilityOff()

class Pipeline():
    def __init__(self) -> None:
        colors = vtk.vtkNamedColors()

        self.polyData = vtk.vtkPolyData()

        # Mappers
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputData(self.polyData)
    
        # Actors
        property = vtk.vtkProperty()
        property.SetColor(colors.GetColor3d("Tomato"))
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.SetProperty(property)
        self.actor.VisibilityOff()

class ImageDataPipeline():
    def __init__(self) -> None:
        self.imageData = vtk.vtkImageData()

        # self.mapper = vtk.vtkImageSliceMapper()
        # self.mapper.SetInputData(self.imageData)

        self.mapper = vtk.vtkDataSetMapper()
        self.mapper.SetInputData(self.imageData)

        # self.imageActor = vtk.vtkImageSlice()
        # self.imageActor.SetMapper(self.mapper)
        # self.imageActor.VisibilityOff()

        self.imageActor = vtk.vtkActor()
        self.imageActor.SetMapper(self.mapper)
        self.imageActor.VisibilityOff()

class BeforeInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline, pipeline2, imgDataPipeline, imageData, map) -> None:
        self.pipeline = pipeline
        self.pipeline2 = pipeline2
        self.imgDataPipeline = imgDataPipeline
        self.imageData = imageData
        self.map = map
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.leftButtonReleaseEvent)

    def leftButtonReleaseEvent(self, obj, event) -> None:
        # print(self.imageData.GetSpacing())
        self.OnLeftButtonUp()
        style = InteractorStyle(self.pipeline, self.pipeline2, self.imgDataPipeline, self.imageData, self.map)
        self.GetInteractor().SetInteractorStyle(style)

class InteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline, pipeline2, imgDataPipeline, imageData, map) -> None:
        self.pipeline = pipeline
        self.pipeline2 = pipeline2
        self.imgDataPipeline = imgDataPipeline
        self.imageData = imageData
        self.map = map

        self.AddObserver("LeftButtonPressEvent", self.left_button_down)
        self.AddObserver("LeftButtonReleaseEvent", self.left_button_up)
        
        # vtkPolyDataNormals is a filter that computes point and/or cell normals for a polygonal mesh
        self.brushPolyDataNormals = vtk.vtkPolyDataNormals()
        self.brushPolyDataNormals.AutoOrientNormalsOn()

        # vtkTransformPolyDataFilter is a filter to transform point coordinates and associated point and cell normals and vectors
        self.worldToModifierLabelmapIjkTransformer = vtk.vtkTransformPolyDataFilter()
        self.worldToModifierLabelmapIjkTransform = vtk.vtkTransform()
        self.worldToModifierLabelmapIjkTransformer.SetTransform(self.worldToModifierLabelmapIjkTransform)
        self.worldToModifierLabelmapIjkTransformer.SetInputConnection(self.brushPolyDataNormals.GetOutputPort())

        # use polydata to mask an image
        # The vtkPolyDataToImageStencil class will convert polydata into an image stencil. 
        # The polydata can either be a closed surface mesh or a series of polyline contours (one contour per slice).
        self.brushPolyDataToStencil = vtk.vtkPolyDataToImageStencil()
        self.brushPolyDataToStencil .SetOutputOrigin(0, 0, 0)
        self.brushPolyDataToStencil.SetOutputSpacing(1, 1, 1)
        # self.brushPolyDataToStencil.SetOutputSpacing(self.imageData.GetSpacing())
        self.brushPolyDataToStencil.SetInputConnection(self.worldToModifierLabelmapIjkTransformer.GetOutputPort())

    @staticmethod
    def createGlyph(pipeline, eventPosition):
        if pipeline.isDragging:
            points = vtk.vtkPoints()
            lines = vtk.vtkCellArray()
            pipeline.polyData.SetPoints(points)
            pipeline.polyData.SetLines(lines)

            # points.InsertNextPoint(0, 0, 0)
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
    def updateGlyphWithNewPosition(pipeline, eventPosition, finalize):
        if pipeline.isDragging:
            points = pipeline.polyData.GetPoints()
            newPointIndex = points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            idList = vtk.vtkIdList()
            if finalize:
                idList.InsertNextId(newPointIndex)
                idList.InsertNextId(0)
            else:
                idList.InsertNextId(newPointIndex - 1)
                idList.InsertNextId(newPointIndex)
            pipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)
            points.Modified()
            pipeline.polyDataThin.GetPoints().SetPoint(1, eventPosition[0], eventPosition[1], 0)
            pipeline.polyDataThin.GetPoints().Modified()
        else:
            pipeline.actor.VisibilityOff()
            pipeline.actorThin.VisibilityOff()

    def left_button_down(self, obj, event):
        self.pipeline.isDragging = True
        eventPosition = self.GetInteractor().GetEventPosition()
        self.createGlyph(self.pipeline, eventPosition)

        if not self.HasObserver("MouseMoveEvent"):
            self.AddObserver("MouseMoveEvent", self.mouse_move)
        self.OnLeftButtonDown()

    def mouse_move(self, obj, event):
        if self.pipeline.isDragging:
            eventPosition = self.GetInteractor().GetEventPosition()
            self.updateGlyphWithNewPosition(self.pipeline, eventPosition, False)
            self.GetInteractor().Render()
            
    def left_button_up(self, obj, event):
        if self.pipeline.isDragging:
            eventPosition = self.GetInteractor().GetEventPosition()
            self.pipeline.isDragging = False
            self.updateGlyphWithNewPosition(self.pipeline, eventPosition, True)

            if self.HasObserver("MouseMoveEvent"):
                self.RemoveObservers("MouseMoveEvent")
        
            self.updateBrushModel()

            self.OnLeftButtonUp()

            style = vtk.vtkInteractorStyleTrackballCamera()
            self.GetInteractor().SetInteractorStyle(style)

    def updateBrushModel(self):
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()

        pointsXY = self.pipeline.polyData.GetPoints() # Return vtkPoints object
        numberOfPoints = pointsXY.GetNumberOfPoints()

        segmentationToWorldMatrix = vtk.vtkMatrix4x4()
        segmentationToWorldMatrix.Identity()

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
        # Camera view up
        cameraViewUp = list(camera.GetViewUp())
        vtk.vtkMath().Normalize(cameraViewUp)
        
        renderer.SetWorldPoint(cameraFP[0], cameraFP[1], cameraFP[2], cameraFP[3])
        renderer.WorldToDisplay()
        displayCoords = renderer.GetDisplayPoint()
        selectionZ = displayCoords[2]

        # Get modifier labelmap extent in camera coordinates to know how much we have to cut through
        cameraToWorldMatrix = vtk.vtkMatrix4x4()
        cameraViewRight = [1, 0, 0]
        vtk.vtkMath().Cross(cameraDOP, cameraViewUp, cameraViewRight) # Tich co huong
        for i in range(3):
            cameraToWorldMatrix.SetElement(i, 0, cameraViewUp[i])
            cameraToWorldMatrix.SetElement(i, 1, cameraViewRight[i])
            cameraToWorldMatrix.SetElement(i, 2, cameraDOP[i])
            cameraToWorldMatrix.SetElement(i, 3, cameraPos[i])
            # [cameraViewUp cameraViewRight cameraDOP cameraPos]
        worldToCameraMatrix = vtk.vtkMatrix4x4()
        vtk.vtkMatrix4x4().Invert(cameraToWorldMatrix, worldToCameraMatrix) # Chuyen vi
        segmentationToCameraTransform = vtk.vtkTransform()
        # Tinh tich 2 ma tran
        segmentationToCameraTransform.Concatenate(worldToCameraMatrix)
        segmentationToCameraTransform.Concatenate(segmentationToWorldMatrix)

        # Calculate values of segmentationBounds_Camera
        segmentationBounds_Camera = [0, -1, 0, -1, 0, -1]
        vtk.vtkMath().UninitializeBounds(segmentationBounds_Camera) # [1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
        imageExtentCenter = self.imageData.GetExtent()
        imageToWorldMatrix = vtk.vtkMatrix4x4()
        imageToWorldMatrix.Identity()
        origin = self.imageData.GetOrigin()
        spacing = self.imageData.GetSpacing()
        directionMatrix = self.imageData.GetDirectionMatrix()
        for row in range(3):
            for col in range(3):
                imageToWorldMatrix.SetElement(row, col, spacing[col] * directionMatrix.GetElement(row, col))
            imageToWorldMatrix.SetElement(row, 3, origin[row])
        imageExtent = [
            imageExtentCenter[0] - 0.5, imageExtentCenter[1] + 0.5,
            imageExtentCenter[2] - 0.5, imageExtentCenter[3] + 0.5,
            imageExtentCenter[4] - 0.5, imageExtentCenter[5] + 0.5
        ]
        appendPolyData = vtk.vtkAppendPolyData()
        for i in range(6):
            normalAxis = int(i/2)
            currentPlaneOriginImage = [imageExtent[0], imageExtent[2], imageExtent[4], 1.0]
            currentPlaneOriginImage[normalAxis] += (imageExtent[i] - imageExtent[normalAxis * 2])
            currentPlaneOriginWorld = [0, 0, 0, 1]
            imageToWorldMatrix.MultiplyPoint(currentPlaneOriginImage, currentPlaneOriginWorld)
            # print(currentPlaneOriginWorld)

            currentPlanePoint1Image = [currentPlaneOriginImage[0], currentPlaneOriginImage[1], currentPlaneOriginImage[2], 1.0]
            point1Axis = (normalAxis + 1) % 3
            currentPlanePoint1Image[point1Axis] = imageExtent[point1Axis * 2 + 1]
            currentPlanePoint1World = [0, 0, 0, 1]
            imageToWorldMatrix.MultiplyPoint(currentPlanePoint1Image, currentPlanePoint1World)
            # print(currentPlanePoint1World)

            currentPlanePoint2Image = [currentPlaneOriginImage[0], currentPlaneOriginImage[1], currentPlaneOriginImage[2], 1.0]
            point2Axis = 3 - normalAxis - point1Axis
            currentPlanePoint2Image[point2Axis] = imageExtent[point2Axis * 2 + 1]
            currentPlanePoint2World = [0, 0, 0, 1]
            imageToWorldMatrix.MultiplyPoint(currentPlanePoint2Image, currentPlanePoint2World)

            planeSource = vtk.vtkPlaneSource()
            planeSource.SetOrigin(currentPlaneOriginWorld[0], currentPlaneOriginWorld[1], currentPlaneOriginWorld[2])
            planeSource.SetPoint1(currentPlanePoint1World[0], currentPlanePoint1World[1], currentPlanePoint1World[2])
            planeSource.SetPoint2(currentPlanePoint2World[0], currentPlanePoint2World[1], currentPlanePoint2World[2])
            planeSource.SetResolution(5, 5)
            planeSource.Update()

            appendPolyData.AddInputData(planeSource.GetOutput())
        transformFilter = vtk.vtkTransformPolyDataFilter()
        transformFilter.SetInputConnection(appendPolyData.GetOutputPort())
        transformFilter.SetTransform(segmentationToCameraTransform)
        transformFilter.Update()
        transformFilter.GetOutput().ComputeBounds()
        segmentationBounds_Camera = transformFilter.GetOutput().GetBounds()
        # print(segmentationBounds_Camera)
        clipRangeFromModifierLabelmap = [
            min(segmentationBounds_Camera[4], segmentationBounds_Camera[5]),
            max(segmentationBounds_Camera[4], segmentationBounds_Camera[5])
        ]
        clipRangeFromModifierLabelmap[0] -= 0.5
        clipRangeFromModifierLabelmap[1] += 0.5
        clipRangeFromCamera = camera.GetClippingRange()
        clipRange = [
            max(clipRangeFromModifierLabelmap[0], clipRangeFromCamera[0]),
            min(clipRangeFromModifierLabelmap[1], clipRangeFromCamera[1])
        ]

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

        # Skirt
        closedSurfaceStrips = vtk.vtkCellArray() # object to represent cell connectivity
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
        # closedSurfacePolyData = vtk.vtkPolyData()
        closedSurfacePolyData = self.pipeline2.polyData
        closedSurfacePolyData.SetPoints(closedSurfacePoints)
        closedSurfacePolyData.SetStrips(closedSurfaceStrips)
        closedSurfacePolyData.SetPolys(closedSurfacePolys)

        # self.pipeline2.actor.VisibilityOn()
        # self.GetInteractor().Render()

        self.brushPolyDataNormals.SetInputData(closedSurfacePolyData)
        self.brushPolyDataNormals.Update()

        self.updateBrushStencil()

    def updateBrushStencil(self):
        self.worldToModifierLabelmapIjkTransform.Identity()

        segmentationToSegmentationIjkTransformMatrix = vtk.vtkMatrix4x4()
        origin = self.imageData.GetOrigin()
        spacing = self.imageData.GetSpacing()
        directionMatrix = self.imageData.GetDirectionMatrix()
        segmentationToSegmentationIjkTransformMatrix.Identity()
        for row in range(3):
            for col in range(3):
                segmentationToSegmentationIjkTransformMatrix.SetElement(row, col, spacing[col] * directionMatrix.GetElement(col, row))
            segmentationToSegmentationIjkTransformMatrix.SetElement(row, 3, origin[row])
        segmentationToSegmentationIjkTransformMatrix.Invert()

        self.worldToModifierLabelmapIjkTransform.Concatenate(segmentationToSegmentationIjkTransformMatrix)

        worldToSegmentationTransformMatrix = vtk.vtkMatrix4x4()
        worldToSegmentationTransformMatrix.Identity()

        self.worldToModifierLabelmapIjkTransform.Concatenate(worldToSegmentationTransformMatrix)
        # print(self.worldToModifierLabelmapIjkTransform)

        self.worldToModifierLabelmapIjkTransformer.Update()

        brushModel_ModifierLabelmapIjk = self.worldToModifierLabelmapIjkTransformer.GetOutput() # return vtkPolyData object
        boundsIjk = brushModel_ModifierLabelmapIjk.GetBounds()
        self.brushPolyDataToStencil.SetOutputWholeExtent(
            math.floor(boundsIjk[0]) - 1, math.ceil(boundsIjk[1]) + 1,
            math.floor(boundsIjk[2]) - 1, math.ceil(boundsIjk[3]) + 1,
            math.floor(boundsIjk[4]) - 1, math.ceil(boundsIjk[5]) + 1,
        )

        self.paintApply()

    def paintApply(self):
        self.brushPolyDataToStencil.Update()
        stencilData = self.brushPolyDataToStencil.GetOutput() # vtkImageStencilData
        stencilExtent = stencilData.GetExtent()
        # print(stencilExtent)
        # ...
        # vtkImageStencilToImage will convert an image stencil into a binary image
        # The default output will be an 8-bit image with a value of 1 inside the stencil and 0 outside
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetInputData(self.brushPolyDataToStencil.GetOutput())
        # print(self.brushPolyDataToStencil.GetOutput())
        stencilToImage.SetInsideValue(1)
        stencilToImage.SetOutsideValue(0)
        stencilToImage.SetOutputScalarType(self.imageData.GetScalarType()) # vtk.VTK_SHORT: [-32768->32767], vtk.VTK_UNSIGNED_CHAR: [0->255]
        # stencilToImage.SetOutputScalarType(vtk.VTK_UNSIGNED_CHAR)
        stencilToImage.Update()
        # print(stencilToImage.GetOutput()) # vtkImageData

        orientedBrushPositionerOutput = vtk.vtkImageData()
        orientedBrushPositionerOutput.DeepCopy(stencilToImage.GetOutput())

        imageToWorld = vtk.vtkMatrix4x4()
        imageToWorld.Identity()
        origin = self.imageData.GetOrigin()
        spacing = self.imageData.GetSpacing()
        directionMatrix = self.imageData.GetDirectionMatrix()
        for row in range(3):
            for col in range(3):
                imageToWorld.SetElement(row, col, spacing[col] * directionMatrix.GetElement(row, col))
            imageToWorld.SetElement(row, 3, origin[row])

        mat = vtk.vtkMatrix4x4()
        mat.DeepCopy(imageToWorld)
        isModified = False
        nspacing = list(orientedBrushPositionerOutput.GetSpacing())
        norigin = list(orientedBrushPositionerOutput.GetOrigin())
        ndirections = orientedBrushPositionerOutput.GetDirectionMatrix()
        for col in range(3):
            len = 0
            for row in range(3):
                len += mat.GetElement(row, col) * mat.GetElement(row, col)
            len = math.sqrt(len)
            # Set spacing
            if nspacing[col] != len:
                nspacing[col] = len
                isModified = True
            for row in range(3):
                mat.SetElement(row, col, mat.GetElement(row, col) / len)
        for row in range(3):
            for col in range(3):
                # Set directions
                if ndirections.GetElement(row, col) != mat.GetElement(row, col):
                    ndirections.SetElement(row, col, mat.GetElement(row, col))
                    isModified = True
                # Set origin
                if norigin[row] != mat.GetElement(row, 3):
                    norigin[row] = mat.GetElement(row, 3)
                    isModified = True
        if isModified:
            orientedBrushPositionerOutput.SetSpacing(nspacing)
            orientedBrushPositionerOutput.SetOrigin(norigin)
            orientedBrushPositionerOutput.Modified()
        # print(orientedBrushPositionerOutput)

        # self.imgDataPipeline.imageData.DeepCopy(orientedBrushPositionerOutput)
        # self.imgDataPipeline.imageData.DeepCopy(stencilToImage.GetOutput())
        # self.imgDataPipeline.imageData.DeepCopy(brushPositioner.GetOutput())
        # print(self.imgDataPipeline.imageData)
        # self.imgDataPipeline.imageActor.VisibilityOn()
        # self.GetInteractor().Render()

        baseImage = vtk.vtkImageData() # modifierLabelmap
        baseImage.SetExtent(self.imageData.GetExtent())
        baseImage.SetOrigin(self.imageData.GetOrigin())
        baseImage.SetSpacing(self.imageData.GetSpacing())
        baseImage.SetDirectionMatrix(self.imageData.GetDirectionMatrix())
        baseImage.AllocateScalars(self.imageData.GetScalarType(), 1)
        # print(baseImage)

        # modifierImage = stencilToImage.GetOutput() # vtkImageData
        # print(modifierImage)

        # self.modifyImage(baseImage, modifierImage)
        self.modifyImage(baseImage, orientedBrushPositionerOutput)

    def modifyImage(self, baseImage: vtk.vtkImageData, modifierImage: vtk.vtkImageData):
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
        
        baseIncX = vtk.reference(0); baseIncY = vtk.reference(0); baseIncZ = vtk.reference(0)
        modifierIncX = vtk.reference(0); modifierIncY = vtk.reference(0); modifierIncZ = vtk.reference(0)

        # baseImage.GetContinuousIncrements(updateExtent, baseIncX, baseIncY, baseIncZ)
        # modifierImage.GetContinuousIncrements(updateExtent, modifierIncX, modifierIncY, modifierIncZ)
        # print(baseIncX, baseIncY, baseIncZ); print(modifierIncX, modifierIncY, modifierIncZ)

        maxX = (updateExtent[1] - updateExtent[0]) * baseImage.GetNumberOfScalarComponents()
        maxY = updateExtent[3] - updateExtent[2]
        maxZ = updateExtent[5] - updateExtent[4]
        
        # baseImagePtr =  baseImage.GetScalarPointerForExtent(updateExtent)
        # modifierImagePtr = modifierImage.GetScalarPointerForExtent(updateExtent)

        baseImageModified = False
        # print(updateExtent)
        for z in range(updateExtent[4], updateExtent[5] + 1):
            for y in range(updateExtent[2], updateExtent[3] + 1):
                for x in range(updateExtent[0], updateExtent[1] + 1):
                    if modifierImage.GetScalarComponentAsFloat(x, y, z, 0) > baseImage.GetScalarComponentAsFloat(x, y, z, 0):
                        baseImage.SetScalarComponentFromFloat(x, y, z, 0, modifierImage.GetScalarComponentAsFloat(x, y, z, 0))
                        baseImageModified = True
        if baseImageModified:
            baseImage.Modified()
        # print(baseImage)

        # ...

        self.maskVolume(baseImage)
    
    def maskVolume(self, baseImage):

        # mask volume
        maskToStencil = vtk.vtkImageToImageStencil()
        maskToStencil.ThresholdByLower(0)
        maskToStencil.SetInputData(baseImage)
        maskToStencil.Update()
        
        stencil = vtk.vtkImageStencil()
        stencil.SetInputData(self.imageData)
        stencil.SetStencilConnection(maskToStencil.GetOutputPort())
        stencil.Update()

        # self.imgDataPipeline.imageData.DeepCopy(baseImage)
        # print(self.imgDataPipeline.imageData)
        # self.imgDataPipeline.imageActor.VisibilityOn()
        # self.GetInteractor().Render()
        # print(stencil.GetOutput()) # vtkImageData

        self.map.SetInputData(stencil.GetOutput())

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
    path4 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/digest_article"
    path5 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/1.2.840.113619.2.428.3.678656.285.1684973027.401"

    rgb_points = to_rgb_points(STANDARD)
    colors = vtk.vtkNamedColors()
    reader = vtk.vtkDICOMImageReader()
    map = vtk.vtkSmartVolumeMapper()
    # map = vtk.vtkFixedPointVolumeRayCastMapper()
    vol = vtk.vtkVolume()
    volProperty = vtk.vtkVolumeProperty()
    render = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    scalarOpacity = vtk.vtkPiecewiseFunction()
    color = vtk.vtkColorTransferFunction()
    renIn = vtk.vtkRenderWindowInteractor()

    pipeline = Contour2DPipeline()
    pipeline2 = Pipeline()
    imgDataPipeline = ImageDataPipeline()

    # Outline
    # Description: drawing a bounding box out volume object
    outline = vtk.vtkOutlineFilter()
    outline.SetInputConnection(reader.GetOutputPort())
    outlineMapper = vtk.vtkPolyDataMapper()
    outlineMapper.SetInputConnection(outline.GetOutputPort())
    outlineActor = vtk.vtkActor()
    outlineActor.SetMapper(outlineMapper)
    outlineActor.GetProperty().SetColor(0, 0, 0)
    
    reader.SetDirectoryName(path2)
    reader.Update()
    imageData = reader.GetOutput() # vtkImageData

    # origin = [0, 0, 0]
    # spacing = imageData.GetSpacing()
    # dimention = imageData.GetDimensions()
    # origin[0] = -spacing[0] * (dimention[0] - 1) / 2
    # origin[1] = -spacing[1] * (dimention[1] - 1) / 2
    # origin[2] = -spacing[2] * (dimention[2] - 1) / 2
    # imageData.SetOrigin(origin)
    # imageData.SetOrigin(174.8000, 180.0000, -352.2200)
    
    # imageData.SetDirectionMatrix(-1, 0, 0, 0, -1, 0, 0, 0, 1)

    # print(imageData)
    
    # This option will use hardware accelerated rendering exclusively
    # This is a good option if you know there is hardware acceleration
    map.SetRequestedRenderModeToGPU()
    map.SetInputData(imageData)

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
    # scalarOpacity.AddPoint(80, 0)
    # scalarOpacity.AddPoint(400, 0.2)
    # scalarOpacity.AddPoint(1000, 1)
    # Muscle preset
    scalarOpacity.AddPoint(-63.16470588235279, 0)
    scalarOpacity.AddPoint(559.1764705882356, 1)
    volProperty.SetScalarOpacity(scalarOpacity)

    vol.SetMapper(map)
    vol.SetProperty(volProperty)

    render.SetBackground(colors.GetColor3d("White"))
    render.AddVolume(vol)
    render.AddActor(outlineActor)
    # Add actors of Contour2DPipeline
    render.AddActor(pipeline.actor)
    render.AddActor(pipeline.actorThin)
    # Add actor of Pipeline
    render.AddActor(pipeline2.actor)
    # Add actor of ImageDataPipeline
    # render.AddViewProp(imgDataPipeline.imageActor)
    render.AddActor(imgDataPipeline.imageActor)
    
    renWin.SetWindowName("3D Dicom")
    renWin.SetSize(500, 500)
    renWin.AddRenderer(render)
    
    renIn.SetRenderWindow(renWin)
    cellPicker = vtk.vtkCellPicker()
    cellPicker.AddPickList(vol)
    cellPicker.PickFromListOn()
    renIn.SetPicker(cellPicker)
    style = BeforeInteractorStyle(pipeline, pipeline2, imgDataPipeline, imageData, map)
    renIn.SetInteractorStyle(style)

    renIn.Initialize()
    renIn.Start()

if __name__ == "__main__":
    main()