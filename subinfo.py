import re
import time
import requests
import telebot
from bs4 import BeautifulSoup
from datetime import datetime
from urllib import parse
from urllib.parse import unquote

API_KEY = "你的bot_token"
bot = telebot.TeleBot(API_KEY)


def botinit():
    bot.delete_my_commands(scope=None, language_code=None)

    bot.set_my_commands(
        commands=[
            telebot.types.BotCommand("subinfo", "查询机场订阅信息"),
            telebot.types.BotCommand("sub", "回复消息查询⬆"),
            telebot.types.BotCommand("dyzh", "转换订阅为clash格式"),
            telebot.types.BotCommand("zh", "回复消息转换⬆"),
            telebot.types.BotCommand("help", "帮助菜单")
        ],
    )
    print('Bot初始化完成')


def get_filename_from_url(url):
    if "sub?target=" in url:
        pattern = r"url=([^&]*)"
        match = re.search(pattern, url)
        if match:
            encoded_url = match.group(1)
            decoded_url = unquote(encoded_url)
            return get_filename_from_url(decoded_url)
    elif "api/v1/client/subscribe?token" in url:
        if "&flag=clash" not in url:
            url = url + "&flag=clash"
        else:
            pass
        try:
            response = requests.get(url)
            header = response.headers.get('Content-Disposition')
            if header:
                pattern = r"filename\*=UTF-8''(.+)"
                result = re.search(pattern, header)
                if result:
                    filename = result.group(1)
                    filename = parse.unquote(filename)
                    airport_name = filename.replace("%20", " ").replace("%2B", "+")
                    return airport_name
        except:
            return '未知'
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) '
                          'Chrome/108.0.0.0'
                          'Safari/537.36'}
        try:
            pattern = r'(https?://)([^/]+)'
            match = re.search(pattern, url)
            base_url = None
            if match:
                base_url = match.group(1) + match.group(2)
            response = requests.get(url=base_url + '/auth/login', headers=headers, timeout=10)
            if response.status_code != 200:
                response = requests.get(base_url, headers=headers, timeout=1)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.title.string
            title = str(title).replace('登录 — ', '')
            if "Attention Required! | Cloudflare" in title:
                title = '该域名仅限国内IP访问'
            elif "Access denied" in title or "404 Not Found" in title:
                title = '该域名非机场面板域名'
            elif "Just a moment" in title:
                title = '该域名开启了5s盾'
            else:
                pass
            return title
        except:
            return '未知'


def convert_time_to_str(time):
    # 时间数字转化成字符串，不够10的前面补个0
    if (time < 10):
        time = '0' + str(time)
    else:
        time = str(time)
    return time


