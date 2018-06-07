#!/usr/bin/env python

import os
from multiprocessing import Process, Queue
from datetime import datetime
import tkinter as tk
from uwh.gamemanager import PoolLayout, TeamColor
from uwh.uwhscores_comms import UWHScores
from PIL import Image, ImageTk

import time
import sys

class MaskKind:
    NONE, CHROMA, VMAC = range(3)

def sized_frame(master, height, width):
    F = tk.Frame(master, height=height, width=width)
    F.pack_propagate(0)
    return F

class OverlayView(tk.Canvas):
    def __init__(self, parent, bbox, mgr, mask, version, demo):
        tk.Canvas.__init__(self, parent)

        self.parent = parent
        self.root = parent
        self.mgr = mgr
        self.mask = mask
        self.version = version
        self.demo = demo

        self.uwhscores = UWHScores('https://uwhscores.com/api/v1/', mock=False)
        #self.uwhscores = UWHScores('https://uwhscores.com/api/v1/', mock=True)
        #self.uwhscores = UWHScores('http://192.168.50.52:5000/api/v1/', mock=False)
        self.tid = None
        self.gid = None
        self.reset_uwhscores()

        self.init_ui(bbox)

    def init_ui(self, bbox):
        self.parent.title("TimeShark Scores")
        self.pack(fill=tk.BOTH, expand=1)

        self.w = bbox[0]
        self.h = bbox[1]

        self.refresh = 100
        self.t = 0
        def draw(self):
            try:
                self.delete(tk.ALL)
                if self.mask == MaskKind.VMAC:
                    # Borrowed from the first few minutes of: https://www.youtube.com/watch?v=hb8NU1LdhnI
                    vmac = Image.open('res/vmac.png')
                    vmac = vmac.resize((self.w, self.h), Image.ANTIALIAS)
                    self.vmac = ImageTk.PhotoImage(vmac)
                    self.create_image(0, 0, anchor=tk.NW, image=self.vmac)
                else:
                    self.clear(fill=self.color("bg"))
                self.render()
                self.update()
                self.after(self.refresh, lambda : draw(self))
            except KeyboardInterrupt:
                print("Quitting...")
                self.root.quit()
        self.after(1, lambda : draw(self))

        # Update UWHScores data periodically
        def refresh_uwhscores(self):
            self.fetch_uwhscores()
            self.after(60 * 1000, lambda : refresh_uwhscores(self))
        self.after(1, lambda : refresh_uwhscores(self))

        if self.demo:
            def cycle(self):
                self.mgr.setGid(max((self.mgr.gid() + 1) % 100, 1))
                self.after(5000, lambda : cycle(self))
            self.after(1, lambda : cycle(self))

    def clear(self, fill):
        self.create_rectangle((0, 0, self.w, self.h), fill=fill)

    def round_rectangle(self, bbox, radius, fill, fill_t=None, fill_b=None):
        x1, y1, x2, y2 = bbox
        fill_t = fill_t or fill
        fill_b = fill_b or fill
        self.create_arc((x2 - radius, y1, x2 + radius, y2), fill=fill_t, outline=fill_t, start=0)
        self.create_arc((x1 - radius, y1, x1 + radius, y2), fill=fill_t, outline=fill_t, start=90)
        self.create_arc((x1 - radius, y1, x1 + radius, y2), fill=fill_b, outline=fill_b, start=180)
        self.create_arc((x2 - radius, y1, x2 + radius, y2), fill=fill_b, outline=fill_b, start=270)
        self.create_rectangle((x1, y1, x2, (y1+y2)/2), fill=fill_t, outline=fill_t)
        self.create_rectangle((x1, (y1+y2)/2, x2, y2), fill=fill_b, outline=fill_b)

    def bordered_round_rectangle(self, bbox, radius, outset, fill, border,
                                 fill_t=None, fill_b=None, border_t=None, border_b=None):
        self.round_rectangle(bbox=(bbox[0]-outset, bbox[1]-outset,
                                   bbox[2]+outset, bbox[3]+outset),
                             radius=radius, fill=border,
                             fill_t=border_t, fill_b=border_b)
        self.round_rectangle(bbox, radius=radius, fill=fill,
                             fill_t=fill_t, fill_b=fill_b)

    @staticmethod
    def versions():
        return ["center", "split", "worlds", "left"]

    def get(self, side, feature):
        if ((self.mgr.layout() == PoolLayout.white_on_right) ==
            (side == 'right')):
            return {
                'score' : self.mgr.whiteScore(),
                'color' : 'white',
                'id' : self.white_id,
                'name' : self.white_name,
                'roster' : self.white_roster,
                'flag' : self.white_flag,
            }[feature]
        else:
            return {
                'score' : self.mgr.blackScore(),
                'color' : 'black',
                'id' : self.black_id,
                'name' : self.black_name,
                'roster' : self.black_roster,
                'flag' : self.black_flag,
            }[feature]

    def reset_uwhscores(self):
        self.game = None
        self.white_id = None
        self.black_id = None
        self.black_name = "Black"
        self.white_name = "White"
        self.black_roster = None
        self.white_roster = None
        self.tournament = None
        self.black_flag = None
        self.white_flag = None

    def fetch_uwhscores(self):
        self.tid = self.mgr.tid()
        self.gid = self.mgr.gid()
        def game(response):
            self.game = response
            self.black_name = response['black']
            self.white_name = response['white']
            self.black_id = response['black_id']
            self.white_id = response['white_id']
            def black_roster(roster):
                self.black_roster = roster
            def white_roster(roster):
                self.white_roster = roster
            self.uwhscores.get_roster(self.tid, self.black_id, black_roster)
            self.uwhscores.get_roster(self.tid, self.white_id, white_roster)
            def white_flag(flag):
                self.white_flag = flag
            def black_flag(flag):
                self.black_flag = flag
            self.uwhscores.get_team_flag(self.tid, self.black_id, black_flag)
            self.uwhscores.get_team_flag(self.tid, self.white_id, white_flag)

        self.uwhscores.get_game(self.tid, self.gid, game)

        def tournament(response):
            self.tournament = response
        self.uwhscores.get_tournament(self.tid, tournament)

    def render(self):
        # Force update of teams between games
        if (self.tid != self.mgr.tid() or
            self.gid != self.mgr.gid()):
            self.fetch_uwhscores()

        if not self.roster_view():
            self.game_play_view()

    def color(self, name):
        if self.mask == MaskKind.CHROMA and name == "bg":
            return "#00ff00"

        return {
            "bg" : "#054a91",
            "border" : "#ffffff",
            "fill" : "#313FA1",
            "fill_text" : "#ffffff",
            "black_fill" : "#000000",
            "black_text" : "#2e96ff",
            "white_fill" : "#ffffff",
            "white_text" : "#313FA1",
            "team_text"  : "#000000",
            "title_text" : "#ffffff",
        }.get(name, "#ff0000")

    def abbreviate(self, s, max_len = 16):
        if len(s) > max_len:
            return s[0:max_len-3] + "..."
        else:
            return s

    def game_play_view(self):
        radius = 10
        score_radius = 0
        height = 30
        width = 250
        flag_width = 60
        score_width = 40
        score_offset = width - score_width
        time_width = 155
        state_width = 110
        timeout_width = 150
        state_offset = score_offset + time_width
        outset = 3

        x1 = 40 + outset
        y1 = 40

        font=("Avenir Next LT Pro", 10)
        score_font=("Avenir Next LT Pro", 20)
        time_font=("Avenir Next LT Pro", 40)
        state_font=("Avenir Next LT Pro", 20)

        # Bottom Rectangle
        if (self.mgr.timeoutStateRef() or
            self.mgr.timeoutStateWhite() or
            self.mgr.timeoutStateBlack() or
            self.mgr.timeoutStatePenaltyShot()):
            if self.mgr.timeoutStateRef():
                fill_color = "#ffff00"
                border_color = "#000000"
            elif self.mgr.timeoutStateWhite():
                fill_color = "#ffffff"
                border_color = "#000000"
            elif self.mgr.timeoutStateBlack():
                fill_color = "#000000"
                border_color = "#ffffff"
            elif self.mgr.timeoutStatePenaltyShot():
                fill_color = "#ff0000"
                border_color = "#000000"

            # ((       )    (   ))####)
            self.bordered_round_rectangle(bbox=(x1 + width + state_width + time_width,
                                                y1,
                                                x1 + width + state_width + time_width + timeout_width,
                                                y1 + height * 2 + outset * 2),
                                          radius=radius, outset=outset,
                                          fill=fill_color,
                                          border=border_color)

        # ((       )####(   ))    )
        self.bordered_round_rectangle(bbox=(x1 + width,
                                            y1,
                                            x1 + width + state_width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=self.color("fill"),
                                      border=self.color("border"))

        # ((#######)    (   ))    )
        self.bordered_round_rectangle(bbox=(x1,
                                            y1,
                                            x1 + width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=None,
                                      fill_t=self.get('left', 'color'),
                                      fill_b=self.get('right', 'color'),
                                      border=None,
                                      border_t=self.get('right', 'color'),
                                      border_b=self.get('left', 'color'))

        # ((       )    (###))    )
        time_fill = self.color("fill")
        time_border=self.color("border")
        if (self.mgr.timeoutStateWhite() or
            self.mgr.timeoutStateBlack()):
            time_fill = "#ffff00"
            time_border = "#000000"
        self.bordered_round_rectangle(bbox=(x1 + width + state_width,
                                            y1,
                                            x1 + width + state_width + time_width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=time_fill,
                                      border=time_border)

        logo = Image.open('res/logo-nationals2018.png')
        size = 100
        logo = logo.resize((size, size), Image.ANTIALIAS)
        self.logo = ImageTk.PhotoImage(logo)
        self.create_image(self.w - x1, y1, anchor=tk.NE, image=self.logo)

        # Flags
        left_flag = self.get('left', 'flag')
        if left_flag is not None:
            left_flag = left_flag.resize((flag_width, height + outset), Image.ANTIALIAS)
            self._left_flag = ImageTk.PhotoImage(left_flag)
            self.create_image(x1 + width - score_width, y1, anchor=tk.NE, image=self._left_flag)

        right_flag = self.get('right', 'flag')
        if right_flag is not None:
            right_flag = right_flag.resize((flag_width, height + outset), Image.ANTIALIAS)
            self._right_flag = ImageTk.PhotoImage(right_flag)
            self.create_image(x1 + width - score_width, y1 + height + outset, anchor=tk.NE, image=self._right_flag)

        # Scores Fill
        self.round_rectangle(bbox=(x1 + score_offset,
                                   y1,
                                   x1 + score_offset + score_width,
                                   y1 + height + outset),
                             radius=score_radius, fill=self.get('left', 'color'))
        self.round_rectangle(bbox=(x1 + score_offset,
                                   y1 + height + outset,
                                   x1 + score_offset + score_width,
                                   y1 + height * 2 + outset * 2),
                             radius=score_radius, fill=self.get('right', 'color'))

        # Timeout
        timeout_text=""
        text_color = self.color('fill_text')
        if self.mgr.timeoutStateRef():
            timeout_text="Ref\nTimeout"
            text_color="#000000"
        elif self.mgr.timeoutStateWhite():
            timeout_text="White\nTimeout"
            text_color="#000000"
        elif self.mgr.timeoutStateBlack():
            timeout_text="Black\nTimeout"
            text_color="#ffffff"
        elif self.mgr.timeoutStatePenaltyShot():
            timeout_text="Penalty\nShot"
            text_color="#000000"
        self.create_text((x1 + width + state_width + time_width + 30, y1 + height + outset * 2),
                        text=timeout_text, fill=text_color, font=state_font, anchor=tk.W)

        # Game State Text
        state_text=""
        if self.mgr.gameStatePreGame():
            state_text="Pre\nGame"
        if self.mgr.gameStateFirstHalf():
            state_text="1st\nHalf"
        elif self.mgr.gameStateSecondHalf():
            state_text="2nd\nHalf"
        elif self.mgr.gameStateHalfTime():
            state_text="Half\nTime"
        elif self.mgr.gameStateGameOver():
            state_text="Game\nOver"
        self.create_text((x1 + width + outset + 20, y1 + height + outset),
                        text=state_text, fill=self.color("fill_text"), font=state_font, anchor=tk.W)

        # Time Text
        time_fill=self.color("fill_text")
        if (self.mgr.timeoutStateWhite() or
            self.mgr.timeoutStateBlack()):
            time_fill = "#000000"
        clock_time = self.mgr.gameClock()
        clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
        self.create_text((x1 + width + state_width + time_width / 2, y1 + height + outset * 3),
                         text=clock_text, fill=time_fill,
                         font=time_font, anchor=tk.CENTER)

        # White Score Text
        left_score = self.get('left', 'score')
        l_score="%d" % (left_score,)
        self.create_text((x1 + score_offset + score_width / 2, y1 + height / 2 + outset),
                         text=l_score, fill=self.get('right', 'color'),
                         font=score_font)

        # Black Score Text
        right_score = self.get('right', 'score')
        r_score="%d" % (right_score,)
        self.create_text((x1 + score_offset + score_width / 2,
                          y1 + height / 2 + height + outset * 2),
                         text=r_score, fill=self.get('left', 'color'),
                         font=score_font)

        # Team Names
        white_team=self.abbreviate(self.get('left', 'name'))
        self.create_text((x1 + 10, y1 + outset + height / 2), text=white_team,
                         fill=self.get('right','color'), anchor=tk.W, font=font)

        black_team=self.abbreviate(self.get('right', 'name'))
        self.create_text((x1 + 10, y1 + height + outset * 2 + height / 2), text=black_team,
                         fill=self.get('left', 'color'), anchor=tk.W, font=font)

        # Sin-bin
        penalties = self.mgr.penalties(TeamColor.white) + self.mgr.penalties(TeamColor.black)
        if len(penalties) > 0:
            penalties.sort(key=lambda p: p.timeRemaining(self.mgr))

            inset = 0
            v_spacing = 45
            penalty_height = 30

            y_offset = 10
            for p in penalties:
                if p.servedCompletely(self.mgr):
                    continue

                if p.team() == TeamColor.black:
                    roster = self.black_roster
                else:
                    roster = self.white_roster

                name = None
                if roster is not None:
                    for player in roster:
                        if p.player() == player['number']:
                            name = player['name']
                            break

                if name is not None:
                    name = self.abbreviate(name, 32)
                    penalty_width = width
                else:
                    name = ""
                    penalty_width = 120

                fill_color = "#000000" if p.team() == TeamColor.black else "#ffffff"
                text_color = "#ffffff" if p.team() == TeamColor.black else "#000000"
                self.bordered_round_rectangle(bbox=(x1 + inset, y1 + height * 3 + y_offset - penalty_height / 2,
                                                    x1 + penalty_width - inset,
                                                    y1 + height * 3 + y_offset + penalty_height / 2),
                                              radius=radius, fill=fill_color, border="#ff0000",
                                              outset=outset)

                penalty_text = "#%d - %s" % (p.player(), name)
                self.create_text((x1, y1 + height * 3 + y_offset), text=penalty_text,
                                 fill=text_color, anchor=tk.W, font=font)

                if p.dismissed():
                    penalty_text = "X"
                else:
                    remaining = p.timeRemaining(self.mgr)
                    penalty_text = "%d:%02d" % (remaining // 60, remaining % 60)
                self.create_text((x1 + penalty_width, y1 + height * 3 + y_offset), text=penalty_text,
                                 fill=text_color, anchor=tk.E, font=font)


                y_offset += v_spacing

    def roster_view(self):
        if (not self.mgr.gameStateGameOver() and
            not self.mgr.gameStatePreGame()):
            return False

        if (self.game is None and
            self.tournament is None):
            return False

        font=("Avenir Next LT Pro", 20)
        team_font=("Avenir Next LT Pro", 20, "bold")
        players_font=("Avenir Next LT Pro", 15)
        title_font=("Avenir Next LT Pro", 20, "bold")

        if self.game is not None:
            bar_width = 1100
            title_width = 250
            col_spread = 400
        else:
            bar_width = 1200
            title_width = 450
            col_spread = 450

        radius = 10
        outset = 3
        center_x = self.w / 2
        left_col = center_x - col_spread
        right_col = center_x + col_spread
        flag_width = 150
        col_width = (bar_width - title_width - flag_width * 2) / 2
        roster_y = 425
        bar_y = 300
        title_y = bar_y
        bar_height = 100
        title_height = bar_height
        flags_y = bar_y
        player_h = 25

        # Worlds
        #self.logo = ImageTk.PhotoImage(Image.open('res/worlds-roster-logo.png'))
        #self.create_image(center_x, 80, anchor=tk.N, image=self.logo)

        # Nationals
        logo = Image.open('res/logo-nationals2018.png')
        logo = logo.resize((400, 400), Image.ANTIALIAS)
        self.logo = ImageTk.PhotoImage(logo)
        self.create_image(center_x, 625, anchor=tk.CENTER, image=self.logo)

        # Navisjon
        navisjon = Image.open('res/navisjon.png')
        navisjon = navisjon.resize((400, 100), Image.ANTIALIAS)
        self.navisjon = ImageTk.PhotoImage(navisjon)
        self.create_image(self.w / 2, self.h - 150, anchor=tk.CENTER, image=self.navisjon)

        self.bordered_round_rectangle(bbox=(center_x - bar_width / 2,
                                            bar_y,
                                            center_x + bar_width / 2,
                                            bar_y + bar_height),
                                      radius=radius, outset=outset,
                                      fill=self.color('fill'),
                                      border=self.color("border"))

        # Flags
        left_flag = self.get('left', 'flag')
        if left_flag is not None:
            left_flag = left_flag.resize((flag_width, title_height), Image.ANTIALIAS)
            self._left_flag = ImageTk.PhotoImage(left_flag)
            self.create_image(center_x - title_width / 2, title_y, anchor=tk.NE, image=self._left_flag)

            self.bordered_round_rectangle(bbox=(center_x - bar_width / 2,
                                                bar_y,
                                                center_x - title_width / 2 - flag_width,
                                                bar_y + bar_height),
                                          radius=radius, outset=outset,
                                          fill=self.get('left', 'color'),
                                          border=self.get('right', 'color'))

        right_flag = self.get('right', 'flag')
        if right_flag is not None:
            right_flag = right_flag.resize((flag_width, title_height), Image.ANTIALIAS)
            self._right_flag = ImageTk.PhotoImage(right_flag)
            self.create_image(center_x + title_width / 2, title_y, anchor=tk.NW, image=self._right_flag)

            self.bordered_round_rectangle(bbox=(center_x + title_width / 2 + flag_width,
                                                bar_y,
                                                center_x + bar_width / 2,
                                                bar_y + bar_height),
                                          radius=radius, outset=outset,
                                          fill=self.get('right', 'color'),
                                          border=self.get('left', 'color'))

        self.bordered_round_rectangle(bbox=(center_x - title_width / 2,
                                            title_y,
                                            center_x + title_width / 2,
                                            title_y + title_height),
                                      radius=radius, outset=outset,
                                      fill=self.color('fill'),
                                      border=self.color("border"))

        # Team Names
        name = self.get('left', 'name')
        if name is not None:
            self.create_text((center_x - bar_width / 2 + col_width / 2, bar_y + bar_height / 2), text=name,
                             fill=self.get('right', 'color'), font=team_font, anchor=tk.CENTER)

        name = self.get('right', 'name')
        if name is not None:
            self.create_text((center_x + bar_width / 2 - col_width / 2, bar_y + bar_height / 2), text=name,
                             fill=self.get('left', 'color'), font=team_font, anchor=tk.CENTER)

        roster = self.get('left', 'roster')
        if roster is not None:
            y_offset = 0
            for player in roster:
                self.round_rectangle(bbox=(left_col - col_width / 2 - radius * 2, roster_y + y_offset,
                                           left_col + col_width / 2 - radius * 2, roster_y + y_offset + player_h),
                                     radius=radius, fill=self.get('left', 'color'))

                number = player['number']
                name = player['name']

                display_text = "#{} - {}".format(number, name)
                self.create_text((left_col - col_width / 2 + radius * 2, roster_y + y_offset + player_h / 2), text=display_text,
                                 fill=self.get('right', 'color'), font=players_font,
                                 anchor=tk.W)
                y_offset += 40

        roster = self.get('right', 'roster')
        if roster is not None:
            y_offset = 0
            for player in roster:
                self.round_rectangle(bbox=(right_col - col_width / 2 + radius * 2, roster_y + y_offset,
                                           right_col + col_width / 2 + radius * 2, roster_y + y_offset + player_h),
                                     radius=radius, fill=self.get('right', 'color'))

                number = player['number']
                name = player['name']

                display_text = "#{} - {}".format(number, name)
                self.create_text((right_col - col_width / 2 + radius * 2, roster_y + y_offset + player_h / 2), text=display_text,
                                 fill=self.get('left', 'color'), font=players_font,
                                 anchor=tk.W)
                y_offset += 40

        # Tournament / Game info
        if self.game is not None:
            game_type = self.game['game_type']
            game_type = {
                "RR" : "Round Robin",
                "CO" : "Crossover",
                "BR" : "Bracket",
                "E"  : "Exhibition",
            }.get(game_type, game_type)

            top_text = "{} #{}".format(game_type, self.gid)
            self.create_text((center_x, bar_y + bar_height / 4), text=top_text,
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

            from datetime import datetime
            import calendar
            start = datetime.strptime(self.game['start_time'], "%Y-%m-%dT%H:%M:%S")
            bottom_text = "Pool {}, {} {}".format(self.game['pool'],
                                                  calendar.day_abbr[start.weekday()],
                                                  start.strftime("%H:%M"))

            self.create_text((center_x, bar_y + 3 * bar_height / 4), text=bottom_text,
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

        elif self.tournament is not None:
            self.create_text((center_x, bar_y + bar_height / 4), text=self.tournament['name'],
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

            self.create_text((center_x, bar_y + 3 * bar_height / 4), text=self.tournament['location'],
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

        return True


def is_rpi():
    return os.uname().machine == 'armv7l'

def maybe_hide_cursor(root):
    # Don't show a cursor on Pi.
    if is_rpi():
        root.configure(cursor='none')

class Overlay(object):
    def __init__(self, mgr, mask, version, demo):
        self.root = tk.Tk()
        # make it cover the entire screen
        #w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = 1920, 1080
        self.ov = OverlayView(self.root, (w, h), mgr, mask, version, demo)
        self.root.geometry("%dx%d-0+0" % (w, h))
        self.root.attributes('-fullscreen', True)

        self.root.overrideredirect(1)

        maybe_hide_cursor(self.root)

    @staticmethod
    def versions():
        return OverlayView.versions()

    def mainloop(self):
        def quit(event):
            print("Quitting...")
            self.root.quit()
        try:
            self.root.bind('<Control-c>', quit)
            self.root.bind('<Escape>', quit)
            self.root.mainloop()
        except KeyboardInterrupt:
            quit(None)
