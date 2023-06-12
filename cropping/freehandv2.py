import vtk
from vtkmodules.vtkCommonCore import vtkMath, vtkCommand
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from enum import Enum
from typing import List, Tuple
import time

import utils

class Operation(Enum): 
    INSIDE=1,
    OUTSIDE=2

# Description: Drawing a 2D contour on display coordinates
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

        # Thin 
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

        # Test
        colors = vtk.vtkNamedColors()
        self.polyData3D = vtk.vtkPolyData()
        # Mappers
        self.polyData3Dmapper = vtk.vtkPolyDataMapper()
        self.polyData3Dmapper.SetInputData(self.polyData3D)
        # Actors
        property = vtk.vtkProperty()
        property.SetColor(colors.GetColor3d("Tomato"))
        self.polyData3Dactor = vtk.vtkActor()
        self.polyData3Dactor.SetMapper(self.polyData3Dmapper)
        self.polyData3Dactor.SetProperty(property)
        self.polyData3Dactor.VisibilityOff()

        # Test
        self.imageData = vtk.vtkImageData()
        self.imageDataMapper = vtk.vtkImageSliceMapper()
        self.imageDataMapper.SetInputData(self.imageData)
        # self.imageDataMapper = vtk.vtkDataSetMapper()
        # self.imageDataMapper.SetInputData(self.imageData)
        self.imageDataActor = vtk.vtkImageSlice()
        self.imageDataActor.SetMapper(self.imageDataMapper)
        self.imageDataActor.VisibilityOff()
        # self.imageDataActor = vtk.vtkActor()
        # self.imageDataActor.SetMapper(self.imageDataMapper)
        # self.imageDataActor.VisibilityOff()

# Description: Interaction before cropping freehand
class BeforeCropFreehandInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, contour2Dpipeline, imageData, modifierLabelmap, operation, mapper) -> None:
        self.contour2Dpipeline = contour2Dpipeline
        self.imageData = imageData
        self.modifierLabelmap = modifierLabelmap
        self.operation = operation
        self.mapper = mapper

        self.AddObserver(vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)

    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.OnLeftButtonUp()

        style = CropFreehandInteractorStyle(self.contour2Dpipeline, self.imageData, self.modifierLabelmap, self.operation, self.mapper)
        self.GetInteractor().SetInteractorStyle(style)

