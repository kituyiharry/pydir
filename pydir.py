#!/usr/bin/env python3

"""
Simple File Directory Browser that i wrote as a Weekend project 


TODO: use shutil for some file operations
"""

import urwid
import os
import stat
from math import log
from  extra.exporters import JSONExporter

class FileWalker(object):

    """Provides a Model for creating a List of current Directory 
        Structure"""

    def __init__(self,on_error):
        """TODO: to be defined1. """
        self.curdir = os.getcwd();
        self.error_callback = on_error
        self.desc_file = ".comments"
        self.has_description = False

    def chdir_into(self,new_dir):
        if os.path.isdir(new_dir):
            try:
                os.chdir(new_dir)
                self.curdir = os.getcwd()
            except Exception as e:
                self.error_callback(str(e))
                return False
            return True
        return False

    def filter_directory(self,item_list=[],hide_hidden=False):
        items = item_list
        if self.desc_file in items:
            self.has_description = True
        if hide_hidden:
            items = [item for item in items if str(item).startswith('.')]
        items.insert(0,".")
        items.insert(1,"..")
        return items




    def get_dir_list(self):
        dir_list = os.listdir(self.curdir)
        return self.filter_directory(dir_list)
    
    def join_to_cur(self,path_append):
        return os.path.join(self.curdir,path_append)

    #Thank you Stack Overflow
    def pretty_size(self,n,pow=0,b=1024,u='B',pre=['']+[p+'i'for p in'KMGTPEZY']):
        pow,n=min(int(log(max(n*b**pow,1),b)),len(pre)-1),n*b**pow
        return "%%.%if %%s%%s"%abs(pow%(-pow-1))%(n/b**float(pow),pre[pow],u)

    def get_stat_info(self,file_or_dir=".",f_sim=True):
        stat_inf =  os.stat(os.path.join( self.curdir,file_or_dir),follow_symlinks=f_sim)
        return  {
                'file-perm':stat.filemode(stat_inf.st_mode) ,'file-size' : self.pretty_size(stat_inf.st_size),   
                'Links'   : stat_inf.st_nlink,'Owner'   : stat_inf.st_uid
        }






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

    """Override for Custom Keypress Actions"""


    def __init__(self,frame_area,*args,**kwargs):
        self.frame_widget = frame_area
        super(CustomListBox,self).__init__(*args,**kwargs)


    def create_pop_up_bridge(self,bridge):
        self.pop_up_bridge = bridge
        return self

    def keypress(self,size,key):

        if key in ('e','E'):
            #TODO : Another Popup
            return self.pop_up_bridge.open_pop_up()
            #return super(CustomListBox,self).keypress(size,key)
        else:
            return super(CustomListBox,self).keypress(size,key)

    def attach_to_frame(self,frame_widget):
        self.frame_widget = frame_widget
        return self
        


