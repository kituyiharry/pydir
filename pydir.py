#!/usr/bin/env python3
#######################################################################
#                               Pydir!                                #
#######################################################################
#########################################
#  Minimalist python directory browser  #
#########################################

#######################################################################
#            Author: Harry Kituyi <kituyiharry@gmail.com>             #
#######################################################################


"""
Simple File Directory Browser that i wrote as a Weekend project 


TODO: use shutil for some file operations
"""

import urwid
import os
import stat
import shutil
from math import log
from  extra.exporters import JSONExporter
from  extra.ops_manager import MoveOperation

class FileWalker(object):

    """Provides a Model for creating a List of current Directory 
        Structure"""

    def __init__(self,on_error):
        """basic constructor """
        self.curdir = os.getcwd();
        self.error_callback = on_error
        #self.desc_file = ".comments"
        #self.has_description = False

    
    def chdir_into(self,new_dir):
        """
        Switches from the current directory to a new directory
        """
        if os.path.isdir(new_dir):
            try:
                os.chdir(new_dir)
                self.curdir = os.getcwd()
            except Exception as e:
                self.error_callback(str(e))
                return False
            return True
        return False

    def filter_directory(self,item_list=[],hide_hidden=False,hide_dir_changers=False):
        """
        Depending on arguments it filters out hidden files that normally begin with a
        fullstop if needed
        """
        items = item_list
        if hide_hidden:
            items = [item for item in items if str(item).startswith('.')]
        if hide_dir_changers:
            return items
        else:
            items.insert(0,"..")
            #items.insert(1,"..")
        return items

    def get_dir_list(self,hide_dir_changers=False):
        """
        Returns a filtered list of current items in this directory
        """
        dir_list = os.listdir(self.curdir)
        return self.filter_directory(dir_list,hide_dir_changers=hide_dir_changers)
    
    def join_to_cur(self,path_append):
        """
        Concatenates the passed path to the current path
        """
        return os.path.join(self.curdir,path_append)

    #Thank you Stack Overflow
    def pretty_size(self,n,pow=0,b=1024,u='B',pre=['']+[p+'i'for p in'KMGTPEZY']):
        """
        it just changes directory file sizes (e.g 11843334345) to more readable ones e.g
        118GB (may be ironically unreadable code)
        """
        pow,n=min(int(log(max(n*b**pow,1),b)),len(pre)-1),n*b**pow
        return "%%.%if %%s%%s"%abs(pow%(-pow-1))%(n/b**float(pow),pre[pow],u)



    def get_stat_info(self,file_or_dir=".",f_sim=True):
        """
        Returns a dict of stat information of file passed (os.stat)
        """
        stat_inf =  os.stat(os.path.join( self.curdir,file_or_dir),follow_symlinks=f_sim)
        return  {
                'file-perm':stat.filemode(stat_inf.st_mode) ,'file-size' : self.pretty_size(stat_inf.st_size),   
                'Links'   : stat_inf.st_nlink,'Owner'   : stat_inf.st_uid
        }

    def get_disk_usage(self):
        """
        Gets the Disk usage and returns a dict   
        """
        du = shutil.disk_usage(self.curdir)
        return {'total':self.pretty_size(du.total),'free':self.pretty_size(du.free),'used':self.pretty_size(du.used)}



class PaletteInflator(object):

    """An abstraction The Global palette and various operations
        such as Perhaps Loading from a config file or whatever :P"""

    def __init__(self):
        """TODO: to be defined1. """
        self._palette=[]


    @property
    def palette(self):
        """
        Returns Current active palette
        """
        return self._palette

    @palette.setter
    def palette(self,palette_list):
        """Sets Currents active Palette"""
        self._palette = palette_list

class CustomListBox(urwid.ListBox):

    """
    Custom implementation of the Listbox able to handle extra Keypresses

    """
    signals = ['toggle-select']


    def __init__(self,*args,**kwargs):
        super(CustomListBox,self).__init__(*args,**kwargs) 


    def create_pop_up_bridge(self,bridge):
        """
        bbox
        Used to backreference this widget so that popups inflated can have a Close button that closes them
        ,Probably not a good callback pattern but meh!!
        """
        self.pop_up_bridge = bridge
        return self

    def keypress(self,size,key):
        """
        Override method to customize key handling
        """
        if key in ('e','E'):
            #TODO : Another Popup
            return self.pop_up_bridge.open_pop_up()
        elif key in ('s','S'):
            return self.toggle_select_mode()
        else:
            return super(CustomListBox,self).keypress(size,key)

    def toggle_select_mode(self):
        """
        Emits a signal using urwids signalling system telling the listbox to swap its walker between the 
        normal mode or multi select mode
        """
        self._emit('toggle-select')