def sec_to_data(y):
    h = int(y // 3600 % 24)
    d = int(y // 86400)
    h = convert_time_to_str(h)
    d = convert_time_to_str(d)
    return d + "天" + h + '小时'


def StrOfSize(size):
    def strofsize(integer, remainder, level):
        if integer >= 1024:
            remainder = integer % 1024
            integer //= 1024
            level += 1
            return strofsize(integer, remainder, level)
        elif integer < 0:
            integer = 0
            return strofsize(integer, remainder, level)
        else:
            return integer, remainder, level

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    integer, remainder, level = strofsize(size, 0, 0)
    if level + 1 > len(units):
        level = -1
    return '{}.{:>03d} {}'.format(integer, remainder, units[level])


def subinfo(url):
    headers = {'User-Agent': 'ClashforWindows/0.18.1'}
    try:
        urls_list = re.findall("https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]", url)
        final_output = []
        for url in urls_list:
            try:
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code == 200:
                    try:
                        info = res.headers['subscription-userinfo']
                        info_num = re.findall('\d+', info)
                        time_now = int(time.time())
                        output_text_head = '订阅链接：`' + url + '`\n机场名：`' + get_filename_from_url(url) + '`\n已用上行：`' + StrOfSize(
                            int(info_num[0])) + '`\n已用下行：`' + StrOfSize(int(info_num[1])) + '`\n剩余：`' + StrOfSize(
                            int(info_num[2]) - int(info_num[1]) - int(info_num[0])) + '`\n总共：`' + StrOfSize(
                            int(info_num[2]))
                        if len(info_num) == 4:
                            timeArray = time.localtime(int(info_num[3]) + 28800)
                            dateTime = time.strftime("%Y-%m-%d", timeArray)
                            if time_now <= int(info_num[3]):
                                lasttime = int(info_num[3]) - time_now
                                output_text = output_text_head + '`\n过期时间：`' + dateTime + '`\n剩余时间：`' + sec_to_data(
                                    lasttime) + '`'
                            elif time_now > int(info_num[3]):
                                output_text = output_text_head + '`\n此订阅已于`' + dateTime + '`过期！'
                        else:
                            output_text = output_text_head + '`\n到期时间：`没有说明`'
                    except:
                        output_text = '订阅链接：`' + url + '`\n机场名：`' + get_filename_from_url(url) + '`\n无流量信息'
                else:
                    output_text = '订阅链接：`' + url + '`\n无法访问\n'
            except:
                output_text = '订阅链接：`' + url + '`\n连接错误\n\n'
            final_output.append(output_text + '\n\n')
        return ''.join(final_output)
    except:
        return '参数错误'


def subzh(url):
    try:
        message_raw = url
        final_output = []
        urls_list = re.findall("https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]", message_raw)  # 使用正则表达式查找订阅链接并创建列表
        if len(urls_list) == 0:
            return '未查找到有效订阅'
        for url in urls_list:
            try:
                if "sub?target=" in url:
                    output_text = f'{url}\n该订阅已被转换过，不支持再次转换!'
                else:
                    ss = parse.quote_plus(url)
                    output_text = "https://api.183tk.tk/sub?target=clash&url=" + ss + '&emoji=true'
            except:
                raise RuntimeError('网络错误，请重新尝试')
            final_output.append(output_text + '\n\n')
        return ''.join(final_output)
    except:
        return '参数错误'


@bot.message_handler(commands=['start'], func=lambda message: message.chat.type == "private")
def start(message):
    bot.send_message(message.chat.id, f"您好`{message.from_user.first_name}`，您可以使用我来查询机场订阅信息，也可以使用我来转换订阅为clash格式",
                     parse_mode='Markdown')


@bot.message_handler(commands=["help"])
def help(message):
    back_msg = bot.send_message(message.chat.id, f" /subinfo <订阅链接>，查询流量\n"
                                                 f" /sub[空格] 回复一条消息，查询流量\n"
                                                 f" /dyzh[空格] 订阅链接，订阅转换\n"
                                                 f" /zh[空格] 回复一条消息将其转换为clash格式\n"
                                                 f" /ping 检查机器人是否工作")
                                                 f"如有bug请向 @fffffx2 反馈"
    time.sleep(15)
    try:
        bot.delete_message(message.chat.id, back_msg.id, timeout=3)
    except:
        return


@bot.message_handler(commands=['subinfo'])
def get_subinfo(message):
    back_msg = bot.send_message(message.chat.id, f" `---正在查询--->`", disable_notification=True,
                                parse_mode='Markdown')
    info_text = subinfo(message.text)
    try:
        bot.delete_message(message.chat.id, back_msg.id, timeout=3)
        bot.reply_to(message, info_text, parse_mode='Markdown')
    except:
        bot.delete_message(message.chat.id, back_msg.id, timeout=3)
        return


@bot.message_handler(commands=['sub'])
def get_sub(message):
    back_msg = bot.send_message(message.chat.id, f" `---正在查询--->`", disable_notification=True, parse_mode='Markdown')
    info_text = subinfo(message.reply_to_message.text)
    try:
        bot.reply_to(message, info_text, parse_mode='Markdown')
        bot.delete_message(message.chat.id, back_msg.id, timeout=3)
    except:
        bot.delete_message(message.chat.id, back_msg.id, timeout=3)
        return


@bot.message_handler(commands=['dyzh'])
def get_subzh(message):
    atext = subzh(message.text)
    bot.reply_to(message, atext)


@bot.message_handler(commands=['zh'])
def get_zh(message):
    if message.reply_to_message is None:
        return
    back_msg = bot.send_message(message.chat.id, f" `---正在转换--->`", disable_notification=True, parse_mode='Markdown')
    info_text = subzh(message.reply_to_message.text)
    try:
        bot.reply_to(message, info_text, parse_mode='Markdown')
        bot.delete_message(message.chat.id, back_msg.id, timeout=3)
    except:
        bot.delete_message(message.chat.id, back_msg.id, timeout=3)
        return


@bot.message_handler(commands=['ping'])
def get_dalay(message):
    start = datetime.now()
    message = bot.reply_to(message, "pong~", disable_notification=True)
    end = datetime.now()
    msg_delay = (end - start).microseconds / 1000
    bot.edit_message_text(f"pong~ | 消息延迟: `{msg_delay:.2f}ms`", message.chat.id, message.id, parse_mode='Markdown')


if __name__ == '__main__':
    botinit()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(15)
