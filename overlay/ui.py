#!/usr/bin/env python

from multiprocessing import Process, Queue
from datetime import datetime
import tkinter as tk
from uwh.gamemanager import PoolLayout, TeamColor
from uwh.uwhscores_comms import UWHScores
from PIL import Image, ImageTk

import time
import sys

class MaskKind:
    NONE, LUMA, CHROMA, VMAC = range(4)

def sized_frame(master, height, width):
    F = tk.Frame(master, height=height, width=width)
    F.pack_propagate(0)
    return F

class OverlayView(tk.Canvas):
    def __init__(self, parent, bbox, mgr, mask, version):
        tk.Canvas.__init__(self, parent)

        self.parent = parent
        self.root = parent
        self.mgr = mgr
        self.mask = mask
        self.version = version

        #self.uwhscores = UWHScores('https://uwhscores.com/api/v1/', mock=True)
        self.uwhscores = UWHScores('http://localhost:5000/api/v1/', mock=False)
        self.tid = None
        self.gid = None
        self.white_id = None
        self.black_id = None
        self.white_name = None
        self.black_name = None
        self.white_roster = None
        self.black_roster = None
        self.tournament = None
        self.black_flag = None
        self.white_flag = None

        self.init_ui(bbox)

    def init_ui(self, bbox):
        self.parent.title("TimeShark Scores")
        self.pack(fill=tk.BOTH, expand=1)

        self.w = bbox[0]
        self.h = bbox[1]

        self.refresh = 100
        self.t = 0
        def draw(self):
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
        self.after(1, lambda : draw(self))

    def clear(self, fill):
        self.create_rectangle((0, 0, self.w, self.h), fill=fill)

    def round_rectangle(self, bbox, radius, fill):
        x1, y1, x2, y2 = bbox
        self.create_oval((x1 - radius, y1, x1 + radius, y2), fill=fill, outline=fill)
        self.create_oval((x2 - radius, y1, x2 + radius, y2), fill=fill, outline=fill)
        self.create_rectangle(bbox, fill=fill, outline=fill)

    def bordered_round_rectangle(self, bbox, radius, outset, fill, border):
        self.round_rectangle(bbox=(bbox[0]-outset, bbox[1]-outset,
                                   bbox[2]+outset, bbox[3]+outset),
                             radius=radius, fill=border)
        self.round_rectangle(bbox, radius=radius, fill=fill)

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

    def render(self):
        # Update teams between games
        if (self.tid != self.mgr.tid() or
            self.gid != self.mgr.gid()):
            self.tid = self.mgr.tid()
            self.gid = self.mgr.gid()
            self.white_id = None
            self.black_id = None
            self.black_name = "Black"
            self.white_name = "White"
            self.black_roster = None
            self.white_roster = None
            self.tournament = None
            self.black_flag = None
            self.white_flag = None

            def game(response):
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

        if (self.mgr.gameStateGameOver() and self.tournament is not None):
            self.roster_view()
        else:
            self.game_play_view()

    def color(self, name):
        if self.mask == MaskKind.LUMA:
            return "#000000" if name == "bg" else "#ffffff"

        if self.mask == MaskKind.CHROMA and name == "bg":
            return "#00ff00"

        return {
            "bg" : "#054a91",
            "border" : "#ffffff",
            "fill" : "#2e96ff",
            "fill_text" : "#ffffff",
            "black_fill" : "#000000",
            "black_text" : "#2e96ff",
            "white_fill" : "#ffffff",
            "white_text" : "#2e96ff",
            "team_text"  : "#000000",
            "title_text" : "#ffffff",
        }.get(name, "#ff0000")

    def abbreviate(self, s, max_len = 16):
        if len(s) > max_len:
            return s[0:max_len-3] + "..."
        else:
            return s

    def game_play_view(self):
        radius = 5
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

        x1 = 40
        y1 = 40

        font=("Menlo", 20)
        score_font=("Menlo", 30, "bold")
        logo_font=("Menlo", 30)
        time_font=("Menlo", 50)
        state_font=("Menlo", 25)

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

            self.bordered_round_rectangle(bbox=(x1 + width + state_width + time_width,
                                                y1,
                                                x1 + width + state_width + time_width + timeout_width,
                                                y1 + height * 2 + outset * 2),
                                          radius=radius, outset=outset,
                                          fill=fill_color,
                                          border=border_color)

            self.bordered_round_rectangle(bbox=(x1,
                                                y1,
                                                x1 + width + state_width + time_width,
                                                y1 + height * 2 + outset * 2),
                                          radius=radius, outset=outset,
                                          fill=self.color('fill'),
                                          border=self.color("border"))
        else:
            self.bordered_round_rectangle(bbox=(x1,
                                                y1,
                                                x1 + width + state_width + time_width,
                                                y1 + height * 2 + outset * 2),
                                          radius=radius, outset=outset,
                                          fill=self.color("fill"),
                                          border=self.color("border"))

        self.bordered_round_rectangle(bbox=(x1 + width + state_width,
                                            y1,
                                            x1 + width + state_width + time_width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=self.color("fill"),
                                      border=self.color("border"))

        # Flags
        left_flag = self.get('left', 'flag')
        if left_flag is not None:
            left_flag = left_flag.resize((flag_width, height + outset * 2), Image.ANTIALIAS)
            self._left_flag = ImageTk.PhotoImage(left_flag)
            self.create_image(x1 + width - score_width, y1, anchor=tk.NE, image=self._left_flag)

        right_flag = self.get('right', 'flag')
        if right_flag is not None:
            right_flag = right_flag.resize((flag_width, height + outset * 2), Image.ANTIALIAS)
            self._right_flag = ImageTk.PhotoImage(right_flag)
            self.create_image(x1 + width - score_width, y1 + height + outset, anchor=tk.NE, image=self._right_flag)

        # Scores Fill
        self.round_rectangle(bbox=(x1 + score_offset,
                                   y1,
                                   x1 + score_offset + score_width,
                                   y1 + height + outset),
                             radius=score_radius, fill=self.color("%s_fill" % (self.get('left', 'color'),)))
        self.round_rectangle(bbox=(x1 + score_offset,
                                   y1 + height + outset,
                                   x1 + score_offset + score_width,
                                   y1 + height * 2 + outset * 2),
                             radius=score_radius, fill=self.color("%s_fill" % (self.get('right', 'color'),)))

        if not self.mask == MaskKind.LUMA:
            # Timeout
            timeout_text=""
            text_color = self.color('fill_text')
            if self.mgr.timeoutStateRef():
                timeout_text="Ref\nTimeout"
                text_color="#000000"
            elif self.mgr.timeoutStateWhite():
                timeout_text="White\nTimeout"
                text_color=self.color('fill')
            elif self.mgr.timeoutStateBlack():
                timeout_text="Black\nTimeout"
                text_color=self.color('fill')
            elif self.mgr.timeoutStatePenaltyShot():
                timeout_text="Penalty\nShot"
                text_color="#000000"
            self.create_text((x1 + width + state_width + time_width + 30, y1 + height + outset),
                            text=timeout_text, fill=text_color, font=state_font, anchor=tk.W)

            # Game State Text
            state_text=""
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
            clock_time = self.mgr.gameClock()
            clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
            self.create_text((x1 + width + state_width, y1 + height + outset),
                             text=clock_text, fill=self.color("fill_text"),
                             font=time_font, anchor=tk.W)

            # White Score Text
            left_score = self.get('left', 'score')
            l_score="%d" % (left_score,)
            self.create_text((x1 + score_offset + score_width / 2, y1 + height / 2),
                             text=l_score, fill=self.color("%s_text" % (self.get('left', 'color'),)),
                             font=score_font)

            # Black Score Text
            right_score = self.get('right', 'score')
            r_score="%d" % (right_score,)
            self.create_text((x1 + score_offset + score_width / 2,
                              y1 + height / 2 + height + outset * 2),
                             text=r_score, fill=self.color("%s_text" % (self.get('right', 'color'),)),
                             font=score_font)

            # White Team Text
            white_team=self.abbreviate(self.get('left', 'name'))
            self.create_text((x1 + 10, y1 + outset + height / 2), text=white_team,
                             fill=self.color("fill_text"), anchor=tk.W, font=font)

            black_team=self.abbreviate(self.get('right', 'name'))
            self.create_text((x1 + 10, y1 + height + outset * 3 + height / 2), text=black_team,
                             fill=self.color("fill_text"), anchor=tk.W, font=font)

            # Sin-bin
            penalties = self.mgr.penalties(TeamColor.white) + self.mgr.penalties(TeamColor.black)
            if len(penalties) > 0:
                penalties.sort(key=lambda p: p.timeRemaining(self.mgr))

                inset = 0
                v_spacing = 40
                penalty_height = 30

                y_offset = 0
                for p in penalties:
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
                        penalty_width = width + state_width + time_width
                    else:
                        name = ""
                        penalty_width = 120

                    fill_color = "#000000" if p.team() == TeamColor.black else "#ffffff"
                    self.round_rectangle(bbox=(x1 + inset, y1 + height * 3 + y_offset - penalty_height / 2,
                                               x1 + penalty_width - inset,
                                               y1 + height * 3 + y_offset + penalty_height / 2),
                                         radius=radius, fill=fill_color)

                    penalty_text = "#%d - %s" % (p.player(), name)
                    self.create_text((x1, y1 + height * 3 + y_offset), text=penalty_text,
                                     fill=self.color("fill"), anchor=tk.W, font=font)

                    remaining = p.timeRemaining(self.mgr)
                    penalty_text = "%d:%02d" % (remaining // 60, remaining % 60)
                    self.create_text((x1 + penalty_width, y1 + height * 3 + y_offset), text=penalty_text,
                                     fill=self.color("fill"), anchor=tk.E, font=font)


                    y_offset += v_spacing

    def roster_view(self):
        font=("Menlo", 20)
        score_font=("Menlo", 30, "bold")
        logo_font=("Menlo", 30)
        time_font=("Menlo", 30)
        state_font=("Menlo", 40)
        team_font=("Menlo", 30, "bold")
        players_font=("Menlo", 20)
        title_font=("Menlo", 25, "bold")

        if not self.mask == MaskKind.LUMA:
            radius = 5
            outset = 3
            center_x = self.w / 2
            col_spread = 300
            left_col = center_x - col_spread
            right_col = center_x + col_spread
            col_width = 300
            flag_width = 150
            roster_y = 625
            bar_y = 500
            title_y = bar_y
            bar_width = 1000
            bar_height = 100
            title_width = col_spread
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
            self.create_image(center_x, 1080 / 4, anchor=tk.CENTER, image=self.logo)

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
            name_width = (bar_width - title_width - flag_width * 2) / 2
            name = self.get('left', 'name')
            if name is not None:
                name_fill = self.color("fill") if left_flag else "#ffffff"
                self.create_text((center_x - bar_width / 2 + name_width / 2, bar_y + bar_height / 2), text=name,
                                 fill=name_fill, font=team_font, anchor=tk.CENTER)

            name = self.get('right', 'name')
            if name is not None:
                name_fill = self.color("fill") if left_flag else "#ffffff"
                self.create_text((center_x + bar_width / 2 - name_width / 2, bar_y + bar_height / 2), text=name,
                                 fill=name_fill, font=team_font, anchor=tk.CENTER)

            roster = self.get('left', 'roster')
            if roster is not None:
                y_offset = 0
                for player in roster:
                    self.round_rectangle(bbox=(left_col - col_width / 2, roster_y + y_offset,
                                               left_col + col_width / 2, roster_y + y_offset + player_h),
                                         radius=radius, fill=self.get('left', 'color'))

                    number = player['number']
                    name = player['name']

                    display_text = "#{} - {}".format(number, name)
                    self.create_text((left_col - col_width / 2, roster_y + y_offset + player_h / 2), text=display_text,
                                     fill=self.color("fill"), font=players_font,
                                     anchor=tk.W)
                    y_offset += 40

            roster = self.get('right', 'roster')
            if roster is not None:
                y_offset = 0
                for player in roster:
                    self.round_rectangle(bbox=(right_col - col_width / 2, roster_y + y_offset,
                                               right_col + col_width / 2, roster_y + y_offset + player_h),
                                         radius=radius, fill=self.get('right', 'color'))

                    number = player['number']
                    name = player['name']

                    display_text = "#{} - {}".format(number, name)
                    self.create_text((right_col - col_width / 2, roster_y + y_offset + player_h / 2), text=display_text,
                                     fill=self.color("fill"), font=players_font,
                                     anchor=tk.W)
                    y_offset += 40

            # Tournament info
            if self.tournament is not None:
                self.create_text((center_x, bar_y + bar_height / 4), text=self.tournament['name'],
                                 fill=self.color("title_text"), font=title_font,
                                 anchor=tk.CENTER)

                self.create_text((center_x, bar_y + 3 * bar_height / 4), text=self.tournament['location'],
                                 fill=self.color("title_text"), font=title_font,
                                 anchor=tk.CENTER)


class Overlay(object):
    def __init__(self, mgr, mask, version):
        self.root = tk.Tk()
        # make it cover the entire screen
        #w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = 1920, 1080
        self.ov = OverlayView(self.root, (w, h), mgr, mask, version)
        self.root.geometry("%dx%d-0+0" % (w, h))
        #self.root.attributes('-fullscreen', True)

    @staticmethod
    def versions():
        return OverlayView.versions()

    def mainloop(self):
        self.root.mainloop()
