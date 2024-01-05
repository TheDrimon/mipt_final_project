from timeit import default_timer as timer
import GUI
import pygame as pg
import numpy as np
import torch
device = torch.device("cuda")


def field_init(w_type="cylinder"):
    global NL, idxs, cxs, cys, Cxs, Cys, weights
    global F
    NL = 9
    # маски для расчётов
    idxs = np.arange(NL)
    cxs = torch.asarray([-1, 0, 1,
                         -1, 0, 1,
                         -1, 0, 1], dtype=torch.int8).cuda()
    cys = torch.asarray([1, 1, 1,
                         0, 0, 0,
                         -1, -1, -1], dtype=torch.int8).cuda()
    Cxs = np.byte(cxs.cpu())
    Cys = np.byte(cys.cpu())
    weights = np.array([1/36, 1/9, 1/36,
                        1/9,  4/9, 1/9,
                        1/36, 1/9, 1/36])

    Nx, Ny = N * He//Wi, N

    # Начальные условия
    global wall, rho0, tau, OO

    rho0 = 10  # average density
    tau = 0.65  # collision timescale

    F = (torch.ones((Ny, Nx, NL), dtype=torch.float32)
         * rho0 / NL).cuda()  # поле жидкости

    OO = torch.zeros(F.shape, dtype=torch.float32).cuda()

    F += 0.01*torch.randn(Ny, Nx, NL).cuda()

    Y, X = torch.meshgrid(torch.range(0, Ny-1), torch.range(0, Nx-1))

    # создание потока
    F[:, :, 1] += (2 + .4 * torch.cos(torch.pi * X.cuda()/Nx * 8))

    rho = torch.sum(F, 2).cuda()
    for i in idxs:
        F[:, :, i] *= rho0 / rho

    # wall boundary
    wall = torch.zeros((Ny, Nx), dtype=torch.bool).cuda()
    if w_type == "none":
        pass
    if w_type == "cylinder":
        wall = (X - Nx/2)**2 + (Y - Ny/4)**2 < (Nx/4)**2
    if w_type == "rectangle":
        wall[Nx // 3: 2 * Nx // 3, Nx // 3: 2 * Nx // 3] = True

    global display
    display.update(F, wall)


def init():
    # GUI init <--
    global N, screen, Wi, He, b
    global Buttons, display

    Wi, He = 1400, 400
    N = 1400  # 864  # 432  # Wi liquid resolition
    b = 30  # отступ меню

    pg.init()

    screen = pg.display.set_mode((Wi, He + b))

    # карта интерфейса
    Buttons = [GUI.Button(screen, 0, He, b*2, b,
                          "reset"),
               GUI.Switch(screen, b*4.2, He, b*2, b,
                          ["draw", "select", "del"]),
               GUI.Switch(screen, b*2.1, He, b*2, b,
                          ["play", "pause"]),
               GUI.Switch(screen, b*6.3, He, b*4, b,
                          ["none", "cylinder", "rectangle"]),
               GUI.Switch(screen, b*10.4, He, b*2, b,
                          ["rot", "rho"])]
    display = GUI.Display(screen, 0, 0, Wi, He)

    field_init()  # MODEL init


def step_calc():
    global wall, F
    global display
    global Feq

    # Drift
    for i, cx, cy in zip(idxs, Cxs, Cys):
        F[:, :, i] = torch.roll(F[:, :, i], cx, 1)
        F[:, :, i] = torch.roll(F[:, :, i], cy, 0)

    # Calculate fluid variables
    rho = torch.sum(F, 2).cuda()
    ux = torch.sum(F*cxs, 2) / rho
    uy = torch.sum(F*cys, 2) / rho

    # Apply Collision
    Feq = OO
    for i, cx, cy, w in zip(idxs, Cxs, Cys, weights):
        ss = 3 * (cx*ux + cy*uy)

        Feq[:, :, i] = rho * w * (1 + ss + ss*ss/2 - 1.5*(ux*ux + uy*uy))

    F -= (1.0 / tau) * (F - Feq)

    # Apply boundary
    F[wall, :] = F[wall, :][:, [-1, -2, -3, -4, -5, -6, -7, -8, 0]]

    # display.update(F, wall)


def interract(press, pos):
    global Buttons
    global wall

    x, y = pos[:2]  # координаты косания
    if 0 < x < Wi:
        if 0 < y < He:
            # работа с полем
            mode = Buttons[1].text[Buttons[1].state]
            if mode == "draw":
                wall[x * N//Wi, y * N//Wi] = True

            if mode == "select":
                G = display.get(x * N//Wi, y * N//Wi)
                pg.display.set_caption(str((x * N//Wi, y * N//Wi))
                                       + " col = " + str(np.int16(G[0].cpu()))
                                       + " rho = " + str(G[1].cpu()))
            elif mode == "del":
                wall[x * N//Wi, y * N//Wi] = False

        elif He < y < He + b:
            for Bt in Buttons:  # переключение кнопок
                if Bt.pos[0] < x < Bt.pos[0] + Bt.size[0]:
                    Bt.press(press)

        if press == 0:
            for Bt in Buttons:  # сброс кнопок
                Bt.reset()

    # реакции кнопок
    if Buttons[0].active:
        field_init(Buttons[3].text[Buttons[3].state])
        Buttons[0].active = 0


def swipe(pos, prs):
    if prs == (-1, -1):
        return

    if not (0 < prs[0] < Wi):
        return
    if not (0 < prs[1] < He):
        return

    global wall, display
    x, y = pos[:2]
    if 0 < x < Wi:
        if 0 < y < He:
            # работа с полем
            pg.display.set_caption(str((x, y)))
            mode = Buttons[1].text[Buttons[1].state]

            if mode == "draw":
                wall[x * N//Wi, y * N//Wi] = True

            if mode == "select":
                G = display.get(x * N//Wi, y * N//Wi)
                pg.display.set_caption(str((x * N//Wi, y * N//Wi))
                                       + " col = " + str(np.int16(G[0].cpu()))
                                       + " rho = " + str(G[1].cpu()))
            elif mode == "del":
                wall[x * N//Wi, y * N//Wi] = False


def draw():
    screen.fill((0, 0, 0))

    if Buttons[4].text[Buttons[4].state] == "rho":
        display.simple_draw()  # отрисовка по плотности
    else:
        display.draw()  # отрисовка по скорости кручения

    for i in Buttons:  # интерфейс
        i.draw()

    pg.display.update()


def main():
    init()

    clock = pg.time.Clock()
    RUN = True
    prs = (-1, -1)

    while RUN:
        if Buttons[2].state:
            start = timer()
            for i in range(4):
                step_calc()
            print(str((timer() - start) * 1000)[:2], "мс")

        display.update(F, wall)
        draw()

        # clock.tick(600)

        for event in pg.event.get():  # события
            if event.type == pg.QUIT:
                RUN = False
                pg.quit()

            elif event.type == pg.MOUSEBUTTONDOWN:
                interract(1, event.pos)
                prs = event.pos

            elif event.type == pg.MOUSEBUTTONUP:
                interract(0, event.pos)
                prs = (-1, -1)

            elif event.type == pg.MOUSEMOTION:
                swipe(event.pos, prs)


if __name__ == "__main__":
    main()
