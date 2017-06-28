"""
Exporters main duty is to represent a directory structure as XML or Json

TO BE IMPLEMENTED
"""
import os
import json


class BaseExporter(object):

    """A base for Writing Directory structure Exportation formats"""

    def __init__(self,path_name):
        self.pathname = path_name

    def repr_as_dict(self,path):
        base = {'root-name' : os.path.basename(path) }
        if os.path.isdir(path):
            base['type'] = 'Directory'
            base['children'] = [self.repr_as_dict(os.path.join(path,the_dir)) for the_dir in os.listdir(path)]
        else:
            base['type'] = "file"
        return base

        

    def dump(self,out_file):
        raise Exception("Unimplemented")


class JSONExporter(BaseExporter):

    """Export Directory Structure as JSON"""

    def __init__(self,*args):
        super(JSONExporter,self).__init__(*args)

    def dump(self,out_file):
        json.dump(self.repr_as_dict(self.pathname),out_file)
