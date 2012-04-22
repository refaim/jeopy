import functools
import sys

import wxversion; wxversion.select('2.8')
import wx
import wx.grid

import suite
from common import *


DEFAULT_WINDOW_SIZE = (640, 480)
DEFAULT_FONT_SIZE = 16
DEFALUT_BORDER_SIZE = 5
DEFAULT_TABLE_MARGIN = DEFALUT_BORDER_SIZE * 10

PRICE_MULTIPLIER = 100
MINIMAL_PLAYERS_COUNT = 2
MAXIMAL_PLAYERS_COUNT = 5

WINDOW_TITLE = 'JeoPy'


def PreventEvent(widget, event):
    stub = lambda event: None
    widget.Bind(event, stub)


class Game(object):
    def __init__(self):
        self.players = {}
        self.started = False


class JeopyGrid(wx.grid.Grid):
    def __init__(self, *args, **kwargs):
        super(JeopyGrid, self).__init__(*args, **kwargs)
        self.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.EnableEditing(edit=False)
        self.EnableDragRowSize(enable=False)
        self.EnableDragColSize(enable=False)
        self.EnableDragGridSize(enable=False)

        # hide headers
        self.SetRowLabelSize(0)
        self.SetColLabelSize(0)

        PreventEvent(self, wx.grid.EVT_GRID_CELL_LEFT_CLICK)
        self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.PreventSelect)


    def PreventSelect(self, event):
        self.SetSelectionBackground(self.GetDefaultCellBackgroundColour())
        self.SetSelectionForeground(self.GetDefaultCellTextColour())
        self.ClearSelection()


class QuestionsTable(JeopyGrid):
    def __init__(self, *args, **kwargs):
        super(QuestionsTable, self).__init__(*args, **kwargs)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)


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

        row = topicsCount / 2
        col = sum(divmod(questionsOnTopicCount, 2))
        self.SetGridCursor(row, col)


    def Stretch(self):
        curWidth, curHeight = self.GetClientSize().asTuple()
        newWidth, newHeight = [value - DEFAULT_TABLE_MARGIN for value in
            self.GetParent().GetClientSize().asTuple()]

        self.BeginBatch()

        if curWidth < newWidth:
            colCount = self.GetNumberCols()
            addWidth = (newWidth - curWidth) / colCount
            for col in range(colCount):
                colWidth = self.GetColSize(col) + addWidth
                self.SetColSize(col, colWidth)
            self.SetColMinimalAcceptableWidth(colWidth)

        if curHeight < newHeight:
            rowCount = self.GetNumberRows()
            addHeight = (newHeight - curHeight) / rowCount
            for row in range(rowCount):
                rowHeight = self.GetRowSize(row) + addHeight
                self.SetRowSize(row, rowHeight)
            self.SetRowMinimalAcceptableHeight(rowHeight)

        self.AutoSize()
        self.Centre()
        self.EndBatch()


    def OnKeyDown(self, event):
        row, col = self.GetGridCursorRow(), self.GetGridCursorCol()
        moves = (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT, wx.WXK_RIGHT)

        key = event.GetKeyCode()
        if key in moves:
            # forbid going to topics
            if key != wx.WXK_LEFT or col != 1:
                event.Skip()
            return

        # stub
        if key != wx.WXK_RETURN:
            return

        if col != 0 and self.GetCellValue(row, col) != '':
            attr = self.GetOrCreateCellAttr(row, col)
            wx.MessageBox(attr.text)
            self.SetCellValue(row, col, '')


class PlayersTable(JeopyGrid):
    def __init__(self, *args, **kwargs):
        super(PlayersTable, self).__init__(*args, **kwargs)
        self.SetCellHighlightPenWidth(0) # hide cursor


    def Fill(self, players):
        rowcount = 2 # name, score
        self.CreateGrid(rowcount, len(players))

        for i, player in enumerate(players):
            self.SetCellValue(0, i, player)