class ViewBuilder(object):

    """Sets up the Required View"""

    def __init__(self):
        """Constructor """
        self.file_walker = FileWalker(self.disp_error_msg)
        self.header = self.setup_header()
        self.body = self.setup_body()
        self.frame = None

    def setup_header(self,header_align="left"):
        """
        Creates a Header 
        TODO: Filter text with Ellipsizing long names
        """
        base_dir = self.file_walker.curdir

        self.header = urwid.AttrMap(urwid.Columns(
            [
                urwid.Text(item ,align=header_align) for item in base_dir.split(os.path.sep) 
            ],1
            ),"header")
        return self.header

    def gen_walker(self):
        """Creates a SimpleFocusListWalker
        :returns: TODO
        """
        return  urwid.MonitoredList([
                    urwid.AttrMap(
                        PopupableListItemButton(choice,self.SignalHandler,self.file_walker),
                        None,focus_map="reversed") 
                    for choice in self.file_walker.get_dir_list()
                    ])

    def disp_error_msg(self,err):
        self.frame.footer = urwid.AttrMap(urwid.Text([ u"Error : ", str(err)]), 'footer')

    def setup_body(self):
        """
        Body that Will be wrapped in a Frame
        """
        # return urwid.AttrMap(urwid.SolidFill(),"body")
        # for b in list_items:
            # urwid.connect_signal(b.base_widget,'click',self.SignalHandler)
        # insert a divider top pseudo-padding
        # list_items.insert(0,urwid.Divider())
        return  urwid.AttrWrap(
                urwid.LineBox(
                urwid.Padding(                                                  #Padd left and right edges
                        urwid.Columns([                                         #Column of Entries
                            ('weight',1.39, urwid.LineBox(
                            #urwid.ListBox(
                            ListPopUpLauncher(None,
                                urwid.SimpleFocusListWalker(
                                    self.gen_walker())),title="Contents")), #Our ListBox of Items
                                urwid.LineBox(
                                    urwid.Filler( 
                                        urwid.Text("No Comments",align="center")
                                        ),
                                title="Extra")
                                               #TODO:replace placeholder
                        ],1),left=2,right=2) , title="Directory Browser")
                    ,"body")

    def SignalHandler(self,key):
        #TODO: Alter header data
        if self.file_walker.chdir_into(os.path.join(self.file_walker.curdir,key.get_label())):
            self.frame.body.base_widget[0].body.clear() 
            self.frame.body.base_widget[0].body.extend(self.gen_walker())
            self.frame.body.base_widget[0].body.set_focus(0)
            self.frame.footer = urwid.AttrMap(urwid.Text(["Changed!!" , str(self.frame.body.base_widget[1])]),'footer')
            if self.file_walker.has_description:
                self.frame.body.base_widget[1].set_text("Comments available")

        

    def get_frame(self):
        """
        Returns TopMostFrame
        """
        if self.frame == None:
            self.frame=urwid.Frame(self.body,self.header)
        return self.frame




class PopupItemInstance(urwid.WidgetWrap):
    signals = ['close']
    """
    Show Some stat information
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
                        urwid.AttrMap(close_b,'green')
                        ]),
                title="Stats")
                )
        super(PopupItemInstance,self).__init__(urwid.AttrWrap(filler,'popupbg'))

class ListPopUpLauncher(urwid.PopUpLauncher):

    def __init__(self,*args,**kwargs):
        super(ListPopUpLauncher,self).__init__(CustomListBox(*args,**kwargs).create_pop_up_bridge(self))

    def create_pop_up(self):
        pp = FileOperationsDialog(".",self)
        urwid.connect_signal(pp,'exit',self.close_pop_up())
        return pp

    def get_pop_up_parameters(self):
        return {'left':4,'top':3  , 'overlay_width':36,'overlay_height':9 } 



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
        #with open('dir_struct.json','w') as out_file:
        #    exp_json.dump(out_file)
       








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
        :returns: TODO: Split among to typesof popup dialogs, 1 for stats another for Plugins basis on KeyPress
        """
        popup = PopupItemInstance(self.file_walker_ref.get_stat_info(self.file_walker_ref.join_to_cur(self.item_label)))
        urwid.connect_signal(popup,'close',lambda stub :self.close_pop_up())
        return popup

    def open_pop_up(self,stat_file_or_dir,keypress):
        self.cur_key = keypress
        self.item_label = stat_file_or_dir
        super(PopupableListItemButton,self).open_pop_up()
        

    def get_pop_up_parameters(self):
        """
        return dict with parameters for new pop up renderinng -- see ref
        """
        return {'left':4,'top':1,'overlay_width':36,'overlay_height':8 } 

class ListItemButton(urwid.Button):

    """Customized Button for the Listwidget able to respond to various input"""

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
            #TODO: Show some mappings
            pass


    def run(self):
        loop = urwid.MainLoop(self.view,self.palette,pop_ups=True,unhandled_input=self.exit_handler)
        loop.run()

if __name__ == "__main__":
    paletteInflator = PaletteInflator();
    paletteInflator.palette = [
        ('header','black','white','bold'),
        ('body','white','dark blue','bold'),
        ('reversed','standout',''),
        ('footer','black','dark red','underline'),
        ('popupbg','white','dark red',''),
        ('bold','black','white',''),
        ('green','black','dark green',('bold','standout'))
        ]
    tree = PyTree(ViewBuilder().get_frame(),paletteInflator)
    tree.run()
