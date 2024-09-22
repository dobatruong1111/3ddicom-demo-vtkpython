import vtk

def main() -> None:
    cone = vtk.vtkConeSource()
    mapper = vtk.vtkPolyDataMapper()
    actor = vtk.vtkActor()
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(500, 500)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    style = vtk.vtkInteractorStyleTrackballCamera()
    renderWindowInteractor.SetInteractorStyle(style)
    boundingBox = vtk.vtkBoundingBox()

    cone.SetHeight(3.0)
    cone.SetRadius(1.0)
    cone.SetResolution(10)

    mapper.SetInputConnection(cone.GetOutputPort())
    
    actor.SetMapper(mapper)

    boundingBox.SetBounds(actor.GetBounds())
    cubeSource = vtk.vtkCubeSource()
    cubeSource.SetBounds(boundingBox.GetBounds())
    cubeMapper = vtk.vtkPolyDataMapper()
    cubeMapper.SetInputConnection(cubeSource.GetOutputPort())
    

    boxActor = vtk.vtkActor()
    boxActor.SetMapper(cubeMapper)
    boxActor.GetProperty().SetColor(1, 0, 0)  # Set the color to red
    boxActor.GetProperty().SetWireframe(True)  # Show as wireframe

    renderer.AddActor(actor)

    renderWindow.AddRenderer(renderer)

    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindowInteractor.Initialize()
    renderWindowInteractor.Start()

if __name__ == "__main__":
    main()