class SelectPlayersWindow(wx.Frame):
    def __init__(self, parent):
        super(SelectPlayersWindow, self).__init__(
            parent,
            title='Enter player names',
            style=wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)

        def createButton(title, parent, sizer, wxid=wx.ID_ANY, event=None):
            button = wx.Button(parent, wxid, title)
            sizer.Add(button, proportion=0, flag=wx.ALIGN_CENTER | wx.ALL,
                border=DEFALUT_BORDER_SIZE)
            if not event is None:
                button.Bind(wx.EVT_BUTTON, event)
            return button

        def createBlock(orient):
            panel = wx.Panel(self, wx.ID_ANY)
            sizer = wx.BoxSizer(orient)
            panel.SetSizer(sizer)
            return panel, sizer

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(mainSizer)

        countPanel, countSizer = createBlock(wx.HORIZONTAL)
        self.incButton = createButton('Increase', countPanel, countSizer,
            event=self.CreateEdit)
        self.decButton = createButton('Decrease', countPanel, countSizer,
            event=self.RemoveEdit)

        self.playersControls = []
        self.editPanel, self.editSizer = createBlock(wx.VERTICAL)
        for i in range(MINIMAL_PLAYERS_COUNT):
            self.CreateEdit()

        buttonPanel, buttonSizer = createBlock(wx.HORIZONTAL)
        createButton('Start', buttonPanel, buttonSizer, wx.ID_OK,
            self.OnExit)
        createButton('Cancel', buttonPanel, buttonSizer, wx.ID_CANCEL,
            self.OnExit)

        mainSizer.Add(countPanel)
        mainSizer.Add(self.editPanel, flag=wx.EXPAND)
        mainSizer.Add(buttonPanel)
        mainSizer.Fit(self)


    def CreateEdit(self, event=None):
        if len(self.playersControls) < MAXIMAL_PLAYERS_COUNT:
            edit = wx.TextCtrl(self.editPanel)
            self.playersControls.append(edit)
            self.editSizer.Add(edit, proportion=1, flag=wx.ALL | wx.EXPAND,
                border=DEFALUT_BORDER_SIZE)
            self.GetSizer().Fit(self)

            self.decButton.Enable()
            if len(self.playersControls) == MAXIMAL_PLAYERS_COUNT:
                self.incButton.Disable()


    def RemoveEdit(self, event):
        if len(self.playersControls) > MINIMAL_PLAYERS_COUNT:
            target = self.playersControls.pop()
            self.editSizer.Remove(target)
            target.Destroy()
            self.editSizer.Fit(self.editPanel)
            self.GetSizer().Fit(self)

            self.incButton.Enable()
            if len(self.playersControls) == MINIMAL_PLAYERS_COUNT:
                self.decButton.Disable()


    def Show(self, callback):
        self.callback = callback
        self.CenterOnParent()
        self.GetParent().Enable(False)
        super(SelectPlayersWindow, self).Show()
        self.Raise()


    def OnExit(self, event):
        self.GetParent().Enable(True)
        self.Destroy()
        if event.EventObject.GetId() == wx.ID_OK:
            names = [edit.Value for edit in self.playersControls]
            self.callback(names)


class MainWindow(wx.Frame):
    def __init__(self):
        super(MainWindow, self).__init__(parent=None, title=WINDOW_TITLE,
            size=DEFAULT_WINDOW_SIZE,
            style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)
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
        menu.Append(wx.ID_ANY, '&New Game\tCtrl+N')
        wx.EVT_MENU(self, wx.ID_ANY, self.OnNewGame)
        menu.Append(wx.ID_EXIT, '&Quit\tCtrl+Q')
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnClose)
        bar.Append(menu, '&File')

        self.SetMenuBar(bar)


    def CreatePanels(self):
        self.questionsPanel = wx.Panel(self, wx.ID_ANY | wx.SUNKEN_BORDER)
        self.playersPanel = wx.Panel(self, wx.ID_ANY | wx.SUNKEN_BORDER)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.questionsPanel, proportion=5, flag=wx.EXPAND)
        box.Add(self.playersPanel, proportion=2, flag=wx.EXPAND)
        self.SetSizer(box)


    def AskForAbort(self):
        if not self.game.started:
            return True
        try:
            dialog = wx.MessageDialog(
                self,
                'Abort current game?',
                self.GetTitle(),
                wx.YES_NO | wx.NO_DEFAULT)
            return dialog.ShowModal() == wx.ID_YES
        finally:
            dialog.Destroy()


    def OnClose(self, event):
        if not self.AskForAbort():
            return
        self.Close()


    def OnNewGame(self, event):
        if not self.AskForAbort():
            return

        def setPlayers(players, startGame, game):
            game.players = players
            startGame()

        dialog = SelectPlayersWindow(parent=self)
        dialog.Show(functools.partial(setPlayers,
            startGame=self.StartGame, game=self.game))


    def StartGame(self):
        try:
            whole = suite.parse(open('sample.fb2', 'rU'))
        except JeopyError, ex:
            self.DisplayError(ex)
            return
        selection = suite.select(whole)

        def initTable(memberName, memberClass, parent, data):
            table = getattr(self, memberName)
            if not table is None:
                table.Destroy()
            table = memberClass(parent, style=wx.SUNKEN_BORDER)
            table.SetDefaultCellFont(self.font)
            table.Fill(data)
            table.AutoSize()
            table.Centre()
            setattr(self, memberName, table)

        initTable('questionsTable', QuestionsTable, self.questionsPanel,
            selection)
        self.questionsTable.Stretch()

        initTable('playersTable', PlayersTable, self.playersPanel,
            self.game.players)

        self.game.started = True


if __name__ == '__main__':
    application = wx.App(redirect=True)
    window = MainWindow()
    window.Show()
    application.MainLoop()