class ViewBuilder(object):

    """Sets up the Required View"""

    def __init__(self):
        """Constructor """
        self.is_in_normal_mode= True
        self.file_walker = FileWalker(self.disp_error_msg)
        self.header = self.setup_header()
        self.body = self.setup_body()
        self.frame = None
        self.select_mode_walker_cache = {} #TODO: Clear this minimal Cache after running an operation

    def setup_header(self,header_align="left"):
        """
        Creates a Header 
        TODO: Filter text with Ellipsizing long names
        """
        base_dir = self.file_walker.curdir

        self.header = urwid.AttrMap(urwid.Columns(
            [
                ('weight',1.59,urwid.Text(self.file_walker.curdir)),
                urwid.ProgressBar('popupbg','green')
            ],1
            ),"header")
        return self.header

    def type_aware_wrap(self,file_or_dir):
        if os.path.isdir(self.file_walker.join_to_cur(file_or_dir)):
            return urwid.AttrMap(PopupableListItemButton(file_or_dir,self.SignalHandler,self.file_walker),"directory",focus_map="reversed")
        return urwid.AttrMap(PopupableListItemButton(file_or_dir,self.SignalHandler,self.file_walker),"file",focus_map='reversed')


    def gen_walker(self):
        """Creates a SimpleFocusListWalker
        :returns: TODO
        """
        return  urwid.MonitoredList([
                        self.type_aware_wrap(choice) for choice in self.file_walker.get_dir_list()
                    ])

    def disp_error_msg(self,err):
        """
        Callback function used by the FileWalker to display error messages to the footer
        """
        self.frame.footer = urwid.AttrMap(urwid.Text([ u"Error : ", str(err)]), 'footer')

    def setup_body(self):
        """
        Body that Will be wrapped in a Frame
        """
        return  urwid.AttrWrap(
                urwid.LineBox(
                urwid.Padding(                                                  #Padd left and right edges
                        urwid.Columns([                                         #Column of Entries
                            ('weight',1.59, urwid.LineBox(
                            ListPopUpLauncher(self.mode_switch_handler,body=urwid.SimpleFocusListWalker(self.gen_walker())),title="Contents")), 
                                urwid.LineBox(
                                    urwid.ListBox([urwid.Text("No Comments",align="center")]),
                                title="Operations")
                        ],1),
                        left=2,right=2) , 
                title="Directory Browser")
                ,"body")

    def mode_switch_handler(self,key):

        """
        Switch between Normal mode for browsing file and Select mode for Checking and Picking Multiple items

        key: widget selected i.e the ListBox in this case
        """
        if(self.is_in_normal_mode):
            #Switch to select mode
            if self.check_sel_cache():
                mode = self.select_mode_walker_cache[self.file_walker.curdir]
            else:
                mode  =   self.selectable_mode(self.file_walker.get_dir_list(hide_dir_changers=True))
                self.select_mode_walker_cache.update({self.file_walker.curdir:mode})
            self.switch_to_mode(key,mode)
        else:
            self.switch_to_mode(key,self.gen_walker())
    
    def check_sel_cache(self):
        """
        Check if the Current directory is in the dict, useful for select mode operations to track 
        Selected Widgets
        """
        if self.select_mode_walker_cache.keys().__contains__(self.file_walker.curdir):
            return True
        return False

    def switch_to_mode(self,key,FocusWalker):
        """
        Switch The listbox Walkers between Select mode and Normal mode

        key : Widget in question :Listbox
        FocusWalker: new MonitoredList to swap
        """
        prev_pos = key.body.get_focus()[1]
        key.body.clear()
        key.body.extend(FocusWalker)
        key.body.set_focus(prev_pos)
        self.is_in_normal_mode = not self.is_in_normal_mode

    def SignalHandler(self,key):
        """
        Handles normal mode button clicks

        key: widget in question :Button
        """
        #TODO: Alter header data
        if self.file_walker.chdir_into(os.path.join(self.file_walker.curdir,key.get_label())):
            self.frame.body.base_widget[0].body.clear() 
            self.frame.body.base_widget[0].body.extend(self.gen_walker())
            self.frame.body.base_widget[0].body.set_focus(0)
            self.frame.header.base_widget[0].set_text(self.file_walker.curdir)

    def get_frame(self):
        """
        Returns TopMostFrame
        """
        if self.frame == None:
            self.frame=urwid.Frame(self.body,self.header,footer=self.get_footer())
        return self.frame

    def select_signal_handler(self,key):
        """
        Handles switching directories while in select mode, all while keeping track of
        selected files or directories
        """
        if self.file_walker.chdir_into(self.file_walker.join_to_cur(key.get_label())):
            selectable_list_box  = self.frame.body.base_widget[0]
            selectable_list_box.body.clear()
            if(self.check_sel_cache()):
                selectable_list_box.body.extend(self.select_mode_walker_cache[self.file_walker.curdir])
            else:
                tracked_item = self.selectable_mode(self.file_walker.get_dir_list(hide_dir_changers=True))
                self.select_mode_walker_cache.update({self.file_walker.curdir:tracked_item })
                selectable_list_box.body.extend(tracked_item)

    def selectable_mode(self,dir_contents=[]):
        """
        Return a Specialized list for use in the Listbox
        """
        traverse_buttons = [urwid.Button('..',on_press=self.select_signal_handler)]
        traverse_buttons.extend([urwid.CheckBox(file_or_dir,on_state_change=self.change_attr) for file_or_dir in dir_contents ])
        return urwid.MonitoredFocusList(traverse_buttons)

    def msg_to_footer(self,msg):
        """
        Alters contents of the footer with a Text message
        """
        self.frame.footer=urwid.AttrMap(urwid.Text(str(msg)),'footer')

    def change_attr(self,key,data):
        """
        Allows for highlighting selected items in the current directory while in select mode
        however it is temporary 
        key  : The widget in focus 
        data : The current value for the widget
        """
        if(data):
            self.msg_to_footer(str((key,data)))
            key = urwid.AttrMap(key,'footer')
            self.swap_widget_at_focus(key)
        else:
            self.msg_to_footer(str((key,data)))
            key = urwid.AttrMap(key,'body')
            self.swap_widget_at_focus(key)

    def get_footer(self):
        """
        Creates a footer with information of current disk usage
        """
        du = self.file_walker.get_disk_usage()
        return urwid.AttrMap(urwid.Text(du['used'] + '/' + du['total'],align='right'),'footer')

    def swap_widget_at_focus(self,key):
        pos = self.frame.body.base_widget[0].focus_position
        self.frame.body.base_widget[0].body[pos] = key
    



