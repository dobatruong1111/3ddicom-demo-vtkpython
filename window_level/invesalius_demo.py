import vtk

class Volume:
    def __init__(self) -> None:
        self.isWL = False
        self.initialize()

    def initialize(self) -> None:
        self.colors = vtk.vtkNamedColors()
        self.reader = vtk.vtkDICOMImageReader()
        self.mapper = vtk.vtkOpenGLGPUVolumeRayCastMapper()
        self.volumeProperty = vtk.vtkVolumeProperty()
        self.colorTransferFunction = vtk.vtkColorTransferFunction()
        self.scalarOpacity = vtk.vtkPiecewiseFunction()
        self.gradientOpacity = vtk.vtkPiecewiseFunction()
        self.volume = vtk.vtkVolume()
        self.renderer = vtk.vtkRenderer()
        self.renderWindow = vtk.vtkRenderWindow()
        self.renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        self.interactorStyle = vtk.vtkInteractorStyle()
        # self.interactorStyle = vtk.vtkInteractorStyleTrackballCamera()
        self.renderWindowInteractor.SetInteractorStyle(self.interactorStyle)
        self.setupRenderWindow()

    def setupRenderWindow(self) -> None:
        self.renderWindow.SetSize(1000, 500)
        self.renderWindow.AddRenderer(self.renderer)
        self.renderWindow.SetInteractor(self.renderWindowInteractor)

    def setLighting(self, ambientValue: float = 0.1, diffuseValue: float = 0.9, specularValue: float = 0.2, specularPower: float = 10) -> None:
        self.volumeProperty.SetAmbient(ambientValue)
        self.volumeProperty.SetDiffuse(diffuseValue)
        self.volumeProperty.SetSpecular(specularValue)
        self.volumeProperty.SetSpecularPower(specularPower)

    def TranslateScale(self, scale, value) -> float:
        return value - scale[0]

    def colorMapping(self) -> None:
        self.colorTransferFunction.RemoveAllPoints()
        r = [0, 2, 5, 8, 10, 13, 16, 18, 21, 24, 26, 29, 32, 34, 37, 40, 42, 45, 48, 51, 53, 56, 59, 61, 64, 67, 69, 72, 75, 77, 80, 83, 85, 88, 91, 93, 96, 99, 102, 104, 107, 110, 112, 115, 118, 120, 123, 126, 128, 131, 134, 136, 139, 142, 144, 147, 150, 153, 155, 158, 161, 163, 166, 169, 171, 174, 177, 179, 182, 185, 187, 190, 193, 195, 198, 201, 204, 206, 209, 212, 214, 217, 220, 222, 225, 228, 230, 233, 236, 238, 241, 244, 246, 249, 252, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255]
        g = [0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 15, 15, 15, 15, 15, 16, 16, 16, 16, 17, 17, 17, 17, 18, 18, 18, 18, 18, 19, 19, 19, 19, 20, 20, 20, 20, 21, 21, 21, 21, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60, 63, 66, 69, 72, 75, 78, 81, 84, 87, 90, 93, 96, 99, 102, 105, 108, 111, 114, 117, 120, 123, 126, 129, 131, 134, 137, 140, 143, 146, 149, 152, 155, 158, 161, 164, 167, 170, 173, 176, 177, 179, 180, 181, 182, 183, 185, 186, 187, 188, 189, 191, 192, 193, 194, 195, 197, 198, 199, 200, 201, 203, 204, 205, 206, 207, 209, 210, 211, 212, 213, 215, 216, 217, 218, 220, 221, 222, 223, 224, 226, 227, 228, 229, 230, 232, 233, 234, 235, 236, 238, 239, 240, 241, 241, 242, 242, 242, 242, 243, 243, 243, 243, 244, 244, 244, 244, 245, 245, 245, 245, 246, 246, 246, 246, 247, 247, 247, 247, 248, 248, 248, 248, 248, 249, 249, 249, 249, 250, 250, 250, 250, 251, 251, 251, 251, 252, 252, 252, 252, 253, 253, 253, 253, 254, 254, 254, 254]
        b = [0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 14, 14, 14, 15, 15, 15, 15, 16, 16, 16, 17, 17, 17, 17, 18, 18, 18, 19, 19, 19, 20, 20, 20, 20, 21, 21, 21, 22, 22, 22, 22, 23, 23, 23, 24, 24, 24, 25, 25, 25, 25, 26, 26, 26, 27, 27, 27, 27, 27, 27, 26, 26, 26, 25, 25, 25, 24, 24, 24, 23, 23, 22, 22, 22, 21, 21, 21, 20, 20, 20, 19, 19, 19, 18, 18, 18, 17, 17, 16, 16, 16, 15, 15, 15, 14, 14, 14, 13, 13, 13, 12, 12, 11, 11, 11, 10, 10, 10, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 21, 21, 22, 22, 23, 23, 24, 24, 25, 26, 26, 27, 27, 28, 28, 29, 29, 30, 31, 31, 32, 32, 33, 33, 34, 34, 35, 36, 36, 37, 37, 38, 38, 39, 43, 47, 51, 55, 58, 62, 66, 70, 74, 78, 82, 86, 90, 94, 98, 102, 105, 109, 113, 117, 121, 125, 129, 133, 137, 141, 145, 149, 153, 156, 160, 164, 168, 172, 176, 180, 184, 188, 192, 196, 200, 204, 207, 211, 215, 219, 223, 227, 231, 235, 239, 243, 247, 251]
        colors = list(zip(r, g, b))
        ww = self.ww
        wl = self.wl
        wl = self.TranslateScale(self.scale, wl)
        init = wl - ww / 2
        inc = ww / (len(colors) - 1)
        for n, rgb in enumerate(colors):
            temp = [i / 255.0 for i in rgb]
            self.colorTransferFunction.AddRGBPoint(init + n * inc, temp[0], temp[1], temp[2])

    def scalarOpacityMapping(self) -> None:
        self.scalarOpacity.RemoveAllPoints()
        self.scalarOpacity.AddSegment(0, 0, 2**16 - 1, 0)
        ww = self.ww
        wl = self.wl
        wl = self.TranslateScale(self.scale, wl)
        l1 = wl - ww / 2
        l2 = wl + ww / 2
        self.scalarOpacity.AddPoint(l1, 0)
        self.scalarOpacity.AddPoint(l2, 1)

    def gradientOpacityMapping(self) -> None:
        self.gradientOpacity.RemoveAllPoints()
        self.gradientOpacity.AddPoint(0, 1)
        self.gradientOpacity.AddPoint(255, 1)

    def leftButtonPressEvent(self, obj, event) -> None:
        self.isWL = True

    def mouseMoveEvent(self, obj, event) -> None:
        if self.isWL:
            lastEventPosition = obj.GetLastEventPosition()
            eventPosition = obj.GetEventPosition()
            wl = eventPosition[0] - lastEventPosition[0]
            ww = eventPosition[1] - lastEventPosition[1]
            self.wl += wl
            self.ww += ww
            self.colorMapping()
            self.scalarOpacityMapping()
            self.renderWindow.Render()

    def leftButtonReleaseEvent(self, obj, event) -> None:
        if self.isWL:
            self.isWL = False
    
    def show(self, path: str) -> None:
        self.reader.SetDirectoryName(path)
        self.reader.Update()
        self.imageData = self.reader.GetOutput()
        self.scale = self.imageData.GetScalarRange()

        # Invesalius preset
        cast = vtk.vtkImageShiftScale()
        cast.SetInputData(self.imageData)
        cast.SetShift(abs(self.scale[0]))
        cast.SetOutputScalarTypeToUnsignedShort()
        cast.Update()
        imageData2 = cast.GetOutput()

        self.mapper.UseJitteringOn()
        self.mapper.SetBlendModeToComposite()
        self.mapper.SetInputData(imageData2)

        self.volumeProperty.SetInterpolationTypeToLinear()
        self.volumeProperty.SetColor(self.colorTransferFunction)
        self.volumeProperty.SetScalarOpacity(self.scalarOpacity)
        # self.volumeProperty.SetGradientOpacity(self.gradientOpacity)

        self.ww = 243.73239135742188
        self.wl = 199.64259338378906

        self.colorMapping()
        self.scalarOpacityMapping()
        # self.gradientOpacityMapping()

        self.volumeProperty.ShadeOn()
        # self.setLighting()
        self.setLighting(0.15, 0.9, 0.3, 15)

        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volumeProperty)

        self.renderer.AddVolume(self.volume)
        self.renderer.ResetCamera()
        center = self.volume.GetCenter()
        camera = self.renderer.GetActiveCamera()
        distance = camera.GetDistance()
        camera.SetViewUp(0, 0, -1)
        camera.SetPosition(center[0], center[1] + distance, center[2])

        self.renderWindowInteractor.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.leftButtonPressEvent)
        self.renderWindowInteractor.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.mouseMoveEvent)
        self.renderWindowInteractor.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.leftButtonReleaseEvent)
        
        self.renderWindowInteractor.Start()

if __name__ == "__main__":
    volume = Volume()
    path = "D:/workingspace/dicom/220277460 Nguyen Thanh Dat"
    path2 = "D:/javaworkspace/viewer-core/server3d/data/1.3.12.2.1107.5.1.4.66827.30000023041823414870500000460/1.3.12.2.1107.5.1.4.66827.30000023041823425238300067039/data"
    path3 = "D:/workingspace/2.25.48614890022365423197101599370205019791"
    volume.show(path)
