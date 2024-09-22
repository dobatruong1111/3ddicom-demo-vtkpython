import vtk

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

def to_rgb_points(colormap):
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

def create_sphere() -> vtk.vtkActor:
    pass

def viewPlane(path: str) -> None:
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(1000, 500)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    interactorStyle = vtk.vtkInteractorStyleTrackballCamera()
    renderWindowInteractor.SetInteractorStyle(interactorStyle)
    renderWindow.SetInteractor(renderWindowInteractor)
    renderWindow.AddRenderer(renderer)

    reader = vtk.vtkDICOMImageReader()
    reader.SetDirectoryName(path)
    reader.Update()
    imageData = reader.GetOutput()
    
    volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
    volumeMapper.SetInputData(imageData)
    volume = vtk.vtkVolume()
    volume.SetMapper(volumeMapper)
    volumeProperty = vtk.vtkVolumeProperty()
    set_volume_properties(volumeProperty)
    volume.SetProperty(volumeProperty)
    (xMin, xMax, yMin, yMax, zMin, zMax) = volume.GetBounds()
    print(f"bounds: {volume.GetBounds()}")
    center = volume.GetCenter()
    print(f"center: {center}")

    renderer.AddVolume(volume)
    # Automatically set up the camera based on the visible actors
    renderer.ResetCamera()

    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(center)
    
    # I (default)
    camera.SetPosition(center[0], center[1], 3*(zMax-zMin))
    camera.SetViewUp(0, 1, 0)

    # A
    # camera.SetPosition(center[0], 3*(yMax-yMin), center[2])
    # camera.SetViewUp(0, 0, -1)

    # P
    # camera.SetPosition(center[0], -3*(yMax-yMin), center[2])
    # camera.SetViewUp(0, 0, -1)

    # L
    # camera.SetPosition(-3*(xMax-xMin), center[1], center[2])
    # camera.SetViewUp(0, 0, -1)

    # R
    # camera.SetPosition(3*(xMax-xMin), center[1], center[2])
    # camera.SetViewUp(0, 0, -1)

    # S
    # camera.SetPosition(center[0], center[1], -3*(zMax-zMin))
    # camera.SetViewUp(0, -1, 0)

    # Start
    renderWindowInteractor.Start()

def set_volume_properties(volumeProperty: vtk.vtkVolumeProperty) -> None:
    gradientOpacity = vtk.vtkPiecewiseFunction()
    scalarOpacity = vtk.vtkPiecewiseFunction()
    colorTransferFunction = vtk.vtkColorTransferFunction()

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

    scalarOpacity.AddPoint(184.129411764706, 0)
    scalarOpacity.AddPoint(2271.070588235294, 1)
    volumeProperty.SetScalarOpacity(scalarOpacity)

    rgb_points = to_rgb_points(STANDARD)
    for rgb_point in rgb_points:
        colorTransferFunction.AddRGBPoint(rgb_point[0], rgb_point[1], rgb_point[2], rgb_point[3])
    volumeProperty.SetColor(colorTransferFunction)

if __name__ == "__main__":
    viewPlane("D:/javaworkspace/viewer-core/server3d/data/1.3.12.2.1107.5.1.4.66827.30000023041823414870500000460/1.3.12.2.1107.5.1.4.66827.30000023041823425238300067039/data")
