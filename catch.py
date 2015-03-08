import os
import os.path
import requests
import re
import ConfigParser
#from HTMLParser import HTMLParser

def success(val): return val,None
def error(why): return None,why
def get_val(m_val): return m_val[0]
def get_error(m_val): return m_val[1]

class GetCaoliuPic(object):
    """docstring for ClassName"""
    def __init__(self):
        super(GetCaoliuPic, self).__init__()
        self.max = None
        # sample: <img src="http://ww1.sinaimg.cn/mw600/005vbOHfgw1eohghggdpjj30cz0ll0x5.jpg" style="max-width: 486px; max-height: 450px;">
        #self.ImgRegex = r'<p><img[^>]*?src\s*=\s*["\']?([^\'" >]+?)[ \'"][^>]*?></p>'
        self.ImgRegex = r'<input\s*type=\'image\'\s*src\s*=\s*["\']?([^\'" >]+?)[ \'"]'
        self.ThreadsRegex = r'<h3><a\s*href\s*=\s*["\']?([^\'">]+?)[ \'"][^>]*?>(?:<font color=green>)?[^<]*(?:</font>)?</a></h3>'
        self._isUrlFormat = re.compile(r'https?://([\w-]+\.)+[\w-]+(/[\w\- ./?%&=]*)?');
        self._path = self.DealDir("Images")
        self.currentDir = ""
        self.cf = ConfigParser.ConfigParser()
        self.pageNum = 1
        self.isMono = True
        self.numToDownload = -1

        if not os.path.exists('config'):
            print('No config file. Creating a default one.')
            self.SetDefaultConfig();
        self.LoadConfig()

        print("===============   start   ===============");
        i = self.pageNum
        print("===============   loading page {0}   ===============".format(i))
        res = self.DoFetch(i)
        if get_error(res):
            print(get_error(res))
        print("===============   end   ===============")

    def LoadConfig(self):
        self.cf.read("config")
        self.pageNum = self.cf.getint('web','page')
        self.isMono = self.cf.getboolean('file','mono')
        self.numToDownload = self.cf.getint('web','num_to_download')

    def SetDefaultConfig(self):
        self.cf.add_section('web')
        self.cf.set('web','page','1')
        self.cf.set('web','num_to_download','-1')
        self.cf.add_section('file')
        self.cf.set('file','mono','true')
        with open('config', 'wb') as configfile:
            self.cf.write(configfile)

    def DealDir(self, path):
        if not os.path.exists(path):
            os.mkdir(path);
            return path;

    def FetchHtml(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            return error("Failed to fetch html. CODE:%i" % response.status_code)
        elif (response.text) == 0:
            return error("Empty html.")
        else:
            return success(response.text)

    def DoFetch(self, pageNum):
        res = self.FetchHtml("http://wo.yao.cl/thread0806.php?fid=16&search=&page={0}".format(pageNum))
        if get_error(res):
            return res
        html = get_val(res)
        self.FetchThreadsLinks(html);
        return success(0)

    def FetchThreadsLinks(self, htmlSource):
        prog = re.compile(self.ThreadsRegex, re.IGNORECASE)
        matchesThreads = prog.findall(htmlSource)
        num = 0
        for href in matchesThreads:
            if self.CheckThreadsValid(href) is True:
                #print href
                threadurl = "http://wo.yao.cl/" + href
                print('Thread '+str(num + 1)+':'+threadurl)
                self.currentDir = href.split('/')[-3] + href.split('/')[-2] + href.split('/')[-1]
                self.currentDir = self.currentDir.split('.')[-2]
                print(self.currentDir+'/')
                res = self.FetchImageLinks(threadurl)
                if(get_error(res)):
                    print(get_error(res))
                num+=1
                if self.numToDownload>0 and num>=self.numToDownload:
                    break

    def CheckThreadsValid(self, href):
        return href[0:8] == "htm_data"

    def FetchImageLinks(self, threadurl):
        res = self.FetchHtml(threadurl)
        if get_error(res):
            return res
        html = get_val(res)
        self.FetchLinksFromSource(html);
        return success(0)

    def FetchLinksFromSource(self, htmlSource):
        prog = re.compile(self.ImgRegex, re.IGNORECASE)
        matchesImgSrc = prog.findall(htmlSource)
        for href in matchesImgSrc:
            if not self.CheckIsUrlFormat(href):
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
