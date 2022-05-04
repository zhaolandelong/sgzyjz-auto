#!/usr/bin/python3
from time import sleep
from pywinauto.application import Application
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.04

z = 1  # zoom rate
GRID_SIZE = 32 * z
GRID_MAX_X = 12
GRID_MAX_Y = 10
GRID_FIRST = (34.5 * z, 113.5 * z)
GENERAL_FIRST = (550 * z, 150 * z)
EMPTY_POS = (10 * GRID_SIZE, 2 * GRID_SIZE)
ITEM_HEIGHT = 24 * z
LINE_HEIGHT = 20 * z
ITEM_ACT_LIST = ('use', 'send', 'drop', 'view')
ANIMATION_DELAY = 1.6


def grid_pos(x, y):
    return (round(GRID_FIRST[0] + x * GRID_SIZE), round(GRID_FIRST[1] + y * GRID_SIZE))


def define_click(offsetLeft=0, offsetTop=0):
    def _click(coords=(None, None), times=1, button='left'):
        pyautogui.moveTo(coords[0] + offsetLeft, coords[1] + offsetTop)
        for _ in range(times):
            pyautogui.mouseDown(button=button)
            pyautogui.mouseUp(button=button)
            # main_win.press_mouse_input(
            #     button, coords, key_up=False, absolute=False)
            # main_win.release_mouse_input(
            #     button, coords, key_down=False, absolute=False)
    return _click


def define_select_general(generals_list, click_fun):
    def _select_general(general_name, offset=(0, 0)):
        click_fun((GENERAL_FIRST[0], GENERAL_FIRST[1] +
                   generals_list.index(general_name) * LINE_HEIGHT))
        general_grid = (7 + offset[0], 6 + offset[1])
        click_fun(grid_pos(general_grid[0], general_grid[1]), button='right')
        return general_grid
    return _select_general


def define_click_relative_grid(click_fun):
    def _click_relative_grid(cur_grid=(0, 0), offset=(0, 0)):
        grid_x = cur_grid[0] + offset[0]
        grid_y = cur_grid[1] + offset[1]
        if grid_x >= GRID_MAX_X:
            for _ in range(grid_x - GRID_MAX_X + 1):
                click_fun(grid_pos(GRID_MAX_X, grid_y))
            grid_x = GRID_MAX_X - 1
        if grid_x <= 0:
            for _ in range(1 - grid_x):
                click_fun(grid_pos(0, grid_y))
            grid_x = 1
        if grid_y >= GRID_MAX_Y:
            for _ in range(grid_y - GRID_MAX_Y + 1):
                click_fun(grid_pos(grid_x, GRID_MAX_Y))
            grid_y = GRID_MAX_Y - 1
        if grid_y <= 0:
            for _ in range(1 - grid_y):
                click_fun(grid_pos(grid_x, 0))
            grid_y = 1
        click_fun(grid_pos(grid_x, grid_y))
        return (grid_x, grid_y)
    return _click_relative_grid


def define_general_act(click_fun):
    def _general_act(general_grid=(7, 6), act=(3, 0, 0), target=(0, 0)):
        pos = grid_pos(general_grid[0], general_grid[1])
        act_x = pos[0] + 3 * LINE_HEIGHT
        item_x = pos[0] + 3 * ITEM_HEIGHT
        act_y = pos[1]
        item_y = pos[1] + LINE_HEIGHT
        strategy_y = pos[1] + ITEM_HEIGHT
        list_y = pos[1] + GRID_SIZE
        if general_grid[0] > 5:
            act_x -= 6 * LINE_HEIGHT
            item_x -= 6 * ITEM_HEIGHT
        if general_grid[1] > 7:
            act_y = 11 * GRID_SIZE
            item_y = 14 * ITEM_HEIGHT
            list_y = 11 * GRID_SIZE - ITEM_HEIGHT
        click_fun((act_x, act_y + act[0] * ITEM_HEIGHT))
        if act[0] == 3:
            return
        if act[0] == 1:
            click_fun((item_x, strategy_y + act[1] * LINE_HEIGHT))
            click_fun(EMPTY_POS, 2)
        if act[0] == 2:
            click_fun((item_x, item_y + act[1] * ITEM_HEIGHT))
            click_fun((item_x, list_y + act[2] * LINE_HEIGHT))
            click_fun(EMPTY_POS, 2)
        define_click_relative_grid(click_fun)(general_grid, target)
        click_fun(EMPTY_POS, 2)
        sleep(ANIMATION_DELAY)
        click_fun(EMPTY_POS, 2)
    return _general_act


def define_run_general(click_fun, select_fun):
    def _run_general(parms):
        '''
        params may be like:
         ('gy', (2, 0), ('item', 'send', 0), (0, -1)),
         (('lb', (0, 0)), (-3, 0), 'rest'),
        '''
        target = (0, 0)
        offset = (0, 0)
        name = parms[0]
        extra = []
        if len(parms) > 4:
            extra = parms[4]
        if len(parms) > 3:
            target = parms[3]
        if isinstance(name, tuple):
            offset = name[1]
            name = name[0]
        init_grid = select_fun(name, offset)
        curr_grid = define_click_relative_grid(click_fun)(init_grid, parms[1])
        act_arr = [0, 0, 0]
        if parms[2] == 'rest':
            act_arr[0] = 3
        elif isinstance(parms[2], tuple):
            if parms[2][0] == 'item':
                act_arr = [2, ITEM_ACT_LIST.index(parms[2][1]), parms[2][2]]
            elif parms[2][0] == 'strategy':
                act_arr = [1, 0, 0]
        define_general_act(click_fun)(curr_grid, act_arr, target)
        if len(extra) > 0:
            for ext_pos in extra:
                click_fun(EMPTY_POS, 1)
                click_fun(ext_pos)
                click_fun(EMPTY_POS, 1)
            click_fun(EMPTY_POS, 4)
    return _run_general


def main(path, generals_list, rnd_list, delay_list=[], start=0, debug=0):
    app = Application(backend='win32').connect(path=path)
    main_win = app.window(class_name='SDL_app')
    main_win.set_focus()
    # main_win.move_window(0, 0)
    main_win_rect = main_win.rectangle()

    do_click = define_click(main_win_rect.left,  main_win_rect.top)
    run_general = define_run_general(
        do_click,
        define_select_general(generals_list, do_click),
    )

    delay_list_len = len(delay_list)
    for rnd_idx in range(start, len(rnd_list)):
        print("Round", rnd_idx, "start")
        if debug > 0:
            print("sv:", rnd_idx)
            pyautogui.press(['ctrl', 'ctrl', '7', 's'])
            pyautogui.press([str(rnd_idx//10), str(rnd_idx % 10), 'enter'])
            sleep(0.2)
            pyautogui.press(['esc', 'esc'])
            sleep(0.2)
            if debug > 1:
                tmp = input("Enter:")
                if tmp != "":
                    rnd_idx = int(tmp)
                elif tmp == "e":
                    exit()
                main_win.set_focus()
        for _act in rnd_list[rnd_idx]:
            print(_act)
            run_general(_act)
            do_click(EMPTY_POS, 4)
        # click yes
        print("Round ", rnd_idx, "finish")
        do_click((7 * GRID_SIZE, 8 * GRID_SIZE))
        # empty click
        times = 2
        if delay_list_len > rnd_idx:
            times = delay_list[rnd_idx]
        for _ in range(times):
            do_click(EMPTY_POS, 2)
            pyautogui.mouseDown()
            sleep(1)
            pyautogui.mouseUp()
            do_click(EMPTY_POS, 2)
        print("Round ", rnd_idx, "over")