class PopupItemInstance(urwid.WidgetWrap):
    signals = ['close']
    """
    Show Some stat information about file under cursor
    TODO: Make this have more functionality with either Show stat info or Some other plugin 
    e.g JSON export, XML export etc
    """

    def __init__(self,path):
        close_b = urwid.Button("close")
        urwid.connect_signal(close_b,"click",lambda stub : self._emit("close"))
        items = [urwid.Text( key , align="left") for key in path.keys()]
        itema = [urwid.Text(str(value),align="right") for value in path.values()]
        pile = urwid.Pile(
                items
            )
        pile_b = urwid.Pile(itema)

        filler = urwid.Filler(
                urwid.LineBox(
                urwid.Pile([
                    urwid.Divider(div_char="="),
                    urwid.Padding( 
                        urwid.Columns([
                            pile,
                            pile_b
                            ]),left=1,right=1),
                        urwid.Divider(div_char="="),
                        urwid.AttrMap(close_b,'green'),
                        urwid.Divider()
                        ]),
                title="Stats")
                )
        super(PopupItemInstance,self).__init__(urwid.AttrWrap(filler,'popupbg'))

class ListPopUpLauncher(urwid.PopUpLauncher):
    """
    Allows the Listbox to show Popups
    """
    def __init__(self,handler_func,*args,**kwargs):
        super(ListPopUpLauncher,self).__init__(CustomListBox(*args,**kwargs).create_pop_up_bridge(self))
        urwid.connect_signal(self.base_widget,'toggle-select',handler_func)

    def create_pop_up(self):
        """
        Override method to create a popup
        """
        pp = FileOperationsDialog(".",self)
        urwid.connect_signal(pp,'exit',self.close_pop_up())
        return pp

    def get_pop_up_parameters(self):
        """
        Override method to return layout parameters
        """
        return {'left':4,'top':3  , 'overlay_width':36,'overlay_height':7 } 



