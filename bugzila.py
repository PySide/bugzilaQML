from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *
from PySide.QtDeclarative import *

class Bugzilla (QAbstractListModel):

    # Role names
    ID = 0
    STATUS = 1
    PRIORITY = 2
    ASSIGNEE = 3
    SUMARY = 4
    COMPONENT = 5

    def __init__(self, parent = None):
        QAbstractListModel.__init__(self, parent)
        self.manager = QNetworkAccessManager(self)
        self.manager.finished[QNetworkReply].connect(self.replyFinished)
        self._statistics = {
            'P1' : 0,
            'P2' : 0,
            'P3' : 0,
            'P4' : 0,
            'P5' : 0,
            'FIXED' : 0,
            'UNCONFIRMED' : 0,
            '---' : 0
        }
        self._bugs = []
        self._maxValue = 0
        self.setRoleNames({self.ID       : 'BUG_ID',
                           self.STATUS   : 'BUG_STATUS',
                           self.PRIORITY : 'BUG_PRIORITY',
                           self.ASSIGNEE : 'BUG_ASSIGNEE',
                           self.SUMARY   : 'BUG_SUMMARY',
                           self.COMPONENT: 'BUG_COMPONENT'})
        self.update()

    @Slot()
    def update(self):
        url = "http://bugs.pyside.org/buglist.cgi?bug_status=UNCONFIRMED&bug_status=NEW&bug_status=WAITING&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=RESOLVED&bug_status=VERIFIED&product=PySide&query_format=advanced&resolution=---&resolution=FIXED&ctype=csv"
        self.manager.get(QNetworkRequest(QUrl(url)))

    @Slot(QNetworkReply)
    def replyFinished(self, reply):
        for k in self._statistics:
            self._statistics[k] = 0

        self._bugs = []
        while not reply.atEnd():
            line = str(reply.readLine())
            fields = line.split(',', 8)

            fields = map(lambda (x) : x[1:-1] if x.startswith('"') else x, fields)
            fields = map(lambda (x) : x.replace('""', '"'), fields)
            self._bugs.append(fields)

            #print fields
            for i in (2, 5, 6):
                key = fields[i]
                if key in self._statistics:
                    self._statistics[key] += 1


        self._maxValue = max(self._statistics['P1'], self._statistics['P2'], self._statistics['P3'], self._statistics['P4'], self._statistics['P5'])
        reply.deleteLater()
        #self.dataChanged.emit(self.index(0, 0), self.index(4, 0))
        self.reset()
        self.modelUpdated.emit()

    def getMaxValue(self):
        return self._maxValue

    modelUpdated = Signal()
    maxValue = Property(int, getMaxValue, notify = modelUpdated)

    unconfirmedBugs = Property(int, lambda(self) : self._statistics['UNCONFIRMED'], notify = modelUpdated)
    fixedBugs = Property(int, lambda(self) : self._statistics['FIXED'], notify = modelUpdated)
    openedBugs = Property(int, lambda(self) : self._statistics['---'], notify = modelUpdated)
    p1 = Property(int, lambda(self) : self._statistics['P1'], notify = modelUpdated)
    p2 = Property(int, lambda(self) : self._statistics['P2'], notify = modelUpdated)
    p3 = Property(int, lambda(self) : self._statistics['P3'], notify = modelUpdated)
    p4 = Property(int, lambda(self) : self._statistics['P4'], notify = modelUpdated)
    p5 = Property(int, lambda(self) : self._statistics['P5'], notify = modelUpdated)


    def rowCount(self, index):
        return len(self._bugs)

    def data(self, index, role):
        row = index.row()
        if role == self.ID:
            return self._bugs[row][0]
        elif role == self.STATUS:
            return self._bugs[row][4]
        elif role == self.PRIORITY:
            return self._bugs[row][2]
        elif role == self.ASSIGNEE:
            return self._bugs[row][5]
        elif role == self.SUMARY:
            return self._bugs[row][7]
        elif role == self.COMPONENT:
            return "Qt" # TODO
        elif Qt.DisplayRole:
            return self._bugs[row][7]
        return None

def main():
    app = QApplication([])
    bug = Bugzilla()
    view = QDeclarativeView()
    view.setResizeMode(QDeclarativeView.SizeRootObjectToView)
    view.rootContext().setContextProperty('bugmodel', bug)
    view.setSource(QUrl.fromLocalFile('bugqml.qml'))

    timer = QTimer()
    timer.timeout.connect(bug.update)
    timer.start(1000 * 60 * 10)

    view.show()
    app.exec_()


if __name__ == '__main__':
    main()