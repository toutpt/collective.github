import urllib2
import json
import feedparser

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope import interface

GITHUB_URL = "https://github.com/"
BASE_URL = GITHUB_URL+"api/v2/json/"

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
        if not urlInfo['repo']:
            urlInfo['repo'] = self.request.get('github_repo',None)
        if urlInfo['repo']:
            return self.context.restrictedTraverse('github_repo.html')()
        return self.context.restrictedTraverse('github_user.html')()


class GithubLink(BrowserView):
    """Github view helper"""
    interface.implements(IGithubView)

    user_info_tile = ViewPageTemplateFile('user_info_tile.pt')
    user_public_repositories_tile = ViewPageTemplateFile('user_public_repositories_tile.pt')
    user_public_activity_tile = ViewPageTemplateFile('user_public_activity_tile.pt')
    repo_commits_tile = ViewPageTemplateFile('repo_commits_tile.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.url = self.context.getRemoteUrl()
        self.urlInfo = githubUrlInfo(self.url)
        self.isOrganisation = False
        if self.urlInfo['repo'] is None:
            #try to get it from the request
            self.urlInfo['repo'] = self.request.get('github_repo',None)

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
        jsonInfo = urllib2.urlopen(BASE_URL+'repos/show/'+user).read()
        info = json.loads(jsonInfo, 'utf-8')
        info = info[u'repositories']
        self.stay_in_plone(info)
        return info

    def stay_in_plone(self, repositories):
        for repository in repositories:
            new_url = self.context.absolute_url()+'?github_repo='+repository['name']
            repository['url'] = new_url

    def activities(self):
        #['updated', 'published_parsed', 'subtitle', 'updated_parsed', 'links',
        #'title', 'author', 'thumbnail', 'content', 'title_detail', 'href', 
        #'link', 'published', 'author_detail', 'id']
        user = self.urlInfo['user']
        feed = feedparser.parse("https://github.com/%s.atom"%user)
        return feed['entries']

    def repo_info(self):
        #https://github.com/api/v2/json/repos/show/toutpt/collective.github
        user = self.urlInfo['user']
        repo = self.urlInfo['repo']
        jsonInfo = urllib2.urlopen(BASE_URL+'repos/show/%s/%s'%(user,repo)).read()
        info = json.loads(jsonInfo)
        info = info['repository']
        return info

    def repo_links(self):
        user = self.urlInfo['user']
        repo = self.urlInfo['repo']
        url = GITHUB_URL + user + '/'+repo
        links = []
        links.append({'title':"Source",       'url':url})
        links.append({'title':"Commits",      'url':url+'/commits/master'})
        links.append({'title':"Network",      'url':url+'/network'})
        links.append({'title':"Pull requests",'url':url+'/pulls'})
        links.append({'title':"Issues",       'url':url+'/issues'})
        links.append({'title':"Graphs",       'url':url+'/graphs'})
        links.append({'title':"Repo HTTP",    'url':url+'.git'})
        links.append({'title':"Repo Git RO",  'url':'git://github.com/%s/%s.git'%(user, repo)})
        return links

    def commits(self):
        #commits/list/:user_id/:repository/:branch
        user = self.urlInfo['user']
        repo = self.urlInfo['repo']
        if not repo:
            return []
        jsonInfo = urllib2.urlopen(BASE_URL+'commits/list/%s/%s/master'%(user,repo)).read()
        info = json.loads(jsonInfo)
        info = info['commits']
        return info
