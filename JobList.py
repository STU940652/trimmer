import wx # 2.8

from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ColumnSorterMixin

class ListCtrlAutoWidth(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent, resizecolumn=0):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(resizecolumn)


class JobList(wx.Panel):
    def __init__ (self, parent, responseQueue, CancelJobCallback):
        wx.Panel.__init__(self, parent)
        self.responseQueue = responseQueue
        self.CancelJobCallback = CancelJobCallback
        self.CompletionCallback = None
        
        #Window Splitter
        splitter = wx.SplitterWindow(self)

        # Job List Window
        self.MessageList = ListCtrlAutoWidth(splitter, resizecolumn='LAST')
        self.MessageList.InsertColumn(0,'Job', width = 175)
        self.MessageList.InsertColumn(1,'Message')
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick, self.MessageList)
        
        # Log Window
        self.Messages = wx.TextCtrl (splitter, style=wx.TE_MULTILINE|wx.TE_READONLY)

        # Add sizer and init splitter
        Sizer=wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(splitter, 1, flag=wx.EXPAND)
        splitter.SplitHorizontally(self.MessageList, self.Messages, 100)
        self.SetSizer(Sizer)

        # finally create the timer, which checks for the source files
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1000)

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
    def OnDestroy (self, evt):
        # Cleanup Timer
        self.timer.Stop()
        
        # Let the event pass
        evt.Skip()
        
    def AddJob (self, cName):
        row = self.MessageList.GetItemCount()
        self.MessageList.InsertItem(row, cName)
        self.MessageList.SetItem(row,1, 'Pending...')

    def OnRightClick(self, event):
        self.ItemIndexRightClicked = event.GetIndex()
        
        self.menuItems = []     
        self.menuItems.append((wx.NewId(),'Cancel'))
            
        menu = wx.Menu()
        for (id,nm) in self.menuItems:
            menu.Append(id,nm)
            wx.EVT_MENU(menu, id, self.OnRightMenuSelect)
            
        self.menuItems = dict(self.menuItems)
        self.PopupMenu (menu, event.GetPoint())
        menu.Destroy

    def OnRightMenuSelect(self, event):
        """
        Handle a right-click event.
        """
        if (self.menuItems[event.GetId()] == 'Cancel'):
            self.CancelJobCallback(self.MessageList.GetItemText(self.ItemIndexRightClicked))
            self.MessageList.SetItem(self.ItemIndexRightClicked,1 , "Canceling...")

    def SetCompletionCallback(self, CompletionCallback):
        self.CompletionCallback = CompletionCallback

    def OnTimer (self, evt):
        while not self.responseQueue.empty(): 
            cName, message, completion = self.responseQueue.get ()
            found = False
            for row in range(self.MessageList.GetItemCount()):
                if cName==self.MessageList.GetItemText(row):
                    self.MessageList.SetItem(row,1, message)
                    self.Messages.AppendText(message+'\n')
                    found = True
                    break
            if not found:
                row = self.MessageList.GetItemCount()
                self.MessageList.InsertStringItem(row, cName)
                self.MessageList.SetItem(row,1, message)
                
            if completion:
                # We have a completed job, report it to the Upload tab
                self.CompletionCallback(completion)
            
