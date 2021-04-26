from PyQt5.QtCore import QDir, Qt, QUrl, pyqtSignal, QPoint, QRect, QObject
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QVideoFrame, QAbstractVideoSurface, QAbstractVideoBuffer, QVideoSurfaceFormat
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
        QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget)
from PyQt5.QtWidgets import QMainWindow,QWidget, QPushButton, QAction
from PyQt5.QtGui import QIcon, QPainter, QImage
import sys
import os
import os.path as osp

class VideoFrameGrabber(QAbstractVideoSurface):
    frame_available = pyqtSignal(QImage)            

    def __init__(self, widget: QWidget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self.current_frame = None
        self.image_format = QImage.Format_Invalid
        self.target_rect = None
        self.source_rect = None
        self.image_size = None

    def supportedPixelFormats(self, type):
        print("supportedPixelFormats() called")
        print("supportedPixelFormats() finished")
        return [QVideoFrame.Format_ARGB32, QVideoFrame.Format_ARGB32_Premultiplied,
                QVideoFrame.Format_RGB32, QVideoFrame.Format_RGB24, QVideoFrame.Format_RGB565,
                QVideoFrame.Format_RGB555, QVideoFrame.Format_ARGB8565_Premultiplied,
                QVideoFrame.Format_BGRA32, QVideoFrame.Format_BGRA32_Premultiplied, QVideoFrame.Format_BGR32,
                QVideoFrame.Format_BGR24, QVideoFrame.Format_BGR565, QVideoFrame.Format_BGR555,
                QVideoFrame.Format_BGRA5658_Premultiplied, QVideoFrame.Format_AYUV444,
                QVideoFrame.Format_AYUV444_Premultiplied, QVideoFrame.Format_YUV444,
                QVideoFrame.Format_YUV420P, QVideoFrame.Format_YV12, QVideoFrame.Format_UYVY,
                QVideoFrame.Format_YUYV, QVideoFrame.Format_NV12, QVideoFrame.Format_NV21,
                QVideoFrame.Format_IMC1, QVideoFrame.Format_IMC2, QVideoFrame.Format_IMC3,
                QVideoFrame.Format_IMC4, QVideoFrame.Format_Y8, QVideoFrame.Format_Y16,
                QVideoFrame.Format_Jpeg, QVideoFrame.Format_CameraRaw, QVideoFrame.Format_AdobeDng]

    def isFormatSupported(self, format):
        print("isFormatSupported() called")

        image_format = QVideoFrame.imageFormatFromPixelFormat(format.pixelFormat())
        size = format.frameSize()

        print("isFormatSupported() finished")
        return image_format != QVideoFrame.Format_Invalid and not size.isEmpty() and \
            format.handleType() == QAbstractVideoBuffer.NoHandle

    def start(self, format):
        print("start() called")

        image_format = QVideoFrame.imageFormatFromPixelFormat(format.pixelFormat())
        size = format.frameSize()

        if image_format != QImage.Format_Invalid and not size.isEmpty():
            self.image_format = image_format
            self.image_size = size
            self.source_rect = format.viewport()

            super().start(format) 
            print("start() finished")
            return True
        else:
            print("start() finished")
            return False

    def stop(self):
        print("stop() called")

        self.current_frame = QVideoFrame()
        self.target_rect = QRect()

        super().stop()                                

        print("stop() finished")

    def present(self, frame: QVideoFrame):
        print("present called")

        if frame.isValid():

            clone_frame = QVideoFrame(frame)

            clone_frame.map(QAbstractVideoBuffer.ReadOnly)
            image = QImage(clone_frame.bits(), frame.width(), frame.height(), frame.bytesPerLine(), \
                QVideoFrame.imageFormatFromPixelFormat(frame.pixelFormat()))
            clone_frame.unmap()

            self.frame_available.emit(image)

        if self.surfaceFormat().pixelFormat() != frame.pixelFormat() or \
            self.surfaceFormat().frameSize() != frame.size():
            self.setError(QAbstractVideoSurface.IncorrectFormatError)
            self.stop()

            print("present finished: Return False")
            return False
        else:
            self.current_frame = frame

            print("present finished: Return True")
            return True
            
class VideoWindow(QMainWindow):

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setWindowTitle("Media-Player")
        self.resize(1900, 1000)
        self.frame_counter = 0
        self.volume = 0
        self.setStyleSheet("background-color: rgb(0, 0, 0);\n"
"color: rgb(255, 170, 0);\n"
"")        
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.videoWidget = QVideoWidget()

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setStyleSheet("background-color: rgb(85, 0, 0); color: rgb(255, 0, 0)")
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                QSizePolicy.Maximum)

        # Create new action
        openAction = QAction(QIcon('open.png'), '&Open', self)        
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.openFile)

        # Create exit action
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)
        
        saveAction = QAction(QIcon('save.png'), '&Save', self)        
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Take Screenshot')
        saveAction.triggered.connect(self.saveCall)

        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        screenshotMenu = menuBar.addMenu('&Screenshot')
        #fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)
        screenshotMenu.addAction(saveAction)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)

        layout = QVBoxLayout()
        layout.addWidget(self.videoWidget)
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Movie",
                QDir.homePath())

        if fileName != '':
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)

    def exitCall(self):
        sys.exit(app.exec_())
        
    def saveCall(self):
        self.grabber = VideoFrameGrabber(self.videoWidget, self)
        self.mediaPlayer.setVideoOutput(self.grabber)
        self.grabber.frame_available.connect(self.save_frame)
    
    def save_frame(self, frame: QImage):
        self.frame_counter += 1
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.pause()
        if frame is None:
            return
        frame.save("C:\\Video-Player\\Screenshots\\screenshot"+str(self.frame_counter)+".jpg")
        
    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.show()
    sys.exit(app.exec_())