import vtk

def main() -> None:
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(1000, 500)
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    style = vtk.vtkInteractorStyleTrackballCamera()
    renderWindowInteractor.SetInteractorStyle(style)
    renderWindow.SetInteractor(renderWindowInteractor)

    transform = vtk.vtkTransform()

    cone = vtk.vtkConeSource()
    cone.SetHeight(3.0)
    cone.SetRadius(1.0)
    cone.SetResolution(10)
    passThrough = vtk.vtkPassThrough()
    passThrough.SetInputConnection(cone.GetOutputPort())
    transformPolyDataFilter = vtk.vtkTransformPolyDataFilter()
    transformPolyDataFilter.SetTransform(transform)
    transformPolyDataFilter.SetInputConnection(passThrough.GetOutputPort())
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(transformPolyDataFilter.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    outline = vtk.vtkOutlineFilter()
    outline.SetInputConnection(passThrough.GetOutputPort())
    outlineTransformFilter = vtk.vtkTransformPolyDataFilter()
    outlineTransformFilter.SetTransform(transform)
    outlineTransformFilter.SetInputConnection(outline.GetOutputPort())
    outlineMapper = vtk.vtkPolyDataMapper()
    outlineMapper.SetInputConnection(outlineTransformFilter.GetOutputPort())
    outlineActor = vtk.vtkActor()
    outlineActor.SetMapper(outlineMapper)

    renderer.AddActor(actor)
    renderer.AddActor(outlineActor)
    
    # Start
    renderWindowInteractor.Start()

if __name__ == "__main__":
    main()
