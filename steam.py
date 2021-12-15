import json
import os
import random
import re
import requests
import time
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger
from PIL import Image, ImageDraw, ImageFont

from . import whois
from .DOTA2_dicts import *
from .utils import *

CONFIG = load_config()
APIKEY = CONFIG['STEAM_APIKEY']
BOT = CONFIG['BOT']
ATBOT = f'[CQ:at,qq={BOT}]'
UNKNOWN = None
IDK = '我不知道'
MAX_ATTEMPTS = 5
MEMBER = os.path.expanduser('~/.Steam_watcher/member.json')
STEAM  = os.path.expanduser('~/.Steam_watcher/steam.json')
IMAGES = os.path.expanduser('~/.Steam_watcher/images/')
DOTA2_MATCHES = os.path.expanduser('~/.Steam_watcher/DOTA2_matches/')

PLAYER_SUMMARY = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={}&steamids={}'
LAST_MATCH = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v001/?key={}&account_id={}&matches_requested=1'
MATCH_DETAILS = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/?key={}&match_id={}'
OPENDOTA_REQUEST = 'https://api.opendota.com/api/request/{}'
OPENDOTA_MATCHES = 'https://api.opendota.com/api/matches/{}'
OPENDOTA_PLAYERS = 'https://api.opendota.com/api/players/{}'

DEFAULT_DATA = {
    'DOTA2_matches_pool': {},
    'players': {},
    'subscribe_groups': [],
    'subscribers': {},
}

