import pygame
import numpy as np
import torch
device = torch.device("cuda")

color = [(200, 200, 200),
         (180, 180, 240)]  # базовые цвета кнопок

# карты течений
cxs = torch.ByteTensor([-1, 0, 1,
                        -1, 0, 1,
                        -1, 0, 1]).cuda()
cys = torch.ByteTensor([1, 1, 1,
                        0, 0, 0,
                        -1, -1, -1]).cuda()
OOO = torch.zeros(3).cuda()


class GUI_window:  # класс пустого окна
    def __init__(self, screen, Px, Py, Sx, Sy):
        self._screen = screen
        self.pos = (Px, Py)
        self.size = (Sx, Sy)

    def draw(self):
        pygame.draw.rect(self._screen, color[0], (self.pos, self.size), 2)


class Display(GUI_window):  # класс экрана
    def __init__(self, screen, Px, Py, Sx, Sy, F=np.ones((1, 1, 9)), Walls=torch.zeros((1, 1), dtype=torch.bool)):
        super().__init__(screen, Px, Py, Sx, Sy)
        self._F = F  # поле жидкости
        self._Walls = Walls
        self._dat = torch.ones((2, 1, 1))

    def update(self, F, cylinder):
        self._F = F
        self._Walls = cylinder

    def simple_draw(self):
        m = 2  # np.mean(np.sum(self.F[:,:,:3], 2))
        mm = 3  # np.min(np.sum(self.F[:,:,:3], 2))
        # W = self.F[:,:,:3] * 0 для доработки
        K = 255*((m - torch.sum(self._F[:, :, :3], 2))/(mm+1e-14))

        W = torch.zeros((len(K), len(K[0]), 3)).cuda()
        W[:, :, 2] = 50
        W[:, :, 0][K < 0] -= K[K < 0]
        W[:, :, 1][K > 0] += K[K > 0]

        W[W > 255] = 255
        # for i in range(3):
        #    W[W[:, :, i] > 255, i] = 255
        W[self._Walls] = OOO
        self._screen.blit(pygame.transform.scale(
            pygame.surfarray.make_surface(np.array(W.cpu())), self.size), self.pos)

    def get(self, x, y):  # получение точки

        return self._dat[0][x, y], self._dat[1][x, y]

    def draw(self):  # отрисовка
        rho = torch.sum(self._F, 2).cuda()
        ux = torch.sum(self._F*cxs, 2) / rho
        uy = torch.sum(self._F*cys, 2) / rho

        vorticity = (torch.roll(ux, -1, 0) - torch.roll(ux, 1, 0)) - \
            (torch.roll(uy, -1, 1) - torch.roll(uy, 1, 1))  # карта кручения

        m = torch.mean(vorticity)
        mm = torch.min(vorticity)

        K = 255 * ((m - vorticity) / (mm + 1e-14))

        W = torch.zeros((len(K), len(K[0]), 3)).cuda()
        W[:, :, 2] = 50
        W[:, :, 0][K < 0] = -K[K < 0]
        W[:, :, 1][K > 0] = K[K > 0]
        W[self._Walls] = OOO

        self._dat = [W, rho]

        self._screen.blit(pygame.transform.scale(
            pygame.surfarray.make_surface(np.array((255**0.3*W**0.7//1).cpu())), self.size), self.pos)


class Button(GUI_window):  # кнопки
    def __init__(self, screen, Px, Py, Sx, Sy, text=""):
        super().__init__(screen, Px, Py, Sx, Sy)
        self._text = text
        self.pressed = 0
        self.active = 0

    def draw(self):  # визуализация состояния кнопки
        pygame.draw.rect(
            self._screen, color[self.pressed], (self.pos, self.size), 2+self.pressed*5)

        if self._text != '':
            # общая функция выравнивания размера
            M = int(min(2*self.size[0] // len(self._text), self.size[1]))
            T_pose = (self.pos[0]+5, self.pos[1]-3)

            self._screen.blit(pygame.font.SysFont('arial', M).render(
                self._text, False, (250, 250, 250)), T_pose)

    def press(self, pressed):  # событие
        if self.pressed and not pressed:
            self.active = 1
        else:
            self.active = 0
        self.pressed = pressed

    def reset(self):
        self.pressed = 0


class Switch(GUI_window):  # переключатели
    def __init__(self, screen, Px, Py, Sx, Sy, text=[""]):
        super().__init__(screen, Px, Py, Sx, Sy)
        self.pressed = 0
        self.state = 0
        self.text = text

    def draw(self):  # визуализация состояния переключателя
        pygame.draw.rect(
            self._screen, color[self.pressed], (self.pos, self.size), 2)

        if self.text[self.state] != '':
            # общая функция выравнивания размера текста
            M = int(
                min(1.9*self.size[0] // (1.4+len(self.text[self.state])**0.7), self.size[1]))
            T_pose = (self.pos[0]+5, self.pos[1]-5)
            self._screen.blit(pygame.font.SysFont('arial', M).render(
                self.text[self.state], False, (250, 250, 250)), T_pose)

    def reset(self):
        self.pressed = 0

    def press(self, pressed):  # событие
        if self.pressed and not pressed:
            self.state = (self.state + 1) % len(self.text)

        self.pressed = pressed