class FileOperationsDialog(urwid.WidgetWrap):
    signals = ['exit']

    """A dialog box Encapsulating all the Basic Available File Operations"""

    def __init__(self,path,bridge):
        self.bridge = bridge
        close_butt = urwid.Button('exit')
        json_b =  urwid.Button('Export to JSON')
        urwid.connect_signal(json_b,'click',self.json_exp)
        urwid.connect_signal(close_butt,'click',lambda x:self.bridge.close_pop_up()) 
        """
        ^
        |

        Issues with Weakreferences being GC'd early therfore signals not working,
        Not sure what todo
        """
        widg = urwid.Filler(
                urwid.LineBox(
                    urwid.Pile(
                        [json_b,
                            close_butt]
                        )
                    ,title="File operations"
                    )
                )
        self.base_path = path
        super(FileOperationsDialog,self).__init__(urwid.AttrWrap(widg,'popupbg'))


    def json_exp(self,caller):
        exp_json = JSONExporter(self.base_path)
        with open('dir_struct.json','w') as out_file:
            exp_json.dump(out_file)
       



class PopupableListItemButton(urwid.PopUpLauncher):
    """
    Attached to any Button which when clicked

    TODO: Inflate some sort of button and watch out for its click signal,
            Create An abstraction for separate popups
    """

    def __init__(self,choice_item,handler_func,walker):
        self.file_walker_ref = walker 
        super(PopupableListItemButton,self).__init__(ListItemButton(choice_item).attach_to_handler(handler_func).create_pop_up_bridge(self))

    def create_pop_up(self):
        """Inflate a new list with items desired 
        """
        popup = PopupItemInstance(self.file_walker_ref.get_stat_info(self.file_walker_ref.join_to_cur(self.item_label)))
        urwid.connect_signal(popup,'close',lambda stub :self.close_pop_up())
        return popup

    def open_pop_up(self,stat_file_or_dir,keypress):
        """
        """
        self.cur_key = keypress
        self.item_label = stat_file_or_dir
        super(PopupableListItemButton,self).open_pop_up()
        

    def get_pop_up_parameters(self):
        """
        return dict with parameters for new pop up renderinng -- see ref
        """
        return {'left':6,'top':1,'overlay_width':36,'overlay_height':9 } 

class ListItemButton(urwid.Button):

    """Customized Button for the Listwidget able to respond to various input, and make popups"""

    def create_pop_up_bridge(self,bridge):
        self.pop_up_bridge = bridge
        return self


    def attach_to_handler(self,handler_func):
        urwid.connect_signal(self,'click',handler_func)
        return self

    def keypress(self, size, key):
        """Set Customized Actions for diff Keys e.g, Chdir or POpup

        :size: TODO
        :key: TODO
        :returns: TODO

        """
        if key in ('p' or 'P'):
            #TODO:Inflate some sort of submenu here!!
            return self.pop_up_bridge.open_pop_up(self.label,key)
        else:
            return super(ListItemButton,self).keypress(size,key)


class PyTree(object):

    """Main Entry point for the Application, Sets up the Loop
    and inflates the Widgets"""

    def __init__(self,view_holder,paletteInflator):
        """TODO: to be defined1. 
        Retrieve our palette, Build our View
        """
        self.palette = paletteInflator.palette
        self.view = view_holder

    def exit_handler(self,keybutton):
        if keybutton in ('q','Q'):
            raise urwid.ExitMainLoop()
        elif keybutton in ('h','H'):
            pass
            #TODO: Show some mappings
            #bt =urwid.AttrWrap(urwid.BigText(u"Quit",urwid.Thin6x6Font()),'popupbg');
            #prev_w = self.loop.widget
            #self.loop.widget = urwid.Overlay(bt,prev_w,"center",None,'middle',None)

    def run(self):
        self.loop = urwid.MainLoop(self.view,self.palette,pop_ups=True,unhandled_input=self.exit_handler)
        self.loop.run()

if __name__ == "__main__":
    paletteInflator = PaletteInflator();
    paletteInflator.palette = [
        ('header','black','white','bold'),
        ('body','white','dark blue','bold'),
        ('reversed','standout',''),
        ('footer','black','white','underline'),
        ('popupbg','white','dark red',''),
        ('bold','black','white',''),
        ('green','black','dark green',('bold','standout')),
        ('directory','white','dark blue'),
        ('file','black','dark blue')
        ]
    tree = PyTree(ViewBuilder().get_frame(),paletteInflator)
    tree.run()
