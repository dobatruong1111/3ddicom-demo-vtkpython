import vtk, math

from typing import Tuple, List

from vtkmodules.vtkCommonCore import vtkCommand

from utils import to_rgb_points, STANDARD, findProjectionPoint

def main() -> None:
    cone = vtk.vtkConeSource()
    mapper = vtk.vtkPolyDataMapper()
    actor = vtk.vtkActor()
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(500, 500)
    renderWindow.SetWindowName('Cut Tool')
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    style = vtk.vtkInteractorStyleTrackballCamera()
    renderWindowInteractor.SetInteractorStyle(style)

    # Cellpicker
    cellPicker = vtk.vtkCellPicker()
    cellPicker.AddPickList(actor)
    renderWindowInteractor.SetPicker(cellPicker)

    # Distance widget
    distanceRepresentation = vtk.vtkDistanceRepresentation3D()
    distanceWidget = vtk.vtkDistanceWidget()
    distanceWidget.SetInteractor(renderWindowInteractor)
    distanceWidget.SetRepresentation(distanceRepresentation)
    # callback = Callback()
    # distanceWidget.AddObserver(vtkCommand.InteractionEvent, callback)
    # distanceWidget.AddObserver(vtkCommand.StartInteractionEvent, callback)
    
    cone.SetHeight(3.0)
    cone.SetRadius(1.0)
    cone.SetResolution(10)

    mapper.SetInputConnection(cone.GetOutputPort())
    
    actor.SetMapper(mapper)

    renderer.AddActor(actor)
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # Turn on widget
    distanceWidget.On()
    
    renderWindowInteractor.Start()

def distance_widget(path) -> None:
    reader = vtk.vtkDICOMImageReader()
    volumeMapper = vtk.vtkSmartVolumeMapper()
    volume = vtk.vtkVolume()
    volumeProperty = vtk.vtkVolumeProperty()
    renderer = vtk.vtkRenderer()
    # renderer.SetBackground(1, 1, 1)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    interactorStyle = vtk.vtkInteractorStyleTrackballCamera()
    renderWindowInteractor.SetInteractorStyle(interactorStyle)
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(1000, 500)
    renderWindow.SetInteractor(renderWindowInteractor)

    # Cell picker
    cellPicker = vtk.vtkCellPicker()
    cellPicker.AddPickList(volume)
    cellPicker.PickFromListOn()
    renderWindowInteractor.SetPicker(cellPicker)

    # Distance widget
    distanceRepresentation = vtk.vtkDistanceRepresentation2D()
    distanceWidget = vtk.vtkDistanceWidget()
    
    reader.SetDirectoryName(path)
    reader.Update()
    
    volumeMapper.SetInputData(reader.GetOutput())
    volume.SetMapper(volumeMapper)

    set_volume_properties(volumeProperty)
    volume.SetProperty(volumeProperty)

    renderer.AddVolume(volume)
    renderer.ResetCamera()

    renderWindow.AddRenderer(renderer)

    # Distance widget
    if isinstance(distanceRepresentation, vtk.vtkDistanceRepresentation3D):
        # Line property
        distanceRepresentation.GetLineProperty().SetColor(0, 1, 0)
        distanceRepresentation.GetLineProperty().SetLineWidth(1.5)
        # distanceRepresentation.GetLineProperty().SetAmbient(0.1)
        # distanceRepresentation.GetLineProperty().SetDiffuse(0.9)
        # distanceRepresentation.GetLineProperty().SetSpecular(0.2)
        # distanceRepresentation.GetLineProperty().SetSpecularPower(10)
        # distanceRepresentation.GetLineProperty().ShadingOn()
        # Label property
        distanceRepresentation.GetLabelProperty().SetColor(1, 1, 0)
        # distanceRepresentation.SetLabelPosition(1)

        # Scale text (font size along each dimension)
        # distanceRepresentation.SetLabelScale(6, 6, 6)
    else:
        # Line property
        distanceRepresentation.GetAxisProperty().SetColor(0, 1, 0)
        distanceRepresentation.GetAxisProperty().SetLineWidth(1.5)
        # Label property
        distanceRepresentation.GetAxis().GetTitleTextProperty().SetColor(1, 1, 0)
        # distanceRepresentation.GetAxis().SetTitlePosition(1)

        # distanceRepresentation.GetAxis().TickVisibilityOff()

    labelFormat = distanceRepresentation.GetLabelFormat()
    distanceRepresentation.SetLabelFormat(f"{labelFormat} mm")

    distanceWidget.SetRepresentation(distanceRepresentation)
    distanceWidget.SetInteractor(renderWindowInteractor)

    # distanceWidget.GetRepresentation().SetPoint1WorldPosition([0, 0, 0])

    # distanceWidget.AddObserver(vtkCommand.PlacePointEvent, distancePlacePointEventCallback)
    distanceWidget.AddObserver(vtkCommand.InteractionEvent, distanceInteractionEventCallback)
    # distanceWidget.AddObserver(vtkCommand.InteractionEvent, test)
    # distanceWidget.AddObserver(vtkCommand.EndInteractionEvent, test2)
    # distanceWidget.AddObserver(vtkCommand.EndInteractionEvent, distanceEndInteractionEventCallback)

    # Turn on widget
    distanceWidget.On()

    renderWindowInteractor.Start()