class Steam:
    Passive = True
    Active = True
    Request = False

    def __init__(self, **kwargs):
        print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '初始化Steam 开始！')

        self.api = kwargs['bot_api']
        self.whois = whois.Whois(**kwargs)
        self.dota2 = Dota2()
        self.MINUTE = random.randint(0, 59)

        mkdir_if_not_exists(DOTA2_MATCHES)
        self.init_fonts()
        self.init_images()
        if not os.path.exists(STEAM):
            dumpjson(DEFAULT_DATA, STEAM)

        print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '初始化Steam 完成！MINUTE={}'.format(self.MINUTE))


    async def execute_async(self, func_num, message):
        msg = message['raw_message'].strip()
        group = str(message.get('group_id', ''))
        user = str(message.get('user_id', ''))
        if not group:
            return None

        whois_reply = await self.whois.execute_async(message)
        if whois_reply:
            return whois_reply

        if 'steam' in msg.lower() and ('help' in msg.lower() or '帮助' in msg or '说明书' in msg):
            return 'https://docs.qq.com/sheet/DWGFiTVpPS0lkZ2Vv'

        if msg.lower() == '订阅steam':
            steamdata = loadjson(STEAM)
            if group in steamdata['subscribe_groups']:
                return '本群已订阅Steam'
            else:
                steamdata['subscribe_groups'].append(group)
                dumpjson(steamdata, STEAM)
                return '订阅Steam成功'

        if msg.lower() == '取消订阅steam':
            steamdata = loadjson(STEAM)
            if group in steamdata['subscribe_groups']:
                steamdata['subscribe_groups'].remove(group)
                dumpjson(steamdata, STEAM)
                return '取消订阅Steam成功'
            else:
                return '本群未订阅Steam'

        prm = re.match('(怎么)?绑定 *steam(.*)', msg, re.I)
        if prm:
            usage = '使用方法：\n绑定Steam Steam好友代码（8~10位）'
            success = '绑定{}成功'
            try:
                if prm[1]:
                    return usage
                id3 = int(prm[2])
                await self.api.send_group_msg(
                    group_id=message['group_id'],
                    message=f'正在尝试绑定并初始化玩家信息',
                )
                if id3 > 76561197960265728:
                    id3 -= 76561197960265728
                id64 = id3 + 76561197960265728
                id3 = str(id3)
                steamdata = loadjson(STEAM)
                # 之前已经绑定过
                if steamdata['subscribers'].get(user):
                    old_id3 = steamdata['subscribers'][user]
                    if id3 == old_id3:
                        success = f'你已绑定{old_id3}'
                    if old_id3 != id3:
                        steamdata['players'][old_id3]['subscribers'].remove(user)
                        if not steamdata['players'][old_id3]['subscribers']:
                            del steamdata['players'][old_id3]
                        success += f'\n已自动解除绑定{old_id3}'
                steamdata['subscribers'][user] = id3
                if steamdata['players'].get(id3):
                    steamdata['players'][id3]['subscribers'].append(user)
                    steamdata['players'][id3]['subscribers'] = list(set(steamdata['players'][id3]['subscribers']))
                else:
                    now = int(datetime.now().timestamp())
                    gameextrainfo = ''
                    match_id, start_time, action, rank = 0, 0, 0, 0
                    try:
                        try:
                            j = requests.get(PLAYER_SUMMARY.format(APIKEY, id64), timeout=10).json()
                        except requests.exceptions.RequestException as e:
                            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale PLAYER_SUMMARY', e)
                            success += '\nkale'
                            raise
                        p = j['response']['players'][0]
                        if p.get('gameextrainfo'):
                            gameextrainfo = p['gameextrainfo']
                            s1 = p['personaname'] + '现在正在玩' + p['gameextrainfo']
                        else:
                            gameextrainfo = ''
                            s1 = p['personaname'] + '现在没在玩游戏'
                        match_id, start_time = self.dota2.get_last_match(id64)
                        if match_id and start_time:
                            s2 = '最近一场Dota 2比赛编号为{}，开始于{}'.format(
                                match_id,
                                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
                            )
                        else:
                            s2 = '没有查询到最近的Dota 2比赛'
                        name, rank = self.dota2.get_rank_tier(id3)
                        if rank:
                            s3 = '现在是{}{}'.format(PLAYER_RANK[rank // 10], rank % 10 or '')
                        else:
                            s3 = '没有查询到天梯段位'
                        action = max(start_time, now if gameextrainfo == 'Dota 2' else 0)
                        success += '\n{}，{}，{}'.format(s1, s2, s3)
                    except Exception as e:
                        success += '\n初始化玩家信息失败'
                        print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '初始化玩家信息失败', e)
                    steamdata['players'][id3] = {
                        'steam_id64': id64,
                        'subscribers': [user],
                        'gameextrainfo': gameextrainfo,
                        'last_change': now,
                        'last_DOTA2_action': action,
                        'last_DOTA2_match_id': match_id,
                        'DOTA2_rank_tier': rank,
                    }
                dumpjson(steamdata, STEAM)
                return success.format(id3)
            except:
                return usage

        if msg.lower() == '解除绑定steam':
            steamdata = loadjson(STEAM)
            if steamdata['subscribers'].get(user):
                id3 = steamdata['subscribers'][user]
                steamdata['players'][id3]['subscribers'].remove(user)
                if not steamdata['players'][id3]['subscribers']:
                    del steamdata['players'][id3]
                del steamdata['subscribers'][user]
                dumpjson(steamdata, STEAM)
                return '解除绑定成功'
            else:
                return '没有找到你的绑定记录'

        prm = re.match('(.+)在(干|做|搞|整)(嘛|啥|哈|什么)', msg)
        if prm:
            name = prm[1].strip()
            steamdata = loadjson(STEAM)
            memberdata = loadjson(MEMBER)
            if re.search('群友', name):
                is_solo = False
                players_in_group = []
                for qq, id3 in steamdata['subscribers'].items():
                    if qq in memberdata[group]:
                        players_in_group.append(steamdata['players'][id3]['steam_id64'])
                players_in_group = list(set(players_in_group))
                sids = ','.join(str(p) for p in players_in_group)
            else:
                is_solo = True
                obj = self.whois.object_explainer(group, user, name)
                name = obj['name'] or name
                steam_info = steamdata['players'].get(steamdata['subscribers'].get(obj['uid']))
                if steam_info:
                    sids = steam_info.get('steam_id64')
                    if not sids:
                        return IDK
                else: # steam_info is None
                    if obj['uid'] == UNKNOWN:
                        return f'我们群里有{name}吗？'
                    return f'{IDK}，因为{name}还没有绑定SteamID'
            replys = []
            try:
                j = requests.get(PLAYER_SUMMARY.format(APIKEY, sids), timeout=10).json()
            except requests.exceptions.RequestException as e:
                print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale PLAYER_SUMMARY', e)
                return 'kale，请稍后再试'
            for p in j['response']['players']:
                if p.get('gameextrainfo'):
                    replys.append(p['personaname'] + '现在正在玩' + p['gameextrainfo'])
                elif is_solo:
                    replys.append(p['personaname'] + '现在没在玩游戏')
            if replys:
                if len(replys) > 2:
                    replys.append('大家都有光明的未来！')
                return '\n'.join(replys)
            elif not is_solo:
                return '群友都没在玩游戏'
            return IDK

        prm = re.match('查询(.+)的天梯段位$', msg)
        if prm:
            await self.api.send_group_msg(
                group_id=message['group_id'],
                message=f'正在查询',
            )
            name = prm[1].strip()
            steamdata = loadjson(STEAM)
            memberdata = loadjson(MEMBER)
            if re.search('群友', name):
                players_in_group = []
                for qq, id3 in steamdata['subscribers'].items():
                    if qq in memberdata[group]:
                        players_in_group.append(id3)
                players_in_group = list(set(players_in_group))
            else:
                obj = self.whois.object_explainer(group, user, name)
                name = obj['name'] or name
                id3 = steamdata['subscribers'].get(obj['uid'])
                if not id3:
                    if obj['uid'] == UNKNOWN:
                        return f'我们群里有{name}吗？'
                    return f'查不了，{name}可能还没有绑定SteamID'
                players_in_group = [id3]
            ranks = []
            replys = []
            for id3 in players_in_group:
                name, rank = self.dota2.get_rank_tier(id3)
                if rank:
                    ranks.append((name, rank))
            if ranks:
                ranks = sorted(ranks, key=lambda i: i[1], reverse=True)
                for name, rank in ranks:
                    replys.append('{}现在是{}{}'.format(name, PLAYER_RANK[rank // 10], rank % 10 or ''))
                if len(replys) > 2:
                    replys.append('大家都有光明的未来！')
                return '\n'.join(replys)
            else:
                return '查不到哟'

        prm = re.match('查询(.+)的(常用英雄|英雄池)$', msg)
        if prm:
            name = prm[1]
            item = prm[2]
            if name == '群友':
                return '唔得，一个一个查'
            steamdata = loadjson(STEAM)
            obj = self.whois.object_explainer(group, user, name)
            name = obj['name'] or name
            id3 = steamdata['subscribers'].get(obj['uid'])
            if not id3:
                if obj['uid'] == UNKNOWN:
                    return f'我们群里有{name}吗？'
                return f'查不了，{name}可能还没有绑定SteamID'
            try:
                j = requests.get(OPENDOTA_PLAYERS.format(id3) + '/heroes', timeout=10).json()
            except requests.exceptions.RequestException as e:
                print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale OPENDOTA_PLAYERS', e)
                return 'kale，请稍后再试'
            if item == '常用英雄':
                hero_stat = []
                if j[0]['games'] == 0:
                    return f'这个{name}是不是什么都没玩过啊'
                for i in range(5):
                    if j[i]['games'] > 0:
                        hero = HEROES_CHINESE[int(j[i]["hero_id"])][0]
                        games = j[i]["games"]
                        win = j[i]["win"]
                        win_rate = 100 * win / games
                        hero_stat.append(f'{games}局{hero}，赢了{win}局，胜率{win_rate:.2f}%')
                    else:
                        break
                return f'{name}玩得最多的{len(hero_stat)}个英雄：\n' + '\n'.join(hero_stat)
            if item == '英雄池':
                hero_num = 0
                hero_ge20 = 0
                if j[0]['games'] == 0:
                    return f'这个{name}什么都没玩过啊哪来的英雄池'
                for i in range(len(j)):
                    if j[i]['games'] > 0:
                        hero_num += 1
                        if j[i]['games'] >= 20:
                            hero_ge20 += 1
                    else:
                        break
                return f'{name}玩过{hero_num}个英雄，其中大于等于20局的有{hero_ge20}个'

        prm = re.match('查询战报(.*)', msg, re.I)
        if prm:
            usage = '使用方法：\n查询战报 Dota2比赛编号'
            try:
                match_id = str(int(prm[1]))
                steamdata = loadjson(STEAM)
                if steamdata['DOTA2_matches_pool'].get(match_id, 0) != 0:
                    return f'比赛{match_id}已在比赛缓冲池中，战报将稍后发出'
                steamdata['DOTA2_matches_pool'][match_id] = {
                    'request_attempts': 0,
                    'players': [],
                    'is_solo': {
                        'group': group,
                        'user' : user,
                    },
                }
                dumpjson(steamdata, STEAM)
                return f'已将比赛{match_id}添加至比赛缓冲池，战报将稍后发出'
            except Exception as e:
                print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'查询战报失败', e)
                return usage

        prm = re.match('查询(.+)的最近比赛$', msg)
        if prm:
            name = prm[1].strip()
            if name == '群友':
                return '唔得，一个一个查'
            await self.api.send_group_msg(
                group_id=message['group_id'],
                message=f'正在查询',
            )
            steamdata = loadjson(STEAM)
            obj = self.whois.object_explainer(group, user, name)
            name = obj['name'] or name
            id3 = steamdata['subscribers'].get(obj['uid'])
            if not id3:
                if obj['uid'] == UNKNOWN:
                    return f'我们群里有{name}吗？'
                return f'查不了，{name}可能还没有绑定SteamID'
            match_id, start_time = self.dota2.get_last_match(id3)
            if match_id and start_time:
                replys = []
                match_id = str(match_id)
                replys.append('查到了')
                # replys.append('{}的最近一场Dota 2比赛编号为{}'.format(name, match_id))
                # replys.append('开始于{}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))))
                if steamdata['DOTA2_matches_pool'].get(match_id, 0) != 0:
                    replys.append('该比赛已在比赛缓冲池中')
                else:
                    steamdata['DOTA2_matches_pool'][match_id] = {
                        'request_attempts': 0,
                        'players': [],
                        'is_solo': {
                            'group': group,
                            'user' : user,
                        },
                    }
                    dumpjson(steamdata, STEAM)
                    replys.append( '已将该比赛添加至比赛缓冲池')
                if group in steamdata['subscribe_groups']:
                    replys.append('等着瞧吧（指战报）')
                else:
                    replys.append('但是因为本群未订阅Steam所以不会发出来')
                return '，'.join(replys)
            else:
                return '查不到哟'


    def jobs(self):
        trigger = CronTrigger(minute='*', second='30')
        job = (trigger, self.send_news_async)
        return (job,)

    async def send_news_async(self):
        steamdata = loadjson(STEAM)
        groups = steamdata.get('subscribe_groups')
        if not groups:
            return None
        news = await self.get_news_async()
        sends = []
        for msg in news:
            for g in groups:
                if str(g) in msg['target_groups']:
                    sends.append({
                        'message_type': 'group',
                        'group_id': g,
                        'message': msg['message']
                    })
        return sends

    async def get_news_async(self):
        '''
        返回最新消息
        '''
        news = []
        memberdata = loadjson(MEMBER)
        steamdata = loadjson(STEAM)
        players = self.get_players()
        sids = ','.join(str(p) for p in players.keys())
        if not sids:
            sids = '0'
        now = int(datetime.now().timestamp())
        # print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'Steam雷达开始扫描')
        try:
            j = requests.get(PLAYER_SUMMARY.format(APIKEY, sids), timeout=10).json()
        except requests.exceptions.RequestException as e:
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale PLAYER_SUMMARY', e)
            j = {'response': {'players': []}}
        for p in j['response']['players']:
            id64 = int(p['steamid'])
            id3 = str(id64 - 76561197960265728)
            cur_game = p.get('gameextrainfo', '')
            pre_game = steamdata['players'][id3]['gameextrainfo']
            pname    = p['personaname']

            # 游戏状态更新
            if cur_game == 'Dota 2':
                steamdata['players'][id3]['last_DOTA2_action'] = max(now, steamdata['players'][id3]['last_DOTA2_action'])
            if cur_game != pre_game:
                minutes = (now - steamdata['players'][id3]['last_change']) // 60
                if cur_game:
                    if pre_game:
                        mt = f'{pname}玩了{minutes}分钟{pre_game}后，玩起了{cur_game}'
                    else:
                        mt = f'{pname}启动了{cur_game}'
                    if datetime.now().hour <= 6:
                        mt += '\n你他娘的不用睡觉吗？'
                    if datetime.now().weekday() < 5 and datetime.now().hour in range(8, 18):
                        mt += '\n见鬼，这群人都不用上班的吗'
                    news.append({
                        'message': mt,
                        'user'   : players[id64]
                    })
                else:
                    news.append({
                        'message': f'{pname}退出了{pre_game}，本次游戏时长{minutes}分钟',
                        'user'   : players[id64]
                    })
                steamdata['players'][id3]['gameextrainfo'] = cur_game
                steamdata['players'][id3]['last_change'] = now

            # DOTA2最近比赛更新
            # 每分钟请求时只请求最近3小时内有DOTA2活动的玩家的最近比赛，其余玩家的比赛仅每小时请求一次
            if steamdata['players'][id3]['last_DOTA2_action'] >= now - 10800 or datetime.now().minute == self.MINUTE:
                # print('{} 请求最近比赛更新 {}'.format(datetime.now(), id64))
                match_id, start_time = self.dota2.get_last_match(id64)
            else:
                match_id, start_time = (0, 0) # 将跳过之后的步骤
            new_match = False
            if match_id > steamdata['players'][id3]['last_DOTA2_match_id']:
                new_match = True
                steamdata['players'][id3]['last_DOTA2_action'] = max(start_time, steamdata['players'][id3]['last_DOTA2_action'])
                steamdata['players'][id3]['last_DOTA2_match_id'] = match_id
            if new_match:
                match_id = str(match_id)
                player = {
                    'personaname': pname,
                    'steam_id3' : int(id3),
                }
                if steamdata['DOTA2_matches_pool'].get(match_id, 0) != 0:
                    steamdata['DOTA2_matches_pool'][match_id]['players'].append(player)
                else:
                    steamdata['DOTA2_matches_pool'][match_id] = {
                        'request_attempts': 0,
                        'start_time': start_time,
                        'subscribers': [],
                        'players': [player]
                    }
                for qq in players[id64]:
                    if qq not in steamdata['DOTA2_matches_pool'][match_id]['subscribers']:
                        steamdata['DOTA2_matches_pool'][match_id]['subscribers'].append(qq)

            # 每3小时请求一次天梯段位
            if datetime.now().hour % 3 == 0 and datetime.now().minute == self.MINUTE:
                pname, cur_rank = self.dota2.get_rank_tier(id3)
                pre_rank = steamdata['players'][id3]['DOTA2_rank_tier']
                if cur_rank != pre_rank:
                    if cur_rank:
                        if pre_rank:
                            word = '升' if cur_rank > pre_rank else '掉'
                            mt = '{}从{}{}{}到了{}{}'.format(
                                pname,
                                PLAYER_RANK[pre_rank // 10], pre_rank % 10 or '',
                                word,
                                PLAYER_RANK[cur_rank // 10], cur_rank % 10 or ''
                            )
                        else:
                            mt = '{}达到了{}{}'.format(pname, PLAYER_RANK[cur_rank // 10], cur_rank % 10 or '')
                        news.append({
                            'message': mt,
                            'user'   : players[id64]
                        })
                        steamdata['players'][id3]['DOTA2_rank_tier'] = cur_rank
                    else:
                        pass

        dumpjson(steamdata, STEAM)

        news += self.dota2.get_matches_report()

        if len(news) > 0:
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'Steam雷达扫描到了{len(news)}个新事件')

        for msg in news:
            if msg.get('target_groups', 0) == 0:
                msg['target_groups'] = []
            for u in msg['user']:
                for g in memberdata:
                    if u in memberdata[g] and g not in msg['target_groups']:
                        msg['target_groups'].append(g)

        return news

    def init_fonts(self):
        print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '初始化字体')
        font_path = os.path.expanduser('~/.Steam_watcher/fonts/MSYH.TTC')
        font_OK = False
        try:
            font = ImageFont.truetype(font_path, 12)
            font_OK = True
            if os.path.getsize(font_path) < 19647736:
                print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '字体文件不完整')
                font_OK = False
        except Exception as e:
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'初始化字体失败', e)
        if font_OK:
            return
        try:
            with open(font_path, 'wb') as f:
                t0 = time.time()
                for i in range(1, 193):
                    n = f'{i:0>3}'
                    per = i / 192 * 100
                    t1 = (time.time() - t0) / i * (192 - i)
                    print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'正在重新下载字体({per:.2f}%)，预计还需要{t1:.2f}秒', end='\r')
                    f.write(requests.get(f'https://yubo65536.gitee.io/manager/assets/MSYH/x{n}', timeout=10).content)
            print()
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '字体下载完成')
        except Exception as e:
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '字体下载失败', e)

    def init_images(self):
        print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '初始化图片')
        total, downloaded, successful, failed = 0, 0, 0, 0
        images = []
        try:
            images = requests.get('https://yubo65536.gitee.io/manager/assets/DOTA2_images.list', timeout=10).text.split('\n')
            total = len(images)
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'加载图片列表成功，共有{total}条图片记录')
        except Exception as e:
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '加载图片列表失败', e)
            return
        if not images:
            return
        for img in images:
            img_OK = False
            img_path = os.path.join(IMAGES, img)
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), '初始化图片({}/{})'.format(downloaded + successful + failed + 1, total), end='\r')
            try:
                cur_img = Image.open(img_path).verify()
                img_OK = True
                successful += 1
            except Exception as e:
                # print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'读取图片{img}失败', e)
                # print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'开始重新下载{img}')
                pass
            if img_OK:
                continue
            try:
                with open(img_path, 'wb') as f:
                    f.write(requests.get(f'https://yubo65536.gitee.io/manager/assets/images/{img}', timeout=10).content)
                    downloaded += 1
            except Exception as e:
                # print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'下载{img}失败', e)
                failed += 1
        print()
        print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), f'从本地读取{successful}，重新下载{downloaded}，读取/下载失败{failed}')

    def get_players(self):
        steamdata  = loadjson(STEAM)
        players = {}
        for p in steamdata['players'].values():
            players[p['steam_id64']] = p['subscribers']
        return players


