import sys
import logging
import os
import os.path
import requests
import re
import ConfigParser

def success(val): return val,None
def error(why): return None,why
def get_val(m_val): return m_val[0]
def get_error(m_val): return m_val[1]

class GetCaoliuPic(object):
    """docstring for ClassName"""
    def __init__(self):
        super(GetCaoliuPic, self).__init__()

        self.ImgRegex = r'<input\s*type=\'image\'\s*src\s*=\s*["\']?([^\'" >]+?)[ \'"]'
        self.ThreadsRegex = r'<h3><a\s*href\s*=\s*["\']?([^\'">]+?)[ \'"][^>]*?>(?:<font color=green>)?[^<]*(?:</font>)?</a></h3>'
        self._isUrlFormat = re.compile(r'https?://([\w-]+\.)+[\w-]+(/[\w\- ./?%&=]*)?');
        self._path = self.DealDir("Images")
        self.currentDir = ""
        self.cf = ConfigParser.ConfigParser()
        self.pageNum = 1
        self.isMono = True
        self.numToDownload = -1
        self.loggingFile = 'log.txt'
        self.retryTimes = 5
        self.caoliudomain = 'example.com'

        if not os.path.exists('config'):
            print('No config file. Creating a default one.')
            self.SetDefaultConfig();
        self.LoadConfig()

        #init logging file
        logging.basicConfig(filename = os.path.join(os.getcwd(), self.loggingFile), level = logging.WARN, filemode = 'w', format = '%(asctime)s - %(levelname)s: %(message)s')

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
        self.loggingFile = self.cf.get('basic','log_file')
        self.retryTimes = self.cf.getint('web','retry_times')
        self.caoliudomain = self.cf.get('web','domain')

    def SetDefaultConfig(self):
        self.cf.add_section('basic')
        self.cf.set('basic','log_file','log.txt')
        self.cf.add_section('web')
        self.cf.set('web','page','1')
        self.cf.set('web','num_to_download','-1')
        self.cf.set('web','retry_times','5')
        self.cf.set('web','domain','example.com')
        self.cf.add_section('file')
        self.cf.set('file','mono','true')
        with open('config', 'wb') as configfile:
            self.cf.write(configfile)

    def DealDir(self, path):
        if not os.path.exists(path):
            os.mkdir(path);
            return path;

    def FetchHtml(self, url):
        retry = 0
        while True:
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    return error("Failed to fetch html. CODE:%i" % response.status_code)
                elif (response.text) == 0:
                    return error("Empty html.")
                else:
                    return success(response.text)
            except requests.ConnectionError:
                if retry<self.retryTimes:
                    retry+=1
                    print('Can\'t retrive html. retry %i' % retry)
                    continue
                logging.error('Can not connect to %s' % url)
                return error("The server is not responding.")

    def DoFetch(self, pageNum):
        res = self.FetchHtml("http://"+self.caoliudomain+"/thread0806.php?fid=16&search=&page={0}".format(pageNum))
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
                threadurl = 'http://'+self.caoliudomain+'/' + href
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
            res = self.download_file(href)
            if get_error(res):
                print(get_error(res))

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
            return error('\t skip '+local_filename)
        else:
            print('\t=>'+local_filename)
            # NOTE the stream=True parameter
            retry = 0
            while True:
                try:
                    r = requests.get(url, stream=True)
                    break
                except requests.ConnectionError:
                    if retry<self.retryTimes:
                        retry+=1
                        print('\tCan\'t retrive image. retry %i' % retry)
                        continue
                    logging.error('Can not connect to %s' % url)
                    return error('The server is not responding.')
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
            return success(local_filename)

if __name__ == '__main__':
    g = GetCaoliuPic()
