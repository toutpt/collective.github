from zope import interface

class IGithubLayer(interface.Interface):
    """browser layer"""

#dependencies
try:
    #plone4
    from Products.ATContentTypes.interfaces.link import IATLink as ILink
except ImportError, e:
    from collective.github import logger
    logger.info('BBB: switch to plone3 %s'%e)
    #plone3
    from Products.ATContentTypes.interface import IATLink as ILink
