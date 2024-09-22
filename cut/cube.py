from typing import Any

import vtk

from vtkmodules.vtkCommonCore import vtkCommand

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

    # Cutting
    planes = vtk.vtkPlanes()
    # planeCollection = vtk.vtkPlaneCollection()
    boxRep = vtk.vtkBoxRepresentation()
    # boxRep = MyBoxRepresentation()
    rep = vtk.vtkParallelopipedRepresentation()
    boxWidget = vtk.vtkBoxWidget2()
    parallelopipedWidget = vtk.vtkParallelopipedWidget()
    
    cone.SetHeight(3.0)
    cone.SetRadius(1.0)
    cone.SetResolution(10)

    mapper.SetInputConnection(cone.GetOutputPort())
    actor.SetMapper(mapper)
    renderer.AddActor(actor)
    renderWindow.AddRenderer(renderer)
    renderWindow.SetInteractor(renderWindowInteractor)
    # renderWindowInteractor.SetRenderWindow(renderWindow)

    # Cutting tool
    # Parallelopiped representation
    rep.GetOutlineProperty().SetColor(1, 1, 1)
    rep.GetOutlineProperty().SetOpacity(0)
    rep.GetSelectedOutlineProperty().SetOpacity(0)
    rep.GetHandleProperty().SetColor(0, 1, 0)
    rep.GetHoveredHandleProperty().SetColor(0, 1, 0)
    rep.GetSelectedHandleProperty().SetColor(0, 1, 0)
    rep.SetHandleSize(10)
    # Parallelopiped widget
    parallelopipedWidget.SetRepresentation(rep)
    parallelopipedWidget.SetInteractor(renderWindowInteractor)
    parallelopipedWidget.GetRepresentation().SetPlaceFactor(1)
    parallelopipedWidget.GetRepresentation().PlaceWidget(actor.GetBounds())
    # parallelopipedWidget.SetEnabled(True)

    # Box representation
    boxRep.GetOutlineProperty().SetColor(1, 1, 1)
    boxRep.GetHandleProperty().SetColor(0, 1, 0)
    boxRep.SetInsideOut(True)
    boxRep.SetHandleSize(10)
    boxRep.OutlineCursorWiresOff()
    # Box widget
    boxWidget.SetRepresentation(boxRep)
    boxWidget.SetInteractor(renderWindowInteractor)
    boxWidget.GetRepresentation().SetPlaceFactor(1)
    boxWidget.GetRepresentation().PlaceWidget(actor.GetBounds())
    boxWidget.RotationEnabledOff()
    boxWidget.TranslationEnabledOff()
    boxWidget.SetEnabled(True)

    # Defind callbacks
    callback = IPWCallback(planes, mapper, parallelopipedWidget)
    boxWidget.AddObserver(vtkCommand.InteractionEvent, callback)
    callback2 = IPWCallback2(planes, mapper, boxWidget)
    parallelopipedWidget.AddObserver(vtkCommand.InteractionEvent, callback2)
    
    # Start
    renderWindowInteractor.Start()

def test(path) -> None:
    reader = vtk.vtkDICOMImageReader()
    volumeMapper = vtk.vtkSmartVolumeMapper()
    volume = vtk.vtkVolume()
    volumeProperty = vtk.vtkVolumeProperty()
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(1000, 500)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    interactorStyle = vtk.vtkInteractorStyleTrackballCamera()
    renderWindowInteractor.SetInteractorStyle(interactorStyle)
    renderWindow.SetInteractor(renderWindowInteractor)

    # Cutting
    planes = vtk.vtkPlanes()
    boxRep = vtk.vtkBoxRepresentation()
    boxWidget = vtk.vtkBoxWidget2()

    reader.SetDirectoryName(path)
    reader.Update()
    imageData = reader.GetOutput()
    
    volumeMapper.SetInputData(imageData)
    volume.SetMapper(volumeMapper)
    set_volume_properties(volumeProperty)
    volume.SetProperty(volumeProperty)

    renderer.AddVolume(volume)
    renderWindow.AddRenderer(renderer)
    renderWindow.ResetCamera()

    # Box representation
    boxRep.GetOutlineProperty().SetColor(1, 1, 1)
    boxRep.GetHandleProperty().SetColor(0, 1, 0)
    boxRep.SetInsideOut(True)
    boxRep.SetHandleSize(10)
    boxRep.OutlineCursorWiresOff()
    # Box widget
    boxWidget.SetRepresentation(boxRep)
    boxWidget.SetInteractor(renderWindowInteractor)
    boxWidget.GetRepresentation().SetPlaceFactor(1)
    boxWidget.GetRepresentation().PlaceWidget(volume.GetBounds())
    boxWidget.SetEnabled(True)
    boxWidget.RotationEnabledOff()
    boxWidget.TranslationEnabledOff()

    # Handle events


    # Start
    renderWindowInteractor.Start()

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

