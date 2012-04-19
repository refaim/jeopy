from __future__ import print_function

import sys

import wxversion
wxversion.select("2.8")
import wx

from common import *

class Application(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        self.retcode = 0


class MainWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Centre()
        self.CreateMenu()

    def CreateMenu(self):
        menubar = wx.MenuBar()

        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, "E&xit")
        #self.Bind(wx.EVT_MENU, self.OnClose, m_exit)
        menubar.Append(menu, "&File")

        menu = wx.Menu()
        m_about = menu.Append(wx.ID_ABOUT, "&About")
        #self.Bind(wx.EVT_MENU, self.OnAbout, m_about)
        menubar.Append(menu, "&Help")

        self.SetMenuBar(menubar)

    def DisplayError(message):
        wx.MessageBox(message, 'Error', wx.OK | wx.ICON_ERROR)


if __name__ == '__main__':
    application = Application(redirect=True)
    window = MainWindow(parent=None, title='JeoPy')
    window.Show()
    application.MainLoop()
    sys.exit(application.retcode)
