from xml.etree import cElementTree
from core import arguments
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.helpers import get_filter, get_filter_api
from core.validator import validate_filter_parameters, validate_parameter
from copy import deepcopy
import core.config.config
import logging

logger = logging.getLogger(__name__)


class Filter(ExecutionElement):

    def __init__(self, action=None, xml=None, parent_name='', args=None, ancestry=None):
        """Initializes a new Filter object. A Filter is used to filter input into a workflow.
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            action (str, optional): The action name for the filter. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            ancestry (list[str], optional): The ancestry for the Filter object. Defaults to None.
        """
        if xml is not None:
            self._from_xml(xml, parent_name, ancestry)
        else:
            if action is None:
                raise ValueError('Action or xml must be specified in filter constructor')
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            self.args_api, self.data_in_api = get_filter_api(self.action)
            args = args if args is not None else {}
            self.args = validate_filter_parameters(self.args_api, args, self.action)

    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a Filter object. This is needed in case a workflow and/or playbook is renamed.
        
        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)

    def _from_xml(self, xml_element, parent_name=None, ancestry=None):
        self.action = xml_element.get('action')
        ExecutionElement.__init__(self, name=self.action, parent_name=parent_name, ancestry=ancestry)
        self.args_api, self.data_in_api = get_filter_api(self.action)
        args = {arg.tag: arg.text for arg in xml_element.findall('args/*')}
        self.args = validate_filter_parameters(self.args_api, args, self.action)

    def to_xml(self, *args):
        """Converts the Filter object to XML format.
        
        Args:
            args (list[str], optional): A list of arguments to place in the XML.
            
        Returns:
            The XML representation of the Filter object.
        """
        elem = cElementTree.Element('filter')
        elem.set('action', self.action)
        if self.args:
            args_element = cElementTree.SubElement(elem, 'args')
            for arg_name, arg_value in self.args.items():
                element = cElementTree.Element(arg_name)
                element.text = arg_value
                args_element.append(element)
        return elem

    def __call__(self, output=None):
        try:
            args = deepcopy(self.args)
            output = validate_parameter(output, self.data_in_api, 'Flag {0}'.format(self.action))
            args.update({self.data_in_api['name']: output})
            result = get_filter(self.action)(**args)
            callbacks.FilterSuccess.send(self)
            return result
        except Exception as e:
            callbacks.FilterError.send(self)
            logger.error('Filter {0} encountered an error: {1}'.format(self.action, str(e)))
            return output

    def __repr__(self):
        output = {'action': self.action,
                  'args': self.args}
        return str(output)

    def as_json(self):
        """Gets the JSON representation of a Filter object.
        
        Returns:
            The JSON representation of a Filter object.
        """
        return {"action": self.action,
                "args": self.args}

    @staticmethod
    def from_json(json, parent_name='', ancestry=None):
        """Forms a Filter object from the provided JSON object.
        
        Args:
            json (JSON object): The JSON object to convert from.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            ancestry (list[str], optional): The ancestry for the new Filter object. Defaults to None.
            
        Returns:
            The Filter object parsed from the JSON object.
        """
        out_filter = Filter(action=json['action'],
                            args=json['args'],
                            parent_name=parent_name,
                            ancestry=ancestry)
        return out_filter

    def get_children(self, ancestry):
        """Gets the children Filters of the Flag in JSON format.
        
        Args:
            ancestry (list[str]): The ancestry list for the Filter to be returned.
            
        Returns:
            Empty dictionary {}
        """
        return {}
