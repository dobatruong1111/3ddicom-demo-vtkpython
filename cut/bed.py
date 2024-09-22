import vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
import vtkITK

# import utils

from typing import List
import math

def GetAllLabelValues(labels: vtk.vtkIntArray, labelmap: vtk.vtkImageData) -> None:
    dimensions = labelmap.GetDimensions()
    if dimensions[0] <= 0 or dimensions[1] <= 0 or dimensions[2] <= 0:
        # labelmap is empty, there are no label values
        # Running vtkImageAccumulate would cause a crash
        return

    scalarRange = labelmap.GetScalarRange()
    lowLabel = math.floor(scalarRange[0])
    highLabel = math.ceil(scalarRange[1])

    imageAccumulate = vtk.vtkImageAccumulate()
    imageAccumulate.SetInputData(labelmap)
    imageAccumulate.IgnoreZeroOn()
    imageAccumulate.SetComponentExtent(lowLabel, highLabel, 0, 0, 0, 0)
    imageAccumulate.SetComponentOrigin(0, 0, 0)
    imageAccumulate.SetComponentSpacing(1, 1, 1)
    imageAccumulate.Update()

    # print(imageAccumulate.GetOutput().GetPointData().GetScalars().GetTuple1(0))
    # print(vtk_to_numpy(imageAccumulate.GetOutput().GetPointData().GetScalars()))
    # print(imageAccumulate.GetVoxelCount()) # số voxel khác 0 

    for label in range(lowLabel, highLabel + 1):
        if label == 0:
            continue
        frequency = imageAccumulate.GetOutput().GetPointData().GetScalars().GetTuple1(label - lowLabel)
        if frequency == 0:
            continue
        labels.InsertNextValue(label)

"""
Description: Thresholding for origin image
"""
def imageThreshold(imageData: vtk.vtkImageData, imageThresh=-50) -> vtk.vtkImageData:
    scalarRange = imageData.GetScalarRange()

    thresh = vtk.vtkImageThreshold()
    thresh.SetInputData(imageData)
    thresh.ThresholdBetween(imageThresh, scalarRange[1])
    thresh.SetInValue(1)
    thresh.SetOutValue(0)
    thresh.SetOutputScalarType(imageData.GetScalarType())
    thresh.Update()

    return thresh.GetOutput() # vtkImageData

def splitSegments(imageData: vtk.vtkImageData, minimumSize=1000, maxNumberOfSegments=1, split=True):
    # modifierlabelmap
    selectedSegmentLabelmap = imageThreshold(imageData)
    
    # Change scalar type of image data
    castIn = vtk.vtkImageCast()
    castIn.SetInputData(selectedSegmentLabelmap)
    castIn.SetOutputScalarTypeToUnsignedInt()
    castIn.Update()

    # Xác định các island trong inverted volume và tìm pixel tương ứng với background
    islandMath = vtkITK.vtkITKIslandMath()
    islandMath.SetInputConnection(castIn.GetOutputPort())
    islandMath.SetFullyConnected(False)
    islandMath.SetMinimumSize(minimumSize)
    islandMath.Update()
    # print(islandMath.GetOutput())
    # print(islandMath.GetOutput().GetScalarRange()) # (0, 2)
    # print(islandMath.GetOutput()) # vtkImageData
    
    islandImage = vtk.vtkImageData()
    islandImage.DeepCopy(islandMath.GetOutput())
    # print(islandImage)

    # islandCount = islandMath.GetNumberOfIslands()
    # islandOrigCount = islandMath.GetOriginalNumberOfIslands()
    # ignoredIslands = islandOrigCount - islandCount
    # print(islandOrigCount)

    labelValues = vtk.vtkIntArray()
    GetAllLabelValues(labelValues, islandImage)
    # print(labelValues.GetTuple1(1))
    # print(vtk_to_numpy(labelValues))
    # print(labelValues.GetNumberOfTuples()) # size of array

    for i in range(labelValues.GetNumberOfTuples()):
        if maxNumberOfSegments > 0 and i >= maxNumberOfSegments:
            break

        labelValue = int(labelValues.GetTuple1(i))
        
        threshold = vtk.vtkImageThreshold()
        threshold.SetInputData(islandMath.GetOutput())
        if not split and maxNumberOfSegments <= 0:
            threshold.ThresholdByLower(0)
            threshold.SetInValue(0)
            threshold.SetOutValue(1)
        else:
            threshold.ThresholdBetween(labelValue, labelValue)
            threshold.SetInValue(1)
            threshold.SetOutValue(0)
        threshold.Update()

        modifierImage = vtk.vtkImageData()
        modifierImage.DeepCopy(threshold.GetOutput())
        # selectedSegmentLabelmapImageToWorldMatrix = vtk.vtkMatrix4x4()
        # utils.GetImageToWorldMatrix(selectedSegmentLabelmap, selectedSegmentLabelmapImageToWorldMatrix)
        # utils.SetImageToWorldMatrix(modifierImage, selectedSegmentLabelmapImageToWorldMatrix)
        # print(modifierImage.GetScalarType())

        castIn = vtk.vtkImageCast()
        castIn.SetInputData(modifierImage)
        castIn.SetOutputScalarTypeToUnsignedChar()
        castIn.Update()

        return castIn.GetOutput()

