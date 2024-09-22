import vtk, math

from typing import List

class WindowLevelInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self) -> None:
        self.isWL = False

        self.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.leftButtonPressEvent)
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.mouseMoveEvent)
        self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.leftButtonReleaseEvent)

    def leftButtonPressEvent(self, obj, event) -> None:
        # print(event)
        self.OnLeftButtonDown()

    def mouseMoveEvent(self, obj, event) -> None:
        # print(event)
        self.OnMouseMove()

    def leftButtonReleaseEvent(self, obj, event) -> None:
        # print(event)
        self.OnLeftButtonUp()

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

    def colorMapping(self) -> None:
        self.colorTransferFunction.RemoveAllPoints()
        # self.colorTransferFunction.AddRGBPoint(-3024, 0, 0, 0)
        # self.colorTransferFunction.AddRGBPoint(143.556, 0.615686, 0.356863, 0.184314)
        # self.colorTransferFunction.AddRGBPoint(166.222, 0.882353, 0.603922, 0.290196)
        # self.colorTransferFunction.AddRGBPoint(214.389, 1, 1, 1)
        # self.colorTransferFunction.AddRGBPoint(419.736, 1, 0.937033, 0.954531)
        # self.colorTransferFunction.AddRGBPoint(3071, 0.827451, 0.658824, 1)
        for key in self.colorPoints.keys():
            self.colorTransferFunction.AddRGBPoint(self.colorPoints[key]["x"], *self.colorPoints[key]["rgb"])

    def scalarOpacityMapping(self) -> None:
        self.scalarOpacity.RemoveAllPoints()
        # self.scalarOpacity.AddPoint(-3024, 0)
        # self.scalarOpacity.AddPoint(143.556, 0)
        # self.scalarOpacity.AddPoint(166.222, 0.686275)
        # self.scalarOpacity.AddPoint(214.389, 0.696078)
        # self.scalarOpacity.AddPoint(419.736, 0.833333)
        # self.scalarOpacity.AddPoint(3071, 0.803922)
        for key in self.scalarOpacityPoints.keys():
            self.scalarOpacity.AddPoint(self.scalarOpacityPoints[key]["x"], self.scalarOpacityPoints[key]["opacity"])

    def gradientOpacityMapping(self) -> None:
        self.gradientOpacity.RemoveAllPoints()
        self.gradientOpacity.AddPoint(0, 1)
        self.gradientOpacity.AddPoint(255, 1)

    def leftButtonPressEvent(self, obj, event) -> None:
        self.isWL = True
        self.point1 = obj.GetEventPosition()
        print(obj.GetLastEventPosition())
        print(obj.GetEventPosition())

    def mouseMoveEvent(self, obj, event) -> None:
        if self.isWL:
            point1 = obj.GetLastEventPosition()
            point2 = obj.GetEventPosition()
            distance = math.sqrt(vtk.vtkMath.Distance2BetweenPoints([point1[0], point1[1], 0], [point2[0], point2[1], 0]))
            print(obj.GetLastEventPosition())
            print(obj.GetEventPosition())
            # print(f"distance: {distance}")

            if point2[0] - point1[0] < 0 or point2[1] - point1[1] < 0:
                for key in self.colorPoints.keys():
                    self.colorPoints[key]["x"] -= distance
                self.colorMapping()
                for key in self.scalarOpacityPoints.keys():
                    self.scalarOpacityPoints[key]["x"] -= distance
                self.scalarOpacityMapping()
            else:
                for key in self.colorPoints.keys():
                    self.colorPoints[key]["x"] += distance
                self.colorMapping()
                for key in self.scalarOpacityPoints.keys():
                    self.scalarOpacityPoints[key]["x"] += distance
                self.scalarOpacityMapping()
            self.renderWindow.Render()

    def leftButtonReleaseEvent(self, obj, event) -> None:
        if self.isWL:
            self.isWL = False
    
    def show(self, path: str) -> None:
        self.reader.SetDirectoryName(path)
        self.reader.Update()
        imageData = self.reader.GetOutput()

        self.mapper.UseJitteringOn()
        self.mapper.SetBlendModeToComposite()
        self.mapper.SetInputData(imageData)

        self.volumeProperty.SetInterpolationTypeToLinear()
        self.volumeProperty.SetColor(self.colorTransferFunction)
        self.volumeProperty.SetScalarOpacity(self.scalarOpacity)
        self.volumeProperty.SetGradientOpacity(self.gradientOpacity)
        self.colorPoints = {
            0: {
                "x": -3024,
                "rgb": [0, 0, 0]
            },
            1: {
                "x": 143.556,
                "rgb": [0.615686, 0.356863, 0.184314]
            },
            2: {
                "x": 166.222,
                "rgb": [0.882353, 0.603922, 0.290196]
            },
            3: {
                "x": 214.389,
                "rgb": [1, 1, 1]
            },
            4: {
                "x": 419.736,
                "rgb": [1, 0.937033, 0.954531]
            },
            5: {
                "x": 3071,
                "rgb": [0.827451, 0.658824, 1]
            }
        }
        self.scalarOpacityPoints = {
            0: {
                "x": -3024,
                "opacity": 0
            },
            1: {
                "x": 143.556,
                "opacity": 0
            },
            2: {
                "x": 166.222,
                "opacity": 0.686275
            },
            3: {
                "x": 214.389,
                "opacity": 0.696078
            },
            4: {
                "x": 419.736,
                "opacity": 0.833333
            },
            5: {
                "x": 3071,
                "opacity": 0.803922
            }
        }
        self.colorMapping()
        self.scalarOpacityMapping()
        self.gradientOpacityMapping()

        self.volumeProperty.ShadeOn()
        self.setLighting()

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