'''
Description: Interaction for cropping freehand 
    Step 1: Drawing a 2D contour on the screen
    Step 2: Mapping display space points to world positions
    Step 3: Take 2D contour as polydata line, and extrude surfaces from the near clipping plane
            to the far clipping plane.
    Step 4: Take the rasterized polydata from step 3, and do a 3D stencil operation/filter, where
            you leave voxels on if it's in the rasterized volume, and vice-versa. This can be
            inplemented as a filter, at the cost of duplicating the volume memory.
    Step 5: Render the new volume
'''
class CropFreehandInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, contour2Dpipeline, imageData, modifierLabelmap, operation, mapper) -> None:
        # Pipeline used to drawing a 2D contour on the screen
        self.contour2Dpipeline = contour2Dpipeline
        # Origin image data
        self.imageData = imageData
        # Image data extends some properties from origin image data such as: 
        # extent, origin, spacing, direction and scalar type
        self.modifierLabelmap = modifierLabelmap
        self.mapper = mapper
        # operation: INSIDE or OUTSIDE
        self.operation = operation
    
        # Events
        self.AddObserver(vtkCommand.LeftButtonPressEvent, self.__leftButtonPressEvent)
        self.AddObserver(vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
        self.AddObserver(vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)
        
        # Được sử dụng để tính toán vector pháp tuyến cho dữ liệu vtkPolyData.
        # Vector pháp tuyến là thông tin quan trọng trong việc hiển thị và tính toán trên đối tượng.
        self.brushPolyDataNormals = vtk.vtkPolyDataNormals()
        self.brushPolyDataNormals.AutoOrientNormalsOn()

        # Được sử dụng để áp dụng một phép biến đổi affline lên dữ liệu vtkPolyData.
        # Nó thực hiện biến đổi các điểm, hướng pháp tuyến,... theo phép biến đổi đã được xác định.
        self.worldToModifierLabelmapIjkTransformer = vtk.vtkTransformPolyDataFilter()
        self.worldToModifierLabelmapIjkTransform = vtk.vtkTransform()
        self.worldToModifierLabelmapIjkTransformer.SetTransform(self.worldToModifierLabelmapIjkTransform)
        self.worldToModifierLabelmapIjkTransformer.SetInputConnection(self.brushPolyDataNormals.GetOutputPort())

        # Image stencil là một đối tượng dữ liệu dạng ma trận nhị phân có cùng kích thước và phân giải với một hình ảnh.
        # Sử dụng image stencil để thực hiện các phép biến đổi hoặc lọc hình ảnh trên phạm vi chỉ định bởi vtkPolyData.
        self.brushPolyDataToStencil = vtk.vtkPolyDataToImageStencil()
        self.brushPolyDataToStencil .SetOutputOrigin(0, 0, 0)
        self.brushPolyDataToStencil.SetOutputSpacing(1, 1, 1)
        self.brushPolyDataToStencil.SetInputConnection(self.worldToModifierLabelmapIjkTransformer.GetOutputPort())

    def __createGlyph(self, eventPosition: Tuple) -> None:
        if self.contour2Dpipeline.isDragging:
            points = vtk.vtkPoints()
            lines = vtk.vtkCellArray()
            self.contour2Dpipeline.polyData.SetPoints(points)
            self.contour2Dpipeline.polyData.SetLines(lines)

            points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

            # Thin
            pointsThin = vtk.vtkPoints()
            linesThin = vtk.vtkCellArray()
            self.contour2Dpipeline.polyDataThin.SetPoints(pointsThin)
            self.contour2Dpipeline.polyDataThin.SetLines(linesThin)

            pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

            idList = vtk.vtkIdList()
            idList.InsertNextId(0)
            idList.InsertNextId(1)
            self.contour2Dpipeline.polyDataThin.InsertNextCell(vtk.VTK_LINE, idList)

            self.contour2Dpipeline.actorThin.VisibilityOn()
            self.contour2Dpipeline.actor.VisibilityOn()
        else:
            self.contour2Dpipeline.actor.VisibilityOff()
            self.contour2Dpipeline.actorThin.VisibilityOff()

    def __updateGlyphWithNewPosition(self, eventPosition: Tuple, finalize: bool) -> None:
        if self.contour2Dpipeline.isDragging:
            points = self.contour2Dpipeline.polyData.GetPoints()
            newPointIndex = points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            points.Modified()

            idList = vtk.vtkIdList()
            if finalize:
                idList.InsertNextId(newPointIndex)
                idList.InsertNextId(0)
            else:
                idList.InsertNextId(newPointIndex - 1)
                idList.InsertNextId(newPointIndex)

            self.contour2Dpipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)

            self.contour2Dpipeline.polyDataThin.GetPoints().SetPoint(1, eventPosition[0], eventPosition[1], 0)
            self.contour2Dpipeline.polyDataThin.GetPoints().Modified()
        else:
            self.contour2Dpipeline.actor.VisibilityOff()
            self.contour2Dpipeline.actorThin.VisibilityOff()

    def __leftButtonPressEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.contour2Dpipeline.isDragging = True
        eventPosition = self.GetInteractor().GetEventPosition()
        self.__createGlyph(eventPosition)
        self.OnLeftButtonDown()

    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        if self.contour2Dpipeline.isDragging:
            eventPosition = self.GetInteractor().GetEventPosition()
            self.__updateGlyphWithNewPosition(eventPosition, False)
            self.GetInteractor().Render()
            
    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        if self.contour2Dpipeline.isDragging:
            eventPosition = self.GetInteractor().GetEventPosition()
            self.contour2Dpipeline.isDragging = False
            self.__updateGlyphWithNewPosition(eventPosition, True)
            start = time.time()
            self.__paintApply()
            stop = time.time()
            print("-----")
            print("__paintApply():", stop - start)
            self.OnLeftButtonUp()

            style = vtk.vtkInteractorStyleTrackballCamera()
            self.GetInteractor().SetInteractorStyle(style)

    '''
    Description: Extrude surfaces from the near clipping plane to the far clipping plane.
    '''
    def __updateBrushModel(self) -> bool:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()

        pointsXY = self.contour2Dpipeline.polyData.GetPoints() # vtkPoints
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
        vtkMath.Normalize(cameraDOP)
        # Camera view up
        cameraViewUp = list(camera.GetViewUp())
        vtkMath.Normalize(cameraViewUp)
        
        renderer.SetWorldPoint(cameraFP[0], cameraFP[1], cameraFP[2], cameraFP[3])
        renderer.WorldToDisplay()
        displayCoords = renderer.GetDisplayPoint()
        selectionZ = displayCoords[2]

        # Get modifier labelmap extent in camera coordinates to know how much we have to cut through
        cameraToWorldMatrix = vtk.vtkMatrix4x4()
        cameraViewRight = [1, 0, 0]
        vtkMath.Cross(cameraDOP, cameraViewUp, cameraViewRight) # Tich co huong
        for i in range(3):
            cameraToWorldMatrix.SetElement(i, 0, cameraViewUp[i])
            cameraToWorldMatrix.SetElement(i, 1, cameraViewRight[i])
            cameraToWorldMatrix.SetElement(i, 2, cameraDOP[i])
            cameraToWorldMatrix.SetElement(i, 3, cameraPos[i])
        # cameraToWorldMatrix = [cameraViewUp cameraViewRight cameraDOP cameraPos]
        # print(cameraToWorldMatrix)

        worldToCameraMatrix = vtk.vtkMatrix4x4()
        vtk.vtkMatrix4x4().Invert(cameraToWorldMatrix, worldToCameraMatrix)
        # print(worldToCameraMatrix)

        segmentationToCameraTransform = vtk.vtkTransform()
        segmentationToCameraTransform.Concatenate(worldToCameraMatrix)
        segmentationToCameraTransform.Concatenate(segmentationToWorldMatrix)
        # print(segmentationToCameraTransform)

        clipRange = utils.calcClipRange(self.modifierLabelmap, segmentationToCameraTransform, camera)
        
        for pointIndex in range(numberOfPoints):
            # Convert the selection point into world coordinates
            pointXY = pointsXY.GetPoint(pointIndex)
            renderer.SetDisplayPoint(pointXY[0], pointXY[1], selectionZ)
            renderer.DisplayToWorld()
            worldCoords = renderer.GetWorldPoint()
            if worldCoords[3] == 0:
                print("Bad homogeneous coordinates")
                return False
            
            # Convert from homo coordinates to world coordinates
            pickPosition = [0, 0, 0]
            for i in range(3):
                pickPosition[i] = worldCoords[i] / worldCoords[3]

            # Compute the ray endpoints. The ray is along the line running from
            # the camera position to the selection point, starting where this line
            # intersects the front clipping plane, and terminating where this line
            # intersects the back clipping plane.
            ray = [0, 0, 0]
            for i in range(3):
                ray[i] = pickPosition[i] - cameraPos[i] # vector
            rayLength = vtk.vtkMath().Dot(cameraDOP, ray)
            if rayLength == 0:
                print("Cannot process points")
                return False

            # Finding a point on the near clipping plane and a point on the far clipping plane 
            # (two points in world coordinates)
            p1World = [0, 0, 0]
            p2World = [0, 0, 0]
            tF = 0
            tB = 0
            if camera.GetParallelProjection():
                tF = clipRange[0] - rayLength
                tB = clipRange[1] - rayLength
                for i in range(3):
                    p1World[i] = pickPosition[i] + tF * cameraDOP[i]
                    p2World[i] = pickPosition[i] + tB * cameraDOP[i]
            else:
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
        # closedSurfacePolyData = self.contour2Dpipeline.polyData3D
        closedSurfacePolyData = vtk.vtkPolyData()
        closedSurfacePolyData.SetPoints(closedSurfacePoints)
        closedSurfacePolyData.SetStrips(closedSurfaceStrips)
        closedSurfacePolyData.SetPolys(closedSurfacePolys)

        # self.contour2Dpipeline.polyData3Dactor.VisibilityOn()
        # self.GetInteractor().Render()

        self.brushPolyDataNormals.SetInputData(closedSurfacePolyData)
        self.brushPolyDataNormals.Update()

        return True

    '''
    Description:
        Using a transform matrix to convert from world coordinates to model (image) coordinates.
        Set bounds for image stencil with two cases: INSIDE or OUTSIDE
    '''
    def __updateBrushStencil(self) -> None:
        self.worldToModifierLabelmapIjkTransform.Identity()

        segmentationToSegmentationIjkTransformMatrix = vtk.vtkMatrix4x4()
        utils.GetImageToWorldMatrix(self.modifierLabelmap, segmentationToSegmentationIjkTransformMatrix)
        segmentationToSegmentationIjkTransformMatrix.Invert()
        self.worldToModifierLabelmapIjkTransform.Concatenate(segmentationToSegmentationIjkTransformMatrix)

        worldToSegmentationTransformMatrix = vtk.vtkMatrix4x4()
        worldToSegmentationTransformMatrix.Identity()
        self.worldToModifierLabelmapIjkTransform.Concatenate(worldToSegmentationTransformMatrix)

        self.worldToModifierLabelmapIjkTransformer.Update()

        self.brushPolyDataToStencil.SetOutputWholeExtent(self.modifierLabelmap.GetExtent())

    '''
    Description: 
        Convert from image stencil to image data, set cropped region equal 1.
        Set spacing, origin and direction.
    '''
    def __paintApply(self) -> None:
        start = time.time()
        if not self.__updateBrushModel():
            return
        stop = time.time()
        print("__updateBrushModel():", stop-start)
        
        start = time.time()
        self.__updateBrushStencil()
        stop = time.time()
        print("__updateBrushStencil():", stop-start)

        self.brushPolyDataToStencil.Update()
    
        # vtkImageStencilToImage will convert an image stencil into a binary image
        # The default output will be an 8-bit image with a value of 1 inside the stencil and 0 outside
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetInputData(self.brushPolyDataToStencil.GetOutput())

        stencilToImage.SetInsideValue(self.operation == Operation.INSIDE)
        stencilToImage.SetOutsideValue(self.operation != Operation.INSIDE)

        stencilToImage.SetOutputScalarType(self.modifierLabelmap.GetScalarType()) # vtk.VTK_SHORT: [-32768->32767], vtk.VTK_UNSIGNED_CHAR: [0->255]
        stencilToImage.Update()

        orientedBrushPositionerOutput = vtk.vtkImageData()
        orientedBrushPositionerOutput.DeepCopy(stencilToImage.GetOutput())

        imageToWorld = vtk.vtkMatrix4x4()
        utils.GetImageToWorldMatrix(self.modifierLabelmap, imageToWorld)

        utils.SetImageToWorldMatrix(orientedBrushPositionerOutput, imageToWorld)

        utils.modifyImage(self.modifierLabelmap, orientedBrushPositionerOutput)
        start = time.time()
        self.__maskVolume()
        stop = time.time()
        print("__maskVolume():", stop-start)

    '''
    Description: Apply the mask for volume and render the new volume
        Hard edge: CT-Bone, CT-Angio
        Soft edge: CT-Muscle, CT-Mip
    '''
    def __maskVolume(self, fillValue=-1000) -> None:
        # Hard, Soft edge
        # Thresholding of modifierLabelmap
        thresh = vtk.vtkImageThreshold()
        maskMin = 0
        maskMax = 1
        thresh.SetOutputScalarTypeToUnsignedChar() # vtk.VTK_UNSIGNED_CHAR: 0-255
        thresh.SetInputData(self.modifierLabelmap)
        thresh.ThresholdByLower(0) # <= 0
        thresh.SetInValue(maskMin)
        thresh.SetOutValue(maskMax)
        thresh.Update()
        maskImage = thresh.GetOutput()

        nshape = tuple(reversed(maskImage.GetDimensions())) # (z, y, x)

        # Convert binary mask image and origin image data from vtkDataArray (supper class) to numpy
        maskArray = vtk_to_numpy(maskImage.GetPointData().GetScalars()).reshape(nshape).astype(float)
        inputArray = vtk_to_numpy(self.imageData.GetPointData().GetScalars()).reshape(nshape)

        resultArray = inputArray[:] * (1 - maskArray[:]) + float(fillValue) * maskArray[:] # -1000 HU: air

        result = numpy_to_vtk(resultArray.astype(inputArray.dtype).reshape(1, -1)[0])   
        
        maskedImageData = vtk.vtkImageData()
        maskedImageData.SetExtent(self.modifierLabelmap.GetExtent())
        maskedImageData.SetOrigin(self.modifierLabelmap.GetOrigin())
        maskedImageData.SetSpacing(self.modifierLabelmap.GetSpacing())
        maskedImageData.SetDirectionMatrix(self.modifierLabelmap.GetDirectionMatrix())
        maskedImageData.GetPointData().SetScalars(result)
        
        # Render the new volume
        self.mapper.SetInputData(maskedImageData)

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

