from PyQt5.QtWidgets import QLineEdit,QVBoxLayout,QDialog,QLabel,QPushButton
from PyQt5.QtCore import pyqtSignal


class SetContourDialog(QDialog):
    _signal = pyqtSignal(int, list)
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.flag_set = 0

        self.Contour_Label = QLabel()
        self.Contour_Label.setText("等间距等高线级别数(大于等于0, 不需要时输入0即可):")

        self.Contour_LineEdit = QLineEdit()

        self.Custom_Label = QLabel()
        self.Custom_Label.setText("自定义等高线(0-1之间, 多个数值请用逗号隔开, 不需要时输入0即可):")

        self.Custom_LineEdit = QLineEdit()

        self.setContour =  QPushButton()
        self.setContour.setText("确认")

        self.Contour_LineEdit.textEdited.connect(self.Contour_LineEditSlot)
        self.Custom_LineEdit.textEdited.connect(self.Custom_LineEditSlot)
        self.setContour.clicked.connect(self.SetSlot)

        self.Hlayout = QVBoxLayout()
        self.Hlayout.addWidget(self.Contour_Label)
        self.Hlayout.addWidget(self.Contour_LineEdit)
        self.Hlayout.addWidget(self.Custom_Label)
        self.Hlayout.addWidget(self.Custom_LineEdit)
        self.Hlayout.addWidget(self.setContour)

        self.setLayout(self.Hlayout)
        self.setWindowTitle("Set Contour")


    def Contour_LineEditSlot(self):
        if (self.Contour_LineEdit.text() != ""):
            self.contour_num = int(self.Contour_LineEdit.text())

    def Custom_LineEditSlot(self):
        if (self.Custom_LineEdit.text() != ""):
            self.text_list = self.Custom_LineEdit.text()

    def SetSlot(self):

        if (self.Contour_LineEdit.text() != "") and (self.Custom_LineEdit.text() != ""):
            number_list = self.text_list.split(',')
            self.custom_contour = []
            for i in range(len(number_list)):
               self.custom_contour.append(float(number_list[i]))


            # 合法性判断：等高线数量必须大于等于0且自定义等高线的高程值在[0, 1]区间范围内
            if  (self.contour_num >= 0) and (min(self.custom_contour) >= 0) and (max(self.custom_contour) <= 1):
                self._signal.emit(self.contour_num, self.custom_contour)
                self.close()
            else:
                pass

        else:
            pass
