"""

Basic File and Directory operations are managed here


"""


class FileOperationsManager(object):

    """Manages instances of FileOperations , typically a singleton"""

    def __init__(self,op_insts=[],err_msg_callback=None):
        """TODO: to be defined1. """
        self.file_ops_instances = op_insts
        self.on_err = err_msg_callback

    def execute(self):
        """Execute and Clear all available operation instances
        :returns: TODO

        """
        pass

class BaseOperation(object):

    """A common base class for all file Operations"""

    def __init__(self,dir_items=[]):
        """TODO: to be defined1. """
        self.paths = dir_items

    def run_operation(self):
        """
        Please override this method to define your operation
        """
        raise Exception('Unimplemented')