def main() -> None:
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
    path2 = "../dicomdata/CT1.25mmStndKHONGTIEM"
    path3 = "../dicomdata/digest_article"

    rgb_points = to_rgb_points(STANDARD)
    colors = vtk.vtkNamedColors()
    reader = vtk.vtkDICOMImageReader()
    mapper = vtk.vtkSmartVolumeMapper()
    # map = vtk.vtkFixedPointVolumeRayCastMapper()
    volume = vtk.vtkVolume()
    volumeProperty = vtk.vtkVolumeProperty()
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    scalarOpacity = vtk.vtkPiecewiseFunction()
    color = vtk.vtkColorTransferFunction()
    renderWindowIn = vtk.vtkRenderWindowInteractor()
    contour2Dpipeline = Contour2DPipeline()

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
    modifierLabelmap = vtk.vtkImageData()
    modifierLabelmap.SetExtent(imageData.GetExtent())
    modifierLabelmap.SetOrigin(imageData.GetOrigin())
    modifierLabelmap.SetSpacing(imageData.GetSpacing())
    modifierLabelmap.SetDirectionMatrix(imageData.GetDirectionMatrix())
    modifierLabelmap.AllocateScalars(imageData.GetScalarType(), 1)
    modifierLabelmap.GetPointData().GetScalars().Fill(0)
    # print(imageData)

    # This option will use hardware accelerated rendering exclusively
    # This is a good option if you know there is hardware acceleration
    mapper.SetRequestedRenderModeToGPU()
    mapper.SetInputData(imageData)

    volumeProperty.SetInterpolationTypeToLinear()
    volumeProperty.ShadeOn()
    # Lighting of volume
    volumeProperty.SetAmbient(0.1)
    volumeProperty.SetDiffuse(0.9)
    volumeProperty.SetSpecular(0.2)
    # Color map thought a transfer function
    for rgb_point in rgb_points:
        color.AddRGBPoint(rgb_point[0], rgb_point[1], rgb_point[2], rgb_point[3])
    # CT-MIP 3D Slicer
    # color.AddRGBPoint(-3024.00, 0, 0, 0)
    # color.AddRGBPoint(-637.62, 1, 1, 1)
    volumeProperty.SetColor(color)

    # Bone preset
    # scalarOpacity.AddPoint(184.129411764706, 0)
    # scalarOpacity.AddPoint(2271.070588235294, 1)
    # Angio preset
    # scalarOpacity.AddPoint(125.42352941176478, 0)
    # scalarOpacity.AddPoint(1785, 1)
    # Muscle preset
    scalarOpacity.AddPoint(-63.16470588235279, 0)
    scalarOpacity.AddPoint(559.1764705882356, 1)
    # Mip preset
    # scalarOpacity.AddPoint(-1661.5882352941176, 0)
    # scalarOpacity.AddPoint(2449.5490196078435, 1)
    # CT-MIP 3D Slicer
    # scalarOpacity.AddPoint(-637.62, 0)
    # scalarOpacity.AddPoint(700.0, 1)
    volumeProperty.SetScalarOpacity(scalarOpacity)

    volume.SetMapper(mapper)
    volume.SetProperty(volumeProperty)

    renderer.SetBackground(colors.GetColor3d("White"))
    renderer.AddVolume(volume)
    renderer.AddActor(outlineActor)
    renderer.AddActor(contour2Dpipeline.actor)
    renderer.AddActor(contour2Dpipeline.actorThin)
    # renderer.AddActor(contour2Dpipeline.polyData3Dactor)
    # renderer.AddActor(contour2Dpipeline.imageDataActor)
    
    renderWindow.SetWindowName("3D Dicom")
    renderWindow.SetSize(500, 500)
    renderWindow.AddRenderer(renderer)
    
    renderWindowIn.SetRenderWindow(renderWindow)
    operation = Operation.INSIDE
    style = BeforeCropFreehandInteractorStyle(contour2Dpipeline, imageData, modifierLabelmap, operation, mapper)
    renderWindowIn.SetInteractorStyle(style)

    renderWindowIn.Initialize()
    renderWindowIn.Start()

if __name__ == "__main__":
    main()