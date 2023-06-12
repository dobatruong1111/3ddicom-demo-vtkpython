### Thuật toán mask volume với ảnh Dicom

```
Bước 1:
Vẽ đường viền 2D trên hệ tọa độ màn hình (screen/display). Lưu lại các điểm.

Bước 2:
Tìm khoảng cắt (clipping range) nhỏ hơn khoảng cắt mặc định lấy từ đối tượng camera.
Mục đính: tối ưu thời gian xử lý sau này.

Bước 3:
Duyệt qua các điểm sau đó chuyển đổi điểm sang hệ tọa độ world. Tìm điểm nằm trên mặt phẳng gần và xa.

Bước 4:
Nối điểm trên mặt phẳng gần với điểm nằm trên mặt phẳng xa sau đó nối với điểm tiếp theo.
Mục đích là tạo ra một đa giác (polydata).

Bước 5:
Tính toán model matrix dựa trên các giá trị spacing, origin và direction matrix của đối tượng 3D, sau đó tính nghịch đảo ma trận. Xét transform matrix vào polydata ở bước 4
Mục đích: đồng nhất hệ tọa độ

Bước 6:
Chuyển đổi polydata ở bước 4 về image stencil.
Image stencil là một đối tượng dữ liệu dạng ma trận nhị phân có cùng kích thước và phân giải với một hình ảnh, image stencil thực hiện các phép biến đổi hoặc lọc ảnh trên phạm vi chỉ định bởi vtkPolyData.

Bước 7:
Chuyển đổi image stencil về image data.
Đặt giá trị điểm ảnh nằm bên trong polydata là 1, bên ngoài là 0 (cắt bên trong), đặt ngược lại (cắt bên ngoài). Set lại scalar type, origin, spacing và direction matrix giống với ảnh ban đầu.
Lưu lại vào một đối tượng vtkImageData (modifierLabelmap).
Mục đích: có thể sử dụng để cắt nhiều lần

Bước 8:
Thực hiện phân ngưỡng với input là modifierLabelmap, với ngưỡng = 0
Nếu giá trị <= 0, set lại = 0
Nếu giá trị > 0, set lại = 1
Tiếp theo, set vùng giá trị = 1 bởi -1000HU (vì không thuộc phạm vi được ánh xạ opacity). Tạo đối tượng vtkImageData mới để lưu trữ, sau đó set vào đối tượng Mapper.
```
