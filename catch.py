import os
import os.path
import requests
import re
import ConfigParser
#from HTMLParser import HTMLParser

class GetCaoliuPic(object):
    """docstring for ClassName"""
    def __init__(self):
        super(GetCaoliuPic, self).__init__()
        self.max = None
        # sample: <img src="http://ww1.sinaimg.cn/mw600/005vbOHfgw1eohghggdpjj30cz0ll0x5.jpg" style="max-width: 486px; max-height: 450px;">
        #self.ImgRegex = r'<p><img[^>]*?src\s*=\s*["\']?([^\'" >]+?)[ \'"][^>]*?></p>'
        self.ImgRegex = r'<input\s*type=\'image\'\s*src\s*=\s*["\']?([^\'" >]+?)[ \'"]'
        self.ThreadsRegex = r'<h3><a\s*href\s*=\s*["\']?([^\'">]+?)[ \'"][^>]*?>(<font color=green>)?[^<]*(</font>)?</a></h3>'
        self._isUrlFormat = re.compile(r'https?://([\w-]+\.)+[\w-]+(/[\w\- ./?%&=]*)?');
        self._path = self.DealDir("Images")
        self.currentDir = ""
        self.cf = ConfigParser.ConfigParser()
        self.pageNum = 1
        self.isMono = True

        if not os.path.exists('config'):
            print('No config file. Creating a default one.')
            self.SetDefaultConfig();
        self.LoadConfig()

        print("===============   start   ===============");
        i = self.pageNum
        print("===============   loading page {0}   ===============".format(i))
        self.DoFetch(i)
        print("===============   end   ===============")

    def LoadConfig(self):
        self.cf.read("config")
        self.pageNum = self.cf.getint('web','page')
        self.isMono = self.cf.getboolean('file','mono')

    def SetDefaultConfig(self):
        self.cf.add_section('web')
        self.cf.set('web','page','1')
        self.cf.add_section('file')
        self.cf.set('file','mono','true')
        with open('config', 'wb') as configfile:
            self.cf.write(configfile)

    def DealDir(self, path):
        if not os.path.exists(path):
            os.mkdir(path);
            return path;

    def DoFetch(self, pageNum):
        response = requests.get("http://wo.yao.cl/thread0806.php?fid=16&search=&page={0}".format(pageNum))
        # request.Credentials = CredentialCache.DefaultCredentials;

        if response.status_code != 200: return;
        # stream = response.GetResponseStream();
        if len(response.text) == 0: return;
        #print response.text;
        self.FetchThreadsLinks(response.text);

    def FetchThreadsLinks(self, htmlSource):
        prog = re.compile(self.ThreadsRegex, re.IGNORECASE)
        matchesThreads = prog.findall(htmlSource)
        for href in matchesThreads:
            if self.CheckThreadsValid(href) is True:
                #print href[0]
                threadurl = "http://wo.yao.cl/" + href[0]
                print(threadurl)
                self.currentDir = href[0].split('/')[-3] + href[0].split('/')[-2] + href[0].split('/')[-1]
                self.currentDir = self.currentDir.split('.')[-2]
                print(self.currentDir+'/')
                self.FetchImageLinks(threadurl)

    def CheckThreadsValid(self, href):
        return href[0][0:8] == "htm_data"

    def FetchImageLinks(self, threadurl):
        response = requests.get(threadurl)
        if response.status_code != 200: return;
        if len(response.text) == 0: return;
        #print response.text;
        self.FetchLinksFromSource(response.text);

    def FetchLinksFromSource(self, htmlSource):
        prog = re.compile(self.ImgRegex, re.IGNORECASE)
        matchesImgSrc = prog.findall(htmlSource)
        for href in matchesImgSrc:
            if not self.CheckIsUrlFormat(href):
                #print href
            #else:
                continue;
            self.download_file(href)

    def CheckIsUrlFormat(self, value):
        return self._isUrlFormat.match(value) is not None

    def download_file(self, url):
        local_filename = ""
        if self.isMono:
            local_filename = "Images/"+ url.split('/')[-1]
        else:
            self.DealDir("Images/" + self.currentDir)
            local_filename = "Images/" + self.currentDir + '/' + url.split('/')[-1]
        if os.path.exists(local_filename):
            print('\t skip '+local_filename)
            return
        else:
            print('\t=>'+local_filename)
            # NOTE the stream=True parameter
            r = requests.get(url, stream=True)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
            return local_filename

if __name__ == '__main__':
    g = GetCaoliuPic()
