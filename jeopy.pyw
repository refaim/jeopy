import sys

import wxversion; wxversion.select('2.8')
import wx
import wx.grid

import suite
from common import *


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


class Application(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        self.retcode = 0


class MainWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Centre()
        self.CreateMenu()
        self.CreatePanel()
        self.game = Game()
        self.qtable = None
        self.font = wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD)

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


    def CreatePanel(self):
        self.panel = wx.Panel(self, wx.ID_ANY)
        #box = wx.BoxSizer(wx.VERTICAL)
        #box.Add(self.panel, 1, wx.EXPAND)
        #self.SetAutoLayout(True)
        #self.SetSizer(box)
        #self.Layout()


    def OnClose(self, event):
        if self.game.started:
            try:
                dialog = wx.MessageDialog(
                    self,
                    'Do you really want to exit?',
                    self.GetTitle(),
                    wx.YES_NO | wx.NO_DEFAULT)
                if dialog.ShowModal() == wx.ID_NO:
                    return
            finally:
                dialog.Destroy()
        self.Close()


    def OnNewGame(self, event):
        try:
            rawquestions = suite.download('http://db.chgk.info/tour/nesp05sv/')
        except JeopyError, ex:
            self.DisplayError(ex)
            return
        rawquestions = suite.select(rawquestions)

        if self.qtable:
            self.qtable.Destroy()

        self.qtable = wx.grid.Grid(self)#.panel)
        self.qtable.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.qtable.SetDefaultCellFont(self.font)

        self.qtable.SetDefaultRowSize(100)
        self.qtable.SetDefaultColSize(100)

        self.qtable.CreateGrid(len(rawquestions), len(rawquestions[0][1]) + 1)

        prices = (100, 200, 300, 500, 1000)
        for rownum, (topic, questions) in enumerate(rawquestions):
            self.qtable.SetCellValue(rownum, 0, topic)
            for colnum, question in enumerate(questions):
                self.qtable.SetCellValue(rownum, colnum + 1, str(prices[colnum]))

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.qtable, 1, wx.EXPAND)
        #self.panel.SetSizer(box)
        self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Layout()


if __name__ == '__main__':
    register_identifiers()
    application = Application(redirect=True)
    window = MainWindow(parent=None, title='JeoPy')
    window.Show()
    application.MainLoop()
    sys.exit(application.retcode)
