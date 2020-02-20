# import the main window object (mw) from aqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *

from anki import Collection

import re

from . import main


# col = Collection("/Users/Esteban/Library/Application Support/Anki2/Lightyear/collection.anki2")

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.


def parseCards():
    # get the number of cards in the current collection, which is stored in main window
    cardCount = mw.col.cardCount()
    col = mw.col

    # get all notes of a type
    ids = col.findNotes("")

    if not ids:
        return


    count = 0

    #pattern = "(?:<img .*?>){2,}"
    #pattern = "<img .*?>(.+?)<img .*?>"
    #pattern = "<img .*?>((?:</?div>|<br.*/?>)+?)<img .*?>"
    #pattern = "<u>"

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


    #always end editing a note with note.flush()


def openWindow():
    differ = main.OptionsWindow()
    differ.exec_()


# create a new menu item, "test"
action = QAction("Run BetterThen", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(openWindow)
# and add it to the tools menu
mw.form.menuTools.addAction(action)