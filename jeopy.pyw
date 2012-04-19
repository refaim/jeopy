import sys

import wxversion; wxversion.select('2.8')
import wx
import wx.grid

import suite
from common import *

PRICE_MULTIPLIER = 100
DEFAULT_WINDOW_SIZE = (640, 480)
DEFAULT_FONT_SIZE = 16
WINDOW_TITLE = 'JeoPy'


def register_identifiers():
    identifiers = (
        'JEOPY_ID_NEWGAME',
    )
    for id_ in identifiers:
        globals()[id_] = wx.NewId()


class Game(object):
    def __init__(self):
        self.players = {}
        self.started = False


class QuestionsTable(wx.grid.Grid):
    def __init__(self, *args, **kwargs):
        wx.grid.Grid.__init__(self, *args, **kwargs)
        self.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.EnableEditing(edit=False)
        self.EnableDragRowSize(enable=False)
        self.EnableDragColSize(enable=False)
        self.EnableDragGridSize(enable=False)
        # Hide headers.
        self.SetRowLabelSize(0)
        self.SetColLabelSize(0)

        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)


    def OnDblClick(self, event):
        row, col = event.GetRow(), event.GetCol()
        if col != 0 and self.GetCellValue(row, col) != '':
            attr = self.GetOrCreateCellAttr(row, col)
            wx.MessageBox(attr.text)
            self.SetCellValue(row, col, '')


class MainWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Centre()
        self.CreateMenu()
        self.CreatePanels()
        self.game = Game()
        self.questions = None
        self.font = wx.SystemSettings.GetFont(0)
        self.font.SetPointSize(DEFAULT_FONT_SIZE)

        wx.EVT_SIZE(self, self.OnResize)


    def DisplayError(self, data):
         wx.MessageBox(str(data), 'Error', wx.OK | wx.ICON_ERROR)


    def CreateMenu(self):
        bar = wx.MenuBar()

        menu = wx.Menu()
        menu.Append(JEOPY_ID_NEWGAME, '&New Game\tCtrl+N')
        wx.EVT_MENU(self, JEOPY_ID_NEWGAME, self.OnNewGame)
        menu.Append(wx.ID_EXIT, '&Quit\tCtrl+Q')
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnClose)
        bar.Append(menu, '&File')

        self.SetMenuBar(bar)


    def CreatePanels(self):
        self.questionsPanel = wx.Panel(self, wx.ID_ANY | wx.SUNKEN_BORDER)
        self.playersPanel = wx.Panel(self, wx.ID_ANY | wx.SUNKEN_BORDER)
        self.questionsPanel.SetBackgroundColour("BLUE")
        self.playersPanel.SetBackgroundColour("RED")

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.questionsPanel, 2, wx.EXPAND)
        box.Add(self.playersPanel, 1, wx.EXPAND)
        self.SetSizer(box)


    def OnResize(self, event):
        if self.questions:
            self.questions.Centre()
        event.Skip()


    def OnClose(self, event):
        if self.game.started:
            try:
                dialog = wx.MessageDialog(
                    self,
                    'Do you really want to quit?',
                    self.GetTitle(),
                    wx.YES_NO | wx.NO_DEFAULT)
                if dialog.ShowModal() == wx.ID_NO:
                    return
            finally:
                dialog.Destroy()
        self.Close()


    def OnNewGame(self, event):
        try:
            whole = suite.download('http://db.chgk.info/tour/nesp05sv/')
        except JeopyError, ex:
            self.DisplayError(ex)
            return
        selection = suite.select(whole)

        if self.questions:
            self.questions.Destroy()

        self.questions = QuestionsTable(self.questionsPanel,
            style=wx.SUNKEN_BORDER)
        self.questions.SetDefaultCellFont(self.font)
        self.questions.CreateGrid(len(rawquestions),
            len(rawquestions[0][1]) + 1)

        for rownum, (topic, questions) in enumerate(rawquestions):
            self.questions.SetCellValue(rownum, 0, topic)
            for colnum, question in enumerate(questions):
                number = colnum + 1
                self.questions.SetCellValue(rownum, number,
                    str(number * PRICE_MULTIPLIER))
                attr = self.questions.GetOrCreateCellAttr(rownum, number)
                attr.text = question[0]

        self.questions.AutoSize()
        self.questions.Centre()


if __name__ == '__main__':
    register_identifiers()
    application = wx.App(redirect=True)
    window = MainWindow(parent=None, title=WINDOW_TITLE, size=DEFAULT_WINDOW_SIZE)
    window.Show()
    application.MainLoop()
