from xml.etree import ElementTree as XmlET
from xml.etree import ElementInclude


class DoctypeSafeCallbackTarget(XmlET.TreeBuilder):
    # Handle deprecation warning for parsing a file with DOCTYPE.

    def doctype(*args):
        pass


class CommentedTreeBuilder(XmlET.TreeBuilder):
    # Python 2.7 uses ElementTree 1.3.x.

    def comment(self, data):
        self.start(XmlET.Comment, {})
        self.data(data)
        self.end(XmlET.Comment)


def parse_xml(file_name, lh, include_comments=False):
    """Returns a parsed xml tree with comments intact."""
    fh = open(file_name, 'r')
    try:
        if include_comments:
            tree = XmlET.parse(fh, parser=XmlET.XMLParser(target=CommentedTreeBuilder()))
        else:
            tree = XmlET.parse(fh, parser=XmlET.XMLParser(target=DoctypeSafeCallbackTarget()))
    except Exception, e:
        fh.close()
        lh.write("Exception attempting to parse %s:\n%s\n\n" % (file_name, str(e)))
        return None
    fh.close()
    root = tree.getroot()
    ElementInclude.include(root)
    return tree