class Dota2:
    @staticmethod
    def get_last_match(id64):
        try:
            match = requests.get(LAST_MATCH.format(APIKEY, id64), timeout=10).json()['result']['matches'][0]
            return match['match_id'], match['start_time']
        except requests.exceptions.RequestException as e:
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale LAST_MATCH', e)
            return 0, 0
        except Exception as e:
            return 0, 0

    @staticmethod
    def get_rank_tier(id3):
        try:
            j = requests.get(OPENDOTA_PLAYERS.format(id3), timeout=10).json()
            name = j['profile']['personaname']
            rank = j.get('rank_tier') if j.get('rank_tier') else 0
            return name, rank
        except requests.exceptions.RequestException as e:
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale OPENDOTA_PLAYERS', e)
            return '', 0
        except Exception as e:
            return '', 0

    # 根据slot判断队伍, 返回0为天辉, 1为夜魇
    @staticmethod
    def get_team_by_slot(slot):
        return slot // 100

    def get_match(self, match_id):
        MATCH = os.path.join(DOTA2_MATCHES, f'{match_id}.json')
        if os.path.exists(MATCH):
            print('{} 比赛编号 {} 读取本地保存的分析结果'.format(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), match_id))
            return loadjson(MATCH)
        steamdata = loadjson(STEAM)
        try:
            try:
                match = requests.get(OPENDOTA_MATCHES.format(match_id), timeout=10).json()
            except requests.exceptions.RequestException as e:
                print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale OPENDOTA_MATCHES', e)
                raise
            if match_id in steamdata['DOTA2_matches_pool']:
                if steamdata['DOTA2_matches_pool'][match_id]['request_attempts'] >= MAX_ATTEMPTS:
                    print('{} 比赛编号 {} 重试次数过多，跳过分析'.format(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), match_id))
                    if not match.get('players'):
                        print('{} 比赛编号 {} 从OPENDOTA获取不到分析结果，使用Valve的API'.format(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), match_id))
                        try:
                            match = requests.get(MATCH_DETAILS.format(APIKEY, match_id), timeout=10).json()['result']
                        except requests.exceptions.RequestException as e:
                            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale MATCH_DETAILS', e)
                            raise
                    match['incomplete'] = True
                    dumpjson(match, MATCH)
                    return match
            if match['game_mode'] in (15, 19):
                # 活动模式
                print('{} 比赛编号 {} 活动模式，跳过分析'.format(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), match_id))
                match['incomplete'] = True
                if match_id in steamdata['DOTA2_matches_pool']:
                    for pp in steamdata['DOTA2_matches_pool'][match_id]['players']:
                        for pm in match['players']:
                            if pp['steam_id3'] == pm['account_id']:
                                pm['personaname'] = pp['personaname']
                                break
                dumpjson(match, MATCH)
                return match
            received = match['players'][0]['damage_inflictor_received']
        except Exception as e:
            attempts = ''
            if match_id in steamdata['DOTA2_matches_pool']:
                steamdata['DOTA2_matches_pool'][match_id]['request_attempts'] += 1
                attempts = '（第{}次）'.format(steamdata['DOTA2_matches_pool'][match_id]['request_attempts'])
            print('{} {}{} {}'.format(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), match_id, attempts, e))
            dumpjson(steamdata, STEAM)
            return {}
        if received is None:
            # 比赛分析结果不完整
            job_id = None
            if match_id in steamdata['DOTA2_matches_pool']:
                job_id = steamdata['DOTA2_matches_pool'][match_id].get('job_id')
            if job_id:
                # 存在之前请求分析的job_id，则查询这个job是否已完成
                try:
                    j = requests.get(OPENDOTA_REQUEST.format(job_id), timeout=10).json()
                except requests.exceptions.RequestException as e:
                    print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale OPENDOTA_REQUEST', e)
                    return {}
                if j:
                    # 查询返回了数据，说明job仍未完成
                    print('{} job_id {} 仍在处理中'.format(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), job_id))
                    return {}
                else:
                    # job完成了，可以删掉
                    del steamdata['DOTA2_matches_pool'][match_id]['job_id']
                    dumpjson(steamdata, STEAM)
                    return {}
            else:
                # 不存在之前请求分析的job_id，重新请求一次，保存，下次再确认这个job是否已完成
                attempts = ''
                if match_id in steamdata['DOTA2_matches_pool']:
                    steamdata['DOTA2_matches_pool'][match_id]['request_attempts'] += 1
                    attempts = '（第{}次）'.format(steamdata['DOTA2_matches_pool'][match_id]['request_attempts'])
                try:
                    j = requests.post(OPENDOTA_REQUEST.format(match_id), timeout=10).json()
                except requests.exceptions.RequestException as e:
                    print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), 'kale OPENDOTA_REQUEST', e)
                    return {}
                job_id = j['job']['jobId']
                print('{} 比赛编号 {} 请求OPENDOTA分析{}，job_id: {}'.format(
                    datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'),
                    match_id, attempts, job_id
                ))
                if match_id in steamdata['DOTA2_matches_pool']:
                    steamdata['DOTA2_matches_pool'][match_id]['job_id'] = job_id
                    dumpjson(steamdata, STEAM)
                return {}
        else:
            # 比赛分析结果完整了
            print('{} 比赛编号 {} 从OPENDOTA获取到分析结果'.format(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), match_id))
            if match_id in steamdata['DOTA2_matches_pool']:
                for pp in steamdata['DOTA2_matches_pool'][match_id]['players']:
                    for pm in match['players']:
                        if pp['steam_id3'] == pm['account_id']:
                            pm['personaname'] = pp['personaname']
                            break
            dumpjson(match, MATCH)
            return match

    def get_image(self, img_path):
        try:
            return Image.open(os.path.join(IMAGES, img_path))
        except Exception as e:
            print(e)
            return Image.new('RGBA', (30, 30), (255, 160, 160))

    def init_player(self, player):
        if not player.get('net_worth'):
            player['net_worth'] = player.get('total_gold') or 0
        if not player.get('total_xp'):
            player['total_xp'] = 0
        if not player.get('damage_inflictor_received'):
            player['damage_inflictor_received'] = {}
        if not player.get('hero_healing'):
            player['hero_healing'] = 0
        if not player.get('stuns'):
            player['stuns'] = 0
        if not player.get('purchase_log'):
            player['purchase_log'] = []
        if not player.get('item_usage'):
            player['item_usage'] = {}
        if not player.get('item_uses'):
            player['item_uses'] = {}
        if not player.get('lane_role'):
            player['lane_role'] = 0
        if not player.get('permanent_buffs'):
            player['permanent_buffs'] = {}

    def draw_title(self, match, draw, font, item, title, color):
        idx = item[0]
        draw.text(
            (match['players'][idx]['title_position'][0], match['players'][idx]['title_position'][1]),
            title, font=font, fill=color
        )
        title_size = font.getsize(title)
        match['players'][idx]['title_position'][0] += title_size[0] + 1
        # if match['players'][idx]['title_position'][0] > 195:
        #     match['players'][idx]['title_position'][0] = 10
        #     match['players'][idx]['title_position'][1] += 14


    def generate_match_message(self, match_id):
        match = self.get_match(match_id)
        if not match:
            return None
        for p in match['players']:
            self.init_player(p)
        steamdata = loadjson(STEAM)
        players = steamdata['DOTA2_matches_pool'][match_id]['players']
        start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(match['start_time']))
        duration = match['duration']

        # 比赛模式
        mode_id = match['game_mode']
        mode = GAME_MODE[mode_id] if mode_id in GAME_MODE else '未知'

        lobby_id = match['lobby_type']
        lobby = LOBBY[lobby_id] if lobby_id in LOBBY else '未知'
        # 更新玩家对象的比赛信息
        for i in players:
            for j in match['players']:
                if i['steam_id3'] == j['account_id']:
                    i['dota2_kill'] = j['kills']
                    i['dota2_death'] = j['deaths']
                    i['dota2_assist'] = j['assists']
                    i['kda'] = ((1. * i['dota2_kill'] + i['dota2_assist']) / i['dota2_death']) \
                        if i['dota2_death'] != 0 else (1. * i['dota2_kill'] + i['dota2_assist'])
                    i['dota2_team'] = self.get_team_by_slot(j['player_slot'])
                    i['hero'] = j['hero_id']
                    i['last_hit'] = j['last_hits']
                    i['damage'] = j['hero_damage']
                    i['gpm'] = j['gold_per_min']
                    i['xpm'] = j['xp_per_min']
                    break
        personanames = '，'.join([players[i]['personaname'] for i in range(-len(players),-1)])
        if personanames:
            personanames += '和'
        personanames += players[-1]['personaname']

        # 队伍信息
        team = players[0]['dota2_team']
        win = match['radiant_win'] == (team == 0)

        team_damage = 0
        team_score = [match['radiant_score'], match['dire_score']][team]
        team_deaths = 0
        for i in match['players']:
            if self.get_team_by_slot(i['player_slot']) == team:
                team_damage += i['hero_damage']
                team_deaths += i['deaths']

        top_kda = 0
        for i in players:
            if i['kda'] > top_kda:
                top_kda = i['kda']

        if (win and top_kda > 5) or (not win and top_kda > 3):
            postive = True
        elif (win and top_kda < 2) or (not win and top_kda < 1):
            postive = False
        else:
            if random.randint(0, 1) == 0:
                postive = True
            else:
                postive = False

        tosend = []
        if win and postive:
            tosend.append(random.choice(WIN_POSTIVE).format(personanames))
        elif win and not postive:
            tosend.append(random.choice(WIN_NEGATIVE).format(personanames))
        elif not win and postive:
            tosend.append(random.choice(LOSE_POSTIVE).format(personanames))
        else:
            tosend.append(random.choice(LOSE_NEGATIVE).format(personanames))

        tosend.append('开始时间: {}'.format(start_time))
        tosend.append('持续时间: {:.0f}分{:.0f}秒'.format(duration / 60, duration % 60))
        tosend.append('游戏模式: [{}/{}]'.format(mode, lobby))

        for i in players:
            personaname = i['personaname']
            hero = random.choice(HEROES_CHINESE[i['hero']]) if i['hero'] in HEROES_CHINESE else '不知道什么鬼'
            kda = i['kda']
            last_hits = i['last_hit']
            damage = i['damage']
            kills, deaths, assists = i['dota2_kill'], i['dota2_death'], i['dota2_assist']
            gpm, xpm = i['gpm'], i['xpm']

            damage_rate = 0 if team_damage == 0 else (100 * damage / team_damage)
            participation = 0 if team_score == 0 else (100 * (kills + assists) / team_score)
            deaths_rate = 0 if team_deaths == 0 else (100 * deaths / team_deaths)

            tosend.append(
                '{}使用{}, KDA: {:.2f}[{}/{}/{}], GPM/XPM: {}/{}, ' \
                '补刀数: {}, 总伤害: {}({:.2f}%), ' \
                '参战率: {:.2f}%, 参葬率: {:.2f}%' \
                .format(personaname, hero, kda, kills, deaths, assists, gpm, xpm, last_hits,
                        damage, damage_rate,
                        participation, deaths_rate)
            )

        return '\n'.join(tosend)

    def generate_match_image(self, match_id):
        match = self.get_match(match_id)
        if not match:
            return None
        image = Image.new('RGB', (800, 900), (255, 255, 255))
        font = ImageFont.truetype(os.path.expanduser('~/.Steam_watcher/fonts/MSYH.TTC'), 12)
        font2 = ImageFont.truetype(os.path.expanduser('~/.Steam_watcher/fonts/MSYH.TTC'), 18)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 800, 70), 'black')
        title = '比赛 ' + str(match['match_id'])
        # 手动加粗
        draw.text((30, 15), title, font=font2, fill=(255, 255, 255))
        draw.text((31, 15), title, font=font2, fill=(255, 255, 255))
        draw.text((250, 20), '开始时间', font=font, fill=(255, 255, 255))
        draw.text((251, 20), '开始时间', font=font, fill=(255, 255, 255))
        draw.text((400, 20), '持续时间', font=font, fill=(255, 255, 255))
        draw.text((401, 20), '持续时间', font=font, fill=(255, 255, 255))
        draw.text((480, 20), 'Level', font=font, fill=(255, 255, 255))
        draw.text((481, 20), 'Level', font=font, fill=(255, 255, 255))
        draw.text((560, 20), '地区', font=font, fill=(255, 255, 255))
        draw.text((561, 20), '地区', font=font, fill=(255, 255, 255))
        draw.text((650, 20), '比赛模式', font=font, fill=(255, 255, 255))
        draw.text((651, 20), '比赛模式', font=font, fill=(255, 255, 255))
        start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(match['start_time']))
        duration = '{}分{}秒'.format(match['duration'] // 60, match['duration'] % 60)
        skill = SKILL_LEVEL[match['skill']] if match.get('skill') else 'Unknown'
        region_id = 'region_{}'.format(match.get('region'))
        region = REGION[region_id] if region_id in REGION else '未知'
        mode_id = match['game_mode']
        mode = GAME_MODE[mode_id] if mode_id in GAME_MODE else '未知'
        lobby_id = match['lobby_type']
        lobby = LOBBY[lobby_id] if lobby_id in LOBBY else '未知'
        draw.text((250, 40), start_time, font=font, fill=(255, 255, 255))
        draw.text((400, 40), duration, font=font, fill=(255, 255, 255))
        draw.text((480, 40), skill, font=font, fill=(255, 255, 255))
        draw.text((560, 40), region, font=font, fill=(255, 255, 255))
        draw.text((650, 40), f'{mode}/{lobby}', font=font, fill=(255, 255, 255))
        if match.get('incomplete'):
            draw.text((30, 40), '※分析结果不完整', font=font, fill=(255, 180, 0))
        else:
            draw.text((30, 40), '※录像分析成功', font=font, fill=(123, 163, 52))
        RADIANT_GREEN = (60, 144, 40)
        DIRE_RED = (156, 54, 40)
        winner = 1 - int(match['radiant_win'])
        draw.text((364, 81), SLOT_CHINESE[winner] + '胜利', font=font2, fill=[RADIANT_GREEN, DIRE_RED][winner])
        draw.text((365, 81), SLOT_CHINESE[winner] + '胜利', font=font2, fill=[RADIANT_GREEN, DIRE_RED][winner])
        radiant_score = str(match['radiant_score'])
        radiant_score_size = font2.getsize(radiant_score)
        draw.text((338 - radiant_score_size[0], 81), radiant_score, font=font2, fill=RADIANT_GREEN)
        draw.text((339 - radiant_score_size[0], 81), radiant_score, font=font2, fill=RADIANT_GREEN)
        draw.text((460, 81), str(match['dire_score']), font=font2, fill=DIRE_RED)
        draw.text((461, 81), str(match['dire_score']), font=font2, fill=DIRE_RED)
        draw.rectangle((0, 120, 800, 122), RADIANT_GREEN)
        draw.rectangle((0, 505, 800, 507), DIRE_RED)
        image.paste(self.get_image('radiant_logo.png').resize((32, 32), Image.ANTIALIAS), (10, 125))
        image.paste(self.get_image('dire_logo.png').resize((32, 32), Image.ANTIALIAS), (10, 510))
        draw.text((100, 128 + 385 * winner), '胜利', font=font2, fill=[RADIANT_GREEN, DIRE_RED][winner])
        max_net = [0, 0]
        max_xpm = [0, 0]
        max_kills = [0, 0, 0]
        max_deaths = [0, 0, 99999]
        max_assists = [0, 0, 0]
        max_hero_damage = [0, 0]
        max_tower_damage = [0, 0]
        max_stuns = [0, 0]
        max_healing = [0, 0]
        max_hurt = [0, 0]
        min_participation = [0, 999, 999, 999999]
        for slot in range(0, 2):
            team_damage = 0
            team_damage_received = 0
            team_score = [match['radiant_score'], match['dire_score']][slot]
            team_kills = 0
            team_deaths = 0
            team_gold = 0
            team_exp = 0
            max_mvp_point = [0, 0]
            draw.text((50, 126 + slot * 385), SLOT[slot],         font=font, fill=[RADIANT_GREEN, DIRE_RED][slot])
            draw.text((50, 140 + slot * 385), SLOT_CHINESE[slot], font=font, fill=[RADIANT_GREEN, DIRE_RED][slot])
            for i in range(5):
                idx = slot * 5 + i
                p = match['players'][idx]
                self.init_player(p)
                p['hurt'] = sum(p['damage_inflictor_received'].values())
                p['participation'] = 0 if team_score == 0 else 100 * (p['kills'] + p['assists']) / team_score
                team_damage += p['hero_damage']
                team_damage_received += p['hurt']
                team_kills += p['kills']
                team_deaths += p['deaths']
                team_gold += p['net_worth']
                team_exp += p['total_xp']
                hero_img = self.get_image('{}_full.png'.format(HEROES.get(p['hero_id'])))
                hero_img = hero_img.resize((64, 36), Image.ANTIALIAS)
                image.paste(hero_img, (10, 170 + slot * 60 + idx * 65))
                draw.rectangle((54, 191 + slot * 60 + idx * 65, 73, 205 + slot * 60 + idx * 65), fill=(50, 50, 50))
                level = str(p['level'])
                level_size = font.getsize(level)
                draw.text((71 - level_size[0], 190 + slot * 60 + idx * 65), level, font=font, fill=(255, 255, 255))
                rank = p.get('rank_tier') if p.get('rank_tier') else 0
                rank, star = rank // 10, rank % 10
                rank_img = self.get_image(f'rank_icon_{rank}.png')
                if star:
                    rank_star = self.get_image(f'rank_star_{star}.png')
                    rank_img = Image.alpha_composite(rank_img, rank_star)
                rank_img = Image.alpha_composite(Image.new('RGBA', rank_img.size, (255, 255, 255)), rank_img)
                rank_img = rank_img.convert('RGB')
                rank_img = rank_img.resize((45, 45), Image.ANTIALIAS)
                image.paste(rank_img, (75, 164 + slot * 60 + idx * 65))
                rank = '[{}{}] '.format(PLAYER_RANK[rank], star if star else '')
                rank_size = font.getsize(rank)
                draw.text((122, 167 + slot * 60 + idx * 65), rank, font=font, fill=(128, 128, 128))
                pname = p.get('personaname') if p.get('personaname') else '匿名玩家'
                pname_size = font.getsize(pname)
                while rank_size[0] + pname_size[0] > 240:
                    pname = pname[:-2] + '…'
                    pname_size = font.getsize(pname)
                draw.text((122 + rank_size[0], 167 + slot * 60 + idx * 65), pname, font=font, fill=[RADIANT_GREEN, DIRE_RED][slot])
                pick = '第?手'
                if match.get('picks_bans'):
                    for bp in match.get('picks_bans'):
                        if bp['hero_id'] == p['hero_id']:
                            pick = '第{}手'.format(bp['order'] + 1)
                            break
                if p.get('randomed'):
                    pick = '随机'
                lane = '未知分路'
                if p.get('lane_role'):
                    lane = ['优势路', '中路', '劣势路', '打野'][p['lane_role'] - 1]
                draw.text((122, 181 + slot * 60 + idx * 65), '{} {}'.format(pick, lane), font=font, fill=(0, 0, 0))
                net = '{:,}'.format(p['net_worth'])
                net_size = font.getsize(net)
                damage_to_net = '({:.2f})'.format(p['hero_damage'] / p['net_worth'] if p['net_worth'] else 0)
                draw.text((123, 196 + slot * 60 + idx * 65), net, font=font, fill=(0, 0, 0))
                draw.text((122, 195 + slot * 60 + idx * 65), net, font=font, fill=(255, 255, 0))
                draw.text((126 + net_size[0], 195 + slot * 60 + idx * 65), damage_to_net, font=font, fill=(0, 0, 0))

                draw.text((215, 209 + slot * 60 + idx * 65), '建筑伤害: {:,}'.format(p['tower_damage']), font=font, fill=(0, 0, 0))
                kda = '{}/{}/{} ({:.2f})'.format(
                    p['kills'], p['deaths'], p['assists'],
                    (p['kills'] + p['assists']) if p['deaths'] == 0 else (p['kills'] + p['assists']) / p['deaths']
                )
                draw.text((375, 167 + slot * 60 + idx * 65), kda, font=font, fill=(0, 0, 0))
                draw.text((375, 195 + slot * 60 + idx * 65), '控制时间: {:.2f}s'.format(p['stuns']), font=font, fill=(0, 0, 0))
                draw.text((375, 209 + slot * 60 + idx * 65), '治疗量: {:,}'.format(p['hero_healing']), font=font, fill=(0, 0, 0))

                p['title_position'] = [10, 209 + slot * 60 + idx * 65]
                mvp_point = p['kills'] * 5 + p['assists'] * 3 + p['stuns'] * 0.5 + p['hero_damage'] * 0.001 + p['tower_damage'] * 0.01 + p['hero_healing'] * 0.002
                if mvp_point > max_mvp_point[1]:
                    max_mvp_point = [idx, mvp_point]
                if p['net_worth'] > max_net[1]:
                    max_net = [idx, p['net_worth']]
                if p['xp_per_min'] > max_xpm[1]:
                    max_xpm = [idx, p['xp_per_min']]
                if p['kills'] > max_kills[1] or (p['kills'] == max_kills[1] and p['hero_damage'] > max_kills[2]):
                    max_kills = [idx, p['kills'], p['hero_damage']]
                if p['deaths'] > max_deaths[1] or (p['deaths'] == max_deaths[1] and p['net_worth'] < max_deaths[2]):
                    max_deaths = [idx, p['deaths'], p['net_worth']]
                if p['assists'] > max_assists[1] or (p['assists'] == max_assists[1] and p['hero_damage'] > max_assists[2]):
                    max_assists = [idx, p['assists'], p['hero_damage']]
                if p['hero_damage'] > max_hero_damage[1]:
                    max_hero_damage = [idx, p['hero_damage']]
                if p['tower_damage'] > max_tower_damage[1]:
                    max_tower_damage = [idx, p['tower_damage']]
                if p['stuns'] > max_stuns[1]:
                    max_stuns = [idx, p['stuns']]
                if p['hero_healing'] > max_healing[1]:
                    max_healing = [idx, p['hero_healing']]
                if p['hurt'] > max_hurt[1]:
                    max_hurt = [idx, p['hurt']]
                if (
                    p['participation'] < min_participation[1]
                ) or (
                    p['participation'] == min_participation[1] and p['kills'] + p['assists'] < min_participation[2]
                ) or (
                    p['participation'] == min_participation[1] and p['kills'] + p['assists'] == min_participation[2] and p['hero_damage'] < min_participation[3]
                ):
                    min_participation = [idx, p['participation'], p['kills'] + p['assists'], p['hero_damage']]

                scepter = 0
                shard = 0
                image.paste(Image.new('RGB', (252, 32), (192, 192, 192)), (474, 171 + slot * 60 + idx * 65))
                p['purchase_log'].reverse()
                for item in ITEM_SLOTS:
                    if p[item] == 0:
                        item_img = Image.new('RGB', (40, 30), (128, 128, 128))
                    else:
                        item_img = self.get_image('{}_lg.png'.format(ITEMS.get(p[item])))
                    if p[item] == 108:
                        scepter = 1
                    if item == 'item_neutral':
                        ima = item_img.convert('RGBA')
                        size = ima.size
                        r1 = min(size[0], size[1])
                        if size[0] != size[1]:
                            ima = ima.crop((
                                (size[0] - r1) // 2,
                                (size[1] - r1) // 2,
                                (size[0] + r1) // 2,
                                (size[1] + r1) // 2
                            ))
                        r2 = r1 // 2
                        imb = Image.new('RGBA', (r2 * 2, r2 * 2), (255, 255, 255, 0))
                        pima = ima.load()
                        pimb = imb.load()
                        r = r1 / 2
                        for i in range(r1):
                            for j in range(r1):
                                l = ((i - r) ** 2 + (j - r) ** 2) ** 0.5
                                if l < r2:
                                    pimb[i - (r - r2), j - (r - r2)] = pima[i, j]
                        imb = imb.resize((30, 30), Image.ANTIALIAS)
                        imb = Image.alpha_composite(Image.new('RGBA', imb.size, (255, 255, 255)), imb)
                        item_img = imb.convert('RGB')
                        image.paste(item_img, (733, 170 + slot * 60 + idx * 65))
                    else:
                        item_img = item_img.resize((40, 30), Image.ANTIALIAS)
                        image.paste(item_img, (475 + 42 * ITEM_SLOTS.index(item), 172 + slot * 60 + idx * 65))
                        purchase_time = None
                        for pl in p['purchase_log']:
                            if p[item] == 0:
                                continue
                            if pl['key'] == ITEMS.get(p[item]):
                                purchase_time = pl['time']
                                pl['key'] += '_'
                                break
                        if purchase_time:
                            draw.rectangle((475 + 42 * ITEM_SLOTS.index(item), 191 + slot * 60 + idx * 65, 514 + 42 * ITEM_SLOTS.index(item), 201 + slot * 60 + idx * 65), fill=(50, 50, 50))
                            draw.text(
                                (479 + 42 * ITEM_SLOTS.index(item), 188 + slot * 60 + idx * 65),
                                '{:0>2}:{:0>2}'.format(purchase_time // 60, purchase_time % 60) if purchase_time > 0 else '-{}:{:0>2}'.format(-purchase_time // 60, -purchase_time % 60),
                                font=font, fill=(192, 192, 192)
                            )
                for buff in p['permanent_buffs']:
                    if buff['permanent_buff'] == 2:
                        scepter = 1
                    if buff['permanent_buff'] == 12:
                        shard = 1
                scepter_img = self.get_image(f'scepter_{scepter}.png')
                scepter_img = scepter_img.resize((20, 20), Image.ANTIALIAS)
                image.paste(scepter_img, (770 , 170 + slot * 60 + idx * 65))
                shard_img = self.get_image(f'shard_{shard}.png')
                shard_img = shard_img.resize((20, 11), Image.ANTIALIAS)
                image.paste(shard_img, (770 , 190 + slot * 60 + idx * 65))

            for i in range(4):
                draw.rectangle((0, 228 + slot * 385 + i * 65, 800,  228 + slot * 385 + i * 65), (225, 225, 225))

            for i in range(5):
                idx = slot * 5 + i
                p = match['players'][idx]
                damage_rate = 0 if team_damage == 0 else 100 * (p['hero_damage'] / team_damage)
                damage_received_rate = 0 if team_damage_received == 0 else 100 * (p['hurt'] / team_damage_received)
                draw.text((215, 181 + slot * 60 + idx * 65), '造成伤害: {:,} ({:.2f}%)'.format(p['hero_damage'], damage_rate), font=font, fill=(0, 0, 0))
                draw.text((215, 195 + slot * 60 + idx * 65), '承受伤害: {:,} ({:.2f}%)'.format(p['hurt'], damage_received_rate), font=font, fill=(0, 0, 0))
                draw.text((375, 181 + slot * 60 + idx * 65), '参战率: {:.2f}%'.format(p['participation']), font=font, fill=(0, 0, 0))

            if slot == winner:
                self.draw_title(match, draw, font, max_mvp_point, 'MVP', (255, 127, 39))
            else:
                self.draw_title(match, draw, font, max_mvp_point, '魂', (0, 162, 232))

            draw.text((475, 128 + slot * 385), '杀敌', font=font, fill=(64, 64, 64))
            draw.text((552, 128 + slot * 385), '总伤害', font=font, fill=(64, 64, 64))
            draw.text((636, 128 + slot * 385), '总经济', font=font, fill=(64, 64, 64))
            draw.text((726, 128 + slot * 385), '总经验', font=font, fill=(64, 64, 64))
            draw.text((475, 142 + slot * 385), f'{team_kills}', font=font, fill=(128, 128, 128))
            draw.text((552, 142 + slot * 385), f'{team_damage}', font=font, fill=(128, 128, 128))
            draw.text((636, 142 + slot * 385), f'{team_gold}', font=font, fill=(128, 128, 128))
            draw.text((726, 142 + slot * 385), f'{team_exp}', font=font, fill=(128, 128, 128))

        if max_net[1] > 0:
            self.draw_title(match, draw, font, max_net, '富', (255, 192, 30))
        if max_xpm[1] > 0:
            self.draw_title(match, draw, font, max_xpm, '睿', (30, 30, 255))
        if max_stuns[1] > 0:
            self.draw_title(match, draw, font, max_stuns, '控', (255, 0, 128))
        if max_hero_damage[1] > 0:
            self.draw_title(match, draw, font, max_hero_damage, '爆', (192, 0, 255))
        if max_kills[1] > 0:
            self.draw_title(match, draw, font, max_kills, '破', (224, 36, 36))
        if max_deaths[1] > 0:
            self.draw_title(match, draw, font, max_deaths, '鬼', (192, 192, 192))
        if max_assists[1] > 0:
            self.draw_title(match, draw, font, max_assists, '助', (0, 132, 66))
        if max_tower_damage[1] > 0:
            self.draw_title(match, draw, font, max_tower_damage, '拆', (128, 0, 255))
        if max_healing[1] > 0:
            self.draw_title(match, draw, font, max_healing, '奶', (0, 228, 120))
        if max_hurt[1] > 0:
            self.draw_title(match, draw, font, max_hurt, '耐', (112, 146, 190))
        if min_participation[1] < 999:
            self.draw_title(match, draw, font, min_participation, '摸', (200, 190, 230))

        draw.text(
            (10, 880),
            '※录像分析数据来自opendota.com，DOTA2游戏图片素材版权归Valve所有',
            font=font,
            fill=(128, 128, 128)
        )
        image.save(os.path.join(DOTA2_MATCHES, f'{match_id}.png'), 'png')
        print('{} 比赛编号 {} 生成战报图片'.format(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), match_id))

    def get_matches_report(self):
        steamdata = loadjson(STEAM)
        reports = []
        todelete = []
        for match_id, match_info in steamdata['DOTA2_matches_pool'].items():
            if match_info.get('is_solo'):
                match = self.get_match(match_id)
                if match:
                    if match.get('error'):
                        print('{} 比赛编号 {} 在分析结果中发现错误 {}'.format(
                            datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), match_id, match['error']
                        ))
                        m = '[CQ:at,qq={}] 你点的比赛战报来不了了！'.format(match_info['is_solo']['user'])
                        m += '\n在分析结果中发现错误 {}'.format(match['error'])
                    else:
                        self.generate_match_image(match_id)
                        m = '[CQ:at,qq={}] 你点的比赛战报来了！'.format(match_info['is_solo']['user'])
                        m += '\n[CQ:image,file=file:///{}]'.format(os.path.join(DOTA2_MATCHES, f'{match_id}.png'))
                    reports.append(
                        {
                            'message': m,
                            'target_groups': [match_info['is_solo']['group']],
                            'user': [],
                        }
                    )
                    todelete.append(match_id)
            else:
                now = int(datetime.now().timestamp())
                if match_info['start_time'] <= now - 86400 * 7:
                    todelete.append(match_id)
                    continue
                m = self.generate_match_message(match_id)
                if isinstance(m, str):
                    self.generate_match_image(match_id)
                    m += '\n[CQ:image,file=file:///{}]'.format(os.path.join(DOTA2_MATCHES, f'{match_id}.png'))
                    reports.append(
                        {
                            'message': m,
                            'user' : match_info['subscribers'],
                        }
                    )
                    todelete.append(match_id)
        # 数据在生成比赛报告的过程中会被修改，需要重新读取
        steamdata = loadjson(STEAM)
        for match_id in todelete:
            del steamdata['DOTA2_matches_pool'][match_id]
        dumpjson(steamdata, STEAM)
        return reports