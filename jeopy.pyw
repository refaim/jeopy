import functools
import sys

import wxversion; wxversion.select('2.8')
import wx
import wx.grid

import suite
from common import *

PRICE_MULTIPLIER = 100
DEFAULT_WINDOW_SIZE = (640, 480)
DEFAULT_FONT_SIZE = 16
DEFALUT_BORDER_SIZE = 5
DEFAULT_PLAYERS_COUNT = 3
MINIMAL_PLAYERS_COUNT = 2
MAXIMAL_PLAYERS_COUNT = 5
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


class JeopyGrid(wx.grid.Grid):
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


class QuestionsTable(JeopyGrid):
    def __init__(self, *args, **kwargs):
        JeopyGrid.__init__(self, *args, **kwargs)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)


    def Fill(self, data):
        topicsCount = len(data)
        questionsOnTopicCount = len(data[0][1])
        self.CreateGrid(topicsCount, questionsOnTopicCount + 1)

        for rownum, (topic, questions) in enumerate(data):
            self.SetCellValue(rownum, 0, topic)
            for colnum, question in enumerate(questions):
                number = colnum + 1
                self.SetCellValue(rownum, number, str(number * PRICE_MULTIPLIER))
                attr = self.GetOrCreateCellAttr(rownum, number)
                attr.text = question[0]


    def OnDblClick(self, event):
        row, col = event.GetRow(), event.GetCol()
        if col != 0 and self.GetCellValue(row, col) != '':
            attr = self.GetOrCreateCellAttr(row, col)
            wx.MessageBox(attr.text)
            self.SetCellValue(row, col, '')


class PlayersTable(JeopyGrid):
    def __init__(self, *args, **kwargs):
        JeopyGrid.__init__(self, *args, **kwargs)


    def Fill(self, players):
        rowcount = 2 # name, score
        self.CreateGrid(rowcount, len(players))

        for i, player in enumerate(players):
            self.SetCellValue(0, i, player)


class SelectPlayersWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title='Enter player names',
            style=wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)

        def createButton(title, parent, sizer, wxid=wx.ID_ANY, event=None):
            button = wx.Button(parent, wxid, title)
            sizer.Add(button, proportion=0, flag=wx.ALIGN_CENTER | wx.ALL,
                border=DEFALUT_BORDER_SIZE)
            if not event is None:
                button.Bind(wx.EVT_BUTTON, event)

        def createBlock(orient):
            panel = wx.Panel(self, wx.ID_ANY)
            sizer = wx.BoxSizer(orient)
            panel.SetSizer(sizer)
            return panel, sizer

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(mainSizer)

        self.playersControls = []
        self.editPanel, self.editSizer = createBlock(wx.VERTICAL)
        for i in range(DEFAULT_PLAYERS_COUNT):
            self.CreateEdit()

        countPanel, countSizer = createBlock(wx.HORIZONTAL)
        createButton('Increase', countPanel, countSizer)#, event=self.CreateEdit)
        createButton('Decrease', countPanel, countSizer)#, event=self.RemoveEdit)

        buttonPanel, buttonSizer = createBlock(wx.HORIZONTAL)
        createButton('Start', buttonPanel, buttonSizer, wx.ID_OK, self.OnExit)
        createButton('Cancel', buttonPanel, buttonSizer, wx.ID_CANCEL, self.OnExit)

        mainSizer.Add(countPanel, proportion=1)
        mainSizer.Add(self.editPanel, proportion=len(self.playersControls),
            flag=wx.EXPAND)
        mainSizer.Add(buttonPanel, proportion=1)
        mainSizer.Fit(self)


    def CreateEdit(self, event=None):
        if len(self.playersControls) < MAXIMAL_PLAYERS_COUNT:
            edit = wx.TextCtrl(self.editPanel)
            self.playersControls.append(edit)
            self.editSizer.Add(edit, proportion=1, flag=wx.ALL | wx.EXPAND,
                border=DEFALUT_BORDER_SIZE)
            self.GetSizer().Fit(self)


    def RemoveEdit(self, event):
        if len(self.playersControls) > MINIMAL_PLAYERS_COUNT:
            target = self.playersControls.pop()
            self.editSizer.Remove(target)
            target.Destroy()
            self.editSizer.Fit(self.editPanel)
            self.GetSizer().Fit(self)


    def Show(self, callback):
        self.callback = callback
        self.CenterOnParent()
        self.GetParent().Enable(False)
        super(SelectPlayersWindow, self).Show()
        self.Raise()


    def OnExit(self, event):
        try:
            if event.EventObject.GetId() == wx.ID_OK:
                names = [edit.Value for edit in self.playersControls]
                self.callback(names)
        finally:
            self.GetParent().Enable(True)
            self.Destroy()


class MainWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Centre()
        self.CreateMenu()
        self.CreatePanels()
        self.game = Game()
        self.questionsTable = None
        self.playersTable = None
        self.font = wx.SystemSettings.GetFont(0)
        self.font.SetPointSize(DEFAULT_FONT_SIZE)


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

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.questionsPanel, proportion=2, flag=wx.EXPAND)
        box.Add(self.playersPanel, proportion=1, flag=wx.EXPAND)
        self.SetSizer(box)


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
        def setPlayers(players, startGame, game):
            game.players = players
            startGame()

        dialog = SelectPlayersWindow(parent=self)
        dialog.Show(functools.partial(setPlayers,
            startGame=self.StartGame, game=self.game))


    def StartGame(self):
        try:
            whole = suite.download('http://db.chgk.info/tour/nesp05sv/')
        except JeopyError, ex:
            self.DisplayError(ex)
            return
        selection = suite.select(whole)

        def initTable(tableClass, parent, fillData):
            table = tableClass(parent, style=wx.SUNKEN_BORDER)
            table.SetDefaultCellFont(self.font)
            table.Fill(fillData)
            table.AutoSize()
            table.Centre()
            return table

        if not self.questionsTable is None:
            self.questionsTable.Destroy()
        self.questionsTable = initTable(QuestionsTable, self.questionsPanel,
            selection)

        if not self.playersTable is None:
            self.playersTable.Destroy()
        self.playersTable = initTable(PlayersTable, self.playersPanel,
            self.game.players)


if __name__ == '__main__':
    register_identifiers()
    application = wx.App(redirect=True)
    window = MainWindow(parent=None, title=WINDOW_TITLE,
        size=DEFAULT_WINDOW_SIZE,
        style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)
    window.Show()
    application.MainLoop()
