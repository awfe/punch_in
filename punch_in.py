#!/usr/bin/python3
# -*- coding: utf-8 -*-

from wxpy import *
import re
import json
import datetime
import operator
import traceback

TARGET_GROUP_NAME = '盛安德打卡群（20160203）'
# TARGET_GROUP_NAME = '测试群'
KEY = '05292ac218ba4248a37c1cec9a320937'

bot = Bot(cache_path=True, console_qr=2)

bot.enable_puid()

tuling = Tuling(api_key=KEY)

target_group = ensure_one(bot.groups().search(TARGET_GROUP_NAME))

# hub = ensure_one(target_group.search('胡斌'))

record = {}

fp = open('record.json', 'r')
record = json.load(fp)
fp.close()


def save():
    with open('record.json', 'w') as fp:
        json.dump(record, fp, indent=4)


def remove_entry(msg_body, name, puid):
    date_string = datetime.datetime.now().strftime("%Y-%m-%d")
    record_today = record[date_string]
    record_today.pop(puid)


def add_new_entry(msg_body, name, puid):
    date_string = datetime.datetime.now().strftime("%Y-%m-%d")
    if not record.get(date_string):
        record[date_string] = {}
    record[date_string][puid] = {'name': name, 'msg': msg_body}


def determine_msg(msg):
    print(msg)

    # name = msg.member.name
    name = msg.member.nick_name
    #puid = None
    puid = msg.member.puid
    msg_body = re.sub('@[^\s]*', '', msg.text).strip()

    msg_body_for_key_word_checking = re.sub(u'[^\u4e00-\u9fa5]+$', '', msg_body).strip()

    if msg_body_for_key_word_checking.endswith('打卡'):

        if msg_body_for_key_word_checking.endswith('不打卡'):
            return '不打卡别捣乱😎'
        if msg_body_for_key_word_checking.endswith('没打卡'):
            return '别问我，自己用"列表"命令查询🤣'
        add_new_entry(msg_body, name, puid)
        save()
        return '{}已经打卡👍\n打卡内容: {}'.format(name, msg_body)

    elif msg_body_for_key_word_checking.endswith('请假') and not msg_body_for_key_word_checking.endswith('不请假'):

        add_new_entry(msg_body, name, puid)
        save()
        return '{}请假了👌'.format(name)

    elif msg_body_for_key_word_checking == '撤销':

        remove_entry(msg_body, name, puid)
        save()
        return '{}的打卡已经撤销👌'.format(name)

    elif msg_body_for_key_word_checking == '列表':

        date_string = datetime.datetime.now().strftime("%Y-%m-%d")
        if not record.get(date_string):
            return '今天还没有人打卡😕'

        record_list = [date_string]
        index = 1
        for uid, value in record.get(date_string).items():
            record_list.append('{}. {}: {}'.format(index, value['name'], value['msg']))
            index += 1
        return '\n'.join(record_list)

    elif msg_body_for_key_word_checking == '记录' or msg_body_for_key_word_checking == '本周':

        members = msg.sender.members

        uid_count_dict = {}
        uid_name_dict = {}

        today = datetime.date.today()
        weekday = today.weekday()

        for delta in range(0, weekday + 1):
            date_string = (today - datetime.timedelta(delta)).strftime("%Y-%m-%d")
            if record.get(date_string):
                for uid in record.get(date_string).keys():
                    uid_name_dict[uid] = record.get(date_string)[uid]['name']
                    uid_count_dict[uid] = uid_count_dict.get(uid, 0) + 1

        sorted_record = sorted(uid_count_dict.items(), key=operator.itemgetter(1), reverse=True)

        record_list = ['本周记录：', '']
        index = 1

        for uid, value in sorted_record:
            record_list.append('{}. {}: 共打卡{}天'.format(index, uid_name_dict[uid], value))
            index += 1

        no_record = len(members) - 1 - len(sorted_record)
        if no_record > 0:
            record_list.append('')
            record_list.append('还有{}人尚未打卡'.format(no_record))

        return '\n'.join(record_list)
    else:
        return tuling.reply_text(msg, at_member=True)


@bot.register(target_group)
def receive_message_in_group(msg):
    if msg.is_at:

        if msg.type != TEXT:
            return '你发的我看不懂🤔'

        try:
            text = determine_msg(msg)
        except:
            print(traceback.format_exc())
            return ''

        return text


bot.join()

# # 堵塞线程
# embed()
