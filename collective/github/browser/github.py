from Products.Five import BrowserView
from zope import interface
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class IGithubView(interface.Interface):
    """Github view helper"""
    
    def user_info_tile():
        """Return html of the user info tile"""
    
    def user_public_repositories_tile():
        """Return html of the repository """

    def user_public_activity_tile():
        """Return html of the user activity"""

def isGithubUrl(url):
    """Return True if it is a github url"""
    return url.startswith("https://github.com/") or url.startswith("http://github.com/")

def githubUrlInfo(url):
    res = {}
    splited = url.split('/')
    if splited[-1] == '':splited.pop(-1) #remove traling slash
    res['user'] = splited[3]
    res['repo'] = None
    if len(splited)>4:
        res['repo'] = splited[4]
    return res

class GithubLinkView(BrowserView):
    """Github view over link content type"""

    def __call__(self):
        """call the good template from skin directory to use"""
        url = self.context.getRemoteUrl()
        if not isGithubUrl(url):
            self.request.response.redirect(self.context.absolute_url()+"/link_view")
            return ""
        urlInfo = githubUrlInfo(url)
        if urlInfo['repo']:
            return self.context.restrictedTraverse('github_repo.html')()
        return self.context.restrictedTraverse('github_user.html')()

import urllib2
import json
import feedparser
BASE_URL = "https://github.com/api/v2/json/"

class GithubLink(BrowserView):
    """Github view helper"""
    interface.implements(IGithubView)
    tpl_user_info_tile = ViewPageTemplateFile('user_info_tile.pt')
    tpl_user_public_repositories_tile = ViewPageTemplateFile('user_public_repositories_tile.pt')
    tpl_user_public_activity_tile = ViewPageTemplateFile('user_public_activity_tile.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.url = self.context.getRemoteUrl()
        self.urlInfo = githubUrlInfo(self.url)
        self.isOrganisation = False

    def user_info(self):
        user = self.urlInfo['user']
        if not self.isOrganisation:
            try:
                jsonUserInfo = urllib2.urlopen(BASE_URL+'user/show/'+user).read()
            except urllib2.HTTPError, e:
                self.isOrganisation = True

        if self.isOrganisation:
            jsonUserInfo = urllib2.urlopen(BASE_URL+'organizations/'+user).read()

        userInfo = json.loads(jsonUserInfo, 'utf-8')
        userInfo = userInfo[u'user']
        return userInfo

    def repositories(self):
        user = self.urlInfo['user']
        jsonInfo = urllib2.urlopen(BASE_URL+'repos/watched/'+user).read()
        info = json.loads(jsonInfo, 'utf-8')
        info = info[u'repositories']
        return info

    def activities(self):
        #['updated', 'published_parsed', 'subtitle', 'updated_parsed', 'links',
        #'title', 'author', 'thumbnail', 'content', 'title_detail', 'href', 
        #'link', 'published', 'author_detail', 'id']
        user = self.urlInfo['user']
        feed = feedparser.parse("https://github.com/%s.atom"%user)
        return feed['entries']

    def user_info_tile(self):
        return self.tpl_user_info_tile()

    def user_public_repositories_tile(self):
        return self.tpl_user_public_repositories_tile()

    def user_public_activity_tile(self):
        return self.tpl_user_public_activity_tile()
