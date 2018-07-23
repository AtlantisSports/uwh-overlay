#!/usr/bin/env python

import os
from multiprocessing import Process, Queue
from datetime import datetime
import tkinter as tk
from uwh.gamemanager import PoolLayout, TeamColor, GameState, TimeoutState
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
            def cycle_teams(self):
                self.mgr.setGid(max((self.mgr.gid() + 1) % 272, 1))
                self.after(2500, lambda : cycle_teams(self))
            self.after(1, lambda : cycle_teams(self))

            def cycle_goal_black(self):
                self.mgr.addBlackGoal(5)
                self.after(3000, lambda : cycle_goal_white(self))
            def cycle_goal_white(self):
                self.mgr.addWhiteGoal(5)
                self.after(3000, lambda : cycle_goal_black(self))
            self.after(1, lambda : cycle_goal_black(self))

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

    def bordered_circle(self, bbox, outset, fill, border):
        self.create_oval(bbox[0]-outset, bbox[1]-outset,
                         bbox[2]+outset, bbox[3]+outset,
                         fill=border)
        self.create_oval(bbox[0], bbox[1],
                         bbox[2], bbox[3],
                         fill=fill)

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
                self.white_flag = Image.open(flag)
            def black_flag(flag):
                self.black_flag = Image.open(flag)
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

        if (not self.mgr.gameState() == GameState.game_over and
            not self.mgr.gameState() == GameState.pre_game):
            self.game_play_view()

            if self.mgr.gameState() == GameState.half_time:
                self.roster_view(bar_only=900)
                self.gofundme()

        elif (self.game is None and
              self.tournament is None):
            self.game_play_view()

            if self.mgr.gameState() == GameState.half_time:
                self.roster_view(bar_only=900)
                self.gofundme()

        else:
            self.roster_view()

    def gofundme(self):
        height = 100
        width = 325
        radius = 10
        outset = 3

        center_x = self.w * 4 / 5

        logo = Image.open('res/gofundme.png')
        logo = logo.resize((300, 400), Image.ANTIALIAS)
        self.logo = ImageTk.PhotoImage(logo)
        self.create_image(center_x, self.h / 2, anchor=tk.CENTER, image=self.logo)


        self.bordered_round_rectangle(bbox=(center_x - width /2,
                                            self.h * 1 / 4 - height/2,
                                            center_x + width /2,
                                            self.h * 1 / 4 + height/2),
                                      radius=radius, outset=outset,
                                      fill="#000000",
                                      border="#ffffff")

        font = ("Avenir Next LT Pro", 15, "bold")

        self.create_text((center_x, self.h * 1/4 - 25), text="GoFundMe Underwater\nHockey World Champs 2018",
                         fill="#ffffff", font=font, anchor=tk.CENTER)

        font = ("Avenir Next LT Pro", 15, "underline")

        self.create_text((center_x, self.h * 1/4 + 25), text="http://bit.ly/2mzRBFe",
                         fill="#4040ff", font=font, anchor=tk.CENTER)


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
        bar_width = 350
        player_width = 450
        flag_width = 60
        score_width = 50
        score_offset = bar_width - score_width
        time_width = 155
        state_width = 110
        timeout_R_width = 110
        timeout_L_width = 150
        state_offset = score_offset + time_width
        outset = 3

        x1 = 40 + outset
        y1 = 40

        font=("Avenir Next LT Pro", 15, "bold")
        score_font=("Avenir Next LT Pro", 24, "bold")
        time_font=("Avenir Next LT Pro", 40)
        state_font=("Avenir Next LT Pro", 16, "bold")

        # Bottom Rectangle
        if (self.mgr.timeoutState() == TimeoutState.ref or
            self.mgr.timeoutState() == TimeoutState.white or
            self.mgr.timeoutState() == TimeoutState.black or
            self.mgr.timeoutState() == TimeoutState.penalty_shot or
            self.mgr.gameState() == GameState.pre_ot or
            self.mgr.gameState() == GameState.ot_first or
            self.mgr.gameState() == GameState.ot_half or
            self.mgr.gameState() == GameState.ot_second or
            self.mgr.gameState() == GameState.pre_sudden_death or
            self.mgr.gameState() == GameState.sudden_death):
            if self.mgr.timeoutState() == TimeoutState.ref:
                L_fill_color = "#ffff00"
                border_color = "#000000"
            elif self.mgr.timeoutState() == TimeoutState.white:
                R_fill_color = "#ffff00"
                L_fill_color = "#ffffff"
                border_color = "#000000"
            elif self.mgr.timeoutState() == TimeoutState.black:
                R_fill_color = "#ffff00"
                L_fill_color = "#000000"
                border_color = "#ffffff"
            elif (self.mgr.timeoutState() == TimeoutState.penalty_shot or
                  self.mgr.gameState() == GameState.pre_ot or
                  self.mgr.gameState() == GameState.ot_first or
                  self.mgr.gameState() == GameState.ot_half or
                  self.mgr.gameState() == GameState.ot_second or
                  self.mgr.gameState() == GameState.pre_sudden_death or
                  self.mgr.gameState() == GameState.sudden_death):
                L_fill_color = "#ff0000"
                border_color = "#000000"

            if (self.mgr.timeoutState() == TimeoutState.white or
                self.mgr.timeoutState() == TimeoutState.black):

                # ((       )    (   ))    )####)
                self.bordered_round_rectangle(bbox=(x1 + bar_width + state_width + time_width,
                                                    y1,
                                                    x1 + bar_width + state_width + time_width + timeout_L_width + timeout_R_width,
                                                    y1 + height * 2 + outset * 2),
                                              radius=radius, outset=outset,
                                              fill=R_fill_color,
                                              border="#000000")

            # ((       )    (   ))####)
            self.bordered_round_rectangle(bbox=(x1 + bar_width + state_width + time_width,
                                                y1,
                                                x1 + bar_width + state_width + time_width + timeout_L_width,
                                                y1 + height * 2 + outset * 2),
                                          radius=radius, outset=outset,
                                          fill=L_fill_color,
                                          border=border_color)



        # ((       )####(   ))    )
        self.bordered_round_rectangle(bbox=(x1 + bar_width,
                                            y1,
                                            x1 + bar_width + state_width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=self.color("fill"),
                                      border=self.color("border"))

        # ((#######)    (   ))    )
        self.bordered_round_rectangle(bbox=(x1,
                                            y1,
                                            x1 + bar_width,
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
        self.bordered_round_rectangle(bbox=(x1 + bar_width + state_width,
                                            y1,
                                            x1 + bar_width + state_width + time_width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=time_fill,
                                      border=time_border)

        logo = Image.open('res/worlds-cmas-sticker.png')
        size = 130
        logo = logo.resize((size, size), Image.ANTIALIAS)
        self.logo = ImageTk.PhotoImage(logo)
        self.create_image(self.w - x1 + 30, y1, anchor=tk.NE, image=self.logo)

        # Flags
        left_flag = self.get('left', 'flag')
        if left_flag is not None:
            left_flag = left_flag.resize((flag_width, height + outset), Image.ANTIALIAS)
            self._left_status_flag = ImageTk.PhotoImage(left_flag)
            self.create_image(x1 + bar_width - score_width, y1, anchor=tk.NE, image=self._left_status_flag)

        right_flag = self.get('right', 'flag')
        if right_flag is not None:
            right_flag = right_flag.resize((flag_width, height + outset), Image.ANTIALIAS)
            self._right_status_flag = ImageTk.PhotoImage(right_flag)
            self.create_image(x1 + bar_width - score_width, y1 + height + outset, anchor=tk.NE, image=self._right_status_flag)

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
        if self.mgr.timeoutState() == TimeoutState.ref:
            timeout_text="Ref\nTimeout"
            text_color="#000000"
        elif self.mgr.timeoutState() == TimeoutState.white:
            timeout_text="White\nTimeout"
            text_color="#000000"
        elif self.mgr.timeoutState() == TimeoutState.black:
            timeout_text="Black\nTimeout"
            text_color="#ffffff"
        elif self.mgr.timeoutState() == TimeoutState.penalty_shot:
            timeout_text="Penalty\nShot"
            text_color="#000000"
        elif (self.mgr.gameState() == GameState.pre_ot or
              self.mgr.gameState() == GameState.ot_first or
              self.mgr.gameState() == GameState.ot_half or
              self.mgr.gameState() == GameState.ot_second):
            timeout_text="Overtime"
            text_color="#000000"
        elif (self.mgr.gameState() == GameState.pre_sudden_death or
              self.mgr.gameState() == GameState.sudden_death):
            timeout_text="Sudden\nDeath"
            text_color="#000000"
        self.create_text((x1 + bar_width + state_width + time_width + 30, y1 + height + outset * 2),
                        text=timeout_text, fill=text_color, font=state_font, anchor=tk.W)

        if (self.mgr.timeoutState() == TimeoutState.white or
            self.mgr.timeoutState() == TimeoutState.black):
            clock_time = self.mgr.gameClock()
            clock_text = "%02d" % (clock_time,)
            self.create_text((x1 + bar_width + state_width + time_width +timeout_L_width + 30, y1 + height + outset * 2),
                             text=clock_time, fill="#000000", font=time_font, anchor=tk.W)

        # Game State Text
        state_text=""
        if self.mgr.gameState() == GameState.pre_game:
            state_text="Pre\nGame"
        if (self.mgr.gameState() == GameState.first_half or
            self.mgr.gameState() == GameState.ot_first):
            state_text="1st\nHalf"
        elif (self.mgr.gameState() == GameState.second_half or
            self.mgr.gameState() == GameState.ot_second):
            state_text="2nd\nHalf"
        elif (self.mgr.gameState() == GameState.half_time or
              self.mgr.gameState() == GameState.ot_half):
            state_text="Half\nTime"
        elif self.mgr.gameState() == GameState.game_over:
            state_text="Game\nOver"
        elif (self.mgr.gameState() == GameState.pre_ot or
              self.mgr.gameState() == GameState.pre_sudden_death):
            state_text="Break"
        self.create_text((x1 + bar_width + outset + 25, y1 + height + outset),
                        text=state_text, fill=self.color("fill_text"), font=state_font, anchor=tk.W)

        # Time Text
        time_fill=self.color("fill_text")
        clock_time = self.mgr.gameClockAtPause()
        clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
        self.create_text((x1 + bar_width + state_width + time_width / 2, y1 + height + outset * 3),
                         text=clock_text, fill=time_fill,
                         font=time_font, anchor=tk.CENTER)

        # White Score Text
        left_score = self.get('left', 'score')
        l_score="%d" % (left_score,)
        self.create_text((x1 + score_offset + score_width / 2 + 3, y1 + height / 2 + outset),
                         text=l_score, fill=self.get('right', 'color'),
                         font=score_font, anchor=tk.CENTER)

        # Black Score Text
        right_score = self.get('right', 'score')
        r_score="%d" % (right_score,)
        self.create_text((x1 + score_offset + score_width / 2 + 3,
                          y1 + height / 2 + height + outset * 2),
                         text=r_score, fill=self.get('left', 'color'),
                         font=score_font, anchor=tk.CENTER)

        # Team Names
        white_team=self.abbreviate(self.get('left', 'name'))
        self.create_text((x1 + 10, y1 + outset + height / 2), text=white_team,
                         fill=self.get('right','color'), anchor=tk.W, font=font)

        black_team=self.abbreviate(self.get('right', 'name'))
        self.create_text((x1 + 10, y1 + height + outset * 2 + height / 2), text=black_team,
                         fill=self.get('left', 'color'), anchor=tk.W, font=font)

        def player_name(player_no, team):
            if team == TeamColor.black:
                roster = self.black_roster
            else:
                roster = self.white_roster

            if roster is not None:
                for player in roster:
                    if player_no == player['number']:
                        return player['name']
            return None

        # Goals
        inset = 0
        y_offset = 0

        goal_height = 50
        v_spacing = 15

        def recent_goal(g):
            state_idx = {
                GameState.pre_game :     0,
                GameState.first_half :   1,
                GameState.half_time :    2,
                GameState.second_half :  3,
                GameState.pre_ot :       4,
                GameState.ot_first :     5,
                GameState.ot_half :      6,
                GameState.ot_second :    7,
                GameState.pre_sudden_death : 8,
                GameState.sudden_death : 9,
                GameState.game_over :   10,
            }
            return (state_idx[self.mgr.gameState()] -
                    state_idx[g.state()]) <= 1

        goals = [g for g in self.mgr.goals() if recent_goal(g)]
        if len(goals) > 0:
            goals = sorted(goals, key=lambda g: g.goal_no())

            g = goals[-1]
            number = len(goals)

            # Display goals for at most 30 seconds after they were scored
            if g.time() - 30 < self.mgr.gameClockAtPause():

                name = player_name(g.player(), g.team())
                if name is not None:
                    name = self.abbreviate(name, 28)
                    goal_width = player_width
                else:
                    name = ""
                    goal_width = 120

                fill_color = "#000000" if g.team() == TeamColor.black else "#ffffff"
                text_color = "#ffffff" if g.team() == TeamColor.black else "#000000"
                self.bordered_round_rectangle(bbox=(x1 + inset, y1 + height * 3 + y_offset,
                                                    x1 + goal_width - inset,
                                                    y1 + height * 3 + y_offset + goal_height),
                                              radius=radius, fill=fill_color, border=text_color,
                                              outset=outset)

                goal_text = "Goal: #%d - %s" % (g.player(), name)
                self.create_text((x1, y1 + height * 3 + y_offset + goal_height / 2), text=goal_text,
                                 fill=text_color, anchor=tk.W, font=font)

                y_offset += goal_height + v_spacing

        # Sin-bin
        penalty_height = 30

        penalties = self.mgr.penalties(TeamColor.white) + self.mgr.penalties(TeamColor.black)
        if len(penalties) > 0:
            penalties.sort(key=lambda p: p.player())
            penalties.sort(key=lambda p: p.timeRemaining(self.mgr))

            for p in penalties:
                if p.servedCompletely(self.mgr):
                    continue

                name = player_name(p.player(), p.team())
                if name is not None:
                    name = self.abbreviate(name, 28)
                    penalty_width = player_width
                else:
                    name = ""
                    penalty_width = 120

                fill_color = "#000000" if p.team() == TeamColor.black else "#ffffff"
                text_color = "#ffffff" if p.team() == TeamColor.black else "#000000"
                self.bordered_round_rectangle(bbox=(x1 + inset, y1 + height * 3 + y_offset,
                                                    x1 + penalty_width - inset,
                                                    y1 + height * 3 + y_offset + penalty_height),
                                              radius=radius, fill=fill_color, border="#ff0000",
                                              outset=outset)

                penalty_text = "#%d - %s" % (p.player(), name)
                self.create_text((x1, y1 + height * 3 + y_offset + penalty_height / 2), text=penalty_text,
                                 fill=text_color, anchor=tk.W, font=font)

                if p.dismissed():
                    penalty_text = "X"
                else:
                    remaining = p.timeRemaining(self.mgr)
                    penalty_text = "%d:%02d" % (remaining // 60, remaining % 60)
                self.create_text((x1 + penalty_width, y1 + height * 3 + y_offset + penalty_height / 2), text=penalty_text,
                                 fill=text_color, anchor=tk.E, font=font)

                y_offset += penalty_height + v_spacing


    def roster_view(self, bar_only=None):
        font=("Avenir Next LT Pro", 20)
        team_font=("Avenir Next LT Pro", 35, "bold")
        players_font=("Avenir Next LT Pro", 20, "bold")
        title_font=("Avenir Next LT Pro", 20, "bold")

        if self.game is not None:
            bar_width = 1600
            title_width = 250
            col_spread = 525
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
        roster_y = 250

        if bar_only is not None:
            bar_y = bar_only
        else:
            bar_y = 100 if self.mgr.gameState() == GameState.pre_game else 725

        title_y = bar_y
        bar_height = 100
        title_height = bar_height
        flags_y = bar_y
        player_h = 40

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
            self._left_bar_flag = ImageTk.PhotoImage(left_flag)
            self.create_image(center_x - title_width / 2, title_y, anchor=tk.NE, image=self._left_bar_flag)

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
            self._right_bar_flag = ImageTk.PhotoImage(right_flag)
            self.create_image(center_x + title_width / 2, title_y, anchor=tk.NW, image=self._right_bar_flag)

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

        # Tournament / Game info
        if self.game is not None:

            if self.tid == 17:
                if 200 <= self.gid:
                    top_text = "#PO" + str(self.gid)
                else:
                    top_text = "#" + str(self.gid)
            else:
                game_type = self.game['game_type']
                game_type = {
                    "RR" : "Round Robin",
                    "CO" : "Crossover",
                    "BR" : "Bracket",
                    "E"  : "Exhibition",
                }.get(game_type, game_type)
                top_text = "{} #{}".format(game_type, self.gid)

            self.create_text((center_x, bar_y + bar_height / 4 - 5), text=top_text,
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

            if self.tid == 17:
                if self.game['description'] is not None:
                    self.create_text((center_x, bar_y + bar_height / 2),
                                     text=self.game['description'],
                                     fill=self.color("title_text"), font=title_font,
                                     anchor=tk.CENTER)

            game_state = ""
            if self.mgr.gameState() == GameState.game_over:
                game_state = "Final Scores"
            elif self.mgr.gameState() == GameState.half_time:
                game_state = "Half Time"
            self.create_text((center_x, bar_y + bar_height / 2), text=game_state,
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

            from datetime import datetime
            import calendar
            start = datetime.strptime(self.game['start_time'], "%Y-%m-%dT%H:%M:%S")
            bottom_text = "Pool {}, {} {}".format(self.game['pool'],
                                                  calendar.day_abbr[start.weekday()],
                                                  start.strftime("%H:%M"))

            self.create_text((center_x, bar_y + 3 * bar_height / 4 + 5), text=bottom_text,
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

        elif self.tournament is not None:
            self.create_text((center_x, bar_y + bar_height / 4 - 5), text=self.tournament['name'],
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

            game_state = ""
            if self.mgr.gameState() == GameState.game_over:
                game_state = "Final Scores"
            elif self.mgr.gameState() == GameState.half_time:
                game_state = "Half Time"
            self.create_text((center_x, bar_y + bar_height / 2), text=game_state,
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

            self.create_text((center_x, bar_y + 3 * bar_height / 4 + 5), text=self.tournament['location'],
                             fill=self.color("title_text"), font=title_font,
                             anchor=tk.CENTER)

        if bar_only is not None:
            return

        # Roster
        if self.mgr.gameState() == GameState.pre_game:
            roster = self.get('left', 'roster')
            if roster is not None:
                y_offset = 0
                roster.sort(key=lambda p: p['number'])
                for player in roster:
                    self.round_rectangle(bbox=(left_col - col_width / 2 - radius, roster_y + y_offset,
                                               left_col + col_width / 2 - radius, roster_y + y_offset + player_h),
                                         radius=radius, fill=self.get('left', 'color'))

                    number = player['number']
                    name = player['name']

                    name = self.abbreviate(name, 26)
                    display_text = "#{} - {}".format(number, name)
                    self.create_text((left_col - col_width / 2, roster_y + y_offset + player_h / 2), text=display_text,
                                     fill=self.get('right', 'color'), font=players_font,
                                     anchor=tk.W)
                    y_offset += 60

            roster = self.get('right', 'roster')
            if roster is not None:
                y_offset = 0
                roster.sort(key=lambda p: p['number'])
                for player in roster:
                    self.round_rectangle(bbox=(right_col - col_width / 2 + radius, roster_y + y_offset,
                                               right_col + col_width / 2 + radius, roster_y + y_offset + player_h),
                                         radius=radius, fill=self.get('right', 'color'))

                    number = player['number']
                    name = player['name']

                    name = self.abbreviate(name, 26)
                    display_text = "#{} - {}".format(number, name)
                    self.create_text((right_col - col_width / 2 + radius * 2, roster_y + y_offset + player_h / 2), text=display_text,
                                     fill=self.get('left', 'color'), font=players_font,
                                     anchor=tk.W)
                    y_offset += 60

            # Worlds
            logo = Image.open('res/logo-worlds2018.png')
            scale = 400 / 1500
            logo = logo.resize((int(1500 * scale), int(900 * scale)), Image.ANTIALIAS)
            self.logo = ImageTk.PhotoImage(logo)
            self.create_image(center_x, 550, anchor=tk.CENTER, image=self.logo)

            # Nationals
            #logo = Image.open('res/logo-nationals2018.png')
            #logo = logo.resize((400, 400), Image.ANTIALIAS)
            #self.logo = ImageTk.PhotoImage(logo)
            #self.create_image(center_x, 625, anchor=tk.CENTER, image=self.logo)

            # Navisjon
            navisjon = Image.open('res/navisjon.png')
            navisjon = navisjon.resize((400, 100), Image.ANTIALIAS)
            self.navisjon = ImageTk.PhotoImage(navisjon)
            self.create_image(self.w / 2, self.h - 150, anchor=tk.CENTER, image=self.navisjon)
        else:
            score_y = 500
            score_radius = 300
            score_font=("Avenir Next LT Pro", 160, "bold")
            self.bordered_circle(bbox=(center_x - col_spread - score_radius / 2, score_y - score_radius / 2,
                                       center_x - col_spread + score_radius / 2, score_y + score_radius / 2),
                                 fill=self.get('left', 'color'),
                                 border=self.get('right', 'color'),
                                 outset=outset)
            self.bordered_circle(bbox=(center_x + col_spread - score_radius / 2, score_y - score_radius / 2,
                                       center_x + col_spread + score_radius / 2, score_y + score_radius / 2),
                                 fill=self.get('right', 'color'),
                                 border=self.get('left', 'color'),
                                 outset=outset)
            self.create_text((center_x - col_spread, score_y + 20), text=self.get('left', 'score'),
                             fill=self.get('right', 'color'), font=score_font, anchor=tk.CENTER)
            self.create_text((center_x + col_spread, score_y + 20), text=self.get('right', 'score'),
                             fill=self.get('left', 'color'), font=score_font, anchor=tk.CENTER)

            # Worlds
            logo = Image.open('res/logo-worlds2018.png')
            scale = 400 / 1500
            logo = logo.resize((int(1500 * scale), int(900 * scale)), Image.ANTIALIAS)
            self.logo = ImageTk.PhotoImage(logo)
            self.create_image(center_x, score_y, anchor=tk.CENTER, image=self.logo)

            # Navisjon
            navisjon = Image.open('res/navisjon.png')
            navisjon = navisjon.resize((400, 100), Image.ANTIALIAS)
            self.navisjon = ImageTk.PhotoImage(navisjon)
            self.create_image(self.w / 2, self.h - 150, anchor=tk.CENTER, image=self.navisjon)


        next_y = self.h - 50
        next_w = 200
        next_h = 50

        self.bordered_round_rectangle((center_x - next_w / 2, next_y - next_h / 2,
                                       center_x + next_w / 2, next_y + next_h / 2),
                                      fill=self.color('fill'), border="#ffffff",
                                      outset=outset, radius=radius)

        if self.mgr.gameState() == GameState.pre_game:
            next_time = self.mgr.gameClock()
            next_status = "Start: "
        else:
            next_time = self.mgr.gameClock() + 3 * 60
            next_status = "Next: "

        next_in_text = next_status + "%2d:%02d" % (next_time // 60, next_time % 60)
        self.create_text((center_x - next_w / 2 + 20, next_y), text=next_in_text,
                         fill="#ffffff", font=title_font, anchor=tk.W)


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

        if is_rpi():
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