def angle_widget(path) -> None:
    reader = vtk.vtkDICOMImageReader()
    volumeMapper = vtk.vtkSmartVolumeMapper()
    volume = vtk.vtkVolume()
    volumeProperty = vtk.vtkVolumeProperty()
    renderer = vtk.vtkRenderer()
    # renderer.SetBackground(1, 1, 1)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    interactorStyle = vtk.vtkInteractorStyleTrackballCamera()
    renderWindowInteractor.SetInteractorStyle(interactorStyle)
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(1000, 500)
    renderWindow.SetInteractor(renderWindowInteractor)

    # Cell picker
    cellPicker = vtk.vtkCellPicker()
    cellPicker.AddPickList(volume)
    cellPicker.PickFromListOn()
    renderWindowInteractor.SetPicker(cellPicker)

    # Distance widget
    angleRepresentation = vtk.vtkAngleRepresentation2D()
    angleWidget = vtk.vtkAngleWidget()
    
    reader.SetDirectoryName(path)
    reader.Update()
    
    volumeMapper.SetInputData(reader.GetOutput())
    volume.SetMapper(volumeMapper)

    set_volume_properties(volumeProperty)
    volume.SetProperty(volumeProperty)

    renderer.AddVolume(volume)
    renderer.ResetCamera()

    renderWindow.AddRenderer(renderer)

    # Distance widget
    if isinstance(angleRepresentation, vtk.vtkAngleRepresentation3D):
        pass
    else:
        angleRepresentation.GetRay1().SetArrowPlacementToNone()
        angleRepresentation.GetRay1().GetProperty().SetLineWidth(1.5)
        angleRepresentation.GetRay1().GetProperty().SetColor(0, 1, 0)

        angleRepresentation.GetArc().GetProperty().SetLineWidth(1.5)
        angleRepresentation.GetArc().GetProperty().SetColor(0, 1, 0)
        angleRepresentation.GetArc().GetLabelTextProperty().SetColor(1, 1, 0)

        angleRepresentation.GetRay2().SetArrowPlacementToNone()
        angleRepresentation.GetRay2().GetProperty().SetLineWidth(1.5)
        angleRepresentation.GetRay2().GetProperty().SetColor(0, 1, 0)

    angleWidget.SetRepresentation(angleRepresentation)
    angleWidget.SetInteractor(renderWindowInteractor)

    angleWidget.AddObserver(vtkCommand.EndInteractionEvent, angleEndInteractionEventCallback)

    # Turn on widget
    angleWidget.On()

    renderWindowInteractor.Start()