def maskVolume(imageData: vtk.vtkImageData, maskImage: vtk.vtkImageData, fillValue=-1000) -> vtk.vtkImageData:
    nshape = tuple(reversed(maskImage.GetDimensions()))
    inputArray = vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(nshape)
    maskArray = vtk_to_numpy(maskImage.GetPointData().GetScalars()).reshape(nshape).astype(float)

    resultArray = inputArray[:] * maskArray[:] + float(fillValue) * (1 - maskArray[:])

    resultImage = numpy_to_vtk(resultArray.astype(inputArray.dtype).reshape(1, -1)[0])

    maskedImageData = vtk.vtkImageData()
    maskedImageData.SetExtent(imageData.GetExtent())
    maskedImageData.SetOrigin(imageData.GetOrigin())
    maskedImageData.SetSpacing(imageData.GetSpacing())
    maskedImageData.SetDirectionMatrix(imageData.GetDirectionMatrix())
    maskedImageData.GetPointData().SetScalars(resultImage)

    return maskedImageData

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
    path2 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/220277460 Nguyen Thanh Dat/Unknown Study/CT 1.25mm Stnd KHONG TIEM"
    path3 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/64733 NGUYEN TAN THANH/DONG MACH CHI DUOI CTA/CT CTA iDose 5"
    path4 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/digest_article"
    path5 = "C:/Users/DELL E5540/Desktop/Python/dicom-data/1.2.840.113619.2.428.3.678656.285.1684973027.401"

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
    modifierLabelmap.DeepCopy(imageData)
    # print(modifierLabelmap.GetPointData().GetScalars().GetNumberOfTuples())

    maskImage = splitSegments(modifierLabelmap)
    maskedImageData = maskVolume(imageData, maskImage)
    
    # This option will use hardware accelerated rendering exclusively
    # This is a good option if you know there is hardware acceleration
    mapper.SetRequestedRenderModeToGPU()
    mapper.SetInputData(maskedImageData)

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

    # imageDataMapper = vtk.vtkImageSliceMapper()
    # imageDataMapper.SetInputData(maskImage)
    # imageDataActor = vtk.vtkImageSlice()
    # imageDataActor.SetMapper(imageDataMapper)

    renderer.SetBackground(colors.GetColor3d("White"))
    renderer.AddVolume(volume)
    renderer.AddActor(outlineActor)
    # renderer.AddActor(imageDataActor)
    
    renderWindow.SetWindowName("3D Dicom")
    renderWindow.SetSize(500, 500)
    renderWindow.AddRenderer(renderer)
    
    renderWindowIn.SetRenderWindow(renderWindow)
    style = vtk.vtkInteractorStyleTrackballCamera()
    renderWindowIn.SetInteractorStyle(style)

    renderWindowIn.Initialize()
    renderWindowIn.Start()

if __name__ == "__main__":
    main()