from anki import collection
from aqt.qt import *
from aqt.utils import showInfo
import re
from .gui import initializeQtResources
from aqt import mw

initializeQtResources()

class OptionsWindow(QDialog):

    noteIDs = []

    def __init__(self):
        QDialog.__init__(self, parent=mw)
        self._setupUI()

    def _setupUI(self):
        querylabel = QLabel("Filter notes:")
        self.queryfield = QLineEdit()
        self.queryfield.setPlaceholderText("all notes")
        self.queryNoteCount = QLabel("0")
        querygobutton = QPushButton("Test", clicked=self.filterNotes)

        top_hbox = QHBoxLayout()
        top_hbox.addWidget(querylabel)
        top_hbox.addWidget(self.queryfield)
        top_hbox.addWidget(self.queryNoteCount)
        self.queryNoteCount.setVisible(False)
        top_hbox.addWidget(querygobutton)

        self.regexInputLabel = QLabel("Search for this Regular Expression")
        self.regexInput = QPlainTextEdit()
        self.regexInput.setMinimumHeight(80)
        self.regexInput.setPlaceholderText("r\"/ query /\"gm or plain text")
        self.regexInput.setTabChangesFocus(True)

        self.regexReplaceLabel = QLabel("Replace with this Regular Expression")
        self.regexReplace = QPlainTextEdit()
        self.regexReplace.setMinimumHeight(80)
        self.regexReplace.setPlaceholderText("r\"/ replace /\"gm or plain text")
        self.regexReplace.setTabChangesFocus(True)

        flabel = QLabel("In this field:")
        self.fsel = QComboBox()
        #fields = self._getFields()
        #self.fsel.addItems(fields)

        self.matchCase = QCheckBox(self)
        self.matchCase.setText("Match case")
        self.matchCase.setChecked(False)

        self.regex = QCheckBox(self, stateChanged=self.regexChecked)
        self.regex.setText("Use Regular Expressions")
        self.regex.setChecked(True)

        self.deleteOnly = QCheckBox(self, stateChanged=self.deleteOnlyChecked)
        self.deleteOnly.setText("Delete without replacing")
        self.deleteOnly.setChecked(False)

        f_hbox = QHBoxLayout()
        # f_hbox.addWidget(flabel)
        # f_hbox.addWidget(self.fsel)
        f_hbox.addWidget(self.matchCase)
        f_hbox.addStretch(1)
        f_hbox.addWidget(self.deleteOnly)
        f_hbox.addStretch(1)
        f_hbox.addWidget(self.regex)
        f_hbox.setAlignment(Qt.AlignJustify)

        self.noteFields = QLineEdit()
        self.noteFields.setPlaceholderText("e.g. \"Front, Extra, answer\"...")
        noteFieldsLabel = QLabel("Limit to fields named: ")

        noteFieldLayout = QHBoxLayout()
        noteFieldLayout.addWidget(noteFieldsLabel)
        noteFieldLayout.addWidget(self.noteFields)

        button_box = QDialogButtonBox(Qt.Horizontal, self)
        closeButton = button_box.addButton("&Cancel", QDialogButtonBox.RejectRole)
        exportButton = button_box.addButton("Simulate as Text", QDialogButtonBox.ActionRole)
        executeButton = button_box.addButton("Replace Immediately", QDialogButtonBox.ActionRole)
        diffButton = button_box.addButton("Run Comparator", QDialogButtonBox.ActionRole)
        diffButton.setDefault(True)

        executeButton.setToolTip("Executes the replacement without a preview. WARNING: this change is permanent!")
        exportButton.setToolTip("Save a text file showing the potential changes. Original notes are NOT altered.")
        diffButton.setToolTip("Visually compare and approve changes to each note one-by-one.")

        executeButton.clicked.connect(lambda state, x="execute": self.onGo(x))
        exportButton.clicked.connect(lambda state, x="simulate": self.onGo(x))
        diffButton.clicked.connect(lambda state, x="diff": self.onGo(x))
        closeButton.clicked.connect(self.close)

        vbox_main = QVBoxLayout()
        vbox_main.addLayout(top_hbox)
        vbox_main.addWidget(self.regexInputLabel)
        vbox_main.addWidget(self.regexInput)
        vbox_main.addWidget(self.regexReplaceLabel)
        vbox_main.addWidget(self.regexReplace)
        vbox_main.addLayout(f_hbox)
        vbox_main.addLayout(noteFieldLayout)
        vbox_main.addWidget(button_box)
        self.setLayout(vbox_main)

        self.queryfield.setFocus()

        self.setMinimumWidth(750)
        self.setMinimumHeight(400)
        self.setWindowTitle("BetterThen ➔ BetterThan")

    def onGo(self, mode):
        if mode == "diff":
            diffWindow = DifferWindow(self.noteIDs, self.regexInput.toPlainText(), self.regexReplace.toPlainText())
            diffWindow.exec_()
        elif mode == "simulate":
            #simulate
            showInfo("Simulating")
        elif mode == "execute":
            #execute immediately
            showInfo("You dumb bastard. Here we go...")

    def filterNotes(self, query):
        col = mw.col

        if not query:
            query = self.queryfield.text()

        self.noteIDs = col.findNotes(query)
        self.queryNoteCount.setVisible(True)
        self.queryNoteCount.setText(str(len(self.noteIDs)) + " notes found ")

        return len(self.noteIDs)

    def regexChecked(self):
        if self.regex.isChecked():
            self.matchCase.setDisabled(True)
            self.regexInputLabel.setText("Search for this Regular Expression")
            self.regexReplaceLabel.setText("Replace with this Regular Expression")
            self.regexInput.setPlaceholderText("r\"/ find /\"gm")
            self.regexReplace.setPlaceholderText("r\"/ replace /\"gm")
        else:
            self.matchCase.setDisabled(False)
            self.regexInputLabel.setText("Search for")
            self.regexReplaceLabel.setText("Replace with")
            self.regexInput.setPlaceholderText("Find")
            self.regexReplace.setPlaceholderText("Replace")

    def deleteOnlyChecked(self):
        if self.deleteOnly.isChecked():
            self.regexReplace.setDisabled(True)
            self.regexReplaceLabel.setDisabled(True)
        else:
            self.regexReplace.setDisabled(False)
            self.regexReplaceLabel.setDisabled(False)


