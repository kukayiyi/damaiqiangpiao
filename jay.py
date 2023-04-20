import argparse
import os  # 创建文件夹, 文件是否存在
import string
import sys
import threading
import time  # time 计时
import pickle  # 保存和读取cookie实现免登陆的一个工具
from time import sleep
from selenium import webdriver  # 操作浏览器的工具
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import subprocess

"""
一. 实现免登陆
二. 抢票并且下单
"""
# 大麦网主页
damai_url = 'https://www.damai.cn/'
# 登录
login_url = 'https://passport.damai.cn/login?ru=https%3A%2F%2Fwww.damai.cn%2F'
# 抢票目标页
target_url = 'https://m.damai.cn/damai/detail/item.html?itemId=709402698664'
# 场次，第一场填0，第二场填1，以此类推
sku_times = 0
# 票档，同上
sku_tickets = 3
# 数量
sku_number = 4
# 联系人
contact = "习近平"
# 手机号
contact_phone = "18857774314"
# 是否跳过选场，如果提前设置了场次、票档、数量和观影人可以设置跳过，务必注意所有东西都要提前填好，包括联系人
sku_skip = False
# 浏览器调试端口
watch_port = "9222"



# class Concert:
class Concert:
    # 初始化加载
    time_saver = None
    def __init__(self):
        mobile_emulation = {
            "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
            "userAgent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Mobile Safari/537.36"
        }
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:" + watch_port)
        # chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        self.status = 0  # 状态, 表示当前操作执行到了哪个步骤
        self.login_method = 1  # {0:模拟登录, 1:cookie登录}自行选择登录的方式
        self.driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=chrome_options)  # 当前浏览器驱动对象

    # cookies: 登录网站时出现的 记录用户信息用的
    def set_cookies(self):
        """cookies: 登录网站时出现的 记录用户信息用的"""
        self.driver.get(damai_url)
        print('###请点击登录###')
        # 我没有点击登录,就会一直延时在首页, 不会进行跳转
        while self.driver.title.find('大麦网-全球演出赛事官方购票平台') != -1:
            sleep(1)
        print('###请扫码登录###')
        # 没有登录成功
        while self.driver.title != '大麦网-全球演出赛事官方购票平台-100%正品、先付先抢、在线选座！':
            sleep(1)
        print('###扫码成功###')
        # get_cookies: driver里面的方法
        pickle.dump(self.driver.get_cookies(), open('cookies.pkl', 'wb'))
        print('###cookie保存成功###')
        self.driver.get(target_url)

    # 假如说我现在本地有 cookies.pkl 那么 直接获取
    def get_cookie(self):
        """假如说我现在本地有 cookies.pkl 那么 直接获取"""
        cookies = pickle.load(open('cookies.pkl', 'rb'))
        for cookie in cookies:
            cookie_dict = {
                'domain': '.damai.cn',  # 必须要有的, 否则就是假登录
                'name': cookie.get('name'),
                'value': cookie.get('value')
            }
            self.driver.add_cookie(cookie_dict)
        print('###载入cookie###')

    def login(self):
        """登录"""
        if self.login_method == 0:
            self.driver.get(login_url)
            print('###开始登录###')
        elif self.login_method == 1:
            # 创建文件夹, 文件是否存在
            if not os.path.exists('cookies.pkl'):
                self.set_cookies()  # 没有文件的情况下, 登录一下
            else:
                self.driver.get(target_url)  # 跳转到抢票页
                self.get_cookie()  # 并且登录

    def enter_concert(self):
        """打开浏览器"""
        print('###打开浏览器,进入大麦网###')
        # 调用登录
        # self.login()  # 先登录再说
        self.driver.get(target_url)
        # self.driver.refresh()  # 刷新页面
        self.status = 2  # 登录成功标识
        print('###登录成功###')
        # 处理弹窗
        if self.isElementExist('/html/body/div[2]/div[2]/div/div/div[3]/div[2]'):
            self.driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div/div[3]/div[2]').click()

    # 二. 抢票并且下单
    def choose_ticket(self):
        """选票操作"""
        if self.status == 2:
            print('=' * 30)
            print('###开始进行日期及票价选择###')
            while self.driver.title.find("订单确认页") == -1:
                try:
                    buybutton = self.driver.find_element(By.CLASS_NAME, 'buy__button__text').text
                    if '缺货' in buybutton:
                        # self.status = 2  # 没有进行更改操作
                        # self.driver.get(target_url)  # 刷新页面 继续执行操作
                        print("抢票失败了！")
                        sys.exit()
                    elif "立即" in buybutton:
                        # 点击购买，进行选
                        self.driver.find_element(By.CLASS_NAME, 'buy__button').click()
                        sleep(0.1)
                        self.choice_sku('sku-times-card', 'sku-tickets-card')
                        sleep(0.5)

                    elif '即将开抢' in buybutton:
                        if self.time_saver is None:
                            self.time_saver = time.time()
                        elif time.time()-self.time_saver > 60:
                            print("刷新页面..")
                            self.driver.refresh()
                            self.time_saver = None
                        print("还没开卖哦！紧张紧张...别忘了预填所有能填的东西！", end="\r")

                    elif '选座' in buybutton:
                        self.driver.find_element(By.CLASS_NAME, 'buy__button').click()
                        self.status = 5
                    else:
                        self.driver.get(target_url)
                        time.sleep(3)
                except Exception as e:
                    print(e)
                    print('###没有跳转到订单结算界面###')
                title = self.driver.title
                if title == '选座购买':
                    # 选座购买的逻辑
                    self.choice_seats()
                elif title == '订单确认页':
                    # 实现下单的逻辑
                    while True:
                        # 如果标题为确认订单
                        self.check_order()
                        print('正在加载.......')
                        if self.time_saver is None:
                            self.time_saver = time.time()
                        elif time.time() - self.time_saver >= 3:
                            print("刷新页面..")
                            self.driver.refresh()
                            self.time_saver = None
                        sleep(0.3)
                        if "付款" in self.driver.title:
                            print("抢票成功,恭喜捏!")
                            sys.exit()


    def choice_sku(self, time_name: str, ticket_name: str):  # 选择场次和票档和数量
        while True:
            try:
                if not sku_skip:
                    print("开始选场次")
                    times = self.driver.find_element(By.CLASS_NAME, time_name)
                    times_elements = times.find_elements(By.CLASS_NAME, "theme-normal")
                    times_elements[sku_times].click()
                    print("选定场次" + str(sku_times))
                    sleep(0.3)

                    print("开始选票档")
                    tickets = self.driver.find_element(By.CLASS_NAME, ticket_name)
                    tickets_elements = tickets.find_elements(By.CLASS_NAME, "theme-normal")
                    tickets_elements[sku_tickets].click()
                    print("选定票档" + str(sku_tickets))
                    sleep(0.3)

                    print("开始选数量")
                    add_num_button = self.driver.find_element(By.CLASS_NAME, "plus-enable")
                    for _ in range(sku_number-1):
                        add_num_button.click()
                        sleep(0.3)

                print("选定数量" + str(sku_tickets))
                self.driver.find_element(By.CLASS_NAME, "sku-footer-buy-button").click()
                break

            except Exception as e:
                print(e)

    def choice_seats(self):
        """选择座位"""
        while self.driver.title == '选座购买':
            while self.isElementExist('//*[@id="app"]/div[2]/div[2]/div[1]/div[2]/img'):
                print('请快速选择你想要的座位!!!')
            while self.isElementExist('//*[@id="app"]/div[2]/div[2]/div[2]/div'):
                self.driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div[2]/div[2]/button').click()

    def check_order(self):
        """下单操作"""
        try:
            # 默认选第一个购票人信息
            # if not sku_skip:
            print("选定观影人...")
            se_buts = self.driver.find_elements(By.CLASS_NAME, "icondanxuan-weixuan_")
            # se_buts.click()s
            for b in se_buts[:4]:
                b.click()
                sleep(0.1)
                # print("填写联系人...")
            # self.driver.find_element(By.XPATH, '//input[@placeholder="请填写联系人姓名"]').send_keys(contact)
            # self.driver.find_element(By.XPATH, '//input[@placeholder="请填写联系人手机号"]').send_keys(contact_phone)
            # sleep(0.9)
            submit = self.driver.find_element(By.XPATH, '//div[@view-name="MColorFrameLayout"]')
            x = submit.location["x"]
            y = submit.location["y"]
            print(str(x) + "," + str(y))
            ActionChains(self.driver).move_by_offset(x, y).click().perform()
            ActionChains(self.driver).move_by_offset(-x, -y).perform()
            # self.driver.execute_script("arguments[0].click();", submit)

        except Exception as e:
            print('###购票人信息选中失败, 自行查看元素位置###')
            print(e)

    def isElementExist(self, element):
        """判断元素是否存在"""
        flag = True
        browser = self.driver
        try:
            browser.find_element(By.XPATH, element)
            return flag
        except:
            flag = False
            return flag

    def finish(self):
        """抢票完成, 退出"""
        self.driver.quit()


def start_chrome():
    cmd = '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\chrome-profile"'
    subprocess.run(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str)
    args = parser.parse_args()
    if args.port is not None:
        watch_port = args.port

    print(f"开始执行！跳过设置信息:{sku_skip},监测浏览器端口:{watch_port}")
    con = Concert()
    try:
        con.enter_concert()  # 打开浏览器
        con.choose_ticket()  # 选择座位
    except Exception as e:
        print(e)
        con.finish()