def angleEndInteractionEventCallback(obj: vtk.vtkAngleWidget, event: str) -> None:
    cellPicker = obj.GetInteractor().GetPicker()
    renderer = obj.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()

    point1DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint1DisplayPosition(point1DisplayPoint)
    if cellPicker.Pick(point1DisplayPoint[0], point1DisplayPoint[1], point1DisplayPoint[2], renderer):
        pickPosition = cellPicker.GetPickPosition()
        obj.GetRepresentation().SetPoint1WorldPosition(list(pickPosition))

    centerDisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetCenterDisplayPosition(centerDisplayPoint)
    if cellPicker.Pick(centerDisplayPoint[0], centerDisplayPoint[1], centerDisplayPoint[2], renderer):
        pickPosition = cellPicker.GetPickPosition()
        obj.GetRepresentation().SetCenterWorldPosition(list(pickPosition))

    point2DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint2DisplayPosition(point2DisplayPoint)
    if cellPicker.Pick(point2DisplayPoint[0], point2DisplayPoint[1], point2DisplayPoint[2], renderer):
        pickPosition = cellPicker.GetPickPosition()
        obj.GetRepresentation().SetPoint2WorldPosition(list(pickPosition))

def test(obj: vtk.vtkDistanceWidget, event: str) -> None:
    obj.GetRepresentation().SetPoint1WorldPosition([0, 0, 0])

def test2(obj: vtk.vtkDistanceWidget, event: str) -> None:
    point1DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint1DisplayPosition(point1DisplayPoint)
    print(f"point1DisplayPoint: {point1DisplayPoint}")
    point1WorldPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint1WorldPosition(point1WorldPoint)
    print(f"point1WorldPoint: {point1WorldPoint}")

    point2DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint2DisplayPosition(point2DisplayPoint)
    print(f"point2DisplayPoint: {point2DisplayPoint}")
    point2WorldPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint2WorldPosition(point2WorldPoint)
    print(f"point2WorldPoint: {point2WorldPoint}")

    print(f"3d: {math.sqrt(vtk.vtkMath.Distance2BetweenPoints(point1WorldPoint, point2WorldPoint))}")
    print(f"2d: {math.sqrt(vtk.vtkMath.Distance2BetweenPoints(point1DisplayPoint, point2DisplayPoint))}")

def distancePlacePointEventCallback(obj: vtk.vtkDistanceWidget, event: str) -> None:
    print(f"event: {event}")

    cellPicker = obj.GetInteractor().GetPicker()
    renderer = obj.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()

    point1DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint1DisplayPosition(point1DisplayPoint)

    if cellPicker.Pick(point1DisplayPoint[0], point1DisplayPoint[1], point1DisplayPoint[2], renderer):
        pickPosition = cellPicker.GetPickPosition()
        obj.GetRepresentation().SetPoint1WorldPosition(list(pickPosition))

def distanceInteractionEventCallback(obj: vtk.vtkDistanceWidget, event: str) -> None:
    print(f"event: {event}")

    cellPicker = obj.GetInteractor().GetPicker()
    renderer = obj.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()

    point1DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint1DisplayPosition(point1DisplayPoint)

    if cellPicker.Pick(point1DisplayPoint[0], point1DisplayPoint[1], point1DisplayPoint[2], renderer):
        pickPosition = cellPicker.GetPickPosition()
        obj.GetRepresentation().SetPoint1WorldPosition(list(pickPosition))

    point2DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint2DisplayPosition(point2DisplayPoint)

    if cellPicker.Pick(point2DisplayPoint[0], point2DisplayPoint[1], point2DisplayPoint[2], renderer):
        pickPosition = cellPicker.GetPickPosition()
        obj.GetRepresentation().SetPoint2WorldPosition(list(pickPosition))

