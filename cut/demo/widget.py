import vtk

from vtkmodules.vtkCommonCore import vtkCommand

def main() -> None:
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(1000, 500)
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    style = vtk.vtkInteractorStyleTrackballCamera()
    # style = CustomInteractorStyle()
    renderWindowInteractor.SetInteractorStyle(style)
    renderWindow.SetInteractor(renderWindowInteractor)

    planes = vtk.vtkPlanes()
    
    cone = vtk.vtkConeSource()
    cone.SetHeight(3.0)
    cone.SetRadius(1.0)
    cone.SetResolution(10)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cone.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    center = actor.GetCenter()
    (xMin, xMax, yMin, yMax, zMin, zMax) = actor.GetBounds()

    renderer.AddActor(actor)
    # Camera
    camera = renderer.GetActiveCamera()
    camera.SetPosition(center[0], center[1], 7*zMax)
    distance = camera.GetDistance()
    # print(f"distance: {distance}")

    # Box representation
    boxRep = vtk.vtkBoxRepresentation()
    boxRep.GetHandleProperty().SetColor(0, 1, 0)
    boxRep.SetHandleSize(10)
    boxRep.SetInsideOut(True)
    boxRep.OutlineCursorWiresOff()
    # boxRep.HandlesOff()
    # Box widget
    boxWidget = vtk.vtkBoxWidget2()
    boxWidget.SetInteractor(renderWindowInteractor)
    boxWidget.SetRepresentation(boxRep)
    boxWidget.GetRepresentation().SetPlaceFactor(1)
    boxWidget.GetRepresentation().PlaceWidget(actor.GetBounds())
    boxWidget.RotationEnabledOff()
    boxWidget.TranslationEnabledOff()
    boxWidget.SetEnabled(True)

    # Sphere widget
    sphereWidget1 = vtk.vtkSphereWidget()
    sphereWidget1.SetInteractor(renderWindowInteractor)
    sphereWidget1.SetRepresentationToSurface()
    sphereWidget1.GetSphereProperty().SetColor(0, 1, 0)
    sphereWidget1.SetRadius(0.07)
    sphereWidget1.SetCenter(xMin, yMax, zMin)
    sphereWidget1.SetEnabled(True)
    sphereWidget1.SetScale(False)

    sphereWidget2 = vtk.vtkSphereWidget()
    sphereWidget2.SetInteractor(renderWindowInteractor)
    sphereWidget2.SetRepresentationToSurface()
    sphereWidget2.GetSphereProperty().SetColor(0, 1, 0)
    sphereWidget2.SetRadius(0.07)
    sphereWidget2.SetCenter(xMax, yMax, zMin)
    sphereWidget2.SetEnabled(True)
    sphereWidget2.SetScale(False)

    sphereWidget3 = vtk.vtkSphereWidget()
    sphereWidget3.SetInteractor(renderWindowInteractor)
    sphereWidget3.SetRepresentationToSurface()
    sphereWidget3.GetSphereProperty().SetColor(0, 1, 0)
    sphereWidget3.SetRadius(0.07)
    sphereWidget3.SetCenter(xMax, yMax, zMax)
    sphereWidget3.SetEnabled(True)
    sphereWidget3.SetScale(False)

    sphereWidget4 = vtk.vtkSphereWidget()
    sphereWidget4.SetInteractor(renderWindowInteractor)
    sphereWidget4.SetRepresentationToSurface()
    sphereWidget4.GetSphereProperty().SetColor(0, 1, 0)
    sphereWidget4.SetRadius(0.07)
    sphereWidget4.SetCenter(xMin, yMax, zMax)
    sphereWidget4.SetEnabled(True)
    sphereWidget4.SetScale(False)

    sphereWidget5 = vtk.vtkSphereWidget()
    sphereWidget5.SetInteractor(renderWindowInteractor)
    sphereWidget5.SetRepresentationToSurface()
    sphereWidget5.GetSphereProperty().SetColor(0, 1, 0)
    sphereWidget5.SetRadius(0.07)
    sphereWidget5.SetCenter(xMin, yMin, zMin)
    sphereWidget5.SetEnabled(True)
    sphereWidget5.SetScale(False)

    sphereWidget6 = vtk.vtkSphereWidget()
    sphereWidget6.SetInteractor(renderWindowInteractor)
    sphereWidget6.SetRepresentationToSurface()
    sphereWidget6.GetSphereProperty().SetColor(0, 1, 0)
    sphereWidget6.SetRadius(0.07)
    sphereWidget6.SetCenter(xMax, yMin, zMin)
    sphereWidget6.SetEnabled(True)
    sphereWidget6.SetScale(False)

    sphereWidget7 = vtk.vtkSphereWidget()
    sphereWidget7.SetInteractor(renderWindowInteractor)
    sphereWidget7.SetRepresentationToSurface()
    sphereWidget7.GetSphereProperty().SetColor(0, 1, 0)
    sphereWidget7.SetRadius(0.07)
    sphereWidget7.SetCenter(xMax, yMin, zMax)
    sphereWidget7.SetEnabled(True)
    sphereWidget7.SetScale(False)

    sphereWidget8 = vtk.vtkSphereWidget()
    sphereWidget8.SetInteractor(renderWindowInteractor)
    sphereWidget8.SetRepresentationToSurface()
    sphereWidget8.GetSphereProperty().SetColor(0, 1, 0)
    sphereWidget8.SetRadius(0.07)
    sphereWidget8.SetCenter(xMin, yMin, zMax)
    sphereWidget8.SetEnabled(True)
    sphereWidget8.SetScale(False)

    def boxWidgetInteractionEventHandler(boxWidget: vtk.vtkBoxWidget2, event: str) -> None:
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget1.SetCenter(bounds[0], bounds[3], bounds[4])
        sphereWidget2.SetCenter(bounds[1], bounds[3], bounds[4])
        sphereWidget3.SetCenter(bounds[1], bounds[3], bounds[5])
        sphereWidget4.SetCenter(bounds[0], bounds[3], bounds[5])
        sphereWidget5.SetCenter(bounds[0], bounds[2], bounds[4])
        sphereWidget6.SetCenter(bounds[1], bounds[2], bounds[4])
        sphereWidget7.SetCenter(bounds[1], bounds[2], bounds[5])
        sphereWidget8.SetCenter(bounds[0], bounds[2], bounds[5])

    def sphereWidget1InteractionEventHandler(sphereWidget: vtk.vtkSphereWidget, event: str) -> None:
        newCenter = sphereWidget.GetCenter()
        bounds = boxWidget.GetRepresentation().GetBounds()

        boxWidget.GetRepresentation().PlaceWidget([newCenter[0], bounds[1], bounds[2], newCenter[1], newCenter[2], bounds[5]])
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget2.SetCenter(bounds[1], bounds[3], bounds[4])
        sphereWidget3.SetCenter(bounds[1], bounds[3], bounds[5])
        sphereWidget4.SetCenter(bounds[0], bounds[3], bounds[5])
        sphereWidget5.SetCenter(bounds[0], bounds[2], bounds[4])
        sphereWidget6.SetCenter(bounds[1], bounds[2], bounds[4])
        sphereWidget7.SetCenter(bounds[1], bounds[2], bounds[5])
        sphereWidget8.SetCenter(bounds[0], bounds[2], bounds[5])

    def sphereWidget2InteractionEventHandler(sphereWidget: vtk.vtkSphereWidget, event: str) -> None:
        newCenter = sphereWidget.GetCenter()
        bounds = boxWidget.GetRepresentation().GetBounds()

        boxWidget.GetRepresentation().PlaceWidget([bounds[0], newCenter[0], bounds[2], newCenter[1], newCenter[2], bounds[5]])
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget1.SetCenter(bounds[0], bounds[3], bounds[4])
        sphereWidget3.SetCenter(bounds[1], bounds[3], bounds[5])
        sphereWidget4.SetCenter(bounds[0], bounds[3], bounds[5])
        sphereWidget5.SetCenter(bounds[0], bounds[2], bounds[4])
        sphereWidget6.SetCenter(bounds[1], bounds[2], bounds[4])
        sphereWidget7.SetCenter(bounds[1], bounds[2], bounds[5])
        sphereWidget8.SetCenter(bounds[0], bounds[2], bounds[5])

    def sphereWidget3InteractionEventHandler(sphereWidget: vtk.vtkSphereWidget, event: str) -> None:
        newCenter = sphereWidget.GetCenter()
        bounds = boxWidget.GetRepresentation().GetBounds()

        boxWidget.GetRepresentation().PlaceWidget([bounds[0], newCenter[0], bounds[2], newCenter[1], bounds[4], newCenter[2]])
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget1.SetCenter(bounds[0], bounds[3], bounds[4])
        sphereWidget2.SetCenter(bounds[1], bounds[3], bounds[4])
        sphereWidget4.SetCenter(bounds[0], bounds[3], bounds[5])
        sphereWidget5.SetCenter(bounds[0], bounds[2], bounds[4])
        sphereWidget6.SetCenter(bounds[1], bounds[2], bounds[4])
        sphereWidget7.SetCenter(bounds[1], bounds[2], bounds[5])
        sphereWidget8.SetCenter(bounds[0], bounds[2], bounds[5])
    
    def sphereWidget4InteractionEventHandler(sphereWidget: vtk.vtkSphereWidget, event: str) -> None:
        newCenter = sphereWidget.GetCenter()
        bounds = boxWidget.GetRepresentation().GetBounds()

        boxWidget.GetRepresentation().PlaceWidget([newCenter[0], bounds[1], bounds[2], newCenter[1], bounds[4], newCenter[2]])
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget1.SetCenter(bounds[0], bounds[3], bounds[4])
        sphereWidget2.SetCenter(bounds[1], bounds[3], bounds[4])
        sphereWidget3.SetCenter(bounds[1], bounds[3], bounds[5])
        sphereWidget5.SetCenter(bounds[0], bounds[2], bounds[4])
        sphereWidget6.SetCenter(bounds[1], bounds[2], bounds[4])
        sphereWidget7.SetCenter(bounds[1], bounds[2], bounds[5])
        sphereWidget8.SetCenter(bounds[0], bounds[2], bounds[5])

    def sphereWidget5InteractionEventHandler(sphereWidget: vtk.vtkSphereWidget, event: str) -> None:
        newCenter = sphereWidget.GetCenter()
        bounds = boxWidget.GetRepresentation().GetBounds()

        boxWidget.GetRepresentation().PlaceWidget([newCenter[0], bounds[1], newCenter[1], bounds[3], newCenter[2], bounds[5]])
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget1.SetCenter(bounds[0], bounds[3], bounds[4])
        sphereWidget2.SetCenter(bounds[1], bounds[3], bounds[4])
        sphereWidget3.SetCenter(bounds[1], bounds[3], bounds[5])
        sphereWidget4.SetCenter(bounds[0], bounds[3], bounds[5])
        sphereWidget6.SetCenter(bounds[1], bounds[2], bounds[4])
        sphereWidget7.SetCenter(bounds[1], bounds[2], bounds[5])
        sphereWidget8.SetCenter(bounds[0], bounds[2], bounds[5])

    def sphereWidget6InteractionEventHandler(sphereWidget: vtk.vtkSphereWidget, event: str) -> None:
        newCenter = sphereWidget.GetCenter()
        bounds = boxWidget.GetRepresentation().GetBounds()

        boxWidget.GetRepresentation().PlaceWidget([bounds[0], newCenter[0], newCenter[1], bounds[3], newCenter[2], bounds[5]])
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget1.SetCenter(bounds[0], bounds[3], bounds[4])
        sphereWidget2.SetCenter(bounds[1], bounds[3], bounds[4])
        sphereWidget3.SetCenter(bounds[1], bounds[3], bounds[5])
        sphereWidget4.SetCenter(bounds[0], bounds[3], bounds[5])
        sphereWidget5.SetCenter(bounds[0], bounds[2], bounds[4])
        sphereWidget7.SetCenter(bounds[1], bounds[2], bounds[5])
        sphereWidget8.SetCenter(bounds[0], bounds[2], bounds[5])

    def sphereWidget7InteractionEventHandler(sphereWidget: vtk.vtkSphereWidget, event: str) -> None:
        newCenter = sphereWidget.GetCenter()
        bounds = boxWidget.GetRepresentation().GetBounds()

        boxWidget.GetRepresentation().PlaceWidget([bounds[0], newCenter[0], newCenter[1], bounds[3], bounds[4], newCenter[2]])
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget1.SetCenter(bounds[0], bounds[3], bounds[4])
        sphereWidget2.SetCenter(bounds[1], bounds[3], bounds[4])
        sphereWidget3.SetCenter(bounds[1], bounds[3], bounds[5])
        sphereWidget4.SetCenter(bounds[0], bounds[3], bounds[5])
        sphereWidget5.SetCenter(bounds[0], bounds[2], bounds[4])
        sphereWidget6.SetCenter(bounds[1], bounds[2], bounds[4])
        sphereWidget8.SetCenter(bounds[0], bounds[2], bounds[5])
    
    def sphereWidget8InteractionEventHandler(sphereWidget: vtk.vtkSphereWidget, event: str) -> None:
        newCenter = sphereWidget.GetCenter()
        bounds = boxWidget.GetRepresentation().GetBounds()

        boxWidget.GetRepresentation().PlaceWidget([newCenter[0], bounds[1], newCenter[1], bounds[3], bounds[4], newCenter[2]])
        boxWidget.GetRepresentation().GetPlanes(planes)
        mapper.SetClippingPlanes(planes)

        bounds = boxWidget.GetRepresentation().GetBounds()
        sphereWidget1.SetCenter(bounds[0], bounds[3], bounds[4])
        sphereWidget2.SetCenter(bounds[1], bounds[3], bounds[4])
        sphereWidget3.SetCenter(bounds[1], bounds[3], bounds[5])
        sphereWidget4.SetCenter(bounds[0], bounds[3], bounds[5])
        sphereWidget5.SetCenter(bounds[0], bounds[2], bounds[4])
        sphereWidget6.SetCenter(bounds[1], bounds[2], bounds[4])
        sphereWidget7.SetCenter(bounds[1], bounds[2], bounds[5])

   
        print(f"event: {event}")

        deltaDistance = renderer.GetActiveCamera().GetDistance()
        sphereWidget1.SetRadius(0.07 * (deltaDistance / distance))
        sphereWidget2.SetRadius(0.07 * (deltaDistance / distance))
        sphereWidget3.SetRadius(0.07 * (deltaDistance / distance))
        sphereWidget4.SetRadius(0.07 * (deltaDistance / distance))
        sphereWidget5.SetRadius(0.07 * (deltaDistance / distance))
        sphereWidget6.SetRadius(0.07 * (deltaDistance / distance))
        sphereWidget7.SetRadius(0.07 * (deltaDistance / distance))
        sphereWidget8.SetRadius(0.07 * (deltaDistance / distance))

        interactorStyle.OnMouseWheelBackward()

    # Defind callbacks
    boxWidget.AddObserver(vtkCommand.InteractionEvent, boxWidgetInteractionEventHandler)
    sphereWidget1.AddObserver(vtkCommand.InteractionEvent, sphereWidget1InteractionEventHandler)
    sphereWidget2.AddObserver(vtkCommand.InteractionEvent, sphereWidget2InteractionEventHandler)
    sphereWidget3.AddObserver(vtkCommand.InteractionEvent, sphereWidget3InteractionEventHandler)
    sphereWidget4.AddObserver(vtkCommand.InteractionEvent, sphereWidget4InteractionEventHandler)
    sphereWidget5.AddObserver(vtkCommand.InteractionEvent, sphereWidget5InteractionEventHandler)
    sphereWidget6.AddObserver(vtkCommand.InteractionEvent, sphereWidget6InteractionEventHandler)
    sphereWidget7.AddObserver(vtkCommand.InteractionEvent, sphereWidget7InteractionEventHandler)
    sphereWidget8.AddObserver(vtkCommand.InteractionEvent, sphereWidget8InteractionEventHandler)

    # Start
    renderWindowInteractor.Start()

if __name__ == "__main__":
    main()
