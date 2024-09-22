import vtk
import math
import numpy as np

def main():
    colors = vtk.vtkNamedColors()
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(20)
    sphere.Update()
    bounds = sphere.GetOutput().GetBounds()
    # print(bounds)
    # print(sphere.GetOutput()) # vtkPolyData

    polyData2ImageStencil = vtk.vtkPolyDataToImageStencil()
    polyData2ImageStencil.SetInputData(sphere.GetOutput())
    polyData2ImageStencil.SetOutputOrigin(0, 0, 0)
    # polyData2ImageStencil.SetOutputSpacing(1, 1, 1)
    polyData2ImageStencil.SetOutputSpacing(2, 2, 2)
    polyData2ImageStencil.SetOutputWholeExtent(
        math.floor(bounds[0] - 1), math.ceil(bounds[1] + 1),
        math.floor(bounds[2] - 1), math.ceil(bounds[3] + 1),
        math.floor(bounds[4] - 1), math.ceil(bounds[5] + 1)
    )
    polyData2ImageStencil.Update()
    # print(polyData2ImageStencil.GetOutput()) # vtkImageStencilData

    stencilToImage = vtk.vtkImageStencilToImage()
    stencilToImage.SetInputData(polyData2ImageStencil.GetOutput())
    stencilToImage.SetInsideValue(255)
    stencilToImage.SetOutsideValue(0)
    stencilToImage.SetOutputScalarType(vtk.VTK_INT)
    stencilToImage.Update()
    # print(stencilToImage.GetOutput())

    # imageData = stencilToImage.GetOutput()
    # imageData = vtk.vtkImageData()
    # extent = stencilToImage.GetOutput().GetExtent()
    # imageData.SetExtent(extent)
    # print(imageData)
    # i, j, k = extent[0] + 10, extent[2], 0
    # scalarValue = 255
    # for k in range(extent[4], extent[5] + 1):
    # for j in range(extent[2], extent[3] + 1):
    #     for i in range(extent[0], extent[1] + 1):
    #         imageData.SetScalarComponentFromFloat(i, j, 0, 0, scalarValue)
    #         print(imageData.GetScalarComponentAsFloat(i, j, 0, 0))
    # print(imageData.GetScalarComponentAsFloat(extent[0] + 10, extent[2], extent[4], 0))

    sphereMapper = vtk.vtkPolyDataMapper()
    sphereMapper.SetInputData(sphere.GetOutput())
    # imageMapper = vtk.vtkDataSetMapper()
    # imageMapper.SetInputData(stencilToImage.GetOutput())
    imageMapper = vtk.vtkImageSliceMapper()
    imageMapper.SetInputData(stencilToImage.GetOutput())

    sphereActor = vtk.vtkActor()
    sphereActor.SetMapper(sphereMapper)
    sphereActor.GetProperty().SetColor(colors.GetColor3d("Tomato"))
    # imageActor = vtk.vtkActor()
    # imageActor.SetMapper(imageMapper)
    imageActor = vtk.vtkImageSlice()
    imageActor.SetMapper(imageMapper)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(colors.GetColor3d("Blue"))
    renderer.AddActor(sphereActor)
    renderer.AddActor(imageActor)

    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)

    renWinIn = vtk.vtkRenderWindowInteractor()
    style = vtk.vtkInteractorStyleTrackballCamera()
    renWinIn.SetInteractorStyle(style)
    renWinIn.SetRenderWindow(renderWindow)

    renWinIn.Start()

if __name__ == "__main__":
    main()