def distanceEndInteractionEventCallback(obj: vtk.vtkDistanceWidget, event: str) -> None:
    print(f"event: {event}")
    cellPicker = obj.GetInteractor().GetPicker()
    renderer = obj.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()

    point1DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint1DisplayPosition(point1DisplayPoint)

    if cellPicker.Pick(point1DisplayPoint[0], point1DisplayPoint[1], point1DisplayPoint[2], renderer):
        pickPosition = cellPicker.GetPickPosition()
        obj.GetRepresentation().SetPoint1WorldPosition(list(pickPosition))

    point2DisplayPoint = [0, 0, 0]
    obj.GetRepresentation().GetPoint2DisplayPosition(point2DisplayPoint)

    if cellPicker.Pick(point2DisplayPoint[0], point2DisplayPoint[1], point2DisplayPoint[2], renderer):
        pickPosition = cellPicker.GetPickPosition()
        obj.GetRepresentation().SetPoint2WorldPosition(list(pickPosition))

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

    # scalarOpacity.AddPoint(-800.0, 0.0)
    # scalarOpacity.AddPoint(-750.0, 1.0)
    # scalarOpacity.AddPoint(-350.0, 1.0)
    # scalarOpacity.AddPoint(-300.0, 0.0)
    # scalarOpacity.AddPoint(-200.0, 0.0)
    # scalarOpacity.AddPoint(-100.0, 1.0)
    # scalarOpacity.AddPoint(1000.0, 0.0)
    # scalarOpacity.AddPoint(2750.0, 0.0)
    # scalarOpacity.AddPoint(2976.0, 1.0)
    # scalarOpacity.AddPoint(3000.0, 0.0)
    # volumeProperty.SetScalarOpacity(scalarOpacity)

    # color.AddRGBPoint(-750.0, 0.08, 0.05, 0.03)
    # color.AddRGBPoint(-350.0, 0.39, 0.25, 0.16)
    # color.AddRGBPoint(-200.0, 0.80, 0.80, 0.80)
    # color.AddRGBPoint(2750.0, 0.70, 0.70, 0.70)
    # color.AddRGBPoint(3000.0, 0.35, 0.35, 0.35)
    # volumeProperty.SetColor(color)

    rgb_points = to_rgb_points(STANDARD)
    for rgb_point in rgb_points:
        color.AddRGBPoint(rgb_point[0], rgb_point[1], rgb_point[2], rgb_point[3])
    volumeProperty.SetColor(color)

    # Bone preset
    scalarOpacity.AddPoint(80, 0)
    scalarOpacity.AddPoint(400, 0.2)
    scalarOpacity.AddPoint(1000, 1)
    volumeProperty.SetScalarOpacity(scalarOpacity)

def convertFromDisplayCoords2WorldCoords(point: Tuple, focalPoint: Tuple, renderer: vtk.vtkRenderer) -> List:
    # Select z-axis when convert the focal point from homogeneous coordinates to display coordinates
    renderer.SetWorldPoint(focalPoint[0], focalPoint[1], focalPoint[2], 1) 
    renderer.WorldToDisplay()
    displayCoord = renderer.GetDisplayPoint()
    selectionz = displayCoord[2] # the distance from the position of camera to screen

    # Convert from display coordinates to world coordinates
    renderer.SetDisplayPoint(point[0], point[1], selectionz)
    renderer.DisplayToWorld()
    worldPoint = renderer.GetWorldPoint()

    # Convert from homogeneous coordinates to world coordinates
    pickPosition = [0, 0, 0]
    for i in range(3):
        pickPosition[i] = worldPoint[i] / worldPoint[3] if worldPoint[3] else worldPoint[i]
    return pickPosition

if __name__ == "__main__":
    path1 = "D:/javaworkspace/viewer-core/server3d/data/1.2.840.113704.9.1000.16.0.20240527133901371/1.2.840.113704.9.1000.16.1.2024052713392627100020002/data"
    path2 = "D:/javaworkspace/viewer-core/server3d/data/1.3.12.2.1107.5.1.4.66827.30000023041823414870500000460/1.3.12.2.1107.5.1.4.66827.30000023041823425238300067039/data"
    distance_widget(path2)
    # angle_widget(path2)
    # main()