class DifferWindow(QDialog):

    def __init__(self, noteIDs, query, replace="", regex=False, mode="replace", matchCase=False, fields=None):
        QDialog.__init__(self, parent=mw)
        self._setupUI(noteIDs, query, replace, regex, mode, matchCase, fields)

    def _setupUI(self, noteIDs, query, replace, regex=False, mode="replace", matchCase=False, fields=None):

        # two vertical boxes contained in a horizontal box, for the comparisons, with a horizontal button row beneath

        originalLabel = QLabel("Original")
        originalPreview = QTextEdit()

        originalLayout = QVBoxLayout()
        originalLayout.addWidget(originalLabel)
        originalLayout.addWidget(originalPreview)

        newLabel = QLabel("Modified")
        newPreview = QTextEdit()

        newLayout = QVBoxLayout()
        newLayout.addWidget(newLabel)
        newLayout.addWidget(newPreview)

        previewLayout = QHBoxLayout()
        previewLayout.addLayout(originalLayout)
        previewLayout.addLayout(newLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(previewLayout)

        self.setLayout(mainLayout)
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.setWindowTitle("BetterThen ➔ BetterThan")




def parseCards():
    # get the number of cards in the current collection, which is stored in main window
    cardCount = mw.col.cardCount()
    col = mw.col

    # get all notes of a type
    ids = col.findNotes("")

    if not ids:
        return

    count = 0

    # pattern = "(?:<img .*?>){2,}"
    # pattern = "<img .*?>(.+?)<img .*?>"
    # pattern = "<img .*?>((?:</?div>|<br.*/?>)+?)<img .*?>"
    # pattern = "<u>"

    pattern = " [A-Z]"
    replaceWith = " "

    middleBits = ""

    commitChanges = False
    mode = "replace"

    if commitChanges:
        mw.checkpoint("BetterThen Search")
        mw.progress.start()

    for id in ids:
        note = col.getNote(id)
        cardEdited = False

        # model = note.model()
        # fieldNames = mw.col.models.fieldNames(model)

        for (field, value) in note.items():

            search = re.search(pattern, value)

            if search is not None:
                cardEdited = True

                if mode == "delete":
                    output = value[:search.start(1)] + value[search.end(1):]

                    middleBits = middleBits + str(id) + " " + field + " REMOVED: " + search.group(
                        1) + "\n\t\tNEW: " + output + "\n\n"

                elif mode == "replace":
                    output = re.sub(pattern, replaceWith, value)

                    middleBits = middleBits + str(id) + " " + field + " REPLACED: " + search.group(
                    ) + "\n\t\tNEW: " + output + "\n\n"

                if commitChanges:
                    note[field] = output

        if cardEdited:
            middleBits = middleBits + "-- -- --\n\n"
            count = count + 1

            if commitChanges:
                note.flush()

    if commitChanges:
        mw.progress.finish()
        mw.requireReset()
        mw.reset()

    showInfo("I found " + str(count) + " matches")

    file = open("/Users/Esteban/Desktop/out.txt", "w", encoding='utf-8')
    file.write(middleBits)
    file.close()

    # always end editing a note with note.flush()



# def _getFields(self):
#     nid = self.nids[0]
#     model = mw.col.getNote(nid).model()
#     fields = mw.col.models.fieldNames(model)
#     return fields

