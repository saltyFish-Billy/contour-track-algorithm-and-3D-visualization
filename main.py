import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
import vtk


if __name__ == '__main__':
    app = QApplication(sys.argv)
    vtk.vtkOutputWindow.SetGlobalWarningDisplay(0)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