class IPWCallback():
    def __init__(self, planes: vtk.vtkPlanes, mapper: vtk.vtkPolyDataMapper, parallelopipedWidget: vtk.vtkParallelopipedWidget) -> None:
        self.planes = planes
        self.mapper = mapper
        self.parallelopipedWidget = parallelopipedWidget

    def __call__(self, obj: vtk.vtkBoxWidget2, event: str) -> None:
        # print(f"event: {event}")
        obj.GetRepresentation().GetPlanes(self.planes)
        self.mapper.SetClippingPlanes(self.planes)

        # points = self.planes.GetPoints()
        # for i in range(points.GetNumberOfPoints()):
        #     pt = points.GetPoint(i)
        #     print(pt)
        # print(f"plane bounds: {points.GetBounds()}")

        self.parallelopipedWidget.GetRepresentation().PlaceWidget(obj.GetRepresentation().GetBounds())
        # self.parallelopipedWidget.GetRepresentation().PlaceWidget([points.GetPoint(0)[0], points.GetPoint(1)[0], points.GetPoint(2)[1], points.GetPoint(3)[1], points.GetPoint(4)[2], points.GetPoint(5)[2]])

class IPWCallback2():
    def __init__(self, planes: vtk.vtkPlanes, mappper: vtk.vtkPolyDataMapper, boxWidget: vtk.vtkBoxWidget2) -> None:
        self.planes = planes
        self.mapper = mappper
        self.boxWidget = boxWidget

    def __call__(self, obj: vtk.vtkParallelopipedWidget, event: str) -> None:
        # print(f"event: {event}")
        polyData = vtk.vtkPolyData()
        obj.GetRepresentation().GetPolyData(polyData)
        points = polyData.GetPoints()
        # print(f"numberOfPoints: {points.GetNumberOfPoints()}")
        # for i in range(points.GetNumberOfPoints()):
        #     pt = points.GetPoint(i)
        #     print(pt)

        bounds = obj.GetRepresentation().GetBounds()
        self.boxWidget.GetRepresentation().PlaceWidget([points.GetPoint(0)[0], bounds[1], points.GetPoint(0)[1], bounds[3], points.GetPoint(0)[2], bounds[5]])

        # print(f"before - bounds of box widget: {self.boxWidget.GetRepresentation().GetBounds()}. bounds of paral widget: {obj.GetRepresentation().GetBounds()}")
        # self.boxWidget.GetRepresentation().PlaceWidget(obj.GetRepresentation().GetBounds())
        # print(f"after - bounds of box widget: {self.boxWidget.GetRepresentation().GetBounds()}. bounds of paral widget: {obj.GetRepresentation().GetBounds()}")

        self.boxWidget.GetRepresentation().GetPlanes(self.planes)
        self.mapper.SetClippingPlanes(self.planes)

# Function to create a sphere at a given position
def create_sphere(center, radius=0.05, color=(1, 0, 0)):
    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetCenter(center)
    sphereSource.SetRadius(radius)
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphereSource.GetOutputPort())
    
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    
    return actor

if __name__ == '__main__':
    # test("D:/workingspace/python-base/dicom-data/220277460 Nguyen Thanh Dat")
    main()
